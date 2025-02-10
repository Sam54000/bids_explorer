"""Tests for BIDS path handling functionality."""
from pathlib import Path

import pytest

from bids_explorer.paths.bids import BidsPath


def test_bids_path_initialization() -> None:
    """Test BidsPath initialization with various parameters."""
    path = BidsPath(
        subject="001",
        session="01",
        task="rest",
        datatype="eeg",
        suffix="eeg",
        extension=".vhdr",
    )
    assert path.subject == "001"
    assert path.session == "01"
    assert path.task == "rest"
    assert path.suffix == "eeg"
    assert path.extension == ".vhdr"

    path = BidsPath(
        subject="sub-002",
        session="ses-02",
        task="task-test",
    )
    assert path.subject == "002"
    assert path.session == "02"
    assert path.task == "test"


def test_bids_path_normalization() -> None:
    """Test normalization of BIDS entities."""
    path = BidsPath(
        subject="sub-001",
        session="01",
        task="task-rest",
        run="run-01",
        acquisition="acq-full",
    )
    assert path.subject == "001"
    assert path.session == "01"
    assert path.task == "rest"
    assert path.run == "01"
    assert path.acquisition == "full"


def test_bids_path_basename() -> None:
    """Test BIDS-compliant basename generation."""
    path = BidsPath(
        subject="001",
        session="01",
        task="rest",
        run="01",
        suffix="eeg",
    )
    expected = Path("sub-001_ses-01_task-rest_run-01_eeg")
    assert path.basename == expected


def test_bids_path_filename() -> None:
    """Test complete filename generation."""
    path = BidsPath(
        subject="001",
        session="01",
        task="rest",
        suffix="eeg",
        extension=".vhdr",
    )
    expected = Path("sub-001_ses-01_task-rest_eeg.vhdr")
    assert path.filename == expected


def test_bids_path_from_filename() -> None:
    """Test BidsPath creation from existing filename."""
    filename = "sub-001_ses-01_task-rest_run-01_eeg.vhdr"
    path = Path("sub-001/ses-01/eeg") / filename
    bids_path = BidsPath.from_filename(path)

    assert bids_path.subject == "001"
    assert bids_path.session == "01"
    assert bids_path.task == "rest"
    assert bids_path.run == "01"
    assert bids_path.suffix == "eeg"
    assert bids_path.extension == ".vhdr"
    assert bids_path.datatype == "eeg"


def test_bids_path_invalid_prefix() -> None:
    """Test handling of invalid entity prefixes."""
    with pytest.raises(ValueError):
        BidsPath(subject="subject-001")

    with pytest.raises(ValueError):
        BidsPath(task="mytask-rest")


def test_bids_path_space_handling() -> None:
    """Test handling of space attribute in BidsPath."""
    path = BidsPath(
        subject="001",
        session="01",
        task="rest",
        space="MNI152NLin2009cAsym",
        suffix="bold",
    )
    assert path.space == "MNI152NLin2009cAsym"
    expected = Path("sub-001_ses-01_task-rest_space-MNI152NLin2009cAsym_bold")
    assert path.basename == expected

    path = BidsPath(
        subject="001",
        session="01",
        space="space-MNI152NLin2009cAsym",
    )
    assert path.space == "MNI152NLin2009cAsym"

    filename = "sub-001_ses-01_task-rest_space-MNI152NLin2009cAsym_bold.nii.gz"
    path_path = Path("sub-001/ses-01/func") / filename
    bids_path = BidsPath.from_filename(path_path)
    assert bids_path.space == "MNI152NLin2009cAsym"

    with pytest.raises(ValueError):
        BidsPath(space="wrongprefix-MNI152NLin2009cAsym")
