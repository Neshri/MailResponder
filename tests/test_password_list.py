import unittest
import sys
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# --- Path Setup ---
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_factories import create_mock_email

class TestPasswordList(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        from database import DatabaseManager
        self.db_manager = DatabaseManager(self.test_dir, db_prefix="test")
        self.db_manager.init_dbs()
        
        from scenario_manager import Scenario
        from scenario_handlers import BaseScenarioHandler
        
        self.problems = [
            [{"id": "L1_P1", "start_prompt": "Prob 1", "persona_context": {}, "evaluator_context": {}}],
            [{"id": "L2_P1", "start_prompt": "Prob 2", "persona_context": {}, "evaluator_context": {}}],
            [{"id": "L3_P1", "start_prompt": "Prob 3", "persona_context": {}, "evaluator_context": {}}]
        ]
        
        self.scenario = Scenario(
            name="Multi Level Scenario",
            persona_name="Test Persona",
            description="Unit Test",
            target_email="test@test.com",
            persona_model="mock-model",
            eval_model="mock-model",
            db_manager=self.db_manager,
            problems=self.problems,
            start_phrases=["phrase1", "phrase2", "phrase3"],
            image_warning="",
            persona_prompt="",
            evaluator_prompt="",
            handler=BaseScenarioHandler("Test")
        )
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('graph_api.get_graph_token', return_value="mock_token")
    @patch('email_processor.make_graph_api_call')
    @patch('email_processor.mark_email_as_read')
    @patch('conversation_manager.graph_send_email', return_value=True)
    # Patch where it's used
    @patch('evaluator.chat_with_model')
    @patch('response_generator.chat_with_model')
    @patch('response_generator.PERSONA_MODEL', 'mock-model')
    @patch('evaluator.EVAL_MODEL', 'mock-model')
    @patch('conversation_manager.random.choice', side_effect=lambda x: x[0])
    def test_password_list_flows(self, mock_choice, mock_chat_resp, mock_chat_eval, mock_send, mock_read, mock_api, mock_token):
        """Verify password listing for L1 solve and final solve."""
        from email_processor import graph_check_emails
        
        # Setup common mock behavior
        def side_effect(model, messages, **kwargs):
            full_content = str(messages)
            if "Solution 1" in full_content or "Solution 3" in full_content:
                return "[LÖST]"
            return "Success Response!"

        mock_chat_eval.side_effect = side_effect
        mock_chat_resp.side_effect = side_effect

        # --- TEST 1: Solve Level 1 ---
        self.db_manager.set_active_problem("user@test.com", self.problems[0][0], 0, "convo1")
        email1 = create_mock_email(sender="user@test.com", body="Solution 1")
        mock_api.side_effect = lambda method, url, **kwargs: {"value": [email1]} if method == "GET" and "messages" in url else {}

        graph_check_emails(self.scenario)
        
        self.assertTrue(mock_send.called)
        reply_body = mock_send.call_args[0][2]
        self.assertIn("Nivå 1: \"phrase1\"", reply_body)
        self.assertIn("Nivå 2: \"phrase2\"", reply_body)
        self.assertNotIn("Nivå 3", reply_body)
        
        mock_send.reset_mock()
        mock_api.reset_mock()

        # --- TEST 2: Solve Level 3 (Final) ---
        self.db_manager.update_student_level("user@test.com", 2)
        self.db_manager.set_active_problem("user@test.com", self.problems[2][0], 2, "convo3")
        email3 = create_mock_email(sender="user@test.com", body="Solution 3")
        mock_api.side_effect = lambda method, url, **kwargs: {"value": [email3]} if method == "GET" and "messages" in url else {}

        graph_check_emails(self.scenario)
        
        self.assertTrue(mock_send.called)
        reply_body = mock_send.call_args[0][2]
        self.assertIn("Nivå 1: \"phrase1\"", reply_body)
        self.assertIn("Nivå 2: \"phrase2\"", reply_body)
        self.assertIn("Nivå 3: \"phrase3\"", reply_body)
        self.assertIn("Du har klarat alla nivåer! Grattis!", reply_body)

if __name__ == '__main__':
    unittest.main()
