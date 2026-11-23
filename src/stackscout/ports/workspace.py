from pathlib import PurePosixPath
from typing import Protocol

from stackscout.domain.code_location import CodeLocation
from stackscout.domain.search import SearchResult


class Workspace(Protocol):
    def list_files(self, extensions: frozenset[str] | None = None) -> list[PurePosixPath]: ...
    def read_file(self, location: CodeLocation) -> str: ...
    def search(self, query: str, *, regex: bool = False, max_results: int = 50) -> SearchResult: ...
