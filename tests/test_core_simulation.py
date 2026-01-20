import unittest
import sys
import os
import shutil
import tempfile
import logging
from unittest.mock import patch, MagicMock

# --- Path Setup ---
# Add project root to sys.path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_factories import create_mock_email, MockOllamaResponse

# Function hacks to patch imports before they load effectively
# We need to make sure we use a temporary DB for these tests
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class TestCoreSimulation(unittest.TestCase):
    
    def setUp(self):
        # 1. Setup Temporary Directory for DBs
        self.test_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.test_dir, 'sim_test.db')
        self.completed_db = os.path.join(self.test_dir, 'sim_completed.db')
        self.debug_db = os.path.join(self.test_dir, 'sim_debug.db')
        
        # 2. Patch Configuration Constants GLOBALLY
        # We must patch them in 'config' and anywhere they are imported from 'config'
        self.patches = [
            patch('config.DB_FILE', self.db_file),
            patch('config.COMPLETED_DB_FILE', self.completed_db),
            patch('config.DEBUG_DB_FILE', self.debug_db),
            patch('database.DB_FILE', self.db_file),
            patch('database.COMPLETED_DB_FILE', self.completed_db),
            patch('database.DEBUG_DB_FILE', self.debug_db),
            
            # Patch Graph API in the modules where it is imported
            patch('graph_api.get_graph_token', return_value="mock_token"),
            # We must patch where it is used because of 'from X import Y'
            patch('email_processor.make_graph_api_call'),
            patch('email_processor.mark_email_as_read'),
            patch('conversation_manager.graph_send_email', return_value=True),
            # Also patch active problem getters if needed, but since we use real DB (temp), maybe not?
            # Actually, email_processor imports get_current_active_problem from database
            # We want to use the REAL database logic, so we should NOT patch DB functions unless strictly needed.
            # But we ARE patching config.
            
            # Patch LLM Client - Patching the library wrapper directly is safest
            patch('llm_client.ollama'),
            
            # Patch random.choice to always pick the first problem (determinism)
            patch('conversation_manager.random.choice', side_effect=lambda x: x[0]),
            
            # Patch time.sleep to speed up tests if logic sleeps
            patch('time.sleep', return_value=None),
            patch('email_processor.time.sleep', return_value=None)
        ]
        
        for p in self.patches:
            p.start()
            
        # 3. Initialize fresh DBs
        from llm_client import reset_llm_client
        reset_llm_client()
        
        from database import init_db, init_completed_db, init_debug_db, clear_active_problem
        init_db()
        init_completed_db()
        init_debug_db()
        
    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(self.test_dir)

    def test_01_start_new_session_flow(self):
        """
        Scenario: User sends 'Starta övning'. 
        Expected: System detects start command, sets up DB for Level 1, sends Welcome Email.
        """
        from email_processor import graph_check_emails
        # Import the mocks from the module to configure them
        from email_processor import make_graph_api_call, mark_email_as_read
        from conversation_manager import graph_send_email
        from database import get_current_active_problem

        # Mock: Graph API returns one 'Starta övning' email
        email = create_mock_email(sender="student1@test.com", body="Starta övning tack.")
        
        # Configure make_graph_api_call to return this email when asked for messages
        def mock_api_side_effect(*args, **kwargs):
            # If requesting messages (GET)
            if args[0] == "GET" and "mailFolders/inbox/messages" in args[1]:
                return {"value": [email]}
            return {}
            
        make_graph_api_call.side_effect = mock_api_side_effect

        # --- EXECUTE ---
        graph_check_emails()
        
        # --- VERIFY ---
        # 1. DB should have active problem L1_P001
        history, problem, level_idx, convo_id, metadata = get_current_active_problem("student1@test.com")
        self.assertIsNotNone(problem, "Active problem should be set")
        self.assertEqual(problem['id'], "L1_P001")
        self.assertEqual(level_idx, 0)
        
        # 2. Should have sent a Welcome Email
        # graph_send_email(recipient, subject, body, ...)
        graph_send_email.assert_called()
        call_args = graph_send_email.call_args[0]
        self.assertEqual(call_args[0], "student1@test.com")
        self.assertIn("Kära nån", call_args[2]) # Part of the prompt text for P001

        # 3. Email should be marked as read
        mark_email_as_read.assert_called_with(email['id'])

    def test_02_student_reply_not_solved(self):
        """
        Scenario: Student is in a problem. Sends a vague/unhelpful reply.
        Expected: Evaluator says [EJ_LÖST]. Persona responds with hint.
        """
        from email_processor import graph_check_emails, make_graph_api_call
        from conversation_manager import graph_send_email
        from database import set_active_problem, find_problem_by_id
        from llm_client import ollama as mock_ollama

        # 1. Setup State: Active Problem L1_P001
        problem, _ = find_problem_by_id("L1_P001")
        set_active_problem("student2@test.com", problem, 0, "old_convo_id")
        
        # 2. Mock Input: Student sends generic/vague response
        # "That sounds weird, have you tried waiting?" - Not a concrete technical solution
        email = create_mock_email(sender="student2@test.com", body="Vad konstigt. Har du provat att vänta lite?", subject="Re: Uppdatering")
        
        make_graph_api_call.side_effect = lambda method, url, **kwargs: {"value": [email]} if method == "GET" and "messages" in url else {}

        # 3. Mock LLM Responses
        # The code calls `ollama.chat` twice or more
        
        # customized side effect to return different things based on the prompt content
        def llm_side_effect(model, messages, **kwargs):
            system_prompt = messages[0]['content']
            if "EVALUATOR_SYSTEM_PROMPT" in str(model) or "utvärderings-AI" in system_prompt:
                return MockOllamaResponse("[EJ_LÖST]")
            else:
                return MockOllamaResponse("Har du kollat den blå sladden?")
                
        mock_ollama.chat.side_effect = llm_side_effect

        # --- EXECUTE ---
        graph_check_emails()
        
        # --- VERIFY ---
        # Should send a reply
        graph_send_email.assert_called()
        reply_body = graph_send_email.call_args[0][2]
        self.assertIn("Har du kollat den blå sladden?", reply_body)

    def test_03_student_reply_solved(self):
        """
        Scenario: Student sends correct solution (instruction to Ulla).
        Expected: Evaluator says [LÖST]. System sends "Success" email (or next problem).
        """
        from email_processor import graph_check_emails, make_graph_api_call
        from conversation_manager import graph_send_email
        from database import set_active_problem, find_problem_by_id, get_current_active_problem
        from llm_client import ollama as mock_ollama

        # 1. Setup State: Active Problem L1_P001
        problem, _ = find_problem_by_id("L1_P001")
        set_active_problem("student3@test.com", problem, 0, "convo_1")
        
        # 2. Mock Input: Correct solution (Instruction to Ulla)
        email = create_mock_email(sender="student3@test.com", body="Du måste köra Windows Update på din dator och sedan starta om den.")
        make_graph_api_call.side_effect = lambda method, url, **kwargs: {"value": [email]} if method == "GET" and "messages" in url else {}

        # 3. Mock LLM: Evaluator says [LÖST]
        def llm_side_effect(model, messages, **kwargs):
            system_prompt = messages[0]['content']
            if "utvärderings-AI" in system_prompt:
                return MockOllamaResponse("[LÖST]")
            return MockOllamaResponse("Bra jobbat!") 

        mock_ollama.chat.side_effect = llm_side_effect

        # --- EXECUTE ---
        graph_check_emails()
        
        # --- VERIFY ---
        # 1. Should send success email
        graph_send_email.assert_called()
        
        # 2. User should NO LONGER have an active problem (waiting for next command) OR have moved to next level?
        # Logic: If solved, `process_completed_problem` is called. 
        # It calls `save_completed_conversation` and `update_student_level`.
        # It sends a "Bra jobbat! mail" and CLEARS the active problem.
        
        hist, prob, _, _, _ = get_current_active_problem("student3@test.com")
        self.assertIsNone(prob, "Active problem should be cleared after success")

if __name__ == '__main__':
    # manual test runner to ensure we see output
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCoreSimulation)
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
