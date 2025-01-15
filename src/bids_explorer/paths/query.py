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
    space: Optional[str] = None
    task: Optional[str] = None
    acquisition: Optional[str] = None
    run: Optional[str] = None
    recording: Optional[str] = None
    description: Optional[str] = None
    suffix: Optional[str] = None
    extension: Optional[str] = None

    def __post_init__(self) -> None:  # noqa: D105
        super().__post_init__()

    def _format_mandatory_attrs(self, mandatory_attrs: list[str]) -> str:
        str_attrs = [
            f"sub-{self.subject or '*'}",
            f"ses-{self.session or '*'}",
        ]

        print(f"str_mandatory: {'_'.join(str_attrs)}")
        return "_".join(str_attrs)

    def _all_optional_exist(self, optional_attrs: list[str]) -> bool:
        condition_regular_files = [
            getattr(self, attr) is not None
            for attr in optional_attrs
            if attr != "space"
        ]
        condition_on_electrode_file = self.space is not None
        return condition_on_electrode_file or all(condition_regular_files)

    def _format_optional_attrs(self, optional_attrs: list[str]) -> str:
        string_key_reference = {
            "task": "task-",
            "acquisition": "acq-",
            "run": "run-",
            "recording": "recording-",
            "description": "desc-",
        }
        str_attrs = "_".join(
            [
                f"{string_key_reference.get(attr)}{getattr(self,attr)}"
                if attr is not None and attr != "space"
                else "*"
                for attr in optional_attrs
            ]
        )

        str_attrs = str_attrs.replace("_*_", "*")

        if not self._all_optional_exist(optional_attrs=optional_attrs):
            str_attrs += "*"

        str_attrs = str_attrs.replace("**", "*")
        print(f"str_optional: {str_attrs}")

        return str_attrs

    def _build_query_filename(self) -> Path:
        """Build the query."""
        mandatory_attrs = ["subject", "session", "datatype"]
        optional_attrs = [
            "space",
            "task",
            "acquisition",
            "run",
            "recording",
            "description",
        ]

        formated_mandatory_str = self._format_mandatory_attrs(mandatory_attrs)
        formated_optional_str = self._format_optional_attrs(optional_attrs)
        if not self._all_optional_exist(optional_attrs):
            formated_mandatory_str += "*"

        if self.suffix is None and self._all_optional_exist(optional_attrs):
            suffix_str: str | None = "*"
        else:
            suffix_str = self.suffix

        if suffix_str is not None:
            extension_str: str | None = "*"
        else:
            extension_str = self.extension

        if suffix_str is not None and extension_str is not None:
            suffix_extension_str = ".".join([suffix_str, extension_str])

        suffix_extension_str = suffix_extension_str.replace("*.*", "*")
        opt_suff_ext_str = "_".join(
            [formated_optional_str, suffix_extension_str]
        )
        opt_suff_ext_str = opt_suff_ext_str.replace("*_*", "*")

        full_formated_str = "_".join(
            [formated_mandatory_str, opt_suff_ext_str]
        )
        full_formated_str = full_formated_str.replace("*_*", "*")

        return Path(full_formated_str)

    def _build_query_pathname(self) -> Path:
        path = (
            f"sub-{self.subject or '*'}/"
            f"ses-{self.session or '*'}/{self.datatype or '*'}"
        )
        return Path(path)

    @property
    def filename(self) -> Path:
        """Get filename pattern for querying."""

        return self._build_query_filename()

    @property
    def relative_path(self) -> Path:
        """Get relative path for querying."""

        return self._build_query_pathname()

    @property
    def fullpath(self) -> Path:
        """Get full path for querying."""
        return self.relative_path / self.filename

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
