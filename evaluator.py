import re
import logging
from config import EVAL_MODEL
from prompts import EVALUATOR_SYSTEM_PROMPT
from llm_client import chat_with_model
from database import append_evaluator_response_to_debug

def get_evaluator_decision(student_email, problem_description, solution_keywords, latest_student_message_cleaned, problem_id=None):
    """
    Uses LLM to evaluate if the student's message contains a correct solution.
    """
    if not EVAL_MODEL:
        logging.error(f"Evaluator ({student_email}): EVAL_MODEL ej satt.")
        return "[EJ_LÖST]", ""

    # The first item in keywords is a technical description of the problem
    technical_problem_desc = solution_keywords[0]
    actionable_solutions = solution_keywords[1:]

    logging.info(f"Evaluator AI för {student_email}: Utvärderar studentens meddelande med modell '{EVAL_MODEL}'.")

    evaluator_prompt_content = f"""Ullas Problem: "{problem_description}"
Teknisk problembeskrivning: "{technical_problem_desc}"
Korrekta Lösningar/lösningsnyckelord: {actionable_solutions}
Studentens SENASTE Meddelande:
---
{latest_student_message_cleaned}
---
Uppgift: Följ ALLA regler och formatkrav från din system-prompt. Utvärdera studentens meddelande noggrant, generera först ett <think>-block med din fullständiga analys, och avsluta sedan med antingen '[LÖST]' eller '[EJ_LÖST]' på en ny rad.
"""

    messages_for_evaluator = [
        {'role': 'system', 'content': EVALUATOR_SYSTEM_PROMPT},
        {'role': 'user', 'content': evaluator_prompt_content}
    ]

    try:
        response = chat_with_model(
            model=EVAL_MODEL,
            messages=messages_for_evaluator,
            options={'temperature': 0.1, 'num_predict': 2500}
        )
        if not response:
            return "[EJ_LÖST]", ""

        raw_eval_reply_from_llm = response['message']['content'].strip()
        logging.info(f"Evaluator AI ({student_email}): Raw LLM response: '{raw_eval_reply_from_llm}' | Evaluator prompt sent: {evaluator_prompt_content}")
        processed_eval_reply = re.sub(r"<think>.*?</think>", "", raw_eval_reply_from_llm, flags=re.DOTALL).strip()

        if processed_eval_reply != raw_eval_reply_from_llm:
            logging.info(f"Evaluator AI ({student_email}): Removed <think> block. Original: '{raw_eval_reply_from_llm}', Processed: '{processed_eval_reply}'")

        # Save evaluator response to debug database
        if problem_id:
            append_evaluator_response_to_debug(student_email, problem_id, raw_eval_reply_from_llm)

        # Extract the final decision from the LLM response
        lines = processed_eval_reply.strip().split('\n')
        final_decision = ""
        
        # Look for [LÖST] or [EJ_LÖST] at the end of the response
        for line in reversed(lines):
            line = line.strip()
            match = re.match(r'^\s*\[(LÖST|EJ_LÖST)\]\s*$', line)
            if match:
                final_decision = f"[{match.group(1)}]"
                break
        
        if final_decision == "[LÖST]":
            logging.info(f"Evaluator AI ({student_email}): Bedömning [LÖST] (baserat på LLM:s slutgiltiga beslut)")
            return "[LÖST]", raw_eval_reply_from_llm
        elif final_decision == "[EJ_LÖST]":
            logging.info(f"Evaluator AI ({student_email}): Bedömning [EJ_LÖST] (baserat på LLM:s slutgiltiga beslut)")
            return "[EJ_LÖST]", raw_eval_reply_from_llm
        else:
            logging.warning(f"Evaluator AI ({student_email}): Kunde inte hitta ett slutgiltigt beslut i '{processed_eval_reply}', tolkar som [EJ_LÖST].")
            return "[EJ_LÖST]", raw_eval_reply_from_llm
    except Exception as e:
        logging.error(f"Evaluator AI ({student_email}): Fel vid LLM-anrop: {e}", exc_info=True)
        return "[EJ_LÖST]", ""