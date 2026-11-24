import pytest

from stackscout.adapters.fake_llm import FakeCall, FakeLlmClient
from stackscout.domain.chat import ChatMessage, Role
from stackscout.ports.llm import LlmClient

QUESTION = [ChatMessage(role=Role.USER, content="Gdzie jest liczony rabat?")]


def test_returns_scripted_responses_in_order() -> None:
    client: LlmClient = FakeLlmClient(["pierwsza", "druga"])

    first = client.complete(QUESTION)
    second = client.complete(QUESTION)

    assert first.content == "pierwsza"
    assert second.content == "druga"
    assert first.model == "fake"


def test_records_every_call() -> None:
    fake = FakeLlmClient(["ok"])
    schema = {"type": "object"}

    fake.complete(QUESTION, temperature=0.7, json_schema=schema)

    assert fake.calls == [
        FakeCall(messages=tuple(QUESTION), temperature=0.7, json_schema=schema),
    ]


def test_records_default_arguments() -> None:
    fake = FakeLlmClient(["ok"])

    fake.complete(QUESTION)

    assert fake.calls[0].temperature == 0.0
    assert fake.calls[0].json_schema is None


def test_raises_when_responses_run_out() -> None:
    fake = FakeLlmClient(["jedyna"])
    fake.complete(QUESTION)

    with pytest.raises(AssertionError, match="#2"):
        fake.complete(QUESTION)


def test_recorded_messages_do_not_change_when_caller_list_changes() -> None:
    fake = FakeLlmClient(["ok"])
    messages = list(QUESTION)

    fake.complete(messages)
    messages.append(ChatMessage(role=Role.USER, content="dopisane później"))

    assert len(fake.calls[0].messages) == 1


def test_changing_original_list_does_not_affect_responses() -> None:
    responses = ["pierwsza"]
    fake = FakeLlmClient(responses)

    responses.clear()

    assert fake.complete(QUESTION).content == "pierwsza"