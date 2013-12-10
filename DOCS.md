# Documentation

See online docs, built off head of the `master` branch, [here](http://numenta.org/docs/).

## Building Docs Yourself

### Requirements

- [doxypy](http://code.foosel.org/doxypy)
  - must exist at `/usr/local/bin/doxypy.py`, which is where the Doxygen config expects it to exist.
- [Doxygen](www.doxygen.org)

### Usage

    $> cd $NUPIC
    $> doxygen

HTML documentation is generated in `$NUPIC/html`.
