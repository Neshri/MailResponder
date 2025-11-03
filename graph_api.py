import requests
import msal
import time
import logging
import base64
import json
from config import (
    AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET, TARGET_USER_GRAPH_ID,
    GRAPH_API_ENDPOINT, GRAPH_SCOPES, MSAL_AUTHORITY
)

# Global variables for MSAL and token
MSAL_APP = None
ACCESS_TOKEN = None

# --- Graph API Helper Functions ---
def get_graph_token():
    global MSAL_APP, ACCESS_TOKEN
    if MSAL_APP is None: MSAL_APP = msal.ConfidentialClientApplication(AZURE_CLIENT_ID, authority=MSAL_AUTHORITY, client_credential=AZURE_CLIENT_SECRET)
    token_result = MSAL_APP.acquire_token_silent(GRAPH_SCOPES, account=None)
    if not token_result: logging.info("Hämtar nytt Graph API-token."); token_result = MSAL_APP.acquire_token_for_client(scopes=GRAPH_SCOPES)
    if "access_token" in token_result: ACCESS_TOKEN = token_result['access_token']; return ACCESS_TOKEN
    logging.error(f"Misslyckades hämta Graph token: {token_result.get('error_description')}"); ACCESS_TOKEN = None; return None

def jwt_is_expired(token_str):
    if not token_str: return True;
    try: payload_str = token_str.split('.')[1]; payload_str += '=' * (-len(payload_str) % 4); payload = json.loads(base64.urlsafe_b64decode(payload_str).decode()); return payload.get('exp', 0) < time.time()
    except Exception: return True

def make_graph_api_call(method, endpoint_or_url, data=None, params=None, headers_extra=None):
    global ACCESS_TOKEN
    if ACCESS_TOKEN is None or jwt_is_expired(ACCESS_TOKEN):
        logging.info("Token saknas/utgånget i make_graph_api_call, försöker förnya.")
        if not get_graph_token(): logging.error("Misslyckades förnya token."); return None
    if ACCESS_TOKEN is None: logging.error("ACCESS_TOKEN fortfarande None."); return None

    headers = {'Authorization': 'Bearer ' + ACCESS_TOKEN, 'Content-Type': 'application/json'}
    if headers_extra: headers.update(headers_extra)

    if endpoint_or_url.startswith("https://") or endpoint_or_url.startswith("http://"):
        url = endpoint_or_url
    else:
        url = f"{GRAPH_API_ENDPOINT}{endpoint_or_url}"

    try:
        response = requests.request(method, url, headers=headers, json=data, params=params, timeout=30)
        response.raise_for_status()
        if response.status_code in [202, 204]: return True
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401: logging.warning("Graph API 401. Ogiltigförklarar token."); ACCESS_TOKEN = None
        err_details = "Okänt."
        try: err_details = e.response.json().get("error", {}).get("message", e.response.text)
        except json.JSONDecodeError: err_details = e.response.text
        logging.error(f"Graph HTTP-fel: {e.response.status_code} - {err_details} ({method} {url})"); return None
    except requests.exceptions.RequestException as e: logging.error(f"Graph anropsfel: {e} ({method} {url})", exc_info=True); return None

# --- Graph API Email Functions ---
def graph_send_email(recipient_email, subject, body_content, in_reply_to_message_id=None, references_header_str=None, conversation_id=None):
    message_payload = {"message": {"subject": subject, "body": {"contentType": "Text", "content": body_content}, "toRecipients": [{"emailAddress": {"address": recipient_email}}]}, "saveToSentItems": "true"}
    headers_list = []
    if in_reply_to_message_id: headers_list.append({"name": "X-In-Reply-To", "value": in_reply_to_message_id})
    if references_header_str: headers_list.append({"name": "X-References", "value": references_header_str})
    if conversation_id: message_payload["message"]["conversationId"] = conversation_id
    if headers_list: message_payload["message"]["internetMessageHeaders"] = headers_list
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/sendMail"
    logging.info(f"Skickar e-post till: {recipient_email} | Ämne: {subject}")
    response = make_graph_api_call("POST", endpoint, data=message_payload)
    if response is True: logging.info("E-post skickat."); return True
    logging.error(f"Misslyckades skicka e-post. Svar: {response}"); return False

def mark_email_as_read(graph_message_id):
    endpoint = f"/users/{TARGET_USER_GRAPH_ID}/messages/{graph_message_id}"; payload = {"isRead": True}
    if make_graph_api_call("PATCH", endpoint, data=payload): logging.info(f"E-post {graph_message_id} markerad som läst.")
    else: logging.error(f"Misslyckades markera {graph_message_id} som läst.")

def graph_delete_all_emails_in_inbox(user_principal_name_or_id=TARGET_USER_GRAPH_ID):
    logging.info(f"Attempting to delete all emails in inbox for {user_principal_name_or_id}...")
    global ACCESS_TOKEN
    if ACCESS_TOKEN is None or jwt_is_expired(ACCESS_TOKEN):
        logging.info("Token for delete operation missing/expired, attempting to refresh.")
        if not get_graph_token():
            logging.error("Failed to refresh token. Cannot proceed with email deletion.")
            return False

    all_message_ids = []
    current_request_url = f"/users/{user_principal_name_or_id}/mailFolders/inbox/messages?$select=id&$top=100"

    logging.info("Fetching message IDs from inbox...")
    page_count = 0
    while current_request_url:
        page_count += 1
        logging.debug(f"Fetching page {page_count} of messages using URL: {current_request_url}")
        response = make_graph_api_call("GET", current_request_url)

        if not response or "value" not in response:
            if response is None:
                  logging.error(f"Failed to fetch messages (page {page_count}). Aborting further fetching.")
            else:
                  logging.info(f"No 'value' in response or empty message list on page {page_count}. Assuming no more messages.")
            break

        messages_page = response.get("value", [])
        if not messages_page and page_count == 1 and not all_message_ids:
              logging.info("Inbox is empty or no messages retrieved on the first page.")
              return True

        for msg in messages_page:
            if msg.get("id"):
                all_message_ids.append(msg["id"])

        current_request_url = response.get("@odata.nextLink")
        if current_request_url:
            logging.info(f"Fetching next page of messages... ({len(all_message_ids)} IDs collected so far)")
        else:
            logging.info(f"All message pages fetched. Total messages to delete: {len(all_message_ids)}")
            break

    if not all_message_ids:
        logging.info("No messages found in the inbox to delete.")
        return True

    logging.info(f"Proceeding to delete {len(all_message_ids)} messages...")
    deleted_count = 0
    failed_count = 0

    for i, msg_id in enumerate(all_message_ids):
        delete_endpoint_suffix = f"/users/{user_principal_name_or_id}/messages/{msg_id}"
        if make_graph_api_call("DELETE", delete_endpoint_suffix):
            logging.debug(f"Successfully deleted message ID: {msg_id}")
            deleted_count += 1
        else:
            logging.error(f"Failed to delete message ID: {msg_id}")
            failed_count += 1

        if (i + 1) % 50 == 0 or (i + 1) == len(all_message_ids):
            logging.info(f"Deletion progress: {deleted_count} deleted, {failed_count} failed. ({i + 1}/{len(all_message_ids)} processed)")

    logging.info(f"Email deletion process completed. Successfully deleted: {deleted_count}, Failed to delete: {failed_count}.")
    return failed_count == 0