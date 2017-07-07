# <img src="http://numenta.org/87b23beb8a4b7dea7d88099bfb28d182.svg" alt="NuPIC Logo" width=100/> NuPIC

## Numenta Platform for Intelligent Computing

The Numenta Platform for Intelligent Computing (**NuPIC**) is a machine intelligence platform that implements the [HTM learning algorithms](http://numenta.com/learn/hierarchical-temporal-memory-white-paper.html). HTM is a detailed computational theory of the neocortex. At the core of HTM are time-based continuous learning algorithms that store and recall spatial and temporal patterns. NuPIC is suited to a variety of problems, particularly anomaly detection and prediction of streaming data sources. For more information, see [numenta.org](http://numenta.org) or the [NuPIC Forum](https://discourse.numenta.org/c/nupic).

For usage guides, quick starts, and API documentation, see <http://nupic.docs.numenta.org/>.

## This project is in Maintenance Mode

We plan to do minor releases only, and limit changes in NuPIC and NuPIC Core to:

- Fixing critical bugs.
- Features needed to support ongoing research.

## Installing NuPIC

NuPIC binaries are available for:

- Linux x86 64bit
- OS X 10.9
- OS X 10.10
- Windows 64bit

### Dependencies

The following dependencies are required to install NuPIC on all operating systems.

- [Python 2.7](https://www.python.org/)
- [pip](https://pip.pypa.io/en/stable/installing/)>=8.1.2
- [setuptools](https://setuptools.readthedocs.io)>=25.2.0
- [wheel](http://pythonwheels.com)>=0.29.0
- [numpy](http://www.numpy.org/)
- C++ 11 compiler like [gcc](https://gcc.gnu.org/) (4.8+) or [clang](http://clang.llvm.org/)

Additional OS X requirements:

- [Xcode command line tools](https://developer.apple.com/library/ios/technotes/tn2339/_index.html)

### Install

Run the following to install NuPIC:

    pip install nupic

### Test

    # From the root of the repo:
    py.test tests/unit

### _Having problems?_

- You may need to use the `--user` flag for the commands above to install in a non-system location (depends on your environment). Alternatively, you can execute the `pip` commands with `sudo` (not recommended).
- You may need to add the `--use-wheel` option if you have an older pip version (wheels are now the default binary package format for pip).

For any other installation issues, please see our [search our forums](https://discourse.numenta.org/search?q=tag%3Ainstallation%20category%3A10) (post questions there). You can report bugs at https://github.com/numenta/nupic/issues.

Live Community Chat: [![Gitter](https://img.shields.io/badge/gitter-join_chat-blue.svg?style=flat)](https://gitter.im/numenta/public?utm_source=badge)

### Installing NuPIC From Source

To install from local source code, run from the repository root:

    pip install .

Use the optional `-e` argument for a developer install.

If you want to build the dependent `nupic.bindings` from source, you should build and install from [`nupic.core`](https://github.com/numenta/nupic.core) prior to installing nupic (since a PyPI release will be installed if `nupic.bindings` isn't yet installed).

- Build:
[![Build Status](https://travis-ci.org/numenta/nupic.png?branch=master)](https://travis-ci.org/numenta/nupic)
[![AppVeyor Status](https://ci.appveyor.com/api/projects/status/4toemh0qtr21mk6b/branch/master?svg=true)](https://ci.appveyor.com/project/numenta-ci/nupic/branch/master)
[![CircleCI](https://circleci.com/gh/numenta/nupic.svg?style=svg)](https://circleci.com/gh/numenta/nupic)
- To cite this codebase: [![DOI](https://zenodo.org/badge/19461/numenta/nupic.svg)](https://zenodo.org/badge/latestdoi/19461/numenta/nupic)
