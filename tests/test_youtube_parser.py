from __future__ import annotations

import pytest

from youtube_notes_ai.youtube_parser import extract_video_id


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/watch/?v=dQw4w9WgXcQ&feature=share", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("youtu.be/dQw4w9WgXcQ?t=43", "dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ&t=31", "dQw4w9WgXcQ"),
        ("https://music.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ?feature=share", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ?start=5", "dQw4w9WgXcQ"),
        ("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?rel=0", "dQw4w9WgXcQ"),
        ("dQw4w9WgXcQ", "dQw4w9WgXcQ"),
    ],
)
def test_extract_video_id_valid(input_value: str, expected: str) -> None:
    assert extract_video_id(input_value) == expected


@pytest.mark.parametrize(
    "input_value",
    [
        "https://example.com/not-youtube",
        "https://www.youtube.com/watch?v=invalid",
        "https://www.youtube.com/shorts/",
    ],
)
def test_extract_video_id_invalid(input_value: str) -> None:
    with pytest.raises(ValueError):
        extract_video_id(input_value)
