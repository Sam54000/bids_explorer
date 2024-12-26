"""Error handling utilities."""

import pandas as pd

from bids_explorer.core.mixins import BidsArchitectureMixin


def set_errors(object: BidsArchitectureMixin, value: pd.DataFrame) -> None:
    """Set the error DataFrame for an object.

    Args:
        object: The object to set errors on.
        value: DataFrame containing error information to be set.
    """
    if hasattr(object, "errors"):
        delattr(object, "errors")
    if hasattr(object, "_errors"):
        delattr(object, "_errors")

    setattr(object, "_errors", value)


def merge_error_logs(
    self: BidsArchitectureMixin, other: BidsArchitectureMixin
) -> pd.DataFrame:
    """Merge error logs from two objects efficiently.

    Args:
        self: Base object containing error logs to merge from.
        other: Another object containing error logs to merge with this one.

    Returns:
        pd.DataFrame: A merged DataFrame containing combined error logs.

    Raises:
        AttributeError: If either object is missing error logs.
    """
    if not hasattr(self, "_errors") or not hasattr(other, "_errors"):
        raise AttributeError("One or both objects missing error logs")

    if self._errors.empty and other._errors.empty:
        return self._errors

    return pd.concat(
        [
            self._errors,
            other._errors.loc[~other._errors.index.isin(self._errors.index)],
        ],
        copy=False,
    )
