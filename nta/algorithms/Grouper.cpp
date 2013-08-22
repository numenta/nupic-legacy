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
 * Implementation for class Grouper
 */

#include <iomanip>

#include <nta/algorithms/Grouper.hpp>
#include <nta/math/array_algo.hpp>

using namespace std;

namespace nta {   

  //--------------------------------------------------------------------------------
  Grouper::Grouper(size_type transitionMemory, 
                   size_type topNeighbors,
		   size_type maxNGroups,
		   size_type maxGroupSize,
                   bool symmetricTam, 
		   bool overlappingGroups,
		   value_type ahc_lgp,
                   Mode mode,
		   size_type hot_markovOrder,
		   double hot_min_cnt2,
		   size_type hot_iterPerStage,
		   int hot_maxPerStage,
		   size_type hot_maxCoincidenceSplitsPerRound,
		   bool hot_handleSelf,
		   size_type n_tbis,
		   size_type segmentSize,
		   bool rescaleTBI)
    : mode_(mode),
      symmetricTam_(symmetricTam),
      topNeighbors_(topNeighbors),
      maxNGroups_(maxNGroups),
      maxGroupSize_(maxGroupSize),
      overlappingGroups_(overlappingGroups),
      rescaleTBI_(rescaleTBI),
      tam_(0,0,
	   transitionMemory,
	   hot_markovOrder,
	   hot_min_cnt2,
	   hot_iterPerStage,
	   hot_maxPerStage,
	   hot_maxCoincidenceSplitsPerRound,
	   hot_handleSelf),
      groups_(),
      weights_(),
      n_tbis_(n_tbis),
      tbiCellWeights_(),
      tbiCellOutputs_(),
      tbiBuffer_(),
      tbiPredBuf_(),
      lgp_(ahc_lgp),
      merges_(),
      segmentSize_(segmentSize)
  {     
    const char* where = "Grouper::Grouper(<parameters>): ";
/*
    NTA_CHECK(topNeighbors > 0)
      << where
      << "Invalid top neighbors: " << topNeighbors
      << " - Top neighbors should be > 0";
    
    NTA_CHECK(maxNGroups > 0)
      << where
      << "Invalid max number of groups: " << maxNGroups
      << " - Max number of groups should be > 0";

    NTA_CHECK(maxGroupSize > 0)
      << where
      << "Invalid max group size: " << maxGroupSize
      << " - Max group size should be > 0";

    NTA_CHECK(n_tbis >= 0)
      << where
      << "Invalid number of tbis: " << n_tbis
      << " - Should be >= 0";
*/
  }

  //--------------------------------------------------------------------------------
  Grouper::Grouper(std::istream& inStream, size_type n_tbis)
    : mode_(sumProp),
      symmetricTam_(false),
      topNeighbors_(1),
      maxNGroups_(1),
      maxGroupSize_(9999),
      overlappingGroups_(false),
      rescaleTBI_(true),
      tam_(),
      groups_(),
      weights_(),
      n_tbis_(n_tbis),
      tbiCellWeights_(),
      tbiCellOutputs_(),
      tbiBuffer_(),
      tbiPredBuf_(),
      lgp_(0),
      merges_(),
      segmentSize_(1)
  {
/*
    readState(inStream);
*/
  }

  //--------------------------------------------------------------------------------
  Grouper::~Grouper()
  { 
  }

  //--------------------------------------------------------------------------------
  // TBI
  //--------------------------------------------------------------------------------
  void Grouper::tbi_create_()
  { 
/*
    // Delete current data, if any
    tbi_delete_();
    
    // tam2 contains our tam, adjusted to be symmetric if requested
    IntegerTAM tam2(tam_);

    if (symmetricTam_) 
      tam_.addToTranspose(tam2);

    // For each group, extract a 'mini-TAM' corresponding to 
    // the entries in that group. The mini-TAMs are square.
    // The size of the mini-TAM is the size of the correspondign group.
    // We normalize along the columns. In the TAM, we have time t-1
    // across the top, and time t across the rows, so normalizing along
    // the columns means that when we transition from t-1 to t, we 
    // have to be in one of the coincidences at t. It doesn't take into
    // account the probability of exiting the group. 
    // We can also skip the creation of the small tams altogether if 
    // we had a special mat vec prod operation that takes indices
    // of which columns to multiply (and indices of rows to consider too). 
    tbiCellWeights_.resize(groups_.size());
    Groups::const_iterator g = groups_.begin();
    TBICellWeightsVec::iterator w = tbiCellWeights_.begin();

    for (; g != groups_.end(); ++g, ++w) {
      tam2.getOuter(*g, *g, *w);
      w->normalizeCols();
    }

    // Allocate space for the cell outputs:
    // tbiCellOutputs is a two dimensional "array:, with nrows = ngroups
    // and ncols = ncoincidences, basically.
    // We use a vector of vector because each group has a different
    // number of coincidences.
    // It represents the joint pdf (group, coincidence).
    tbiCellOutputs_.resize(n_tbis_);
    for (size_type i = 0; i != tbiCellOutputs_.size(); ++i) {
      tbiCellOutputs_[i].resize(groups_.size());
      size_type j = 0;
      for (g = groups_.begin(); g != groups_.end(); ++g, ++j) 
	tbiCellOutputs_[i][j].resize(g->size(), (value_type) 0.0);
    }

    // We size the buffer to the largest group size.
    size_type reqBufSize = (size_type) 0;
    for (g = groups_.begin(); g != groups_.end(); ++g) 
      reqBufSize = std::max((size_type) g->size(), reqBufSize);

    tbiBuffer_.resize(reqBufSize, (value_type) 0.0);
*/
  }

  //--------------------------------------------------------------------------------
  void Grouper::tbi_delete_()
  {
/*
    tbiCellWeights_.clear();
    tbiCellOutputs_.clear();
    tbiBuffer_.clear();
*/
  }

  //--------------------------------------------------------------------------------
  /**
   * Resets TBI cell outputs to 0.
   */
  void Grouper::resetTBIHistory(void)
  { 
/*
    // If we haven't formed the TBI structures yet, nothing to do
    if (tbiCellWeights_.size() == 0)
      return;
      
    for (size_type i = 0; i != tbiCellOutputs_.size(); ++i) {
      for (size_type j = 0; j != tbiCellOutputs_[i].size(); ++j) {
	TBICellOutputs& cells = tbiCellOutputs_[i][j];
	std::fill(cells.begin(), cells.end(), (value_type)0.0);
      }
    }
*/
  }

  //--------------------------------------------------------------------------------
  // END TBI
  //--------------------------------------------------------------------------------

  //--------------------------------------------------------------------------------
  void Grouper::resetGroups()
  {
/*
    resetHistory();
    groups_.clear();
    weights_.resize(0,0);
    tbi_delete_();
*/
  }

  //--------------------------------------------------------------------------------
  Grouper::Groups Grouper::getGroups(bool collapsed) const
  {
    if (!collapsed || !tam_.usesHOT())
      return groups_;

    Grouper::Groups slimGroups; // without HOT states
/*
    // Trim groups by keeping only roots of HOT states
    for (size_type i = 0; i != groups_.size(); ++i) {
      AGroup agroup;
      Grouper::AGroup::const_iterator it;
      for (it = groups_[i].begin(); it != groups_[i].end(); ++it)
	agroup.insert(tam_.getHOTCoincidence(*it));
      slimGroups.push_back(agroup);
    }
 */   
    return slimGroups;
  }

  //--------------------------------------------------------------------------------
  void Grouper::getGroupsString(std::ostream& buf, bool collapsed)
  {   
/*
    const Grouper::Groups groups = getGroups(collapsed);
    buf << groups.size() << endl;
    for (size_type i = 0; i != groups.size(); ++i) {
      buf << groups[i].size() << " ";
      AGroup::const_iterator it;
      for (it = groups[i].begin(); it != groups[i].end(); ++it)
        buf << *it << " ";
      buf << endl;
    }
*/
  }

  //--------------------------------------------------------------------------------
  template <typename IdxVal>
  struct NonZeroOrder
  {
    typedef typename IdxVal::first_type size_type;

    NonZeroOrder(const vector<IdxVal>& counts)
      : counts_(counts) 
    {}

    const vector<IdxVal>& counts_;

    inline bool operator()(const IdxVal& p1, const IdxVal& p2) const
    {
      size_type val = 4;

      if (p1.second > p2.second)
        val = 1;
      else if (p1.second == p2.second) {
        if (counts_[p1.first].second > counts_[p2.first].second) 
          val = 2;
        else if (counts_[p1.first].second == counts_[p2.first].second)
          if (p1.first < p2.first)
            val = 3;
      }

      return val < 4;
    }
  };

  //--------------------------------------------------------------------------------
  struct SeedsOrder 
    : public std::binary_function<Grouper::IdxVal, Grouper::IdxVal, bool>
  {
    inline bool operator()(const Grouper::IdxVal& p1, const Grouper::IdxVal& p2) const
    {
      if (p1.second > p2.second) 
        return true;
      else if (p1.second == p2.second)
        return p1.first < p2.first;
      return false;
    }      
  };

  //--------------------------------------------------------------------------------
  void Grouper::pruneCoincidences(const std::vector<size_type>& toDelete)
  {
/*
    tam_.deleteRows(toDelete.begin(), toDelete.end());
    tam_.deleteCols(toDelete.begin(), toDelete.end());
    resetHistory();
*/
  }

  //--------------------------------------------------------------------------------
  void Grouper::available_neighbors_(size_type cur, const IntegerTAM& tam2, 
				     const AGroup& alreadyGrouped,
				     const vector<IdxVal>& sortedCounts,
				     std::vector<size_type>& neighbors)
  {
/*
    list<IdxVal> row;
    tam2.getRowToSparse(cur, back_inserter(row));
    if (!alreadyGrouped.empty())
      row.remove_if(IsIncluded<AGroup, select1st<IdxVal> >(alreadyGrouped));
    row.sort(NonZeroOrder<IdxVal>(sortedCounts));
    row.resize(min(size_type(row.size()), topNeighbors_));
    neighbors.clear();
    transform(row.begin(), row.end(), back_inserter(neighbors), select1st<IdxVal>());
*/
  }

  //--------------------------------------------------------------------------------
  /**
   * Counts come in possibly unsorted, not even by index number.
   */
  void Grouper::group(const vector<IdxVal>& counts)
  {      
/*
    const char* where = "Grouper::group(): ";

    // tam2 contains our tam, adjusted to be symmetric if requested
    IntegerTAM tam2(tam_);
    if (symmetricTam_) 
      tam_.addToTranspose(tam2);

    // Clear out the old vector of groups and tbi info, 
    // and cache the number of coincidences
    size_type nCoincidences = (size_type) counts.size();
    groups_.clear();  
    tbi_delete_();
     
    // ranks contains the counts, sorted with the highest count first. Each entry is
    //  a pair containing <coincIdx, coincCount>
    vector<IdxVal> ranks(counts);
    stable_sort(ranks.begin(), ranks.end(), SeedsOrder());

    // sortedCounts is a vector of the counts sorted by coincidence index, 
    //  the i'th entry containing <coincIdx=i, coincCount>
    vector<IdxVal> sortedCounts(counts.size());
    for (size_type i = 0; i < counts.size(); ++i)
      sortedCounts[counts[i].first] = counts[i];

    list<size_type> front, nextFront; 
    AGroup alreadyGrouped, neighborSet;
    vector<size_type> neighbors;
    vector<size_type>::iterator n;

    size_type i, cur, nmax, seed;

    for (i = 0; i < nCoincidences; ++i) {
      // Get the coincidence index of the coincidence with the highest count
      seed = ranks[i].first;
      
      // Skip if this coincidence was already grouped
      if (alreadyGrouped.find(seed) != alreadyGrouped.end())
        continue;
      
      // Start formation of a new set of neighbors, using 'seed' to start
      neighborSet.clear();
      neighborSet.insert(seed);
        
      // The general idea here is 'front' contains the coincidences we have just
      //  inserted into the group and 'nextFront' is the set of coincidences that
      //  are topNeighbors of each of the elements of 'front' 
      // Once we have collected all of the topNeighbors of 'front' and generated 
      // 'nextFront',
      //  we insert them into the group, and then iterate again, setting 'front' to
      //  be the 'nextFront' we just calculated. 
      nextFront.push_back(seed);
      while (!nextFront.empty()) {
        front.swap(nextFront);
        nextFront.clear();
        nmax = std::max(maxGroupSize_ - (size_type)neighborSet.size(), (size_type)0); 
        while (!front.empty() && nextFront.size() < nmax) {
          cur = front.front();
          front.pop_front();
          
          // This function sets 'neighbors' to contain up to 'topNeighbors_' concidences
          //  with the highest counts from the 'cur' row of the tam. That is, 
	  // the coincidences most likely to precede the 'cur' coincidence. 
	  available_neighbors_(cur, tam2, alreadyGrouped, sortedCounts, neighbors);
          for (n = neighbors.begin(); n != neighbors.end() && nextFront.size() < nmax; ++n) 
            {
              size_type elt = *n;
              if (neighborSet.find(elt) == neighborSet.end()
                  && find(nextFront.begin(), nextFront.end(), elt) == nextFront.end()) {
                nextFront.push_back(elt);
              }
            } // neighbors
        } // ! front.empty()
        neighborSet.insert(nextFront.begin(), nextFront.end()); 
      } // ! nextFront.empty()
      alreadyGrouped.insert(neighborSet.begin(), neighborSet.end());
      groups_.push_back(neighborSet);
    }

    Groups::iterator git;   
    AGroup::iterator e;

    // --------------------------------------------------------------------------------
    // Adjust the groups to be overlapping, if requested. 
    // We do this by adding to the existing groups, ALL coincidences that are within
    // topNeighbors of the current members.
    if (overlappingGroups_) {
      alreadyGrouped.clear();
      for (git = groups_.begin(); git != groups_.end(); ++git) {
        AGroup fringe;
        for (e = git->begin(); e != git->end(); ++e) {
          available_neighbors_(*e, tam2, alreadyGrouped, sortedCounts, neighbors);
          for (i = 0; i < neighbors.size(); ++i)
            fringe.insert(neighbors[i]);
        }
        for (AGroup::iterator it = fringe.begin(); it != fringe.end(); ++it)
          git->insert(*it);
      }
    }

    NTA_CHECK(groups_.size() <= maxNGroups_)
      << where << "The current parameters generated " << groups_.size()
      << " groups, which exceeds the maximum of "
      << maxNGroups_ << " groups.";

    vector<value_type> coincidence_counts(counts.size());
    for (size_type i = 0; i != counts.size(); ++i)
      coincidence_counts[counts[i].first] = value_type(counts[i].second);

    finish_grouping_(coincidence_counts);
*/
  }

  //--------------------------------------------------------------------------------
  /**
   * Compute weights matrix for inference.
   * This contains a row for each group. Each row contains non-zero weights in the 
   *  columns corresponding to members of the group. The weight for each member
   *  is set according to the frequency count of that coincidence. 
   */
  void Grouper::finish_grouping_(const vector<value_type>& counts)
  {
/*
    const size_type n_coincidences = tam_.nRows(); // not HOT!
    weights_.resize(groups_.size(), n_coincidences, true);
    vector<value_type> row(n_coincidences);
   
    Groups::const_iterator g = groups_.begin(), g_end = groups_.end();
    for (size_type row_idx = 0; g != g_end; ++g, ++row_idx) {
      fill(row, (value_type) 0);
      AGroup::const_iterator e = g->begin(), e_end = g->end();
      for (; e != e_end; ++e) 
	row[*e] = counts[*e];
      weights_.setRowFromDense(row_idx, row.begin());
    }
    
    weights_.normalizeRows();
*/
  }

  //--------------------------------------------------------------------------------
  // AHC
  //--------------------------------------------------------------------------------
#define TRACE_AHC							\
  if (trace) {								\
    cout << endl << endl;						\
    cout << "==============================================================" \
	 << endl;							\
    cout << "Iteration #" << (i+1) << endl;				\
    cout << "==============================================================" \
	 << endl;							\
    if (ntam.nRows() <= 10) {						\
      cout << setw(4) << "ntam";					\
      for (size_type i = 0; i != ntam.nRows(); ++i)			\
	cout << setw(7) << i;						\
      cout << endl;							\
      for (size_type i = 0; i != ntam.nRows(); ++i) {			\
	cout << setw(3) << i << ":";					\
	for (size_type j = 0; j != ntam.nCols(); ++j)			\
	  cout << setw(7) << setprecision(2) << ntam.get(i,j);		\
	cout << endl;							\
      }									\
      cout << endl << endl;						\
      cout << setw(4) << "utam";					\
      for (size_type i = 0; i != utam.nRows(); ++i)			\
	cout << setw(7) << i;						\
      cout << endl;							\
      for (size_type i = 0; i != utam.nRows(); ++i) {			\
	cout << setw(3) << i << ":";					\
	for (size_type j = 0; j != utam.nCols(); ++j)			\
	  cout << setw(7) << setprecision(4) << utam.get(i,j);		\
	cout << " : " << (size_type)utam.rowSum(i) << endl;		\
      }									\
    }									\
    cout << "\nMerging " << g2 << " into " << g1			\
	 << ": " << val << endl;					\
    groups_from_merges_(nCoincidences - nIter);				\
    cout << groups_.size() << " groups:" << endl;			\
    for (size_type i = 0; i != groups_.size(); ++i) {			\
      cout << i << ":[";						\
      set<size_type>::iterator j = groups_[i].begin();			\
      size_type k = 0;							\
      for (; j != groups_[i].end(); ++j, ++k) {				\
	size_type s = *j, c = tam_.getHOTCoincidence(s);		\
	cout << s;							\
	if (c != s)							\
	  cout << "/" << c;						\
	if (k != groups_[i].size()-1)					\
	  cout << " ";							\
      }									\
      cout << "] ";							\
    }									\
    cout << endl;							\
  }

  //--------------------------------------------------------------------------------
  void Grouper::AHCGroup(size_type nGroups)
  {
/*
    { // Preconditions
      NTA_CHECK(tam_.nNonZeroRows() > 0)
	<< "Grouper::AHCGroup: No coincidence learnt yet";
    } // End pre-conditions

    size_type trace = 0;
    value_type scale = 1.0;

    // tam2 contains our tam, adjusted to be symmetric always in AHC
    IntegerTAM tam2(tam_);
    tam_.addToTranspose(tam2);

    // Clear out the old vector of groups and tbi info, 
    // and cache the number of coincidences
    groups_.clear();  
    tbi_delete_();

    // utam stores actual counts
    // ntam is normalized and used find best way to merge
    FloatTAM utam, ntam;
    utam.copy(tam2);
    ntam.copy(tam2);

    // So that we don't pick a coincidence and itself to put 
    // in the same group
    for (size_type i = 0; i != tam_.nRows(); ++i)
      ntam.setZero(i,i);

    // We will update the ntam based on sums in the utam
    std::vector<value_type> row_sums(tam_.nRows(), (value_type)0);
    utam.rowSums(row_sums.begin());

    merges_.clear();

    AHC_Groups groups;
    size_type nnzc = 0;

    for (size_type i = 0; i != tam_.nRows(); ++i) {
      if (utam.isRowZero(i))
	groups.push_back(AHC_Group(0));
      else {
	groups.push_back(AHC_Group(1,i));
	++ nnzc;
      }
    }

    for (size_type i = 0; i != tam_.nRows(); ++i)
      if (!utam.isRowZero(i))
	ahc_update_(i, scale, groups, utam, ntam, row_sums);

    size_type nIter = utam.nNonZeroRows()-1;
    size_type nCoincidences = utam.nNonZeroRows();
    size_type g1 = 0, g2 = 0;
    value_type val = 0;

    for (size_type i = 0; i != nIter; ++i) {

      ntam.max(g1, g2, val);

      // If the largest value in the ntam is zero,
      // we select groups to merge in order of sizes,
      // smaller sizes first. 
      // We need that even if we rescale in update, because there
      // can be groups with no transitions between them, and we need
      // to pick two groups to continue merging anyway.
      if (val == 0) {
	g1 = g2 = 99999;
	for (size_type j = 0; j != groups.size(); ++j) {
	  size_type group_size = groups[j].size();
	  if (group_size != 0) {
	    if (g1 == 99999) {
	      g1 = j;
	    } else if (group_size < groups[g1].size()) {
	      g2 = g1;
	      g1 = j;
	    } else if (g2 == 99999 || group_size < groups[g2].size()) {
	      g2 = j;
	    }
	  }
	}
      }

      merges_.push_back(std::make_pair(g1, g2));
      std::copy(groups[g2].begin(), groups[g2].end(), 
		std::back_inserter(groups[g1]));
      groups[g2].clear();

      TRACE_AHC;

      utam.addTwoRows(g2, g1);
      utam.addTwoCols(g2, g1);
      
      // We want the diagonal term to be the count of self-transitions
      // for the new group. If g1 = 0 and g2 = 2, we need to bring the
      // transitions counts in utam[2,2] and utam[0,2], which are contributing
      // to the count of self-transitions for the new group. Since the utam
      // is symmetric, utam[0,2] needs to be counted only once (no utam[2,0]).
      utam.set(g1, g1, utam.get(g1, g1) - utam.get(g1,g2) + utam.get(g2,g2));

      utam.setRowToZero(g2);
      utam.setColToZero(g2);
      
      row_sums[g1] = utam.rowSum(g1);
      row_sums[g2] = 0;

      ahc_update_(g1, scale, groups, utam, ntam, row_sums);

      ntam.setRowToZero(g2);
      ntam.setColToZero(g2);
    }

    groups_from_merges_(nGroups);
*/
  }

  //--------------------------------------------------------------------------------

#define TRACE_AHC_UPDATE			\
  if (trace)					\
    cout << "Update: scale= " << scale		\
	 << " g1= " << g1			\
	 << " row_sums[g1]= " << row_sums[g1]	\
	 << " lgp= " << lgp_			\
	 << endl;

  /**
   * prod of the row sums on the numerator didn't help separate 1,2 and 3,4 into
   * different groups.
   */
  void Grouper::ahc_update_(size_type g1, value_type& scale, 
			    const AHC_Groups& groups,
			    const FloatTAM& utam, FloatTAM& ntam,
			    std::vector<value_type>& row_sums)

  {
/*
    size_type trace = 0;
    
    if (!(row_sums[g1] > 0)) {
      if (trace)
	cout << "No update, row_sums[" << g1 << "]= 0" << endl;
      return;
    }

    // Alpha = 1, beta = gamma = 0 works well in mini- unit testing
    // but there are issues in mocap
    // Gamma = 1 on 1,2,3,4: creates 1,2 and 3,4 in 2 merges, but then
    // won't merge 1,2 and 3,4 because they each contain lots of transitions
    // so their affinity drops sharply when dividing by the prod of the 
    // diagonal terms.
    //value_type alpha = 0.0, beta = 1.0, gamma = 0.0, delta = 0.0;
    //lgp_ = 0;

    FloatTAM::const_row_nz_index_iterator ind = utam.row_nz_index_begin(g1);
    FloatTAM::const_row_nz_index_iterator ind_end = utam.row_nz_index_end(g1);
    FloatTAM::const_row_nz_value_iterator nz = utam.row_nz_value_begin(g1);

    Pow<value_type> pow_f;

    TRACE_AHC_UPDATE;

    for (; ind != ind_end; ++ind, ++nz) {
	  
      size_type g2 = *ind;
	  
      // Since ntam and utam are symmetric, the number of transitions into
      // a coincidence is the same as the number of transitions out of 
      // that coincidence.
      // g1 = 0, g2 = 3, ntam[0,3] = 7, row_sums[0] = 48, row_sums[2] = 190
      if (g2 != g1 && row_sums[g2] > 0) {
	// val = 7 / (48 + 190): 
	// transitions from 3 to 0 / (total transitions into 0 and into 3)
	// = importance of that transition 
	value_type row_sum = row_sums[g1] + row_sums[g2];
//	  value_type diag_prod = 1.0, diag_sum = 1.0;
//	  if (groups[g1].size() >= 2 && groups[g2].size() >= 2) {
//	  diag_prod += utam.get(g1,g1) * utam.get(g2,g2);
//	  diag_sum += utam.get(g1,g1) + utam.get(g2,g2);
//	  }

	value_type val = *nz / row_sum;
//	//alpha * *nz / diag_prod 
//	  + beta * *nz / row_sum 
//	  + gamma * *nz / (row_sum * diag_prod)
//	  + delta * *nz / diag_sum;

	// Reduce the importance by dividing by a power of the size of the 
	// groups. This will tend to equalize the group sizes.
	value_type size_sum(groups[g1].size() + groups[g2].size());
	val /= pow_f(size_sum, (value_type)lgp_);
	// If some values in the ntam escape below epsilon, we rescale the
	// ntam.
	val *= scale;
	if (val <= nta::Epsilon) {
	  value_type scaleval = ceilf(1.0/val);
	  ntam.multiply(scaleval);
	  scale *= scaleval;
	  val *= scaleval;
	}
	ntam.set(g1, g2, val);
	ntam.set(g2, g1, val);
      }
    }
*/
  }

  //--------------------------------------------------------------------------------
#define TRACE_AHC_GROUPS_FROM_MERGES_1				\
  if (trace) {							\
    cout << "\n\nComputing " << nGroups << " groups"		\
	 << ", tam = " << tam_.nRows() << "X" << tam_.nCols()	\
	 << ", n nz rows = " << tam_.nNonZeroRows()		\
	 << ", merges = " << merges_.size()			\
	 << ", nIter = " << nIter				\
	 << endl;						\
  }

#define TRACE_AHC_GROUPS_FROM_MERGES_2			\
  if (trace > 2) {					\
    cout << m.second << " into " << m.first << endl;	\
    NTA_CHECK(m.first < groups_.size()) << "first";	\
    NTA_CHECK(m.second < groups_.size()) << "second";	\
  }
  
#define TRACE_AHC_GROUPS_FROM_MERGES_3					\
  if (trace) {								\
    size_type n_check = 0;						\
    for (size_type i = 0; i != groups_.size(); ++i) {			\
      cout << "Group #" << i << " size = " << groups_[i].size() << ": "; \
      n_check += groups_[i].size();					\
      set<size_type>::iterator j = groups_[i].begin();			\
      for (; j != groups_[i].end(); ++j)				\
	cout << *j << " ";						\
      cout << endl;							\
    }									\
    NTA_CHECK(n_check == tam_.nNonZeroRows())				\
      << "Lost coincidences in grouping";				\
  }
  
  //--------------------------------------------------------------------------------
  void Grouper::groups_from_merges_(size_type nGroups)
  {
/*
    { // Preconditions
      NTA_CHECK(tam_.nNonZeroRows() > 0)
	<< "Grouper::groups_from_merges_: No coincidence learnt yet";

      NTA_CHECK(nGroups >= 1)
	<< "Grouper::groups_from_merges_: Invalid nGroups: " << nGroups
	<< " - Should be at least 1";

      NTA_CHECK(nGroups <= merges_.size() + 1)
	<< "Grouper::groups_from_merges_: Invalid nGroups: " << nGroups
	<< " - Should be less than number of coincidences learnt: "
	<< tam_.nNonZeroRows();
    } // End pre-conditions

    int trace = 0;

    IntegerTAM tam2(tam_);
    tam_.addToTranspose(tam2);
    FloatTAM utam;
    utam.copy(tam2);

    groups_.clear();

    size_type n_coincidences = utam.nRows();
    size_type nIter = merges_.size() - nGroups + 1;
    set<size_type> empty_group;

    TRACE_AHC_GROUPS_FROM_MERGES_1;

    for (size_type i = 0; i != n_coincidences; ++i) { 
      if (utam.isRowZero(i)) {
	groups_.push_back(empty_group);
      } else {
	set<size_type> a_group;
	a_group.insert(i);
	groups_.push_back(a_group);
      }
    }

    for (size_type i = 0; i != nIter; ++i) {
      AMerge m = merges_[i];
      TRACE_AHC_GROUPS_FROM_MERGES_2;
      const set<size_type>& to_insert = groups_[m.second];
      groups_[m.first].insert(to_insert.begin(), to_insert.end());
      groups_[m.second].clear();
    }

    Groups::iterator it = groups_.begin();
    while (it != groups_.end()) 
      if (it->empty())
	it = groups_.erase(it);
      else
	++it;

    TRACE_AHC_GROUPS_FROM_MERGES_3;
    
    // Compute counts
    std::vector<value_type> counts(n_coincidences);
    tam_.rowSums(counts.begin());
   
    finish_grouping_(counts);
*/
  }

  //--------------------------------------------------------------------------------
  // END AHC
  //--------------------------------------------------------------------------------

  //--------------------------------------------------------------------------------
  // Sampling / Prediction
  //--------------------------------------------------------------------------------
  /**
   * This is a prediction function based on TBI. 
   *
   * It takes 4 arguments: group index, number of steps forward, algorithm 
   * ('distribution', 'single_path_max', 'single_path_sample'), and an initial 
   * distribution. Number of steps forward, algorithm and initial distribution 
   * are optional. If not specified, the number of steps forward is 1, algorithm 
   * defaults to 'single_path_sample' and the initial distribution is the uniform 
   * distribution. If the initial distribution is specified, it is a vector that 
   * has as many elements as there coincidences in the group. The returned value 
   * is either a full distribution over the group specified for each step forward, 
   * or a single path, expressed a list of coincidences. 
   *
   * future needs to be sized to the number of steps desired.
   */
  void 
  Grouper::sampleFromGroup(size_type grp_idx,
			   SamplingMode mode,
			   const std::vector<value_type>& initial_dist,
			   Sequences& future) const
  {
/*
    { // Pre-conditions
      NTA_ASSERT(getMode() == tbi)
	<< "Grouper::predict: Available only in tbi mode.";

      NTA_ASSERT(grp_idx >= 0 && grp_idx < tbiCellWeights_.size())
	<< "Grouper::sampleFromGroup: Invalid group index: " << grp_idx
	<< " - Should be between 0 and " << tbiCellWeights_.size();
      
      NTA_ASSERT(initial_dist.empty() 
		 || initial_dist.size() == tbiCellWeights_[grp_idx].nCols())
	<< "Grouper::sampleFromGroup: Invalid size for initial distribution: " 
	<< initial_dist.size()
	<< " - Should be empty (uniform) or of size: " 
	<< tbiCellWeights_[grp_idx].nCols()
	<< " for group: " << grp_idx;

      NTA_ASSERT(getMode() == tbi)
	<< "Grouper::sampleFromGroup: Available only in tbi mode";
    } // End pre-conditions

    TBICellWeights m(tbiCellWeights_[grp_idx]);

    m.setDiagonalToZero();
    m.normalizeCols();

    const size_type n_steps = future.size();
    const size_type size = m.nCols();

    for (size_type i = 0; i != n_steps; ++i) 
      if (mode == distribution)
	future[i].resize(size);
      else 
	future[i].resize(1);

    size_type s = 0, c = 0;
    vector<size_type> sequence;
    vector<value_type> x(size), y(size);

    if (initial_dist.empty()) 
      uniform_range(x);
    else 
      copy(initial_dist, x);

    for (size_type i = 0; i != n_steps; ++i) {

      m.rightVecProd(x.begin(), y.begin());

      if (mode == distribution) {

	copy(y, future[i]);

      } else {
	
	s = mode == single_path_max ? max_element(y) : sample_one(y);
	c = tam_.getHOTCoincidence(s);
	future[i][0] = c;
	dirac(s, y);
      }

      copy(y, x);
    }
*/
  }

  //--------------------------------------------------------------------------------
  /**
   * future needs to be sized to the number of steps desired.
   * max works better than marginalization when there are lots of long,
   * overlapping sequences, and is about as good as marginalization otherwise.
   */
  void Grouper::predict(size_type tbi_idx, PredictionMode mode, Sequences& future)
  {
/*
    using namespace std;

    { // Pre-conditions
      NTA_ASSERT(getMode() == tbi)
	<< "Grouper::predict: Available only in tbi mode.";
      NTA_ASSERT(!future.empty())
	<< "Grouper::predict: Empty future.";
    } // End pre-conditions

    if (tbiCellWeights_.empty())
      tbi_create_();

    const size_type n_steps = future.size();
    const TBICellOutputsVec& cells = tbiCellOutputs_[tbi_idx];
    
    // Allocate the cache if needed
    if (tbiPredBuf_.empty()) {
      tbiPredBuf_.resize(cells.size());
      for (size_type i = 0; i != cells.size(); ++i) 
	tbiPredBuf_[i].resize(cells[i].size());
    }

    // Copy current tbi cells to buffer
    for (size_type i = 0; i != cells.size(); ++i) 
      copy(cells[i], tbiPredBuf_[i]);

    // run tbi inference for n_steps
    vector<value_type> out(groups_.size());

    for (size_type i = 0; i != n_steps; ++i) {
      
      // Compute coincidence likelihood for each group
      // by going through subset of TAM
      for (size_type j = 0; j != tbiPredBuf_.size(); ++j) {
	tbiCellWeights_[j].rightVecProd(tbiPredBuf_[j], tbiBuffer_);
	copy(tbiBuffer_.begin(), tbiBuffer_.begin() + tbiPredBuf_[j].size(), 
	     tbiPredBuf_[j].begin());
	add_val(tbiPredBuf_[j], .1);
      }

      if (mode == groups) {

	// The size of the outputs is the number of groups
	// and we "marginalize" on the coincidences
	future[i].resize(groups_.size(), 0);
	for (size_type j = 0; j != tbiPredBuf_.size(); ++j)
	  for (size_type k = 0; k != tbiPredBuf_[j].size(); ++k)
	    future[i][j] = max(future[i][j], tbiPredBuf_[j][k]);

      } else {

	// The size of the outputs is the size of the input
	// (the input is a distribution over the coincidences)
	// and we "marginalize" on the groups.
	// max rather than sum gives bette results with lots of 
	// overlapping sequences. Summing introduces a systematic
	// error because of A0, and it can blow up the importance
	// of heavily split states in the presence of noise. Max
	// doesn't have that problem, and corresponds to the most
	// likely state of the Markov graph when no variable is 
	// instantiated.
	future[i].resize(tam_.getNCoincidences(), 0);

	for (size_type j = 0; j != tbiPredBuf_.size(); ++j) {

	  AGroup::const_iterator g = groups_[j].begin(), g_end = groups_[j].end();
	  for (size_type k = 0; g != g_end; ++g, ++k) {
	    size_type c = tam_.getHOTCoincidence(*g);
	    //future[i][c] += tbiPredBuf_[j][k];
	    future[i][c] = max(future[i][c], tbiPredBuf_[j][k]);
	  }
	}
      }
    }
*/
  }

  //--------------------------------------------------------------------------------
  // END Sampling / Prediction
  //--------------------------------------------------------------------------------
  
  //--------------------------------------------------------------------------------
  // Persistence
  //--------------------------------------------------------------------------------
  /**
   * Version 13 adds overlapping groups_ flag
   * Version 14 adds tbiCellWeights and tbiCellOutputs to the end
   * Version 15 uses TAM::saveState
   * Version 16 saves lgp_ and merges_ for AHC grouping
   * Version 17 saves n_tbis_
   * Version 18 saves segment size?
   * Version 19 saves rescaleTBI
   */
  void Grouper::saveState(std::ostream& outStream) const
  {
/*
    {
      NTA_CHECK(outStream.good())
        << "Grouper::saveState(): "
        << "- Bad stream";
    }
   
    outStream << "Grouper19 ";
    outStream << mode_ << " "
              << (symmetricTam_ ? "1 " : "0 ")
              << topNeighbors_ << " "
              << maxNGroups_ << " "
              << maxGroupSize_ << " "
	      << overlappingGroups_ << " ";
    
    tam_.saveState(outStream);

    outStream << groups_.size() << " ";
    Groups::const_iterator it = groups_.begin();
    for (; it != groups_.end(); ++it) {
      outStream << it->size() << " ";
      AGroup::const_iterator it2 = it->begin();
      for (; it2 != it->end(); ++it2)
        outStream << *it2 << " ";
    }

    if (weights_.nRows() > 0) {
      outStream << weights_.nCols() << " ";
      weights_.toCSR(outStream);
    } else {
      outStream << "0 ";
    }
    
    // TBI
    outStream << n_tbis_ << " ";

    // AHC
    outStream << " " << lgp_ << " ";
    outStream << merges_.size() << " ";
    for (size_type i = 0; i != merges_.size(); ++i) {
      outStream << merges_[i].first << " "
		<< merges_[i].second << " ";
    }

    outStream << segmentSize_ << " ";
    outStream << (size_type) rescaleTBI_ << " ";
*/
  }

  //--------------------------------------------------------------------------------
  /**
   * inStream can be empty, when this is called the first time around on the tools
   * side.
   *
   * If file format is 12, there is no overlapping groups_, we don't overlap groups_. 
   * If file format is 13, the overlapping groups_ flag is read. 
   * If file format is 14, tbiCellWeights_ and tbiCellOutputs_ are read.
   * If file format is 15, we use TAM::readState.
   * If file format is 16, we save/restore AHC grouping data.
   * If file format is 17, we save/restore n_tbis_.
   * If file format is 19, we save/restore rescaleTBI.
   */
  void Grouper::readState(std::istream& inStream)
  {
/*
    const char* where = "Grouper::readState(): ";
    
    {
      NTA_CHECK(inStream.good()) 
	<< where << "- Bad stream";
    }
    
    // -----------------------------------------------------------------------------
    // Check for our keyword and valid version
    string str;
    inStream >> str;
    size_type version = 10;
    if (str == "Grouper")
      version = 10;
    else if (str == "Grouper13")
      version = 13;
    else if (str == "Grouper14")
      version = 14;
    else if (str == "Grouper15")
      version = 15;
    else if (str == "Grouper16")
      version = 16;
    else if (str == "Grouper17")
      version = 17;
    else if (str == "Grouper18")
      version = 18;
    else if (str == "Grouper19")
      version = 19;
    else {
      NTA_THROW
        << where
        << "- Wrong class data format, expected data for Grouper";
    }

    // -----------------------------------------------------------------------------
    // Read in the flags and modes
    unsigned int mode = 0;
    size_type hms, tn, mng, mgs, h, st, og;
    hms = tn = mng = mgs = h = st = 0;
    const size_type M = std::numeric_limits<size_type>::max();

    inStream >> mode >> st;

    // Starting with 15, hms is saved with the TAM itself
    if (version < 15) {
      inStream >> hms;
      tam_.setTransitionMemory(hms);
    }
    
    inStream >> tn >> mng >> mgs;
    
    // Overlapping groups
    og = false;               // 1.2
    if (version >= 13)        // 1.3
      inStream >> og;

    mode_ = (Mode) mode;
    symmetricTam_ = (st == 1);

    NTA_CHECK(tn > 0 && tn < M)
      << where
      << "Invalid top neighbors: " << tn
      << " - Top neighbors should be > 0 and < " << M;

    NTA_CHECK(mng > 0 && mng < M)
      << where
      << "Invalid max number of groups_: " << mgs
      << " - Max number of groups_ should be > 0 and < " << M;

    NTA_CHECK(mgs > 0 && mgs < M)
      << where
      << "Invalid max group size: " << mgs
      << " - Max group size should be > 0 and < " << M;

    topNeighbors_ = size_type(tn);
    maxNGroups_ = size_type(mng);
    maxGroupSize_ = size_type(mgs);
    overlappingGroups_ = og ? true : false;
    
    // -----------------------------------------------------------------------------
    // Read in the history if version less than 15
    // Starting with 15, the history is saved together with the IntegerTAM
    if (version < 15) {

      size_type hs = 0;
      IntegerTAM::History history;

      inStream >> hs;
      
      NTA_CHECK(hs >= 0 && hs < M)
	<< where
	<< "Invalid history size: " << hs
	<< " - History size should be > 0 and < " << M;
      
      history.resize(hs);

      for (size_type i = 0; i < hs; ++i) 
	inStream >> history[i];

      // -----------------------------------------------------------------------------
      // Read in the TAM
      tam_.fromCSR(inStream);
      tam_.setHistory(history);

    } else { // version >= 15
      
      tam_.readState(inStream);
    }

    // -----------------------------------------------------------------------------
    // Read in the formed groups_
    size_type nGroups = 0, groupSize = 0, e = 0;

    inStream >> nGroups;     

    NTA_CHECK(nGroups >= 0 && nGroups < M)
      << where
      << "Invalid number of groups_: " << nGroups
      << " - Number of groups_ should be > 0 and < " << M;
  
    groups_.clear();

    for (size_type i = 0; i < nGroups; ++i) {

      inStream >> groupSize;

      NTA_CHECK(groupSize > 0 && groupSize < M)
        << where
        << "Invalid group size: " << groupSize
        << " - Group size should be > 0 and < " << M;

      AGroup agroup;

      for (size_type j = 0; j < groupSize; ++j) {
        
        inStream >> e;

        NTA_CHECK(e >= 0 && e < size_type(tam_.nCols())) 
          << where
          << "Invalid grouper member: " << e
          << " - All group members should be >= 0 and < " << tam_.nCols();

        agroup.insert(e);
      }
      groups_.push_back(agroup);
    }   

    // -----------------------------------------------------------------------------
    // Read in the weights matrix
    size_type nCols = 0;
    inStream >> nCols;
    if (nCols > 0) 
      weights_.fromCSR(inStream);
    
    // -----------------------------------------------------------------------------
    // Read in the tbi cell weights and cell outputs
    if (version >= 14) {
      
      tbi_delete_();

      size_type n_tbis = 1;

      if (version >= 17) {

	inStream >> n_tbis;

	NTA_CHECK(n_tbis >= 0)
	  << where
	  << "Invalid number of tbis: " << n_tbis
	  << " - should be >= 0";
      }
      
      n_tbis_ = n_tbis;
    }

    // --------------------------------------------------------------------------------
    // AHC
    if (version >= 16) {
      
      inStream >> lgp_;
      
      size_type n = 0;
      inStream >> n;
      
      NTA_CHECK(n >= 0)
	<< where << "Invalid number of merges: " << n
	<< " - Should be >= 0";

      for (size_type i = 0; i != n; ++i) {
	AMerge amerge;
	inStream >> amerge.first >> amerge.second;
	NTA_CHECK(0 <= amerge.first && amerge.first <= tam_.nRows())
	  << where << "Invalid merge index: " << amerge.first
	  << " - Should be >= 0 and < n coincidences: " << tam_.nRows();
	NTA_CHECK(0 <= amerge.second && amerge.second <= tam_.nRows())
	  << where << "Invalid merge index: " << amerge.second
	  << " - Should be >= 0 and < n coincidences: " << tam_.nRows();
	merges_.push_back(amerge);
      }
    }

    if (version >= 18) 
      inStream >> segmentSize_;

    if (version >= 19)
      inStream >> rescaleTBI_;
*/
  }

  //--------------------------------------------------------------------------------

} // end namespace nta



