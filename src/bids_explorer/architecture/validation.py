"""Validation utilities for BIDS architecture."""

import os
import re
from pathlib import Path
from typing import Optional, Set

import pandas as pd

VALID_COLUMNS = {
    "root",
    "subject",
    "session",
    "datatype",
    "task",
    "run",
    "acquisition",
    "recording",
    "description",
    "suffix",
    "extension",
    "atime",
    "mtime",
    "ctime",
    "filename",
}


class BidsValidationError(Exception):
    """Exception raised for BIDS validation errors."""


def all_columns_valid(database: pd.DataFrame, strict: bool = True) -> bool:
    """Check if a DataFrame contains all required BIDS columns.

    Args:
        database: DataFrame to validate columns for.
        strict: If True, requires exact column match. If False, allow
                additional columns.

    Returns:
        bool: True if all required columns are present, False otherwise.
    """
    if strict:
        return set(database.columns) == VALID_COLUMNS
    else:
        database_columns = set(database.columns)
        return VALID_COLUMNS.issubset(database_columns)


def get_invalid_columns(database: pd.DataFrame) -> Set[str]:
    """Get set of invalid columns in database.

    Args:
        database: DataFrame to check columns for.

    Returns:
        Set[str]: Set of column names that are not valid BIDS columns.
    """
    return set(database.columns) - VALID_COLUMNS


def validate_bids_file(file: Path) -> bool:
    """Validate the BIDS filename and pathname.

    Args:
        file: Path to validate

    Returns:
        bool: True if validation passes

    Raises:
        BidsValidationError: If validation fails
    """
    valid_keys = {
        "sub",
        "ses",
        "task",
        "run",
        "acq",
        "recording",
        "desc",
        "space",
    }

    valid_datatype_pattern = re.compile(r"^[a-z0-9]+$")
    key_value_pattern = re.compile(
        r"(?P<key>[a-zA-Z0-9]+)-(?P<value>[a-zA-Z0-9]+)"
    )
    path_pattern = re.compile(r"(sub|ses)-[\w\d]+")

    errors = []

    filename = os.fspath(file.name) if file.suffix else None
    if filename:
        bids_path_parts = file.parent.parts[-3:]

        conditions = (
            bids_path_parts[0].startswith("sub"),
            bids_path_parts[2].startswith("ses"),
            "-" in bids_path_parts[0],
            "-" in bids_path_parts[2],
        )
        if not any(conditions):
            raise BidsValidationError(
                "Path does not contain valid BIDS elements (e.g., 'sub-*')."
                "Should be in the form of"
                "'root/sub-<label>/ses-<label>/<datatype>'"
            )
        datatype = file.parent.parts[-1]
    else:
        bids_path_parts = file.parent.parts[-2:]
        datatype = file.parts[-1]

    if datatype and not valid_datatype_pattern.match(datatype):
        errors.append(
            f"Invalid datatype: '{datatype}' should be a lowercase "
            "alphanumeric string."
        )

    for part in [bids_path_parts[0], bids_path_parts[1]]:
        if not path_pattern.match(part):
            errors.append(
                f"Invalid path component: '{part}' should match the pattern "
                "'<key>-<value>' with key being 'sub' or 'ses'."
            )

    if filename:
        name_parts = file.stem.split("_")

        for i, part in enumerate(name_parts):
            if i == len(name_parts) - 1:
                continue

            match = key_value_pattern.match(part)
            if not match:
                errors.append(
                    f"Invalid format in '{part}': should be '<key>-<value>'"
                )
            else:
                key = match.group("key")
                if key not in valid_keys:
                    errors.append(
                        f"Invalid key '{key}': must be one of"
                        f"{sorted(valid_keys)}"
                    )

    path_subject = (
        bids_path_parts[0].split("-")[1] if "-" in bids_path_parts[0] else None
    )
    path_session = (
        bids_path_parts[1].split("-")[1] if "-" in bids_path_parts[1] else None
    )

    filename_entities = {}
    name_parts = file.stem.split("_")
    for part in name_parts:
        if "-" in part:
            key, value = part.split("-", 1)
            filename_entities[key] = value

    if path_subject and "sub" in filename_entities:
        if path_subject != filename_entities["sub"]:
            errors.append(
                f"Subject mismatch: path has 'sub-{path_subject}' but "
                f"filename has 'sub-{filename_entities['sub']}'"
            )

    if path_session and "ses" in filename_entities:
        if path_session != filename_entities["ses"]:
            errors.append(
                f"Session mismatch: path has 'ses-{path_session}' but "
                f"filename has 'ses-{filename_entities['ses']}'"
            )

    if errors:
        message = f"Non-standardized BIDS name\n" f"{file}\n\n" + "\n".join(
            f"{i + 1}. {error}" for i, error in enumerate(errors)
        )
        raise BidsValidationError(message)

    return True


def normalize_entity(
    prefix: str,
    value: Optional[str],
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


def validate_and_normalize_entities(
    subject: Optional[str],
    session: Optional[str],
    task: Optional[str],
    acquisition: Optional[str],
    run: Optional[str],
    recording: Optional[str],
    space: Optional[str],
    description: Optional[str],
) -> dict[str, str | None]:
    """Validate and normalize all BIDS entities."""
    prefix_mapping = {
        "subject": "sub",
        "session": "ses",
        "task": "task",
        "acquisition": "acq",
        "run": "run",
        "recording": "recording",
        "space": "space",
        "description": "desc",
    }

    special_char_pattern = re.compile(r"[^a-zA-Z0-9-]")

    entities = {}
    for attr, prefix in prefix_mapping.items():
        value = locals()[attr]
        if value is not None and isinstance(value, str):
            if special_char_pattern.search(value):
                raise ValueError(
                    f"Invalid character in {attr}='{value}'. "
                    "Only alphanumeric characters and '-' are allowed."
                )

            if "-" in value:
                given_prefix = value.split("-")[0]
                if given_prefix != prefix:
                    raise ValueError(
                        f"Invalid prefix in {attr}='{value}'. "
                        f"Expected '{prefix}-' prefix if any, got "
                        f"'{given_prefix}-'"
                    )

            entities[attr] = normalize_entity(prefix, value)

    return entities
