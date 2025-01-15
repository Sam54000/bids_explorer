"""Utility functions for parsing BIDS entities."""
from pathlib import Path
from typing import Dict, List, Optional


def parse_bids_filename(file: Path) -> Dict[str, Optional[str]]:
    """Parse BIDS entities from a filename.

    Args:
        file: Path object representing the BIDS file

    Returns:
        Dictionary containing parsed BIDS entities
    """
    entities: Dict[str, Optional[str]] = {
        "subject": None,
        "session": None,
        "datatype": None,
        "task": None,
        "run": None,
        "acquisition": None,
        "description": None,
        "suffix": None,
        "extension": None,
    }

    # Get datatype from parent directory
    parts: List[str] = list(file.parts)
    if len(parts) >= 2:
        entities["datatype"] = str(parts[-2])

    # Parse filename
    name: str = str(file.stem)
    extension: str = str(file.suffix)
    entities["extension"] = extension

    # Split into components
    parts_list: List[str] = name.split("_")

    # Parse each entity
    if parts_list:  # Check if parts_list is not empty
        # Process all parts except the last one
        for part in parts_list[:-1]:
            if "-" not in part:
                continue
            try:
                key, value = part.split("-", 1)
                if key == "sub":
                    entities["subject"] = str(value)
                elif key == "ses":
                    entities["session"] = str(value)
                elif key == "task":
                    entities["task"] = str(value)
                elif key == "run":
                    entities["run"] = str(value)
                elif key == "acq":
                    entities["acquisition"] = str(value)
                elif key == "desc":
                    entities["description"] = str(value)
            except ValueError:
                continue  # Skip malformed entities

        # Get suffix (last part)
        if parts_list:  # Check again in case list was modified
            entities["suffix"] = str(parts_list[-1])

    return entities
