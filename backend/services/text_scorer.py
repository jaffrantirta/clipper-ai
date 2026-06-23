import json
import logging

from openai import OpenAI

from backend.config import TOKENROUTER_API_KEY, TOKENROUTER_BASE_URL

logger = logging.getLogger(__name__)

_client: OpenAI | None = None

_PROMPT = """\
You are a YouTube clip-worthiness scorer. Given a transcript segment, score how
memorable or engaging it is as a standalone clip.

High scores (8–10): key insight, surprising fact, strong emotion, quotable line,
  clear punchline, or moment that stands alone without prior context.
Medium scores (5–7): somewhat interesting but needs context, or generic filler.
Low scores (1–4): silence, transition phrases, off-topic tangent.

Return ONLY valid JSON, no markdown, no extra text:
{"score": <integer 1-10>, "reason": "<one sentence>"}

Transcript:
{text}"""


def _client_instance() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=TOKENROUTER_API_KEY, base_url=TOKENROUTER_BASE_URL)
    return _client


def score_segments(
    transcript_segments: list[dict],
    audio_segments: list[dict],
) -> list[dict]:
    """
    For each audio segment that passed the pre-filter, collect overlapping
    transcript text and score it via TokenRouter / gpt-4o-mini.

    Returns [{start, end, audio_score, text_score, reason, text}, ...]
    """
    client = _client_instance()
    results: list[dict] = []

    for audio_seg in audio_segments:
        a_start, a_end = audio_seg["start"], audio_seg["end"]

        # Gather all transcript text overlapping this window
        texts = [
            t["text"]
            for t in transcript_segments
            if t["end"] > a_start and t["start"] < a_end and t["text"]
        ]
        text = " ".join(texts).strip()

        if not text:
            logger.debug("No transcript for %.1f–%.1f, skipping LLM", a_start, a_end)
            continue

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=120,
                messages=[{"role": "user", "content": _PROMPT.format(text=text)}],
            )
            raw = (resp.choices[0].message.content or "").strip()
            logger.debug("LLM raw response for %.1f–%.1f: %s", a_start, a_end, raw)

            # Strip markdown code fences if present
            if "```" in raw:
                parts = raw.split("```")
                for part in parts:
                    part = part.lstrip("json").strip()
                    if part.startswith("{"):
                        raw = part
                        break

            # Extract the first JSON object from the response
            start_idx = raw.find("{")
            end_idx = raw.rfind("}") + 1
            if start_idx != -1 and end_idx > start_idx:
                raw = raw[start_idx:end_idx]

            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise ValueError(f"Expected dict, got {type(parsed).__name__}: {parsed}")
            text_score = float(parsed["score"])
            reason = str(parsed.get("reason", ""))
        except Exception as exc:
            logger.warning("LLM scoring failed for %.1f–%.1f: %s | raw=%r", a_start, a_end, exc, locals().get("raw", ""))
            text_score = None  # signals fusion to fall back to audio-only scoring
            reason = "scoring unavailable"

        results.append(
            {
                "start": a_start,
                "end": a_end,
                "audio_score": audio_seg["audio_score"],
                "text_score": text_score,
                "reason": reason,
                "text": text,
            }
        )

    logger.info("Text scored %d segments", len(results))
    return results
