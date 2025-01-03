"""Tests for BIDS validation functionality."""
from pathlib import Path

import pandas as pd
import pytest

from bids_explorer.architecture.validation import (
    BidsValidationError,
    get_invalid_columns,
    is_all_columns_valid,
    validate_bids_file,
)


def test_is_all_columns_valid() -> None:
    """Test validation of DataFrame columns."""
    valid_df = pd.DataFrame(
        columns=[
            "root",
            "subject",
            "session",
            "datatype",
            "task",
            "run",
            "acquisition",
            "description",
            "suffix",
            "extension",
            "atime",
            "mtime",
            "ctime",
            "filename",
        ]
    )
    assert is_all_columns_valid(valid_df)

    invalid_df = pd.DataFrame(columns=["subject", "invalid_column"])
    assert not is_all_columns_valid(invalid_df)


def test_get_invalid_columns() -> None:
    """Test detection of invalid columns."""
    df = pd.DataFrame(
        columns=["subject", "session", "invalid1", "datatype", "invalid2"]
    )
    invalid_cols = get_invalid_columns(df)
    assert invalid_cols == {"invalid1", "invalid2"}


def test_validate_bids_file_valid_paths() -> None:
    """Test validation of valid BIDS file paths."""
    valid_paths = [
        Path("sub-001/ses-01/eeg/sub-001_ses-01_task-rest_eeg.vhdr"),
        Path("sub-002/ses-02/eeg/sub-002_ses-02_task-test_run-01_eeg.vhdr"),
        Path(
            "sub-003/ses-01/eeg/"
            "sub-003_ses-01_task-test_acq-full_run-01_eeg.vhdr"
        ),
    ]
    for path in valid_paths:
        assert validate_bids_file(path) is True


def test_validate_bids_file_invalid_paths() -> None:
    """Test validation of invalid BIDS file paths."""
    invalid_paths = [
        Path("invalid/ses-01/eeg/sub-001_ses-01_task-rest_eeg.vhdr"),
        Path("sub-001/ses-01/eeg/sub-002_ses-01_task-rest_eeg.vhdr"),
        Path("sub-001/ses-01/eeg/sub-001_ses-02_task-rest_eeg.vhdr"),
        Path("sub-001/ses-01/eeg/sub-001_ses-01_invalid-key_eeg.vhdr"),
        Path("sab-001/ses-01/eeg/sub-001_ses-01_task-rest_eeg.vhdr"),
    ]
    for path in invalid_paths:
        with pytest.raises(BidsValidationError):
            validate_bids_file(path)


def test_validate_bids_file_datatype() -> None:
    """Test validation of BIDS datatype specifications."""
    valid_path = Path("sub-001/ses-01/eeg/sub-001_ses-01_task-rest_eeg.vhdr")
    assert validate_bids_file(valid_path) is True

    invalid_path = Path("sub-001/ses-01/EEG/sub-001_ses-01_task-rest_eeg.vhdr")
    with pytest.raises(BidsValidationError):
        validate_bids_file(invalid_path)

    invalid_path = Path("sub-001/ses-01/$e$/sub-001_ses-01_task-rest_eeg.vhdr")
    with pytest.raises(BidsValidationError):
        validate_bids_file(invalid_path)


def test_validate_bids_file_entity_format() -> None:
    """Test validation of BIDS entity format in filenames."""
    valid_path = Path(
        "sub-001/ses-01/eeg/sub-001_ses-01_task-rest_run-01_eeg.vhdr"
    )
    assert validate_bids_file(valid_path) is True

    invalid_path = Path(
        "sub-001/ses-01/eeg/sub-001_ses01_task-rest_run-01_eeg.vhdr"
    )
    with pytest.raises(BidsValidationError):
        validate_bids_file(invalid_path)
