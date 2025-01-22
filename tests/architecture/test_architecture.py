"""Tests for the BidsArchitecture class and related functionality."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bids_explorer.architecture.architecture import BidsArchitecture


@pytest.fixture
def bids_dataset(tmp_path: Path) -> Path:
    """Create a temporary BIDS dataset structure."""
    data_dir = tmp_path / "data"
    subjects = ["001", "002", "003", "004", "005"]
    sessions = ["01", "02"]
    runs = ["01", "02"]
    acquisitions = ["anAcq", "anotherAcq"]
    datatypes = ["eeg", "multimodal", "pupil"]

    for sub in subjects:
        for ses in sessions:
            for datatype in datatypes:
                for run in runs:
                    for acq in acquisitions:
                        base_path = (
                            data_dir / f"sub-{sub}" / f"ses-{ses}" / datatype
                        )
                        base_path.mkdir(parents=True, exist_ok=True)

                        files = [
                            (
                                f"sub-{sub}_ses-{ses}_task-aTask_{datatype}.vhdr",
                                "Brain Vision Data Exchange Header File\n",
                            ),
                            (
                                f"sub-{sub}_ses-{ses}_task-aTask_run-{run}_{datatype}.vhdr",
                                "Brain Vision Data Exchange Header File\n",
                            ),
                            (
                                f"sub-{sub}_ses-{ses}_task-aTask_acq-{acq}_run-01_{datatype}.vhdr",
                                "Brain Vision Data Exchange Header File\n",
                            ),
                        ]

                        for filename, content in files:
                            file_path = base_path / filename
                            file_path.write_text(content)

    return data_dir


@pytest.fixture
def invalid_bids_dataset(tmp_path: Path) -> Path:
    """Create a temporary BIDS dataset with invalid files."""
    data_dir = tmp_path / "data"

    invalid_files = [
        (
            "sub-001/ses-01/eeg/sub-001_ses-02_task-rest_eeg.vhdr",
            "Brain Vision Data Exchange Header File Version 1.0\n",
        ),
        (
            "sub-002/ses-01/eeg/sub-001_ses-01_task-rest_eeg.vhdr",
            "Brain Vision Data Exchange Header File Version 1.0\n",
        ),
        (
            "sub-003/ses-01/eeg/sub-003_sus-01_task-rest_eeg.vhdr",
            "Brain Vision Data Exchange Header File Version 1.0\n",
        ),
        (
            "sub-004/ses-01/eeg/sub-004_ses-01_run-badrun_eeg.vhdr",
            "Brain Vision Data Exchange Header File Version 1.0\n",
        ),
        (
            "sub-005/ses-01/eeg/sub-005_ses-01_task-invalid@task_eeg.vhdr",
            "Brain Vision Data Exchange Header File Version 1.0\n",
        ),
    ]

    for filepath, content in invalid_files:
        full_path = data_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    return data_dir


def test_architecture_database_creation(bids_dataset: Path) -> None:
    """Test database creation and basic properties."""
    arch = BidsArchitecture(root=bids_dataset)
    assert not arch.database.empty
    assert arch.subjects == ["001", "002", "003", "004", "005"]
    assert arch.sessions == ["01", "02"]
    assert arch.datatypes == ["eeg", "multimodal", "pupil"]
    assert arch.tasks == ["aTask"]
    assert arch.runs == ["01", "02"]
    assert arch.acquisitions == ["anAcq", "anotherAcq"]
    assert arch.suffixes == ["eeg", "multimodal", "pupil"]
    assert arch.extensions == [".vhdr"]


def test_architecture_select(bids_dataset: Path) -> None:
    """Test selection methods.

    References original test cases from:
    ```python:tests/test_bids_selector.py
    startLine: 137
    endLine: 173
    ```
    """
    arch = BidsArchitecture(root=bids_dataset)

    result = arch.select(subject="001")
    assert not arch.database.empty
    assert result.subjects == ["001"]
    assert len(result) == 30
    assert all(result.database["subject"] == "001")

    result = arch.select(subject="001", task="aTask")
    assert result.subjects == ["001"]
    assert result.tasks == ["aTask"]
    assert len(result) == 30

    result = arch.select(subject="001", task="aTask", run="01", session="01")
    assert result.subjects == ["001"]
    assert result.tasks == ["aTask"]
    assert result.runs == ["01"]
    assert result.sessions == ["01"]
    assert len(result) == 9

    result = arch.select(subject=["001", "002"])
    assert result.subjects == ["001", "002"]
    assert len(result) == 60

    with pytest.raises(ValueError, match="Invalid selection keys"):
        arch.select(invalid_key="value")

    result = arch.select(subject="001").select(task="aTask").select(run="01")
    assert len(result) == 18
    assert result.subjects == ["001"]
    assert result.tasks == ["aTask"]
    assert result.runs == ["01"]

    result = arch.select(subject="001", task="aTask", datatype="eeg", run="01")
    assert len(result) == 6
    assert result.subjects == ["001"]
    assert result.tasks == ["aTask"]
    assert result.runs == ["01"]

    result = arch.select(
        subject="001-003", task="aTask", datatype="eeg", run="01"
    )
    assert len(result) == 18
    assert result.subjects == ["001", "002", "003"]
    assert result.tasks == ["aTask"]
    assert result.runs == ["01"]

    result = arch.select(
        subject="001", task="nonExistingTask", datatype="eeg", run="01"
    )
    assert result.database.empty

    arch = BidsArchitecture(
        root=bids_dataset, subject="001", session="01", task="aTask", run="01"
    )
    assert arch.subjects == ["001"]
    assert arch.tasks == ["aTask"]
    assert arch.runs == ["01"]
    assert arch.sessions == ["01"]
    assert len(arch) == 9


def test_architecture_set_operations(bids_dataset: Path) -> None:
    """Test set operations between BidsArchitecture instances."""
    arch = BidsArchitecture(root=bids_dataset)
    arch.database
    arch1 = arch.select(subject=["001", "002"])
    arch2 = arch.select(subject=["002", "004"])

    print("\nDebug information:")
    print(f"arch1 subjects: {arch1.subjects}")
    print(f"arch1 database subjects:\n{arch1.database['subject'].unique()}")
    print(f"\narch2 subjects: {arch2.subjects}")
    print(f"arch2 database subjects:\n{arch2.database['subject'].unique()}")

    union = arch1 + arch2
    print(f"\nunion subjects: {union.subjects}")
    print(f"union database subjects:\n{union.database['subject'].unique()}")

    assert union.subjects == ["001", "002", "004"]

    diff = arch1 - arch2
    assert diff.subjects == ["001"]

    intersect = arch1 & arch2
    assert intersect.subjects == ["002"]


def test_architecture_representation(bids_dataset: Path) -> None:
    """Test string representation of BidsArchitecture."""
    arch = BidsArchitecture(root=bids_dataset)

    # Get the string representation
    repr_str = repr(arch)

    # Check that the representation contains all expected components
    assert "BidsArchitecture:" in repr_str
    assert "files" in repr_str
    assert "errors" in repr_str
    assert "subjects:" in repr_str
    assert "sessions:" in repr_str
    assert "datatypes:" in repr_str
    assert "tasks:" in repr_str

    # Test with specific values based on the bids_dataset fixture
    expected_repr = (
        "BidsArchitecture: 150 files, "
        "0 errors, "
        "subjects: 5, "
        "sessions: 2, "
        "datatypes: 3, "
        "tasks: 1"
    )
    assert repr(arch) == expected_repr

    # Test that str() returns the same as repr()
    assert str(arch) == repr(arch)

    # Test empty architecture
    empty_arch = BidsArchitecture()
    empty_repr = (
        "BidsArchitecture: 0 files, "
        "0 errors, "
        "subjects: 0, "
        "sessions: 0, "
        "datatypes: 0, "
        "tasks: 0"
    )
    assert repr(empty_arch) == empty_repr


def test_getitem() -> None:
    """Test the __getitem__ functionality of BidsArchitecture."""
    # Create test data
    test_data = {
        "root": ["path1", "path2"],
        "subject": ["01", "02"],
        "session": ["01", "02"],
        "datatype": ["eeg", "eeg"],
        "task": ["rest", "task"],
        "run": ["01", "02"],
        "acquisition": ["full", "full"],
        "description": ["desc", "desc"],
        "suffix": ["eeg", "eeg"],
        "extension": [".vhdr", ".vhdr"],
        "atime": [1000, 2000],
        "mtime": [1000, 2000],
        "ctime": [1000, 2000],
        "filename": ["file1.vhdr", "file2.vhdr"],
    }

    # Create DataFrame with specific index
    df = pd.DataFrame(test_data, index=[1, 2])

    # Create BidsArchitecture instance and set the database
    bids = BidsArchitecture()
    bids._database = df

    # Test getting item by index
    result = bids[0]
    assert isinstance(result, pd.Series)
    assert result["subject"] == "01"
    assert result["session"] == "01"

    # Test getting item by negative index
    result = bids[-1]
    assert isinstance(result, pd.Series)
    assert result["subject"] == "02"
    assert result["session"] == "02"

    # Test index out of bounds
    with pytest.raises(IndexError):
        _ = bids[len(df)]


def test_getitem_operations() -> None:
    """Test indexing operations on BidsArchitecture."""
    # Create test data
    test_data = pd.DataFrame(
        {
            "root": ["path1", "path2", "path3"],
            "subject": ["01", "02", "03"],
            "session": ["01", "02", "03"],
            "datatype": ["eeg", "eeg", "eeg"],
            "task": ["rest", "task", "test"],
            "run": ["01", "02", "03"],
            "acquisition": ["full", "full", "full"],
            "description": ["desc", "desc", "desc"],
            "suffix": ["eeg", "eeg", "eeg"],
            "extension": [".vhdr", ".vhdr", ".vhdr"],
            "atime": [1000, 2000, 3000],
            "mtime": [1000, 2000, 3000],
            "ctime": [1000, 2000, 3000],
            "filename": ["file1.vhdr", "file2.vhdr", "file3.vhdr"],
        }
    )

    # Create BidsArchitecture instance
    bids = BidsArchitecture()
    bids._database = test_data

    # Test positive indexing
    first_item = bids[0]
    assert isinstance(first_item, pd.Series)
    assert first_item["subject"] == "01"
    assert first_item["session"] == "01"

    # Test negative indexing
    last_item = bids[-1]
    assert isinstance(last_item, pd.Series)
    assert last_item["subject"] == "03"
    assert last_item["session"] == "03"

    # Test index out of bounds
    with pytest.raises(IndexError):
        _ = bids[len(test_data)]

    # Test setting items (should raise NotImplementedError)
    with pytest.raises(NotImplementedError):
        bids[0] = pd.Series()


def test_iteration_and_properties() -> None:
    """Test iteration and property setters of BidsArchitecture."""
    # Create test data
    test_data = pd.DataFrame(
        {
            "root": ["path1", "path2"],
            "subject": ["01", "02"],
            "session": ["01", "02"],
            "datatype": ["eeg", "eeg"],
            "task": ["rest", "task"],
            "run": ["01", "02"],
            "acquisition": ["full", "full"],
            "description": ["desc", "desc"],
            "suffix": ["eeg", "eeg"],
            "extension": [".vhdr", ".vhdr"],
            "atime": [1000, 2000],
            "mtime": [1000, 2000],
            "ctime": [1000, 2000],
            "filename": ["file1.vhdr", "file2.vhdr"],
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test __iter__
    for i, item in enumerate(bids):
        assert isinstance(item, pd.Series)
        assert item["subject"] == test_data.iloc[i]["subject"]
        assert item["session"] == test_data.iloc[i]["session"]

    # Verify length
    assert len(list(bids)) == 2

    # Test database property setter
    new_data = test_data.copy()
    bids._database = new_data
    pd.testing.assert_frame_equal(bids._database, new_data)

    # Test errors property setter
    error_data = pd.DataFrame(
        {
            "error_message": ["Error 1", "Error 2"],
            "filename": ["file1.txt", "file2.txt"],
        }
    )
    bids.errors = error_data
    pd.testing.assert_frame_equal(bids._errors, error_data)

    # Test empty database case
    empty_bids = BidsArchitecture()
    assert len(list(empty_bids)) == 0
    assert empty_bids.subjects == []
    assert empty_bids.sessions == []
    assert empty_bids.datatypes == []

    # Test invalid database setter
    invalid_df = pd.DataFrame({"invalid_column": [1, 2, 3]})
    with pytest.raises(
        ValueError, match="Invalid or missing columns in" " database"
    ):
        bids.database = invalid_df


def test_get_unique_values() -> None:
    """Test getting unique values from database columns."""
    # Create test data with duplicates and None values
    test_data = pd.DataFrame(
        {
            "root": ["path1", "path1", "path2", None],
            "subject": ["01", "01", "02", "03"],
            "session": ["01", "01", "02", None],
            "datatype": ["eeg", "eeg", "meg", None],
            "task": ["rest", "rest", "task", np.nan],
            "run": ["01", "01", "02", None],
            "acquisition": ["full", "full", None, None],
            "description": ["desc", "desc", "", np.nan],
            "suffix": ["eeg", "eeg", "meg", None],
            "extension": [".vhdr", ".vhdr", ".fif", None],
            "filename": ["file1.vhdr", "file1.vhdr", "file2.fif", "file3.txt"],
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test unique values with duplicates
    assert bids.subjects == ["01", "02", "03"]
    assert bids.sessions == ["01", "02"]  # None values should be filtered
    assert bids.datatypes == ["eeg", "meg"]  # None values should be filtered

    # Test property access for other columns
    assert isinstance(bids.tasks, list)
    assert isinstance(bids.runs, list)
    assert isinstance(bids.acquisitions, list)
    assert isinstance(bids.descriptions, list)
    assert isinstance(bids.suffixes, list)
    assert isinstance(bids.extensions, list)

    # Test with empty database
    empty_bids = BidsArchitecture()
    assert empty_bids._get_unique_values("subject") == []
    assert empty_bids._get_unique_values("session") == []


def test_get_range() -> None:
    """Test the _get_range method with various inputs."""
    test_data = pd.DataFrame(
        {
            "numeric_col": ["1", "2", "3", "4", "5"],
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test with numeric strings
    result = bids._get_range(test_data["numeric_col"], "2", "4")
    assert list(result) == [False, True, True, False, False]

    result = bids._get_range(test_data["numeric_col"], "02", "04")
    assert list(result) == [False, True, True, False, False]

    # Test with integers
    result = bids._get_range(test_data["numeric_col"], 2, 4)
    assert list(result) == [False, True, True, False, False]

    # Test with None/wildcard for stop
    result = bids._get_range(test_data["numeric_col"], None, "04")
    assert list(result) == [True, True, True, False, False]

    # Test with None/wildcard for start
    result = bids._get_range(test_data["numeric_col"], "002", None)
    assert list(result) == [False, True, True, True, True]


def test_get_single_loc() -> None:
    """Test the _get_single_loc method."""
    test_data = pd.DataFrame(
        {
            "col": ["a", "b", "c", "d"],
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test existing value
    result = bids._get_single_loc(test_data["col"], "b")
    assert list(result) == [False, True, False, False]

    # Test non-existing value (should warn and return inverted mask)
    with pytest.warns(
        UserWarning, match="No location corresponding found in the database"
    ):
        result = bids._get_single_loc(test_data["col"], "x")
        assert not any(result)


def test_is_numerical() -> None:
    """Test the _is_numerical method."""
    test_data = pd.DataFrame(
        {
            "numeric": ["1", "2", "3"],
            "mixed": ["1", "a", "3"],
            "non_numeric": ["a", "b", "c"],
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    assert bids._is_numerical(test_data["numeric"]) is True
    assert bids._is_numerical(test_data["mixed"]) is False
    assert bids._is_numerical(test_data["non_numeric"]) is False


def test_interpret_string() -> None:
    """Test the _interpret_string method."""
    test_data = pd.DataFrame(
        {
            "numeric_col": ["01", "02", "03", "04", "05"],
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test range pattern
    result = bids._interpret_string(test_data["numeric_col"], "02-04")
    assert list(result) == [False, True, True, False, False]

    # Test wildcard range
    result = bids._interpret_string(test_data["numeric_col"], "*-04")
    assert list(result) == [True, True, True, False, False]

    result = bids._interpret_string(test_data["numeric_col"], "02-*")
    assert list(result) == [False, True, True, True, True]

    # Test invalid range format
    with pytest.raises(
        ValueError, match="Input must be 2 digits separated by a `-`"
    ):
        bids._interpret_string(test_data["numeric_col"], "a-b")


def test_errors_display() -> None:
    """Test error display functionality."""
    bids = BidsArchitecture()

    # Test empty errors
    assert bids.errors.empty

    # Create test error data
    error_data = pd.DataFrame(
        {
            "error_message": ["Error 1", "Error 2"],
            "error_type": ["type1", "type2"],
            "filename": ["file1.txt", "file2.txt"],
        }
    )

    # Test with errors
    bids.errors = error_data
    assert not bids.errors.empty
    assert len(bids.errors) == 2
    assert list(bids.errors["error_type"].unique()) == ["type1", "type2"]


def test_get_range_edge_cases() -> None:
    """Test edge cases for the _get_range method."""
    test_data = pd.DataFrame(
        {
            "numeric_col": ["1", "2", "3", "4", "5"],
            "mixed_col": [
                "1",
                "a",
                "3",
                "b",
                "5",
            ],  # Contains non-numeric values
            "empty_col": ["", "", "", "", ""],  # Empty strings
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test with non-numeric column
    with pytest.raises(ValueError):
        bids._get_range(test_data["mixed_col"], "1", "3")

    # Test with empty strings
    with pytest.raises(ValueError):
        bids._get_range(test_data["empty_col"], "1", "3")

    # Test with invalid range (start > stop)
    result = bids._get_range(test_data["numeric_col"], "4", "2")
    assert not any(result)  # Should return all False

    # Test with equal start and stop
    result = bids._get_range(test_data["numeric_col"], "2", "2")
    assert not any(result)  # Should return all False


def test_get_single_loc_edge_cases() -> None:
    """Test edge cases for the _get_single_loc method."""
    test_data = pd.DataFrame(
        {
            "col": ["a", "b", "", None, np.nan],
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test with empty string
    result = bids._get_single_loc(test_data["col"], "")
    assert list(result) == [False, False, True, False, False]

    # Test with None
    with pytest.warns(UserWarning):
        result = bids._get_single_loc(test_data["col"], None)
        assert not any(result)

    # Test with numeric value for string column
    with pytest.warns(UserWarning):
        result = bids._get_single_loc(test_data["col"], "123")
        assert not any(result)


def test_interpret_string_edge_cases() -> None:
    """Test edge cases for the _interpret_string method."""
    test_data = pd.DataFrame(
        {
            "numeric_col": ["1", "2", "3", "4", "5"],
            "text_col": ["a", "b", "c", "d", "e"],
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test invalid range format
    with pytest.raises(
        ValueError, match="Input must be 2 digits separated by a `-`"
    ):
        bids._interpret_string(test_data["numeric_col"], "a-b")

    with pytest.raises(
        ValueError, match="Input must be 2 digits separated by a `-`"
    ):
        bids._interpret_string(test_data["numeric_col"], "1-b")

    # Test with empty string
    with pytest.warns(UserWarning):
        result = bids._interpret_string(test_data["numeric_col"], "")
        assert not any(result)

    # Test with non-range string on numeric column
    with pytest.warns(UserWarning):
        result = bids._interpret_string(test_data["numeric_col"], "abc")
        assert not any(result)

    # Test with range pattern on text column
    with pytest.raises(ValueError):
        bids._interpret_string(test_data["text_col"], "1-3")


def test_database_initialization() -> None:
    """Test database initialization and validation."""
    # Test initialization with valid DataFrame
    valid_df = pd.DataFrame(
        {
            "root": ["path1"],
            "subject": ["01"],
            "session": ["01"],
            "datatype": ["eeg"],
            "task": ["rest"],
            "run": ["01"],
            "acquisition": ["full"],
            "description": ["desc"],
            "suffix": ["eeg"],
            "extension": [".vhdr"],
            "atime": [1000],
            "mtime": [1000],
            "ctime": [1000],
            "filename": ["file1.vhdr"],
        }
    )

    bids = BidsArchitecture()
    bids.database = valid_df
    pd.testing.assert_frame_equal(bids._database, valid_df)

    # Test initialization with extra columns
    invalid_df = valid_df.copy()
    invalid_df["extra_col"] = ["extra"]
    with pytest.raises(
        ValueError, match="Invalid or missing columns in" " database"
    ):
        bids.database = invalid_df


def test_select_edge_cases() -> None:
    """Test edge cases in the select method."""
    test_data = pd.DataFrame(
        {
            "root": ["path1", "path2"],
            "subject": ["01", "02"],
            "session": ["01", "02"],
            "datatype": ["eeg", "meg"],
            "task": ["rest", "task"],
            "run": ["01", "02"],
            "acquisition": ["full", None],
            "description": ["desc", ""],
            "suffix": ["eeg", "meg"],
            "extension": [".vhdr", ".fif"],
            "atime": [1000, 2000],
            "mtime": [1000, 2000],
            "ctime": [1000, 2000],
            "filename": ["file1.vhdr", "file2.fif"],
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test selection with empty string
    result = bids.select(subject="")
    assert result.database.empty

    # Test selection with non-existent value
    result = bids.select(subject="999")
    assert result.database.empty

    # Test selection with multiple values including None
    result = bids.select(acquisition=[None, "full"])
    assert len(result) == 2

    # Test selection with empty list
    result = bids.select(subject=[])
    assert result.database.empty


def test_property_edge_cases() -> None:
    """Test edge cases for properties."""
    bids = BidsArchitecture()

    # Test properties with empty database
    assert bids.subjects == []
    assert bids.sessions == []
    assert bids.datatypes == []
    assert bids.tasks == []
    assert bids.runs == []
    assert bids.acquisitions == []
    assert bids.descriptions == []
    assert bids.suffixes == []
    assert bids.extensions == []

    # Test with database containing only None/empty values
    test_data = pd.DataFrame(
        {
            "root": [None, None],
            "subject": ["", ""],
            "session": [None, None],
            "datatype": ["", ""],
            "task": [None, None],
            "run": ["", ""],
            "acquisition": [None, None],
            "description": ["", ""],
            "suffix": [None, None],
            "extension": ["", ""],
            "atime": [None, None],
            "mtime": [None, None],
            "ctime": [None, None],
            "filename": ["", ""],
        }
    )

    bids._database = test_data
    assert bids.subjects == []
    assert bids.sessions == []
    assert bids.datatypes == []
    assert bids.tasks == []
    assert bids.runs == []
    assert bids.acquisitions == []
    assert bids.descriptions == []
    assert bids.suffixes == []
    assert bids.extensions == []


def test_get_range_invalid_types() -> None:
    """Test _get_range with invalid type conversions."""
    test_data = pd.DataFrame(
        {
            "numeric_col": ["1", "2", "3", "4", "5"],
            "invalid_col": ["a", "b", "c", "d", "e"],
        }
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test with non-convertible string values
    with pytest.raises(ValueError):
        bids._get_range(test_data["invalid_col"], "1", "3")

    # Test with invalid types
    with pytest.raises(
        ValueError, match="Start and stop must be integers, strings, or None"
    ):
        bids._get_range(test_data["numeric_col"], [], "3")  # type: ignore

    with pytest.raises(
        ValueError, match="Start and stop must be integers, strings, or None"
    ):
        bids._get_range(test_data["numeric_col"], "1", {})  # type: ignore

    with pytest.raises(
        ValueError, match="Start and stop must be integers, strings, or None"
    ):
        bids._get_range(test_data["numeric_col"], dict(), "3")  # type: ignore


def test_get_single_loc_comprehensive() -> None:
    """Test _get_single_loc with various value types."""
    test_data = pd.DataFrame({"col": ["a", "b", "c", None, np.nan]})

    bids = BidsArchitecture()
    bids._database = test_data

    # Test with None value
    with pytest.warns(UserWarning):
        result = bids._get_single_loc(test_data["col"], None)  # type: ignore
        assert not any(result)

    # Test with numeric value
    with pytest.warns(UserWarning):
        result = bids._get_single_loc(test_data["col"], 123)  # type: ignore
        assert not any(result)


def test_create_mask() -> None:
    """Test the _create_mask method with various filtering scenarios."""
    test_data = pd.DataFrame(
        {
            "root": ["path1", "path2", "path3"],
            "subject": ["001", "002", "003"],
            "session": ["01", "02", "03"],
            "datatype": ["eeg", "meg", "eeg"],
            "task": ["rest", "task", "rest"],
            "run": ["01", "02", "03"],
            "acquisition": ["full", None, "partial"],
            "description": ["desc1", "", "desc3"],
            "suffix": ["eeg", "meg", "eeg"],
            "extension": [".vhdr", ".fif", ".vhdr"],
            "atime": [1000, 2000, 3000],
            "mtime": [1000, 2000, 3000],
            "ctime": [1000, 2000, 3000],
            "filename": ["file1.vhdr", "file2.fif", "file3.vhdr"],
        },
        index=[1465, 2241, 3123],
    )

    bids = BidsArchitecture()
    bids._database = test_data

    # Test basic single value filtering
    mask = bids._create_mask(subject="001")
    assert list(mask) == [True, False, False]

    # Test multiple criteria
    mask = bids._create_mask(subject="001", datatype="eeg")
    assert list(mask) == [True, False, False]

    # Test numerical range with hyphen
    mask = bids._create_mask(subject="001-002")
    assert list(mask) == [True, True, False]

    # Test with wildcard range
    mask = bids._create_mask(subject="002-*")
    assert list(mask) == [False, True, True]

    # Test with list of values
    mask = bids._create_mask(datatype=["eeg", "meg"])
    assert list(mask) == [True, True, True]

    # Test with invalid key
    with pytest.raises(ValueError, match="Invalid selection keys"):
        bids._create_mask(invalid_key="value")

    # Test with multiple ranges
    mask = bids._create_mask(subject="001-002", run="01-02")
    assert list(mask) == [True, True, False]

    # Test with mixed criteria (range and exact match)
    mask = bids._create_mask(subject="001-003", datatype="eeg")
    assert list(mask) == [True, False, True]
