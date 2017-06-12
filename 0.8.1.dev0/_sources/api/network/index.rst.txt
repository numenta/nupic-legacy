Network API
-----------

The Network API is a lower-level API designed to allow users the power and
flexibility to construct hierarchical structures of nodes. For more detailed
information, see the `Network API Guide <../../guides/network.html>`_ and
`Network API Quick Start <../../quick-start/network.html>`_.

The Network API interface is defined in C++, but also exported in a Python
interface. So it can be used from either C++ or Python.

    An HTM Network is a collection of Regions that implement HTM algorithms and
    other algorithms. The Network Engine allows users to create and manipulate
    HTM Networks.

Examples of Network API usages can be found at
`examples/network <https://github.com/numenta/nupic/tree/master/examples/network>`_.

--------------------------------------------

.. toctree::
   :maxdepth: 3

   network
   regions
   sensors
   viz
