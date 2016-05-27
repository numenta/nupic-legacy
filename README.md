# ![Numenta Logo](http://numenta.org/images/numenta-icon128.png) NuPIC

## Numenta Platform for Intelligent Computing

The Numenta Platform for Intelligent Computing (**NuPIC**) is a machine intelligence platform that implements the [HTM learning algorithms](http://numenta.com/learn/hierarchical-temporal-memory-white-paper.html). HTM is a detailed computational theory of the neocortex. At the core of HTM are time-based continuous learning algorithms that store and recall spatial and temporal patterns. NuPIC is suited to a variety of problems, particularly anomaly detection and prediction of streaming data sources.

For more information, see [numenta.org](http://numenta.org) or the [NuPIC wiki](https://github.com/numenta/nupic/wiki).

## Installing NuPIC 0.5.3

NuPIC binaries are available for:

- Linux x86 64bit
- OS X 10.9
- OS X 10.10
- Windows 64bit

#### Dependencies

The following dependencies are required to install NuPIC on all operating systems.

- [Python 2.7 & development headers](https://docs.python.org/devguide/setup.html#build-dependencies)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [wheel](http://pythonwheels.com)
- [numpy](http://www.numpy.org/)
- C++ 11 compiler like [gcc](https://gcc.gnu.org/) (4.8+) or [clang](http://clang.llvm.org/)

### Install OS X

First, you must install [Xcode command line tools](https://developer.apple.com/library/ios/technotes/tn2339/_index.html), which will get you a C++ compiler.

    pip install nupic

### Install Linux

> **NOTE**: The `nupic.bindings` binary distribution is not stored on [PyPi](https://pypi.python.org/pypi/nupic) along with the OS X distribution. NuPIC uses the [wheel](http://pythonwheels.com) binary format, and PyPi does not support hosting Linux wheel files. So we are forced to host our own.

    pip install https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic.core/releases/nupic.bindings/nupic.bindings-0.4.3-cp27-none-linux_x86_64.whl
    pip install nupic

### Install Windows

    pip install nupic

For problems installing NuPIC, please see our [Installation and Build Wiki](https://github.com/numenta/nupic/wiki/Installing-and-Building-NuPIC).

### Test

    # From the root of the repo:
    py.test tests/unit

### _Having problems?_

- You may need to use the `--user` flag for the commands above to install in a non-system location (depends on your environment). Alternatively, you can execute the `pip` commands with `sudo` (not recommended).
- You may need to add the `--use-wheel` option if you have an older pip version (wheels are now the default binary package format for pip).

For any other installation issues, please see our [FAQ](https://github.com/numenta/nupic/wiki/FAQ), email the [nupic-discuss](http://lists.numenta.org/mailman/listinfo/nupic_lists.numenta.org) mailing list, or chat with us on Gitter.

[![Gitter](https://img.shields.io/badge/gitter-join_chat-blue.svg?style=flat)](https://gitter.im/numenta/public?utm_source=badge)

### Building NuPIC From Source Code

For details about checking out this repository and building in your local environment, see the [Installing and Building NuPIC](https://github.com/numenta/nupic/wiki/Installing-and-Building-NuPIC) wiki page.

## How to Contribute:

 Please see the [Contributing to NuPIC](https://github.com/numenta/nupic/wiki/Contributing-to-NuPIC) wiki page.

 * Build: 
[![Build Status](https://travis-ci.org/numenta/nupic.png?branch=master)](https://travis-ci.org/numenta/nupic)
[![AppVeyor Status](https://ci.appveyor.com/api/projects/status/4toemh0qtr21mk6b/branch/master?svg=true)](https://ci.appveyor.com/project/numenta-ci/nupic/branch/master)
 * Unit Test Coverage: [![Coverage Status](https://coveralls.io/repos/numenta/nupic/badge.png?branch=master)](https://coveralls.io/r/numenta/nupic?branch=master)
 * [Regression Tests](https://github.com/numenta/nupic.regression): [![Build Status](https://travis-ci.org/numenta/nupic.regression.svg?branch=master)](https://travis-ci.org/numenta/nupic.regression)
 * To cite this codebase: [![DOI](https://zenodo.org/badge/19461/numenta/nupic.svg)](https://zenodo.org/badge/latestdoi/19461/numenta/nupic)
