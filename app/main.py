from fastapi import FastAPI, Depends, status,HTTPException,Header
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.schemas.email_schema import EmailResponse
from fastapi.security import APIKeyHeader
import os
from dotenv import load_dotenv
from app.ai.classifier import classify_email
load_dotenv()
from sqlalchemy import func
from .logger import logger
API_KEY=os.getenv("API_KEY")
api_key_header=APIKeyHeader(name="X-API-Key")

from app.database import SessionLocal, engine, Base
from app.models.email import Email
from app.models.google_account import GoogleAccount  
from app.routes import auth,user,google_auth
HIGH_CONFIDENCE_THRESHOLD=0.8
LOW_CONFIDENCE_THRESHOLD=0.6

app = FastAPI()
if os.getenv("ENV")!="test":
    Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(google_auth.router)

class EmailRequest(BaseModel):
    email: EmailStr
    content:str

class EmailUpdate(BaseModel):
    email_type:str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != API_KEY:
        logger.warning("Unauthorized API key attemot")
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )

@app.get("/emails/analytics")
def email_analytics(db:Session=Depends(get_db)):
    total=db.query(func.count(Email.id)).scalar() or 0

    ai_decisions=db.query(func.count(Email.id)).filter(
        Email.is_ai_generated==True
    ).scalar() or 0

    human_overrides=db.query(func.count(Email.id)).filter(
        Email.is_ai_generated==False
    ).scalar() or 0

    needs_review=db.query(func.count(Email.id)).filter(
        Email.needs_review==True
    ).scalar() or 0

    avg_confidence=db.query(func.avg(Email.confidence_score)).scalar()
    avg_confidence=round(avg_confidence,2) if avg_confidence else 0.0

    high_conf=db.query(func.count(Email.id)).filter(
        Email.confidence_score>=HIGH_CONFIDENCE_THRESHOLD
    ).scalar() or 0

    mid_conf=db.query(func.count(Email.id)).filter(
        Email.confidence_score<HIGH_CONFIDENCE_THRESHOLD,
        Email.confidence_score>=LOW_CONFIDENCE_THRESHOLD
    ).scalar() or 0

    low_conf=db.query(func.count(Email.id)).filter(
        Email.confidence_score<LOW_CONFIDENCE_THRESHOLD
    ).scalar() or 0

    return{
        "total_emails":total,
        "ai_decisions":ai_decisions,
        "human_overrides":human_overrides,
        "needs_review":needs_review,
        "average_confidence":avg_confidence,
        "confidence_distribution":{
            "high":high_conf,
            "medium":mid_conf,
            "low":low_conf

        }
    }


@app.post("/emails/reclassify")
def reclassify_emails(limit: int = 10, db: Session = Depends(get_db)):
    """
    Re-run AI classification on existing emails.
    Only affects AI-generated decisions.
    """

    emails = (
        db.query(Email)
        .filter(
            Email.is_active == True,
            Email.is_ai_generated == True
        )
        .order_by(Email.created_at.desc())
        .limit(limit)
        .all()
    )

    updated = 0

    for email in emails:
        ai_result = classify_email(email.ai_reason or "")

        email.ai_email_type = ai_result["email_type"]
        email.confidence_score = ai_result["confidence"]
        email.ai_reason = ai_result["reason"]
        email.model_version = ai_result["model_version"]

        if email.confidence_score >= HIGH_CONFIDENCE_THRESHOLD:
            email.needs_review = False
        else:
            email.needs_review = True

        updated += 1

    db.commit()

    return {
        "message": "Reclassification completed",
        "emails_reclassified": updated
    }



@app.post("/emails",status_code=status.HTTP_201_CREATED)
def save_email(request: EmailRequest, db: Session = Depends(get_db)):
    try:

        ai_result=classify_email(request.content)
        ai_email_type=ai_result["email_type"]
        confidence=ai_result["confidence"]
        reason=ai_result["reason"]
        model_version=ai_result["model_version"]

        if confidence>= HIGH_CONFIDENCE_THRESHOLD:
            needs_review=False
        elif confidence>=LOW_CONFIDENCE_THRESHOLD:
            needs_review=True
        else:
            needs_review=True

        if confidence is None or not isinstance(confidence,(int,float)):
            confidence=0.0
        if not reason or not isinstance(reason,str):
            reason="No explaination provided by AI"
        
        confidence=max(0.0,min(confidence,1))


        new_email = Email(
        email=request.email,
        email_type=ai_email_type,
        ai_email_type=ai_email_type,
        confidence_score=confidence,
        ai_reason=reason,
        model_version=model_version,
        needs_review=needs_review,
        is_ai_generated=True
        )
        db.add(new_email)
        db.commit()
        db.refresh(new_email)

        return {
            "id":new_email.id,
            "message": "Email saved successfully",
            "email": new_email.email,
            "email_type":new_email.email_type,
            "created_at": new_email.created_at
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Email or Email already exists"
        )


@app.get("/emails",response_model=List[EmailResponse])
def get_emails(limit:int=10,offset:int =0,db:Session=Depends(get_db)):
    emails=(
        db.query(Email)
        .filter(Email.is_active==True)
        .order_by(Email.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return emails

@app.patch("/emails/{email_id}",response_model=EmailResponse)
def update_email_type(
    email_id:int,
    request: EmailUpdate,
    db:Session=Depends(get_db)
):
    logger.info(
        "Human Override | id =%s new_type=%s",
        email_id,
        request.email_type
    )
    email=(
        db.query(Email)
        .filter(Email.id==email_id,Email.is_active==True)
        .first()
    )
    if not email:
        logger.warning(
            "Update failed :Email not found | id=%s",
            email_id
        )
        raise HTTPException(
            status_code=404,
            detail="Email Not Found"
        )
    try:
        email.email_type=request.email_type
        email.is_ai_generated=False
        email.needs_review=False
        db.commit()
        db.refresh(email)
        logger.info(
            "Email Updated successfully | id=%s new_type=%s",
            email_id,
            request.email_type
        )
        return email

    except IntegrityError:
        db.rollback()
        logger.warning(
            "Update failed:Constraint violation | id=%s type=%s",
            email_id,
            request.email_type
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid Email type or Duplicate email"
        )
    
@app.delete("/emails/{email_id}",status_code=204)
def delete_email(
    email_id:int,
    db: Session=Depends(get_db)
):  
    logger.info(
        "Delete email request | id=%s",
        email_id
    )
    email=(
        db.query(Email)
        .filter(
            Email.id==email_id,Email.is_active==True
        )
        .first()
    )

    if not email:
        logger.warning(
            "Delete failed : email not found | id=%s",
            email_id
        )
        raise HTTPException(
            status_code=404,
            detail="Email Not Found"
        )
    email.is_active=False
    db.commit()

    logger.info(
        "Email soft deleted | id=%s",
        email_id
    )