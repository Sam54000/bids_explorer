from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from bids_explorer.architecture.architecture import BidsArchitecture
from bids_explorer.paths.query import BidsQuery
from bids_explorer.utils.parsing import parse_bids_filename


@dataclass
class Electrodes:
    def from_file(self, electrode_file: Path, channels_file: Path):
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

    def from_dataframe(self, dataframe=pd.DataFrame):
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
    electrodes: list[Electrodes]
