import unittest
import sys
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# --- Path Setup ---
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from scenario_manager import Scenario
from scenario_handlers import ArgaAlexHandler
from mock_factories import MockOllamaResponse

class TestArgaAlexLogic(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_manager = DatabaseManager(self.test_dir, db_prefix="alex_logic")
        self.db_manager.init_dbs()
        
        self.problem = {
            "id": "ALEX_P1",
            "start_prompt": "JAG ÄR ARG!",
            "persona_context": {"description": "Angry customer"},
            "evaluator_context": {"solution_keywords": ["sorry"]}
        }
        
        self.scenario = Scenario(
            name="Arga Alex", # Case sensitive check in code
            persona_name="Alex",
            description="De-escalation",
            target_email="alex@test.com",
            persona_model="mock",
            eval_model="mock",
            db_manager=self.db_manager,
            problems=[[self.problem]],
            start_phrases=["start"],
            image_warning="WARN",
            persona_prompt="Persona Prompt",
            evaluator_prompt="Eval Prompt",
            handler=ArgaAlexHandler("Arga Alex")
        )
        
        self.patches = [
            patch('conversation_manager.graph_send_email', return_value=True),
            patch('llm_client.ollama'),
            patch('config.PERSONA_MODEL', 'mock'),
            patch('config.EVAL_MODEL', 'mock'),
            patch('response_generator.PERSONA_MODEL', 'mock'),
            patch('evaluator.EVAL_MODEL', 'mock'),
        ]
        for p in self.patches: p.start()

    def tearDown(self):
        for p in self.patches: p.stop()
        shutil.rmtree(self.test_dir)

    def test_01_anger_accumulation(self):
        """Verify that anger level is correctly stored and updated across turns."""
        from conversation_manager import llm_evaluation_and_reply_task
        
        student_email = "student@test.com"
        # Initial anger is 100
        track_metadata = {"anger_level": 100}
        
        # Mock Evaluator to return a score adjustment of +20
        with patch('conversation_manager.get_evaluator_decision') as mock_eval, \
             patch('conversation_manager.get_persona_reply', return_value="Reply"):
            
            mock_eval.return_value = ("[EJ_LÖST]", "Raw", 20)
            
            result = llm_evaluation_and_reply_task(
                student_email, "History", self.problem, "Latest", 0, "convo_id",
                {"subject": "Sub", "internet_message_id": "id1", "references_header_value": "ref1", "graph_conversation_id_incoming": "g1", "has_images": False},
                "Student Entry", "ALEX_P1", self.scenario, track_metadata=track_metadata
            )
            
            self.assertEqual(result["new_track_metadata"]["anger_level"], 120)

    def test_02_solution_rejection_high_anger(self):
        """Verify that [LÖST] is rejected if anger is > 10."""
        from conversation_manager import llm_evaluation_and_reply_task
        
        student_email = "student@test.com"
        track_metadata = {"anger_level": 50} # Above 10
        
        with patch('conversation_manager.get_evaluator_decision') as mock_eval, \
             patch('conversation_manager.get_persona_reply', return_value="Reply"):
            
            mock_eval.return_value = ("[LÖST]", "Raw", -10) # Evaluator says solved
            
            result = llm_evaluation_and_reply_task(
                student_email, "History", self.problem, "Latest", 0, "convo_id",
                {"subject": "Sub", "internet_message_id": "id1", "references_header_value": "ref1", "graph_conversation_id_incoming": "g1", "has_images": False},
                "Student Entry", "ALEX_P1", self.scenario, track_metadata=track_metadata
            )
            
            self.assertFalse(result["is_solved"], "Should NOT be solved because anger is 40 (50-10)")
            self.assertEqual(result["new_track_metadata"]["anger_level"], 40)

    def test_03_solution_upgrade_zero_anger(self):
        """Verify that [EJ_LÖST] is upgraded to [LÖST] if anger reaches 0 with good score."""
        from conversation_manager import llm_evaluation_and_reply_task
        
        student_email = "student@test.com"
        track_metadata = {"anger_level": 5} 
        
        with patch('conversation_manager.get_evaluator_decision') as mock_eval, \
             patch('conversation_manager.get_persona_reply', return_value="Reply"):
            
            # Evaluator says NOT solved, but score adjustment is -10 (bringing anger to -5)
            mock_eval.return_value = ("[EJ_LÖST]", "Raw", -10) 
            
            result = llm_evaluation_and_reply_task(
                student_email, "History", self.problem, "Latest", 0, "convo_id",
                {"subject": "Sub", "internet_message_id": "id1", "references_header_value": "ref1", "graph_conversation_id_incoming": "g1", "has_images": False},
                "Student Entry", "ALEX_P1", self.scenario, track_metadata=track_metadata
            )
            
            self.assertTrue(result["is_solved"], "Should be upgraded to [LÖST] because anger <= 0")
            self.assertEqual(result["new_track_metadata"]["anger_level"], -5)

    def test_04_fail_state_anger_200(self):
        """Verify that anger >= 200 triggers a failure."""
        from conversation_manager import process_completed_problem
        
        student_email = "student@test.com"
        result_package = {
            "is_solved": False,
            "new_track_metadata": {"anger_level": 205},
            "ulla_final_reply_body": "Go away!",
            "reply_subject": "Re: Help",
            "in_reply_to_for_send": "id1",
            "references_for_send": "ref1",
            "convo_id_for_send": "c1",
            "active_problem_level_idx": 0,
            "active_problem_info_id": "ALEX_P1",
            "student_entry_for_db": "Entry",
            "full_history_string": "Hist"
        }
        
        email_data = {
            "sender_email": student_email,
            "graph_msg_id": "msg_sql_id"
        }
        
        # We need to make sure the student exists in progress table for the update logic
        self.db_manager._init_main_db() # Ensure tables exist
        
        # Check for failure message injection
        with patch('conversation_manager.graph_send_email', return_value=True):
            process_completed_problem(result_package, email_data, self.scenario)
            
            final_reply = result_package["ulla_final_reply_body"]
            self.assertIn("[SYSTEM: KONTAKTEN BRUTEN]", final_reply)
            self.assertIn("MISSLYCKATS", final_reply)
            
            # Verify problem is cleared
            def resolver(pid, tid): return self.problem, 0
            _, prob, _, _, _ = self.db_manager.get_current_active_problem(student_email, resolver)
            self.assertIsNone(prob, "Active problem should be cleared on failure")

if __name__ == "__main__":
    unittest.main()
