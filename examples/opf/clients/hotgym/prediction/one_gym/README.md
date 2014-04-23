# One Hot Gym Prediction Tutorial

The program in this folder is the complete source code for the "One Hot Gym Prediction" Tutorial.

## Program Description

This is a Python CLI program that uses NuPIC's [Online Prediction Framework](https://github.com/numenta/nupic/wiki/Online-Prediction-Framework). The CLI wrapper is described in the [Running the Program](#running-the-program) section below. There are two steps that this program performs to get predictions for the input data from the [Balgowlah_Platinum.csv](Balgowlah_Platinum.csv) file, which are described below. There is also an optional step ([Cleanup](#cleanup)), which removes artifacts from the files system after the previous steps have run.

## Program Phases

### 1. Swarming Over the Input Data

Swarming is a way for us to find the best NuPIC model parameters for a particular data set. It only needs to be done once, and can be performed over a subset of the data. NuPIC knows nothing about the structure and data types within [Balgowlah_Platinum.csv](Balgowlah_Platinum.csv), so we have to define this data. The swarming process requires an initial _swarm description_, which defines the input data and limits some of the permutations that must occur during the swarming process.

Once the swarm is complete, you'll see a `swarm` folder within your working directory. It contains the internal workings of the swarm, which includes utilities you can use for advanced swarming (out of scope for this tutorial).

Within the `model_params` directory, you'll also see a python file appear called `Balgowlah_Platinum_model_params.py`. This file contains a configuration object for the **best model** the swarm found for the input data. This config object is used to create the NuPIC Model in the next step.

### 2. Running the NuPIC Model

The primary result of swarming is the **best model** configuration (detailed above). Once the best model parameters have been identified, a new NuPIC Model object can be created, data can be passed into it, and predictions can be retrieved. During this phase of the program, a new Model is created, and the [Balgowlah_Platinum.csv](Balgowlah_Platinum.csv) input data file is fed line-by-line into the model. For each line feed, a prediction for the next value of energy consumption is retrieved from the NuPIC Model and either written to file or presenting in a graph on the screen.

### 3. Cleanup (optional)

This phase simply removes all the file artifacts created within previous steps from the file system and presents a clean slate for further program executions.

## Running the Program

The program is a Python CLI script. You can see all the options by running:

    ./run.py --help

There are two major steps: _swarming_ & _running_. Descriptions of these steps are above.

### Swarming

    ./run.py swarm

This command uses the _swarm description_ at [swarm_description.py](swarm_description.py) as a configuration. It can be updated to change swarm parameters. As a part of the swarm process, a `swarm` directory is created to contain the files created by the swarm. This includes the `description.py` and `permutations.py` files, which are elements that can be manipulated for advanced swarming.

### Running

    ./run.py run [--plot]
