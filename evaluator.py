import json
import re
import logging
from config import EVAL_MODEL
from llm_client import chat_with_model

def get_evaluator_decision(student_email, evaluator_context, latest_student_message_cleaned, model_name, problem_id=None, system_prompt=None):
    """
    Uses LLM to evaluate if the student's message contains a correct solution.
    """
    if not model_name:
        logging.error(f"Evaluator ({student_email}): model_name ej satt.")
        return "[EJ_LÖST]", "", 0

    logging.info(f"Evaluator för {student_email}: Utvärderar studentens meddelande med modell '{model_name}'.")

    # Serialize context for the LLM
    context_str = json.dumps(evaluator_context, indent=2, ensure_ascii=False)

    evaluator_prompt_content = f"""
**SCENARIO & UTVÄRDERINGSKONTEXT:**
{context_str}

**Studentens SENASTE Meddelande:**
---
{latest_student_message_cleaned}
---

**Uppgift:**
Följ ALLA regler och formatkrav från din system-prompt.
Utvärdera studentens meddelande noggrant baserat på kontexten ovan.
Generera först ett <think>-block med din fullständiga analys.
Avsluta sedan med antingen '[LÖST]' eller '[EJ_LÖST]' (eller [SCORE: ...]) på en ny rad.
"""
    
    # Fallback if not provided
    if not system_prompt:
        system_prompt = "Bedöm om studenten har löst problemet. Svara [LÖST] eller [EJ_LÖST]."

    messages_for_evaluator = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': evaluator_prompt_content}
    ]

    try:
        response = chat_with_model(
            model=model_name,
            messages=messages_for_evaluator,
            options={'temperature': 0.1, 'num_predict': 2500}
        )
        if not response:
            return "[EJ_LÖST]", "", 0

        raw_eval_reply_from_llm = response.strip()
        logging.info(f"Evaluator ({student_email}): Raw LLM response: '{raw_eval_reply_from_llm}' | Evaluator prompt sent: {evaluator_prompt_content}")
        processed_eval_reply = re.sub(r"<think>.*?</think>", "", raw_eval_reply_from_llm, flags=re.DOTALL).strip()

        if processed_eval_reply != raw_eval_reply_from_llm:
            logging.info(f"Evaluator ({student_email}): Removed <think> block. Original: '{raw_eval_reply_from_llm}', Processed: '{processed_eval_reply}'")

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
        
        # Return result: Only LÖST if explicitly stated, otherwise EJ_LÖST (even if score adjustment exists)
        # This prevents the de-escalation track from finishing before the anger is gone.
        result_marker = final_decision if final_decision else "[EJ_LÖST]"
        
        # We'll return a richer response for conversation_manager to handle
        return result_marker, raw_eval_reply_from_llm, score_adjustment
    except Exception as e:
        logging.error(f"Evaluator ({student_email}): Fel vid LLM-anrop: {e}", exc_info=True)
        return "[EJ_LÖST]", "", 0