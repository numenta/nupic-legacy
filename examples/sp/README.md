# ![Numenta Logo](http://numenta.org/images/numenta-icon128.png) NuPIC

## Basic Spatial Pooler Example

hello_sp.py contains a simple spatial pooler demonstration written in python.

#### To run
	python hello_sp.py


#### Details

This script provides 3 examples demonstrating the effects of the spatial pooler on the following 3 sets of input values:
		
1. Displaying the output [SDRs](https://github.com/numenta/nupic/wiki/Sparse-Distributed-Representations) of 3 randomized input values.
2. Displaying 3 [SDR's](https://github.com/numenta/nupic/wiki/Sparse-Distributed-Representations) generated from the same input value.
3. Displaying 3 [SDR's](https://github.com/numenta/nupic/wiki/Sparse-Distributed-Representations) generated with slightly different input values, by adding 10% and 20% noise to the original input vector.

The script uses a simple binary vector for input.

After running this example and reading through the output you should have a basic understanding of the relationship between input and output of the spatial pooler.


Further reading: [Encoders](https://github.com/numenta/nupic/wiki/Encoders)