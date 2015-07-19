# Changelog

## 0.2.6

* Sets zip-safe to false to make sure relative capnp schema imports will work and importing .capnp files will work.
* Clean up capnp imports.
* Changes to TM test to accommodate changes in the default value of predictedSegmentDecrement
* Merge remote-tracking branch 'upstream/master'
* Change default value of predictedSegmentDecrement to be 0 to be backward compatible
* Change default value of predictedSegmentDecrement to be 0 to be backward compatible
* Change default value of predictedSegmentDecrement to be 0 to be backward compatible
* Merge remote-tracking branch 'upstream/master'
* Rename testconsoleprinter_output.txt so as to not be picked up by py.test as a test during discovery
* likelihood test: fix raw-value must be int
* Fix broken TPShim
* Revert "Fix TP Shim"
* Anomaly serialization verify complex anomaly instance
* Likelihood pickle serialization test
* MovingAverage pickle serialization test
* Fix TP Shim
* Removed stripUnlearnedColumns-from-SPRegion
* Updated comment describing activeArray paramater of stripUnlearnedColumns method in SP
* Revert "MovingAvera: remove unused pickle serialization method"
* Updated NUPIC_CORE_COMMITISH to use the core without stripNeverLearned
* Removed stripNeverLearned from SP.compute
* MovingAverage has getter for current value
* Fixes bug in mmGetCellActivityPlot
* Merge remote-tracking branch 'upstream/master'
* Fixes bug in mmGetCellActivityPlot
* Fixes bug in mmGetCellActivityPlot
* addressing scott's cr
* addressing cr; docstring formatting and minor
* Continuing work on 0.2.6.dev0.
* minor
* first version of knn tests
* Update SHA and fix files
* Rename cpp_region to py_region
* pylint
* fix likelihood equals problem when default timestamp
* Likelihood: @param docstring
* AnomalyLikelihood: add __str__
* ANomalyLikelihood equals test case
* Anomaly: add eq test
* add MovingAverage eq test
* anomaly likelihood, MA, Anomaly: review - better _eq_ statement
* Anomaly: code review - use instance access
* improving constructor docs
* AnomalyLikelihood: add _eq_
* Anomaly: compare likelihood in _eq_
* improve anomaly serialization test - use eq
* MovingAvera: remove unused pickle serialization method
* Anomaly & MovingAverage : change __cmp__ to __eq__
* define equals operator (__cmp__) for anomaly & MovingAverage
* anomaly serialize test - comment out parts
* Anomaly: add serialization test

## 0.2.5

* Fix MANIFEST.in capnp include.
* Update documentation related to PyRegion serialization introduction.
* Updates nupic.core and adds function definitions for read/write in PyRegion

## 0.2.4

* Fix a minor bug in the algorithm
* Implement orphan synapse decay
* register python regions in Region class method
* moved registration of python regions to nupic.core
* date encoder bug fix
* Implement orphan synapse decay
* changed default regions to tuples
* fill predictedActiveCells with 0
* removing irrelevant files
* removing old network api demo 2
* modified PyRegion to accept custom classes
* renamed unionMode to computePredictedActiveCellIndices
* set the output size for active indices and predicted+active indices to max possible size
* converting union pooler input to right format
* Port AnomalyRegion serialization
* Rename "enc" to "encoder"

## 0.2.3

* updated custom region methods and example to be static
* demo for custom regions
* Improve docstring for 'save' method and others.
* allows custom regions
* moved encoder changes to network_api_demo
* updated network_api_demo in new file to make swapping out encoders easier
* bit more explanation for MultiEncoder
* Use different logic for determining whether or not to translate back into actual values from bucket indices
* Switch over to C++ SpatialPooler where possible to speed up tests/build.
* Finish implementation of TemporalMemory serialization

## 0.2.2

* Fixed equality test for Connections class
* Removing learning radius parameter from nupic
* Add Cap'n Proto serialization to Python Connections
* Remove FDRCSpatial2.py
* Replace the use of FDRCSpatial2 to SpatialPooler
* SP profile implemented from tp_large
* TP profile: can use args from command-line, random data used
* Adds AnomalyRegion for computing the raw anomaly score. Updates the network api example to use the new anomaly region. Updates PyRegion to have better error messages.
* Remove FlatSpatialPooler
* Add delete segment/synapse functionality to Connections data structure
* Adding dependency listing with licenses.
* Bump pycapnp to latest (0.5.5) for security update
* Remove redundant encoderMap operations
* Remove redundant index, and EncoderDetails in favor of using the outer union directly
* Use union in capnp schema per feedback
* MultiEncoder capnp implementation, including a switch to relative imports as a workaround for an issue described in https://github.com/jparyani/pycapnp/issues/59
* SparsePassThroughEncoder capnp implementation
* PassThroughEncoder capnp implementation
* LogEncoder capnproto implementation
* GeospatialCoordinateEncoder capnp implementation
* DeltaEncoder capnp implementation
* CoordinateEncoder capnp implementation
* AdaptiveScalarEncoder capnp implementation
* SDRCategoryEncoder capnproto implementation
* CategoryEncoder capnproto serialization, fixes #1964
* Change anomaly score to always be zero when there are no active columns.
* Date encoder capnproto implementation
* RDSE capnproto implementation w/ bugfix in encoder base
* Remove redundant radius and resolution in favor of relying on them to be recalculated based on n.
* Remove explicit int casts and update tests to allow ints or longs.
* Integrate capnproto serialization into ScalarEncoder re: #1715
* Allowing relative paths for input files in swarm desc.
* accepts anomaly records as both lists and tuples

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
