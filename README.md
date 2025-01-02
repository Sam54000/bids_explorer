[![DOI](https://zenodo.org/badge/657341621.svg)](https://zenodo.org/doi/10.5281/zenodo.10383685)


- [ ] If it hasn't already been done for your organization/acccount, grant third-party app permissions for CodeCov.
- [ ] To set up an API documentation website, after the first successful build, go to the `Settings` tab of your repository, scroll down to the `GitHub Pages` section, and select `gh-pages` as the source. This will generate a link to your API docs.
- [ ] Update stability badge in `README.md` to reflect the current state of the project. A list of stability badges to copy can be found [here](https://github.com/orangemug/stability-badges). The [node documentation](https://nodejs.org/docs/latest-v20.x/api/documentation.html#documentation_stability_index) can be used as a reference for the stability levels.

# BIDS Explorer
Tool for exploring BIDS datasets which is more flexible than mne-bids or pybids
(which are both great tools I use very often).

[![Build](https://github.com/Sam54000/bids_explorer/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/Sam54000/bids_explorer/actions/workflows/test.yaml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/Sam54000/bids_explorer/branch/main/graph/badge.svg?token=22HWWFWPW5)](https://codecov.io/gh/Sam54000/bids_explorer)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![stability-stable](https://img.shields.io/badge/stability-stable-green.svg)
[![LGPL--3.0 License](https://img.shields.io/badge/license-LGPL--3.0-blue.svg)](https://github.com/Sam54000/bids_explorer/blob/main/LICENSE)
[![pages](https://img.shields.io/badge/api-docs-blue)](https://Sam54000.github.io/bids_explorer)

## Features

## Installation

Install this package via :

```sh
pip install bids_explorer
```

Or get the newest development version via:

```sh
pip install git+https://github.com/childmindresearch/bids_explorer
```

## Quick start


The main class is `BidsArchitecture`.
```Python
import bids_explorer

# Create an instance of BidsArchitecture
bids = bids_explorer.BidsArchitecture(root="path/to/bids/dataset")

```

the BidsArchitecture instance has several attributes which define the BIDS
dataset such as `subject`, `session`, `task`, `acquisition`, `run`, `suffix`.

In the example above `bids.subject` will give a list of all the subjects in the
BIDS dataset provided.
### Selecting files
It is possible to select files based on BIDS entities.
```Python
selected_files = bids.select(subject="01", session="01")
```
This will return a new instance of `BidsArchitecture` with the selected files.

### Performing operations between two `BidsArchitecture` instances
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

### Removing entries from the `BidsArchitecture` instance
It is possible to remove entries from the `BidsArchitecture` instance.
```Python
bids = bids.remove(subject="01", session="01")
```
This will return a new instance of `BidsArchitecture` with the specified files removed.
