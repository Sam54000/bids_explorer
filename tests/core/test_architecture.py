"""Tests for the BidsArchitecture class and related functionality."""
from pathlib import Path

import pytest

from bids_explorer.core.architecture import BidsArchitecture


@pytest.fixture
def bids_dataset(tmp_path: Path) -> Path:
    """Create a temporary BIDS dataset structure."""
    data_dir = tmp_path / "data"
    subjects = ["001", "002", "003", "004", "005"]  # Reduced set for clearer testing
    ses = "01"
    run = "01"
    acq = "anAcq"
    desc = "aDescription"

    for sub in subjects:
        base_path = data_dir / f"sub-{sub}" / f"ses-{ses}" / "eeg"
        base_path.mkdir(parents=True, exist_ok=True)

        # Create files with minimal content to make them valid BIDS files
        files = [
            (f"sub-{sub}_ses-{ses}_task-aTask_eeg.vhdr", 
             "Brain Vision Data Exchange Header File Version 1.0\n"),
            (f"sub-{sub}_ses-{ses}_task-aTask_run-{run}_eeg.vhdr", 
             "Brain Vision Data Exchange Header File Version 1.0\n"),
            (f"sub-{sub}_ses-{ses}_task-aTask_acq-{acq}_run-01_eeg.vhdr", 
             "Brain Vision Data Exchange Header File Version 1.0\n"),
        ]

        for filename, content in files:
            file_path = base_path / filename
            file_path.write_text(content)

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
    assert arch.subjects == ["001", "002", "003", "004", "005"]
    assert arch.sessions == ["01"]
    assert arch.datatypes == ["eeg"]
    assert arch.tasks == ["aTask"]
    assert arch.runs == ["01"]
    assert arch.acquisitions == ["anAcq"]
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
    # Initialize architectures and create their databases
    arch = BidsArchitecture(root=bids_dataset)
    arch1 = arch.select(subject=["001", "002"])
    arch2 = arch.select(subject=["002", "004"])

    # Debug prints
    print("\nDebug information:")
    print(f"arch1 subjects: {arch1.subjects}")
    print(f"arch1 database subjects:\n{arch1.database['subject'].unique()}")
    print(f"\narch2 subjects: {arch2.subjects}")
    print(f"arch2 database subjects:\n{arch2.database['subject'].unique()}")

    # Union
    union = arch1 + arch2
    print(f"\nunion subjects: {union.subjects}")
    print(f"union database subjects:\n{union.database['subject'].unique()}")

    assert union.subjects == ["001", "002", "004"]

    # Difference
    diff = arch1 - arch2
    assert diff.subjects == ["001"]

    # Intersection
    intersect = arch1 & arch2
    assert intersect.subjects == ["002"]

def test_architecture_error_handling(bids_dataset: Path) -> None:
    """Test error handling during database creation."""
    # First create the architecture and database
    arch = BidsArchitecture(root=bids_dataset)
    arch.create_database_and_error_log()
    
    # Create an invalid file that looks more like a BIDS file
    invalid_file = (
        bids_dataset / "sub-001" / "ses-01" / "eeg" / 
        "sub-001_ses-02_invalid-task_run-badrun_eeg.vhdr"
    )
    invalid_file.touch()

    # Debug prints
    print("\nBefore recreation:")
    print(f"Files in directory: {list(bids_dataset.rglob('*.vhdr'))}")
    print(f"Invalid file exists: {invalid_file.exists()}")
    
    # Recreate the database to pick up the new invalid file
    arch.create_database_and_error_log()

    # Debug prints
    print("\nAfter recreation:")
    print("Database:")
    print(arch.database)
    print("\nError log:")
    print(arch.errors)
    print(f"Error log empty: {arch.errors.empty}")
    print(f"Error log columns: {arch.errors.columns}")
    print(f"Error log shape: {arch.errors.shape}")

    # Check error log
    assert not arch.errors.empty, "Error log should not be empty"
    assert "sub-001_ses-02_invalid-task_run-badrun_eeg.vhdr" in str(arch.errors["filename"].iloc[0])
