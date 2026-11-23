from pydantic import BaseModel, ConfigDict, field_validator

from stackscout.domain.code_location import CodeLocation


class SearchHit(BaseModel):
    model_config = ConfigDict(frozen=True)

    location: CodeLocation
    line_text: str

    @field_validator("location")
    @classmethod
    def lines_have_to_be_equal(cls, value: CodeLocation) -> CodeLocation:
        if value.start_line is None or value.end_line is None:
            raise ValueError("In SearchHit you have to set start_line and end_line")
        if value.start_line != value.end_line:
            raise ValueError("In SearchHit you have to search exactly one line")
        return value


class SearchResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    hits: tuple[SearchHit, ...]
    truncated: bool = False
