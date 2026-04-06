from dataclasses import dataclass
import os
from typing import Any

import httpx


class OpenRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    model: str = "openai/gpt-oss-120b"
    base_url: str = "https://openrouter.ai/api/v1"


class OpenRouterClient:
    def __init__(self, config: OpenRouterConfig, http_client: httpx.Client | None = None) -> None:
        self.config = config
        self.http_client = http_client or httpx.Client(timeout=30.0)

    def ask(self, prompt: str) -> str:
        payload = {
            "model": self.config.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        response = self.http_client.post(
            f"{self.config.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices")
        if not choices:
            raise OpenRouterError("OpenRouter response missing choices")

        message = choices[0].get("message", {})
        content = message.get("content")

        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    text_parts.append(part["text"])
            combined = "\n".join(text_parts).strip()
            if combined:
                return combined

        raise OpenRouterError("OpenRouter response missing message content")


def load_openrouter_config() -> OpenRouterConfig:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing")

    return OpenRouterConfig(api_key=api_key)
