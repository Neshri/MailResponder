import time
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import TARGET_USER_GRAPH_ID
from graph_api import make_graph_api_call, mark_email_as_read
from database import (
    get_student_progress, 
    get_current_active_problem, 
)
from email_parser import (
    _parse_graph_email_item, 
    extract_student_message_from_reply, 
    get_name_from_email
)
from problem_catalog import START_PHRASES, NUM_LEVELS
from conversation_manager import (
    handle_start_new_problem_main_thread, 
    llm_evaluation_and_reply_task, 
    process_completed_problem, 
    inform_level_error
)

# =========================================================================
# 1. ORCHESTRATOR
# =========================================================================

def graph_check_emails():
    """Main Orchestrator: Fetches, Filters, Classifies, and Executes."""
    
    # Step 1: Fetch
    unread_messages_raw = _fetch_raw_messages()
    if not unread_messages_raw:
        return

    logging.info(f"Hittade {len(unread_messages_raw)} olästa e-post. Startar bearbetning...")

    # Step 2: Group by User & Filter Noise (The Race Condition Fix)
    valid_processing_queue = []
    user_batches = _group_by_user(unread_messages_raw)
    
    for sender_email, emails in user_batches.items():
        valid_emails = _filter_batch_for_user(sender_email, emails)
        valid_processing_queue.extend(valid_emails)

    # Sort the clean queue chronologically
    valid_processing_queue.sort(key=lambda x: x['received_datetime'])

    # Step 3: Processing Loop (Classify & Execute Sequentially)
    # We process linearly so that a "Start Command" updates the DB immediately,
    # allowing subsequent emails in the same batch to be treated as valid replies.
    
    llm_tasks = []
    
    for email_data in valid_processing_queue:
        # Classify the action based on CURRENT database state
        task = _classify_email_action(email_data)
        
        if task['type'] == 'llm':
            # Queue LLM tasks to run in parallel later
            llm_tasks.append(task)
            
        elif task['type'] == 'start_command':
            # Execute Start Commands IMMEDIATELY to update DB state
            if handle_start_new_problem_main_thread(task['data'], task['level_idx']):
                mark_email_as_read(task['data']["graph_msg_id"])
                
        elif task['type'] == 'info_error':
            # Execute errors immediately
            inform_level_error(task['data'], task['level_idx'])
            mark_email_as_read(task['data']["graph_msg_id"])
            
        elif task['type'] == 'ignore':
            # Just mark as read (logging handled in classify)
            mark_email_as_read(task['data']["graph_msg_id"])

    # Step 4: Execute gathered LLM tasks
    _execute_llm_tasks(llm_tasks)
    
    logging.info(f"Cykel klar. {len(valid_processing_queue)} meddelanden behandlades.")


# =========================================================================
# 2. HELPER FUNCTIONS
# =========================================================================

def _fetch_raw_messages():
    """Fetching logic only."""
    select_fields = "id,subject,from,sender,receivedDateTime,bodyPreview,body,internetMessageId,conversationId,isRead,internetMessageHeaders,attachments"
    params = {"$filter": "isRead eq false", "$select": select_fields, "$orderby": "receivedDateTime asc"}
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/mailFolders/inbox/messages"
    
    logging.info("Söker olästa e-post (Graph)...")
    response_data = make_graph_api_call("GET", endpoint, params=params)
    
    if response_data and "value" in response_data:
        return response_data["value"]
    return None

def _group_by_user(raw_messages):
    """Parses JSON and groups into a dict: { 'user@email.com': [email1, email2] }"""
    batches = defaultdict(list)
    for item in raw_messages:
        email_data = _parse_graph_email_item(item)
        
        # Immediate System Filter
        if not email_data["sender_email"] or \
           email_data["sender_email"] == TARGET_USER_GRAPH_ID.lower() or \
           'mailer-daemon' in email_data["sender_email"] or \
           'noreply' in email_data["sender_email"]:
            mark_email_as_read(email_data["graph_msg_id"])
            continue
            
        batches[email_data["sender_email"]].append(email_data)
    return batches

def _filter_batch_for_user(sender_email, emails):
    """
    Event Coalescing Logic:
    If a valid 'Start Command' is found, discard all emails received BEFORE it.
    """
    # 1. Sort chronological
    emails.sort(key=lambda x: x['received_datetime'])
    
    # 2. Get User State (CRITICAL: Do not filter based on Subject if user is Active)
    _, active_problem_info, _, _ = get_current_active_problem(sender_email)
    
    last_start_index = -1
    
    # 3. Scan for the LATEST Reset Command
    for i, email in enumerate(emails):
        is_reset = False
        
        # Check Body (Always a valid reset)
        body_clean = email["cleaned_body"].lower().strip().strip("\"").strip("'").strip(" ")
        if any(body_clean.startswith(p.lower()) for p in START_PHRASES):
            is_reset = True
            
        # Check Subject (Only valid if NOT playing)
        elif email["subject"]:
            has_phrase = any(p.lower() in email["subject"].lower() for p in START_PHRASES)
            if has_phrase:
                if not active_problem_info:
                    is_reset = True
                else:
                    logging.debug(f"Filter: Ignoring Subject-based Start from {sender_email} (User is Active).")

        if is_reset:
            last_start_index = i

    # 4. Filter (Throw away obsolete emails)
    start_processing_at = 0
    if last_start_index != -1:
        start_processing_at = last_start_index
        # Mark superseded emails as read immediately
        if start_processing_at > 0:
            logging.warning(f"Filter: Dropping {start_processing_at} obsolete emails from {sender_email}.")
            for k in range(0, start_processing_at):
                mark_email_as_read(emails[k]["graph_msg_id"])

    return emails[start_processing_at:]

def _classify_email_action(email_data):
    """Decides WHAT to do with a single valid email."""
    sender = email_data["sender_email"]
    
    # Fetch fresh DB state
    student_next_level_idx, _ = get_student_progress(sender)
    active_hist_str, active_problem_info, active_problem_level_idx, active_convo_id = get_current_active_problem(sender)
    
    # --- Check for Start Command ---
    detected_level = -1
    is_explicit = False
    
    # Body Check
    body_clean = email_data["cleaned_body"].lower().strip().strip("\"").strip("'").strip(" ")
    for idx, phrase in enumerate(START_PHRASES):
        if idx >= NUM_LEVELS: break
        if body_clean.startswith(phrase.lower()):
            detected_level = idx
            is_explicit = True
            break
            
    # Subject Check (Safe logic)
    if not is_explicit and not active_problem_info and email_data["subject"]:
        for idx, phrase in enumerate(START_PHRASES):
            if idx >= NUM_LEVELS: break
            if phrase.lower() in email_data["subject"].lower():
                detected_level = idx
                break
    
    # --- Action Selection ---
    if detected_level != -1:
        if detected_level <= student_next_level_idx:
            return {
                'type': 'start_command',
                'data': email_data,
                'level_idx': detected_level
            }
        else:
            return {
                'type': 'info_error',
                'data': email_data,
                'level_idx': student_next_level_idx
            }
            
    if active_problem_info:
        # Prepare LLM payload
        full_body = email_data["cleaned_body"]
        if not full_body.strip(): full_body = email_data.get('body_preview') or ""
        
        msg_content = extract_student_message_from_reply(full_body, active_hist_str)
        if not msg_content:
            logging.warning(f"Classify: Empty body from {sender}. Ignoring.")
            return {'type': 'ignore', 'data': email_data}

        student_name = get_name_from_email(sender)
        db_entry = f"{student_name}: {msg_content}\n\n"
        
        return {
            'type': 'llm',
            'email_data': email_data,
            'full_history': active_hist_str + db_entry,
            'problem_info': active_problem_info,
            'msg_content': msg_content,
            'level_idx': active_problem_level_idx,
            'convo_id': active_convo_id,
            'db_entry': db_entry
        }

    # Fallback (No active problem, no start command)
    return {
        'type': 'info_error',
        'data': email_data,
        'level_idx': student_next_level_idx
    }

def _execute_llm_tasks(tasks):
    """Submits to ThreadPool and handles results."""
    if not tasks: return

    logging.info(f"Exec: Submitting {len(tasks)} LLM tasks...")
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future_to_task = {
            executor.submit(
                llm_evaluation_and_reply_task,
                t['email_data']["sender_email"],
                t['full_history'],
                t['problem_info'],
                t['msg_content'],
                t['level_idx'],
                t['convo_id'],
                t['email_data'],
                t['db_entry'],
                t['problem_info']['id']
            ): t for t in tasks
        }
        
        for future in as_completed(future_to_task):
            try:
                res = future.result()
                if not res: continue
                
                email_data = res["email_data"]
                
                if res.get("error"):
                    logging.error(f"LLM Error for {email_data['graph_msg_id']}: {res['error']}")
                    # Do NOT mark as read, so it retries next cycle
                    continue 
                    
                if res.get("send_reply"):
                    if process_completed_problem(res, email_data):
                        mark_email_as_read(email_data["graph_msg_id"])
                elif res.get("mark_as_read"):
                    mark_email_as_read(email_data["graph_msg_id"])
                    
            except Exception as e:
                logging.error(f"Thread execution failed: {e}", exc_info=True)