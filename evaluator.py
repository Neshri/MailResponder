import re
import logging
from config import EVAL_MODEL
from prompts import EVALUATOR_SYSTEM_PROMPT
from llm_client import chat_with_model
from database import append_evaluator_response_to_debug

def get_evaluator_decision(student_email, problem_description, solution_keywords, latest_student_message_cleaned, problem_id=None, system_prompt=None):
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
    
    # Fallback if not provided
    if not system_prompt:
        system_prompt = EVALUATOR_SYSTEM_PROMPT

    messages_for_evaluator = [
        {'role': 'system', 'content': system_prompt},
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

        raw_eval_reply_from_llm = response.strip()
        logging.info(f"Evaluator AI ({student_email}): Raw LLM response: '{raw_eval_reply_from_llm}' | Evaluator prompt sent: {evaluator_prompt_content}")
        processed_eval_reply = re.sub(r"<think>.*?</think>", "", raw_eval_reply_from_llm, flags=re.DOTALL).strip()

        if processed_eval_reply != raw_eval_reply_from_llm:
            logging.info(f"Evaluator AI ({student_email}): Removed <think> block. Original: '{raw_eval_reply_from_llm}', Processed: '{processed_eval_reply}'")

        # Save evaluator response to debug database
        if problem_id:
            append_evaluator_response_to_debug(student_email, problem_id, raw_eval_reply_from_llm)

        # Extract the final decision or score from the LLM response
        lines = processed_eval_reply.strip().split('\n')
        final_decision = ""
        score_adjustment = 0
        
        # Look for [SCORE: +/-X] or [LÖST]/[EJ_LÖST]
        # Check for Score first as it's the new multi-turn mechanic
        score_match = re.search(r'\[SCORE:\s*([+-]?\d+)\]', processed_eval_reply)
        if score_match:
            score_adjustment = int(score_match.group(1))

        for line in reversed(lines):
            line = line.strip()
            match = re.match(r'^\s*\[(LÖST|EJ_LÖST)\]\s*$', line)
            if match:
                final_decision = f"[{match.group(1)}]"
                break
        
        # Return result with potential score adjustment
        result_marker = final_decision if final_decision else ("[LÖST]" if score_adjustment != 0 else "[EJ_LÖST]")
        
        # We'll return a richer response for conversation_manager to handle
        return result_marker, raw_eval_reply_from_llm, score_adjustment
    except Exception as e:
        logging.error(f"Evaluator AI ({student_email}): Fel vid LLM-anrop: {e}", exc_info=True)
        return "[EJ_LÖST]", ""