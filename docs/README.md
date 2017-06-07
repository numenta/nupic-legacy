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
│   ├── backtracking_tm.py [OK]
│   ├── backtracking_tm_cpp.py [OK]
│   ├── connections.py [OK]
│   ├── fdrutilities.py [DEFER]
│   ├── monitor_mixin [DEFER]
│   ├── spatial_pooler.py [OK]
│   └── temporal_memory.py [OK]
├── data
│   ├── fieldmeta.py [OK]
│   ├── file_record_stream.py [OK]
│   ├── inference_shifter.py [OK]
│   ├── record_stream.py [OK]
│   ├── stream_reader.py [OK]
│   └── utils.py [OK]
├── encoders
│   ├── adaptive_scalar.py [OK]
│   ├── base.py [OK]
│   ├── category.py [OK]
│   ├── coordinate.py [OK]
│   ├── date.py [OK]
│   ├── delta.py [OK]
│   ├── geospatial_coordinate.py [OK]
│   ├── logarithm.py [OK]
│   ├── multi.py [OK]
│   ├── pass_through.py [OK]
│   ├── random_distributed_scalar.py [OK]
│   ├── scalar.py [OK]
│   ├── scalarspace.py [OK]
│   ├── sdr_category.py [OK]
│   └── sparse_pass_through.py [OK]
├── frameworks
│   ├── opf
│   │   ├── htm_prediction_model.py [OK]
│   │   ├── client.py [OK]
│   │   ├── common_models
│   │   │   └── cluster_params.py [OK]
│   │   ├── exceptions.py [OK]
│   │   ├── exp_description_api.py [OK]
│   │   │   └── ExperimentDescriptionAPI [TODO]
│   │   ├── experiment_runner.py [OK]
│   │   ├── metrics.py [OK]
│   │   ├── model.py [OK]
│   │   ├── model_factory.py [OK]
│   │   ├── opf_basic_environment.py [OK]
│   │   ├── opf_environment.py [OK]
│   │   ├── opf_helpers.py [OK]
│   │   ├── opf_task_driver.py [OK]
│   │   ├── opf_utils.py [OK]
│   │   │   ├── ModelResults [OK]
│   │   │   └── SensorInput [OK]
│   │   ├── periodic.py [DEFER]
│   │   ├── prediction_metrics_manager.py [TODO]
│   │   ├── previous_value_model.py [OK]
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
│   ├── anomaly_likelihood_region.py [OK]
│   ├── anomaly_region.py [OK]
│   ├── cla_classifier_region.py [TODO]
│   ├── knn_anomaly_classifier_region.py [TODO]
│   ├── knn_classifier_region.py [TODO]
│   ├── pluggable_encoder_sensor.py [TODO]
│   ├── record_sensor.py [TODO]
│   ├── record_sensor_filters
│   │   ├── add_noise.py [TODO]
│   │   └── modify_fields.py [TODO]
│   ├── sdr_classifier_region.py [TODO]
│   ├── sp_region.py [TODO]
│   ├── svm_classifier_node.py [TODO]
│   ├── spec.py [TODO]
│   ├── tm_region.py [TODO]
│   ├── test_region.py [TODO]
│   └─── unimportable_node.py [TODO]
├── serializable.py [TODO]
├── simple_server.py [TODO]
├── support
│   ├── __init__ [OK]
│   ├── configuration.py [OK]
│   ├── configuration_base.py [OK]
│   ├── configuration_custom.py [OK]
│   ├── console_printer.py [OK]
│   ├── exceptions.py [OK]
│   ├── fs_helpers.py [OK]
│   ├── group_by.py [OK]
│   ├── lock_attributes.py [OK]
│   └── pymysql_helpers.py [TODO]
├── swarming [DEFER]
└── utils.py [TODO]

```
