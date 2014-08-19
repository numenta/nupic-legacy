# CPU 

This is a custom client that attempts to predict CPU on the local system. It uses the NuPIC [Online Prediction Framework](https://github.com/numenta/nupic/wiki/Online-Prediction-Framework) (OPF), to derive predictions in realtime.

##Usage
Simply run the cpu.py file to start the client.

    ./cpu.py

##Explanation
The client gathers CPU usage data from the computer using python's psutil library, and feeds the data into an OPF model specified by the `model_params.py` file.



