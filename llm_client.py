import logging
try:
    import ollama
except ImportError:
    ollama = None

from config import PERSONA_MODEL, EVAL_MODEL, ollama_client_args

def init_llm_client():
    """Initialize and test the Ollama connection by making a chat request."""
    if not ollama:
        logging.error("Ollama module not available")
        return None

    try:
        # Test connection by making a chat request with the evaluator model
        response = ollama.chat(
            model=EVAL_MODEL,
            messages=[{'role': 'user', 'content': 'Hello'}]
        )
        logging.info(f"Ollama connection tested successfully with model '{EVAL_MODEL}'")
        return ollama
    except Exception as e:
        logging.error(f"Failed to test Ollama connection with model '{EVAL_MODEL}': {e}")
        return None

def chat_with_model(model, messages, options=None, **kwargs):
    """
    Unified function to chat with LLM models.
    """
    if not init_llm_client():
        logging.error("Ollama not available")
        return None

    try:
        response = ollama.chat(
            model=model,
            messages=messages,
            options=options,
            **kwargs
        )
        return response
    except Exception as e:
        logging.error(f"Error chatting with model {model}: {e}")
        return None

def get_ollama_client():
    """Get the ollama module."""
    return init_llm_client()