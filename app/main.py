import os
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth import auth_middleware, credentials_configured
from app.routes import bots, auth as auth_routes, system as system_routes
from app.models.bot import Base, engine

logging.basicConfig(level=logging.INFO)

os.makedirs("bots", exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="Bot Hosting Panel", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

Base.metadata.create_all(bind=engine)

# Auth routes (login/logout) — mounted at root level
app.include_router(auth_routes.router, tags=["Auth"])
# Bot API routes
app.include_router(bots.router, prefix="/api/bots", tags=["Bots"])
# System actions API routes
app.include_router(system_routes.router, prefix="/api/system", tags=["System"])
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def index():
    if not credentials_configured():
        return RedirectResponse("/setup", status_code=302)
    return FileResponse("frontend/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}
