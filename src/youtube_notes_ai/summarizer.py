from __future__ import annotations

import json
from typing import Any

import requests

from .models import Notes


class SummarizationError(RuntimeError):
    pass


class OllamaSummarizer:
    def __init__(
        self,
        model: str = "llama3.1:8b",
        base_url: str = "http://localhost:11434",
        max_transcript_chars: int = 18000,
        num_predict: int = 700,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_transcript_chars = max_transcript_chars
        self.num_predict = num_predict

    def summarize(self, transcript: str) -> Notes:
        if not transcript.strip():
            raise SummarizationError("Transcript is empty.")

        prompt = self._build_prompt(transcript)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2,
                "num_predict": self.num_predict,
                "num_ctx": 4096,
            },
        }

        try:
            response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=180)
            response.raise_for_status()
            body = response.json()
            content = body.get("response", "").strip()
            parsed = json.loads(content)
            return self._to_notes(parsed)
        except requests.RequestException as exc:
            raise SummarizationError(
                "Could not reach Ollama. Ensure Ollama is running on localhost and the model is installed."
            ) from exc
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise SummarizationError("Ollama returned an invalid summary format.") from exc

    def _build_prompt(self, transcript: str) -> str:
        trimmed = self._condense_transcript(transcript)
        return (
            "You are a note-taking assistant. Read the transcript and return ONLY valid JSON "
            "with this exact schema: "
            '{"title": string, "summary": string, "key_points": string[], '
            '"detailed_notes": string[], "action_items": string[]}. '
            "Keep items concise but useful.\n\n"
            f"Transcript:\n{trimmed}"
        )

    def _condense_transcript(self, transcript: str) -> str:
        lines = [line.strip() for line in transcript.splitlines() if line.strip()]
        if not lines:
            return transcript[: self.max_transcript_chars]

        deduped: list[str] = []
        previous = ""
        for line in lines:
            if line != previous:
                deduped.append(line)
            previous = line

        joined = "\n".join(deduped)
        if len(joined) <= self.max_transcript_chars:
            return joined

        keep_head = int(self.max_transcript_chars * 0.7)
        keep_tail = self.max_transcript_chars - keep_head
        head = joined[:keep_head]
        tail = joined[-keep_tail:]
        return f"{head}\n...\n{tail}"

    @staticmethod
    def _to_notes(payload: dict[str, Any]) -> Notes:
        def normalize_list(value: Any) -> list[str]:
            if not isinstance(value, list):
                return []
            return [str(item).strip() for item in value if str(item).strip()]

        title = str(payload.get("title", "Untitled Notes")).strip() or "Untitled Notes"
        summary = str(payload.get("summary", "")).strip()
        return Notes(
            title=title,
            summary=summary,
            key_points=normalize_list(payload.get("key_points")),
            detailed_notes=normalize_list(payload.get("detailed_notes")),
            action_items=normalize_list(payload.get("action_items")),
        )
