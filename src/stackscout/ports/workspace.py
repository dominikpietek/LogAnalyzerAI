from pathlib import PurePosixPath
from typing import Protocol

from stackscout.domain.code_location import CodeLocation


class Workspace(Protocol):
    def list_files(self) -> list[PurePosixPath]: ...
    def read_file(self, location: CodeLocation) -> str: ...
