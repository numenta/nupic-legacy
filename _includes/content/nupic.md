<section>
  <nav>
    <ul>
      <li><a href="#getting_started">Getting Started</a></li>
      <li><a href="#features_of_nupic">Features</a></li>
      <li><a href="#requirements">Requirements</a></li>
      <li><a href="#project_status">Status</a></li>
      <li><a href="#source_code">Code</a></li>
      <li><a href="#issue_tracking">Issues</a></li>
    </ul>
  </nav>
</section>

Getting Started
---------------
There are two things to be aware of before diving into NuPIC.  The NuPIC source code is embedded in a commercial product called [Grok](https://www.groksolutions.com/product.html).  Because of this, it is no longer a "pure" implementation of the algorithms.  We have made optimizations, added tweaks, and taken some short cuts to improve performance.  For those interested in studying and characterizing the [CLA]({{ site.baseurl }}/resources/HTM_CorticalLearningAlgorithms.pdf) you may want to back out some of these changes.  If your interest is using NuPIC as a _product_, then you may be happy with the code as-is.  The second thing to consider is that the CLA is based on principles that most people are not familiar with, including [sparse distributed representations](#sparse_distributed_representations), [online learning](#online_learning), and distributed memory.  There is a steeper than normal learning curve.

We will be releasing documentation over time and welcome both contributions and suggestions for areas to focus on.

Features of NuPIC
-----------------

### Online Learning

Conventional machine learning techniques are static: the best statistical fit is calculated from a training data set, verified on a testing data set, and applied to real-world data. Some are powerful enough to find a fit for nearly any set of training data, although this introduces the possibility of "over-fitting." This is similar to how a specific set of economic variables can be selected that correlates with all past Presidential elections, but fail to predict the next one. More importantly, real-world data changes over time. In these cases, previously accurate models must be retrained with new data, repeating the time and expense of the original manual process.

NuPIC's automated learning, on the other hand, does not require conventional training and testing data sets. As described above, NuPIC returns a prediction for every data input value, and adjusts over time. NuPIC can automatically adjust predictions if the underlying field combinations and parameters remain valid.

### Sparse Distributed Representations

NuPIC converts disparate data types into a common format, to learn patterns and see relationships. This format must be flexible enough to generalize and recognize "similar" patterns, an ability that has eluded computers. Artificial intelligence experts call this the problem of "representation." How do you represent and store information about the world? The brain's model of the world generates concepts like what a car is, what it does, and what its attributes are. We translate sensory input into representations so effortlessly that it's difficult to understand why computers struggle with it.

Computers store data in “dense” representations of 1s and 0s. For example, ASCII characters are stored in blocks of 8 bits. The letter "m" is represented by the string "01101101." Each 1 and 0 has no inherent meaning, and changing one bit will completely change the meaning of the entire string of bits (“vector”).

By contrast, data stored in the brain is very sparse. The human brain has between 30 and 100 billion neurons, but at any given time only a few percent are active. You can translate this into a data storage system called “Sparse Distributed Representations” (SDRs), where active neurons are represented by 1s and inactive neurons are 0s. SDRs have thousands of bits, but typically only about 2% are 1s and 98% are 0s.

<div class="image-wrapper">
  <img alt="Example of a sparse distributed representation in an array of cells" src="{{ site.baseurl }}/images/sdr.png" />
  <p>This diagram represents sparsity: two thousand circles with a small number of red circles active.</p>
</div>

In SDRs, unlike computer data, each bit has meaning. This means that if two vectors have 1s in the same position they are semantically similar. Vectors can therefore be expressed in degrees of similarity rather than simply being identical or different. These large vectors can be stored accurately even using a subsampled index of, say, 10 of 2,000 bits. This makes SDR memory fault tolerant to gaps in data. SDRs also exhibit properties that reliably allow the neocortex to determine if a new input is unexpected. After understanding the benefits of SDRs, it is difficult to imagine that an intelligent system could be built without them.

For more details about SDRs, watch [this excerpt](http://www.youtube.com/embed/t6NcTdXxVeo) from a talk given by Jeff Hawkins.


Requirements
------------

We're working in providing virtual machines ready to run NuPIC so Windows developers can work on NuPIC within [Virtual Box](https://www.virtualbox.org). Currently, the build requirements are:

* Linux or Unix environment with gnu compilers
* Python 2.6

Project Status
------------------
The code is open source (see [below](#source_code)), as of 03 June, 2013. However, the project is currently in a transitional period before contributions will be seriously accepted. This month-long period will give the community a chance to review and understand the source code, as well as Numenta's internal engineers a chance to update their processes to include an open source build.

Starting in July, we will seriously consider incoming Pull Requests on our codebase. In the meantime, minor contributions to our [website source code](https://github.com/numenta/nupic/tree/gh-pages), documentation, wikis, etc. are welcome, as long as they follow the [development workflow](https://github.com/numenta/nupic/wiki/Developer-workflow).

Source Code
-----------
We're rocking [Github](http://github.com/numenta/nupic).

Issue Tracking
--------------
We use JIRA for issue tracking at [issues.numenta.org](http://issues.numenta.org).