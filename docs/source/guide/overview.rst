NuPIC exposes three primary interfaces: the the
`Online Prediction Framework (OPF) <opf.html>`_,
the `Network API <network.html>`_, and the core `Algorithms <algorithms.html>`_.

The **OPF** is an easier-to-use interface, but compromises the flexibility to create
new network structures. The OPF takes a typical network design and wraps it in a
model class so it can be easily created. Many of our examples use the OPF
because it is easier to set up new experiments.

The **Network API** allows users to create a network structure with each node
performing a different task, making for a very flexible experiment framework and
a future foundation for hierarchy.

For those more comfortable with HTM theory, the **core Algorithms** provide direct
access to HTM algorithsm like Spatial Pooling and Temporal Memory. This allows
you to instatiate these components manually and wire together your own system
with encoders and classifiers.

There is also an API for `Swarming <swarming.html>`_, which allows
users to find the best model parameters for a particular data set using a
particle swarm optimization algorithm. This API is not always needed, however.
You can always use existing model parameters and tweak them to your needs.
