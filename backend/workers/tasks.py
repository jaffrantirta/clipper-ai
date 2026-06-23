import logging

from celery import Celery

from backend.config import REDIS_URL, STORAGE_PATH
from backend.models.job import update_job

logger = logging.getLogger(__name__)

celery_app = Celery("clipper", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(bind=True, max_retries=0, name="tasks.process_video")
def process_video(self, job_id: str, youtube_url: str, options: dict | None = None) -> None:
    from backend.services.audio_analyzer import analyze_audio
    from backend.services.clipper import cut_clips, get_video_duration
    from backend.services.downloader import download_video
    from backend.services.fusion import fuse_and_filter
    from backend.services.text_scorer import score_segments
    from backend.services.transcriber import transcribe_audio

    options = options or {}
    job_dir = STORAGE_PATH / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    try:
        # ── Stage 1: Download ──────────────────────────────────────────────
        update_job(job_id, status="downloading", progress=10)
        video_path, audio_path = download_video(youtube_url, job_dir)

        # ── Stage 2: Transcribe ────────────────────────────────────────────
        update_job(job_id, status="transcribing", progress=30)
        transcript_segments = transcribe_audio(audio_path)

        # ── Stage 3: Audio analysis (pre-filter, free) ────────────────────
        update_job(job_id, status="analyzing", progress=50)
        audio_segments = analyze_audio(audio_path)

        # ── Stage 4: LLM text scoring (only filtered segments) ────────────
        update_job(job_id, status="scoring", progress=70)
        scored = score_segments(transcript_segments, audio_segments)

        # ── Stage 5: Fuse scores + cut clips ─────────────────────────────
        update_job(job_id, status="cutting", progress=90)
        video_duration = get_video_duration(video_path)
        final_segments = fuse_and_filter(
            scored,
            video_duration,
            min_duration=options.get("min_duration", 5.0),
            max_duration=options.get("max_duration", 60.0),
        )
        clips = cut_clips(
            video_path,
            final_segments,
            job_dir,
            aspect_ratio=options.get("aspect_ratio", "16:9"),
            add_subtitles=options.get("add_subtitles", False),
            transcript_segments=transcript_segments,
        )

        # ── Done ──────────────────────────────────────────────────────────
        update_job(job_id, status="completed", progress=100, clips=clips)
        logger.info("Job %s completed — %d clips", job_id, len(clips))

    except Exception as exc:
        logger.exception("Job %s failed: %s", job_id, exc)
        update_job(job_id, status="failed", progress=0, error=str(exc))
        raise
