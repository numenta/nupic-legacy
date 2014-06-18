# ![Numenta Logo](http://numenta.org/images/numenta-icon128.png) NuPIC

## Numenta Platform for Intelligent Computing 

[![Build Status](https://travis-ci.org/numenta/nupic.png?branch=master)](https://travis-ci.org/numenta/nupic) [![Coverage Status](https://coveralls.io/repos/numenta/nupic/badge.png?branch=master)](https://coveralls.io/r/numenta/nupic?branch=master)
 
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

## Build and test NuPIC:

NuPIC needs the following environment variables to build:

```
# `$NUPIC` is the path to your NuPIC repository.
# Remember to replace <NuPIC path> with the real path:
export NUPIC=<NuPIC path>

# `$NTA` is the installation path for NuPIC. 
export NTA=$NUPIC/build/release
```

NuPIC needs to be added to `$PYTHONPATH` to run and test:

```
# You may choose one of the following based on your version of Python:
# For Python 2.6:
export PYTHONPATH=$PYTHONPATH:$NTA/lib/python2.6/site-packages
# For Python 2.7:
export PYTHONPATH=$PYTHONPATH:$NTA/lib/python2.7/site-packages
```

Tips:

* You may set these environment variables in your dotfiles(e.g. `~/.bashrc` under Bash) to avoid repeated typing. 
* You may set a different path for `$NTA` or specify the location with CMake with the command line option `-DPROJECT_BUILD_RELEASE_DIR:STRING=/my/custom/path`.
* For more tips, please see [Development-Tips](https://github.com/numenta/nupic/wiki/Development-Tips)

### Using command line

#### Configure and generate build files:

    mkdir -p $NUPIC/build/scripts
    cd $NUPIC/build/scripts
    cmake $NUPIC

#### Build:

    cd $NUPIC/build/scripts
    make -j3

> **Note**: -j3 option specify '3' as the maximum number of parallel jobs/threads that Make will use during the build in order to gain speed. However, you can increase this number depending your CPU.

#### Run the tests:

    cd $NUPIC/build/scripts
    # all C++ tests
    make tests_everything
    # C++ HTM Network API tests
    make tests_cpphtm
    # Python HTM Network API tests
    make tests_pyhtm
    # Python OPF unit tests
    make tests_run
    # Python OPF unit and integration tests (requires mysql)
    make tests_run_all
    # Run all tests!
    make tests_all

### Using graphical interface

#### Generate the IDE solution:

 * Open CMake executable.
 * Specify the source folder (`$NUPIC`).
 * Specify the build system folder (`$NUPIC/build/scripts`), i.e. where IDE solution will be created.
 * Click `Generate`.
 * Choose the IDE that interest you (remember that IDE choice is limited to your OS, i.e. Visual Studio is available only on CMake for Windows).

#### Build:

 * Open `nupic.*proj` solution file generated on `$NUPIC/build/scripts`.
 * Run `ALL_BUILD` project from your IDE.

#### Run the tests:

 * Run any `tests_*` project from your IDE (check `output` panel to see the results).

### Examples

For examples, tutorials, and screencasts about using NuPIC, see the [Using NuPIC](https://github.com/numenta/nupic/wiki/Using-NuPIC) wiki page.

