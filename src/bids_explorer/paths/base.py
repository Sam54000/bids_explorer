"""Base path handling for BIDS-like structures."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class BasePath:
    """Base class for handling file paths.

    This class provides core functionality for working with paths, including
    path construction and attribute management.

    Attributes:
        root: Root directory path
        subject: Subject identifier
        session: Session identifier
        datatype: Type of data
        suffix: File suffix/type identifier
        extension: File extension
    """

    root: Optional[Path] = None
    subject: Optional[str] = None
    session: Optional[str] = None
    datatype: Optional[str] = None
    suffix: Optional[str] = None
    extension: Optional[str] = None

    def __post_init__(self) -> None:
        """Ensure extension starts with a period if provided."""
        if self.extension and not self.extension.startswith("."):
            self.extension = f".{self.extension}"

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
        """Create filename without extension.

        Returns:
            Base filename constructed from available attributes
        """
        components = []
        if self.subject:
            components.append(f"sub-{self.subject}")
        if self.session:
            components.append(f"ses-{self.session}")
        if self.suffix:
            components.append(self.suffix)
        return Path("_".join(components))
