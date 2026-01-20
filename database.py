import sqlite3
import logging
import datetime
import json
from contextlib import contextmanager
from config import DB_FILE, COMPLETED_DB_FILE, DEBUG_DB_FILE

# --- Re-export Print Functions ---
from db_inspector import print_db_content, print_debug_db_content

# --- Connection Management ---
@contextmanager
def get_db_connection(db_file):
    """
    Standard context manager.
    Guarantees connection closes (releasing locks) immediately after the block.
    """
    conn = sqlite3.connect(db_file, timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except sqlite3.Error as e:
        logging.error(f"Database error in '{db_file}': {e}", exc_info=True)
        raise
    finally:
        conn.close()

# --- Initialization ---
def _init_sql(db_file, statements, name):
    try:
        with get_db_connection(db_file) as conn:
            for sql in statements:
                conn.execute(sql)
            conn.commit()
        logging.info(f"{name} DB initialized.")
    except Exception:
        logging.critical(f"FATAL: {name} DB initialization failed.")
        raise

def init_db():
    stmts = [
        '''CREATE TABLE IF NOT EXISTS student_progress (
            student_email TEXT PRIMARY KEY,
            next_level_index INTEGER NOT NULL DEFAULT 0,
            last_completed_problem_id TEXT,
            last_active_graph_convo_id TEXT,
            current_track_id TEXT DEFAULT 'ulla_classic'
        );''',
        '''CREATE TABLE IF NOT EXISTS active_problems (
            student_email TEXT PRIMARY KEY,
            problem_id TEXT NOT NULL,
            conversation_history TEXT NOT NULL,
            track_metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_email) REFERENCES student_progress(student_email)
        );'''
    ]
    _init_sql(DB_FILE, stmts, "Main")

    # Migration: Add current_track_id if missing
    try:
        with get_db_connection(DB_FILE) as conn:
            cursor = conn.execute("PRAGMA table_info(student_progress)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'current_track_id' not in columns:
                conn.execute("ALTER TABLE student_progress ADD COLUMN current_track_id TEXT DEFAULT 'ulla_classic'")
                conn.commit()
                logging.info("Migrated DB: Added current_track_id column to student_progress.")
            
            # Migration: Add track_metadata to active_problems if missing
            cursor = conn.execute("PRAGMA table_info(active_problems)")
            ap_columns = [info[1] for info in cursor.fetchall()]
            if 'track_metadata' not in ap_columns:
                conn.execute("ALTER TABLE active_problems ADD COLUMN track_metadata TEXT DEFAULT '{}'")
                conn.commit()
                logging.info("Migrated DB: Added track_metadata column to active_problems.")
    except Exception as e:
        logging.error(f"Migration check failed: {e}")

def init_completed_db():
    stmt = ['''CREATE TABLE IF NOT EXISTS completed_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            problem_level_index INTEGER NOT NULL,
            full_conversation_history TEXT NOT NULL,
            evaluator_response TEXT,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );''']
    _init_sql(COMPLETED_DB_FILE, stmt, "Completed")

def init_debug_db():
    stmt = ['''CREATE TABLE IF NOT EXISTS debug_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_email TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            problem_level_index INTEGER NOT NULL,
            full_conversation_history TEXT NOT NULL,
            evaluator_responses TEXT NOT NULL DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );''']
    _init_sql(DEBUG_DB_FILE, stmt, "Debug")

# --- Utilities ---
def find_problem_by_id(problem_id, track_id="ulla_classic"):
    from tracks import get_track_config
    track_config = get_track_config(track_id)
    catalog = track_config["catalog"]

    for level_idx, level_catalogue in enumerate(catalog):
        for problem in level_catalogue:
            if problem['id'] == problem_id:
                return problem, level_idx
    return None, -1

# --- Operations (Signatures Restored) ---

def get_student_progress(student_email):
    try:
        with get_db_connection(DB_FILE) as conn:
            cursor = conn.execute("SELECT next_level_index, last_active_graph_convo_id, current_track_id FROM student_progress WHERE student_email = ?", (student_email,))
            row = cursor.fetchone()
            if row:
                tid = row['current_track_id'] if row['current_track_id'] else 'ulla_classic'
                return row['next_level_index'], row['last_active_graph_convo_id'], tid
            
            # Create default if missing
            conn.execute("INSERT OR IGNORE INTO student_progress (student_email, next_level_index, current_track_id) VALUES (?, 0, 'ulla_classic')", (student_email,))
            conn.commit()
            return 0, None, 'ulla_classic'
    except sqlite3.Error:
        return 0, None, 'ulla_classic'

def update_student_level(student_email, next_level_index, last_completed_id=None):
    try:
        with get_db_connection(DB_FILE) as conn:
            # First ensure the row exists with a safety check
            conn.execute("INSERT OR IGNORE INTO student_progress (student_email, next_level_index, current_track_id) VALUES (?, 0, 'ulla_classic')", (student_email,))
            
            if last_completed_id:
                conn.execute(
                    "UPDATE student_progress SET next_level_index = ?, last_completed_problem_id = ?, last_active_graph_convo_id = NULL WHERE student_email = ?",
                    (next_level_index, last_completed_id, student_email)
                )
            else:
                conn.execute(
                    "UPDATE student_progress SET next_level_index = ? WHERE student_email = ?",
                    (next_level_index, student_email)
                )
            conn.commit()
        return True
    except sqlite3.Error:
        return False

def set_student_track(student_email, track_id):
    """Updates the user's active track and RESETS progress to level 0."""
    try:
        with get_db_connection(DB_FILE) as conn:
            conn.execute('''
                INSERT INTO student_progress (student_email, next_level_index, current_track_id) 
                VALUES (?, 0, ?)
                ON CONFLICT(student_email) DO UPDATE SET 
                    current_track_id = excluded.current_track_id,
                    next_level_index = 0,
                    last_active_graph_convo_id = NULL
            ''', (student_email, track_id))
            conn.execute("DELETE FROM active_problems WHERE student_email = ?", (student_email,))
            conn.commit()
        logging.info(f"Student {student_email} switched to track '{track_id}'")
        return True
    except sqlite3.Error as e:
        logging.error(f"Failed to set track: {e}")
        return False

def set_active_problem(student_email, problem, problem_level_idx, graph_conversation_id, track_metadata=None):
    history = f"Ulla: {problem['start_prompt']}\n\n"
    metadata_json = json.dumps(track_metadata) if track_metadata else "{}"
    try:
        with get_db_connection(DB_FILE) as conn:
            conn.execute(
                "INSERT INTO student_progress (student_email, next_level_index, last_active_graph_convo_id) VALUES (?, ?, ?) "
                "ON CONFLICT(student_email) DO UPDATE SET last_active_graph_convo_id = excluded.last_active_graph_convo_id",
                (student_email, problem_level_idx, graph_conversation_id)
            )
            conn.execute('''
                REPLACE INTO active_problems
                (student_email, problem_id, conversation_history, track_metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_email, problem['id'], history, metadata_json, datetime.datetime.now()))
            conn.commit()
            
        save_debug_conversation(student_email, problem['id'], problem_level_idx, history, "[]")
        logging.info(f"Active problem set for {student_email}")
        return True
    except sqlite3.Error:
        return False

def get_current_active_problem(student_email):
    try:
        with get_db_connection(DB_FILE) as conn:
            cursor = conn.execute('''
                SELECT ap.problem_id, ap.conversation_history, ap.track_metadata, sp.last_active_graph_convo_id, sp.current_track_id
                FROM active_problems ap
                LEFT JOIN student_progress sp ON ap.student_email = sp.student_email
                WHERE ap.student_email = ?
            ''', (student_email,))
            row = cursor.fetchone()
            
            if row:
                tid = row['current_track_id'] if row['current_track_id'] else 'ulla_classic'
                metadata = json.loads(row['track_metadata']) if row['track_metadata'] else {}
                problem_info, level_idx = find_problem_by_id(row['problem_id'], tid)
                if problem_info:
                    return row['conversation_history'], problem_info, level_idx, row['last_active_graph_convo_id'], metadata
                else:
                    logging.error(f"DB Inconsistency: Problem {row['problem_id']} not in catalog.")
            
            return None, None, None, None, {}
    except sqlite3.Error:
        return None, None, None, None, {}

def update_active_problem_metadata(student_email, new_metadata):
    try:
        metadata_json = json.dumps(new_metadata)
        with get_db_connection(DB_FILE) as conn:
            conn.execute("UPDATE active_problems SET track_metadata = ? WHERE student_email = ?", (metadata_json, student_email))
            conn.commit()
        return True
    except sqlite3.Error:
        return False

def append_to_active_problem_history(student_email, text_to_append):
    if not text_to_append.endswith("\n\n"): text_to_append += "\n\n"
    try:
        with get_db_connection(DB_FILE) as conn:
            conn.execute("UPDATE active_problems SET conversation_history = conversation_history || ? WHERE student_email = ?", (text_to_append, student_email))
            cursor = conn.execute("SELECT problem_id FROM active_problems WHERE student_email = ?", (student_email,))
            row = cursor.fetchone()
            conn.commit()
        
        if row:
            with get_db_connection(DEBUG_DB_FILE) as dbg_conn:
                dbg_conn.execute('''
                    UPDATE debug_conversations
                    SET full_conversation_history = full_conversation_history || ?, last_updated = CURRENT_TIMESTAMP
                    WHERE student_email = ? AND problem_id = ?
                ''', (text_to_append, student_email, row['problem_id']))
                dbg_conn.commit()
        return True
    except sqlite3.Error:
        return False

def clear_active_problem(student_email):
    try:
        with get_db_connection(DB_FILE) as conn:
            conn.execute("UPDATE student_progress SET last_active_graph_convo_id = NULL WHERE student_email = ?", (student_email,))
            conn.execute("DELETE FROM active_problems WHERE student_email = ?", (student_email,))
            conn.commit()
        return True
    except sqlite3.Error:
        return False

def save_completed_conversation(student_email, problem_id, problem_level_index, full_conversation_history, evaluator_response=None):
    try:
        with get_db_connection(COMPLETED_DB_FILE) as conn:
            conn.execute('''
                INSERT INTO completed_conversations
                (student_email, problem_id, problem_level_index, full_conversation_history)
                VALUES (?, ?, ?, ?)
            ''', (student_email, problem_id, problem_level_index, full_conversation_history))
            conn.commit()
        return True
    except sqlite3.Error:
        return False

def save_debug_conversation(student_email, problem_id, problem_level_index, history_string, evaluator_responses):
    try:
        with get_db_connection(DEBUG_DB_FILE) as conn:
            cursor = conn.execute("SELECT id FROM debug_conversations WHERE student_email = ? AND problem_id = ?", (student_email, problem_id))
            existing = cursor.fetchone()
            
            if existing:
                conn.execute('''
                    UPDATE debug_conversations
                    SET full_conversation_history = ?, evaluator_responses = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (history_string, evaluator_responses, existing['id']))
            else:
                conn.execute('''
                    INSERT INTO debug_conversations
                    (student_email, problem_id, problem_level_index, full_conversation_history, evaluator_responses)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_email, problem_id, problem_level_index, history_string, evaluator_responses))
            conn.commit()
        return True
    except sqlite3.Error:
        return False

def append_evaluator_response_to_debug(student_email, problem_id, evaluator_response_text):
    try:
        with get_db_connection(DEBUG_DB_FILE) as conn:
            cursor = conn.execute("SELECT evaluator_responses FROM debug_conversations WHERE student_email = ? AND problem_id = ?", (student_email, problem_id))
            row = cursor.fetchone()
            
            if not row: return False
            
            try: data = json.loads(row['evaluator_responses'])
            except: data = []
            
            data.append({"timestamp": datetime.datetime.now().isoformat(), "response": evaluator_response_text})
            
            conn.execute(
                "UPDATE debug_conversations SET evaluator_responses = ?, last_updated = CURRENT_TIMESTAMP WHERE student_email = ? AND problem_id = ?",
                (json.dumps(data), student_email, problem_id)
            )
            conn.commit()
        return True
    except sqlite3.Error:
        return False

def purge_student_data(student_email):
    try:
        with get_db_connection(DB_FILE) as conn:
            conn.execute("DELETE FROM active_problems WHERE student_email = ?", (student_email,))
            conn.execute("DELETE FROM student_progress WHERE student_email = ?", (student_email,))
            conn.commit()
        with get_db_connection(COMPLETED_DB_FILE) as conn:
            conn.execute("DELETE FROM completed_conversations WHERE student_email = ?", (student_email,))
            conn.commit()
        with get_db_connection(DEBUG_DB_FILE) as conn:
            conn.execute("DELETE FROM debug_conversations WHERE student_email = ?", (student_email,))
            conn.commit()
        logging.info(f"Purged data for {student_email}")
    except Exception as e:
        logging.error(f"Purge failed: {e}")