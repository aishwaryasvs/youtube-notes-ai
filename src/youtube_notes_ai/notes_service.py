from __future__ import annotations

from .models import Notes, TranscriptResult
from .summarizer import OllamaSummarizer
from .transcript_service import TranscriptUnavailableError, fetch_transcript
from .transcription_fallback import LocalTranscriber


class NotesGenerationService:
    def __init__(self, summarizer: OllamaSummarizer, transcriber: LocalTranscriber) -> None:
        self._summarizer = summarizer
        self._transcriber = transcriber

    def get_transcript(self, video_id: str) -> TranscriptResult:
        try:
            text = fetch_transcript(video_id)
            return TranscriptResult(text=text, source="youtube-transcript-api")
        except TranscriptUnavailableError:
            text = self._transcriber.transcribe_from_youtube(video_id)
            return TranscriptResult(text=text, source="faster-whisper (local fallback)")

    def generate_notes(self, transcript_text: str) -> Notes:
        return self._summarizer.summarize(transcript_text)
