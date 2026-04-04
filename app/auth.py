import os
import secrets

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from passlib.hash import bcrypt

from app import auth

router = APIRouter()


@router.get("/api/auth/setup-status")
async def setup_status():
    """Check whether admin credentials have been configured."""
    return {"configured": auth.credentials_configured()}


@router.get("/setup")
async def setup_page():
    """Serve the first-run setup page, or redirect to login if already configured."""
    if auth.credentials_configured():
        return RedirectResponse("/login", status_code=302)
    return FileResponse("frontend/setup.html")


@router.post("/api/auth/setup")
async def create_admin(
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    """First-run endpoint: create the admin account and write credentials to .env."""
    if auth.credentials_configured():
        raise HTTPException(status_code=400, detail="Admin account already exists")

    username = username.strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    pw_hash = bcrypt.hash(password)
    secret_key = secrets.token_hex(32)

    env_path = auth._ENV_PATH
    lines = []
    if os.path.isfile(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    keys_to_set = {
        "ADMIN_USERNAME": username,
        "ADMIN_PASSWORD_HASH": pw_hash,
        "SECRET_KEY": secret_key,
    }
    existing_keys = set()
    new_lines = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in keys_to_set:
            new_lines.append(f"{key}={keys_to_set[key]}\n")
            existing_keys.add(key)
        else:
            new_lines.append(line)
    for key, value in keys_to_set.items():
        if key not in existing_keys:
            new_lines.append(f"{key}={value}\n")

    with open(env_path, "w") as f:
        f.writelines(new_lines)
    os.chmod(env_path, 0o600)

    # Issue a token so the user is immediately logged in
    token = auth.create_access_token(username)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/login")
async def login_page(request: Request):
    """Serve the login HTML page, or redirect to setup if not configured."""
    if not auth.credentials_configured():
        return RedirectResponse("/setup", status_code=302)
    return FileResponse("frontend/login.html")


@router.post("/login")
async def login_json(username: str = Form(...), password: str = Form(...)):
    """POST /login — authenticate and return JWT token."""
    if not auth.authenticate_user(username, password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth.create_access_token(username)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/api/auth/login")
async def login_form(username: str = Form(...), password: str = Form(...)):
    """Form-based login (used by the login page). Returns JWT in JSON."""
    if not auth.authenticate_user(username, password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth.create_access_token(username)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/api/auth/logout")
async def logout():
    """Logout — client should discard the token."""
    return {"detail": "Logged out. Discard your token."}
