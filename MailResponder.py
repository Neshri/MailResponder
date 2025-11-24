import time
import logging
import sqlite3
import json
import re
from config import PERSONA_MODEL, EVAL_MODEL, DB_FILE, COMPLETED_DB_FILE, DEBUG_DB_FILE, TARGET_USER_GRAPH_ID
from database import init_db, init_completed_db, init_debug_db, print_db_content, print_debug_db_content, get_db_connection, find_problem_by_id
from llm_client import init_llm_client
from email_processor import graph_check_emails
from graph_api import get_graph_token, graph_delete_all_emails_in_inbox, ACCESS_TOKEN, jwt_is_expired
from prompts import NUM_LEVELS, PROBLEM_CATALOGUES

# --- Main Execution Block ---
if __name__ == "__main__":
    logging.info(f"Script startat.")
    try:
        init_db()
        init_completed_db()
        init_debug_db()
    except Exception as db_err:
        logging.critical(f"DB-initiering misslyckades: {db_err}. Avslutar."); exit(1)

    import sys
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--printdb":
        # Helper function to find level index from problem ID
        def find_level_idx_by_id(problem_id):
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
                            level_idx = find_level_idx_by_id(problem_id)
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

        email_to_filter = sys.argv[2] if len(sys.argv) > 2 else None
        print_db_content(email_filter=email_to_filter)
        exit()

    elif len(sys.argv) > 1 and sys.argv[1].lower() == "--printdebugdb":
        email_to_filter = sys.argv[2] if len(sys.argv) > 2 else None
        problem_filter = sys.argv[3] if len(sys.argv) > 3 else None
        print_debug_db_content(email_filter=email_to_filter, problem_filter=problem_filter)
        exit()

    elif len(sys.argv) > 1 and sys.argv[1].lower() == "--emptyinbox":
        logging.info("--- EMPTYING INBOX (via --emptyinbox command) ---")
        if not TARGET_USER_GRAPH_ID:
             logging.critical("TARGET_USER_GRAPH_ID is not set in .env. Cannot empty inbox.")
             exit(1)
        if not get_graph_token():
            logging.critical("Failed to get Graph API token. Cannot empty inbox.")
            exit(1)

        success = graph_delete_all_emails_in_inbox()
        if success:
            logging.info("Inbox emptying process reported success overall.")
        else:
            logging.warning("Inbox emptying process reported one or more failures during deletion.")
        exit(0)


    logging.info("--- Kör i E-post Bot-läge (Graph API) ---")
    if not PERSONA_MODEL or not EVAL_MODEL:
        logging.critical(f"Saknar PERSONA_MODEL ('{PERSONA_MODEL}') och/eller EVAL_MODEL ('{EVAL_MODEL}')."); exit(1)
    # Initialize LLM client
    ollama_module = init_llm_client()
    if not ollama_module:
        logging.critical("Failed to initialize Ollama connection")
        exit("FEL: Ollama-anslutning.")

    if not get_graph_token():
        logging.critical("Misslyckades hämta Graph API-token.")
        exit(1)

    logging.info("Startar huvudloop för e-postkontroll...")
    while True:
        try:
            if ACCESS_TOKEN is None or jwt_is_expired(ACCESS_TOKEN):
                logging.info("Token saknas/utgånget före e-postkontroll, förnyar...")
                if not get_graph_token():
                    logging.error("Misslyckades förnya token, väntar till nästa cykel.")
                    time.sleep(60)
                    continue
            graph_check_emails()
        except Exception as loop_err:
            logging.error(f"Kritiskt fel i huvudloop: {loop_err}", exc_info=True)
            if "401" in str(loop_err) or "token" in str(loop_err).lower():
                ACCESS_TOKEN = None
        sleep_interval = 30
        logging.info(f"Sover i {sleep_interval} sekunder...")
        time.sleep(sleep_interval)