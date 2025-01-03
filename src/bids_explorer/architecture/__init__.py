"""Main bids_explorer object.

This module contains the `BidsArchitecture` class, which represents the
structure of a BIDS dataset. The class provides methods to query and interact
with the dataset, allowing users to select specific files based on various
criteria (subjects, sessions, datatypes, tasks, runs, etc.). It is designed
for read-only operations and does not modify the underlying dataset structure.
"""
from bids_explorer.architecture.architecture import BidsArchitecture

__all__ = ["BidsArchitecture"]
