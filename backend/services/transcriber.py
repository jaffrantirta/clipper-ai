import logging
from pathlib import Path

from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

# "base" is multilingual (~145 MB), good balance of speed vs accuracy.
# Model is downloaded once and cached in /root/.cache/huggingface inside the container.
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        logger.info("Loading Whisper base model (first run downloads ~145 MB)")
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribe_audio(audio_path: Path) -> list[dict]:
    model = _get_model()
    logger.info("Transcribing %s", audio_path.name)

    segments_iter, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=True,
    )
    logger.info("Detected language: %s (%.0f%%)", info.language, info.language_probability * 100)

    segments = [
        {"start": seg.start, "end": seg.end, "text": seg.text.strip()}
        for seg in segments_iter
        if seg.text.strip()
    ]
    segments.sort(key=lambda s: s["start"])
    logger.info("Transcription: %d segments", len(segments))
    return segments
