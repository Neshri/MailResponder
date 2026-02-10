
import sys
import os
import json

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from response_generator import get_persona_reply
from email_parser import get_name_from_email
from unittest.mock import patch, MagicMock

def verify():
    print("--- VERIFYING PROMPT STRUCTURE ---")
    
    student_email = "test@student.com"
    # History includes the initial message with anger level
    full_history_string = "Alex: HÖRRO DU! Jag har väntat i TIO MINUTER...\n\n[Ilskenivå: 100]\n\nStudent: Hej Alex, jag ska hjälpa dig."
    persona_context = {
        "description": "Kunden är rasande för att ingenting fungerar.",
        "current_anger_level_tag": "[Ilskenivå: 100]"
    }
    latest_student_message = "Hej Alex, jag ska hjälpa dig."
    problem_level_idx = 0
    evaluator_decision_marker = "[EJ_LÖST]"
    system_prompt = "Du är Arga Alex..."
    
    with patch('response_generator.chat_with_model') as mock_chat, \
         patch('response_generator.PERSONA_MODEL', 'mock-model'):
        mock_chat.return_value = "VA?! Äntligen svarar nån!"
        
        get_persona_reply(
            student_email,
            full_history_string,
            persona_context,
            latest_student_message,
            problem_level_idx,
            evaluator_decision_marker,
            system_prompt=system_prompt
        )
        
        # Check what was sent to LLM
        args, kwargs = mock_chat.call_args
        messages = kwargs.get('messages')
        
        system_message = messages[0]['content']
        user_message = messages[1]['content']
        
        print("\n--- GENERATED SYSTEM PROMPT ---")
        print(system_message)
        print("--- GENERATED USER PROMPT ---")
        print(user_message)
        print("--- END OF PROMPTS ---\n")
        
        # Assertions for Arga Alex
        assert "DIN NUVARANDE SINNESSTÄMNING: [Ilskenivå: 100]" in system_message
        assert "**DIN KONTEXT & VERKLIGHET:**" in user_message
        assert "**DITT NUVARANDE TILLSTÅND:**" not in user_message # Should be in system now
        
        # Order check for user prompt
        history_pos = user_message.find("**Hittillsvarande Konversation:**")
        context_pos = user_message.find("**DIN KONTEXT & VERKLIGHET:**")
        message_pos = user_message.find(f"**{get_name_from_email(student_email)}s Senaste Meddelande till dig:**")
        task_pos = user_message.find("**Din Uppgift:**")
        
        assert history_pos < context_pos < message_pos < task_pos
        print("Success: Arga Alex prompt structure followed.")

    print("\n--- VERIFYING TAG STRIPPING (HALLUCINATION PREVENTION) ---")
    with patch('response_generator.chat_with_model') as mock_chat, \
         patch('response_generator.PERSONA_MODEL', 'mock-model'):
        # Mock returns a response with a hallucinated tag
        mock_chat.return_value = "Okej Anna, jag fattar. [Ilskenivå: 115]"
        
        reply = get_persona_reply(
            student_email,
            full_history_string,
            persona_context,
            latest_student_message,
            0,
            "[EJ_LÖST]",
            system_prompt="Du är Alex"
        )
        
        print(f"Raw reply: 'Okej Anna, jag fattar. [Ilskenivå: 115]'")
        print(f"Cleaned reply: '{reply}'")
        assert "[Ilskenivå: 115]" not in reply
        assert "Okej Anna, jag fattar." in reply
        print("Success: Hallucinated tags are stripped.")

    print("\n--- VERIFYING ULLA (NO ANGER LEVEL) ---")
    persona_context_ulla = {
        "description": "Ulla är en hjälpsam tant.",
        "technical_facts": {"kaka": "god"}
    }
    
    with patch('response_generator.chat_with_model') as mock_chat, \
         patch('response_generator.PERSONA_MODEL', 'mock-model'):
        mock_chat.return_value = "Vill du ha en kaka?"
        
        get_persona_reply(
            student_email,
            full_history_string,
            persona_context_ulla,
            latest_student_message,
            problem_level_idx,
            evaluator_decision_marker,
            system_prompt="Du är Ulla..."
        )
        
        args, kwargs = mock_chat.call_args
        user_message = kwargs.get('messages')[1]['content']
        
        print("\n--- GENERATED ULLA PROMPT ---")
        print(user_message)
        print("--- END OF PROMPT ---\n")
        
        assert "**DITT NUVARANDE TILLSTÅND:**" not in user_message
        assert "[Ilskenivå: Okänd]" not in user_message
        print("Success: Ulla prompt does not contain anger level information.")

if __name__ == "__main__":
    verify()
