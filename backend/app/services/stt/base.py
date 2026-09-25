"""
STTProvider interface. Any speech-to-text backend (Whisper API, a local
model, another vendor) must implement this contract so the rest of the
application never depends on a specific provider.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranscriptionResult:
    transcript: str
    provider: str
    duration_ms: int
    raw_meta: dict


class STTProvider(ABC):
    name: str = "base"

    @abstractmethod
    def transcribe(self, audio_path: str, content_type: str) -> TranscriptionResult:
        """Transcribe an audio file on disk and return the transcript."""
        raise NotImplementedError
