"""Tests for BIDS query functionality."""

from pathlib import Path

import pytest

from bids_explorer.paths.query import BidsQuery


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
            {"task": "rest", "run": "01"},
            Path("sub-*_ses-*_task-rest*_run-01*"),
            Path("sub-*/ses-*/*"),
        ),
        (
            {"subject": "001", "task": "rest", "acquisition": "01"},
            Path("sub-001_ses-*_task-rest_acq-01*"),
            Path("sub-001/ses-*/*"),
        ),
        (
            {"suffix": "eeg"},
            Path("sub-*_ses-*_eeg.*"),
            Path("sub-*/ses-*/*"),
        ),
        (
            {"subject": "001", "suffix": "eeg"},
            Path("sub-001_ses-*_eeg.*"),
            Path("sub-001/ses-*/*"),
        ),
        (
            {"description": "aDesc", "suffix": "eeg"},
            Path("sub-*_ses-*desc-aDesc*_eeg.*"),
            Path("sub-*/ses-*/*"),
        ),
        (
            {"session": "01", "task": "rest", "suffix": "eeg"},
            Path("sub-*_ses-01*task-aDesc*_eeg.*"),
            Path("sub-*/ses-01/*"),
        ),
        (
            {"extension": ".vhdr"},
            Path("sub-*_ses-*.vhdr"),
            Path("sub-*/ses-*/*"),
        ),
        (
            {"session": "001", "extension": ".vhdr"},
            Path("sub-*_ses-001*.vhdr"),
            Path("sub-*/ses-001/*"),
        ),
        (
            {"task": "rest", "extension": ".vhdr"},
            Path("sub-*_ses-*task-rest*.vhdr"),
            Path("sub-*/ses-*/*"),
        ),
        (
            {"subject": "001", "task": "rest", "extension": ".vhdr"},
            Path("sub-001_ses-*task-rest*.vhdr"),
            Path("sub-001/ses-*/*"),
        ),
        (
            {"suffix": "eeg", "extension": ".vhdr"},
            Path("sub-*_ses-*_eeg.vhdr"),
            Path("sub-*/ses-*/*"),
        ),
        (
            {"session": "001", "suffix": "eeg", "extension": ".vhdr"},
            Path("sub-*_ses-001*_eeg.vhdr"),
            Path("sub-*/ses-001/*"),
        ),
        (
            {"run": "001", "suffix": "eeg", "extension": ".vhdr"},
            Path("sub-*_ses-*run-001*_eeg.vhdr"),
            Path("sub-*/ses-*/*"),
        ),
        (
            {
                "session": "02",
                "run": "001",
                "suffix": "eeg",
                "extension": ".vhdr",
            },
            Path("sub-*_ses-02*run-001*_eeg.vhdr"),
            Path("sub-*/ses-02/*"),
        ),
        (
            {
                "subject": "001",
                "session": "002",
                "description": "aDesc",
                "extension": ".vhdr",
            },
            Path("sub-001_ses-002*desc-aDesc*.vhdr"),
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
