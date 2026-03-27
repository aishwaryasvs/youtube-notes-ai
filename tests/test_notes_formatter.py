from __future__ import annotations

from youtube_notes_ai.models import Notes
from youtube_notes_ai.notes_formatter import to_markdown


def test_to_markdown_formats_all_sections() -> None:
    notes = Notes(
        title="Test Video",
        summary="A concise summary.",
        key_points=["Point A", "Point B"],
        detailed_notes=["Detail 1", "Detail 2"],
        action_items=["Action 1"],
    )

    markdown = to_markdown(notes, source="youtube-transcript-api")

    assert "# Test Video" in markdown
    assert "## Summary" in markdown
    assert "- Point A" in markdown
    assert "## Detailed Notes" in markdown
    assert "## Action Items / Takeaways" in markdown
    assert "**Transcript Source:** youtube-transcript-api" in markdown


def test_to_markdown_handles_empty_lists() -> None:
    notes = Notes(title="Test", summary="Summary")
    markdown = to_markdown(notes, source="fallback")

    assert markdown.count("- None") == 3
