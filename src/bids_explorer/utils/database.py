"""Database handling utilities."""
import pandas as pd


def get_database_property(database: pd.DataFrame, column: str) -> tuple:
    """Get unique sorted values from a database column.

    Args:
        database: DataFrame to get values from.
        column: Column name to get unique values from.

    Returns:
        tuple: Sorted unique values from the column.
    """
    return tuple(sorted(database[column].unique()))
