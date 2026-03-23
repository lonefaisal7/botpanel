from fastapi import APIRouter, Request, Form
from fastapi.responses import FileResponse, RedirectResponse
from app import auth

router = APIRouter()


@router.get("/login")
async def login_page(request: Request):
    if auth.get_current_user(request):
        return RedirectResponse("/", status_code=302)
    return FileResponse("frontend/login.html")


@router.post("/api/auth/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if not auth.verify_login(username, password):
        return RedirectResponse("/login?error=1", status_code=302)
    response = RedirectResponse("/", status_code=302)
    auth.create_session(response, username)
    return response


@router.get("/api/auth/logout")
async def logout():
    response = RedirectResponse("/login", status_code=302)
    auth.clear_session(response)
    return response
