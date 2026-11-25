from collections.abc import Sequence
from typing import Any

import httpx

from stackscout.domain.chat import ChatMessage, LlmResponse


class OllamaLlmClient:
    def __init__(
        self, model: str, base_url: str = "http://localhost:11434", timeout_s: float = 120.0, transport: httpx.BaseTransport | None = None
    ) -> None:
        self.model = model
        self._client = httpx.Client(base_url=base_url, timeout=timeout_s, transport=transport)

    def complete(self, messages: Sequence[ChatMessage], *, temperature: float = 0.0, json_schema: dict[str, Any] | None = None) -> LlmResponse:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": mes.role.value, "content": mes.content} for mes in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_schema is not None:
            body["format"] = json_schema

        response = self._client.post("/api/chat", json=body)
        resp_json = response.json()
        return LlmResponse(
            content=resp_json["message"]["content"],
            model=resp_json["model"],
            prompt_tokens=resp_json.get("prompt_eval_count"),
            completion_tokens=resp_json.get("eval_count"),
        )
