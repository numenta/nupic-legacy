Example Data
============

The example data we want to feed into the model for the
`Quick Start <index.html>`_ looks like this:

.. literalinclude:: ../../examples/data/gymdata.csv
   :lines: 1-20

`Running Swarmings <../guides/swarming/>`_ and using the `OPF <../guides/opf/index.html>`_
requires your input data to be in a certain format, described in this document.

Header Rows
-----------

The first 3 lines of each input CSV file are special header rows. The first line contains the field names, the second line contains the field types, and the 3rd line contains special flags for each column.

Row 1: Field Names
^^^^^^^^^^^^^^^^^^

The first row consists of the names of the fields, which are used to identify input columns within swarm descriptions and model parameters. These field names are tied directly to encoders defined within model parameters.

Row 2: Field Types
^^^^^^^^^^^^^^^^^^

::

    - `datetime`

        Valid date format strings are:
        - `%Y-%m-%d %H:%M:%S.%f`
        - `%Y-%m-%d %H:%M:%S:%f`
        - `%Y-%m-%d %H:%M:%S`
        - `%Y-%m-%d %H:%M`
        - `%Y-%m-%d`
        - `%m/%d/%Y %H:%M`
        - `%m/%d/%y %H:%M`
        - `%Y-%m-%dT%H:%M:%S.%fZ`
        - `%Y-%m-%dT%H:%M:%SZ`
        - `%Y-%m-%dT%H:%M:%S`
    - `int`
    - `float`
    - `bool`
    - `string`
    - `list` - third-party - not supported

Row 3: Flags
^^^^^^^^^^^^

The allowed special flags are reset (R), sequence (S), timestamp (T), and category (C).

- `R`: reset - Specify that a reset should be inserted into the model when this field evaluates to true. This is used to manually insert resets.

Here is an example with two sequences, each with three records:

::

    reset,timestamp,value
    bool,datetime,float
    R,T,
    1,2010-07-02 00:00:00,5.4
    0,2010-07-02 00:00:15,3.6
    0,2010-07-02 00:00:30,2.4
    1,2010-09-08 10:00:00,12.7
    0,2010-09-08 10:01:15,12.8
    0,2010-09-08 10:01:30,13.1

- `S`: sequence - Specify that a reset should be inserted into the model when this field changes. This is used when you have a field that identifies sequences and you want to insert resets between each sequence.

Here is an example with two sequences, each with three records:

::

    location,timestamp,value
    string,datetime,float
    S,T,
    RWC,2010-07-02 00:00:00,5.4
    RWC,2010-07-02 00:00:15,3.6
    RWC,2010-07-02 00:00:30,2.4
    SF,2010-09-08 10:00:00,12.7
    SF,2010-09-08 10:01:15,12.8
    SF,2010-09-08 10:01:30,13.1

- `T`: timestamp - This identifies a date/time field that should be used as the timestamp for aggregation and other time-related functions.
- `C`: category - This indicates that the category encoder should be used.

Rows 4 - ∞: Data
^^^^^^^^^^^^^^^^

The remaining rows are assumed to be data rows that match the headers above.
