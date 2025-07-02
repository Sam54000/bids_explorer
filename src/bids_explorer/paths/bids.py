"""BIDS-compliant path handling."""

import os
import re
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from bids_explorer.architecture.validation import (
    validate_and_normalize_entities,
    validate_bids_file,
)


class BidsPath:
    """BIDS-compliant path handler with query capabilities.

    Extends BasePath with BIDS-specific functionality and query features.
    Handles path construction, validation, and pattern matching for BIDS
    datasets.

    Attributes:
        task: Task identifier
        run: Run number
        acquisition: Acquisition identifier
        description: Description identifier
        space: Space identifier
    """

    entity_keys = {
        "subject": "sub-",
        "session": "ses-",
        "task": "task-",
        "acquisition": "acq-",
        "run": "run-",
        "recording": "recording-",
        "space": "space-",
        "description": "desc-",
    }

    def __init__(
        self,
        root: Optional[Path] = None,
        subject: Optional[str] = None,
        session: Optional[str] = None,
        datatype: Optional[str] = None,
        task: Optional[str] = None,
        acquisition: Optional[str] = None,
        run: Optional[str] = None,
        recording: Optional[str] = None,
        space: Optional[str] = None,
        description: Optional[str] = None,
        suffix: Optional[str] = None,
        extension: Optional[str] = None,
    ) -> None:
        self.root = root
        self.subject = subject
        self.session = session
        self.datatype = datatype
        self.task = task
        self.acquisition = acquisition
        self.run = run
        self.recording = recording
        self.space = space
        self.description = description
        self.suffix = suffix
        self.extension = extension

    def _make_path(self, absolute: bool = True) -> Path:
        """Construct directory path.

        Args:
            absolute: If True and root is set, returns absolute path.
                     If False, returns relative path.

        Returns:
            Path object representing the constructed path
        """
        components = []
        if self.subject:
            components.append(f"sub-{self.subject}")
        if self.session:
            components.append(f"ses-{self.session}")
        if self.datatype:
            components.append(self.datatype)

        relative_path = Path(*components)
        if absolute and self.root:
            return self.root / relative_path
        return relative_path

    def _make_basename(self) -> Path:
        """Create BIDS-compliant filename without extension.

        Returns:
            str: BIDS-compliant filename
        """
        components = []

        for entity, key in self.entity_keys.items():
            if getattr(self, entity):
                components.append(key + getattr(self, entity))

        if self.suffix:
            components.append(self.suffix)

        return Path("_".join(filter(None, components)))

    @property
    def basename(self) -> Path:
        """Get BIDS-compliant filename without extension."""
        return self._make_basename()

    @property
    def filename(self) -> Path:
        """Get complete filename with extension."""
        return Path(f"{self.basename}{self.extension or ''}")

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

        for entity, key in cls.entity_keys.items():
            match = re.match(
                rf"{key}([A-Za-z0-9]+)", string=os.fspath(os.fspath(file))
            )

            if match:
                entities[entity] = match.group().split("-")[1]

        entities["suffix"] = file.stem.split("_")[-1]
        entities["extension"] = file.suffix

        # Get the root path (everything before subject directory)
        root = Path(*path.parts[:-3]) if len(path.parts) > 3 else None

        # Create instance with root path and entities
        return cls(root=root, **entities)
