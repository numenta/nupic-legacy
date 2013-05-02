<section>
  <nav>
    <ul>
      <li><a href="#getting_started">Getting Started</a></li>
      <li><a href="#features_of_nupic">Features</a></li>
      <li><a href="#requirements">Requirements</a></li>
      <li><a href="#development_status">Status</a></li>
      <li><a href="#source_code">Code</a></li>
      <li><a href="#issue_tracking">Issues</a></li>
    </ul>
  </nav>
</section>

Getting Started
---------------
There are two things to be aware of before diving into NuPIC.  The NuPIC source code is embedded in a commercial product called [Grok](https://www.groksolutions.com/product.html).  Because of this, it is no longer a "pure" implementation of the algorithms.  We have made optimizations, added tweaks, and taken some short cuts to improve performance.  For those interested in studying and characterizing the [CLA](https://www.numenta.com/technology.html#cla-whitepaper) you may want to back out some of these changes.  If your interest is using NuPIC as a _product_, then you may be happy with the code as-is.  The second thing to consider is that the CLA is based on principles that most people are not familiar with, including [sparse distributed representations](#sparse_distributed_representations), [online learning](#online_learning), and [distributed memory](#distributed_memory).  There is a steeper than normal learning curve.

We will be releasing documentation over time and welcome both contributions and suggestions for areas to focus on.

Features of NuPIC
-----------------

### Online Learning

<p class="todo">Anyone: Describe online learning.</p>

### Sparse Distributed Representations

<p class="todo">Anyone: Describe SDRs.</p>

### Distributed Memory

<p class="todo">Anyone: Describe distributed memory.</p>

Requirements
------------
* Linux or Unix environment
* Python 2.6

Development Status
------------------
Being extracted from the current Grok codebase. Soon to be scrubbed and made available at the address below.

Source Code
-----------
[Github](http://github.com/numenta/nupic).

Issue Tracking
--------------
_JIRA coming soon_