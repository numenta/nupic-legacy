# Audio Stream Example

A simple example that streams your mic input into the temporal pooler (TP), 
and outputs an anomaly score, based on how familiar the TP has become to that
particular mic input sequence. Think of it as being able to recognize a song,
or become more familiar with your speech pattern.

## Requirements

- Mac OS X
- [matplotlib](http://matplotlib.org/)
- [pyaudio](http://people.csail.mit.edu/hubert/pyaudio/)

## Usage

    python audiostream_tp.py

This script will run automatically & forever.
To stop it, use KeyboardInterrupt (CRTL+C).

## General algorithm:

1. Mic input is received (voltages in the time domain)
2. Mic input is transformed into the frequency domain, using fast fourier transform
3. The few strongest frequencies (in Hz) are identified
4. Those frequencies are encoded into an SDR
5. That SDR is passed to the temporal pooler
6. The temporal pooler provides a prediction
7. An anomaly score is calculated off that prediction against the next input
    A low anomaly score means that the temporal pooler is properly predicting 
    the next frequency pattern.

## Print outs include:

1. An array comparing the actual and predicted TP inputs
	A - actual
	P - predicted
	E - expected (both A & P)
2. A hashbar representing the anomaly score
3. Plot of the frequency domain in real-time   

## Next steps:

1. Benchmark different parameters (especially TP parameters)
	Use annoying_test and Online Tone Generator http://onlinetonegenerator.com/
2. Implement anomaly smoothing
3. Implement spatial pooler
4. Look into better algorithms to pick out the frequency peaks (sound fingerprinting)
