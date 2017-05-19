# Network API Examples

## Overview

The Network API provides an interface for defining regions that have named
inputs and outputs and linking the regions together. The API automates the
process of propagating the data from one region to another. The API also
allows regions to specify how they should be serialized so that you can
serialize an entire network easily.

## Defining a Region

Regions can be implemented in Python by subclassing
:class:`nupic.regions.PyRegion.PyRegion` or in C++ by subclassing the C++
Region. See the base class definitions for more details on implementing your own
region.

## Creating a Network

Take a look at `network_api_demo.py` for how to create and run a network.
