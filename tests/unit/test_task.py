from pathlib import Path

import pytest
from pydantic import ValidationError

from stackscout.domain.task import AgentTask


def test_are_AgentTask_id_diffrent() -> None:
    agent1 = AgentTask(prompt="test", project_root=Path())
    agent2 = AgentTask(prompt="test", project_root=Path())

    assert agent1.id != agent2.id


def test_blank_prompt() -> None:
    with pytest.raises(ValidationError):
        AgentTask(prompt="", project_root=Path())
    with pytest.raises(ValidationError):
        AgentTask(prompt=" ", project_root=Path())
