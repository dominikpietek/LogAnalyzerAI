import json
from typing import Any

import httpx

from stackscout.adapters.ollama_client import OllamaLlmClient
from stackscout.domain.chat import ChatMessage, Role
from stackscout.ports.llm import LlmClient

MESSAGES = [
    ChatMessage(role=Role.SYSTEM, content="Jesteś asystentem."),
    ChatMessage(role=Role.USER, content="Cześć"),
]

OK_BODY: dict[str, Any] = {
    "model": "test-model",
    "message": {"role": "assistant", "content": "Hej!"},
    "prompt_eval_count": 12,
    "eval_count": 3,
}


class RecordingServer:
    """Udaje Ollamę: zapisuje żądania i zawsze zwraca OK_BODY."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(200, json=OK_BODY)

    def last_body(self) -> dict[str, Any]:
        body: dict[str, Any] = json.loads(self.requests[-1].content)
        return body


def _client(server: RecordingServer) -> OllamaLlmClient:
    return OllamaLlmClient(
        model="test-model",
        base_url="http://ollama.test",
        transport=httpx.MockTransport(server),
    )


def test_posts_to_chat_endpoint() -> None:
    server = RecordingServer()

    _client(server).complete(MESSAGES)

    request = server.requests[0]
    assert request.method == "POST"
    assert request.url.path == "/api/chat"


def test_sends_model_messages_and_disables_streaming() -> None:
    server = RecordingServer()

    _client(server).complete(MESSAGES)

    body = server.last_body()
    assert body["model"] == "test-model"
    assert body["stream"] is False
    assert body["options"]["temperature"] == 0.0
    assert body["messages"] == [
        {"role": "system", "content": "Jesteś asystentem."},
        {"role": "user", "content": "Cześć"},
    ]


def test_sends_format_only_when_schema_given() -> None:
    server = RecordingServer()
    schema = {"type": "object", "properties": {"keywords": {"type": "array"}}}
    client = _client(server)

    client.complete(MESSAGES)
    assert "format" not in server.last_body()

    client.complete(MESSAGES, json_schema=schema)
    assert server.last_body()["format"] == schema


def test_parses_content_model_and_tokens() -> None:
    client: LlmClient = _client(RecordingServer())

    response = client.complete(MESSAGES)

    assert response.content == "Hej!"
    assert response.model == "test-model"
    assert response.prompt_tokens == 12
    assert response.completion_tokens == 3
