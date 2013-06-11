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
 * Definition for Time Adjacency Matrix.
 */

#ifndef NTA_TAM_HPP
#define NTA_TAM_HPP

#include <deque>
#include <iostream>
#include <fstream>

#include <nta/math/stl_io.hpp>
#include <nta/math/array_algo.hpp>
#include <nta/math/SparseMatrix.hpp>

//----------------------------------------------------------------------
namespace nta {

  //--------------------------------------------------------------------------------
  template <typename T>
  class TAM : public T
  {
  public:
    typedef T parent_type;
    typedef TAM self_type;

    typedef typename parent_type::size_type size_type;
    typedef typename parent_type::difference_type difference_type;
    typedef typename parent_type::value_type value_type;
    typedef typename parent_type::prec_value_type prec_value_type;

    typedef std::deque<size_type> History;

    //--------------------------------------------------------------------------------
    // CONSTRUCTORS
    //--------------------------------------------------------------------------------
    inline TAM()
      : parent_type(),
        transitionMemory_(1),
        history_(1),
        hot_nRounds_(1),
        hot_min_cnt2_(0),
        hot_nStates_(0),
        hot_iterPerStage_(0),
        hot_maxPerStage_(-1),
        hot_maxCoincidenceSplitsPerRound_(0),
        hot_handleSelf_(false),
        hot_s2c_(),
        hot_c2s_(),
        trace_learning(0),
        trace_hot(0)
    {}

    //--------------------------------------------------------------------------------
    /**
     * Constructor with a number of columns and a hint for the number
     * of rows. The SparseMatrix is empty.
     *
     * @param nrows [size_type >= 0] number of rows
     * @param ncols [size_type >= 0] number of columns
     *
     * @b Exceptions:
     *  @li nrows < 0 (check)
     *  @li ncols < 0 (check)
     *  @li Not enough memory (error)
     */
    inline TAM(size_type nrows, size_type ncols, 
               size_type tm =1,
               size_type nRounds =1,
               float min_cnt2 =0,
               size_type iterPerStage =0,
               int maxPerStage =-1,
               size_type maxCoincidenceSplitsPerRound =0,
               bool handleSelf =false)
      : parent_type(nrows, ncols),
        transitionMemory_(tm),
        history_(1),
        hot_nRounds_(nRounds),
        hot_min_cnt2_(min_cnt2),
        hot_nStates_(0),
        hot_iterPerStage_(iterPerStage),
        hot_maxPerStage_(maxPerStage),
        hot_maxCoincidenceSplitsPerRound_(maxCoincidenceSplitsPerRound),
        hot_handleSelf_(handleSelf),
        hot_s2c_(),
        hot_c2s_(),
        trace_learning(0),
        trace_hot(0)
    {
      NTA_CHECK(transitionMemory_ > 0)
        << "TAM "
        << "Invalid history max size: " << transitionMemory_
        << " - History max size should be  > 0";
    }
    
    //--------------------------------------------------------------------------------
    /**
     * Constructor from a stream in CSR format (don't forget number of bytes after
     * 'csr' tag!).
     */
    inline TAM(std::istream& inStream)
      : parent_type(inStream),
        transitionMemory_(1),
        history_(1),
        hot_nRounds_(1),
        hot_min_cnt2_(0),
        hot_nStates_(0),
        hot_iterPerStage_(0),
        hot_maxPerStage_(-1),
        hot_maxCoincidenceSplitsPerRound_(0),
        hot_handleSelf_(false),
        hot_s2c_(),
        hot_c2s_(),
        trace_learning(0),
        trace_hot(0)
    {
      readState(inStream);
    }

    //--------------------------------------------------------------------------------
    /**
     * Copy constructor.
     *
     * TODO copy part of a matrix?
     *
     * Copies the given TAM into this one.
     */
    inline TAM(const TAM& other)
      : parent_type(other),
        transitionMemory_(other.transitionMemory_),
        history_(other.history_),
        hot_nRounds_(other.hot_nRounds_),
        hot_min_cnt2_(other.hot_min_cnt2_),
        hot_nStates_(other.hot_nStates_),
        hot_iterPerStage_(other.hot_iterPerStage_),
        hot_maxPerStage_(other.hot_maxPerStage_),
        hot_maxCoincidenceSplitsPerRound_(other.hot_maxCoincidenceSplitsPerRound_),
        hot_handleSelf_(other.hot_handleSelf_),
        hot_s2c_(other.hot_s2c_),
        hot_c2s_(other.hot_c2s_),
        trace_learning(other.trace_learning),
        trace_hot(other.trace_hot)
    {}

    //--------------------------------------------------------------------------------
    /**
     * Assignment operator.
     */
    inline TAM& operator=(const TAM& other)
    {
      parent_type::operator=(other);
      transitionMemory_ = other.transitionMemory_;
      history_ = other.history_;
      hot_nRounds_ = other.hot_nRounds_;
      hot_min_cnt2_ = other.hot_min_cnt2_;
      hot_nStates_ = other.hot_nStates_;
      hot_iterPerStage_ = other.hot_iterPerStage_;
      hot_maxPerStage_ = other.hot_maxPerStage_;
      hot_maxCoincidenceSplitsPerRound_ = other.hot_maxCoincidenceSplitsPerRound_;
      hot_handleSelf_ = other.hot_handleSelf_;
      hot_s2c_ = other.hot_s2c_;
      hot_c2s_ = other.hot_c2s_;
      return *this;
    }

    //--------------------------------------------------------------------------------
    /**
     * Finishes initialization by sizing data structures that depend on the number 
     * of baby nodes.
     */
    inline void setNTBIs(size_type n_tbis)
    {
      history_.resize(n_tbis);
    }

    //--------------------------------------------------------------------------------
#define TRACE_TAM_LEARNING_1						\
    if (trace_learning) {						\
      cout << "\nbaby_idx=" << baby_idx					\
           << "/" << history_.size()					\
           << " winnerIndex=" << winnerIndex				\
           << " transition memory=" << transitionMemory_;		\
      cout << " History: ";						\
      typename History::const_iterator					\
        i = history_[baby_idx].begin(), e = history_[baby_idx].end();	\
      for (; i != e; ++i)						\
        cout << *i << " ";						\
      cout << endl;							\
    } 

#define TRACE_TAM_LEARNING_2						\
    if (trace_learning) {						\
      cout << "Updating TAM row #" << winnerIndex << endl;		\
      cout << "History is now: ";					\
      typename History::const_iterator					\
        ii = history_[baby_idx].begin(), ee = history_[baby_idx].end(); \
      for (; ii != ee; ++ii)						\
        cout << *ii << " ";						\
      cout << endl;							\
      this->print(cout);                                                \
    }

    //--------------------------------------------------------------------------------
    /**
     */
    void learn(size_type winnerIndex, size_type baby_idx =0)
    {
      using namespace std;
   
      History& history = history_[baby_idx];
      
      /*
	TRACE_TAM_LEARNING_1;
	size_type nhs = getHOTNStates();
	size_type ns = this->nRows();
	NTA_ASSERT((!nhs) || (winnerIndex < (ns - nhs)))
        << "New coincidence (" << winnerIndex << ") encountered, "
        "but HOT states " << (ns - nhs) << "-" << ns 
        << "have already been allocated in cloning rounds. "
        "All unique coincidences must be seen during the first "
        "round of training.";
      */

      // We change the index of the winner according to the c2s table.
      // previous can be a state, but winnerIndex is in the original
      // "alphabet". c2s holds destination states when given a pair
      // (state or coincidence) -> original digit.
      // The history is now in terms of augmented states, rather
      // than original coincidences.
      if (usesHOT() && !history.empty()) {
        //size_type w = winnerIndex;
        winnerIndex = getHOTState(history[0], winnerIndex);
        /* KEEP */
        /*
	  if (trace_learning) {
          if (winnerIndex != w) {
	  cout << "(" << w 
	  << "/" << winnerIndex
	  << ")";
          } else {
	  cout << winnerIndex;
          }
          cout << " ";
	  }
        */
      }
      
      if (winnerIndex >= this->nRows()) 
        this->resize(winnerIndex+1, winnerIndex+1);
      
      // It's faster to update the CSR stored TAM by rows,
      // but the column indices are origin states, and the row indices 
      // are destination states!
      // We use methods of SparseMatrix directly for speed.
      if (!history.empty()) {
        if (transitionMemory_ == 1) {
          this->incrementWNZ(winnerIndex, history[0]);
        } else {
          // TODO: batch increment on SM, and copy to nzb only if needed
          this->to_nzb_(winnerIndex);
          for (size_type i = 0; i != history.size(); ++i)
            this->nzb_[history[i]] += transitionMemory_ - i;
          this->set_row_(winnerIndex, this->nzb_, this->nzb_ + this->nCols());
        }
      }
      
      history.push_front(winnerIndex);
      if (history.size() > transitionMemory_) 
        history.pop_back();

      // TRACE_TAM_LEARNING_2;
    }

    //--------------------------------------------------------------------------------
    inline size_type getTransitionMemory() const 
    { 
      return transitionMemory_; 
    }

    //--------------------------------------------------------------------------------
    inline void setTransitionMemory(size_type tm) 
    { 
      NTA_CHECK(tm > 0)
        << "TAM::setTransitionMemory: "
        << "Invalid transition memory size: " << tm
        << " - Expecting value > 0";
      transitionMemory_ = tm; 
    }

    //--------------------------------------------------------------------------------
    inline const History& getHistory(size_type i) const
    {
      return history_[i];
    }

    //--------------------------------------------------------------------------------
    inline History getCollapsedHistory(size_type i) const
    {
      History ret;
      for (size_type j = 0; j != history_[i].size(); ++j)
        ret.push_back(getHOTCoincidence(history_[i][j]));
      return ret;
    }

    //--------------------------------------------------------------------------------
    inline void setHistory(const History& history, size_type baby_idx =0)
    {
      history_[baby_idx] = history;
    }

    //--------------------------------------------------------------------------------
    inline void resetHistory()
    {
      for (size_type i = 0; i != history_.size(); ++i)
        history_[i].clear();
    }

    //--------------------------------------------------------------------------------
    inline std::vector<value_type> getRowCounts() const
    {
      std::vector<value_type> counts(this->nRows());
      this->rowSums(counts.begin());
      return counts;
    }

    //--------------------------------------------------------------------------------
    // HOT
    //--------------------------------------------------------------------------------
#define TRACE_HOT_1							\
    if (trace_hot) {							\
      if (selfPhase || !handleSelf) {					\
        cout << "\n\n###################################################" \
             << "\nHOT " << endl;					\
        cout << "\nreqNRounds=" << getHOTRequestedNRounds()		\
             << " iterPerStage=" << getHOTIterPerStage()                \
             << " max=" << getHOTMaxPerStage()				\
             << " maxCoincidenceSplits=" << getHOTMaxCoincidenceSplitsPerRound() \
             << " min_cnt2=" << (float) min_cnt2                        \
             << " nStates=" << getHOTNStates()				\
             << " tam nrows=" << this->nRows()				\
             << " nnzr=" << this->nNonZeros();				\
        if (selfPhase)							\
          cout << " nnzself=" << n_actual;				\
        cout << endl							\
             << endl;							\
      }									\
      if (!selfPhase) {							\
        cout << "Sorted non-zeros (n_actual=" << n_actual << "): ";	\
        if (n_actual > 0)						\
          for (size_type i = 0; i != n_actual; ++i)			\
            cout << "(" << nnzs[i].j() << ", " << nnzs[i].i()		\
                 << ", " << nnzs[i].v() << ")";				\
        else								\
          cout << "none.";						\
        cout << endl;							\
      }									\
    }
    
    template<typename T1, typename T2>
    inline T2 getWithDefault(const std::map<T1, T2> &m, 
                             const T1 &key, const T2 &defValue)
    {
      typename std::map<T1, T2>::const_iterator found = m.find(key);
      if(found == m.end()) return defValue;
      else return found->second;
    }

#define TRACE_HOT_2							\
    if (trace_hot) {							\
      cout.precision(5);                                                \
      cout << "Examining "						\
           << current							\
           << "(" << getWithDefault(hot_s2c_, current, current) << ") -> " \
           << next							\
           << "(" << getWithDefault(hot_s2c_, next, next) << ")";	\
      cout << ", transval= " << transVal                                \
           << ": " << cntNext << "-" << transVal << "= "                \
           << delta;							\
      if (transVal <= min_cnt1)						\
        cout << " Pass (too few transitions in)" << endl;		\
      else if (delta > min_cnt2) {					\
        if (splitCounts[nextCoincidence] < maxSplitsPerRound)		\
          cout << " > " << min_cnt2 << "  Cloning ("			\
               << hot_nStates_ << ")" << endl;                          \
        else								\
          cout << " > " << min_cnt2 << "; "				\
               << splitCounts[nextCoincidence] << " splits of "		\
               << nextCoincidence << " >= " << maxSplitsPerRound        \
               << " Pass (too many splits)" << endl;			\
      }									\
      else								\
        cout << " <= " << min_cnt2 << " Pass (too few others)" << endl;	\
    }

#define TRACE_HOT_3				\
    if (trace_hot) {				\
      if (0) {					\
        print_debug_HOT_C2S_();			\
        cout << "s2c: " << hot_s2c_ << endl;	\
      }						\
    }

#define TRACE_HOT_4							\
    if (trace_hot) {							\
      cout << endl;							\
      print_debug_HOT_C2S_();						\
      cout << "s2c: " << hot_s2c_ << endl;				\
      cout << "###################################################\n\n"; \
    }

    //--------------------------------------------------------------------------------
    typedef SparseMatrix<size_type,size_type> HOTC2S;
    typedef std::map<size_type,size_type> HOTS2C;

    //--------------------------------------------------------------------------------
    inline bool computeHOT(size_type iteration) const
    {
      return usesHOT() 
        && iteration > 0
        && iteration % hot_iterPerStage_ == 0 
        && iteration / hot_iterPerStage_ <= hot_nRounds_;
    }

    //--------------------------------------------------------------------------------
    void checkC2SOrphans() const 
    {
      std::vector<size_type> refCount(hot_nStates_);
      
      // Scan all non-zeros in c2s.
      size_type c2snr = hot_c2s_.nRows();
      for (size_type c2sr = 0; c2sr < c2snr; ++c2sr) {
        typename SparseMatrix<size_type, size_type>::const_row_nz_value_iterator 
          nziter=hot_c2s_.row_nz_value_begin(c2sr),
          nzend=hot_c2s_.row_nz_value_end(c2sr);
        for(; nziter!=nzend; ++nziter) {
          size_type destination = (*nziter) - 1;
          NTA_ASSERT(destination < hot_nStates_);
          ++refCount[destination];
        }
      }

      // What about non-HOT states?
      size_type C = hot_nStates_ - hot_s2c_.size(); // HACK!
      for(size_type stateToCheck = C; stateToCheck < hot_nStates_; ++stateToCheck)
        if (refCount[stateToCheck] > 0) // ORPHAN!
          NTA_WARN << "Created orphan: " << stateToCheck 
                   << " refcount = " << refCount[stateToCheck];
    }

    //--------------------------------------------------------------------------------
    /**
     * This method computes HOT states to track statistics of worthwhile transitions.
     */
    inline void hot()
    {
      using namespace std;

      //cout << "Entropy= " << (float) entropy(1) << endl;

      typedef vector<vector<size_type> > PostProcess;
      PostProcess postprocess;

      // We compute the threshold to use when determining whether to split 
      // or not. Values less than zero don't make sense, since min_cnt2
      // is a frequency count.
      float min_cnt2 = pow(1.0f - hot_min_cnt2_, 4.0f) * hot_iterPerStage_;
      min_cnt2 = min_cnt2 < 0.0f ? (float) 0.0f : min_cnt2;

      const value_type min_cnt1(0);
      const bool handleSelf = hot_handleSelf_;

      size_type n_actual(0);

      // No maximum implies that the maximum is equal to the number of incoming
      // transitions.
      size_type maxSplitsPerRound = hot_maxCoincidenceSplitsPerRound_;

      if(maxSplitsPerRound == 0)
        maxSplitsPerRound = this->nRows();

      typedef typename parent_type::IJV IJV;
      vector<IJV> nnzs;
      size_type originalCoincidences = this->nRows() - getHOTNStates();
      vector<size_type> splitCounts(originalCoincidences);
      vector<value_type> row_sums(this->nRows());
      this->rowSums(row_sums.begin());

      // We resume indexing the split-off states at nRows(), 
      // or hot_nStates_ if we didn't learn new coincidences.
      // We resize hot_c2s_ to be in sync.
      // TAM is always square by construction. 
      hot_nStates_ = std::max(this->nRows(), hot_nStates_);
      hot_c2s_.resize(hot_nStates_, hot_c2s_.nCols());
        
      for (int phase = 0; phase != (int(handleSelf)+1); ++phase) {

        bool selfPhase = handleSelf && (phase == 0);
  
        if (selfPhase) {
          size_type n_self = this->nRows();
          nnzs.resize(n_self);
          n_actual = 0;
          // Need a fast accessor for non-zeros on the diagonal.
          for (size_type state = 0; state < n_self; ++state) {
            value_type count = this->get(state, state);
            if (count)
              nnzs[n_actual++] = IJV(state, state, count);
          }
          nnzs.resize(n_actual);
        }
        else {
          // There might be less non-zeros available than required by the user,
          // so we compute the actual number of non-zeros we are going to get.
          n_actual = hot_maxPerStage_ == -1 ?
            this->nNonZeros() : std::min(this->nNonZeros(), (size_type) hot_maxPerStage_);
  
          nnzs.resize(n_actual);
  
          // Focus on more frequent transitions if the total number of splits or 
          // the number of splits per state are limited.
          if ((hot_maxPerStage_ > -1) || (maxSplitsPerRound > 0)) {
            typename IJV::greater_value o;
            n_actual = this->getNonZerosSorted(nnzs.begin(), (int) n_actual, o);
            nnzs.resize(n_actual);
          } else
            this->getAllNonZeros(nnzs.begin());
        }
  
        //TRACE_HOT_1;
  
        for (size_type i = 0; i != n_actual; ++i) {
  
          // In the original TAM, columns represent origin states
          // and rows represent destination states.
          // But in hot_c2s_, rows represent origin states
          // and columns represent destination states.
          size_type current = nnzs[i].j();
          size_type next = nnzs[i].i();
  
          // Only process self transitions the first time through the loop.
          if (handleSelf) {
            if (selfPhase ^ (current == next)) continue;
          }
  
          value_type transVal = nnzs[i].v();
          value_type cntNext = row_sums[next];
  
          // Need original coincidence, so that we can retrieve the right 
          // split state when learning, and the previous digit is a state
          // and the current one is an original coincidence.
          // We get the original coincidence in the first pass, and we'll
          // continue getting original coincidences after that,
          // because we store original coincidence indices in c2s and s2c.
          size_type nextCoincidence = getHOTCoincidence_(next);
          value_type delta = cntNext - transVal;
  
          //TRACE_HOT_2;
  
          // If the difference ('delta') between all the transition counts 
          // into 'next' and the transition from 'current' to 'next', we 
          // isolate 'current' -> 'next' by creating a new state, 'newState'
          // that is a copy of 'next'. We call 'newState' a split of 'next'.
          // When we split, the split ('newState') takes transVal transitions 
          // out of the incoming transitions into 'next'. The split state 
          // itself is never a candidate for splitting in the round it was 
          // split off. The sum of the transition counts from 'next' and 
          // 'newState' to their successors is invariant. 'newState' is 
          // tracked in c2s. The TAM itself is never modified, except that its
          // size will grow by one to account for 'newState'. We do not keep
          // track of the transition counts from 'newState' to the successors
          // of 'next' since the TAM will be recounted anyway, and the transitions
          // from 'newState' to its successors will never be candidates for 
          // splitting in this round (we have locked down the list of candidates
          // for splitting above). 

          // In the case where there is a single transition into,
          // delta = 0, and min_cnt2 = 0, so we won't split the target
          // state if it has a single transition into.
          if ((transVal > min_cnt1) && (delta > min_cnt2) && 
              (splitCounts[nextCoincidence] < maxSplitsPerRound)) 
            {
              size_type newState = hot_nStates_++;
              setHOT_C2S_(current, nextCoincidence, newState);
              hot_c2s_.duplicateRow(next);
              row_sums[next] -= transVal;
              hot_s2c_.insert(make_pair(newState, nextCoincidence));
              vector<size_type> triplet(3);
              triplet[0] = newState;
              triplet[1] = current;
              triplet[2] = nextCoincidence;
              postprocess.push_back(triplet);
              ++splitCounts[nextCoincidence];
              //TRACE_HOT_3;
            } 
        }
  
      } // End of phase (self/non-self).

      //#if NTA_ASSERTIONS_ON
      //checkC2SOrphans();
      //#endif

      // We don't want to depend on the order in which we did the splits,
      // so we post-process when we know all the splits, to add routings
      // into new states in c2s.
      // This procedure has the side-effect of creating 'orphan' states,
      // that is, states that cannot be reached. Those orphans will be
      // detected and removed later. They cause problems when grouping, 
      // leading to many undesirable singleton groups. 
      // Suppose we are learning sequence 4,2,6 and that we are splitting 
      // 4 -> 2 first, 2 becoming state 26, then 2 -> 6, 6 becoming state 27.
      // However, when learning, it will see 4 -> 2, updating 4 -> 26
      // in the TAM, then 26 -> 6, and there is no entry in c2s for that,
      // so we won't update 26 -> 27. The problem is that when duplicating 6
      // into 27, we need to go back to 26, and add an entry for 26 -> 6.
      typename PostProcess::const_iterator it1, it2, end;
      it1 = postprocess.begin(); end = postprocess.end();
      
      //TRACE_HOT_4;

      // postprocessing = (26, (4,2)) (27, (2,6))

      for (; it1 != end; ++it1) {

        size_type newState = (*it1)[0]; // 26
        size_type to = (*it1)[2]; // 2
        
        for (it2 = postprocess.begin(); it2 != end; ++it2) {

          size_type newState2 = (*it2)[0]; // 27

          if (newState2 == newState) 
            continue;

          size_type from2 = (*it2)[1]; // 2
          size_type to2 = (*it2)[2]; // 6

          if (from2 == to) 
            setHOT_C2S_(newState, to2, newState2);
        }
      }

      //#if NTA_ASSERTIONS_ON
      //checkC2SOrphans();
      //#endif

      if (handleSelf) {
        // Intentionally hook up new state self-transitions so that 
        // they are counted. This allows us to treat self-transitions specially,
        // even for HOT states.
        // This is set after the general post-processing, as the general
        // post-processing would sometimes modify these entries.
        it1 = postprocess.begin();
        for (; it1 != end; ++it1) {
          size_type newState = (*it1)[0];
          size_type to = (*it1)[2]; 
          setHOT_C2S_(newState, to, newState);
        }
      }

      //#if NTA_ASSERTIONS_ON
      //checkC2SOrphans();
      //#endif

      //TRACE_HOT_4;

      // We resize to stay in sync, and erase (true parameter).
      // Don't forget to resize the buffer too! 
      // This resizing has the effect of adding row/cols for the states
      // we have created in this round. 
      this->resize(hot_nStates_, hot_nStates_, true);

      // Clear history to avoid spurious counts from coincidences
      // that are now re-routed to states, or states that are defunct
      resetHistory();
    }

    //--------------------------------------------------------------------------------
    typedef std::map<size_type, size_type> Mapping;

    //--------------------------------------------------------------------------------
    /**
     * Orphans are defined as states that have no count in or out after the last pass
     * of counting (just prior to switching to inference).
     */
    inline void cleanOrphans()
    {
      using namespace std;

      vector<size_type> orphans;
      size_type C = this->nRows() - getHOTNStates();
      for (size_type row = C; row != this->nRows(); ++row) 
        if (this->rowSum(row) == 0 && this->colSum(row) == 0)
          orphans.push_back(row);

      Mapping mapping;
      size_type old_i = 0, new_i = 0, k = 0;

      while (old_i != this->nRows()) {
        if (k != orphans.size() && old_i == orphans[k]) {
          ++k; ++old_i;
        } else {
          mapping[old_i++] = new_i++;
        }
      }

      this->deleteRows(orphans);
      this->deleteCols(orphans);

      hot_c2s_.deleteRows(orphans);

      size_type nnz = hot_c2s_.nNonZeros();
      vector<size_type> nzi(nnz), nzj(nnz);
      vector<size_type> nzv(nnz);
      hot_c2s_.getAllNonZeros(nzi.begin(), nzj.begin(), nzv.begin());

      // If pointing to orphan, set to 0, i.e. redirect to parent coincidence
      for (size_type i = 0; i != nnz; ++i) 
        hot_c2s_.set(nzi[i], nzj[i], mapping[nzv[i]]);

      HOTS2C new_s2c;

      for (size_type i = 0; i != orphans.size(); ++i) 
        hot_s2c_.erase(orphans[i]);

      typename HOTS2C::iterator it = hot_s2c_.begin(), e = hot_s2c_.end();
      for (; it != e; ++it) 
        new_s2c[mapping[it->first]] = mapping[it->second];
      
      hot_s2c_.swap(new_s2c);
      hot_nStates_ -= orphans.size();
    }

    //--------------------------------------------------------------------------------
    inline void setHOTNRounds(size_type nRounds)
    {
      NTA_CHECK(nRounds >= 0)
        << "TAM::setHOTNRounds: Invalid number of rounds: " << nRounds
        << " - N rounds needs to be >= 0";

      hot_nRounds_ = nRounds;
    }

    //--------------------------------------------------------------------------------
    inline size_type getHOTRequestedNRounds() const
    {
      return hot_nRounds_;
    }

    //--------------------------------------------------------------------------------
    inline void setHOTMinCnt2(float min_cnt2)
    {
      hot_min_cnt2_ = min_cnt2;
    }

    //--------------------------------------------------------------------------------
    inline float getHOTMinCnt2() const
    {
      return hot_min_cnt2_;
    }

    //--------------------------------------------------------------------------------
    inline void setHOTIterPerStage(size_type iterPerStage)
    {
      hot_iterPerStage_ = iterPerStage;
    }

    //--------------------------------------------------------------------------------
    inline size_type getHOTIterPerStage() const
    {
      return hot_iterPerStage_;
    }

    //--------------------------------------------------------------------------------
    inline void setHOTMaxPerStage(int maxPerStage)
    {
      hot_maxPerStage_ = maxPerStage;
    }

    //--------------------------------------------------------------------------------
    inline int getHOTMaxPerStage() const
    {
      return hot_maxPerStage_;
    }

    //--------------------------------------------------------------------------------
    inline void setHOTMaxCoincidenceSplitsPerRound(size_type m)
    {
      hot_maxCoincidenceSplitsPerRound_ = m;
    }

    //--------------------------------------------------------------------------------
    inline size_type getHOTMaxCoincidenceSplitsPerRound() const
    {
      return hot_maxCoincidenceSplitsPerRound_;
    }

    //--------------------------------------------------------------------------------
    inline bool getHOTHandleSelfTransitions() const
    {
      return hot_handleSelf_;
    }

    //--------------------------------------------------------------------------------
    inline void setHOTHandleSelfTransitions(bool handleSelf)
    {
      hot_handleSelf_ = handleSelf;
    }

    //--------------------------------------------------------------------------------
    inline bool usesHOT() const
    {
      return hot_nRounds_ > 0;
    }

    //--------------------------------------------------------------------------------
    inline size_t getHOTNStates() const
    {
      return hot_s2c_.size();
    }

    //--------------------------------------------------------------------------------
    /**
     * Watch out! The returned SparseMatrix encodes the coincidences starting at 1!
     */
    inline const HOTC2S& getHOTC2S() const 
    {
      return hot_c2s_;
    }

    //--------------------------------------------------------------------------------
    inline const HOTS2C& getHOTS2C() const
    {
      return hot_s2c_;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of original coincidences (does not count the states
     * created by HOT).
     */
    inline size_type getNCoincidences() const
    {
      return this->nRows() - hot_s2c_.size();
    }

    //--------------------------------------------------------------------------------
    /**
     * !!! WATCH OUT !!!
     * The state and coincidence indices are interleaved!!!
     * But this function returns the coincidence indices as if there were no states, 
     * i.e. if '6' is a coincidence index that happens to correspond to the 3rd 
     * real coincidence because there are 3 states inserted before the '6'-th 
     * coincidence, this method returns '3'.
     */
    inline size_type getHOTCoincidence(size_type state) const
    {
      typename HOTS2C::const_iterator it, e = hot_s2c_.end();

      it = hot_s2c_.find(state);

      if (it != e)
        return it->second;

      if (hot_s2c_.lower_bound(state) == e)
        return state;

      size_type n = 0;
      for (it = hot_s2c_.begin(); it != e && it->first < state; ++it)
        ++n;

      return state - n;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the state to update when encountering a given previous -> current
     * transition.
     */
    inline size_type getHOTState(size_type previous, size_type current) const
    {
      return const_cast<self_type&>(*this).getHOT_C2S_(previous, current);
    }

    //--------------------------------------------------------------------------------
    /**
     * Collapses TAM.
     */
    inline void HOTCollapse(self_type& collapsed) const
    {
      using namespace std;

      size_type nrows = this->nRows();
      size_type nc = getNCoincidences();
      collapsed.resize(nc, nc);

      for (size_type row = 0; row != nrows; ++row) {
        size_type *ind = this->ind_begin_(row);
        size_type *ind_end = this->ind_end_(row);
        value_type *nz = this->nz_begin_(row);
        size_type dst = getHOTCoincidence(row);
        for (; ind != ind_end; ++ind, ++nz) {
          collapsed.increment(dst, getHOTCoincidence(*ind), *nz);
        }
      }
    }

    //--------------------------------------------------------------------------------

  private:
    size_type transitionMemory_;
    std::vector<History> history_;

    // HOT
    size_type hot_nRounds_;      // number of HOT graph modification rounds
    float     hot_min_cnt2_;     // threshold for splitting
    size_type hot_nStates_;      // aggregate number of split states and coincidences
    size_type hot_iterPerStage_; // learning iterations between HOT 
    int       hot_maxPerStage_;  // max number of new splits per HOT
    /// Maximum number of splits of a unique coincidence per round of HOT.
    size_type hot_maxCoincidenceSplitsPerRound_;
    // Whether to treat self-transitions in a way that is different from others.
    bool      hot_handleSelf_;   
    HOTS2C    hot_s2c_;          // state to coincidence 
    HOTC2S    hot_c2s_;          // (coincidence or state) -> coincidence : state

  public:
    // Turn those on to trace either the learning or the HOT splitting
    // algorithm. Those traces are off by default. They are public
    // so that we can set them from Python directly. 
    size_type trace_learning;
    size_type trace_hot;

  private:
    //--------------------------------------------------------------------------------
    /**
     * Set a new entry in the c2s sparse table. c2s is a table where the rows are 
     * coincidence or states indices, and the columns correspond to coincidence
     * indices in the original alphabet. When learning, we use that table to find 
     * the split state corresponding to a given transition from a coincidence or state
     * into the current digit (in the original alphabet). 
     * HOT will periodically overwrite entries, when a split state is re-split.
     */
    inline void setHOT_C2S_(size_type p, size_type c, size_type i)
    {
      if (p >= hot_c2s_.nRows())
        hot_c2s_.resize(p+1, hot_c2s_.nCols());
      if (c >= hot_c2s_.nCols())
        hot_c2s_.resize(hot_c2s_.nRows(), c+1);
      hot_c2s_.setNonZero(p, c, i+1); 
    }

    //--------------------------------------------------------------------------------
    /**
     * If there is no entry for a transition (coincidence/state -> current digit), then
     * we return the current digit. Otherwise, we find the split state that was 
     * created to track the transition.
     */
    inline size_type getHOT_C2S_(size_type p, size_type c) 
    {
      if (p >= hot_c2s_.nRows() || c >= hot_c2s_.nCols())
        return c;

      size_type cc = (size_type) hot_c2s_.get(p, c);
      return cc == 0 ? c : (cc - 1);
    }

    //--------------------------------------------------------------------------------
    /**
     * c2s and s2c are built to contain original coincidence indices, 
     * so this method always returns a coincidence index in the original alphabet.
     *
     * !!! WATCH OUT !!!
     * Coincidence indices are interleaved with states indices!
     * If this method returns '6' for example, it might be only the 3rd coincidence
     * if 3 states have been inserted already! 
     */
    inline size_type getHOTCoincidence_(size_type state) const
    {
      typename HOTS2C::const_iterator it;

      it = hot_s2c_.find(state);

      if (it == hot_s2c_.end())
        return state;
      else
        return it->second;
    }

  private:
    //--------------------------------------------------------------------------------
    inline void print_debug_HOT_C2S_() const
    {
      using namespace std;

      if (hot_c2s_.nNonZeros() == 0)
        cout  << "hot_c2s_ is empty" << endl;
      else {
        cout << "hot_c2s_: " << hot_c2s_.nRows() << " rows, "
             << hot_c2s_.nCols() << " cols, "
             << hot_c2s_.nNonZeros() << " non-zeros."
             << endl;
        for (size_type i = 0; i != hot_c2s_.nRows(); ++i) {
          if (hot_c2s_.nNonZerosOnRow(i) > 0) {
            cout << i << " to: ";
            for (size_type j = 0; j != hot_c2s_.nCols(); ++j)
              if ((size_type) hot_c2s_.get(i, j) != 0)
                cout << j << ":" << (size_type) hot_c2s_.get(i, j) - 1 << " ";
            cout << endl;
          }
        }
      }
    }

  public:
    //--------------------------------------------------------------------------------
    // PERSISTENCE
    //--------------------------------------------------------------------------------
    inline void saveState(std::ostream& outStream) const
    {
      {
        NTA_CHECK(outStream.good())
          << "TAM::saveState(): "
          << "- Bad stream";
      }

      outStream << "TAM4 ";
      outStream << transitionMemory_ << " ";
      outStream << history_.size() << " ";

      for (size_type i = 0; i != history_.size(); ++i) {
        outStream << history_[i].size() << " ";
        for (size_type j = 0; j != history_[i].size(); ++j) {
          outStream << history_[i][j] << " ";
        }
      } 

      this->toCSR(outStream);
      outStream << " ";

      // HOT
      outStream << hot_nRounds_ << " "
                << hot_min_cnt2_ << " "
                << hot_nStates_ << " "
                << hot_iterPerStage_ << " "
                << hot_maxPerStage_ << " "
                << hot_maxCoincidenceSplitsPerRound_ << " "
                << hot_handleSelf_ << " "
                << hot_s2c_ << " ";
      hot_c2s_.toCSR(outStream);
    }

    //--------------------------------------------------------------------------------
    inline void readState(std::istream& inStream)
    {
      {
        NTA_CHECK(inStream.good())
          << "TAM::readState(): "
          << " - Bad stream";
      }

      std::string version;
      inStream >> version;

      size_type versionNumber = 0;

      if (version.find("TAM") != 0) {
        versionNumber = 0;
      }
      else 
        {
          if (version == "TAM1.6") {
            versionNumber = 1;
          }
          else if (version == "TAM1.6.1") {
            versionNumber = 2;
          }
          else if (version == "TAM3") {
            versionNumber = 3;
          }
          else if (version == "TAM4") {
            versionNumber = 4;
          }
        }
       
      if (versionNumber == 0) { 
        transitionMemory_ = atoi(version.c_str());
      }
      else {
        inStream >> transitionMemory_;
      }
      
      NTA_CHECK(transitionMemory_ > 0)
        << "TAM::readState(): Invalid transition memory: " 
        << transitionMemory_
        << " - Should be > 0";

      size_type hs = 0;
      inStream >> hs;

      NTA_CHECK(hs > 0)
        << "TAM::readState(): Invalid history size: " << hs
        << " - Should be >= 0";

      history_.resize(hs);

      for (size_type i = 0; i != hs; ++i) {

        size_type baby_hs = 0;
        inStream >> baby_hs;
        
        NTA_CHECK(baby_hs >= 0)
          << "TAM::readState(): Invalid history size: " << baby_hs
          << " for baby node: " << i
          << " - Should be > 0";
        
        history_[i].resize(baby_hs);
        
        for (size_type j = 0; j != baby_hs; ++j) {
        
          size_type h = 0;
          inStream >> h;
        
          NTA_CHECK(h >= 0) 
            << "TAM::readState(): "
            << "Invalid value for history: " << h
            << " - History values should be >= 0";
        
          history_[i][j] = h;
        }
      }

      this->fromCSR(inStream);

      for (size_type i = 0; i != hs; ++i) 
        for (size_type j = 0; j != history_[i].size(); ++j)
          NTA_CHECK(history_[i][j] <= this->nRows())
            << "TAM::readState(): "
            << "Invalid value for history: " << history_[i][j]
            << " - History values should be less than tam size: " << this->nRows();

      if (versionNumber > 0) {
        // HOT
        inStream >> hot_nRounds_
                 >> hot_min_cnt2_
                 >> hot_nStates_;

        if (versionNumber == 1) { // Throw-away.
          size_type hot_iter = 0;
          inStream >> hot_iter;
        }

        inStream >> hot_iterPerStage_;
        inStream >> hot_maxPerStage_;

        if (versionNumber >= 3)
          inStream >> hot_maxCoincidenceSplitsPerRound_;
        else
          hot_maxCoincidenceSplitsPerRound_ = 0;

        if (versionNumber >= 4)
          inStream >> hot_handleSelf_;
        else
          hot_handleSelf_ = false;

        inStream >> hot_s2c_;
        hot_c2s_.fromCSR(inStream);
      }
    }
  };

  //--------------------------------------------------------------------------------

} // end namespace nta

#endif // NTA_TAM_HPP



