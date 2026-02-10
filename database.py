import sqlite3
import logging
import datetime
import json
import os
from contextlib import contextmanager
from typing import Tuple, Any, Optional

class DatabaseManager:
    def __init__(self, db_dir: str, db_prefix: str = ""):
        self.db_dir = db_dir
        prefix = f"{db_prefix}_" if db_prefix else ""
        self.db_file = os.path.join(db_dir, f"{prefix}conversations.db")
        self.completed_db_file = os.path.join(db_dir, f"{prefix}completed_conversations.db")
        self.debug_db_file = os.path.join(db_dir, f"{prefix}debug_conversations.db")
        self.track_config_getter = None # callback to get track config if needed

    @contextmanager
    def get_connection(self, db_path: str):
        conn = sqlite3.connect(db_path, timeout=20.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Database error in '{db_path}': {e}", exc_info=True)
            raise
        finally:
            conn.close()

    def init_dbs(self):
        self._init_main_db()
        self._init_completed_db()
        self._init_debug_db()

    def _init_sql(self, db_file, statements, name):
        try:
            with self.get_connection(db_file) as conn:
                for sql in statements:
                    conn.execute(sql)
                conn.commit()
            logging.debug(f"{name} DB initialized at {db_file}.")
        except Exception:
            logging.critical(f"FATAL: {name} DB initialization failed at {db_file}.")
            raise

    def _init_main_db(self):
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
            );''',
            '''CREATE TABLE IF NOT EXISTS processed_emails (
                message_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );'''
        ]
        self._init_sql(self.db_file, stmts, "Main")

    def _init_completed_db(self):
        stmt = ['''CREATE TABLE IF NOT EXISTS completed_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_email TEXT NOT NULL,
                problem_id TEXT NOT NULL,
                problem_level_index INTEGER NOT NULL,
                full_conversation_history TEXT NOT NULL,
                evaluator_response TEXT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );''']
        self._init_sql(self.completed_db_file, stmt, "Completed")

    def _init_debug_db(self):
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
        self._init_sql(self.debug_db_file, stmt, "Debug")

    # --- Operations ---

    def get_student_progress(self, student_email: str) -> Tuple[int, Optional[str], str]:
        try:
            with self.get_connection(self.db_file) as conn:
                cursor = conn.execute("SELECT next_level_index, last_active_graph_convo_id, current_track_id FROM student_progress WHERE student_email = ?", (student_email,))
                row = cursor.fetchone()
                if row:
                    tid = row['current_track_id'] if row['current_track_id'] else 'ulla_classic'
                    return row['next_level_index'], row['last_active_graph_convo_id'], tid
                
                conn.execute("INSERT OR IGNORE INTO student_progress (student_email, next_level_index, current_track_id) VALUES (?, 0, 'ulla_classic')", (student_email,))
                conn.commit()
                return 0, None, 'ulla_classic'
        except sqlite3.Error:
            return 0, None, 'ulla_classic'

    def update_student_level(self, student_email, next_level_index, last_completed_id=None):
        try:
            with self.get_connection(self.db_file) as conn:
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

    def set_student_track(self, student_email, track_id):
        try:
            with self.get_connection(self.db_file) as conn:
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

    def set_active_problem(self, student_email, problem, problem_level_idx, graph_conversation_id, track_metadata=None, persona_name="Ulla"):
        history = f"{persona_name}: {problem['start_prompt']}\n\n"
        metadata_json = json.dumps(track_metadata) if track_metadata else "{}"
        try:
            with self.get_connection(self.db_file) as conn:
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
                
            self.save_debug_conversation(student_email, problem['id'], problem_level_idx, history, "[]")
            logging.info(f"Active problem set for {student_email}")
            return True
        except sqlite3.Error:
            return False

    def get_current_active_problem(self, student_email, problem_finder_callback):
        """
        problem_finder_callback: function(problem_id, track_id) -> (problem_info, level_idx)
        """
        try:
            with self.get_connection(self.db_file) as conn:
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
                    
                    problem_info, level_idx = problem_finder_callback(row['problem_id'], tid)
                    
                    if problem_info:
                        return row['conversation_history'], problem_info, level_idx, row['last_active_graph_convo_id'], metadata
                    else:
                        logging.error(f"DB Inconsistency: Problem {row['problem_id']} not in catalog.")
                
                return None, None, None, None, {}
        except sqlite3.Error:
            return None, None, None, None, {}

    def update_active_problem_metadata(self, student_email, new_metadata):
        try:
            metadata_json = json.dumps(new_metadata)
            with self.get_connection(self.db_file) as conn:
                conn.execute("UPDATE active_problems SET track_metadata = ? WHERE student_email = ?", (metadata_json, student_email))
                conn.commit()
            return True
        except sqlite3.Error:
            return False

    def append_to_active_problem_history(self, student_email, text_to_append):
        if not text_to_append.endswith("\n\n"): text_to_append += "\n\n"
        try:
            with self.get_connection(self.db_file) as conn:
                conn.execute("UPDATE active_problems SET conversation_history = conversation_history || ? WHERE student_email = ?", (text_to_append, student_email))
                cursor = conn.execute("SELECT problem_id FROM active_problems WHERE student_email = ?", (student_email,))
                row = cursor.fetchone()
                conn.commit()
            
            if row:
                with self.get_connection(self.debug_db_file) as dbg_conn:
                    dbg_conn.execute('''
                        UPDATE debug_conversations
                        SET full_conversation_history = full_conversation_history || ?, last_updated = CURRENT_TIMESTAMP
                        WHERE student_email = ? AND problem_id = ?
                    ''', (text_to_append, student_email, row['problem_id']))
                    dbg_conn.commit()
            return True
        except sqlite3.Error:
            return False

    def clear_active_problem(self, student_email):
        try:
            with self.get_connection(self.db_file) as conn:
                conn.execute("UPDATE student_progress SET last_active_graph_convo_id = NULL WHERE student_email = ?", (student_email,))
                conn.execute("DELETE FROM active_problems WHERE student_email = ?", (student_email,))
                conn.commit()
            return True
        except sqlite3.Error:
            return False

    def save_completed_conversation(self, student_email, problem_id, problem_level_index, full_conversation_history, evaluator_response=None):
        try:
            with self.get_connection(self.completed_db_file) as conn:
                conn.execute('''
                    INSERT INTO completed_conversations
                    (student_email, problem_id, problem_level_index, full_conversation_history)
                    VALUES (?, ?, ?, ?)
                ''', (student_email, problem_id, problem_level_index, full_conversation_history))
                conn.commit()
            return True
        except sqlite3.Error:
            return False

    def save_debug_conversation(self, student_email, problem_id, problem_level_index, history_string, evaluator_responses):
        try:
            with self.get_connection(self.debug_db_file) as conn:
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

    def add_debug_evaluator_response(self, student_email, problem_id, evaluator_response):
        """Append a new evaluator response to the JSON list in debug_conversations."""
        try:
            with self.get_connection(self.debug_db_file) as conn:
                cursor = conn.execute(
                    "SELECT evaluator_responses FROM debug_conversations WHERE student_email = ? AND problem_id = ?",
                    (student_email, problem_id)
                )
                row = cursor.fetchone()
                if row:
                    try:
                        responses = json.loads(row['evaluator_responses'])
                    except (ValueError, TypeError):
                        responses = []
                    
                    responses.append({
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "response": evaluator_response
                    })
                    
                    conn.execute(
                        "UPDATE debug_conversations SET evaluator_responses = ?, last_updated = CURRENT_TIMESTAMP WHERE student_email = ? AND problem_id = ?",
                        (json.dumps(responses), student_email, problem_id)
                    )
                    conn.commit()
            return True
        except sqlite3.Error:
            return False

    def is_email_processed(self, message_id: str) -> bool:
        try:
            with self.get_connection(self.db_file) as conn:
                cursor = conn.execute("SELECT 1 FROM processed_emails WHERE message_id = ?", (message_id,))
                return cursor.fetchone() is not None
        except sqlite3.Error:
            return False

    def mark_email_as_processed(self, message_id: str):
        try:
            with self.get_connection(self.db_file) as conn:
                conn.execute("INSERT OR IGNORE INTO processed_emails (message_id) VALUES (?)", (message_id,))
            return True
        except sqlite3.Error:
            return False
