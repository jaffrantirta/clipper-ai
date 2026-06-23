import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def download_video(youtube_url: str, output_dir: Path) -> tuple[Path, Path]:
    """
    Download YouTube video and extract a mono WAV for audio analysis.
    Returns (video_path, audio_path).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    video_tmpl = str(output_dir / "source.%(ext)s")
    audio_path = output_dir / "audio.wav"

    logger.info("Downloading: %s", youtube_url)
    result = subprocess.run(
        [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", video_tmpl,
            "--no-playlist",
            "--js-runtimes", "node",
            youtube_url,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        logger.error("yt-dlp stderr: %s", result.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)

    video_path = output_dir / "source.mp4"
    if not video_path.exists():
        candidates = sorted(output_dir.glob("source.*"))
        if not candidates:
            raise FileNotFoundError("yt-dlp produced no video file")
        video_path = candidates[0]

    logger.info("Extracting audio WAV")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vn", "-ac", "1", "-ar", "22050",
            "-f", "wav", str(audio_path),
        ],
        capture_output=True,
        check=True,
    )

    return video_path, audio_path
