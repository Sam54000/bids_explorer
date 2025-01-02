"""Tests for BIDS query functionality."""

from pathlib import Path

import pytest

from bids_explorer.paths.query import BidsQuery


def test_query_initialization() -> None:
    """Test BidsQuery initialization with various parameters."""
    query = BidsQuery(
        subject="001",
        session="01",
        task="rest",
    )

    assert query.user_input["subject"] == "001"
    assert query.user_input["session"] == "01"
    assert query.user_input["task"] == "rest"


@pytest.mark.parametrize(
    "params,expected_filename,expected_path",
    [
        (
            {},
            Path("sub-*_ses-*"),
            Path("sub-*/ses-*/*"),
        ),
        (
            {"subject": "001"},
            Path("sub-001_ses-*"),
            Path("sub-001/ses-*/*"),
        ),
        (
            {"subject": "001", "session": "01"},
            Path("sub-001_ses-01_*"),
            Path("sub-001/ses-01/*"),
        ),
        (
            {"subject": "001", "task": "rest", "run": "01"},
            Path("sub-001_ses-*_task-rest*_run-01*"),
            Path("sub-001/ses-*/*"),
        ),
        (
            {"subject": "001", "session": "002", "extension": ".vhdr"},
            Path("sub-001_ses-002_*.vhdr"),
            Path("sub-001/ses-002/*"),
        ),
    ],
)
def test_query_pattern_generation(
    params: dict, expected_filename: str, expected_path: Path
) -> None:
    """Test generation of query patterns with different parameter combinations.

    Args:
        params: Dictionary of parameters to pass to BidsQuery
        expected_filename: Expected filename pattern
        expected_path: Expected relative path
    """
    query = BidsQuery(**params)
    assert query.filename == expected_filename
    assert query.relative_path == expected_path
    assert query.fullpath == expected_path / expected_filename


def test_query_validation() -> None:
    """Test query parameter validation."""
    with pytest.raises(ValueError):
        BidsQuery(subject="invalid subject")

    with pytest.raises(ValueError):
        BidsQuery(session="invalid session")

    with pytest.raises(ValueError):
        BidsQuery(task="invalid task")
