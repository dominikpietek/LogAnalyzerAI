from pydantic import BaseModel

from stackscout.domain.code_location import CodeLocation


class FileContent(BaseModel):
    location: CodeLocation
    text: str
