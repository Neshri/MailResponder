import re
import json
import logging
from config import PERSONA_MODEL, ULLA_IMAGE_WARNING
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


def get_persona_reply(student_email, full_history_string, persona_context,
                        latest_student_message, problem_level_idx, evaluator_decision_marker, 
                        system_prompt=None, has_images=False, model_name=None):
    """
    Calls an LLM to generate the Persona's reply.

    model_name should be the scenario's own persona model (e.g.
    scenario.persona_model) - callers must pass it explicitly. If omitted,
    falls back to the global PERSONA_MODEL default for backward
    compatibility, but any scenario with its own model configured
    (via config.json or a scenario-specific .env) will silently use the
    wrong model unless its caller passes model_name through.
    """
    model_to_use = model_name or PERSONA_MODEL
    if not model_to_use:
        logging.error(f"Persona ({student_email}): Inget persona-modellnamn tillgängligt (varken model_name eller global PERSONA_MODEL).")
        return "Glömde vad jag skulle säga..."

    logging.info(f"Persona AI för {student_email} (Nivå {problem_level_idx+1}): Genererar svar baserat på '{evaluator_decision_marker}' med modell '{model_to_use}'.")

    # Extract current mood tag if it exists in context. Different scenario
    # handlers use different key names (e.g. Arga Alex sets
    # "current_anger_level_tag", Bengt sets "current_stress_tag") - check
    # known keys rather than hardcoding one, so new handlers don't need a
    # matching edit here to have their mood tag actually used.
    mood_tag = None
    for mood_key in ("current_anger_level_tag", "current_stress_tag"):
        if mood_key in persona_context:
            mood_tag = persona_context.pop(mood_key)
            break

    system_prompt_content = system_prompt if system_prompt else "Du är en hjälpsam assistent."
    
    # Inject mood into system prompt if present to separate it from conversation history
    if mood_tag:
        system_prompt_content += f"\n\nDIN NUVARANDE SINNESSTÄMNING: {mood_tag}"

    if evaluator_decision_marker == "[LÖST]":
        # SUCCESS STATE - Use scenario-specific resolution if available
        description = persona_context.get('description', 'Problemet')
        reality = persona_context.get('reality', {})
        # Prefer a nested reality.success_outcome (Arga Alex's shape) if present,
        # otherwise a flat success_outcome (e.g. set by BengtHandler), otherwise
        # a generic fallback.
        success_outcome = (
            reality.get('success_outcome')
            or persona_context.get('success_outcome')
            or 'Studentens svar hjälpte dig att lösa problemet! Du ser nu att allt fungerar som det ska.'
        )
        
        user_prompt_content = f"""
        **Din Berättelse (Kontext):**
        ---
        {description}
        ---
        **Utfall:** 
        {success_outcome}
        ---
        **Uppgift:** 
        Svara i karaktär baserat på utfallet ovan. Om utfallet innebär att problemet är löst, bekräfta detta hånfullt eller snäsigt. 
        Om utfallet innebär att kontakten bryts eller att du blivit "besegrad" av en gränssättning, svara enligt det.
        """
        if has_images:
             user_prompt_content += "\n\n(OBS: Studenten skickade med en bild som du inte kan se. Nämn detta kort i din karaktär.)"
    else:
        student_name = get_name_from_email(student_email)
        
        # Truncate the conversation history
        capped_history_string = cap_history(full_history_string, max_turns=4)

        # Serialize remaining context
        context_str = json.dumps(persona_context, indent=2, ensure_ascii=False)

        # UPDATED PROMPT STRUCTURE (Clean and context-focused)
        user_prompt_content = f"""
        **Hittillsvarande Konversation:**
        {capped_history_string}

        ---
        **DIN KONTEXT & VERKLIGHET:**
        {context_str}

        ---
        **{student_name}s Senaste Meddelande till dig:**
        {latest_student_message}

        ---
        **Din Uppgift:** 
        Svara {student_name} baserat på din karaktär och kontexten ovan.
        Referera endast till fakta som finns i din KONTEXT & VERKLIGHET.
        Hitta inte på tekniska detaljer som inte står där.
        """
        if has_images:
             user_prompt_content += "\n\n(OBS: Studenten skickade med en bild som du inte kan se. Nämn detta kort i din karaktär.)"

    messages_for_mailbot = [
        {'role': 'system', 'content': system_prompt_content},
        {'role': 'user', 'content': user_prompt_content}
    ]

    try:
        response = chat_with_model(
            model=model_to_use,
            messages=messages_for_mailbot,
            options={'temperature': 0.8, 'num_predict': 16000, 'repeat_penalty': 1.1}
        )
        if not response:
            return "Åh nej, nu tappade jag visst bort mig lite..."

        persona_svar = response.strip()
        persona_svar = re.sub(r"<think>.*?</think>", "", persona_svar, flags=re.DOTALL).strip()
        
        # STRICT CLEANING: Remove any hallucinated state tags. Matches any
        # "[...nivå: ...]"-style bracket tag (Ilskenivå, Stressnivå, and any
        # future scenario's mood tag) rather than one hardcoded name, so a
        # new handler's tag is cleaned up automatically.
        persona_svar = re.sub(r"\[\S*[Nn]ivå:.*?\]", "", persona_svar).strip()
        
        # Clean up common LLM artifacts
        artifacts_to_strip = [
            "</end_of_turn>", "<end_of_turn>", 
            "</start_of_turn>", "<start_of_turn>",
            "</startofturn>", "<startofturn>",
            "</endofturn>", "<endofturn>",
            "User:", "Assistant:", "Human:", "AI:"
        ]
        for art in artifacts_to_strip:
            persona_svar = persona_svar.replace(art, "")

        persona_svar = strip_markdown(persona_svar.strip())
        logging.info(f"Persona AI ({student_email}): Genererade svar: '{persona_svar}'")
        return persona_svar
    except Exception as e:
        logging.error(f"Persona AI ({student_email}): Fel vid LLM-anrop: {e}", exc_info=True)
        return "Åh nej, nu tappade jag visst bort mig lite..."