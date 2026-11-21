from pathlib import Path

from pydantic import BaseModel


class AgentTask(BaseModel):
    id: str
    prompt: str
    project_root: Path
    # mode:
