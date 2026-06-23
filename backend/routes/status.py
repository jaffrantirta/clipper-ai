from fastapi import APIRouter, HTTPException

from backend.models.job import Job, get_session

router = APIRouter()


@router.get("/status/{job_id}")
def get_status(job_id: str):
    with get_session() as session:
        job = session.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        return {
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "error": job.error,
            "clips": job.clips or [],
        }
