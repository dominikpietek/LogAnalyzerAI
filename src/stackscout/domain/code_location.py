from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CodeLocation(BaseModel):
    model_config = ConfigDict(frozen=True)

    file_path: PurePosixPath
    start_line: int | None = Field(default=None, gt=0)
    end_line: int | None = Field(default=None, gt=0)
    symbol: str | None = None

    @field_validator("file_path")
    @classmethod
    def path_must_be_relative(cls, value: PurePosixPath) -> PurePosixPath:
        if value.is_absolute() or ".." in value.parts:
            raise ValueError("Path cannot be absoulute")
        return value

    @model_validator(mode="after")
    def lines_must_be_ordered(self) -> "CodeLocation":
        if self.end_line is not None and self.start_line is None:
            raise ValueError("end_line requires start_line")
        if self.end_line is not None and self.start_line is not None and self.end_line < self.start_line:
            raise ValueError(f"Wrong start_line and end_line. start_line: {self.start_line}, end_line: {self.end_line}")
        return self
