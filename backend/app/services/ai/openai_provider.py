import time
from openai import OpenAI, OpenAIError
from app.services.ai.base import LLMProvider, LLMResult


class OpenAILLMProvider(LLMProvider):
    """
    Real structured-extraction provider using the OpenAI Chat Completions
    API in JSON mode. Requires OPENAI_API_KEY. The key is never logged or
    exposed to the frontend — it is only read server-side from the
    environment.
    """
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the openai LLM provider.")
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        start = time.time()
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                response_format={"type": "json_object"},
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except OpenAIError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc

        duration_ms = int((time.time() - start) * 1000)
        choice = response.choices[0]
        usage = getattr(response, "usage", None)
        token_usage = getattr(usage, "total_tokens", None) if usage else None

        return LLMResult(
            raw_text=choice.message.content or "{}",
            provider=self.name,
            model=self._model,
            duration_ms=duration_ms,
            token_usage=token_usage,
        )
