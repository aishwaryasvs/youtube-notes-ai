from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Notes:
    title: str
    summary: str
    key_points: list[str] = field(default_factory=list)
    detailed_notes: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TranscriptResult:
    text: str
    source: str
