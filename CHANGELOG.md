# Changelog

## 0.5.6

* Since manylinux nupic.bindings wheel 0.4.10 has now been released to PyPi, we no longer need to install nupic.bindings from S3.
* fix logic in _getColumnNeighborhood
* Bugfix in flatIdx reuse after a segment is destroyed
* Change private _burstColumn class method signature to accept a cellsForColumn argument in lieu of a cellsPerColumn argument.  Move the calculation that otherwise depends on cellsPerColumn into the instance method.
* TM: Support extensibility by using traditional methods
* Update expected error for topology changes
* Update expected hotgym result for topology changes
* Adds RELEASE.md with documentation for releasing NuPIC.
* Match nupic.core's SP neighborhood ordering.
* Update inhibition comments and docstrings.
* Introduce mechanism by which already-installed pre-release versions of nupic.bindings are ignored during installation
* Assign self.connections value from self.connectionsFactory() rather than direct usage of Connections constructor. Allows better extensibility should the user want to change some aspect of the creation of the connections instance in a subclass
* Removed obsolete directory src/nupic/bindings/
* Remove the notion of "destroyed" Segments / Synapses
* Enable proper subclassing by converting staticmethods that referenced `TemporalMemory` to classmethods that reference their class.
* Fixup TemporalMemory.write() to handle columnDimensions as tuples.
* Initialize columnDimensions as a tuple in test to reflect common convention.  This forces the TemporalMemoryTest.testWriteRead test to fail in its current state.
* Store "numActivePotentialSynapses". No more "SegmentOverlap".
* Add a lot more scenarios to the TM perf benchmark
* Moved audiostream example to htm-community
* Safer "addToWinners" value. Play nicely with surgical boosting.
* Bugfix: With no stimulus threshold, still break ties when overlaps=0
* Clean up trailing whitespace and tabs
* Properly apply the stimulus threshold
* Add test for new "learn on predicted segments" behavior
* Split compute into activateCells and activateDendrites
* Grow synapses in predicted columns, not just bursting columns
* Removed bundled get-pip.py and instead fetch version copy from S3
* Removed .nupic_modules and now rely on versioned release of nupic.bindings on PyPI
* averagingWindow size updated to improve HTM scores for RES-296
* Build system updates for Bamboo (Linux), Travis (OS X), and AppVeyor (Windows)
* Added nyc taxi example for anomaly detection

## 0.5.5

* Renamed a misclassed class name from ConnectionsTest to GroupByTest
* not _ is => is not and fixes groupby comment and passes integration tests
* overhaul to groupby, now 10% faster than current implementation
* NUP-2299 Install specific versions of pip, setuptools, and wheel.
* NUP-2299 Added platform-conditional dependency on pycapnp==0.5.8 using PEP-508.
* lazy group_by and changes to GroupByGenerator
* perf improvement to segment comparison in compute activity
* 100 % increase in spped
* small perf changes
* demonstrate that compatability test works with predictedSegmentDec not 0.0
* fixes subtle bug in numSegments that caused integration tests to fail
* fixes bug where minIdx could be passed as a float rather than an int
* skip serialization test if capnp is not installed
* lints and updates comments in group_by.py and group_by_tests.py
* gets same results as c++ temporal memory after group_by changes
* ports group_by tests and they pass
* adds groupByN utility function for use in TM
* all connections tests written and passing, moved some stuff around and added missing function to connections
* started porting new connections tests and minor changes to connections.py
* improves permanence >= testing in computeActivity
* confirmed python implementation is same as cpp version. Needs better perf now
* adds back AnomalyRegion and Anomaly class in anomaly.py and related tests
* fixes bug in growSynapses, almost exactly the same
* Updated core SHA and default SDR classifier implementation
* Updated SDRClassifier factory and region to handle cpp
* changed input name from value to metricValue
* updates variables names in anomaly_likelihood.py and AnomalyLikelihoodRegion
* adds new connections methods
* create new methods for creating/destroying synapses/segments
* continues change of connections datastructures
* move raw anomaly calculation back to nupic.algorithms.anomaly
* Finished swarming/hypersearch separation
* Moved base hypersearch classes to hypersearch
* Moved experimentutils to nupic.swarming
* Updated SDR classifier internals
* calculate raw anomly score in KNNAnomalyClassifier
* removes anomaly.py dependency in network_api_demo.py
* changes how TPRegion computes prevPredictdColumns and updates clamodel
* Install pip from local copy, other simplifications
* Fixup PYTHONPATH to properly include previously-defined PYTHONPATH
* adds pseudocode to core functions
* continues implementation of AnomalyLikelihoodRegion
* Limit tests to unit after ovverriding pytest args on cli
* DEVOPS-85 OS X build infrastructure for Bamboo CI environment
* replaces segmentCMP with lambda and updates docstrings
* uses arrays instead of dicts in computeActivity
* Corrections to examples in tm_high_order.py
* incorporates binary search into the algorithm where applicable
* remove outdated nab unit tests
* use Q function
* Corrections to examples in tm_high_order.py
* change to column generator
* Added tm_high_order.py to show examples of the temporal memory.
* Fixed conversion bug in SDRClassifier serialization
* Fixed patternNZ proto writing.
* Slight fix for pattern history handling in sdr classifier
* Small fix on SDR classifier
* Better fix for #3172, using the initialize() function and checking if _sdrClassifier is set
* Updated learning rate for SDR classifier + slight changes to the error ranges in OPF test
* Updated hotgym test with actual value and implemented first fix for OPF test
* Updated tests and examples with SDR classifier
* Finished updating examples with SDR classifier.
* Updated hotgym and general anomaly examples with SDR classifier.
* Updates pycapnp to 0.5.8
* test_db-fixes avoids printing user password in plaintext
* test_db-fixes updates database and table name
* Corrections made to the spatial pooler tutorial.
* changes maxBoost default value to 1.0
* fixes connection tests and prints config file used in test_db.py
* Moved back overlap accesors test for spatial_pooler from API tests to unit tests.
* Added tutorial script for the spatial pooler. Modified README file accordingly.
* Moved the unit test for SP overlap accesors to API tests.

## 0.5.4

* Added overlap accessors to spatial_pooler.py plus unit tests. (Code style corrected)
* Updated VERSION in Spatial Pooler and added backward compatibility in setstate()
* Added members overlaps and boostedOverlaps to SpatialPooler class.
* Addition of overlaps and boostedOverlaps members to SpatialPooler class plus unit tests.
* Added docs for return type in RDSE internal func.
* tm_cpp with tuned parameters
* RES-215 Changes to add params for new TM subclass for NAB
* Remove main function from SDRClassifierRegion
* remove unused methods from SDRClassifierRegion
* Add simple end-to-end integration test for SDRClassifierRegion
* use string split instead of eval to parse strings
* correct inconsistent error msg in sdr_classifier_factory.py
* Fix readWrite test of SDR classifier
* Add SDRClassifier Region to pyRegions
* Initial implementation of SDRClassifier Region
* implement SDR classifier factory
* Add capnp proto for SDR classifier region
* Add default value for SDR classifier implementation in nupic-default.xml

## 0.5.3

* Default DATETIME columns to NULL in ClientJobsDAO for compatibility across mysql versions. As of mysql 5.7.8, values of 0 are not allowed for DATETIME columns, and CURRENT_TIMESTAMP is semantically inappropriate for those columns.
* Suppress this optional dependency on matplotlib without logging, because python logging implicitly adds the StreamHandler to root logger when calling `logging.debug`, etc., which may undermine an application's logging configuration
* Bugfix: Write the 'actualValues' to the output, don't reassign the output
* Fixed Username Regex in ClientJobsDAO
* cleaned up region a bit to make it compliant with numenta's coding guidelines.

## 0.5.2

* Fixe to GCE to return the right number of scalars when altitude is missing.

## 0.5.1

* Improves SDR classifier and tests
* Modify the continuous online learning test
* Add 3 tests on multiple item prediction
* Fix test_pFormatArray
* Implement SDR classifier in NuPIC
* Make the 'arrayTypes' list more informative
* Add getParameter/setParameter support for Bool and BoolArray
* Improved anomaly params (from NAB)
* Added minSparsity option
* Get the encoder's outputWidth via parameter
* Use nupic.core encoders from nupic via the Network API
* Fix bugs and inconsistencies in the custom region demo
* Adds BINDINGS_VERSION envvar to wheel filename (for iterative builds)

## 0.5.0

* Removes references to FastTemporalMemory.
* Lower TM epsilon threshold for compatibility.
* Add documentation for the Monitor Mixins
* Removed FastTemporalMemory from nupic
* Update temporal memory compatibility test to use C++ TM.
* Sort segments before iterating for compatibility with C++
* Sort unpredictedActiveColumns before iterating for compatibility with C++

## 0.4.5

* This release is just to sync with nupic.bindings 0.3.1.

## 0.4.4

* Botched release (sorry!)

## 0.4.3

* Updating to proper core sha

## 0.4.2

* Using official release version of bindings for nupic release.

## 0.4.1

* Manualy update of nupic.bindings dev version after botched release attempt

## 0.4.0

* Updated hello_tm.py to use accessors
* Updated TP_shim.py to use accessors Updated `columnForCell` and `_validateCell` in FastTemporalMemory to conform to their docstrings, which is needed for the change to TP_shim.py
* Updated temporal memory monitor mixin to use accessors
* Updated temporal_memory_test.py to use accessor methods.
* Added accessors to temporal_memory.py
* Change temporalImp to tm_py for both networks and add comment about it being a temporary value until C++ TM is implemented
* Refactored to remove common code between network_checkpoint_test.py and temporal_memory_compatibility_test.py
* Use named constants from nupic.data.fieldmeta in aggregator module instead of naked constants.
* Fix AttributeError: 'TPShim' object has no attribute 'topDownCompute'
* Support more parameters in TPShim
* Serialize remaining fields in CLAModel using capnproto
* Enforce pyproj==1.9.3 in requirements.txt
* Use FastCLAClassifier read class method instead of instance method
* Have CLAClassifierFactory.read take just the proto object
* Add capnp serialization to CLAClassifierRegion
* Add capnp serialization to SPRegion

## 0.3.6

* Windows support
* Serialization work
* Moved SWIG out into nupic.core
* Major build changes

## 0.3.5

* Raise explicit exception if user passes non-str path
* SP: simplify local inhibition
* SP: adapt tests, sort winning columns output
* SP: simplify active columns assignment
* SP: simplify global inhibition
* file Rename as hello_tm.py and modifications in comments

## 0.3.4

* Added src/nupic/frameworks/opf/common_models/cluster_params.py and supporting files from numenta-apps htmengine. A separate numenta-apps PR will remove this code from htmengine.
* fixes #2592
* fix for #2265
* fix for bug #2265
* Fixup Dockerfile to install nupic.bindings, and other cleanup
* Adding C++ compiler requirement to README.
* Fix for test failure
* Fixed stream definition reference error.
* Reduce default reestimation period.
* Remove greedy reestimation of distribution
* Pointing README to proper bindings version.
* Continuing work on 0.3.4.dev0.
* removing a test that depends on nupic.vision
* PCA_Node test: some fixes, WIP
* formatting
* test for PCANode region
* remove Pillow from requirements.txt as it was used for vision only
* fix merge mistake in csv file
* move test from PCANode to nupic.vision unittest

## 0.3.3

* Include additional file types in MANIFEST.in, consistent with setup.py
* Pattern and Sequence machines using nupic::Random
* Wrap sparse matrix implementations with cortical column-centric semantics as a way to abstract away the underlying implementation
* Re-enable testHotgymRegression

## 0.3.2

* Update to nupic.bindings version with fix for platform differences
* Rename nupic directory to src/nupic
* Updated S3 URL to nupic.bindings for Linux install
* Fix paths for data files in an integration test
* Fix issue with storing temporary file in wrong location in integration test

## 0.3.1

* Specify nupic.bindings version to match commit sha (0.2).
* Use logging.debug for emitting the message about not being able to import matplotlib; we log it at debug level to avoid polluting the logs of apps and services that don't care about plotting.
* Add Dockerfile ready to perform swarming.
* Removes PCANode
* Updated Linux binary install instructions.

## 0.3.0

* Updated comment about greedy stats refresh when likelihood > 0.99

## 0.2.12

* Implemented unit tests for the new features in AnomalyLikelihood class.
* Convert AnomalyLikelihood._historicalScores to a user-configurable sliding window, instead of accumulating all of the incoming data points. This improved performance a ton! Added AnomalyLikelihood.forceModelRefresh() method.
* Update nupic.core to include backwards compatibility fix for RandomImpl.
* Uninstall pycapnp to avoid running tests that utilize the functionality and currently fail with Duplicate ID error.
* Makes pycapnp and corresponding serialization optional. If pycapnp is not installed then the corresponding serialization tests will be skipped.
* Add Multiple Prediction Test for NegLL Metric
* Add test for NegLL Error Metric
* Fix Orphan Decay Bug in temporal memory test
* Change decreasing overlaps test for coordinate encoder to not require a strict decrease (staying the same is ok).
* Allow specifying MonitoredTemporalMemory as TM implementation through OPF
* include bucket likelihood and classifier input in clamodel
* update metrics managers to pass model results to metrics
* introducting a computeFlag to prevent double-computation. * The flag is used to prevent double computation in the event that customCompute() is called at the same time as compute()
* Added `numRecords` param for consitency with the newly added `infer` method in FastCLACLassifier
* checking if classifier has a `maxCategoryCount` attribute. If not, set it to solve backward compatibilities issues
* renaming numCategories to maxCategoryCount to be constistent between KNN and CLA classifier
* made new experimentutils file containing InferenceElement, InferenceType, and ModelResult duplicates which we will want to change in the future

## 0.2.11

* Updating nupic.core sha.
* Updated location of NuPIC Linux wheel on S3.

## 0.2.10

* Updating bindings version.

## 0.2.9

* Added pip install command for linux bindings.
* Change term predictedColumns to predictedActiveColumns in the TemporalMemory

## 0.2.8

* Updated to correct pypi license string.

## 0.2.7

* Changed all copyright headers on all files to AGPL.
* split up pip wheel to multiple commands
* Fixed fast_temporal_memory cellsForColumn calculation. Column is an int (specifically a numpy.int64 and getCellIndex would fail in this), not a cell
* Broke out model record encoding functionality from RecordStreamIface into ModelRecordEncoder class.
* Convert nupic to namespace
* updated include statements in swig files
* added dict utils to hypersearch specific utils file and modified dependencies accordingly
* Updated to AGPL.
* Remove tweepy.
* KNNClassifier input multiple categories, and integration test
* enable multiple categories in Network API
* Makes nupic a namespace package that other projects can extend.
* Added NRMSE metric
* Allow Connections to be serialized.
* Added ability to unregister python regions and updated core sha
* Remove unused synapses in Temporal Memory
* Fix: TemporalMemory.getCellIndex doesn't work correctly when running through OPF

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
