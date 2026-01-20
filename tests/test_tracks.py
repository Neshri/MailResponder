import unittest
import os
import sys
import shutil
import sqlite3
import datetime
import logging
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Mocks
from mock_factories import MockGraphEmail, MockGraphResponse, MockOllamaResponse

# Import App Modules
import config
import database
import email_processor
import conversation_manager
import tracks

# Set up logging for tests
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class TestTracks(unittest.TestCase):

    def setUp(self):
        # 1. Environment Variables
        os.environ["TARGET_USER_GRAPH_ID"] = "ulla.support@test.se"
        config.TARGET_USER_GRAPH_ID = "ulla.support@test.se"
        
        # 2. LLM Cache Reset (Critical for patch isolation)
        from llm_client import reset_llm_client
        reset_llm_client()
        
        # 3. Database (Clean Slate)
        self.db_path = "test_tracks.db"
        self.completed_db_path = "test_completed_tracks.db"
        self.debug_db_path = "test_debug_tracks.db"
        
        # 3. Patchers
        self.patches = [
            patch('config.DB_FILE', self.db_path),
            patch('database.DB_FILE', self.db_path),
            patch('config.COMPLETED_DB_FILE', self.completed_db_path),
            patch('config.DEBUG_DB_FILE', self.debug_db_path),
            
            patch('email_processor.make_graph_api_call'),
            patch('email_processor.mark_email_as_read'),
            patch('conversation_manager.graph_send_email', return_value=True),
            
            patch('llm_client.ollama'),
            patch('random.choice', side_effect=lambda x: x[0])
        ]
        
        # Start all patches and keep reference to mock objects
        self.mock_objs = {}
        for p in self.patches:
            mock_obj = p.start()
            # Store mock object by its target name (last part of patch path)
            target = p.target.__name__ if hasattr(p.target, '__name__') else str(p.target)
            self.mock_objs[p.attribute] = mock_obj

        # Convenience references
        self.mock_graph_api = self.mock_objs['make_graph_api_call']
        self.mock_graph_send = self.mock_objs['graph_send_email']
        self.mock_ollama_lib = self.mock_objs['ollama']
        
        # Init DBs (Now using patched paths)
        database.init_db()
        database.init_completed_db()
        database.init_debug_db()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        if hasattr(self, 'patcher_init'):
            self.patcher_init.stop()
        
        # Cleanup DBs
        try:
            if os.path.exists(self.db_path): os.remove(self.db_path)
            if os.path.exists(self.completed_db_path): os.remove(self.completed_db_path)
            if os.path.exists(self.debug_db_path): os.remove(self.debug_db_path)
        except PermissionError:
            pass

    def test_01_track_switch_to_evil(self):
        """Scenario: User sends 'Starta deeskalering'. System should switch to 'evil_persona'."""
        sender = "student_evil@test.com"
        
        # 1. Setup Incoming Email
        email_body = "Jag vill starta deeskalering nu!" # Trigger phrase (contains 'starta deeskalering')
        email = MockGraphEmail(sender=sender, subject="Start", body=email_body)
        
        # Mock Graph Response
        self.mock_graph_api.return_value = MockGraphResponse([email.to_dict()])
        
        # 2. Run Processor
        email_processor.graph_check_emails()
        
        # 3. Assertions
        # Check DB for correct track
        _, _, track_id = database.get_student_progress(sender)
        self.assertEqual(track_id, "evil_persona", "Student should be on 'evil_persona' track.")
        
        # Verify call to graph_send_email
        self.mock_graph_send.assert_called()
        args, _ = self.mock_graph_send.call_args
        sent_body = args[2]
        self.assertIn("HÖRRO DU!", sent_body)

    def test_02_evil_persona_llm_routing(self):
        """Scenario: User is in Evil Track. Sends reply. Verify correct System Prompt used."""
        sender = "student_evil_llm@test.com"
        
        # 1. Setup: Put user in Evil Track directly
        database.set_student_track(sender, "evil_persona")
        # Start problem E1_P001 directly
        track_config = tracks.get_track_config("evil_persona")
        problem = track_config["catalog"][0][0]
        # set_active_problem now accepts metadata
        database.set_active_problem(sender, problem, 0, "convo_123", track_metadata={"anger_level": 100})
        
        # 2. Incoming Email (Reply)
        reply_body = "Jag förstår att du är arg, Gunilla. Jag heter Anton och vill hjälpa dig."
        email = MockGraphEmail(sender=sender, subject="Sv: Mail problem", body=reply_body)
        self.mock_graph_api.return_value = MockGraphResponse([email.to_dict()])
        
        # 3. Mock LLM Response
        # By patching init_llm_client, we bypass the health check calls in tests
        self.patcher_init = patch('llm_client.init_llm_client', return_value=self.mock_ollama_lib)
        self.patcher_init.start()
        
        # Evaluator now returns [LÖST]/[EJ_LÖST] and a score delta.
        # But we mock OLLAMA, which returns a raw string.
        # The evaluator.py will parse this.
        mock_eval_response = MockOllamaResponse("<think>Analyzing...</think>\n[SCORE: -20]\n[EJ_LÖST]")
        mock_persona_response = MockOllamaResponse("Hjälpa mig? Du låter som en robot!")
        
        # side_effect for chat
        self.mock_ollama_lib.chat.side_effect = [mock_eval_response, mock_persona_response]

        # 4. Run Processor
        email_processor.graph_check_emails()
        
        # 5. Assertions: Check System Prompt passed to Ollama
        self.assertEqual(self.mock_ollama_lib.chat.call_count, 2)
        
        # Inspect Call 1 (Evaluator)
        args_eval, kwargs_eval = self.mock_ollama_lib.chat.call_args_list[0]
        messages_eval = kwargs_eval.get('messages') or args_eval[1]
        system_content_eval = messages_eval[0]['content']
        self.assertIn("Gunilla", system_content_eval)
        self.assertIn("ilskenivå", system_content_eval)
        self.assertIn("SCORE", system_content_eval)

        # Inspect Call 2 (Persona)
        args_pers, kwargs_pers = self.mock_ollama_lib.chat.call_args_list[1]
        messages_pers = kwargs_pers.get('messages') or args_pers[1]
        system_content_pers = messages_pers[0]['content']
        self.assertIn("Gunilla", system_content_pers)
        self.assertIn("narcissistisk", system_content_pers)

    def test_03_sandbox_flow(self):
        """Scenario: User sends 'aktivera sandlåda'. Verify switch to sandbox track."""
        sender = "sandbox@test.com"
        
        # 1. Trigger Sandbox Track
        email = MockGraphEmail(sender=sender, subject="Sandlåda", body="Snälla aktivera sandlåda")
        self.mock_graph_api.return_value = MockGraphResponse([email.to_dict()])
        
        # Run Processor
        email_processor.graph_check_emails()
        
        # Assert Track
        _, _, track_id = database.get_student_progress(sender)
        self.assertEqual(track_id, "sandbox")
        
        # 2. Start Sandbox Level 1
        email_start = MockGraphEmail(sender=sender, subject="Test", body="testa nivå 1")
        self.mock_graph_api.return_value = MockGraphResponse([email_start.to_dict()])
        
        # Reset send mock to check for new email
        self.mock_graph_send.reset_mock()
        
        # Run Processor
        email_processor.graph_check_emails()
        
        # Verify call to graph_send_email with sandbox problem
        self.mock_graph_send.assert_called()
        args, _ = self.mock_graph_send.call_args
        sent_body = args[2]
        self.assertIn("testmeddelande för sandlådan", sent_body)

if __name__ == '__main__':
    unittest.main()
