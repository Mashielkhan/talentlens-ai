import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from fastapi import Depends, HTTPException, Request, Response
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import Session, User

hasher = PasswordHasher()
DUMMY_HASH = hasher.hash("constant dummy value to equalize password checks")


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def verify_password(encoded, password):
    try:
        return hasher.verify(encoded, password)
    except VerificationError:
        return False


def rate_limit(key: str, limit: int, seconds: int = 60):
    client = Redis.from_url(settings().redis_url, socket_connect_timeout=2, socket_timeout=2)
    try:
        # Atomic counter with expiration, shared by API processes.
        value = client.eval(
            "local n=redis.call('INCR',KEYS[1]); if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end; return n",
            1,
            "limit:" + digest(key),
            seconds,
        )
    except Exception as exc:
        raise HTTPException(503, "Rate limiter unavailable; retry shortly") from exc
    finally:
        client.close()
    if value > limit:
        raise HTTPException(429, "Too many requests; try again later", headers={"Retry-After": str(seconds)})


def issue_session(db: DBSession, user: User, response: Response):
    token, csrf = secrets.token_urlsafe(48), secrets.token_urlsafe(32)
    seconds = settings().session_hours * 3600
    db.add(
        Session(
            user_id=user.id,
            token_hash=digest(token),
            csrf_hash=digest(csrf),
            expires_at=datetime.now(UTC) + timedelta(seconds=seconds),
        )
    )
    db.commit()
    common = {"secure": settings().cookie_secure, "samesite": "lax", "max_age": seconds, "path": "/"}
    response.set_cookie("tl_session", token, httponly=True, **common)
    response.set_cookie("tl_csrf", csrf, httponly=False, **common)


def current_user(request: Request, db: DBSession = Depends(get_db)):
    token = request.cookies.get("tl_session", "")
    session = (
        db.scalar(
            select(Session).where(Session.token_hash == digest(token), Session.expires_at > datetime.now(UTC))
        )
        if token
        else None
    )
    if not session:
        raise HTTPException(401, "Please sign in")
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "Session expired")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if not secrets.compare_digest(digest(request.headers.get("x-csrf-token", "")), session.csrf_hash):
            raise HTTPException(403, "CSRF token invalid")
    request.state.session = session
    return user


def require_role(role):
    def dependency(user=Depends(current_user)):
        if user.role != role:
            raise HTTPException(403, "This action is unavailable for your account role")
        if settings().require_email_verification and not user.email_verified:
            raise HTTPException(403, "Verify your email in Account access before using this feature")
        return user

    return dependency
