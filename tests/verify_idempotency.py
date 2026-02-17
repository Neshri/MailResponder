import os
import sys
import tempfile
# --- Path Setup ---
# Add project root to sys.path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import DatabaseManager

def test_idempotency():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_manager = DatabaseManager(tmpdir, "test")
        db_manager.init_dbs()
        
        test_msg_id = "test_message_123"
        
        # Initial state
        print(f"Checking if {test_msg_id} is processed: {db_manager.is_email_processed(test_msg_id)}")
        assert db_manager.is_email_processed(test_msg_id) is False
        
        # Mark as processed
        print(f"Marking {test_msg_id} as processed...")
        db_manager.mark_email_as_processed(test_msg_id)
        
        # Final state
        print(f"Checking if {test_msg_id} is processed: {db_manager.is_email_processed(test_msg_id)}")
        assert db_manager.is_email_processed(test_msg_id) is True
        
        print("Idempotency test passed!")

if __name__ == "__main__":
    test_idempotency()
