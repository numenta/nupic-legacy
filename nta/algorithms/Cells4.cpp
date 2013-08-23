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

// #include <iostream>
#include <iomanip>
#include <vector>
#include <iostream>
#include <limits>  // numeric_limits
#include <set>
#include <sstream>

#include <external/common/include/cycle_counter.hpp>
#include <nta/utils/Random.hpp>
#include <nta/utils/Log.hpp>
#include <assert.h>
#include <cstring>
#include <map>
#include <nta/math/array_algo.hpp> // is_in
#include <nta/math/stl_io.hpp> // binary_save
#include <nta/algorithms/Cells4.hpp>
#include <nta/algorithms/SegmentUpdate.hpp>
#include <nta/algorithms/Cell.hpp>
#include <nta/os/FStream.hpp>

#include <nta/os/Timer.hpp>

using namespace nta::algorithms::Cells4;

// Comment or uncomment to turn on timing
//#define CELLS4_TIMING

// Various timers and instrumentation contingent on above flag
#ifdef CELLS4_TIMING

#define TIMER(code) (code)

static nta::Timer computeTimer, inferenceTimer, learningTimer;
static nta::Timer learnPhase1Timer, learnPhase2Timer, learnBacktrackTimer;
static nta::Timer infPhase1Timer, infPhase2Timer, infBacktrackTimer;
static nta::Timer forwardLearnPropTimer, forwardInfPropTimer;
static nta::Timer getNewCellTimer, adaptSegmentTimer;
static nta::Timer chooseCellsTimer;

#else

#define TIMER(code)

#endif

Cells4::Cells4(UInt nColumns, UInt nCellsPerCol,
                     UInt activationThreshold,
                     UInt minThreshold,
                     UInt newSynapseCount,
                     UInt segUpdateValidDuration,
                     Real permInitial,
                     Real permConnected,
                     Real permMax,
                     Real permDec,
                     Real permInc,
                     Real globalDecay,
                     bool doPooling,
                     int seed,
                     bool doItAll,
                     bool checkSynapseConsistency)
  : _rng(seed < 0 ? rand() : seed)
{
  _version = VERSION;
  initialize(nColumns,
             nCellsPerCol,
             activationThreshold,
             minThreshold,
             newSynapseCount,
             segUpdateValidDuration,
             permInitial,
             permConnected,
             permMax,
             permDec,
             permInc,
             globalDecay,
             doPooling,
             doItAll,
             checkSynapseConsistency);
}

Cells4::~Cells4()
{
  if (_ownsMemory) {
    delete [] _cellConfidenceT;
    delete [] _cellConfidenceT1;
    delete [] _colConfidenceT;
    delete [] _colConfidenceT1;
  }
  delete [] _cellConfidenceCandidate;
  delete [] _colConfidenceCandidate;
  delete [] _tmpInputBuffer;
}

//--------------------------------------------------------------------------------
// Utility routines used in this file to print list of active columns and cell indices
//--------------------------------------------------------------------------------
static void printActiveColumns(std::ostream& out, const std::vector<UInt> & activeColumns)
{
  out << "[";
  for (UInt i= 0; i < activeColumns.size(); i++) {
    out << " " << activeColumns[i];
  }
  out << "]";
}

static void printCell(UInt srcCellIdx, UInt nCellsPerCol)
{
  UInt col =  (UInt) (srcCellIdx / nCellsPerCol);
  UInt cell = srcCellIdx - col*nCellsPerCol;
  std::cout << "[" << col << "," << cell << "]  ";
}



//--------------------------------------------------------------------------------
bool Cells4::isActive(UInt cellIdx, UInt segIdx, const CState& state) const
{
  {
    NTA_ASSERT(cellIdx < nCells());
    NTA_ASSERT(segIdx < _cells[cellIdx].size());
  }

  const Segment& seg = _cells[cellIdx][segIdx];

  if (seg.size() < _activationThreshold)
    return false;
  else
    return seg.isActive(state, _permConnected, _activationThreshold);
}

//--------------------------------------------------------------------------------
/**
 * Push a segmentUpdate data structure containing a list of proposed changes
 * to segment s into our SegmentUpdate list. Return false if no update was actually
 * pushed (this can happen if we didn't find any new synapses).
 *
 * Let activeSynapses be the list of active synapses where the
 * originating cells have their activeState output = 1 at time step t.
 * (This list is empty if s is None since the segment doesn't exist.)
 * newSynapses is an optional argument that defaults to false. If newSynapses
 * is true, then newSynapseCount - len(activeSynapses) synapses are added to
 * activeSynapses. These synapses are randomly chosen from the set of cells
 * that have learnState = 1 at timeStep.
 *
 * NOTE: called getSegmentActiveSynapses in Python
 *
 */
bool Cells4::computeUpdate(UInt cellIdx, UInt segIdx, CStateIndexed& activeState,
                          bool sequenceSegmentFlag, bool newSynapsesFlag)
{
  {
    NTA_ASSERT(cellIdx < nCells());
    NTA_ASSERT(segIdx == (UInt) - 1 || segIdx < _cells[cellIdx].size());
  }

  static std::vector<UInt> newSynapses;
  newSynapses.clear();                 // purge residual data

  if (segIdx != (UInt) -1) { // not a new segment

    Segment& segment = _cells[cellIdx][segIdx];

    static UInt highWaterSize = 0;
    if (highWaterSize < segment.size()) {
      highWaterSize = segment.size();
      newSynapses.reserve(highWaterSize);
    }
    for (UInt i = 0; i != segment.size(); ++i)
      if (activeState.isSet(segment[i].srcCellIdx())) {
        newSynapses.push_back(segment[i].srcCellIdx());
      }
  }

  if (newSynapsesFlag) {

    int nSynToAdd = (int) _newSynapseCount - (int) newSynapses.size();

    if (nSynToAdd > 0) {
      chooseCellsToLearnFrom(cellIdx, segIdx, nSynToAdd, activeState, newSynapses);
    }
  }

  // It's possible that we didn't find any suitable connection to make
  // in which case we just give up silently.
  if (newSynapses.empty())
    return false;

  SegmentUpdate update(cellIdx, segIdx, sequenceSegmentFlag,
                       _nLrnIterations, newSynapses); // TODO: Add this for invariants check

  _segmentUpdates.push_back(update);
  return true;
}

//--------------------------------------------------------------------------------
/**
 * Adds OutSynapses to the internal data structure that maintains OutSynapses
 * for each InSynapses. This enables us to propagation activation forward, which
 * is faster since activation is sparse.
 *
 * This is a templated method because sometimes we are called with
 * std::set<UInt>::const_iterator and sometimes with
 * std::vector<UInt>::const_iterator
 * Explicit instantiations are just below.
 */

template <typename It>
void Cells4::addOutSynapses(UInt dstCellIdx, UInt dstSegIdx,
            It newSynapse,
            It newSynapsesEnd)
{
  NTA_ASSERT(dstCellIdx < nCells());
  NTA_ASSERT(dstSegIdx < _cells[dstCellIdx].size());

  for (; newSynapse != newSynapsesEnd; ++newSynapse) {
    UInt srcCellIdx = *newSynapse;
    OutSynapse newOutSyn(dstCellIdx, dstSegIdx);
    NTA_ASSERT(not_in(newOutSyn, _outSynapses[srcCellIdx]));
    _outSynapses[srcCellIdx].push_back(newOutSyn);
  }

}

// explicit instantiations for the method above
namespace nta {
  namespace algorithms {
    namespace Cells4 {
      template void Cells4::addOutSynapses(nta::UInt, nta::UInt,
                       std::set<nta::UInt>::const_iterator,
                       std::set<nta::UInt>::const_iterator);
      template void Cells4::addOutSynapses(nta::UInt, nta::UInt,
                       std::vector<nta::UInt>::const_iterator,
                       std::vector<nta::UInt>::const_iterator);

    }
  }
}


//--------------------------------------------------------------------------------
/**
 * Erases an OutSynapses. See addOutSynapses just above.
 */
void Cells4::eraseOutSynapses(UInt dstCellIdx, UInt dstSegIdx,
                  const std::vector<UInt>& srcCells)
{
  NTA_ASSERT(dstCellIdx < nCells());
  NTA_ASSERT(dstSegIdx < _cells[dstCellIdx].size());

  for (UInt i = 0; i != srcCells.size(); ++i) {
    UInt srcCellIdx = srcCells[i];
    OutSynapses& outSyns = _outSynapses[srcCellIdx];
    // TODO: binary search or faster
    for (UInt j = 0; j != outSyns.size(); ++j)
      if (outSyns[j].goesTo(dstCellIdx, dstSegIdx)) {
        std::swap(outSyns[j], outSyns[outSyns.size() - 1]);
        outSyns.resize(outSyns.size() - 1);
        break; // TODO: make sure we can do that
      }
  }
}

//--------------------------------------------------------------------------------
/**
 * This "backtracks" our inference state, trying to see if we can lock
 * onto the current set of inputs by assuming the sequence started N
 * steps ago on start cells.
 */
void Cells4::inferBacktrack(const std::vector<UInt> & activeColumns)
{
  //---------------------------------------------------------------------------
  // How much input history have we accumulated? Is it enough to backtrack?
  // The current input is always at the end of self._prevInfPatterns, but
  // it is also evaluated as a potential starting point
  if (_prevInfPatterns.size() == 0) return;

  TIMER(infBacktrackTimer.start());

  // This is an easy to use label for the current time step
  UInt currentTimeStepsOffset = _prevInfPatterns.size() - 1;

  //---------------------------------------------------------------------------
  // Save our current active state in case we fail to find a place to restart
  // Save our t-1 predicted state because we will write over it as we evaluate
  // each potential starting point.
  _infActiveBackup = _infActiveStateT;
  _infPredictedBackup = _infPredictedStateT1;

  // We will record which previous input patterns did not generate predictions
  // up to the current time step and remove all the ones at the head of the
  // input history queue so that we don't waste time evaluating them again at
  // a later time step.
  static std::vector<UInt> badPatterns;
  badPatterns.clear();                      // purge residual data

  //---------------------------------------------------------------------------
  // Let's go back in time and replay the recent inputs from start cells and
  // see if we can lock onto this current set of inputs that way. A detailed
  // description is in TP.py
  bool inSequence = false;
  Real candConfidence = -1;
  Int candStartOffset = -1;
  UInt startOffset = 0;
  for (; startOffset < _prevInfPatterns.size(); startOffset++) {

    // If we have a candidate already in the past, don't bother falling back
    // to start cells on the current input.
    if ( (startOffset == currentTimeStepsOffset) &&
         (candConfidence != -1) )
      break;

    if (_verbosity >= 3) {
      std::cout << "Trying to lock-on using startCell state from "
                << _prevInfPatterns.size() - 1 - startOffset << " steps ago:";
      printActiveColumns(std::cout, _prevInfPatterns[startOffset]);
      std::cout << "\n";
    }

    // Play through starting from time t-startOffset
    inSequence = false;
    Real totalConfidence = 0;
    for (UInt offset = startOffset; offset < _prevInfPatterns.size(); offset++)
    {
      // If we are about to set the active columns for the current time step
      // based on what we predicted, capture and save the total confidence of
      // predicting the current input
      if (offset == currentTimeStepsOffset) {
        totalConfidence = 0;
        for (UInt i= 0; i < activeColumns.size(); i++) {
          totalConfidence += _colConfidenceT[activeColumns[i]];
        }
      }

      // Compute activeState[t] given bottom-up and predictedState[t-1]
      _infPredictedStateT1 = _infPredictedStateT;
      inSequence = inferPhase1(_prevInfPatterns[offset],
                               (offset == startOffset));
      if (!inSequence) break;

      // Compute predictedState['t'] given activeState['t']
      if (_verbosity >= 3) {
        std::cout << "  backtrack: computing predictions from ";
        printActiveColumns(std::cout, _prevInfPatterns[offset]);
        std::cout << "\n";

      }
      inSequence = inferPhase2();
      if (!inSequence) break;
    }

    // If starting from startOffset got lost along the way, mark it as an
    // invalid start point.
    if (!inSequence) {
      badPatterns.push_back(startOffset);
    }
    else {
      candConfidence = totalConfidence;
      candStartOffset = startOffset;
      
      // If we got to here, startOffset is a candidate starting point.
      if (_verbosity >= 3 && (startOffset != currentTimeStepsOffset) ) {
        std::cout << "# Prediction confidence of current input after starting "
        << _prevInfPatterns.size() - 1 - startOffset
        << " steps ago: " << totalConfidence << "\n";
      }
      
      if (candStartOffset == (Int) currentTimeStepsOffset)
        break;
      _infActiveStateCandidate = _infActiveStateT;
      _infPredictedStateCandidate = _infPredictedStateT;
      memcpy(_cellConfidenceCandidate, _cellConfidenceT, _nCells * sizeof(_cellConfidenceT[0]));
      memcpy(_colConfidenceCandidate, _colConfidenceT, _nColumns * sizeof(_colConfidenceT[0]));
      
      break;
    }

  }

  //---------------------------------------------------------------------------
  // If we failed to lock on at any starting point, fall back to the original
  // active state that we had on entry
  if (candStartOffset == -1) {
    if (_verbosity >= 3) {
      std::cout << "Failed to lock on."
                << " Falling back to bursting all unpredicted.\n";
    }
    _infActiveStateT = _infActiveBackup;
    inferPhase2();
  } else {
    if (_verbosity >= 3) {
      std::cout << "Locked on to current input by using start cells from "
                << _prevInfPatterns.size() - 1 - candStartOffset <<
                " steps ago.\n";
    }
    // Install the candidate state, if it wasn't the last one we evaluated.
    if (candStartOffset != (Int) currentTimeStepsOffset) {
      _infActiveStateT = _infActiveStateCandidate;
      _infPredictedStateT = _infPredictedStateCandidate;
      memcpy(_cellConfidenceT, _cellConfidenceCandidate, _nCells * sizeof(_cellConfidenceCandidate[0]));
      memcpy(_colConfidenceT, _colConfidenceCandidate, _nColumns * sizeof(_colConfidenceCandidate[0]));
    }
  }

  //---------------------------------------------------------------------------
  // Remove any useless patterns at the head of the previous input pattern
  // queue.
  UInt numPrevPatterns = _prevInfPatterns.size();
  for (UInt i = 0; i < numPrevPatterns; i++)
  {
    std::vector<UInt>::iterator result;
    result = find(badPatterns.begin(), badPatterns.end(), i);
    if ( result != badPatterns.end() ||
         ( (candStartOffset != -1) && ((Int)i <= candStartOffset) ) )
    {
      if (_verbosity >= 3) {
        std::cout << "Removing useless pattern from history ";
        printActiveColumns(std::cout, _prevInfPatterns[0]);
        std::cout << "\n";
      }
      _prevInfPatterns.pop_front();
    }
    else
      break;
  }

  // Restore the original predicted state
  _infPredictedStateT1 = _infPredictedBackup;

  // Turn off timer
  TIMER(infBacktrackTimer.stop());
}

//--------------------------------------------------------------------------------
/**
 * A utility method called from learnBacktrack. This will backtrack
 * starting from the given startOffset in our prevLrnPatterns queue.
 */
bool Cells4::learnBacktrackFrom(UInt startOffset, bool readOnly)
{
  // How much input history have we accumulated?
  // The current input is always at the end of self._prevInfPatterns (at
  // index -1), but it is also evaluated as a potential starting point by
  // turning on it's start cells and seeing if it generates sufficient
  // predictions going forward.
  UInt numPrevPatterns = _prevLrnPatterns.size();

  // This is an easy to use label for the current time step
  NTA_CHECK(numPrevPatterns >= 2);
  UInt currentTimeStepsOffset = numPrevPatterns - 1;

  // Clear out any old segment updates. learnPhase2() adds to the segment
  // updates if we're not readOnly
  if (!readOnly) {
    _segmentUpdates.clear();
  }

  if (_verbosity >= 3) {
    std::cout << "startOffset = " << startOffset;
    if (readOnly) {
      std::cout << " Trying to lock-on using startCell state from ";
    } else {
      std::cout << " Locking on using startCell state from ";
    }
    std::cout << numPrevPatterns - 1 - startOffset << " steps ago\n";
    printActiveColumns(std::cout, _prevLrnPatterns[startOffset]);
    std::cout << "\n";
  }

  //---------------------------------------------------------------------------
  // Play through up to the current time step
  bool inSequence = true;
  for (UInt offset = startOffset; offset < numPrevPatterns; offset++)
  {

    //--------------------------------------------------------------------------
    // Copy predicted and active states into t-1
    _learnActiveStateT1 = _learnActiveStateT;
    _learnPredictedStateT1 = _learnPredictedStateT;

    // Apply segment updates from the last set of predictions
    if (!readOnly) {
      memset(_tmpInputBuffer, 0, _nColumns * sizeof(_tmpInputBuffer[0]));
      for (UInt i= 0; i < _prevLrnPatterns[offset].size(); i++) {
        _tmpInputBuffer[_prevLrnPatterns[offset][i]] = 1;
      }
      processSegmentUpdates(_tmpInputBuffer, _learnPredictedStateT);
    }

    //--------------------------------------------------------------------------
    // Compute activeState[t] given bottom-up and predictedState[t-1]
    if (offset == startOffset) {
      _learnActiveStateT.resetAll();
      for (UInt i= 0; i < _prevLrnPatterns[offset].size(); i++) {
        UInt cellIdx = _prevLrnPatterns[offset][i]*_nCellsPerCol;
        _learnActiveStateT.set(cellIdx);
        inSequence = true;
      }
    } else {
      inSequence = learnPhase1(_prevLrnPatterns[offset], readOnly);
    }

    // Break out immediately if we fell out of sequence or reached the current
    // time step
    if (!inSequence || (offset == currentTimeStepsOffset) )
      break;

    //--------------------------------------------------------------------------
    // Phase 2:
    // Computes predictedState['t'] given activeState['t'] and also queues
    // up active segments into self.segmentUpdates, unless this is readOnly
    if (_verbosity >= 3) {
      std::cout << "  backtrack: computing predictions from ";
      printActiveColumns(std::cout, _prevLrnPatterns[offset]);
      std::cout << "\n";
    }

    // Call learnPhase2, but turn off backtrack timer to help isolate timing
    TIMER(learnBacktrackTimer.stop());
    learnPhase2(readOnly);
    TIMER(learnBacktrackTimer.start());
  } // offset < numPrevPatterns

  return inSequence;
}

//------------------------------------------------------------------------------
/**
 * This "backtracks" our learning state, trying to see if we can lock
 * onto the current set of inputs by assuming the sequence started
 * up to N steps ago on start cells.
 */
UInt Cells4::learnBacktrack()
{
  // How much input history have we accumulated?
  // The current input is always at the end of self._prevInfPatterns (at
  // index -1), and is not a valid startingOffset to evaluate.
  Int numPrevPatterns = _prevLrnPatterns.size() - 1;
  if (numPrevPatterns <= 0) {
    if (_verbosity >= 3) {
      std::cout << "lrnBacktrack: No available history to backtrack from\n";
    }
    return false;
  }

  // We will record which previous input patterns did not generate predictions
  // up to the current time step and remove all the ones at the head of the
  // input history queue so that we don't waste time evaluating them again at
  // a later time step.
  static std::vector<UInt> badPatterns;
  badPatterns.clear();                      // purge residual data

  //---------------------------------------------------------------------------
  // Let's go back in time and replay the recent inputs from start cells and
  // see if we can lock onto this current set of inputs that way. A detailed
  // description is in TP.py
  bool inSequence = false;
  UInt startOffset = 0;
  for (; startOffset < (UInt) numPrevPatterns; startOffset++) {
    // Can we backtrack from startOffset?
    inSequence = learnBacktrackFrom(startOffset, true);

    // Done playing through the sequence from starting point startOffset
    // Break out as soon as we find a good path
    if (inSequence)
      break;

    // Take this bad starting point out of our input history so we don't
    // try it again later.
    badPatterns.push_back(startOffset);
  }

  //---------------------------------------------------------------------------
  // If we failed to lock on at any starting point, return failure. The caller
  // will start over again on start cells
  if (!inSequence) {
    if (_verbosity >= 3) {
      std::cout << "Failed to lock on."
                << " Falling back to start cells on current time step.\n";
    }
    // Nothing in our input history was a valid starting point, so get rid
    // of it so we don't try any of them again at a later iteration
    _prevLrnPatterns.clear();
    return false;
  }

  //---------------------------------------------------------------------------
  // We did find a valid starting point in the past. Now, we need to
  // re-enforce all segments that became active when following this path.
  if (_verbosity >= 3) {
    std::cout << "Discovered path to current input by using start cells from "
              << numPrevPatterns - startOffset << " steps ago:\n   ";
    dumpPrevPatterns(_prevLrnPatterns);
  }
  learnBacktrackFrom(startOffset, false);

  // Remove any useless patterns at the head of the input pattern history
  // queue
  for (UInt i = 0; i < (UInt) numPrevPatterns; i++)
  {
    std::vector<UInt>::iterator result;
    result = find(badPatterns.begin(), badPatterns.end(), i);
    if ( result != badPatterns.end() || (i <= startOffset) )
    {
      if (_verbosity >= 3) {
        std::cout << "Removing useless pattern from history ";
        printActiveColumns(std::cout, _prevLrnPatterns[0]);
        std::cout << "\n";
      }
      _prevLrnPatterns.pop_front();
    }
    else
      break;
  }

  return numPrevPatterns - startOffset;

}

//----------------------------------------------------------------------
/**
 * Return the index of a cell in this column which is a good candidate
 * for adding a new segment.
 */
UInt Cells4::getCellForNewSegment(UInt colIdx)
{
  TIMER(getNewCellTimer.start());
  UInt candidateCellIdx = 0;

  // Not fixed size CLA, just choose a cell randomly
  if (_maxSegmentsPerCell < 0) {
    if (_nCellsPerCol > 1) {
      // Don't ever choose the start cell (cell # 0) in each column
      candidateCellIdx = _rng.getUInt32(_nCellsPerCol-1) + 1;
    }
    else {
      candidateCellIdx = 0;
    }
    TIMER(getNewCellTimer.stop());
    return getCellIdx(colIdx,candidateCellIdx);
  }

  // ---------------------------------------------------------------------
  // Fixed size CLA, choose from among the cells that are below the maximum
  //  number of segments.
  // NOTE: It is important NOT to always pick the cell with the fewest number of
  //  segments. The reason is that if we always do that, we are more likely to
  //  run into situations where we choose the same set of cell indices to
  //  represent an 'A' in both context 1 and context 2. This is because the
  //  cell indices we choose in each column of a pattern will advance in
  //  lockstep (i.e. we pick cell indices of 1, then cell indices of 2, etc.).
  static std::vector<UInt> candidateCellIdxs;
  candidateCellIdxs.clear();                // purge residual data
  UInt minIdx = getCellIdx(colIdx,0), maxIdx = getCellIdx(colIdx,0);
  if (_nCellsPerCol > 0) {
    minIdx = getCellIdx(colIdx,1);        // Don't include startCell in the mix
    maxIdx = getCellIdx(colIdx,_nCellsPerCol - 1);
  }
  for (UInt i = minIdx; i <= maxIdx; i++)
  {
    Int numSegs = (Int) _cells[i].size();
    if (numSegs < _maxSegmentsPerCell) {
      candidateCellIdxs.push_back(i);
    }
  }

  // If we found one, return with it
  if (candidateCellIdxs.size() > 0)
  {
    candidateCellIdx =
                candidateCellIdxs[_rng.getUInt32(candidateCellIdxs.size())];
    if (_verbosity >= 5) {
      std::cout << "Cell [" << colIdx
                << "," << candidateCellIdx - getCellIdx(colIdx,0)
                << "] chosen for new segment, # of segs is "
                << _cells[candidateCellIdx].size() << "\n";
    }
    TIMER(getNewCellTimer.stop());
    return candidateCellIdx;
  }

  // ---------------------------------------------------------------------
  // All cells in the column are full, find a segment with lowest duty
  // cycle to free up

  UInt candidateSegmentIdx = (UInt) -1;
  Real candidateSegmentDC = 1.0;
  // For each cell in this column
  for (UInt i = minIdx; i <= maxIdx; i++)
  {
    // For each non-empty segment in this cell
    for (UInt segIdx= 0; segIdx < _cells[i].size(); segIdx++)
    {
      if (!_cells[i][segIdx].empty()) {
        Real dc = _cells[i][segIdx].dutyCycle(_nLrnIterations, false, false);
        if (dc < candidateSegmentDC) {
          candidateCellIdx = i;
          candidateSegmentDC = dc;
          candidateSegmentIdx = segIdx;
        }
      }
    }
  }

  // Free up the least used segment
  if (_verbosity >= 5) {
    std::cout << "Deleting segment #" << candidateSegmentIdx << " for cell["
              << colIdx << "," << candidateCellIdx - getCellIdx(colIdx,0)
              << "] to make room for new segment ";
    _cells[candidateCellIdx][candidateSegmentIdx].print(std::cout,
                                                       _nCellsPerCol);
    std::cout << "\n";

  }

  // Remove this segment from cell and remove any pending updates to this
  // segment. Update outSynapses structure.
  std::vector<UInt> synsToRemove;
  synsToRemove.clear();                     // purge residual data
  _cells[candidateCellIdx][candidateSegmentIdx].getSrcCellIndices(synsToRemove);
  eraseOutSynapses(candidateCellIdx, candidateSegmentIdx, synsToRemove);
  cleanUpdatesList(candidateCellIdx, candidateSegmentIdx);
  _cells[candidateCellIdx].releaseSegment(candidateSegmentIdx);

  TIMER(getNewCellTimer.stop());

  return candidateCellIdx;
}

//--------------------------------------------------------------------------------
/**
 * Compute the learning active state given the predicted state and
 * the bottom-up input.
 */
bool Cells4::learnPhase1(const std::vector<UInt> & activeColumns, bool readOnly)
{
  TIMER(learnPhase1Timer.start());

  // Save previous active state (where?) and start out on a clean slate
  _learnActiveStateT.resetAll();

  UInt numUnpredictedColumns = 0;
  for (UInt i= 0; i < activeColumns.size(); i++) {
    UInt cell0 = activeColumns[i]*_nCellsPerCol;

    // Find any predicting cell in this column (there is at most one)
    UInt numPredictedCells = 0, predictingCell = _nCellsPerCol;
    for (UInt j= 0; j < _nCellsPerCol; j++) {
      if (_learnPredictedStateT1.isSet(j+cell0)) {
        numPredictedCells++;
        predictingCell = j;
      }
    }
    NTA_ASSERT(numPredictedCells <= 1);

    // If we have a predicted cell, turn it on. The segment's posActivation
    // count will have already been incremented by processSegmentUpdates
    if (numPredictedCells == 1) {
      NTA_ASSERT(predictingCell < _nCellsPerCol);
      _learnActiveStateT.set(cell0 + predictingCell);
    }
    else {
      //----------------------------------------------------------------------
      // If no predicted cell, pick the closest matching one to reinforce, or
      // if none exists, create a new segment on a cell in that column
      numUnpredictedColumns++;
      if (! readOnly)
      {
        std::pair<UInt, UInt> p;
        p = getBestMatchingCellT1(activeColumns[i], _learnActiveStateT1, _minThreshold);
        UInt cellIdx = p.first, segIdx = p.second;

        // If we found a sequence segment, reinforce it
        if (segIdx != (UInt) -1 &&
            _cells[cellIdx][segIdx].isSequenceSegment()) {

          if (_verbosity >= 4) {
            std::cout << "Learn branch 0, found segment match: ";
            std::cout << "   learning on col=" << activeColumns[i]
            << ", cellIdx=" << cellIdx << "\n";
          }
          _learnActiveStateT.set(cellIdx);
          bool newUpdate = computeUpdate(cellIdx, segIdx,
                                         _learnActiveStateT1, true, true);
          _cells[cellIdx][segIdx]._totalActivations++;

          if (newUpdate) {
            // This will update the permanences,  posActivationsCount, and the
            // lastActiveIteration (age).
            const SegmentUpdate& update = _segmentUpdates.back();
            adaptSegment(update);
            _segmentUpdates.pop_back();
          }
        }

        // If no close match exists, create a new one
        else {
          UInt newCellIdx = getCellForNewSegment(activeColumns[i]);

          if (_verbosity >= 4) {
            std::cout << "Learn branch 1, no match: ";
            std::cout << "   learning on col=" << activeColumns[i]
                      << ", newCellIdxInCol="
                      << newCellIdx - getCellIdx(activeColumns[i], 0)
                      << "\n";
          }
          _learnActiveStateT.set(newCellIdx);
          bool newUpdate = computeUpdate(newCellIdx, (UInt) -1,
                                         _learnActiveStateT1, true, true);

          // This will update the permanences,  posActivationsCount, and the
          // lastActiveIteration (age).
          if (newUpdate) {
            const SegmentUpdate& update = _segmentUpdates.back();
            adaptSegment(update);
            _segmentUpdates.pop_back();
          }
        }
      }
    }
  } // for each active column

  // Turn off timer before we return
  TIMER(learnPhase1Timer.stop());

  //----------------------------------------------------------------------
  // Determine if we are out of sequence or not and reset our PAM counter
  // if we are in sequence
  if (numUnpredictedColumns < activeColumns.size()/2) {
    return true;
  } else {
    return false;
  }
}

//--------------------------------------------------------------------------------
/**
 * Compute the predicted segments given the current set of active cells.
 */
void Cells4::learnPhase2(bool readOnly)
{
  // Compute number of active synapses per segment based on forward propagation
  TIMER(forwardLearnPropTimer.start());
  computeForwardPropagation(_learnActiveStateT);
  TIMER(forwardLearnPropTimer.stop());

  TIMER(learnPhase2Timer.start());

  // Clear out predicted state to start with
  _learnPredictedStateT.resetAll();

  for (UInt colIdx = 0; colIdx != _nColumns; ++colIdx) {

    // Is there a cell predicted to turn on in this column?
    std::pair<UInt, UInt> p;
    p = getBestMatchingCellT(colIdx, _learnActiveStateT, _activationThreshold);
    UInt cellIdx = p.first, segIdx = p.second;
    if (segIdx != (UInt) -1) {
      // Turn on the predicted state for the best matching cell and queue
      // the pertinent segment up for an update, which will get processed if
      // the cell receives bottom up in the future.
      _learnPredictedStateT.set(cellIdx);
      if (!readOnly) {
        if (_verbosity >= 4) {
          std::cout << "learnPhase2, learning on col=" << colIdx << ", cellIdx="
          << cellIdx << ", seg ID: " << segIdx << ", segment: ";
          _cells[cellIdx][segIdx].print(std::cout, _nCellsPerCol);
          std::cout << "\n";
        }
        computeUpdate(cellIdx, segIdx, _learnActiveStateT, false, true);
        _cells[cellIdx][segIdx]._totalActivations++;
      }
      // Leave out pooling logic for now
    }
  }

  // Turn off timer before we return
  TIMER(learnPhase2Timer.stop());
}

//--------------------------------------------------------------------------------
/**
 * Update the learning state. Called from compute()
 */
void Cells4::updateLearningState(const std::vector<UInt> & activeColumns,
                                 Real* input)
{
  // =========================================================================
  // Copy over learning states to t-1 and reset state at t to 0
  _learnActiveStateT1 = _learnActiveStateT;
  _learnPredictedStateT1 = _learnPredictedStateT;

  //---------------------------------------------------------------------------
  // Update our learning input history
  if (_maxLrnBacktrack > 0) {
    if (_prevLrnPatterns.size() > _maxLrnBacktrack)
      _prevLrnPatterns.pop_front();
    _prevLrnPatterns.push_back(activeColumns);
    if (_verbosity >= 4) {
      std::cout << "Previous learn patterns: \n";
      dumpPrevPatterns(_prevLrnPatterns);
    }
  }

  //---------------------------------------------------------------------------
  // Process queued up segment updates, now that we have bottom-up, we
  // can update the permanences on the cells that we predicted to turn on
  // and did receive bottom-up
  processSegmentUpdates(input, _learnPredictedStateT);

  // Decrement the PAM counter if it is running and increment our learned
  // sequence length
  if (_pamCounter > 0) {
    _pamCounter -= 1;
  }
  _learnedSeqLength++;

  // =========================================================================
  // Phase 1 - turn on predicted cells in each column receiving bottom-up

  //---------------------------------------------------------------------------
  // For each column, turn on the predicted cell. At all times at most
  // 1 cell is active per column in the learn predicted state.
  if (! _resetCalled) {
    bool inSequence = learnPhase1(activeColumns, false);
    if (inSequence) {
      _pamCounter = _pamLength;
    }
  }

  // Print status of PAM counter, learned sequence length
  if (_verbosity >= 3) {
    std::cout << "pamCounter = " << _pamCounter << ", learnedSeqLength = "
              << _learnedSeqLength << "\n";
  }

  //---------------------------------------------------------------------------
  // Start over on start cells if any of the following occur:
  //   1.) A reset was just called
  //   2.) We have been too long out of sequence (the pamCounter has expired)
  //   3.) We have reached maximum allowed sequence length.
  if (  _resetCalled ||
      ( _pamCounter==0) ||
      ( (_maxSeqLength != 0) && (_learnedSeqLength >= _maxSeqLength) )
     )
  {
    if (_verbosity >= 3) {
      std::cout << "Starting over:";
      printActiveColumns(std::cout, activeColumns);
      if (_resetCalled)           std::cout << "(reset was called)\n";
      else if (_pamCounter == 0)  std::cout << "(PAM counter expired)\n";
      else                        std::cout << "(reached maxSeqLength)\n";
    }

    // Update average learned sequence length - this is a diagnostic statistic
    UInt seqLength = ( _pamCounter == 0 ?
                       _learnedSeqLength - _pamLength :
                       _learnedSeqLength );
    if (_verbosity >= 3)
      std::cout << "  learned sequence length was: " << seqLength << "\n";
    _updateAvgLearnedSeqLength(seqLength);

    // Backtrack to an earlier starting point, if we find one
    UInt backsteps = 0;
    if (! _resetCalled ) {
      TIMER(learnBacktrackTimer.start());
      backsteps = learnBacktrack();
      TIMER(learnBacktrackTimer.stop());
    }

    // Start over in the current time step if reset was called, or we couldn't
    // backtrack
    if (_resetCalled || backsteps==0) {
      _learnActiveStateT.resetAll();
      for (UInt i= 0; i < activeColumns.size(); i++) {
        UInt cell0 = activeColumns[i]*_nCellsPerCol;
        _learnActiveStateT.set(cell0);
      }

      // Remove any old input history patterns
      _prevLrnPatterns.clear();
    }

    // reset PAM counter
    _pamCounter = _pamLength;
    _learnedSeqLength = backsteps;

    // Clear out any old segment updates from prior sequences
    _segmentUpdates.clear();

  }

  // Done computing active state


  // =========================================================================
  // Phase 2 - Compute new predicted state. When computing predictions for
  // phase 2, we predict at  most one cell per column (the one with the best
  // matching segment).

  learnPhase2(false);
}


//--------------------------------------------------------------------------------
/**
 * Update the inference state. Called from compute() on every iteration
 */
void Cells4::updateInferenceState(const std::vector<UInt> & activeColumns)
{
  //---------------------------------------------------------------------------
  // Copy over inference related states to t-1 and reset state at t to 0
  // We need to do a copy here in case the buffers are numpy allocated
  // A possible optimization here is to do a swap if Cells4 owns its memory.
  _infActiveStateT1 = _infActiveStateT;
  _infPredictedStateT1 = _infPredictedStateT;
  memcpy(_cellConfidenceT1, _cellConfidenceT, _nCells * sizeof(_cellConfidenceT[0]));

  // Copy over previous column confidences and zero out current confidence
  for (UInt i = 0; i != _nColumns; ++i) {
    _colConfidenceT1[i] = _colConfidenceT[i];
  }

  //---------------------------------------------------------------------------
  // Update our inference input history
  if (_maxInfBacktrack > 0) {
    if (_prevInfPatterns.size() > _maxInfBacktrack)
      _prevInfPatterns.pop_front();
    _prevInfPatterns.push_back(activeColumns);
    if (_verbosity >= 4) {
      std::cout << "Previous inference patterns: \n";
      dumpPrevPatterns(_prevInfPatterns);
    }
  }

  //---------------------------------------------------------------------------
  // Compute the active state given the predictions from last time step and
  // the current bottom-up
  bool inSequence = inferPhase1(activeColumns, _resetCalled);

  //---------------------------------------------------------------------------
  // If this input was considered unpredicted, let's go back in time and
  // replay the recent inputs from start cells and see if we can lock onto
  // this current set of inputs that way.
  if (!inSequence) {
    if (_verbosity >= 3) {
      std::cout << "Too much unpredicted input, re-tracing back to try and"
                << "lock on at an earlier timestep.\n";
    }
    inferBacktrack(activeColumns);
    return;
  }

  //---------------------------------------------------------------------------
  // Compute the predicted cells and the cell and column confidences
  inSequence = inferPhase2();
  if (!inSequence) {
    if (_verbosity >= 3) {
      std::cout << "Not enough predictions going forward, re-tracing back"
                << "to try and lock on at an earlier timestep.\n";
    }
    inferBacktrack(activeColumns);
  }
}

//--------------------------------------------------------------------------------
/**
 * Update the inference active state from the last set of predictions
 * and the current bottom-up.
 */
bool Cells4::inferPhase1(const std::vector<UInt> & activeColumns,
                         bool useStartCells)
{
  TIMER(infPhase1Timer.start());
  //---------------------------------------------------------------------------
  // Initialize current active state to 0 to start
  _infActiveStateT.resetAll();

  //---------------------------------------------------------------------------
  // Phase 1 - turn on predicted cells in each column receiving bottom-up

  // If we are following a reset, activate only the start cell in each
  // column that has bottom-up
  UInt numPredictedColumns = 0;
  if (useStartCells)
  {
    for (UInt i= 0; i < activeColumns.size(); i++) {
      UInt cellIdx = activeColumns[i] * _nCellsPerCol;
      _infActiveStateT.set(cellIdx);
    }

  }
  // else, for each column turn on any predicted cells. If there are none, then
  // turn on all cells (burst the column)
  else
  {
    for (UInt i= 0; i < activeColumns.size(); i++) {
      UInt cellIdx = activeColumns[i] * _nCellsPerCol;
      UInt numPredictingCells = 0;

      for (UInt ci = cellIdx; ci < cellIdx + _nCellsPerCol; ci++)
      {
        if (_infPredictedStateT1.isSet(ci)) {
          numPredictingCells++;
          _infActiveStateT.set(ci);
        }
      }

      if (numPredictingCells > 0) {
        numPredictedColumns += 1;
      }
      else {
        //std::cout << "inferPhase1 bursting col=" << activeColumns[i] << "\n";
        for (UInt ci = cellIdx; ci < cellIdx + _nCellsPerCol; ci++)
        {
          _infActiveStateT.set(ci);    // whole column bursts
        }
      }
    }
  }

  TIMER(infPhase1Timer.stop());
  // Did we predict this input well enough?
  if (useStartCells || (numPredictedColumns >= 0.50 * activeColumns.size()) )
    return true;
  else
    return false;
}

//------------------------------------------------------------------------------
/**
 * Phase 2 for the inference state. The computes the predicted state,
 * then checks to insure that the predicted state is not over-saturated,
 * i.e. look too close like a burst.
 */
bool Cells4::inferPhase2()
{
  // Compute number of active synapses per segment based on forward propagation
  TIMER(forwardInfPropTimer.start());
  computeForwardPropagation(_infActiveStateT);
  TIMER(forwardInfPropTimer.stop());

  TIMER(infPhase2Timer.start());
  //---------------------------------------------------------------------------
  // Initialize to 0 to start
  _infPredictedStateT.resetAll();
  memset(_cellConfidenceT, 0, _nCells * sizeof(_cellConfidenceT[0]));
  memset(_colConfidenceT, 0, _nColumns * sizeof(_colConfidenceT[0]));

  //---------------------------------------------------------------------------
  // Phase 2 - Compute predicted state and update cell and column confidences
  UInt cellIdx = 0, numPredictedCols = 0;
  Real sumColConfidence = 0;
  for (UInt c = 0; c < _nColumns; c++) {

    // For each cell in the column
    bool colPredicted = false;
    for (UInt i = 0; i < _nCellsPerCol; i++, cellIdx++) {

      if (_inferActivity.get(cellIdx) >= _activationThreshold) {

        // For each segment in the cell
        for (UInt j = 0; j != _cells[cellIdx].size(); ++j) {

          // Run sanity check to ensure forward prop matches activity
          // calcuations (turned on in some tests)
          if (_checkSynapseConsistency) {
            const Segment& seg = _cells[cellIdx][j];
            UInt numActiveSyns = seg.computeActivity(
                                    _infActiveStateT, _permConnected, false);
            NTA_CHECK( numActiveSyns == _inferActivity.get(cellIdx, j) );
          }

          // See if segment has a min number of active synapses
          if (_inferActivity.get(cellIdx, j) >= _activationThreshold) {

            // Incorporate the confidence into the owner cell and column
            // Use segment::getLastPosDutyCycle() here
            Real dc = _cells[cellIdx][j].dutyCycle(_nLrnIterations, false, false);
            _cellConfidenceT[cellIdx] += dc;
            _colConfidenceT[c] += dc;

            // If we reach threshold on the connected synapses, predict it
            if (isActive(cellIdx, j, _infActiveStateT)) {
              _infPredictedStateT.set(cellIdx);
              colPredicted = true;
            }
          }

        } // for each segment

      } // _cellActivity >= _activationThreshold

    } // each cell in col

    sumColConfidence += _colConfidenceT[c];
    numPredictedCols += (colPredicted ? 1 : 0);
  } // each col

  //---------------------------------------------------------------------------
  // Normalize column confidences
  if (sumColConfidence > 0) {
    for (UInt c = 0; c < _nColumns; c++) _colConfidenceT[c] /= sumColConfidence;
    for (UInt i = 0; i < _nCells; i++)   _cellConfidenceT[i] /= sumColConfidence;
  }


  // Turn off timer before we return
  TIMER(infPhase2Timer.stop());

  //---------------------------------------------------------------------------
  // Are we predicting the required minimum number of columns?
  if (numPredictedCols >= (0.5*_avgInputDensity))
    return true;
  else
    return false;
}


//------------------------------------------------------------------------------
/**
 * Main compute routine, called for both learning and inference.
 */
void Cells4::compute(Real* input, Real* output, bool doInference, bool doLearning)
{
  TIMER(computeTimer.start());
  NTA_CHECK(doInference || doLearning);

  if (doLearning) _nLrnIterations++;
  ++_nIterations;

#ifdef CELLS4_TIMING
  if (_nIterations % 1000 == 0) {
    std::cout << "\n=================\n_nIterations = " << _nIterations << "\n";
    dumpTiming();
    resetTimers();
  }

  if (_verbosity >= 3) {
    std::cout << "\n==== CPP Iteration: " << _nIterations << " =====" << std::endl;
  }
#endif

  // Create array of active bottom up column indices for later use
  static std::vector<UInt> activeColumns;
  activeColumns.clear();                    // purge residual data
  for (UInt i = 0; i != _nColumns; ++i) {
    if (input[i]) activeColumns.push_back(i);
  }

  // Print active columns
  if (_verbosity >= 3) {
    std::cout << "Active cols: ";
    printActiveColumns(std::cout, activeColumns);
    std::cout << "\n";
  }


  //---------------------------------------------------------------------------
  // Update segment duty cycles if we are crossing a "tier"

  if (doLearning && Segment::atDutyCycleTier(_nLrnIterations)) {
    for (UInt i = 0; i < _nCells; i++) {
      _cells[i].updateDutyCycle(_nLrnIterations);
    }
  }

  //---------------------------------------------------------------------------
  // Update average input density
  if (_avgInputDensity == 0.0) {
    _avgInputDensity = (Real) activeColumns.size();
  } else {
    _avgInputDensity = 0.99*_avgInputDensity + 0.01 * (Real) activeColumns.size();
  }

  //---------------------------------------------------------------------------
  // Update the inference state
  if (doInference) {
    TIMER(inferenceTimer.start());
    updateInferenceState(activeColumns);
    TIMER(inferenceTimer.stop());
  }

  //---------------------------------------------------------------------------
  // Update the learning state
  if (doLearning) {
    TIMER(learningTimer.start());
    updateLearningState(activeColumns, input);
    TIMER(learningTimer.stop());

    // Apply age-based global decay
    applyGlobalDecay();
  }

  _resetCalled = false;

  // compute output
  // If the state arrays are not aligned, performance will suffer.
  // An alternative design specifies _infPredictedStateT and _infActiveStateT
  // as CStateIndexed objects instead of CState.  That will require us also
  // to define 8 other objects as CStateIndexed,
  //
  //   _infActiveStateT1
  //   _infPredictedStateT
  //   _infPredictedStateT1
  //   _learnPredictedStateT1
  //   _infActiveStateCandidate
  //   _infPredictedStateCandidate
  //   _infActiveBackup
  //   _infPredictedBackup
  //
  // which will add some unnecessary overhead.  More importantly, we will
  // need to define TP10X2.predict() to keep TPTest.py from calling the
  // base function in TP.py, which modifies various states, thereby
  // invalidating our indexes.
  memset(output, 0, _nCells * sizeof(output[0])); // most output is zero
#if SOME_STATES_NOT_INDEXED
#ifdef NTA_PLATFORM_darwin86
  const UInt multipleOf4 = 4 * (_nCells/4);
  UInt i;
  for (i = 0; i < multipleOf4; i += 4) {
    UInt32 fourStates = * (UInt32 *)(_infPredictedStateT.arrayPtr() + i);
    if (fourStates != 0) {
      if ((fourStates & 0x000000ff) != 0) output[i + 0] = 1.0;
      if ((fourStates & 0x0000ff00) != 0) output[i + 1] = 1.0;
      if ((fourStates & 0x00ff0000) != 0) output[i + 2] = 1.0;
      if ((fourStates & 0xff000000) != 0) output[i + 3] = 1.0;
    }
    fourStates = * (UInt32 *)(_infActiveStateT.arrayPtr() + i);
    if (fourStates != 0) {
      if ((fourStates & 0x000000ff) != 0) output[i + 0] = 1.0;
      if ((fourStates & 0x0000ff00) != 0) output[i + 1] = 1.0;
      if ((fourStates & 0x00ff0000) != 0) output[i + 2] = 1.0;
      if ((fourStates & 0xff000000) != 0) output[i + 3] = 1.0;
    }
  }

  // process the tail if (_nCells % 4) != 0
  for (i = multipleOf4; i < _nCells; i++) {
    if (_infPredictedStateT.isSet(i)) {
      output[i] = 1.0;
    }
    else if (_infActiveStateT.isSet(i)) {
      output[i] = 1.0;
    }
  }
#else
  const UInt multipleOf8 = 8 * (_nCells/8);
  UInt i;
  for (i = 0; i < multipleOf8; i += 8) {
    UInt64 eightStates = * (UInt64 *)(_infPredictedStateT.arrayPtr() + i);
    if (eightStates != 0) {
      if ((eightStates & 0x00000000000000ff) != 0) output[i + 0] = 1.0;
      if ((eightStates & 0x000000000000ff00) != 0) output[i + 1] = 1.0;
      if ((eightStates & 0x0000000000ff0000) != 0) output[i + 2] = 1.0;
      if ((eightStates & 0x00000000ff000000) != 0) output[i + 3] = 1.0;
      if ((eightStates & 0x000000ff00000000) != 0) output[i + 4] = 1.0;
      if ((eightStates & 0x0000ff0000000000) != 0) output[i + 5] = 1.0;
      if ((eightStates & 0x00ff000000000000) != 0) output[i + 6] = 1.0;
      if ((eightStates & 0xff00000000000000) != 0) output[i + 7] = 1.0;
    }
    eightStates = * (UInt64 *)(_infActiveStateT.arrayPtr() + i);
    if (eightStates != 0) {
      if ((eightStates & 0x00000000000000ff) != 0) output[i + 0] = 1.0;
      if ((eightStates & 0x000000000000ff00) != 0) output[i + 1] = 1.0;
      if ((eightStates & 0x0000000000ff0000) != 0) output[i + 2] = 1.0;
      if ((eightStates & 0x00000000ff000000) != 0) output[i + 3] = 1.0;
      if ((eightStates & 0x000000ff00000000) != 0) output[i + 4] = 1.0;
      if ((eightStates & 0x0000ff0000000000) != 0) output[i + 5] = 1.0;
      if ((eightStates & 0x00ff000000000000) != 0) output[i + 6] = 1.0;
      if ((eightStates & 0xff00000000000000) != 0) output[i + 7] = 1.0;
    }
  }

  // process the tail if (_nCells % 8) != 0
  for (i = multipleOf8; i < _nCells; i++) {
    if (_infPredictedStateT.isSet(i)) {
      output[i] = 1.0;
    }
    else if (_infActiveStateT.isSet(i)) {
      output[i] = 1.0;
    }
  }
#endif // NTA_PLATFORM_darwin86
#else
  static std::vector<UInt> cellsOn;
  std::vector<UInt>::iterator iterOn;
  cellsOn = _infPredictedStateT.cellsOn();
  for (iterOn = cellsOn.begin(); iterOn != cellsOn.end(); ++iterOn)
    output[*iterOn] = 1.0;
  cellsOn = _infActiveStateT.cellsOn();
  for (iterOn = cellsOn.begin(); iterOn != cellsOn.end(); ++iterOn)
    output[*iterOn] = 1.0;
#endif  // SOME_STATES_NOT_INDEXED

  if (_checkSynapseConsistency)
  {
    NTA_CHECK(invariants(true));
  }
  TIMER(computeTimer.stop());
}

//--------------------------------------------------------------------------------
/**
 * Update our moving average of learned sequence length.
 */
void Cells4::_updateAvgLearnedSeqLength(UInt prevSeqLength)
{
  Real alpha = 0.1;
  if (_nLrnIterations < 100) alpha = 0.5;
  if (_verbosity >= 5) {
    std::cout << "_updateAvgLearnedSeqLength before = "
              << _avgLearnedSeqLength << " prevSeqLength = "
              << prevSeqLength << "\n";
  }
  _avgLearnedSeqLength = (1.0 - alpha)*_avgLearnedSeqLength +
                         alpha * (Real) prevSeqLength;
  if (_verbosity >= 5) {
    std::cout << "   after = "
    << _avgLearnedSeqLength << "\n";
  }
}

//--------------------------------------------------------------------------------
/**
 * Go through the list of accumulated segment updates and process them.
 */
void Cells4::processSegmentUpdates(Real* input, const CState& predictedState)
{
  static std::vector<UInt> delUpdates;
  delUpdates.clear();                       // purge residual data

  for (UInt i = 0; i != _segmentUpdates.size(); ++i) {

    const SegmentUpdate& update = _segmentUpdates[i];

    if (_verbosity >= 4) {
      std::cout << "\n_nLrnIterations: " << _nLrnIterations
                << " segment update: ";
      update.print(std::cout, true, _nCellsPerCol);
      std::cout << std::endl;
    }

    // Decide whether to apply the update now. If update has expired, then
    // mark this update for deletion
    if (_nLrnIterations - update.timeStamp() > _segUpdateValidDuration) {
      if (_verbosity >= 4) std::cout << "     Expired, deleting now.\n";
      delUpdates.push_back(i);
    }

    // Update has not expired
    else {
      UInt cellIdx = update.cellIdx();
      UInt colIdx =  (UInt) (cellIdx / _nCellsPerCol);

      // If we received bottom up input, then adapt this segment and schedule
      // update for removal
      if ( input[colIdx] == 1 ) {

        if (_verbosity >= 4) std::cout << "     Applying update now.\n";
        adaptSegment(update);
        delUpdates.push_back(i);
      } else {
        // We didn't receive bottom up input. If we are not (pooling and still
        // predicting) then delete this update
        if ( ! (_doPooling && predictedState.isSet(cellIdx)) ) {
          if (_verbosity >= 4) std::cout << "     Deleting update now.\n";
          delUpdates.push_back(i);
        }
      }

    } // unexpired update

  } // Loop over updates

  remove_at(delUpdates, _segmentUpdates);

}

//----------------------------------------------------------------------
/**
 * Removes any updates that would be applied to the given col,
 * cellIdx, segIdx.
 */
void Cells4::cleanUpdatesList(UInt cellIdx, UInt segIdx)
{
  static std::vector<UInt> delUpdates;
  delUpdates.clear();                       // purge residual data

  for (UInt i = 0; i != _segmentUpdates.size(); ++i) {

    // Get the cell and column associated with this update
    const SegmentUpdate& update = _segmentUpdates[i];

    if (_verbosity >= 4) {
      std::cout << "\nIn cleanUpdatesList. _nLrnIterations: " << _nLrnIterations
      << " checking segment: ";
      update.print(std::cout, true, _nCellsPerCol);
      std::cout << std::endl;
    }

    // Decide whether to remove update. Note: we can't remove update from
    // vector while we are iterating over it.
    if ( (update.cellIdx() == cellIdx) && (segIdx == update.segIdx()) )
    {
      if (_verbosity >= 4) {
        std::cout << "    Removing it\n";
      }

      delUpdates.push_back(i);
    }

  } // Loop over updates

  // Remove any we found
  remove_at(delUpdates, _segmentUpdates);
}

//----------------------------------------------------------------------
/**
 * Apply age-based global decay logic and remove segments/synapses
 * as appropriate.
 */
void Cells4::applyGlobalDecay()
{
  UInt nSegmentsDecayed = 0, nSynapsesRemoved = 0;
  if (_globalDecay != 0 && (_maxAge>0) && (_nLrnIterations % _maxAge == 0) ) {
    for (UInt cellIdx = 0; cellIdx != _nCells; ++cellIdx) {
      for (UInt segIdx = 0; segIdx != _cells[cellIdx].size(); ++segIdx) {

        Segment& seg = segment(cellIdx, segIdx);
        UInt age = _nLrnIterations - seg._lastActiveIteration;

        if ( age > _maxAge ) {

          static std::vector<UInt> removedSynapses;
          removedSynapses.clear();          // purge residual data
          nSegmentsDecayed++;

          seg.decaySynapses2(_globalDecay, removedSynapses, _permConnected);
          nSynapsesRemoved += removedSynapses.size();
          if (!removedSynapses.empty()) {
            eraseOutSynapses(cellIdx, segIdx, removedSynapses);
          }

          if (seg.empty()) {
            _cells[cellIdx].releaseSegment(segIdx);
          }

        }
      }
    }
    if (_verbosity >= 3) {
      std::cout << "CPP Global decay decremented " << nSegmentsDecayed
                << " segments and removed "
                << nSynapsesRemoved << " synapses\n";
      std::cout << "_nLrnIterations = " << _nLrnIterations << ", _maxAge = "
                << _maxAge << ", globalDecay = " << _globalDecay << "\n";
    }
  } // (_globalDecay)
}


//--------------------------------------------------------------------------------
/**
 * Applies segment update information to a segment in a cell.
 *
 * Implementation issues: we need to maintain the OutSynapses correctly.
 *
 * TODO: This whole method is really ugly and could do with a serious cleanup.
 *
 */
void Cells4::adaptSegment(const SegmentUpdate& update)
{
  TIMER(adaptSegmentTimer.start());
  {
    // consistency checks:
    // update synapses need to be sorted and unique
    // make sure update is not stale
  }

  UInt cellIdx = update.cellIdx();
  UInt segIdx = update.segIdx();

  // Modify an existing segment?
  if (! update.isNewSegment()) {

    // Sometimes you can have a pending update after a segment has already
    // been released. It's cheaper to deal with it here rather than do
    // a search through pending updates each time a segment has been deleted.
    if (_cells[cellIdx][segIdx].empty()) {
      TIMER(adaptSegmentTimer.stop());
      return;
    }

    Segment& segment = _cells[cellIdx][segIdx];

    if (_verbosity >= 4) {
      UInt col =  (UInt) (cellIdx / _nCellsPerCol);
      UInt cell = cellIdx - col*_nCellsPerCol;
      std::cout << "Reinforcing segment " << segIdx << " for cell["
                << col<< "," << cell << "]\n     before: ";
      segment.print(std::cout, _nCellsPerCol);
      std::cout << std::endl;
    }

    // Update last active iteration and duty cycle related counts
    segment._lastActiveIteration = _nLrnIterations;
    segment._positiveActivations++;
    segment.dutyCycle(_nLrnIterations, true, false);

    // TODO: The following logic seems really convoluted. Why can't we
    // increment/decrement inline here? Also, why can't we grow potential new
    // synapses instead of creating a list of all synapses and then erasing
    // them from this list? Seems like a lot of extra memory thrashing.
    // Also, why don't we just send a list of synapse indices into
    // updateSynapses? It would be cleaner and avoid the need to keep the
    // synapses sorted.

    // Accumulate list of synapses to decrement, increment, add, and remove
    std::set<UInt> synapsesSet(update.begin(), update.end());
    static std::vector<UInt> removed; // srcCellIdx
    static std::vector<UInt> synToDec, synToInc,
                             inactiveSegmentIndices, activeSegmentIndices;
    removed.clear() ;                       // purge residual data
    synToDec.clear() ;                      // purge residual data
    synToInc.clear() ;                      // purge residual data
    inactiveSegmentIndices.clear() ;        // purge residual data
    activeSegmentIndices.clear() ;          // purge residual data
    for (UInt i = 0; i != segment.size(); ++i) {
      UInt srcCellIdx = segment[i].srcCellIdx();
      if (not_in(srcCellIdx, synapsesSet)) {
        synToDec.push_back(srcCellIdx);  // TODO: Check synapse still exists!
        inactiveSegmentIndices.push_back(i);
      }
      else {
        synToInc.push_back(srcCellIdx);
        synapsesSet.erase(srcCellIdx);
        activeSegmentIndices.push_back(i);
      }
    }

    // Now update synapses which need to be decremented or incremented
    // TODO: Why can't we just do this inline in the above loop?
    segment.updateSynapses(synToDec, - _permDec, _permMax, _permConnected, removed);
    segment.updateSynapses(synToInc, _permInc, _permMax, _permConnected, removed);

    // Add any new synapses, add these to Outlist, and update delta objects

    // If we have fixed resources, get rid of some old syns if necessary
    if ( (_maxSynapsesPerSegment > 0) &&
         (synapsesSet.size() + segment.size() > (UInt) _maxSynapsesPerSegment) ) {
      UInt numToFree = synapsesSet.size() + segment.size() - _maxSynapsesPerSegment;
      segment.freeNSynapses(numToFree,
                            synToDec, inactiveSegmentIndices,
                            synToInc, activeSegmentIndices,
                            removed, _verbosity,
                            _nCellsPerCol, _permMax);
    }
    segment.addSynapses(synapsesSet, _permInitial, _permConnected);
    addOutSynapses(cellIdx, segIdx, synapsesSet.begin(), synapsesSet.end());

    if (_verbosity >= 4) {
      std::cout << "    after: ";
      segment.print(std::cout, _nCellsPerCol);
      std::cout << std::endl;
    }

    // Deal with removed synapses and delete this segment if it now has no
    // synapses. We need to ensure we update the forward propagation
    // structures appropriately.
    if (!removed.empty()) {
      eraseOutSynapses(cellIdx, segIdx, removed);
      _cells[cellIdx][segIdx].recomputeConnected(_permConnected);
    }

    if (segment.empty()) {
      _cells[cellIdx].releaseSegment(segIdx);
    }

  } else { // create new segment

    // Create a list of InSynapses and add it to the list of segments
    InSynapses synapses;
    for (UInt i = 0; i != update.size(); ++i) {
      synapses.push_back(InSynapse(update[i], _permInitial));
    }
    UInt segIdx =
      _cells[cellIdx].getFreeSegment(synapses, _initSegFreq,
                                   update.isSequenceSegment(), _permConnected,
                                     _nLrnIterations);

    // Initialize the new segment's last active iteration and frequency related
    // counts
    _cells[cellIdx][segIdx]._lastActiveIteration = _nLrnIterations;
    _cells[cellIdx][segIdx]._positiveActivations = 1;
    _cells[cellIdx][segIdx]._totalActivations = 1;

    if (_verbosity >= 3) {
      std::cout << "New segment for cell ";
      printCell(cellIdx, _nCellsPerCol);
      std::cout << "cellIdx = " << cellIdx << ", ";
      _cells[cellIdx][segIdx].print(std::cout, _nCellsPerCol);
      std::cout << std::endl;
    }

#if 0                                       // Art testing 2011-08-14; this call appears unnecessary
    _learnActivity.add(cellIdx, synapses.size());
#endif

    addOutSynapses(cellIdx, segIdx, update.begin(), update.end());

  }

  if (_checkSynapseConsistency) {
    NTA_CHECK(invariants());
  }

  TIMER(adaptSegmentTimer.stop());
}



// Rebalance segment lists for each cell
void Cells4::_rebalance()
{
  std::cout << "Rebalancing\n";
  _nIterationsSinceRebalance = _nLrnIterations;

  for (UInt cellIdx = 0; cellIdx != _nCells; ++cellIdx) {
    if (_cells[cellIdx].size() > 0) {
      _cells[cellIdx].rebalanceSegments();
    }
  }

  // After rebalancing we need to redo the OutSynapses
  rebuildOutSynapses();

}

//--------------------------------------------------------------------------------
/**
 * Removes any old segment that has not been touched for maxAge iterations and
 * where the number of connected synapses is less than activation threshold.
 */
void Cells4::trimOldSegments(UInt maxAge)
{
  UInt nSegsRemoved = 0;

  for (UInt cellIdx = 0; cellIdx != _nCells; ++cellIdx) {
    for (UInt segIdx = 0; segIdx != _cells[cellIdx].size(); ++segIdx) {
      Segment& seg = segment(cellIdx, segIdx);
      UInt age = _nLrnIterations - seg._lastActiveIteration;

      if ( (age > maxAge) && (seg.nConnected() < _activationThreshold) ) {
        static std::vector<UInt> removedSynapses;
        removedSynapses.clear();            // purge residual data

        for (UInt i = 0; i != seg.size(); ++i)
          removedSynapses.push_back(seg[i].srcCellIdx());

        eraseOutSynapses(cellIdx, segIdx, removedSynapses);
        _cells[cellIdx].releaseSegment(segIdx);
        nSegsRemoved++;

      }
    }
  }

  std::cout << "In trimOldSegments. Removed " << nSegsRemoved << " segments\n";
  NTA_CHECK(invariants());

}

// Clear out and rebuild the entire _outSynapses data structure
// This is useful if segments have changed.
void Cells4::rebuildOutSynapses()
{
  // TODO: Is this logic sufficient?
  _outSynapses.resize(_nCells);

  // Clear existing out synapses
  for (UInt srcCellIdx = 0; srcCellIdx != _nCells; ++srcCellIdx) {
    _outSynapses[srcCellIdx].clear();
  }

  // Iterate through every synapse in every cell and rebuild new OutSynapses
  // data structure
  for (UInt dstCellIdx = 0; dstCellIdx != _nCells; ++dstCellIdx) {
    for (UInt segIdx = 0; segIdx != _cells[dstCellIdx].size(); ++segIdx) {
      const Segment& seg = _cells[dstCellIdx][segIdx];
      for (UInt synIdx = 0; synIdx != seg.size(); ++synIdx) {
        UInt srcCellIdx = seg.getSrcCellIdx(synIdx);
        OutSynapse newOutSyn(dstCellIdx, segIdx);
        _outSynapses[srcCellIdx].push_back(newOutSyn);
      }
    }
  }

  /*
  for (UInt i = 0; i != _nCells; ++i) {
    UInt srcCol =  (UInt) (i / _nCellsPerCol);
    UInt srcCell = i  - srcCol*_nCellsPerCol;
    std::cout << "\nCell [" << i << " : " << srcCol << "," << srcCell
              << "] connects to: ";

    // Analyze OutSynapses
    for (UInt j = 0; j != _outSynapses[i].size(); ++j) {
      const OutSynapse& syn = _outSynapses[i][j];
      UInt destCol =  (UInt) (syn.dstCellIdx() / _nCellsPerCol);
      UInt destCell = syn.dstCellIdx() - destCol*_nCellsPerCol;

      std::cout << "\n       [" << syn.dstCellIdx() << " : " << destCol << "," << destCell
                << "] segment: " << syn.dstSegIdx() << ",";

    }

  }
  std::cout << "\n";
  */

}


//--------------------------------------------------------------------------------
/**
 */
void Cells4::reset()
{
  if (_verbosity >= 3) {
    std::cout << "\n==== RESET =====\n";
  }
  _infActiveStateT.resetAll();
  _infActiveStateT1.resetAll();
  _infPredictedStateT.resetAll();
  _infPredictedStateT1.resetAll();
  _learnActiveStateT.resetAll();
  _learnActiveStateT1.resetAll();
  _learnPredictedStateT.resetAll();
  _learnPredictedStateT1.resetAll();
  memset(_cellConfidenceT, 0, _nCells * sizeof(_cellConfidenceT[0]));
  memset(_cellConfidenceT1, 0, _nCells * sizeof(_cellConfidenceT1[0]));
  memset(_colConfidenceT, 0, _nColumns * sizeof(_colConfidenceT[0]));
  memset(_colConfidenceT1, 0, _nColumns * sizeof(_colConfidenceT1[0]));

  // Flush the segment update queue
  _segmentUpdates.clear();

  _resetCalled = true;

  // Clear out input history
  _prevInfPatterns.clear();
  _prevLrnPatterns.clear();
  //if (_nLrnIterations - _nIterationsSinceRebalance > 1000) {
  //  //_rebalance();
  //}
}

//--------------------------------------------------------------------------------
void Cells4::save(std::ostream& outStream) const
{
  // Check invariants for smaller networks or if explicitly requested
  if (_checkSynapseConsistency || (_nCells * _maxSegmentsPerCell < 100000) )
  {
    NTA_CHECK(invariants(true));
  }

  outStream << version() << " "
            << _ownsMemory << " "
            << _rng << " "
            << _nColumns << " "
            << _nCellsPerCol << " "
            << _activationThreshold << " "
            << _minThreshold << " "
            << _newSynapseCount << " "
            << _nIterations << " "
            << _segUpdateValidDuration << " "
            << _initSegFreq << " "
            << _permInitial << " "
            << _permConnected << " "
            << _permMax << " "
            << _permDec << " "
            << _permInc << " "
            << _globalDecay << " "
            << _doPooling << " "
            << _maxInfBacktrack << " "
            << _maxLrnBacktrack << " "
            << _pamLength << " "
            << _maxAge << " "
            << _avgInputDensity << " "
            << _pamCounter << " "
            << _maxSeqLength << " "
            << _avgLearnedSeqLength << " "
            << _nLrnIterations << " "
            << _maxSegmentsPerCell << " "
            << _maxSynapsesPerSegment << " "
            << std::endl;

  // Additions in version 1.
  outStream << _learnedSeqLength << " "
            << _verbosity << " "
            << _checkSynapseConsistency << " "
            << _resetCalled << std::endl;
  outStream << _learnActiveStateT << " "
            << _learnActiveStateT1 << " "
            << _learnPredictedStateT << " "
            << _learnPredictedStateT1 << std::endl;

  // Additions in version 2.
  outStream << _segmentUpdates.size() << " ";
  for (UInt i = 0; i < _segmentUpdates.size(); ++i)
  {
    _segmentUpdates[i].save(outStream);
  }

  NTA_CHECK(_nCells == _cells.size());
  for (UInt i = 0; i != _nCells; ++i) {
    _cells[i].save(outStream);
    outStream << std::endl;
  }

  outStream << " out ";
}

//----------------------------------------------------------------------------
/**
 * Save the state to the given file
 */
void Cells4::saveToFile(std::string filePath) const
{
  OFStream outStream(filePath.c_str(), std::ios_base::out | std::ios_base::binary);
  outStream.precision(std::numeric_limits<double>::digits10 + 1);
  save(outStream);
}

//----------------------------------------------------------------------
/**
 * Load the state from the given file
 */
void Cells4::loadFromFile(std::string filePath)
{
  IFStream outStream(filePath.c_str(), std::ios_base::in | std::ios_base::binary);
  load(outStream);
}



//------------------------------------------------------------------------------
/**
 * Need to load and re-propagate activities so that we can really persist
 * at any point, load back and resume inference at exactly the same point.
 */
void Cells4::load(std::istream& inStream)
{
  std::string tag = "";
  inStream >> tag;
  // If the checkpoint starts with "cellsV4" then it is the original,
  // otherwise the version is a UInt.
  UInt v = 0;
  std::stringstream ss;
  if (tag != "cellsV4")
  {
    ss << tag;
    ss >> v;
  }

  inStream >> _ownsMemory;
  inStream >> _rng;

  UInt nColumns = 0, nCellsPerCol = 0;
  UInt nIterations = 0;

  inStream >> nColumns >> nCellsPerCol;

  inStream >> _activationThreshold
           >> _minThreshold
           >> _newSynapseCount
           >> nIterations
           >> _segUpdateValidDuration
           >> _initSegFreq
           >> _permInitial
           >> _permConnected
           >> _permMax
           >> _permDec
           >> _permInc
           >> _globalDecay
           >> _doPooling;

  // TODO: clean up constructor/initialization and _segActivity below
  initialize(nColumns, nCellsPerCol,
             _activationThreshold,
             _minThreshold,
             _newSynapseCount,
             _segUpdateValidDuration,
             _permInitial,
             _permConnected,
             _permMax,
             _permDec,
             _permInc,
             _globalDecay,
             _doPooling,
             _ownsMemory);

  _nIterations = nIterations;

  inStream  >> _maxInfBacktrack
            >> _maxLrnBacktrack
            >> _pamLength
            >> _maxAge
            >> _avgInputDensity
            >> _pamCounter
            >> _maxSeqLength
            >> _avgLearnedSeqLength
            >> _nLrnIterations
            >> _maxSegmentsPerCell
            >> _maxSynapsesPerSegment;

  if (v >= 1)
  {
    inStream >> _learnedSeqLength
             >> _verbosity
             >> _checkSynapseConsistency
             >> _resetCalled;
    _learnActiveStateT.load(inStream);
    _learnActiveStateT1.load(inStream);
    _learnPredictedStateT.load(inStream);
    _learnPredictedStateT1.load(inStream);
  }

  if (v >= 2)
  {
    UInt n;
    _segmentUpdates.clear();
    inStream >> n;
    for (UInt i = 0; i < n; ++i)
    {
      _segmentUpdates.push_back(SegmentUpdate());
      _segmentUpdates[i].load(inStream);
    }
  }

  for (UInt i = 0; i != _nCells; ++i) {
    _cells[i].load(inStream);
  }

  std::string marker;
  inStream >> marker;
  NTA_CHECK(marker == "out");

  // Restore out synapses
  rebuildOutSynapses();

  // Check invariants for smaller networks or if explicitly requested
  if (_checkSynapseConsistency || (_nCells * _maxSegmentsPerCell < 100000) )
  {
    NTA_CHECK(invariants(true));
  }

  // Update the version after loading everything.
  _version = VERSION;
}

//--------------------------------------------------------------------------------
// Invariants
//--------------------------------------------------------------------------------
/**
 * Checks consistency of InSynapses and OutSynapses: those are kept in sync
 * each time synapses/segments are created/deleted. This test takes some time
 * but it's indispensable in development.
 */
bool Cells4::invariants(bool verbose) const
{
  using namespace std;

  set<string> back_map;
  set<string> forward_map;

  bool consistent = true;

  if (_nCellsPerCol > 1) {
    // Since we have a start cell, ensure that the 0'th cell in each
    // column has no incoming segments
    for (UInt colIdx = 0; colIdx != _nColumns; ++colIdx) {
      UInt cellIdx = colIdx * _nCellsPerCol;
      consistent &= (_cells[cellIdx].size() == 0);
    }

    if (!consistent && verbose) {
      std::cout << "0'th cell in some column has segments\n";
    }
  }

  for (UInt i = 0; i != _nCells; ++i) {

    // Analyze InSynapses
    for (UInt j = 0; j != _cells[i].size(); ++j) {

      const Segment& seg = _cells[i][j];

      for (UInt k = 0; k != seg.size(); ++k) {

        stringstream buf;
        buf << i << '.' << j << '.' << seg[k].srcCellIdx();

        if (is_in(buf.str(), back_map)) {
          std::cout << "\nDuplicate incoming synapse: " << std::endl;
          consistent = false;
        }

        back_map.insert(buf.str());
      }

      consistent &= seg.checkConnected(_permConnected);
    }

    // Analyze OutSynapses
    for (UInt j = 0; j != _outSynapses[i].size(); ++j) {

      const OutSynapse& syn = _outSynapses[i][j];

      stringstream buf;
      buf << syn.dstCellIdx() << '.' << syn.dstSegIdx() << '.' << i;

      if (is_in(buf.str(), forward_map)) {
        std::cout << "\nDuplicate outgoing synapse:" << std::endl;
        consistent = false;
      }

      forward_map.insert(buf.str());
    }
  }

  consistent &= back_map == forward_map;

  if (!consistent) {
    std::cout << "synapses inconsistent forward_map size="
    << forward_map.size() << " back_map size="
    << back_map.size() << std::endl;
    //std::cout << "\nBack/forward maps: "
    //     << back_map.size() << " " << forward_map.size() << std::endl;
    //set<string>::iterator it1 = back_map.begin();
    //set<string>::iterator it2 = forward_map.begin();
    //while (it1 != back_map.end() && it2 != forward_map.end())
    //  std::cout << *it1++ << " " << *it2++ << std::endl;
    //while (it1 != back_map.end())
    //  std::cout << *it1++ << std::endl;
    //while (it2 != forward_map.end())
    //  std::cout << *it2++ << std::endl;
  } else {
    //std::cout << "synapses consistent" << std::endl;
  }

  return consistent;
}



void
Cells4::addNewSegment(UInt colIdx, UInt cellIdxInCol,
                      bool sequenceSegmentFlag,
                      const std::vector<std::pair<UInt, UInt> >& extSynapses)
{
  NTA_ASSERT(colIdx < nColumns());
  NTA_ASSERT(cellIdxInCol < nCellsPerCol());

  UInt cellIdx = colIdx * _nCellsPerCol + cellIdxInCol;

  static std::vector<UInt> synapses;
  synapses.resize(extSynapses.size());      // how many slots we need
  for (UInt i = 0; i != extSynapses.size(); ++i)
    synapses[i] = extSynapses[i].first * _nCellsPerCol + extSynapses[i].second;

  SegmentUpdate update(cellIdx, (UInt) -1, sequenceSegmentFlag,
                       _nLrnIterations, synapses);  // TODO: Add this for invariants check

  _segmentUpdates.push_back(update);
}

//--------------------------------------------------------------------------------
void
Cells4::updateSegment(UInt colIdx, UInt cellIdxInCol, UInt segIdx,
                      const std::vector<std::pair<UInt, UInt> >& extSynapses)
{
  NTA_ASSERT(colIdx < nColumns());
  NTA_ASSERT(cellIdxInCol < nCellsPerCol());

  UInt cellIdx = colIdx * _nCellsPerCol + cellIdxInCol;
  bool sequenceSegmentFlag = segment(cellIdx, segIdx).isSequenceSegment();

  static std::vector<UInt> synapses;
  synapses.resize(extSynapses.size());      // how many slots we need
  for (UInt i = 0; i != extSynapses.size(); ++i)
    synapses[i] = extSynapses[i].first * _nCellsPerCol + extSynapses[i].second;

  SegmentUpdate update(cellIdx, segIdx, sequenceSegmentFlag, _nLrnIterations,
                       synapses);

  _segmentUpdates.push_back(update);
}

//--------------------------------------------------------------------------------
/**
 * Simple helper function for allocating our numerous state variables
 */
template <typename It> void allocateState(It *&state, const UInt numElmts)
{
  state  = new It [numElmts];
  memset(state, 0, numElmts * sizeof(It));
}

void Cells4::setCellSegmentOrder(bool matchPythonOrder)
{
  Cell::setSegmentOrder(matchPythonOrder);
}

void
Cells4::initialize(UInt nColumns,
                   UInt nCellsPerCol,
                   UInt activationThreshold,
                   UInt minThreshold,
                   UInt newSynapseCount,
                   UInt segUpdateValidDuration,
                   Real permInitial,
                   Real permConnected,
                   Real permMax,
                   Real permDec,
                   Real permInc,
                   Real globalDecay,
                   bool doPooling,
                   bool doItAll,
                   bool checkSynapseConsistency)
{
  _nColumns                   = nColumns;
  _nCellsPerCol               = nCellsPerCol;
  _nCells                     = nColumns * nCellsPerCol;
  NTA_CHECK(_nCells <= _MAX_CELLS);

  _activationThreshold        = activationThreshold;
  _minThreshold               = minThreshold;
  _newSynapseCount            = newSynapseCount;
  _segUpdateValidDuration     = segUpdateValidDuration;

  _initSegFreq                = 0.5;
  _permInitial                = permInitial;
  _permConnected              = permConnected;
  _permMax = permMax;
  _permDec = permDec;
  _permInc = permInc;
  _globalDecay = globalDecay;
  _doPooling = doPooling;
  _resetCalled = false;
  _pamLength = 3;
  _avgInputDensity = 0;

  _nIterations = 0;
  _nLrnIterations = 0;
  _pamCounter = _pamLength+1;
  _maxInfBacktrack = 10;
  _maxLrnBacktrack = 5;
  _maxSeqLength = 0;
  _learnedSeqLength = 0;
  _avgLearnedSeqLength = 0.0;
  _verbosity = 0;
  _maxAge = 0;
  _maxSegmentsPerCell = -1;
  _maxSynapsesPerSegment = -1;

  _cells.resize(_nCells);
  Cell::setSegmentOrder(false);
  _outSynapses.resize(_nCells);

  // This is for Python: TP10X is a thin class
  // that contains an instance of Cells4, and we can have either
  // Python allocate numpy arrays and pass them to C++, or C++
  // allocate memory here (then Python gets pointers via
  // getStatePointers).
  if (doItAll) {
    _ownsMemory = true;
    _infActiveStateT.initialize(_nCells);
    _infActiveStateT1.initialize(_nCells);
    _infPredictedStateT.initialize(_nCells);
    _infPredictedStateT1.initialize(_nCells);
    allocateState(_cellConfidenceT,         _nCells);
    allocateState(_cellConfidenceT1,        _nCells);
    allocateState(_colConfidenceT,          _nColumns);
    allocateState(_colConfidenceT1,         _nColumns);
  }
  else {
    _ownsMemory = false;
  }

  // Initialize the state variables that are always managed inside the class
  _learnActiveStateT.initialize(_nCells);
  _learnActiveStateT1.initialize(_nCells);
  _learnPredictedStateT.initialize(_nCells);
  _learnPredictedStateT1.initialize(_nCells);
  _infActiveBackup.initialize(_nCells);
  _infPredictedBackup.initialize(_nCells);
  _infActiveStateCandidate.initialize(_nCells);
  _infPredictedStateCandidate.initialize(_nCells);
  allocateState(_cellConfidenceCandidate,     _nCells);
  allocateState(_colConfidenceCandidate,      _nColumns);
  allocateState(_tmpInputBuffer,              _nColumns);

  // Internal timings and states used for optimization
  _nIterationsSinceRebalance = 0;

  _checkSynapseConsistency = checkSynapseConsistency;
  if (_checkSynapseConsistency)
    std::cout << "*** Synapse consistency checking turned on for Cells4 ***\n";

}

UInt Cells4::nSegments() const
{
  UInt n = 0;
  for (UInt i = 0; i != _nCells; ++i)
    n += _cells[i].nSegments();
  return n;
}

UInt Cells4::__nSegmentsOnCell(UInt cellIdx) const
{
  NTA_ASSERT(cellIdx < _nCells);
  return _cells[cellIdx].size();
}

UInt Cells4::nSegmentsOnCell(UInt colIdx, UInt cellIdxInCol) const
{
  NTA_ASSERT(colIdx < nColumns());
  NTA_ASSERT(cellIdxInCol < nCellsPerCol());

  return _cells[colIdx * nCellsPerCol() + cellIdxInCol].nSegments();
}


UInt Cells4::nSynapses() const
{
  UInt n = 0;
  for (UInt i = 0; i != _nCells; ++i)
    n += _cells[i].nSynapses();
  return n;
}


UInt Cells4::nSynapsesInCell(UInt cellIdx) const
{
  NTA_ASSERT(cellIdx < nCells());

  return _cells[cellIdx].nSynapses();
}

Cell* Cells4::getCell(UInt colIdx, UInt cellIdxInCol)
{
  NTA_ASSERT(colIdx < nColumns());
  NTA_ASSERT(cellIdxInCol < nCellsPerCol());

  return & _cells[colIdx * _nCellsPerCol + cellIdxInCol];
}

UInt Cells4::getCellIdx(UInt colIdx, UInt cellIdxInCol)
{
  NTA_ASSERT(colIdx < nColumns());
  NTA_ASSERT(cellIdxInCol < nCellsPerCol());

  return colIdx * _nCellsPerCol + cellIdxInCol;
}

Segment*
Cells4::getSegment(UInt colIdx, UInt cellIdxInCol, UInt segIdx)
{
  NTA_ASSERT(colIdx < nColumns());
  NTA_ASSERT(cellIdxInCol < nCellsPerCol());

  UInt cellIdx = colIdx * nCellsPerCol() + cellIdxInCol;

  NTA_ASSERT(segIdx < _cells[cellIdx].size());

  return & segment(cellIdx, segIdx);
}


Segment& Cells4::segment(UInt cellIdx, UInt segIdx)
{
  NTA_ASSERT(cellIdx < nCells());
  NTA_ASSERT(segIdx < _cells[cellIdx].size());

  return _cells[cellIdx][segIdx];
}


std::vector<UInt>
Cells4::getNonEmptySegList(UInt colIdx, UInt cellIdxInCol)
{
  NTA_ASSERT(colIdx < nColumns());
  NTA_ASSERT(cellIdxInCol < nCellsPerCol());

  UInt cellIdx = colIdx * nCellsPerCol() + cellIdxInCol;

  return _cells[cellIdx].getNonEmptySegList();
}

//----------------------------------------------------------------------
/**
 * Find weakly activated cell in column.
 */
std::pair<UInt, UInt> Cells4::getBestMatchingCellT(UInt colIdx, const CState& state, UInt minThreshold)
{
  {
    NTA_ASSERT(colIdx < nColumns());
  }

  int start = colIdx * _nCellsPerCol,
      end   = start + _nCellsPerCol;
  UInt best_cell = UInt(-1);
  UInt best_seg  = UInt(-1);
  UInt best_activity = minThreshold > 0 ? minThreshold - 1 : 0;

  // For each cell in the column
  for (int ii = end - 1; ii >= start; --ii) {    // reverse segment order to match Python logic
    UInt i = UInt(ii);

    // Check synapse consistency for each segment if requested
    if (_checkSynapseConsistency) {
      for (UInt j = 0; j != _cells[i].size(); ++j) {
        NTA_CHECK( segment(i,j).computeActivity(state, _permConnected, false) == _learnActivity.get(i, j) );
      }
    }

    if (_learnActivity.get(i) > best_activity) { // if this cell may have a worthy segment

      for (UInt j = 0; j != _cells[i].size(); ++j) {

        // Open: Does _cells[i].size() vary?
        UInt activity = _learnActivity.get(i, j);

        if (best_activity < activity) {     // if a new maximum
          best_activity = activity;         // set the new maximum
          best_cell = i;                    // remember the cell
          best_seg = j;                     // remember the segment
        }
        if (_verbosity >= 6 && activity >= minThreshold) {
          std::cout << "getBestMatchingCell, learning on col=" << colIdx
                    << ", segment: ";
          _cells[i][j].print(std::cout, _nCellsPerCol);
          std::cout << "\n";
          std::cout << "activity = " << activity << ", maxSegActivity = "
                    << best_activity << "\n";
        }
      } // for each segment in cell

    } // if this cell may have a segment with a new maximum
  } // for each cell in the column

  return std::make_pair(best_cell, best_seg);    // could be (-1,-1)
}

//----------------------------------------------------------------------
/**
 * Find weakly activated cell in column.
 */
std::pair<UInt, UInt> Cells4::getBestMatchingCellT1(UInt colIdx, const CState& state, UInt minThreshold)
{
  {
    NTA_ASSERT(colIdx < nColumns());
  }

  UInt start = colIdx * _nCellsPerCol, end = start + _nCellsPerCol;
  UInt best_cell = (UInt) -1;
  std::pair<UInt, UInt> best((UInt) -1, minThreshold);

  // For each cell in column
  for (UInt i = start; i != end; ++i) {

    UInt maxSegActivity = 0, maxSegIdx = 0, activity = 0;


    for (UInt j = 0; j != _cells[i].size(); ++j) {

      if (segment(i,j).empty())
        continue;

      activity = segment(i,j).computeActivity(state, _permConnected, false);

      if (activity > maxSegActivity) {
        maxSegActivity = activity;
        maxSegIdx = j;
      }
      if (_verbosity >= 6 && activity >= minThreshold) {
        std::cout << "getBestMatchingCell, learning on col=" << colIdx
                  << ", segment: ";
        _cells[i][j].print(std::cout, _nCellsPerCol);
        std::cout << "\n";
        std::cout << "activity = " << activity << ", maxSegActivity = "
                  << maxSegActivity << "\n";
      }
    } // for each segment in cell

    // Does this cell have largest activity?
    if (maxSegActivity >= best.second) {
      best = std::make_pair(maxSegIdx, maxSegActivity);
      best_cell = i;
    }

  } // for each cell in column

  if (best_cell != (UInt) -1)
    return std::make_pair(best_cell, best.first);
  else
    return std::make_pair((UInt) -1, (UInt) -1);
}

void
Cells4::chooseCellsToLearnFrom(UInt cellIdx, UInt segIdx,
                               UInt nSynToAdd, CStateIndexed& state,
                               std::vector<UInt>& srcCells)
{
  // bail out if no cells requested
  if (nSynToAdd == 0)
    return;
  TIMER(chooseCellsTimer.start());

  // start with a sorted vector of all the cells that are on in the current state
  static std::vector<UInt> vecCellBuffer;
  vecCellBuffer = state.cellsOn();

  // remove any cells already in this segment
  static std::vector<UInt> vecPruned;
  if (segIdx != (UInt) -1) {

    // collect the sorted list of source cell indices
    Segment segThis = _cells[cellIdx][segIdx];
    static std::vector<UInt> vecAlreadyHave;
    if (vecAlreadyHave.capacity() < segThis.size())
      vecAlreadyHave.reserve(segThis.size());
    vecAlreadyHave.clear();                 // purge residual data
    for (UInt i = 0; i != segThis.size(); ++i)
      vecAlreadyHave.push_back(segThis[i].srcCellIdx());

    // remove any of these found in vecCellBuffer
    if (vecPruned.size() < vecCellBuffer.size())   // ensure there is enough room for the results
      vecPruned.resize(vecCellBuffer.size());
    std::vector<UInt>::iterator iterPruned;
    iterPruned = std::set_difference(vecCellBuffer.begin(),
                                     vecCellBuffer.end(),
                                     vecAlreadyHave.begin(),
                                     vecAlreadyHave.end(),
                                     vecPruned.begin());
    vecPruned.resize(iterPruned - vecPruned.begin());
  }
  else {
    vecPruned = vecCellBuffer;
  }
  const UInt nbrCells = vecPruned.size();

  // bail out if there are no cells left to process
  if (nbrCells == 0) {
    TIMER(chooseCellsTimer.stop());         // turn off timer
    return;
  }

  // if we found fewer cells than requested, return all of them
  // The new ones are sorted, but we need to sort again if there were
  // any old ones.
  bool fSortNeeded = srcCells.size() > 0;   // may be overridden below
  if (nbrCells <= nSynToAdd) {
    // since we use all of vecPruned, we don't need a random number
    srcCells.reserve(nbrCells + srcCells.size());
    std::vector<UInt>::iterator iterCellBuffer;
    for (iterCellBuffer = vecPruned.begin(); iterCellBuffer != vecPruned.end(); ++iterCellBuffer) {
      srcCells.push_back(*iterCellBuffer);
    }
  }
  else if (nSynToAdd == 1) {
    // if just one cell requested, choose one at random
    srcCells.push_back(vecPruned[_rng.getUInt32(nbrCells)]);
  }
  else {
    // choose a random subset of the cells found, and append them to the caller's array
    std::random_shuffle(vecPruned.begin(), vecPruned.end(), _rng);
    srcCells.insert( srcCells.end(), vecPruned.begin(), vecPruned.begin() + nSynToAdd);
    fSortNeeded = true;                     // will need to sort
  }

  // sort the new additions with any prior elements
  if (fSortNeeded)
    std::sort(srcCells.begin(), srcCells.end());

  // Turn off timer
  TIMER(chooseCellsTimer.stop());
}


std::pair<UInt, UInt> Cells4::trimSegments(Real minPermanence,
                                           UInt minNumSyns)
{
  UInt nSegsRemoved = 0, nSynsRemoved = 0;

  // Fill in defaults
  if (minPermanence == 0.0)
    minPermanence = _permConnected;
  if (minNumSyns == 0)
    minNumSyns = _activationThreshold;

  for (UInt cellIdx = 0; cellIdx != _nCells; ++cellIdx) {
    for (UInt segIdx = 0; segIdx != _cells[cellIdx].size(); ++segIdx) {

      static std::vector<UInt> removedSynapses;
      removedSynapses.clear();              // purge residual data

      Segment& seg = segment(cellIdx, segIdx);

      seg.decaySynapses(minPermanence,
                        removedSynapses,
                        minPermanence, false);

      if (seg.size() < minNumSyns) {

        for (UInt i = 0; i != seg.size(); ++i)
          removedSynapses.push_back(seg[i].srcCellIdx());

        eraseOutSynapses(cellIdx, segIdx, removedSynapses);
        _cells[cellIdx].releaseSegment(segIdx);

        ++ nSegsRemoved;

      } else {
        eraseOutSynapses(cellIdx, segIdx, removedSynapses);
      }

      nSynsRemoved += removedSynapses.size();
    }
  }

  if (_checkSynapseConsistency) {
    NTA_CHECK(invariants(true));
  }

  return std::make_pair(nSegsRemoved, nSynsRemoved);
}

//----------------------------------------------------------------------
// Debugging helpers
//----------------------------------------------------------------------

void Cells4::printState(UInt *state)
{
  for (UInt i = 0; i != nCellsPerCol(); ++i) {
    for (UInt c = 0; c != nColumns(); ++c) {
      if (c > 0 && c % 10 == 0)
        std::cout << ' ';
      UInt cellIdx = c * nCellsPerCol() + i;
      std::cout << (state[cellIdx] ? 1 : 0);
    }
    std::cout << std::endl;
  }
}

void Cells4::printStates()
{
  // Print out active state for debugging
  if (true) {
    std::cout << "TP10X: Active  T-1      \t T\n";
    for (UInt i = 0; i != nCellsPerCol(); ++i) {
      for (UInt c = 0; c != nColumns(); ++c) {
        if (c > 0 && c % 10 == 0)
          std::cout << ' ';
        UInt cellIdx = c * nCellsPerCol() + i;
        std::cout << (_infActiveStateT1.isSet(cellIdx) ? 1 : 0);
      }
      std::cout << "  ";

      for (UInt c = 0; c != nColumns(); ++c) {
        if (c > 0 && c % 10 == 0)
          std::cout << ' ';
        UInt cellIdx = c * nCellsPerCol() + i;
        std::cout << (_infActiveStateT.isSet(cellIdx) ? 1 : 0);
      }
      std::cout << std::endl;
    }

    std::cout << "TP10X: Predicted T-1      \t T\n";
    for (UInt i = 0; i != nCellsPerCol(); ++i) {
      for (UInt c = 0; c != nColumns(); ++c) {
        if (c > 0 && c % 10 == 0)
          std::cout << ' ';
        UInt cellIdx = c * nCellsPerCol() + i;
        std::cout << (_infPredictedStateT1.isSet(cellIdx) ? 1 : 0);
      }
      std::cout << "  ";

      for (UInt c = 0; c != nColumns(); ++c) {
        if (c > 0 && c % 10 == 0)
          std::cout << ' ';
        UInt cellIdx = c * nCellsPerCol() + i;
        std::cout << (_infPredictedStateT.isSet(cellIdx) ? 1 : 0);
      }
      std::cout << std::endl;
    }

    std::cout << "TP10X: Learn  T-1      \t\t T\n";
    for (UInt i = 0; i != nCellsPerCol(); ++i) {
      for (UInt c = 0; c != nColumns(); ++c) {
        if (c > 0 && c % 10 == 0)
          std::cout << ' ';
        UInt cellIdx = c * nCellsPerCol() + i;
        std::cout << (_learnActiveStateT1.isSet(cellIdx) ? 1 : 0);
      }
      std::cout << "  ";

      for (UInt c = 0; c != nColumns(); ++c) {
        if (c > 0 && c % 10 == 0)
          std::cout << ' ';
        UInt cellIdx = c * nCellsPerCol() + i;
        std::cout << (_learnActiveStateT.isSet(cellIdx) ? 1 : 0);
      }
      std::cout << std::endl;
    }
  }
}

void Cells4::dumpSegmentUpdates()
{
  std::cout << _segmentUpdates.size() << " updates" << std::endl;
  for (UInt i = 0; i != _segmentUpdates.size(); ++i) {
    _segmentUpdates[i].print(std::cout, true);
    std::cout << std::endl;
  }
}

// Print input pattern queue
void Cells4::dumpPrevPatterns(std::deque<std::vector<UInt> > &patterns)
{
  for (UInt p = 0; p < patterns.size(); p++) {
    std::cout << "Pattern " << p << ": ";
    for (UInt i= 0; i < patterns[p].size(); i++) {
      std::cout << patterns[p][i] << " ";
    }
    std::cout << std::endl;
  }
  std::cout << std::endl;

}

void Cells4::print(std::ostream& outStream) const
{
  for (UInt i = 0; i != _nCells; ++i) {
    std::cout << "Cell #" << i << " ";
    for (UInt j = 0; j != _cells[i].size(); ++j) {
      std::cout << "(" << _cells[i][j] << ")";
    }
    std::cout << std::endl;
  }
}

std::ostream& operator<<(std::ostream& outStream, const Cells4& cells)
{
  cells.print(outStream);
  return outStream;
}

//----------------------------------------------------------------------
/**
 * Compute cell and segment activities using forward propagation
 * and the given state variable.
 */
void Cells4::computeForwardPropagation(CStateIndexed& state)
{
  // Zero out previous values
  // Using memset is quite a bit faster on laptops, but has almost no effect
  // on Neo15!
  _learnActivity.reset();

  // Compute cell and segment activity by following forward propagation
  // links from each source cell.  _cellActivity will be set to the total
  // activity coming into a cell.

  // process all cells that are on in the current state
  static std::vector<UInt> vecCellBuffer ;
  vecCellBuffer = state.cellsOn();
  std::vector<UInt>::iterator iterCellBuffer;
  for (iterCellBuffer = vecCellBuffer.begin(); iterCellBuffer != vecCellBuffer.end(); ++iterCellBuffer) {
    std::vector< OutSynapse >& os = _outSynapses[*iterCellBuffer];
    for (UInt j = 0; j != os.size(); ++j) {
      UInt dstCellIdx = os[j].dstCellIdx();
      UInt dstSegIdx = os[j].dstSegIdx();
      _learnActivity.increment(dstCellIdx, dstSegIdx);
    }
  }
}

#if SOME_STATES_NOT_INDEXED
//----------------------------------------------------------------------
/**
 * Compute cell and segment activities using forward propagation
 * and the given state variable.
 *
 * 2011-08-11: We will remove this overloaded function if we can
 * convert _infActiveStateT from a CState object to CStateIndexed
 * without degrading performance.  Conversion will also require us
 * to move all state array modifications from Python to C++.  One
 * known offender is TP.py.
 */
void Cells4::computeForwardPropagation(CState& state)
{
  // Zero out previous values
  // Using memset is quite a bit faster on laptops, but has almost no effect
  // on Neo15!
  _inferActivity.reset();

  // Compute cell and segment activity by following forward propagation
  // links from each source cell.  _cellActivity will be set to the total
  // activity coming into a cell.
#ifdef NTA_PLATFORM_darwin86
  const UInt multipleOf8 = 8 * (_nCells/8);
  UInt i;
  for (i = 0; i < multipleOf8; i += 8) {
    UInt64 eightStates = * (UInt64 *)(state.arrayPtr() + i);
    for (int k = 0; eightStates != 0  &&  k < 8; eightStates >>= 8, k++) {
      if ((eightStates & 0xff) != 0) {
        std::vector< OutSynapse >& os = _outSynapses[i + k];
        for (UInt j = 0; j != os.size(); ++j) {
          UInt dstCellIdx = os[j].dstCellIdx();
          UInt dstSegIdx = os[j].dstSegIdx();
          _inferActivity.increment(dstCellIdx, dstSegIdx);
        }
      }
    }
  }

  // process the tail if (_nCells % 8) != 0
  for (i = multipleOf8; i < _nCells; i++) {
    if (state.isSet(i)) {
      std::vector< OutSynapse >& os = _outSynapses[i];
      for (UInt j = 0; j != os.size(); ++j) {
        UInt dstCellIdx = os[j].dstCellIdx();
        UInt dstSegIdx = os[j].dstSegIdx();
        _inferActivity.increment(dstCellIdx, dstSegIdx);
      }
    }
  }
#else
  const UInt multipleOf4 = 4 * (_nCells/4);
  UInt i;
  for (i = 0; i < multipleOf4; i += 4) {
    UInt32 fourStates = * (UInt32 *)(state.arrayPtr() + i);
    for (int k = 0; fourStates != 0  &&  k < 4; fourStates >>= 8, k++) {
      if ((fourStates & 0xff) != 0) {
        std::vector< OutSynapse >& os = _outSynapses[i + k];
        for (UInt j = 0; j != os.size(); ++j) {
          UInt dstCellIdx = os[j].dstCellIdx();
          UInt dstSegIdx = os[j].dstSegIdx();
          _inferActivity.increment(dstCellIdx, dstSegIdx);
        }
      }
    }
  }

  // process the tail if (_nCells % 4) != 0
  for (i = multipleOf4; i < _nCells; i++) {
    if (state.isSet(i)) {
      std::vector< OutSynapse >& os = _outSynapses[i];
      for (UInt j = 0; j != os.size(); ++j) {
        UInt dstCellIdx = os[j].dstCellIdx();
        UInt dstSegIdx = os[j].dstSegIdx();
        _inferActivity.increment(dstCellIdx, dstSegIdx);
      }
    }
  }
#endif // NTA_PLATFORM_darwin86
}
#endif  // SOME_STATES_NOT_INDEXED


//--------------------------------------------------------------------------------
// Dump detailed Cells4 timing report to stdout
//--------------------------------------------------------------------------------
void Cells4::dumpTiming()
{
#ifdef CELLS4_TIMING
  Real64 learnTime = learningTimer.getElapsed(),
         inferenceTime = inferenceTimer.getElapsed();

  std::cout << "Total time in compute:   " << computeTimer.toString()   << "\n";
  std::cout << "Total time in learning:  " << learningTimer.toString()  << "\n";
  std::cout << "Total time in inference: " << inferenceTimer.toString() << "\n";

  std::cout << "\n\nLearning breakdown:" << std::endl;
  std::cout << "Phase 1: " << learnPhase1Timer.toString() << " "
            << std::setprecision(3)
            << 100.0 * learnPhase1Timer.getElapsed() / learnTime << "%\n";
  std::cout << "Phase 2: " << learnPhase2Timer.toString() << " "
            << std::setprecision(3)
            << 100.0 * learnPhase2Timer.getElapsed() / learnTime << "%\n";
  std::cout << "Backtrack: " << learnBacktrackTimer.toString() << " "
            << std::setprecision(3)
            << 100.0 * learnBacktrackTimer.getElapsed() / learnTime << "%\n";
  std::cout << "Forward prop: " << forwardLearnPropTimer.toString() << " "
            << std::setprecision(3)
            << 100.0 * forwardLearnPropTimer.getElapsed() / learnTime << "%\n";
  std::cout << "getCellForNewSegment: " << getNewCellTimer.toString() << " "
            << std::setprecision(3)
            << 100.0 * getNewCellTimer.getElapsed() / learnTime << "%\n";
  std::cout << "chooseCells: " << chooseCellsTimer.toString() << " "
            << std::setprecision(3)
            << 100.0 * chooseCellsTimer.getElapsed() / learnTime << "%\n";
  std::cout << "adaptSegment: " << adaptSegmentTimer.toString() << " "
                                << std::setprecision(3)
                                << 100.0 * adaptSegmentTimer.getElapsed() / learnTime
                                << "%\n";
  std::cout << "Note: % is percentage of learning time\n";

  std::cout << "\n\nInference breakdown:" << std::endl;
  std::cout << "Phase 1: " << infPhase1Timer.toString() << " "
            << std::setprecision(3)
            << 100.0 * infPhase1Timer.getElapsed() / inferenceTime << "%\n";
  std::cout << "Phase 2: " << infPhase2Timer.toString() << " "
            << std::setprecision(3)
            << 100.0 * infPhase2Timer.getElapsed() / inferenceTime << "%\n";
  std::cout << "Backtrack: " << infBacktrackTimer.toString() << " "
            << std::setprecision(3)
            << 100.0 * infBacktrackTimer.getElapsed() / inferenceTime << "%\n";
  std::cout << "Forward prop: " << forwardInfPropTimer.toString() << " "
            << std::setprecision(3)
            << 100.0 * forwardInfPropTimer.getElapsed() / inferenceTime << "%\n";
  std::cout << "Note: % is percentage of inference time\n";

#endif
}

//--------------------------------------------------------------------------------
// Reset timers and counters to 0
//--------------------------------------------------------------------------------
void Cells4::resetTimers()
{
#ifdef CELLS4_TIMING
  computeTimer.reset();
  inferenceTimer.reset();
  learningTimer.reset();
  learnPhase1Timer.reset();
  learnPhase2Timer.reset();
  learnBacktrackTimer.reset();
  forwardLearnPropTimer.reset();
  infPhase1Timer.reset();
  infPhase2Timer.reset();
  infBacktrackTimer.reset();
  forwardInfPropTimer.reset();
  getNewCellTimer.reset();
  chooseCellsTimer.reset();
#endif
}
