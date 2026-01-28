import os
import logging
from dotenv import load_dotenv

# --- Constants ---
ULLA_IMAGE_WARNING = "Kära nån, min syn är inte vad den har varit, så jag använder ett speciellt uppläsningsprogram som läser texten i mejlen för mig. Tyvärr kan det inte beskriva bilder, så om du skickade med en bild kan jag inte se den. Om det var något viktigt på bilden får du gärna beskriva det med ord!"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

# --- Environment Loading ---
script_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(script_dir, '.env')
if os.path.exists(dotenv_path):
    logging.info(f"DEBUG: Loading .env from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path, override=True)
else:
    logging.warning(f"DEBUG: .env file NOT found at {dotenv_path}.")
    load_dotenv(override=True)

# --- Environment Variables (Dynamically accessed usually, but defining headers here) ---
# We do NOT exit if these are missing, to allow Scenarios to load their own.
def get_credential(key): return os.getenv(key)

TARGET_USER_GRAPH_ID = os.getenv('BOT_EMAIL_ADDRESS')
PERSONA_MODEL = os.getenv('PERSONA_MODEL')
EVAL_MODEL = os.getenv('EVAL_MODEL')
OLLAMA_HOST = os.getenv('OLLAMA_HOST')

logging.info("Miljövariabler förberedda (validering sker vid användning).")

ollama_client_args = {}
if OLLAMA_HOST: ollama_client_args['host'] = OLLAMA_HOST; logging.info(f"Ollama-klient: {OLLAMA_HOST}")

# --- Database Files ---
DB_FILE = 'conversations.db'
COMPLETED_DB_FILE = 'completed_conversations.db'
DEBUG_DB_FILE = 'debug_conversations.db'

# --- Graph API Configuration ---
GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
GRAPH_SCOPES = ['https://graph.microsoft.com/.default']
ACCESS_TOKEN = None