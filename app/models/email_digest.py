from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base

class EmailDigest(Base):
    __tablename__ = "email_digests"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    range = Column(String, nullable=False)

    content = Column(String, nullable=False) 
    email_count = Column(Integer, nullable=False)
    model_version = Column(String, nullable=False)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )
