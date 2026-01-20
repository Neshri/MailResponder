# tracks.py
from prompts import ULLA_PERSONA_PROMPT, EVALUATOR_SYSTEM_PROMPT, EVIL_PERSONA_PROMPT, EVIL_EVALUATOR_PROMPT
from problem_catalog import PROBLEM_CATALOGUES, START_PHRASES as ULLA_START_PHRASES

from deescalation_catalog import (
    EVIL_CATALOGUES,
    EVIL_START_PHRASES
)

# --- Sandbox Track (Safe Testing) ---
SANDBOX_CATALOG = [
    [
        {
            "id": "S1_P001",
            "start_prompt": "Detta är ett testmeddelande för sandlådan. Svara 'OK' för att klara nivån.",
            "beskrivning": "Enkel testuppgift för verifiering.",
            "losning_nyckelord": ["ok"]
        }
    ]
]
SANDBOX_START_PHRASES = ["testa nivå 1"]

# Define Tracks
# Each track must have:
# - trigger_phrases: List[str] - phrases that switch the user to this track
# - persona_prompt: str - System prompt for the persona
# - evaluator_prompt: str - System prompt for the evaluator
# - catalog: List[List[dict]] - The problem catalog (Levels -> Problems)
# - start_phrases: List[str] - Specific start phrases for levels within this track

TRACKS = {
    "ulla_classic": {
        "description": "Classic Ulla Support Scenarios",
        "trigger_phrases": ["starta övning", "börja övning"], # triggers that force a switch/reset to this track
        "persona_prompt": ULLA_PERSONA_PROMPT,
        "evaluator_prompt": EVALUATOR_SYSTEM_PROMPT,
        "catalog": PROBLEM_CATALOGUES,
        "start_phrases": ULLA_START_PHRASES
    },
    "evil_persona": {
        "description": "Deescalation Training - Gunilla",
        "trigger_phrases": ["starta deeskalering", "börja deeskalering"],
        "persona_prompt": EVIL_PERSONA_PROMPT,
        "evaluator_prompt": EVIL_EVALUATOR_PROMPT,
        "catalog": EVIL_CATALOGUES,
        "start_phrases": EVIL_START_PHRASES
    },
    "sandbox": {
        "description": "Safe Testing Sandbox",
        "trigger_phrases": ["aktivera sandlåda"],
        "persona_prompt": ULLA_PERSONA_PROMPT, # reuse Ulla for basic sandbox
        "evaluator_prompt": EVALUATOR_SYSTEM_PROMPT,
        "catalog": SANDBOX_CATALOG,
        "start_phrases": SANDBOX_START_PHRASES
    }
}

def get_track_config(track_id):
    return TRACKS.get(track_id, TRACKS["ulla_classic"])

def detect_track_trigger(body_text):
    """
    Checks if the body text contains a trigger phrase for any track.
    Returns (track_id, matched_phrase) or (None, None).
    """
    body_lower = body_text.lower().strip()
    
    for track_id, config in TRACKS.items():
        for phrase in config["trigger_phrases"]:
            if phrase in body_lower:
                return track_id, phrase
    return None, None
