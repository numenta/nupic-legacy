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

## How to Document Code

We are using [reStructuredText](http://docutils.sourceforge.net/docs/user/rst/quickref.html) and [Sphinx](http://www.sphinx-doc.org/en/stable/) to build docs. Here is an example of a properly formatted function docstring:

```python
def compute(self, recordNum, patternNZ, classification, learn, infer):
  """
  Process one input sample.

  This method is called by outer loop code outside the nupic-engine. We
  use this instead of the nupic engine compute() because our inputs and
  outputs aren't fixed size vectors of reals.


  :param recordNum: Record number of this input pattern. Record numbers
    normally increase sequentially by 1 each time unless there are missing
    records in the dataset. Knowing this information insures that we don't get
    confused by missing records.

  :param patternNZ: List of the active indices from the output below. When the
    input is from TemporalMemory, this list should be the indices of the
    active cells.

  :param classification: Dict of the classification information where:

    - bucketIdx: index of the encoder bucket
    - actValue: actual value going into the encoder

    Classification could be None for inference mode.
  :param learn: (bool) if true, learn this sample
  :param infer: (bool) if true, perform inference

  :return:    Dict containing inference results, there is one entry for each
              step in self.steps, where the key is the number of steps, and
              the value is an array containing the relative likelihood for
              each bucketIdx starting from bucketIdx 0.

              There is also an entry containing the average actual value to
              use for each bucket. The key is 'actualValues'.

              for example:

              .. code-block:: python

                 {1 :             [0.1, 0.3, 0.2, 0.7],
                   4 :             [0.2, 0.4, 0.3, 0.5],
                   'actualValues': [1.5, 3,5, 5,5, 7.6],
                 }
  """

```

See the codebase that has been documented (denoted below) for examples of completely documented code.

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
│   ├── sdr_classifier_factory.py [OK]
│   ├── backtracking_tm.py [TODO]
│   ├── backtracking_tm_cpp.py [TODO]
│   ├── tm_shim.py [TODO]
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
│   └── temporal_memory_shim.py [TODO]
├── data
│   ├── fieldmeta.py [OK]
│   ├── file_record_stream.py [OK]
│   ├── inference_shifter.py [OK]
│   ├── record_stream.py [OK]
│   ├── stream_reader.py [OK]
│   └── utils.py [OK]
├── encoders
│   ├── adaptivescalar.py [OK]
│   ├── base.py [OK]
│   ├── category.py [OK]
│   ├── coordinate.py [OK]
│   ├── date.py [OK]
│   ├── delta.py [OK]
│   ├── geospatial_coordinate.py [OK]
│   ├── logenc.py [OK]
│   ├── multi.py [OK]
│   ├── pass_through_encoder.py [OK]
│   ├── random_distributed_scalar.py [OK]
│   ├── scalar.py [OK]
│   ├── scalarspace.py [OK]
│   ├── sdrcategory.py [OK]
│   └── sparse_pass_through_encoder.py [OK]
├── frameworks
│   ├── opf
│   │   ├── htm_prediction_model.py [OK]
│   │   ├── client.py [TODO]
│   │   ├── common_models
│   │   │   └── cluster_params.py [TODO]
│   │   ├── exceptions.py [TODO]
│   │   ├── exp_description_api.py [TODO]
│   │   ├── exp_description_helpers.py [TODO]
│   │   ├── experiment_runner.py [TODO]
│   │   ├── metrics.py [TODO]
│   │   ├── model.py [OK]
│   │   ├── model_factory.py [OK]
│   │   ├── opf_basic_environment.py [TODO]
│   │   ├── opf_environment.py [TODO]
│   │   ├── opf_helpers.py [TODO]
│   │   ├── opf_task_driver.py [TODO]
│   │   ├── opf_utils.py [TODO]
│   │   │   ├── ModelResults [OK]
│   │   │   └── SensorInput [OK]
│   │   ├── periodic.py [TODO]
│   │   ├── prediction_metrics_manager.py [TODO]
│   │   ├── previous_value_model.py [OK]
│   │   ├── safe_interpreter.py [TODO]
│   │   └── two_gram_model.py [OK]
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
│   ├── TMRegion.py [TODO]
│   ├── TestRegion.py [TODO]
│   └─── UnimportableNode.py [TODO]
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
│   └── mysqlhelpers.py [TODO]
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
