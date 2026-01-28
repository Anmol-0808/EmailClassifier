import requests
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

from app.core.google_oauth import (
    GOOGLE_AUTH_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_REDIRECT_URI,
    GOOGLE_SCOPES,
    GOOGLE_TOKEN_URL,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_USERINFO_URL,
)
from app.core.security import create_access_token
from app.database import SessionLocal
from app.models.user import User
from app.models.google_account import GoogleAccount

router = APIRouter(prefix="/auth/google", tags=["google-auth"])


@router.get("/login")
def google_login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }

    url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/callback")
def google_callback(code: str):
    db = SessionLocal()
    try:
       
        token_response = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch token from Google",
            )

        tokens = token_response.json()
        access_token = tokens["access_token"]

        
        userinfo_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch Google user info",
            )

        userinfo = userinfo_response.json()
        google_user_id = userinfo["id"]
        email = userinfo["email"]

        
        google_account = (
            db.query(GoogleAccount)
            .filter(GoogleAccount.google_user_id == google_user_id)
            .first()
        )

        if google_account:
            user = google_account.user

        else:
           
            user = db.query(User).filter(User.email == email).first()

            if not user:
                user = User(email=email)
                db.add(user)
                db.commit()
                db.refresh(user)

           
            google_account = GoogleAccount(
                user_id=user.id,
                google_user_id=google_user_id,
                email=email,
            )
            db.add(google_account)
            db.commit()

      
        jwt_token = create_access_token({"sub": user.email})

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
        }

    finally:
        db.close()
