import logging
from pathlib import Path

import librosa
import numpy as np

from backend.config import AUDIO_SCORE_THRESHOLD, CALIBRATION, SEGMENT_DURATION

logger = logging.getLogger(__name__)


def _normalize(value: float, lo: float, hi: float) -> float:
    """Clamp-normalize value to 0–10."""
    if hi <= lo:
        return 5.0
    return float(np.clip((value - lo) / (hi - lo) * 10.0, 0.0, 10.0))


def analyze_audio(audio_path: Path) -> list[dict]:
    """
    Slide a SEGMENT_DURATION-second window over the audio track.
    Each window is scored by energy, spectral dynamism, and silence ratio.
    Returns only segments with audio_score >= AUDIO_SCORE_THRESHOLD.

    In CALIBRATION mode raw feature values are printed so the normalisation
    ranges can be tuned without redeploying.
    """
    logger.info("Loading audio for analysis: %s", audio_path.name)
    y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
    duration = librosa.get_duration(y=y, sr=sr)

    results: list[dict] = []
    t = 0.0

    while t < duration:
        seg_end = min(t + SEGMENT_DURATION, duration)
        segment = y[int(t * sr) : int(seg_end * sr)]

        if len(segment) < int(sr * 0.5):
            t = seg_end
            continue

        # ── Feature 1: RMS energy ──────────────────────────────────────────
        rms = librosa.feature.rms(y=segment, frame_length=2048, hop_length=512)[0]
        mean_rms = float(np.mean(rms))

        # ── Feature 2: Spectral centroid std (pitch / tonal dynamics) ──────
        centroid = librosa.feature.spectral_centroid(y=segment, sr=sr)[0]
        centroid_std = float(np.std(centroid))

        # ── Feature 3: Silence ratio ────────────────────────────────────────
        silence_ratio = float(np.mean(rms < 0.005))

        if CALIBRATION:
            print(
                f"[CALIBRATION] {t:.1f}–{seg_end:.1f}s | "
                f"rms={mean_rms:.6f} | centroid_std={centroid_std:.2f} | "
                f"silence={silence_ratio:.3f}"
            )

        # ── Normalise to 0–10 ───────────────────────────────────────────────
        # Typical RMS 0.001–0.12 → full score near 0.08+
        energy_score = _normalize(mean_rms, 0.001, 0.10)
        # Spectral centroid std 0–2500 Hz → full score near 1500+
        dynamics_score = _normalize(centroid_std, 0.0, 1500.0)
        # Less silence = higher score
        silence_score = (1.0 - silence_ratio) * 10.0

        audio_score = round(
            energy_score * 0.45 + dynamics_score * 0.30 + silence_score * 0.25,
            2,
        )

        if CALIBRATION:
            print(
                f"[CALIBRATION]   → energy={energy_score:.2f} "
                f"dynamics={dynamics_score:.2f} silence={silence_score:.2f} "
                f"→ audio_score={audio_score:.2f}"
            )

        results.append({"start": round(t, 2), "end": round(seg_end, 2), "audio_score": audio_score})
        t = seg_end

    passing = [r for r in results if r["audio_score"] >= AUDIO_SCORE_THRESHOLD]
    logger.info(
        "Audio analysis: %d/%d segments pass threshold %.1f",
        len(passing), len(results), AUDIO_SCORE_THRESHOLD,
    )
    return passing
