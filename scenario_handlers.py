import logging
import re
import random

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

class BengtHandler(BaseScenarioHandler):
    """
    Handler for the 'Bengt' scenario (guiding a non-technical persona to
    correctly read a MAC address off a cluttered device label under mounting,
    passive stress). Unlike Arga Alex, stress rises a fixed amount EVERY turn
    regardless of performance (Krogh's pressure doesn't wait) and can only be
    offset by clear, reassuring instructions. Whether the correct MAC is
    revealed is a weighted random roll ("perception check") rather than a
    hard cutoff, with worse odds as stress rises.

    Tunable constants below are initial proposals, not fixed rules.
    """

    STARTING_STRESS = 30
    PASSIVE_STRESS_PER_TURN = 15
    STRESS_FAIL_THRESHOLD = 100

    # A message's score must be at least this negative (i.e. clearly good)
    # before a reveal roll is attempted at all.
    CLARITY_SCORE_THRESHOLD = -10

    # Floor on reveal probability so it's never quite impossible, even at
    # high stress - mirrors a DnD perception check always having some chance.
    MIN_REVEAL_PROBABILITY = 0.05

    def _generate_random_mac(self):
        return "-".join(f"{random.randint(0, 255):02X}" for _ in range(6))

    def on_start_problem(self, problem, track_metadata):
        track_metadata["stress_level"] = self.STARTING_STRESS
        track_metadata["last_score_adjustment"] = 0
        track_metadata["mac_revealed"] = False

        real_mac = self._generate_random_mac()
        track_metadata["real_mac"] = real_mac

        label_data = problem.get("label_data", {})
        rows = [row.replace("{{MAC_ADDRESS}}", real_mac) for row in label_data.get("rows", [])]
        track_metadata["label_rows"] = rows
        track_metadata["correct_row_key"] = label_data.get("correct_row_key", "")

    def modify_start_email_body(self, reply_body, track_metadata):
        return reply_body + f"\n\n[Stressnivå: {self.STARTING_STRESS}]"

    def get_eval_history_context(self, full_history_string, track_metadata):
        # Keep a modest window of recent turns for evaluator context - enough
        # to judge trend/redundant questions without needing the full thread.
        history_entries = [e.strip() for e in re.split(r'\n+(?=\S+:\s)', full_history_string.strip()) if e.strip()]
        return "\n\n".join(history_entries[-8:]) if history_entries else ""

    def on_evaluator_result(self, student_email, score_adjustment, track_metadata):
        if track_metadata.get("stress_level") is None:
            track_metadata["stress_level"] = self.STARTING_STRESS

        track_metadata["last_score_adjustment"] = score_adjustment
        # Krogh's pressure ticks up every turn regardless of performance;
        # a good (negative) score can offset or reverse it, a bad one compounds it.
        track_metadata["stress_level"] += self.PASSIVE_STRESS_PER_TURN + score_adjustment
        track_metadata["stress_level"] = max(0, track_metadata["stress_level"])

        logging.info(
            f"Handler ({student_email}): Stressnivå justerad med "
            f"{self.PASSIVE_STRESS_PER_TURN + score_adjustment} (bas {self.PASSIVE_STRESS_PER_TURN} + score {score_adjustment}). "
            f"Ny nivå: {track_metadata['stress_level']}"
        )

    def is_problem_solved(self, is_solved_by_evaluator, track_metadata, score_adjustment, student_email):
        # The evaluator's own [LÖST] is ignored - per design, the evaluator
        # decides via its SCORE (which drives stress), and solving is a
        # mechanical consequence of that: a good-enough score earns a
        # perception-check roll against current stress. A pass is an
        # instant win, decided here (before modify_persona_context /
        # persona generation run) so the same turn's reply can already be
        # the celebratory [LÖST] branch.
        if track_metadata.get("mac_revealed"):
            return True

        last_score = track_metadata.get("last_score_adjustment", 0)
        stress = track_metadata.get("stress_level", self.STARTING_STRESS)

        if last_score <= self.CLARITY_SCORE_THRESHOLD:
            # Higher stress -> lower odds, floored so it's never quite impossible.
            reveal_probability = max(self.MIN_REVEAL_PROBABILITY, 1 - (stress / 100))
            roll = random.random()
            passed = roll < reveal_probability
            logging.info(
                f"Handler ({student_email}): MAC-reveal roll - stress={stress}, "
                f"sannolikhet={reveal_probability:.2f}, slag={roll:.2f}, "
                f"resultat={'LYCKAT' if passed else 'MISSLYCKAT'}"
            )
            if passed:
                track_metadata["mac_revealed"] = True
                return True

        return False

    def modify_persona_context(self, persona_context, track_metadata):
        stress = track_metadata.get("stress_level", self.STARTING_STRESS)
        persona_context["current_stress_tag"] = f"[Stressnivå: {stress}]"

        if track_metadata.get("mac_revealed"):
            # The [LÖST] branch in response_generator only reads
            # 'description' and 'success_outcome' from persona_context - it
            # never sees etikett_rad_att_lasa or other fields. So the actual
            # MAC has to be embedded directly into success_outcome, or the
            # win turn's reply would never actually contain the code Bengt
            # was supposed to be revealing.
            real_mac = track_metadata.get("real_mac", "")
            persona_context["success_outcome"] = (
                f"Bengt hittar och läser tydligt upp rätt kod på etiketten: {real_mac}. "
                "Ge honom en kort, tacksam och lättad slutreplik där han läser upp "
                f"koden rakt av (t.ex. \"Jag tror jag hittade den: {real_mac}\") innan "
                "han avslutar mejlet. Lättnaden gäller inte bara skrivaren, utan också "
                "att ärendet löstes utan att dra ut på tiden. Han tackar gärna lite väl mycket."
            )
            return

        rows = track_metadata.get("label_rows", [])
        correct_key = track_metadata.get("correct_row_key", "")
        distractor_rows = [r for r in rows if correct_key not in r]
        if distractor_rows:
            persona_context["etikett_rad_att_lasa"] = random.choice(distractor_rows)
        else:
            persona_context["etikett_rad_att_lasa"] = "[flera rader, oklart vilken som menas]"

    def modify_persona_reply(self, reply_text, track_metadata):
        if reply_text:
            stress = track_metadata.get("stress_level", self.STARTING_STRESS)
            return reply_text + f"\n\n[Stressnivå: {stress}]"
        return reply_text

    def check_failure_state(self, track_metadata):
        # Once the goal is achieved, a same-turn or later passive stress tick
        # must not be able to clobber the win - check_failure_state runs
        # after modify_persona_context in the calling code, so without this
        # guard a reveal and a stress-threshold breach on the same turn would
        # incorrectly archive the session as a failure.
        if track_metadata.get("mac_revealed"):
            return False, None

        stress = track_metadata.get("stress_level", 0)
        if stress >= self.STRESS_FAIL_THRESHOLD:
            fail_msg = (
                "\n\n[SYSTEM: ÄRENDET AVBRUTET] Bengt är för stressad och disträ för att fortsätta "
                "vara till hjälp just nu. Övningen avbryts."
            )
            return True, fail_msg
        return False, None


# Registry mapping scenario_name -> handler class. Add new scenarios here
# only - nowhere else needs to change. See get_handler_for_scenario() below.
HANDLER_REGISTRY = {
    "Arga Alex": ArgaAlexHandler,
    "Bengt Support": BengtHandler,
}


def get_handler_for_scenario(scenario_name):
    """
    Looks up the registered handler class for a scenario name and
    instantiates it, falling back to BaseScenarioHandler if none is
    registered. Wherever the current if/elif factory function lives, it can
    call this instead - so adding a new scenario's handler only ever
    requires editing HANDLER_REGISTRY above, in this one file.
    """
    handler_cls = HANDLER_REGISTRY.get(scenario_name, BaseScenarioHandler)
    return handler_cls(scenario_name)