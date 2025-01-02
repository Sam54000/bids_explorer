"""Tests for the BidsArchitecture class and related functionality."""
from pathlib import Path

import pytest

from bids_explorer.core.architecture import BidsArchitecture


@pytest.fixture
def bids_dataset(tmp_path: Path) -> Path:
    """Create a temporary BIDS dataset structure."""
    data_dir = tmp_path / "data"
    subjects = ["001", "002", "003", "004", "005"]
    sessions = ["01", "02"]
    runs = ["01", "02"]
    acquisitions = ["anAcq", "anotherAcq"]

    for sub in subjects:
        for ses in sessions:
            for run in runs:
                for acq in acquisitions:
                    base_path = data_dir / f"sub-{sub}" / f"ses-{ses}" / "eeg"
                    base_path.mkdir(parents=True, exist_ok=True)

                    # Create files with minimal content to make them valid BIDS files
                    files = [
                        (
                            f"sub-{sub}_ses-{ses}_task-aTask_eeg.vhdr",
                            "Brain Vision Data Exchange Header File\n",
                        ),
                        (
                            f"sub-{sub}_ses-{ses}_task-aTask_run-{run}_eeg.vhdr",
                            "Brain Vision Data Exchange Header File\n",
                        ),
                        (
                            f"sub-{sub}_ses-{ses}_task-aTask_acq-{acq}_run-01_eeg.vhdr",
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

    # Create invalid files with different types of errors
    invalid_files = [
        # Session mismatch between path and filename
        (
            "sub-001/ses-01/eeg/sub-001_ses-02_task-rest_eeg.vhdr",
            "Brain Vision Data Exchange Header File Version 1.0\n",
        ),
        # Subject mismatch between path and filename
        (
            "sub-002/ses-01/eeg/sub-001_ses-01_task-rest_eeg.vhdr",
            "Brain Vision Data Exchange Header File Version 1.0\n",
        ),
        # Invalid session key (sus instead of ses)
        (
            "sub-003/ses-01/eeg/sub-003_sus-01_task-rest_eeg.vhdr",
            "Brain Vision Data Exchange Header File Version 1.0\n",
        ),
        # Invalid run value
        (
            "sub-004/ses-01/eeg/sub-004_ses-01_run-badrun_eeg.vhdr",
            "Brain Vision Data Exchange Header File Version 1.0\n",
        ),
        # Invalid task name with special characters
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
    assert arch.datatypes == ["eeg"]
    assert arch.tasks == ["aTask"]
    assert arch.runs == ["01", "02"]
    assert arch.acquisitions == ["anAcq", "anotherAcq"]
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

    assert not arch.database.empty
    result = arch.select(subject="001")
    assert result.subjects == ["001"]
    assert len(result) == 10
    assert all(result.database["subject"] == "001")

    result = arch.select(subject="001", task="aTask")
    assert result.subjects == ["001"]
    assert result.tasks == ["aTask"]
    assert len(result) == 10

    result = arch.select(subject="001", task="aTask", run="01", session="01")
    assert result.subjects == ["001"]
    assert result.tasks == ["aTask"]
    assert result.runs == ["01"]
    assert result.sessions == ["01"]
    assert len(result) == 3

    result = arch.select(subject=["001", "002"])
    assert result.subjects == ["001", "002"]
    assert len(result) == 20

    # Invalid key
    with pytest.raises(ValueError, match="Invalid selection keys"):
        arch.select(invalid_key="value")

    # Chained selection
    result = arch.select(subject="001").select(task="aTask").select(run="01")
    assert len(result) == 6
    assert result.subjects == ["001"]
    assert result.tasks == ["aTask"]
    assert result.runs == ["01"]


def test_architecture_set_operations(bids_dataset: Path) -> None:
    """Test set operations between BidsArchitecture instances."""
    # Initialize architectures and create their databases
    arch = BidsArchitecture(root=bids_dataset)
    arch.database
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
