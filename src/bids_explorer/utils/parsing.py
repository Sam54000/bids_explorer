"""Utility functions for parsing BIDS entities."""
import re
from pathlib import Path
from typing import Dict, List, Optional


def parse_bids_filename(
    file: Path, patterns: Optional[Dict[str, str]] = None
) -> Dict[str, Optional[str]]:
    """Parse BIDS entities from a filename.

    This function uses regular expression pattern matching for BIDS entities.
    Each pattern should contain exactly one capturing group that will be used
    as the entity value.

    Args:
        file: Path object representing the BIDS file
        patterns: Optional dictionary of custom regex patterns for each entity.
                 Keys should be entity names (e.g., "subject", "session") and
                 values should be valid regex patterns. Each pattern should
                 contain exactly one capturing group.

    Returns:
        Dictionary containing parsed BIDS entities

    Raises:
        re.error: If a regex pattern compilation fails
    """
    entities: Dict[str, Optional[str]] = {
        "subject": None,
        "session": None,
        "datatype": None,
        "task": None,
        "run": None,
        "recording": None,
        "acquisition": None,
        "space": None,
        "description": None,
        "suffix": None,
        "extension": None,
    }

    default_patterns: Dict[str, str] = {
        "subject": r"sub-([^_]+)",
        "session": r"ses-([^_]+)",
        "task": r"task-([^_]+)",
        "run": r"run-([^_]+)",
        "recording": r"recording-([^_]+)",
        "acquisition": r"acq-([^_]+)",
        "description": r"desc-([^_]+)",
        "space": r"space-([^_]+)",
        "suffix": r"[^_]+_([^_.]+)(?:\.|$)",
    }

    parts: List[str] = list(file.parts)
    if len(parts) >= 2:
        entities["datatype"] = str(parts[-2])

    name: str = str(file.stem)
    extension: str = str(file.suffix)
    entities["extension"] = extension
    active_patterns = patterns if patterns is not None else default_patterns
    components = name.split("_")

    for component in components:
        for entity, pattern in active_patterns.items():
            if entity == "suffix":
                continue
            try:
                if not pattern.endswith(
                    r"(?:[^0-9]|$)"
                ) and not pattern.endswith(r"(?:_|$)"):
                    pattern = pattern + r"(?:_|$)"
                match = re.match(pattern, component)
                if match and match.groups():
                    entities[entity] = str(match.group(1))
            except re.error as e:
                raise re.error(f"Invalid regex pattern for {entity}: {str(e)}")

    if patterns is None or "suffix" in patterns:
        suffix_pattern = (
            patterns["suffix"]
            if patterns and "suffix" in patterns
            else default_patterns["suffix"]
        )
        try:
            match = re.search(suffix_pattern, name)
            if match and match.groups():
                entities["suffix"] = str(match.group(1))
        except re.error as e:
            raise re.error(f"Invalid regex pattern for suffix: {str(e)}")

    return entities
