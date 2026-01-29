import os
import json
import sqlite3
import datetime
import sys

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager

def test_debug_logging():
    db_dir = "test_dbs"
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    db_prefix = "test"
    db_manager = DatabaseManager(db_dir=db_dir, db_prefix=db_prefix)
    db_manager.init_dbs()
    
    student_email = "tester@example.com"
    problem_id = "L1_P001"
    
    print("Testing set_active_problem...")
    problem = {"id": problem_id, "start_prompt": "Hello"}
    db_manager.set_active_problem(student_email, problem, 0, "convo_123")
    
    print("Testing add_debug_evaluator_response...")
    responses = ["Decision 1: Needs more info", "Decision 2: Correct! [LÖST]"]
    
    for resp in responses:
        db_manager.add_debug_evaluator_response(student_email, problem_id, resp)
        
    print("Verifying database contents...")
    with db_manager.get_connection(db_manager.debug_db_file) as conn:
        cursor = conn.execute("SELECT evaluator_responses FROM debug_conversations WHERE student_email = ? AND problem_id = ?", (student_email, problem_id))
        row = cursor.fetchone()
        
        if not row:
            print("FAILED: No record found in debug_conversations")
            return False
            
        stored_responses = json.loads(row['evaluator_responses'])
        print(f"Found {len(stored_responses)} stored responses.")
        
        if len(stored_responses) != 2:
            print(f"FAILED: Expected 2 responses, found {len(stored_responses)}")
            return False
            
        for i, resp in enumerate(stored_responses):
            print(f"  Response {i+1}: {resp['timestamp']} - {resp['response']}")
            if resp['response'] != responses[i]:
                print(f"FAILED: Response mismatch! Expected '{responses[i]}', found '{resp['response']}'")
                return False
                
    print("SUCCESS: Debug logging verified!")
    return True

if __name__ == "__main__":
    success = test_debug_logging()
    if not success:
        sys.exit(1)
