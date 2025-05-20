# ... (other imports and functions) ...
import sqlite3
import json
import logging

def print_all_active_conversations():
    """Prints all records from the active_conversations table for debugging."""
    conn = None
    logging.info("--- UTSKRIFT AV DATABASINNEHÅLL (active_conversations) ---")
    try:
        conn = sqlite3.connect("conversations.db")
        conn.row_factory = sqlite3.Row # To access columns by name
        cursor = conn.cursor()
        
        cursor.execute("SELECT student_email, problem_id, problem_description, correct_solution_keywords, conversation_history, created_at, last_update, graph_conversation_id FROM active_conversations")
        rows = cursor.fetchall()
        
        if not rows:
            print("Databasen (active_conversations) är tom.")
            logging.info("Databasen (active_conversations) är tom.")
            return

        for i, row in enumerate(rows):
            print(f"\n--- Post {i+1} ---")
            print(f"Student Email: {row['student_email']}")
            print(f"Problem ID: {row['problem_id']}")
            print(f"Problem Description: {row['problem_description']}")
            try:
                # Keywords are stored as a JSON string, try to parse for pretty print
                keywords = json.loads(row['correct_solution_keywords'])
                print(f"Correct Solution Keywords: {keywords}")
            except json.JSONDecodeError:
                print(f"Correct Solution Keywords (raw): {row['correct_solution_keywords']}")
            print(f"Graph Conversation ID: {row['graph_conversation_id']}")
            print(f"Created At: {row['created_at']}")
            print(f"Last Update: {row['last_update']}")
            print(f"Conversation History (string):\n{'-'*20}\n{row['conversation_history']}\n{'-'*20}")
        
        logging.info(f"Skrev ut {len(rows)} poster från active_conversations.")

    except sqlite3.Error as e:
        print(f"Databasfel vid utskrift: {e}")
        logging.error(f"Databasfel vid utskrift av active_conversations: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
        logging.info("--- SLUT UTSKRIFT AV DATABASINNEHÅLL ---")

# ... (rest of your script) ...

print_all_active_conversations()