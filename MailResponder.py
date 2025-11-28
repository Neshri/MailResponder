import time
import logging
import sqlite3
import json
import re
import sys

# --- Corrected Imports ---
# We import the module 'graph_api' to access the global ACCESS_TOKEN variable dynamically
import graph_api 
from config import PERSONA_MODEL, EVAL_MODEL, DB_FILE, COMPLETED_DB_FILE, DEBUG_DB_FILE, TARGET_USER_GRAPH_ID
from database import init_db, init_completed_db, init_debug_db, print_debug_db_content, get_db_connection, find_problem_by_id
from llm_client import init_llm_client
from email_processor import graph_check_emails
# Removed ACCESS_TOKEN from this import list to avoid creating a stale local copy
from graph_api import get_graph_token, graph_delete_all_emails_in_inbox, jwt_is_expired
from problem_catalog import NUM_LEVELS, PROBLEM_CATALOGUES

# --- Main Execution Block ---
if __name__ == "__main__":
    logging.info(f"Script startat.")
    try:
        init_db()
        init_completed_db()
        init_debug_db()
    except Exception as db_err:
        logging.critical(f"DB-initiering misslyckades: {db_err}. Avslutar."); exit(1)

    # --- CLI Argument Handling ---
    if len(sys.argv) > 1 and sys.argv[1].lower() == "--printdb":
        # Import print_db_content for the printdb command
        from database import print_db_content
        
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

    # Initial token fetch
    if not get_graph_token():
        logging.critical("Misslyckades hämta Graph API-token.")
        exit(1)

    logging.info("Startar huvudloop för e-postkontroll...")
    while True:
        try:
            # Check the variable inside the module (graph_api.ACCESS_TOKEN)
            # This ensures we see the live value updated by get_graph_token()
            if graph_api.ACCESS_TOKEN is None or jwt_is_expired(graph_api.ACCESS_TOKEN):
                logging.info("Token saknas/utgånget före e-postkontroll, förnyar...")
                if not get_graph_token():
                    logging.error("Misslyckades förnya token, väntar till nästa cykel.")
                    time.sleep(60)
                    continue
            
            graph_check_emails()

        except Exception as loop_err:
            logging.error(f"Kritiskt fel i huvudloop: {loop_err}", exc_info=True)
            # If 401 occurs, reset the variable in the MODULE, not locally
            if "401" in str(loop_err) or "token" in str(loop_err).lower():
                graph_api.ACCESS_TOKEN = None
        
        sleep_interval = 30
        logging.info(f"Sover i {sleep_interval} sekunder...")
        time.sleep(sleep_interval)