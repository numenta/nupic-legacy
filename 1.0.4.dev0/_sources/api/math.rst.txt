Math
====

.. automodule:: nupic.math

The primary sub-modules include (use help on these modules for additional
online documentation):

Stats
-----

.. automodule:: nupic.math.stats
   :members:

Topology
--------

.. automodule:: nupic.math.topology
   :members:

NuPIC C++ Math Lib
------------------

A module containing many low-level mathematical data structures and algorithms.
This module is a set of Python bindings for the Numenta C++ math libraries.
Because of this, some calling conventions may more closely reflect the underlying
C++ architecture than a typical Python module.
All classes, functions and constants of :mod:`nupic.bindings.math` are pre-imported
into :mod:`nupic.math`, and thus are accessible from :mod:`nupic.math`.

The module contains the following important and frequently used classes:

* :class:`nupic.bindings.math.SparseMatrix`
* :class:`SparseTensor`
* :class:`TensorIndex`
* :class:`Domain`


.. automodule:: nupic.bindings.math
   :members: