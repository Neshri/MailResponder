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
from prompts import ULLA_PERSONA_PROMPT, PROBLEM_KATALOG
# Ollama will only be imported if RUN_EMAIL_BOT is True to avoid error if not installed in read-only mode
ollama = None

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
    logging.critical("Saknar kritisk Graph API-konfiguration i .env.")
    exit("FEL: Graph API-konfiguration ofullständig.")

ollama_client_args = {}
if OLLAMA_HOST:
    ollama_client_args['host'] = OLLAMA_HOST
    logging.info(f"Ollama-klient konfigurerad för värd: {OLLAMA_HOST}")

DB_FILE = 'conversations.db' # New DB name
RUN_EMAIL_BOT = True # <--- SET TO True FOR FULL BOT, False FOR READ-ONLY
START_COMMAND_SUBJECT = "starta övning"

GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
GRAPH_SCOPES = ['https://graph.microsoft.com/.default']
MSAL_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
MSAL_APP = None
ACCESS_TOKEN = None

# --- Database Functions (Modified for single string history) ---
def init_db():
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_conversations (
                student_email TEXT PRIMARY KEY,
                problem_id TEXT NOT NULL,
                problem_description TEXT NOT NULL,
                correct_solution_keywords TEXT NOT NULL, -- Stored as JSON string
                conversation_history TEXT NOT NULL,    -- NOW A SINGLE STRING
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                graph_conversation_id TEXT DEFAULT NULL
            )
        ''')
        conn.commit()
        logging.info(f"Databas {DB_FILE} initierad/kontrollerad.")
    except sqlite3.Error as e:
        logging.critical(f"Databasinitiering misslyckades: {e}", exc_info=True); raise
    finally:
        if conn: conn.close()

def start_new_conversation(student_email, problem, graph_conversation_id=None):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now()
        # Initial history is Ulla's first prompt as a single string
        initial_history_string = f"Ulla: {problem['start_prompt']}\n\n"
        keywords_json = json.dumps(problem['losning_nyckelord'])

        cursor.execute('''
            REPLACE INTO active_conversations
            (student_email, problem_id, problem_description, correct_solution_keywords, conversation_history, created_at, last_update, graph_conversation_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_email, problem['id'], problem['beskrivning'], keywords_json, initial_history_string, timestamp, timestamp, graph_conversation_id))
        conn.commit()
        logging.info(f"Startade/ersatte konversation för {student_email} med problem {problem['id']}")
        return True
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid start av konv. för {student_email}: {e}", exc_info=True); return False
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
            # conversation_history is now a direct string
            history_string = row['conversation_history']
            problem_info = {
                'id': row['problem_id'],
                'beskrivning': row['problem_description'],
                'losning_nyckelord': json.loads(row['correct_solution_keywords'])
            }
            graph_convo_id = row['graph_conversation_id']
            return history_string, problem_info, graph_convo_id # Return string history
        return None, None, None
    except (sqlite3.Error, json.JSONDecodeError) as e: # JSONDecodeError for keywords
        logging.error(f"Fel vid hämtning/avkodning av konv. för {student_email}: {e}", exc_info=True)
        return None, None, None
    finally:
        if conn: conn.close()

def update_conversation_history(student_email, new_entry_string, graph_conversation_id_to_set=None):
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now()
        
        # Append new entry to existing history string
        # Ensure there's a newline separator if history isn't empty
        # And that new_entry_string also ends with newlines for future appends
        if not new_entry_string.endswith("\n\n"):
            new_entry_string += "\n\n"

        if graph_conversation_id_to_set is not None:
            cursor.execute('''
                UPDATE active_conversations
                SET conversation_history = conversation_history || ?, 
                    last_update = ?,
                    graph_conversation_id = ?
                WHERE student_email = ?
            ''', (new_entry_string, timestamp, graph_conversation_id_to_set, student_email))
        else:
            cursor.execute('''
                UPDATE active_conversations
                SET conversation_history = conversation_history || ?, 
                    last_update = ?
                WHERE student_email = ?
            ''', (new_entry_string, timestamp, student_email))
        conn.commit()
        logging.info(f"Uppdaterade konversationshistorik (string) för {student_email}")
        return True
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid uppdatering av string-historik för {student_email}: {e}", exc_info=True)
        return False
    finally:
        if conn: conn.close()

def delete_conversation(student_email): # Unchanged
    # ... (same as your existing delete_conversation) ...
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM active_conversations WHERE student_email = ?', (student_email,))
        conn.commit()
        if cursor.rowcount > 0: logging.info(f"Raderade avslutad konversation för {student_email}"); return True
        return False
    except sqlite3.Error as e:
        logging.error(f"DB-fel vid radering av konversation för {student_email}: {e}", exc_info=True); return False
    finally:
        if conn: conn.close()

# --- LLM Interaction (Modified for detailed logging) ---
def get_llm_response_with_history(student_email, full_history_string, problem_info, latest_student_message_cleaned):
    global ollama # To access the imported module
    if not OLLAMA_MODEL:
        logging.error("OLLAMA_MODEL miljövariabel ej satt.")
        return "Nej men kära nån, nu tappade jag tråden helt...", False

    logging.info(f"Hämtar LLM-svar för {student_email} (modell: {OLLAMA_MODEL})")

    persona_with_history_awareness = f"""{ULLA_PERSONA_PROMPT}
Du har haft följande konversation hittills (senaste meddelandet från studenten är inkluderat i slutet av detta):
--- KONVERSATIONSHISTORIK ---
{full_history_string}
--- SLUT KONVERSATIONSHISTORIK ---
"""

    system_prompt_combined = f"""{persona_with_history_awareness}
Ditt nuvarande specifika tekniska problem är: {problem_info['beskrivning']}
Den korrekta tekniska lösningen innefattar specifikt dessa idéer/nyckelord: {problem_info['losning_nyckelord']}
Du ska utvärdera studentens SENASTE meddelande (som är det sista "Support:"-meddelandet i historiken ovan) baserat på denna historik och den exakta korrekta lösningen."""

    evaluation_prompt = f"""**Utvärdering:** Har studenten i sitt SENASTE meddelande (det sista "Support:"-meddelandet i historiken ovan) föreslagit den specifika korrekta lösningen relaterad till '{problem_info['losning_nyckelord']}'? (Analysera mot *exakta* nyckelord/koncept. Generella IT-råd är fel om de inte direkt adresserar nyckelorden.)
**Instruktion för ditt svar:**
1. Skriv *först*, på en helt egen rad och utan någon annan text på den raden, antingen `[LÖST]` eller `[EJ_LÖST]`.\n2. Börja sedan på en *ny rad* och skriv ditt svar *som Ulla*.
"""
    
    messages_for_ollama = [
        {'role': 'system', 'content': system_prompt_combined},
        {'role': 'user', 'content': evaluation_prompt} 
    ]

    # --- DETAILED LOGGING OF LLM INTERACTION ---
    try:
        # Log the exact messages being sent to Ollama
        # For readability, pretty-print the JSON structure of messages_for_ollama
        # Be cautious with logging very long histories in production, but good for debug.
        logging.info(f"--- MEDDELANDE TILL OLLAMA (för {student_email}) ---")
        try:
            # Attempt to pretty print the JSON for better log readability
            pretty_messages = json.dumps(messages_for_ollama, indent=2, ensure_ascii=False)
            logging.info(f"\n{pretty_messages}")
        except TypeError: # In case some part is not serializable, log as is
            logging.info(str(messages_for_ollama))
        logging.info("--- SLUT MEDDELANDE TILL OLLAMA ---")

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages_for_ollama,
            options={'temperature': 0.7, 'num_predict': 1000}, # Adjust num_predict if needed
            **ollama_client_args
        )
        raw_reply_from_llm = response['message']['content'] # Get the raw string

        # Log the exact raw reply from Ollama BEFORE any cleaning/splitting
        logging.info(f"--- RÅTT SVAR FRÅN OLLAMA (för {student_email}) ---")
        logging.info(f"\n{raw_reply_from_llm}")
        logging.info("--- SLUT RÅTT SVAR FRÅN OLLAMA ---")
        
        # Proceed with parsing the raw reply
        processed_reply = raw_reply_from_llm.strip() # Basic strip first
        lines = processed_reply.split('\n', 1) 
        marker = lines[0].strip()
        is_solved = (marker == "[LÖST]")
        
        if len(lines) > 1:
            ulla_reply = lines[1].strip()
            # Remove markers if they somehow leak into Ulla's part AFTER the first line
            ulla_reply = ulla_reply.replace("[LÖST]", "").replace("[EJ_LÖST]", "").strip()
        elif is_solved: 
            ulla_reply = "Åh, tack snälla du, nu fungerar det visst!"
            logging.warning(f"LLM returnerade bara LÖST-markör för {student_email}. Använder reservsvar.")
        else: # EJ_LÖST or unexpected marker/text is returned as the only line
            ulla_reply = "Jaha ja, jag är inte riktigt säker på vad jag ska göra nu..."
            logging.warning(f"LLM returnerade bara EJ_LÖST-markör eller oväntat/kort svar för {student_email}. Använder reservsvar.")
            is_solved = False # Ensure is_solved is False if marker wasn't exactly [LÖST]

        if not ulla_reply: # If Ulla's reply ended up empty after processing
             ulla_reply = "Åh, tack snälla du, nu fungerar det visst!" if is_solved else "Jaha ja, jag är inte riktigt säker på vad jag ska göra nu..."
             logging.warning(f"Ullas svar var tomt efter bearbetning för {student_email}. Använder reservsvar.")

        logging.info(f"LLM genererade svar för {student_email}. Rå marker: '{marker}'. Tolkat som löst: {is_solved}. Ullas svar: '{ulla_reply[:100]}...'")
        return ulla_reply, is_solved
        
    except ollama.ResponseError as e:
         logging.error(f"Ollama API-fel för {student_email}: {e.error} (Status: {e.status_code})", exc_info=True)
         return "Nej men kära nån, nu krånglar min tankeverksamhet...", False
    except ConnectionRefusedError:
         logging.error(f"Kunde inte ansluta till Ollama-servern ({ollama_client_args.get('host', 'http://localhost:11434')}). Kör Ollama?")
         return "Det verkar vara upptaget i ledningen just nu...", False
    except Exception as e: # Catch any other exceptions during the LLM call or processing
        logging.error(f"Oväntat fel vid anrop av Ollama LLM för {student_email}: {e}", exc_info=True)
        return "Nej, nu vet jag inte vad jag ska ta mig till...", False

# ... (rest of your script, including the main block, database functions, Graph API functions, etc.)


# --- Graph API Helper Functions (msal + requests) ---
def get_graph_token():
    global MSAL_APP, ACCESS_TOKEN
    if MSAL_APP is None:
        MSAL_APP = msal.ConfidentialClientApplication(
            AZURE_CLIENT_ID, authority=MSAL_AUTHORITY, client_credential=AZURE_CLIENT_SECRET
        )
    token_result = MSAL_APP.acquire_token_silent(GRAPH_SCOPES, account=None)
    if not token_result:
        logging.info("Inget giltigt Graph API-token i cache, hämtar nytt.")
        token_result = MSAL_APP.acquire_token_for_client(scopes=GRAPH_SCOPES)
    if "access_token" in token_result:
        ACCESS_TOKEN = token_result['access_token']
        return ACCESS_TOKEN
    else:
        logging.error(f"Misslyckades hämta Graph API-token: {token_result.get('error_description')}")
        ACCESS_TOKEN = None; return None

def jwt_is_expired(token_str):
    if not token_str: return True
    try:
        payload_str = token_str.split('.')[1]; payload_str += '=' * (-len(payload_str) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_str).decode())
        return payload.get('exp', 0) < time.time()
    except Exception: return True

def make_graph_api_call(method, endpoint_suffix, data=None, params=None, headers_extra=None):
    global ACCESS_TOKEN
    if ACCESS_TOKEN is None or jwt_is_expired(ACCESS_TOKEN):
        logging.info("ACCESS_TOKEN är None eller utgånget, försöker hämta/förnya.")
        if not get_graph_token(): logging.error("Misslyckades hämta/förnya token."); return None
    if ACCESS_TOKEN is None: logging.error("ACCESS_TOKEN fortfarande None."); return None
    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN, 'Content-Type': 'application/json'}
    if headers_extra: headers.update(headers_extra)
    url = f"{GRAPH_API_ENDPOINT}{endpoint_suffix}"
    try:
        response = requests.request(method, url, headers=headers, json=data, params=params, timeout=30)
        response.raise_for_status()
        if response.status_code in [202, 204]: return True
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logging.warning("Graph API 401 (Unauthorized). Ogiltigförklarar token."); ACCESS_TOKEN = None
        err_details = "Okänd felstruktur."
        try: err_details = e.response.json().get("error", {}).get("message", e.response.text)
        except json.JSONDecodeError: err_details = e.response.text
        logging.error(f"Graph API HTTP-fel: {e.response.status_code} - {err_details} för {method} {url}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Graph API anropsfel: {e} för {method} {url}", exc_info=True); return None

# --- Graph API Email Functions ---
def graph_send_email(recipient_email, subject, body_content, 
                     in_reply_to_message_id=None, # This is the InternetMessageID of the email being replied to
                     references_header_str=None,    # This is the full References string
                     conversation_id=None):
    message_payload = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body_content},
            "toRecipients": [{"emailAddress": {"address": recipient_email}}]
        },
        "saveToSentItems": "true"
    }

    headers_list = []
    # IMPORTANT: Graph API requires custom headers (even standard ones set this way)
    # to be prefixed with X- or x-
    if in_reply_to_message_id:
        # While In-Reply-To is standard, setting it via internetMessageHeaders might require the X- prefix.
        # However, a more common way for replies is to ensure the conversationId is set,
        # and the `replyToMessageId` property MIGHT be available on the message object directly
        # for a reply action (though sendMail is more general).
        # Let's try with the X- prefix for explicit control.
        headers_list.append({"name": "X-In-Reply-To", "value": in_reply_to_message_id})
    
    if references_header_str:
        headers_list.append({"name": "X-References", "value": references_header_str})
    
    # Setting conversationId directly on the message is usually preferred by Graph
    # for its own threading if available and correct.
    if conversation_id:
         message_payload["message"]["conversationId"] = conversation_id # This is good
    
    if headers_list:
        message_payload["message"]["internetMessageHeaders"] = headers_list

    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/sendMail"
    logging.info(f"Skickar e-post via Graph till: {recipient_email} | Ämne: {subject}")
    # logging.debug(f"SendMail payload: {json.dumps(message_payload, indent=2)}") # For debugging payload
    
    response = make_graph_api_call("POST", endpoint, data=message_payload)
    
    if response is True: # make_graph_api_call returns True for 202 Accepted
        logging.info("E-post skickat framgångsrikt via Graph API.")
        return True
    else:
        logging.error(f"Misslyckades skicka e-post via Graph API. Svar från API: {response}")
        return False

def clean_email_body(body_text, original_sender_email_for_attribution=None): # Your existing improved clean_email_body
    # ... (same as your existing clean_email_body) ...
    if not body_text: return ""
    lines = body_text.splitlines()
    cleaned_lines = []
    quote_indicators_sw = ["från:", "-----ursprungligt meddelande-----", "den ", "på "]
    quote_indicators_en = ["from:", "-----original message-----", "on ", "wrote:"]
    # Add specific attribution line if original_sender is known
    if original_sender_email_for_attribution:
        quote_indicators_sw.append(f"skrev {original_sender_email_for_attribution.lower()}")

    all_quote_indicators = [q.lower() for q in quote_indicators_sw + quote_indicators_en]
    attribution_line_found = False
    for line in lines:
        stripped_line_lower = line.strip().lower()
        if ((" skrev " in stripped_line_lower or " wrote " in stripped_line_lower) and
             original_sender_email_for_attribution and 
             original_sender_email_for_attribution.lower() in stripped_line_lower): # More specific check
            attribution_line_found = True; break
        for indicator in all_quote_indicators:
            if stripped_line_lower.startswith(indicator):
                attribution_line_found = True; break
        if attribution_line_found: break
        if not line.strip().startswith('>'): cleaned_lines.append(line)
    final_text = "\n".join(cleaned_lines).strip()
    if not final_text and body_text.strip(): return "" 
    return final_text

def graph_check_emails():
    global ACCESS_TOKEN
    select_fields = "id,subject,from,sender,toRecipients,receivedDateTime,bodyPreview,body,internetMessageId,conversationId,isRead,internetMessageHeaders"
    params = {"$filter": "isRead eq false", "$select": select_fields, "$orderby": "receivedDateTime asc"}
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/mailFolders/inbox/messages"
    
    logging.info("Söker efter olästa e-postmeddelanden via Graph API...")
    response_data = make_graph_api_call("GET", endpoint, params=params)

    if not response_data or "value" not in response_data:
        if response_data is None: logging.warning("Ingen data/fel vid hämtning av e-post från Graph.")
        else: logging.info("Inga olästa e-postmeddelanden (Graph).")
        return

    unread_messages = response_data["value"]
    if not unread_messages: logging.info("Inga olästa e-postmeddelanden (Graph)."); return
    logging.info(f"Hittade {len(unread_messages)} olästa e-postmeddelanden (Graph).")
    
    processed_graph_ids = set()

    for msg_graph in unread_messages:
        graph_message_id = msg_graph.get('id')
        logging.info(f"--- Bearbetar Graph e-post ID: {graph_message_id} ---")
        try:
            subject = msg_graph.get('subject', "") 
            sender_info = msg_graph.get('from') or msg_graph.get('sender')
            sender_email = sender_info.get('emailAddress', {}).get('address', '').lower() if sender_info else ''
            internet_message_id = msg_graph.get('internetMessageId')
            graph_conversation_id_incoming = msg_graph.get('conversationId')
            references_header_value = next((h.get('value') for h in msg_graph.get('internetMessageHeaders', []) if h.get('name', '').lower() == 'references'), None)
            
            logging.info(f"Från: {sender_email} | Ämne: '{subject}' | Graph ID: {graph_message_id}")

            if not sender_email or sender_email == TARGET_USER_GRAPH_ID.lower() or 'mailer-daemon' in sender_email or 'noreply' in sender_email:
                logging.warning(f"Skippar e-post (själv, studs, no-reply). Markerar som läst.")
                mark_email_as_read(graph_message_id); processed_graph_ids.add(graph_message_id); continue

            # --- MODIFIED LOGIC FLOW ---
            history_string, problem_info, existing_graph_convo_id_db = get_active_conversation(sender_email)

            if history_string and problem_info:
                # ACTIVE CONVERSATION EXISTS: Process as a reply to the current problem.
                # "starta övning" in subject is IGNORED here if a conversation is active.
                logging.info(f"E-post {graph_message_id} tillhör aktiv konversation för {sender_email}")

                email_body_graph_obj = msg_graph.get('body', {})
                email_body_content = email_body_graph_obj.get('content', '')
                raw_body_for_cleaning = ""
                if email_body_graph_obj.get('contentType', '').lower() == 'html':
                    soup = BeautifulSoup(email_body_content, "html.parser")
                    raw_body_for_cleaning = soup.get_text(separator='\n').strip()
                else: raw_body_for_cleaning = email_body_content
                
                email_body_final = clean_email_body(raw_body_for_cleaning, TARGET_USER_GRAPH_ID)
                logging.debug(f"Rensad e-posttext för ID {graph_message_id}: '{email_body_final[:100]}...'")

                email_body_final_for_llm = email_body_final
                if not email_body_final.strip():
                    logging.warning(f"E-posttext tom efter rensning för ID {graph_message_id}. Använder bodyPreview.")
                    email_body_final_for_llm = (msg_graph.get('bodyPreview') or "").strip()
                    if not email_body_final_for_llm:
                        logging.warning(f"BodyPreview också tom för ID {graph_message_id}. Skippar svar. Markerar som läst.")
                        mark_email_as_read(graph_message_id); processed_graph_ids.add(graph_message_id); continue
                
                new_student_entry = f"Support: {email_body_final_for_llm}\n\n"
                update_conversation_history(sender_email, new_student_entry, graph_conversation_id_incoming) 
                current_full_history = history_string + new_student_entry

                reply_body, is_solved = get_llm_response_with_history(sender_email, current_full_history, problem_info, email_body_final_for_llm)

                if reply_body:
                    new_ulla_entry = f"Ulla: {reply_body}\n\n"
                    current_convo_id_for_reply = graph_conversation_id_incoming or existing_graph_convo_id_db
                    new_references_for_reply = f"{references_header_value if references_header_value else ''} {internet_message_id}".strip()
                    
                    # Determine subject for Ulla's reply. It should be "Re: <Subject of Ulla's PREVIOUS email in this thread>"
                    # This is tricky without knowing Ulla's last subject easily.
                    # Simplest: use "Re: <Student's current subject>"
                    reply_subject_for_ulla = subject
                    if not reply_subject_for_ulla.lower().startswith("re:"):
                        reply_subject_for_ulla = f"Re: {subject}"

                    if graph_send_email(sender_email, reply_subject_for_ulla, reply_body, 
                                        in_reply_to_message_id=internet_message_id, 
                                        references_header_str=new_references_for_reply, 
                                        conversation_id=current_convo_id_for_reply):
                        update_conversation_history(sender_email, new_ulla_entry)
                        if is_solved: delete_conversation(sender_email)
                        mark_email_as_read(graph_message_id); processed_graph_ids.add(graph_message_id)
                        logging.info(f"Bearbetat och svarat på Graph e-post {graph_message_id} för {sender_email}.")
                    else: logging.error(f"Misslyckades skicka svar. E-post INTE markerad som läst.")
                else: logging.error(f"Misslyckades få LLM-svar. E-post INTE markerad som läst.")

            else: # NO ACTIVE CONVERSATION for this sender
                is_start_command = subject and START_COMMAND_SUBJECT in subject.lower()
                if is_start_command:
                    logging.info(f"Mottog startkommando från {sender_email} (Ämne: '{subject}'). Startar ny övning.")
                    # Body of start command email is not used by LLM directly for this step.
                    problem = random.choice(PROBLEM_KATALOG)
                    if start_new_conversation(sender_email, problem, graph_conversation_id_incoming):
                        initial_reply_body = problem['start_prompt']
                        
                        # Ulla's reply subject should be based on the student's "starta övning" subject
                        reply_subject_for_ulla_start = subject 
                        # No need to add Re: here as Ulla is initiating her part of the problem thread
                        # Email clients will make the student's reply "Re: starta övning"

                        if graph_send_email(sender_email, reply_subject_for_ulla_start, initial_reply_body, conversation_id=graph_conversation_id_incoming):
                            logging.info(f"Skickade initial problembeskrivning till {sender_email}")
                            mark_email_as_read(graph_message_id); processed_graph_ids.add(graph_message_id)
                        else:
                            logging.error(f"Misslyckades skicka initialt problem. Startkommando INTE markerat som läst.")
                            # Consider deleting the conversation if the very first email from Ulla fails
                            delete_conversation(sender_email) 
                    else:
                        logging.error(f"Misslyckades skapa/ersätta ny konversation i DB. Startkommando INTE markerat som läst.")
                else: # Not a start command, no active conversation
                    logging.warning(f"Mottog e-post från {sender_email} - ej aktiv konversation/startkommando. Ignorerar. Markerar som läst.")
                    mark_email_as_read(graph_message_id); processed_graph_ids.add(graph_message_id)

        except Exception as processing_error:
             logging.error(f"Ohanterat fel vid bearbetning av Graph e-post ID {graph_message_id}: {processing_error}", exc_info=True)
    
    if unread_messages:
        logging.info(f"Avslutade Graph e-postbearbetning. {len(processed_graph_ids)} av {len(unread_messages)} e-postmeddelanden markerades som bearbetade.")
def mark_email_as_read(graph_message_id):
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/messages/{graph_message_id}"
    payload = {"isRead": True}
    logging.debug(f"Markerar Graph e-post {graph_message_id} som läst...")
    if make_graph_api_call("PATCH", endpoint, data=payload):
        logging.info(f"Graph e-post {graph_message_id} markerad som läst.")
    else: logging.error(f"Misslyckades markera Graph e-post {graph_message_id} som läst.")

# --- Main Execution Block ---
if __name__ == "__main__":
    logging.info("Script startat (Graph API-version, string history).")
    try: init_db()
    except Exception as db_err: logging.critical(f"Misslyckades initiera databas: {db_err}. Avslutar."); exit(1)

    if RUN_EMAIL_BOT:
        logging.info("--- Kör i E-post Bot-läge (Graph API) ---")
        if not OLLAMA_MODEL: logging.critical("Saknar OLLAMA_MODEL."); exit(1)
        # Dynamically import ollama only if in bot mode
        try:
            import ollama as ollama_module
            globals()['ollama'] = ollama_module # Make it available globally if imported
            logging.info(f"Kontrollerar Ollama och modell '{OLLAMA_MODEL}'...")
            ollama.show(OLLAMA_MODEL, **ollama_client_args)
            logging.info(f"Ansluten till Ollama och modell '{OLLAMA_MODEL}' hittad.")
        except ImportError:
            logging.critical("Ollama-biblioteket kunde inte importeras. Installera det (`pip install ollama`).")
            exit("FEL: Ollama-biblioteket saknas.")
        except Exception as ollama_err:
            logging.critical(f"Ollama Fel: {ollama_err}"); exit("FEL: Ollama-anslutning/-modell misslyckades.")

        if not get_graph_token(): logging.critical("Misslyckades hämta Graph API-token."); exit(1)
        logging.info("Startar huvudloop för Graph e-postkontroll...")
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
            select_fields_readonly = "id,subject,from,sender,receivedDateTime,bodyPreview,body,internetMessageId,conversationId,isRead,internetMessageHeaders"
            params_readonly = {"$filter": "isRead eq false", "$select": select_fields_readonly, "$orderby": "receivedDateTime asc"} # Oldest first
            endpoint_readonly = f"/users/{TARGET_USER_GRAPH_ID}/mailFolders/inbox/messages"
            print("\n--- Kontrollerar olästa e-postmeddelanden (läs-läge) ---")
            response_data = make_graph_api_call("GET", endpoint_readonly, params=params_readonly)
            if not response_data or "value" not in response_data:
                if response_data is None: print("Fel vid hämtning av e-post.")
                else: print("Inga olästa e-postmeddelanden.")
            else:
                unread_messages = response_data["value"]
                if not unread_messages: print("Inga olästa e-postmeddelanden.")
                else:
                    print(f"Hittade {len(unread_messages)} olästa e-postmeddelanden:")
                    for i, msg_graph in enumerate(unread_messages):
                        print(f"\n--- E-post {i+1}/{len(unread_messages)} ---")
                        sender_info = msg_graph.get('from') or msg_graph.get('sender')
                        sender_email = sender_info.get('emailAddress', {}).get('address', '') if sender_info else 'Okänd'
                        print(f"  Från: {sender_email}")
                        print(f"  Ämne: {msg_graph.get('subject', '[Inget ämne]')}")
                        
                        email_body_graph_obj_ro = msg_graph.get('body', {})
                        email_body_content_ro = email_body_graph_obj_ro.get('content', '')
                        raw_body_for_display = ""
                        if email_body_graph_obj_ro.get('contentType', '').lower() == 'html':
                            soup_ro = BeautifulSoup(email_body_content_ro, "html.parser")
                            raw_body_for_display = soup_ro.get_text(separator='\n').strip()
                        else: raw_body_for_display = email_body_content_ro
                        
                        cleaned_body_for_display = clean_email_body(raw_body_for_display, TARGET_USER_GRAPH_ID)
                        print(f"  Rensad Text:\n{'-'*20}\n{cleaned_body_for_display if cleaned_body_for_display else msg_graph.get('bodyPreview', '[Tom eller ingen text]')}\n{'-'*20}")
                        mark_email_as_read(msg_graph.get('id'))
                    print("\nAlla olästa e-postmeddelanden listade och markerade som lästa.")
        except Exception as readonly_err:
            logging.error(f"Fel i läs-läge: {readonly_err}", exc_info=True)
        logging.info("--- Avslutade Enkelt E-postläsningsläge ---")
    logging.info("Script avslutat.")