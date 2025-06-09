"""Main BIDS architecture implementation."""
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union
from warnings import warn

import pandas as pd

from bids_explorer.architecture.mixins import (
    BidsArchitectureMixin,
    prepare_for_operations,
)
from bids_explorer.architecture.validation import (
    all_columns_valid,
    validate_bids_file,
)
from bids_explorer.paths.query import BidsQuery
from bids_explorer.utils.errors import merge_error_logs
from bids_explorer.utils.parsing import parse_bids_filename


class BidsArchitecture(BidsArchitectureMixin):
    """Main class for handling BIDS directory structure.

    Args:
        root: Optional root path to BIDS directory.

    Attributes:
        root (Optional[Path]):
            Path to the BIDS directory root, or None if not set.
        database (pd.DataFrame):
            DataFrame containing all BIDS files and their metadata.
        errors (List[Dict[str, Any]]):
            List of validation errors found during database creation.
        subjects (List[str]):
            List of subjects IDs present in the instance.
        sessions (List[str]):
            List of session IDs present in the instance.
        datatypes (List[str]):
            List of datatypes present in the dataset.
        tasks (List[str]):
            List of task names present in the dataset.
        runs (List[str]):
            List of run numbers present in the dataset.
    """

    def __init__(  # noqa: D107
        self,
        root: Optional[Union[str, Path]] = None,
        subject: Optional[str] = None,
        session: Optional[str] = None,
        datatype: Optional[str] = None,
        task: Optional[str] = None,
        run: Optional[str] = None,
        acquisition: Optional[str] = None,
        recording: Optional[str] = None,
        description: Optional[str] = None,
        suffix: Optional[str] = None,
        extension: Optional[str] = None,
    ) -> None:
        self.root = Path(root) if root else None
        if root:
            self._path_handler = BidsQuery(
                root=self.root,
                subject=subject,
                session=session,
                datatype=datatype,
                task=task,
                run=run,
                acquisition=acquisition,
                recording=recording,
                description=description,
                suffix=suffix,
                extension=extension,
            )
            self._database, self._errors = self.create_database()
        else:
            self._database = pd.DataFrame()
            self._errors = pd.DataFrame()

    def __repr__(self) -> str:  # noqa: D105
        if hasattr(self, "_database"):
            return (
                f"BidsArchitecture: {len(self._database)} files, "
                f"{len(self._errors)} errors, "
                f"subjects: {len(self._get_unique_values('subject'))}, "
                f"sessions: {len(self._get_unique_values('session'))}, "
                f"datatypes: {len(self._get_unique_values('datatype'))}, "
                f"recordings: {len(self._get_unique_values('recording'))}, "
                f"tasks: {len(self._get_unique_values('task'))}"
            )
        else:
            empty_repr = (
                "BidsArchitecture: 0 files, "
                "0 errors, "
                "subjects: 0, "
                "sessions: 0, "
                "datatypes: 0, "
                "recordings: 0, "
                "tasks: 0"
            )
            return empty_repr

    def __str__(self) -> str:  # noqa: D105
        return self.__repr__()

    def __len__(self) -> int:  # noqa: D105
        return len(self._database)

    def __getitem__(self, index: int) -> pd.DataFrame:  # noqa: D105
        return self._database.iloc[index]

    def __setitem__(self, index: int, value: pd.DataFrame) -> None:  # noqa: D105
        raise NotImplementedError("Setting items is not supported")

    def __iter__(self) -> Iterator[pd.DataFrame]:
        """Iterate over rows in the database."""
        return self._database.iterrows()

    def __add__(  # noqa: D105
        self,
        other: "BidsArchitecture",
    ) -> "BidsArchitecture":
        _ = prepare_for_operations(self, other)
        non_duplicates = other._database.index.difference(self._database.index)
        combined_db = pd.concat(
            [self._database, other._database.loc[non_duplicates]]
        )
        new_instance = BidsArchitecture()
        new_instance._database = combined_db
        new_instance._errors = merge_error_logs(self, other)
        return new_instance

    def __sub__(  # noqa: D105
        self,
        other: "BidsArchitecture",
    ) -> "BidsArchitecture":
        indices_other = prepare_for_operations(self, other)
        remaining_indices = self._database.index.difference(indices_other)
        new_instance = BidsArchitecture()
        new_instance._database = self._database.loc[remaining_indices]
        new_instance._errors = merge_error_logs(self, other)
        return new_instance

    def __and__(  # noqa: D105
        self,
        other: "BidsArchitecture",
    ) -> "BidsArchitecture":
        indices_other = prepare_for_operations(self, other)
        common_indices = self._database.index.intersection(indices_other)

        new_instance = BidsArchitecture()
        new_instance._database = self._database.loc[common_indices]
        new_instance._errors = merge_error_logs(self, other)
        return new_instance

    @property
    def database(self) -> pd.DataFrame:
        """Returns the BIDS dataset as a DataFrame.

        This DataFrame represents the entire BIDS dataset with indexed files.
        Each row represents a single file, with columns containing:
        - BIDS entities (subject, session, datatype, task, run, etc.)
        - Full file path
        - UNIX metadata (atime, mtime, ctime)

        Rows are indexed by the file's inode number, which uniquely identifies
        each file in the filesystem.

        This DataFrame serves as the core representation of the BIDS dataset
        and is used for all operations.
        """
        if hasattr(self, "_database"):
            return self._database
        else:
            return pd.DataFrame()

    @database.setter
    def database(self, value: pd.DataFrame) -> None:
        valid_db = all_columns_valid(value, strict=True)
        if not valid_db:
            raise ValueError("Invalid or missing columns in database")
        self._database = value

    @property
    def errors(self) -> pd.DataFrame:
        """Returns the error log as a DataFrame.

        This DataFrame contains information about files that failed validation
        during the database creation process.
        """
        if hasattr(self, "_errors"):
            return self._errors
        else:
            return pd.DataFrame()

    @errors.setter
    def errors(self, value: pd.DataFrame) -> None:
        self._errors = value

    def _get_unique_values(self, column: str) -> List[str]:
        """Get unique values from a database column.

        Args:
            column: Name of the column to get unique values from.

        Returns:
            List of unique values, excluding None, empty strings, and NaN
            values.
            Values are converted to strings and sorted.
        """
        if self._database.empty:
            return []

        # Get unique values and convert to list for filtering
        values = self._database[column].unique()

        # Filter out None, empty strings, and NaN values
        value_list = [
            str(elem)  # Convert all values to strings
            for elem in values
            if pd.notna(elem)  # Handles both None and np.nan
            and str(elem).strip() != ""  # Handles empty strings and whitespace
        ]

        return sorted(value_list)

    @property
    def subjects(self) -> List[str]:
        """Returns a list of unique subjects present in the dataset.

        This list contains all the subject IDs found in the BIDS dataset or
        after a selection has been performed.
        """
        return self._get_unique_values("subject")

    @property
    def sessions(self) -> List[str]:
        """Returns a list of unique sessions present in the dataset.

        This list contains all the session IDs found in the BIDS dataset or
        after a selection has been performed.
        """
        return self._get_unique_values("session")

    @property
    def datatypes(self) -> List[str]:
        """Returns a list of unique datatypes present in the dataset.

        This list contains all the datatypes found in the BIDS dataset or
        after a selection has been performed.
        """
        return self._get_unique_values("datatype")

    @property
    def tasks(self) -> List[str]:
        """Returns a list of unique tasks present in the dataset.

        This list contains all the task names found in the BIDS dataset or
        after a selection has been performed.
        """
        return self._get_unique_values("task")

    @property
    def runs(self) -> List[str]:
        """Returns a list of unique runs present in the dataset.

        This list contains all the run numbers found in the BIDS dataset or
        after a selection has been performed.
        """
        return self._get_unique_values("run")

    @property
    def acquisitions(self) -> List[str]:
        """Returns a list of unique acquisitions present in the dataset.

        This list contains all the acquisition names found in the BIDS dataset
        or after a selection has been performed.
        """
        return self._get_unique_values("acquisition")

    @property
    def recordings(self) -> List[str]:
        """Returns a list of unique recordings present in the dataset.

        This list contains all the recording names found in the BIDS dataset
        or after a selection has been performed.
        """
        return self._get_unique_values("description")

    @property
    def descriptions(self) -> List[str]:
        """Returns a list of unique descriptions present in the dataset.

        This list contains all the description names found in the BIDS dataset
        or after a selection has been performed.
        """
        return self._get_unique_values("description")

    @property
    def suffixes(self) -> List[str]:
        """Returns a list of unique suffixes present in the dataset.

        This list contains all the suffixes found in the BIDS dataset or
        after a selection has been performed.
        """
        return self._get_unique_values("suffix")

    @property
    def extensions(self) -> List[str]:  # noqa: D102
        return self._get_unique_values("extension")

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
            "recording",
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
                entities = parse_bids_filename(file)
                self._add_file_to_database(file, entities, data)
            except Exception as e:
                self._add_error_to_log(file, e, error_flags)

        return self._create_dataframes(data, error_flags)

    def _add_file_to_database(
        self, file: Path, entities: dict, data: Dict[str, List[Any]]
    ) -> None:
        """Add file information to database dictionary.

        Args:
            file: Path object representing the file.
            entities: Dictionary containing parsed BIDS entities.
            data: Dictionary to store file information.
        """
        # Add root separately since it's not in entities
        data["root"].append(self.root)

        # Add all other entities
        for key in data.keys():
            if key in ["atime", "mtime", "ctime", "filename", "root", "inode"]:
                continue
            data[key].append(entities.get(key))

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
        # Validate input types
        valid_types = (int, str, type(None))
        if not isinstance(start, valid_types) or not isinstance(
            stop, valid_types
        ):
            raise ValueError(
                "Start and stop must be integers, strings, or None"
            )

        if isinstance(start, str):
            start = int(start)

        if isinstance(stop, str):
            stop = int(stop)

        dataframe_column = dataframe_column.apply(lambda s: int(s))

        if start is None or start == "*":
            start = min(dataframe_column)

        if stop is None or stop == "*":
            stop = max(dataframe_column) + 1

        return (start <= dataframe_column) & (dataframe_column < stop)

    def _get_single_loc(
        self, dataframe_column: pd.core.series.Series, value: str | None
    ) -> pd.core.series.Series:
        if not isinstance(value, (str, type(None))):
            value = str(value)
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

    def _create_mask(self, **kwargs: str | list[str] | None) -> pd.Series:
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
            "recording",
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

            if value == "":
                return pd.Series(False, index=self._database.index)

            if isinstance(value, list):
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
                    col_numeric = pd.to_numeric(col, errors="coerce")
                    start_val = (
                        int(start) if start.isdigit() else col_numeric.min()
                    )
                    stop_val = (
                        int(stop) if stop.isdigit() else col_numeric.max()
                    )
                    range_mask = (col_numeric >= start_val) & (
                        col_numeric <= stop_val
                    )
                    print(range_mask)
                    matching_inodes = set(self._database[range_mask].index)
                    valid_inodes &= matching_inodes

            else:
                matching_inodes = set(self._database[col == value].index)
                valid_inodes &= matching_inodes

        return self._database.index.isin(valid_inodes)

    def select(
        self,
        inplace: bool = False,
        **kwargs: str | list[None | str] | None,
    ) -> "BidsArchitecture":
        """Select files from database based on BIDS entities.

        It select files from the database based on the BIDS entities provided.
        The selection can be done with wildcards or ranges.

        Args:
            inplace: If True, modify the current instance. If False,
                     return a new instance.
            **kwargs: BIDS entities to filter by (
                      e.g., subject='01', session='1').

        Returns:
            BidsArchitecture: Filtered instance containing only matching files.

        Example 1:
            >>> bids = BidsArchitecture(
            ...     "path/to/data"
            ... )
            >>> subset = bids.select(
            ...     subject="01",
            ...     session="1",
            ... )

        Example 2:
            It is possible to select multiple subjects at once:
            >>> subset = (
            ...     bids.select(
            ...         subject=[
            ...             "01",
            ...             "02",
            ...         ]
            ...     )
            ... )

        Example 3:
            If we don't know the exact session number, we can use a wildcard
            with a `-` to tell we want from session 1 to the maximum number of
            sessions:
            >>> subset = bids.select(
            ...     session="1-*"
            ... )

        """
        mask = self._create_mask(**kwargs)  # type: ignore
        if inplace:
            setattr(self, "_database", self._database.loc[mask])
            return self

        new_instance = copy.copy(self)
        if any(mask):
            new_database = self._database.loc[mask]
        else:
            new_database = pd.DataFrame()

        setattr(new_instance, "_database", new_database)
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


@dataclass
class ElectrodesArchitecture:
    """Class for electrodes operations."""

    root: Path
    subject: str
    session: str
    space: str
    datatype: str
    task: str
    run: str
    acquisition: str
    description: str

    def __post_init__(self):  # noqa: ANN204, D105
        if self.root:
            self._channel_database = BidsArchitecture(
                root=self.root,
                subject=self.subject,
                session=self.session,
                datatype=self.datatype,
                task=self.task,
                run=self.run,
                acquisition=self.acquisition,
                description=self.description,
                suffix="channels",
                extension=".tsv",
            ).database

            self._electrodes_database = BidsArchitecture(
                root=self.root,
                subject=self.subject,
                session=self.session,
                space=self.space,
                suffix="electrodes",
                extension=".tsv",
            ).database

        else:
            self._channels = pd.DataFrame()
            self._errors = pd.DataFrame()
