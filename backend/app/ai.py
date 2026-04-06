from dataclasses import dataclass
import json
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
        data = self._post_chat(payload)
        return self._extract_content_text(data)

    def ask_structured(
        self,
        *,
        messages: list[dict[str, str]],
        schema_name: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "model": self.config.model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        data = self._post_chat(payload)
        content = self._extract_content_text(data)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OpenRouterError("OpenRouter structured response was not valid JSON") from exc

        if not isinstance(parsed, dict):
            raise OpenRouterError("OpenRouter structured response must be a JSON object")

        return parsed

    def _post_chat(self, payload: dict[str, Any]) -> dict[str, Any]:
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
        if not isinstance(data, dict):
            raise OpenRouterError("OpenRouter response must be a JSON object")
        return data

    def _extract_content_text(self, data: dict[str, Any]) -> str:
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
