import logging
import random
import re
from graph_api import graph_send_email
from evaluator import get_evaluator_decision
from response_generator import get_persona_reply
from email_parser import extract_student_message_from_reply

# Note: We do not import Scenario for runtime usage to avoid circular imports, 
# but we expect 'scenario' arguments to be of type Scenario.

def handle_start_new_problem_main_thread(email_data, student_next_eligible_level_idx, scenario):
    """
    Handle the logic for starting a new problem when a user sends a start command.
    """
    # 2. Get Catalog from Scenario
    problem_catalog = scenario.problems
    
    if student_next_eligible_level_idx >= len(problem_catalog):
         logging.error(f"Nivåindex {student_next_eligible_level_idx} utanför katalogen för scenario {scenario.name}!")
         return False

    problem_list_for_level = problem_catalog[student_next_eligible_level_idx]
    
    if not problem_list_for_level:
        logging.error(f"Inga problem definierade för nivåindex {student_next_eligible_level_idx} i scenario {scenario.name}!")
        return False
        
    problem = random.choice(problem_list_for_level)
    
    # Initialize Track Metadata if needed
    track_metadata = {}
    scenario.handler.on_start_problem(problem, track_metadata)

    if scenario.db_manager.set_active_problem(email_data["sender_email"], problem, student_next_eligible_level_idx, email_data["graph_conversation_id_incoming"], track_metadata=track_metadata, persona_name=scenario.persona_name):
        reply_subject = email_data["subject"]
        initial_rant = problem['start_prompt']
        briefing_header = ""
        
        if "internal_briefing" in problem:
            briefing = problem["internal_briefing"]
            briefing_header = f"*** INTERNT MEDDELANDE: {briefing.get('subject')} ***\n"
            briefing_header += f"{briefing.get('body')}\n"
            briefing_header += "--------------------------------------------------\n\n"
        
        reply_body = briefing_header + initial_rant
        
        # Scenario-specific modification (e.g., inject anger level)
        reply_body = scenario.handler.modify_start_email_body(reply_body, track_metadata)

        if email_data.get("has_images"):
            reply_body = scenario.image_warning + "\n\n" + reply_body
        
        if graph_send_email(email_data["sender_email"], reply_subject, reply_body, conversation_id=email_data["graph_conversation_id_incoming"], from_user_id=scenario.target_email):
            scenario.db_manager.mark_email_as_processed(email_data["graph_msg_id"])
            logging.info(f"Skickade problem (Nivå {student_next_eligible_level_idx+1}) till {email_data['sender_email']} [Scenario: {scenario.name}]")
            
            if briefing_header:
                logging.info(f"LLM-start: Briefing inkluderad i start-mejlet för {problem.get('id')}.")

            return True
        else:
            logging.error("Misslyckades skicka initialt problem för ny nivå.")
            scenario.db_manager.clear_active_problem(email_data["sender_email"])
            return False
    else:
        logging.error("Misslyckades sätta aktivt problem i DB för ny nivå.")
        return False

def llm_evaluation_and_reply_task(student_email, full_history_string, problem_info,
                                   latest_student_message_cleaned, problem_level_idx_for_prompt,
                                   active_problem_convo_id_db,
                                   email_data_for_result, student_entry_for_db, problem_info_id, 
                                   scenario,
                                   track_metadata=None): 
    """
    Handle LLM evaluation and reply generation for active problems.
    """
    logging.info(f"LLM-tråd (_llm_evaluation_and_reply_task) startad för {student_email} [Scenario: {scenario.name}]")
    
    if track_metadata is None: track_metadata = {}

    # 1. Evaluate
    # Extract Contexts - Support legacy and new structure
    evaluator_context = problem_info.get('evaluator_context')
    if not evaluator_context: 
        # Fallback/Legacy construction if 'losning_nyckelord' exists directly
        evaluator_context = {
            "source_problem_description": problem_info.get('beskrivning', ''),
            "solution_keywords": problem_info.get('losning_nyckelord', [])
        }

    # Pass history context ONLY for scenarios that need it (e.g., de-escalation/trend analysis)
    eval_history_context = scenario.handler.get_eval_history_context(full_history_string, track_metadata)

    evaluator_marker, evaluator_raw_response, score_adjustment = get_evaluator_decision(
        student_email,
        evaluator_context,
        latest_student_message_cleaned,
        scenario.eval_model,
        problem_info_id,
        system_prompt=scenario.evaluator_prompt,
        history_string=eval_history_context
    )
    
    # Update state via handler if applicable
    scenario.handler.on_evaluator_result(student_email, score_adjustment, track_metadata)

    # Store the raw evaluator response in the debug log
    scenario.db_manager.add_debug_evaluator_response(student_email, problem_info_id, evaluator_raw_response)
    
    is_solved_by_evaluator = (evaluator_marker == "[LÖST]")
    
    # Scenario-specific solve logic (e.g., Arga Alex rejection/upgrade)
    is_solved_by_evaluator = scenario.handler.is_problem_solved(is_solved_by_evaluator, track_metadata, score_adjustment, student_email)
    evaluator_marker = "[LÖST]" if is_solved_by_evaluator else "[EJ_LÖST]"

    # 2. Generate Reply
    context_enhanced_history = full_history_string
    
    persona_context = problem_info.get('persona_context', {}).copy()
    if not persona_context:
        # Fallback/Legacy
        persona_context = {
            "description": problem_info.get('beskrivning', ''),
            "technical_facts": problem_info.get('tekniska_fakta', {})
        }
    
    # Inject Anger Level into context via handler
    scenario.handler.modify_persona_context(persona_context, track_metadata)
    
    ulla_final_reply_text = get_persona_reply(
        student_email,
        context_enhanced_history,
        persona_context,
        latest_student_message_cleaned,
        problem_level_idx_for_prompt,
        evaluator_marker,
        system_prompt=scenario.persona_prompt,
        has_images=email_data_for_result.get("has_images", False)
    )

    # Scenario-specific reply modification
    ulla_final_reply_text = scenario.handler.modify_persona_reply(ulla_final_reply_text, track_metadata)

    result_package = {
        "email_data": email_data_for_result,
        "ulla_final_reply_body": ulla_final_reply_text,
        "is_solved": is_solved_by_evaluator,
        "evaluator_response": evaluator_raw_response,
        "error": False,
        "send_reply": bool(ulla_final_reply_text),
        "active_problem_level_idx": problem_level_idx_for_prompt,
        "active_problem_info_id": problem_info['id'],
        "active_problem_convo_id_db": active_problem_convo_id_db,
        "reply_subject": email_data_for_result["subject"],
        "in_reply_to_for_send": email_data_for_result["internet_message_id"],
        "references_for_send": f"{email_data_for_result['references_header_value'] if email_data_for_result['references_header_value'] else ''} {email_data_for_result['internet_message_id']}".strip(),
        "convo_id_for_send": email_data_for_result["graph_conversation_id_incoming"] or active_problem_convo_id_db,
        "full_history_string": full_history_string,
        "has_images": email_data_for_result["has_images"],
        "student_entry_for_db": student_entry_for_db,
        "new_track_metadata": track_metadata 
    }

    if not ulla_final_reply_text:
        result_package["error"] = True
        result_package["send_reply"] = False
        logging.error(f"LLM-tråd ({student_email}): Persona ({scenario.name}) genererade inget svar.")

    return result_package

def process_completed_problem(result_package, email_data, scenario):
    """
    Process the completion of a problem, including level advancement and archiving.
    """
    is_solved = result_package["is_solved"]
    
    # Check for Fail State via handler
    track_metadata = result_package.get("new_track_metadata", {})
    is_failed, fail_msg = scenario.handler.check_failure_state(track_metadata)

    if is_failed:
         result_package["is_solved"] = False # Ensure it counts as a fail
         result_package["ulla_final_reply_body"] += fail_msg
         logging.warning(f"Main: Student {email_data['sender_email']} misslyckades [Scenario: {scenario.name}].")

    if is_solved and not is_failed and "\nStartfras för nästa nivå" not in result_package["ulla_final_reply_body"] and "\nDu har klarat alla nivåer!" not in result_package["ulla_final_reply_body"]:
        active_lvl_idx = result_package["active_problem_level_idx"]
        prob_id = result_package["active_problem_info_id"]
        
        num_levels = len(scenario.problems)
        student_current_max_level_idx, _, _ = scenario.db_manager.get_student_progress(email_data["sender_email"]) 
        potential_new_next_level_idx = max(active_lvl_idx + 1, student_current_max_level_idx)
        
        # Determine the highest unlocked level index (cap it at total levels)
        highest_unlocked_idx = min(potential_new_next_level_idx, num_levels - 1)

        completion_msg = f"\n\nJättebra! Problem {prob_id} (Nivå {active_lvl_idx + 1}) är löst!"
        completion_msg += "\n\nTillgängliga startfraser för detta scenario:"
        
        for i in range(highest_unlocked_idx + 1):
            phrase = scenario.start_phrases[i]
            completion_msg += f"\nNivå {i + 1}: \"{phrase}\""
        
        if potential_new_next_level_idx >= num_levels:
            completion_msg += "\n\nDu har klarat alla nivåer! Grattis!"
            
        result_package["ulla_final_reply_body"] += completion_msg

    if email_data.get("has_images") and scenario.image_warning:
        result_package["ulla_final_reply_body"] = scenario.image_warning + "\n\n" + result_package["ulla_final_reply_body"]

    ulla_db_entry = f"{scenario.persona_name}: {result_package['ulla_final_reply_body']}\n\n"

    reply_s = result_package["reply_subject"]
    if not reply_s.lower().startswith("re:"): reply_s = f"Re: {result_package['reply_subject']}"

    if graph_send_email(email_data["sender_email"], reply_s, result_package["ulla_final_reply_body"],
                        result_package["in_reply_to_for_send"],
                        result_package["references_for_send"],
                        result_package["convo_id_for_send"],
                        from_user_id=scenario.target_email):
        scenario.db_manager.mark_email_as_processed(email_data["graph_msg_id"])
        # Update Metadata if provided (e.g. stateful score tracking)
        if result_package.get("new_track_metadata"):
            scenario.db_manager.update_active_problem_metadata(email_data["sender_email"], result_package["new_track_metadata"])

        # FIRST, save the student's message that we passed through.
        scenario.db_manager.append_to_active_problem_history(email_data["sender_email"], result_package["student_entry_for_db"])

        # SECOND, save Persona's reply.
        scenario.db_manager.append_to_active_problem_history(email_data["sender_email"], ulla_db_entry)
        
        if is_solved or is_failed:
            # --- Save the completed conversation before clearing it ---
            final_history_for_archive = result_package["full_history_string"] + ulla_db_entry
            scenario.db_manager.save_completed_conversation(
                student_email=email_data["sender_email"],
                problem_id=result_package["active_problem_info_id"],
                problem_level_index=result_package["active_problem_level_idx"],
                full_conversation_history=final_history_for_archive,
                evaluator_response=result_package.get("evaluator_response")
            )

            scenario.db_manager.clear_active_problem(email_data["sender_email"])

            if is_failed:
                # Don't advance level, but we could inform the student to try again
                return True

            current_progress_level_before_update, _, _ = scenario.db_manager.get_student_progress(email_data["sender_email"])
            new_next_level_for_db = max(current_progress_level_before_update, result_package["active_problem_level_idx"] + 1)

            scenario.db_manager.update_student_level(email_data["sender_email"],
                                 new_next_level_for_db,
                                 result_package["active_problem_info_id"])
            if new_next_level_for_db > current_progress_level_before_update:
                logging.info(f"Main: Student {email_data['sender_email']} avancerade till nästa nivå index {new_next_level_for_db} (Nivå {new_next_level_for_db+1}) efter att ha klarat problem {result_package['active_problem_info_id']}.")
            else:
                logging.info(f"Main: Student {email_data['sender_email']} klarade om problem {result_package['active_problem_info_id']} (nivå index {result_package['active_problem_level_idx']}). Huvudprogression oförändrad på index {current_progress_level_before_update}.")

        return True
    else:
        logging.error(f"Main: Misslyckades skicka svar för {email_data['graph_msg_id']} efter LLM.")
        return False

def inform_level_error(email_data, student_level_idx, scenario, attempted_level_idx=None):
    """
    Inform the student about level access errors.
    """
    start_phrases = scenario.start_phrases
    num_levels = len(scenario.problems)

    if attempted_level_idx is not None:
        msg_body = (f"Hej! Du försökte starta Nivå {attempted_level_idx + 1} (index {attempted_level_idx}), "
                    f"men du har för närvarande endast låst upp nivåer upp till och med Nivå {student_level_idx + 1} (index {student_level_idx}).")

        if student_level_idx < num_levels - 1:
            msg_body += (f"\nFör att spela din nästa upplåsta nivå ({student_level_idx + 1}), "
                        f"använd startfrasen: \"{start_phrases[student_level_idx]}\"")
        else:
            msg_body = (f"Hej! Du försökte starta Nivå {attempted_level_idx + 1}. "
                        f"Det ser ut som att du redan har klarat alla {num_levels} nivåer! Grattis!")
    else:
        # Wrong level start phrase
        any_start_phrase_detected = None
        attempted_level_idx_seq = -1
        for idx_s, phrase_s in enumerate(start_phrases):
            if (email_data["subject"] and phrase_s.lower() in email_data["subject"].lower()) or \
               (email_data["cleaned_body"].lower().strip().startswith(phrase_s.lower())):
                any_start_phrase_detected = phrase_s
                attempted_level_idx_seq = idx_s
                break

        if any_start_phrase_detected and attempted_level_idx_seq != student_level_idx and attempted_level_idx_seq <= student_level_idx:
            msg = (f"Hej! Du använde startfrasen för Nivå {attempted_level_idx_seq + 1}. "
                   f"Din nästa nivå är {student_level_idx + 1}. "
                   f"För att starta den, använd: \"{start_phrases[student_level_idx]}\".")
        elif student_level_idx >= num_levels:
            msg = "Hej! Det ser ut som du redan har klarat alla nivåer! Grattis!"
        else:
            msg = f"Hej! Du har ingen aktiv konversation och ingen giltig startfras detekterades. För att starta nivå {student_level_idx + 1}, använd: \"{start_phrases[student_level_idx]}\"."

    if email_data.get("has_images"):
        msg = scenario.image_warning + "\n\n" + msg

    subj = f"Re: {email_data['subject']}" if email_data['subject'] and not email_data['subject'].lower().startswith("re:") else email_data['subject']
    if not subj: subj = "Angående nivåstart"

    if graph_send_email(email_data["sender_email"], subj, msg,
                     email_data["internet_message_id"],
                     email_data["references_header_value"],
                     email_data["graph_conversation_id_incoming"],
                     from_user_id=scenario.target_email):
        scenario.db_manager.mark_email_as_processed(email_data["graph_msg_id"])
