# ![Numenta Logo](http://numenta.org/images/numenta-icon128.png) NuPIC

## Numenta Platform for Intelligent Computing 

* Build: [![Build Status](https://travis-ci.org/numenta/nupic.png?branch=master)](https://travis-ci.org/numenta/nupic)
* Unit Test Coverage: [![Coverage Status](https://coveralls.io/repos/numenta/nupic/badge.png?branch=master)](https://coveralls.io/r/numenta/nupic?branch=master)
* [Regression Tests](https://github.com/numenta/nupic.regression): [![Build Status](https://travis-ci.org/numenta/nupic.regression.svg?branch=master)](https://travis-ci.org/numenta/nupic.regression)
 
NuPIC is a library that provides the building blocks for online prediction and anomaly detection systems.  The library contains the [Cortical Learning Algorithm (CLA)](https://github.com/numenta/nupic/wiki/Cortical-Learning-Algorithm), but also the [Online Prediction Framework (OPF)] (https://github.com/numenta/nupic/wiki/Online-Prediction-Framework) that allows clients to build prediction systems out of encoders, models, and metrics.

For more information, see [numenta.org](http://numenta.org) or the [NuPIC wiki](https://github.com/numenta/nupic/wiki).

## Installation

For all installation options, see the [Installing and Building NuPIC](https://github.com/numenta/nupic/wiki/Installing-and-Building-NuPIC) wiki page.

Currently supported platforms:
 * Linux (32/64bit)
 * Mac OSX
 * Raspberry Pi (ARMv6)
 * Chromebook (Ubuntu ARM, Crouton) (ARMv7)
 * [VM images](https://github.com/numenta/nupic/wiki/Running-Nupic-in-a-Virtual-Machine)

Dependencies:
 * Python (2.6-2.7) (with development headers)
 * GCC (4.6-4.8), or Clang
 * Make or any IDE supported by CMake (Visual Studio, Eclipse, XCode, KDevelop, etc)

The dependencies are included in platform-specific repositories for convenience:

* [nupic-linux64](https://github.com/numenta/nupic-linux64) for 64-bit Linux systems
* [nupic-darwin64](https://github.com/numenta/nupic-darwin64) for 64-bit OS X systems

Complete set of python requirements are documented in [requirements.txt](/external/common/requirements.txt),
compatible with [pip](http://www.pip-installer.org/en/latest/cookbook.html#requirements-files):

    pip install -r external/common/requirements.txt

_Note_: If using pip 1.5 or later:

    pip install --allow-all-external --allow-unverified PIL --allow-unverified psutil -r external/common/requirements.txt

_Note_: If you get a "permission denied" error when using pip, you may add the --user flag to install to a location in your home directory, which should resolve any permissions issues. Doing this, you may need to add this location to your PATH and PYTHONPATH. Alternatively, you can run pip with 'sudo'.

## User instructions

If you want NuPIC only for your apps use it, cd into the NuPIC installation directory and run:

    python setup.py install

Do to a current [bug](https://github.com/numenta/nupic/issues/1122), you must also add the following environment variable. You can do this by updating your `.bashrc` or `.bash_profile` with the following line:

    export NTA_DATA_PATH=$NUPIC/resources

> This assumes the `NUPIC` environment variable is set to the directory where the NuPIC source code exists.

_Note_: If you get a "permission denied" error when using this, you may add the --user flag to install to a location in your home directory, which should resolve any permissions issues. Doing this, you may need to add this location to your PATH and PYTHONPATH. Alternatively, you can run this with 'sudo'.

Once it is installed, you can import NuPIC library to your python script using:

    import nupic

For examples, tutorials, and screencasts about using NuPIC, see the [Using NuPIC](https://github.com/numenta/nupic/wiki/Using-NuPIC) wiki page.

## Developer instructions

If you want develop, debug, or simply test NuPIC, clone it and follow the instructions:

### Using command line

> This assumes the `NUPIC` environment variable is set to the directory where the NuPIC source code exists.

    cd $NUPIC
    python setup.py build
    python setup.py develop

#### To run the tests:

    cd $NUPIC/build/scripts
    # all C++ unit tests
    make cpp_unit_tests
    # C++ HTM Network API tests
    make tests_cpphtm
    # Python HTM Network API tests
    make tests_pyhtm
    # Python OPF unit tests
    make python_unit_tests
    # Python OPF integration tests (requires mysql)
    make python_integration_tests
    # Run all tests!
    make tests_all

### Using an IDE

See our [Development Tips](https://github.com/numenta/nupic/wiki/Development-Tips) wiki page for details.

#### To run the tests:

 * Run any [test](#run-the-tests) project from your IDE (check `output` panel to see the results).

For more tips, please see [Development-Tips](https://github.com/numenta/nupic/wiki/Development-Tips)
