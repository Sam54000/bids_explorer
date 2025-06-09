"""Tests for BIDS architecture mixin functionality."""
import pandas as pd
import pytest

from bids_explorer.architecture.mixins import (
    BidsArchitectureMixin,
    prepare_for_operations,
)


class TestBidsArchitecture(BidsArchitectureMixin):
    """Test class implementing BidsArchitectureMixin."""

    def __init__(self, database: pd.DataFrame | None = None) -> None:
        """Initialize test class with optional database."""
        self._database = database if database is not None else pd.DataFrame()
        self._errors = pd.DataFrame()


def test_prepare_for_operations_valid() -> None:
    """Test prepare_for_operations with valid inputs."""
    columns = [
        "root",
        "subject",
        "session",
        "datatype",
        "task",
        "run",
        "acquisition",
        "recording",
        "description",
        "suffix",
        "extension",
        "atime",
        "mtime",
        "ctime",
        "filename",
    ]
    df1 = pd.DataFrame({col: [1, 2, 3] for col in columns}, index=[1, 2, 3])
    df2 = pd.DataFrame({col: [2, 3, 4] for col in columns}, index=[2, 3, 4])

    arch1 = TestBidsArchitecture(df1)
    arch2 = TestBidsArchitecture(df2)

    result = prepare_for_operations(arch1, arch2)
    assert isinstance(result, pd.Index)
    assert list(result) == [2, 3, 4]

    result = prepare_for_operations(arch1, df2)
    assert isinstance(result, pd.Index)
    assert list(result) == [2, 3, 4]

    test_set = {2, 3, 4}
    result = prepare_for_operations(arch1, test_set)
    assert result == {2, 3, 4}


def test_prepare_for_operations_invalid() -> None:
    """Test prepare_for_operations with invalid inputs."""
    columns = [
        "root",
        "subject",
        "session",
        "datatype",
        "task",
        "run",
        "acquisition",
        "recording",
        "description",
        "suffix",
        "extension",
        "atime",
        "mtime",
        "ctime",
        "filename",
    ]
    df1 = pd.DataFrame({col: [1, 2, 3] for col in columns}, index=[1, 2, 3])
    arch = TestBidsArchitecture(df1)

    with pytest.raises(
        TypeError,
        match="Cannot perform operations between types TestBidsArchitecture"
        " and str",
    ):
        prepare_for_operations(arch, "invalid")

    invalid_df = pd.DataFrame({"invalid_col": [1, 2, 3]})
    arch_invalid = TestBidsArchitecture(invalid_df)

    with pytest.raises(
        ValueError,
        match="has invalid columns",
    ):
        prepare_for_operations(arch, arch_invalid)
