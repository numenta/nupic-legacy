Online Prediction Framework
---------------------------

The OPF is a Python-only convenience library that uses the
`Network API <../api/network.html>`_ to construct commonly used models. The primary
classes it exposes to users are the :class:`.HTMPredictionModel` and
the :class:`.ModelFactory`.

Online Prediction Framework (OPF) is a framework for working with and deriving
predictions from online learning algorithms, including HTM. OPF is designed to
work in conjunction with a larger architecture, as well as in a standalone mode
(i.e. directly from the command line). It is also designed such that new model
algorithms and functionalities can be added with minimal code changes.

--------------------------------------------

.. toctree::
   :maxdepth: 3

   models
   clients
   description-api
   exp-runner
   environment
   metrics
   results
   utils
   exceptions
