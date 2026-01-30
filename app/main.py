from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import SessionLocal, engine, Base
from app.models.email import Email
from app.schemas.email_schema import EmailResponse
from app.utils.time_filter import get_time_cutoff
from app.ai.digest_generator import generate_digest
from app.ai.classifier import classify_email
from app.core.email_service import create_email
from app.routes import auth, user, google_auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(user.router)
app.include_router(google_auth.router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




@app.post("/emails", status_code=status.HTTP_201_CREATED)
def save_email(request: dict, db: Session = Depends(get_db)):
    email = create_email(
        db=db,
        sender=request["email"],
        body=request["content"],
    )

    return {
        "id": email.id,
        "email": email.email,
        "email_type": email.email_type,
        "created_at": email.created_at
    }



@app.get("/emails", response_model=List[EmailResponse])
def get_emails(db: Session = Depends(get_db)):
    return (
        db.query(Email)
        .filter(Email.is_active == True)
        .order_by(Email.received_at.desc())
        .all()
    )



@app.get("/emails/digest")
def get_email_digest(
    range: str = Query("7d", description="7d | 15d | 30d"),
    db: Session = Depends(get_db)
):
    try:
        cutoff = get_time_cutoff(range)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    emails = (
        db.query(Email)
        .filter(
            Email.is_active == True,
            Email.received_at >= cutoff
        )
        .order_by(Email.received_at.desc())
        .all()
    )

    summaries = []
    categories = []

    for email in emails:
        if email.ai_reason:
            summaries.append(email.ai_reason)
            categories.append(email.email_type)

    digest = generate_digest(
        summaries=summaries,
        categories=categories
    )

    return {
        "range": range,
        "email_count": len(emails),
        "digest": digest["digest"],
        "model_version": digest["model_version"]
    }
