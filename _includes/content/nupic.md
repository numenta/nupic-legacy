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
There are a few things to be aware of before diving into NuPIC. The NuPIC source code is embedded in a commercial product called [Grok](https://www.groksolutions.com/product.html). Because of this, it is no longer a “pure” implementation of the algorithms. We have made optimizations, added tweaks, and taken some short cuts to improve performance. For those interested in studying and characterizing a purer form of the [CLA]({{ site.baseurl }}/resources/HTM_CorticalLearningAlgorithms.pdf) you may want to back out some of these changes or at least be aware of them. If your interest is using NuPIC in a product, then you may be happy with the code as-is or you may want to make additional changes. Another thing to consider is that the CLA is based on principles that most people are not familiar with, including [sparse distributed representations](#sparse_distributed_representations), [online learning](#online_learning), and distributed memory. There is a steeper than normal learning curve.

We will be releasing documentation over time and welcome both contributions and suggestions for areas to focus on.

Features of NuPIC
-----------------

### Online Learning

Most machine learning techniques are relatively static.  A model is constructed from a training data set, verified on a testing data set, and then applied to real-world data. However the patterns and structure in the world changes over time. Therefore previously accurate models must be regularly retrained with new data, repeating the time and expense of the original process.

The CLA on the other hand is an online learning system.  It does not require conventional training and testing data sets. Instead, the CLA learns continuously with each new data point.  The CLA is constantly making predictions which are continually verified as more data arrives.  As the underlying patterns in the data change the CLA adjusts accordingly.  An online learning system such as the CLA forces you to think about many things differently than you do with algorithms that relay on static training data sets.

### Sparse Distributed Representations

Computers store information in “dense” representations such as a 32 bit word where all combinations of 1s and 0s are possible.

By contrast, brains us sparse distributed representations. The human neocortex has roughly 100 billion neurons, but at any given time only a small percent are active. The activity of neurons are like bits in a computer, and therefore the representation is sparse.  The CLA also uses SDRs.  A typical implementation of the CLA might have 2048 columns and 64K artificial neurons where as few as 40 might be active at once.  There are many mathematical advantages of using SDRs.  The CLA and the brain could not work otherwise.

<div class="image-wrapper">
  <img alt="Example of a sparse distributed representation in an array of cells" src="{{ site.baseurl }}/images/sdr.png" />
  <p>This diagram represents sparsity: two thousand circles with a small number of red circles active.</p>
</div>

This diagram represents a sparse distributed representation: two thousand circles with a small number of red circles active.

In SDRs, unlike in a dense representations, each bit has meaning. This means that if two vectors have 1s in the same position they are semantically similar in that attrribute. SDRs are how brains solve the problem of knowledge representation that has plagued AI for decades.

For more details about SDRs, watch [this excerpt](http://www.youtube.com/embed/t6NcTdXxVeo) from a talk given by Jeff Hawkins.


Requirements
------------

We're working in providing virtual machines ready to run NuPIC so Windows developers can work on NuPIC within [Virtual Box](https://www.virtualbox.org). Currently, the build requirements are:

* Linux or Unix environment with gnu compilers
* Python 2.6

Project Status
------------------
The code is open source (see [below](#source_code)), as of 03 June, 2013. However, the project is currently in a **one month transition period** before contributions will be seriously accepted. This will give the community a chance to review and understand the source code, as well as Numenta's internal engineers a chance to update their processes to include an open source build.

Starting in July, we will seriously consider incoming Pull Requests on our codebase. In the meantime, minor contributions to our [website source code](https://github.com/numenta/nupic/tree/gh-pages), documentation, wikis, etc. are welcome, as long as they follow the [development workflow](https://github.com/numenta/nupic/wiki/Developer-workflow).

Source Code
-----------
We're rocking [Github](http://github.com/numenta/nupic).


Issue Tracking
--------------
We use JIRA for issue tracking at [issues.numenta.org](http://issues.numenta.org).
