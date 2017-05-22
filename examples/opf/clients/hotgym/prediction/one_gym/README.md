# One Hot Gym Prediction Tutorial

The program in this folder is the complete source code for the "One Hot Gym Prediction" Tutorial. You can follow along with the construction of this tutorial's source code in the screencast below.

[![One Hot Gym Prediction Tutorial Screencast](http://img.youtube.com/vi/S-0thrzOHTc/hqdefault.jpg)](http://www.youtube.com/watch?v=S-0thrzOHTc)

## Premise

The "hot gym" sample application has been around for a long time, and was one of the first real-world applications of NuPIC that actually worked. The data used is real energy consumption data from a gym in Australia. It is aggregated hourly already, so the input file at [rec-center-hourly.csv](rec-center-hourly.csv) simply contains a timestamp and float value for energy consumption during that hour.

This tutorial shows how to take that data file, create a [swarm](http://nupic.docs.numenta.org/0.7.0.dev0/guides/swarming/index.html) to find the best NuPIC Model parameters, then use those Model parameters to create a NuPIC Model and feed the data into it, getting 1-step-ahead predictions for each row of data being fed into NuPIC. Essentially, this example shows how NuPIC can prediction the energy consumption of a building one hour into the future.

## Program Description

This is a program consisting of a simple collection of Python scripts using NuPIC's [Online Prediction Framework](http://nupic.docs.numenta.org/0.7.0.dev0/guides/opf.html). Program execution is described in the [Running the Program](#running-the-program) section below. There are two steps this program performs to get predictions for the input data from the [rec-center-hourly.csv](rec-center-hourly.csv) file, which are described below. There is also an optional step ([Cleanup](#cleanup)), which removes artifacts from the files system after the previous steps have run.

## Program Phases

### 1. Swarming Over the Input Data

Swarming ain't perfect, but it is an essential way for us to find the best NuPIC model parameters for a particular data set. It only needs to be done once, and can be performed over a subset of the data. NuPIC knows nothing about the structure and data types within [rec-center-hourly.csv](rec-center-hourly.csv), so we have to define this data.

#### Swarm Description

The swarming process requires an initial _swarm description_, which defines the input data and limits some of the permutations that must occur during the swarming process. The _swarm description_ for this tutorial application is within the [swarm_description.py](swarm_description.py) file, and looks like this:

```
{
  "includedFields": [
    {
      "fieldName": "timestamp",
      "fieldType": "datetime"
    },
    {
      "fieldName": "kw_energy_consumption",
      "fieldType": "float",
      "maxValue": 53.0,
      "minValue": 0.0
    }
  ],
  "streamDef": {
    "info": "kw_energy_consumption",
    "version": 1,
    "streams": [
      {
        "info": "Rec Center",
        "source": "file://rec-center-hourly.csv",
        "columns": [
          "*"
        ]
      }
    ],
  },

  "inferenceType": "TemporalMultiStep",
  "inferenceArgs": {
    "predictionSteps": [
      1
    ],
    "predictedField": "kw_energy_consumption"
  },
  "iterationCount": -1,
  "swarmSize": "medium"
}
```

- `includedFields`: These correspond do the columns of data the swarm will use when searching for model parameters. A `fieldName` and `fieldType` are required. In this example, we are specifying minimum and maximum values for the `kw_energy_consuption` data column, which will help the swarm logic limit the amount of work it does to find the best params.

- `streamDef`: Tells the swarm where the input data file is. You have to put the "file://" prefix before the path to the data file defined in `streams.source`. The path can be relative or absolute.

- `inferenceType`: Indicates that we expect time-based multistep predictions to be evaluated. Other inference types include `Multistep`, `NontemporalMultistep`, and `TemporalAnomaly`.

- `inferenceArgs`: Defines which field should be predicted, and how many steps into the future the field should be predicted. Several step-ahead predictions can be specified in `predictionSteps`, but be aware that more prediction steps will slow down NuPIC execution.

- `iterationCount`: How many rows within the input data file to swarm over. If `-1`, assume all rows.

- `swarmSize`: Can be `small`, `medium`, and `large`. Small swarms are used only for debugging. Medium swarms are almost always what you want. Large swarms can take a very long time, but get slightly better model params than medium.

#### Results of the Swarm

##### Working files (junk)
Once the swarm is complete, you'll see a `swarm` folder within your working directory. It contains the internal workings of the swarm, which includes utilities you can use for advanced swarming (out of scope for this tutorial). This tutorial application places all the swarming junk into the `swarm` folder mostly just to keep the working directory uncluttered. When you [run swarms](http://nupic.docs.numenta.org/0.7.0.dev0/guides/swarming/index.html) through the swarming CLI, all this cruft is dumped into your current working directory.

##### Model Params (GOLD!)
Within the `model_params` directory, you'll also see a python file appear called `rec-center-hourly_model_params.py`. This file contains a configuration object for the **best model** the swarm found for the input data. This config object is used to create the NuPIC Model in the next step.

### 2. Running the NuPIC Model

The primary result of swarming is the **best model** configuration (detailed above). Once the best model parameters have been identified, a new NuPIC Model object can be created, data can be passed into it, and predictions can be retrieved. During this phase of the program, a new Model is created, and the [rec-center-hourly.csv](rec-center-hourly.csv) input data file is fed line-by-line into the model. For each line feed, a prediction for the next value of energy consumption is retrieved from the NuPIC Model and either written to file or presenting in a graph on the screen.

### 3. Cleanup (optional)

This phase simply removes all the file artifacts created within previous steps from the file system and presents a clean slate for further program executions.

## Running the Program

This program consists of 3 Python scripts you can execute from the command line and a few helper modules. The executable scripts are `swarm.py`, `run.py`, and `cleanup.py`. Each script prints out a description of the actions it takes when executed.

There are two major steps: _swarming_ & _running_. Descriptions of these steps are above.

### Swarming

    ./swarm.py

Hard-coded to run the [rec-center-hourly.csv](rec-center-hourly.csv) input for purposes of this tutorial application. Could take quite a long time for a medium swarm, depending on your hardware resources.

### Running

    ./run.py [--plot]

If `--plot` is not specified, writes predictions to `rec-center-hourly_out.csv` file within the current working directory. If `--plot` is specified, will attempt to plot on screen using **matplotlib**. If matplotlib is not installed, this will fail miserably.

### Cleanup

    ./cleanup.py

The previous steps leave some artifacts on your file system. Run this command to clean them up and start from scratch.
