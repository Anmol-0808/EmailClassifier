from datetime import datetime,timedelta
from typing import Optional

from jose import JWTError,jwt
from passlib.context import CryptContext
import os

pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")

SECRET_KEY =os.getenv("SECRET_KEY","change_this_secret")
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE=60


def hash_password(password:str)->str:
    """
    Hash a plain password using bcrypt
      """
    return pwd_context.hash(password)


def verify_password(plain_password:str,hashed_password:str)->bool:
    """
    Verify plain password against hashed password
    """
    return pwd_context.verify(plain_password,hashed_password)



def create_access_token(
        data:dict,
        expires_delta:Optional[timedelta]=None
)->str:
    """
    Create a JWT Token
    """

    to_encode=data.copy()
    expire=datetime.utcnow()+(
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE)
    )

    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
        )
            return payload
        except JWTError:
            return None


