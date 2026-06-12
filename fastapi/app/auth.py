import os

import bcrypt
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account
from app.ui import GOOGLE_BUTTON_HTML, LOGIN_HTML, REGISTER_HTML

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
# Origin whose /auth/google/callback is registered with Google. The SSO
# button links here absolutely, so the OAuth flow (state cookie + callback)
# stays on one host no matter which hostname served the login page.
GOOGLE_AUTH_ORIGIN = os.environ.get("GOOGLE_AUTH_ORIGIN", "")

ERROR_MESSAGES = {
    "invalid": "Invalid email or password.",
    "exists": "An account with that email already exists.",
    "sso": "Google sign-in failed. Please try again.",
}

router = APIRouter()

oauth = OAuth()
if GOOGLE_ENABLED:
    oauth.register(
        name="google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def current_account(request: Request, db: Session) -> Account | None:
    account_id = request.session.get("account_id")
    if account_id is None:
        return None
    return db.get(Account, account_id)


def require_account(request: Request, db: Session = Depends(get_db)) -> Account:
    account = current_account(request, db)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    return account


def _render(template: str, error: str) -> str:
    message = ERROR_MESSAGES.get(error, "")
    google_html = GOOGLE_BUTTON_HTML.replace(
        "__GOOGLE_AUTH_URL__", f"{GOOGLE_AUTH_ORIGIN}/auth/google"
    )
    return template.replace(
        "__ERROR__", f'<p class="error">{message}</p>' if message else ""
    ).replace("__GOOGLE__", google_html if GOOGLE_ENABLED else "")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = ""):
    if request.session.get("account_id"):
        return RedirectResponse("/")
    return _render(LOGIN_HTML, error)


@router.post("/login")
def login(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter(Account.email == email).first()
    if (
        account is None
        or account.password_hash is None
        or not verify_password(password, account.password_hash)
    ):
        return RedirectResponse(
            "/login?error=invalid", status_code=status.HTTP_303_SEE_OTHER
        )
    request.session["account_id"] = account.id
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, error: str = ""):
    if request.session.get("account_id"):
        return RedirectResponse("/")
    return _render(REGISTER_HTML, error)


@router.post("/register")
def register(
    request: Request,
    display_name: str = Form(""),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if db.query(Account).filter(Account.email == email).first() is not None:
        return RedirectResponse(
            "/register?error=exists", status_code=status.HTTP_303_SEE_OTHER
        )
    account = Account(
        email=email,
        display_name=display_name or None,
        password_hash=hash_password(password),
        provider="local",
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    request.session["account_id"] = account.id
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/auth/google")
async def auth_google(request: Request):
    if not GOOGLE_ENABLED:
        raise HTTPException(status_code=404, detail="Google SSO is not configured")
    redirect_uri = str(request.url_for("auth_google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    if not GOOGLE_ENABLED:
        raise HTTPException(status_code=404, detail="Google SSO is not configured")
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(
            "/login?error=sso", status_code=status.HTTP_303_SEE_OTHER
        )
    userinfo = token["userinfo"]
    account = (
        db.query(Account).filter(Account.google_sub == userinfo["sub"]).first()
    )
    if account is None:
        # Link an existing local account by email, otherwise auto-provision
        account = (
            db.query(Account).filter(Account.email == userinfo["email"]).first()
        )
        if account is None:
            account = Account(
                email=userinfo["email"],
                display_name=userinfo.get("name"),
                provider="google",
            )
            db.add(account)
        account.google_sub = userinfo["sub"]
        db.commit()
        db.refresh(account)
    request.session["account_id"] = account.id
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
