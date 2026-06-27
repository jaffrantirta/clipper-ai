import logging
import subprocess
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# FFmpeg crop expressions for each aspect ratio (center crop, even dimensions)
_AR_CROP = {
    "9:16": "crop=trunc(ih*9/16/2)*2:ih",
    "1:1":  "crop=trunc(ih/2)*2:trunc(ih/2)*2",
    "4:3":  "crop=trunc(ih*4/3/2)*2:ih",
}

# ASS colour format: &HAABBGGRR&  (AA=alpha 00=opaque, BGR not RGB)
_SUBTITLE_STYLES: dict[str, str] = {
    "default": (
        "FontSize=20,Alignment=2,"
        "PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H00000000&,"
        "Outline=2,Bold=1,MarginV=25"
    ),
    "bold": (
        "FontSize=26,Alignment=2,"
        "PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H00000000&,"
        "Outline=3,Bold=1,MarginV=20"
    ),
    "minimal": (
        "FontSize=15,Alignment=2,"
        "PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H00000000&,"
        "Outline=1,Bold=0,MarginV=15"
    ),
}


def get_video_duration(video_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def _srt_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round(seconds % 1, 3) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _write_srt(
    srt_path: Path,
    transcript_segments: list[dict],
    clip_start: float,
    clip_end: float,
) -> bool:
    """Write an SRT file with timestamps relative to clip_start. Returns True if non-empty."""
    lines = []
    idx = 1
    for seg in transcript_segments:
        if seg["end"] <= clip_start or seg["start"] >= clip_end:
            continue
        rel_start = max(0.0, seg["start"] - clip_start)
        rel_end = min(clip_end - clip_start, seg["end"] - clip_start)
        if rel_end <= rel_start or not seg.get("text"):
            continue
        lines.append(str(idx))
        lines.append(f"{_srt_timestamp(rel_start)} --> {_srt_timestamp(rel_end)}")
        lines.append(seg["text"].strip())
        lines.append("")
        idx += 1
    if not lines:
        return False
    srt_path.write_text("\n".join(lines), encoding="utf-8")
    return True


def cut_clips(
    video_path: Path,
    segments: list[dict],
    output_dir: Path,
    aspect_ratio: str = "16:9",
    add_subtitles: bool = False,
    subtitle_style: str = "default",
    transcript_segments: list[dict] | None = None,
) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    job_id = output_dir.name
    clips: list[dict] = []

    crop_filter = _AR_CROP.get(aspect_ratio)  # None means no crop

    for seg in segments:
        clip_id = str(uuid.uuid4())
        clip_file = f"{clip_id}.mp4"
        thumb_file = f"{clip_id}.jpg"
        clip_path = output_dir / clip_file
        thumb_path = output_dir / thumb_file
        srt_path = output_dir / f"{clip_id}.srt"
        duration = round(seg["end"] - seg["start"], 2)

        logger.info("Cutting %s: %.2f–%.2f s | ar=%s subtitles=%s",
                    clip_id, seg["start"], seg["end"], aspect_ratio, add_subtitles)

        # Build -vf filter chain
        vf_parts: list[str] = []
        if crop_filter:
            vf_parts.append(crop_filter)

        srt_kept = False
        if add_subtitles and transcript_segments:
            has_subs = _write_srt(srt_path, transcript_segments, seg["start"], seg["end"])
            if has_subs:
                style = _SUBTITLE_STYLES.get(subtitle_style, _SUBTITLE_STYLES["default"])
                safe_path = str(srt_path).replace("'", "\\'")
                vf_parts.append(f"subtitles='{safe_path}':force_style='{style}'")
                srt_kept = True

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-ss", str(seg["start"]),
            "-t", str(duration),
        ]
        if vf_parts:
            ffmpeg_cmd += ["-vf", ",".join(vf_parts)]
        ffmpeg_cmd += [
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(clip_path),
        ]

        try:
            result = subprocess.run(ffmpeg_cmd, capture_output=True, check=False)
            if result.returncode != 0:
                logger.error("FFmpeg failed for clip %s: %s", clip_id, result.stderr.decode())
                continue

            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", str(clip_path),
                    "-frames:v", "1",
                    "-q:v", "2",
                    str(thumb_path),
                ],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.error("FFmpeg failed for clip %s: %s", clip_id, exc.stderr)
            if srt_path.exists():
                srt_path.unlink(missing_ok=True)
            continue

        clip_data: dict = {
            "clip_id": clip_id,
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "duration": duration,
            "score": seg["final_score"],
            "reason": seg["reason"],
            "download_url": f"/clips/{job_id}/{clip_file}",
            "thumbnail_url": f"/clips/{job_id}/{thumb_file}",
        }
        if srt_kept:
            clip_data["subtitle_url"] = f"/clips/{job_id}/{clip_id}.srt"
        clips.append(clip_data)

    logger.info("Cut %d clips for job %s", len(clips), job_id)
    return clips
