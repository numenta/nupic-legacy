.. include:: common.rst

Quick Start
===========

Install NuPIC
-------------

.. code-block:: bash

   pip install nupic [--user]

The ``--user`` is in brackets because it is optional. See the
`pip reference guide <https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-user>`_
for details.

The output of this command should end with:

::

    Successfully installed nupic-X.X.X nupic.bindings-X.X.X

where ``X.X.X`` represents the most recent versions shown for each project at:

* https://pypi.python.org/pypi/nupic
* https://pypi.python.org/pypi/nupic.bindings

If your installation was unsuccessful, you can find help on
`NuPIC Forums <https://discourse.numenta.org/c/nupic/>`_ and on
`Github <https://github.com/numenta/nupic/issues/>`_.

Choose Your API
---------------

You can choose to construct an HTM `several ways <../api>`_ with NuPIC. Below are Quick Start
guides for each interface:

.. toctree::
    :maxdepth: 3

    opf
    network
    algorithms
