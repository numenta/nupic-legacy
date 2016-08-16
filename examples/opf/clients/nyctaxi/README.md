## Nyc Taxi 

This custom client is similar to hotgym client and demonstrates how to configure an OPF client with a Numenta's Hierarchical Temporal Memory (HTM) algorithm to detect anomalies. The internal model is constantly generating predictions about the future. The model is configured to output an "anomaly score", a value between 0 and 1 which measures the discrepancy between the actual input and its predicted value.

##Usage 

Simply run the nyctaxi_anomaly.py file to start the client.

    ./nyctaxi_anomaly.py

The parameters used to create the model are specified in `model_params.py`.

##Output 

The output anomaly scores generated are written into `anomaly_scores.csv`. The ground truth labels for anomalies in this dataset are known, including 5 major anomalies that occur during the NYC marathon, Thanksgiving, Christmas, New Years day, and a snow storm.