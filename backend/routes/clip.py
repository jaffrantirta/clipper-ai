import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from backend.models.job import Job, get_session
from backend.workers.tasks import process_video

router = APIRouter()


class ClipRequest(BaseModel):
    youtube_url: str
    aspect_ratio: str = "16:9"   # "16:9" | "9:16" | "1:1" | "4:3"
    min_duration: float = 5.0    # seconds
    max_duration: float = 60.0   # seconds
    add_subtitles: bool = False


@router.post("/clip")
def submit_clip(req: ClipRequest):
    job_id = str(uuid.uuid4())
    with get_session() as session:
        session.add(Job(id=job_id, youtube_url=req.youtube_url, status="queued", progress=0, clips=[]))
    options = {
        "aspect_ratio": req.aspect_ratio,
        "min_duration": req.min_duration,
        "max_duration": req.max_duration,
        "add_subtitles": req.add_subtitles,
    }
    process_video.delay(job_id, req.youtube_url, options)
    return {"job_id": job_id, "status": "queued"}
