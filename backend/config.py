import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Core ──────────────────────────────────────────────────────────────────────
TOKENROUTER_API_KEY: str = os.getenv("TOKENROUTER_API_KEY", "")
TOKENROUTER_BASE_URL: str = os.getenv("TOKENROUTER_BASE_URL", "https://api.tokenrouter.io/v1")
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://clipper:clipper@localhost:5432/clipperai")
CALIBRATION: bool = os.getenv("CALIBRATION", "false").lower() == "true"

# ── Storage ───────────────────────────────────────────────────────────────────
# STORAGE_PROVIDER: "local" | "s3" | "gcs"
STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local").lower()

# Local storage — used as working dir for all providers (temp dir for cloud)
STORAGE_PATH: Path = Path(os.getenv("STORAGE_PATH", "./storage/clips"))

# S3 / S3-compatible (AWS, Cloudflare R2, MinIO, Wasabi, DigitalOcean Spaces, etc.)
S3_BUCKET: str = os.getenv("S3_BUCKET", "")
S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "")   # leave empty for standard AWS
S3_PUBLIC_URL: str = os.getenv("S3_PUBLIC_URL", "")        # public base URL (e.g. R2 custom domain)
S3_ACL: str = os.getenv("S3_ACL", "public-read")           # set "" to disable ACL (required for R2)
AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")

# Google Cloud Storage
GCS_BUCKET: str = os.getenv("GCS_BUCKET", "")
# Set GOOGLE_APPLICATION_CREDENTIALS env var to your service account JSON path

# ── Clip tuning ───────────────────────────────────────────────────────────────
SEGMENT_DURATION: int = 5          # seconds per audio window
AUDIO_SCORE_THRESHOLD: float = 5.0
FINAL_SCORE_THRESHOLD: float = 7.0
CLIP_BUFFER: float = 1.5           # seconds added before/after each clip
