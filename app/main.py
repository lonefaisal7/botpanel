import os, logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routes import bots
from app.models.bot import Base, engine

logging.basicConfig(level=logging.INFO)

os.makedirs("bots",    exist_ok=True)
os.makedirs("uploads", exist_ok=True)

app = FastAPI(title="Bot Hosting Panel", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(bots.router, prefix="/api/bots", tags=["Bots"])
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/")
async def index():
    return FileResponse("frontend/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}
