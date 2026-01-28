import time
import logging
import sys
import graph_api 
from llm_client import init_llm_client
from email_processor import graph_check_emails
from graph_api import get_graph_token, jwt_is_expired
from scenario_manager import ScenarioManager

if __name__ == "__main__":
    logging.info(f"Script startat.")

    # --- CLI Argument Handling (Temporarily Disabled/Modified) ---
    if len(sys.argv) > 1:
        logging.warning("CLI arguments are currently disabled during refactoring.")
        # TODO: Refactor CLI tools to work with specific scenarios
        
    logging.info("--- Kör i E-post Bot-läge (Graph API) ---")
        
    # Initialize LLM client
    ollama_module = init_llm_client()
    if not ollama_module:
        logging.critical("Failed to initialize Ollama connection")
        exit("FEL: Ollama-anslutning.")

    # Initialize Scenario Manager FIRST to load .env variables from scenarios
    scenario_manager = ScenarioManager()
    scenario_manager.load_scenarios()
    
    if not scenario_manager.scenarios:
        logging.critical("Inga scenarier hittades. Avslutar.")
        exit(1)

    # Initial token fetch (Now that env vars might be loaded)
    if not get_graph_token():
        logging.critical("Misslyckades hämta Graph API-token. Kontrollera att minst ett scenario har giltiga Azure-uppgifter i sin config/.env.")
        exit(1)

    logging.info(f"Startar huvudloop för {len(scenario_manager.scenarios)} scenarier...")
    
    while True:
        try:
            # Token Refresh Check
            if graph_api.ACCESS_TOKEN is None or jwt_is_expired(graph_api.ACCESS_TOKEN):
                logging.info("Token saknas/utgånget före e-postkontroll, förnyar...")
                if not get_graph_token():
                    logging.error("Misslyckades förnya token, väntar till nästa cykel.")
                    time.sleep(60)
                    continue
            
            # Iterate through all loaded scenarios
            for scenario in scenario_manager.scenarios:
                try:
                    graph_check_emails(scenario)
                except Exception as e:
                     logging.error(f"Fel vid bearbetning av scenario {scenario.name}: {e}", exc_info=True)
        
        except Exception as loop_err:
            logging.error(f"Kritiskt fel i huvudloop: {loop_err}", exc_info=True)
            if "401" in str(loop_err) or "token" in str(loop_err).lower():
                graph_api.ACCESS_TOKEN = None
        
        sleep_interval = 30
        logging.info(f"Sover i {sleep_interval} sekunder...")
        time.sleep(sleep_interval)