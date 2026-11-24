from typing import Protocol
from stackscout.domain.chat import ChatMessage, LlmResponse
from collections.abc import Sequence
from typing import Any

class LlmClient(Protocol):
    def complete(self, messages: Sequence[ChatMessage], *, 
                 temperature: float = 0.0, json_schema: dict[str, Any] | None  = None) -> LlmResponse:
        """Wysyła całą rozmowę do modelu i zwraca jedną odpowiedź.

        Model nie ma pamięci między wywołaniami, więc `messages` musi zawierać
        pełną historię rozmowy. Odpowiedź jest zwracana w całości (bez streamingu).
        """ 
    