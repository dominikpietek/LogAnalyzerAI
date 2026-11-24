from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Role
    content: str


class LlmResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    content: str
    model: str
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
