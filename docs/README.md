# Code documentation

## Usage
* Install `nupic` in dev mode: `python setup.py develop --user`
* Install dev dependencies: `pip install -r requirements-dev.txt --user`
* Build the docs by running: `make html`
* Or instead, to build the docs and watch for changes in the code and `.rst` files, run:
```
sphinx-autobuild  ${NUPIC}/docs/source  ${NUPIC}/docs/_build_html  \
    --watch ${NUPIC}/src  --poll  --open-browser
```

## Documentation status
List of NuPIC packages and their documentation status:
* `TODO`: Package doc needs to be reviewed and potentially converted to RST
* `OK`: Package RST doc reviewed and approved.
* `DEFER`: Would be nice to document, but not necessary for 1.0

```
nupic
├── algorithms
│   ├── KNNClassifier.py [OK]
│   ├── anomaly.py [OK]
│   ├── anomaly_likelihood.py [OK]
│   ├── sdr_classifier.py [OK]
│   └── sdr_classifier_factory.py [OK]
├── data
│   ├── aggregator.py [DEFER]
│   ├── dictutils.py [DEFER]
│   ├── fieldmeta.py [OK]
│   ├── file_record_stream.py [TODO]
│   ├── filters.py [TODO]
│   ├── functionsource.py [TODO]
│   ├── generators
│   │   ├── anomalyzer.py [TODO]
│   │   ├── data_generator.py [TODO]
│   │   ├── distributions.py [TODO]
│   │   ├── pattern_machine.py [TODO]
│   │   └── sequence_machine.py [TODO]
│   ├── inference_shifter.py [TODO]
│   ├── joiner.py [TODO]
│   ├── jsonhelpers.py [TODO]
│   ├── record_stream.py [TODO]
│   ├── sorter.py [TODO]
│   ├── stats.py [TODO]
│   ├── stats_v2.py [TODO]
│   ├── stream_reader.py [TODO]
│   └── utils.py [TODO]
├── database
│   ├── ClientJobsDAO.py [TODO]
│   └── Connection.py [TODO]
├── datafiles
│   ├── extra
│   │   ├── firstOrder
│   │   │   └── raw
│   │   │       └── makeDataset.py [TODO]
│   │   ├── generated
│   │   │   ├── GenerateSampleData.py [TODO]
│   │   ├── gym
│   │   │   └── raw
│   │   │       └── makeDataset.py [TODO]
│   │   ├── hotgym
│   │   │   └── raw
│   │   │       └── makeDataset.py [TODO]
│   │   ├── regression
│   │   │   └── makeDataset.py [TODO]
│   │   ├── secondOrder
│   │   │   └── makeDataset.py [TODO]
├── encoders
│   ├── adaptivescalar.py [TODO]
│   ├── base.py [TODO]
│   ├── category.py [TODO]
│   ├── coordinate.py [TODO]
│   ├── date.py [TODO]
│   ├── delta.py [TODO]
│   ├── geospatial_coordinate.py [TODO]
│   ├── logenc.py [TODO]
│   ├── multi.py [TODO]
│   ├── pass_through_encoder.py [TODO]
│   ├── random_distributed_scalar.py [TODO]
│   ├── scalar.py [TODO]
│   ├── scalarspace.py [TODO]
│   ├── sdrcategory.py [TODO]
│   ├── sparse_pass_through_encoder.py [TODO]
│   └── utils.py [TODO]
├── frameworks
│   ├── opf
│   │   ├── clamodel.py [TODO]
│   │   ├── clamodel_classifier_helper.py [TODO]
│   │   ├── clamodelcallbacks.py [TODO]
│   │   ├── client.py [TODO]
│   │   ├── common_models
│   │   │   └── cluster_params.py [TODO]
│   │   ├── exceptions.py [TODO]
│   │   ├── exp_description_api.py [TODO]
│   │   ├── exp_description_helpers.py [TODO]
│   │   ├── experiment_runner.py [TODO]
│   │   ├── jsonschema
│   │   ├── metrics.py [TODO]
│   │   ├── model.py [TODO]
│   │   ├── modelcallbacks.py [TODO]
│   │   ├── modelfactory.py [TODO]
│   │   ├── opfbasicenvironment.py [TODO]
│   │   ├── opfenvironment.py [TODO]
│   │   ├── opfhelpers.py [TODO]
│   │   ├── opftaskdriver.py [TODO]
│   │   ├── opfutils.py [TODO]
│   │   ├── periodic.py [TODO]
│   │   ├── predictionmetricsmanager.py [TODO]
│   │   ├── previousvaluemodel.py [TODO]
│   │   ├── safe_interpreter.py [TODO]
│   │   └── two_gram_model.py [TODO]
│   └── viz
│       ├── dot_renderer.py [TODO]
│       ├── examples
│       │   └── visualize_network.py [TODO]
│       ├── graphviz_renderer.py [TODO]
│       ├── network_visualization.py [TODO]
│       └── networkx_renderer.py [TODO]
├── math
│   ├── cross.py [TODO]
│   ├── dist.py [TODO]
│   ├── logarithms.py [TODO]
│   ├── mvn.py [TODO]
│   ├── proposal.py [TODO]
│   ├── roc_utils.py [TODO]
│   ├── stats.py [TODO]
│   └── topology.py [TODO]
├── regions
│   ├── AnomalyLikelihoodRegion.py [TODO]
│   ├── AnomalyRegion.py [TODO]
│   ├── CLAClassifierRegion.py [TODO]
│   ├── KNNAnomalyClassifierRegion.py [TODO]
│   ├── KNNClassifierRegion.py [TODO]
│   ├── PluggableEncoderSensor.py [TODO]
│   ├── RecordSensor.py [TODO]
│   ├── RecordSensorFilters
│   │   ├── AddNoise.py [TODO]
│   │   └── ModifyFields.py [TODO]
│   ├── SDRClassifierRegion.py [TODO]
│   ├── SPRegion.py [TODO]
│   ├── SVMClassifierNode.py [TODO]
│   ├── Spec.py [TODO]
│   ├── TPRegion.py [TODO]
│   ├── TestRegion.py [TODO]
│   └─── UnimportableNode.py [TODO]
├── research
│   ├── TP.py [TODO]
│   ├── TP10X2.py [TODO]
│   ├── TP_shim.py [TODO]
│   ├── connections.py [TODO]
│   ├── fdrutilities.py [TODO]
│   ├── monitor_mixin
│   │   ├── metric.py [TODO]
│   │   ├── monitor_mixin_base.py [TODO]
│   │   ├── plot.py [TODO]
│   │   ├── temporal_memory_monitor_mixin.py [TODO]
│   │   └── trace.py [TODO]
│   ├── spatial_pooler.py [OK]
│   ├── temporal_memory.py [TODO]
│   ├── temporal_memory_shim.py [TODO]
│   └── utils.py [TODO]
├── serializable.py [TODO]
├── simple_server.py [TODO]
├── support
│   ├── configuration.py [TODO]
│   ├── configuration_base.py [TODO]
│   ├── configuration_custom.py [TODO]
│   ├── consoleprinter.py [TODO]
│   ├── datafiles.py [TODO]
│   ├── decorators.py [TODO]
│   ├── enum.py [TODO]
│   ├── exceptions.py [TODO]
│   ├── feature_groups.py [TODO]
│   ├── features.py [TODO]
│   ├── features_list.py [TODO]
│   ├── fshelpers.py [TODO]
│   ├── group_by.py [TODO]
│   ├── lockattributes.py [TODO]
│   ├── log_utils.py [TODO]
│   ├── loophelpers.py [TODO]
│   ├──.py [TODO]mysqlhelpers.py [TODO]
│   └── unittesthelpers
│       ├── abstract_temporal_memory_test.py [TODO]
│       ├── algorithm_test_helpers.py [TODO]
│       ├── test_framework_helpers.py [TODO]
│       └── testcasebase.py [TODO]
├── swarming
│   ├── DummyModelRunner.py [TODO]
│   ├── HypersearchV2.py [TODO]
│   ├── HypersearchWorker.py [TODO]
│   ├── ModelRunner.py [TODO]
│   ├── api.py [TODO]
│   ├── exp_generator
│   │   └── ExpGenerator.py [TODO]
│   ├── experimentutils.py [TODO]
│   ├── hypersearch
│   │   ├── ExtendedLogger.py [TODO]
│   │   ├── HsState.py [TODO]
│   │   ├── ModelTerminator.py [TODO]
│   │   ├── Particle.py [TODO]
│   │   ├── SwarmTerminator.py [TODO]
│   │   ├── errorcodes.py [TODO]
│   │   ├── object_json.py [TODO]
│   │   ├── permutation_helpers.py [TODO]
│   │   ├── regression.py [TODO]
│   │   └── support.py [TODO]
│   ├── jsonschema
│   ├── modelchooser.py [TODO]
│   ├── permutationhelpers.py [TODO]
│   ├── permutations_runner.py [TODO]
│   └── utils.py [TODO]
└── utils.py [TODO]

```
