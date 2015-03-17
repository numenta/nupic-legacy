# ![Numenta Logo](http://numenta.org/images/numenta-icon128.png) NuPIC

## Numenta Platform for Intelligent Computing

The Numenta Platform for Intelligent Computing (**NuPIC**) is a machine intelligence platform that implements the [HTM learning algorithms](http://numenta.com/learn/hierarchical-temporal-memory-white-paper.html). HTM is a detailed computational theory of the neocortex. At the core of HTM are time-based continuous learning algorithms that store and recall spatial and temporal patterns. NuPIC is suited to a variety of problems, particularly anomaly detection and prediction of streaming data sources.

For more information, see [numenta.org](http://numenta.org) or the [NuPIC wiki](https://github.com/numenta/nupic/wiki).

## Installing NuPIC 0.2.1

NuPIC binaries are available for:

- Linux x86 64b
- OS X 10.9
- OS X 10.10

#### Dependencies

- [Python 2.7 & development headers](https://docs.python.org/devguide/setup.html#build-dependencies)
- [pip](https://pypi.python.org/pypi/pip)
- [wheel](http://pythonwheels.com)
- [numpy](http://www.numpy.org/)

### Mac OS X

    pip install nupic

### Linux

> The Linux wheel file is hosted on AWS S3 instead of on the standard PyPi servers because [Linux wheels are not allowed to be uploaded to pypi](https://bitbucket.org/pypa/pypi-metadata-formats/issue/15/enhance-the-platform-tag-definition-for) yet.

    pip install https://s3-us-west-2.amazonaws.com/artifacts.numenta.org/numenta/nupic/releases/nupic-0.2.1-cp27-none-linux_x86_64.whl


### _Having problems?_

- You may need to use the `--user` flag for the commands above to install in a non-system location (depends on your environment). Alternatively, you can execute the `pip` commands with `sudo` (not recommended).
- You may need to add the `--use-wheel` option if you have an older pip version (wheels are now the default binary package format for pip).

For any other installation issues, please see our [FAQ](https://github.com/numenta/nupic/wiki/FAQ), email the [nupic-discuss](http://lists.numenta.org/mailman/listinfo/nupic_lists.numenta.org) mailing list, or chat with us on Gitter.

[![Gitter](https://img.shields.io/badge/gitter-join_chat-blue.svg?style=flat)](https://gitter.im/numenta/public?utm_source=badge)

### Building NuPIC From Source Code

For details about checking out this repository and building in your local environment, see the [Installing and Building NuPIC](https://github.com/numenta/nupic/wiki/Installing-and-Building-NuPIC) wiki page.

## How to Contribute:

 Please see the [Contributing to NuPIC](https://github.com/numenta/nupic/wiki/Contributing-to-NuPIC) wiki page.

 * Build: [![Build Status](https://travis-ci.org/numenta/nupic.png?branch=master)](https://travis-ci.org/numenta/nupic)
 * Unit Test Coverage: [![Coverage Status](https://coveralls.io/repos/numenta/nupic/badge.png?branch=master)](https://coveralls.io/r/numenta/nupic?branch=master)
 * [Regression Tests](https://github.com/numenta/nupic.regression): [![Build Status](https://travis-ci.org/numenta/nupic.regression.svg?branch=master)](https://travis-ci.org/numenta/nupic.regression)
