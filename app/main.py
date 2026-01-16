from fastapi import FastAPI, Depends, status,HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from app.schemas.email_schema import EmailResponse



from app.database import SessionLocal, engine, Base
from app.models.email import Email  

app = FastAPI()

Base.metadata.create_all(bind=engine)


class EmailRequest(BaseModel):
    email: EmailStr


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/emails", status_code=status.HTTP_201_CREATED)
def save_email(request: EmailRequest, db: Session = Depends(get_db)):
    try:
        new_email = Email(email=request.email)
        db.add(new_email)
        db.commit()
        db.refresh(new_email)

        return {
            "message": "Email saved successfully",
            "email": new_email.email,
            "created_at": new_email.created_at
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )


@app.get("/emails",response_model=List[EmailResponse])
def get_emails(limit:int=10,db:Session=Depends(get_db)):
    emails=(
        db.query(Email)
        .order_by(Email.created_at.desc())
        .limit(limit)
        .all()
    )
    return emails