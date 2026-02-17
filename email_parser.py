import re
import logging
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
from config import TARGET_USER_GRAPH_ID

def clean_email_body(body_text, original_sender_email_for_attribution=None):
    """
    Cleans the body of an email by finding the most likely reply header and truncating the message there.
    It checks for multiple common formats in a specific order of reliability.
    """
    if not body_text:
        return ""

    # 1. The Outlook/Exchange Header (very reliable)
    # This looks for the horizontal line <hr> often used by Outlook, OR
    # a line starting with "From:" or "Från:" which indicates the start of a metadata block.
    # We split the text at this point and take what's before it.
    outlook_split_patterns = [
        re.compile(r'________________________________', re.IGNORECASE),
        re.compile(r'^from:\s*.*', re.IGNORECASE | re.MULTILINE),
        re.compile(r'^från:\s*.*', re.IGNORECASE | re.MULTILINE)
    ]
    for pattern in outlook_split_patterns:
        match = pattern.search(body_text)
        if match:
            cleaned_text = body_text[:match.start()].strip()
            logging.info("Outlook-style reply header found and stripped.")
            return cleaned_text

    # 2. The Gmail/Apple Mail "On [date], [sender] wrote:" Header (very reliable)
    # UPDATED: 
    # - Uses re.DOTALL to handle headers split across multiple lines.
    # - SAFETY: Requires a digit (\d+) to exist (prevents matching text like "Den filen du skrev:").
    # - Matches content between the verb "skrev" and the final colon.
    gmail_style_pattern = re.compile(
        r"^(on|den|le|am)\s+"                # Start of a line with "Den", "On", etc.
        r".*?\d+"                            # <--- THIS IS CRITICAL: Must find a number (date)
        r".*?"                               # Content between date and verb
        r"\b(wrote|skrev|a écrit|schrieb)\b" # The verb (whole word only)
        r".*?:\s*$",                         # Match the sender name/email until the final colon
        re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    match = gmail_style_pattern.search(body_text)
    if match:
        cleaned_text = body_text[:match.start()].strip()
        logging.info("Gmail/Apple Mail-style reply header found and stripped.")
        return cleaned_text

    # 3. The "---- Original Message ----" Header (less common but reliable)
    original_message_pattern = re.compile(r'---- original message ----', re.IGNORECASE)
    match = original_message_pattern.search(body_text)
    if match:
        cleaned_text = body_text[:match.start()].strip()
        logging.info("'Original Message'-style reply header found and stripped.")
        return cleaned_text

    # 4. Fallback: Line-by-line check for ">" (least reliable, used as a last resort)
    # If no headers were found, we assume it's a simple plain-text reply.
    # We will only strip from the *bottom up* to avoid cutting inline quotes.
    lines = body_text.splitlines()
    last_unquoted_line_index = -1
    for i in range(len(lines) - 1, -1, -1):
        if not lines[i].strip().startswith('>'):
            last_unquoted_line_index = i
            break

    if last_unquoted_line_index != -1:
        # Join only the lines up to the last unquoted one.
        cleaned_lines = lines[:last_unquoted_line_index + 1]
        fallback_text = "\n".join(cleaned_lines).strip()
    else:
        # This happens if the ENTIRE message is quoted. We return an empty string.
        fallback_text = ""

    # Only log if we actually changed something.
    if len(fallback_text) < len(body_text):
        logging.info("No reliable header found; performed fallback cleaning of '>' characters from the end of the message.")

    return fallback_text

def get_name_from_email(email):
    """Extracts a capitalized first name from an email address."""
    try:
        name_part = email.split('@')[0]
        # Replace dots or other common separators with a space
        name_part = name_part.replace('.', ' ').replace('_', ' ')
        first_name = name_part.split(' ')[0]
        if not first_name:
            return "Support"
        return first_name.capitalize()
    except Exception:
        return "Support" # Fallback to the old label if anything goes wrong

def parse_graph_email_item(msg_graph_item):
    email_data = {
        "graph_msg_id": msg_graph_item.get('id'),
        "subject": msg_graph_item.get('subject', ""),
        "sender_email": "",
        "internet_message_id": msg_graph_item.get('internetMessageId'),
        "graph_conversation_id_incoming": msg_graph_item.get('conversationId'),
        "references_header_value": None,
        "cleaned_body": "",
        "body_preview": msg_graph_item.get('bodyPreview', ""),
        "received_datetime": msg_graph_item.get('receivedDateTime', "")
    }
    
    sender_info = msg_graph_item.get('from') or msg_graph_item.get('sender')
    if sender_info and sender_info.get('emailAddress'):
        email_data["sender_email"] = sender_info['emailAddress'].get('address', '').lower()
        
    for header in msg_graph_item.get('internetMessageHeaders', []):
        if header.get('name', '').lower() == 'references':
            email_data["references_header_value"] = header.get('value')
            break
            
    body_obj = msg_graph_item.get('body', {})
    body_content = body_obj.get('content', '')
    
    if body_obj.get('contentType','').lower()=='html' and BeautifulSoup:
        raw_body = BeautifulSoup(body_content, "html.parser").get_text(separator='\n').strip()
    else:
        raw_body = body_content
        
    email_data["cleaned_body"] = clean_email_body(raw_body, TARGET_USER_GRAPH_ID)

    # Detect images (including inline and attachments)
    has_images = msg_graph_item.get('hasAttachments', False)
    
    if not has_images:
        attachments = msg_graph_item.get('attachments', [])
        for att in attachments:
            if att.get('contentType', '').startswith('image/'):
                has_images = True
                break
                
    if not has_images and body_obj.get('contentType','').lower()=='html' and BeautifulSoup:
        soup = BeautifulSoup(body_content, "html.parser")
        # Check for <img> tags or cid: references which indicate inline images
        if soup.find('img') or 'src="cid:' in body_content:
            has_images = True
    email_data["has_images"] = has_images

    logging.debug(f"Parsed email: ID={email_data['graph_msg_id']}, From={email_data['sender_email']}, Time={email_data['received_datetime']}")
    return email_data

def extract_student_message_from_reply(full_body, active_hist_str=None, persona_email=None):
    """
    Extracts only the new student message content from a reply email, excluding quoted replies.
    """
    if not full_body.strip():
        return ""

    # Look for the pattern where previous persona messages start (usually with date headers)
    lines = full_body.split('\n')
    extracted_content = []
    found_reply_marker = False

    persona_email_pattern = persona_email.lower() if persona_email else None

    for line in lines:
        line_lower = line.strip().lower()
        # Look for date headers that indicate start of quoted content
        if re.search(r'^\s*(den|on)\s+\d{1,2}\s+\w{3}\s+\d{4}', line_lower) or \
           re.search(r'^\s*\d{4}-\d{2}-\d{2}', line) or \
           re.search(r'^\s*\w{3}\s+\d{1,2}', line) or \
           (persona_email_pattern and persona_email_pattern in line_lower and 'skrev:' in line_lower):
            found_reply_marker = True
            break
        extracted_content.append(line)

    if found_reply_marker and extracted_content:
        body_for_llm_task = '\n'.join(extracted_content).strip()
    else:
        body_for_llm_task = full_body.strip()

    return body_for_llm_task