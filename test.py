# Save this file as debug_matcher.py

import logging
import re
from prompts import PROBLEM_CATALOGUES

# --- Setup basic logging to see the output ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- SIMULATE THE INPUTS ---

# This is the student's message that was failing.
# We use a literal string to ensure it's exactly what we expect.
student_message = "Vad har du för grafikkort?"

# This is the specific problem being tested (L5_P010)
problem_id_to_test = "L5_P010"

# --- THE CORE LOGIC FROM THE APPLICATION, ISOLATED FOR TESTING ---

def test_keyword_matching(problem_id, message):
    """
    This function isolates the keyword matching logic to test it directly.
    """
    # Find the correct problem from the imported catalogue
    problem_to_test = None
    for level in PROBLEM_CATALOGUES:
        for problem in level:
            if problem['id'] == problem_id:
                problem_to_test = problem
                break
        if problem_to_test:
            break

    if not problem_to_test:
        logging.error(f"Could not find problem with ID: {problem_id}")
        return

    technical_facts_dict = problem_to_test.get('tekniska_fakta', {})
    if not technical_facts_dict:
        logging.error(f"Problem {problem_id} has no 'tekniska_fakta' dictionary.")
        return

    student_message_lower = message.lower()
    found_match = False

    logging.info(f"--- STARTING TEST ---")
    logging.info(f"Student Message: '{message}'")
    logging.info(f"Lowercased Message: '{student_message_lower}'")
    logging.info(f"repr() of Lowercased Message: {repr(student_message_lower)}")
    print("-" * 20)

    for keyword, fact in technical_facts_dict.items():
        keyword_lower = keyword.lower()
        
        # --- TEST 1: The original 'in' operator ---
        match_in = keyword_lower in student_message_lower
        logging.info(f"[Test 'in']      Keyword: '{keyword_lower}' (repr: {repr(keyword_lower)}) -> Match: {match_in}")

        # --- TEST 2: The more robust 're.search' operator ---
        # The regex r'\b' denotes a word boundary.
        match_re = bool(re.search(r'\b' + re.escape(keyword_lower) + r'\b', student_message_lower))
        logging.info(f"[Test 're.search'] Keyword: '{keyword_lower}' (repr: {repr(keyword_lower)}) -> Match: {match_re}")
        
        print("-" * 20)

        if match_re: # Let's use the better method for the final verdict
            found_match = True

    logging.info(f"--- TEST COMPLETE ---")
    if found_match:
        logging.info("VERDICT: A keyword was successfully matched.")
    else:
        logging.error("VERDICT: FAILED to match any keyword.")


# --- RUN THE TEST ---
if __name__ == "__main__":
    test_keyword_matching(problem_id_to_test, student_message)