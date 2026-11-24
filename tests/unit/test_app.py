import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from stackscout.adapters.filesystem_workspace import FileSystemWorkspace
from stackscout.api.app import create_app

ORDER = "class Order\n{\n    decimal Discount = 0;\n}\n"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Order.cs").write_text(ORDER, encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def client(project: Path) -> TestClient:
    return TestClient(create_app(FileSystemWorkspace(project)))


# --- /files ---


def test_files_lists_project_files(client: TestClient) -> None:
    response = client.get("/files")

    assert response.status_code == 200
    assert response.json() == ["README.md", "src/Order.cs"]


def test_files_filters_by_extension(client: TestClient) -> None:
    response = client.get("/files", params={"ext": [".cs"]})

    assert response.status_code == 200
    assert response.json() == ["src/Order.cs"]


# --- /file ---


def test_file_returns_whole_text(client: TestClient) -> None:
    response = client.get("/file", params={"path": "src/Order.cs"})

    assert response.status_code == 200
    assert response.json()["text"] == ORDER


def test_file_returns_line_range(client: TestClient) -> None:
    response = client.get("/file", params={"path": "src/Order.cs", "start_line": 2, "end_line": 3})

    body = response.json()
    assert response.status_code == 200
    assert body["text"] == "{\n    decimal Discount = 0;\n"
    assert body["location"]["start_line"] == 2


def test_file_missing_returns_400(client: TestClient) -> None:
    with pytest.raises(Exception, match="Wrong file path!"):
        client.get("/file", params={"path": "nope.cs"})


def test_file_path_escaping_project_returns_422(client: TestClient) -> None:
    response = client.get("/file", params={"path": "../secret.txt"})

    assert response.status_code == 422


def test_file_start_line_out_of_range_returns_400(client: TestClient) -> None:
    with pytest.raises(Exception, match=re.escape("end_line or start_line larger than lines_count: 99, None")):
        client.get("/file", params={"path": "src/Order.cs", "start_line": 99})


# --- /search ---


def test_search_returns_hits(client: TestClient) -> None:
    response = client.get("/search", params={"q": "discount"})

    body = response.json()
    assert response.status_code == 200
    assert body["truncated"] is False
    assert len(body["hits"]) == 1
    hit = body["hits"][0]
    assert hit["location"]["file_path"] == "src/Order.cs"
    assert hit["location"]["start_line"] == 3
    assert hit["line_text"] == "    decimal Discount = 0;"


def test_search_invalid_regex_returns_400(client: TestClient) -> None:
    with pytest.raises(ValueError, match=re.escape("Nieprawidłowy regex: '(['")):
        client.get("/search", params={"q": "([", "regex": "true"})


def test_search_rejects_too_large_limit(client: TestClient) -> None:
    response = client.get("/search", params={"q": "x", "max_results": 10_000})

    assert response.status_code == 422
