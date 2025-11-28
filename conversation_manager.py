import logging
import datetime
import random
from database import (
    get_student_progress, update_student_level, set_active_problem,
    get_current_active_problem, append_to_active_problem_history, clear_active_problem,
    save_completed_conversation
)
from problem_catalog import PROBLEM_CATALOGUES, NUM_LEVELS, START_PHRASES
from graph_api import graph_send_email
from config import ULLA_IMAGE_WARNING
from evaluator import get_evaluator_decision
from response_generator import get_ulla_persona_reply
from email_parser import extract_student_message_from_reply

def handle_start_new_problem_main_thread(email_data, student_next_eligible_level_idx):
    """
    Handle the logic for starting a new problem when a user sends a start command.
    """
    problem_list_for_level = PROBLEM_CATALOGUES[student_next_eligible_level_idx]
    if not problem_list_for_level:
        logging.error(f"Inga problem definierade för nivåindex {student_next_eligible_level_idx}!")
        return False
    problem = random.choice(problem_list_for_level)
    if set_active_problem(email_data["sender_email"], problem, student_next_eligible_level_idx, email_data["graph_conversation_id_incoming"]):
        reply_subject = email_data["subject"]
        reply_body = problem['start_prompt']
        if email_data.get("has_images"):
            reply_body = ULLA_IMAGE_WARNING + "\n\n" + reply_body
        if graph_send_email(email_data["sender_email"], reply_subject, reply_body, conversation_id=email_data["graph_conversation_id_incoming"]):
            logging.info(f"Skickade problem (Nivå {student_next_eligible_level_idx+1}) till {email_data['sender_email']}")
            return True
        else:
            logging.error("Misslyckades skicka initialt problem för ny nivå.")
            clear_active_problem(email_data["sender_email"])
            return False
    else:
        logging.error("Misslyckades sätta aktivt problem i DB för ny nivå.")
        return False

def llm_evaluation_and_reply_task(student_email, full_history_string, problem_info,
                                   latest_student_message_cleaned, problem_level_idx_for_prompt,
                                   active_problem_convo_id_db,
                                   email_data_for_result, student_entry_for_db, problem_id=None):
    """
    Handle LLM evaluation and reply generation for active problems.
    """
    logging.info(f"LLM-tråd (_llm_evaluation_and_reply_task) startad för {student_email}")

    evaluator_marker, evaluator_raw_response = get_evaluator_decision(
        student_email,
        problem_info['beskrivning'],
        problem_info['losning_nyckelord'],
        latest_student_message_cleaned,
        problem_id or problem_info['id']
    )
    is_solved_by_evaluator = (evaluator_marker == "[LÖST]")

    ulla_final_reply_text = get_ulla_persona_reply(
        student_email,
        full_history_string,
        problem_info,
        latest_student_message_cleaned,
        problem_level_idx_for_prompt,
        evaluator_marker
    )

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
        "full_history_string": full_history_string, # Pass this through for archiving
        "has_images": email_data_for_result["has_images"],
        "student_entry_for_db": student_entry_for_db
    }

    if not ulla_final_reply_text:
        result_package["error"] = True
        result_package["send_reply"] = False
        logging.error(f"LLM-tråd ({student_email}): Ulla Persona genererade inget svar.")

    return result_package

def process_completed_problem(result_package, email_data):
    """
    Process the completion of a problem, including level advancement and archiving.
    """
    is_solved = result_package["is_solved"]

    if is_solved and "\nStartfras för nästa nivå" not in result_package["ulla_final_reply_body"] and "\nDu har klarat alla nivåer!" not in result_package["ulla_final_reply_body"]:
        active_lvl_idx = result_package["active_problem_level_idx"]
        prob_id = result_package["active_problem_info_id"]

        student_current_max_level_idx, _ = get_student_progress(email_data["sender_email"])
        potential_new_next_level_idx = active_lvl_idx + 1

        completion_msg = f"\n\nJättebra! Problem {prob_id} (Nivå {active_lvl_idx + 1}) är löst!"

        if potential_new_next_level_idx < NUM_LEVELS:
            next_start_phrase_level_idx = max(potential_new_next_level_idx, student_current_max_level_idx)

            if next_start_phrase_level_idx < NUM_LEVELS:
                completion_msg += f"\nStartfras för nästa nivå ({next_start_phrase_level_idx + 1}): \"{START_PHRASES[next_start_phrase_level_idx]}\""
            else:
                completion_msg += "\nDu har klarat alla nivåer! Grattis!"
        else:
            completion_msg += "\nDu har klarat alla nivåer! Grattis!"
        result_package["ulla_final_reply_body"] += completion_msg

    ulla_db_entry = f"Ulla: {result_package['ulla_final_reply_body']}\n\n"

    reply_s = result_package["reply_subject"]
    if not reply_s.lower().startswith("re:"): reply_s = f"Re: {result_package['reply_subject']}"

    if graph_send_email(email_data["sender_email"], reply_s, result_package["ulla_final_reply_body"],
                        result_package["in_reply_to_for_send"],
                        result_package["references_for_send"],
                        result_package["convo_id_for_send"]):
        # FIRST, save the student's message that we passed through.
        append_to_active_problem_history(email_data["sender_email"], result_package["student_entry_for_db"])

        # SECOND, save Ulla's reply.
        append_to_active_problem_history(email_data["sender_email"], ulla_db_entry)
        if is_solved:
            # --- Save the completed conversation before clearing it ---
            final_history_for_archive = result_package["full_history_string"] + ulla_db_entry
            save_completed_conversation(
                student_email=email_data["sender_email"],
                problem_id=result_package["active_problem_info_id"],
                problem_level_index=result_package["active_problem_level_idx"],
                full_conversation_history=final_history_for_archive,
                evaluator_response=result_package.get("evaluator_response")
            )

            clear_active_problem(email_data["sender_email"])

            current_progress_level_before_update, _ = get_student_progress(email_data["sender_email"])
            new_next_level_for_db = max(current_progress_level_before_update, result_package["active_problem_level_idx"] + 1)

            update_student_level(email_data["sender_email"],
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

def inform_level_error(email_data, student_level_idx, attempted_level_idx=None):
    """
    Inform the student about level access errors.
    """
    if attempted_level_idx is not None:
        msg_body = (f"Hej! Du försökte starta Nivå {attempted_level_idx + 1} (index {attempted_level_idx}), "
                    f"men du har för närvarande endast låst upp nivåer upp till och med Nivå {student_level_idx + 1} (index {student_level_idx}).")

        if student_level_idx < NUM_LEVELS - 1:
            msg_body += (f"\nFör att spela din nästa upplåsta nivå ({student_level_idx + 1}), "
                        f"använd startfrasen: \"{START_PHRASES[student_level_idx]}\"")
        else:
            msg_body = (f"Hej! Du försökte starta Nivå {attempted_level_idx + 1}. "
                        f"Det ser ut som att du redan har klarat alla {NUM_LEVELS} nivåer! Grattis!")
    else:
        # Wrong level start phrase
        any_start_phrase_detected = None
        attempted_level_idx_seq = -1
        for idx_s, phrase_s in enumerate(START_PHRASES):
            if (email_data["subject"] and phrase_s.lower() in email_data["subject"].lower()) or \
               (email_data["cleaned_body"].lower().strip().startswith(phrase_s.lower())):
                any_start_phrase_detected = phrase_s
                attempted_level_idx_seq = idx_s
                break

        if any_start_phrase_detected and attempted_level_idx_seq != student_level_idx and attempted_level_idx_seq <= student_level_idx:
            msg = (f"Hej! Du använde startfrasen för Nivå {attempted_level_idx_seq + 1}. "
                   f"Din nästa nivå är {student_level_idx + 1}. "
                   f"För att starta den, använd: \"{START_PHRASES[student_level_idx]}\".")
        elif student_level_idx >= NUM_LEVELS:
            msg = "Hej! Det ser ut som du redan har klarat alla nivåer! Grattis!"
        else:
            msg = f"Hej! Du har ingen aktiv konversation och ingen giltig startfras detekterades. För att starta nivå {student_level_idx + 1}, använd: \"{START_PHRASES[student_level_idx]}\"."

    if email_data.get("has_images"):
        msg = ULLA_IMAGE_WARNING + "\n\n" + msg

    subj = f"Re: {email_data['subject']}" if email_data['subject'] and not email_data['subject'].lower().startswith("re:") else email_data['subject']
    if not subj: subj = "Angående nivåstart"

    graph_send_email(email_data["sender_email"], subj, msg,
                     email_data["internet_message_id"],
                     email_data["references_header_value"],
                     email_data["graph_conversation_id_incoming"])