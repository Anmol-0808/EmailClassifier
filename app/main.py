from fastapi import FastAPI, Depends, status, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import func
import os

from app.database import SessionLocal, engine, Base
from app.models.email import Email
from app.schemas.email_schema import EmailResponse
from app.ai.classifier import classify_email
from app.ai.digest_generator import generate_digest
from app.utils.time_filter import get_time_cutoff
from app.routes import auth, user, google_auth
from app.logger import logger

load_dotenv()

HIGH_CONFIDENCE_THRESHOLD = 0.8
LOW_CONFIDENCE_THRESHOLD = 0.6

app = FastAPI()

if os.getenv("ENV") != "test":
    Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(google_auth.router)

# ------------------------------------------------------------------
# DB Dependency
# ------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class EmailRequest(BaseModel):
    email: EmailStr
    content: str

class EmailUpdate(BaseModel):
    email_type: str

# ------------------------------------------------------------------
# Analytics
# ------------------------------------------------------------------

@app.get("/emails/analytics")
def email_analytics(db: Session = Depends(get_db)):
    total = db.query(func.count(Email.id)).scalar() or 0
    ai_decisions = db.query(func.count(Email.id)).filter(Email.is_ai_generated == True).scalar() or 0
    human_overrides = db.query(func.count(Email.id)).filter(Email.is_ai_generated == False).scalar() or 0
    needs_review = db.query(func.count(Email.id)).filter(Email.needs_review == True).scalar() or 0

    avg_confidence = db.query(func.avg(Email.confidence_score)).scalar()
    avg_confidence = round(avg_confidence, 2) if avg_confidence else 0.0

    high_conf = db.query(func.count(Email.id)).filter(
        Email.confidence_score >= HIGH_CONFIDENCE_THRESHOLD
    ).scalar() or 0

    mid_conf = db.query(func.count(Email.id)).filter(
        Email.confidence_score < HIGH_CONFIDENCE_THRESHOLD,
        Email.confidence_score >= LOW_CONFIDENCE_THRESHOLD
    ).scalar() or 0

    low_conf = db.query(func.count(Email.id)).filter(
        Email.confidence_score < LOW_CONFIDENCE_THRESHOLD
    ).scalar() or 0

    return {
        "total_emails": total,
        "ai_decisions": ai_decisions,
        "human_overrides": human_overrides,
        "needs_review": needs_review,
        "average_confidence": avg_confidence,
        "confidence_distribution": {
            "high": high_conf,
            "medium": mid_conf,
            "low": low_conf
        }
    }

# ------------------------------------------------------------------
# Reclassify
# ------------------------------------------------------------------

@app.post("/emails/reclassify")
def reclassify_emails(limit: int = 10, db: Session = Depends(get_db)):
    emails = (
        db.query(Email)
        .filter(Email.is_active == True, Email.is_ai_generated == True)
        .order_by(Email.created_at.desc())
        .limit(limit)
        .all()
    )

    updated = 0

    for email in emails:
        ai_result = classify_email(email.body)

        email.ai_email_type = ai_result["email_type"]
        email.confidence_score = ai_result["confidence"]
        email.ai_reason = ai_result["reason"]
        email.model_version = ai_result["model_version"]
        email.needs_review = email.confidence_score < HIGH_CONFIDENCE_THRESHOLD

        updated += 1

    db.commit()

    return {
        "message": "Reclassification completed",
        "emails_reclassified": updated
    }

# ------------------------------------------------------------------
# Create Email
# ------------------------------------------------------------------

@app.post("/emails", status_code=status.HTTP_201_CREATED)
def save_email(request: EmailRequest, db: Session = Depends(get_db)):
    try:
        ai_result = classify_email(request.content)

        confidence = ai_result["confidence"]
        confidence = max(0.0, min(confidence, 1.0))

        new_email = Email(
            email=request.email,
            body=request.content,
            email_type=ai_result["email_type"],
            ai_email_type=ai_result["email_type"],
            confidence_score=confidence,
            ai_reason=ai_result["reason"],
            model_version=ai_result["model_version"],
            needs_review=confidence < HIGH_CONFIDENCE_THRESHOLD,
            is_ai_generated=True,
            received_at=datetime.utcnow()
        )

        db.add(new_email)
        db.commit()
        db.refresh(new_email)

        return {
            "id": new_email.id,
            "message": "Email saved successfully",
            "email": new_email.email,
            "email_type": new_email.email_type,
            "created_at": new_email.created_at
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid Email or Email already exists"
        )

# ------------------------------------------------------------------
# Get Emails
# ------------------------------------------------------------------

@app.get("/emails", response_model=List[EmailResponse])
def get_emails(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    emails = (
        db.query(Email)
        .filter(Email.is_active == True)
        .order_by(Email.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return emails

# ------------------------------------------------------------------
# Update Email (Human Override)
# ------------------------------------------------------------------

@app.patch("/emails/{email_id}", response_model=EmailResponse)
def update_email_type(
    email_id: int,
    request: EmailUpdate,
    db: Session = Depends(get_db)
):
    email = (
        db.query(Email)
        .filter(Email.id == email_id, Email.is_active == True)
        .first()
    )

    if not email:
        raise HTTPException(status_code=404, detail="Email Not Found")

    email.email_type = request.email_type
    email.is_ai_generated = False
    email.needs_review = False

    db.commit()
    db.refresh(email)
    return email

# ------------------------------------------------------------------
# Delete Email (Soft Delete)
# ------------------------------------------------------------------

@app.delete("/emails/{email_id}", status_code=204)
def delete_email(email_id: int, db: Session = Depends(get_db)):
    email = (
        db.query(Email)
        .filter(Email.id == email_id, Email.is_active == True)
        .first()
    )

    if not email:
        raise HTTPException(status_code=404, detail="Email Not Found")

    email.is_active = False
    db.commit()

# ------------------------------------------------------------------
# Digest (DAY 10)
# ------------------------------------------------------------------

@app.get("/emails/digest")
def get_email_digest(
    range: str = Query("7d", description="Time range: 7d, 15d, 30d"),
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

    digest_result = generate_digest(
        summaries=summaries,
        categories=categories
    )

    return {
        "range": range,
        "email_count": len(emails),
        "digest": digest_result["digest"],
        "model_version": digest_result["model_version"]
    }
