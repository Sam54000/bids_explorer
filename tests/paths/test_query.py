"""Tests for BIDS query functionality."""

import pytest

from bids_explorer.paths.query import BidsQuery


def test_query_initialization() -> None:
    """Test BidsQuery initialization with various parameters."""
    # Basic initialization
    query = BidsQuery(
        subject="001",
        session="01",
        task="rest",
    )
    assert query.subject == "001"
    assert query.session == "01"
    assert query.task == "rest"

    # Test with list values
    query = BidsQuery(
        subject=["001", "002"],
        session=["01", "02"],
    )
    assert query.subject == ["001", "002"]
    assert query.session == ["01", "02"]


def test_query_pattern_generation() -> None:
    """Test generation of query patterns."""
    # Test single value pattern
    query = BidsQuery(subject="001", task="rest")
    pattern = query.filename
    assert "sub-001" in pattern
    assert "task-rest" in pattern
    assert "ses-*" in pattern
    assert "sub-001/ses-*/"


def test_query_validation() -> None:
    """Test query parameter validation."""
    # Test invalid subject format
    with pytest.raises(ValueError):
        BidsQuery(subject="invalid subject")

    # Test invalid session format
    with pytest.raises(ValueError):
        BidsQuery(session="invalid session")

    # Test invalid task format
    with pytest.raises(ValueError):
        BidsQuery(task="invalid task")
