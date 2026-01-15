from fastapi import FastAPI, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
app=FastAPI()
models.Base.metadata.create_all(bind=engine)
class EmailRequest(BaseModel):
    email:EmailStr

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/emails", status_code=status.HTTP_201_CREATED)
def save_email(request: EmailRequest,db:Session =Depends(get_db)):
    new_email=models.Email(email=request.email)
    db.add(new_email)
    db.commit()
    db.refresh(new_email)

    return {
        "message":"Email saved successfully",
        "email":new_email.email
    }