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
    email_type:str

class EmailUpdate(BaseModel):
    email_type:str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/emails", status_code=status.HTTP_201_CREATED)
def save_email(request: EmailRequest, db: Session = Depends(get_db)):
    try:
        new_email = Email(email=request.email,
                          email_type=request.email_type)
        db.add(new_email)
        db.commit()
        db.refresh(new_email)

        return {
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
    email=(
        db.query(Email)
        .filter(Email.id==email_id,Email.is_active==True)
        .first()
    )
    if not email:
        raise HTTPException(
            status_code=404,
            detail="Email Not Found"
        )
    try:
        email.email_type=request.email_type
        db.commit()
        db.refresh(email)
        return email
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Invalid Email type or Duplicate email"
        )
    
@app.delete("/emails/{email_id}",status_code=204)
def delete_email(
    email_id:int,
    db: Session=Depends(get_db)
):  
    email=(
        db.query(Email)
        .filter(
            Email.id==email_id,Email.is_active==True
        )
        .first()
    )

    if not email:
        raise HTTPException(
            status_code=404,
            detail="Email Not Found"
        )
    email.is_active=False
    db.commit()