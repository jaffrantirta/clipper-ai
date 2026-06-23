import logging

from backend.config import CLIP_BUFFER, FINAL_SCORE_THRESHOLD

logger = logging.getLogger(__name__)


def fuse_and_filter(
    scored_segments: list[dict],
    video_duration: float,
    min_duration: float = 5.0,
    max_duration: float = 60.0,
) -> list[dict]:
    candidates: list[dict] = []
    for seg in scored_segments:
        text_score = seg.get("text_score")
        audio_score = seg["audio_score"]
        if text_score is None:
            final_score = round(audio_score, 2)
        else:
            final_score = round(text_score * 0.60 + audio_score * 0.40, 2)
        if final_score >= FINAL_SCORE_THRESHOLD:
            candidates.append(
                {
                    "start": seg["start"],
                    "end": seg["end"],
                    "final_score": final_score,
                    "text_score": text_score,
                    "audio_score": audio_score,
                    "reason": seg["reason"],
                }
            )

    logger.info(
        "Fusion: %d/%d segments pass threshold %.1f",
        len(candidates), len(scored_segments), FINAL_SCORE_THRESHOLD,
    )

    if not candidates:
        return []

    # Add buffer and clamp to video bounds
    buffered = [
        {
            **c,
            "start": max(0.0, round(c["start"] - CLIP_BUFFER, 2)),
            "end": min(video_duration, round(c["end"] + CLIP_BUFFER, 2)),
        }
        for c in candidates
    ]

    # Sort then merge overlaps
    buffered.sort(key=lambda x: x["start"])
    merged: list[dict] = [buffered[0]]

    for seg in buffered[1:]:
        last = merged[-1]
        if seg["start"] <= last["end"]:
            if seg["final_score"] >= last["final_score"]:
                merged[-1] = {**seg, "start": last["start"], "end": max(last["end"], seg["end"])}
            else:
                merged[-1] = {**last, "end": max(last["end"], seg["end"])}
        else:
            merged.append(seg)

    # Enforce duration bounds
    result = []
    for seg in merged:
        dur = seg["end"] - seg["start"]
        if dur < min_duration:
            continue
        if dur > max_duration:
            seg = {**seg, "end": round(seg["start"] + max_duration, 2)}
        result.append(seg)

    logger.info(
        "After buffer + merge + duration filter [%.0f–%.0fs]: %d clips",
        min_duration, max_duration, len(result),
    )
    return result
