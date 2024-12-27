"""BIDS-compliant path handling."""
import re
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from bids_explorer.core.validation import validate_bids_file, validate_entities
from bids_explorer.paths.base import BasePath


@dataclass
class BidsPath(BasePath):
    """BIDS-compliant path handler with query capabilities.

    Extends BasePath with BIDS-specific functionality and query features.
    Handles path construction, validation, and pattern matching for BIDS
    datasets.

    Attributes:
        task: Task identifier
        run: Run number
        acquisition: Acquisition identifier
        description: Description identifier
    """

    task: Optional[str] = None
    run: Optional[str] = None
    acquisition: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self) -> None:
        """Initialize and normalize BIDS entities."""
        validate_entities(
            self.subject,
            self.session,
            self.task,
            self.run,
            self.acquisition,
            self.description,
        )
        super().__post_init__()

    def _normalize_entity(
        self, prefix: str, value: Optional[str]
    ) -> Optional[str]:
        """Normalize BIDS entity value by removing prefix if present.

        Args:
            prefix: Expected prefix for the entity
            value: Value to normalize

        Returns:
            Normalized value with prefix removed if present
        """
        if value is None:
            return None

        value = value.strip()
        prefix_pattern = f"^{prefix}-"
        if re.match(prefix_pattern, value):
            return value[len(prefix) + 1 :]

        return value

    def _make_basename(self) -> str:
        """Create BIDS-compliant filename without extension.

        Returns:
            str: BIDS-compliant filename
        """
        components = [f"sub-{self.subject}", f"ses-{self.session}"]

        if self.task:
            components.append(f"task-{self.task}")
        if self.acquisition:
            components.append(f"acq-{self.acquisition}")
        if self.run:
            components.append(f"run-{self.run}")
        if self.description:
            components.append(f"desc-{self.description}")
        if self.suffix:
            components.append(self.suffix)

        return "_".join(filter(None, components))

    @property
    def basename(self) -> str:
        """Get BIDS-compliant filename without extension."""
        return self._make_basename()

    @property
    def filename(self) -> str:
        """Get complete filename with extension."""
        return f"{self.basename}{self.extension or ''}"

    @property
    def relative_path(self) -> Path:
        """Get relative path."""
        return self._make_path(absolute=False)

    @property
    def fullpath(self) -> Path:
        """Get complete path including filename."""
        path = self._make_path(absolute=bool(self.root))
        return path / self.filename

    def match_pattern(self, pattern: str = "*") -> bool:
        """Check if path matches given pattern.

        Args:
            pattern: Glob pattern to match against

        Returns:
            True if path matches pattern, False otherwise
        """
        return Path(self.filename).match(pattern)

    @classmethod
    def from_filename(cls, file: Union[str, Path]) -> "BidsPath":
        """Create BidsPath instance from existing filename.

        Args:
            file: BIDS-compliant filename or path

        Returns:
            New BidsPath instance with normalized entities
        """
        if isinstance(file, str):
            file = Path(file)

        validate_bids_file(file)
        entities = {}

        if file.suffix:
            path = file.parent
        else:
            path = copy(file)

        entities["datatype"] = path.parts[-1]
        entities["session"] = path.parts[-2].split("-")[1]
        entities["subject"] = path.parts[-3].split("-")[1]

        name_parts = file.stem.split("_")
        for part in name_parts:
            if "-" in part:
                key, value = part.split("-", 1)
                if key == "sub":
                    entities["subject"] = value
                elif key == "ses":
                    entities["session"] = value
                elif key == "task":
                    entities["task"] = value
                elif key == "acq":
                    entities["acquisition"] = value
                elif key == "run":
                    entities["run"] = value
                elif key == "desc":
                    entities["description"] = value

        entities["suffix"] = name_parts[-1]
        entities["extension"] = file.suffix

        return cls(**entities)
