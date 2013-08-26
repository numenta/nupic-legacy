
# The Cortical Learning Algorithm (CLA)

## Online Learning

Most machine learning techniques are relatively static.  A model is constructed from a training data set, verified on a testing data set, and then applied to real-world data. However the patterns and structure in the world changes over time. Therefore previously accurate models must be regularly retrained with new data, repeating the time and expense of the original process.

The CLA on the other hand is an online learning system.  It does not require conventional training and testing data sets. Instead, the CLA learns continuously with each new data point.  The CLA is constantly making predictions which are continually verified as more data arrives.  As the underlying patterns in the data change the CLA adjusts accordingly.  An online learning system such as the CLA forces you to think about many things differently than you do with algorithms that relay on static training data sets.

## Sparse Distributed Representations

Computers store information in “dense” representations such as a 32 bit word where all combinations of 1s and 0s are possible.

By contrast, brains use sparse distributed representations. The human neocortex has roughly 100 billion neurons, but at any given time only a small percent are active. The activity of neurons are like bits in a computer, and therefore the representation is sparse.  The CLA also uses SDRs.  A typical implementation of the CLA might have 2048 columns and 64K artificial neurons where as few as 40 might be active at once.  There are many mathematical advantages of using SDRs.  The CLA and the brain could not work otherwise.

<div class="image-wrapper">
  <img alt="Example of a sparse distributed representation in an array of cells" src="{{ site.baseurl }}/images/sdr.png" />
  <p>This diagram represents sparsity: two thousand circles with a small number of red circles active.</p>
</div>

This diagram represents a sparse distributed representation: two thousand circles with a small number of red circles active.

In SDRs, unlike in a dense representations, each bit has meaning. This means that if two vectors have 1s in the same position they are semantically similar in that attribute. SDRs are how brains solve the problem of knowledge representation that has plagued AI for decades.

For more details about SDRs, watch <a href="http://www.youtube.com/watch?v=t6NcTdXxVeo" rel="prettyPhoto" title="">this excerpt</a> from a talk given by Jeff Hawkins.
