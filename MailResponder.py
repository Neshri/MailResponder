import imaplib
import smtplib
import email
from email.message import EmailMessage
from email.header import decode_header, make_header
import email.utils
import time
import os
import logging
import sqlite3
import datetime
import random
import json # For storing history as JSON

import ollama
from dotenv import load_dotenv

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

# --- Load .env variables ---
load_dotenv()
logging.info("Läste in miljövariabler från .env-fil.")

# --- Configuration ---
# Email Config
EMAIL_ADDRESS = os.environ.get('BOT_EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('BOT_EMAIL_PASSWORD')
IMAP_SERVER = os.environ.get('IMAP_SERVER', 'outlook.office365.com')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.office365.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
# Ollama Config
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL')
OLLAMA_HOST = os.environ.get('OLLAMA_HOST')

# --- Ollama Client Arguments ---
ollama_client_args = {}
if OLLAMA_HOST:
    ollama_client_args['host'] = OLLAMA_HOST
    logging.info(f"Ollama-klient konfigurerad för värd: {OLLAMA_HOST}")

# --- Constants ---
DB_FILE = 'ulla_conversations.db'
RUN_EMAIL_BOT = True # <-- SET TO False TO RUN COMMAND-LINE TEST MODE
START_COMMAND_SUBJECT = "starta övning" # Subject to initiate training (case-insensitive)

# --- Persona Prompt (Swedish) ---
ULLA_PERSONA_PROMPT = """
Du är Ulla, en vänlig men tekniskt ovan äldre dam i 85-årsåldern.
Du interagerar med en IT-supportstudent via e-post eftersom något inte fungerar med dina "apparater".
Du använder ofta felaktiga termer (t.ex. "klickern" för musen, "internetlådan" för routern, "fönsterskärmen" för bildskärmen).
Du beskriver saker vagt baserat på vad du ser eller hör.
Du kan ibland spåra ur lite och prata om din katt Måns, dina barnbarn eller vad du drack till fikat, men återgår så småningom till problemet som nämns i konversationen.
Du uttrycker mild frustration, förvirring eller att du känner dig överväldigad, men är alltid artig och tacksam för hjälp.
Du svarar på det senaste e-postmeddelandet i konversationstråden som tillhandahålls.
Analysera studentens meddelande i kontexten av konversationshistoriken och ditt nuvarande problem.
Formulera ett svar *som Ulla*. Agera INTE som en AI-assistent. Svara bara som Ulla skulle göra.
Håll dina svar relativt korta och konverserande, som ett riktigt e-postmeddelande. Använd inte emojis.
"""

# --- Problem Catalog (Swedish & Precise) ---
PROBLEM_KATALOG = [
    {
        "id": "P001",
        "beskrivning": "Min 'klicker' (musen) hoppar inte fram när jag rör den. Den lilla röda lampan under lyser inte alls.",
        "losning_nyckelord": ["byt batteri", "byta batterier", "ladda musen"], # Only battery/charging related solutions
        "start_prompt": "Kära nån, nu har klickern gett upp helt! Den är alldeles död och den lilla lampan under är släckt. Jag kan inte klicka på någonting på fönsterskärmen. Vad ska jag ta mig till?"
    },
    {
        "id": "P002",
        "beskrivning": "Det är katthår i sensorn under 'klickern' (musen), vilket gör att pekaren hoppar och far oberäkneligt på skärmen.",
        "losning_nyckelord": ["rengör sensorn", "blås bort håret", "ta bort skräpet under"], # Only cleaning the sensor
        "start_prompt": "Hjälp! Min klicker har blivit alldeles tokig! Pekaren på skärmen hoppar som en skållad råtta. Jag tittade under och det ser ut som Måns har fällt lite hår där igen... Hur får jag bort det?"
    },
    {
        "id": "P003",
        "beskrivning": "Internetlådan (routern) har en fast orange lampa istället för en blinkande grön. Internet fungerar inte.",
        "losning_nyckelord": ["starta om routern", "dra ut strömsladden", "vänta", "sätt i sladden igen"], # Only restarting the router
        "start_prompt": "Nej men nu är det väl ändå typiskt! Hela internet har försvunnit. Den där lilla internetlådan lyser bara med ett envist orange sken, den brukar ju blinka så glatt i grönt. Hur ska jag nu kunna läsa tidningen på plattan?"
    },
    {
        "id": "P004",
        "beskrivning": "Fönsterskärmen (bildskärmen) är helt svart, men datorlådan låter som vanligt. Strömkabeln till skärmen sitter i väggen.",
        "losning_nyckelord": ["kontrollera skärmkabeln", "tryck på skärmens strömknapp", "sitter kabeln fast", "växla ingångskälla"], # Only checking screen power/connection
        "start_prompt": "Men kära nån, nu blev allt svart på fönsterskärmen! Datorlådan brummar på som vanligt, men skärmen är helt mörk. Jag har känt på sladden som går in i väggen, den sitter där. Har jag kommit åt någon knapp?"
    }
]

# --- Database Functions (Simplified Schema) ---
def init_db():
    """Initializes the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Single table using student_email as PK
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_conversations (
                student_email TEXT PRIMARY KEY,
                problem_id TEXT NOT NULL,
                problem_description TEXT NOT NULL,
                correct_solution_keywords TEXT NOT NULL,
                conversation_history TEXT NOT NULL, -- Store as JSON list of dicts
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logging.info(f"Databas {DB_FILE} initierad/kontrollerad.")
    except sqlite3.Error as e:
        logging.critical(f"Databasinitiering misslyckades: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()

def start_new_conversation(student_email, problem):
    """Starts a new conversation or replaces existing one for the student."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now()

        # Initial history contains only Ulla's first prompt
        initial_history = [{'role': 'assistant', 'content': problem['start_prompt']}]
        history_json = json.dumps(initial_history)

        # Use REPLACE INTO to overwrite if student starts a new session while one is active
        cursor.execute('''
            REPLACE INTO active_conversations
            (student_email, problem_id, problem_description, correct_solution_keywords, conversation_history, created_at, last_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_email, problem['id'], problem['beskrivning'], problem['losning_nyckelord'], history_json, timestamp, timestamp))
        conn.commit()
        logging.info(f"Startade/ersatte konversation för {student_email} med problem {problem['id']}")
        return True
    except sqlite3.Error as e:
        logging.error(f"Databasfel vid start av konversation för {student_email}: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()

def get_active_conversation(student_email):
    """Retrieves the active conversation details for a student."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        cursor = conn.cursor()
        cursor.execute('''
            SELECT problem_id, problem_description, correct_solution_keywords, conversation_history
            FROM active_conversations
            WHERE student_email = ?
        ''', (student_email,))
        row = cursor.fetchone()
        if row:
            logging.info(f"Hittade aktiv konversation för {student_email}")
            # Decode JSON history
            history = json.loads(row['conversation_history'])
            problem_info = {
                'id': row['problem_id'],
                'beskrivning': row['problem_description'],
                'losning_nyckelord': row['correct_solution_keywords']
            }
            return history, problem_info
        else:
            logging.debug(f"Ingen aktiv konversation hittad för {student_email}")
            return None, None
    except sqlite3.Error as e:
        logging.error(f"Databasfel vid hämtning av konversation för {student_email}: {e}", exc_info=True)
        return None, None
    except json.JSONDecodeError as e:
         logging.error(f"Fel vid avkodning av JSON-historik för {student_email}: {e}", exc_info=True)
         return None, None # History is corrupt
    finally:
        if conn:
            conn.close()

def update_conversation_history(student_email, history):
    """Updates the conversation history for an active conversation."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        history_json = json.dumps(history)
        timestamp = datetime.datetime.now()
        cursor.execute('''
            UPDATE active_conversations
            SET conversation_history = ?, last_update = ?
            WHERE student_email = ?
        ''', (history_json, timestamp, student_email))
        conn.commit()
        logging.info(f"Uppdaterade konversationshistorik för {student_email}")
        return True
    except sqlite3.Error as e:
        logging.error(f"Databasfel vid uppdatering av historik för {student_email}: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()

def delete_conversation(student_email):
    """Deletes an active conversation, typically upon completion."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM active_conversations WHERE student_email = ?
        ''', (student_email,))
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"Raderade avslutad konversation för {student_email}")
            return True
        else:
            logging.warning(f"Försökte radera konversation för {student_email}, men ingen hittades.")
            return False
    except sqlite3.Error as e:
        logging.error(f"Databasfel vid radering av konversation för {student_email}: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()


# (Keep imports and other functions as they were)

# --- LLM Interaction (Swedish - REVISED PROMPT) ---
def get_llm_response_with_history(student_email, history, problem_info):
    """Gets LLM response considering history and precise evaluation task, using clearer marker logic."""
    if not OLLAMA_MODEL:
        logging.error("OLLAMA_MODEL miljövariabel ej satt.")
        return "Nej men kära nån, nu tappade jag tråden helt...", False # Swedish fallback

    latest_student_message = history[-1]['content'] if history and history[-1]['role'] == 'user' else "[INGET SENASTE MEDDELANDE]"

    logging.info(f"Hämtar LLM-svar för {student_email} (modell: {OLLAMA_MODEL})")

    # --- REVISED PROMPT SECTIONS ---
    system_prompt_combined = f"""{ULLA_PERSONA_PROMPT}

Ditt nuvarande specifika tekniska problem är: {problem_info['beskrivning']}
Den korrekta tekniska lösningen innefattar specifikt dessa idéer/nyckelord: {problem_info['losning_nyckelord']}

Du ska utvärdera studentens senaste e-postmeddelande baserat på konversationshistoriken och den exakta korrekta lösningen.
"""

    evaluation_prompt = f"""Här är det senaste meddelandet från studenten:
---
{latest_student_message}
---
**Utvärdering:** Har studenten i detta senaste meddelande föreslagit den specifika korrekta lösningen relaterad till '{problem_info['losning_nyckelord']}'? (Analysera mot *exakta* nyckelord/koncept. Generella IT-råd är fel.)

**Instruktion för ditt svar:**
1.  Skriv *först*, på en helt egen rad och utan någon annan text på den raden, antingen `[LÖST]` (om studentens senaste meddelande innehöll den korrekta specifika lösningen) eller `[EJ_LÖST]` (om det inte gjorde det).
2.  Börja sedan på en *ny rad* och skriv ditt svar *som Ulla*.
    *   Om du skrev `[LÖST]` på första raden, ska Ullas svar bekräfta att rådet fungerade, tacka och avsluta artigt.
    *   Om du skrev `[EJ_LÖST]` på första raden, ska Ullas svar vara i karaktär, *inte* avslöja lösningen, och kanske vara lite förvirrat eller beskriva symptomen igen.

**Exempel på format (om lösningen var FELAKTIG):**
[EJ_LÖST]
Nej men kära du, jag provade det där men det blev ingen skillnad alls. Internetlådan lyser fortfarande envist orange...

**Exempel på format (om lösningen var KORREKT):**
[LÖST]
Åh, tusen tack snälla rara! Nu fungerar det perfekt igen. Det var precis som du sa! Nu ska jag och Måns ta en kopp kaffe och läsa tidningen på plattan.

**VIKTIGT:** Ullas svar (allt efter första radens markör) ska *aldrig* nämna utvärderingen, markörerna `[LÖST]` / `[EJ_LÖST]`, eller ge ledtrådar utöver vad Ulla naturligt skulle säga.
"""
    # --- END OF REVISED PROMPT SECTIONS ---

    messages = [{'role': 'system', 'content': system_prompt_combined}]
    # Pass history *before* the evaluation prompt
    messages.extend(history[:-1]) # History up to the turn *before* the latest student message
    messages.append({'role': 'user', 'content': evaluation_prompt}) # Evaluation prompt contains latest msg

    try:
        logging.debug(f"Skickar meddelanden till Ollama för {student_email}: {messages}")
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={'temperature': 0.7, 'num_predict': 300}, # Adjust num_predict if needed
            **ollama_client_args
        )
        raw_reply = response['message']['content'].strip()
        logging.debug(f"Rått svar från Ollama för {student_email}: {raw_reply}")

        # --- REVISED PARSING LOGIC ---
        lines = raw_reply.split('\n', 1) # Split into max 2 parts: first line and the rest
        marker = lines[0].strip()
        is_solved = (marker == "[LÖST]")
        is_unsolved_marker = (marker == "[EJ_LÖST]")

        if len(lines) > 1:
            Ulla_reply = lines[1].strip()
            # Extra safety: remove markers if they somehow leak into Ulla's part
            Ulla_reply = Ulla_reply.replace("[LÖST]", "").replace("[EJ_LÖST]", "").strip()
        elif is_solved: # Handle case where only [LÖST] is returned
            Ulla_reply = "Åh, tack snälla du, nu fungerar det visst!"
            logging.warning(f"LLM returnerade bara LÖST-markör för {student_email}. Använder reservsvar.")
        else: # Handle case where only [EJ_LÖST] or unexpected marker/text is returned
            Ulla_reply = "Jaha ja, jag är inte riktigt säker på vad jag ska göra nu..."
            logging.warning(f"LLM returnerade bara EJ_LÖST-markör eller oväntat/kort svar för {student_email}. Använder reservsvar.")
            is_solved = False # Ensure is_solved is False if marker wasn't exactly [LÖST]

        # Final check for empty reply after processing
        if not Ulla_reply:
             Ulla_reply = "Åh, tack snälla du, nu fungerar det visst!" if is_solved else "Jaha ja, jag är inte riktigt säker på vad jag ska göra nu..."
             logging.warning(f"Ulla's svar var tomt efter bearbetning för {student_email}. Använder reservsvar.")

        logging.info(f"LLM genererade svar för {student_email}. Marker: {marker}. Tolkat som löst: {is_solved}")
        return Ulla_reply, is_solved
        # --- END OF REVISED PARSING LOGIC ---

    except ollama.ResponseError as e:
         logging.error(f"Ollama API-fel för {student_email}: {e.error} (Status: {e.status_code})", exc_info=True)
         return "Nej men kära nån, nu krånglar min tankeverksamhet...", False
    except ConnectionRefusedError:
         logging.error(f"Kunde inte ansluta till Ollama-servern ({ollama_client_args.get('host', 'http://localhost:11434')}). Kör Ollama?")
         return "Det verkar vara upptaget i ledningen just nu...", False
    except Exception as e:
        logging.error(f"Oväntat fel vid anrop av Ollama LLM för {student_email}: {e}", exc_info=True)
        return "Nej, nu vet jag inte vad jag ska ta mig till...", False


# --- Email Utility Functions ---
def decode_header_simple(header_value):
    """Safely decodes email headers."""
    if header_value is None: return ""
    try: return str(make_header(decode_header(header_value)))
    except Exception: return str(header_value) # Fallback

def get_email_body(msg):
    """Extracts the plain text body from an email.message.Message object."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    charset = part.get_content_charset('utf-8')
                    body = part.get_payload(decode=True).decode(charset, errors='replace')
                    break
                except Exception:
                    try: body = part.get_payload(decode=True).decode('utf-8', errors='replace'); break
                    except Exception as e2: logging.error(f"Kunde ej avkoda meddelandedel: {e2}"); body = "[Oläslig meddelandetext]"; break
    else:
        if msg.get_content_type() == 'text/plain':
            try:
                charset = msg.get_content_charset('utf-8')
                body = msg.get_payload(decode=True).decode(charset, errors='replace')
            except Exception:
                try: body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                except Exception as e2: logging.error(f"Kunde ej avkoda meddelande: {e2}"); body = "[Oläslig meddelandetext]"
        else: body = "[Meddelandet är inte vanlig text]"

    # Basic cleaning (Swedish adaptation might be needed if reply patterns differ)
    cleaned_body = "\n".join([line for line in body.splitlines() if not line.strip().startswith('>')])
    cleaned_body = "\n".join([line for line in cleaned_body.splitlines() if not (line.strip().lower().startswith('de ') and ('skrev:' in line.lower() or 'wrote:' in line.lower()))])
    cleaned_body = "\n".join([line for line in cleaned_body.splitlines() if not (line.strip().lower().startswith('on ') and 'wrote:' in line.lower())])
    return cleaned_body.strip()

# --- Core Email Processing Functions ---
def send_email(recipient, subject, body, incoming_message_id=None, references_header=None):
    """Sends an email using SMTP, setting correct threading headers."""
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT]):
        logging.error("Saknar SMTP-konfiguration. Kan ej skicka e-post.")
        return None

    msg = EmailMessage()
    safe_subject = subject if subject else ""
    # Keep subject, add Re: if it's a reply and not already there
    if incoming_message_id and not safe_subject.lower().startswith("re:"):
         msg['Subject'] = f"Re: {safe_subject}"
    else:
         msg['Subject'] = safe_subject

    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient

    domain_part = EMAIL_ADDRESS.split('@')[-1] if EMAIL_ADDRESS and '@' in EMAIL_ADDRESS else 'Ulla.bot'
    new_message_id = email.utils.make_msgid(domain=domain_part)
    msg['Message-ID'] = new_message_id

    # Set Threading Headers if it's a reply
    if incoming_message_id:
        msg['In-Reply-To'] = incoming_message_id
        if references_header:
            if not references_header.strip().endswith(incoming_message_id):
                 msg['References'] = f"{references_header.strip()} {incoming_message_id}"
            else:
                 msg['References'] = references_header.strip()
        else:
            msg['References'] = incoming_message_id

    msg.set_content(body)

    try:
        logging.info(f"Ansluter till SMTP-server: {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            logging.info(f"Skickar e-post till: {recipient} | Ämne: {msg['Subject']} | Nytt Message-ID: {new_message_id}")
            server.send_message(msg)
            logging.info("E-post skickat framgångsrikt.")
            return new_message_id
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"SMTP Authentiseringsfel: {e}. Kontrollera e-post/lösenord (App-lösenord för outlook!) i .env.")
        return None
    except Exception as e:
        logging.error(f"Oväntat fel vid skickande av e-post: {e}", exc_info=True)
        return None

def check_emails():
    """Checks for new emails, processes them based on student email and state."""
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER]):
        logging.error("Saknar IMAP-konfiguration. Kan ej kontrollera e-post.")
        return

    mail = None
    processed_email_ids = set()

    try:
        logging.info(f"Ansluter till IMAP-server: {IMAP_SERVER}")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select('inbox')
        logging.info("INBOX vald.")

        status, search_data = mail.search(None, 'UNSEEN')
        if status != 'OK': raise imaplib.IMAP4.error(f"IMAP search failed: {status}")

        email_ids = search_data[0].split()
        if not email_ids or email_ids == [b'']:
            logging.info("Inga olästa e-postmeddelanden hittades.")
            mail.logout()
            return

        logging.info(f"Hittade {len(email_ids)} olästa e-postmeddelanden.")

        for email_id_bytes in email_ids:
            email_id_str = email_id_bytes.decode()
            logging.info(f"--- Bearbetar e-post ID: {email_id_str} ---")

            try:
                status, msg_data = mail.fetch(email_id_bytes, '(RFC822)')
                if status != 'OK': raise imaplib.IMAP4.error(f"Fetch failed for {email_id_str}: {status}")

                raw_email = next((part[1] for part in msg_data if isinstance(part, tuple)), None)
                if not raw_email: raise ValueError(f"Could not extract raw email for {email_id_str}")

                msg = email.message_from_bytes(raw_email)

                subject = decode_header_simple(msg.get('Subject'))
                sender_email = email.utils.parseaddr(msg.get('From'))[1].lower() # Use lowercase for lookup
                incoming_message_id = msg.get('Message-ID')
                references = msg.get('References')

                logging.info(f"Från: {sender_email} | Ämne: {subject} | Message-ID: {incoming_message_id}")

                # Filter out self/no-reply/missing sender
                if not sender_email or sender_email == EMAIL_ADDRESS or 'mailer-daemon' in sender_email or 'noreply' in sender_email:
                    logging.warning(f"Skippar e-post ID {email_id_str} (själv, studs, no-reply). Markerar som läst.")
                    mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                    processed_email_ids.add(email_id_bytes)
                    continue

                email_body = get_email_body(msg)
                if not email_body or email_body.startswith("[Ol"): # Check for our error messages
                    logging.warning(f"E-posttext tom eller oläslig för ID {email_id_str}. Markerar som läst.")
                    mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                    processed_email_ids.add(email_id_bytes)
                    continue

                # --- State Logic ---
                history, problem_info = get_active_conversation(sender_email)

                if history and problem_info:
                    # --- Existing Conversation ---
                    logging.info(f"E-post {incoming_message_id} tillhör aktiv konversation för {sender_email}")

                    # 1. Append student's message to history
                    history.append({'role': 'user', 'content': email_body})

                    # 2. Get LLM response
                    reply_body, is_solved = get_llm_response_with_history(sender_email, history, problem_info)

                    # 3. Send reply (if LLM succeeded)
                    if reply_body:
                        Ulla_message_id = send_email(sender_email, subject, reply_body, incoming_message_id, references)
                        if Ulla_message_id:
                            # 4. Append Ulla's reply to history
                            history.append({'role': 'assistant', 'content': reply_body})
                            # 5. Update DB or Delete if solved
                            if is_solved:
                                delete_conversation(sender_email)
                            else:
                                update_conversation_history(sender_email, history)
                            # 6. Mark student's email as seen
                            mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                            processed_email_ids.add(email_id_bytes)
                            logging.info(f"Bearbetat och svarat på e-post {email_id_str} för {sender_email}.")
                        else:
                             logging.error(f"Misslyckades skicka svar för {sender_email}. Studentens e-post {email_id_str} INTE markerad som läst.")
                    else:
                        logging.error(f"Misslyckades få LLM-svar för {sender_email}. Studentens e-post {email_id_str} INTE markerad som läst.")

                else:
                    # --- No Active Conversation ---
                    if subject and START_COMMAND_SUBJECT in subject.lower():
                        logging.info(f"Mottog startkommando från {sender_email} (Ämne: '{subject}')")
                        # 1. Select problem & Start conversation in DB
                        problem = random.choice(PROBLEM_KATALOG)
                        if start_new_conversation(sender_email, problem):
                            # 2. Send Ulla's initial problem description
                            initial_reply_body = problem['start_prompt']
                            # Note: First email has no incoming_message_id or references
                            Ulla_message_id = send_email(sender_email, subject, initial_reply_body, None, None)
                            if Ulla_message_id:
                                logging.info(f"Skickade initial problembeskrivning till {sender_email}")
                                # 3. Mark student's start command as seen
                                mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                processed_email_ids.add(email_id_bytes)
                            else:
                                logging.error(f"Misslyckades skicka initialt problem till {sender_email}. Startkommando {email_id_str} INTE markerat som läst.")
                                # Consider deleting the conversation record if first send fails
                                delete_conversation(sender_email)
                        else:
                             logging.error(f"Misslyckades skapa ny konversation i DB för {sender_email}. Startkommando {email_id_str} INTE markerat som läst.")
                    else:
                        # --- Unrecognized Email ---
                        logging.warning(f"Mottog e-post ID {email_id_str} från {sender_email} - ej aktiv konversation eller startkommando. Ignorerar. Markerar som läst.")
                        mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                        processed_email_ids.add(email_id_bytes)

            except Exception as processing_error:
                 logging.error(f"Ohanterat fel vid bearbetning av e-post ID {email_id_str}: {processing_error}", exc_info=True)
                 # Avoid marking as seen on generic errors to allow retry

        logging.info(f"Avslutade bearbetning. {len(processed_email_ids)} e-postmeddelanden bearbetades framgångsrikt denna körning.")
        if mail: mail.logout(); logging.info("IMAP utloggad.")

    except imaplib.IMAP4.error as e:
        if "AUTHENTICATIONFAILED" in str(e).upper(): logging.error(f"IMAP Authentiseringsfel: {e}. Kontrollera .env.")
        else: logging.error(f"IMAP Fel under session: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"Oväntat fel i check_emails huvudloop: {e}", exc_info=True)
        try: # Attempt logout even after error
            if mail and mail.state in ('SELECTED', 'AUTH'): mail.logout(); logging.info("IMAP utloggad efter fel.")
        except Exception as logout_err: logging.error(f"Fel vid utloggning efter fel: {logout_err}")


# --- Main Execution Block ---
if __name__ == "__main__":
    logging.info("Script startat.")

    if RUN_EMAIL_BOT:
        logging.info("--- Kör i E-post Bot-läge ---")
        # --- Config Checks ---
        if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, OLLAMA_MODEL]):
            logging.critical("Saknar kritisk konfiguration i .env: BOT_EMAIL_ADDRESS, BOT_EMAIL_PASSWORD, OLLAMA_MODEL.")
            exit("FEL: Konfiguration ofullständig. Avslutar.")

        # --- Initialize Database ---
        try: init_db()
        except Exception as db_err: logging.critical(f"Misslyckades initiera databas: {db_err}. Avslutar."); exit(1)

        # --- Verify Ollama Connection ---
        try:
            logging.info(f"Kontrollerar anslutning till Ollama och modell '{OLLAMA_MODEL}'...")
            ollama.show(OLLAMA_MODEL, **ollama_client_args)
            logging.info(f"Ansluten till Ollama och modell '{OLLAMA_MODEL}' hittad.")
        except Exception as ollama_err:
            logging.critical(f"Ollama Fel: Kunde inte ansluta eller hitta modell '{OLLAMA_MODEL}'. Fel: {ollama_err}")
            exit(f"FEL: Ollama-anslutning/-modell misslyckades.")

        # --- Main Loop ---
        logging.info("Startar huvudloop för e-postkontroll...")
        while True:
            try: check_emails()
            except Exception as loop_err: logging.error(f"Kritiskt fel i huvudloop: {loop_err}", exc_info=True)

            sleep_interval = 60
            logging.info(f"Sover i {sleep_interval} sekunder...")
            time.sleep(sleep_interval)

    else:
        # --- Command-Line Test Mode (Swedish) ---
        logging.info(f"--- Kör i Kommandorads Testläge (Modell: {OLLAMA_MODEL}) ---")
        logging.info("Detta läge simulerar konversationer utan e-post. Skriv 'quit' för att avsluta.")

        if not OLLAMA_MODEL: logging.critical("OLLAMA_MODEL ej satt i .env."); exit(1)
        try: ollama.list(**ollama_client_args); logging.info("Ansluten till Ollama.")
        except Exception as e: logging.critical(f"Kunde ej ansluta till Ollama: {e}"); exit(1)

        # Simulate conversation state
        test_student_email = "test.student@example.com"
        test_history = []
        problem = random.choice(PROBLEM_KATALOG)
        test_problem_info = {
            'id': problem['id'],
            'beskrivning': problem['beskrivning'],
            'losning_nyckelord': problem['losning_nyckelord']
        }
        print(f"\n--- Startar Testscenario ---")
        print(f"Ullas Problem: {test_problem_info['beskrivning']}")
        print(f"(Lösningsledtråd: {test_problem_info['losning_nyckelord']})")
        print(f"Ullas Startmeddelande:\n{problem['start_prompt']}\n")
        test_history.append({'role': 'assistant', 'content': problem['start_prompt']})

        while True:
            try:
                user_input = input(f"Studentens Svar ({test_student_email}) > ")
                if user_input.lower() == 'quit': break
                if not user_input: continue

                # Add student message to history
                test_history.append({'role': 'user', 'content': user_input})

                Ulla_response, is_solved = get_llm_response_with_history(test_student_email, test_history, test_problem_info)

                print("\n--- Ullas Svar ---")
                print(Ulla_response)
                print("--------------------\n")

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