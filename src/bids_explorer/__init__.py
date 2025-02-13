"""
.. include:: ../../README.md

User Guide
----------

Getting Started
~~~~~~~~~~~~~~

The ``bids_explorer`` package provides tools for exploring and querying BIDS
datasets.
Here's a quick example to get you started:

.. code-block:: python

    from bids_explorer.architecture.architecture import BidsArchitecture

    # Initialize with your BIDS dataset root
    bids = BidsArchitecture("path/to/bids/dataset")

    # Print the subjects in the dataset
    print(bids.subjects)


    # Select data for specific subjects
    sub01_data = bids.select(subject="01")

    # Print any validation errors
    bids.print_errors_log()

Common Use Cases
~~~~~~~~~~~~~~

1. Selecting Data
----------------

The package provides flexible ways to select data:

.. code-block:: python

    # Select specific subject and session
    subset = bids.select(subject="01", session="1")

    # Select multiple subjects
    subset = bids.select(subject=["01", "02"])

    # Select range of sessions
    subset = bids.select(session="1-3")

    # Select with wildcards
    subset = bids.select(session="1-*")  # All sessions from 1 onwards

2. Working with Electrodes
-------------------------

This feature is under development. Contributions are welcome!

3. Query Patterns
----------------

Use flexible query patterns:

.. code-block:: python

    # Get all files for a specific task
    task_data = bids.select(task="rest")

    # Get specific file types
    eeg_data = bids.select(datatype="eeg", suffix="eeg", extension=".set")

Advanced Usage
~~~~~~~~~~~~~

1. Error Handling
----------------

The package provides comprehensive error checking when file doesn't respect
BIDS structure. We can have a entire log of all files that are not BIDS
compatibel:

.. code-block:: python

    # Check for BIDS validation errors
    bids.print_errors_log()

    # Handle specific validation cases
    if not bids.errors.empty:
        print("Found validation errors:")
        print(bids.errors['error_type'].unique())

2. Custom Queries
----------------

Create complex queries:

.. code-block:: python

    # Combine multiple criteria
    subset = bids.select(
        subject="01",
        session="1-3",
        task="rest",
        run="1",
        suffix="bold",
        extension=".nii.gz"
    )

Best Practices
~~~~~~~~~~~~~

1. Always initialize with the correct BIDS root directory
2. Check for validation errors before processing data
3. Use appropriate wildcards and ranges for flexible queries
4. Chain selections for complex queries
5. Handle errors appropriately in your applications

"""  # noqa: D200, D415, D212
