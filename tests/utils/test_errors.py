"""Tests for error handling utilities."""
import pandas as pd
import pytest

from bids_explorer.architecture.mixins import BidsArchitectureMixin
from bids_explorer.utils.errors import merge_error_logs


class TestBidsArchitecture(BidsArchitectureMixin):
    """Test class implementing BidsArchitectureMixin."""

    def __init__(self, errors: pd.DataFrame | None = None) -> None:
        """Initialize test class with optional errors."""
        self._errors = errors if errors is not None else pd.DataFrame()
        self._database = pd.DataFrame()


def test_merge_error_logs() -> None:
    """Test merging error logs from two objects."""
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

    assert len(merged) == 3

    assert set(merged["error_message"]) == {"Error 1", "Error 2", "Error 3"}

    assert set(merged["filename"]) == {
        "file1.txt",
        "file2.txt",
        "file3.txt",
    }


def test_merge_error_logs_empty() -> None:
    """Test merging error logs when one or both are empty."""
    empty_arch = TestBidsArchitecture()
    errors = pd.DataFrame(
        {
            "error_message": ["Error 1"],
            "filename": ["file1.txt"],
            "inode": [1],
        }
    )
    non_empty_arch = TestBidsArchitecture(errors)

    merged = merge_error_logs(empty_arch, non_empty_arch)
    pd.testing.assert_frame_equal(merged, errors)

    empty_merged = merge_error_logs(empty_arch, empty_arch)
    assert empty_merged.empty


def test_merge_error_logs_missing_attributes() -> None:
    """Test merging error logs with missing attributes."""

    class InvalidArchitecture(BidsArchitectureMixin):
        """Test class without required attributes."""

        pass

    arch1 = TestBidsArchitecture()
    arch2 = InvalidArchitecture()

    with pytest.raises(AttributeError):
        merge_error_logs(arch1, arch2)
