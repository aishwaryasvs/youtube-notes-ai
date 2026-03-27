from __future__ import annotations

from .models import Notes


def _section_list(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def to_markdown(notes: Notes, source: str) -> str:
    return "\n".join(
        [
            f"# {notes.title}",
            "",
            f"**Transcript Source:** {source}",
            "",
            "## Summary",
            notes.summary or "No summary generated.",
            "",
            "## Key Points",
            _section_list(notes.key_points),
            "",
            "## Detailed Notes",
            _section_list(notes.detailed_notes),
            "",
            "## Action Items / Takeaways",
            _section_list(notes.action_items),
            "",
        ]
    ).strip() + "\n"
