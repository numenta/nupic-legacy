API Docs
========

NuPIC exposes **three primary interfaces**:

The `Online Prediction Framework (OPF) <opf/>`_ is an easier-to-use interface,
but compromises the flexibility to create new network structures. The OPF takes
a typical network design and wraps it in a model class so it can be easily
created. Many of our examples use the OPF because it is easier to set up new
experiments. The OPF also includes `Swarming <../guides/swarming/>`_, which
allows users to find the best model parameters for a particular data set using a
particle swarm optimization algorithm. This API is not always needed, however.
You can always use existing model parameters and tweak them to your needs.

The `Network API <network/>`_ allows users to create a network structure with
each node performing a different task, making for a very flexible experiment
framework and a future foundation for hierarchy.

The `core Algorithms <algorithms/>`_ provide direct access to HTM algorithms
like Spatial Pooling and Temporal Memory for those more comfortable with HTM
theory. This allows you to instatiate these components manually and wire
together your own system with encoders and classifiers.

----------------------------------------

.. toctree::
    :maxdepth: 3

    opf/index
    network/index
    algorithms/index
    data/index
    support/index
    math
