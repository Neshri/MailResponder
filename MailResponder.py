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
from concurrent.futures import ThreadPoolExecutor, as_completed 

# --- Import Prompts from prompts.py ---
from prompts import ULLA_PERSONA_PROMPT, EVALUATOR_SYSTEM_PROMPT, PROBLEM_CATALOGUES, START_PHRASES, NUM_LEVELS
ollama = None 

# --- Logging Setup & Config ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
if os.path.exists(dotenv_path):
    logging.info(f"DEBUG: Loading .env from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path, override=True)
else:
    logging.warning(f"DEBUG: .env file NOT found at {dotenv_path}.")
    load_dotenv(override=True)

AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
TARGET_USER_GRAPH_ID = os.getenv('BOT_EMAIL_ADDRESS')
PERSONA_MODEL = os.getenv('PERSONA_MODEL') # Changed
EVAL_MODEL = os.getenv('EVAL_MODEL')       # Added
OLLAMA_HOST = os.getenv('OLLAMA_HOST')

logging.info("Miljövariabler inlästa.")
if not all([AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET, TARGET_USER_GRAPH_ID]):
    logging.critical("Saknar kritisk Graph API-konfiguration i .env."); exit("FEL: Config ofullständig.")
ollama_client_args = {}
if OLLAMA_HOST: ollama_client_args['host'] = OLLAMA_HOST; logging.info(f"Ollama-klient: {OLLAMA_HOST}")

DB_FILE = 'conversations.db' 

GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
GRAPH_SCOPES = ['https://graph.microsoft.com/.default']
MSAL_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
MSAL_APP = None
ACCESS_TOKEN = None

# --- Database Functions ---
# (Your existing, corrected DB functions: init_db, get_student_progress, update_student_level, 
#  set_active_problem, get_current_active_problem, append_to_active_problem_history, clear_active_problem)
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
        logging.info(f"Student {student_email} ej hittad i progress, skapar ny post på nivå 0.")
        cursor.execute("INSERT OR IGNORE INTO student_progress (student_email, next_level_index) VALUES (?, ?)", (student_email, 0))
        conn.commit()
        return 0, None 
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
        else: 
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
        current_level_for_insert, _ = get_student_progress(student_email)
        cursor.execute(
            "INSERT INTO student_progress (student_email, next_level_index, last_active_graph_convo_id) VALUES (?, ?, ?) "
            "ON CONFLICT(student_email) DO UPDATE SET last_active_graph_convo_id = excluded.last_active_graph_convo_id",
            (student_email, current_level_for_insert, graph_conversation_id)
        )
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
        cursor.execute('''
            SELECT ap.problem_id, ap.problem_description, ap.correct_solution_keywords, 
                   ap.conversation_history, ap.problem_level_index, sp.last_active_graph_convo_id
            FROM active_problems ap
            LEFT JOIN student_progress sp ON ap.student_email = sp.student_email
            WHERE ap.student_email = ?
        ''', (student_email,)) 
        row = cursor.fetchone()
        if row:
            history_string = row['conversation_history']
            problem_info = {'id': row['problem_id'], 'beskrivning': row['problem_description'], 'losning_nyckelord': json.loads(row['correct_solution_keywords'])}
            level_idx = row['problem_level_index']
            active_graph_convo_id = row['last_active_graph_convo_id'] 
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
        cursor.execute("DELETE FROM active_problems WHERE student_email = ?", (student_email,))
        deleted_rows = cursor.rowcount
        cursor.execute("UPDATE student_progress SET last_active_graph_convo_id = NULL WHERE student_email = ?", (student_email,))
        conn.commit()
        if deleted_rows > 0: logging.info(f"Rensade aktivt problem för {student_email}"); return True
        logging.info(f"Inget aktivt problem att rensa för {student_email}, men säkerställde att convo ID är rensat i progress.")
        return True 
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid rensning av aktivt problem för {student_email}: {e}"); return False
    finally:
        if conn: conn.close()

# --- Graph API Helper Functions (Unchanged) ---
def get_graph_token():
    global MSAL_APP, ACCESS_TOKEN
    if MSAL_APP is None: MSAL_APP = msal.ConfidentialClientApplication(AZURE_CLIENT_ID, authority=MSAL_AUTHORITY, client_credential=AZURE_CLIENT_SECRET)
    token_result = MSAL_APP.acquire_token_silent(GRAPH_SCOPES, account=None)
    if not token_result: logging.info("Hämtar nytt Graph API-token."); token_result = MSAL_APP.acquire_token_for_client(scopes=GRAPH_SCOPES)
    if "access_token" in token_result: ACCESS_TOKEN = token_result['access_token']; return ACCESS_TOKEN
    logging.error(f"Misslyckades hämta Graph token: {token_result.get('error_description')}"); ACCESS_TOKEN = None; return None

def jwt_is_expired(token_str):
    if not token_str: return True; 
    try: payload_str = token_str.split('.')[1]; payload_str += '=' * (-len(payload_str) % 4); payload = json.loads(base64.urlsafe_b64decode(payload_str).decode()); return payload.get('exp', 0) < time.time()
    except Exception: return True

def make_graph_api_call(method, endpoint_or_url, data=None, params=None, headers_extra=None): # Parameter name changed
    global ACCESS_TOKEN
    if ACCESS_TOKEN is None or jwt_is_expired(ACCESS_TOKEN):
        logging.info("Token saknas/utgånget i make_graph_api_call, försöker förnya.")
        if not get_graph_token(): logging.error("Misslyckades förnya token."); return None
    if ACCESS_TOKEN is None: logging.error("ACCESS_TOKEN fortfarande None."); return None

    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN, 'Content-Type': 'application/json'}
    if headers_extra: headers.update(headers_extra)

    # Determine if endpoint_or_url is a full URL or a suffix
    if endpoint_or_url.startswith("https://") or endpoint_or_url.startswith("http://"):
        url = endpoint_or_url
    else:
        url = f"{GRAPH_API_ENDPOINT}{endpoint_or_url}"
    
    try:
        response = requests.request(method, url, headers=headers, json=data, params=params, timeout=30)
        response.raise_for_status()
        if response.status_code in [202, 204]: return True # 204 is typical for successful DELETE
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401: logging.warning("Graph API 401. Ogiltigförklarar token."); ACCESS_TOKEN = None
        err_details = "Okänt."
        try: err_details = e.response.json().get("error", {}).get("message", e.response.text)
        except json.JSONDecodeError: err_details = e.response.text
        logging.error(f"Graph HTTP-fel: {e.response.status_code} - {err_details} ({method} {url})"); return None
    except requests.exceptions.RequestException as e: logging.error(f"Graph anropsfel: {e} ({method} {url})", exc_info=True); return None

# --- Graph API Email Functions (Unchanged) ---
def graph_send_email(recipient_email, subject, body_content, in_reply_to_message_id=None, references_header_str=None, conversation_id=None):
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

def clean_email_body(body_text, original_sender_email_for_attribution=None):
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

def mark_email_as_read(graph_message_id):
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/messages/{graph_message_id}"; payload = {"isRead": True}
    if make_graph_api_call("PATCH", endpoint, data=payload): logging.info(f"E-post {graph_message_id} markerad som läst.")
    else: logging.error(f"Misslyckades markera {graph_message_id} som läst.")

# --- Helper to parse email details ---
def _parse_graph_email_item(msg_graph_item):
    email_data = {"graph_msg_id": msg_graph_item.get('id'), "subject": msg_graph_item.get('subject', ""), "sender_email": "", "internet_message_id": msg_graph_item.get('internetMessageId'), "graph_conversation_id_incoming": msg_graph_item.get('conversationId'), "references_header_value": None, "cleaned_body": "", "body_preview": msg_graph_item.get('bodyPreview', "")}
    sender_info = msg_graph_item.get('from') or msg_graph_item.get('sender')
    if sender_info and sender_info.get('emailAddress'): email_data["sender_email"] = sender_info['emailAddress'].get('address', '').lower()
    for header in msg_graph_item.get('internetMessageHeaders', []):
        if header.get('name', '').lower() == 'references': email_data["references_header_value"] = header.get('value'); break
    body_obj = msg_graph_item.get('body', {}); body_content = body_obj.get('content', '')
    raw_body = BeautifulSoup(body_content, "html.parser").get_text(separator='\n').strip() if body_obj.get('contentType','').lower()=='html' else body_content
    email_data["cleaned_body"] = clean_email_body(raw_body, TARGET_USER_GRAPH_ID)
    logging.debug(f"Parsed email: ID={email_data['graph_msg_id']}, From={email_data['sender_email']}, CleanedBody='{email_data['cleaned_body'][:50]}...'")
    return email_data

# --- Helper to handle "start new problem" logic (Main Thread) ---
def _handle_start_new_problem_main_thread(email_data, student_next_eligible_level_idx):
    problem_list_for_level = PROBLEM_CATALOGUES[student_next_eligible_level_idx]
    if not problem_list_for_level:
        logging.error(f"Inga problem definierade för nivåindex {student_next_eligible_level_idx}!")
        return False 
    problem = random.choice(problem_list_for_level)
    if set_active_problem(email_data["sender_email"], problem, student_next_eligible_level_idx, email_data["graph_conversation_id_incoming"]):
        reply_subject = email_data["subject"] 
        if graph_send_email(email_data["sender_email"], reply_subject, problem['start_prompt'], conversation_id=email_data["graph_conversation_id_incoming"]):
            logging.info(f"Skickade problem (Nivå {student_next_eligible_level_idx+1}) till {email_data['sender_email']}")
            return True
        else:
            logging.error("Misslyckades skicka initialt problem för ny nivå.")
            clear_active_problem(email_data["sender_email"]) 
            return False
    else:
        logging.error("Misslyckades sätta aktivt problem i DB för ny nivå.")
        return False
    
def get_evaluator_decision(student_email, problem_description, solution_keywords, latest_student_message_cleaned):
    """
    Calls an LLM to act as a strict evaluator.
    Removes <think>...</think> blocks and checks for "[LÖST]" presence.
    Returns '[LÖST]' or '[EJ_LÖST]'.
    """
    global ollama # Ensure ollama is accessible
    if not EVAL_MODEL: # Changed
        logging.error(f"Evaluator ({student_email}): EVAL_MODEL ej satt."); return "[EJ_LÖST]" # Default to not solved on error

    logging.info(f"Evaluator AI för {student_email}: Utvärderar studentens meddelande med modell '{EVAL_MODEL}'.") # Logging model used

    # System prompt for the evaluator is very direct
    evaluator_prompt_content = f"""Tekniskt Problem: "{problem_description}"
Korrekta Lösningar/lösningsnyckelord: {solution_keywords}
Studentens SENASTE Meddelande:
---
{latest_student_message_cleaned}
---
Uppgift: Innehåller studentens senaste meddelande en lösning som matchar något av lösningsnyckelorden?
Svara ENDAST med '[LÖST]' eller '[EJ_LÖST]'."""

    messages_for_evaluator = [
        {'role': 'system', 'content': EVALUATOR_SYSTEM_PROMPT},
        {'role': 'user', 'content': evaluator_prompt_content}
    ]
    
    # Log input to evaluator
    # logging.debug(f"--- MEDDELANDE TILL EVALUATOR AI ({student_email}) ---\n{json.dumps(messages_for_evaluator, indent=2, ensure_ascii=False)}\n--- SLUT ---")

    try:
        response = ollama.chat(
            model=EVAL_MODEL, # Changed
            messages=messages_for_evaluator,
            options={'temperature': 0.1, 'num_predict': 500, "num_thread": 24},
            **ollama_client_args
        )
        raw_eval_reply_from_llm = response['message']['content'].strip()
        
        # Remove <think>...</think> blocks
        processed_eval_reply = re.sub(r"<think>.*?</think>", "", raw_eval_reply_from_llm, flags=re.DOTALL).strip()
        
        if processed_eval_reply != raw_eval_reply_from_llm:
            logging.info(f"Evaluator AI ({student_email}): Removed <think> block. Original: '{raw_eval_reply_from_llm}', Processed: '{processed_eval_reply}'")
        
        # logging.debug(f"--- RÅTT SVAR FRÅN EVALUATOR AI ({student_email}) ---\n{raw_eval_reply_from_llm}\n--- SLUT ---")
        # logging.debug(f"--- PROCESSED SVAR FRÅN EVALUATOR AI ({student_email}) ---\n{processed_eval_reply}\n--- SLUT ---")


        if "[LÖST]" in processed_eval_reply:
            logging.info(f"Evaluator AI ({student_email}): Bedömning [LÖST] (baserat på närvaro i '{processed_eval_reply}')")
            return "[LÖST]"
        else: # Default to EJ_LÖST if not an exact match, or if it errors/gives other text
            # Check if the processed reply was *meant* to be "[EJ_LÖST]" or something else entirely
            if "[EJ_LÖST]" not in processed_eval_reply : # If it's not [EJ_LÖST] either, it's unexpected
                 logging.warning(f"Evaluator AI ({student_email}): Oväntat svar '{processed_eval_reply}', tolkar som [EJ_LÖST].")
            else: # It contained [EJ_LÖST] or was empty/something else not [LÖST]
                logging.info(f"Evaluator AI ({student_email}): Bedömning [EJ_LÖST] (baserat på frånvaro av '[LÖST]' i '{processed_eval_reply}')")
            return "[EJ_LÖST]"
    except Exception as e:
        logging.error(f"Evaluator AI ({student_email}): Fel vid LLM-anrop: {e}", exc_info=True)
        return "[EJ_LÖST]" # Default to not solved on error
    
def get_ulla_persona_reply(student_email, full_history_string_for_ulla, problem_info_for_ulla, 
                           latest_student_message_for_ulla, problem_level_idx_for_ulla, evaluator_decision_marker):
    """
    Calls an LLM to generate Ulla's persona reply, conditioned on the evaluator's decision.
    """
    global ollama
    if not PERSONA_MODEL: # Changed
        logging.error(f"Ulla Persona ({student_email}): PERSONA_MODEL ej satt."); return "Glömde vad jag skulle säga..."

    logging.info(f"Ulla Persona AI för {student_email} (Nivå {problem_level_idx_for_ulla+1}): Genererar svar baserat på '{evaluator_decision_marker}' med modell '{PERSONA_MODEL}'.") # Logging model used

    # System prompt for Ulla includes her persona and the current context.
    # The history already contains the student's latest message.
    ulla_system_context = f"""{ULLA_PERSONA_PROMPT}
Du har haft följande konversation:
--- KONVERSATIONSHISTORIK ---
{full_history_string_for_ulla}
--- SLUT KONVERSATIONSHISTORIK ---

Ditt nuvarande tekniska problem är: "{problem_info_for_ulla['beskrivning']}"
"""

    # User prompt for Ulla tells her how to react based on the evaluator's decision.
    if evaluator_decision_marker == "[LÖST]":
        ulla_task_prompt = "Studenten har precis gett ett råd som löste problemet! Svara som Ulla, uttryck glädje och tacksamhet. Bekräfta att det fungerade. Du kan sedan avsluta konversationen artigt."
    else: # "[EJ_LÖST]"
        ulla_task_prompt = "Studentens senaste råd löste tyvärr inte problemet. Svara som Ulla. Var artig, kanske lite förvirrad eller upprepa symptomen på ett Ulla-vis, men avslöja INTE den korrekta lösningen eller att du utvärderar studenten. Fortsätt konversationen."

    messages_for_ulla = [
        {'role': 'system', 'content': ulla_system_context},
        {'role': 'user', 'content': ulla_task_prompt}
    ]
    
    # logging.debug(f"--- MEDDELANDE TILL ULLA PERSONA AI ({student_email}) ---\n{json.dumps(messages_for_ulla, indent=2, ensure_ascii=False)}\n--- SLUT ---")

    try:
        response = ollama.chat(
            model=PERSONA_MODEL, # Changed
            messages=messages_for_ulla,
            options={'temperature': 0.75, 'num_predict': 1000, 'num_thread': 24}, # Higher temp for more natural Ulla
            **ollama_client_args
        )
        ulla_svar = response['message']['content'].strip()
        ulla_svar = re.sub(r"<think>.*?</think>", "", ulla_svar, flags=re.DOTALL).strip()
        ulla_svar = re.sub("</end_of_turn>", "", ulla_svar) # Remove the </end_of_turn> tag in gemma
        # logging.debug(f"--- RÅTT SVAR FRÅN ULLA PERSONA AI ({student_email}) ---\n{ulla_svar}\n--- SLUT ---")
        logging.info(f"Ulla Persona AI ({student_email}): Genererade svar: '{ulla_svar[:50]}...'")
        return ulla_svar
    except Exception as e:
        logging.error(f"Ulla Persona AI ({student_email}): Fel vid LLM-anrop: {e}", exc_info=True)
        return "Åh nej, nu tappade jag visst bort mig lite..."
    
def _llm_evaluation_and_reply_task(student_email, full_history_string, problem_info, 
                                   latest_student_message_cleaned, problem_level_idx_for_prompt,
                                   active_problem_convo_id_db, # Added for result package
                                   email_data_for_result): # Added for result package
    """
    Worker function: 
    1. Calls Evaluator AI.
    2. Calls Ulla Persona AI based on evaluator's decision.
    Returns a dictionary for the main thread.
    """
    logging.info(f"LLM-tråd (_llm_evaluation_and_reply_task) startad för {student_email}")

    # Step 1: Get Evaluator's Decision
    evaluator_marker = get_evaluator_decision(
        student_email, 
        problem_info['beskrivning'], 
        problem_info['losning_nyckelord'], 
        latest_student_message_cleaned
    )
    is_solved_by_evaluator = (evaluator_marker == "[LÖST]")

    # Step 2: Get Ulla's Persona Reply
    ulla_final_reply_text = get_ulla_persona_reply(
        student_email,
        full_history_string, # History already includes latest student message
        problem_info,
        latest_student_message_cleaned, # For Ulla's context if needed, though history has it
        problem_level_idx_for_prompt,
        evaluator_marker # Pass the decision to Ulla's prompt
    )

    result_package = {
        "email_data": email_data_for_result,
        "ulla_final_reply_body": ulla_final_reply_text,
        "is_solved": is_solved_by_evaluator, # Decision comes from evaluator
        "error": False, # Assuming no critical error in this worker itself yet
        "send_reply": bool(ulla_final_reply_text), # Send if Ulla generated something
        # Pass through other necessary data for main thread
        "active_problem_level_idx": problem_level_idx_for_prompt,
        "active_problem_info_id": problem_info['id'],
        "active_problem_convo_id_db": active_problem_convo_id_db,
        "reply_subject": email_data_for_result["subject"], # Base subject
        "in_reply_to_for_send": email_data_for_result["internet_message_id"],
        "references_for_send": f"{email_data_for_result['references_header_value'] if email_data_for_result['references_header_value'] else ''} {email_data_for_result['internet_message_id']}".strip(),
        "convo_id_for_send": email_data_for_result["graph_conversation_id_incoming"] or active_problem_convo_id_db
    }
    
    if not ulla_final_reply_text:
        result_package["error"] = True
        result_package["send_reply"] = False
        logging.error(f"LLM-tråd ({student_email}): Ulla Persona genererade inget svar.")

    return result_package

# --- Core Email Processing Loop (graph_check_emails - Modified to use new worker) ---
def graph_check_emails():
    global ACCESS_TOKEN 
    # ... (select_fields, params, endpoint, initial Graph call - same as your last version) ...
    select_fields = "id,subject,from,sender,receivedDateTime,bodyPreview,body,internetMessageId,conversationId,isRead,internetMessageHeaders"
    params = {"$filter": "isRead eq false", "$select": select_fields, "$orderby": "receivedDateTime asc"}
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/mailFolders/inbox/messages"
    logging.info("Söker olästa e-post (Graph)...")
    response_data = make_graph_api_call("GET", endpoint, params=params)
    if not response_data or "value" not in response_data:
        logging.info("Inga olästa e-post eller fel." if response_data is None else "Inga olästa e-post (Graph).")
        return
    unread_messages_raw = response_data["value"]
    if not unread_messages_raw: logging.info("Inga olästa e-post (Graph)."); return
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
            mark_email_as_read(email_data["graph_msg_id"]); processed_ids_in_phase1.add(email_data["graph_msg_id"]); continue

        student_next_eligible_level_idx, _ = get_student_progress(email_data["sender_email"]) # This is the highest level_idx they are eligible for + 1 (or 0 for new)
        active_hist_str, active_problem_info, active_problem_level_idx_db, active_problem_convo_id_db = get_current_active_problem(email_data["sender_email"])
        
        detected_start_level_idx = -1  # Level index if a valid start command is found
        is_explicit_body_start_command = False

        # 1. Check for a start command in the email BODY first. This takes precedence.
        for level_idx, phrase_text in enumerate(START_PHRASES):
            if level_idx >= NUM_LEVELS:
                break
            current_start_phrase_lower = phrase_text.lower()
            if email_data["cleaned_body"].lower().strip().startswith(current_start_phrase_lower):
                detected_start_level_idx = level_idx
                is_explicit_body_start_command = True
                # Log intent, actual eligibility check comes after subject check
                break
        
        # 2. If no explicit body command, check the SUBJECT.
        #    A subject command only counts if there's NO active problem.
        if not is_explicit_body_start_command:
            for level_idx, phrase_text in enumerate(START_PHRASES):
                if level_idx >= NUM_LEVELS:
                    break
                current_start_phrase_lower = phrase_text.lower()
                if email_data["subject"] and current_start_phrase_lower in email_data["subject"].lower():
                    if not active_problem_info: # Only treat as start if no active problem
                        detected_start_level_idx = level_idx
                        # Log intent, actual eligibility check comes after subject check
                        break 
                    else:
                        logging.info(f"Main: Startkommando i ÄMNESRAD ignorerat för {email_data['sender_email']} (nivå {level_idx +1}) p.g.a. pågående aktivt problem ({active_problem_info['id']}). Tolkas som svar.")
                        break 
        
        # 3. Categorize the email based on the findings AND eligibility
        if detected_start_level_idx != -1:
            # A start command was potentially found (either body or valid subject).
            # NOW, check if the user is eligible for this detected level.
            # student_next_eligible_level_idx is the highest level index they can start (e.g., 0 for new, 1 if level 0 completed)
            if detected_start_level_idx <= student_next_eligible_level_idx:
                # User is eligible for this level (it's a replay or the current next level).
                if is_explicit_body_start_command:
                    logging.info(f"Main: Startkommando explicit i E-POSTKROPP detekterat för behörig nivå {detected_start_level_idx + 1} från {email_data['sender_email']}. Köar 'start_command'.")
                else: # Must be subject command with no active problem
                    logging.info(f"Main: Startkommando i ÄMNESRAD detekterat för behörig nivå {detected_start_level_idx + 1} (inget aktivt problem) från {email_data['sender_email']}. Köar 'start_command'.")
                
                emails_to_process_sequentially.append({
                    "type": "start_command", 
                    "data": email_data, 
                    "level_idx": detected_start_level_idx 
                })
            else:
                # User is trying to start a level that is too high / not yet unlocked.
                logging.warning(f"Main: Student {email_data['sender_email']} försökte starta nivå {detected_start_level_idx + 1}, men är endast behörig upp till (och med) nivå {student_next_eligible_level_idx + 1}.")
                
                msg_body = (f"Hej! Du försökte starta Nivå {detected_start_level_idx + 1} (index {detected_start_level_idx}), "
                            f"men du har för närvarande endast låst upp nivåer upp till och med Nivå {student_next_eligible_level_idx + 1} (index {student_next_eligible_level_idx}).")
                
                if student_next_eligible_level_idx < NUM_LEVELS :
                     msg_body += (f"\nFör att spela din nästa upplåsta nivå ({student_next_eligible_level_idx + 1}), "
                                  f"använd startfrasen: \"{START_PHRASES[student_next_eligible_level_idx]}\"")
                else: # They've completed all levels (student_next_eligible_level_idx == NUM_LEVELS)
                    msg_body = (f"Hej! Du försökte starta Nivå {detected_start_level_idx + 1}. "
                                f"Det ser ut som att du redan har klarat alla {NUM_LEVELS} nivåer! Grattis!")

                reply_subject_locked = f"Re: {email_data['subject']}" if email_data['subject'] and not email_data['subject'].lower().startswith("re:") else email_data['subject']
                if not reply_subject_locked: reply_subject_locked = "Angående nivåstart" 

                graph_send_email(email_data["sender_email"], reply_subject_locked, msg_body, 
                                 email_data["internet_message_id"], 
                                 email_data["references_header_value"], 
                                 email_data["graph_conversation_id_incoming"])
                mark_email_as_read(email_data["graph_msg_id"])
                processed_ids_in_phase1.add(email_data["graph_msg_id"])
        
        elif active_hist_str and active_problem_info:
            # No valid new start command was processed (either none found, subject-only ignored, or level locked).
            # AND an active problem exists. So, this is a reply to the active problem.
            logging.info(f"Main: E-post från {email_data['sender_email']} är svar på aktivt problem ({active_problem_info['id']}). Köar för LLM-bearbetning.")
            body_for_llm_task = email_data["cleaned_body"] if email_data["cleaned_body"].strip() else (email_data.get('body_preview') or "").strip()
            if not body_for_llm_task:
                logging.warning(f"Main: Tomt meddelande från {email_data['sender_email']} i svar på aktivt problem. Markerar som läst.")
                mark_email_as_read(email_data["graph_msg_id"]); processed_ids_in_phase1.add(email_data["graph_msg_id"]); continue
            
            student_entry_for_db = f"Support: {body_for_llm_task}\n\n"
            append_to_active_problem_history(email_data["sender_email"], student_entry_for_db)
            
            llm_tasks_to_submit.append({
                "email_data_for_result": email_data,
                "full_history_string": active_hist_str + student_entry_for_db,
                "problem_info": active_problem_info,
                "latest_student_message_cleaned": body_for_llm_task,
                "problem_level_idx_for_prompt": active_problem_level_idx_db,
                "active_problem_convo_id_db": active_problem_convo_id_db
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
                    task["email_data_for_result"]      
                ): task for task in llm_tasks_to_submit
            }
            for future in as_completed(future_to_task_package):
                try:
                    llm_result_package = future.result() 
                    llm_results_from_threads.append(llm_result_package) 
                except Exception as exc_llm_future:
                    logging.error(f"En LLM-uppgift genererade ett oväntat undantag: {exc_llm_future}", exc_info=True)


    # --- Phase 3: Process results from LLM threads (Main Thread) ---
    for result_package in llm_results_from_threads:
        email_data = result_package["email_data"]
        if email_data["graph_msg_id"] in processed_ids_in_phase1: continue

        if not result_package["error"] and result_package["send_reply"]:
            final_ulla_reply = result_package["ulla_final_reply_body"]
            is_solved = result_package["is_solved"]
            
            if is_solved and "\nStartfras för nästa nivå" not in final_ulla_reply and "\nDu har klarat alla nivåer!" not in final_ulla_reply :
                active_lvl_idx = result_package["active_problem_level_idx"]
                prob_id = result_package["active_problem_info_id"]
                
                # Determine the student's next eligible level *after this solve*
                # Get current progress to see if this solve advances them
                student_current_max_level_idx, _ = get_student_progress(email_data["sender_email"])
                potential_new_next_level_idx = active_lvl_idx + 1
                
                completion_msg = f"\n\nJättebra! Problem {prob_id} (Nivå {active_lvl_idx + 1}) är löst!"

                if potential_new_next_level_idx < NUM_LEVELS:
                    # If they solved their current highest level or a new higher one that advances them
                    if potential_new_next_level_idx > student_current_max_level_idx:
                         next_start_phrase_level_idx = potential_new_next_level_idx
                    else: # They replayed an older level, direct to their actual next level
                         next_start_phrase_level_idx = student_current_max_level_idx
                    
                    if next_start_phrase_level_idx < NUM_LEVELS: # Ensure it's still a valid level
                        completion_msg += f"\nStartfras för nästa nivå ({next_start_phrase_level_idx + 1}): \"{START_PHRASES[next_start_phrase_level_idx]}\""
                    else: # This case implies they just completed the last level
                        completion_msg += "\nDu har klarat alla nivåer! Grattis!"
                else: # They solved the last level (active_lvl_idx + 1 == NUM_LEVELS)
                    completion_msg += "\nDu har klarat alla nivåer! Grattis!"
                final_ulla_reply += completion_msg
            
            ulla_db_entry = f"Ulla: {final_ulla_reply}\n\n" 
            
            reply_s = result_package["reply_subject"] 
            if not reply_s.lower().startswith("re:"): reply_s = f"Re: {result_package['reply_subject']}"

            if graph_send_email(email_data["sender_email"], reply_s, final_ulla_reply, 
                                result_package["in_reply_to_for_send"], 
                                result_package["references_for_send"], 
                                result_package["convo_id_for_send"]):
                append_to_active_problem_history(email_data["sender_email"], ulla_db_entry)
                if is_solved:
                    clear_active_problem(email_data["sender_email"])
                    
                    # Get current progress *before* this update.
                    current_progress_level_before_update, _ = get_student_progress(email_data["sender_email"])
                    
                    # new_next_level_for_db should be the higher of their current progress 
                    # or the level just completed + 1. This ensures progress only moves forward or stays.
                    new_next_level_for_db = max(current_progress_level_before_update, result_package["active_problem_level_idx"] + 1)
                    
                    update_student_level(email_data["sender_email"], 
                                         new_next_level_for_db, 
                                         result_package["active_problem_info_id"])
                    if new_next_level_for_db > current_progress_level_before_update:
                         logging.info(f"Main: Student {email_data['sender_email']} avancerade till nästa nivå index {new_next_level_for_db} (Nivå {new_next_level_for_db+1}) efter att ha klarat problem {result_package['active_problem_info_id']}.")
                    else:
                         logging.info(f"Main: Student {email_data['sender_email']} klarade om problem {result_package['active_problem_info_id']} (nivå index {result_package['active_problem_level_idx']}). Huvudprogression oförändrad på index {current_progress_level_before_update}.")

                mark_email_as_read(email_data["graph_msg_id"])
                processed_ids_in_phase1.add(email_data["graph_msg_id"])
            else: logging.error(f"Main: Misslyckades skicka svar för {email_data['graph_msg_id']} efter LLM.")
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
        if email_data_seq["graph_msg_id"] in processed_ids_in_phase1 : continue 

        student_level_idx_seq = task["level_idx"] # This is the already validated level_idx for start_command
        if task["type"] == "start_command":
            if _handle_start_new_problem_main_thread(email_data_seq, student_level_idx_seq):
                mark_email_as_read(email_data_seq["graph_msg_id"])
                processed_ids_in_phase1.add(email_data_seq["graph_msg_id"])
        elif task["type"] == "inform_wrong_level_or_ignore":
            # This handles emails that were not valid start commands (for any reason other than level locked)
            # and were not replies to an active problem.
            # The original `student_level_idx_seq` here is the student's current next_eligible_level_idx
            # for context in the message.
            any_start_phrase_detected_seq = None; attempted_level_idx_seq = -1
            for idx_s, phrase_s in enumerate(START_PHRASES): # Check again for any start phrase
                if (email_data_seq["subject"] and phrase_s.lower() in email_data_seq["subject"].lower()) or \
                   (email_data_seq["cleaned_body"].lower().strip().startswith(phrase_s.lower())):
                    any_start_phrase_detected_seq = phrase_s; attempted_level_idx_seq = idx_s; break
            
            # If they used a start phrase for a level they *are* eligible for, but it wasn't caught as 'start_command'
            # (e.g., subject command with active problem, but active problem since cleared), this might be redundant
            # or offer a chance to guide. However, Phase 1 now handles locked levels explicitly.
            # This block mostly catches "general wrong start phrase" or "no start phrase, no active problem".

            if any_start_phrase_detected_seq and attempted_level_idx_seq != student_level_idx_seq and attempted_level_idx_seq <= student_level_idx_seq :
                # They used a start phrase for a *lower or current unlocked* level, but it wasn't the *expected* next one.
                # This case should be rare now due to Phase 1's explicit start_command handling.
                # This implies they might be confused about their current level if they are trying to start an *older* one.
                logging.warning(f"Main: Student {email_data_seq['sender_email']} använde startfras '{any_start_phrase_detected_seq}' (Nivå {attempted_level_idx_seq + 1}), förväntad/aktuell är Nivå {student_level_idx_seq + 1}.")
                msg = (f"Hej! Du använde startfrasen för Nivå {attempted_level_idx_seq + 1}. "
                       f"Din nästa nivå är {student_level_idx_seq + 1}. "
                       f"För att starta den, använd: \"{START_PHRASES[student_level_idx_seq]}\".")
                if student_level_idx_seq >= NUM_LEVELS:
                    msg = "Hej! Det ser ut som du redan har klarat alla nivåer! Grattis!"

                subj = f"Re: {email_data_seq['subject']}" if email_data_seq['subject'] and not email_data_seq['subject'].lower().startswith("re:") else email_data_seq['subject']
                if not subj: subj = "Angående nivåstart"
                graph_send_email(email_data_seq["sender_email"], subj, msg, email_data_seq["internet_message_id"], email_data_seq["references_header_value"], email_data_seq["graph_conversation_id_incoming"])
            else: 
                # No recognizable start phrase, or a phrase for a level that was already handled (e.g. locked)
                # or truly unrecognized email.
                logging.warning(f"Main: E-post från {email_data_seq['sender_email']} - ignorerar (ingen matchande åtgärd). Markerar läst.")
            mark_email_as_read(email_data_seq["graph_msg_id"])
            processed_ids_in_phase1.add(email_data_seq["graph_msg_id"])


    if unread_messages_raw:
        final_processed_count = len(processed_ids_in_phase1) 
        logging.info(f"Avslutade e-postbearbetning. {final_processed_count} av {len(unread_messages_raw)} e-postmeddelanden hanterades denna cykel.")


def graph_delete_all_emails_in_inbox(user_principal_name_or_id=TARGET_USER_GRAPH_ID):
    """
    Deletes all emails in the inbox for the specified user.
    Handles pagination to retrieve all message IDs before deleting.
    """
    logging.info(f"Attempting to delete all emails in inbox for {user_principal_name_or_id}...")
    global ACCESS_TOKEN
    if ACCESS_TOKEN is None or jwt_is_expired(ACCESS_TOKEN):
        logging.info("Token for delete operation missing/expired, attempting to refresh.")
        if not get_graph_token():
            logging.error("Failed to refresh token. Cannot proceed with email deletion.")
            return False

    all_message_ids = []
    # Initial endpoint to get messages from the inbox, requesting only 'id' and using $top for efficiency.
    # Note: $top max value can vary, 100 is generally safe. Max is 1000 for messages.
    current_request_url = f"/users/{user_principal_name_or_id}/mailFolders/inbox/messages?$select=id&$top=100"

    logging.info("Fetching message IDs from inbox...")
    page_count = 0
    while current_request_url:
        page_count += 1
        logging.debug(f"Fetching page {page_count} of messages using URL: {current_request_url}")
        # make_graph_api_call will handle if current_request_url is a full path or a suffix
        response = make_graph_api_call("GET", current_request_url)

        if not response or "value" not in response:
            if response is None: # Indicates a request error
                 logging.error(f"Failed to fetch messages (page {page_count}). Aborting further fetching.")
            else: # Response received, but no 'value' field or empty 'value'
                 logging.info(f"No 'value' in response or empty message list on page {page_count}. Assuming no more messages.")
            break 

        messages_page = response.get("value", [])
        if not messages_page and page_count == 1 and not all_message_ids:
             logging.info("Inbox is empty or no messages retrieved on the first page.")
             return True # Considered success as inbox is effectively empty

        for msg in messages_page:
            if msg.get("id"):
                all_message_ids.append(msg["id"])
        
        # Check for the next page link
        current_request_url = response.get("@odata.nextLink") # This will be a full URL
        if current_request_url:
            logging.info(f"Fetching next page of messages... ({len(all_message_ids)} IDs collected so far)")
        else:
            logging.info(f"All message pages fetched. Total messages to delete: {len(all_message_ids)}")
            break # No more pages

    if not all_message_ids:
        logging.info("No messages found in the inbox to delete.")
        return True

    logging.info(f"Proceeding to delete {len(all_message_ids)} messages...")
    deleted_count = 0
    failed_count = 0

    for i, msg_id in enumerate(all_message_ids):
        delete_endpoint_suffix = f"/users/{user_principal_name_or_id}/messages/{msg_id}"
        # Consider adding a small delay if API throttling becomes an issue, e.g., time.sleep(0.05)
        if make_graph_api_call("DELETE", delete_endpoint_suffix):
            logging.debug(f"Successfully deleted message ID: {msg_id}")
            deleted_count += 1
        else:
            logging.error(f"Failed to delete message ID: {msg_id}")
            failed_count += 1
        
        if (i + 1) % 50 == 0 or (i + 1) == len(all_message_ids): # Log progress every 50 emails or at the end
            logging.info(f"Deletion progress: {deleted_count} deleted, {failed_count} failed. ({i + 1}/{len(all_message_ids)} processed)")

    logging.info(f"Email deletion process completed. Successfully deleted: {deleted_count}, Failed to delete: {failed_count}.")
    return failed_count == 0

# --- Main Execution Block ---
if __name__ == "__main__":
    logging.info(f"Script startat (DB: {DB_FILE}).")
    try: init_db()
    except Exception as db_err: logging.critical(f"DB-initiering misslyckades: {db_err}. Avslutar."); exit(1)

    import sys
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--printdb":
        # ... (Your existing print_db_content function definition here) ...
        def print_db_content(): 
            conn_pdb = None; print("\n--- UTSKRIFT STUDENT PROGRESS ---")
            try:
                conn_pdb = sqlite3.connect(DB_FILE); conn_pdb.row_factory = sqlite3.Row; c_pdb = conn_pdb.cursor()
                c_pdb.execute("SELECT * FROM student_progress"); rows_pdb = c_pdb.fetchall()
                if not rows_pdb: print("Tabellen student_progress är tom.")
                else: 
                    for r_pdb in rows_pdb: print(dict(r_pdb))
            except Exception as e_pdb: print(f"Fel vid utskrift av student_progress: {e_pdb}")
            finally: 
                if conn_pdb: conn_pdb.close()
            conn_apdb = None; print("\n--- UTSKRIFT ACTIVE PROBLEMS ---")
            try:
                conn_apdb = sqlite3.connect(DB_FILE); conn_apdb.row_factory = sqlite3.Row; c_apdb = conn_apdb.cursor()
                c_apdb.execute("SELECT * FROM active_problems"); rows_apdb = c_apdb.fetchall()
                if not rows_apdb: print("Tabellen active_problems är tom.")
                else: 
                    for r_apdb in rows_apdb: 
                        d = dict(r_apdb)
                        print(f"Student: {d.get('student_email')}, Problem ID: {d.get('problem_id')}, Level Idx: {d.get('problem_level_index')}")
                        print(f"  History:\n{d.get('conversation_history', '')}")
            except Exception as e_apdb: print(f"Fel vid utskrift av active_problems: {e_apdb}")
            finally: 
                if conn_apdb: conn_apdb.close()
            print("--- SLUT DB UTSKRIFT ---")
        print_db_content()
        exit()
    elif len(sys.argv) > 1 and sys.argv[1].lower() == "--emptyinbox":
        logging.info("--- EMPTYING INBOX (via --emptyinbox command) ---")
        if not TARGET_USER_GRAPH_ID: # Ensure critical config is present
             logging.critical("TARGET_USER_GRAPH_ID is not set in .env. Cannot empty inbox.")
             exit(1)
        if not get_graph_token(): # Ensure token can be acquired
            logging.critical("Failed to get Graph API token. Cannot empty inbox.")
            exit(1)
        
        # Call the function to delete emails
        # (Ensure graph_delete_all_emails_in_inbox and modified make_graph_api_call are defined above)
        success = graph_delete_all_emails_in_inbox() 
        if success:
            logging.info("Inbox emptying process reported success overall.")
        else:
            logging.warning("Inbox emptying process reported one or more failures during deletion.")
        exit(0) # Exit after attempting to empty the inbox


    logging.info("--- Kör i E-post Bot-läge (Graph API) ---")
    if not PERSONA_MODEL or not EVAL_MODEL: 
        logging.critical(f"Saknar PERSONA_MODEL ('{PERSONA_MODEL}') och/eller EVAL_MODEL ('{EVAL_MODEL}')."); exit(1) 
    try:
        import ollama as ollama_module; globals()['ollama'] = ollama_module
        logging.info(f"Kontrollerar Ollama & modeller: PERSONA_MODEL='{PERSONA_MODEL}', EVAL_MODEL='{EVAL_MODEL}'...") 
        ollama.show(PERSONA_MODEL, **ollama_client_args) 
        logging.info(f"Ansluten till Ollama & PERSONA_MODEL '{PERSONA_MODEL}' hittad.") 
        ollama.show(EVAL_MODEL, **ollama_client_args) 
        logging.info(f"Ansluten till Ollama & EVAL_MODEL '{EVAL_MODEL}' hittad.")     
    except ImportError: logging.critical("Ollama-bibliotek saknas."); exit("FEL: Ollama saknas.")
    except Exception as ollama_err: logging.critical(f"Ollama Fel: {ollama_err}"); exit("FEL: Ollama-anslutning/-modell.")

    if not get_graph_token(): logging.critical("Misslyckades hämta Graph API-token."); exit(1) 
    
    logging.info("Startar huvudloop för e-postkontroll...")
    while True:
        try:
            if ACCESS_TOKEN is None or jwt_is_expired(ACCESS_TOKEN):
                logging.info("Token saknas/utgånget före e-postkontroll, förnyar...")
                if not get_graph_token():
                    logging.error("Misslyckades förnya token, väntar till nästa cykel.")
                    time.sleep(60); continue 
            graph_check_emails() 
        except Exception as loop_err:
            logging.error(f"Kritiskt fel i huvudloop: {loop_err}", exc_info=True)
            if "401" in str(loop_err) or "token" in str(loop_err).lower():
                logging.warning("Ogiltigförklarar token pga fel i huvudloop."); ACCESS_TOKEN = None 
        sleep_interval = 30
        logging.info(f"Sover i {sleep_interval} sekunder..."); time.sleep(sleep_interval)
    