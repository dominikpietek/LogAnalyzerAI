from pathlib import PurePosixPath

import pytest
from pydantic import ValidationError

from stackscout.domain.code_location import CodeLocation


def test_creates_location_with_line_range() -> None:
    location = CodeLocation(file_path="src/Orders/OrderService.cs", start_line=10, end_line=20)

    assert location.file_path == PurePosixPath("src/Orders/OrderService.cs")
    assert location.start_line == 10
    assert location.end_line == 20


def test_creates_location_only_file() -> None:
    location = CodeLocation(file_path="OrderService.cs", start_line=10, end_line=20)

    assert location.file_path == PurePosixPath("OrderService.cs")
    assert location.start_line == 10
    assert location.end_line == 20


def test_rejects_end_line_without_start_line() -> None:
    with pytest.raises(ValidationError):
        CodeLocation(file_path="OrderService.cs", end_line=20)


def test_creates_location_end_line_start_line_error() -> None:
    with pytest.raises(ValidationError):
        CodeLocation(file_path="OrderService.cs", start_line=30, end_line=20)


def test_creates_location_end_line_start_line_equals() -> None:
    location = CodeLocation(file_path="OrderService.cs", start_line=20, end_line=20)

    assert location.file_path == PurePosixPath("OrderService.cs")
    assert location.start_line == 20
    assert location.end_line == 20


def test_creates_location_start_line_zero() -> None:
    with pytest.raises(ValidationError):
        CodeLocation(file_path="OrderService.cs", start_line=0, end_line=20)
