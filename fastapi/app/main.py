import html
import os

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app import auth, schemas
from app.database import get_db
from app.models import User
from app.ui import INDEX_HTML

app = FastAPI(title="FastAPI Users")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-insecure-secret"),
    same_site="lax",
)
app.include_router(auth.router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    account = auth.current_account(request, db)
    if account is None:
        return RedirectResponse("/login")
    return INDEX_HTML.replace(
        "__ACCOUNT_NAME__", html.escape(account.display_name or account.email)
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/users",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth.require_account)],
)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = User(name=payload.name, email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get(
    "/users",
    response_model=list[schemas.UserOut],
    dependencies=[Depends(auth.require_account)],
)
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@app.get(
    "/users/{user_id}",
    response_model=schemas.UserOut,
    dependencies=[Depends(auth.require_account)],
)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put(
    "/users/{user_id}",
    response_model=schemas.UserOut,
    dependencies=[Depends(auth.require_account)],
)
def update_user(
    user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db)
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.name = payload.name
    user.email = payload.email
    db.commit()
    db.refresh(user)
    return user


@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(auth.require_account)],
)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
