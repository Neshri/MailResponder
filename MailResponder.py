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
import re
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
OLLAMA_EVAL_MODEL = os.getenv('OLLAMA_EVAL_MODEL', OLLAMA_MODEL) 
OLLAMA_HOST = os.getenv('OLLAMA_HOST')

logging.info("Miljövariabler inlästa.")
if not all([AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET, TARGET_USER_GRAPH_ID]):
    logging.critical("Saknar kritisk Graph API-konfiguration i .env."); exit("FEL: Config ofullständig.")
ollama_client_args = {}
if OLLAMA_HOST: ollama_client_args['host'] = OLLAMA_HOST; logging.info(f"Ollama-klient: {OLLAMA_HOST}")

DB_FILE = 'conversations.db' # Consistent DB name
RUN_EMAIL_BOT = True

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
        conn = sqlite3.connect(DB_FILE); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
        cursor.execute("SELECT next_level_index, last_active_graph_convo_id FROM student_progress WHERE student_email = ?", (student_email,))
        row = cursor.fetchone()
        if row: return row['next_level_index'], row['last_active_graph_convo_id']
        return 0, None 
    except sqlite3.Error as e: logging.error(f"DB-fel studentprogress {student_email}: {e}"); return 0, None
    finally:
        if conn: conn.close()

def update_student_level(student_email, new_next_level_index, last_completed_id=None):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO student_progress (student_email, next_level_index) VALUES (?, ?)", (student_email, 0))
        if last_completed_id:
             cursor.execute("UPDATE student_progress SET next_level_index = ?, last_completed_problem_id = ?, last_active_graph_convo_id = NULL WHERE student_email = ?", 
                           (new_next_level_index, last_completed_id, student_email))
        else:
            cursor.execute("UPDATE student_progress SET next_level_index = ? WHERE student_email = ?", (new_next_level_index, student_email))
        conn.commit(); logging.info(f"Student {student_email} nivåindex: {new_next_level_index}"); return True
    except sqlite3.Error as e: logging.error(f"DB-fel uppd. studentnivå {student_email}: {e}"); return False
    finally:
        if conn: conn.close()

def set_active_problem(student_email, problem, problem_level_idx, graph_conversation_id):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
        timestamp = datetime.datetime.now(); initial_history_string = f"Ulla: {problem['start_prompt']}\n\n"
        keywords_json = json.dumps(problem['losning_nyckelord'])
        current_level, _ = get_student_progress(student_email)
        cursor.execute("INSERT OR IGNORE INTO student_progress (student_email, next_level_index, last_active_graph_convo_id) VALUES (?, ?, ?)",
                       (student_email, current_level, graph_conversation_id))
        cursor.execute("UPDATE student_progress SET last_active_graph_convo_id = ? WHERE student_email = ?", (graph_conversation_id, student_email))
        cursor.execute('''REPLACE INTO active_problems (student_email, problem_id, problem_description, correct_solution_keywords, conversation_history, problem_level_index, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)''', (student_email, problem['id'], problem['beskrivning'], keywords_json, initial_history_string, problem_level_idx, timestamp))
        conn.commit(); logging.info(f"Aktivt problem {problem['id']} (Nivå {problem_level_idx + 1}) satt för {student_email}"); return True
    except sqlite3.Error as e: logging.error(f"DB-fel sätt aktivt problem {student_email}: {e}", exc_info=True); return False
    finally:
        if conn: conn.close()

def get_current_active_problem(student_email):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE); conn.row_factory = sqlite3.Row; cursor = conn.cursor()
        cursor.execute(''' SELECT ap.problem_id, ap.problem_description, ap.correct_solution_keywords, ap.conversation_history, ap.problem_level_index, sp.last_active_graph_convo_id
            FROM active_problems ap LEFT JOIN student_progress sp ON ap.student_email = sp.student_email WHERE ap.student_email = ? ''', (student_email,))
        row = cursor.fetchone()
        if row:
            history_string = row['conversation_history']
            problem_info = {'id': row['problem_id'], 'beskrivning': row['problem_description'], 'losning_nyckelord': json.loads(row['correct_solution_keywords'])}
            level_idx = row['problem_level_index']
            active_graph_convo_id = row['last_active_graph_convo_id']
            return history_string, problem_info, level_idx, active_graph_convo_id
        return None, None, None, None
    except (sqlite3.Error, json.JSONDecodeError) as e: logging.error(f"Fel hämtning aktivt problem {student_email}: {e}", exc_info=True); return None, None, None, None
    finally:
        if conn: conn.close()

def append_to_active_problem_history(student_email, text_to_append):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
        if not text_to_append.endswith("\n\n"): text_to_append += "\n\n"
        cursor.execute("UPDATE active_problems SET conversation_history = conversation_history || ? WHERE student_email = ?", (text_to_append, student_email))
        conn.commit(); logging.info(f"Lade till i historik för {student_email}"); return True
    except sqlite3.Error as e: logging.error(f"DB-fel tillägg historik {student_email}: {e}"); return False
    finally:
        if conn: conn.close()

def clear_active_problem(student_email):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE); cursor = conn.cursor()
        cursor.execute("DELETE FROM active_problems WHERE student_email = ?", (student_email,)); deleted_rows = cursor.rowcount
        cursor.execute("UPDATE student_progress SET last_active_graph_convo_id = NULL WHERE student_email = ?", (student_email,))
        conn.commit()
        if deleted_rows > 0: logging.info(f"Rensade aktivt problem för {student_email}"); return True
        logging.info(f"Inget aktivt problem att rensa för {student_email}, men convo ID rensat."); return True
    except sqlite3.Error as e: logging.error(f"DB-fel rensning aktivt problem {student_email}: {e}"); return False
    finally:
        if conn: conn.close()

# --- LLM Interaction ---
def get_evaluation_marker(student_email, full_history_string_for_eval, problem_info, latest_student_message_cleaned): # full_history_string_for_eval is no longer used by this prompt
    global ollama
    if not ollama: logging.error("Ollama-modul ej laddad."); return "[EJ_LÖST]"
    if not OLLAMA_EVAL_MODEL: logging.error("OLLAMA_EVAL_MODEL ej satt."); return "[EJ_LÖST]"
    logging.info(f"Hämtar eval-markör för {student_email} (eval-modell: {OLLAMA_EVAL_MODEL})")

    # latest_student_message_cleaned is what we want to use directly
    last_student_msg_for_eval = latest_student_message_cleaned
    if not last_student_msg_for_eval.strip(): # Check if it's empty or just whitespace
        logging.warning("latest_student_message_cleaned var tom eller endast whitespace för utvärdering. Tolkar som [EJ_LÖST].")
        # It's important that the LLM still gets *some* text indicating no input,
        # rather than a malformed prompt if last_student_msg_for_eval is truly empty.
        last_student_msg_for_eval = "[Studenten skrev inget nytt i detta meddelande]"


    system_prompt_eval = f"""Du är en AI-utvärderare. Din enda uppgift är att strikt bedöma om studentens SENASTE förslag löser ett specifikt problem.
Problemets korrekta lösningsidéer (givna som nyckelord/koncept): {problem_info['losning_nyckelord']}"""
    # Removed "Use code with caution. Python" - it was an artifact.

    user_prompt_eval = f"""Här är studentens SENASTE meddelande som du ska utvärdera:
\"\"\"
{last_student_msg_for_eval}
\"\"\"

Fråga: Matchar innehållet i studentens SENASTE meddelande (ovan) någon av idéerna i lösningsnyckelorden: {problem_info['losning_nyckelord']}?
Fokusera på om studenten har bett Ulla att UTFÖRA en konkret handling som är en av nyckelordslösningarna.
Att bara ställa en fråga, be om mer information, eller föreslå ett verktyg (som en ficklampa) utan att direkt föreslå en nyckelordshandling räknas INTE som [LÖST].

Svara ENDAST med `[LÖST]` eller `[EJ_LÖST]` på en enda rad. Inget annat.
"""
    
    messages = [ # Renamed from messages_for_eval_ollama for clarity within this function
        {'role': 'system', 'content': system_prompt_eval},
        {'role': 'user', 'content': user_prompt_eval}
    ]
    
    logging.info(f"--- MEDDELANDE TILL EVAL MODELL ({student_email}) ---\n{json.dumps(messages, indent=2, ensure_ascii=False)}\n--- SLUT ---")
    try:
        response = ollama.chat(model=OLLAMA_EVAL_MODEL, messages=messages, options={'temperature': 0.1, 'num_predict': 1000}, **ollama_client_args) # num_predict was 10, might be too short if think block still occurs
        raw_reply = response['message']['content'].strip()
        logging.info(f"--- RÅTT SVAR FRÅN EVAL MODELL ({student_email}) ---\n{raw_reply}\n--- SLUT ---")
        
        # Strip <think> block using regex (ensure re is imported globally in your script)
        # import re # (should be at the top of your file)
        cleaned_reply_for_marker = re.sub(r"<think>.*?</think>", "", raw_reply, flags=re.DOTALL | re.IGNORECASE).strip()
        
        if cleaned_reply_for_marker == "[LÖST]": # Exact match after stripping think block
            return "[LÖST]"
        if cleaned_reply_for_marker == "[EJ_LÖST]": # Exact match after stripping think block
            return "[EJ_LÖST]"
        
        # Fallback if the marker is present but with other text (e.g., after a newline from think block)
        if "[LÖST]" in cleaned_reply_for_marker: 
            logging.warning(f"Markören '[LÖST]' hittades med extra text i EVAL-svar: '{cleaned_reply_for_marker}'. Tolkar som [LÖST].")
            return "[LÖST]"
        if "[EJ_LÖST]" in cleaned_reply_for_marker:
            logging.warning(f"Markören '[EJ_LÖST]' hittades med extra text i EVAL-svar: '{cleaned_reply_for_marker}'. Tolkar som [EJ_LÖST].")
            return "[EJ_LÖST]"

        logging.warning(f"Oväntad output från EVAL (efter rensning av think block): '{cleaned_reply_for_marker}'. Tolkar som [EJ_LÖST]."); 
        return "[EJ_LÖST]"
    except Exception as e: 
        logging.error(f"Ollama EVAL LLM-fel: {e}", exc_info=True); 
        return "[EJ_LÖST]"

def get_ulla_persona_response(student_email, full_history_string_for_persona, problem_info, evaluation_marker, latest_student_message_cleaned, problem_level_idx):
    global ollama
    if not ollama: logging.error("Ollama-modul ej laddad."); return "Tappade tråden..."
    if not OLLAMA_MODEL: logging.error("OLLAMA_MODEL ej satt."); return "Tappade tråden..."
    is_solved = (evaluation_marker == "[LÖST]")
    logging.info(f"Hämtar Ullas svar för {student_email} (persona-modell: {OLLAMA_MODEL}), problem bedömt: {evaluation_marker}")
    unhinged = ""
    if problem_level_idx >= 2 and not is_solved: unhinged = random.choice([" Lite virrig.", " Lite otålig.", " Pratar om annat."])
    sys_prompt = f"{ULLA_PERSONA_PROMPT}{unhinged}\nKonversation:\n--- HISTORIK ---\n{full_history_string_for_persona}\n--- SLUT HISTORIK ---\nProblem: {problem_info['beskrivning']}"
    user_prompt = "Studentens förslag löste problemet! Svara glatt." if is_solved else "Studentens förslag löste INTE problemet. Svara förvirrat/beskriv igen. Avslöja ej lösning."
    messages = [{'role': 'system', 'content': sys_prompt}, {'role': 'user', 'content': user_prompt}]
    logging.info(f"--- MEDDELANDE TILL PERSONA MODELL ({student_email}) ---\n{json.dumps(messages, indent=2, ensure_ascii=False)}\n--- SLUT ---")
    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages, options={'temperature': 0.8, 'num_predict': 1000}, **ollama_client_args)
        ulla_reply = response['message']['content'].strip().replace("[LÖST]", "").replace("[EJ_LÖST]", "").strip()
        ulla_reply = re.sub(r"<think>.*?</think>", "", ulla_reply, flags=re.DOTALL)
        if not ulla_reply: 
            ulla_reply = "Tack!" if is_solved else "Jaha?"
        logging.info(f"Ullas svar: '{ulla_reply[:50]}...'"); return ulla_reply
    except Exception as e: logging.error(f"Ollama PERSONA LLM-fel: {e}", exc_info=True); return "Huvudet snurrar..."

def get_llm_response_with_history(student_email, full_history_string, problem_info, latest_student_message_cleaned, problem_level_idx):
    evaluation_marker = get_evaluation_marker(student_email, full_history_string, problem_info, latest_student_message_cleaned)
    is_solved = (evaluation_marker == "[LÖST]")
    ulla_reply_body = get_ulla_persona_response(student_email, full_history_string, problem_info, evaluation_marker, latest_student_message_cleaned, problem_level_idx)
    return ulla_reply_body, is_solved

# --- Graph API Helper Functions ---
def get_graph_token(): # ... (same)
    global MSAL_APP, ACCESS_TOKEN
    if MSAL_APP is None: MSAL_APP = msal.ConfidentialClientApplication(AZURE_CLIENT_ID, authority=MSAL_AUTHORITY, client_credential=AZURE_CLIENT_SECRET)
    token_result = MSAL_APP.acquire_token_silent(GRAPH_SCOPES, account=None)
    if not token_result: logging.info("Hämtar nytt Graph API-token."); token_result = MSAL_APP.acquire_token_for_client(scopes=GRAPH_SCOPES)
    if "access_token" in token_result: ACCESS_TOKEN = token_result['access_token']; return ACCESS_TOKEN
    logging.error(f"Misslyckades hämta Graph token: {token_result.get('error_description')}"); ACCESS_TOKEN = None; return None

def jwt_is_expired(token_str): # ... (same)
    if not token_str: return True
    try: payload_str = token_str.split('.')[1]; payload_str += '=' * (-len(payload_str) % 4); payload = json.loads(base64.urlsafe_b64decode(payload_str).decode()); return payload.get('exp', 0) < time.time()
    except Exception: return True

def make_graph_api_call(method, endpoint_suffix, data=None, params=None, headers_extra=None): # ... (same)
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
        err_details = "Okänt."
        try: err_details = e.response.json().get("error", {}).get("message", e.response.text)
        except json.JSONDecodeError: err_details = e.response.text
        logging.error(f"Graph HTTP-fel: {e.response.status_code} - {err_details} ({method} {url})"); return None
    except requests.exceptions.RequestException as e: logging.error(f"Graph anropsfel: {e} ({method} {url})", exc_info=True); return None

def graph_send_email(recipient_email, subject, body_content, in_reply_to_message_id=None, references_header_str=None, conversation_id=None): # ... (same)
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

def clean_email_body(body_text, original_sender_email_for_attribution=None): # ... (same)
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

def mark_email_as_read(graph_message_id): # ... (same)
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/messages/{graph_message_id}"; payload = {"isRead": True}
    if make_graph_api_call("PATCH", endpoint, data=payload): logging.info(f"E-post {graph_message_id} markerad som läst.")
    else: logging.error(f"Misslyckades markera {graph_message_id} som läst.")

# --- NEW HELPER: Parse email data ---
def parse_graph_email_details(msg_graph):
    details = {
        "graph_msg_id": msg_graph.get('id'),
        "subject": msg_graph.get('subject', ""),
        "internet_message_id": msg_graph.get('internetMessageId'),
        "graph_conversation_id_incoming": msg_graph.get('conversationId'),
        "references_header_value": next((h.get('value') for h in msg_graph.get('internetMessageHeaders', []) if h.get('name', '').lower() == 'references'), None),
        "sender_email": "",
        "bodyPreview": msg_graph.get('bodyPreview', '')
    }
    sender_info = msg_graph.get('from') or msg_graph.get('sender')
    if sender_info and isinstance(sender_info.get('emailAddress'), dict): # Check type before access
        details["sender_email"] = sender_info.get('emailAddress', {}).get('address', '').lower()
    
    body_obj = msg_graph.get('body', {}); body_content = body_obj.get('content', '')
    raw_body = BeautifulSoup(body_content, "html.parser").get_text(separator='\n').strip() if body_obj.get('contentType','').lower()=='html' else body_content
    details["cleaned_body"] = clean_email_body(raw_body, TARGET_USER_GRAPH_ID)
    
    logging.info(f"Från: {details['sender_email']} | Ämne: '{details['subject']}' (ID: {details['graph_msg_id']})")
    logging.debug(f"Rensad text: '{details['cleaned_body'][:100]}...'")
    return details

# --- Core Email Processing (Refactored graph_check_emails) ---
def graph_check_emails():
    global ACCESS_TOKEN
    select_fields = "id,subject,from,sender,receivedDateTime,bodyPreview,body,internetMessageId,conversationId,isRead,internetMessageHeaders"
    params = {"$filter": "isRead eq false", "$select": select_fields, "$orderby": "receivedDateTime asc"}
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/mailFolders/inbox/messages"
    logging.info("Söker olästa e-post (Graph)...")
    response_data = make_graph_api_call("GET", endpoint, params=params)

    if not response_data or "value" not in response_data:
        logging.info("Inga olästa e-post eller fel." if response_data is None else "Inga olästa e-post (Graph).")
        return

    unread_messages = response_data["value"]
    if not unread_messages: logging.info("Inga olästa e-post (Graph)."); return
    logging.info(f"Hittade {len(unread_messages)} olästa e-post (Graph).")
    
    processed_count = 0
    for msg_graph_item in unread_messages: # Renamed to avoid conflict with outer scope msg_graph
        email_data = parse_graph_email_details(msg_graph_item) # Use the helper

        if not email_data["sender_email"] or email_data["sender_email"] == TARGET_USER_GRAPH_ID.lower() or \
           'mailer-daemon' in email_data["sender_email"] or 'noreply' in email_data["sender_email"]:
            logging.warning("Skippar (själv/system). Markerar läst.")
            mark_email_as_read(email_data["graph_msg_id"]); processed_count +=1; continue
        
        try:
            student_next_eligible_level_idx, _ = get_student_progress(email_data["sender_email"])
            active_hist_str, active_problem_info, active_problem_level_idx, active_problem_convo_id_db = get_current_active_problem(email_data["sender_email"])
            
            attempted_start_level_idx_from_email = -1
            detected_start_phrase_from_email = None
            for idx, phrase in enumerate(START_PHRASES):
                if (email_data["subject"] and phrase.lower() in email_data["subject"].lower()) or \
                   (email_data["cleaned_body"].lower().strip().startswith(phrase.lower())):
                    attempted_start_level_idx_from_email = idx
                    detected_start_phrase_from_email = phrase
                    logging.info(f"Mail innehåller startfras '{phrase}' för nivå {idx + 1}.")
                    break 
            
            should_start_new_level = False
            if detected_start_phrase_from_email:
                if active_problem_info and email_data["cleaned_body"].lower().strip().startswith(detected_start_phrase_from_email.lower()) and attempted_start_level_idx_from_email == student_next_eligible_level_idx:
                    logging.info(f"Omstartkommando för nästa nivå '{detected_start_phrase_from_email}'.")
                    should_start_new_level = True
                elif not active_problem_info and attempted_start_level_idx_from_email == student_next_eligible_level_idx:
                    logging.info(f"Nytt startkommando '{detected_start_phrase_from_email}'.")
                    should_start_new_level = True
                elif not active_problem_info and attempted_start_level_idx_from_email != student_next_eligible_level_idx:
                    logging.warning(f"Student använde startfras för nivå {attempted_start_level_idx_from_email + 1}, men nästa är {student_next_eligible_level_idx + 1}.")
                    msg = f"Hej! Fel startfras. För Nivå {student_next_eligible_level_idx + 1}, använd: \"{START_PHRASES[student_next_eligible_level_idx]}\"." if student_next_eligible_level_idx < NUM_LEVELS else "Du har klarat alla nivåer!"
                    subj = f"Re: {email_data['subject']}" if not email_data['subject'].lower().startswith("re:") else email_data['subject']
                    graph_send_email(email_data["sender_email"], subj, msg, email_data["internet_message_id"], email_data["references_header_value"], email_data["graph_conversation_id_incoming"])
                    mark_email_as_read(email_data["graph_msg_id"]); processed_count +=1; continue 
            
            if should_start_new_level:
                target_level = student_next_eligible_level_idx
                if target_level >= NUM_LEVELS: logging.info(f"Student redan klarat alla {NUM_LEVELS} nivåer."); mark_email_as_read(email_data["graph_msg_id"]); processed_count +=1; continue
                problems = PROBLEM_CATALOGUES[target_level]
                if not problems: logging.error(f"Inga problem för nivå {target_level+1}!"); mark_email_as_read(email_data["graph_msg_id"]); processed_count +=1; continue
                
                problem = random.choice(problems)
                if set_active_problem(email_data["sender_email"], problem, target_level, email_data["graph_conversation_id_incoming"]):
                    reply_subj = email_data["subject"] if detected_start_phrase_from_email and detected_start_phrase_from_email.lower() in email_data["subject"].lower() else f"Övning Nivå {target_level + 1}"
                    if graph_send_email(email_data["sender_email"], reply_subj, problem['start_prompt'], conversation_id=email_data["graph_conversation_id_incoming"]):
                        logging.info(f"Skickade problem (Nivå {target_level+1}) till {email_data['sender_email']}")
                        mark_email_as_read(email_data["graph_msg_id"]); processed_count +=1
                    else: logging.error("Misslyckades skicka problem."); clear_active_problem(email_data["sender_email"]) 
                else: logging.error("Misslyckades sätta aktivt problem.")
            
            elif active_hist_str and active_problem_info:
                logging.info(f"E-post tillhör aktivt problem {active_problem_info['id']} (Nivå {active_problem_level_idx+1})")
                body_for_llm = email_data["cleaned_body"] if email_data["cleaned_body"].strip() else (email_data.get('bodyPreview') or "").strip()
                if not body_for_llm: logging.warning("Tom text/förhandsvisning. Ignorerar."); mark_email_as_read(email_data["graph_msg_id"]); processed_count +=1; continue
                
                student_entry = f"Support: {body_for_llm}\n\n"
                append_to_active_problem_history(email_data["sender_email"], student_entry)
                full_hist_for_llm = active_hist_str + student_entry
                ulla_reply, is_solved = get_llm_response_with_history(email_data["sender_email"], full_hist_for_llm, active_problem_info, body_for_llm, active_problem_level_idx)

                if ulla_reply:
                    final_reply = ulla_reply
                    if is_solved:
                        next_lvl = active_problem_level_idx + 1
                        msg = f"\n\nJättebra! Problem {active_problem_info['id']} (Nivå {active_problem_level_idx + 1}) är löst!"
                        msg += f"\nStartfras för Nivå {next_lvl + 1}: \"{START_PHRASES[next_lvl]}\"" if next_lvl < NUM_LEVELS else "\nAlla nivåer klara! Grattis!"
                        final_reply += msg
                    
                    ulla_db_entry = f"Ulla: {final_reply}\n\n"
                    reply_s = email_data["subject"] if not email_data["subject"].lower().startswith("re:") else email_data["subject"]
                    if not reply_s.lower().startswith("re:"): reply_s = f"Re: {email_data['subject']}"
                    convo_id_reply = email_data["graph_conversation_id_incoming"] or active_problem_convo_id_db
                    refs_reply = f"{email_data['references_header_value'] if email_data['references_header_value'] else ''} {email_data['internet_message_id']}".strip()

                    if graph_send_email(email_data["sender_email"], reply_s, final_reply, email_data["internet_message_id"], refs_reply, convo_id_reply):
                        append_to_active_problem_history(email_data["sender_email"], ulla_db_entry)
                        if is_solved:
                            clear_active_problem(email_data["sender_email"])
                            update_student_level(email_data["sender_email"], active_problem_level_idx + 1, active_problem_info['id'])
                        mark_email_as_read(email_data["graph_msg_id"]); processed_count +=1
                        logging.info(f"Bearbetat och svarat på e-post {email_data['graph_msg_id']}.")
                    else: logging.error("Misslyckades skicka svar.")
                else: logging.error("Misslyckades få Ullas svar.")
            
            else: 
                logging.warning(f"E-post från {email_data['sender_email']} - ignorerar. Markerar läst.")
                mark_email_as_read(email_data["graph_msg_id"]); processed_count +=1
        
        except Exception as proc_err:
             logging.error(f"Ohanterat fel vid bearbetning av ID {email_data.get('graph_msg_id', 'OKÄNT')}: {proc_err}", exc_info=True)
             # Fallback to mark as read to prevent loops on consistent error for one mail
             graph_id_to_mark = email_data.get('graph_msg_id') or msg_graph_item.get('id')
             if graph_id_to_mark: mark_email_as_read(graph_id_to_mark)
    
    if unread_messages:
        logging.info(f"Avslutade e-postbearbetning. {processed_count} av {len(unread_messages)} hanterades.")

def print_db_content():
    """Prints content of student_progress and active_problems tables."""
    conn_pdb = None
    print("\n--- UTSKRIFT STUDENT PROGRESS ---")
    try:
        conn_pdb = sqlite3.connect(DB_FILE) # Assumes DB_FILE is globally defined
        conn_pdb.row_factory = sqlite3.Row
        c_pdb = conn_pdb.cursor()
        c_pdb.execute("SELECT * FROM student_progress ORDER BY student_email")
        rows_pdb = c_pdb.fetchall()
        if not rows_pdb:
            print("Tabellen student_progress är tom.")
        else:
            for r_pdb in rows_pdb:
                print(f"  {dict(r_pdb)}") # Indent for slight clarity
    except Exception as e_pdb:
        print(f"Fel vid utskrift av student_progress: {e_pdb}")
        logging.error(f"DB Print (student_progress) Error: {e_pdb}", exc_info=True)
    finally:
        if conn_pdb: conn_pdb.close()

    conn_apdb = None
    print("\n--- UTSKRIFT ACTIVE PROBLEMS ---")
    try:
        conn_apdb = sqlite3.connect(DB_FILE) # Assumes DB_FILE is globally defined
        conn_apdb.row_factory = sqlite3.Row
        c_apdb = conn_apdb.cursor()
        c_apdb.execute("SELECT * FROM active_problems ORDER BY student_email")
        rows_apdb = c_apdb.fetchall()
        if not rows_apdb:
            print("Tabellen active_problems är tom.")
        else:
            for r_apdb in rows_apdb:
                d = dict(r_apdb)
                print(f"\n  Student: {d.get('student_email')}")
                print(f"    Problem ID: {d.get('problem_id')}")
                print(f"    Level Index: {d.get('problem_level_index')}")
                print(f"    Created At: {d.get('created_at')}")
                # For very long histories, you might want to truncate or summarize
                history_to_print = d.get('conversation_history', '')
                print(f"    History (last 500 chars):\n      {'-'*15}\n      {history_to_print[-500:] if len(history_to_print) > 500 else history_to_print}\n      {'-'*15}")
    except Exception as e_apdb:
        print(f"Fel vid utskrift av active_problems: {e_apdb}")
        logging.error(f"DB Print (active_problems) Error: {e_apdb}", exc_info=True)
    finally:
        if conn_apdb: conn_apdb.close()
    print("\n--- SLUT DB UTSKRIFT ---")

# --- Main Execution Block ---
if __name__ == "__main__":
    logging.info(f"Script startat (DB: {DB_FILE}).")
    try: init_db()
    except Exception as db_err: logging.critical(f"DB-initiering misslyckades: {db_err}. Avslutar."); exit(1)

    import sys
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--printdb":
        print_db_content(); exit(0)

    logging.info("--- Kör i E-post Bot-läge (Graph API) ---")
    if not OLLAMA_MODEL or not OLLAMA_EVAL_MODEL: # Check both
        logging.critical("Saknar OLLAMA_MODEL och/eller OLLAMA_EVAL_MODEL i .env."); exit(1)
    try:
        import ollama as ollama_module; globals()['ollama'] = ollama_module
        logging.info(f"Kontrollerar Ollama & persona-modell '{OLLAMA_MODEL}'...")
        ollama.show(OLLAMA_MODEL, **ollama_client_args)
        logging.info(f"Ansluten till Ollama & persona-modell '{OLLAMA_MODEL}' hittad.")
        if OLLAMA_EVAL_MODEL != OLLAMA_MODEL:
             logging.info(f"Kontrollerar Ollama & eval-modell '{OLLAMA_EVAL_MODEL}'...")
             ollama.show(OLLAMA_EVAL_MODEL, **ollama_client_args)
             logging.info(f"Ansluten till Ollama & eval-modell '{OLLAMA_EVAL_MODEL}' hittad.")
        else: logging.info(f"Eval-modell är samma som persona-modell.")
    except ImportError: logging.critical("Ollama-bibliotek saknas."); exit("FEL: Ollama saknas.")
    except Exception as ollama_err: logging.critical(f"Ollama Fel: {ollama_err}"); exit(f"FEL: Ollama-anslutning/-modell.")

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