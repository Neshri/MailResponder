import sys
import time
import logging
import os

from config import PERSONA_MODEL, EVAL_MODEL, TARGET_USER_GRAPH_ID, MSAL_APP, ACCESS_TOKEN
from database import init_db, init_completed_db, init_debug_db
from graph_api import get_graph_token, jwt_is_expired, graph_delete_all_emails_in_inbox
from llm_client import init_llm_client
from email_processor import graph_check_emails

def main():
    logging.info(f"Script startat.")
    try:
        init_db()
        init_completed_db()
        init_debug_db()
    except Exception as db_err:
        logging.critical(f"DB-initiering misslyckades: {db_err}. Avslutar.")
        exit(1)

    # Command-line argument handling
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "--printdb":
            from database import print_db_content
            email_filter = sys.argv[2] if len(sys.argv) > 2 else None
            print_db_content(email_filter=email_filter)
            exit(0)
        elif sys.argv[1].lower() == "--printdebugdb":
            from database import print_debug_db_content
            email_filter = sys.argv[2] if len(sys.argv) > 2 else None
            problem_filter = sys.argv[3] if len(sys.argv) > 3 else None
            print_debug_db_content(email_filter=email_filter, problem_filter=problem_filter)
            exit(0)
        elif sys.argv[1].lower() == "--emptyinbox":
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
        else:
            logging.error(f"Unknown command-line argument: {sys.argv[1]}")
            print("Available options: --printdb [--email_filter], --printdebugdb [--email_filter] [--problem_filter], --emptyinbox")
            exit(1)

    # Initialize LLM client
    ollama_module = init_llm_client()
    if not ollama_module:
        logging.critical("Failed to initialize Ollama connection")
        exit("FEL: Ollama-anslutning.")

    # Get initial Graph API token
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
                logging.warning("Ogiltigförklarar token pga fel i huvudloop.")
                ACCESS_TOKEN = None
        sleep_interval = 30
        logging.info(f"Sover i {sleep_interval} sekunder...")
        time.sleep(sleep_interval)

if __name__ == "__main__":
    main()