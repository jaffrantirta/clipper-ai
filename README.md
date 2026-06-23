# Clipper AI

AI-powered YouTube video clipper. Submit a URL → the system downloads, transcribes, scores every segment with a local audio model + GPT-4o-mini, and cuts the best moments into downloadable MP4 clips.

## Architecture

```
YouTube URL
    │
    ▼
[yt-dlp] ──────────────────► source.mp4 + audio.wav
    │
    ▼
[Whisper API] ─────────────► transcript segments [{start, end, text}]
    │
    ▼
[librosa — free, local] ───► audio_score per 5-second window
    │  (filters ~60% of segments before LLM)
    ▼
[GPT-4o-mini via TokenRouter] ► text_score + reason per segment
    │
    ▼
[Fusion layer]
  final_score = text_score × 0.60 + audio_score × 0.40
  keep segments with final_score ≥ 7
    │
    ▼
[FFmpeg] ──────────────────► clip_{id}.mp4 + thumbnail
```

## Prerequisites

- Docker & Docker Compose v2
- `ffmpeg` and `ffprobe` (only needed for local dev without Docker)
- Python 3.11 (only needed for local dev)
- Node.js 20 (only needed for local dev)

## Quick Start (Docker)

```bash
# 1. Clone and enter project
cd clipper-ai

# 2. Copy and fill env file
cp .env.example .env
# Edit .env and set OPENAI_API_KEY and TOKENROUTER_API_KEY

# 3. Start everything
docker compose up --build

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Local Development (no Docker)

### Backend

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env
# Edit .env with your keys and point DATABASE_URL/REDIS_URL to local services

# Run Postgres and Redis (e.g. via Homebrew or native install)
# Then:

# Start FastAPI
uvicorn backend.main:app --reload

# In a second terminal, start the Celery worker
celery -A backend.workers.tasks.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI key used for Whisper transcription |
| `TOKENROUTER_API_KEY` | TokenRouter key for GPT-4o-mini scoring |
| `TOKENROUTER_BASE_URL` | TokenRouter base URL (default: `https://api.tokenrouter.io/v1`) |
| `REDIS_URL` | Celery broker + result backend |
| `DATABASE_URL` | PostgreSQL connection string |
| `STORAGE_PATH` | Directory where clips are stored (default: `./storage/clips`) |
| `CALIBRATION` | Set to `true` to print raw librosa features for threshold tuning |

## API Reference

### `POST /api/clip`
Submit a YouTube URL for processing.
```json
{ "youtube_url": "https://youtube.com/watch?v=..." }
```
Response:
```json
{ "job_id": "uuid", "status": "queued" }
```

### `GET /api/status/{job_id}`
Poll job status (every 3 seconds from the frontend).
```json
{
  "job_id": "uuid",
  "status": "analyzing",
  "progress": 50,
  "error": null,
  "clips": []
}
```
Status values: `queued → downloading → transcribing → analyzing → scoring → cutting → completed` (or `failed`).

### `GET /clips/{job_id}/{clip_id}.mp4`
Download a clip directly (served as a static file by FastAPI).

## Tuning

Set `CALIBRATION=true` and process a video to see raw librosa values printed in the worker log. Adjust the normalisation ranges in `backend/services/audio_analyzer.py` (`_normalize` calls) to match your content type:
- Talk shows: lower energy thresholds
- Music / action: raise spectral centroid range

Change `AUDIO_SCORE_THRESHOLD` (default 5) and `FINAL_SCORE_THRESHOLD` (default 7) in `backend/config.py` to get more or fewer clips.

## Storage

Clips are saved to `STORAGE_PATH/{job_id}/`:
- `source.mp4` — original download
- `audio.wav` — extracted mono audio
- `{clip_id}.mp4` — each clip
- `{clip_id}.jpg` — thumbnail (first frame)

Old jobs are not automatically deleted — add a cron or `DELETE /api/jobs/{job_id}` endpoint if needed.
