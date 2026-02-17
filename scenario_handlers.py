import logging
import re

class BaseScenarioHandler:
    """
    Base class for scenario-specific logic overrides (hooks).
    """
    def __init__(self, scenario_name):
        self.scenario_name = scenario_name

    def on_start_problem(self, problem, track_metadata):
        """Called when a new problem is started."""
        pass

    def modify_start_email_body(self, reply_body, track_metadata):
        """Allows modifying the initial email body (e.g., adding tags)."""
        return reply_body

    def get_eval_history_context(self, full_history_string, track_metadata):
        """Returns the history string to be sent to the evaluator."""
        # Default: No history context for evaluation to keep it simple
        return None

    def on_evaluator_result(self, student_email, score_adjustment, track_metadata):
        """Called after the evaluator has made a decision."""
        pass

    def is_problem_solved(self, is_solved_by_evaluator, track_metadata, score_adjustment, student_email):
        """Final check if the problem is solved, allowing overrides based on state."""
        return is_solved_by_evaluator

    def modify_persona_context(self, persona_context, track_metadata):
        """Allows modifying the context sent to the persona generator."""
        pass

    def modify_persona_reply(self, reply_text, track_metadata):
        """Allows modifying the final reply text before sending."""
        return reply_text

    def check_failure_state(self, track_metadata):
        """
        Returns (is_failed, failure_message).
        If failed, the session is terminated.
        """
        return False, None

class ArgaAlexHandler(BaseScenarioHandler):
    """
    Specific handler for the 'Arga Alex' scenario (anger de-escalation).
    """
    def on_start_problem(self, problem, track_metadata):
        # Arga Alex always starts with 100 anger
        track_metadata["anger_level"] = 100

    def modify_start_email_body(self, reply_body, track_metadata):
        return reply_body + "\n\n[Ilskenivå: 100]"

    def get_eval_history_context(self, full_history_string, track_metadata):
        # Use regex to split history into individual messages (looking for "Name: ")
        history_entries = [e.strip() for e in re.split(r'\n+(?=\S+:\s)', full_history_string.strip()) if e.strip()]
        # Arga Alex needs more history (12 messages / 6 turns)
        return "\n\n".join(history_entries[-12:]) if history_entries else ""

    def on_evaluator_result(self, student_email, score_adjustment, track_metadata):
        # Safety: Default to 100 if missing or invalid (for old sessions)
        if track_metadata.get("anger_level") is None:
            track_metadata["anger_level"] = 100
            
        track_metadata["anger_level"] += score_adjustment
        logging.info(f"Handler ({student_email}): Ilskenivå justerad med {score_adjustment}. Ny nivå: {track_metadata['anger_level']}")

    def is_problem_solved(self, is_solved_by_evaluator, track_metadata, score_adjustment, student_email):
        current_anger = track_metadata.get("anger_level", 100)
        
        # Override 1: Reject if anger is too high
        if is_solved_by_evaluator and current_anger > 10:
             logging.info(f"Handler ({student_email}): Överskrider evaluatorns [LÖST] - Ilskenivå {current_anger} är för hög (>10).")
             return False
        
        # Override 2: Upgrade if anger reaches 0 with good score
        if not is_solved_by_evaluator and current_anger <= 0 and score_adjustment <= -10:
             logging.info(f"Handler ({student_email}): Uppgraderar till [LÖST] – ilskenivå har nått noll via poängjustering.")
             return True
             
        return is_solved_by_evaluator

    def modify_persona_context(self, persona_context, track_metadata):
        persona_context["current_anger_level_tag"] = f"[Ilskenivå: {track_metadata.get('anger_level', 100)}]"

    def modify_persona_reply(self, reply_text, track_metadata):
        if reply_text:
            current_anger = track_metadata.get("anger_level", 100)
            return reply_text + f"\n\n[Ilskenivå: {current_anger}]"
        return reply_text

    def check_failure_state(self, track_metadata):
        anger_level = track_metadata.get("anger_level", 0)
        if anger_level >= 200:
             fail_msg = "\n\n[SYSTEM: KONTAKTEN BRUTEN] Kunden har nått en nivå av raseri där de inte längre går att kommunicera med. Du har MISSLYCKATS med de-eskaleringen. Övningen avbryts."
             return True, fail_msg
        return False, None
