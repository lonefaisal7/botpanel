import json
import logging
import os
import shlex
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException

log = logging.getLogger(__name__)

JOB_ROOT = Path(tempfile.gettempdir()) / "botpanel-system-jobs"
JOB_ROOT.mkdir(parents=True, exist_ok=True)
ACTIVE_JOB_FILE = JOB_ROOT / "active_job"

UPDATE_SCRIPT = "/opt/botpanel/update.sh"
UNINSTALL_SCRIPT = "/opt/botpanel/uninstall.sh"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_meta_path(job_id: str) -> Path:
    return JOB_ROOT / f"{job_id}.json"


def _job_log_path(job_id: str) -> Path:
    return JOB_ROOT / f"{job_id}.log"


def _read_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, data: Dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)
    tmp.replace(path)


def _set_active_job(job_id: Optional[str]) -> None:
    if job_id:
        ACTIVE_JOB_FILE.write_text(job_id, encoding="utf-8")
    elif ACTIVE_JOB_FILE.exists():
        ACTIVE_JOB_FILE.unlink()


def _get_active_job_id() -> Optional[str]:
    if not ACTIVE_JOB_FILE.exists():
        return None
    job_id = ACTIVE_JOB_FILE.read_text(encoding="utf-8").strip()
    return job_id or None


def _is_systemd_available() -> bool:
    return bool(shutil.which("systemd-run") and shutil.which("systemctl"))


def _parse_key_value(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def _query_systemd_unit(unit_name: str) -> Tuple[str, Optional[int], Optional[str]]:
    proc = subprocess.run(
        [
            "systemctl",
            "show",
            unit_name,
            "--no-page",
            "--property=ActiveState",
            "--property=Result",
            "--property=ExecMainStatus",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return "failed", None, proc.stderr.strip() or "systemd unit not found"

    details = _parse_key_value(proc.stdout)
    active_state = details.get("ActiveState", "")
    result = details.get("Result", "")
    exit_code_raw = details.get("ExecMainStatus", "")
    exit_code = int(exit_code_raw) if exit_code_raw.isdigit() else None

    if active_state in {"active", "activating", "deactivating", "reloading"}:
        return "running", exit_code, None

    if active_state == "inactive":
        if result in {"success", ""} and (exit_code is None or exit_code == 0):
            return "success", exit_code or 0, None
        return "failed", exit_code, f"result={result or 'unknown'}"

    if active_state == "failed":
        return "failed", exit_code, f"result={result or 'failed'}"

    return "failed", exit_code, f"unexpected active_state={active_state or 'unknown'}"


def _query_pid(pid: int, log_path: Path) -> Tuple[str, Optional[int], Optional[str]]:
    try:
        os.kill(pid, 0)
        return "running", None, None
    except OSError:
        if not log_path.exists():
            return "failed", None, "job process exited without logs"

        marker = None
        for line in reversed(log_path.read_text(encoding="utf-8", errors="replace").splitlines()):
            if line.startswith("__EXIT_CODE__="):
                marker = line.split("=", 1)[1].strip()
                break

        if marker is None:
            return "failed", None, "job exited without exit marker"

        if marker.isdigit() and int(marker) == 0:
            return "success", 0, None

        code = int(marker) if marker.isdigit() else None
        return "failed", code, "non-zero exit code"


def _refresh_job_locked(meta: Dict) -> Dict:
    if meta.get("status") != "running":
        return meta

    mode = meta.get("launch_mode")
    if mode == "systemd":
        status, exit_code, error = _query_systemd_unit(meta["unit_name"])
    elif mode == "pid":
        pid = meta.get("pid")
        if not isinstance(pid, int):
            status, exit_code, error = "failed", None, "missing pid"
        else:
            status, exit_code, error = _query_pid(pid, Path(meta["log_path"]))
    else:
        status, exit_code, error = "failed", None, "unknown launch mode"

    if status == "running":
        return meta

    meta["status"] = status
    meta["finished_at"] = _now_iso()
    meta["exit_code"] = exit_code
    meta["error"] = error
    _write_json(_job_meta_path(meta["job_id"]), meta)

    active_job_id = _get_active_job_id()
    if active_job_id == meta["job_id"]:
        _set_active_job(None)

    return meta


def _get_job_meta(job_id: str, refresh: bool = True) -> Dict:
    path = _job_meta_path(job_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    meta = _read_json(path)
    if refresh:
        meta = _refresh_job_locked(meta)
    return meta


def _get_active_running_job() -> Optional[Dict]:
    active_job_id = _get_active_job_id()
    if not active_job_id:
        return None

    try:
        meta = _get_job_meta(active_job_id, refresh=True)
    except HTTPException:
        _set_active_job(None)
        return None

    if meta.get("status") == "running":
        return meta

    _set_active_job(None)
    return None


def _start_with_systemd(meta: Dict, cmd_parts: List[str]) -> None:
    shell_cmd = " ".join(shlex.quote(part) for part in cmd_parts)
    log_path = shlex.quote(meta["log_path"])
    wrapper = f"{shell_cmd} >> {log_path} 2>&1"

    proc = subprocess.run(
        [
            "systemd-run",
            "--unit",
            meta["unit_name"],
            "--property=Type=oneshot",
            "/bin/bash",
            "-lc",
            wrapper,
        ],
        capture_output=True,
        text=True,
    )

    if proc.returncode != 0:
        meta["status"] = "failed"
        meta["finished_at"] = _now_iso()
        meta["error"] = proc.stderr.strip() or "failed to start transient unit"
        _write_json(_job_meta_path(meta["job_id"]), meta)
        _set_active_job(None)
        raise HTTPException(status_code=500, detail=meta["error"])


def _start_with_pid(meta: Dict, cmd_parts: List[str]) -> None:
    quoted = " ".join(shlex.quote(part) for part in cmd_parts)
    wrapper = (
        f"{quoted} >> {shlex.quote(meta['log_path'])} 2>&1; "
        "ec=$?; echo __EXIT_CODE__=$ec >> "
        f"{shlex.quote(meta['log_path'])}; exit $ec"
    )

    log_handle = open(meta["log_path"], "a", encoding="utf-8")
    proc = subprocess.Popen(  # noqa: S603
        ["/bin/bash", "-lc", wrapper],
        stdout=log_handle,
        stderr=log_handle,
        start_new_session=True,
    )
    log_handle.close()
    meta["pid"] = proc.pid


def _start_job(action: str, cmd_parts: List[str]) -> Dict:
    running = _get_active_running_job()
    if running:
        raise HTTPException(
            status_code=409,
            detail=f"Another panel action is already running ({running.get('action')})",
        )

    for part in cmd_parts:
        if part.endswith(".sh") and not Path(part).exists():
            raise HTTPException(status_code=500, detail=f"Script not found: {part}")

    job_id = uuid.uuid4().hex
    log_path = _job_log_path(job_id)
    unit_name = f"botpanel-{action}-{job_id[:8]}"

    meta = {
        "job_id": job_id,
        "action": action,
        "status": "running",
        "created_at": _now_iso(),
        "started_at": _now_iso(),
        "finished_at": None,
        "exit_code": None,
        "error": None,
        "unit_name": unit_name,
        "pid": None,
        "launch_mode": "systemd" if _is_systemd_available() else "pid",
        "log_path": str(log_path),
    }

    _write_json(_job_meta_path(job_id), meta)
    _set_active_job(job_id)

    log_path.write_text(f"[{_now_iso()}] Starting {action} action\n", encoding="utf-8")

    if meta["launch_mode"] == "systemd":
        _start_with_systemd(meta, cmd_parts)
    else:
        _start_with_pid(meta, cmd_parts)
        _write_json(_job_meta_path(job_id), meta)

    return _get_job_meta(job_id, refresh=True)


def start_update_job() -> Dict:
    return _start_job("update", ["bash", UPDATE_SCRIPT])


def start_uninstall_job() -> Dict:
    return _start_job("uninstall", ["bash", UNINSTALL_SCRIPT, "--yes"])


def get_job_status(job_id: str) -> Dict:
    meta = _get_job_meta(job_id, refresh=True)
    return {
        "job_id": meta["job_id"],
        "action": meta["action"],
        "status": meta["status"],
        "created_at": meta["created_at"],
        "started_at": meta["started_at"],
        "finished_at": meta.get("finished_at"),
        "exit_code": meta.get("exit_code"),
        "error": meta.get("error"),
    }


def _tail_lines(path: Path, max_lines: int = 200) -> str:
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-max_lines:])


def get_job_logs(job_id: str, max_lines: int = 200) -> Dict:
    meta = _get_job_meta(job_id, refresh=True)
    logs = _tail_lines(Path(meta["log_path"]), max_lines=max_lines)
    return {
        "job_id": job_id,
        "action": meta["action"],
        "status": meta["status"],
        "logs": logs,
    }
