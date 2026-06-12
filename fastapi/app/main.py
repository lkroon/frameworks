import html
import os
import socket
import time

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app import auth, schemas
from app.database import get_db
from app.models import User
from app.ui import DASHBOARD_HTML

app = FastAPI(title="FastAPI Users")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-insecure-secret"),
    same_site="lax",
)
app.include_router(auth.router)


# Filled by the Downward API in k8s; sensible fallbacks for docker-compose
POD_INFO = {
    "pod": os.environ.get("POD_NAME") or socket.gethostname(),
    "pod_ip": os.environ.get("POD_IP", "unknown"),
    "node": os.environ.get("NODE_NAME", "unknown"),
    "namespace": os.environ.get("POD_NAMESPACE", "unknown"),
    "version": os.environ.get("APP_VERSION", "dev"),
}


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    account = auth.current_account(request, db)
    if account is None:
        return RedirectResponse("/login")
    return DASHBOARD_HTML.replace(
        "__ACCOUNT_NAME__", html.escape(account.display_name or account.email)
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/whoami", dependencies=[Depends(auth.require_account)])
def whoami():
    return POD_INFO


@app.get("/work", dependencies=[Depends(auth.require_account)])
def work(ms: int = 200):
    """Burn CPU for ~ms milliseconds (capped) to drive the HPA demo."""
    ms = max(1, min(ms, 2000))
    deadline = time.monotonic() + ms / 1000
    x = 0.0001
    while time.monotonic() < deadline:
        x = (x * x + 1.000001) % 1000
    return {"pod": POD_INFO["pod"], "burned_ms": ms}


K8S_SA_DIR = "/var/run/secrets/kubernetes.io/serviceaccount"
K8S_API = "https://kubernetes.default.svc"


class ScaleIn(BaseModel):
    replicas: int


def _scale_subresource(method: str, body: dict | None = None) -> dict:
    """Call the scale subresource of our own deployment via the k8s API,
    authenticated with the pod's ServiceAccount token."""
    try:
        # Read per request: projected tokens rotate
        with open(f"{K8S_SA_DIR}/token") as f:
            token = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Not running in Kubernetes")
    url = (
        f"{K8S_API}/apis/apps/v1/namespaces/{POD_INFO['namespace']}"
        "/deployments/fastapi/scale"
    )
    headers = {"Authorization": f"Bearer {token}"}
    if method == "PATCH":
        headers["Content-Type"] = "application/merge-patch+json"
    r = httpx.request(
        method, url, headers=headers, json=body, verify=f"{K8S_SA_DIR}/ca.crt"
    )
    if r.status_code >= 400:
        raise HTTPException(
            status_code=502, detail=f"Kubernetes API: {r.status_code} {r.text[:200]}"
        )
    return r.json()


@app.get("/scale", dependencies=[Depends(auth.require_account)])
def get_scale():
    s = _scale_subresource("GET")
    return {
        "desired": s["spec"].get("replicas", 0),
        "running": s["status"].get("replicas", 0),
    }


@app.post("/scale", dependencies=[Depends(auth.require_account)])
def set_scale(payload: ScaleIn):
    if not 1 <= payload.replicas <= 5:
        raise HTTPException(
            status_code=422, detail="replicas must be between 1 and 5"
        )
    s = _scale_subresource("PATCH", {"spec": {"replicas": payload.replicas}})
    return {
        "desired": s["spec"].get("replicas", 0),
        "running": s["status"].get("replicas", 0),
    }


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
