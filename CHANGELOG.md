# Changelog

## 0.2.1

* Moved data pkg_resource data into nupic/datafiles.
* Replaces datasethelpers with pkg_resources.
* refactor submetrics computation handling None
* Adding numpy to README requirements.
* Move pattern/sequence machine tests to proper location.
* Moves pattern_machine and sequence_machine files into generators module.
* Get cell indices methods added an amazing super cool docstring formatting
* Updates data generator tool filename and adds executable bit.
* Moves anomalyzer to nupic.data.generators module
* Move data generators to nupic.data.generators module
* fixme burn-in for multi metric addInstance()
* fix AggregateMetric with None metricSpec
* add MetricMulti class
* AggregateMetric sets id from params (if specified)
* Removes isDelta method from encoder base class.
* fixed predicted active cells in tm-mm
* rename --enable-optimizations to --optimizations-native
* add --optimizations-lto option to setup.py to enable Link Time Optimizations
* Simplify docker setup to single Dockerfile at root
* Adding cell activity plt and improving metrics table
* add python setup.py --enable-optimization
* enable -Wextra warnings
* sane optimization defaults for binary published builds
* Revert "default make with -j4"
* add Ofast linker flag for gcc
* fix: remove inline - let LTO decide

## 0.2.0

* Code changes required for a Windows build.
* Updates nupic.core to d233c58b64e8064d4d12684634dc5e5e78c7ce0b.
* Implements capnp serialization for Python spatial pooler. Also implements temporary hack for putting .capnp files into the source tree since the build seems to be set up to install in-tree.

## 0.1.3

* Remove unnecessary build flag and fix a bug that was causing duplicated definition names.
* Added warning in README for OS X.
* Doc updates
* Include additional libs in common libs
* Use gcc in default docker configuration to match nupic.core binary release. Increase resources in coreos configuration.
* Fixed ValueError When coordinate encoder is used with DateEncoder
* Add library path for capnp libraries to linker.
* Adds capnp libraries to linker args.
* Adds interface file for converting from pycapnp schema to compiled in schema and uses it with SWIGed C++ SpatialPooler class's read and write methods.
* Discard NTA_PLATFORM_* in favor of NTA_OS_* and NTA_ARCH_* macro variables
* Raises exception when enableInference was not called, or when predicted field missing from input row.

## 0.1.2

* Add archflags env var before deploy command on OSX

## 0.1.1

* Removal of CMakeLists.txt
* Removes fake C extension from setup.
* Adds warning on darwin platform when ARCHFLAGS not set.
* Cleanup re: #1579.  Fixup namespace conflicts with builtins (file, dir, etc.) as well as minor alignment issues
* Switch from cmake to distutils extensions for nupic installation

## 0.1.0

* Cleaned up README and CHANGELOG for 0.1 release.

## 0.0.38

* SWIG optimizations.
* Script to deploy linux wheel to S3 on release.
* Publishing select artifacts to pypi on release.
* Changed dev version pattern to match what python wants.
* Cleaned up setup and manifest for proper sdists.
* Faking extensions to get platform-specific wheels.
* Added core capnp files to bindings.
* GCE now encodes altitude using a 3D coordinate system.
* Distributing `*.i` files from `nupic.bindings` in binary packages.
* Updates test entry points to pure python. README instructions for running tests were updated.
* Missing configuration files are no longer ignored. A runtime exception is raised immediately when an expected configuration file is not found. 
* Updated deployment logic to account for both deployment scenarios (iterative and release).
* Configured pypi deployment on all branches with tags.
* Added pypi deployment configuration for binary releases.
* Parsing python requirements in setuptools so they are included within published packages (working toward releases).
* Setting up python wheels packaging and upload to S3 for future distribution.
* Implemented logic for reusing segments, to enforce a fixed-size connectivity (nupic.core).
