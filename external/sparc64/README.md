NuPIC external libraries
=============================

NuPIC depends on Swig, for creating python language bindings.  Swig is
normally distributed with the source, however, since Solaris is not an
officially supported platform, you will need to build the libraries yourself.
Use the following commands as a guide.

**BEFORE YOU BEGIN:** Obtain the source for Swig 1.3.36 and extract in
$NUPIC/external/sparc64

```
cd $NUPIC/external/sparc64/swig-1.3.36
gmake clean
CFLAGS="-m64 -fPIC" CXXFLAGS="-m64 -fPIC" LDFLAGS="-m64" ./configure --prefix=$NUPIC/external/sparc64
VERBOSE=1 gmake
gmake install
```
