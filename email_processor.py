import time
import logging
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import TARGET_USER_GRAPH_ID, GRAPH_API_ENDPOINT
from graph_api import get_graph_token, jwt_is_expired, make_graph_api_call, graph_send_email, mark_email_as_read
from database import get_student_progress, set_active_problem, get_current_active_problem, append_to_active_problem_history, clear_active_problem, save_completed_conversation, update_student_level
from email_parser import _parse_graph_email_item, extract_student_message_from_reply, get_name_from_email, clean_email_body
from problem_catalog import PROBLEM_CATALOGUES, START_PHRASES, NUM_LEVELS
from conversation_manager import _handle_start_new_problem_main_thread, _llm_evaluation_and_reply_task, process_completed_problem, inform_level_error
from config import ULLA_IMAGE_WARNING

def graph_check_emails():
    """
    Core email processing loop: Check unread emails, parse and process them.
    """
    select_fields = "id,subject,from,sender,receivedDateTime,bodyPreview,body,internetMessageId,conversationId,isRead,internetMessageHeaders,attachments"
    params = {"$filter": "isRead eq false", "$select": select_fields, "$orderby": "receivedDateTime asc"}
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/mailFolders/inbox/messages"
    logging.info("Söker olästa e-post (Graph)...")
    response_data = make_graph_api_call("GET", endpoint, params=params)
    if not response_data or "value" not in response_data:
        logging.info("Inga olästa e-post eller fel." if response_data is None else "Inga olästa e-post (Graph).")
        return
    unread_messages_raw = response_data["value"]
    if not unread_messages_raw:
        logging.info("Inga olästa e-post (Graph).")
        return
    logging.info(f"Hittade {len(unread_messages_raw)} olästa e-post (Graph). Förbereder bearbetning...")

    llm_tasks_to_submit = []
    emails_to_process_sequentially = []
    processed_ids_in_phase1 = set()

    # --- Phase 1: Parse and Categorize emails (Main Thread) ---
    for msg_graph_item in unread_messages_raw:
        email_data = _parse_graph_email_item(msg_graph_item)
        if not email_data["sender_email"] or email_data["sender_email"] == TARGET_USER_GRAPH_ID.lower() or \
           'mailer-daemon' in email_data["sender_email"] or 'noreply' in email_data["sender_email"]:
            logging.warning(f"Main: Skippar {email_data['graph_msg_id']} (själv/system). Markerar läst.")
            mark_email_as_read(email_data["graph_msg_id"])
            processed_ids_in_phase1.add(email_data["graph_msg_id"])
            continue

        student_next_eligible_level_idx, _ = get_student_progress(email_data["sender_email"])
        active_hist_str, active_problem_info, active_problem_level_idx_db, active_problem_convo_id_db = get_current_active_problem(email_data["sender_email"])

        detected_start_level_idx = -1
        is_explicit_body_start_command = False

        for level_idx, phrase_text in enumerate(START_PHRASES):
            if level_idx >= NUM_LEVELS:
                break
            current_start_phrase_lower = phrase_text.lower()
            if email_data["cleaned_body"].lower().strip().strip("\"").strip("'").strip(" ").startswith(current_start_phrase_lower):
                detected_start_level_idx = level_idx
                is_explicit_body_start_command = True
                break

        if not is_explicit_body_start_command:
            for level_idx, phrase_text in enumerate(START_PHRASES):
                if level_idx >= NUM_LEVELS:
                    break
                current_start_phrase_lower = phrase_text.lower()
                if email_data["subject"] and current_start_phrase_lower in email_data["subject"].lower():
                    if not active_problem_info:
                        detected_start_level_idx = level_idx
                        break
                    else:
                        logging.info(f"Main: Startkommando i ÄMNESRAD ignorerat för {email_data['sender_email']} (nivå {level_idx +1}) p.g.a. pågående aktivt problem ({active_problem_info['id']}). Tolkas som svar.")
                        break

        if detected_start_level_idx != -1:
            if detected_start_level_idx <= student_next_eligible_level_idx:
                if is_explicit_body_start_command:
                    logging.info(f"Main: Startkommando explicit i E-POSTKROPP detekterat för behörig nivå {detected_start_level_idx + 1} från {email_data['sender_email']}. Köar 'start_command'.")
                else:
                    logging.info(f"Main: Startkommando i ÄMNESRAD detekterat för behörig nivå {detected_start_level_idx + 1} (inget aktivt problem) från {email_data['sender_email']}. Köar 'start_command'.")

                emails_to_process_sequentially.append({
                    "type": "start_command",
                    "data": email_data,
                    "level_idx": detected_start_level_idx
                })
            else:
                logging.warning(f"Main: Student {email_data['sender_email']} försökte starta nivå {detected_start_level_idx + 1}, men är endast behörig upp till (och med) nivå {student_next_eligible_level_idx + 1}.")

                msg_body = (f"Hej! Du försökte starta Nivå {detected_start_level_idx + 1} (index {detected_start_level_idx}), "
                            f"men du har för närvarande endast låst upp nivåer upp till och med Nivå {student_next_eligible_level_idx + 1} (index {student_next_eligible_level_idx}).")

                if student_next_eligible_level_idx < NUM_LEVELS:
                     msg_body += (f"\nFör att spela din nästa upplåsta nivå ({student_next_eligible_level_idx + 1}), "
                                  f"använd startfrasen: \"{START_PHRASES[student_next_eligible_level_idx]}\"")

                if email_data.get("has_images"):
                    msg_body = ULLA_IMAGE_WARNING + "\n\n" + msg_body

                reply_subject_locked = email_data["subject"] if email_data['subject'] and not email_data['subject'].lower().startswith("re:") else f"Re: {email_data['subject']}"
                if not reply_subject_locked: reply_subject_locked = "Angående nivåstart"

                graph_send_email(email_data["sender_email"], reply_subject_locked, msg_body,
                                 email_data["internet_message_id"],
                                 email_data["references_header_value"],
                                 email_data["graph_conversation_id_incoming"])
                mark_email_as_read(email_data["graph_msg_id"])
                processed_ids_in_phase1.add(email_data["graph_msg_id"])

        elif active_hist_str and active_problem_info:
            logging.info(f"Main: E-post från {email_data['sender_email']} är svar på aktivt problem ({active_problem_info['id']}). Köar för LLM-bearbetning.")
            # Extract only the new content, excluding quoted replies
            full_body = email_data["cleaned_body"]
            if not full_body.strip():
                full_body = email_data.get('body_preview') or ""

            body_for_llm_task = extract_student_message_from_reply(full_body, active_hist_str)

            if not body_for_llm_task:
                logging.warning(f"Main: Tomt meddelande från {email_data['sender_email']} i svar på aktivt problem. Markerar som läst.")
                mark_email_as_read(email_data["graph_msg_id"])
                processed_ids_in_phase1.add(email_data["graph_msg_id"])
                continue

            student_name = get_name_from_email(email_data["sender_email"])
            student_entry_for_db = f"{student_name}: {body_for_llm_task}\n\n"

            llm_tasks_to_submit.append({
                "email_data_for_result": email_data,
                "full_history_string": active_hist_str + student_entry_for_db,
                "problem_info": active_problem_info,
                "latest_student_message_cleaned": body_for_llm_task,
                "problem_level_idx_for_prompt": active_problem_level_idx_db,
                "active_problem_convo_id_db": active_problem_convo_id_db,
                "student_entry_for_db": student_entry_for_db,
                "problem_id": active_problem_info['id']
            })
        else:
            emails_to_process_sequentially.append({
                "type": "inform_wrong_level_or_ignore",
                "data": email_data,
                "level_idx": student_next_eligible_level_idx
            })

    # --- Phase 2: Process LLM tasks in ThreadPool ---
    llm_results_from_threads = []
    if llm_tasks_to_submit:
        logging.info(f"Skickar {len(llm_tasks_to_submit)} uppgifter till LLM trådpool...")
        with ThreadPoolExecutor(max_workers=1) as executor:
            future_to_task_package = {
                executor.submit(
                    _llm_evaluation_and_reply_task,
                    task["email_data_for_result"]["sender_email"],
                    task["full_history_string"],
                    task["problem_info"],
                    task["latest_student_message_cleaned"],
                    task["problem_level_idx_for_prompt"],
                    task["active_problem_convo_id_db"],
                    task["email_data_for_result"],
                    task["student_entry_for_db"],
                    task.get("problem_id")
                ): task for task in llm_tasks_to_submit
            }
            for future in as_completed(future_to_task_package):
                try:
                    llm_result_package = future.result()
                    llm_results_from_threads.append(llm_result_package)
                except Exception as exc_llm_future:
                    logging.error(f"En LLM-uppgift genererade ett oväntat undantag: {exc_llm_future}", exc_info=True)

    # --- Check for LLM failures ---
    llm_failures = [rp for rp in llm_results_from_threads if rp.get("error")]
    if llm_failures:
        logging.warning(f"LLM failures detected ({len(llm_failures)}/{len(llm_results_from_threads)} tasks failed). Aborting email processing to retry later.")
        return  # Exit early without processing, so emails remain unread for next cycle

    # --- Phase 3: Process results from LLM threads (Main Thread) ---
    for result_package in llm_results_from_threads:
        email_data = result_package["email_data"]
        if email_data["graph_msg_id"] in processed_ids_in_phase1:
            continue

        if not result_package["error"] and result_package["send_reply"]:
            success = process_completed_problem(result_package, email_data)
            if success:
                mark_email_as_read(email_data["graph_msg_id"])
                processed_ids_in_phase1.add(email_data["graph_msg_id"])
        elif result_package["error"]:
             logging.error(f"Main: LLM-arbetare returnerade fel för {email_data['graph_msg_id']}.")
        elif not result_package["send_reply"]:
             logging.info(f"Main: LLM-arbetare indikerade inget svar ska skickas för {email_data['graph_msg_id']} (t.ex. tomt meddelande från student).")
             if result_package.get("mark_as_read", False):
                 mark_email_as_read(email_data['graph_msg_id'])
                 processed_ids_in_phase1.add(email_data["graph_msg_id"])

    # --- Phase 4: Process sequential tasks (Main Thread) ---
    for task in emails_to_process_sequentially:
        email_data_seq = task["data"]
        if email_data_seq["graph_msg_id"] in processed_ids_in_phase1:
            continue

        student_level_idx_seq = task["level_idx"]
        if task["type"] == "start_command":
            if _handle_start_new_problem_main_thread(email_data_seq, student_level_idx_seq):
                mark_email_as_read(email_data_seq["graph_msg_id"])
                processed_ids_in_phase1.add(email_data_seq["graph_msg_id"])
        elif task["type"] == "inform_wrong_level_or_ignore":
            inform_level_error(email_data_seq, student_level_idx_seq)
            mark_email_as_read(email_data_seq["graph_msg_id"])
            processed_ids_in_phase1.add(email_data_seq["graph_msg_id"])

    if unread_messages_raw:
        final_processed_count = len(processed_ids_in_phase1)
        logging.info(f"Avslutade e-postbearbetning. {final_processed_count} av {len(unread_messages_raw)} e-postmeddelanden hanterades denna cykel.")