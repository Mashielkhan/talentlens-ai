from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.core.security import DUMMY_HASH, current_user, hasher, issue_session, rate_limit, verify_password
from app.db.session import get_db
from app.models.entities import AccountToken, AuditLog, Deletion, Resume, Session, User
from app.schemas.contracts import Login, PasswordUpdate, ProfileUpdate, Register, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: Register, response: Response, request: Request, db=Depends(get_db)):
    rate_limit("register:" + (request.client.host if request.client else "unknown"), 10, 3600)
    user = User(
        email=str(data.email).lower(),
        full_name=data.full_name.strip(),
        password_hash=hasher.hash(data.password),
        role=data.role,
        profile={"company": data.company, "visibility": "private"},
    )
    db.add(user)
    try:
        db.flush()
        db.add(AuditLog(actor_id=user.id, action="account.registered", resource_id=str(user.id)))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Registration unavailable for this email") from exc
    issue_session(db, user, response)
    return user


@router.post("/login", response_model=UserOut)
def login(data: Login, response: Response, request: Request, db=Depends(get_db)):
    rate_limit("login-ip:" + (request.client.host if request.client else "unknown"), 40, 900)
    rate_limit("login-email:" + str(data.email).lower(), 10, 900)
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    valid = verify_password(user.password_hash if user else DUMMY_HASH, data.password)
    if not user or not valid or not user.is_active:
        raise HTTPException(401, "Email or password is incorrect")
    issue_session(db, user, response)
    return user


@router.get("/me", response_model=UserOut)
def me(user=Depends(current_user)):
    return user


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, user=Depends(current_user), db=Depends(get_db)):
    db.delete(request.state.session)
    db.commit()
    response.delete_cookie("tl_session", path="/")
    response.delete_cookie("tl_csrf", path="/")


@router.post("/refresh", response_model=UserOut)
def refresh(request: Request, response: Response, user=Depends(current_user), db=Depends(get_db)):
    db.delete(request.state.session)
    issue_session(db, user, response)
    return user


@router.patch("/profile", response_model=UserOut)
def update_profile(data: ProfileUpdate, user=Depends(current_user), db=Depends(get_db)):
    user.full_name = data.full_name.strip()
    user.profile = {**data.model_dump(exclude={"full_name"}), "visibility": "private"}
    db.commit()
    return user


@router.post("/password", status_code=204)
def password(data: PasswordUpdate, response: Response, user=Depends(current_user), db=Depends(get_db)):
    user = db.scalar(
        select(User).where(User.id == user.id).with_for_update().execution_options(populate_existing=True)
    )
    if not verify_password(user.password_hash, data.current_password):
        raise HTTPException(400, "Current password is incorrect")
    user.password_hash = hasher.hash(data.new_password)
    db.execute(delete(Session).where(Session.user_id == user.id))
    db.execute(delete(AccountToken).where(AccountToken.user_id == user.id, AccountToken.purpose == "reset"))
    issue_session(db, user, response)


@router.delete("/account", status_code=204)
def delete_account(data: Login, response: Response, user=Depends(current_user), db=Depends(get_db)):
    if str(data.email).lower() != user.email or not verify_password(user.password_hash, data.password):
        raise HTTPException(400, "Account credentials are incorrect")
    for resume in db.scalars(select(Resume).where(Resume.owner_id == user.id).with_for_update()):
        db.add(Deletion(storage_key=resume.storage_key))
    db.add(AuditLog(actor_id=None, action="account.deleted", resource_id=str(user.id)))
    db.delete(user)
    db.commit()
    response.delete_cookie("tl_session", path="/")
    response.delete_cookie("tl_csrf", path="/")
