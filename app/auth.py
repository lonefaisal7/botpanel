"""
Authentication module for Bot Hosting Panel.

Uses JWT tokens with bcrypt-hashed password stored in .env.
"""

import os
import logging
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.hash import bcrypt
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

log = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Path to .env file (project root)
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


def _load_credentials():
    """Reload credentials from .env so runtime changes are picked up."""
    load_dotenv(override=True)
    return {
        "username": os.getenv("ADMIN_USERNAME", ""),
        "password_hash": os.getenv("ADMIN_PASSWORD_HASH", ""),
        "secret_key": os.getenv("SECRET_KEY", "change-me-to-a-random-secret"),
    }


def credentials_configured() -> bool:
    """Return True if admin credentials have been set up in .env."""
    creds = _load_credentials()
    return bool(creds["username"]) and bool(creds["password_hash"])

security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.verify(plain_password, hashed_password)
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate admin user against .env credentials."""
    creds = _load_credentials()
    if not creds["password_hash"]:
        return False
    if username != creds["username"]:
        return False
    return verify_password(password, creds["password_hash"])


def create_access_token(username: str) -> str:
    """Create a JWT access token."""
    creds = _load_credentials()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, creds["secret_key"], algorithm=ALGORITHM)


def verify_token(token: str) -> str:
    """Verify JWT token and return username. Raises HTTPException on failure."""
    creds = _load_credentials()
    try:
        payload = jwt.decode(token, creds["secret_key"], algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Dependency: extract and verify the current user from the JWT Bearer token."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return verify_token(credentials.credentials)


# Paths that don't require authentication
PUBLIC_PATHS = {
    "/", "/login", "/api/auth/login", "/health", "/docs", "/openapi.json", "/redoc",
    "/setup", "/api/auth/setup", "/api/auth/setup-status",
}
PUBLIC_PREFIXES = ("/static/",)


def requires_auth(request: Request) -> bool:
    """Return True if the request path needs authentication."""
    path = request.url.path
    if path in PUBLIC_PATHS:
        return False
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return False
    return True


async def auth_middleware(request: Request, call_next):
    """Middleware that returns 401 for unauthenticated API requests
    and redirects browser requests to /login (or /setup on first run)."""
    from fastapi.responses import JSONResponse, RedirectResponse

    # If no credentials configured yet, redirect everything to setup
    if not credentials_configured():
        path = request.url.path
        # Allow setup-related and static paths through
        if path in ("/setup", "/api/auth/setup", "/api/auth/setup-status") or path.startswith("/static/"):
            return await call_next(request)
        if path.startswith("/api/"):
            return JSONResponse({"detail": "Setup required"}, status_code=403)
        return RedirectResponse("/setup", status_code=302)

    if not requires_auth(request):
        return await call_next(request)

    # Check for Bearer token in Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            verify_token(token)
            return await call_next(request)
        except HTTPException:
            pass

    # Not authenticated
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    return RedirectResponse("/login", status_code=302)
