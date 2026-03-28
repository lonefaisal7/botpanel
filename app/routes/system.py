from fastapi import APIRouter

from app.services import system_service

router = APIRouter()


@router.post("/update")
def start_update():
    job = system_service.start_update_job()
    return {
        "job_id": job["job_id"],
        "action": job["action"],
        "status": job["status"],
    }


@router.post("/uninstall")
def start_uninstall():
    job = system_service.start_uninstall_job()
    return {
        "job_id": job["job_id"],
        "action": job["action"],
        "status": job["status"],
    }


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    return system_service.get_job_status(job_id)


@router.get("/jobs/{job_id}/logs")
def get_job_logs(job_id: str):
    return system_service.get_job_logs(job_id)
