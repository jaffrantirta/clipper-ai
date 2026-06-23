import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TOKENROUTER_API_KEY: str = os.getenv("TOKENROUTER_API_KEY", "")
TOKENROUTER_BASE_URL: str = os.getenv("TOKENROUTER_BASE_URL", "https://api.tokenrouter.io/v1")
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://clipper:clipper@localhost:5432/clipperai")
STORAGE_PATH: Path = Path(os.getenv("STORAGE_PATH", "./storage/clips"))
CALIBRATION: bool = os.getenv("CALIBRATION", "false").lower() == "true"

SEGMENT_DURATION: int = 5          # seconds per audio window
AUDIO_SCORE_THRESHOLD: float = 5.0
FINAL_SCORE_THRESHOLD: float = 7.0
CLIP_BUFFER: float = 1.5           # seconds added before/after each clip
