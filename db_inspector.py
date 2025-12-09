import sqlite3
import json
import re
from config import DB_FILE, COMPLETED_DB_FILE, DEBUG_DB_FILE

# Local helper to avoid circular dependency with database.py
def _get_inspector_conn(db_file):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    return conn

def _find_level_idx_for_print(problem_id):
    from problem_catalog import PROBLEM_CATALOGUES
    for level_idx, level_catalogue in enumerate(PROBLEM_CATALOGUES):
        for problem in level_catalogue:
            if problem['id'] == problem_id:
                return level_idx
    return -1

def print_db_content(email_filter=None):
    if email_filter:
        print(f"--- DB UTSKRIFT (Filtrerat på: {email_filter}) ---")
    else:
        print("--- DB UTSKRIFT (All data) ---")

    # --- 1. Student Progress ---
    print("\n--- UTSKRIFT STUDENT PROGRESS ---")
    try:
        with _get_inspector_conn(DB_FILE) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM student_progress ORDER BY student_email"
            params = []
            if email_filter:
                query = "SELECT * FROM student_progress WHERE student_email = ?"
                params.append(email_filter)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if not rows: print("Tabellen student_progress är tom (eller inget matchar filter).")
            else:
                for r in rows: print(dict(r))
    except Exception as e: print(f"Fel vid utskrift av student_progress: {e}")

    # --- 2. Active Problems ---
    print("\n--- UTSKRIFT ACTIVE PROBLEMS ---")
    try:
        with _get_inspector_conn(DB_FILE) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM active_problems ORDER BY student_email"
            params = []
            if email_filter:
                query = "SELECT * FROM active_problems WHERE student_email = ?"
                params.append(email_filter)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if not rows: print("Tabellen active_problems är tom (eller inget matchar filter).")
            else:
                for r in rows:
                    d = dict(r)
                    level_idx = _find_level_idx_for_print(d.get('problem_id'))
                    level_display = level_idx + 1 if level_idx != -1 else "N/A"
                    print(f"Student: {d.get('student_email')}, Problem ID: {d.get('problem_id')}, Level: {level_display}")
                    print(f"  History:\n{d.get('conversation_history', '')}")
    except Exception as e: print(f"Fel vid utskrift av active_problems: {e}")

    # --- 3. Completed Conversations ---
    print("\n--- UTSKRIFT COMPLETED CONVERSATIONS ---")
    try:
        with _get_inspector_conn(COMPLETED_DB_FILE) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM completed_conversations ORDER BY completed_at DESC"
            params = []
            if email_filter:
                query = "SELECT * FROM completed_conversations WHERE student_email = ? ORDER BY completed_at DESC"
                params.append(email_filter)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            if not rows: print("Tabellen completed_conversations är tom (eller inget matchar filter).")
            else:
                for r in rows:
                    d = dict(r)
                    print(f"Student: {d.get('student_email')}, Problem: {d.get('problem_id')}, Completed: {d.get('completed_at')}")
                    print(f"  Conversation:\n{d.get('full_conversation_history', '')}")
    except Exception as e: print(f"Fel vid utskrift av completed_conversations: {e}")
    print("\n--- SLUT DB UTSKRIFT ---")


def print_debug_db_content(email_filter=None, problem_filter=None):
    if email_filter or problem_filter:
        print(f"--- DEBUG DB UTSKRIFT (Filter: email={email_filter}, problem={problem_filter}) ---")
    else:
        print("--- DEBUG DB UTSKRIFT (All data) ---")

    print("\n--- UTSKRIFT DEBUG CONVERSATIONS ---")
    try:
        with _get_inspector_conn(DEBUG_DB_FILE) as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM debug_conversations ORDER BY id ASC"
            params = []
            if email_filter:
                query = "SELECT * FROM debug_conversations WHERE student_email = ? ORDER BY id ASC"
                params.append(email_filter)
            elif problem_filter:
                query = "SELECT * FROM debug_conversations WHERE problem_id = ? ORDER BY id ASC"
                params.append(problem_filter)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows: 
                print("Tabellen debug_conversations är tom.")
                return

            for r in rows:
                d = dict(r)
                print(f"Student: {d.get('student_email')}, Problem: {d.get('problem_id')}")
                print(f"  Last Updated: {d.get('last_updated')}")

                # --- Strict Reconstruction Logic (Preserved) ---
                history = d.get('full_conversation_history', '')
                try:
                    eval_responses = json.loads(d.get('evaluator_responses', '[]'))
                except:
                    eval_responses = []

                print("\n  --- RAW DATA ---")
                print(f"  Evaluator Responses: {len(eval_responses)} entries")
                print("  ----------------\n")

                history_lines = [line.strip() for line in history.split('\n\n') if line.strip()]

                # Identify Student Prefix
                student_prefix = "Student:"
                for line in history_lines:
                    if not line.startswith("Ulla:") and not line.lower().startswith("jättebra!") and not line.startswith("Ulla ("):
                         parts = line.split(':', 1)
                         if len(parts) > 1:
                             student_prefix = parts[0] + ":"
                             break
                
                # Build Timeline
                timeline = []
                eval_idx = 0

                for line in history_lines:
                    if line.startswith("Ulla:") or line.startswith("Ulla ("):
                        timeline.append({'type': 'ULLA', 'content': line})
                    elif line.lower().startswith("jättebra!"):
                        timeline.append({'type': 'COMPLETION', 'content': line})
                    elif line.startswith(student_prefix):
                        timeline.append({'type': 'STUDENT', 'content': line})
                        if eval_idx < len(eval_responses):
                            timeline.append({'type': 'EVAL', 'data': eval_responses[eval_idx]})
                            eval_idx += 1
                    else:
                        # Merge into previous
                        if timeline:
                            timeline[-1]['content'] += "\n\n" + line
                        else:
                            print(f"  [INFO] {line}")

                # Print Timeline
                for event in timeline:
                    if event['type'] == 'ULLA':
                        print(f"  [ULLA] {event['content']}")
                    elif event['type'] == 'STUDENT':
                        print(f"  [STUDENT] {event['content']}")
                    elif event['type'] == 'COMPLETION':
                        print(f"  [COMPLETION] {event['content']}")
                    elif event['type'] == 'EVAL':
                        ts = event['data'].get('timestamp', 'Unknown')
                        print(f"    -> [EVALUATOR {ts}]:")
                        resp = event['data'].get('response', '').replace('</end_of_turn>', '').strip()
                        resp = re.sub(r'^```\s*|\s*```$', '', resp)
                        for l in resp.split('\n'):
                            if l.strip(): print(f"       {l}")
                    print()
                print("-" * 80)
    except Exception as e: print(f"Error printing debug DB: {e}")