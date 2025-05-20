import requests # For Graph API calls
import msal     # For Azure AD authentication
import email # Still useful for parsing some structures if needed, less so for Graph
from email.message import EmailMessage # Less needed for Graph
from email.header import decode_header, make_header # For subject decoding if needed
import email.utils # For parsing addresses, less for Graph direct use
import time
import os
import logging
import sqlite3
import datetime
import random
import json

import ollama
from dotenv import load_dotenv

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

# --- Load .env variables ---
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
if os.path.exists(dotenv_path):
    logging.info(f"DEBUG: Loading .env from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path, override=True)
else:
    logging.warning(f"DEBUG: .env file NOT found at {dotenv_path}. Trying default load_dotenv().")
    load_dotenv(override=True) # Fallback

# --- Configuration ---
# Graph API Config (from .env)
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
# BOT_EMAIL_ADDRESS is the User UPN/ID for Graph API calls (e.g., ulla@movant.org)
TARGET_USER_GRAPH_ID = os.getenv('BOT_EMAIL_ADDRESS') # This is Ulla's email/ID

# Ollama Config
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')
OLLAMA_HOST = os.getenv('OLLAMA_HOST')

logging.info("Miljövariabler inlästa (eller försökt läsas).")

# --- Validate Critical Graph API Config ---
if not all([AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET, TARGET_USER_GRAPH_ID]):
    logging.critical("Saknar kritisk Graph API-konfiguration i .env: AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET, BOT_EMAIL_ADDRESS.")
    exit("FEL: Graph API-konfiguration ofullständig. Avslutar.")

# --- Ollama Client Arguments ---
ollama_client_args = {}
if OLLAMA_HOST:
    ollama_client_args['host'] = OLLAMA_HOST
    logging.info(f"Ollama-klient konfigurerad för värd: {OLLAMA_HOST}")

# --- Constants ---
DB_FILE = 'ulla_conversations.db'
RUN_EMAIL_BOT = True
START_COMMAND_SUBJECT = "starta övning"

# --- Microsoft Graph API Configuration ---
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
GRAPH_SCOPES = ['https://graph.microsoft.com/.default'] # For Client Credentials
MSAL_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
MSAL_APP = None # Will be initialized
ACCESS_TOKEN = None # Global to store current token

# --- Persona and Problem Catalog (Keep as is) ---
ULLA_PERSONA_PROMPT = """...""" # Your existing prompt
PROBLEM_KATALOG = [ ... ] # Your existing catalog

# --- Database Functions (Keep as is, but ensure DB_FILE is used) ---
# init_db, start_new_conversation, get_active_conversation,
# update_conversation_history, delete_conversation
# (No changes needed to their internal logic, just the DB_FILE constant name)
def init_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE) # Use the new DB_FILE
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_conversations (
                student_email TEXT PRIMARY KEY,
                problem_id TEXT NOT NULL,
                problem_description TEXT NOT NULL,
                correct_solution_keywords TEXT NOT NULL,
                conversation_history TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                graph_conversation_id TEXT DEFAULT NULL -- Optional: Store Graph Conversation ID
            )
        ''')
        conn.commit()
        logging.info(f"Databas {DB_FILE} initierad/kontrollerad.")
    except sqlite3.Error as e:
        logging.critical(f"Databasinitiering misslyckades: {e}", exc_info=True); raise
    finally:
        if conn: conn.close()

# ... (other DB functions: start_new_conversation, get_active_conversation, etc. are fine) ...
def start_new_conversation(student_email, problem, graph_conversation_id=None): # Added graph_conversation_id
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now()
        initial_history = [{'role': 'assistant', 'content': problem['start_prompt']}]
        history_json = json.dumps(initial_history)
        cursor.execute('''
            REPLACE INTO active_conversations
            (student_email, problem_id, problem_description, correct_solution_keywords, conversation_history, created_at, last_update, graph_conversation_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_email, problem['id'], problem['beskrivning'], json.dumps(problem['losning_nyckelord']), history_json, timestamp, timestamp, graph_conversation_id))
        conn.commit()
        logging.info(f"Startade/ersatte konversation för {student_email} med problem {problem['id']}")
        return True
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid start av konv. för {student_email}: {e}", exc_info=True)
        return False
    finally:
        if conn: conn.close()

def get_active_conversation(student_email):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT problem_id, problem_description, correct_solution_keywords, conversation_history, graph_conversation_id
            FROM active_conversations
            WHERE student_email = ?
        ''', (student_email,))
        row = cursor.fetchone()
        if row:
            logging.info(f"Hittade aktiv konversation för {student_email}")
            history = json.loads(row['conversation_history'])
            problem_info = {
                'id': row['problem_id'],
                'beskrivning': row['problem_description'],
                'losning_nyckelord': json.loads(row['correct_solution_keywords']) # Assuming keywords stored as JSON string
            }
            graph_convo_id = row['graph_conversation_id']
            return history, problem_info, graph_convo_id
        return None, None, None
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid hämtning av konv. för {student_email}: {e}", exc_info=True)
        return None, None, None
    except json.JSONDecodeError as e:
         logging.error(f"JSON-avkodningsfel för {student_email}: {e}", exc_info=True)
         return None, None, None
    finally:
        if conn: conn.close()

def update_conversation_history(student_email, history, graph_conversation_id=None): # Added graph_convo_id
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        history_json = json.dumps(history)
        timestamp = datetime.datetime.now()
        if graph_conversation_id: # Only update if provided
            cursor.execute('''
                UPDATE active_conversations
                SET conversation_history = ?, last_update = ?, graph_conversation_id = ?
                WHERE student_email = ?
            ''', (history_json, timestamp, graph_conversation_id, student_email))
        else:
             cursor.execute('''
                UPDATE active_conversations
                SET conversation_history = ?, last_update = ?
                WHERE student_email = ?
            ''', (history_json, timestamp, student_email))
        conn.commit()
        logging.info(f"Uppdaterade konversationshistorik för {student_email}")
        return True
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid uppdatering av historik för {student_email}: {e}", exc_info=True)
        return False
    finally:
        if conn: conn.close()

def delete_conversation(student_email):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM active_conversations WHERE student_email = ?', (student_email,))
        conn.commit()
        if cursor.rowcount > 0: logging.info(f"Raderade avslutad konversation för {student_email}"); return True
        logging.warning(f"Försökte radera konversation för {student_email}, men ingen hittades."); return False
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid radering av konversation för {student_email}: {e}", exc_info=True); return False
    finally:
        if conn: conn.close()

# --- LLM Interaction (Keep as is) ---
# get_llm_response_with_history
def get_llm_response_with_history(student_email, history, problem_info):
    """Gets LLM response considering history and precise evaluation task, using clearer marker logic."""
    if not OLLAMA_MODEL:
        logging.error("OLLAMA_MODEL miljövariabel ej satt.")
        return "Nej men kära nån, nu tappade jag tråden helt...", False

    latest_student_message = history[-1]['content'] if history and history[-1]['role'] == 'user' else "[INGET SENASTE MEDDELANDE]"
    logging.info(f"Hämtar LLM-svar för {student_email} (modell: {OLLAMA_MODEL})")

    system_prompt_combined = f"""{ULLA_PERSONA_PROMPT}
Ditt nuvarande specifika tekniska problem är: {problem_info['beskrivning']}
Den korrekta tekniska lösningen innefattar specifikt dessa idéer/nyckelord: {problem_info['losning_nyckelord']}
Du ska utvärdera studentens senaste e-postmeddelande baserat på konversationshistoriken och den exakta korrekta lösningen."""
    evaluation_prompt = f"""Här är det senaste meddelandet från studenten:
---
{latest_student_message}
---
**Utvärdering:** Har studenten i detta senaste meddelande föreslagit den specifika korrekta lösningen relaterad till '{problem_info['losning_nyckelord']}'?
**Instruktion för ditt svar:**
1.  Skriv *först*, på en helt egen rad och utan någon annan text på den raden, antingen `[LÖST]` eller `[EJ_LÖST]`.
2.  Börja sedan på en *ny rad* och skriv ditt svar *som Ulla*.
"""
    messages = [{'role': 'system', 'content': system_prompt_combined}]
    messages.extend(history[:-1])
    messages.append({'role': 'user', 'content': evaluation_prompt})

    try:
        response = ollama.chat(model=OLLAMA_MODEL, messages=messages, options={'temperature': 0.7, 'num_predict': 300}, **ollama_client_args)
        raw_reply = response['message']['content'].strip()
        lines = raw_reply.split('\n', 1)
        marker = lines[0].strip()
        is_solved = (marker == "[LÖST]")
        Ulla_reply = lines[1].strip() if len(lines) > 1 else ("Åh, tack!" if is_solved else "Jaha du...")
        Ulla_reply = Ulla_reply.replace("[LÖST]", "").replace("[EJ_LÖST]", "").strip()
        if not Ulla_reply: Ulla_reply = "Åh, tack!" if is_solved else "Jaha du..."
        logging.info(f"LLM genererade svar för {student_email}. Marker: {marker}. Löst: {is_solved}")
        return Ulla_reply, is_solved
    except Exception as e:
        logging.error(f"Fel vid anrop av Ollama för {student_email}: {e}", exc_info=True)
        return "Nej, nu vet jag inte vad jag ska ta mig till...", False

# --- Graph API Helper Functions ---
def get_graph_token():
    """Acquires and returns an access token for Microsoft Graph using Client Credentials."""
    global MSAL_APP, ACCESS_TOKEN
    if MSAL_APP is None:
        MSAL_APP = msal.ConfidentialClientApplication(
            AZURE_CLIENT_ID, authority=MSAL_AUTHORITY, client_credential=AZURE_CLIENT_SECRET
        )

    # Try to get a token from MSAL's internal cache first
    token_result = MSAL_APP.acquire_token_silent(GRAPH_SCOPES, account=None)

    if not token_result:
        logging.info("Inget giltigt Graph API-token i cache, hämtar nytt.")
        token_result = MSAL_APP.acquire_token_for_client(scopes=GRAPH_SCOPES)

    if "access_token" in token_result:
        ACCESS_TOKEN = token_result['access_token']
        # logging.debug("Graph API-token förnyat/hämtat.")
        return ACCESS_TOKEN
    else:
        logging.error(f"Misslyckades hämta Graph API-token: {token_result.get('error_description')}")
        ACCESS_TOKEN = None
        return None

      
def make_graph_api_call(method, endpoint_suffix, data=None, params=None, headers_extra=None):
    """Makes a generic Graph API call and handles token refresh."""
    global ACCESS_TOKEN # <--- ADD THIS LINE to indicate modification of the global
    
    # Initial check and token acquisition
    # This logic should be robust: if token is None or expired, get a new one.
    if ACCESS_TOKEN is None or jwt_is_expired(ACCESS_TOKEN):
        logging.info("ACCESS_TOKEN is None or expired, attempting to get/refresh.")
        if not get_graph_token(): # get_graph_token will update the global ACCESS_TOKEN
            logging.error("Failed to get/refresh token in make_graph_api_call. Cannot proceed.")
            return None # Could not get token

    # Now ACCESS_TOKEN should be valid if get_graph_token() succeeded
    if ACCESS_TOKEN is None: # Double check in case get_graph_token failed silently (it shouldn't)
        logging.error("ACCESS_TOKEN is still None after get_graph_token attempt.")
        return None

    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN, 'Content-Type': 'application/json'}
    if headers_extra:
        headers.update(headers_extra)

    url = f"{GRAPH_API_ENDPOINT}{endpoint_suffix}"
    try:
        logging.debug(f"Graph API-anrop: {method} {url} | Params: {params} | Data: {json.dumps(data)[:200] if data else 'None'}")
        response = requests.request(method, url, headers=headers, json=data, params=params, timeout=30)
        response.raise_for_status() 

        if response.status_code == 204 or response.status_code == 202: 
            return True 
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401: 
            logging.warning("Graph API returnerade 401 (Unauthorized). Invalidating local token to force refresh on next attempt.")
            ACCESS_TOKEN = None # Invalidate the global token so get_graph_token is called next time
                                # This makes this function aware it's modifying the global
        error_details = "Okänd felstruktur."
        try: error_details = e.response.json().get("error", {}).get("message", e.response.text)
        except json.JSONDecodeError: error_details = e.response.text
        logging.error(f"Graph API HTTP-fel: {e.response.status_code} - {error_details} för {method} {url}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Graph API anropsfel: {e} för {method} {url}", exc_info=True)
        return None

    

def jwt_is_expired(token_str):
    """Rudimentary check if JWT is expired. MSAL handles this better."""
    try:
        # Payload is the middle part of token.data.token
        payload_str = token_str.split('.')[1]
        # Add padding if necessary for base64.urlsafe_b64decode
        payload_str += '=' * (-len(payload_str) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_str).decode())
        return payload.get('exp', 0) < time.time()
    except Exception:
        return True # Assume expired if parsing fails

import base64 # For jwt_is_expired

# --- Graph API Email Functions ---
def graph_send_email(recipient_email, subject, body_content, in_reply_to_message_id=None, references_header=None, conversation_id=None):
    """Sends an email using Microsoft Graph API."""
    message_payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text", # Or "HTML"
                "content": body_content
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient_email}}
            ]
        },
        "saveToSentItems": "true"
    }

    # Threading: Graph API uses 'internetMessageHeaders' for In-Reply-To and References
    # Or directly set conversationId
    headers_list = []
    if in_reply_to_message_id:
        headers_list.append({"name": "In-Reply-To", "value": in_reply_to_message_id})
    if references_header:
        headers_list.append({"name": "References", "value": references_header})
    # If you want to link by conversationId, ensure the original email's conversationId is used
    if conversation_id:
         message_payload["message"]["conversationId"] = conversation_id
    if headers_list:
        message_payload["message"]["internetMessageHeaders"] = headers_list


    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/sendMail"
    logging.info(f"Skickar e-post via Graph till: {recipient_email} | Ämne: {subject}")
    response = make_graph_api_call("POST", endpoint, data=message_payload)

    if response is True: # sendMail returns 202 Accepted, no body. make_graph_api_call returns True.
        logging.info("E-post skickat framgångsrikt via Graph API.")
        return True # Indicate success (no message ID from sendMail directly)
    else:
        logging.error("Misslyckades skicka e-post via Graph API.")
        return False


def graph_check_emails():
    """Checks for new unread emails using Graph API."""
    # Get unread messages from Inbox
    # Select only necessary fields to reduce payload size
    select_fields = "id,subject,from,sender,toRecipients,receivedDateTime,bodyPreview,body,internetMessageId,conversationId,references,isRead"
    params = {
        "$filter": "isRead eq false",
        "$select": select_fields,
        "$orderby": "receivedDateTime asc" # Process oldest first
    }
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/mailFolders/inbox/messages"
    logging.info("Söker efter olästa e-postmeddelanden via Graph API...")
    response_data = make_graph_api_call("GET", endpoint, params=params)

    if not response_data or "value" not in response_data:
        if response_data is None: logging.warning("Ingen data eller fel vid hämtning av e-post från Graph.")
        else: logging.info("Inga olästa e-postmeddelanden hittades i inkorgen (Graph).")
        return

    unread_messages = response_data["value"]
    if not unread_messages:
        logging.info("Inga olästa e-postmeddelanden hittades i inkorgen (Graph).")
        return

    logging.info(f"Hittade {len(unread_messages)} olästa e-postmeddelanden via Graph.")
    processed_graph_ids = set()

    for msg_graph in unread_messages:
        graph_message_id = msg_graph.get('id')
        logging.info(f"--- Bearbetar Graph e-post ID: {graph_message_id} ---")

        try:
            subject = msg_graph.get('subject', "[Inget ämne]")
            sender_info = msg_graph.get('from') or msg_graph.get('sender') # 'from' for sent, 'sender' for received
            sender_email = sender_info.get('emailAddress', {}).get('address', '').lower() if sender_info else ''
            # Graph provides internetMessageId, conversationId, references directly
            internet_message_id = msg_graph.get('internetMessageId') # This is the <foo@bar.com> style ID
            references = msg_graph.get('references') # This is a string of message IDs
            graph_conversation_id = msg_graph.get('conversationId')

            logging.info(f"Från: {sender_email} | Ämne: {subject} | Graph ID: {graph_message_id} | Internet Msg ID: {internet_message_id}")

            if not sender_email or sender_email == TARGET_USER_GRAPH_ID.lower() or 'mailer-daemon' in sender_email or 'noreply' in sender_email:
                logging.warning(f"Skippar e-post ID {graph_message_id} (själv, studs, no-reply). Markerar som läst.")
                mark_email_as_read(graph_message_id)
                processed_graph_ids.add(graph_message_id)
                continue

            # Extract body - Graph API provides 'body' object with 'content' and 'contentType'
            email_body_graph = msg_graph.get('body', {}).get('content', '')
            if msg_graph.get('body', {}).get('contentType', '').lower() == 'html':
                # Basic HTML to text conversion (consider a library like beautifulsoup for complex HTML)
                # For now, a simple placeholder or just use bodyPreview
                logging.debug(f"Meddelande {graph_message_id} är HTML, använder bodyPreview eller rå HTML.")
                # A more robust solution for HTML to text:
                # from bs4 import BeautifulSoup
                # soup = BeautifulSoup(email_body_graph, "html.parser")
                # email_body_text = soup.get_text()
                # For now, let's assume plain text or simple HTML that might work, or use bodyPreview
                email_body_text = msg_graph.get('bodyPreview', email_body_graph) # Fallback to bodyPreview or raw content
            else: # Plain text
                email_body_text = email_body_graph

            # Clean the body (your existing logic)
            cleaned_body = "\n".join([line for line in email_body_text.splitlines() if not line.strip().startswith('>')])
            cleaned_body = "\n".join([line for line in cleaned_body.splitlines() if not (line.strip().lower().startswith('de ') and ('skrev:' in line.lower() or 'wrote:' in line.lower()))])
            cleaned_body = "\n".join([line for line in cleaned_body.splitlines() if not (line.strip().lower().startswith('on ') and 'wrote:' in line.lower())])
            email_body_final = cleaned_body.strip()


            if not email_body_final:
                logging.warning(f"E-posttext tom efter rensning för Graph ID {graph_message_id}. Markerar som läst.")
                mark_email_as_read(graph_message_id)
                processed_graph_ids.add(graph_message_id)
                continue

            # --- State Logic ---
            history, problem_info, existing_graph_convo_id = get_active_conversation(sender_email)

            if history and problem_info:
                logging.info(f"E-post {graph_message_id} tillhör aktiv konversation för {sender_email}")
                history.append({'role': 'user', 'content': email_body_final})
                reply_body, is_solved = get_llm_response_with_history(sender_email, history, problem_info)

                if reply_body:
                    # For threading, pass the incoming email's internetMessageId as In-Reply-To
                    # and its references. Also, use the graph_conversation_id.
                    current_convo_id_for_reply = graph_conversation_id or existing_graph_convo_id
                    if graph_send_email(sender_email, subject, reply_body, internet_message_id, references, current_convo_id_for_reply):
                        history.append({'role': 'assistant', 'content': reply_body})
                        if is_solved:
                            delete_conversation(sender_email)
                        else:
                            update_conversation_history(sender_email, history, current_convo_id_for_reply)
                        mark_email_as_read(graph_message_id)
                        processed_graph_ids.add(graph_message_id)
                        logging.info(f"Bearbetat och svarat på Graph e-post {graph_message_id} för {sender_email}.")
                    else:
                         logging.error(f"Misslyckades skicka svar för {sender_email} (Graph ID {graph_message_id}). Studentens e-post INTE markerad som läst.")
                else:
                    logging.error(f"Misslyckades få LLM-svar för {sender_email} (Graph ID {graph_message_id}). Studentens e-post INTE markerad som läst.")
            else: # No Active Conversation
                if subject and START_COMMAND_SUBJECT in subject.lower():
                    logging.info(f"Mottog startkommando från {sender_email} (Ämne: '{subject}') (Graph ID {graph_message_id})")
                    problem = random.choice(PROBLEM_KATALOG)
                    # Pass the graph_conversation_id of the incoming email to link them
                    if start_new_conversation(sender_email, problem, graph_conversation_id):
                        initial_reply_body = problem['start_prompt']
                        # When starting a new thread, no in_reply_to_message_id or references.
                        # But we can use the graph_conversation_id from the student's initiating email.
                        if graph_send_email(sender_email, subject, initial_reply_body, conversation_id=graph_conversation_id):
                            logging.info(f"Skickade initial problembeskrivning till {sender_email} (Graph)")
                            mark_email_as_read(graph_message_id)
                            processed_graph_ids.add(graph_message_id)
                        else:
                            logging.error(f"Misslyckades skicka initialt problem till {sender_email} (Graph). Startkommando {graph_message_id} INTE markerat som läst.")
                            delete_conversation(sender_email) # Rollback DB entry
                    else:
                         logging.error(f"Misslyckades skapa ny konversation i DB för {sender_email} (Graph). Startkommando {graph_message_id} INTE markerat som läst.")
                else:
                    logging.warning(f"Mottog Graph e-post {graph_message_id} från {sender_email} - ej aktiv konversation eller startkommando. Ignorerar. Markerar som läst.")
                    mark_email_as_read(graph_message_id)
                    processed_graph_ids.add(graph_message_id)

        except Exception as processing_error:
             logging.error(f"Ohanterat fel vid bearbetning av Graph e-post ID {graph_message_id}: {processing_error}", exc_info=True)
             # Consider not marking as read to allow retry on next cycle

    logging.info(f"Avslutade Graph e-postbearbetning. {len(processed_graph_ids)} e-postmeddelanden bearbetades framgångsrikt.")


def mark_email_as_read(graph_message_id):
    """Marks an email as read using Graph API."""
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/messages/{graph_message_id}"
    payload = {"isRead": True}
    logging.info(f"Markerar Graph e-post {graph_message_id} som läst...")
    if make_graph_api_call("PATCH", endpoint, data=payload):
        logging.info(f"Graph e-post {graph_message_id} markerad som läst.")
    else:
        logging.error(f"Misslyckades markera Graph e-post {graph_message_id} som läst.")


# --- Main Execution Block ---
if __name__ == "__main__":
    logging.info("Script startat (Graph API-version).")

    if RUN_EMAIL_BOT:
        logging.info("--- Kör i E-post Bot-läge (Graph API) ---")
        if not OLLAMA_MODEL:
            logging.critical("Saknar OLLAMA_MODEL. Avslutar.")
            exit("FEL: Konfiguration ofullständig.")

        try: init_db()
        except Exception as db_err: logging.critical(f"Misslyckades initiera databas: {db_err}. Avslutar."); exit(1)

        try: # Verify Ollama
            logging.info(f"Kontrollerar anslutning till Ollama och modell '{OLLAMA_MODEL}'...")
            ollama.show(OLLAMA_MODEL, **ollama_client_args)
            logging.info(f"Ansluten till Ollama och modell '{OLLAMA_MODEL}' hittad.")
        except Exception as ollama_err:
            logging.critical(f"Ollama Fel: {ollama_err}"); exit("FEL: Ollama-anslutning/-modell misslyckades.")

        # Initial token acquisition
        if not get_graph_token():
            logging.critical("Misslyckades hämta initialt Graph API-token. Kontrollera Azure AD-konfiguration. Avslutar.")
            exit("FEL: Graph API-autentisering misslyckades.")

        logging.info("Startar huvudloop för Graph e-postkontroll...")
        while True:
            try:
                graph_check_emails()
            except Exception as loop_err:
                logging.error(f"Kritiskt fel i huvudloop (Graph): {loop_err}", exc_info=True)
                # Potentially re-acquire token if it's an auth issue not caught deeper
                if "401" in str(loop_err) or "token" in str(loop_err).lower():
                    logging.warning("Försöker förnya Graph-token efter fel i huvudloop.")
                    get_graph_token()


            sleep_interval = 60
            logging.info(f"Sover i {sleep_interval} sekunder...")
            time.sleep(sleep_interval)
    else:
        # --- Command-Line Test Mode (Remains largely the same as it doesn't use email sending/receiving) ---
        logging.info(f"--- Kör i Kommandorads Testläge (Modell: {OLLAMA_MODEL}) ---")
        # ... (Your existing CLI test mode code can be pasted here, it's independent of email protocol) ...
        logging.info(f"--- Kör i Kommandorads Testläge (Modell: {OLLAMA_MODEL}) ---")
        logging.info("Detta läge simulerar konversationer utan e-post. Skriv 'quit' för att avsluta.")

        if not OLLAMA_MODEL: logging.critical("OLLAMA_MODEL ej satt i .env."); exit(1)
        try: ollama.list(**ollama_client_args); logging.info("Ansluten till Ollama.")
        except Exception as e: logging.critical(f"Kunde ej ansluta till Ollama: {e}"); exit(1)

        test_student_email = "test.student@example.com"
        test_history = []
        problem = random.choice(PROBLEM_KATALOG)
        test_problem_info = {
            'id': problem['id'],
            'beskrivning': problem['beskrivning'],
            'losning_nyckelord': problem['losning_nyckelord'] # Assuming this is already a list
        }
        print(f"\n--- Startar Testscenario ---")
        print(f"Ullas Problem: {test_problem_info['beskrivning']}")
        print(f"(Lösningsledtråd: {test_problem_info['losning_nyckelord']})") # Assuming this is already a list
        print(f"Ullas Startmeddelande:\n{problem['start_prompt']}\n")
        test_history.append({'role': 'assistant', 'content': problem['start_prompt']})

        while True:
            try:
                user_input = input(f"Studentens Svar ({test_student_email}) > ")
                if user_input.lower() == 'quit': break
                if not user_input: continue
                test_history.append({'role': 'user', 'content': user_input})
                Ulla_response, is_solved = get_llm_response_with_history(test_student_email, test_history, test_problem_info)
                print("\n--- Ullas Svar ---"); print(Ulla_response); print("--------------------\n")
                test_history.append({'role': 'assistant', 'content': Ulla_response})
                if is_solved:
                    print("--- Scenario LÖST! Startar nytt scenario. ---")
                    test_history = []
                    problem = random.choice(PROBLEM_KATALOG)
                    test_problem_info = { 'id': problem['id'], 'beskrivning': problem['beskrivning'], 'losning_nyckelord': problem['losning_nyckelord'] }
                    print(f"\n--- Startar Testscenario ---")
                    print(f"Ullas Problem: {test_problem_info['beskrivning']}")
                    print(f"(Lösningsledtråd: {test_problem_info['losning_nyckelord']})")
                    print(f"Ullas Startmeddelande:\n{problem['start_prompt']}\n")
                    test_history.append({'role': 'assistant', 'content': problem['start_prompt']})
            except KeyboardInterrupt: print("\nAvslutar testläge."); break
            except Exception as test_err: logging.error(f"Fel under CLI-test: {test_err}", exc_info=True); time.sleep(1)
        logging.info("--- Avslutade Kommandorads Testläge ---")


    logging.info("Script avslutat.")