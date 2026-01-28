from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.core.security import decode_access_token
from app.core.gmail_client import list_messages,get_message
from app.core.gmail_parser import parse_message

router=APIRouter(prefix="/gmail",tags=["gmail"])

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/sync")
def sync_gmail(current_user:User=Depends(get_current_user)):
    google_account=current_user.google_account
    messages=list_messages(google_account.access_token,max_results=5)

    parsed_emails=[]
    for msg in messages:
        full_msg=get_message(
            google_account.access_token,
            msg["id"]
        )

        parsed_emails.append(parse_message(full_msg))
    
    return parsed_emails