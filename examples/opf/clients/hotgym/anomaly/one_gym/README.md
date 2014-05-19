# One Hot Gym Anomaly Tutorial

The program in this folder is the complete source code for the "One Hot Gym Anomaly" Tutorial. ~~You can follow along with the construction of this tutorial's source code in the screencast below.~~

<!-- 
[![One Hot Gym Prediction Tutorial Screencast](http://img.youtube.com/vi/S-0thrzOHTc/hqdefault.jpg)](http://www.youtube.com/watch?v=S-0thrzOHTc)
 -->

## Premise

The "hot gym" sample application has been around for a long time, and was one of the first real-world applications of NuPIC that actually worked. The data used is real energy consumption data from a gym in Australia. It is aggregated hourly already, so the input file at [rec-center-hourly.csv](rec-center-hourly.csv) simply contains a timestamp and float value for energy consumption during that hour.

This tutorial picks up where the [One Hot Gym Prediction Tutorial](../../prediction/one_gym/README.md) left off, and shows users how to convert their prediction model into an anomaly detection model.

## How to Run

To run and output data to a local file:

    ./run.py

To run and output data to a **matplotlib** graph:

    ./run.py --plot

> You must have **matplotlib** properly installed for this option to work.

## Program Description

This example code assumes a swarm has already been run against the input data (see [One Hot Gym Prediction Tutorial](../../prediction/one_gym/README.md) for details). Model parameters therefore already exist in the `model_params` directory, and the only step to run this tutorial is to simply execute `./run.py`.

## What's Different?

You might be wondering how to convert your prediction model into an anomaly model. This is quite simple. For this example, the only thing necessary was to change the `inferenceType` within the model parameters from `TemporalMultistep` to `TemporalAnomaly`. After this change, model results will contain an `anomalyScore` value in addition to the multi-step inferences. 

## How is the Output Handled?

Most of the code changes for this tutorial were done outside of instantiating and running an OPF CLAModel. For this example, the `nupic_output.py` file was updated to properly handle the additional anomaly data being produced by the model. For file output (sans `--plot` option), the "anomaly score" and "anomaly likelihood" values are simply written to the CSV file as additional columns. For the matplotlib `--plot` option, it plots the "anomaly score" and "anomaly likelihood" values in a separate chart aligned with the energy consumption predictions.
