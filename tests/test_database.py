import unittest
import os
import sqlite3
import shutil
import tempfile
import sys

# --- Path Setup ---
# Add project root to sys.path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DatabaseManager

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # 1. Setup Temporary Directory for DBs
        self.test_dir = tempfile.mkdtemp()
        
        # 2. Initialize fresh DBs via DatabaseManager
        self.db_manager = DatabaseManager(self.test_dir, db_prefix="test")
        self.db_manager.init_dbs()
        
        self.email = "test_student@example.com"

    def tearDown(self):
        # Cleanup
        shutil.rmtree(self.test_dir)

    def test_01_initial_progress(self):
        """Verify that a brand new student starts with defaults."""
        level, convo_id, track_id = self.db_manager.get_student_progress(self.email)
        self.assertEqual(level, 0)
        self.assertIsNone(convo_id)
        self.assertEqual(track_id, "ulla_classic")

    def test_02_track_switching(self):
        """Verify that switching tracks resets level and updates state."""
        # Advances in classic first
        self.db_manager.update_student_level(self.email, 2)
        
        # Switch to evil
        success = self.db_manager.set_student_track(self.email, "evil_persona")
        self.assertTrue(success)
        
        level, _, track_id = self.db_manager.get_student_progress(self.email)
        self.assertEqual(level, 0, "Level should reset to 0 on track switch")
        self.assertEqual(track_id, "evil_persona")

    def test_03_active_problem_persistence(self):
        """Verify that active problems are correctly stored and retrieved."""
        problem = {
            "id": "L1_P001",
            "start_prompt": "Hello",
            "beskrivning": "Test problem"
        }
        self.db_manager.set_student_track(self.email, "ulla_classic")
        metadata = {"test_key": "test_val"}
        self.db_manager.set_active_problem(self.email, problem, 0, "convo_123", track_metadata=metadata)
        
        # Mock resolver callback
        def mock_resolver(pid, tid):
            if pid == "L1_P001":
                return problem, 0
            return None, -1

        history, p_info, level_idx, convo_id, ret_metadata = self.db_manager.get_current_active_problem(self.email, mock_resolver)
        self.assertIsNotNone(p_info)
        self.assertEqual(p_info["id"], "L1_P001")
        self.assertEqual(convo_id, "convo_123")
        self.assertEqual(level_idx, 0)
        self.assertEqual(ret_metadata["test_key"], "test_val")

    def test_04_metadata_update(self):
        """Verify that track_metadata can be updated independently."""
        problem = {"id": "L1_P001", "start_prompt": "Hello", "beskrivning": "Test"}
        self.db_manager.set_active_problem(self.email, problem, 0, "c1")
        
        new_meta = {"anger": 50}
        self.db_manager.update_active_problem_metadata(self.email, new_meta)
        
        # Mock resolver callback
        def mock_resolver(pid, tid): return problem, 0
        
        _, _, _, _, meta = self.db_manager.get_current_active_problem(self.email, mock_resolver)
        self.assertEqual(meta["anger"], 50)

    def test_05_update_level_safety(self):
        """Verify that update_student_level doesn't break if record is missing."""
        email2 = "new_student@example.com"
        success = self.db_manager.update_student_level(email2, 1)
        self.assertTrue(success)
        
        level, _, track_id = self.db_manager.get_student_progress(email2)
        self.assertEqual(level, 1)
        self.assertEqual(track_id, "ulla_classic")

    def test_06_history_append(self):
        """Verify that history can be appended to."""
        problem = {"id": "L1_P001", "start_prompt": "Hello", "beskrivning": "Test"}
        self.db_manager.set_active_problem(self.email, problem, 0, "c1")
        
        self.db_manager.append_to_active_problem_history(self.email, "Student: Help!")
        
        # Mock resolver callback
        def mock_resolver(pid, tid): return problem, 0
        
        history, _, _, _, _ = self.db_manager.get_current_active_problem(self.email, mock_resolver)
        self.assertIn("Student: Help!", history)

if __name__ == "__main__":
    unittest.main()
