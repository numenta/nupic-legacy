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

*__Encoders__* turn raw values into sparse distributed representations (SDRs).  A good encoder will capture the semantics of the data type in the SDR using overlapping bits for semantically similar values.

*__Models__* take sequences of SDRs and make predictions.  The CLA is implemented as an OPF model.

*__Metrics__* take input values and predictions and output scalar representations of the quality of the predictions.  Different metrics are suitable for different problems.

*__Clients__* take input data and feed it through encoders, models, and metrics and store or report the resulting predictions or metric results.

## Installation

For all installation options, see the [Getting Started](https://github.com/numenta/nupic/wiki/Getting-Started) wiki page.

#### Currently supported platforms:

 * Linux (32/64bit)
 * Mac OSX
 * Raspberry Pi (ARMv6)
 * Chromebook (Ubuntu ARM, Crouton) (ARMv7)  
 * [VM images](https://github.com/numenta/nupic/wiki/Running-Nupic-in-a-Virtual-Machine)

#### Dependencies:

 * Python (2.6-2.7) (with development headers)
 * GCC (4.6-4.8), or Clang
 * Make or any IDE supported by CMake (Visual Studio, Eclipse, XCode, KDevelop, etc)

The dependencies are included in platform-specific repositories for convenience:

* [nupic-linux64](https://github.com/numenta/nupic-linux64) for 64-bit Linux systems
* [nupic-darwin64](https://github.com/numenta/nupic-darwin64) for 64-bit OS X systems

Complete set of python requirements are documented in [requirements.txt](/external/common/requirements.txt),
compatible with [pip](http://www.pip-installer.org/en/latest/cookbook.html#requirements-files):

    pip install -r external/common/requirements.txt

## Build and test NuPIC:

Important notes:
 * $REPOSITORY is the current location of the repository that you downloaded from GitHub. Usually its name is "nupic-master".
 * After CMake generation, two useful environment variables will be created:
   * $NUPIC which references $REPOSITORY/source (ie directory with all source code)
   * $NTA which references $REPOSITORY/release (ie directory with all executables and libraries generated from build process). In case of this variable already is set on your system, $REPOSITORY/release creation will be discarded, and $NTA will be re-used.

### Using command line

#### Configure and generate build files:

    cd $REPOSITORY/build_system
    cmake $REPOSITORY/source

#### Build:

    cd $REPOSITORY/build_system
    make -j3
    
Note: -j3 option specify '3' as the maximum number of parallel jobs/threads that Make will can use during build in order to gain speed. However you can increase this number depending your CPU.

#### Run the C++ tests:

    cd $NTA/bin
    htmtest
    testeverything

### Using graphical interface

#### Generate the IDE solution:

 * Open CMake executable.
 * Specify the source folder ($REPOSITORY/source).
 * Specify the build system folder ($REPOSITORY/build_system), ie where IDE solution will be created.
 * Click 'Generate'.
 * Choose the IDE that interest you (remember that IDE choice is limited to your OS, ie Visual Studio is available only on CMake for Windows).

#### Build:

 * Open 'Nupic.*proj' solution file generated on $REPOSITORY/build_system.
 * Run 'ALL_BUILD' project from your IDE.

#### Run the C++ tests:

 * Run 'HtmTest' and 'TestEverything' projects from your IDE (check 'output' panel to see the results).

### Run the Python unit tests:

    cd $NTA/bin
    run_tests.sh

### Examples

You can run the examples using the OpfRunExperiment OPF client:

    python $NUPIC/examples/opf/bin/OpfRunExperiment.py $NUPIC/examples/opf/experiments/multistep/hotgym/

There are also some sample OPF clients. You can modify these to run your own
data sets. One example is the hotgym prediction client:

    python $NUPIC/examples/opf/clients/hotgym/hotgym.py

Also check out other uses of the CLA on the [Getting Started](https://github.com/numenta/nupic/wiki/Getting-Started#next-steps) wiki page. 
