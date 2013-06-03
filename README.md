Numenta Platform for Intelligent Computing (NuPIC)
=====

NuPIC is a library that provides the building blocks for online prediction systems.  The library contains the Cortical Learning Algorithm (CLA), but also the Online Prediction Framework (OPF) that allows clients to build prediction systems out of encoders, models, and metrics.

OPF Basics
----------

__Encoders__ turn raw values into sparse distributed representations (SDRs).  A good encoder will capture the semantics of the data type in the SDR using overlapping bits for semantically similar values.

__Models__ take sequences of SDRs and make predictions.  The CLA is implemented as an OPF model.

__Metrics__ take input values and predictions and output scalar representations of the quality of the predictions.  Different metrics are suitable for different problems.

__Clients__ take input data and feed it through encoders, models, and metrics and store or report the resulting predictions or metric results.

Installation
------------

NuPIC requires Python 2.6, GCC, and Make.

Add an environment variable that points to your installation directory and
update PATH and PYTHONPATH to reference install locations:

    export NTA=$HOME/nta/eng
    export PATH=$NTA/bin:$PATH
    export PYTHONPATH=$NTA/lib/python2.6/site-packages:$PYTHONPATH
    export NUPIC=/path/to/repo
    export NTA_ROOTDIR=$NTA
    # Convenience variable for temporary build files.
    export BUILDDIR=$HOME/ntabuild

Setup the OS dynamic library path to point to $NTA/lib. There are two
different paths to set: DYLD_LIBRARY_PATH on Mac and LD_LIBRARY_PATH on
Linux.

    LDIR="$NTA/lib"
    if [[ ! "$DYLD_LIBRARY_PATH" =~ "$LDIR" ]]; then
      export DYLD_LIBRARY_PATH=$LDIR:$DYLD_LIBRARY_PATH
    fi
    if [[ ! "$LD_LIBRARY_PATH" =~ "$LDIR" ]]; then
      export LD_LIBRARY_PATH=$LDIR:$LD_LIBRARY_PATH
    fi

Build and install NuPIC:

    pushd $NUPIC/build_system
    python setup.py --autogen
    mkdir $BUILDDIR
    cd $BUILDDIR
    $NUPIC/configure
    make install
    popd

NuPIC should now be installed in $NTA!

Try it out!
-----------
Run the C++ tests:

    $NTA/bin/htmtest
    $NTA/bin/testeverything

You can run the examples using the OpfRunExperiment OPF client:

    python $NUPIC/examples/opf/bin/OpfRunExperiment.py $NUPIC/examples/opf/experiments/multistep/hotgym/
