import base64
from typing import Dict


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
            received_at = h["value"]

    body = ""

    if "body" in payload and payload["body"].get("data"):
        body = _decode_base64(payload["body"]["data"])

    elif "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                body = _decode_base64(part["body"].get("data", ""))
                break

    return {
        "subject": subject,
        "sender": sender,
        "body": body,
        "received_at": received_at
    }
