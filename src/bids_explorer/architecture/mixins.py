"""Mixin classes and utilities for BIDS architecture."""
from typing import Union

import pandas as pd

from bids_explorer.architecture.validation import all_columns_valid


def prepare_for_operations(
    object1: Union["BidsArchitectureMixin", pd.DataFrame, set],
    object2: Union["BidsArchitectureMixin", pd.DataFrame, set],
) -> pd.Index:
    """Prepare objects for set operations.

    Args:
        object1: First object to prepare for set operations.
        object2: Second object to prepare for set operations.

    Returns:
        pd.Index: Index suitable for set operations.

    Raises:
        ValueError: If objects are of incompatible types or invalid.
    """
    conditions_on_object1 = (
        isinstance(object1, BidsArchitectureMixin),
        isinstance(object1, pd.DataFrame),
        isinstance(object1, set),
    )
    conditions_on_object2 = (
        isinstance(object2, BidsArchitectureMixin),
        isinstance(object2, pd.DataFrame),
        isinstance(object2, set),
    )
    if not (any(conditions_on_object1) and any(conditions_on_object2)):
        raise TypeError(
            f"Cannot perform operations between types "
            f"{object1.__class__.__name__} "
            f"and {object2.__class__.__name__}. Expected BidsArchitecture, "
            "DataFrame, or set."
        )

    if isinstance(object2, pd.DataFrame):
        return object2.index
    elif isinstance(object2, BidsArchitectureMixin):
        if not all_columns_valid(object2._database):
            raise ValueError(
                f"{object2.__class__.__name__} has invalid columns"
            )
        return object2._database.index
    return object2


class BidsArchitectureMixin:
    """Mixin class for BidsArchitecture operations."""

    _database: pd.DataFrame
