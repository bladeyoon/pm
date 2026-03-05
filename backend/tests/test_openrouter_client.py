import json
from urllib.error import HTTPError, URLError

import pytest

from app.openrouter_client import OpenRouterClient, OpenRouterConfigError, OpenRouterRequestError


class StubHTTPResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "StubHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        return None


def test_client_reads_model_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_MODEL", "openrouter/custom-model")

    client = OpenRouterClient.from_env()

    assert client.model == "openrouter/custom-model"


def test_ask_raises_when_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    client = OpenRouterClient()

    with pytest.raises(OpenRouterConfigError, match="OPENROUTER_API_KEY is not set"):
        client.ask("2+2")


def test_ask_returns_content_from_valid_provider_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    client = OpenRouterClient(model="openrouter/free")

    payload = {
        "choices": [
            {
                "message": {
                    "content": "4",
                }
            }
        ]
    }

    def stub_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        assert request.full_url.endswith("/chat/completions")
        assert request.get_header("Authorization") == "Bearer test-key"
        request_body = json.loads(request.data.decode("utf-8"))
        assert request_body["model"] == "openrouter/free"
        assert request_body["messages"] == [{"role": "user", "content": "2+2"}]
        assert timeout == client.timeout_seconds
        return StubHTTPResponse(json.dumps(payload))

    monkeypatch.setattr("app.openrouter_client.urlopen", stub_urlopen)

    assert client.smoke_check() == "4"


def test_ask_raises_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    client = OpenRouterClient()

    def stub_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        raise HTTPError(request.full_url, 429, "Too Many Requests", hdrs=None, fp=None)

    monkeypatch.setattr("app.openrouter_client.urlopen", stub_urlopen)

    with pytest.raises(OpenRouterRequestError, match="provider returned HTTP 429"):
        client.ask("2+2")


def test_ask_raises_on_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    client = OpenRouterClient()

    def stub_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        raise URLError("network down")

    monkeypatch.setattr("app.openrouter_client.urlopen", stub_urlopen)

    with pytest.raises(OpenRouterRequestError, match="provider request failed"):
        client.ask("2+2")


def test_ask_raises_on_invalid_provider_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    client = OpenRouterClient()

    def stub_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        return StubHTTPResponse(json.dumps({"choices": []}))

    monkeypatch.setattr("app.openrouter_client.urlopen", stub_urlopen)

    with pytest.raises(OpenRouterRequestError, match="missing choices"):
        client.ask("2+2")
