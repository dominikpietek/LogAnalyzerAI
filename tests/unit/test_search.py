import pytest
from pydantic import ValidationError

from stackscout.domain.code_location import CodeLocation
from stackscout.domain.search import SearchHit, SearchResult


def test_hit_pointing_to_single_line_is_created() -> None:
    hit = SearchHit(
        location=CodeLocation(file_path="a.cs", start_line=3, end_line=3),
        line_text="decimal Discount = 0;",
    )

    assert hit.location.start_line == 3
    assert hit.line_text == "decimal Discount = 0;"


@pytest.mark.parametrize(
    ("start_line", "end_line"),
    [
        (None, None),
        (3, None),
        (3, 5),
    ],
)
def test_hit_must_point_to_exactly_one_line(start_line: int | None, end_line: int | None) -> None:
    location = CodeLocation(file_path="a.cs", start_line=start_line, end_line=end_line)

    with pytest.raises(ValidationError):
        SearchHit(location=location, line_text="x")


def test_search_result_json_round_trip() -> None:
    hit = SearchHit(
        location=CodeLocation(file_path="src/a.cs", start_line=1, end_line=1),
        line_text="class A",
    )
    result = SearchResult(hits=(hit,), truncated=True)

    restored = SearchResult.model_validate_json(result.model_dump_json())

    assert restored == result
