import sqlite3
import json
import re
import argparse
import sys
import os
import logging
from scenario_manager import ScenarioManager

# Setup basic logging for the inspector
logging.basicConfig(level=logging.ERROR, format='%(levelname)s: %(message)s')

def _get_inspector_conn(db_file):
    if not os.path.exists(db_file):
        print(f"[!] Database file not found: {db_file}")
        return None
    try:
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"[!] Failed to connect to {db_file}: {e}")
        return None

def print_db_content(db_paths, email_filter=None, search_term=None):
    print(f"\n{'='*60}")
    print(f"       DATABASE INSPECTION REPORT")
    print(f"{'='*60}")
    if email_filter:
        print(f"FILTER: email='{email_filter}'")
    if search_term:
        print(f"SEARCH: keyword='{search_term}'")
    
    # --- 1. Student Progress ---
    print(f"\n--- STUDENT PROGRESS ({os.path.basename(db_paths['main'])}) ---")
    conn = _get_inspector_conn(db_paths['main'])
    if conn:
        with conn:
            try:
                cursor = conn.cursor()
                query = "SELECT * FROM student_progress"
                params = []
                conditions = []
                if email_filter:
                    conditions.append("student_email = ?")
                    params.append(email_filter)
                if search_term:
                    conditions.append("student_email LIKE ?")
                    params.append(f"%{search_term}%")
                
                if conditions:
                    query += " WHERE " + " OR ".join(conditions)
                query += " ORDER BY student_email"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                if not rows: 
                    print("  [Empty or No Match]")
                else:
                    for r in rows: 
                        print(f"  {dict(r)}")
            except Exception as e: 
                print(f"  [Error]: {e}")

    # --- 2. Completed Conversations ---
    print(f"\n--- COMPLETED CONVERSATIONS ({os.path.basename(db_paths['completed'])}) ---")
    conn = _get_inspector_conn(db_paths['completed'])
    if conn:
        with conn:
            try:
                cursor = conn.cursor()
                query = "SELECT * FROM completed_conversations"
                params = []
                conditions = []
                if email_filter:
                    conditions.append("student_email = ?")
                    params.append(email_filter)
                if search_term:
                    conditions.append("(student_email LIKE ? OR full_conversation_history LIKE ?)")
                    params.extend([f"%{search_term}%", f"%{search_term}%"])
                
                if conditions:
                    query += " WHERE " + " OR ".join(conditions)
                query += " ORDER BY completed_at ASC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                if not rows: 
                    print("  [Empty or No Match]")
                else:
                    for r in rows:
                        d = dict(r)
                        print(f"\n  >>> [{d.get('completed_at')}] {d.get('student_email')} - Problem {d.get('problem_id')}")
                        if email_filter or search_term:
                            print("  HISTORY:")
                            print("-" * 40)
                            print(d.get('full_conversation_history', '').strip())
                            print("-" * 40)
            except Exception as e: 
                print(f"  [Error]: {e}")

    # --- 3. Active Problems ---
    print(f"\n--- ACTIVE PROBLEMS ({os.path.basename(db_paths['main'])}) ---")
    conn = _get_inspector_conn(db_paths['main'])
    if conn:
        with conn:
            try:
                cursor = conn.cursor()
                query = "SELECT * FROM active_problems"
                params = []
                conditions = []
                if email_filter:
                    conditions.append("student_email = ?")
                    params.append(email_filter)
                if search_term:
                    conditions.append("(student_email LIKE ? OR conversation_history LIKE ?)")
                    params.extend([f"%{search_term}%", f"%{search_term}%"])
                
                if conditions:
                    query += " WHERE " + " OR ".join(conditions)
                query += " ORDER BY student_email ASC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                if not rows: 
                    print("  [Empty or No Match]")
                else:
                    for r in rows:
                        d = dict(r)
                        print(f"\n  >>> STUDENT: {d.get('student_email')} | PROBLEM: {d.get('problem_id')}")
                        print(f"  LEVEL: {d.get('current_level_index')} | METADATA: {d.get('track_metadata')}")
                        if email_filter or search_term:
                            print("  HISTORY:")
                            print("-" * 40)
                            print(d.get('conversation_history', '').strip())
                            print("-" * 40)
                        else:
                            print(f"  history_len: {len(d.get('conversation_history', ''))} chars")
            except Exception as e: 
                print(f"  [Error]: {e}")
    
    # --- 4. Debug Conversations ---
    # Only print simplified view here, use --debug for full details
    print(f"\n--- DEBUG DB SUMMARY ({os.path.basename(db_paths['debug'])}) ---")
    conn = _get_inspector_conn(db_paths['debug'])
    if conn:
        try:
            cursor = conn.cursor()
            query = "SELECT COUNT(*) as count FROM debug_conversations"
            cursor.execute(query)
            count = cursor.fetchone()['count']
            print(f"  Total records: {count}")
            # Could add last active here
        except Exception as e:
            print(f"  [Error]: {e}")
        finally:
            conn.close()

    print(f"\n{'='*60}\n")


def print_full_debug_history(db_paths, email_filter=None, search_term=None):
    print(f"\n{'!'*60}")
    print(f"       FULL DEBUG HISTORY INSPECTION")
    if search_term:
        print(f"SEARCH KEYWORD: '{search_term}'")
    print(f"{'!'*60}")
    
    conn = _get_inspector_conn(db_paths['debug'])
    if not conn: return

    try:
        cursor = conn.cursor()
        query = "SELECT * FROM debug_conversations ORDER BY last_updated ASC"
        params = []
        
        conditions = []
        if email_filter:
            conditions.append("student_email = ?")
            params.append(email_filter)
        
        if search_term:
            # Search both in email (if not already filtered) and history content
            conditions.append("(student_email LIKE ? OR full_conversation_history LIKE ?)")
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        if conditions:
            query = f"SELECT * FROM debug_conversations WHERE {' AND '.join(conditions)} ORDER BY last_updated ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            print("  [No debug records found]")
            return

        for r in rows:
            d = dict(r)
            print(f"\n>>> STUDENT: {d.get('student_email')} | PROBLEM: {d.get('problem_id')} | UPDATED: {d.get('last_updated')}")
            
            history = d.get('full_conversation_history', '')
            try:
                eval_responses = json.loads(d.get('evaluator_responses', '[]'))
            except:
                eval_responses = []

            print(f"    Evaluator Responses Stored: {len(eval_responses)}")
            print("    ------------------------------------------------")
            
            # Simple dumb print of history logic for robustness
            print(history)
            
            if eval_responses:
                print("\n    [LATEST EVALUATOR LOGS]")
                for item in eval_responses[-3:]: # Show last 3
                    print(f"    -- {item.get('timestamp')}: {item.get('response')}")

            print("    " + ("-"*48))

    except Exception as e:
        print(f"[Error reading debug DB]: {e}")
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Inspect MailResponder Database")
    parser.add_argument("--scenario", "-s", help="Name of the scenario to inspect (e.g. 'Ulla Support')")
    parser.add_argument("--email", "-e", help="Filter results by student email")
    parser.add_argument("--search", "-f", help="Search for keyword in conversation history")
    parser.add_argument("--debug", "-d", action="store_true", help="Print full debug history")
    parser.add_argument("--list", "-l", action="store_true", help="List available scenarios and exit")

    args = parser.parse_args()

    # Load Scenarios
    scenario_manager = ScenarioManager()
    scenario_manager.load_scenarios()
    scenarios = scenario_manager.get_scenarios()

    if not scenarios:
        print("[!] No scenarios found in 'scenarios/' directory.")
        return

    # List mode
    if args.list:
        print("Available Scenarios:")
        for s in scenarios:
            # Safely get db_prefix if we can, otherwise just show info 
            # Note: Scenario object doesn't have db_prefix, but db_manager has db_file
            db_name = os.path.basename(s.db_manager.db_file)
            print(f" - '{s.name}' (DB: {db_name}, Email: {s.target_email})")
        return

    # Select Scenario(s)
    scenarios_to_inspect = []
    if args.scenario:
        # Case-insensitive partial match
        for s in scenarios:
            if args.scenario.lower() in s.name.lower():
                scenarios_to_inspect.append(s)
        if not scenarios_to_inspect:
            print(f"[!] Scenario matching '{args.scenario}' not found.")
            print("Available: " + ", ".join([f"'{s.name}'" for s in scenarios]))
            return
    else:
        # Default to all if search or email filter is used, otherwise maybe just the first one?
        # User wants to search across the system, so default to all scenarios.
        scenarios_to_inspect = scenarios
        if not args.search and not args.email:
             print(f"[i] No scenario specified. Inspecting all {len(scenarios)} scenarios...")
             print(f"    (Use -s <name> for specific scenario)")

    for target_scenario in scenarios_to_inspect:
        if len(scenarios_to_inspect) > 1:
            print(f"\n{'#'*60}")
            print(f"### SCENARIO: {target_scenario.name}")
            print(f"{'#'*60}")

        # Resolve DB Paths using the scenario's DB Manager
        db_paths = {
            "main": target_scenario.db_manager.db_file,
            "completed": target_scenario.db_manager.completed_db_file,
            "debug": target_scenario.db_manager.debug_db_file
        }

        print_db_content(db_paths, email_filter=args.email, search_term=args.search)

        if args.debug or args.search:
            print_full_debug_history(db_paths, email_filter=args.email, search_term=args.search)

if __name__ == "__main__":
    main()