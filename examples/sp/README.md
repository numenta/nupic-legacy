# ![Numenta Logo](http://numenta.org/images/numenta-icon128.png) NuPIC

## Basic Spatial Pooler Example

hello_sp.py contains a simple spatial pooler demonstration written in python.

#### To run
	python hello_sp.py


#### Details

This script provides 3 examples demonstrating the effects of the spatial pooler on the following 3 sets of input values:

1. Displaying the output [SDRs](https://discourse.numenta.org/t/sparse-distributed-representations/2150) of 3 randomized input values.
2. Displaying 3 [SDR's](https://discourse.numenta.org/t/sparse-distributed-representations/2150) generated from the same input value.
3. Displaying 3 [SDR's](https://discourse.numenta.org/t/sparse-distributed-representations/2150) generated with slightly different input values, by adding 10% and 20% noise to the original input vector.

The script uses a simple binary vector for input.

After running this example and reading through the output you should have a basic understanding of the relationship between input and output of the spatial pooler.


Further reading: [Encoders](https://discourse.numenta.org/t/nupic-encoders/2153)

## Second Spatial Pooler Example

sp_tutorial.py replicates figures 5, 7 and 9 from the paper
[Porting HTM Models to the Heidelberg Neuromorphic Computing Platform](http://arxiv.org/abs/1505.02142).
This will show some basic properties of the spatial pooler.

#### To run
	python sp_tutorial.py


#### Details

The script is divided in three parts, each of them addressing one of the following questions:

1. What is the distribution of the overlap scores in a spatial pooler for a random binary input?
2. How robust is the spatial pooler against input noise when untrained?
3. How robust is it after training?

More details can be found in the comments of the script as well as in its command-line output.
