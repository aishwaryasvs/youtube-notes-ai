from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

YOUTUBE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {"youtube.com", "m.youtube.com", "music.youtube.com"}
YOUTUBE_SHORT_HOSTS = {"youtu.be"}
YOUTUBE_EMBED_HOSTS = {"youtube-nocookie.com"}


def extract_video_id(url_or_id: str) -> str:
    """Extract a YouTube video ID from common URL formats or direct IDs."""
    candidate = url_or_id.strip()
    if YOUTUBE_ID_PATTERN.fullmatch(candidate):
        return candidate

    # Handle common scheme-less input like "youtu.be/VIDEO_ID".
    if "://" not in candidate and "." in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    host = parsed.netloc.lower().replace("www.", "").split(":")[0]
    path_parts = [part for part in parsed.path.split("/") if part]

    if host in YOUTUBE_HOSTS:
        if parsed.path.rstrip("/") == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
            if YOUTUBE_ID_PATTERN.fullmatch(video_id):
                return video_id

        if len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed"}:
            video_id = path_parts[1]
            if YOUTUBE_ID_PATTERN.fullmatch(video_id):
                return video_id

    if host in YOUTUBE_SHORT_HOSTS and path_parts:
        video_id = path_parts[0]
        if YOUTUBE_ID_PATTERN.fullmatch(video_id):
            return video_id

    if host in YOUTUBE_EMBED_HOSTS and len(path_parts) >= 2 and path_parts[0] == "embed":
        video_id = path_parts[1]
        if YOUTUBE_ID_PATTERN.fullmatch(video_id):
            return video_id

    raise ValueError("Invalid YouTube URL or video ID.")
