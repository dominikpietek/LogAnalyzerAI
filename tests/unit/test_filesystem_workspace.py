from pathlib import Path, PurePosixPath

import pytest

from stackscout.adapters.filesystem_workspace import FileSystemWorkspace
from stackscout.domain.code_location import CodeLocation
from stackscout.ports.workspace import Workspace


def _touch(root: Path, relative: str) -> None:
    """Tworzy pusty plik (razem z folderami po drodze) wewnątrz root."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("")


def test_returns_nested_files_as_relative_posix_paths(tmp_path: Path) -> None:
    _touch(tmp_path, "Program.cs")
    _touch(tmp_path, "src/Orders/OrderService.cs")

    workspace: Workspace = FileSystemWorkspace(tmp_path)

    assert workspace.list_files() == [
        PurePosixPath("Program.cs"),
        PurePosixPath("src/Orders/OrderService.cs"),
    ]


def test_skips_build_and_ide_folders(tmp_path: Path) -> None:
    _touch(tmp_path, "src/App/Program.cs")
    _touch(tmp_path, "src/App/bin/Debug/App.dll")
    _touch(tmp_path, "src/App/obj/project.assets.json")
    _touch(tmp_path, ".vs/settings.json")
    _touch(tmp_path, ".git/HEAD")

    workspace = FileSystemWorkspace(tmp_path)

    assert workspace.list_files() == [PurePosixPath("src/App/Program.cs")]


def test_ignores_folder_by_name_anywhere_in_tree(tmp_path: Path) -> None:
    # Świadomy kompromis: folder "bin" jest pomijany niezależnie od miejsca,
    # nawet jeśli zawiera kod źródłowy.
    _touch(tmp_path, "src/Features/bin/Handler.cs")

    workspace = FileSystemWorkspace(tmp_path)

    assert workspace.list_files() == []


def test_result_is_sorted(tmp_path: Path) -> None:
    for name in ["c.cs", "a.cs", "b/z.cs", "b/a.cs"]:
        _touch(tmp_path, name)

    files = FileSystemWorkspace(tmp_path).list_files()

    assert files == sorted(files)


def test_empty_project_returns_empty_list(tmp_path: Path) -> None:
    assert FileSystemWorkspace(tmp_path).list_files() == []


def test_missing_root_raises(tmp_path: Path) -> None:
    with pytest.raises(Exception):
        FileSystemWorkspace(tmp_path / "does_not_exist")


def test_file_as_root_raises(tmp_path: Path) -> None:
    _touch(tmp_path, "file.txt")

    with pytest.raises(Exception):
        FileSystemWorkspace(tmp_path / "file.txt")


FIVE_LINES = "l1\nl2\nl3\nl4\nl5\n"


def _write(root: Path, relative: str, content: str, encoding: str = "utf-8") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)


def test_read_whole_file(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", FIVE_LINES)

    text = FileSystemWorkspace(tmp_path).read_file(CodeLocation(file_path="a.cs"))

    assert text == FIVE_LINES


def test_read_line_range_is_inclusive_and_one_based(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", FIVE_LINES)

    location = CodeLocation(file_path="a.cs", start_line=2, end_line=3)
    text = FileSystemWorkspace(tmp_path).read_file(location)

    assert text == "l2\nl3\n"


def test_read_from_start_line_to_end_of_file(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", FIVE_LINES)

    location = CodeLocation(file_path="a.cs", start_line=4)
    text = FileSystemWorkspace(tmp_path).read_file(location)

    assert text == "l4\nl5\n"


def test_end_line_beyond_file_is_clamped(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", FIVE_LINES)

    location = CodeLocation(file_path="a.cs", start_line=4, end_line=100)
    text = FileSystemWorkspace(tmp_path).read_file(location)

    assert text == "l4\nl5\n"


def test_start_line_beyond_file_raises(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", FIVE_LINES)

    location = CodeLocation(file_path="a.cs", start_line=6)
    with pytest.raises(Exception):
        FileSystemWorkspace(tmp_path).read_file(location)


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(Exception):
        FileSystemWorkspace(tmp_path).read_file(CodeLocation(file_path="nope.cs"))


def test_file_in_ignored_folder_raises(tmp_path: Path) -> None:
    _write(tmp_path, "src/bin/Debug/App.cs", FIVE_LINES)

    location = CodeLocation(file_path="src/bin/Debug/App.cs")
    with pytest.raises(Exception):
        FileSystemWorkspace(tmp_path).read_file(location)


def test_utf8_bom_is_not_included_in_text(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", "class A {}\n", encoding="utf-8-sig")

    text = FileSystemWorkspace(tmp_path).read_file(CodeLocation(file_path="a.cs"))

    assert text == "class A {}\n"


def test_symlink_pointing_outside_project_raises(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    _write(outside, "secret.txt", "password")
    project = tmp_path / "project"
    project.mkdir()
    try:
        (project / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("Tworzenie symlinków niedostępne (Windows bez trybu dewelopera)")

    location = CodeLocation(file_path="link/secret.txt")
    with pytest.raises(Exception):
        FileSystemWorkspace(project).read_file(location)
