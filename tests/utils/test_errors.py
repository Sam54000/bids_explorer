"""Tests for error handling utilities."""
import pandas as pd
import pytest

from bids_explorer.core.mixins import BidsArchitectureMixin
from bids_explorer.utils.errors import merge_error_logs, set_errors


class TestBidsArchitecture(BidsArchitectureMixin):
    """Test class implementing BidsArchitectureMixin."""

    def __init__(self, errors=None) -> None:  # noqa: ANN001
        """Initialize test class with optional errors."""
        self._errors = errors if errors is not None else pd.DataFrame()
        self._database = pd.DataFrame()


def test_set_errors() -> None:
    """Test setting error DataFrame on an object."""
    # Test setting new errors
    arch = TestBidsArchitecture()
    new_errors = pd.DataFrame(
        {
            "error_message": ["Error 1", "Error 2"],
            "filename": ["file1.txt", "file2.txt"],
            "inode": [1, 2],
        }
    )
    set_errors(arch, new_errors)
    pd.testing.assert_frame_equal(arch._errors, new_errors)

    # Test overwriting existing errors
    updated_errors = pd.DataFrame(
        {
            "error_message": ["Error 3"],
            "filename": ["file3.txt"],
            "inode": [3],
        }
    )
    set_errors(arch, updated_errors)
    pd.testing.assert_frame_equal(arch._errors, updated_errors)


def test_merge_error_logs() -> None:
    """Test merging error logs from two objects."""
    # Create test error DataFrames
    errors1 = pd.DataFrame(
        {
            "error_message": ["Error 1", "Error 2"],
            "filename": ["file1.txt", "file2.txt"],
        },
        index=[1, 2],
    )
    errors2 = pd.DataFrame(
        {
            "error_message": ["Error 2", "Error 3"],
            "filename": ["file2.txt", "file3.txt"],
        },
        index=[2, 3],
    )

    arch1 = TestBidsArchitecture()
    arch1._errors = errors1
    arch2 = TestBidsArchitecture()
    arch2._errors = errors2

    merged = merge_error_logs(arch1, arch2)

    # Check that merged DataFrame has correct number of rows
    # (3 unique errors across both DataFrames)
    assert len(merged) == 3

    # Check that all error messages are present
    assert set(merged["error_message"]) == {"Error 1", "Error 2", "Error 3"}

    # Check that all filenames are present
    assert set(merged["filename"]) == {
        "file1.txt",
        "file2.txt",
        "file3.txt",
    }


def test_merge_error_logs_empty() -> None:
    """Test merging error logs when one or both are empty."""
    # Create test objects
    empty_arch = TestBidsArchitecture()
    errors = pd.DataFrame(
        {
            "error_message": ["Error 1"],
            "filename": ["file1.txt"],
            "inode": [1],
        }
    )
    non_empty_arch = TestBidsArchitecture(errors)

    # Test merging with empty error log
    merged = merge_error_logs(empty_arch, non_empty_arch)
    pd.testing.assert_frame_equal(merged, errors)

    # Test merging two empty error logs
    empty_merged = merge_error_logs(empty_arch, empty_arch)
    assert empty_merged.empty


def test_merge_error_logs_missing_attributes() -> None:
    """Test merging error logs with missing attributes."""

    class InvalidArchitecture:
        """Test class without required attributes."""

        pass

    arch1 = TestBidsArchitecture()
    arch2 = InvalidArchitecture()

    # Test merging with object missing error logs
    with pytest.raises(AttributeError):
        merge_error_logs(arch1, arch2)
