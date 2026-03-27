from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from youtube_notes_ai.models import Notes
from youtube_notes_ai.notes_formatter import to_markdown
from youtube_notes_ai.notes_service import NotesGenerationService
from youtube_notes_ai.summarizer import OllamaSummarizer, SummarizationError
from youtube_notes_ai.transcription_fallback import LocalTranscriber, LocalTranscriptionError
from youtube_notes_ai.youtube_parser import extract_video_id


def _summarization_profile_settings(profile: str) -> tuple[int, int]:
    if profile == "Fast":
        return 12000, 450
    if profile == "Detailed":
        return 32000, 1000
    return 18000, 700


@st.cache_resource
def get_service(model_name: str, profile: str) -> NotesGenerationService:
    max_chars, num_predict = _summarization_profile_settings(profile)
    try:
        summarizer = OllamaSummarizer(
            model=model_name,
            max_transcript_chars=max_chars,
            num_predict=num_predict,
        )
    except TypeError:
        summarizer = OllamaSummarizer(model=model_name)

    return NotesGenerationService(
        summarizer=summarizer,
        transcriber=LocalTranscriber(model_size="base"),
    )


def _render_notes(notes: Notes, source: str) -> None:
    st.subheader(notes.title)
    st.caption(f"Transcript source: {source}")

    st.markdown("### Summary")
    st.write(notes.summary or "No summary generated.")

    st.markdown("### Key Points")
    if notes.key_points:
        for item in notes.key_points:
            st.markdown(f"- {item}")
    else:
        st.write("No key points generated.")

    st.markdown("### Detailed Notes")
    if notes.detailed_notes:
        for item in notes.detailed_notes:
            st.markdown(f"- {item}")
    else:
        st.write("No detailed notes generated.")

    st.markdown("### Action Items / Takeaways")
    if notes.action_items:
        for item in notes.action_items:
            st.markdown(f"- {item}")
    else:
        st.write("No action items generated.")


def _init_state() -> None:
    if "result" not in st.session_state:
        st.session_state.result = None
    if "raw_transcript" not in st.session_state:
        st.session_state.raw_transcript = ""
    if "history" not in st.session_state:
        st.session_state.history = []


def _save_to_history(entry: dict[str, Any], transcript: str) -> None:
    snapshot = {
        **entry,
        "raw_transcript": transcript,
        "saved_at": time.strftime("%H:%M:%S"),
    }
    history: list[dict[str, Any]] = st.session_state.history
    history.insert(0, snapshot)

    # Keep recent history compact and useful.
    st.session_state.history = history[:8]


def _render_error(title: str, message: str, details: str | None = None) -> None:
    st.error(f"{title}: {message}")
    with st.expander("Troubleshooting"):
        st.markdown("- Confirm Ollama is running (`ollama serve`).")
        st.markdown("- Confirm the model exists (`ollama list`).")
        st.markdown("- For fallback transcription, ensure `ffmpeg` is installed.")
        if details:
            st.caption(details)


def main() -> None:
    _init_state()
    st.set_page_config(page_title="YouTube Notes AI", layout="wide")

    st.title("YouTube Notes AI")
    st.caption("Paste a YouTube URL and generate structured notes locally.")

    with st.sidebar:
        st.header("Settings")
        model_name = st.text_input("Ollama model", value="llama3.1:8b")
        profile = st.selectbox("Note detail", options=["Fast", "Balanced", "Detailed"], index=1)
        show_transcript = st.checkbox("Show raw transcript tab", value=False)
        st.info("Ensure Ollama is running on localhost and the model is installed.")
        st.divider()
        st.subheader("Recent Notes")

        history_items: list[dict[str, Any]] = st.session_state.history
        if not history_items:
            st.caption("No history yet.")
        else:
            for idx, item in enumerate(history_items):
                label = item["notes"].title.strip() or item["video_id"]
                st.caption(f"{item['saved_at']} • {item['video_id']} • {item['profile']}")
                if st.button(label[:50], key=f"history_{idx}", use_container_width=True):
                    st.session_state.result = {
                        "video_id": item["video_id"],
                        "source": item["source"],
                        "profile": item["profile"],
                        "transcript_seconds": item["transcript_seconds"],
                        "notes_seconds": item["notes_seconds"],
                        "notes": item["notes"],
                    }
                    st.session_state.raw_transcript = item["raw_transcript"]
                    st.rerun()

            if st.button("Clear History", use_container_width=True):
                st.session_state.history = []
                st.rerun()

    with st.form("generate_form", clear_on_submit=False):
        url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Supports youtube.com/watch, youtu.be, shorts, embed links, or direct video IDs.",
        )
        left, right = st.columns([1, 1])
        generate_clicked = left.form_submit_button("Generate Notes", type="primary", use_container_width=True)
        clear_clicked = right.form_submit_button("Clear", use_container_width=True)

    if clear_clicked:
        st.session_state.result = None
        st.session_state.raw_transcript = ""
        st.rerun()

    if generate_clicked:
        if not url.strip():
            st.error("Please enter a YouTube URL.")
        else:
            try:
                progress_message = st.empty()
                progress_message.info("Validating YouTube URL...")
                video_id = extract_video_id(url)
                progress_message.info("Initializing services...")
                service = get_service(model_name, profile)

                with st.status("Working on your notes...", expanded=True) as status:
                    status.write("Step 1/2: Fetching transcript")
                    transcript_started_at = time.perf_counter()
                    with st.spinner("Fetching transcript (or running fallback transcription)..."):
                        transcript_result = service.get_transcript(video_id)
                    transcript_seconds = time.perf_counter() - transcript_started_at

                    status.write(f"Transcript source: {transcript_result.source}")
                    status.write("Step 2/2: Summarizing with Ollama")
                    notes_started_at = time.perf_counter()
                    with st.spinner("Generating structured notes..."):
                        notes = service.generate_notes(transcript_result.text)
                    notes_seconds = time.perf_counter() - notes_started_at

                    status.update(label="Done: notes generated", state="complete")
                    progress_message.success("Notes are ready.")

                st.session_state.raw_transcript = transcript_result.text
                st.session_state.result = {
                    "video_id": video_id,
                    "source": transcript_result.source,
                    "profile": profile,
                    "transcript_seconds": transcript_seconds,
                    "notes_seconds": notes_seconds,
                    "notes": notes,
                }
                _save_to_history(st.session_state.result, transcript_result.text)
            except ValueError as exc:
                _render_error("Invalid URL", str(exc))
            except LocalTranscriptionError:
                _render_error(
                    "Transcription failed",
                    "Transcript was unavailable and local fallback failed.",
                )
            except SummarizationError as exc:
                _render_error(
                    "Summarization failed",
                    str(exc),
                    "If Ollama is running, try a smaller model (for example `llama3.2:3b`) for faster response.",
                )
            except Exception as exc:  # noqa: BLE001
                _render_error("Unexpected error", "Something went wrong while generating notes.", str(exc))

    result = st.session_state.result
    if result:
        notes: Notes = result["notes"]
        source = result["source"]
        markdown = to_markdown(notes, source=source)

        metric_a, metric_b, metric_c = st.columns(3)
        metric_a.metric("Transcript", f"{result['transcript_seconds']:.1f}s")
        metric_b.metric("Notes", f"{result['notes_seconds']:.1f}s")
        metric_c.metric("Profile", result["profile"])

        st.download_button(
            label="Download Markdown",
            data=markdown,
            file_name=f"youtube-notes-{result['video_id']}.md",
            mime="text/markdown",
        )

        if show_transcript:
            notes_tab, transcript_tab = st.tabs(["Notes", "Transcript"])
            with notes_tab:
                _render_notes(notes, source)
            with transcript_tab:
                st.text_area("Raw transcript", st.session_state.raw_transcript, height=400)
        else:
            _render_notes(notes, source)


if __name__ == "__main__":
    main()
