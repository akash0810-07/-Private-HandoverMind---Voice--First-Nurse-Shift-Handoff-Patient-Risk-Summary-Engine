import time
from openai import OpenAI, OpenAIError
from app.services.stt.base import STTProvider, TranscriptionResult


class WhisperSTTProvider(STTProvider):
    """
    Real speech-to-text provider using the OpenAI Whisper API.
    Requires OPENAI_API_KEY to be set in the environment. The key is read
    once at construction time and never logged or returned to the client.
    """
    name = "whisper_api"

    def __init__(self, api_key: str, model: str = "whisper-1"):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the whisper_api STT provider.")
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def transcribe(self, audio_path: str, content_type: str) -> TranscriptionResult:
        start = time.time()
        try:
            with open(audio_path, "rb") as audio_file:
                response = self._client.audio.transcriptions.create(
                    model=self._model,
                    file=audio_file,
                )
        except OpenAIError as exc:
            raise RuntimeError(f"Whisper transcription failed: {exc}") from exc
        except OSError as exc:
            raise RuntimeError(f"Could not read audio file: {exc}") from exc

        duration_ms = int((time.time() - start) * 1000)
        return TranscriptionResult(
            transcript=(response.text or "").strip(),
            provider=self.name,
            duration_ms=duration_ms,
            raw_meta={"model": self._model},
        )
