import os
import re
from pathlib import Path, PurePosixPath

from stackscout.domain.code_location import CodeLocation
from stackscout.domain.search import SearchHit, SearchResult

IGNORED_DIRS = frozenset({".git", ".vs", ".idea", "bin", "obj", "node_modules", "__pycache__", ".venv", ".stackscout"})
SEARCH_EXTENSIONS = frozenset({".cs", ".xaml", ".csproj", ".sln", ".json", ".config", ".xml", ".sql", ".md", ".txt"})


class FileSystemWorkspace:
    def __init__(self, root: Path) -> None:
        if root.exists() and root.is_dir():
            self.root = root.resolve()
        else:
            raise Exception("Wrong root path!")

    def list_files(self, extensions: frozenset[str] | None = None) -> list[PurePosixPath]:
        result: list[PurePosixPath] = []

        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
            for name in filenames:
                full = Path(dirpath) / name
                suffix = full.suffix.lower()
                if extensions is not None and suffix not in extensions:
                    continue
                result.append(PurePosixPath(full.relative_to(self.root).as_posix()))

        return sorted(result)

    def _file_to_string(self, path: PurePosixPath, start_line: int | None = None, end_line: int | None = None) -> str:
        lines_count = 0
        with open(self.root / path, encoding="utf-8-sig") as f:
            lines_count = len(f.readlines())
        with open(self.root / path, encoding="utf-8-sig") as f:
            if start_line is None and end_line is None:
                return f.read()
            elif start_line is not None and start_line > lines_count:
                raise Exception(f"end_line or start_line larger than lines_count: {start_line}, {end_line}")
            else:
                line_number = 1
                text_to_return = ""
                if end_line is None:
                    end_line = 999_999
                if start_line is None:
                    start_line = 1
                for line in f:
                    if line_number >= start_line and line_number <= end_line:
                        text_to_return += line
                    if line_number > end_line:
                        break
                    line_number += 1
                return text_to_return

    def _is_valid_file(self, file_path: PurePosixPath) -> bool:
        full = (self.root / file_path).resolve()
        if not full.is_relative_to(self.root):
            raise Exception(f"{file_path} resolves outside the workspace")
        path = Path(self.root / file_path)
        return path.is_file() and not any(part in IGNORED_DIRS for part in path.parent.parts)

    def read_file(self, location: CodeLocation) -> str:
        if not self._is_valid_file(location.file_path):
            raise Exception("Wrong file path!")

        if location.start_line is None:
            return self._file_to_string(location.file_path)
        else:
            return self._file_to_string(location.file_path, location.start_line, location.end_line)

    def search(self, query: str, *, regex: bool = False, max_results: int = 50) -> SearchResult:
        if not regex:
            query = query.lower()
        else:
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error as ex:
                raise ValueError(f"Nieprawidłowy regex: {query!r} ({ex})") from ex
        files: list[PurePosixPath] = self.list_files(extensions=SEARCH_EXTENSIONS)
        hits: list[SearchHit] = []
        truncated = False
        for file in files:
            if truncated:
                break

            with open(self.root / file, encoding="utf-8-sig", errors="replace") as f:
                text = f.read()
                text_lower = text.lower()
                if regex:
                    if not pattern.search(text_lower):
                        continue
                elif query not in text_lower:
                    continue

            with open(self.root / file, encoding="utf-8-sig", errors="replace") as f:
                for line_no, line in enumerate(f, start=1):
                    line_lower = line.lower()
                    if (regex and pattern.search(line_lower)) or (not regex and query in line_lower):
                        if len(hits) >= max_results:
                            truncated = True
                            break
                        if len(line) > 300:
                            line = line[:300]
                        line = line.rstrip("\r\n")
                        hits.append(SearchHit(location=CodeLocation(file_path=file, start_line=line_no, end_line=line_no), line_text=line))

        return SearchResult(hits=tuple(hits), truncated=truncated)
