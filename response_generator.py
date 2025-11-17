import re
import json
import logging
from config import PERSONA_MODEL, ULLA_IMAGE_WARNING
from prompts import ULLA_PERSONA_PROMPT
from llm_client import chat_with_model
from email_parser import get_name_from_email

def strip_markdown(text):
    # (No changes to this function)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[-\*\+]\s*', '', text, flags=re.MULTILINE)
    return text

def cap_history(full_history_string, max_turns=4):
    """
    Caps the conversation history to the last `max_turns`.

    A "turn" is defined as two messages. This function identifies individual
    messages by searching for header patterns (e.g., "Name: ") at the start
    of lines. This method allows it to correctly handle messages that
    contain newline characters.
    """
    if not full_history_string:
        return ""

    max_messages = max_turns * 2

    # Regex to find the character index of each message's starting header.
    # A header is defined as a sequence of non-whitespace characters followed
    # by a colon at the beginning of a line.
    message_start_markers = list(re.finditer(r'^\S+:\s', full_history_string, re.MULTILINE))

    # If the number of found messages is not greater than the maximum, return the original string.
    if len(message_start_markers) <= max_messages:
        return full_history_string.strip()

    # Determine the character index where the truncated history should begin.
    truncation_start_index = message_start_markers[-max_messages].start()

    # Extract the relevant part of the history string.
    capped_history = full_history_string[truncation_start_index:].strip()

    # Prepend an indicator that the history has been truncated.
    return f"[...tidigare konversation...]\n{capped_history}"


def get_ulla_persona_reply(student_email, full_history_string_for_ulla, problem_info_for_ulla,
                           latest_student_message_for_ulla, problem_level_idx_for_ulla, evaluator_decision_marker):
    """
    Calls an LLM to generate Ulla's persona reply.
    """
    if not PERSONA_MODEL:
        logging.error(f"Ulla Persona ({student_email}): PERSONA_MODEL ej satt.")
        return "Glömde vad jag skulle säga..."

    logging.info(f"Ulla Persona AI för {student_email} (Nivå {problem_level_idx_for_ulla+1}): Genererar svar baserat på '{evaluator_decision_marker}' med modell '{PERSONA_MODEL}'.")

    system_prompt_content = ULLA_PERSONA_PROMPT

    if evaluator_decision_marker == "[LÖST]":
        user_prompt_content = f"""
        **Din Berättelse (Kontext):**
        ---
        {problem_info_for_ulla['beskrivning']}
        ---
        **Uppgift:** Studentens svar hjälpte dig att lösa problemet. Svara som Ulla och bekräfta glatt att problemet är borta.
        """
    else:
        technical_facts_dict = problem_info_for_ulla.get('tekniska_fakta', {})
        student_name = get_name_from_email(student_email)

        # Truncate the conversation history to the specified number of turns.
        capped_history_string = cap_history(full_history_string_for_ulla, max_turns=4)

        # The prompt structure with history placed before the instructions remains.
        user_prompt_content = f"""
        **Hittillsvarande Konversation:**
        {capped_history_string}

        **{student_name}s Senaste Meddelande till dig:**
        {latest_student_message_for_ulla}

        ---
        **PÅMINNELSE OM DIN SITUATION (Följ detta noga):**

        **Din Berättelse (För din personlighet):**
        {problem_info_for_ulla['beskrivning']}

        **KÄLLFAKTA (Simons lapp, din enda sanning):**
        {json.dumps(technical_facts_dict, indent=2, ensure_ascii=False)}

        **Din Uppgift Nu:** Svara på det senaste meddelandet från {student_name} som karaktären Ulla. Kom ihåg dina "Naturliga Reaktioner" från dina grundinstruktioner. Föreslå ALDRIG en lösning själv.
        """

    messages_for_ulla = [
        {'role': 'system', 'content': system_prompt_content},
        {'role': 'user', 'content': user_prompt_content}
    ]

    try:
        response = chat_with_model(
            model=PERSONA_MODEL,
            messages=messages_for_ulla,
            options={'temperature': 0.7, 'num_predict': 1000, 'repeat_penalty': 1.1}
        )
        if not response:
            return "Åh nej, nu tappade jag visst bort mig lite..."

        ulla_svar = response['message']['content'].strip()
        ulla_svar = re.sub(r"<think>.*?</think>", "", ulla_svar, flags=re.DOTALL).strip()
        ulla_svar = re.sub("</end_of_turn>", "", ulla_svar)
        ulla_svar = strip_markdown(ulla_svar)
        logging.info(f"Ulla Persona AI ({student_email}): Genererade svar: '{ulla_svar[:150]}...'")
        return ulla_svar
    except Exception as e:
        logging.error(f"Ulla Persona AI ({student_email}): Fel vid LLM-anrop: {e}", exc_info=True)
        return "Åh nej, nu tappade jag visst bort mig lite..."