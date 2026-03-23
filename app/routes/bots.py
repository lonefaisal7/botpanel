from fastapi import APIRouter, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session
from app.models.bot import get_db
from app.services import bot_service

router = APIRouter()


@router.post("/upload")
async def upload_bot(
    file: UploadFile = File(...),
    bot_name: str    = Form(...),
    db: Session      = Depends(get_db),
):
    return await bot_service.upload_bot(file, bot_name, db)


@router.get("/list")
def list_bots(db: Session = Depends(get_db)):
    return bot_service.list_bots(db)


@router.post("/{bot_id}/start")
def start_bot(bot_id: str, db: Session = Depends(get_db)):
    return bot_service.start_bot(bot_id, db)


@router.post("/{bot_id}/stop")
def stop_bot(bot_id: str, db: Session = Depends(get_db)):
    return bot_service.stop_bot(bot_id, db)


@router.post("/{bot_id}/restart")
def restart_bot(bot_id: str, db: Session = Depends(get_db)):
    return bot_service.restart_bot(bot_id, db)


@router.delete("/{bot_id}")
def delete_bot(bot_id: str, db: Session = Depends(get_db)):
    return bot_service.delete_bot(bot_id, db)


@router.get("/{bot_id}/logs")
def get_logs(bot_id: str, db: Session = Depends(get_db)):
    return bot_service.get_logs(bot_id, db)
