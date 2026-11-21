import uuid
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskMode(Enum):
    TRIAGE = 0
    EXPLORE = 1


class AgentTask(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    prompt: str
    project_root: Path
    mode: TaskMode = TaskMode.EXPLORE

    @field_validator("prompt")
    @classmethod
    def not_blank(cls, text: str) -> str:
        if not text.strip():
            raise ValueError("Prompt is blank!")
        return text
