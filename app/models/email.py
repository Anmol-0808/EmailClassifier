from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )
