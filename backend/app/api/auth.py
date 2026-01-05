"""Auth endpoints."""


from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from app.core.config import Settings
from app.core.auth import get_current_user
from app.core.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def find_account(settings: Settings, username: str):
    for account in settings.accounts:
        if account.username == username:
            return account
    return None


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request):
    settings = get_settings(request)
    account = find_account(settings, payload.username)
    if not account or not verify_password(payload.password, account.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(
        subject=account.username,
        secret_key=settings.app.secret_key,
        expires_minutes=settings.app.token_expire_minutes,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"username": account.username},
    }


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user
