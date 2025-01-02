"""Core BIDS architecture implementation."""

import copy
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union
from warnings import warn

import pandas as pd

from bids_explorer.paths import BidsPath, BidsQuery
from bids_explorer.utils.database import set_database
from bids_explorer.utils.errors import merge_error_logs, set_errors

from .mixins import BidsArchitectureMixin, prepare_for_operations
from .validation import validate_bids_file


class BidsArchitecture(BidsArchitectureMixin):
    """Main class for handling BIDS directory structure."""

    def __init__(self, root: Optional[Union[str, Path]] = None):  # noqa: ANN204
        """Initialize BIDS architecture.

        Args:
            root: Optional root path to BIDS directory.
        """
        self.root = Path(root) if root else None
        if root:
            self._path_handler = BidsQuery(root=self.root)
            self.create_database()

    def __repr__(self) -> str:  # noqa: D105
        if not self._database.empty:
            return (
                f"BidsArchitecture: {len(self._database)} files, "
                f"{len(self._errors)} errors, "
                f"subjects: {len(self._database['subject'].unique())}, "
                f"sessions: {len(self._database['session'].unique())}, "
                f"datatypes: {len(self._database['datatype'].unique())}, "
                f"tasks: {len(self._database['task'].unique())}"
            )
        return "BidsArchitecture: No database created yet."

    def __str__(self) -> str:  # noqa: D105
        return self.__repr__()

    def __len__(self) -> int:  # noqa: D105
        return len(self._database)

    def __getitem__(self, index: int) -> pd.DataFrame:  # noqa: D105
        return self._database.iloc[index]

    def __setitem__(self, index: int, value: pd.DataFrame):  # noqa: ANN204, D105
        raise NotImplementedError("Setting items is not supported")

    def __iter__(self) -> Iterator[Path]:  # noqa: D105
        return iter(self._database.iterrows())

    def __add__(self, other: "BidsArchitecture") -> "BidsArchitecture":
        """Union of two BidsArchitecture instances.

        Combines two BidsArchitecture instances, keeping unique files
        from both.

        Args:
            other: Another BidsArchitecture instance to combine with.

        Returns:
            BidsArchitecture: New instance containing files from both
                              architectures.

        Raises:
            ValueError: If other is not a BidsArchitecture instance or has
                        invalid columns.
        """
        _ = prepare_for_operations(self, other)
        non_duplicates = other._database.index.difference(self._database.index)
        combined_db = pd.concat(
            [self._database, other._database.loc[non_duplicates]]
        )
        new_instance = BidsArchitecture()
        set_database(new_instance, combined_db)
        set_errors(new_instance, merge_error_logs(self, other))
        return new_instance

    def __sub__(self, other: "BidsArchitecture") -> "BidsArchitecture":
        """Difference of two BidsArchitecture instances.

        Creates a new instance containing files present in self but not in
        other.

        Args:
            other: BidsArchitecture instance to subtract.

        Returns:
            BidsArchitecture: New instance containing files unique to self.

        Raises:
            ValueError: If other is not a BidsArchitecture instance or has
            invalid columns.
        """
        indices_other = prepare_for_operations(self, other)
        remaining_indices = self._database.index.difference(indices_other)
        new_instance = BidsArchitecture()
        set_database(new_instance, self._database.loc[remaining_indices])
        set_errors(new_instance, merge_error_logs(self, other))
        return new_instance

    def __and__(self, other: "BidsArchitecture") -> "BidsArchitecture":
        """Intersection of two BidsArchitecture instances.

        Creates a new instance containing only files present in both
        architectures.

        Args:
            other: BidsArchitecture instance to intersect with.

        Returns:
            BidsArchitecture: New instance containing common files.

        Raises:
            ValueError: If other is not a BidsArchitecture instance or has
            invalid columns.
        """
        indices_other = prepare_for_operations(self, other)
        common_indices = self._database.index.intersection(indices_other)

        new_instance = BidsArchitecture()
        set_database(new_instance, self._database.loc[common_indices])
        set_errors(new_instance, merge_error_logs(self, other))
        return new_instance

    @property
    def database(self) -> pd.DataFrame:
        """Get database of matching files."""
        conditions = (
            hasattr(self, "_database"),
            self._database.empty,
            self.root is not None,
        )
        if all(conditions):
            self.create_database()
        return self._database

    @property
    def errors(self) -> pd.DataFrame:
        """Get error log database."""
        conditions = (
            hasattr(self, "_database"),
            self._database.empty,
            self.root is not None,
        )
        if all(conditions):
            self.create_database()
        return self._errors

    def _get_unique_values(self, column: str) -> List[str]:
        """Get sorted unique non-None values for a given column.

        Args:
            column: Name of the database column

        Returns:
            List[str]: Sorted list of unique non-None values
        """
        return sorted(
            [
                elem
                for elem in self._database[column].unique()
                if elem is not None
            ]
        )

    @property
    def subjects(self) -> List[str]:
        """Get unique subject identifiers.

        Returns:
            List[str]: Sorted list of subject IDs
        """
        return self._get_unique_values("subject")

    @property
    def sessions(self) -> List[str]:
        """Get unique session identifiers.

        Returns:
            List[str]: Sorted list of session IDs
        """
        return self._get_unique_values("session")

    @property
    def datatypes(self) -> List[str]:
        """Get unique datatypes.

        Returns:
            List[str]: Sorted list of datatypes
        """
        return self._get_unique_values("datatype")

    @property
    def tasks(self) -> List[str]:
        """Get unique task identifiers.

        Returns:
            List[str]: Sorted list of task IDs
        """
        return self._get_unique_values("task")

    @property
    def runs(self) -> List[str]:
        """Get unique run numbers.

        Returns:
            List[str]: Sorted list of run numbers
        """
        return self._get_unique_values("run")

    @property
    def acquisitions(self) -> List[str]:
        """Get unique acquisition identifiers.

        Returns:
            List[str]: Sorted list of acquisition IDs
        """
        return self._get_unique_values("acquisition")

    @property
    def descriptions(self) -> List[str]:
        """Get unique description identifiers.

        Returns:
            List[str]: Sorted list of description IDs
        """
        return self._get_unique_values("description")

    @property
    def suffixes(self) -> List[str]:
        """Get unique suffixes.

        Returns:
            List[str]: Sorted list of suffixes
        """
        return self._get_unique_values("suffix")

    @property
    def extensions(self) -> List[str]:
        """Get unique file extensions.

        Returns:
            List[str]: Sorted list of file extensions
        """
        return self._get_unique_values("extension")

    def create_database_and_error_log(self) -> None:
        """Create database and error log from BIDS dataset."""
        if not self.root:
            return

        # Initialize empty DataFrames
        self._database = pd.DataFrame()
        self._errors = pd.DataFrame(
            columns=["filename", "error_type", "error_message"]
        )

        files = list(self.root.rglob("*.vhdr"))
        for file in files:
            try:
                # Validate file
                validate_bids_file(file)

            except Exception as e:
                # Add error to error log
                new_error = pd.DataFrame(
                    {
                        "filename": [str(file)],
                        "error_type": [str(e.__class__.__name__)],
                        "error_message": [str(e)],
                    }
                )
                self._errors = pd.concat(
                    [self._errors, new_error], ignore_index=True
                )
                continue  # Skip adding to database

    def create_database(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Scan filesystem and build DataFrame of matching files.

        Walks through the BIDS directory structure and creates two DataFrames:
        one for valid files and one for errors encountered during scanning.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing
                                               (database, error_log)

        Raises:
            ValueError: If root directory is not set.
        """
        if not self.root:
            raise ValueError("Root directory not set")

        database_keys = [
            "inode",
            "root",
            "subject",
            "session",
            "datatype",
            "task",
            "run",
            "acquisition",
            "description",
            "suffix",
            "extension",
            "atime",
            "mtime",
            "ctime",
            "filename",
        ]

        data: Dict[str, List[Any]] = {key: [] for key in database_keys}
        error_flags: Dict[str, List[Any]] = {
            "filename": [],
            "error_type": [],
            "error_message": [],
            "inode": [],
        }

        for file in self._path_handler.generate():
            if "test" in file.name.lower():
                continue

            try:
                validate_bids_file(file)
                bids_path = BidsPath.from_filename(file)
                self._add_file_to_database(file, bids_path, data)
            except Exception as e:
                self._add_error_to_log(file, e, error_flags)

        self._database, self._errors = self._create_dataframes(
            data, error_flags
        )

        return self

    def _add_file_to_database(
        self, file: Path, bids_path: BidsPath, data: Dict[str, List[Any]]
    ) -> None:
        """Add file information to database dictionary.

        Args:
            file: Path object representing the file.
            bids_path: BidsPath instance containing parsed BIDS entities.
            data: Dictionary to store file information.
        """
        for key, value in bids_path.__dict__.items():
            if key == "root":
                data["root"].append(self.root)
            else:
                data[key].append(value)

        file_stats = file.stat()
        data["inode"].append(int(file_stats.st_ino))
        data["atime"].append(int(file_stats.st_atime))
        data["mtime"].append(int(file_stats.st_mtime))
        data["ctime"].append(int(file_stats.st_ctime))
        data["filename"].append(file)

    def _add_error_to_log(
        self, file: Path, error: Exception, error_flags: Dict[str, List[Any]]
    ) -> None:
        """Add error information to error log dictionary.

        Args:
            file: Path object representing the problematic file.
            error: Exception that was raised.
            error_flags: Dictionary to store error information.
        """
        error_flags["filename"].append(file)
        error_flags["error_type"].append(error.__class__.__name__)
        error_flags["error_message"].append(str(error))
        error_flags["inode"].append(file.stat().st_ino)

    def _create_dataframes(
        self, data: Dict[str, List[Any]], error_flags: Dict[str, List[Any]]
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Create DataFrames from collected data.

        Args:
            data: Dictionary containing file information.
            error_flags: Dictionary containing error information.

        Returns:
            tuple[pd.DataFrame, pd.DataFrame]: Tuple containing
                                               (database, error_log).
        """
        data_df = pd.DataFrame(
            data,
            index=data["inode"],
            columns=[key for key in data.keys() if key != "inode"],
        )
        error_df = pd.DataFrame(
            error_flags,
            index=error_flags["inode"],
            columns=[key for key in error_flags.keys() if key != "inode"],
        )
        return data_df, error_df

    def print_errors_log(self) -> None:
        """Print summary of errors encountered during database creation.

        Displays the number of files with errors and the types of errors
        encountered.
        If no errors were found, prints a confirmation message.
        """
        if self.errors.empty:
            print("No errors found")
        else:
            print(f"Number of files: {len(self.errors)}")
            print(f"Error types: {self.errors['error_type'].unique()}")

    def _get_range(
        self,
        dataframe_column: pd.core.series.Series,
        start: int | str | None = None,
        stop: int | str | None = None,
    ) -> pd.core.series.Series:
        if isinstance(start, str):
            start = int(start)

        if isinstance(stop, str):
            stop = int(stop)

        dataframe_column = dataframe_column.apply(lambda s: int(s))

        if start is None or start == "*":
            start = min(dataframe_column)

        if stop is None or stop == "*":
            stop = max(dataframe_column)

        return (start <= dataframe_column) & (dataframe_column < stop)

    def _get_single_loc(
        self, dataframe_column: pd.core.series.Series, value: str
    ) -> pd.core.series.Series:
        locations_found = dataframe_column == value
        if not any(locations_found):
            warn("No location corresponding found in the database")
            locations_found.apply(lambda s: not (s))

        return locations_found

    def _is_numerical(
        self, dataframe_column: pd.core.series.Series
    ) -> pd.core.series.Series:
        return all(dataframe_column.apply(lambda x: str(x).isdigit()))

    def _interpret_string(
        self,
        dataframe_column: pd.core.series.Series,
        string: str,
    ) -> pd.core.series.Series:
        """Interpret string patterns for database filtering.

        Args:
            dataframe_column: Series containing the column data to filter
            string: String pattern to interpret (e.g. "1-5" for range)

        Returns:
            pd.core.series.Series: Boolean mask for matching rows
        """
        if "-" in string:
            start, stop = string.split("-")
            conditions = [
                (start.isdigit() or start == "*"),
                (stop.isdigit() or stop == "*"),
            ]

            if not all(conditions):
                raise ValueError(
                    "Input must be 2 digits separated by a `-` or "
                    "1 digit and a wild card `*` separated by a `-`"
                )

            return self._get_range(
                dataframe_column=dataframe_column,
                start=int(start) if start.isdigit() else None,
                stop=int(stop) if stop.isdigit() else None,
            )

        else:
            return self._get_single_loc(dataframe_column, string)

    def _perform_selection(
        self, dataframe_column: pd.core.series.Series, value: str
    ) -> pd.core.series.Series:
        if self._is_numerical(dataframe_column):
            return self._interpret_string(dataframe_column, value)
        else:
            return self._get_single_loc(dataframe_column, value)

    def _create_mask(self, **kwargs) -> pd.Series:  # noqa: ANN003
        """Create boolean mask for filtering DataFrame.

        Creates an optimized boolean mask for filtering the database based on
        provided BIDS entities.

        Args:
            **kwargs: BIDS entities to filter by
                      (e.g., subject='01', session='1').

        Returns:
            pd.Series: Boolean mask for filtering DataFrame.

        Raises:
            ValueError: If invalid selection keys are provided.
        """
        valid_keys = {
            "subject",
            "session",
            "datatype",
            "task",
            "run",
            "acquisition",
            "description",
            "suffix",
            "extension",
        }

        invalid_keys = set(kwargs.keys()) - valid_keys
        if invalid_keys:
            raise ValueError(f"Invalid selection keys: {invalid_keys}")

        valid_inodes = set(self._database.index)

        for key, value in kwargs.items():
            if value is None:
                continue

            if isinstance(value, list):
                # Get inodes matching any value in the list
                matching_inodes = set(
                    self._database[self._database[key].isin(value)].index
                )
                valid_inodes &= matching_inodes
                continue

            if not isinstance(value, str):
                continue

            value = value.strip()
            if not value:
                continue

            col = self._database[key]

            # Handle numerical range queries more efficiently
            if "-" in value and self._is_numerical(col):
                start, stop = value.split("-")
                conditions = [
                    (start.isdigit() or start == "*"),
                    (stop.isdigit() or stop == "*"),
                ]

                if not all(conditions):
                    raise ValueError(
                        "Input must be digits separated by a `-` or "
                        "digits and a wild card `*` separated by a `-`"
                    )

                if all(conditions):
                    # Convert column to numeric once
                    col_numeric = pd.to_numeric(col, errors="coerce")

                    start_val = (
                        int(start) if start.isdigit() else col_numeric.min()
                    )
                    stop_val = (
                        int(stop) if stop.isdigit() else col_numeric.max()
                    )

                    # Get inodes for rows within range
                    range_mask = (col_numeric >= start_val) & (
                        col_numeric <= stop_val
                    )
                    matching_inodes = set(self._database[range_mask].index)
                    valid_inodes &= matching_inodes

            matching_inodes = set(self._database[col == value].index)
            valid_inodes &= matching_inodes

        return self._database.index.isin(valid_inodes)

    def select(self, inplace: bool = False, **kwargs) -> "BidsArchitecture":  # noqa: ANN003
        """Select files from database based on BIDS entities.

        Args:
            inplace: If True, modify the current instance. If False,
                     return a new instance.
            **kwargs: BIDS entities to filter by (
                      e.g., subject='01', session='1').

        Returns:
            BidsArchitecture: Filtered instance containing only matching files.

        Examples:
            >>> bids = BidsArchitecture(
            ...     "path/to/data"
            ... )
            >>> # Select all files for subject '01' and session '1'
            >>> subset = bids.select(
            ...     subject="01",
            ...     session="1",
            ... )
        """
        mask = self._create_mask(**kwargs)
        if inplace:
            setattr(self, "_database", self._database.loc[mask])
            return self

        new_instance = copy.deepcopy(self)
        setattr(new_instance, "_database", new_instance._database.loc[mask])
        return new_instance

    def remove(
        self, inplace: bool = False, **kwargs: str | list[str] | None
    ) -> "BidsArchitecture":
        """Remove files from database based on BIDS entities.

        Args:
            inplace: If True, modify the current instance.
                     If False, return a new instance.
            **kwargs: BIDS entities to filter by for removal.

        Returns:
            BidsArchitecture: Instance with specified files removed.

        Examples:
            >>> bids = BidsArchitecture(
            ...     "path/to/data"
            ... )
            >>> # Remove all files for subject '01'
            >>> filtered = (
            ...     bids.remove(
            ...         subject="01"
            ...     )
            ... )
        """
        mask = self._create_mask(**kwargs)
        if inplace:
            setattr(self, "_database", self._database.loc[~mask])
            return self

        new_instance = copy.deepcopy(self)
        setattr(new_instance, "_database", new_instance._database.loc[~mask])
        return new_instance
