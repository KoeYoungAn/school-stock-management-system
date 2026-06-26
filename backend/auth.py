import os
import hmac
import hashlib
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from utils import verify_password, hash_password, log_audit

SECRET_KEY = os.environ.get("SSMS_SECRET", "change-me-school-stock-secret")
COOKIE_NAME = "ssms_session"

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _sign(user_id: int) -> str:
    msg = str(user_id).encode()
    sig = hmac.new(SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()
    return f"{user_id}.{sig}"


def _unsign(token: str) -> Optional[int]:
    try:
        uid_str, sig = token.split(".", 1)
        expected = hmac.new(SECRET_KEY.encode(), uid_str.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return None
        return int(uid_str)
    except Exception:
        return None


def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(401, "Not authenticated")
    uid = _unsign(token)
    if not uid:
        raise HTTPException(401, "Invalid session")
    user = db.query(models.User).filter(
        models.User.id == uid,
        models.User.is_deleted == False,  # noqa
        models.User.status == "Active",
    ).first()
    if not user:
        raise HTTPException(401, "User not found or inactive")
    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None


def user_to_dict(u: models.User) -> dict:
    return {
        "id": u.id,
        "full_name": u.full_name,
        "email": u.email,
        "phone": u.phone,
        "role": u.role,
        "status": u.status,
        "profile_photo": u.profile_photo,
    }


@router.post("/login")
def login(payload: schemas.LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.email == payload.email.lower().strip(),
        models.User.is_deleted == False,  # noqa
    ).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    if user.status != "Active":
        raise HTTPException(403, "Account is inactive")
    token = _sign(user.id)
    response.set_cookie(
        COOKIE_NAME, token,
        httponly=True, samesite="lax", secure=False,
        max_age=60 * 60 * 24 * 7, path="/",
    )
    return {"user": user_to_dict(user)}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me")
def me(user: models.User = Depends(get_current_user)):
    perms_role = user.role
    return {"user": user_to_dict(user), "role": perms_role}


@router.post("/change-password")
def change_password(payload: schemas.ChangePasswordIn,
                    db: Session = Depends(get_db),
                    user: models.User = Depends(get_current_user)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    if len(payload.new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    log_audit(db, user.id, "password_change", "auth", user.id, "Changed own password")
    return {"ok": True}
