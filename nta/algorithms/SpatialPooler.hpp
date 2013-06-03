/*
 * ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
 * Numenta, Inc. a separate commercial license for this software code, the
 * following terms and conditions apply:
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses.
 *
 * http://numenta.org/licenses/
 * ---------------------------------------------------------------------
 */

/** @file 
 * Definition for SpatialPooler class
 */

#ifndef NTA_SPATIAL_POOLER_HPP
#define NTA_SPATIAL_POOLER_HPP

#include <nta/math/NearestNeighbor.hpp>
#include <nta/math/SparseMatrix01.hpp>

//----------------------------------------------------------------------
namespace nta {

  /** 
   * @b Responsibility:
   *  This is a spatial pooler. It can be learning, or infering.
   *  In learning mode, the spatial pooler's responsibility is to remember
   *  the vectors it receives in input as spatial coincidences. 
   *  In inference mode, the spatial pooler's responsibility is to output
   *  the most likely current coincidence, or an appropriate mixture
   *  of coincidences, depending on the Mode. 
   *
   * @b Details:
   *  
   *
   * @b Rationale:
   *  This is a building block for algorithms that are place inside Nodes.
   * 
   * @b Resources/Ownerships:
   *  This class owns a coincidence matrix, W.
   * 
   * @b Invariants:
   * 
   */
  class SpatialPooler 
  {
  public:

    /**
     * The possible algorithmic modes for the SpatialPooler.
     */
    typedef enum { dot, product, gaussian, dot_maxD, product_maxD } Mode;
    
    static Mode convertMode(const std::string &name)
    {
      if (name == "0" || name == "dot") return dot;
      else if(name == "1" || name == "product") return product;
      else if(name == "2" || name == "gaussian") return gaussian;
      else if(name == "3" || name == "dot_maxD") return dot_maxD;
      else if(name == "4" || name == "product_maxD") return product_maxD;
      else {
        throw std::invalid_argument("'" + name + "' is not a valid "
          "SpatialPooler mode.");
        return product; // Unused.
      }
    }

    /**
     * Initializes an instance of SpatialPooler.
     * The boundaries are the cumulative sizes of the output of the 
     * children nodes.
     * The boundaries need to be passed in strictly increasing order.
     * No child output element count can be zero.
     * 
     * @param boundaries [std::vector<UInt>] the cumulative sizes 
     *  of the inputs from each child
     * @param mode [Mode] the algorithmic mode
     * @param var [Real > 0] the variance for the gaussians
     * @param maxD [Real >= 0] the max distance parameter
     *
     * @b Exceptions:
     *  @li Boundaries not in strictly increasing order.
     *  @li Zero width child output.
     *  @li If var <= 0.
     *  @li If maxD < 0.
     */
    SpatialPooler(const std::vector<UInt>& boundaries, 
                  Mode mode, Real var, Real maxD, bool prodModeScaling=true);

    /**
     * Constructor from a stream.
     */
    SpatialPooler(std::istream& inStream);

    /**
     * Deletes the memory allocated for the coincidence matrix (W).
     */
    ~SpatialPooler();

    /**
     * Returns the algorithmic mode of the SpatialPooler.
     */
    inline Mode getMode() const
    {
      return mode_;
    }

    /**
     * Set the algorithmic mode of the SpatialPooler. 
     *
     * @param mode [Mode] the algorithmic mode
     */
    inline void setMode(Mode mode) 
    {
      mode_ = mode;
    }

    /**
     * Returns the size of the input vectors.
     * 
     * @retval UInt [ > 0 ] size of the input vectors
     */
    inline UInt getInputSize() const 
    { 
      return boundaries_[boundaries_.size()-1];
    }

    /**
     * Returns a pointer to the coincidence matrix W.
     * Throws an exception if the mode is dot or product
     * 
     * @retval SparseMatrix<UInt, Real>* [ ! NULL ] the coincidence matrix pointer
     *
     * @b Exceptions:
     *  @li If mode is dot or product.
     */
    inline NearestNeighbor<SparseMatrix<UInt, Real> >* getW() const 
    { 
      NTA_CHECK(W_ != NULL)
        << "SpatialPooler::getW(): "
        << "No W matrix (try getW01)";
      return W_; 
    }

    /**  
     * Returns a pointer to the coincidence matrix W01.
     * Throws an exception if called when the mode is gaussian. 
     * 
     * @retval SparseMatrix01<UInt, Real>* [ ! NULL ] the coincidence matrix pointer
     *
     * @b Exceptions:
     *  @li If mode is gaussian.
     */
    inline SparseMatrix01<UInt, Real>* getW01() const 
    { 
      NTA_CHECK(W01_ != NULL)
        << "SpatialPooler::getW01(): "
        << "No W01 matrix (try getW)";
      return W01_; 
    }

    /**
     * Return the number of coincidences found so far.
     * The number of coincidences is the size of the 
     * output vectors for the spatial pooler.
     * 
     * @retval UInt [ >= 0] the number of coincidences
     */
    inline UInt getNCoincidences() const 
    {
      if (W_)
        return W_->nRows();
      else if (W01_)
        return W01_->nRows();
      else {
        NTA_WARN << "SpatialPooler::getNCoincidences(): "
                 << "No coincidence yet";
        return 0;
      }
    }

    /**
     * Outputs the coincidence matrix to a stream.
     *
     * @param buf [std::ostream&] the stream
     * @param full [bool =false] whether the full representation
     *    should be used for the W01 coincidence matrix
     * @param dense [bool =false] whether the coincidence matrix
     *    should be output as a dense matrix
     */
    inline void getCoincidenceMatrix(std::ostream& buf, bool full =false, 
                                     bool dense =false) const
    {
      if (W_) {
        if (dense)
          W_->print(buf);
        else
          W_->toCSR(buf);
      } else if (W01_) {
        if (dense)
          W01_->print(buf);
        else if (full) 
          W01_->toCSRFull(buf);
        else 
          W01_->toCSR(buf);
      } else {
        NTA_WARN << "SpatialPooler::getCoincidenceMatrix(): "
                 << "No coincidence yet";
      }
    }

    /**
     * Set variance when the pooler is in gaussian mode.
     */
    inline void setVariance(const Real& v)
    {
      if (mode_ != gaussian) 
        NTA_WARN << "Seting pooler's variance "
                 << "but pooler is not in gaussian mode";

	  k2_ = (Real) -.5/(v*v);
    }

    /**
     * Get the variance, in gaussian mode, 0 otherwise.
     * See setVariance().
     *
     * @retval Real [ > 0 ] variance
     */
    inline Real getVariance() const
    {
      if (mode_ != gaussian) 
        NTA_WARN << "Getting pooler's variance "
                 << "but pooler is not in gaussian mode";
	  nta::Sqrt<Real> s;
	  return s(Real(-.5)/k2_);
    }

    /**
     * Set maxDistance parameter.
     * This parameter is used when deciding whether to 
     * introduce a new quantization point or whether to 
     * increment the count of an already existing 
     * quantization point, in modes:
     * dot_maxD, product_maxD and gaussian.
     *
     * @param maxD [Real >= 0] the max distance
     */
    inline void setMaxD(const Real& maxD)
    {
      NTA_CHECK(maxD >= 0)
	<< "SparseMatrix01::setMaxD(): "
	<< "Max distance needs to be >= 0, "
	<< "but passed: " << maxD;
      
      maxDistance_ = maxD;
    }

    /**
     * Get maxDistance parameter.
     * See setMaxD().
     *
     * @retval Real [ >= 0 ] maxDistance
     */
    inline Real getMaxD() const
    {
      return maxDistance_;
    }

    /**
     * Set prodModeScaling parameter.
     * This parameter is used enable/disable scaling in product mode
     *
     * @param on [bool] the prodModeScaling boolean
     */
    inline void setProdModeScaling(bool on)
    {
      prodModeScaling_ = on;
    }

    /**
     * Get prodModeScaling parameter.
     * See setProdModeScaling().
     *
     * @retval bool prodModeScaling
     */
    inline bool getProdModeScaling() const
    {
      return prodModeScaling_;
    }

    /**
     * Experimental. Returns scale that was used in scaling
     * in product mode. Might not be supported forward.
     */
    inline Real getScale() const
    {
      return scale_;
    }

    /**
     * Data structure used to represent the row counts.
     * Row counts are coincidence counts: how many times
     * each coincidences has been seen so far.
     * Each pair in the vector contains the index and the count
     * of each coincidence.
     */
    typedef std::vector<std::pair<UInt, UInt> > RowCounts;
    
    /**
     * Return the coincidence counts.
     * 
     * @retval [RowCounts] the coincidence counts
     */
    RowCounts getRowCounts() const;

    /**
     * Output the coincidence counts to a stream
     *
     * @param buf [std::ostream] the buffer
     */
    inline void getRowCounts(std::ostream& buf) const
    {
      SpatialPooler::RowCounts counts = getRowCounts();
      buf << counts.size() << " ";
      for (UInt i = 0; i < counts.size(); ++i)
        buf << counts[i].first << " " << counts[i].second << " ";
    }

    /**
     * Learns coincidences.
     *
     * The size of the input and output vectors are inferred from the sizes
     * of internal data structures: the size of the input vector should be 
     * the last element of the boundaries_ array, and the size of the output
     * vector is the number of coincidences learnt so far, that is, the number
     * of rows in the coincidence matrix W_. The size of the inputs is fixed 
     * and is also the number of columns of the W_ matrix.
     *
     * Learning consists in reducing the input vector for each child to a binary
     * vector containing a single one for the highest frequency, and storing
     * that vector into the W_ matrix if it's not been seen yet. A count of how
     * many times each vector is seen is also kept. 
     * 
     * @param begin1 [InIter] iterator to the beginning of the input vector
     * @param begin2 [OutIter] iterator the beginning of the input vector
     */
    template <typename InIter, typename OutIter>
    UInt learn(InIter begin1, OutIter begin2);

    /**
     * Infers.
     * 
     * There are 2 modes of inference available, as set by the setInferenceMode()
     * method, inferDot and inferProduct. The default is inferDot. For inference,
     * the input vector needs to have the same number of columns as the W_ matrix.
     *
     * The inferDot mode of inference consists in multiplying the coincidence matrix 
     * W_ by the input vector on the right side
     *
     * The inferProduct mode of inference consists of the following:
     * for each child in the input (as determined by the boundaries vector) we compute
     *  inferDot[childIndex] from inputChildOnly, where inputFromChildIndex is a copy 
     *    of the input vector where only the elements from that child are non-zero. 
     *   i.e: inferDot[childIndex] = W_ * inputFromChildIndex
     *
     * Then, we element by element multiply each of the inferDot[childIndex]'s to
     * get the output vector. This has the effect of making the output probablity
     * distribution sharper. For example, if any child input has a 0 correlation for
     * a coincidence row in the W matrix, then the entire coincidence will have a 0
     * probablity in the output. 
     *
     * @param begin1 [InIter] iterator to the beginning of the input vector
     * @param begin2 [OutIter] iterator the beginning of the input vector
     * @param blank  [Real*] pointer to the current blank value
     */
    template <typename InIter, typename OutIter>
    void infer(InIter begin1, OutIter begin2, Real* blank=0);

    /**
     * Checks whether the current input vector is a blank or not.
     * The way blanks are determined depends on the algorithmic mode.
     *
     * @param begin1 [InIter] iterator to the beginning of the input vector
     * @retval [bool] true if the input vector is a blank, false otherwise
     */
    template <typename InIter>
    bool checkBlank(InIter begin1) const;

    /**
     * Returns the score of the current input vector as a blank.
     * The way this score is computed depends on the algorithmic mode.
     *
     * @param begin1 [InIter] iterator to the beginning of the input vector
     * @retval [Real] the score of the input vector as a blank
     */
    template <typename InIter>
    Real blankScore(InIter begin1) const;

    /**
     * Removes from the coincidence list all the coincidences whose
     * count is less than threshold. The deleted coincidences are 
     * returned in del.
     *
     * @param threshold [UInt > 0] the threshold
     * @param del [std::vector<UInt>] the list of deleted coincidences
     */
    void pruneCoincidences(const UInt& threshold, std::vector<UInt>& del); 

    /**
     * Save class data to stream.
     *
     * @param state [std::ostream] the stream to write to
     *
     * @b Exceptions:
     *  @li Bad stream.
     */
    void saveState(std::ostream& state) const;

    /**
     * Read class data from stream.
     *
     * @param state [std::istream] the stream to read from
     *
     * @b Exceptions:
     *  @li Bad stream.
     *  @li If child output size == 0.
     *  @li If children cumulative output sizes are not passed in
     *      strictly increasing order.
     *  @li If number of rows of coincidence matrix is < 0.
     *  @li If number of columns of coincidence matrix is <= 0.
     *  @li If number of columns of coincidence matrix doesn't
     *      match cumulative output size of the children.
     */
    void readState(std::istream& state);

    /**
     * Return the child boundaries used by this SpatialPooler.
     *
     * @retval boundaries [std::vector<nta::UInt] the child boundaries
     *
     */
    const std::vector<nta::UInt>& getBoundaries() const
    {
      return boundaries_;
    }

    void resetCounts(UInt prior=0)
    {
      size_t n = counts_.size();
      counts_.clear();
      counts_.resize(n, prior);
    }

  private:
    Mode mode_;
	Real maxDistance_;
	Real k2_;
	std::vector<nta::UInt> boundaries_;
    NearestNeighbor<SparseMatrix<UInt, Real> >* W_; 
    SparseMatrix01<UInt, Real>* W01_;
    std::vector<UInt> counts_;
	Real scale_;
    bool prodModeScaling_;

    friend class SpatialPoolerUnitTest;

    NO_DEFAULTS(SpatialPooler);
  }; // end class SpatialPooler

  //----------------------------------------------------------------------

} // end namespace nta

#include <nta/algorithms/SpatialPooler_t.hpp>

#endif // NTA_SPATIAL_POOLER_HPP



