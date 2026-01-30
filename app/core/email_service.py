from datetime import datetime
from sqlalchemy.orm import Session
from app.models.email import Email
from app.ai.classifier import classify_email


def create_email(
    db: Session,
    *,
    user_id: int,
    gmail_message_id: str,
    sender: str,
    body: str,
    received_at=None,
):
    ai = classify_email(body)

    email = Email(
        user_id=user_id,
        gmail_message_id=gmail_message_id,
        email=sender,
        body=body,
        email_type=ai["email_type"],
        ai_email_type=ai["email_type"],
        confidence_score=ai["confidence"],
        ai_reason=ai["reason"],
        model_version=ai["model_version"],
        is_ai_generated=True,
        needs_review=ai["confidence"] < 0.8,
        received_at=received_at or datetime.utcnow(),
        is_active=True,
    )

    db.add(email)
    db.commit()
    db.refresh(email)

    return email
