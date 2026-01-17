from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    CheckConstraint,
    UniqueConstraint,
    func,
    text
)
from app.database import Base


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)

    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("TRUE")
    )

    email_type = Column(String, nullable=False)

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
