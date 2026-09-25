"""
Provider factory: reads app config and returns the configured STT/LLM
provider implementation. This is the ONLY place that knows how to
construct a concrete provider — everything else in the app depends only on
the STTProvider / LLMProvider interfaces.
"""
from flask import current_app
from app.services.stt.base import STTProvider
from app.services.stt.mock_provider import MockSTTProvider
from app.services.ai.base import LLMProvider
from app.services.ai.mock_llm_provider import MockLLMProvider


def get_stt_provider() -> STTProvider:
    provider_name = current_app.config.get("STT_PROVIDER", "mock")
    if provider_name == "whisper_api":
        from app.services.stt.whisper_provider import WhisperSTTProvider
        return WhisperSTTProvider(
            api_key=current_app.config.get("OPENAI_API_KEY"),
            model=current_app.config.get("WHISPER_MODEL", "whisper-1"),
        )
    return MockSTTProvider()


def get_llm_provider() -> LLMProvider:
    provider_name = current_app.config.get("LLM_PROVIDER", "mock")
    if provider_name == "openai":
        from app.services.ai.openai_provider import OpenAILLMProvider
        return OpenAILLMProvider(
            api_key=current_app.config.get("OPENAI_API_KEY"),
            model=current_app.config.get("LLM_MODEL", "gpt-4o-mini"),
        )
    return MockLLMProvider()
