"""Tests for the BidsArchitecture class and related functionality."""
from pathlib import Path

import pytest

from bids_explorer.core.architecture import BidsArchitecture


@pytest.fixture
def bids_dataset(tmp_path: Path) -> Path:
    """Create a temporary BIDS dataset structure.

    References original test setup from:
    ```python:tests/test_bids_selector.py
    startLine: 11
    endLine: 38
    ```
    """
    data_dir = tmp_path / "data"
    subjects = ["001", "002", "003"]
    ses = "01"
    run = "01"
    acq = "anAcq"
    desc = "aDescription"

    for sub in subjects:
        base_path = data_dir / f"sub-{sub}" / f"ses-{ses}" / "eeg"
        base_path.mkdir(parents=True, exist_ok=True)

        files = [
            f"sub-{sub}_ses-{ses}_task-aTask_eeg.vhdr",
            f"sub-{sub}_ses-{ses}_task-aTask_run-{run}_eeg.vhdr",
            f"sub-{sub}_ses-{ses}_task-aTask_acq-{acq}_run-01_eeg.vhdr",
            f"sub-{sub}_ses-{ses}_task-aTask_acq-{acq}_run-01_desc-{desc}_eeg.vhdr",
        ]

        for file in files:
            (base_path / file).touch()

    return data_dir


def test_architecture_initialization() -> None:
    """Test BidsArchitecture initialization."""
    # Test empty initialization
    arch = BidsArchitecture()
    assert arch._database.empty
    assert arch._errors.empty
    assert arch.root is None


def test_architecture_database_creation(bids_dataset: Path) -> None:
    """Test database creation and basic properties."""
    arch = BidsArchitecture(root=bids_dataset)
    arch.create_database_and_error_log()

    # Test database structure
    print(arch.errors.iloc[0]["error_message"])
    assert arch.errors.empty
    assert not arch.database.empty
    assert set(arch.database.columns).issuperset(
        {
            "subject",
            "session",
            "datatype",
            "task",
            "run",
            "acquisition",
            "description",
            "suffix",
            "extension",
        }
    )

    # Test basic properties
    assert arch.subjects == ["001", "002", "003"]
    assert arch.sessions == ["01"]
    assert arch.datatypes == ["eeg"]
    assert arch.tasks == ["aTask"]
    assert arch.runs == ["01"]
    assert arch.acquisitions == ["anAcq"]
    assert arch.descriptions == ["aDescription"]
    assert arch.suffixes == ["eeg"]
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

    # Single criterion
    result = arch.select(subject="001")
    assert len(result) > 0
    assert all(result.database["subject"] == "001")

    # Multiple criteria
    result = arch.select(subject="001", task="aTask")
    assert len(result) > 0
    assert all(result.database["subject"] == "001")
    assert all(result.database["task"] == "aTask")

    # List of values
    result = arch.select(subject=["001", "002"])
    assert len(result) > 0
    assert all(result.database["subject"].isin(["001", "002"]))

    # Empty result
    result = arch.select(subject="nonexistent")
    assert len(result) == 0

    # Invalid key
    with pytest.raises(ValueError, match="Invalid selection keys"):
        arch.select(invalid_key="value")

    # Chained selection
    result = arch.select(subject="001").select(task="aTask").select(run="01")
    assert len(result) > 0
    assert all(result.database["subject"] == "001")
    assert all(result.database["task"] == "aTask")
    assert all(result.database["run"] == "01")


def test_architecture_set_operations(bids_dataset: Path) -> None:
    """Test set operations between BidsArchitecture instances."""
    arch1 = BidsArchitecture(root=bids_dataset).select(subject=["001", "002"])
    arch2 = BidsArchitecture(root=bids_dataset).select(subject=["002", "003"])

    # Union
    union = arch1 + arch2
    assert set(union.subjects) == {"001", "002", "003"}

    # Difference
    diff = arch1 - arch2
    assert set(diff.subjects) == {"001"}

    # Intersection
    intersect = arch1 & arch2
    assert set(intersect.subjects) == {"002"}

    # Symmetric difference
    sym_diff = arch1 ^ arch2
    assert set(sym_diff.subjects) == {"001", "003"}


def test_architecture_error_handling(bids_dataset: Path) -> None:
    """Test error handling during database creation."""
    # Create an invalid file
    invalid_file = (
        bids_dataset / "sub-001" / "ses-01" / "eeg" / "invalid_file.vhdr"
    )
    invalid_file.touch()

    arch = BidsArchitecture(root=bids_dataset)

    # Check error log
    assert not arch.errors.empty
    assert "invalid_file.vhdr" in str(arch.errors["filename"].iloc[0])
