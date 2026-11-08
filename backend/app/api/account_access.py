import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import current_user, digest, hasher, rate_limit
from app.db.session import get_db
from app.models.entities import AccountToken, AuditLog, Session, User
from app.schemas.beta import EmailRequest, ResetInput, TokenInput
from app.services.account_mail import deliver_safely, mail_available

router = APIRouter(prefix="/auth", tags=["Account access"])
GENERIC = {
    "message": "If the account is eligible, an email will arrive shortly. Check spam or request a new link if needed."
}


def require_mail():
    if not mail_available():
        raise HTTPException(503, "Email delivery is not configured on this deployment yet")


def queue_token(db, user, purpose, background):
    # Serialize issuance/reset/password changes for a user. Only hashes persist.
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    db.execute(delete(AccountToken).where(AccountToken.user_id == user.id, AccountToken.purpose == purpose))
    raw = secrets.token_urlsafe(48)
    db.add(
        AccountToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=digest(raw),
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        )
    )
    db.commit()
    background.add_task(deliver_safely, user.email, purpose, raw)


def consume(db, raw, purpose):
    token = db.scalar(
        select(AccountToken).where(AccountToken.token_hash == digest(raw), AccountToken.purpose == purpose)
    )
    if not token:
        raise HTTPException(400, "This link is invalid or expired. Request a new one.")
    user = db.scalar(select(User).where(User.id == token.user_id).with_for_update())
    token = db.scalar(
        select(AccountToken)
        .where(AccountToken.id == token.id, AccountToken.expires_at > datetime.now(UTC))
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not token or not user or not user.is_active:
        raise HTTPException(400, "This link is invalid or expired. Request a new one.")
    db.delete(token)
    return user


@router.get("/config")
def config():
    return {
        "email_available": mail_available(),
        "verification_required": settings().require_email_verification,
    }


@router.post("/request-password-reset", status_code=202)
def request_reset(data: EmailRequest, request: Request, background: BackgroundTasks, db=Depends(get_db)):
    rate_limit("reset-ip:" + (request.client.host if request.client else "unknown"), 20, 3600)
    rate_limit("reset-email:" + str(data.email).lower(), 3, 900)
    require_mail()
    user = db.scalar(select(User).where(User.email == str(data.email).lower(), User.is_active.is_(True)))
    if user:
        queue_token(db, user, "reset", background)
    return GENERIC


@router.post("/request-verification", status_code=202)
def request_verification(background: BackgroundTasks, user=Depends(current_user), db=Depends(get_db)):
    rate_limit("verify:" + str(user.id), 3, 900)
    require_mail()
    if not user.email_verified:
        queue_token(db, user, "verify", background)
    return GENERIC


@router.post("/verify-email", status_code=204)
def verify(data: TokenInput, request: Request, db=Depends(get_db)):
    rate_limit("verify-token:" + (request.client.host if request.client else "unknown"), 30, 900)
    user = consume(db, data.token, "verify")
    user.email_verified = True
    db.add(AuditLog(actor_id=user.id, action="account.email_verified", resource_id=str(user.id)))
    db.commit()


@router.post("/reset-password", status_code=204)
def reset(data: ResetInput, request: Request, response: Response, db=Depends(get_db)):
    rate_limit("reset-token:" + (request.client.host if request.client else "unknown"), 30, 900)
    user = consume(db, data.token, "reset")
    user.password_hash = hasher.hash(data.new_password)
    db.execute(delete(Session).where(Session.user_id == user.id))
    db.execute(delete(AccountToken).where(AccountToken.user_id == user.id, AccountToken.purpose == "reset"))
    db.add(AuditLog(actor_id=user.id, action="account.password_reset", resource_id=str(user.id)))
    db.commit()
    response.delete_cookie("tl_session", path="/")
    response.delete_cookie("tl_csrf", path="/")
