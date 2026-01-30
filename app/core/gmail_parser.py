from typing import Dict
import base64
from datetime import datetime
from email.utils import parsedate_to_datetime


def _decode_base64(data: str) -> str:
    if not data:
        return ""
    decoded_bytes = base64.urlsafe_b64decode(data + "===")
    return decoded_bytes.decode("utf-8", errors="ignore")


def parse_message(message: Dict) -> Dict:
    payload = message.get("payload", {})
    headers = payload.get("headers", [])

    subject = ""
    sender = ""
    received_at = None

    for h in headers:
        if h["name"] == "Subject":
            subject = h["value"]
        elif h["name"] == "From":
            sender = h["value"]
        elif h["name"] == "Date":
            try:
                received_at = parsedate_to_datetime(h["value"])
            except Exception:
                received_at = None

    body = ""

    if payload.get("body", {}).get("data"):
        body = _decode_base64(payload["body"]["data"])

    elif payload.get("parts"):
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                body = _decode_base64(part["body"].get("data", ""))
                break

    return {
        "gmail_message_id": message.get("id"),
        "subject": subject,
        "sender": sender,
        "body": body,
        "snippet": message.get("snippet", ""),
        "received_at": received_at, 
    }
