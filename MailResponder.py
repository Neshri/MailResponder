import requests
import msal
import time
import os
import logging
import sqlite3
import datetime
import random
import json
import base64
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- Import Prompts from prompts.py ---
from prompts import ULLA_PERSONA_PROMPT, PROBLEM_CATALOGUES, START_PHRASES, NUM_LEVELS
ollama = None # Will be imported if RUN_EMAIL_BOT is True

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

# --- Load .env variables ---
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
if os.path.exists(dotenv_path):
    logging.info(f"DEBUG: Loading .env from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path, override=True)
else:
    logging.warning(f"DEBUG: .env file NOT found at {dotenv_path}.")
    load_dotenv(override=True)

# --- Configuration ---
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TARGET_USER_GRAPH_ID = os.getenv('BOT_EMAIL_ADDRESS')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')
OLLAMA_HOST = os.getenv('OLLAMA_HOST')

logging.info("Miljövariabler inlästa.")
if not all([AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET, TARGET_USER_GRAPH_ID]):
    logging.critical("Saknar kritisk Graph API-konfiguration i .env."); exit("FEL: Config ofullständig.")
ollama_client_args = {}
if OLLAMA_HOST: ollama_client_args['host'] = OLLAMA_HOST; logging.info(f"Ollama-klient: {OLLAMA_HOST}")

DB_FILE = 'conversations.db' # New DB name for clarity
RUN_EMAIL_BOT = True
# START_COMMAND_SUBJECT is now a list in prompts.py (START_PHRASES)

GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
GRAPH_SCOPES = ['https://graph.microsoft.com/.default']
MSAL_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
MSAL_APP = None
ACCESS_TOKEN = None

# --- Database Functions (NEW SCHEMA) ---
def init_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_progress (
                student_email TEXT PRIMARY KEY,
                next_level_index INTEGER NOT NULL DEFAULT 0,
                last_completed_problem_id TEXT,
                last_active_graph_convo_id TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_problems (
                student_email TEXT PRIMARY KEY,
                problem_id TEXT NOT NULL,
                problem_description TEXT NOT NULL,
                correct_solution_keywords TEXT NOT NULL,
                conversation_history TEXT NOT NULL,
                problem_level_index INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_email) REFERENCES student_progress(student_email)
            )
        ''')
        conn.commit()
        logging.info(f"Databas {DB_FILE} initierad/kontrollerad med nivåstruktur.")
    except sqlite3.Error as e:
        logging.critical(f"Databasinitiering misslyckades: {e}", exc_info=True); raise
    finally:
        if conn: conn.close()

def get_student_progress(student_email):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT next_level_index, last_active_graph_convo_id FROM student_progress WHERE student_email = ?", (student_email,))
        row = cursor.fetchone()
        if row: return row['next_level_index'], row['last_active_graph_convo_id']
        return 0, None # Default if no record
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid hämtning av studentprogress för {student_email}: {e}"); return 0, None
    finally:
        if conn: conn.close()

def update_student_level(student_email, new_next_level_index, last_completed_id=None):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO student_progress (student_email, next_level_index) VALUES (?, ?)", (student_email, 0))
        if last_completed_id:
             cursor.execute("UPDATE student_progress SET next_level_index = ?, last_completed_problem_id = ?, last_active_graph_convo_id = NULL WHERE student_email = ?", 
                           (new_next_level_index, last_completed_id, student_email))
        else: # Should not happen if we always complete a problem before updating level
            cursor.execute("UPDATE student_progress SET next_level_index = ? WHERE student_email = ?", (new_next_level_index, student_email))
        conn.commit()
        logging.info(f"Student {student_email} uppdaterad till nästa nivå index: {new_next_level_index}")
        return True
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid uppdatering av studentnivå för {student_email}: {e}"); return False
    finally:
        if conn: conn.close()

def set_active_problem(student_email, problem, problem_level_idx, graph_conversation_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now()
        initial_history_string = f"Ulla: {problem['start_prompt']}\n\n"
        keywords_json = json.dumps(problem['losning_nyckelord'])
        
        # Ensure student_progress row exists and update last_active_graph_convo_id
        current_level, _ = get_student_progress(student_email) # Get current level to preserve it if inserting
        cursor.execute("INSERT OR IGNORE INTO student_progress (student_email, next_level_index, last_active_graph_convo_id) VALUES (?, ?, ?)",
                       (student_email, current_level, graph_conversation_id))
        cursor.execute("UPDATE student_progress SET last_active_graph_convo_id = ? WHERE student_email = ?",
                       (graph_conversation_id, student_email))
        
        cursor.execute('''
            REPLACE INTO active_problems 
            (student_email, problem_id, problem_description, correct_solution_keywords, conversation_history, problem_level_index, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_email, problem['id'], problem['beskrivning'], keywords_json, initial_history_string, problem_level_idx, timestamp))
        conn.commit()
        logging.info(f"Aktivt problem {problem['id']} (Nivå {problem_level_idx + 1}) satt för {student_email}")
        return True
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid sättande av aktivt problem för {student_email}: {e}", exc_info=True); return False
    finally:
        if conn: conn.close()

def get_current_active_problem(student_email):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # We need last_active_graph_convo_id from student_progress, not active_problems for this query's purpose
        cursor.execute('''
            SELECT ap.problem_id, ap.problem_description, ap.correct_solution_keywords, 
                   ap.conversation_history, ap.problem_level_index, sp.last_active_graph_convo_id
            FROM active_problems ap
            LEFT JOIN student_progress sp ON ap.student_email = sp.student_email
            WHERE ap.student_email = ?
        ''', (student_email,)) # Use LEFT JOIN in case student_progress somehow missing, though unlikely
        row = cursor.fetchone()
        if row:
            history_string = row['conversation_history']
            problem_info = {'id': row['problem_id'], 'beskrivning': row['problem_description'], 'losning_nyckelord': json.loads(row['correct_solution_keywords'])}
            level_idx = row['problem_level_index']
            active_graph_convo_id = row['last_active_graph_convo_id'] # This is the key convo ID for the current problem
            return history_string, problem_info, level_idx, active_graph_convo_id
        return None, None, None, None
    except (sqlite3.Error, json.JSONDecodeError) as e:
        logging.error(f"Fel vid hämtning av aktivt problem för {student_email}: {e}", exc_info=True); return None, None, None, None
    finally:
        if conn: conn.close()

def append_to_active_problem_history(student_email, text_to_append):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        if not text_to_append.endswith("\n\n"): text_to_append += "\n\n"
        cursor.execute("UPDATE active_problems SET conversation_history = conversation_history || ? WHERE student_email = ?", (text_to_append, student_email))
        conn.commit()
        logging.info(f"Lade till i historik för aktivt problem för {student_email}")
        return True
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid tillägg i historik för {student_email}: {e}"); return False
    finally:
        if conn: conn.close()

def clear_active_problem(student_email):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Delete from active_problems
        cursor.execute("DELETE FROM active_problems WHERE student_email = ?", (student_email,))
        deleted_rows = cursor.rowcount
        # Clear last_active_graph_convo_id in student_progress
        cursor.execute("UPDATE student_progress SET last_active_graph_convo_id = NULL WHERE student_email = ?", (student_email,))
        conn.commit()
        if deleted_rows > 0: logging.info(f"Rensade aktivt problem för {student_email}"); return True
        logging.info(f"Inget aktivt problem att rensa för {student_email}, men rensade convo ID i progress.")
        return True # Still true if convo ID was cleared
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid rensning av aktivt problem för {student_email}: {e}"); return False
    finally:
        if conn: conn.close()


# --- LLM Interaction (Unchanged from previous full script) ---
def get_llm_response_with_history(student_email, full_history_string, problem_info, latest_student_message_cleaned):
    # ... (Your existing LLM function with detailed logging) ...
    global ollama 
    if not OLLAMA_MODEL: logging.error("OLLAMA_MODEL ej satt."); return "Tappade tråden...", False
    logging.info(f"Hämtar LLM-svar för {student_email} (modell: {OLLAMA_MODEL})")
    persona_hist = f"{ULLA_PERSONA_PROMPT}\nDu har haft följande konversation:\n--- HISTORIK ---\n{full_history_string}\n--- SLUT HISTORIK ---"
    sys_prompt = f"{persona_hist}\nDitt problem: {problem_info['beskrivning']}\nLösningsnyckelord: {problem_info['losning_nyckelord']}\nUtvärdera SENASTE \"Support:\"-meddelande."
    eval_prompt = f"**Utvärdering:** Matchar SENASTE \"Support:\"-meddelande nyckelorden '{problem_info['losning_nyckelord']}'? (Behöver ej vara exakt, men andemeningen.)\n**Svarsinstruktion:**\n1. Första raden: `[LÖST]` eller `[EJ_LÖST]`.\n2. Ny rad: Svara som Ulla."
    messages = [{'role': 'system', 'content': sys_prompt}, {'role': 'user', 'content': eval_prompt}]
    logging.info(f"--- MEDDELANDE TILL OLLAMA ({student_email}) ---\n{json.dumps(messages, indent=2, ensure_ascii=False)}\n--- SLUT MEDDELANDE ---")
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages, options={'temperature': 0.7, 'num_predict': 1000}, **ollama_client_args)
        raw_reply = response['message']['content']
        logging.info(f"--- RÅTT SVAR FRÅN OLLAMA ({student_email}) ---\n{raw_reply}\n--- SLUT RÅTT SVAR ---")
        processed_reply = raw_reply.strip(); lines = processed_reply.split('\n', 1); marker = lines[0].strip()
        is_solved = (marker == "[LÖST]")
        ulla_reply = lines[1].strip() if len(lines) > 1 else ("Tack!" if is_solved else "Jaha?")
        ulla_reply = ulla_reply.replace("[LÖST]", "").replace("[EJ_LÖST]", "").strip()
        if not ulla_reply: ulla_reply = "Tack!" if is_solved else "Jaha?"
        logging.info(f"LLM: Marker: '{marker}'. Löst: {is_solved}. Svar: '{ulla_reply[:50]}...'")
        return ulla_reply, is_solved
    except Exception as e:
        logging.error(f"Ollama LLM-fel för {student_email}: {e}", exc_info=True); return "Tankeverksamheten krånglar...", False


# --- Graph API Helper Functions (msal + requests - Unchanged) ---
def get_graph_token(): # ... (same as before) ...
    global MSAL_APP, ACCESS_TOKEN
    if MSAL_APP is None: MSAL_APP = msal.ConfidentialClientApplication(AZURE_CLIENT_ID, authority=MSAL_AUTHORITY, client_credential=AZURE_CLIENT_SECRET)
    token_result = MSAL_APP.acquire_token_silent(GRAPH_SCOPES, account=None)
    if not token_result: logging.info("Hämtar nytt Graph API-token."); token_result = MSAL_APP.acquire_token_for_client(scopes=GRAPH_SCOPES)
    if "access_token" in token_result: ACCESS_TOKEN = token_result['access_token']; return ACCESS_TOKEN
    logging.error(f"Misslyckades hämta Graph token: {token_result.get('error_description')}"); ACCESS_TOKEN = None; return None

def jwt_is_expired(token_str): # ... (same as before) ...
    if not token_str: return True
    try: payload_str = token_str.split('.')[1]; payload_str += '=' * (-len(payload_str) % 4); payload = json.loads(base64.urlsafe_b64decode(payload_str).decode()); return payload.get('exp', 0) < time.time()
    except Exception: return True

def make_graph_api_call(method, endpoint_suffix, data=None, params=None, headers_extra=None): # ... (same as before) ...
    global ACCESS_TOKEN
    if ACCESS_TOKEN is None or jwt_is_expired(ACCESS_TOKEN):
        if not get_graph_token(): logging.error("Misslyckades förnya token."); return None
    if ACCESS_TOKEN is None: logging.error("ACCESS_TOKEN fortfarande None."); return None
    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN, 'Content-Type': 'application/json'}; url = f"{GRAPH_API_ENDPOINT}{endpoint_suffix}"
    if headers_extra: headers.update(headers_extra)
    try:
        response = requests.request(method, url, headers=headers, json=data, params=params, timeout=30); response.raise_for_status()
        if response.status_code in [202, 204]: return True
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401: logging.warning("Graph API 401. Ogiltigförklarar token."); ACCESS_TOKEN = None
        err_details = "Okänt." ; 
        try: 
            err_details = e.response.json().get("error", {}).get("message", e.response.text)
        except json.JSONDecodeError: 
            err_details = e.response.text
        logging.error(f"Graph HTTP-fel: {e.response.status_code} - {err_details} ({method} {url})"); return None
    except requests.exceptions.RequestException as e: logging.error(f"Graph anropsfel: {e} ({method} {url})", exc_info=True); return None

# --- Graph API Email Functions ---
def graph_send_email(recipient_email, subject, body_content, in_reply_to_message_id=None, references_header_str=None, conversation_id=None): # ... (same, uses X- prefixed headers) ...
    message_payload = {"message": {"subject": subject, "body": {"contentType": "Text", "content": body_content}, "toRecipients": [{"emailAddress": {"address": recipient_email}}]}, "saveToSentItems": "true"}
    headers_list = []
    if in_reply_to_message_id: headers_list.append({"name": "X-In-Reply-To", "value": in_reply_to_message_id})
    if references_header_str: headers_list.append({"name": "X-References", "value": references_header_str})
    if conversation_id: message_payload["message"]["conversationId"] = conversation_id
    if headers_list: message_payload["message"]["internetMessageHeaders"] = headers_list
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/sendMail"
    logging.info(f"Skickar e-post till: {recipient_email} | Ämne: {subject}")
    response = make_graph_api_call("POST", endpoint, data=message_payload)
    if response is True: logging.info("E-post skickat."); return True
    logging.error(f"Misslyckades skicka e-post. Svar: {response}"); return False

def clean_email_body(body_text, original_sender_email_for_attribution=None): # ... (same as before) ...
    if not body_text: return ""
    lines = body_text.splitlines(); cleaned_lines = []
    q_sw = ["från:", "--ursprungl meddelande--", "den ", "på "]; q_en = ["from:", "--original message--", "on ", "wrote:"]
    if original_sender_email_for_attribution: q_sw.append(f"skrev {original_sender_email_for_attribution.lower()}")
    all_q = [q.lower() for q in q_sw + q_en]; found_q = False
    for line in lines:
        s_line_lower = line.strip().lower()
        if ((" skrev " in s_line_lower or " wrote " in s_line_lower) and original_sender_email_for_attribution and original_sender_email_for_attribution.lower() in s_line_lower): found_q = True; break
        for indicator in all_q:
            if s_line_lower.startswith(indicator): found_q = True; break
        if found_q: break
        if not line.strip().startswith('>'): cleaned_lines.append(line)
    final_text = "\n".join(cleaned_lines).strip()
    if not final_text and body_text.strip(): return "" 
    return final_text

def mark_email_as_read(graph_message_id): # ... (same as before) ...
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/messages/{graph_message_id}"; payload = {"isRead": True}
    # logging.debug(f"Markerar {graph_message_id} som läst...") # Can be too verbose
    if make_graph_api_call("PATCH", endpoint, data=payload): logging.info(f"E-post {graph_message_id} markerad som läst.")
    else: logging.error(f"Misslyckades markera {graph_message_id} som läst.")


# --- Core Email Processing (graph_check_emails - HEAVILY MODIFIED) ---
def graph_check_emails():
    global ACCESS_TOKEN
    select_fields = "id,subject,from,sender,receivedDateTime,bodyPreview,body,internetMessageId,conversationId,isRead,internetMessageHeaders"
    params = {"$filter": "isRead eq false", "$select": select_fields, "$orderby": "receivedDateTime asc"}
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/mailFolders/inbox/messages"
    logging.info("Söker olästa e-post (Graph)...")
    response_data = make_graph_api_call("GET", endpoint, params=params)

    if not response_data or "value" not in response_data:
        logging.info("Inga olästa e-post eller fel vid hämtning." if response_data is None else "Inga olästa e-post (Graph).")
        return

    unread_messages = response_data["value"]
    if not unread_messages: logging.info("Inga olästa e-post (Graph)."); return
    logging.info(f"Hittade {len(unread_messages)} olästa e-post (Graph).")
    
    processed_ids = set()
    for msg_graph in unread_messages:
        graph_msg_id = msg_graph.get('id')
        logging.info(f"--- Bearbetar e-post ID: {graph_msg_id} ---")
        try:
            subject_from_email = msg_graph.get('subject', "")
            sender_info = msg_graph.get('from') or msg_graph.get('sender')
            sender_email = sender_info.get('emailAddress', {}).get('address', '').lower() if sender_info else ''
            internet_message_id = msg_graph.get('internetMessageId') # For threading replies
            graph_conversation_id_incoming = msg_graph.get('conversationId') # For threading and DB
            references_header_value = next((h.get('value') for h in msg_graph.get('internetMessageHeaders', []) if h.get('name', '').lower() == 'references'), None)
            
            logging.info(f"Från: {sender_email} | Ämne: '{subject_from_email}'")

            if not sender_email or sender_email == TARGET_USER_GRAPH_ID.lower() or 'mailer-daemon' in sender_email or 'noreply' in sender_email:
                logging.warning("Skippar (själv/system). Markerar läst."); mark_email_as_read(graph_msg_id); processed_ids.add(graph_msg_id); continue

            body_obj = msg_graph.get('body', {}); body_content = body_obj.get('content', '')
            raw_body_for_cleaning = BeautifulSoup(body_content, "html.parser").get_text(separator='\n').strip() if body_obj.get('contentType','').lower()=='html' else body_content
            cleaned_body = clean_email_body(raw_body_for_cleaning, TARGET_USER_GRAPH_ID)
            logging.debug(f"Rensad text: '{cleaned_body[:100]}...'")

            # --- REVISED LOGIC FOR START COMMANDS AND ACTIVE CONVERSATIONS ---
            student_next_eligible_level_idx, _ = get_student_progress(sender_email) # What level are they eligible to START?
            active_hist_str, active_problem_info, active_problem_level_idx, active_problem_convo_id_db = get_current_active_problem(sender_email)

            is_start_command_for_eligible_level = False
            attempted_start_level_idx = -1 # Level index the student is trying to start

            # Check if the incoming email is trying to start ANY known level
            for idx, phrase in enumerate(START_PHRASES):
                if (subject_from_email and phrase.lower() in subject_from_email.lower()) or \
                   (cleaned_body.lower().strip().startswith(phrase.lower())):
                    attempted_start_level_idx = idx
                    logging.info(f"Mail från {sender_email} innehåller startfras '{phrase}' för nivå {idx + 1}.")
                    break
            
            # Scenario 1: Student is trying to start a level
            if attempted_start_level_idx != -1:
                # Is it the level they are actually eligible for?
                if attempted_start_level_idx == student_next_eligible_level_idx:
                    is_start_command_for_eligible_level = True
                    logging.info(f"Detta är en giltig start för nivå {student_next_eligible_level_idx + 1}.")
                else:
                    # They used a start phrase, but not for their current eligible level.
                    # Could be for a past level (restart attempt) or future level (too early).
                    # For now, if they have an active problem, we ignore this out-of-sync start command
                    # and process the email as a reply to the active problem IF one exists.
                    # If no active problem, we could inform them they used the wrong phrase.
                    if not active_problem_info: # No active problem, but wrong start phrase
                        logging.warning(f"Student {sender_email} använde startfras för nivå {attempted_start_level_idx + 1}, men förväntad nästa nivå är {student_next_eligible_level_idx + 1}. Informerar studenten.")
                        wrong_level_msg = f"Hej! Jag ser att du försöker starta en övning, men startfrasen du använde verkar vara för en annan nivå. "
                        if student_next_eligible_level_idx < NUM_LEVELS:
                            wrong_level_msg += f"Om du vill starta nästa övning (Nivå {student_next_eligible_level_idx + 1}), använd frasen: \"{START_PHRASES[student_next_eligible_level_idx]}\"."
                        else:
                            wrong_level_msg += "Du verkar ha klarat alla tillgängliga nivåer redan!"
                        
                        reply_subject_wrong_level = subject_from_email # Keep their subject or "Re:" it
                        if not reply_subject_wrong_level.lower().startswith("re:"): reply_subject_wrong_level = f"Re: {subject_from_email}"

                        graph_send_email(sender_email, reply_subject_wrong_level, wrong_level_msg,
                                         in_reply_to_message_id=internet_message_id,
                                         references_header_str=f"{references_header_value if references_header_value else ''} {internet_message_id}".strip(),
                                         conversation_id=graph_conversation_id_incoming)
                        mark_email_as_read(graph_msg_id); processed_ids.add(graph_msg_id); continue # Move to next email

            # Decision Point:
            if is_start_command_for_eligible_level:
                # This will REPLACE any current active_problem for the student, which is the desired override.
                if student_next_eligible_level_idx >= NUM_LEVELS:
                    logging.info(f"Student {sender_email} försöker starta nivå men har redan klarat alla {NUM_LEVELS} nivåer.")
                    # Optionally send a "Congrats, you're done!" email
                    mark_email_as_read(graph_msg_id); processed_ids.add(graph_msg_id); continue

                problem_list = PROBLEM_CATALOGUES[student_next_eligible_level_idx]
                if not problem_list: logging.error(f"Inga problem för nivå {student_next_eligible_level_idx+1}!"); mark_email_as_read(graph_msg_id); processed_ids.add(graph_msg_id); continue
                
                problem = random.choice(problem_list)
                if set_active_problem(sender_email, problem, student_next_eligible_level_idx, graph_conversation_id_incoming):
                    # Ulla's reply subject should be based on the student's triggering email's subject
                    reply_subject = subject_from_email # Or f"Övning Nivå {student_next_eligible_level_idx + 1}"
                    
                    if graph_send_email(sender_email, reply_subject, problem['start_prompt'], conversation_id=graph_conversation_id_incoming):
                        logging.info(f"Skickade problem (Nivå {student_next_eligible_level_idx+1}) till {sender_email}")
                        mark_email_as_read(graph_msg_id); processed_ids.add(graph_msg_id)
                    else: 
                        logging.error("Misslyckades skicka initialt problem efter startkommando."); 
                        clear_active_problem(sender_email) # Rollback if Ulla's first mail fails
                else: logging.error("Misslyckades sätta aktivt problem i DB efter startkommando.")
            
            elif active_hist_str and active_problem_info: # An active problem exists, AND the current email was NOT a valid start command for their next level
                logging.info(f"E-post tillhör aktivt problem {active_problem_info['id']} för {sender_email}")
                body_for_llm = cleaned_body if cleaned_body.strip() else (msg_graph.get('bodyPreview') or "").strip()
                if not body_for_llm:
                    logging.warning("Tom text/förhandsvisning för aktivt problem. Ignorerar. Markerar läst."); mark_email_as_read(graph_msg_id); processed_ids.add(graph_msg_id); continue
                
                student_entry = f"Support: {body_for_llm}\n\n"
                append_to_active_problem_history(sender_email, student_entry)
                full_hist_for_llm = active_hist_str + student_entry

                ulla_reply_body, is_solved = get_llm_response_with_history(sender_email, full_hist_for_llm, active_problem_info, body_for_llm)

                if ulla_reply_body:
                    final_ulla_reply = ulla_reply_body
                    if is_solved:
                        # Use active_problem_level_idx here as it's the level they just COMPLETED
                        next_lvl_idx_after_solve = active_problem_level_idx + 1
                        completion_msg = f"\n\nJättebra! Problem {active_problem_info['id']} (Nivå {active_problem_level_idx + 1}) är löst!"
                        if next_lvl_idx_after_solve < NUM_LEVELS:
                            completion_msg += f"\nStartfras för nästa nivå ({next_lvl_idx_after_solve + 1}): \"{START_PHRASES[next_lvl_idx_after_solve]}\""
                        else: completion_msg += "\nDu har klarat alla nivåer! Grattis!"
                        final_ulla_reply += completion_msg
                    
                    ulla_entry_for_db = f"Ulla: {final_ulla_reply}\n\n"
                    
                    reply_subj_ongoing = subject_from_email
                    if not reply_subj_ongoing.lower().startswith("re:"): reply_subj_ongoing = f"Re: {subject_from_email}"
                    
                    convo_id_for_reply = graph_conversation_id_incoming or active_problem_convo_id_db
                    refs_for_reply = f"{references_header_value if references_header_value else ''} {internet_message_id}".strip()

                    if graph_send_email(sender_email, reply_subj_ongoing, final_ulla_reply, internet_message_id, refs_for_reply, convo_id_for_reply):
                        append_to_active_problem_history(sender_email, ulla_entry_for_db)
                        if is_solved:
                            clear_active_problem(sender_email)
                            update_student_level(sender_email, active_problem_level_idx + 1, active_problem_info['id'])
                        mark_email_as_read(graph_msg_id); processed_ids.add(graph_msg_id)
                        logging.info(f"Bearbetat och svarat på e-post {graph_msg_id}.")
                    else: logging.error("Misslyckades skicka svar. E-post INTE markerad som läst.")
                else: logging.error("Misslyckades få LLM-svar. E-post INTE markerad som läst.")
            
            else: # No active problem AND not a valid start command for their eligible level
                logging.warning(f"E-post från {sender_email} - inget aktivt problem/giltigt startkommando. Ignorerar. Markerar läst.")
                mark_email_as_read(graph_msg_id); processed_ids.add(graph_msg_id)
        
        except Exception as proc_err:
             logging.error(f"Ohanterat fel vid bearbetning av e-post ID {graph_msg_id}: {proc_err}", exc_info=True)
    
    if unread_messages:
        logging.info(f"Avslutade e-postbearbetning. {len(processed_ids)} av {len(unread_messages)} markerades bearbetade.")

# --- Main Execution Block ---
if __name__ == "__main__":
    logging.info(f"Script startat (DB: {DB_FILE}). RUN_EMAIL_BOT={RUN_EMAIL_BOT}")
    try: init_db()
    except Exception as db_err: logging.critical(f"DB-initiering misslyckades: {db_err}. Avslutar."); exit(1)

    # --- Add DB Print Option via Command Line Argument ---
    import sys
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--printdb":
        def print_db_content(): # Keep this local to main or make it a proper function
            conn_pdb = None
            print("\n--- UTSKRIFT STUDENT PROGRESS ---")
            try:
                conn_pdb = sqlite3.connect(DB_FILE); conn_pdb.row_factory = sqlite3.Row; c_pdb = conn_pdb.cursor()
                c_pdb.execute("SELECT * FROM student_progress"); rows_pdb = c_pdb.fetchall()
                if not rows_pdb: print("Tabellen student_progress är tom.")
                else: 
                    for r_pdb in rows_pdb: print(dict(r_pdb)) # Print as dict for readability
            except Exception as e_pdb: print(f"Fel vid utskrift av student_progress: {e_pdb}")
            finally: 
                if conn_pdb: conn_pdb.close()

            conn_apdb = None
            print("\n--- UTSKRIFT ACTIVE PROBLEMS ---")
            try:
                conn_apdb = sqlite3.connect(DB_FILE); conn_apdb.row_factory = sqlite3.Row; c_apdb = conn_apdb.cursor()
                c_apdb.execute("SELECT * FROM active_problems"); rows_apdb = c_apdb.fetchall()
                if not rows_apdb: print("Tabellen active_problems är tom.")
                else: 
                    for r_apdb in rows_apdb: 
                        d = dict(r_apdb)
                        # Pretty print history for readability
                        print(f"Student: {d.get('student_email')}, Problem ID: {d.get('problem_id')}, Level Idx: {d.get('problem_level_index')}")
                        print(f"  History:\n{d.get('conversation_history', '')}")
            except Exception as e_apdb: print(f"Fel vid utskrift av active_problems: {e_apdb}")
            finally: 
                if conn_apdb: conn_apdb.close()
            print("--- SLUT DB UTSKRIFT ---")
        print_db_content()
        exit()
    # --- End DB Print Option ---

    if RUN_EMAIL_BOT:
        logging.info("--- Kör i E-post Bot-läge (Graph API) ---")
        if not OLLAMA_MODEL: logging.critical("Saknar OLLAMA_MODEL."); exit(1)
        try:
            import ollama as ollama_module; globals()['ollama'] = ollama_module
            logging.info(f"Kontrollerar Ollama & modell '{OLLAMA_MODEL}'...")
            ollama.show(OLLAMA_MODEL, **ollama_client_args)
            logging.info(f"Ansluten till Ollama & modell '{OLLAMA_MODEL}' hittad.")
        except ImportError: logging.critical("Ollama-bibliotek saknas."); exit("FEL: Ollama saknas.")
        except Exception as ollama_err: logging.critical(f"Ollama Fel: {ollama_err}"); exit("FEL: Ollama-anslutning/-modell.")

        if not get_graph_token(): logging.critical("Misslyckades hämta Graph API-token."); exit(1)
        logging.info("Startar huvudloop för e-postkontroll...")
        while True:
            try: graph_check_emails()
            except Exception as loop_err:
                logging.error(f"Kritiskt fel i huvudloop: {loop_err}", exc_info=True)
                if "401" in str(loop_err) or "token" in str(loop_err).lower():
                    logging.warning("Försöker förnya Graph-token."); get_graph_token() 
            sleep_interval = 30
            logging.info(f"Sover i {sleep_interval} sekunder..."); time.sleep(sleep_interval)
    else: # RUN_EMAIL_BOT is False (Read-only mode)
        logging.info(f"--- Kör i Enkelt E-postläsningsläge (Graph API) ---")
        if not get_graph_token(): logging.critical("Misslyckades hämta Graph API-token."); exit(1)
        try:
            select_fields_ro = "id,subject,from,sender,receivedDateTime,bodyPreview,body,internetMessageId,conversationId,isRead,internetMessageHeaders"
            params_ro = {"$filter": "isRead eq false", "$select": select_fields_ro, "$orderby": "receivedDateTime asc"}
            endpoint_ro = f"/users/{TARGET_USER_GRAPH_ID}/mailFolders/inbox/messages"
            print("\n--- Kontrollerar olästa e-postmeddelanden (läs-läge) ---")
            response_data = make_graph_api_call("GET", endpoint_ro, params=params_ro)
            if not response_data or "value" not in response_data:
                if response_data is None: print("Fel vid hämtning av e-post.")
                else: print("Inga olästa e-postmeddelanden.")
            else:
                unread = response_data["value"]
                if not unread: print("Inga olästa e-postmeddelanden.")
                else:
                    print(f"Hittade {len(unread)} olästa e-postmeddelanden:")
                    for i, msg in enumerate(unread):
                        print(f"\n--- E-post {i+1}/{len(unread)} ---")
                        sender_info = msg.get('from') or msg.get('sender')
                        sender_email = sender_info.get('emailAddress',{}).get('address','') if sender_info else 'Okänd'
                        print(f"  Från: {sender_email}\n  Ämne: {msg.get('subject','[Inget ämne]')}")
                        body_obj_ro = msg.get('body',{}); body_content_ro = body_obj_ro.get('content','')
                        raw_body_ro = BeautifulSoup(body_content_ro,"html.parser").get_text(separator='\n').strip() if body_obj_ro.get('contentType','').lower()=='html' else body_content_ro
                        cleaned_ro = clean_email_body(raw_body_ro, TARGET_USER_GRAPH_ID)
                        print(f"  Rensad Text:\n{'-'*20}\n{cleaned_ro if cleaned_ro else msg.get('bodyPreview','[Tom]')}\n{'-'*20}")
                        mark_email_as_read(msg.get('id'))
                    print("\nAlla olästa markerade som lästa.")
        except Exception as ro_err: logging.error(f"Fel i läs-läge: {ro_err}", exc_info=True)
        logging.info("--- Avslutade Enkelt E-postläsningsläge ---")
    logging.info("Script avslutat.")