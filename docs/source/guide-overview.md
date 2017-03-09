NuPIC exposes three primary interfaces: the [Network API](#the-network-api), the [Online Prediction Framework](#the-online-prediction-framework-opf) (OPF). The OPF is an easier-to-use interface, but compromises the flexibility to create new network structures.

The OPF takes a typical network design and wraps it in a model class so it can be easily created. Many of our examples use the OPF because it is easier to set up new experiments.

There is also a third API for [Swarming](#swarming), which allows users to find the best model parameters for a particular data set using a particle swarm optimization algorithm. This API is not always needed, however, so it is listed in the [Advanced](#advanced) section.
