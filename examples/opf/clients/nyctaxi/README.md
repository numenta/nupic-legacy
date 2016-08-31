## Nyc Taxi 

This custom client is similar to hotgym client and demonstrates how to configure an OPF client with a Numenta's Hierarchical Temporal Memory (HTM) algorithm to detect anomalies. The internal model is constantly generating predictions about the future. The model is configured to output an "anomaly score", a value between 0 and 1 which measures the discrepancy between the actual input and its predicted value.

##Usage 

Simply run the nyctaxi_anomaly.py file to start the client.

    ./nyctaxi_anomaly.py

The parameters used to create the model are specified in `model_params.py`.

##Output 

The output anomaly scores generated are written into `anomaly_scores.csv`. The ground truth labels for anomalies in this dataset are known, including 5 major anomalies that occur during the NYC marathon, Thanksgiving, Christmas, New Years day, and a snow storm. The five anomalies occur at the following timestamps,
    `[
        "2014-11-01 19:00:00",
        "2014-11-27 15:30:00",
        "2014-12-25 15:00:00",
        "2015-01-01 01:00:00",
        "2015-01-27 00:00:00"
    ]`