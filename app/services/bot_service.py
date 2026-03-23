import os, uuid, shutil, zipfile, logging
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models.bot import Bot
from app.services import docker_service

log = logging.getLogger(__name__)

BOTS_DIR   = os.path.abspath("bots")
MAX_SIZE   = 50 * 1024 * 1024          # 50 MB
ALLOWED_EXT = {".zip", ".py"}


def _safe_path(base: str, filename: str) -> str:
    """Prevent path traversal."""
    target = os.path.realpath(os.path.join(base, filename))
    if not target.startswith(os.path.realpath(base)):
        raise HTTPException(400, "Invalid file path.")
    return target


def _find_entry(bot_dir: str) -> str:
    for name in ("bot.py", "main.py"):
        if os.path.isfile(os.path.join(bot_dir, name)):
            return name
    py_files = [f for f in os.listdir(bot_dir) if f.endswith(".py")]
    if py_files:
        return py_files[0]
    raise HTTPException(422, "No Python entry file found in upload.")


def _write_dockerfile(bot_dir: str, entry_file: str):
    has_req = os.path.isfile(os.path.join(bot_dir, "requirements.txt"))
    install_line = (
        "RUN pip install --no-cache-dir -r requirements.txt"
        if has_req else "# No requirements.txt found"
    )
    content = f"""FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --upgrade pip
{install_line}
CMD ["python", "-u", "{entry_file}"]
"""
    with open(os.path.join(bot_dir, "Dockerfile"), "w") as fh:
        fh.write(content)


async def upload_bot(file: UploadFile, bot_name: str, db: Session) -> dict:
    # Validate name
    bot_name = bot_name.strip()
    if not bot_name or len(bot_name) > 60:
        raise HTTPException(400, "Bot name must be 1-60 characters.")
    if db.query(Bot).filter(Bot.name == bot_name).first():
        raise HTTPException(409, f"A bot named '{bot_name}' already exists.")

    # Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "Only .zip or .py files are allowed.")

    # Read & size-check
    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(413, "File exceeds 50 MB limit.")

    bot_id  = str(uuid.uuid4())
    bot_dir = os.path.join(BOTS_DIR, bot_id)
    os.makedirs(bot_dir, exist_ok=True)

    try:
        if ext == ".zip":
            tmp_zip = os.path.join(bot_dir, "upload.zip")
            with open(tmp_zip, "wb") as fh:
                fh.write(data)
            with zipfile.ZipFile(tmp_zip, "r") as zf:
                # Prevent zip-slip
                for member in zf.namelist():
                    _safe_path(bot_dir, member)
                zf.extractall(bot_dir)
            os.remove(tmp_zip)
            # Flatten single-directory zips
            entries = os.listdir(bot_dir)
            if len(entries) == 1 and os.path.isdir(sub := os.path.join(bot_dir, entries[0])):
                for item in os.listdir(sub):
                    shutil.move(os.path.join(sub, item), bot_dir)
                os.rmdir(sub)
        else:
            with open(os.path.join(bot_dir, file.filename), "wb") as fh:
                fh.write(data)

        entry_file = _find_entry(bot_dir)
        _write_dockerfile(bot_dir, entry_file)

        # Build Docker image
        image_tag = docker_service.build_image(bot_id, bot_dir)

        # Persist to DB
        bot = Bot(id=bot_id, name=bot_name, entry_file=entry_file,
                  image_id=image_tag, status="stopped")
        db.add(bot)
        db.commit()
        db.refresh(bot)
        return {"id": bot.id, "name": bot.name, "status": bot.status,
                "entry_file": bot.entry_file}

    except HTTPException:
        shutil.rmtree(bot_dir, ignore_errors=True)
        raise
    except Exception as exc:
        shutil.rmtree(bot_dir, ignore_errors=True)
        log.exception("Upload failed")
        raise HTTPException(500, f"Upload/build failed: {exc}")


def list_bots(db: Session) -> list:
    bots = db.query(Bot).all()
    result = []
    for b in bots:
        live_status = b.status
        if b.container_id:
            live_status = docker_service.get_status(b.container_id)
            if b.status != live_status:
                b.status = live_status
                db.commit()
        result.append({
            "id": b.id, "name": b.name, "status": live_status,
            "container_id": b.container_id, "entry_file": b.entry_file,
            "created_at": str(b.created_at),
        })
    return result


def _get_bot(bot_id: str, db: Session) -> Bot:
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(404, "Bot not found.")
    return bot


def start_bot(bot_id: str, db: Session) -> dict:
    bot = _get_bot(bot_id, db)
    if bot.container_id:
        ok = docker_service.start_container(bot.container_id)
        if not ok:
            # Container gone — run fresh
            bot.container_id = None
    if not bot.container_id:
        if not bot.image_id:
            raise HTTPException(409, "No Docker image found. Re-upload the bot.")
        cid = docker_service.run_container(bot_id, bot.image_id)
        bot.container_id = cid
    bot.status = "running"
    db.commit()
    return {"status": "running", "container_id": bot.container_id}


def stop_bot(bot_id: str, db: Session) -> dict:
    bot = _get_bot(bot_id, db)
    if bot.container_id:
        docker_service.stop_container(bot.container_id)
    bot.status = "stopped"
    db.commit()
    return {"status": "stopped"}


def restart_bot(bot_id: str, db: Session) -> dict:
    bot = _get_bot(bot_id, db)
    if bot.container_id:
        docker_service.restart_container(bot.container_id)
        bot.status = "running"
        db.commit()
        return {"status": "running"}
    return start_bot(bot_id, db)


def delete_bot(bot_id: str, db: Session) -> dict:
    bot = _get_bot(bot_id, db)
    if bot.container_id:
        docker_service.remove_container(bot.container_id)
    docker_service.remove_image(bot_id)
    bot_dir = os.path.join(BOTS_DIR, bot_id)
    shutil.rmtree(bot_dir, ignore_errors=True)
    db.delete(bot)
    db.commit()
    return {"deleted": True}


def get_logs(bot_id: str, db: Session) -> dict:
    bot = _get_bot(bot_id, db)
    if not bot.container_id:
        return {"logs": "Bot has never been started."}
    return {"logs": docker_service.get_logs(bot.container_id)}
