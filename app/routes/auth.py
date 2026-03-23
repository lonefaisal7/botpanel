from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from app import auth

router = APIRouter()


@router.get("/login")
async def login_page(request: Request):
    """Serve the login HTML page."""
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
