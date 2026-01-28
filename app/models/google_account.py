from sqlalchemy import Column,Integer,String,ForeignKey,DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class GoogleAccount(Base):
    __tablename__="google_accounts"

    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(Integer,ForeignKey("users.id"),unique=True)
    google_user_id=Column(String,unique=True,index=True)
    email=Column(String,index=True)
    created_at=Column(DateTime,default=datetime.utcnow)
    user=relationship("User",backref="google_account")
    