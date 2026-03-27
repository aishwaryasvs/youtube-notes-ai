from __future__ import annotations

from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi


class TranscriptUnavailableError(RuntimeError):
    pass


def _normalize_segments(items: Any) -> str:
    lines: list[str] = []
    for item in items:
        if isinstance(item, dict):
            text = item.get("text", "")
        else:
            text = getattr(item, "text", "")
        text = (text or "").strip()
        if text:
            lines.append(text)
    return "\n".join(lines).strip()


def fetch_transcript(video_id: str) -> str:
    """Fetch transcript text from YouTube directly via transcript API."""
    try:
        if hasattr(YouTubeTranscriptApi, "get_transcript"):
            segments = YouTubeTranscriptApi.get_transcript(video_id)
        else:
            api = YouTubeTranscriptApi()
            segments = api.fetch(video_id)

        text = _normalize_segments(segments)
        if not text:
            raise TranscriptUnavailableError("Transcript exists but contains no text.")
        return text
    except Exception as exc:  # noqa: BLE001
        raise TranscriptUnavailableError("Transcript unavailable via youtube-transcript-api.") from exc
