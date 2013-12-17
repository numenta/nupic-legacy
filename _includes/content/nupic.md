# Numenta Platform for Intelligent Computing (NuPIC)

NuPIC is a Python / C++ open source project that implements the [CLA]({{ site.baseurl }}/cla.html) as described in the [CLA White Paper]({{ site.baseurl }}/cla-white-paper.html). For an introduction to the project, watch the presentation below, given at the Open Source Conference (OSCON) in 2013.

<div align="center">
    <iframe width="640" height="415" src="//www.youtube.com/embed/5r1vZ1ymrQE" frameborder="0" allowfullscreen="allowfullscreen">
    </iframe>
</div>
<br/>

## Getting Started

If you want to jump right into the code, we have a [Getting Started](https://github.com/numenta/nupic/wiki/Getting-Started) wiki page to help guide you.

There are a few things to be aware of before diving into NuPIC. The NuPIC source code is used by Numenta as a part of a commercial product development. Because of this, it is no longer a “pure” implementation of the algorithms. We have made optimizations, added tweaks, and taken some short cuts to improve performance. For those interested in studying and characterizing a purer form of the [CLA](cla.html) you may want to back out some of these changes or at least be aware of them. If your interest is using NuPIC in a product, then you may be happy with the code as-is or you may want to make additional changes. Another thing to consider is that the CLA is based on principles that most people are not familiar with, including [sparse distributed representations](cla.html#sparse_distributed_representations), [online learning](cla.html#online_learning), and distributed memory. There is a steeper than normal learning curve.

## Requirements

We're working on providing virtual machines ready to run NuPIC so Windows developers can work on NuPIC within [Virtual Box](https://www.virtualbox.org). Currently, the build requirements are:

* Linux or Unix environment with gnu compilers
* Python 2.6 or 2.7

## Source Code

We keep our source code on [Github](http://github.com/numenta/nupic).

<iframe src="http://ghbtns.com/github-btn.html?user=numenta&amp;repo=nupic&amp;type=watch&amp;count=true&amp;size=large"
  allowtransparency="true" frameborder="0" scrolling="0" width="170" height="30">
</iframe>
<iframe src="http://ghbtns.com/github-btn.html?user=numenta&amp;repo=nupic&amp;type=fork&amp;count=true&amp;size=large"
  allowtransparency="true" frameborder="0" scrolling="0" width="170" height="30">
</iframe>

<br/>
<br/>

## Build Status

We run continuous integration with [Travis-CI](https://travis-ci.org/numenta/nupic). You can see detailed status of our build pipeline at [status.numenta.org](http://status.numenta.org).

[![Build Status](https://travis-ci.org/numenta/nupic.png?branch=master)](https://travis-ci.org/numenta/nupic)

## Issue Tracking

We use Github Issues for [issue tracking](https://github.com/numenta/nupic/issues) and [Huboard](https://huboard.com/numenta/nupic) for agile planning.

## Road Map

You can get an indication of our current direction by reading through our [Road Map](https://github.com/numenta/nupic/wiki/Road-Map).
