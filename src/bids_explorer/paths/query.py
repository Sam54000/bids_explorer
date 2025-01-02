"""Query functionality for BIDS paths."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from bids_explorer.paths.bids import BidsPath


@dataclass
class BidsQuery(BidsPath):
    """Class for querying BIDS datasets using wildcards and patterns.

    Extends BidsPath to support flexible querying of BIDS datasets using
    wildcards and patterns. Handles conversion of query parameters to
    filesystem-compatible glob patterns.

    Attributes:
        Inherits all attributes from BidsPath
        All attributes support wildcards (*) for flexible matching
    """

    root: Optional[Path] = None
    subject: Optional[str] = None
    session: Optional[str] = None
    datatype: Optional[str] = None
    task: Optional[str] = None
    acquisition: Optional[str] = None
    run: Optional[str] = None
    description: Optional[str] = None
    suffix: Optional[str] = None
    extension: Optional[str] = None

    def __post_init__(self) -> None:  # noqa: D105
        super().__post_init__()
        self._add_wildcard_to_attributes()

    def _add_wildcard_to_attributes(self) -> "BidsQuery":
        """Add wildcard to attributes."""
        required_attrs = [
            "subject",
            "session",
            "datatype",
            "suffix",
            "extension",
        ]

        for attr in required_attrs:
            if getattr(self, attr) is None:
                if attr == "extension":
                    setattr(self, attr, ".*")
                else:
                    setattr(self, attr, "*")

        for attr in ["task", "run", "acquisition", "description"]:
            if getattr(self, attr) is not None:
                setattr(self, attr, getattr(self, attr) + "*")

        return self

    def _cleanup_pattern(self, pattern: Path) -> Path:
        """Cleanup a pattern by replacing redundant wildcards."""
        pattern_str = os.fspath(pattern)
        potential_cases = ["*_*", "**", "*.*"]
        for case in potential_cases:
            pattern_str = pattern_str.replace(case, "*")
        return Path(pattern_str)  # Convert back to Path at the end

    @property
    def filename(self) -> Path:
        """Get filename pattern for querying."""
        return self._cleanup_pattern(super().filename)

    @property
    def relative_path(self) -> Path:
        """Get relative path for querying."""
        return self._cleanup_pattern(super().relative_path)

    @property
    def fullpath(self) -> Path:
        """Get full path for querying."""
        return self.relative_path / self.filename

    @property
    def user_input(self) -> dict[str, str | list[str]]:
        """Get user input for querying."""
        return {
            args: val.replace("*", "")
            for args, val in self.__dict__.items()
            if val != "*" and val is not None
        }

    def generate(self) -> Iterator[Path]:
        """Generate iterator of matching files.

        Returns:
            Iterator yielding paths matching query pattern

        Raises:
            Exception: If root path is not defined
        """
        if not self.root:
            raise Exception(
                "Root was not defined. Please instantiate the object"
                " by setting root to a desired path"
            )
        return self.root.rglob(os.fspath(self.relative_path / self.filename))
