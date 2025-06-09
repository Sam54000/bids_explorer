![bids_explorer_logo](https://github.com/Sam54000/bids_explorer/blob/main/docs/images/bids_explorer_logo.png)

Tool for exploring BIDS datasets which allows more flexibility than
[mne-bids](https://mne.tools/mne-bids/stable/index.html) or
[pybids](https://bids-standard.github.io/pybids/) (which are both
amazing tools I use very often but sometimes lack flexibility).

[![Build](https://github.com/Sam54000/bids_explorer/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/Sam54000/bids_explorer/actions/workflows/test.yaml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/Sam54000/bids_explorer/branch/main/graph/badge.svg?token=22HWWFWPW5)](https://codecov.io/gh/Sam54000/bids_explorer)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![stability-stable](https://img.shields.io/badge/stability-stable-green.svg)
[![LGPL--3.0 License](https://img.shields.io/badge/license-LGPL--3.0-blue.svg)](https://github.com/Sam54000/bids_explorer/blob/main/LICENSE)
[![pages](https://img.shields.io/badge/api-docs-blue)](https://Sam54000.github.io/bids_explorer)

# Introduction

BidsArchitecture is the primary object for managing BIDS dataset structures.
When provided with a directory (root) containing a BIDS dataset, an instance
of BidsArchitecture extracts key information about the dataset's structure and
populates a [pandas DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html)
with relevant details, such as subject identifiers, sessions,
and other metadata.

Once initialized, the instance supports various operations to filter and
select subsets of the dataset based on criteria like sessions, tasks, and
other BIDS entities.

It is assumed that the dataset adheres to the [BIDS specification](https://bids-specification.readthedocs.io/en/stable/introduction.html), following a directory tree structure similar to the example below:
```
root
├── sub-01
│   ├── ses-01
│   │   └── eeg
│   │       └── sub-01_ses-01_task-aTask_eeg.edf
│   └── ses-02
│       └── eeg
│           └── sub-01_ses-02_task-aTask_eeg.edf
└── sub-02
    │   └── eeg
    │       └── sub-02_ses-01_task-aTask_eeg.edf
    └── ses-02
        └── eeg
            └── sub-02_ses-02_task-aTask_eeg.edf
```

# Installation

For the moment this module is not published on pypi so the installation will
require you to follow these steps:

1. Make sure poetry is installed on your machine (or the remote machine you
are working on). Poetry is a dependancies and environment manager which
make easier python deployment. It is very straightforward to install, just
follow the instruction on their
[website](https://python-poetry.org/docs/#installation)
2. Go to your projects folder `cd ~/projects` (or wherever it is)
3. Clone this repository `git clone https://github.com/Sam54000/bids_explorer.git`.
4. Move to the cloned repository `cd ./bids_explorer`
5. Run `poetry install`

# Quick start

The main class is `BidsArchitecture`.
```Python
import bids_explorer

# Create an instance of BidsArchitecture
bids = bids_explorer.BidsArchitecture(root="path/to/bids/dataset")
```

The dataset will be represented by the attribute database, which is a
pandas DataFrame containing all the individual files within the dataset.

The BidsArchitecture instance also provides several attributes
corresponding to BIDS entities, such as:

- subjects
- sessions
- tasks
- acquisitions
- runs
- description
- suffixes
- extension
- datatype

```Python
>>> bids.subjects
["01","02"]
>>> bids.sessions
["01","02"]
```

In this example:
- bids.subjects returns a list of all subject identifiers.
- bids.sessions returns a list of all session identifiers.

## Selecting files
ou can select files based on BIDS entities. For example, to retrieve files
only for subject "01":
```Python
selected_files = bids.select(subject="01")
```
This will return a new instance of BidsArchitecture containing only
the selected files.

## Performing operations between two `BidsArchitecture` instances
Performing operations between two `BidsArchitecture` instances is possible.
The available operations are `+` and `-` and `*` (intersection).

```Python
bids1 = bids_explorer.BidsArchitecture(root="path/to/bids/dataset1")
bids2 = bids_explorer.BidsArchitecture(root="path/to/bids/dataset2")
```
Add 2 Architectures:
```Python
merged_architecture = bids1 + bids2
```
Subtract 2 Architectures:
```Python
subtracted_architecture = bids1 - bids2
```
Intersection of 2 Architectures:
```Python
intersection_architecture = bids1 * bids2
```

## Removing entries from the `BidsArchitecture` instance
It is possible to remove entries from the `BidsArchitecture` instance.
```Python
bids = bids.remove(subject="01", session="01")
```
This will return a new instance of `BidsArchitecture` with the specified files removed.

## Error logging
A nice feature of `BidsArchitecture` is its `errors` attributes which is a
panda DataFrame that lists all the files that doesn't follow BIDS format within
the dataset.
