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

    def _remove_wildcard_from_attributes(self) -> "BidsQuery":
        """Remove the wildcard from attributes."""
        required_attrs = [
            "subject",
            "session",
            "datatype",
            "suffix",
            "extension",
            "task",
            "run",
            "acquisition",
            "description",
        ]

        for attr in required_attrs:
            if getattr(self, attr) is not None and "*" in getattr(self, attr):
                setattr(self, attr, getattr(self, attr).replace("*", ""))
            if getattr(self, attr) == "*" or getattr(self, attr) == ".*":
                setattr(self, attr, None)

        return self

    @property
    def filename(self) -> str:
        """Get filename pattern for querying."""
        potential_cases = ["*_*", "**", "*.*"]
        self._add_wildcard_to_attributes()
        filename = super().filename
        self._remove_wildcard_from_attributes()
        for case in potential_cases:
            filename = filename.replace(case, "*")
        return filename

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
