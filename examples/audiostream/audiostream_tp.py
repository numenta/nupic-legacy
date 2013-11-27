#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
"""
A simple example that streams your mic input into the temporal pooler (TP), 
and outputs an anomaly score, based on how familiar the TP has become to that
particular mic input sequence. Think of it as being able to recognize a song,
or become more familiar with your speech pattern.

This script will run automatically & forever.
To stop it, use KeyboardInterrupt (CRTL+C).

General algorithm:
1. Mic input is received (voltages in the time domain)
2. Mic input is transformed into the frequency domain, using fast fourier transform
3. The few strongest frequencies (in Hz) are identified
4. Those frequencies are encoded into an SDR
5. That SDR is passed to the temporal pooler
6. The temporal pooler provides a prediction
7. We calculate an anomaly score off that prediction against the next input
8. A low anomaly score means that the temporal pooler is properly predicting 
	the next frequency pattern.
	
Next steps:
 Implement real-time visualization
 Implement anomaly smoother (or make TP pull from a longer history)
 Implement spatial pooler
  Need boosting to account for how the bandpass filter falls on the spectrum
 Look into better algorithms to pick out the frequency peaks (sound fingerprinting)
"""

import numpy
import pyaudio
import matplotlib.pyplot as mpl

# The BitmapArray encoder encodes an array of indices into an SDR
# (This will convert that array of the strongest frequencies)
from nupic.encoders.bitmaparray import BitmapArrayEncoder
# This is the C++ optimized temporal pooler that iandanforth & rhyolight using
from nupic.research.TP10X2 import TP10X2 as TP

# The number of columns in the input and therefore the TP
numCols = 2**8 # 2**8 = 256
sparsity = 0.10
numInput = int(numCols * sparsity)

# Create a bit map encoder
# From the encoder's __init__ method:
#   1st arg: the total bits in input
#   2nd arg: the number of bits used to encode each input bit
encoder = BitmapArrayEncoder	
e = encoder(numCols, 1)

# Sampling details
#  rate: The sampling rate in Hz of my soundcard
#  buffersize: The size of the array to which we will save audio segments (2^12 = 4096 is very good)
#  secToRecord: The length of each sampling
#  buffersToRecord: how many multiples of buffers are we recording?
rate=44100
buffersize=2**12
secToRecord=.1
buffersToRecord=int(rate*secToRecord/buffersize)
if not buffersToRecord: buffersToRecord=1
bufToCol = buffersize / 2 / numCols

# Filters in Hertz
#  highHertz: lower limit of the bandpass filter, in Hertz
#  lowHertz: upper limit of the bandpass filter, in Hertz
#    max lowHertz = (buffersize / 2 - 1) * rate / buffersize
highHertz = 1000
lowHertz = 22000

# Convert filters from Hertz to bins
#  highpass: convert the highHertz into a bin for the FFT
#  lowpass: convert the lowHertz into a bin for the FFt
#  NOTES:
#   highpass is at least the 1st bin since most mics only pick up >=20Hz
#   lowpass is no higher than buffersize/2 - 1 (highest array index)
#   passband needs to be wider than size of numInput - not checking for that
highpass = max(int(highHertz * buffersize / rate),1)
lowpass = min(int(lowHertz * buffersize / rate), buffersize/2 - 1)

# The call to create the temporal pooler region
tp = TP(numberOfCols=numCols, cellsPerColumn=4,
		initialPerm=0.5, connectedPerm=0.5,
		minThreshold=10, newSynapseCount=10,
		permanenceInc=0.1, permanenceDec=0.05,
		activationThreshold=8,
		globalDecay=0.01, burnIn=2,
		checkSynapseConsistency=False,
		pamLength=10)

# Fast fourier transform conditioning
# Output:
#  'output' contains the strength of each frequency in the audio signal
#  frequencies are marked by its position in 'output':
#   frequency = index * rate / buffesize
#  output.size = buffersize/2
# 
# Method:
#  Use numpy's FFT (numpy.fft.fft)
#  Find the magnitude of the complex numbers returned (abs value)
#  Split the FFT array in half, because we have mirror frequencies
#   (they're the complex conjugates)
#  Use just the first half to apply the bandpass filter
#
# Great info here: http://stackoverflow.com/questions/4364823/how-to-get-frequency-from-fft-result

def fft(audio):
	left,right = numpy.split(numpy.abs(numpy.fft.fft(audio)),2)
	output = left[highpass:lowpass]
	return output 

# Calculates the anomaly of two SDRs
# Uses the equation presented on the wiki: 
# https://github.com/numenta/nupic/wiki/Anomaly-Score-Memo
#
# To put this in terms of the temporal pooler:
# A is the actual input array at a given timestep
# P is the predicted array that was produced from the previous timestep(s)
# [A - (A && P)] / [A]
# What are the similarities between the two SDRs?
# What bits are on in A that are not on in P?
# How does that compare to total on bits in A?
#
# Outputs 0 is there's no difference between P and A.
# Outputs 1 if P and A are totally distinct.
#
# Not a perfect metric - it doesn't credit proximity
# Next step: combine with a metric for a spatial pooler

def calcAnomaly(actual, predicted):
	combined = numpy.logical_and(actual, predicted)
	delta = numpy.logical_xor(actual,combined)
	delta_score = sum(delta)
	actual_score = float(sum(actual))
	return delta_score / actual_score
	
def compareArray(actual, predicted):
	compare = []
	for i in range(actual.size):
		if actual[i] and predicted[i]:
			compare.append('E')
		elif actual[i]:
			compare.append('A')
		elif predicted[i]:
			compare.append('P')
		else:
			compare.append(' ')
	return compare

# Basic print out method to visualize the anomaly score
# Scale is from one hashtag to 50
def hashtagAnomaly(anomaly):
	hash = '#'
	for i in range(int(anomaly / 0.02)):
		hash += '#'
	for j in range(int((1 - anomaly) / 0.02)):
		hash += '.'
	return hash
	
#######################
# The meat & potatoes #
#######################

# Creating the audio stream from our mic
p = pyaudio.PyAudio()
inStream = p.open(format=pyaudio.paInt32,channels=1,rate=rate,input=True,frames_per_buffer=buffersize)

# Setting up the array that will handle the timeseries of audio data from our input
audio=numpy.empty((buffersToRecord*buffersize),dtype="uint32")

print "Number of columns:\t" + str(numCols)
print "Max size of input:\t" + str(numInput)

print "Sampling rate (Hz):\t" + str(rate)
print "Passband filter (Hz):\t" + str(highHertz) + " - " + str(lowHertz)

print "Buffersize:\t\t" + str(buffersize)
print "Buffer/columns:\t\t" + str(bufToCol)

# Record and pass the TP forever
while True:
	# for the multiples of buffers that we're sampling at once
	for i in range(buffersToRecord):
		# sample audio for the number of frames in a buffersize
		#  saves mic voltage-level timeseries as 32-bit binary
		audioString=inStream.read(buffersize)
		# convert that 32-bit binary into integers, and save to array for the FFT
		audio[i*buffersize:(i+1)*buffersize]=numpy.fromstring(audioString,dtype="uint32")
	# Getting an int array of all the frequencies in our audio via the fast fourier transform
	ys = fft(audio)
	# Get the indices of our top frequencies (top numInput)
	fs = numpy.sort(ys.argsort()[-numInput:])
	# Scale those indicies so that they fit to our number of columns
	rfs = fs/bufToCol
	# Pick out the unique indices (we've reduced the mapping)
	ufs = numpy.unique(rfs)
	if(False):
		# Convert the indices back to frequencies for debugging
		print fs * rate/buffersize + highHertz
		# Develop an x-axis for the plot, and convert back to frequencies
		bin = numpy.arange(ys.size)*rate/buffersize + highHertz
		mpl.plot(bin,ys)
		mpl.show()
		quit()
	# Encoding our array of frequency indices into an SDR via the BitmapArrayEncoder
	actualInt = e.encode(ufs)
	# Casting the SDR as a float for the TP
	actual = actualInt.astype(numpy.float32)
	# Passing the SDR to the TP
	tp.compute(actual, enableLearn = True, computeInfOutput = True)
	# Collecting the prediction SDR
	predictedInt = tp.getPredictedState().max(axis=1)
	# Passing the prediction & actual SDRs to the anomaly calculator & array comparer
	compare = compareArray(actualInt, predictedInt)
	anomaly = calcAnomaly(actualInt, predictedInt)
	print '.' .join(compare)
	print hashtagAnomaly(anomaly)