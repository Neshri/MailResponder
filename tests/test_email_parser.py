import unittest
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_parser import clean_email_body, get_name_from_email, extract_student_message_from_reply

class TestEmailParser(unittest.TestCase):

    def test_clean_email_body_outlook(self):
        body = "Hello Alex!\n\n________________________________\nFrom: Student <student@test.com>\nSent: Tuesday..."
        cleaned = clean_email_body(body)
        self.assertEqual(cleaned, "Hello Alex!")

    def test_clean_email_body_gmail(self):
        body = "I fixed the issue.\n\nOn Tue, Feb 17, 2026 at 4:30 PM Alex <alex@test.com> wrote:\n> Hello..."
        cleaned = clean_email_body(body)
        self.assertEqual(cleaned, "I fixed the issue.")

    def test_clean_email_body_fallback(self):
        body = "This is my reply.\n\n> Quoted line 1\n> Quoted line 2"
        cleaned = clean_email_body(body)
        self.assertEqual(cleaned, "This is my reply.")

    def test_get_name_from_email(self):
        self.assertEqual(get_name_from_email("anton.svensson@gmail.com"), "Anton")
        self.assertEqual(get_name_from_email("ALEX_TEST@example.org"), "Alex")
        self.assertEqual(get_name_from_email("unknown"), "Unknown")
        self.assertEqual(get_name_from_email(""), "Support")

    def test_extract_student_message_reply_marker_date(self):
        full_body = "This is the new text.\nDen 17 feb 2026 skrev Alex <alex@test.com>:\n> Old text"
        extracted = extract_student_message_from_reply(full_body)
        self.assertEqual(extracted, "This is the new text.")

    def test_extract_student_message_reply_marker_email(self):
        full_body = "New message content.\n\nalex@test.com skrev:\n> Previous content"
        extracted = extract_student_message_from_reply(full_body, persona_email="alex@test.com")
        self.assertEqual(extracted, "New message content.")

    def test_extract_student_message_no_marker(self):
        full_body = "Just a single message."
        extracted = extract_student_message_from_reply(full_body)
        self.assertEqual(extracted, "Just a single message.")

if __name__ == "__main__":
    unittest.main()
