from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class EmailDigest(Base):
    __tablename__ = "email_digests"

    id = Column(Integer, primary_key=True)
    range = Column(String, nullable=False)  # 7d / 15d / 30d
    content = Column(String, nullable=False)
    model_version = Column(String, nullable=False)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )
