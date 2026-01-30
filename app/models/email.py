from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    CheckConstraint,
    UniqueConstraint,
    Float,
    func,
    text,
    ForeignKey,
    Text
)
from app.database import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)

    # 🔑 Ownership & dedup
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    gmail_message_id = Column(Text, index=True)

    # Email content
    email = Column(Text, nullable=False)  # sender
    body = Column(Text, nullable=False)

    email_type = Column(String, nullable=False)

    ai_email_type = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    ai_reason = Column(Text, nullable=True)
    model_version = Column(String, nullable=True)

    is_ai_generated = Column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    needs_review = Column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("TRUE"),
    )

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    received_at = Column(
        DateTime,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        CheckConstraint(
            "email_type IN ('newsletter', 'support', 'marketing')",
            name="email_type_check",
        ),
        UniqueConstraint(
            "user_id",
            "gmail_message_id",
            name="user_gmail_message_unique",
        ),
    )
