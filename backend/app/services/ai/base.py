"""
LLMProvider interface. Any large language model backend (OpenAI, Anthropic,
a local model) must implement this contract, returning raw text that the
caller will parse and validate against the structured-output schema.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResult:
    raw_text: str
    provider: str
    model: str
    duration_ms: int
    token_usage: Optional[int] = None


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        """
        Ask the model to produce a strict-JSON response. Implementations
        should configure the underlying API for JSON-mode output where
        available, but MUST NOT assume the response is valid JSON — the
        caller is responsible for parsing and schema validation.
        """
        raise NotImplementedError
