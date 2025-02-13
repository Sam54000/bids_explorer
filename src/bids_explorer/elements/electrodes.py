"""This module aims to deal with electrodes files and convert them into class.

The electrodes files should be in csv or tsv format according to the BIDS
standard.
"""
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from bids_explorer.utils.parsing import parse_bids_filename


@dataclass
class Electrodes:
    """Class to handle the electrodes data and metadata.

    This class provides functionality for working with BIDS-compliant electrode
    and channel data files. It's particularly useful for analyzing and
    visualizing electrode positions, impedances, and other properties across
    subjects and sessions.

    The class can be instantiated either from BIDS-compliant files or from an
    existing pandas DataFrame.

    Attributes:
        data (pd.DataFrame):
            Combined DataFrame containing both electrode and channel information.
        spaces (List[str]):
            List of coordinate spaces present in the data.
        subjects (List[str]):
            List of subject IDs present in the data.
        sessions (List[str]):
            List of session IDs present in the data.
        datatypes (List[str]):
            List of datatypes present in the data.
        tasks (List[str]):
            List of tasks present in the data.
        runs (List[str]):
            List of runs present in the data.
        acquisitions (List[str]):
            List of acquisition labels present in the data.
        descriptions (List[str]):
            List of description labels present in the data.

    Examples:
        Loading from Files:
            >>> # Initialize electrodes object
            >>> electrodes = (
            ...     Electrodes()
            ... )
            >>> # Load from BIDS files
            >>> electrodes.from_file(
            ...     electrode_file="sub-01/ses-1/ieeg/sub-01_ses-1_space-MNI152_electrodes.tsv",
            ...     channels_file="sub-01/ses-1/ieeg/sub-01_ses-1_channels.tsv",
            ... )

        Loading from DataFrame:
            >>> # Create from existing DataFrame
            >>> import pandas as pd
            >>> df = pd.DataFrame(
            ...     {
            ...         "name": [
            ...             "E1",
            ...             "E2",
            ...         ],
            ...         "x": [0, 1],
            ...         "y": [0, 1],
            ...         "z": [0, 1],
            ...         "size": [
            ...             0.5,
            ...             0.5,
            ...         ],
            ...         "type": [
            ...             "ECOG",
            ...             "ECOG",
            ...         ],
            ...     }
            ... )
            >>> electrodes.from_dataframe(
            ...     df
            ... )

        Accessing Data:
            >>> # Get all electrode names
            >>> print(
            ...     electrodes.data[
            ...         "name"
            ...     ].unique()
            ... )
            >>> # Get coordinate information
            >>> coords = (
            ...     electrodes.data[
            ...         [
            ...             "x",
            ...             "y",
            ...             "z",
            ...         ]
            ...     ]
            ... )
            >>> # Get electrode types
            >>> types = (
            ...     electrodes.data[
            ...         "type"
            ...     ].unique()
            ... )

    Notes:
        - Files should follow BIDS specification for electrodes and channels
        - The electrodes.tsv file should contain position information
        - The channels.tsv file should contain recording parameters
        - Data is merged based on the 'name' column
        - All BIDS entities are extracted from filenames
    """

    def from_file(
        self, electrode_file: Path, channels_file: Path
    ) -> "Electrodes":
        """Instantiate an Electrodes object from an 2 csv file.

        The first file contains the electrode data and the second file
        contains the channels data according to the BIDS specifications.

        Args:
            electrode_file (Path): Path to the electrode csv file.
            channels_file (Path): Path to the channels csv file.

        Returns:
            Electrodes: An Electrodes object.
        """
        electrode_data = pd.read_csv(electrode_file, sep="\t")
        channels_data = pd.read_csvs(channels_file, sep="\t")
        entities = parse_bids_filename(electrode_file)
        entities.update(parse_bids_filename(channels_file))

        self.data = electrode_data.merge(channels_data, on="name", how="outer")

        self.spaces = [entities["space"]]
        self.subjects = [entities["subject"]]
        self.sessions = [entities["session"]]
        self.datatypes = [entities["datatype"]]
        self.tasks = [entities.get("task", None)]
        self.runs = [entities.get("run", None)]
        self.acquisitions = [entities.get("acquisition", None)]
        self.descriptions = [entities.get("description", None)]

        return self

    def from_dataframe(self, dataframe: pd.DataFrame) -> "Electrodes":
        """Instantiate an Electrodes object from a pandas DataFrame.

        Usually used when the data is already taken care from another process.

        Args:
            dataframe (pd.DataFrame): A pandas DataFrame containing the
            electrodes data.

        Returns:
            Electrodes: An Electrodes object.
        """
        self.data = dataframe
        self.spaces = dataframe["space"].unique()
        self.subjects = dataframe["subject"].unique()
        self.sessions = dataframe["session"].unique()
        self.datatypes = dataframe["datatype"].unique()
        self.tasks = dataframe["task"].unique()
        self.runs = dataframe["run"].unique()
        self.acquisitions = dataframe["acquisition"].unique()
        self.descriptions = dataframe["description"].unique()

        return self


class ElectrodesCollection:
    """Class to handle a collection of Electrodes objects.

    This is to facilitate the processing of multiple electrodes data.
    """

    pass
