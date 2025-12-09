import sqlite3
import logging
import datetime
import json
from contextlib import contextmanager
from config import DB_FILE, COMPLETED_DB_FILE, DEBUG_DB_FILE

# --- Re-export Print Functions for main.py compatibility ---
from db_inspector import print_db_content, print_debug_db_content

# --- Database Core ---
@contextmanager
def get_db_connection(db_file):
    """Exposed context manager for safe database connections."""
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    except sqlite3.Error as e:
        logging.error(f"Database error in '{db_file}': {e}", exc_info=True)
        raise
    finally:
        conn.close()

def _execute(db_file, query, params=(), fetch_one=False):
    """Internal helper to reduce boilerplate."""
    try:
        with get_db_connection(db_file) as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            if fetch_one:
                return cursor.fetchone()
            return True
    except sqlite3.Error:
        return False

# --- Initialization (API Preserved) ---
def _run_schema(db_file, schemas, name):
    try:
        with get_db_connection(db_file) as conn:
            for sql in schemas:
                conn.execute(sql)
            conn.commit()
        logging.info(f"{name} DB initialized.")
    except sqlite3.Error:
        logging.critical(f"FATAL: {name} DB initialization failed.")
        raise

def init_db():
    schemas = [
        '''CREATE TABLE IF NOT EXISTS student_progress (
            student_email TEXT PRIMARY KEY, next_level_index INTEGER DEFAULT 0,
            last_completed_problem_id TEXT, last_active_graph_convo_id TEXT)''',
        '''CREATE TABLE IF NOT EXISTS active_problems (
            student_email TEXT PRIMARY KEY, problem_id TEXT NOT NULL,
            conversation_history TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_email) REFERENCES student_progress(student_email))'''
    ]
    _run_schema(DB_FILE, schemas, "Main")

def init_completed_db():
    schema = ['''CREATE TABLE IF NOT EXISTS completed_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, problem_id TEXT,
        problem_level_index INTEGER, full_conversation_history TEXT,
        evaluator_response TEXT, completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''']
    _run_schema(COMPLETED_DB_FILE, schema, "Completed")

def init_debug_db():
    schema = ['''CREATE TABLE IF NOT EXISTS debug_conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_email TEXT, problem_id TEXT,
        problem_level_index INTEGER, full_conversation_history TEXT,
        evaluator_responses TEXT DEFAULT '[]', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''']
    _run_schema(DEBUG_DB_FILE, schema, "Debug")

# --- Utilities ---
def find_problem_by_id(problem_id):
    from problem_catalog import PROBLEM_CATALOGUES
    for level_idx, level_catalogue in enumerate(PROBLEM_CATALOGUES):
        for problem in level_catalogue:
            if problem['id'] == problem_id:
                return problem, level_idx
    return None, -1

# --- Operations ---
def get_student_progress(email):
    row = _execute(DB_FILE, "SELECT next_level_index, last_active_graph_convo_id FROM student_progress WHERE student_email = ?", (email,), fetch_one=True)
    if row: return row['next_level_index'], row['last_active_graph_convo_id']
    _execute(DB_FILE, "INSERT OR IGNORE INTO student_progress (student_email, next_level_index) VALUES (?, 0)", (email,))
    return 0, None

def update_student_level(email, new_idx, last_completed_id=None):
    _execute(DB_FILE, "INSERT OR IGNORE INTO student_progress (student_email, next_level_index) VALUES (?, 0)", (email,))
    if last_completed_id:
        return _execute(DB_FILE, "UPDATE student_progress SET next_level_index = ?, last_completed_problem_id = ?, last_active_graph_convo_id = NULL WHERE student_email = ?", (new_idx, last_completed_id, email))
    return _execute(DB_FILE, "UPDATE student_progress SET next_level_index = ? WHERE student_email = ?", (new_idx, email))

def set_active_problem(email, problem, level_idx, graph_id):
    history = f"Ulla: {problem['start_prompt']}\n\n"
    try:
        with get_db_connection(DB_FILE) as conn:
            conn.execute("INSERT INTO student_progress (student_email, next_level_index, last_active_graph_convo_id) VALUES (?, ?, ?) ON CONFLICT(student_email) DO UPDATE SET last_active_graph_convo_id = ?", (email, level_idx, graph_id, graph_id))
            conn.execute("REPLACE INTO active_problems (student_email, problem_id, conversation_history) VALUES (?, ?, ?)", (email, problem['id'], history))
            conn.commit()
        save_debug_conversation(email, problem['id'], level_idx, history, "[]")
        logging.info(f"Active problem set for {email}")
        return True
    except sqlite3.Error:
        return False

def get_current_active_problem(email):
    row = _execute(DB_FILE, "SELECT ap.problem_id, ap.conversation_history, sp.last_active_graph_convo_id FROM active_problems ap JOIN student_progress sp ON ap.student_email = sp.student_email WHERE ap.student_email = ?", (email,), fetch_one=True)
    if not row: return None, None, None, None
    
    problem_info, level_idx = find_problem_by_id(row['problem_id'])
    if problem_info:
        return row['conversation_history'], problem_info, level_idx, row['last_active_graph_convo_id']
    logging.error(f"DB Inconsistency: Problem {row['problem_id']} missing in catalog.")
    return None, None, None, None

def append_to_active_problem_history(email, text):
    if not text.endswith("\n\n"): text += "\n\n"
    if not _execute(DB_FILE, "UPDATE active_problems SET conversation_history = conversation_history || ? WHERE student_email = ?", (text, email)): return False
    
    row = _execute(DB_FILE, "SELECT problem_id FROM active_problems WHERE student_email = ?", (email,), fetch_one=True)
    if row:
        _execute(DEBUG_DB_FILE, "UPDATE debug_conversations SET full_conversation_history = full_conversation_history || ?, last_updated = CURRENT_TIMESTAMP WHERE student_email = ? AND problem_id = ?", (text, email, row['problem_id']))
    return True

def clear_active_problem(email):
    _execute(DB_FILE, "UPDATE student_progress SET last_active_graph_convo_id = NULL WHERE student_email = ?", (email,))
    return _execute(DB_FILE, "DELETE FROM active_problems WHERE student_email = ?", (email,))

def save_completed_conversation(email, pid, lvl, history, eval_resp=None):
    return _execute(COMPLETED_DB_FILE, "INSERT INTO completed_conversations (student_email, problem_id, problem_level_index, full_conversation_history) VALUES (?, ?, ?, ?)", (email, pid, lvl, history))

def save_debug_conversation(email, pid, lvl, history, eval_json):
    existing = _execute(DEBUG_DB_FILE, "SELECT id FROM debug_conversations WHERE student_email = ? AND problem_id = ?", (email, pid), fetch_one=True)
    if existing:
        return _execute(DEBUG_DB_FILE, "UPDATE debug_conversations SET full_conversation_history = ?, evaluator_responses = ?, last_updated = CURRENT_TIMESTAMP WHERE id = ?", (history, eval_json, existing['id']))
    return _execute(DEBUG_DB_FILE, "INSERT INTO debug_conversations (student_email, problem_id, problem_level_index, full_conversation_history, evaluator_responses) VALUES (?, ?, ?, ?, ?)", (email, pid, lvl, history, eval_json))

def append_evaluator_response_to_debug(email, pid, response_text):
    row = _execute(DEBUG_DB_FILE, "SELECT evaluator_responses FROM debug_conversations WHERE student_email = ? AND problem_id = ?", (email, pid), fetch_one=True)
    if not row: return False
    try: data = json.loads(row['evaluator_responses'])
    except: data = []
    data.append({"timestamp": datetime.datetime.now().isoformat(), "response": response_text})
    return _execute(DEBUG_DB_FILE, "UPDATE debug_conversations SET evaluator_responses = ?, last_updated = CURRENT_TIMESTAMP WHERE student_email = ? AND problem_id = ?", (json.dumps(data), email, pid))

def purge_student_data(email):
    _execute(DB_FILE, "DELETE FROM active_problems WHERE student_email = ?", (email,))
    _execute(DB_FILE, "DELETE FROM student_progress WHERE student_email = ?", (email,))
    _execute(COMPLETED_DB_FILE, "DELETE FROM completed_conversations WHERE student_email = ?", (email,))
    _execute(DEBUG_DB_FILE, "DELETE FROM debug_conversations WHERE student_email = ?", (email,))
    logging.info(f"Purged data for {email}")