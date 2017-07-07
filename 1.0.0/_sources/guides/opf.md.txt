# OPF Guide

Online Prediction Framework (OPF) is a framework for working with and deriving predictions from online learning algorithms, including HTM. OPF is designed to work in conjunction with a larger architecture, as well as in a standalone mode (i.e. directly from the command line). It is also designed such that new model algorithms and functionalities can be added with minimal code changes.

## Examples

Here are some examples of applications using the OPF interface:

- [`examples/opf/clients/cpu`](https://github.com/numenta/nupic/tree/master/examples/opf/clients/cpu)
- [`examples/opf/clients/hotgym/prediction/one_gym`](https://github.com/numenta/nupic/tree/master/examples/opf/clients/hotgym/prediction/one_gym)
- [`examples/opf/clients/hotgym/anomaly`](https://github.com/numenta/nupic/tree/master/examples/opf/clients/hotgym/anomaly)
- [`examples/opf/clients/hotgym/anomaly/one_gym`](https://github.com/numenta/nupic/tree/master/examples/opf/clients/hotgym/anomaly/one_gym)

## OPF in a nutshell

[__Encoders__](../api/algorithms/encoders.html) turn raw values into sparse distributed representations (SDRs).  A good encoder will capture the semantics of the data type in the SDR using overlapping bits for semantically similar values.

[__Models__](../api/opf/models.html) take sequences of SDRs and make predictions.  The CLA is implemented as an OPF model.

[__Metrics__](../api/opf/metrics.html) take input values and predictions and output scalar representations of the quality of the predictions.  Different metrics are suitable for different problems.

[__Clients__](../api/opf/clients.html) take input data and feed it through encoders, models, and metrics and store or report the resulting predictions or metric results.

## What does the OPF do?

The OPF has three main responsibilities:

1. Provide an interface/implementations for models
1. Compute metrics on the output of models
1. Provide an interface to write model output to a permanent store (csv file or some form
of database)

Each of these 3 components is in a separate set of modules. Metrics and writing output are optional when running models.

![Data flow in the OPF](../_static/opf-figure1.png)

> Figure 1: Data flow in the OPF

## What doesn’t the OPF do?

- The OPF does not create models. It is up to the client code to figure out how many models to run, and to instantiate the correct types of models.
- The OPF does not run models automatically. All the models in the OPF operate under a “push” model. The client is responsible for getting records from some data source, feeding records into the model, and handling the output of models.

## Models

### The Model Interface

The OPF defines the abstract "Model" interface for the implementation of any online learning model. Implementers typically subclass the [base class](../api/opf/models.html#nupic.frameworks.opf.model.Model) provided. All models must implement the following methods:

-   **[`__init__(inferenceType)`](../api/opf/models.html#nupic.frameworks.opf.model.Model)**

    Constructor for the model. Must take an [`InferenceType`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.InferenceType) value (see below). *A model’s ``__init__()`` method should always call the `__init__()` method of the superclass.*

-   **[`run(inputRecord)`](../api/opf/models.html#nupic.frameworks.opf.model.Model.run)**

    The main function for the model that does all the computation required for a new input record. Because the OPF only deals with online streaming models, each record is fed to the model one at a time. Returns: A populated ModelResult object (see below)

-   **[`getFieldInfo()`](../api/opf/models.html#nupic.frameworks.opf.model.Model.getFieldInfo)**

    Returns a list of metadata about each of the translated fields (see below about translation). Each entry in the list is a FieldMetaInfo object, which contains information about the field, such as name and data type
Returns: A list of FieldMetaInfo objects

-   **[`finishLearning()`](../api/opf/models.html#nupic.frameworks.opf.model.Model.finishLearning)**

    This is a signal from the client code that the model may be placed in a permanent "finished learning" mode where it will not be able to learn from subsequent input records. This allows the model to perform optimizations and clean up any learning-related state Returns: Nothing

-   **[`resetSequenceStates()`](../api/opf/models.html#nupic.frameworks.opf.model.Model.resetSequenceStates)**

    Signals the model that a logical sequence has finished. The model should not treat the subsequent input record as subsequent to the previous record.
Returns: Nothing

-   **[`getRuntimeStats()`](../api/opf/models.html#nupic.frameworks.opf.model.Model.getRuntimeStats)** – [can be a no-op]

    Get runtime statistics specific to this model. Examples include “number of records seen” or “average cell overlap”

    Returns: A dictionary where the keys are the statistic names, and the values are the
    statistic values

-   **`_getLogger()`** – [used by parent class]

    Returns: The logging object for this class. This is used so that that the operations in the superclass use the same logger object.

It also provides the following functionality, common to all models:

-   **[`enableLearning()`](../api/opf/models.html#nupic.frameworks.opf.model.Model.enableLearning) / [`disableLearning()`](../api/opf/models.html#nupic.frameworks.opf.model.Model.disableLearning)**

    Set’s the learning flag for the model. This can be queried internally and externally using the isLearningEnabled() method

-   **[`enableInference(inferenceArgs=None)`](../api/opf/models.html#nupic.frameworks.opf.model.Model.enableInference) / [`disableInference()`](../api/opf/models.html#nupic.frameworks.opf.model.Model.disableInference)**

    Enables/Disables inference output for this model. Enabling inference takes an optional argument inferenceArgs, which is a dictionary with extra parameters that affect how inference is performed. For instance, an anomaly detection model may have a boolean parameter “doPrediction”, which toggles whether or not a prediction is computed in addition to the anomaly score.

    The inference state of a model can be queried internally and externally using the isInferenceEnabled() method. The inference arguments can be queried using the getInferenceArgs() method.

-   **[`save(saveModelDir)`](../api/opf/models.html#nupic.frameworks.opf.model.Model.saveModelDir)**

    Save the model state via pickle and saves the resulting object in the saveModelDir directory.

-   **`_serializeExtraData(extaDataDir)` / `_deSerializeExtraData(extraDataDir)`**

    If there is state that cannot be pickled and needs to be saved separately, this can be done by overriding these methods (implemented as no-ops by default).

### Model Input

![Records are input to models in the form of dictionary-like objects, where the keys are field names and the values are the raw field values.](../_static/opf-figure2.png)

> Figure 2: Records are input to models in the form of dictionary-like objects, where the keys are field names and the values are the raw field values.

#### Translation
Certain field types need to be converted into primitive input types. For example, datetime types are converted to 2 integer values, timeOfDay and dayOfWeek. In the OPF, this process is called **translation**. Generally, all models will have a translation step. Conceptually, translation produces two parallel lists (for performance reasons): A list of field metadata, and a list of translated field values. In practice, the first list is constant, so it can be pre-computed and stored in the model. This is the return value of **getFieldInfo()**.

#### Encoding
Additionally, for some model types (such as the CLA model), the translated inputs are quantized (put into buckets) and converted into binary vector representation. This process is called **_encoding_** and is handled by [encoders](Encoders) (specific encoders for different data types exist). Most models may not need to encode the input (or, more likely, they will just need to quantize the input).

### Model Output: The [`ModelResult`](../api/opf/results.html#nupic.frameworks.opf.opf_utils.ModelResult) Object

The [`ModelResult`](../api/opf/results.html#nupic.frameworks.opf.opf_utils.ModelResult) object is the main data container in the OPF. When a record is fed to a model, it instantiates a new [`ModelResult`](../api/opf/results.html#nupic.frameworks.opf.opf_utils.ModelResult) instance, which contains model input and inferences, and is shuttled around to the various OPF modules. Below is a description of each of the ModelResult attributes. They default to **None** when the ModelResult is instantiated, and must be populated by the Model object.

- **rawInput**: This is the exact record that is fed into the model. It is a dictionary-like object where the keys are the input field names, and the values are input values of the fields. All the input values maintain their original types.
- **sensorInput**: The translated input record, as well as auxiliary information about the input (See below)
- **inferences**: A dictionary that contains the output of a model (i.e. its inference). The keys are InferenceElement values (described below), and the values are the corresponding inference values
- **metrics**: A dictionary where the keys are the unique metric labels, and the values are the metric values (a single float). This is the only element that is not populated by the model object, but by the surrounding code.

#### Raw Input vs. Sensor Input

As explained above, fields from the raw input are translated into primitive input types. There also may be additional information about the input record that is needed by the OPF framework. The [`SensorInput`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.SensorInput) object is a container that stores translated input record, as well
as auxiliary information about the input. More attributes may be added to the SensorInput object as new features require them. Note: not every model needs to populate every field in [`SensorInput`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.SensorInput), and the exact requirements depend on which inferences and metrics are being computed.

- **sequenceReset**: Control field for temporal patterns. This field has a value of 1 if an explicit temporal reset was specified for this record, 0 otherwise. Resets are currently not being used.
- **dataRow**: The translated version of the input row.
- **dataEncodings**: The encoded version of the input, used by some metrics. This is a list of
binary numpy arrays, one for each field in dataRow.
- **category**: In classification problems, this is the class label for the input record.

### Inference Elements

The concept of [`InferenceElement`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.InferenceElement)s is a key part of the OPF. A model's inference may have multiple parts to it. For example, a model may output both a prediction and an anomaly score. Models output their set of inferences as a dictionary that is keyed by the enumerated type [`InferenceElement`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.InferenceElement). Each entry in an inference dictionary is considered a separate inference element, and is handled independently by the OPF.

Data structures related to inference elements are located in [*Inference Utilities*](../api/opf/utils.html#inference-utilities).

#### Inference Data Types

For reasons unknown and poorly explained, the OPF handles different data types for inferences differently. This helps with the automation of handling new inference types, but can be confusing.

#### Mapping Inferences to Input Values

In order to compute metrics and write output, the OPF needs to know which input values (i.e. attributes of [`SensorInput`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.SensorInput)) correspond to each inference element. This mapping between inputs and outputs are defined in [`InferenceElement`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.InferenceElement)`.__inferenceInputMap`. By specifying this mapping here, the same logic can be used both for writing to output and computing metrics

￼￼Below is an example.

    class InferenceElement(...):

    ...

        _inferenceInputMap = {
            "prediction": "dataRow",
            "encodings": "dataEncodings",
            "classification": "category",
            "multiStepPredictions": "dataRow"
        }

> Snippet 1: Mapping inferences to input

In this example, we can see that the “_prediction_” inference element is associated with [`SensorInput`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.SensorInput)`.dataRow`, and the “_classification_” inference element is associated with [`SensorInput`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.SensorInput)`.category`.

This association is used to compute metrics and to determine which parts of the input to write to output. For example, to compute error, the value of “_prediction_” will be compared to the value of [`SensorInput`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.SensorInput)`.dataRow`, and the value of “_classification_” will be compared to value of [`SensorInput`](../api/opf/utils.html#nupic.frameworks.opf.opf_utils.SensorInput)`.category`.

![Inference elements](../_static/opf-figure3.png)

> Figure 3: Inference Elements

When a new inference element is added, an entry needs to be added in this map to connect it with input.

For example, if we add a new inferenceElement InferenceElement.foo, which corresponds to dataRow (i.e. the groundTruth value for foo will be contained in dataRow), you will need to add an entry:

    {InferenceElement.foo : "dataRow"}

#### Shifting Inferences

Because OPF Models make predictions about the future, the OPF needs to line up inferences with their respective ground truth values so that it can compute metrics and write results appropriately. For example, InferenceElement.prediction is a prediction about the next record. In order to compute error metrics, this inference needs to be shifted one record forward in time to be compared with its corresponding ground-truth record.

    def getTemporalDelay(inferenceElement, key=None):

      if inferenceElement in (InferenceElement.prediction,
                              InferenceElement.encodings):
        return 1

      if inferenceElement in (InferenceElement.anomalyScore,
                              InferenceElement.classification,
                              InferenceElement.classConfidences):
        return 0

      if inferenceElement in (InferenceElement.multiStepPredictions,
                              InferenceElement.multiStepBestPredictions):
        return int(key)

      return 0

> Snippet 2: The getTemporalDelay() method defines how inferences are shifted

The **InferenceElement** class defines the **getTemporalDelay()** method, which specifies how much a given inference element needs to be shifted in time. For dictionaries, an optional key argument is supplied, each entry in the dictionary can be shifted by a different amount.

This shifting applies to both csv output and metrics calculation. Each inference element in a ModelResult is shifted independently of the other inference elements, so you can have inferences about multiple points in the future all contained in a single ModelResult.

Below is an example of how this shifting occurs to compute errors:

![Shifting](../_static/opf-figure4.png)

> Figure 4: Shifting

You can use the [`InferenceShifter`](../api/opf/results.html#inferenceshifter) to shift inferences:

```python
from nupic.data.inference_shifter import InferenceShifter as shifter

shiftedModelResult = shifter.shift(modelResult)
```

## [Metrics](../api/opf/metrics.html)

The 2nd responsibility of the OPF is to compute metrics on a model's output. Typically, this is some form of error metric, but in truth it can be any kind of score computed from the information in the input record and the output inferences. Metric calculations are handled by the [Prediction Metric Manager](../api/opf/metrics.html#module-nupic.frameworks.opf.prediction_metrics_manager), which is instantiated with a series of [`MetricSpec`](../api/opf/metrics.html#nupic.frameworks.opf.metrics.MetricSpec) objects (see below). The [`MetricsManager`](../api/opf/metrics.html#nupic.frameworks.opf.prediction_metrics_manager.MetricsManager) also handles shifting all the inferences appropriately before they are fed into their respective metrics modules

### Metric Specs

A metric calculation is specified by creating a [`MetricSpec`](../api/opf/metrics.html#nupic.frameworks.opf.metrics.MetricSpec) object. This is a container object that contains 4 fields:

- `inferenceElement`
- `metric`
- `field` (optional)
- `params` (optional)

Here is an example MetricSpec:

```python
MetricSpec(  inferenceElement=InferenceElement.multiStepBest,
             metric="aae",
             field="foo",
             params = {"window" : 200 } )
```

This means that we are calculating the average absolute error ("aae") on the `multiStepBest` inference element, for the entry that corresponds to the field `foo`, and with an optional parameter `window` set to 200.

### Metric Labels

Metrics need to be able to be uniquely identified, so that the experiment can indicate which metric should be optimized and which should be written to output. To this end, metric specs can return a "metric label", which is a "human readable" (barely) string that contains all the information to uniquely identify the metric. The metric label for the above metric spec would be:

    multiStepBest:aae:window=200:field=foo

### Metrics Calculation Modules

The modules that actually calculate metrics are located in [*Available Metrics*](../api/opf/metrics.html#available-metrics). They all inherit the abstract base class [`MetricsIface`](../api/opf/metrics.html#nupic.frameworks.opf.metrics.MetricsIface), and they must define the following methods.

- **[`addInstance(prediction, groundTruth, record)`](../api/opf/metrics.html#nupic.frameworks.opf.metrics.MetricsIface.addInstance)**: This is the method where a new inference-groundTruth pair is passed to the metric. Additionally, the raw input record is
also passed to the metric calculator. The module is responsible for calculating the metric
and storing the relevant information here.
- **[`getMetric()`](../api/opf/metrics.html#nupic.frameworks.opf.metrics.MetricsIface.getMetric)**
    - Returns a dictionary with the metric value and any auxillary information. The
metric's value is stored under the key 'value' (confusing, right?)
        - Ex. `{ 'value': 10.3, 'numIterations': 1003}`

## Output

Types: Different inference value types are handled differently. The OPF distinguishes between 3 types: lists, dicts, and other. Lists are assumed to be associated with the model's [`getFieldInfo`](../api/opf/models.html#nupic.frameworks.opf.model.Model.getFieldInfo) output. An individual element is always output as a string, no matter it's actual type. Dicts are the most general, and separate columns are created for each key. Each entry in a dictionary is output as a string, no matter its type.
