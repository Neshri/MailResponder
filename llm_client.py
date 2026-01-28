import logging
try:
    import ollama
except ImportError:
    ollama = None

from config import ollama_client_args

_LLM_CLIENT_CACHE = None

def init_llm_client():
    """Initialize and test the Ollama connection."""
    global _LLM_CLIENT_CACHE
    if _LLM_CLIENT_CACHE:
        return _LLM_CLIENT_CACHE

    if not ollama:
        logging.error("Ollama module not available")
        return None

    try:
        # Test connection by listing models instead of depending on a specific one
        ollama.list()
        logging.info("Ollama connection established and verified.")
        _LLM_CLIENT_CACHE = ollama
        return ollama
    except Exception as e:
        logging.error(f"Failed to connect to Ollama: {e}")
        return None

def chat_with_model(model, messages, options=None, **kwargs):
    """
    Unified function to chat with LLM models. Returns the text content.
    """
    client = init_llm_client()
    if not client:
        logging.error("Ollama not available")
        return None

    try:
        response = client.chat(
            model=model,
            messages=messages,
            options=options,
            **kwargs
        )
        # Handle both dict-like and object-like responses (Ollama library variance)
        try:
            # Try attribute access first (common in newer library versions/mocks)
            if hasattr(response, 'message'):
                msg = response.message
                return msg.content if hasattr(msg, 'content') else msg['content']
            # Fallback to dict access
            return response['message']['content']
        except (KeyError, AttributeError, TypeError):
            # Final fallback if it's already a string or something else
            return str(response)
    except Exception as e:
        logging.error(f"Error chatting with model {model}: {e}")
        return None

def reset_llm_client():
    """Resets the internal cache (useful for testing)."""
    global _LLM_CLIENT_CACHE
    _LLM_CLIENT_CACHE = None

def get_ollama_client():
    """Get the ollama module."""
    return init_llm_client()