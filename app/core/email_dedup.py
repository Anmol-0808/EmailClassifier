from sqlalchemy.orm import Session
from app.models.email import Email


def email_exists(
    db: Session,
    *,
    gmail_message_id: str,
    user_id: int,
) -> bool:
    return (
        db.query(Email)
        .filter(
            Email.gmail_message_id == gmail_message_id,
            Email.user_id == user_id,
        )
        .first()
        is not None
    )
