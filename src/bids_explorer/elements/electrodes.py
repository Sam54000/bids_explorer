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

    This is to facilitate plotting electrode data such as impedances,
    positions, or quality across a cohort of subjects.
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
