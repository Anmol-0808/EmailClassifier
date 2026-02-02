from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from fastapi import Path
from app.database import SessionLocal, engine, Base
from app.models.email import Email
from app.schemas.email_schema import EmailResponse
from app.utils.time_filter import get_time_cutoff
from app.ai.digest_generator import generate_digest
from app.ai.classifier import classify_email
from app.core.email_service import create_email
from app.routes import auth, user, google_auth
from fastapi.middleware.cors import CORSMiddleware
from app.models.email_digest import EmailDigest
from typing import Optional

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

@app.get("/emails")
def get_emails(
    pageToken: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
):
    offset = int(pageToken) if pageToken else 0

    query = (
        db.query(Email)
        .order_by(
            Email.received_at.desc().nullslast(),
            Email.id.desc()
        )
    )

    total_count = query.count()

    emails = query.offset(offset).limit(limit).all()

    next_page_token = (
        str(offset + limit) if offset + limit < total_count else None
    )

    return {
        "emails": emails,
        "nextPageToken": next_page_token
    }


@app.get("/digests")
def get_digest_history(db:Session=Depends(get_db)):
    digests=(
        db.query(EmailDigest)
        .order_by(EmailDigest.created_at.desc())
        .all()
    )
    return [
        {
            "id": d.id,
            "range": d.range,
            "summary": d.content,
            "email_count": d.email_count,
            "model": d.model_version,
            "created_at": d.created_at,
        }
        for d in digests
    ]

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
    digest_row =EmailDigest(
        range=range,
        content=digest["summary"],
        email_count=digest["email_count"],
        model_version=digest["model"],
    )
    db.add(digest_row)
    db.commit()
    db.refresh(digest_row)

    return {
    "summary": digest["summary"],
    "email_count": digest["email_count"],
    "model": digest["model"],
    }

@app.patch("/emails/{email_id}")
def override_email_category(
    email_id: int = Path(..., gt=0),
    payload: dict = None,
    db: Session = Depends(get_db),
):
    email = db.query(Email).filter(
        Email.id == email_id,
        Email.is_active == True
    ).first()

    if not email:
        raise HTTPException(
            status_code=404,
            detail="Email not found"
        )

    new_category = payload.get("email_type")

    if new_category not in ["marketing", "support", "newsletter"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid email category"
        )

    email.email_type = new_category
    email.needs_review = False
    email.is_ai_generated = False

    db.commit()
    db.refresh(email)

    return {
        "id": email.id,
        "email_type": email.email_type,
        "needs_review": email.needs_review,
    }
