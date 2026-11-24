import pytest
from pydantic import ValidationError

from stackscout.domain.chat import ChatMessage, LlmResponse, Role


def test_message_accepts_role_enum() -> None:
    message = ChatMessage(role=Role.USER, content="Cześć")

    assert message.role == Role.USER
    assert message.content == "Cześć"


def test_message_accepts_role_as_text() -> None:
    message = ChatMessage(role="user", content="Cześć")

    assert message.role == Role.USER


@pytest.mark.parametrize("role", [Role.SYSTEM, Role.USER, Role.ASSISTANT])
def test_role_values_match_ollama_api(role: Role) -> None:
    assert role.value in {"system", "user", "assistant"}
    assert role.value == role.name.lower()


def test_message_rejects_unknown_role() -> None:
    with pytest.raises(ValidationError):
        ChatMessage(role="admin", content="Cześć")


def test_message_is_immutable() -> None:
    message = ChatMessage(role=Role.USER, content="Cześć")

    with pytest.raises(ValidationError):
        message.content = "Zmienione"  # type: ignore[misc]


def test_response_token_counts_default_to_none() -> None:
    response = LlmResponse(content="Hej!", model="qwen3:8b")

    assert response.prompt_tokens is None
    assert response.completion_tokens is None


def test_response_rejects_missing_content() -> None:
    with pytest.raises(ValidationError):
        LlmResponse(model="qwen3:8b")  # type: ignore[call-arg]


def test_message_json_round_trip() -> None:
    message = ChatMessage(role=Role.ASSISTANT, content="Odpowiedź")

    restored = ChatMessage.model_validate_json(message.model_dump_json())

    assert restored == message
