from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.schemas.user_schema import UserCreate,UserLogin,TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)

router=APIRouter(prefix="/auth",tags=["auth"])

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

        
@router.post("/signup",response_model=TokenResponse)
def signup(user:UserCreate,db:Session=Depends(get_db)):
    existing_user=db.query(User).filter(User.email==user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user=User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token=create_access_token({"sub":new_user.email})

    return {"access_token":token}

@router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user or not verify_password(
        user.password,
        db_user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({"sub": db_user.email})

    return {"access_token": token}
