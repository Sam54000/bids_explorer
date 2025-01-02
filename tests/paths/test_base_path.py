"""Tests for base path functionality."""
from pathlib import Path

from bids_explorer.paths.base import BasePath


def test_base_path_initialization() -> None:
    """Test BasePath initialization with various parameters."""
    path = BasePath(
        root=Path("/data"),
        subject="001",
        session="01",
        datatype="eeg",
        suffix="eeg",
        extension="vhdr",
    )

    assert path.root == Path("/data")
    assert path.subject == "001"
    assert path.session == "01"
    assert path.datatype == "eeg"
    assert path.suffix == "eeg"
    assert path.extension == ".vhdr"


def test_base_path_extension_normalization() -> None:
    """Test extension normalization in BasePath."""
    path1 = BasePath(extension=".vhdr")
    assert path1.extension == ".vhdr"

    path2 = BasePath(extension="vhdr")
    assert path2.extension == ".vhdr"

    path3 = BasePath(extension=None)
    assert path3.extension is None


def test_base_path_make_path() -> None:
    """Test path construction with BasePath."""
    path = BasePath(
        root=Path("/data"),
        subject="001",
        session="01",
        datatype="eeg",
    )
    expected = Path("/data/sub-001/ses-01/eeg")
    assert path._make_path(absolute=True) == expected

    expected_relative = Path("sub-001/ses-01/eeg")
    assert path._make_path(absolute=False) == expected_relative

    path_no_root = BasePath(
        subject="001",
        session="01",
        datatype="eeg",
    )
    assert path_no_root._make_path(absolute=True) == Path("sub-001/ses-01/eeg")


def test_base_path_optional_components() -> None:
    """Test path construction with optional components."""
    path1 = BasePath(
        root=Path("/data"),
        subject="001",
        datatype="eeg",
    )
    assert path1._make_path() == Path("/data/sub-001/eeg")

    path2 = BasePath(
        root=Path("/data"),
        subject="001",
        session="01",
    )
    assert path2._make_path() == Path("/data/sub-001/ses-01")

    path3 = BasePath(
        root=Path("/data"),
        subject="001",
    )
    assert path3._make_path() == Path("/data/sub-001")
