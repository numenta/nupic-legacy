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
1. Mic input is received (in the time domain)
2. Mic input is transformed into the frequency domain, using fast fourier transform
3. The few strongest frequencies (in kHz) are identified
4. Those frequencies are encoded into an SDR
5. That SDR is passed to the temporal pooler
6. The temporal pooler provides a prediction
7. We calculate an anomaly score off that prediction against the next input
8. A low anomaly score means that the temporal pooler is properly predicting 
	the next frequency pattern.
	
Next steps:
	Develop a spatial pooling-type anomaly score - would like to 'recognize'
		sound patterns heard before (like a voice), but that are not
		necessarily predicted in a sequence
"""

import numpy
# The library to handle the mic input
import pyaudio

# The BitmapArray encoder encodes an array of indices into an SDR
# (This will convert that array of the strongest frequencies)
from nupic.encoders.bitmaparray import BitmapArrayEncoder
# This is the C++ optimized temporal pooler that I noticed Ian & Matt using
from nupic.research.TP10X2 import TP10X2 as TP

# The fast fourier transform algorithm
def fft(audio, BUFFERSIZE, trimBy=10, logScale=False, divBy=100):
	data=audio.flatten()
	left,right=numpy.split(numpy.abs(numpy.fft.fft(data)),2)
	ys=numpy.add(left,right[::-1])
	if logScale:
		ys=numpy.multiply(20,numpy.log10(ys))
	# xs=numpy.arange(BUFFERSIZE/2,dtype=float)
	if trimBy:
		i=int((BUFFERSIZE/2)/trimBy)
		ys=ys[:i]
		# xs=numpy.around(xs[:i]*RATE/BUFFERSIZE,decimals=0)
	if divBy:
		ys=numpy.around(ys/float(divBy),decimals=0)
	return ys 


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
# Outputs 1 is P and A are totally distinct.
#
# Not a perfect metric - it doesn't credit proximity
# Next step: combine with a metric for a spatial pooler

def calcAnomaly(actual, predicted):
	combined = numpy.logical_and(actual, predicted)
	delta = numpy.logical_xor(actual,combined)
	delta_score = sum(delta)
	actual_score = float(sum(actual))
	return delta_score / actual_score
	
# Basic print out method to visualize the anomaly score
# Zero represented as 1 '#'
def hashtagAnomaly(anomaly):
	hash = '#'
	for i in range(int(anomaly / 0.02)):
		hash += '#'
	return hash
	
#######################
# The meat & potatoes #
#######################

# The number of columns in the input and therefore the TP
# 210 seems to be the max of our mic input transformed through the FFT
# If 210 is exceeded, the program will give you an 'out of bounds' error
# Next step: round off the FFT based on this number
numCols = 210

# The call to create the temporal pooler region
tp = TP(numberOfCols=numCols, cellsPerColumn=4,
		initialPerm=0.5, connectedPerm=0.5,
		minThreshold=10, newSynapseCount=10,
		permanenceInc=0.1, permanenceDec=0.05,
		activationThreshold=8,
		globalDecay=0, burnIn=2,
		checkSynapseConsistency=False,
		pamLength=10)

# Create a bit map encoder
# From the encoder's __init__ method:
#   1st arg: the total bits in input
#   2nd arg: the number of bits used to encode each input bit
_encoder = BitmapArrayEncoder	
e = _encoder(numCols, 1)

# Sampling details
# RATE: The sampling rate in Hz of my soundcard
# BUFFERSIZE: The size of the array to which we will save audio segments
# secToRecord: The length of each sampling
RATE=44100
BUFFERSIZE=2**12 #4096 is a good buffer size
secToRecord=.1

# Figuring out how to breakup the audio from the input
buffersToRecord=int(RATE*secToRecord/BUFFERSIZE)
if buffersToRecord==0: buffersToRecord=1
samplesToRecord=int(BUFFERSIZE*buffersToRecord)
chunksToRecord=int(samplesToRecord/BUFFERSIZE)
secPerPoint=1.0/RATE

# Creating the audio stream from our mic
p = pyaudio.PyAudio()
inStream = p.open(format=pyaudio.paInt32,channels=1,rate=RATE,input=True,frames_per_buffer=BUFFERSIZE)

# Setting up the array that will handle the timeseries of audio data from our input
audio=numpy.empty((chunksToRecord*BUFFERSIZE),dtype="uint32")

# Record and pass the TP forever
while True:
	for i in range(chunksToRecord):
		audioString=inStream.read(BUFFERSIZE)
		audio[i*BUFFERSIZE:(i+1)*BUFFERSIZE]=numpy.fromstring(audioString,dtype="uint32")
	# Getting an int array of all the frequencies in our audio via the fast fourier transform
	ys = fft(audio, BUFFERSIZE)
	# Getting the 21 strongest frequencies (21 is 10% of our input length)
	ys = numpy.sort(ys.argsort()[-21:])
	# Encoding our array of frequency indices into an SDR via the BitmapArrayEncoder
	actual = e.encode(ys)
	# Casting the SDR as a float for the TP
	actual = actual.astype(numpy.float32)
	# Passing the SDR to the TP
	tp.compute(actual, enableLearn = True, computeInfOutput = True)
	# Collecting the prediction SDR
	predicted_columns = tp.getPredictedState().max(axis=1)
	# Passing the prediction & actual SDRs to the anomaly calculator
	anomaly = calcAnomaly(actual, predicted_columns)
	print actual
	print hashtagAnomaly(anomaly)
	
