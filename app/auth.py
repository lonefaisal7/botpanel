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

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-to-a-random-secret")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    try:
        return bcrypt.verify(plain_password, hashed_password)
    except Exception:
        return False


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate admin user against .env credentials."""
    if not ADMIN_PASSWORD_HASH:
        return False
    if username != ADMIN_USERNAME:
        return False
    return verify_password(password, ADMIN_PASSWORD_HASH)


def create_access_token(username: str) -> str:
    """Create a JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> str:
    """Verify JWT token and return username. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
PUBLIC_PATHS = {"/login", "/api/auth/login", "/health", "/docs", "/openapi.json", "/redoc"}
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
    and redirects browser requests to /login."""
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
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)

    from fastapi.responses import RedirectResponse
    return RedirectResponse("/login", status_code=302)
