"""Database handling utilities."""
import pandas as pd

from bids_explorer.architecture.mixins import BidsArchitectureMixin


def set_database(object: BidsArchitectureMixin, value: pd.DataFrame) -> None:
    """Set the database DataFrame for an object.

    Args:
        object: The object to set database on.
        value: DataFrame containing database information to be set.
    """
    if hasattr(object, "database"):
        delattr(object, "database")
    if hasattr(object, "_database"):
        delattr(object, "_database")

    setattr(object, "_database", value)


def get_database_property(database: pd.DataFrame, column: str) -> tuple:
    """Get unique sorted values from a database column.

    Args:
        database: DataFrame to get values from.
        column: Column name to get unique values from.

    Returns:
        tuple: Sorted unique values from the column.
    """
    return tuple(sorted(database[column].unique()))
