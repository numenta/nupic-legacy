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

#ifndef NTA_Cells4_HPP
#define NTA_Cells4_HPP

#include <ostream>
#include <sstream>
#include <fstream>
#include <nta/types/types.hpp>
#include <nta/algorithms/Segment.hpp>
#include <nta/algorithms/OutSynapse.hpp>
#include <queue>
#include <cstring>


//-----------------------------------------------------------------------
/**
 * Overview
 * ========
 *
 * The Cells4 class is the primary class implementing the C++ version of
 * the temporal pooler. It is designed to be fully accessible from Python.
 * A primary design goal is to maintain exact functional correspondence
 * with the implementation in TP.py.  Given the same inputs, and the same
 * random number seed, the learned segments should be identical in the
 * two implementations. The structure, and method/member
 * variable names also closely matches TP.py.  As such, much of the
 * detailed documentation for the various parameters and methods
 * can be found in the comments in TP.py.
 *
 * Implementation Notes
 * ====================
 *
 * The Cells4 class contains a vector of Cell's. Each Cell instance
 * contains a list of Segments. Each Segment contains Synapses.
 *
 * Cells4 also maintains additional data structures for optimization
 * purposes. The OutSynapses maintain forward propagation data about
 * which Cell's project to which Cell's and Segments.
 *
 * The Cells4 class is used extensively by Python code. Most of the
 * methods are wrapped automatically by SWIG. Some additional methods
 * are explicitly defined in algorithms_impl.i. The memory for
 * certain states, such as _infActiveStateT, can be initialized as
 * pointers to numpy array buffers, avoiding a copy step.
 */

namespace nta {
  namespace algorithms {
    namespace Cells4 {

      class Cell;
      class Cells4;
      class SegmentUpdate;

      /**
       * Class CBasicActivity:
       * Manage activity counters
       *
       * This class is used by CCellSegActivity.  The counters stay well
       * below 255, allowing us to use UChar elements.  The biggest we
       * have seen is 33.  More important than the raw memory utilization
       * is the reduced pressure on L2 cache.  To see the difference,
       * benchmark this version, then try again after changing
       *
       * CCellSegActivity<UChar> _learnActivity;
       * CCellSegActivity<UChar> _inferActivity;
       *
       * to
       *
       * CCellSegActivity<UInt> _learnActivity;
       * CCellSegActivity<UInt> _inferActivity;
       *
       * We leave this class and CCellSegActivity templated to simplify
       * such testing.
       *
       * While we typically test on just one core, our production
       * configuration may run one engine on each core, thereby increasing
       * the pressure on L2.
       *
       * Counts are collected in one function, following a reset, and
       * used in another.
       *
       *                  Collected in                                     Used in
       * _learnActivity   computeForwardPropagation(CStateIndexed& state)  getBestMatchingCellT
       * _inferActivity   computeForwardPropagation(CState& state)         inferPhase2
       *
       * The _segment counts are the ones that matter.  The _cell counts
       * are an optimization technique.  They track the maximum count
       * for all segments in that cell.  Since segment counts are
       * interesting only if they exceed a threshold, we can skip all of
       * a cell's segments when the maximum is too small.
       *
       * Repeatedly resetting all the counters in large sparse arrays
       * can be costly, and much of the work is unnecessary when most
       * counters are already zero.  To address this, we track which
       * array elements are nonzero, and at reset time zero only those.
       * If an array is not so sparse, this selective zeroing may be
       * slower than a full memset().  We arbitrarily choose a threshold
       * of 6.25%, past which we use memset() instead of selective
       * zeroing.
       */
      const UInt _MAX_CELLS = 1 << 18;      // power of 2 allows efficient array indexing
      const UInt _MAX_SEGS  = 1 <<  7;      // power of 2 allows efficient array indexing
      typedef unsigned char UChar;          // custom type, since NTA_Byte = Byte is signed

      template <typename It>
      class CBasicActivity
      {
      public:
        CBasicActivity()
        {
          _counter = NULL;
          _nonzero = NULL;
          _size = 0;
          _dimension = 0;
        }
        ~CBasicActivity()
        {
          if (_counter != NULL)
            delete [] _counter;
          if (_nonzero != NULL)
            delete [] _nonzero;
        }
        void initialize(UInt n)
        {
          if (_counter != NULL)
            delete [] _counter;
          if (_nonzero != NULL)
            delete [] _nonzero;
          _counter = new It[n];                       // use typename here
          memset(_counter, 0, n * sizeof(_counter[0]));
          _nonzero = new UInt[n];
          _size = 0;
          _dimension = n;
        }
        UInt get(UInt cellIdx)
        {
          return _counter[cellIdx];
        }
        void add(UInt cellIdx, UInt incr)
        {
          // currently unused, but may need to resurrect
          if (_counter[cellIdx] == 0)
            _nonzero[_size++] = cellIdx;
          _counter[cellIdx] += incr;
        }
        It increment(UInt cellIdx)                    // use typename here
        {
          // In the learning phase, the activity count appears never to
          // reach 255.  Is this a safe assumption?
          if (_counter[cellIdx] != 0)
            return ++_counter[cellIdx];
          _counter[cellIdx] = 1;                      // without this, the inefficient compiler reloads the value from memory, increments it and stores it back
          _nonzero[_size++] = cellIdx;
          return 1;
        }
        void max(UInt cellIdx, It val)                // use typename here
        {
          const It curr = _counter[cellIdx];          // use typename here
          if (val > curr) {
            _counter[cellIdx] = val;
            if (curr == 0)
              _nonzero[_size++] = cellIdx;
          }
        }
        void reset()
        {
#define REPORT_ACTIVITY_STATISTICS 0
#if REPORT_ACTIVITY_STATISTICS
          // report the statistics for this table
          // Without a high water counter, we can't tell for sure if a
          // UChar counter overflowed, but it's likely there was no
          // overflow if all the other counters are below, say, 200.
          if (_size == 0) {
            std::cout << "Reset width=" << sizeof(It) << " all zeroes" << std::endl;
          }
          else {
            static std::vector<It> vectStat;
            vectStat.clear();
            UInt ndxStat;
            for (ndxStat = 0; ndxStat < _size; ndxStat++)
              vectStat.push_back(_counter[_nonzero[ndxStat]]);
            std::sort(vectStat.begin(), vectStat.end());
            std::cout << "Reset width=" << sizeof(It)
                      << " size=" << _dimension
                      << " nonzero=" << _size
                      << " min=" << UInt(vectStat.front())
                      << " max=" << UInt(vectStat.back())
                      << " med=" << UInt(vectStat[_size/2])
                      << std::endl;
          }
#endif
          // zero all the nonzero slots
          if (_size < _dimension / 16) {              // if fewer than 6.25% are nonzero
            UInt ndx;                                 // zero selectively
            for (ndx = 0; ndx < _size; ndx++)
              _counter[_nonzero[ndx]] = 0;
          }
          else {
            memset(_counter, 0, _dimension * sizeof(_counter[0]));
          }

          // no more nonzero slots
          _size = 0;
        }
      private:
        It * _counter;                                // use typename here
        UInt * _nonzero;
        UInt _size;
        UInt _dimension;
      };

      template <typename It>
      class CCellSegActivity
      {
      public:
        CCellSegActivity()
        {
          _cell.initialize(_MAX_CELLS);
          _seg.initialize(_MAX_CELLS * _MAX_SEGS);
        }
        UInt get(UInt cellIdx)
        {
          return _cell.get(cellIdx);
        }
        UInt get(UInt cellIdx, UInt segIdx)
        {
          return _seg.get(cellIdx * _MAX_SEGS + segIdx);
        }
        void increment(UInt cellIdx, UInt segIdx)
        {
          _cell.max(cellIdx, _seg.increment(cellIdx * _MAX_SEGS + segIdx));
        }
        void reset()
        {
          _cell.reset();
          _seg.reset();
        }
      private:
        CBasicActivity<It> _cell;
        CBasicActivity<It> _seg;
      };

      class Cells4
      {
      public:

        typedef Segment::InSynapses InSynapses;
        typedef std::vector<OutSynapse> OutSynapses;
        typedef std::vector<SegmentUpdate> SegmentUpdates;
        static const UInt VERSION = 2;

      private:
        nta::Random _rng;

        //-----------------------------------------------------------------------
        /**
         * Temporal pooler parameters, typically set by the user.
         * See TP.py for explanations.
         */
        UInt _nColumns;
        UInt _nCellsPerCol;
        UInt _nCells;
        UInt _activationThreshold;
        UInt _minThreshold;
        UInt _newSynapseCount;
        UInt _nIterations;
        UInt _nLrnIterations;
        UInt _segUpdateValidDuration;
        Real _permInitial;
        Real _permConnected;
        Real _permMax;
        Real _permDec;
        Real _permInc;
        Real _globalDecay;
        bool _doPooling;
        UInt _pamLength;
        UInt _maxInfBacktrack;
        UInt _maxLrnBacktrack;
        UInt _maxSeqLength;
        UInt _learnedSeqLength;
        Real _avgLearnedSeqLength;
        UInt _maxAge;
        UInt _verbosity;
        Int  _maxSegmentsPerCell;
        Int  _maxSynapsesPerSegment;
        bool _checkSynapseConsistency;    // If true, will perform time
                                          // consuming invariance checks.

        //-----------------------------------------------------------------------
        /**
         * Internal variables.
         */
        bool _resetCalled;          // True if reset() was called since the
                                    // last call to compute.
        Real _avgInputDensity;      // Average no. of non-zero inputs
        UInt _pamCounter;           // pamCounter gets reset to pamLength
                                    // whenever we detect that the learning
                                    // state is making good predictions
        UInt _version;

        //-----------------------------------------------------------------------
        /**
         * The various inference and learning states. See TP.py documentation
         *
         * Note: 'T1' means 't-1'
         * TODO: change to more compact data type (later)   2011-07-23 partly done.
         */
#define SOME_STATES_NOT_INDEXED 1
#if SOME_STATES_NOT_INDEXED
        CState _infActiveStateT;
        CState _infActiveStateT1;
        CState _infPredictedStateT;
        CState _infPredictedStateT1;
#else
        CStateIndexed _infActiveStateT;
        CStateIndexed _infActiveStateT1;
        CStateIndexed _infPredictedStateT;
        CStateIndexed _infPredictedStateT1;
#endif
        Real* _cellConfidenceT;
        Real* _cellConfidenceT1;
        Real* _colConfidenceT;
        Real* _colConfidenceT1;
        bool _ownsMemory;                   // If true, this class is responsible
                                            // for managing memory of above
                                            // eight arrays.


        CStateIndexed _learnActiveStateT;
        CStateIndexed _learnActiveStateT1;
        CStateIndexed _learnPredictedStateT;
        CStateIndexed _learnPredictedStateT1;

        Real* _cellConfidenceCandidate;
        Real* _colConfidenceCandidate;
        Real* _tmpInputBuffer;
#if SOME_STATES_NOT_INDEXED
        CState _infActiveStateCandidate;
        CState _infPredictedStateCandidate;
        CState _infActiveBackup;
        CState _infPredictedBackup;
#else
        CStateIndexed _infActiveStateCandidate;
        CStateIndexed _infPredictedStateCandidate;
        CStateIndexed _infActiveBackup;
        CStateIndexed _infPredictedBackup;
#endif

        //-----------------------------------------------------------------------
        /**
         * Internal data structures.
         */
        std::vector< Cell > _cells;
        std::deque<std::vector<UInt> > _prevInfPatterns;
        std::deque<std::vector<UInt> > _prevLrnPatterns;
        SegmentUpdates _segmentUpdates;

        //-----------------------------------------------------------------------
        /**
         * Internal data structures used for speed optimization.
         */
        std::vector<OutSynapses> _outSynapses;
        UInt _nIterationsSinceRebalance;
        CCellSegActivity<UChar> _learnActivity;
        // _inferActivity and _learnActivity use identical data
        // structures, and their use does not overlap
        #define _inferActivity _learnActivity

      public:
        //-----------------------------------------------------------------------
        /**
         * Default constructor needed when lifting from persistence.
         */
        Cells4(UInt nColumns =0, UInt nCellsPerCol =0,
               UInt activationThreshold =1,
               UInt minThreshold =1,
               UInt newSynapseCount =1,
               UInt segUpdateValidDuration =1,
               Real permInitial =.5,
               Real permConnected =.8,
               Real permMax =1,
               Real permDec =.1,
               Real permInc =.1,
               Real globalDecay =0,
               bool doPooling =false,
               int seed =-1,
               bool doItAll =false,
               bool checkSynapseConsistency =false);


        //----------------------------------------------------------------------
        /**
         * This also called when lifting from persistence.
         */
        void
        initialize(UInt nColumns =0, UInt nCellsPerCol =0,
                   UInt activationThreshold =1,
                   UInt minThreshold =1,
                   UInt newSynapseCount =1,
                   UInt segUpdateValidDuration =1,
                   Real permInitial =.5,
                   Real permConnected =.8,
                   Real permMax =1,
                   Real permDec =.1,
                   Real permInc =.1,
                   Real globalDecay =.1,
                   bool doPooling =false,
                   bool doItAll =false,
                   bool checkSynapseConsistency =false);

        //----------------------------------------------------------------------
        ~Cells4();

        //----------------------------------------------------------------------
        UInt version() const
        {
          return _version;
        }

        //----------------------------------------------------------------------
        /**
         * Call this when allocating numpy arrays, to have pointers use those
         * arrays.
         */
        void setStatePointers(Byte* infActiveT, Byte* infActiveT1,
                   Byte* infPredT, Byte* infPredT1,
                   Real* colConfidenceT, Real* colConfidenceT1,
                   Real* cellConfidenceT, Real* cellConfidenceT1)
        {
          if (_ownsMemory) {
            delete [] _cellConfidenceT;
            delete [] _cellConfidenceT1;
            delete [] _colConfidenceT;
            delete [] _colConfidenceT1;
          }

          _ownsMemory = false;

          _infActiveStateT.usePythonMemory(infActiveT, _nCells);
          _infActiveStateT1.usePythonMemory(infActiveT1, _nCells);
          _infPredictedStateT.usePythonMemory(infPredT, _nCells);
          _infPredictedStateT1.usePythonMemory(infPredT1, _nCells);
          _cellConfidenceT = cellConfidenceT;
          _cellConfidenceT1 = cellConfidenceT1;
          _colConfidenceT = colConfidenceT;
          _colConfidenceT1 = colConfidenceT1;
        }

        //-----------------------------------------------------------------------
        /**
         * Use this when C++ allocates memory for the arrays, and Python needs to look
         * at them.
         */
        void getStatePointers(Byte*& activeT, Byte*& activeT1,
                                     Byte*& predT, Byte*& predT1,
                                     Real*& colConfidenceT, Real*& colConfidenceT1,
                                     Real*& confidenceT, Real*& confidenceT1) const
        {
          NTA_ASSERT(_ownsMemory);

          activeT = _infActiveStateT.arrayPtr();
          activeT1 = _infActiveStateT1.arrayPtr();
          predT = _infPredictedStateT.arrayPtr();
          predT1 = _infPredictedStateT1.arrayPtr();
          confidenceT = _cellConfidenceT;
          confidenceT1 = _cellConfidenceT1;
          colConfidenceT = _colConfidenceT;
          colConfidenceT1 = _colConfidenceT1;
        }

        //-----------------------------------------------------------------------
        /**
         * Use this when Python needs to look up the learn states.
         */
        void getLearnStatePointers(Byte*& activeT, Byte*& activeT1,
                                   Byte*& predT, Byte*& predT1) const
        {
          activeT  = _learnActiveStateT.arrayPtr();
          activeT1 = _learnActiveStateT1.arrayPtr();
          predT    = _learnPredictedStateT.arrayPtr();
          predT1   = _learnPredictedStateT1.arrayPtr();
        }

        //----------------------------------------------------------------------
        /**
         * Accessors for getting various member variables
         */
        UInt nSegments() const;
        UInt nCells() const                 { return _nCells; }
        UInt nColumns() const               { return _nColumns; }
        UInt nCellsPerCol() const           { return _nCellsPerCol; }
        UInt getMinThreshold() const        { return _minThreshold; }
        Real getPermConnected() const       { return _permConnected; }
        UInt getVerbosity() const           { return _verbosity; }
        UInt getMaxAge() const              { return _maxAge; }
        UInt getPamLength() const           { return _pamLength; }
        UInt getMaxInfBacktrack() const     { return _maxInfBacktrack;}
        UInt getMaxLrnBacktrack() const     { return _maxLrnBacktrack;}
        UInt getPamCounter() const          { return _pamCounter;}
        UInt getMaxSeqLength() const        { return _maxSeqLength;}
        Real getAvgLearnedSeqLength() const { return _avgLearnedSeqLength;}
        UInt getNLrnIterations() const      { return _nLrnIterations;}
        Int  getmaxSegmentsPerCell() const  { return _maxSegmentsPerCell;}
        Int  getMaxSynapsesPerCell() const  { return _maxSynapsesPerSegment;}
        bool getCheckSynapseConsistency()   { return _checkSynapseConsistency;}


        //----------------------------------------------------------------------
        /**
         * Accessors for setting various member variables
         */
        void setMaxInfBacktrack(UInt t)   {_maxInfBacktrack = t;}
        void setMaxLrnBacktrack(UInt t)   {_maxLrnBacktrack = t;}
        void setVerbosity(UInt v)         {_verbosity = v; }
        void setMaxAge(UInt a)            {_maxAge = a; }
        void setMaxSeqLength(UInt v)      {_maxSeqLength = v;}
        void setCheckSynapseConsistency(bool val)
                                          { _checkSynapseConsistency = val;}

        void setMaxSegmentsPerCell(int maxSegs) {
          if (maxSegs != -1) {
            NTA_CHECK(maxSegs > 0);
            NTA_CHECK(_globalDecay == 0.0);
            NTA_CHECK(_maxAge == 0);
          }
          _maxSegmentsPerCell = maxSegs;
        }

        void setMaxSynapsesPerCell(int maxSyns) {
          if (maxSyns != -1) {
            NTA_CHECK(maxSyns > 0);
            NTA_CHECK(_globalDecay == 0.0);
            NTA_CHECK(_maxAge == 0);
          }
          _maxSynapsesPerSegment = maxSyns;
        }

        void setPamLength(UInt pl)
        {
          NTA_CHECK(pl > 0);
          _pamLength = pl;
          _pamCounter = _pamLength;
        }


        //-----------------------------------------------------------------------
        /**
         * Returns the number of segments currently in use on the given cell.
         */
        UInt nSegmentsOnCell(UInt colIdx, UInt cellIdxInCol) const;

        //-----------------------------------------------------------------------
        UInt nSynapses() const;

        //-----------------------------------------------------------------------
        /**
         * WRONG ONE if you want the current number of segments with actual synapses
         * on the cell!!!!
         * This one counts the total number of segments ever allocated on a cell, which
         * includes empty segments that have been previously freed.
         */
        UInt __nSegmentsOnCell(UInt cellIdx) const;

        //-----------------------------------------------------------------------
        /**
         * Total number of synapses in a given cell (at at given point, changes all the
         * time).
         */
        UInt nSynapsesInCell(UInt cellIdx) const;


        //-----------------------------------------------------------------------
        Cell* getCell(UInt colIdx, UInt cellIdxInCol);

        //-----------------------------------------------------------------------
        UInt getCellIdx(UInt colIdx, UInt cellIdxInCol);

        //-----------------------------------------------------------------------
        /**
         * Can return a previously freed segment (segment size == 0) if called with a segIdx
         * which is in the "free" list of the cell.
         */
        Segment*
        getSegment(UInt colIdx, UInt cellIdxInCol, UInt segIdx);

        //-----------------------------------------------------------------------
        /**
         * Can return a previously freed segment (segment size == 0) if called with a segIdx
         * which is in the "free" list of the cell.
         */
        Segment& segment(UInt cellIdx, UInt segIdx);

        //----------------------------------------------------------------------
        //----------------------------------------------------------------------
        //
        // ROUTINES USED IN PERFORMING INFERENCE AND LEARNING
        //
        //----------------------------------------------------------------------
        //----------------------------------------------------------------------

        //-----------------------------------------------------------------------
        /**
         * Main compute routine, called for both learning and inference.
         *
         * Parameters:
         * ===========
         *
         * input:           array representing bottom up input
         * output:          array representing inference output
         * doInference:     if true, inference output will be computed
         * doLearning:      if true, learning will occur
         */
        void compute(Real* input, Real* output, bool doInference, bool doLearning);

        //-----------------------------------------------------------------------
        /**
         */
        void reset();

        //----------------------------------------------------------------------
        bool isActive(UInt cellIdx, UInt segIdx, const CState& state) const;

        //----------------------------------------------------------------------
        /**
         * Find weakly activated cell in column.
         *
         * Parameters:
         * ==========
         * colIdx:         index of column in which to search
         * state:          the array of cell activities
         * minThreshold:   only consider segments with activity >= minThreshold
         * useSegActivity: if true, use forward prop segment activity values
         *
         * Return value: index and segment of most activated segment whose
         * activity is >= minThreshold. The index returned for the cell
         * is between 0 and _nCells, *not* a cell index inside the column.
         * If no cells are found, return ((UInt) -1, (UInt) -1).
         */
        std::pair<UInt, UInt> getBestMatchingCellT(UInt colIdx, const CState& state, UInt minThreshold);
        std::pair<UInt, UInt> getBestMatchingCellT1(UInt colIdx, const CState& state, UInt minThreshold);

        //----------------------------------------------------------------------
        /**
         * Compute cell and segment activities using forward propagation
         * and the given state variable.
         *
         * 2011-08-11: We will remove the CState& function if we can
         * convert _infActiveStateT from a CState object to CStateIndexed
         * without degrading performance.  Conversion will also require us
         * to move all state array modifications from Python to C++.  One
         * known offender is TP.py.
         */
        void computeForwardPropagation(CStateIndexed& state);
#if SOME_STATES_NOT_INDEXED
        void computeForwardPropagation(CState& state);
#endif

        //----------------------------------------------------------------------
        //----------------------------------------------------------------------
        //
        // ROUTINES FOR PERFORMING INFERENCE
        //
        //----------------------------------------------------------------------
        //----------------------------------------------------------------------

        //----------------------------------------------------------------------
        /**
         * Update the inference state. Called from compute() on every iteration
         *
         * Parameters:
         * ===========
         *
         * activeColumns:   Indices of active columns
         */
        void updateInferenceState(const std::vector<UInt> & activeColumns);

        //----------------------------------------------------------------------
        /**
         * Update the inference active state from the last set of predictions
         * and the current bottom-up.
         *
         * Parameters:
         * ===========
         *
         * activeColumns:   Indices of active columns
         * useStartCells:   If true, ignore previous predictions and simply
         *                  turn on the start cells in the active columns
         *
         * Return value:    whether or not we are in a sequence.
         *                  'true' if the current input was sufficiently
         *                  predicted, OR if we started over on startCells.
         *                  'false' indicates that the current input was NOT
         *                  predicted, and we are now bursting on most columns.
         *
         */
        bool inferPhase1(const std::vector<UInt> & activeColumns, bool useStartCells);

        //-----------------------------------------------------------------------
        /**
         * Phase 2 for the inference state. The computes the predicted state,
         * then checks to insure that the predicted state is not over-saturated,
         * i.e. look too close like a burst. This indicates that there were so
         * many separate paths learned from the current input columns to the
         * predicted input columns that bursting on the current input columns
         * is most likely generated mix and match errors on cells in the
         * predicted columns. If we detect this situation, we instead turn on
         * only the start cells in the current active columns and re-generate
         * the predicted state from those.
         *
         * Return value:    'true' if we have at least some guess  as to the
         *                  next input. 'false' indicates that we have reached
         *                  the end of a learned sequence.
         *
         */
        bool inferPhase2();

        //-----------------------------------------------------------------------
        /**
         * This "backtracks" our inference state, trying to see if we can lock
         * onto the current set of inputs by assuming the sequence started N
         * steps ago on start cells. For details please see documentation in
         * TP.py
         *
         * Parameters:
         * ===========
         *
         * activeColumns:   Indices of active columns
         */
        void inferBacktrack(const std::vector<UInt> & activeColumns);

        //----------------------------------------------------------------------
        //----------------------------------------------------------------------
        //
        // ROUTINES FOR PERFORMING LEARNING
        //
        //----------------------------------------------------------------------
        //----------------------------------------------------------------------

        //----------------------------------------------------------------------
        /**
         * Update the learning state. Called from compute()
         *
         * Parameters:
         * ===========
         *
         * activeColumns:   Indices of active columns
         */
        void updateLearningState(const std::vector<UInt> & activeColumns,
                                 Real* input);

        //-----------------------------------------------------------------------
        /**
         * Compute the learning active state given the predicted state and
         * the bottom-up input.
         *
         *
         * Parameters:
         * ===========
         *
         * activeColumns:   Indices of active columns
         * readOnly:        True if being called from backtracking logic.
         *                  This tells us not to increment any segment
         *                  duty cycles or queue up any updates.
         *
         * Return value:    'true' if the current input was sufficiently
         *                  predicted, OR if we started over on startCells.
         *                  'false' indicates that the current input was NOT
         *                  predicted well enough to be considered inSequence
         *
         */
        bool learnPhase1(const std::vector<UInt> & activeColumns, bool readOnly);

        //-----------------------------------------------------------------------
        /**
         * Compute the predicted segments given the current set of active cells.
         *
         * This computes the lrnPredictedState['t'] and queues up any segments
         * that became active (and the list of active synapses for each
         * segment) into the segmentUpdates queue
         *
         * Parameters:
         * ===========
         *
         * readOnly:        True if being called from backtracking logic.
         *                  This tells us not to increment any segment
         *                  duty cycles or queue up any updates.
         *
         */
        void learnPhase2(bool readOnly);

        //-----------------------------------------------------------------------
        /**
         * This "backtracks" our learning state, trying to see if we can lock
         * onto the current set of inputs by assuming the sequence started
         * up to N steps ago on start cells.
         *
         */
        UInt learnBacktrack();

        //-----------------------------------------------------------------------
        /**
         * A utility method called from learnBacktrack. This will backtrack
         * starting from the given startOffset in our prevLrnPatterns queue.
         *
         * It returns True if the backtrack was successful and we managed to get
         * predictions all the way up to the current time step.
         *
         * If readOnly, then no segments are updated or modified, otherwise, all
         * segment updates that belong to the given path are applied.
         *
         */
        bool learnBacktrackFrom(UInt startOffset, bool readOnly);

        //-----------------------------------------------------------------------
        /**
         * Update our moving average of learned sequence length.
         */
        void _updateAvgLearnedSeqLength(UInt prevSeqLength);

        //----------------------------------------------------------------------
        /**
         * Choose n random cells to learn from, using cells with activity in
         * the state array. The passed in srcCells are excluded.
         *
         * Parameters:
         * - cellIdx:        the destination cell to pick sources for
         * - segIdx:         the destination segment to pick sources for
         * - nSynToAdd:      the numbers of synapses to add
         *
         * Return:
         * - srcCells:       contains the chosen source cell indices upon return
         *
         * NOTE: don't forget to keep cell indices sorted!!!
         * TODO: make sure we don't pick a cell that's already a src for that seg
         */
        void
        chooseCellsToLearnFrom(UInt cellIdx, UInt segIdx,
                               UInt nSynToAdd, CStateIndexed& state, std::vector<UInt>& srcCells);

        //----------------------------------------------------------------------
        /**
         * Return the index of a cell in this column which is a good candidate
         * for adding a new segment.
         *
         * When we have fixed size resources in effect, we insure that we pick a
         * cell which does not already have the max number of allowed segments.
         * If none exists, we choose the least used segment in the column to
         * re-allocate. Note that this routine should never return the start
         * cell (cellIdx 0) if we have more than one cell per column.
         *
         * Parameters:
         * - colIdx:        which column to look at
         *
         * Return:
         * - cellIdx:       index of the chosen cell
         *
         */
        UInt getCellForNewSegment(UInt colIdx);


        //----------------------------------------------------------------------
        /**
         * Insert a segmentUpdate data structure containing a list of proposed changes
         * to segment segIdx. If newSynapses
         * is true, then newSynapseCount - len(activeSynapses) synapses are added to
         * activeSynapses. These synapses are randomly chosen from the set of cells
         * that have learnState = 1 at timeStep.
         *
         * Return: true if a new segmentUpdate data structure was pushed onto
         * the list.
         *
         * NOTE: called getSegmentActiveSynapses in Python
         *
         */
        bool computeUpdate(UInt cellIdx, UInt segIdx, CStateIndexed& activeState,
                           bool sequenceSegmentFlag, bool newSynapsesFlag);

        //----------------------------------------------------------------------
        /**
         * Adds OutSynapses to the internal data structure that maintains OutSynapses
         * for each InSynapses. This enables us to propagation activation forward, which
         * is faster since activation is sparse.
         *
         * This is a templated method because sometimes we are called with
         * std::set<UInt>::const_iterator and sometimes with
         * std::vector<UInt>::const_iterator
         */

        template <typename It>
        void addOutSynapses(UInt dstCellIdx, UInt dstSegIdx,
                            It newSynapse,
                            It newSynapsesEnd);

        //----------------------------------------------------------------------
        /**
         * Erases an OutSynapses. See addOutSynapses just above.
         */
        void eraseOutSynapses(UInt dstCellIdx, UInt dstSegIdx,
                              const std::vector<UInt>& srcCells);

        //----------------------------------------------------------------------
        /**
         * Go through the list of accumulated segment updates and process them
         * as follows:
         *
         * if       the segment update is too old, remove the update
         *
         * elseif   the cell received bottom-up input (activeColumns==1) update
         *          its permanences then positively adapt this segment
         *
         * elseif   the cell is still being predicted, and pooling is on then leave it
         *          in the queue
         *
         * else     remove it from the queue.
         *
         * Parameters:
         * ===========
         *
         * activeColumns:   array of _nColumns columns which are currently active
         * predictedState:  array of _nCells states representing predictions for each
         *                  cell
         *
         */
        void processSegmentUpdates(Real* input, const CState& predictedState);

        //----------------------------------------------------------------------
        /**
         * Removes any updates that would be applied to the given col,
         * cellIdx, segIdx.
         */
        void cleanUpdatesList(UInt cellIdx, UInt segIdx);

        //----------------------------------------------------------------------
        /**
         * Apply age-based global decay logic and remove segments/synapses
         * as appropriate.
         */
        void applyGlobalDecay();

        //-----------------------------------------------------------------------
        /**
         * Applies segment update information to a segment in a cell as follows:
         *
         * If the segment exists, synapses on the active list get their
         * permanence counts incremented by permanenceInc. All other synapses
         * get their permanence counts decremented by permanenceDec. If
         * a synapse's permanence drops to zero, it is removed from the segment.
         * If a segment does not have synapses anymore, it is removed from the
         * Cell. We also increment the positiveActivations count of the segment.
         *
         * If the segment does not exist, it is created using the synapses in
         * update.
         *
         * Parameters:
         * ===========
         *
         * update:        segmentUpdate instance
         */
        void adaptSegment(const SegmentUpdate& update);

        //-----------------------------------------------------------------------
        /**
         * This method deletes all synapses where permanence value is strictly
         * less than minPermanence. It also deletes all segments where the
         * number of connected synapses is strictly less than minNumSyns+1.
         * Returns the number of segments and synapses removed.
         *
         * Parameters:
         *
         * minPermanence:      Any syn whose permamence is 0 or < minPermanence
         *                     will be deleted. If 0 is passed in, then
         *                     _permConnected is used.
         * minNumSyns:         Any segment with less than minNumSyns synapses
         *                     remaining in it will be deleted. If 0 is passed
         *                     in, then _activationThreshold is used.
         *
         */
        std::pair<UInt, UInt> trimSegments(Real minPermanence, UInt minNumSyns);


        //----------------------------------------------------------------------
        //----------------------------------------------------------------------
        //
        // ROUTINES FOR PERSISTENCE
        //
        //----------------------------------------------------------------------
        //----------------------------------------------------------------------

        /**
         * TODO: compute, rather than writing to a buffer.
         * TODO: move persistence to binary, faster and easier to compute expecte size.
         */
        UInt persistentSize() const
        {
          // TODO: this won't scale!
          std::stringstream tmp;
          this->save(tmp);
          return tmp.str().size();
        }

        //----------------------------------------------------------------------
        /**
         * Save the state to the given file
         */
        void saveToFile(std::string filePath) const;

        //----------------------------------------------------------------------
        /**
         * Load the state from the given file
         */
        void loadFromFile(std::string filePath);

        //----------------------------------------------------------------------
        void save(std::ostream& outStream) const;

        //-----------------------------------------------------------------------
        /**
         * Need to load and re-propagate activities so that we can really persist
         * at any point, load back and resume inference at exactly the same point.
         */
        void load(std::istream& inStream);

        //-----------------------------------------------------------------------
        void print(std::ostream& outStream) const;

        //----------------------------------------------------------------------
        //----------------------------------------------------------------------
        //
        // MISC SUPPORT AND DEBUGGING ROUTINES
        //
        //----------------------------------------------------------------------
        //----------------------------------------------------------------------

        // Set the Cell class segment order
        void setCellSegmentOrder(bool matchPythonOrder);

        //----------------------------------------------------------------------
        /**
         * Used in unit tests and debugging.
         */
        void
        addNewSegment(UInt colIdx, UInt cellIdxInCol,
                      bool sequenceSegmentFlag,
                      const std::vector<std::pair<UInt, UInt> >& extSynapses);

        void
        updateSegment(UInt colIdx, UInt cellIdxInCol, UInt segIdx,
                      const std::vector<std::pair<UInt, UInt> >& extSynapses);

        //-----------------------------------------------------------------------
        /**
         * Rebalances and rebuilds internal structures for faster computing
         *
         */
        void _rebalance();
        void rebuildOutSynapses();
        void trimOldSegments(UInt age);

        //----------------------------------------------------------------------
        /**
         * Various debugging helpers
         */
        void printStates();
        void printState(UInt *state);
        void dumpPrevPatterns(std::deque<std::vector<UInt> > &patterns);
        void dumpSegmentUpdates();

        //-----------------------------------------------------------------------
        /**
         * Returns list of indices of segments that are *not* empty in the free list.
         */
        std::vector<UInt>
        getNonEmptySegList(UInt colIdx, UInt cellIdxInCol);


        //-----------------------------------------------------------------------
        /**
         * Dump timing results to stdout
         */
        void dumpTiming();

        //-----------------------------------------------------------------------
        // Reset all timers to 0
        //-----------------------------------------------------------------------
        void resetTimers();

        //-----------------------------------------------------------------------
        // Invariants
        //-----------------------------------------------------------------------
        /**
         * Performs a number of consistency checks. The test takes some time
         * but is very helpful in development. The test is run during load/save.
         * It is also run on every compute if _checkSynapseConsistency is true
         */
        bool invariants(bool verbose = false) const;

        //-----------------------------------------------------------------------
        // Statistics
        //-----------------------------------------------------------------------
        void stats() const
        {
          return;
        }

      };

      //-----------------------------------------------------------------------
#ifndef SWIG
      std::ostream& operator<<(std::ostream& outStream, const Cells4& cells);
#endif

      //-----------------------------------------------------------------------
    } // end namespace Cells4
  } // end namespace algorithms
} // end namespace nta

  //-----------------------------------------------------------------------
#endif // NTA_Cells4_HPP
