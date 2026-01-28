from fastapi import APIRouter,Depends,Query,HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.models.email import Email
from app.core.security import decode_access_token
from app.core.gmail_client import list_messages,get_message
from app.core.gmail_parser import parse_message
from app.dependencies.auth import get_current_user
from app.utils.time_filter import get_time_cutoff
from datetime import datetime
from email.utils import parsedate_to_datetime
from app.ai.classifier import classify_email
from app.ai.summarizer import summarize_email
from app.ai.digest_generator import generate_digest
from app.models.email_digest import EmailDigest


router=APIRouter(prefix="/gmail",tags=["gmail"])

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/sync")
def sync_gmail(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    google_account = current_user.google_account
    messages = list_messages(google_account.access_token, max_results=5)

    parsed_emails = []

    for msg in messages:
        full_msg = get_message(
            google_account.access_token,
            msg["id"]
        )

        parsed = parse_message(full_msg)

        email_obj = Email(
            email=parsed["sender"],
            email_type="newsletter",  # placeholder for now
            body=parsed["body"],
            received_at=parsedate_to_datetime(parsed["received_at"])
        )

        db.add(email_obj)
        parsed_emails.append(parsed)

    db.commit()
    return parsed_emails


@router.get("/emails")
def get_emails_by_time(
    range:str=Query("7d",description="Time range:7d,15d,30d"),
    db:Session=Depends(get_db),
    current_user:User=Depends(get_current_user)
):
    try:
        cutoff_time=get_time_cutoff(range)
    except ValueError as e:
        raise HTTPException(status_code=400,detail=str(e))
    
    emails=(
        db.query(Email)
        .filter(Email.received_at>=cutoff_time)
        .order_by(Email.received_at.desc())
        .all()
    )
    return emails

@router.post("/classify")
def classify_emails(
    range: str = Query("7d", description="Time range: 7d, 15d, 30d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cutoff_time = get_time_cutoff(range)

    emails = (
        db.query(Email)
        .filter(
            Email.received_at >= cutoff_time,
            Email.ai_email_type.is_(None)  # re-runnable safety
        )
        .all()
    )

    classified_count = 0

    for email in emails:
        result = classify_email(email.body)

        email.ai_email_type = result["email_type"]
        email.confidence_score = result["confidence"]
        email.ai_reason = result["reason"]
        email.model_version = result["model_version"]
        email.needs_review = result["confidence"] < 0.6

        classified_count += 1

    db.commit()

    return {
        "classified": classified_count
    }
@router.post("/summarize")
def summarize_emails(
    range: str = Query("7d", description="Time range: 7d, 15d, 30d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    cutoff_time = get_time_cutoff(range)

    emails = (
        db.query(Email)
        .filter(
            Email.received_at >= cutoff_time,
            Email.ai_summary.is_(None)  # re-runnable safety
        )
        .all()
    )

    summarized_count = 0

    for email in emails:
        result = summarize_email(email.body)

        email.ai_summary = result["summary"]
        email.model_version = result["model_version"]

        summarized_count += 1

    db.commit()

    return {
        "summarized": summarized_count
    }
@router.get("/digest")
def get_email_digest(
    range: str = Query("7d", description="Time range: 7d, 15d, 30d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check cached digest
    existing = (
        db.query(EmailDigest)
        .filter(EmailDigest.range == range)
        .order_by(EmailDigest.created_at.desc())
        .first()
    )

    if existing:
        return {
            "range": range,
            "digest": existing.content,
            "cached": True
        }

    cutoff_time = get_time_cutoff(range)

    emails = (
        db.query(Email)
        .filter(Email.received_at >= cutoff_time)
        .all()
    )

    summaries = [e.ai_summary for e in emails if e.ai_summary]
    categories = [e.ai_email_type for e in emails if e.ai_summary]

    result = generate_digest(summaries, categories)

    digest = EmailDigest(
        range=range,
        content=result["digest"],
        model_version=result["model_version"]
    )

    db.add(digest)
    db.commit()

    return {
        "range": range,
        "digest": result["digest"],
        "cached": False
    }

@router.get("/review")
def get_emails_needing_review(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emails = (
        db.query(Email)
        .filter(Email.needs_review.is_(True))
        .order_by(Email.received_at.desc())
        .all()
    )

    return emails

@router.post("/override/{email_id}")
def override_email_classification(
    email_id: int,
    new_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if new_type not in {"newsletter", "support", "marketing"}:
        raise HTTPException(status_code=400, detail="Invalid email type")

    email = db.query(Email).filter(Email.id == email_id).first()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    email.ai_email_type = new_type
    email.needs_review = False
    email.ai_reason = "Manually overridden by user"

    db.commit()

    return {
        "status": "updated",
        "email_id": email_id,
        "new_type": new_type
    }
