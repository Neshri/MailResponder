import datetime
import uuid

def create_mock_email(
    sender="student@example.com", 
    subject="Re: Problem", 
    body="Hello Ulla, I have tried restarting the computer.", 
    received_dt=None
):
    """Generates a Graph API-compatible email dictionary."""
    if received_dt is None:
        received_dt = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
    return {
        "id": str(uuid.uuid4()),
        "internetMessageId": str(uuid.uuid4()),
        "conversationId": str(uuid.uuid4()),
        "receivedDateTime": received_dt,
        "subject": subject,
        "bodyPreview": body[:50],
        "isRead": False,
        "from": {
            "emailAddress": {
                "name": "Student Name",
                "address": sender
            }
        },
        "body": {
            "contentType": "text",
            "content": body
        },
        "internetMessageHeaders": []
    }

class MockOllamaResponse:
    """Simulates an Ollama API response object."""
    def __init__(self, content):
        self.message = {'content': content}
    
    def __getitem__(self, key):
        if key == 'message': return self.message
        raise KeyError(key)

class MockGraphEmail:
    """Helper to create a mock email and convert it to dict for Graph API responses."""
    def __init__(self, sender="student@test.com", subject="Test", body="Body"):
        self.data = create_mock_email(sender=sender, subject=subject, body=body)
    
    def to_dict(self):
        return self.data

class MockGraphResponse:
    """Simulates a Graph API response dictionary."""
    def __init__(self, value_list):
        self.data = {"value": value_list}
    
    def __getitem__(self, key):
        return self.data[key]
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __contains__(self, key):
        return key in self.data
