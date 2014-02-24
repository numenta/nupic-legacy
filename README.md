<div align="center">
    <img title="Numenta Logo" src="http://numenta.org/images/250x250numentaicon.gif"/>
</div>

# Numenta Platform for Intelligent Computing (NuPIC)

[![Build Status](https://travis-ci.org/numenta/nupic.png?branch=master)](https://travis-ci.org/numenta/nupic)

NuPIC is a library that provides the building blocks for online prediction systems.  The library contains the Cortical Learning Algorithm (CLA), but also the Online Prediction Framework (OPF) that allows clients to build prediction systems out of encoders, models, and metrics.

For more information, see [numenta.org](http://numenta.org) or the [Github wiki](https://github.com/numenta/nupic/wiki).

Issue tracker at [issues.numenta.org](https://issues.numenta.org/browse/NPC).

## OPF Basics

For more detailed documentation, see the [OPF wiki page](https://github.com/numenta/nupic/wiki/Online-Prediction-Framework).

__Encoders__ turn raw values into sparse distributed representations (SDRs).  A good encoder will capture the semantics of the data type in the SDR using overlapping bits for semantically similar values.

__Models__ take sequences of SDRs and make predictions.  The CLA is implemented as an OPF model.

__Metrics__ take input values and predictions and output scalar representations of the quality of the predictions.  Different metrics are suitable for different problems.

__Clients__ take input data and feed it through encoders, models, and metrics and store or report the resulting predictions or metric results.

## Installation

For all installation options, see the [Getting Started](https://github.com/numenta/nupic/wiki/Getting-Started) wiki page.

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

Important notes:
 * $REPOSITORY is the current location of the repository that you downloaded from GitHub.
 * After CMake generation, two useful environment variables will be created:
   * $NUPIC, which is the same as $REPOSITORY
   * $NTA, which references $HOME/nta/eng (the directory with all executables and libraries generated from build process). If this variable is already set, the $REPOSITORY/release will not be created, and $NTA will be used as the release directory.

### Using command line

#### Configure and generate build files:

    cd $REPOSITORY/build_system
    cmake $REPOSITORY

#### Build:

    cd $REPOSITORY/build_system
    make -j3
    
> **Note**: -j3 option specify '3' as the maximum number of parallel jobs/threads that Make will use during the build in order to gain speed. However, you can increase this number depending your CPU.

#### Run the C++ tests:

    cd $NTA/bin
    htmtest
    testeverything

### Using graphical interface

#### Generate the IDE solution:

 * Open CMake executable.
 * Specify the source folder ($REPOSITORY).
 * Specify the build system folder ($REPOSITORY/build_system), ie where IDE solution will be created.
 * Click 'Generate'.
 * Choose the IDE that interest you (remember that IDE choice is limited to your OS, ie Visual Studio is available only on CMake for Windows).

#### Build:

 * Open 'Nupic.*proj' solution file generated on $REPOSITORY/build_system.
 * Run 'ALL_BUILD' project from your IDE.

#### Run the C++ tests:

 * Run 'HtmTest' and 'TestEverything' projects from your IDE (check 'output' panel to see the results).

### Run the Python unit tests:

    cd $NUPIC
    $NUPIC/run_tests.sh

### Examples

You can run the examples using the OpfRunExperiment OPF client:

    python $NUPIC/examples/opf/bin/OpfRunExperiment.py $NUPIC/examples/opf/experiments/multistep/hotgym/

There are also some sample OPF clients. You can modify these to run your own
data sets. One example is the hotgym prediction client:

    python $NUPIC/examples/opf/clients/hotgym/hotgym.py

Also check out other uses of the CLA on the [Getting Started](https://github.com/numenta/nupic/wiki/Getting-Started#next-steps) wiki page.
