import os
from pathlib import Path, PurePosixPath

from stackscout.domain.code_location import CodeLocation

IGNORED_DIRS = {".git", ".vs", ".idea", "bin", "obj", "node_modules", "__pycache__", ".venv", ".stackscout"}


class FileSystemWorkspace:
    def __init__(self, root: Path) -> None:
        if root.exists() and root.is_dir():
            self.root = root.resolve()
        else:
            raise Exception("Wrong root path!")

    def list_files(self) -> list[PurePosixPath]:
        result: list[PurePosixPath] = []

        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
            for name in filenames:
                full = Path(dirpath) / name
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
