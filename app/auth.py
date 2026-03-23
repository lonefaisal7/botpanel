"""
Authentication module for Bot Hosting Panel.

Stores bcrypt-hashed credentials in a JSON file.
Uses signed cookies (itsdangerous) for session management.
"""

import json, os, secrets, logging
import bcrypt as _bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, Response
from fastapi.responses import RedirectResponse, JSONResponse

log = logging.getLogger(__name__)

CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "credentials.json")
CREDENTIALS_FILE = os.path.normpath(CREDENTIALS_FILE)

SESSION_COOKIE = "bp_session"
SESSION_MAX_AGE = 86400 * 7  # 7 days

_serializer = None


def _get_serializer() -> URLSafeTimedSerializer:
    global _serializer
    if _serializer is None:
        creds = _load_credentials()
        _serializer = URLSafeTimedSerializer(creds["secret_key"])
    return _serializer


def _load_credentials() -> dict:
    if not os.path.isfile(CREDENTIALS_FILE):
        return {}
    with open(CREDENTIALS_FILE, "r") as f:
        return json.load(f)


def save_credentials(username: str, password: str):
    """Hash password and persist credentials + a random secret key."""
    secret_key = secrets.token_hex(32)
    pw_hash = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")
    data = {
        "username": username,
        "password_hash": pw_hash,
        "secret_key": secret_key,
    }
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(CREDENTIALS_FILE, 0o600)
    log.info("Credentials saved to %s", CREDENTIALS_FILE)


def is_configured() -> bool:
    """Return True if credentials file exists with required fields."""
    creds = _load_credentials()
    return bool(creds.get("username") and creds.get("password_hash") and creds.get("secret_key"))


def verify_login(username: str, password: str) -> bool:
    creds = _load_credentials()
    if not creds:
        return False
    if username != creds.get("username"):
        return False
    stored_hash = creds["password_hash"].encode("utf-8")
    return _bcrypt.checkpw(password.encode("utf-8"), stored_hash)


def create_session(response: Response, username: str):
    s = _get_serializer()
    token = s.dumps({"user": username})
    response.set_cookie(
        SESSION_COOKIE, token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
    )


def get_current_user(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        s = _get_serializer()
        data = s.loads(token, max_age=SESSION_MAX_AGE)
        return data.get("user")
    except (BadSignature, SignatureExpired):
        return None


def clear_session(response: Response):
    response.delete_cookie(SESSION_COOKIE)


# Paths that don't require authentication
PUBLIC_PATHS = {"/login", "/api/auth/login", "/health"}
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
    """Middleware that redirects unauthenticated requests to /login."""
    if not is_configured():
        # No credentials set — allow open access (first-run scenario)
        return await call_next(request)

    if not requires_auth(request):
        return await call_next(request)

    user = get_current_user(request)
    if user:
        return await call_next(request)

    # Not authenticated
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Not authenticated"}, status_code=401)
    return RedirectResponse("/login", status_code=302)
