from __future__ import annotations

import tempfile
from pathlib import Path

from faster_whisper import WhisperModel
from yt_dlp import YoutubeDL


class LocalTranscriptionError(RuntimeError):
    pass


class LocalTranscriber:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8") -> None:
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        self._model: WhisperModel | None = None

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            self._model = WhisperModel(
                self._model_size,
                device=self._device,
                compute_type=self._compute_type,
            )
        return self._model

    @staticmethod
    def _download_audio(video_id: str, output_template: str) -> None:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    @staticmethod
    def _resolve_audio_file(temp_dir: Path) -> Path:
        primary = temp_dir / "audio.mp3"
        if primary.exists():
            return primary

        # If post-processing produced a different extension, use the first audio artifact found.
        fallback_candidates = sorted(
            path for path in temp_dir.iterdir() if path.is_file() and path.suffix.lower() in {".m4a", ".webm", ".wav"}
        )
        if fallback_candidates:
            return fallback_candidates[0]

        raise LocalTranscriptionError("Failed to create audio file for transcription.")

    def transcribe_from_youtube(self, video_id: str) -> str:
        try:
            with tempfile.TemporaryDirectory(prefix="yt_notes_") as temp_dir_name:
                temp_dir = Path(temp_dir_name)
                output_template = str(temp_dir / "audio")

                self._download_audio(video_id, output_template)
                final_audio = self._resolve_audio_file(temp_dir)

                model = self._get_model()
                segments, _info = model.transcribe(str(final_audio), vad_filter=True)
                transcript = "\n".join(segment.text.strip() for segment in segments if segment.text.strip())
                if not transcript:
                    raise LocalTranscriptionError("Local transcription produced empty output.")
                return transcript
        except Exception as exc:  # noqa: BLE001
            raise LocalTranscriptionError("Could not transcribe locally from audio fallback.") from exc
