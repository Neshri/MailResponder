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
import uuid
import ollama # Ollama client library
from dotenv import load_dotenv # For reading .env file

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s'
)

# --- Load .env variables ---
load_dotenv()
logging.info("Loaded environment variables from .env file.")

# --- Configuration (Reads from .env or system environment) ---
# Email Config
EMAIL_ADDRESS = os.environ.get('BOT_EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('BOT_EMAIL_PASSWORD')
IMAP_SERVER = os.environ.get('IMAP_SERVER', 'imap.gmail.com')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587)) # Default Gmail TLS port
# Ollama Config
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL')
OLLAMA_HOST = os.environ.get('OLLAMA_HOST') # Optional: Ollama host override

# --- Ollama Client Arguments ---
ollama_client_args = {}
if OLLAMA_HOST:
    ollama_client_args['host'] = OLLAMA_HOST
    logging.info(f"Ollama client configured for host: {OLLAMA_HOST}")

# --- Constants ---
DB_FILE = 'bessie_conversations.db'
RUN_EMAIL_BOT = False # <-- SET TO False TO RUN COMMAND-LINE TEST MODE

# --- Persona Prompt ---
GRANDMA_PERSONA_PROMPT = """
You are Bessie, a sweet but technologically challenged elderly woman in her late 80s.
You are interacting with an IT support student via email because something isn't working right with your "gadgets".
You often get technical terms wrong (e.g., "the clicker", "the google box", "the window screen").
You describe things vaguely based on what you see or hear.
You sometimes get slightly sidetracked talking about your cat Mittens, your grandkids, or what you had for tea, but eventually return to the problem mentioned in the conversation history.
You express mild frustration, confusion, or being overwhelmed, but always remain polite and appreciative of help.
You are responding to the latest email in the conversation thread provided.
Analyze the student's message in the context of the conversation history and your current problem.
Formulate a reply *as Bessie*. Do NOT act as an AI assistant. Only reply as Bessie would.
Keep your replies relatively short and conversational, like a real email. Do not use emojis.
"""

# --- Problem Catalog ---
PROBLEMS_CATALOG = [
    {
        "id": "P001",
        "description": "My internet box (the one with the blinky lights!) isn't working. I can't get onto the 'world wide web' to check my emails. The main light is orange instead of green.",
        "solution_keywords": "reboot router, restart modem, power cycle, unplug wait plug back",
        "initial_bessie_prompt": "Oh dear, my internet box isn't doing the right blinky dance. The light's gone all orangey and I can't get my emails! It was working fine yesterday. What should I try, young person?"
    },
    {
        "id": "P002",
        "description": "I'm trying to print my knitting pattern, but the printer machine just sits there humming quietly. It says something about 'low ink' but I just put a new cartridge in!",
        "solution_keywords": "check cartridge alignment, run cleaning cycle, ensure correct cartridge type, remove protective tape",
        "initial_bessie_prompt": "My printer machine is being stubborn! It hums like it's thinking, but no pattern comes out. It flashes about ink, but I swear I put a fresh one in just yesterday. Mittens tried batting at it, but that didn't help. What could be wrong?"
    },
    {
        "id": "P003",
        "description": "My clicker (the mouse thingy) is jumping all over the window screen! It's like it's had too much sugar. Makes it terribly hard to click the right buttons.",
        "solution_keywords": "clean mouse sensor, check surface, try different mousepad, check battery wireless",
        "initial_bessie_prompt": "Goodness me, this clicker has gone wild! It zips around the screen like a bumblebee. I can hardly aim it! Is the little red light underneath meant to be dusty? It's making me quite dizzy."
    },
    {
        "id": "P004",
        "description": "My computer screen suddenly went black! The tower box is still humming, but the window screen is completely dark. I wiggled the wires but nothing happened.",
        "solution_keywords": "check cable connection monitor power screen brightness input source",
        "initial_bessie_prompt": "Oh heavens! My window screen has gone completely black! The big box is still making its usual noises, but there's nothing to see. I checked the plug in the wall. Did I press a wrong button?"
    }
]

# --- Database Functions ---
def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                thread_id TEXT PRIMARY KEY,
                student_email TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                problem_description TEXT NOT NULL,
                correct_solution TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'active', -- 'active', 'solved', 'abandoned'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_db_id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                email_message_id TEXT UNIQUE NOT NULL, -- The actual Message-ID header
                sender TEXT NOT NULL, -- 'student' or 'bessie'
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (thread_id) REFERENCES conversations (thread_id) ON DELETE CASCADE
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages (thread_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_email_message_id ON messages (email_message_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_state ON conversations (state)')
        conn.commit()
        logging.info(f"Database {DB_FILE} initialized/checked successfully.")
    except sqlite3.Error as e:
        logging.error(f"Database initialization failed: {e}", exc_info=True)
        raise # Reraise error to prevent starting if DB fails
    finally:
        if conn:
            conn.close()

def add_new_conversation(student_email, problem):
    """Adds a new conversation to the database and returns the thread_id."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Use Bessie's *first* message ID as the unique ID for the conversation thread
        domain_part = EMAIL_ADDRESS.split('@')[-1] if EMAIL_ADDRESS and '@' in EMAIL_ADDRESS else 'bessie.bot'
        initial_message_id = email.utils.make_msgid(domain=domain_part)
        thread_id = initial_message_id # This IS the conversation's primary key

        timestamp = datetime.datetime.now()
        cursor.execute('''
            INSERT INTO conversations
            (thread_id, student_email, problem_id, problem_description, correct_solution, state, last_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (thread_id, student_email, problem['id'], problem['description'], problem['solution_keywords'], 'active', timestamp))
        conn.commit()
        logging.info(f"Started new conversation thread {thread_id} for {student_email} with problem {problem['id']}")
        return thread_id
    except sqlite3.Error as e:
        logging.error(f"Database error adding new conversation: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()

def add_message_to_db(thread_id, email_message_id, sender, content):
    """Adds a message to the database for a given thread."""
    conn = None
    if not email_message_id:
        logging.error(f"Attempted to add message to thread {thread_id} with empty email_message_id. Skipping.")
        return False # Cannot add message without a unique ID

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now()
        cursor.execute('''
            INSERT INTO messages (thread_id, email_message_id, sender, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (thread_id, email_message_id, sender, content, timestamp))
        # Update conversation's last_update time
        cursor.execute('''
            UPDATE conversations SET last_update = ? WHERE thread_id = ?
        ''', (timestamp, thread_id))
        conn.commit()
        logging.info(f"Added message {email_message_id} (sender: {sender}) to thread {thread_id}")
        return True
    except sqlite3.IntegrityError:
         # This usually means the message ID already exists, which might happen with retries. Log as warning.
         logging.warning(f"Message with ID {email_message_id} likely already exists in thread {thread_id}. Skipping duplicate insert.")
         return False
    except sqlite3.Error as e:
        logging.error(f"Database error adding message {email_message_id} to thread {thread_id}: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()

def find_conversation_thread_id(msg_headers):
    """
    Tries to find an active conversation thread_id based on email headers.
    Uses References first, then In-Reply-To.
    msg_headers is a dictionary-like object (e.g., email.message.Message)
    """
    references = msg_headers.get('References', '')
    in_reply_to = msg_headers.get('In-Reply-To', '')

    potential_ids = []
    if references:
        # References header contains space-separated Message-IDs, often starting with the original.
        potential_ids.extend(references.split())
    if in_reply_to:
        # Add In-Reply-To as a potential link, ensure it's not already from References.
        if in_reply_to not in potential_ids:
             potential_ids.append(in_reply_to)

    if not potential_ids:
        logging.debug("No References or In-Reply-To headers found.")
        return None # Cannot determine thread from headers

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        # Query if any message ID in the headers exists in our messages table OR
        # if any header ID matches a conversation's thread_id directly (Bessie's first message ID)
        # belonging to an *active* conversation.
        placeholders = ','.join('?' * len(potential_ids))
        query = f'''
            SELECT DISTINCT c.thread_id
            FROM conversations c
            LEFT JOIN messages m ON c.thread_id = m.thread_id
            WHERE c.state = 'active' AND (c.thread_id IN ({placeholders}) OR m.email_message_id IN ({placeholders}))
        '''
        # Parameters list needs to be duplicated for the two IN clauses
        params = potential_ids * 2
        cursor.execute(query, params)
        result = cursor.fetchone()

        if result:
            found_thread_id = result[0]
            logging.info(f"Found active thread {found_thread_id} based on headers: {potential_ids}")
            return found_thread_id
        else:
            logging.debug(f"Headers {potential_ids} did not match any active thread.")
            return None
    except sqlite3.Error as e:
        logging.error(f"Database error finding conversation thread by headers: {e}", exc_info=True)
        return None
    finally:
        if conn:
            conn.close()

def get_conversation_history(thread_id):
    """Retrieves conversation messages and problem info for a given thread_id."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row # Return rows as dictionary-like objects
        cursor = conn.cursor()

        # Get conversation details (problem, solution)
        cursor.execute('''
            SELECT problem_description, correct_solution FROM conversations WHERE thread_id = ?
        ''', (thread_id,))
        problem_info = cursor.fetchone()
        if not problem_info:
            logging.error(f"Could not find conversation details for thread_id: {thread_id}")
            return [], None # Return empty history and None problem_info

        # Get messages in chronological order
        cursor.execute('''
            SELECT sender, content FROM messages WHERE thread_id = ? ORDER BY timestamp ASC
        ''', (thread_id,))
        messages = cursor.fetchall()

        # Format for LLM (list of {'role': 'user'/'assistant', 'content': ...})
        history = []
        for msg in messages:
            # 'user' is the student, 'assistant' is Bessie
            role = 'assistant' if msg['sender'] == 'bessie' else 'user'
            history.append({'role': role, 'content': msg['content']})

        logging.info(f"Retrieved history ({len(history)} messages) for thread {thread_id}")
        return history, dict(problem_info) # Convert Row object to dict
    except sqlite3.Error as e:
        logging.error(f"Database error getting history for thread {thread_id}: {e}", exc_info=True)
        return [], None
    finally:
        if conn:
            conn.close()

def update_conversation_state(thread_id, new_state):
    """Updates the state of a conversation (e.g., to 'solved')."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = datetime.datetime.now()
        cursor.execute('''
            UPDATE conversations SET state = ?, last_update = ? WHERE thread_id = ?
        ''', (new_state, timestamp, thread_id))
        conn.commit()
        logging.info(f"Updated state for thread {thread_id} to '{new_state}'")
        return True
    except sqlite3.Error as e:
        logging.error(f"Database error updating state for thread {thread_id} to {new_state}: {e}", exc_info=True)
        return False
    finally:
        if conn:
            conn.close()


# --- LLM Interaction ---
def get_llm_response_with_history(thread_id, history, problem_info, new_student_message):
    """Gets LLM response considering conversation history and evaluation task."""
    if not OLLAMA_MODEL:
        logging.error("OLLAMA_MODEL environment variable not set.")
        return "Oh dear, my settings seem to be misplaced. Can't think right now.", False

    logging.info(f"Getting LLM response for thread {thread_id} (model: {OLLAMA_MODEL})")

    # Combine persona prompt with task-specific instructions
    system_prompt_combined = f"""{GRANDMA_PERSONA_PROMPT}

Your current specific problem is: {problem_info['problem_description']}
The correct technical solution involves these ideas: {problem_info['correct_solution']}

You are evaluating the student's latest email based on the conversation history and the correct solution.
"""

    # Structure the final user message for the LLM to include the evaluation task
    evaluation_prompt = f"""Here is the latest email from the student:
---
{new_student_message}
---
Now, evaluate the student's message. Does it suggest the correct solution related to '{problem_info['correct_solution']}'?
Consider the whole conversation history provided.

If YES, the student solved it: Reply as Bessie, confirming their advice worked, express thanks, maybe mention Mittens or tea, and politely end the support session. IMPORTANT: Start your response *only* with the exact phrase "SUCCESS: ".
If NO, the student has not solved it yet: Reply as Bessie, staying in character. Respond naturally to their message. You might be confused by their suggestion, mention you tried something similar, or gently steer them back by describing a symptom vaguely. Do NOT reveal the correct answer. Do NOT start your response with "SUCCESS: ".
"""

    # Build the message list for Ollama API
    messages = [{'role': 'system', 'content': system_prompt_combined}]
    messages.extend(history) # Add past messages
    messages.append({'role': 'user', 'content': evaluation_prompt}) # Add the latest student message + evaluation task

    try:
        logging.debug(f"Sending messages to Ollama for thread {thread_id}: {messages}")
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={'temperature': 0.75, 'num_predict': 350}, # Max tokens/predictions
            **ollama_client_args # Pass host if defined
        )
        raw_reply = response['message']['content'].strip()
        logging.debug(f"Raw reply from Ollama for thread {thread_id}: {raw_reply}")

        # Check for the success marker and extract the clean reply
        is_solved = raw_reply.startswith("SUCCESS:")
        bessie_reply = raw_reply.removeprefix("SUCCESS:").strip()

        if not bessie_reply: # Handle case where LLM only outputs the marker
             bessie_reply = "Oh, well isn't that something! Thank you kindly, dear." if is_solved else "Oh dear, I'm not quite sure what to make of that."
             logging.warning(f"LLM reply was empty after removing marker for thread {thread_id}. Using fallback.")

        logging.info(f"LLM generated reply for thread {thread_id}. Solved: {is_solved}")
        return bessie_reply, is_solved

    except ollama.ResponseError as e:
         logging.error(f"Ollama API Error for thread {thread_id}: {e.error} (Status: {e.status_code})", exc_info=True)
         return "Oh dear, my thinking cap seems to have gone fuzzy. Could you say that again?", False
    except ConnectionRefusedError:
         logging.error(f"Connection to Ollama server ({ollama_client_args.get('host', 'http://localhost:11434')}) refused.")
         return "It seems the line is busy... I can't quite connect right now. Maybe later?", False
    except Exception as e:
        logging.error(f"Unexpected error calling Ollama LLM for thread {thread_id}: {e}", exc_info=True)
        return "Oh dear, I seem to have misplaced my thoughts... could you try again in a moment?", False

# --- Email Utility Functions ---
def decode_header_simple(header_value):
    """Safely decodes email headers."""
    if header_value is None:
        return ""
    try:
        decoded_parts = decode_header(header_value)
        return str(make_header(decoded_parts))
    except Exception as e:
        logging.warning(f"Could not decode header '{header_value}': {e}. Returning raw value.")
        # Fallback: attempt simple decoding or return raw string
        try:
            return str(header_value)
        except: # Handle potential errors converting unusual objects to string
             return repr(header_value)

def get_email_body(msg):
    """Extracts the plain text body from an email.message.Message object."""
    body = ""
    if msg.is_multipart():
        # Walk through parts to find the first text/plain part
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            # Check if it's text/plain and not an attachment
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                try:
                    # Decode using specified charset or fallback to utf-8
                    charset = part.get_content_charset('utf-8')
                    body = part.get_payload(decode=True).decode(charset, errors='replace')
                    break # Found the plain text body, stop searching
                except Exception as e:
                    logging.warning(f"Could not decode part with charset {part.get_content_charset()}: {e}. Trying utf-8 fallback.")
                    try:
                        # Fallback decoding attempt
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
                    except Exception as e2:
                         logging.error(f"Could not decode email part even with fallback: {e2}")
                         body = "[Could not read message content]"
                         break
    else:
        # Not multipart, get the payload directly if it's text/plain
        ctype = msg.get_content_type()
        if ctype == 'text/plain':
             try:
                charset = msg.get_content_charset('utf-8')
                body = msg.get_payload(decode=True).decode(charset, errors='replace')
             except Exception as e:
                logging.warning(f"Could not decode non-multipart message with charset {msg.get_content_charset()}: {e}. Trying utf-8 fallback.")
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                except Exception as e2:
                     logging.error(f"Could not decode non-multipart email message: {e2}")
                     body = "[Could not read message content]"
        else:
             logging.warning(f"Non-multipart message is not text/plain (type: {ctype}). Cannot extract body.")
             body = "[Message is not plain text]"


    # Basic cleaning: remove common reply quoting prefixes
    cleaned_body = "\n".join([line for line in body.splitlines() if not line.strip().startswith('>')])
    # Further cleaning: remove lines like "On [Date], [Sender] wrote:" - simple version
    cleaned_body = "\n".join([line for line in cleaned_body.splitlines() if not (line.strip().startswith('On ') and 'wrote:' in line)])

    return cleaned_body.strip()

# --- Core Email Processing Functions ---
def send_reply(recipient, subject, body, incoming_message_id=None, references_header=None):
    """Sends an email reply using SMTP, setting correct threading headers."""
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT]):
        logging.error("Missing SMTP configuration (address, password, server, port). Cannot send email.")
        return None # Indicate failure

    msg = EmailMessage()
    # Format Subject: Prepend "Re:" if not already there
    safe_subject = subject if subject else ""
    if not safe_subject.lower().startswith("re:"):
         msg['Subject'] = f"Re: {safe_subject}"
    else:
         msg['Subject'] = safe_subject

    # Set sender and recipient
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = recipient

    # Generate a unique Message-ID for this outgoing email
    domain_part = EMAIL_ADDRESS.split('@')[-1] if EMAIL_ADDRESS and '@' in EMAIL_ADDRESS else 'bessie.bot'
    new_message_id = email.utils.make_msgid(domain=domain_part)
    msg['Message-ID'] = new_message_id

    # Set Threading Headers
    if incoming_message_id:
        msg['In-Reply-To'] = incoming_message_id
        # Construct References: Append incoming ID to existing References chain
        if references_header:
            # Ensure incoming_message_id is not already the last ref
            if not references_header.strip().endswith(incoming_message_id):
                 msg['References'] = f"{references_header.strip()} {incoming_message_id}"
            else:
                 msg['References'] = references_header.strip()
        else:
            # If no prior References, start the chain with In-Reply-To ID
            msg['References'] = incoming_message_id
    # If it's the *first* email (no incoming_message_id), no In-Reply-To or References are set.

    # Set email body content
    msg.set_content(body)

    # Send the email
    try:
        logging.info(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.ehlo() # Identify client to ESMTP server
            server.starttls() # Upgrade connection to secure TLS
            server.ehlo() # Re-identify client over TLS connection
            logging.info("Logging into SMTP server...")
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            logging.info(f"Sending email to: {recipient} | Subject: {msg['Subject']} | New Message-ID: {new_message_id}")
            server.send_message(msg)
            logging.info("Email sent successfully.")
            return new_message_id # Return the ID of the message we sent
    except smtplib.SMTPAuthenticationError as e:
        logging.error(f"SMTP Authentication Error: {e}. Check email address/password (App Password for Gmail) in .env.")
        return None
    except smtplib.SMTPException as e:
         logging.error(f"SMTP Error sending email: {e}", exc_info=True)
         return None
    except OSError as e: # Catch socket errors, timeouts
        logging.error(f"Network/OS Error sending email: {e}", exc_info=True)
        return None
    except Exception as e:
        logging.error(f"Unexpected error sending email: {e}", exc_info=True)
        return None

def check_emails():
    """Checks for new emails, processes them based on threading, and triggers replies."""
    if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER]):
        logging.error("Missing IMAP configuration (address, password, server). Cannot check emails.")
        return # Don't proceed if config is missing

    mail = None
    processed_email_ids = set() # Track successfully processed emails in this run

    try:
        logging.info(f"Connecting to IMAP server: {IMAP_SERVER}")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        logging.info("Logging into IMAP server...")
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select('inbox')
        logging.info("INBOX selected.")

        # Search for unseen emails
        status, search_data = mail.search(None, 'UNSEEN')
        if status != 'OK':
            logging.error(f"IMAP search command failed with status: {status}")
            mail.logout()
            return

        email_ids = search_data[0].split()
        if not email_ids or email_ids == [b'']:
            logging.info("No unseen emails found.")
            mail.logout()
            return

        logging.info(f"Found {len(email_ids)} unseen emails.")

        # Process emails one by one
        for email_id_bytes in email_ids:
            email_id_str = email_id_bytes.decode()
            logging.info(f"--- Processing email ID: {email_id_str} ---")

            try:
                status, msg_data = mail.fetch(email_id_bytes, '(RFC822)')
                if status != 'OK':
                    logging.error(f"Failed to fetch email ID: {email_id_str} with status {status}")
                    continue # Skip to next email

                # msg_data is list of tuples, typically [(b'id (RFC822 {size}', email_bytes), b')']
                raw_email = None
                for response_part in msg_data:
                    if isinstance(response_part, tuple) and len(response_part) > 1 and isinstance(response_part[1], bytes):
                        raw_email = response_part[1]
                        break # Found the email bytes

                if not raw_email:
                     logging.error(f"Could not extract raw email bytes for ID: {email_id_str}")
                     continue

                msg = email.message_from_bytes(raw_email)

                # Extract key information
                subject = decode_header_simple(msg.get('Subject'))
                sender_tuple = email.utils.parseaddr(msg.get('From'))
                sender_email = sender_tuple[1] # Email address part
                incoming_message_id = msg.get('Message-ID')
                references = msg.get('References') # Keep original header value

                logging.info(f"From: {sender_email} | Subject: {subject} | Message-ID: {incoming_message_id}")

                # --- Basic Filtering ---
                if not sender_email or sender_email == EMAIL_ADDRESS or 'mailer-daemon' in sender_email.lower() or 'noreply' in sender_email.lower():
                    logging.warning(f"Skipping email ID {email_id_str} from '{sender_email}' (self, bounce, no-reply, or missing sender). Marking as seen.")
                    mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                    processed_email_ids.add(email_id_bytes)
                    continue

                email_body = get_email_body(msg)
                if not email_body or email_body == "[Could not read message content]" or email_body == "[Message is not plain text]":
                    logging.warning(f"Email body is empty or unreadable for ID {email_id_str}. Skipping. Marking as seen.")
                    mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                    processed_email_ids.add(email_id_bytes)
                    continue

                # --- Threading and Processing Logic ---
                thread_id = find_conversation_thread_id(msg)

                if thread_id:
                    # --- Existing Conversation ---
                    logging.info(f"Email {incoming_message_id} belongs to existing active thread {thread_id}")

                    # 1. Add student's message to DB
                    if not add_message_to_db(thread_id, incoming_message_id, 'student', email_body):
                         logging.error(f"Failed to add student message {incoming_message_id} to DB for thread {thread_id}. Aborting processing for this email.")
                         continue # Skip to next email if DB add fails

                    # 2. Get history and problem info
                    history, problem_info = get_conversation_history(thread_id)
                    if not problem_info:
                         logging.error(f"Could not retrieve conversation details for thread {thread_id}. Cannot reply.")
                         # Don't mark as seen, needs investigation
                         continue

                    # 3. Get LLM response based on history
                    reply_body, is_solved = get_llm_response_with_history(thread_id, history, problem_info, email_body)

                    # 4. Send reply (if LLM succeeded)
                    if reply_body:
                        bessie_message_id = send_reply(sender_email, subject, reply_body, incoming_message_id, references)
                        if bessie_message_id:
                            # 5. Add Bessie's reply to DB
                            add_message_to_db(thread_id, bessie_message_id, 'bessie', reply_body)
                            # 6. Update state if solved
                            if is_solved:
                                update_conversation_state(thread_id, 'solved')
                            # 7. Mark student's email as seen (SUCCESS!)
                            mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                            processed_email_ids.add(email_id_bytes)
                            logging.info(f"Successfully processed and replied to email {email_id_str} in thread {thread_id}.")
                        else:
                             logging.error(f"Failed to send reply for thread {thread_id}. Student message {incoming_message_id} NOT marked as seen.")
                             # Don't mark as seen, allow retry on next run
                    else:
                        logging.error(f"Failed to get LLM response for thread {thread_id}. Student email {email_id_str} NOT marked as seen.")
                        # Don't mark as seen

                else:
                    # --- Potentially New Conversation ---
                    start_command = "start training" # Case-insensitive check below
                    if subject and start_command in subject.lower():
                        logging.info(f"Received start command from {sender_email} (Subject: '{subject}')")
                        # 1. Select a random problem
                        problem = random.choice(PROBLEMS_CATALOG)
                        # 2. Start a new conversation in DB
                        new_thread_id = add_new_conversation(sender_email, problem)

                        if new_thread_id:
                            # 3. Add student's initial request message to DB (optional but good practice)
                            add_message_to_db(new_thread_id, incoming_message_id, 'student', email_body)

                            # 4. Get Bessie's initial problem description prompt
                            initial_reply_body = problem['initial_bessie_prompt']

                            # 5. Send Bessie's *first* email (establishes the thread)
                            # For the first email, incoming_message_id and references are None
                            bessie_message_id = send_reply(sender_email, subject, initial_reply_body, None, None)

                            if bessie_message_id:
                                # Check if the sent ID matches the intended thread_id (it should!)
                                if bessie_message_id != new_thread_id:
                                     logging.warning(f"Message-ID mismatch! DB thread_id: {new_thread_id}, Sent ID: {bessie_message_id}. This might indicate an issue.")
                                     # If this happens, the DB conversation record needs fixing or careful handling
                                     # For now, just log the message we *actually* sent
                                     add_message_to_db(new_thread_id, bessie_message_id, 'bessie', initial_reply_body)
                                else:
                                    # 6. Add Bessie's initial message to DB using the correct thread_id/message_id
                                    add_message_to_db(new_thread_id, bessie_message_id, 'bessie', initial_reply_body)

                                logging.info(f"Sent initial problem description for new thread {new_thread_id}")
                                # 7. Mark student's start command email as seen (SUCCESS!)
                                mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                                processed_email_ids.add(email_id_bytes)
                            else:
                                logging.error(f"Failed to send initial problem for new thread {new_thread_id}. Start command email {email_id_str} NOT marked as seen.")
                                # Could attempt to delete the conversation record from DB if the first send fails
                        else:
                            logging.error(f"Failed to create new conversation in DB for {sender_email}. Start command email {email_id_str} NOT marked as seen.")
                    else:
                        # --- Unrecognized Email (Not a start command, not part of active thread) ---
                        logging.warning(f"Received email ID {email_id_str} from {sender_email} with subject '{subject}' - not an active thread or start command. Ignoring. Marking as seen.")
                        mail.store(email_id_bytes, '+FLAGS', '\\Seen')
                        processed_email_ids.add(email_id_bytes)

            except Exception as processing_error:
                 logging.error(f"Unhandled error processing email ID {email_id_str}: {processing_error}", exc_info=True)
                 # Avoid marking as seen on generic errors, allow retry unless it's clearly unrecoverable

        logging.info(f"Finished processing batch. Processed {len(processed_email_ids)} emails successfully in this run.")
        mail.logout()
        logging.info("IMAP logout successful.")

    except imaplib.IMAP4.error as e:
        if "AUTHENTICATIONFAILED" in str(e).upper():
             logging.error(f"IMAP Authentication Failed: {e}. Check email/password/app password in .env.")
             # Consider adding a longer sleep or notification if auth fails repeatedly
        else:
             logging.error(f"IMAP Error during session: {e}", exc_info=True)
    except OSError as e: # Catch socket errors, timeouts during connection/login
         logging.error(f"Network/OS Error during IMAP connection/session: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"An unexpected error occurred in check_emails main loop: {e}", exc_info=True)
        # Ensure logout happens even on unexpected error if mail object exists and is logged in
        try:
            if mail and mail.state == 'SELECTED':
                mail.logout()
                logging.info("IMAP logout performed after unexpected error.")
        except Exception as logout_err:
            logging.error(f"Error during forced logout after exception: {logout_err}")


# --- Main Execution Block ---
if __name__ == "__main__":
    logging.info("Script started.")

    # --- Mode Selection ---
    if RUN_EMAIL_BOT:
        logging.info("--- Running in Email Bot Mode ---")
        # --- Essential Config Checks ---
        if not all([EMAIL_ADDRESS, EMAIL_PASSWORD, OLLAMA_MODEL]):
            logging.critical("Missing critical configuration in .env: BOT_EMAIL_ADDRESS, BOT_EMAIL_PASSWORD, or OLLAMA_MODEL.")
            exit("ERROR: Configuration incomplete. Exiting.")
        if not OLLAMA_MODEL:
             logging.critical("OLLAMA_MODEL not set in .env file.")
             exit("ERROR: Ollama model not specified. Exiting.")

        # --- Initialize Database ---
        try:
            init_db()
        except Exception as db_init_err:
             logging.critical(f"Failed to initialize database: {db_init_err}. Exiting.")
             exit("ERROR: Database initialization failed.")

        # --- Verify Ollama Connection (Optional but Recommended) ---
        try:
             logging.info(f"Checking connection to Ollama and model '{OLLAMA_MODEL}'...")
             # Try listing models or getting model info to test connection/model presence
             ollama.show(OLLAMA_MODEL, **ollama_client_args)
             logging.info(f"Successfully connected to Ollama and model '{OLLAMA_MODEL}' found.")
        except ollama.ResponseError as e:
             logging.critical(f"Ollama Error: Failed to find or connect to model '{OLLAMA_MODEL}'. Error: {e.error}. Status: {e.status_code}")
             exit(f"ERROR: Ollama model '{OLLAMA_MODEL}' not found or connection failed.")
        except ConnectionRefusedError:
             logging.critical(f"Ollama Error: Connection refused at {ollama_client_args.get('host', 'default host')}. Is Ollama running?")
             exit("ERROR: Cannot connect to Ollama.")
        except Exception as ollama_conn_err:
             logging.critical(f"Ollama Error: Unexpected error connecting to Ollama: {ollama_conn_err}")
             exit("ERROR: Ollama connection failed.")

        # --- Main Email Check Loop ---
        logging.info("Starting main email checking loop...")
        while True:
            try:
                check_emails()
            except Exception as loop_error:
                # Catch potential errors in the loop itself to prevent crashing
                logging.error(f"Critical error in main email loop: {loop_error}", exc_info=True)
                # Implement more robust recovery or notification if needed (e.g., exponential backoff)

            sleep_interval = 60 # Check every 60 seconds
            logging.info(f"Sleeping for {sleep_interval} seconds...")
            time.sleep(sleep_interval)

    else:
        # --- Command-Line Test Mode ---
        logging.info(f"--- Running in Command-Line Test Mode (Model: {OLLAMA_MODEL} at {ollama_client_args.get('host', 'default localhost')}) ---")
        logging.info("This mode simulates conversations without checking/sending emails.")
        logging.info("Enter the 'email content' Bessie should reply to. Type 'quit' to exit.")

        if not OLLAMA_MODEL:
            logging.critical("OLLAMA_MODEL not set in .env file.")
            exit("Environment variable missing.")

        # Verify Ollama connection once at the start of test mode
        try:
            ollama.list(**ollama_client_args)
            logging.info("Successfully connected to Ollama.")
        except Exception as conn_err:
             logging.error(f"Failed to connect to Ollama on startup: {conn_err}. Please ensure Ollama is running and accessible.")
             exit("Ollama connection failed.")

        # Simulate an ongoing conversation (in-memory for testing)
        test_history = []
        problem = random.choice(PROBLEMS_CATALOG)
        test_problem_info = {'problem_description': problem['description'], 'correct_solution': problem['solution_keywords']}
        test_thread_id = f"test-thread-{random.randint(1000,9999)}"
        print(f"\n--- Starting Test Scenario ---")
        print(f"Bessie's Problem: {test_problem_info['problem_description']}")
        print(f"(Solution hint: {test_problem_info['correct_solution']})")
        print(f"Bessie's Initial Prompt:\n{problem['initial_bessie_prompt']}\n")
        # Add Bessie's first message to history
        test_history.append({'role': 'assistant', 'content': problem['initial_bessie_prompt']})


        while True:
            try:
                user_input = input(f"Student Reply (Thread: {test_thread_id}) > ")
                if user_input.lower() == 'quit':
                    break
                if not user_input:
                    continue

                # Add student's message to history for next turn
                test_history.append({'role': 'user', 'content': user_input})

                # Get response using the history-aware function
                bessie_response, is_solved = get_llm_response_with_history(test_thread_id, test_history, test_problem_info, user_input)

                print("\n--- Bessie's Reply ---")
                print(bessie_response)
                print("----------------------\n")

                 # Add Bessie's reply to history for next turn
                test_history.append({'role': 'assistant', 'content': bessie_response})

                if is_solved:
                    print("--- Scenario SOLVED! Starting new scenario. ---")
                    # Reset for a new scenario
                    test_history = []
                    problem = random.choice(PROBLEMS_CATALOG)
                    test_problem_info = {'problem_description': problem['description'], 'correct_solution': problem['solution_keywords']}
                    test_thread_id = f"test-thread-{random.randint(1000,9999)}"
                    print(f"\n--- Starting Test Scenario ---")
                    print(f"Bessie's Problem: {test_problem_info['problem_description']}")
                    print(f"(Solution hint: {test_problem_info['correct_solution']})")
                    print(f"Bessie's Initial Prompt:\n{problem['initial_bessie_prompt']}\n")
                    test_history.append({'role': 'assistant', 'content': problem['initial_bessie_prompt']})


            except KeyboardInterrupt:
                print("\nExiting test mode.")
                break
            except Exception as test_error:
                logging.error(f"Error during CLI test: {test_error}", exc_info=True)
                # Add a small delay to prevent rapid error loops if input causes consistent failure
                time.sleep(1)

        logging.info("--- Exited Command-Line Test Mode ---")

    logging.info("Script finished.")