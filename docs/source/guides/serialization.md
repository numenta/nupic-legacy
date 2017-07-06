# Serialization

NuPIC uses Cap'n Proto and the Python library pycapnp for serialization. See the [pycapnp documentation](http://jparyani.github.io/pycapnp/) for more details on the Python API. The NuPIC algorithms expose this serialization through the following methods:

- [`writeToFile`](../api/support/index.html#nupic.serializable.Serializable.writeToFile) - write the instance to the specified file instance (not the path)
- [`readFromFile`](../api/support/index.html#nupic.serializable.Serializable.readFromFile) - class method that returns a new instance using the state saved to the specified file instance (not the path)
- [`write`](../api/support/index.html#nupic.serializable.Serializable.write) - write the instance to the specified pycapnp builder
- [`read`](../api/support/index.html#nupic.serializable.Serializable.read) - class method that returns a new instance using the state saved to the specified pycapnp reader

## Writing to Files

The typical serialization use case is writing to a file. Here is an example for creating a SpatialPooler instance, writing it to a file, and reading it back into a new instance of SpatialPooler:

```python
from nupic.algorithms.spatial_pooler import SpatialPooler

sp1 = SpatialPooler(inputDimensions=(10,), columnDimensions=(10,))
with open("out.tmp", "wb") as f:
  sp1.writeToFile(f)

with open("out.tmp", "rb") as f:
  sp2 = SpatialPooler.readFromFile(f)

print sp1.getColumnDimensions(), sp2.getColumnDimensions()
```

## Writing Directly to Cap'n Proto Messages

Sometimes you may want to write to a stream or other output source. In this case, you can write to a pycapnp builder and use the pycapnp library to write the builder to the appropriate stream. See the [pycapnp documentation](http://jparyani.github.io/pycapnp/) for advanced serialization options. The example below shows how to generate a new pycapnp builder, write a SpatialPooler instance to it, serialize the message, and then read the serialized message back into a new SpatialPooler instance:

```python
# Must import 'capnp' before schema import hook will work
import capnp
from nupic.proto.SpatialPoolerProto_capnp import SpatialPoolerProto

from nupic.algorithms.spatial_pooler import SpatialPooler

sp1 = SpatialPooler(inputDimensions=(10,), columnDimensions=(10,))

# Serialize the SP
builder = SpatialPoolerProto.new_message()
sp1.write(builder)
serializedMessage = builder.to_bytes_packed()

# Deserialize to a new SP instance
reader = SpatialPoolerProto.from_bytes_packed(serializedMessage)
sp2 = SpatialPooler.read(reader)

print sp1.getColumnDimensions(), sp2.getColumnDimensions()
```

## Deprecated Serialization Methods

### OPF Save/Load

**This method of serialization is deprecated.**

```python
import os
from nupic.frameworks.opf.common_models.cluster_params import (
    getScalarMetricWithTimeOfDayAnomalyParams)
from nupic.frameworks.opf.model_factory import ModelFactory

params = getScalarMetricWithTimeOfDayAnomalyParams(
    [0], minVal=0.0, maxVal=100.0)
model1 = ModelFactory.create(modelConfig=params["modelConfig"])

savePath = os.path.join(os.getcwd(), "tmpDir")

# Serialize the SP
model1.save(savePath)

# Deserialize to a new SP instance
model2 = ModelFactory.loadFromCheckpoint(savePath)

print model1._getSPRegion().getSelf().getAlgorithmInstance().getColumnDimensions(), \
      model2._getSPRegion().getSelf().getAlgorithmInstance().getColumnDimensions()
```

### Network Save/Load

**This method of serialization is deprecated.**

```python
import os
from nupic.engine import Network

net1 = Network()
net1.addRegion("encoders", "py.RecordSensor", "")
# ... add regions and links ...

savePath = os.path.join(os.getcwd(), "tmp.nta")

# Save the network
net1.save(savePath)

# Load the network
net2 = Network(savePath)
```

### Pickling

**This method of serialization is deprecated.**

Most algorithms still support pickling objects. But because many algorithms rely on C extensions, you must save the C state in addition to pickling the object. Below is an example of saving a SpatialPooler instance and reading it back using cPickle.

```python
import cPickle as pickle
from nupic.algorithms.spatial_pooler import SpatialPooler

sp1 = SpatialPooler(inputDimensions=(10,), columnDimensions=(10,))

# Serialize the SP
with open("tmp.pkl", "w") as f:
  pickle.dump(sp1, f)

# Deserialize to a new SP instance
with open("tmp.pkl") as f:
  sp2 = pickle.load(f)

print sp1.getColumnDimensions(), sp2.getColumnDimensions()
```
