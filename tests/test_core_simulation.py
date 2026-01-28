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
        
        # 2. Patch Graph API & LLM Dependencies
        self.patches = [
            patch('graph_api.get_graph_token', return_value="mock_token"),
            patch('email_processor.make_graph_api_call'),
            patch('email_processor.mark_email_as_read'),
            patch('conversation_manager.graph_send_email', return_value=True),
            patch('llm_client.ollama'),
            # Patch random.choice to always pick the first problem (determinism)
            patch('conversation_manager.random.choice', side_effect=lambda x: x[0]),
        ]
        
        for p in self.patches:
            p.start()
            
        # 3. Initialize fresh DBs via DatabaseManager
        from database import DatabaseManager
        self.db_manager = DatabaseManager(self.test_dir, db_prefix="test")
        self.db_manager.init_dbs()
        
        # 4. Create Mock Scenario
        from scenario_manager import Scenario
        
        self.mock_problem = {
            "id": "L1_P001",
            "start_prompt": "Kära nån, datorn är trasig.",
            "persona_context": {
                "description": "Problem context.",
                "technical_facts": {}
            },
            "evaluator_context": {
                "solution_keywords": ["wait"]
            }
        }
        
        self.scenario = Scenario(
            name="Test Scenario",
            description="Unit Test",
            target_email="test_bot@movant.org",
            persona_model="mock-model",
            eval_model="mock-model",
            db_manager=self.db_manager,
            problems=[[self.mock_problem]], # Level 1 has 1 problem
            start_phrases=["starta övning"],
            image_warning="IMG WARN",
            persona_prompt="System Prompt",
            evaluator_prompt="Eval Prompt"
        )
        
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
        from email_processor import make_graph_api_call, mark_email_as_read
        from conversation_manager import graph_send_email
        
        # Mock: Graph API returns one 'Starta övning' email
        email = create_mock_email(sender="student1@test.com", body="Starta övning tack.")
        
        # Configure make_graph_api_call to return this email when asked for messages
        def mock_api_side_effect(*args, **kwargs):
            if args[0] == "GET" and "mailFolders/inbox/messages" in args[1]:
                return {"value": [email]}
            return {}
            
        make_graph_api_call.side_effect = mock_api_side_effect

        # --- EXECUTE ---
        graph_check_emails(self.scenario)
        
        # --- VERIFY ---
        # 1. DB should have active problem L1_P001
        def problem_resolver(pid, tid):
            return self.scenario.get_problem_by_id(pid)
            
        history, problem, level_idx, convo_id, metadata = self.db_manager.get_current_active_problem("student1@test.com", problem_resolver)
        
        self.assertIsNotNone(problem, "Active problem should be set")
        self.assertEqual(problem['id'], "L1_P001")
        self.assertEqual(level_idx, 0)
        
        # 2. Should have sent a Welcome Email
        graph_send_email.assert_called()
        call_args = graph_send_email.call_args[0]
        self.assertEqual(call_args[0], "student1@test.com")
        self.assertIn("Kära nån", call_args[2]) # Part of the prompt text for P001

        # 3. Email should be marked as read
        mark_email_as_read.assert_called_with(email['id'], self.scenario.target_email)

    def test_02_student_reply_not_solved(self):
        """
        Scenario: Student is in a problem. Sends a vague/unhelpful reply.
        Expected: Evaluator says [EJ_LÖST]. Persona responds with hint.
        """
        from email_processor import graph_check_emails, make_graph_api_call
        from conversation_manager import graph_send_email
        from llm_client import ollama as mock_ollama

        # 1. Setup State: Active Problem L1_P001
        problem, _ = self.scenario.get_problem_by_id("L1_P001")
        self.db_manager.set_active_problem("student2@test.com", problem, 0, "old_convo_id")
        
        # 2. Mock Input: Student sends generic/vague response
        email = create_mock_email(sender="student2@test.com", body="Vad konstigt. Har du provat att vänta lite?", subject="Re: Uppdatering")
        
        make_graph_api_call.side_effect = lambda method, url, **kwargs: {"value": [email]} if method == "GET" and "messages" in url else {}

        # 3. Mock LLM Responses
        def llm_side_effect(model, messages, **kwargs):
            system_prompt = messages[0]['content']
            if "evaluator_prompt" in str(messages) or "Eval Prompt" in system_prompt: # Check against our mock prompt
                return MockOllamaResponse("[EJ_LÖST]")
            else:
                return MockOllamaResponse("Har du kollat den blå sladden?")
                
        mock_ollama.chat.side_effect = llm_side_effect

        # --- EXECUTE ---
        graph_check_emails(self.scenario)
        
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
        from llm_client import ollama as mock_ollama

        # 1. Setup State: Active Problem L1_P001
        problem, _ = self.scenario.get_problem_by_id("L1_P001")
        self.db_manager.set_active_problem("student3@test.com", problem, 0, "convo_1")
        
        # 2. Mock Input: Correct solution (Instruction to Ulla)
        email = create_mock_email(sender="student3@test.com", body="Du måste köra Windows Update på din dator och sedan starta om den.")
        make_graph_api_call.side_effect = lambda method, url, **kwargs: {"value": [email]} if method == "GET" and "messages" in url else {}

        # 3. Mock LLM: Evaluator says [LÖST]
        def llm_side_effect(model, messages, **kwargs):
            system_prompt = messages[0]['content']
            if "Eval Prompt" in system_prompt:
                return MockOllamaResponse("[LÖST]")
            return MockOllamaResponse("Bra jobbat!") 
        mock_ollama.chat.side_effect = llm_side_effect

        # --- EXECUTE ---
        graph_check_emails(self.scenario)
        
        # --- VERIFY ---
        # 1. Should send success email
        graph_send_email.assert_called()
        
        # 2. User should NO LONGER have an active problem
        def problem_resolver(pid, tid): return self.scenario.get_problem_by_id(pid)
        hist, prob, _, _, _ = self.db_manager.get_current_active_problem("student3@test.com", problem_resolver)
        self.assertIsNone(prob, "Active problem should be cleared after success")

if __name__ == '__main__':
    # manual test runner to ensure we see output
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCoreSimulation)
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
    result = runner.run(suite)
    if not result.wasSuccessful():
        sys.exit(1)
