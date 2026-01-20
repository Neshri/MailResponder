import unittest
import os
import sqlite3
import sys
# --- Path Setup ---
# Add project root to sys.path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database
from config import DB_FILE, COMPLETED_DB_FILE, DEBUG_DB_FILE

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Use a fresh set of test databases
        for db in [DB_FILE, COMPLETED_DB_FILE, DEBUG_DB_FILE]:
            if os.path.exists(db):
                os.remove(db)
        database.init_db()
        database.init_completed_db()
        database.init_debug_db()
        self.email = "test_student@example.com"

    def tearDown(self):
        # Cleanup
        for db in [DB_FILE, COMPLETED_DB_FILE, DEBUG_DB_FILE]:
            if os.path.exists(db):
                os.remove(db)

    def test_01_initial_progress(self):
        """Verify that a brand new student starts with defaults."""
        level, convo_id, track_id = database.get_student_progress(self.email)
        self.assertEqual(level, 0)
        self.assertIsNone(convo_id)
        self.assertEqual(track_id, "ulla_classic")

    def test_02_track_switching(self):
        """Verify that switching tracks resets level and updates state."""
        # Advances in classic first
        database.update_student_level(self.email, 2)
        
        # Switch to evil
        success = database.set_student_track(self.email, "evil_persona")
        self.assertTrue(success)
        
        level, _, track_id = database.get_student_progress(self.email)
        self.assertEqual(level, 0, "Level should reset to 0 on track switch")
        self.assertEqual(track_id, "evil_persona")

    def test_03_active_problem_persistence(self):
        """Verify that active problems are correctly stored and retrieved per track."""
        problem = {
            "id": "L1_P001",
            "start_prompt": "Hello",
            "beskrivning": "Test problem"
        }
        database.set_student_track(self.email, "ulla_classic")
        metadata = {"test_key": "test_val"}
        database.set_active_problem(self.email, problem, 0, "convo_123", track_metadata=metadata)
        
        history, p_info, level_idx, convo_id, ret_metadata = database.get_current_active_problem(self.email)
        self.assertEqual(p_info["id"], "L1_P001")
        self.assertEqual(convo_id, "convo_123")
        self.assertEqual(level_idx, 0)
        self.assertEqual(ret_metadata["test_key"], "test_val")

    def test_06_metadata_update(self):
        """Verify that track_metadata can be updated independently."""
        problem = {"id": "L1_P001", "start_prompt": "Hello", "beskrivning": "Test"}
        database.set_active_problem(self.email, problem, 0, "c1")
        
        new_meta = {"anger": 50}
        database.update_active_problem_metadata(self.email, new_meta)
        
        _, _, _, _, meta = database.get_current_active_problem(self.email)
        self.assertEqual(meta["anger"], 50)

    def test_04_track_isolation(self):
        """Ensure that find_problem_by_id respects track catalogs."""
        # Find in Ulla
        p_ulla, _ = database.find_problem_by_id("L1_P001", "ulla_classic")
        self.assertIsNotNone(p_ulla)
        
        # Should NOT find Ulla problem in Evil track
        p_evil, _ = database.find_problem_by_id("L1_P001", "evil_persona")
        self.assertIsNone(p_evil)

    def test_05_update_level_safety(self):
        """Verify that update_student_level doesn't break if record is missing."""
        email2 = "new_student@example.com"
        success = database.update_student_level(email2, 1)
        self.assertTrue(success)
        
        level, _, track_id = database.get_student_progress(email2)
        self.assertEqual(level, 1)
        self.assertEqual(track_id, "ulla_classic")

if __name__ == "__main__":
    unittest.main()
