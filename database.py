import sqlite3
import logging
import datetime
from contextlib import contextmanager
from config import DB_FILE, COMPLETED_DB_FILE, DEBUG_DB_FILE

# --- Database Context Manager ---
@contextmanager
def get_db_connection(db_file):
    """A context manager for safe database connections."""
    conn = sqlite3.connect(db_file)
    try:
        yield conn
    except sqlite3.Error as e:
        logging.error(f"Database error in '{db_file}': {e}", exc_info=True)
        raise  # Re-raise the exception after logging
    finally:
        conn.close()

# --- Database Initialization Functions ---
def initialize_database(db_file, schema_sql, db_name_for_logging):
    """Initializes a database with a given schema."""
    try:
        with get_db_connection(db_file) as conn:
            cursor = conn.cursor()
            cursor.executescript(schema_sql)
            conn.commit()
        logging.info(f"Database {db_file} for {db_name_for_logging} initialized/verified.")
    except sqlite3.Error:
        # Error is logged by context manager, re-raise to halt execution if needed
        logging.critical(f"FATAL: Initialization of {db_name_for_logging} DB failed.")
        raise

def init_db():
    """Initialize the main database with student progress and active problems tables."""
    MAIN_DB_SCHEMA = '''
        CREATE TABLE IF NOT EXISTS student_progress (
            student_email TEXT PRIMARY KEY,
            next_level_index INTEGER NOT NULL DEFAULT 0,
            last_completed_problem_id TEXT,
            last_active_graph_convo_id TEXT
        );
        CREATE TABLE IF NOT EXISTS active_problems (
            student_email TEXT PRIMARY KEY,
            problem_id TEXT NOT NULL,
            conversation_history TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_email) REFERENCES student_progress(student_email)
        );
    '''
    initialize_database(DB_FILE, MAIN_DB_SCHEMA, "main progress")

def init_completed_db():
    """Initialize the completed conversations archive database."""
    COMPLETED_DB_SCHEMA = '''
        CREATE TABLE IF NOT EXISTS completed_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            problem_level_index INTEGER NOT NULL,
            full_conversation_history TEXT NOT NULL,
            evaluator_response TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    '''
    initialize_database(COMPLETED_DB_FILE, COMPLETED_DB_SCHEMA, "completed archives")

def init_debug_db():
    """Initialize the debug conversations database."""
    DEBUG_DB_SCHEMA = '''
        CREATE TABLE IF NOT EXISTS debug_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            problem_level_index INTEGER NOT NULL,
            full_conversation_history TEXT NOT NULL,
            evaluator_responses TEXT NOT NULL,  -- JSON array of all evaluator interactions
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    '''
    initialize_database(DEBUG_DB_FILE, DEBUG_DB_SCHEMA, "debug logs")

# --- Database Operation Functions ---
def save_debug_conversation(student_email, problem_id, problem_level_index, history_string, evaluator_responses):
    """Save or update debug conversation with evaluator responses."""
    try:
        with get_db_connection(DEBUG_DB_FILE) as conn:
            cursor = conn.cursor()

            # Check if conversation already exists
            cursor.execute('''
                SELECT id FROM debug_conversations
                WHERE student_email = ? AND problem_id = ?
            ''', (student_email, problem_id))

            existing = cursor.fetchone()

            if existing:
                # Update existing conversation
                cursor.execute('''
                    UPDATE debug_conversations
                    SET full_conversation_history = ?, evaluator_responses = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (history_string, evaluator_responses, existing[0]))
            else:
                # Insert new conversation
                cursor.execute('''
                    INSERT INTO debug_conversations
                    (student_email, problem_id, problem_level_index, full_conversation_history, evaluator_responses)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_email, problem_id, problem_level_index, history_string, evaluator_responses))

            conn.commit()
        logging.info(f"Debug-konversation sparad för {student_email} (Problem: {problem_id})")
        return True
    except sqlite3.Error:
        return False

def save_completed_conversation(student_email, problem_id, problem_level_index, full_conversation_history, evaluator_response=None):
    try:
        with get_db_connection(COMPLETED_DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO completed_conversations
                (student_email, problem_id, problem_level_index, full_conversation_history)
                VALUES (?, ?, ?, ?)
            ''', (student_email, problem_id, problem_level_index, full_conversation_history))
            conn.commit()
        logging.info(f"Arkiverade slutförd konversation för {student_email} (Problem: {problem_id})")
        return True
    except sqlite3.Error:
        return False

def get_student_progress(student_email):
    try:
        with get_db_connection(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT next_level_index, last_active_graph_convo_id FROM student_progress WHERE student_email = ?", (student_email,))
            row = cursor.fetchone()
            if row:
                return row['next_level_index'], row['last_active_graph_convo_id']
            logging.info(f"Student {student_email} ej hittad i progress, skapar ny post på nivå 0.")
            cursor.execute("INSERT OR IGNORE INTO student_progress (student_email, next_level_index) VALUES (?, ?)", (student_email, 0))
            conn.commit()
            return 0, None
    except sqlite3.Error:
        return 0, None

def update_student_level(student_email, new_next_level_index, last_completed_id=None):
    try:
        with get_db_connection(DB_FILE) as conn:
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
    except sqlite3.Error:
        return False

def set_active_problem(student_email, problem, problem_level_idx, graph_conversation_id):
    try:
        current_level_for_insert, _ = get_student_progress(student_email)
        with get_db_connection(DB_FILE) as conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now()
            initial_history_string = f"Ulla: {problem['start_prompt']}\n\n"

            cursor.execute(
                "INSERT INTO student_progress (student_email, next_level_index, last_active_graph_convo_id) VALUES (?, ?, ?) "
                "ON CONFLICT(student_email) DO UPDATE SET last_active_graph_convo_id = excluded.last_active_graph_convo_id",
                (student_email, current_level_for_insert, graph_conversation_id)
            )
            # SIMPLIFIED: Only inserts the ID and the history.
            cursor.execute('''
                REPLACE INTO active_problems
                (student_email, problem_id, conversation_history, created_at)
                VALUES (?, ?, ?, ?)
            ''', (student_email, problem['id'], initial_history_string, timestamp))

            conn.commit()
        # Initialize debug conversation with empty evaluator responses
        save_debug_conversation(student_email, problem['id'], problem_level_idx, initial_history_string, "[]")

        logging.info(f"Aktivt problem {problem['id']} (Nivå {problem_level_idx + 1}) satt för {student_email}")
        return True
    except sqlite3.Error:
        return False

def find_problem_by_id(problem_id):
    from problem_catalog import PROBLEM_CATALOGUES

    for level_idx, level_catalogue in enumerate(PROBLEM_CATALOGUES):
        for problem in level_catalogue:
            if problem['id'] == problem_id:
                return problem, level_idx
    return None, -1

def get_current_active_problem(student_email):
    # This helper function finds a problem by ID from the in-memory catalogue.
    from problem_catalog import PROBLEM_CATALOGUES

    def find_problem_by_id_local(problem_id):
        for level_idx, level_catalogue in enumerate(PROBLEM_CATALOGUES):
            for problem in level_catalogue:
                if problem['id'] == problem_id:
                    return problem, level_idx
        return None, -1

    try:
        with get_db_connection(DB_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Get the active problem ID and history from the DB
            cursor.execute('''
                SELECT ap.problem_id, ap.conversation_history, sp.last_active_graph_convo_id
                FROM active_problems ap
                LEFT JOIN student_progress sp ON ap.student_email = sp.student_email
                WHERE ap.student_email = ?
            ''', (student_email,))
            row = cursor.fetchone()

            if row:
                problem_id = row['problem_id']
                history_string = row['conversation_history']
                active_graph_convo_id = row['last_active_graph_convo_id']

                # 2. Look up the full problem details from the in-memory catalogue
                problem_info, level_idx = find_problem_by_id_local(problem_id)

                if problem_info:
                    return history_string, problem_info, level_idx, active_graph_convo_id
                else:
                    logging.error(f"DB Inconsistency! Active problem ID '{problem_id}' for {student_email} not found in PROBLEM_CATALOGUES.")
                    return None, None, None, None # Indicate failure

            # No active problem found for the student
            return None, None, None, None
    except sqlite3.Error:
        return None, None, None, None

def append_to_active_problem_history(student_email, text_to_append):
    try:
        with get_db_connection(DB_FILE) as conn:
            cursor = conn.cursor()
            if not text_to_append.endswith("\n\n"): text_to_append += "\n\n"
            cursor.execute("UPDATE active_problems SET conversation_history = conversation_history || ? WHERE student_email = ?", (text_to_append, student_email))

            # Also update debug conversation history
            cursor.execute("SELECT problem_id FROM active_problems WHERE student_email = ?", (student_email,))
            problem_row = cursor.fetchone()
            if problem_row:
                problem_id = problem_row[0]
                # Get current debug conversation
                try:
                    with get_db_connection(DEBUG_DB_FILE) as debug_conn:
                        debug_cursor = debug_conn.cursor()
                        debug_cursor.execute("SELECT full_conversation_history, evaluator_responses FROM debug_conversations WHERE student_email = ? AND problem_id = ?", (student_email, problem_id))
                        debug_row = debug_cursor.fetchone()
                        if debug_row:
                            current_history = debug_row[0] + text_to_append
                            # Update debug conversation with history only
                            debug_cursor.execute('''
                                UPDATE debug_conversations
                                SET full_conversation_history = ?, last_updated = CURRENT_TIMESTAMP
                                WHERE student_email = ? AND problem_id = ?
                            ''', (current_history, student_email, problem_id))
                            debug_conn.commit()
                except sqlite3.Error:
                    pass  # Silently ignore debug DB errors here

            conn.commit()
        logging.info(f"Lade till i historik för aktivt problem för {student_email}")
        return True
    except sqlite3.Error:
        return False

def clear_active_problem(student_email):
    try:
        with get_db_connection(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM active_problems WHERE student_email = ?", (student_email,))
            deleted_rows = cursor.rowcount
            cursor.execute("UPDATE student_progress SET last_active_graph_convo_id = NULL WHERE student_email = ?", (student_email,))
            conn.commit()
        if deleted_rows > 0: logging.info(f"Rensade aktivt problem för {student_email}"); return True
        logging.info(f"Inget aktivt problem att rensa för {student_email}, men säkerställde att convo ID är rensat i progress.")
        return True
    except sqlite3.Error:
        return False

def append_evaluator_response_to_debug(student_email, problem_id, evaluator_response_text):
    """
    Appends a new evaluator response to the JSON array in the debug database for a specific conversation.
    """
    import json
    try:
        with get_db_connection(DEBUG_DB_FILE) as conn:
            cursor = conn.cursor()

            # 1. Get the current JSON array of responses
            cursor.execute('''
                SELECT evaluator_responses FROM debug_conversations
                WHERE student_email = ? AND problem_id = ?
            ''', (student_email, problem_id))

            row = cursor.fetchone()
            if not row:
                logging.warning(f"Debug DB: No active conversation found for {student_email} (Problem: {problem_id}) to append evaluator response.")
                return False

            # 2. Decode the JSON, append the new response, and re-encode
            try:
                evaluator_responses_list = json.loads(row[0])
            except json.JSONDecodeError:
                evaluator_responses_list = [] # Start fresh if data is corrupt

            new_response_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "response": evaluator_response_text
            }
            evaluator_responses_list.append(new_response_entry)

            new_evaluator_responses_json = json.dumps(evaluator_responses_list)

            # 3. Update the database with the new JSON array
            cursor.execute('''
                UPDATE debug_conversations
                SET evaluator_responses = ?, last_updated = CURRENT_TIMESTAMP
                WHERE student_email = ? AND problem_id = ?
            ''', (new_evaluator_responses_json, student_email, problem_id))

            conn.commit()
        logging.info(f"Appended evaluator response to debug conversation for {student_email} (Problem: {problem_id})")
        return True
    except sqlite3.Error:
        # The context manager will log the detailed error.
        return False
def print_db_content(email_filter=None):
    if email_filter:
        print(f"--- DB UTSKRIFT (Filtrerat på: {email_filter}) ---")
    else:
        print("--- DB UTSKRIFT (All data) ---")

    # --- 1. Print Student Progress ---
    print("\n--- UTSKRIFT STUDENT PROGRESS ---")
    try:
        with get_db_connection(DB_FILE) as conn_pdb:
            conn_pdb.row_factory = sqlite3.Row; c_pdb = conn_pdb.cursor()
            query = "SELECT * FROM student_progress ORDER BY student_email"
            params = []
            if email_filter:
                query = "SELECT * FROM student_progress WHERE student_email = ?"
                params.append(email_filter)
            c_pdb.execute(query, params)
            rows_pdb = c_pdb.fetchall()
            if not rows_pdb: print("Tabellen student_progress är tom (eller inget matchar filter).")
            else:
                for r_pdb in rows_pdb: print(dict(r_pdb))
    except Exception as e_pdb: print(f"Fel vid utskrift av student_progress: {e_pdb}")

    # --- 2. Print Active Problems ---
    print("\n--- UTSKRIFT ACTIVE PROBLEMS ---")
    try:
        with get_db_connection(DB_FILE) as conn_apdb:
            conn_apdb.row_factory = sqlite3.Row; c_apdb = conn_apdb.cursor()
            query = "SELECT * FROM active_problems ORDER BY student_email"
            params = []
            if email_filter:
                query = "SELECT * FROM active_problems WHERE student_email = ?"
                params.append(email_filter)
            c_apdb.execute(query, params)
            rows_apdb = c_apdb.fetchall()
            if not rows_apdb: print("Tabellen active_problems är tom (eller inget matchar filter).")
            else:
                for r_apdb in rows_apdb:
                    d = dict(r_apdb)
                    problem_id = d.get('problem_id')
                    # Find the level index from the in-memory catalogue
                    level_idx = find_problem_by_id(problem_id)[1] if find_problem_by_id(problem_id)[0] else -1
                    level_display = level_idx + 1 if level_idx != -1 else "N/A"
                    print(f"Student: {d.get('student_email')}, Problem ID: {problem_id}, Level: {level_display} (Index: {level_idx})")
                    print(f"  History:\n{d.get('conversation_history', '')}")
    except Exception as e_apdb: print(f"Fel vid utskrift av active_problems: {e_apdb}")

    # --- 3. Print Completed Conversations ---
    print("\n--- UTSKRIFT COMPLETED CONVERSATIONS ---")
    try:
        with get_db_connection(COMPLETED_DB_FILE) as conn_ccdb:
            conn_ccdb.row_factory = sqlite3.Row; c_ccdb = conn_ccdb.cursor()
            query = "SELECT * FROM completed_conversations ORDER BY completed_at DESC"
            params = []
            if email_filter:
                query = "SELECT * FROM completed_conversations WHERE student_email = ? ORDER BY completed_at DESC"
                params.append(email_filter)
            c_ccdb.execute(query, params)
            rows_ccdb = c_ccdb.fetchall()
            if not rows_ccdb: print("Tabellen completed_conversations är tom (eller inget matchar filter).")
            else:
                for r_ccdb in rows_ccdb:
                    d = dict(r_ccdb)
                    level_idx = d.get('problem_level_index', -1)
                    level_display = level_idx + 1 if level_idx != -1 else "N/A"
                    print(f"Student: {d.get('student_email')}, Problem: {d.get('problem_id')}, Level: {level_display} (Index: {level_idx}), Completed: {d.get('completed_at')}")
                    print(f"  Conversation:\n{d.get('full_conversation_history', '')}")
    except Exception as e_ccdb: print(f"Fel vid utskrift av completed_conversations: {e_ccdb}")

    print("\n--- SLUT DB UTSKRIFT ---")


def print_debug_db_content(email_filter=None, problem_filter=None):
    import re
    import json
    if email_filter or problem_filter:
        print(f"--- DEBUG DB UTSKRIFT (Filtrerat på: email={email_filter}, problem={problem_filter}) ---")
    else:
        print("--- DEBUG DB UTSKRIFT (All data) ---")

    # --- Print Debug Conversations ---
    print("\n--- UTSKRIFT DEBUG CONVERSATIONS ---")
    try:
        with get_db_connection(DEBUG_DB_FILE) as conn_ddb:
            conn_ddb.row_factory = sqlite3.Row; c_ddb = conn_ddb.cursor()
            query = "SELECT * FROM debug_conversations ORDER BY id ASC"
            params = []
            if email_filter:
                query = "SELECT * FROM debug_conversations WHERE student_email = ? ORDER BY id ASC"
                params.append(email_filter)
            elif problem_filter:
                query = "SELECT * FROM debug_conversations WHERE problem_id = ? ORDER BY id ASC"
                params.append(problem_filter)
            c_ddb.execute(query, params)
            rows_ddb = c_ddb.fetchall()
            if not rows_ddb: print("Tabellen debug_conversations är tom (eller inget matchar filter).")
            else:
                for r_ddb in rows_ddb:
                    d = dict(r_ddb)
                    level_idx = d.get('problem_level_index', -1)
                    level_display = level_idx + 1 if level_idx != -1 else "N/A"
                    print(f"Student: {d.get('student_email')}, Problem: {d.get('problem_id')}, Level: {level_display} (Index: {level_idx})")
                    print(f"  Last Updated: {d.get('last_updated')}")

                    # --- CORRECTED LOGIC (v5) ---
                    # Get the raw data
                    conversation_history = d.get('full_conversation_history', '')
                    evaluator_responses_json = d.get('evaluator_responses', '[]')
                    evaluator_responses = json.loads(evaluator_responses_json)

                    # Print raw data for debugging
                    print("\n  --- RAW DATA ---")
                    print(f"  Raw Evaluator Responses JSON ({len(evaluator_responses)} entries):")
                    # Use json.dumps for pretty printing the raw JSON
                    print(json.dumps(evaluator_responses, indent=2, ensure_ascii=False))
                    print("  ----------------\n")

                    print("  Conversation History (Chronological):")
                    print("=" * 60)

                    # 1. Parse all messages from the history string.
                    history_lines = [line.strip() for line in conversation_history.split('\n\n') if line.strip()]

                    # 2. Identify Student Name Prefix
                    student_prefix = None
                    for line in history_lines:
                        if not line.startswith("Ulla:") and not line.lower().startswith("jättebra!") and not line.startswith("Ulla ("):
                             # This is likely the first student message. Extract the name.
                             # Format is usually "Name: Message"
                             parts = line.split(':', 1)
                             if len(parts) > 1:
                                 student_prefix = parts[0] + ":"
                                 break
                    
                    # Fallback if no student prefix found (shouldn't happen in normal flow)
                    if not student_prefix:
                        student_prefix = "Student:" # Generic fallback

                    # 3. Build the final timeline by iterating through history and inserting evaluations sequentially.
                    final_timeline = []
                    evaluator_index = 0

                    for line in history_lines:
                        # Differentiate between Ulla, Student, and final Student Completion messages
                        if line.startswith("Ulla:") or line.startswith("Ulla ("):
                            if not final_timeline: # The very first message is the initial prompt
                                final_timeline.append({'type': 'INITIAL', 'content': line})
                            else:
                                final_timeline.append({'type': 'ULLA', 'content': line})

                        elif line.lower().startswith("jättebra!"):
                            final_timeline.append({'type': 'STUDENT_COMPLETION', 'content': line})

                        elif student_prefix and line.startswith(student_prefix):
                             # This is a standard student message that requires an evaluation
                            final_timeline.append({'type': 'STUDENT', 'content': line})

                            # Immediately add the next available evaluator response in sequence
                            if evaluator_index < len(evaluator_responses):
                                final_timeline.append({'type': 'EVAL', 'data': evaluator_responses[evaluator_index]})
                                evaluator_index += 1
                        
                        else:
                            # If it doesn't start with Ulla, Jättebra, or Student Prefix, it's likely a continuation of the previous message.
                            # We append it to the content of the last message in the timeline.
                            if final_timeline:
                                final_timeline[-1]['content'] += "\n\n" + line
                            else:
                                # Orphaned line at start? Treat as info.
                                print(f"  [INFO] {line}")

                    # 4. Print the correctly assembled timeline.
                    for event in final_timeline:
                        if event['type'] == 'INITIAL':
                            print(f"  [INITIAL] {event['content']}")
                        elif event['type'] == 'STUDENT':
                            print(f"  [STUDENT] {event['content']}")
                        elif event['type'] == 'STUDENT_COMPLETION':
                            print(f"  [STUDENT] {event['content']}")
                        elif event['type'] == 'EVAL':
                            print(f"  [EVALUATOR] {event['data']['timestamp']}:")
                            # Clean up response text from markdown and other artifacts
                            response_text = event['data']['response'].replace('</end_of_turn>', '').strip()
                            response_text = re.sub(r'^```\s*|\s*```$', '', response_text)
                            for line in response_text.split('\n'):
                                if line.strip():
                                    print(f"    {line}")
                        elif event['type'] == 'ULLA':
                            print(f"  [ULLA] {event['content']}")
                        print() # Add a blank line for readability

                    print("-" * 80)
    except Exception as e_ddb: print(f"Fel vid utskrift av debug_conversations: {e_ddb}")

    print("\n--- SLUT DEBUG DB UTSKRIFT ---")


def purge_student_data(student_email):
    """
    Completely removes a student from all databases (Progress, Active, Completed, Debug).
    Used for testing 'new student' scenarios.
    """
    logging.info(f"--- STARTING PURGE FOR {student_email} ---")
    
    # 1. Clean Main DB (Active Problems & Progress)
    try:
        with get_db_connection(DB_FILE) as conn:
            cursor = conn.cursor()
            
            # Delete active problem first (to be safe with FKs)
            cursor.execute("DELETE FROM active_problems WHERE student_email = ?", (student_email,))
            active_deleted = cursor.rowcount
            
            # Delete student progress
            cursor.execute("DELETE FROM student_progress WHERE student_email = ?", (student_email,))
            progress_deleted = cursor.rowcount
            
            conn.commit()
            print(f"[Main DB] Deleted active problems: {active_deleted}, Student progress: {progress_deleted}")
    except Exception as e:
        print(f"[Main DB] Error purging: {e}")

    # 2. Clean Completed DB
    try:
        with get_db_connection(COMPLETED_DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM completed_conversations WHERE student_email = ?", (student_email,))
            completed_deleted = cursor.rowcount
            conn.commit()
            print(f"[Completed DB] Deleted archived conversations: {completed_deleted}")
    except Exception as e:
        print(f"[Completed DB] Error purging: {e}")

    # 3. Clean Debug DB
    try:
        with get_db_connection(DEBUG_DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM debug_conversations WHERE student_email = ?", (student_email,))
            debug_deleted = cursor.rowcount
            conn.commit()
            print(f"[Debug DB] Deleted debug logs: {debug_deleted}")
    except Exception as e:
        print(f"[Debug DB] Error purging: {e}")

    logging.info(f"--- PURGE COMPLETE FOR {student_email} ---")