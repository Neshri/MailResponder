import re
import json
import logging
from config import PERSONA_MODEL, ULLA_IMAGE_WARNING
from prompts import ULLA_PERSONA_PROMPT
from llm_client import chat_with_model
from email_parser import get_name_from_email

def strip_markdown(text):
    # Remove inline code `text`
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Remove bold/italic **text** or __text__
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    # Remove italic *text* or _text_
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    # Remove links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    # Remove headers # ## etc at start of line
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    # Remove list markers - * + at start of line
    text = re.sub(r'^[-\*\+]\s*', '', text, flags=re.MULTILINE)
    return text

def get_ulla_persona_reply(student_email, full_history_string_for_ulla, problem_info_for_ulla,
                           latest_student_message_for_ulla, problem_level_idx_for_ulla, evaluator_decision_marker):
    """
    Calls an LLM to generate Ulla's persona reply.
    """
    if not PERSONA_MODEL:
        logging.error(f"Ulla Persona ({student_email}): PERSONA_MODEL ej satt.")
        return "Glömde vad jag skulle säga..."

    logging.info(f"Ulla Persona AI för {student_email} (Nivå {problem_level_idx_for_ulla+1}): Genererar svar baserat på '{evaluator_decision_marker}' med modell '{PERSONA_MODEL}'.")

    # The system prompt contains the rules and persona. This remains the same.
    system_prompt_content = ULLA_PERSONA_PROMPT

    # --- REVISED USER PROMPT LOGIC ---
    if evaluator_decision_marker == "[LÖST]":
        # This prompt for the solved state is good and can remain.
        user_prompt_content = f"""
        **Din Berättelse (Kontext):**
        ---
        {problem_info_for_ulla['beskrivning']}
        ---
        **Uppgift:** Studentens svar hjälpte dig att lösa problemet. Svara som Ulla och bekräfta glatt att problemet är borta.
        """
    else:
        # This is the main prompt that needs fixing.
        # We REMOVE the final "Din Uppgift" instruction.
        technical_facts_dict = problem_info_for_ulla.get('tekniska_fakta', {})
        student_name = get_name_from_email(student_email)
        user_prompt_content = f"""
        **KÄLLFAKTA (Din enda sanning):**
        {json.dumps(technical_facts_dict, indent=2, ensure_ascii=False)}

        **Din Berättelse (För din personlighet):**
        {problem_info_for_ulla['beskrivning']}

        **Hittillsvarande Konversation:**
        {full_history_string_for_ulla}
        **{student_name}s Senaste Meddelande:**
        {latest_student_message_for_ulla}
        """

    messages_for_ulla = [
        {'role': 'system', 'content': system_prompt_content},
        {'role': 'user', 'content': user_prompt_content}
    ]

    try:
        response = chat_with_model(
            model=PERSONA_MODEL,
            messages=messages_for_ulla,
            options={'temperature': 0.7, 'num_predict': 1000}
        )
        if not response:
            return "Åh nej, nu tappade jag visst bort mig lite..."

        ulla_svar = response['message']['content'].strip()
        ulla_svar = re.sub(r"<think>.*?</think>", "", ulla_svar, flags=re.DOTALL).strip()
        ulla_svar = re.sub("</end_of_turn>", "", ulla_svar)
        ulla_svar = strip_markdown(ulla_svar)
        logging.info(f"Ulla Persona AI ({student_email}): Genererade svar: '{ulla_svar[:50]}...'")
        return ulla_svar
    except Exception as e:
        logging.error(f"Ulla Persona AI ({student_email}): Fel vid LLM-anrop: {e}", exc_info=True)
        return "Åh nej, nu tappade jag visst bort mig lite..."