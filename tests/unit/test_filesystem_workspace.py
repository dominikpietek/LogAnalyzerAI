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


def test_list_files_filters_by_extension_case_insensitively(tmp_path: Path) -> None:
    _touch(tmp_path, "a.cs")
    _touch(tmp_path, "src/B.CS")
    _touch(tmp_path, "README.md")
    _touch(tmp_path, "logo.png")

    files = FileSystemWorkspace(tmp_path).list_files(extensions=frozenset({".cs"}))

    assert files == [PurePosixPath("a.cs"), PurePosixPath("src/B.CS")]


def test_list_files_without_extensions_returns_all_files(tmp_path: Path) -> None:
    _touch(tmp_path, "a.cs")
    _touch(tmp_path, "logo.png")

    files = FileSystemWorkspace(tmp_path).list_files()

    assert files == [PurePosixPath("a.cs"), PurePosixPath("logo.png")]


SAMPLE = "class Order\n{\n    decimal Discount = 0;\n}\n"


def test_search_returns_hit_with_location_and_original_line(tmp_path: Path) -> None:
    _write(tmp_path, "src/Order.cs", SAMPLE)

    result = FileSystemWorkspace(tmp_path).search("Discount")

    assert len(result.hits) == 1
    hit = result.hits[0]
    assert hit.location.file_path == PurePosixPath("src/Order.cs")
    assert hit.location.start_line == 3
    assert hit.line_text == "    decimal Discount = 0;"
    assert result.truncated is False


def test_search_is_case_insensitive(tmp_path: Path) -> None:
    _write(tmp_path, "Order.cs", SAMPLE)

    result = FileSystemWorkspace(tmp_path).search("dIsCoUnT")

    assert [h.location.start_line for h in result.hits] == [3]


def test_search_returns_hits_from_many_files_in_order(tmp_path: Path) -> None:
    _write(tmp_path, "b/Second.cs", "Discount\n")
    _write(tmp_path, "a.cs", "x\nDiscount\n")

    result = FileSystemWorkspace(tmp_path).search("discount")

    assert [(str(h.location.file_path), h.location.start_line) for h in result.hits] == [
        ("a.cs", 2),
        ("b/Second.cs", 1),
    ]


def test_search_skips_ignored_folders_and_other_extensions(tmp_path: Path) -> None:
    _write(tmp_path, "bin/Debug/Gen.cs", "Discount\n")
    _write(tmp_path, "App.dll", "Discount\n")
    _write(tmp_path, "notes.png", "Discount\n")

    result = FileSystemWorkspace(tmp_path).search("Discount")

    assert result.hits == ()


def test_search_truncates_when_more_hits_than_limit(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", "x\nx\nx\nx\nx\n")

    result = FileSystemWorkspace(tmp_path).search("x", max_results=2)

    assert len(result.hits) == 2
    assert result.truncated is True


def test_search_not_truncated_when_hits_exactly_equal_limit(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", "x\nx\ny\ny\n")

    result = FileSystemWorkspace(tmp_path).search("x", max_results=2)

    assert len(result.hits) == 2
    assert result.truncated is False


def test_search_with_regex(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", "var p = CalculateNetPrice();\nvar q = Calculate();\n")

    result = FileSystemWorkspace(tmp_path).search(r"Calc\w+Price", regex=True)

    assert [h.location.start_line for h in result.hits] == [1]


def test_search_regex_is_not_lowercased(tmp_path: Path) -> None:
    # \D to "nie-cyfra", a \d to "cyfra". Zamiana na małe litery zmieniłaby znaczenie.
    _write(tmp_path, "a.cs", "12\nab\n")

    result = FileSystemWorkspace(tmp_path).search(r"^\D+$", regex=True)

    assert [h.location.start_line for h in result.hits] == [2]


def test_search_invalid_regex_raises(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", "x\n")

    with pytest.raises(Exception):
        FileSystemWorkspace(tmp_path).search("([", regex=True)


def test_search_survives_file_with_invalid_utf8(tmp_path: Path) -> None:
    (tmp_path / "Old.cs").write_bytes("// Zażółć\nclass Discount {}\n".encode("cp1250"))
    _write(tmp_path, "New.cs", "Discount\n")

    result = FileSystemWorkspace(tmp_path).search("Discount")

    assert [str(h.location.file_path) for h in result.hits] == ["New.cs", "Old.cs"]


def test_search_truncates_very_long_lines(tmp_path: Path) -> None:
    _write(tmp_path, "data.json", "needle" + "x" * 1000 + "\n")

    result = FileSystemWorkspace(tmp_path).search("needle")

    assert len(result.hits[0].line_text) <= 300


def test_search_without_hits_returns_empty_result(tmp_path: Path) -> None:
    _write(tmp_path, "a.cs", SAMPLE)

    result = FileSystemWorkspace(tmp_path).search("nothing-here")

    assert result.hits == ()
    assert result.truncated is False
