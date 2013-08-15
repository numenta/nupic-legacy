
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
 * Declarations for class Grouper
 */

#ifndef NTA_GROUPER_HPP
#define NTA_GROUPER_HPP

// Used in temporal pooler node
#include <nta/utils/Log.hpp>

#include <nta/math/TAM.hpp>
#include <nta/math/array_algo.hpp>

#include <sstream>


//----------------------------------------------------------------------
namespace nta {
  
  /** 
   * @b Responsibility:
   *  Grouper is the temporal pooler: it discovers temporal dependencies
   *  between spatial coincidences. 
   * 
   * There are two operating modes for the Grouper. Learning is the same in both 
   * modes. However, those two modes do different things in inference.
   * 
   * @b Rationale:
   * 
   * @b Resources/Ownerships:
   * 
   * @b Invariants:
   * 
   * @b Notes:
   */
  class Grouper 
  {
  public:
    typedef UInt size_type;
    typedef Real value_type;

    typedef std::pair<size_type, size_type>           IdxVal;
    typedef SparseMatrix<size_type, value_type>       SM;
    typedef TAM<SparseMatrix<size_type, size_type> >  IntegerTAM;
    typedef TAM<SparseMatrix<size_type, value_type> > FloatTAM;
    typedef IntegerTAM::History                       History;
    typedef std::set<size_type>                       AGroup;
    typedef std::vector<AGroup>                       Groups;
    
    // TBI
    typedef std::vector<value_type>             TBICellOutputs;
    typedef std::vector<TBICellOutputs>         TBICellOutputsVec;
    typedef SparseMatrix<size_type, value_type> TBICellWeights;
    typedef std::vector<TBICellWeights>         TBICellWeightsVec;

    // AHC
    typedef std::pair<size_type, size_type> AMerge;
    typedef std::vector<AMerge>             Merges;

    /**
     * The possible algorithmic modes for the Grouper.
     */
    typedef enum { maxProp, sumProp, tbi, hardcoded } Mode;

    static Mode convertMode(const std::string &name)
    {
      if(name == "0") return maxProp;
      else if(name == "1") return sumProp;
      else if(name == "2") return tbi;
      else if(name == "3") return hardcoded;
      
      else if(name == "maxProp") return maxProp;
      else if(name == "sumProp") return sumProp;
      else if(name == "tbi") return tbi;
      else if(name == "hardcoded") return hardcoded;
      
      else {
        throw std::invalid_argument("'" + name + "' is not a valid "
				    "Grouper mode.");
        return sumProp; // Unused.
      }
    }
    
    static std::string convertMode(Mode mode)
    {
      if (mode == maxProp)
	return std::string("maxProp");
      else if (mode == sumProp)
	return std::string("sumProp");
      else if (mode == tbi)
	return std::string("tbi");
      else if (mode == hardcoded)
	return std::string("hardcoded");

      return std::string("Unknown");
    }
    
    /**
     * Initializes an instance of Grouper.
     *
     * @param transitionMemory [size_type > 0] 
     * @param topNeighbors [size_type > 0]
     * @param maxNGroups [ size_type > 0]
     * @param maxGroupSize [size_type > 0]
     * @param symmetricTam [true|false]
     * @param overlappingGroups [true|false]
     * @param lgp [value_type] large goup penalty
     * @param n_tbis [size_type > 0] number of independent tbis
     * @param mode [maxProp|sumProp|tbi]
     */
    Grouper(size_type transitionMemory, 
	    size_type topNeighbors,
	    size_type maxNGroups,
	    size_type maxGroupSize,
            bool symmetricTam,
	    bool overlappingGroups,
	    value_type ahc_lgp,
            Mode mode,
	    size_type hot_markovOrder =1,
	    double hot_min_cnt2 =0,
	    size_type hot_iterPerStage =0,
	    int hot_maxPerStage =-1,
	    size_type hot_maxCoincidenceSplitsPerRound =0,
	    bool hot_handleSelf = false,
	    size_type n_tbis =1,
	    size_type segmentSize =1,
	    bool rescaleTBI=true);

    /**
     * Constructor from a stream.
     * 
     * @param inStream [std::istream&] the input stream.
     */
    Grouper(std::istream& inStream, size_type n_tbis =1);

    /**
     * Destructor.
     */
    ~Grouper();
    
    /**
     * Return the algorithmic mode of the Grouper. 
     *
     * @retval Mode
     */
    inline Mode getMode() const 
    {
      return mode_; 
    }

    inline std::string getModeStr() const
    {
      return convertMode(mode_);
    }

    /**
     * Set the algorithmic mode of the Grouper.
     */
    inline void setMode(Mode mode) 
    {
      mode_ = mode;
    }

    inline void setModeFromStr(const std::string& str)
    {
      mode_ = Grouper::convertMode(str);
    }

    /**
     * Return history max size.
     * 
     * @retval [size_type > 0]
     */
    inline size_type getTransitionMemory() const 
    { 
      return tam_.getTransitionMemory();
    }

    /**
     * Return top neighbors.
     *
     * @retval [size_type > 0]
     */
    inline size_type getTopNeighbors() const 
    { 
      return topNeighbors_; 
    }
    
    /**
     * Return max group size.
     *
     * @retval [size_type > 0]
     */
    inline size_type getMaxGroupSize() const 
    { 
      return maxGroupSize_; 
    }

    /**
     * Return collapsed history, in terms of original coincidences.
     */
    inline IntegerTAM::History getHistory(size_type baby_idx =0) const 
    { 
      return tam_.getCollapsedHistory(baby_idx);
    }

    /**
     * Return full time adjacency matrix, including
     * states added by HOT.
     */
    inline IntegerTAM& getTam()
    { 
      return tam_; 
    }
      
    /**
     * Collapses HOT added stats onto coincidences.
     */
    inline IntegerTAM getCollapsedTAM() const 
    {
      IntegerTAM ret;
      tam_.HOTCollapse(ret);
      return ret;
    }

    /**
     * Return the TBI cell weights for a particular group.
     */
    inline TBICellWeights& getTBIWeights(size_type grpIdx) 
    { 
      if (tbiCellWeights_.size() == 0)
        tbi_create_();
      
      NTA_CHECK(grpIdx < tbiCellWeights_.size()) 
	<< "Grouper::getTBIWeights: Invalid group index: " << grpIdx
	<< " - Should be < " << tbiCellWeights_.size();
      
      return tbiCellWeights_[grpIdx]; 
    }

    /**
     * Return the TBI cell output values for a particular group.
     */
    inline TBICellOutputs& getTBICellOutputs(size_type grpIdx, size_type tbi_idx =0) 
    { 
      if (tbiCellOutputs_.size() == 0)
        tbi_create_();
	
      NTA_CHECK(grpIdx < tbiCellOutputs_[tbi_idx].size()) 
	<< "Grouper::getTBICellOutputs: Invalid group index: " << grpIdx
	<< " - Should be < " << tbiCellOutputs_[tbi_idx].size();

      return tbiCellOutputs_[tbi_idx][grpIdx]; 
    }
    
    /**
     * Reset the TBI history
     */
    void resetTBIHistory(void);

    /**
     * Return number of groups.
     */
    inline size_type getNGroups() const 
    { 
      return size_type(groups_.size()); 
    }

    /**
     * Finishes initialization of data structures that need
     * to know the number of baby nodes. That includes data
     * structures in TAM (history_, hot_previous_).
     */
    inline void setNTBIs(size_type n_tbis)
    {
      { // Pre-conditions
	NTA_CHECK(n_tbis > 0)
	  << "Grouper::setNTBIs: Invaild value for number of tbis: " << n_tbis
	  << " - Should be >= 0";
      } // End pre-conditions

      n_tbis_ = n_tbis;
      tam_.setNTBIs(n_tbis);
    }

    /**
     * Return groups.
     */
    Groups getGroups(bool collapsed =true) const;

    /**
     * Get list of groups.
     */
    void getGroupsString(std::ostream& buf, bool collapsed =true);

    /**
     * Return whether doing overlapping groups or not.
     */ 
    inline bool isOverlappingGroups() const
    {
      return overlappingGroups_;
    }

    /**
     * Set the overlappingGroups flag.
     */
    inline void setOverlappingGroups(bool b)
    {
      overlappingGroups_ = b;
    }

    /**
     * Return whether time adjacency matrix is symmetric or not.
     */
    inline bool isTamSymmetric() const 
    { 
      return symmetricTam_; 
    }

    /**
     * Set the time adjacency matrix to be symmetric.
     */
    inline void setSymmetricTam(bool b) 
    { 
      symmetricTam_ = b; 
    }

    /**
     * Reset history.
     */
    inline void resetHistory() 
    { 
      tam_.resetHistory();
    }

    /**
     * Reset TAM.
     */
    inline void resetTAM() 
    {
      // tam_.clear();
      tam_.multiply(0);
    }

    /**
     * Set history max size.
     *
     * @param hms [size_type > 0] the new history max size
     */
    inline void setTransitionMemory(size_type hms) 
    { 
      NTA_CHECK(hms > 0)
        << "Grouper::setTransitionMemory: "
        << "Invalid transition memory size: " << hms
        << " - Expecting value > 0";

      tam_.setTransitionMemory(hms);
    }

    /**
     * Set the top neighbors parameter.
     *
     * @param tn [size_type > 0] the new top neighbors parameter
     */
    inline void setTopNeighbors(size_type tn) 
    { 
      NTA_CHECK(tn > 0)
        << "Grouper::setTopNeighbors: "
        << "Invalid top neighbors value: " << tn
        << " - Expecting value > 0";

      topNeighbors_ = tn; 
    }

    inline size_type getSegmentSize() const
    {
      return segmentSize_;
    }

    /**
     * Set the max group size.
     *
     * @param mgs [size_type > 0] the new max group size
     */
    inline void setMaxGroupSize(size_type mgs) 
    { 
      NTA_CHECK(mgs > 0)
        << "Grouper::setMaxGroupSize: "
        << "Invalid max group size: " << mgs
        << " - Expecting value > 0";
      maxGroupSize_ = mgs; 
    }

    /**
     * Reset Grouper.
     */
    void resetGroups();

    /**
     * The method called when learning.
     */
    template <typename InIter, typename OutIter>
    void learn(InIter begin1, OutIter begin2, size_type baby_idx =0);

    /**
     * The method called when inferring.
     */
    template <typename InIter, typename OutIter>
    void infer(InIter begin1, InIter end1, OutIter begin2, size_type baby_idx =0);

    template <typename InIter, typename OutIter>
    void tbiInfer(InIter begin1, InIter end1, OutIter begin2, 
		  TBICellOutputsVec::iterator);

    template <typename InIter1, typename InIter2, typename OutIter>
    void topDownInfer(InIter1 bu_in, InIter1 bu_in_end, 
		      InIter2 td_in, InIter2 td_in_end, 
		      OutIter td_out, OutIter td_out_end);

    bool getRescaleTBI() const { return rescaleTBI_; }
    void setRescaleTBI(bool b) { rescaleTBI_ = b; }

    /**
     * Removes from the TAM the rows and columns corresponding to 
     * the coincidences listed in del.
     *
     * @param del [std::vector<size_type>] the list of coincidences to 
     *  remove from the TAM
     */
    void pruneCoincidences(const std::vector<size_type>& toDelete);

    /**
     * Grouping is a separate step that happens after learning 
     * and just before inference.
     */
    void group(const std::vector<IdxVal>& counts);

    /**
     * Set large group penalty for AHC algorithm.
     */
    inline void setAHCLargeGroupPenalty(value_type lgp)
    {
      {
	NTA_CHECK(lgp > 0)
	  << "Grouper::setAHCLargeGroupPenalty: "
	  << "Invalid large group penalty: " << lgp
	  << " - Should be > 0";
      }

      lgp_ = lgp;

      if (tam_.nRows() > 0)
	AHCGroup(groups_.size());
    }

    /**
     * Get large group penalty for AHC algorithm.
     */
    inline value_type getAHCLargeGroupPenalty() const
    {
      return lgp_;
    }

    inline void setAHCNGroups(size_type nGroups)
    {
      groups_from_merges_(nGroups);
    }

    /**
     * Return merges.
     */
    inline const Merges& getAHCMerges() const
    {
      return merges_;
    }

    /**
     * Group using AHC algorithm.
     */
    void AHCGroup(size_type nGroups);

    /**
     * Saves the state of this instance to ouStream.
     */
    void saveState(std::ostream& outStream) const;

    /**
     * Reads the state of this instance from inStream.
     */
    void readState(std::istream& inStream);

    /**
     * Not documented, don't use.
     */
    void setTAMFromCSR(std::istream& inStream)
    {
      tam_.fromCSR(inStream);
    }

    /**
     * Even less documented. Definitely don't use.
     */
    void setTAMStateFromCSR(std::istream& inStream)
    {
      tam_.readState(inStream);
    }

    void setMaxNGroups(size_type maxNGroups)
    {
      NTA_CHECK(groups_.size() <= maxNGroups)
	<< "Grouper::setMaxNGroups(): "
	<< "The current parameters generated " << groups_.size()
	<< " groups, which exceeds the maximum of "
	<< maxNGroups << " groups.";
      
      maxNGroups_ = maxNGroups;
    }

    inline void hot(size_type nRounds, value_type min_cnt2, int max)
    {
      tam_.setHOTNRounds(nRounds);
      tam_.setHOTMinCnt2(min_cnt2);
      tam_.setHOTMaxPerStage(max);
      tam_.hot();
    }

    //--------------------------------------------------------------------------------
    // Sampling / Prediction
    //--------------------------------------------------------------------------------

    typedef std::vector<value_type> Sequence;
    typedef std::vector<Sequence> Sequences;

    typedef enum 
      { 
	distribution, 
	single_path_max, 
	single_path_sample 
      } SamplingMode;

    void sampleFromGroup(size_type grp_idx,
			 SamplingMode, 
			 const std::vector<value_type>& initial_dist, 
			 Sequences& future) const;

    typedef enum 
      {
	coincidences,
	groups
      } PredictionMode;

    void predict(size_type tbi_idx, PredictionMode, Sequences& future);

    //--------------------------------------------------------------------------------

  private:
    Mode mode_; // maxProp, sumProp, tbi
    bool symmetricTam_;
    size_type topNeighbors_;
    size_type maxNGroups_;
    size_type maxGroupSize_;
    bool overlappingGroups_;
    bool rescaleTBI_;
    IntegerTAM tam_; 
    Groups groups_;
    SM weights_;
    
    void available_neighbors_(size_type, const IntegerTAM&, const AGroup&, 
			      const std::vector<IdxVal>&, std::vector<size_type>&);
    
    // TBI
    size_type n_tbis_;
    TBICellWeightsVec tbiCellWeights_;  // One cellWeight matrix for each group
    std::vector<TBICellOutputsVec> tbiCellOutputs_; // one set of outputs for each group
    TBICellOutputs tbiBuffer_; // working buffer, pre-allocated for speed
    TBICellOutputsVec tbiPredBuf_; // prediction

    void tbi_create_();
    void tbi_delete_();

    // AHC
    typedef std::vector<size_type> AHC_Group;
    typedef std::vector<AHC_Group> AHC_Groups;
    
    value_type lgp_; // large group penalty for AHC grouping
    Merges merges_;

    void ahc_update_(size_type, value_type&, const AHC_Groups&, 
		     const FloatTAM&, FloatTAM&, std::vector<value_type>&);
    void groups_from_merges_(size_type nGroups);
    void finish_grouping_(const std::vector<value_type>&);

    size_type segmentSize_;
    
    friend class GrouperUnitTest;

    NO_DEFAULTS(Grouper);
  }; // end class Grouper

  //----------------------------------------------------------------------

} // end namespace nta

#include <nta/algorithms/Grouper_t.hpp>

#endif // NTA_GROUPER_HPP
