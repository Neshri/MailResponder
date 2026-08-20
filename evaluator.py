import json
import re
import logging
from config import EVAL_MODEL
from llm_client import chat_with_model

def get_evaluator_decision(student_email, evaluator_context, latest_student_message_cleaned, model_name, problem_id=None, system_prompt=None, history_string=None):
    """
    Uses LLM to evaluate if the student's message contains a correct solution.

    Returns a 4-tuple: (result_marker, raw_response, score_adjustment, eval_tags).
    eval_tags is a dict of every [TAG_NAME: value] the evaluator's system
    prompt asked it to emit (besides SCORE/LÖST/EJ_LÖST, which are parsed
    separately below). Tag names may use Å/Ä/Ö. A tag value of JA/NEJ is
    normalized to True/False; anything else is kept as the raw string.
    Scenarios that don't request any tags (e.g. Arga Alex) simply get an
    empty dict, so eval_tags.get("WHATEVER_TAG") reads as None - same
    "not applicable" behavior as a missing key always had.
    """
    if not model_name:
        logging.error(f"Evaluator ({student_email}): model_name ej satt.")
        return "[EJ_LÖST]", "", 0, {}

    logging.info(f"Evaluator för {student_email}: Utvärderar studentens meddelande med modell '{model_name}'.")

    # Serialize context for the LLM
    context_str = json.dumps(evaluator_context, indent=2, ensure_ascii=False)

    history_block = f"\n**Konversationshistorik (för sammanhang):**\n---\n{history_string}\n---\n" if history_string else ""

    evaluator_prompt_content = f"""
**SCENARIO & UTVÄRDERINGSKONTEXT:**
{context_str}
{history_block}
**Studentens SENASTE Meddelande:**
---
{latest_student_message_cleaned}
---

**Uppgift:**
Följ ALLA regler och formatkrav från din system-prompt.
Utvärdera studentens SENASTE meddelande noggrant baserat på kontexten och historiken ovan.
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
            options={'temperature': 0.1, 'num_predict': 16000}
        )
        if not response:
            return "[EJ_LÖST]", "", 0, {}

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

        # Generic tag scan: pick up every [TAG_NAME: value] the scenario's
        # evaluator_prompt.txt asked for (e.g. MAC_RELEVANT, ORSAK_FÖRKLARAD),
        # without evaluator.py needing to know which scenario requested what.
        # SCORE is excluded since it's parsed above with signed-int semantics;
        # LÖST/EJ_LÖST have no colon so they never match this pattern anyway.
        eval_tags = {}
        for tag_name, tag_value in re.findall(r'\[([A-ZÅÄÖ_]+):\s*([^\]]+)\]', processed_eval_reply):
            if tag_name == "SCORE":
                continue
            tag_value = tag_value.strip()
            if tag_value.upper() in ("JA", "NEJ"):
                eval_tags[tag_name] = tag_value.upper() == "JA"
            else:
                eval_tags[tag_name] = tag_value

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
        return result_marker, raw_eval_reply_from_llm, score_adjustment, eval_tags
    except Exception as e:
        logging.error(f"Evaluator ({student_email}): Fel vid LLM-anrop: {e}", exc_info=True)
        return "[EJ_LÖST]", "", 0, {}