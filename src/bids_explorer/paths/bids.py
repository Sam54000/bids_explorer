"""BIDS-compliant path handling."""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

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
        self._validate_and_normalize_entities()
        super().__post_init__()

    def _validate_and_normalize_entities(self) -> None:
        """Validate and normalize all BIDS entities."""
        prefix_mapping = {
            "subject": "sub",
            "session": "ses",
            "task": "task",
            "run": "run",
            "acquisition": "acq",
            "description": "desc",
        }

        for attr, prefix in prefix_mapping.items():
            value = getattr(self, attr)
            if value is not None and isinstance(value, str):
                if "-" in value:
                    given_prefix = value.split("-")[0]
                    if given_prefix != prefix:
                        raise ValueError(
                            f"Invalid prefix in {attr}='{value}'. "
                            f"Expected '{prefix}-' prefix if any, got "
                            f"'{given_prefix}-'"
                        )
                setattr(self, attr, self._normalize_entity(prefix, value))

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

        cls._check_filename(cls, file)
        entities = {}

        if len(file.parts) > 2:
            entities["datatype"] = file.parts[-2]
            entities["subject"] = file.parts[-3].split("-")[1]
            if len(file.parts) > 3:
                entities["session"] = file.parts[-4].split("-")[1]

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
