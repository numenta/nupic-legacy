NuPIC exposes three primary interfaces: the raw `Algorithms <algorithms.html>`_,
the `Network API <network.html>`_, and the
`Online Prediction Framework (OPF) <opf.html>`_.

The OPF is an easier-to-use interface, but compromises the flexibility to create
new network structures. The OPF takes a typical network design and wraps it in a
model class so it can be easily created. Many of our examples use the OPF
because it is easier to set up new experiments.

There is also a third API for `Swarming <guide-swarming.html>`_, which allows
users to find the best model parameters for a particular data set using a
particle swarm optimization algorithm. This API is not always needed, however.
You can always use existing model parameters and tweak them to your needs.
