"""Query functionality for BIDS paths."""

import os
import re  # Add this at the top of the file
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional


@dataclass
class BidsQuery:
    """Class for querying BIDS datasets using wildcards and patterns.

    Extends BidsPath to support flexible querying of BIDS datasets using
    wildcards and patterns. Handles conversion of query parameters to
    filesystem-compatible glob patterns.

    Attributes:
        All attributes support wildcards (*) for flexible matching
    """

    root: Optional[Path] = None
    subject: Optional[str] = None
    session: Optional[str] = None
    datatype: Optional[str] = None
    task: Optional[str] = None
    acquisition: Optional[str] = None
    run: Optional[str] = None
    recording: Optional[str] = None
    space: Optional[str] = None
    description: Optional[str] = None
    suffix: Optional[str] = None
    extension: Optional[str] = None

    def __post_init__(self) -> None:  # noqa: D105
        pass

    def _format_mandatory_attrs(self) -> str:
        str_attrs = [
            f"sub-{self.subject or '*'}",
            f"ses-{self.session or '*'}",
        ]

        return "_".join(str_attrs)

    def _all_optional_exist(self, optional_attrs: list[str]) -> bool:
        condition_regular_files = [
            getattr(self, attr) is not None
            for attr in optional_attrs
            if attr != "space"
        ]
        condition_on_electrode_file = self.space is not None
        return condition_on_electrode_file or all(condition_regular_files)

    def _format_optional_attrs(self, optional_attrs: list[str]) -> str | None:
        if self.space is not None:
            return f"space-{self.space}"

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
                if getattr(self, attr) is not None and attr != "space"
                else "*"
                for attr in optional_attrs
            ]
        )

        for i in range(2):
            str_attrs = re.sub(
                r"(\*+_)+|(_\*+)+|(\*+_\*+)+|(_\*+_)+|\*{2,}", "*", str_attrs
            )

        if not self._all_optional_exist(optional_attrs=optional_attrs):
            str_attrs = f"*{str_attrs}*"
            str_attrs = re.sub(
                r"(\*+_)+|(_\*+)+|(\*+_\*+)+|(_\*+_)+|\*{2,}", "*", str_attrs
            )

        if str_attrs == "*":
            return None
        else:
            return str_attrs

    def _format_suffix_extension(
        self, optional_attrs: list[str]
    ) -> str | None:
        if (
            self.suffix is None
            and self._all_optional_exist(optional_attrs)
            and self.extension is None
        ):
            return "*"

        elif self.suffix is not None and self.extension is None:
            return f"{self.suffix}.*"

        elif self.suffix is None and self.extension is not None:
            self.extension = self.extension.replace(".", "")
            return f"*.{self.extension}"

        elif self.suffix is not None and self.extension is not None:
            self.extension = self.extension.replace(".", "")
            return ".".join([self.suffix, self.extension])

        else:
            return None

    def _format_opt_suffix_extension(
        self,
        suffix_extension_str: str | None,
        formated_optional_str: str | None,
    ) -> str | None:
        if (
            suffix_extension_str is not None
            and formated_optional_str is not None
        ):
            return "_".join([formated_optional_str, suffix_extension_str])
        elif (
            suffix_extension_str is not None and formated_optional_str is None
        ):
            return suffix_extension_str

        elif (
            formated_optional_str is not None and suffix_extension_str is None
        ):
            return formated_optional_str
        else:
            return None

    def _build_query_filename(self) -> Path:
        """Build the query."""
        if self.space is not None:
            optional_attrs = ["space"]
        else:
            optional_attrs = [
                "task",
                "acquisition",
                "run",
                "recording",
                "description",
            ]

        formated_mandatory_str = self._format_mandatory_attrs()
        formated_optional_str = self._format_optional_attrs(optional_attrs)
        suffix_extension_str = self._format_suffix_extension(optional_attrs)
        opt_suff_ext_str = self._format_opt_suffix_extension(
            suffix_extension_str, formated_optional_str
        )

        if opt_suff_ext_str is None:
            formated_mandatory_str += "*"
            full_formated_str = formated_mandatory_str
        elif (
            formated_optional_str is None and suffix_extension_str is not None
        ):
            formated_mandatory_str += "*"
            full_formated_str = "_".join(
                [formated_mandatory_str, suffix_extension_str]
            )
        else:
            full_formated_str = "_".join(
                [formated_mandatory_str, opt_suff_ext_str]
            )

        full_formated_str = re.sub(
            r"(\*+_\*+)+|(_\*+_)+|\*{2,}", "*", full_formated_str
        )

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
