from stackscout.domain.chat import ChatMessage, LlmResponse
from collections.abc import Sequence
from typing import Any
from dataclasses import dataclass


@dataclass(frozen=True)
class FakeCall:
    messages: tuple[ChatMessage, ...]
    temperature: float
    json_schema: dict[str, Any] | None


class FakeLlmClient:
    def __init__(self, responses: list[str]) -> None:
        self._responses = list(responses)
        self.calls: list[FakeCall]

    def complete(self, messages: Sequence[ChatMessage], *, 
                     temperature: float = 0.0, json_schema: dict[str, Any] | None  = None) -> LlmResponse:
        self.calls.append(FakeCall(messages=tuple(messages), temperature=temperature, json_schema=json_schema))
        if len(self._responses) == 0:
            raise Exception("No responses")
        else:
            return LlmResponse(content=self._responses.pop(0), model="fake")