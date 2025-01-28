"""Tests for BIDS parsing functionality."""
import re
from pathlib import Path

import pytest

from bids_explorer.utils.parsing import parse_bids_filename


def test_parse_bids_filename_basic() -> None:
    """Test basic BIDS filename parsing with default patterns."""
    # Test a typical BIDS filename
    file = Path("sub-001/ses-01/eeg/sub-001_ses-01_task-rest_run-01_eeg.vhdr")
    result = parse_bids_filename(file)
    assert result["subject"] == "001"
    assert result["session"] == "01"
    assert result["task"] == "rest"
    assert result["run"] == "01"
    assert result["datatype"] == "eeg"
    assert result["suffix"] == "eeg"
    assert result["extension"] == ".vhdr"
    assert result["datatype"] == "eeg"

    # Test filename with acquisition and description
    file = Path(
        "sub-002/ses-02/eeg/sub-002_ses-02_task-test_acq-full_desc-raw_eeg.vhdr"
    )
    result = parse_bids_filename(file)
    assert result["subject"] == "002"
    assert result["session"] == "02"
    assert result["task"] == "test"
    assert result["acquisition"] == "full"
    assert result["description"] == "raw"
    assert result["suffix"] == "eeg"
    assert result["extension"] == ".vhdr"


def test_parse_bids_filename_custom_patterns() -> None:
    """Test BIDS filename parsing with custom regex patterns."""
    # Custom patterns to match specific formats
    custom_patterns = {
        "subject": r"sub-(\d{3})(?:[^0-9]|$)",
        "session": r"ses-(\d{2})",
        "task": r"task-([a-zA-Z]+)",
        "run": r"run-(\d+)",
        "space": r"space-([a-zA-Z0-9]+)",
    }

    # Test with valid patterns
    file = Path(
        "sub-001/ses-01/eeg/sub-001_ses-01_task-rest_run-1_space-MNI_eeg.vhdr"
    )
    result = parse_bids_filename(file, patterns=custom_patterns)
    assert result["subject"] == "001"
    assert result["session"] == "01"
    assert result["task"] == "rest"
    assert result["run"] == "1"
    assert result["space"] == "MNI"
    assert result["datatype"] == "eeg"

    # Test with invalid format (4-digit subject ID)
    file = Path("sub-0001/ses-01/eeg/sub-0001_ses-01_task-rest_eeg.vhdr")
    result = parse_bids_filename(file, patterns=custom_patterns)
    assert result["subject"] is None  # Should not match 4-digit subject

    # Test with invalid format (non-alphabetic task)
    file = Path("sub-001/ses-01/eeg/sub-001_ses-01_task-rest123_eeg.vhdr")
    result = parse_bids_filename(file, patterns=custom_patterns)
    assert result["task"] is None  # Should not match task with numbers


def test_parse_bids_filename_complex_patterns() -> None:
    """Test BIDS filename parsing with more complex regex patterns."""
    complex_patterns = {
        "subject": r"sub-((?:control|patient)\d+)",
        "session": r"ses-(pre|post)",
        "task": r"task-([a-zA-Z]+(?:-\d+)?)",
        "run": r"run-(\d+[a-z]?)",
    }

    # Test with control subject
    file = Path(
        "sub-control01/ses-pre/eeg/sub-control01_ses-pre_task-stroop-1_run-1a_eeg.vhdr"
    )
    result = parse_bids_filename(file, patterns=complex_patterns)
    assert result["subject"] == "control01"
    assert result["session"] == "pre"
    assert result["task"] == "stroop-1"
    assert result["run"] == "1a"

    # Test with patient subject
    file = Path(
        "sub-patient02/ses-post/eeg/sub-patient02_ses-post_task-rest_run-2_eeg.vhdr"
    )
    result = parse_bids_filename(file, patterns=complex_patterns)
    assert result["subject"] == "patient02"
    assert result["session"] == "post"
    assert result["task"] == "rest"
    assert result["run"] == "2"


def test_parse_bids_filename_invalid_patterns() -> None:
    """Test BIDS filename parsing with invalid regex patterns."""
    # Test with invalid regex pattern (unclosed group)
    invalid_patterns = {
        "subject": r"sub-([0-9",  # Invalid pattern - unclosed group
    }
    file = Path("sub-001/ses-01/eeg/sub-001_ses-01_task-rest_eeg.vhdr")
    with pytest.raises(re.error):
        parse_bids_filename(file, patterns=invalid_patterns)

    # Test with pattern without capturing group
    no_group_patterns = {
        "subject": r"sub-\d+",  # No capturing group
    }
    result = parse_bids_filename(file, patterns=no_group_patterns)
    assert (
        result["subject"] is None
    )  # Should not match without capturing group


def test_parse_bids_filename_edge_cases() -> None:
    """Test BIDS filename parsing with edge cases."""
    # Test with minimal filename
    file = Path("sub-001/eeg/sub-001_eeg.vhdr")
    result = parse_bids_filename(file)
    assert result["subject"] == "001"
    assert result["session"] is None
    assert result["task"] is None
    assert result["datatype"] == "eeg"

    # Test with all optional entities
    file = Path(
        "sub-001/ses-01/eeg/sub-001_ses-01_task-rest_acq-full_run-01_space-MNI_desc-raw_eeg.vhdr"
    )
    result = parse_bids_filename(file)
    assert result["subject"] == "001"
    assert result["session"] == "01"
    assert result["task"] == "rest"
    assert result["acquisition"] == "full"
    assert result["run"] == "01"
    assert result["space"] == "MNI"
    assert result["description"] == "raw"

    # Test with unusual but valid characters
    file = Path(
        "sub-001/ses-01/eeg/sub-001_ses-01_task-rest+memory_run-01_eeg.vhdr"
    )
    result = parse_bids_filename(file)
    assert result["subject"] == "001"
    assert result["task"] == "rest+memory"

    # Test with different file extensions
    file = Path("sub-001/ses-01/eeg/sub-001_ses-01_task-rest_eeg.set")
    result = parse_bids_filename(file)
    assert result["extension"] == ".set"
