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
    text
)
from app.database import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)

    email_type = Column(String, nullable=False)

    ai_email_type=Column(String,nullable=True)
    confidence_score=Column(Float,nullable=True)
    ai_reason=Column(String,nullable=True)
    model_version=Column(String,nullable=True)

    is_ai_generated=Column(
        Boolean,
        nullable=False,
        server_default=text("TRUE")
    )

    needs_review=Column(
        Boolean,
        nullable=False,
        server_default=text("FALSE")
    )

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("TRUE")
    )



    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "email_type IN ('newsletter', 'support', 'marketing')",
            name="email_type_check"
        ),
        UniqueConstraint(
            "email",
            "email_type",
            name="email_email_type_unique"
        ),
    )
