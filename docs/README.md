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
  def run(self, inputRecord):
    """
    Run one iteration of this model.

    :param inputRecord: (object)
           A record object formatted according to
           :meth:`~nupic.data.record_stream.RecordStreamIface.getNextRecord` or
           :meth:`~nupic.data.record_stream.RecordStreamIface.getNextRecordDict`
           result format.
    :returns: (:class:`~nupic.frameworks.opf.opf_utils.ModelResult`)
             An ModelResult namedtuple. The contents of ModelResult.inferences
             depends on the the specific inference type of this model, which
             can be queried by :meth:`.getInferenceType`.
    """
```

If the function parameter type is discernable, enter it in parenthesis after the `:param x:` declaration. There must be two newlines between the function description any `:param:` / `:returns`.

### Linking code

Most commonly, you will want to link to modules, classes, or functions:

```rst
:mod:`full.namespace`
:class:`full.namespace.ClassName`
:meth:`full.namespace.ClassName.methodName`
```

If you don't want the full namespace to each thing displayed, use `~`:

```rst
:mod:`~full.namespace`
:class:`~full.namespace.ClassName`
:meth:`~full.namespace.ClassName.methodName`
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
│   ├── knn_classifier.py [OK]
│   ├── backtracking_tm.py [OK]
│   ├── backtracking_tm_cpp.py [OK]
│   ├── connections.py [OK]
│   ├── fdrutilities.py [DEFER]
│   ├── monitor_mixin [DEFER]
│   ├── spatial_pooler.py [OK]
│   └── temporal_memory.py [OK]
├── data [OK]
├── encoders [OK]
├── frameworks
│   ├── opf
│   │   ├── htm_prediction_model.py [OK]
│   │   ├── client.py [OK]
│   │   ├── common_models
│   │   │   └── cluster_params.py [OK]
│   │   ├── exceptions.py [OK]
│   │   ├── exp_description_api.py [OK]
│   │   │   └── ExperimentDescriptionAPI [OK]
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
│   │   ├── prediction_metrics_manager.py [OK]
│   │   ├── previous_value_model.py [OK]
│   │   └── two_gram_model.py [OK]
│   └── viz
│       ├── __init__.py [OK]
│       ├── dot_renderer.py [OK]
│       ├── graphviz_renderer.py [OK]
│       ├── network_visualization.py [OK]
│       └── networkx_renderer.py [OK]
├── math [OK]
├── regions
│   ├── anomaly_likelihood_region.py [OK]
│   ├── anomaly_region.py [OK]
│   ├── knn_anomaly_classifier_region.py [OK]
│   ├── knn_classifier_region.py [OK]
│   ├── pluggable_encoder_sensor.py [OK]
│   ├── record_sensor.py [OK]
│   ├── sdr_classifier_region.py [OK]
│   ├── sp_region.py [OK]
│   └── tm_region.py [OK]
├── serializable.py [OK]
├── support [OK]
└── swarming [DEFER]

```
