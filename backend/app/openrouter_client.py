import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenRouterConfigError(ValueError):
    pass


class OpenRouterRequestError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenRouterClient:
    api_base_url: str = "https://openrouter.ai/api/v1"
    model: str = "openrouter/free"
    timeout_seconds: float = 20.0

    @classmethod
    def from_env(cls) -> "OpenRouterClient":
        model = os.getenv("OPENROUTER_MODEL", "openrouter/free")
        return cls(model=model)

    def _resolve_api_key(self) -> str:
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise OpenRouterConfigError("OPENROUTER_API_KEY is not set")
        return api_key

    def ask(self, prompt: str) -> str:
        api_key = self._resolve_api_key()
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        request = Request(
            url=f"{self.api_base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except HTTPError as exc:
            raise OpenRouterRequestError(f"provider returned HTTP {exc.code}") from exc
        except URLError as exc:
            raise OpenRouterRequestError("provider request failed") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise OpenRouterRequestError("provider returned invalid JSON") from exc

        content = _extract_message_content(parsed)
        if not content.strip():
            raise OpenRouterRequestError("provider returned empty message content")
        return content.strip()

    def smoke_check(self) -> str:
        return self.ask("2+2")


def _extract_message_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenRouterRequestError("provider response missing choices")
    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise OpenRouterRequestError("provider response choice must be an object")
    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise OpenRouterRequestError("provider response missing message object")
    content = message.get("content")
    if not isinstance(content, str):
        raise OpenRouterRequestError("provider response content must be a string")
    return content
