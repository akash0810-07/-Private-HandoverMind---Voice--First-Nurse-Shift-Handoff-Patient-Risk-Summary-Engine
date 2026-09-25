import time
import hashlib
from app.services.stt.base import STTProvider, TranscriptionResult

# A small deterministic bank of synthetic handoff transcripts used when no
# real STT provider is configured (offline dev/demo/CI). Selection is based
# on a hash of the audio file's bytes so the same "recording" always yields
# the same transcript, keeping automated tests reproducible.
_SAMPLE_TRANSCRIPTS = [
    (
        "Bed 12 is Mr Sharma. He has pneumonia. He was given antibiotics at 8 PM. "
        "His temperature was 102 and he complained of breathing difficulty. "
        "Blood test is still pending. He is allergic to penicillin."
    ),
    (
        "Bed 4, Mrs Verma, recovering from hip surgery. Pain is well controlled with "
        "paracetamol. Vitals stable, blood pressure 120 over 80. Physiotherapy is "
        "scheduled for tomorrow morning. No known allergies."
    ),
    (
        "Bed 7 is Mr Iyer, admitted for observation after a fall at home. He reported "
        "dizziness and mild confusion earlier this evening. Vitals otherwise normal. "
        "CT scan is pending. Family should be updated in the morning."
    ),
]


class MockSTTProvider(STTProvider):
    name = "mock"

    def transcribe(self, audio_path: str, content_type: str) -> TranscriptionResult:
        start = time.time()
        try:
            with open(audio_path, "rb") as f:
                content = f.read()
        except OSError:
            content = audio_path.encode("utf-8")

        digest = hashlib.sha256(content).hexdigest()
        index = int(digest, 16) % len(_SAMPLE_TRANSCRIPTS)
        transcript = _SAMPLE_TRANSCRIPTS[index]

        duration_ms = int((time.time() - start) * 1000) + 250  # simulate latency
        return TranscriptionResult(
            transcript=transcript,
            provider=self.name,
            duration_ms=duration_ms,
            raw_meta={"mock": True, "selected_sample": index},
        )
