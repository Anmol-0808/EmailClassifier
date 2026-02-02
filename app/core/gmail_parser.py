from typing import Dict, List
import base64
from datetime import datetime
from email.utils import parsedate_to_datetime


def _decode_base64(data: str) -> str:
    """
    Safely decode Gmail base64url encoded strings.
    """
    if not data:
        return ""
    try:
        padded = data + "=" * (-len(data) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded)
        return decoded_bytes.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_body(payload: Dict) -> str:
    """
    Extracts text/plain body from Gmail payload.
    Falls back gracefully if structure varies.
    """
   
    if payload.get("body", {}).get("data"):
        return _decode_base64(payload["body"]["data"])

    
    for part in payload.get("parts", []):
        mime_type = part.get("mimeType", "")

        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            return _decode_base64(part["body"]["data"])

        
        if part.get("parts"):
            body = _extract_body(part)
            if body:
                return body

    return ""


def parse_message(message: Dict) -> Dict:
    """
    Parse a raw Gmail message JSON into a normalized structure
    while preserving labels for correct Inbox filtering.
    """
    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    subject = ""
    sender = ""
    received_at: datetime | None = None

    for header in headers:
        name = header.get("name", "")
        value = header.get("value", "")

        if name == "Subject":
            subject = value
        elif name == "From":
            sender = value
        elif name == "Date":
            try:
                received_at = parsedate_to_datetime(value)
            except Exception:
                received_at = None

    body = _extract_body(payload)

    return {
        "gmail_message_id": message.get("id"),
        "thread_id": message.get("threadId"),
        "labels": message.get("labelIds", []),  
        "subject": subject,
        "sender": sender,
        "body": body,
        "snippet": message.get("snippet", ""),
        "received_at": received_at,
    }
