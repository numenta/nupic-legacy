/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
 * with Numenta, Inc., for a separate license for this software code, the
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


#include <iomanip>
#include <vector>
#include <iostream>
#include <set>
#include <sstream>
#include <algorithm> // sort

#include <nta/utils/Random.hpp>
#include <nta/utils/Log.hpp>
#include <assert.h>
#include <map>
#include <nta/math/array_algo.hpp> // is_in
#include <nta/math/stl_io.hpp> // binary_save

#include <nta/algorithms/Segment.hpp>

using namespace nta::algorithms::Cells4;

//----------------------------------------------------------------------
/**
 * Utility routine. Given a src cell index, prints synapse as:
 *  [column, cell within col]
 */
void printSynapse(UInt srcCellIdx, UInt nCellsPerCol)
{
  UInt col =  (UInt) (srcCellIdx / nCellsPerCol);
  UInt cell = srcCellIdx - col*nCellsPerCol;
  std::cout << "[" << col << "," << cell << "]  ";
}


//----------------------------------------------------------------------
Segment::Segment(const InSynapses& _s, Real frequency, bool seqSegFlag,
        Real permConnected, UInt iteration)
  : _totalActivations(1),
    _positiveActivations(1),
    _lastActiveIteration(0),
    _lastPosDutyCycle(1.0 / iteration),
    _lastPosDutyCycleIteration(iteration),
    _seqSegFlag(seqSegFlag),
    _frequency(frequency),
    _synapses(_s),
    _nConnected(0)
{
  for (UInt i = 0; i != _synapses.size(); ++i)
    if (_synapses[i].permanence() >= permConnected)
      ++ _nConnected;

  std::sort(_synapses.begin(), _synapses.end(), InSynapseOrder());
  NTA_ASSERT(invariants());
}

//--------------------------------------------------------------------------------
Segment& Segment::operator=(const Segment& o)
{
  if (&o != this) {
    _seqSegFlag = o._seqSegFlag;
    _frequency = o._frequency;
    _synapses = o._synapses;
    _nConnected = o._nConnected;
    _totalActivations = o._totalActivations;
    _positiveActivations = o._positiveActivations;
    _lastActiveIteration = o._lastActiveIteration;
    _lastPosDutyCycle = o._lastPosDutyCycle;
    _lastPosDutyCycleIteration = o._lastPosDutyCycleIteration;
  }
  NTA_ASSERT(invariants());
  return *this;
}



//--------------------------------------------------------------------------------
Segment::Segment(const Segment& o)
  : _totalActivations(o._totalActivations),
    _positiveActivations(o._positiveActivations),
    _lastActiveIteration(o._lastActiveIteration),
    _lastPosDutyCycle(o._lastPosDutyCycle),
    _lastPosDutyCycleIteration(o._lastPosDutyCycleIteration),
    _seqSegFlag(o._seqSegFlag),
    _frequency(o._frequency),
    _synapses(o._synapses),
    _nConnected(o._nConnected)
{
  NTA_ASSERT(invariants());
}



bool Segment::isActive(const CState& activities,
           Real permConnected, UInt activationThreshold) const
{
  {
    NTA_ASSERT(invariants());
  }

  UInt activity = 0;

  if (_nConnected < activationThreshold)
    return false;

  // TODO: maintain nPermConnected incrementally??
  for (UInt i = 0; i != size() && activity < activationThreshold; ++i)
    if (_synapses[i].permanence() >= permConnected  &&  activities.isSet(_synapses[i].srcCellIdx()))
      activity++;

  return activity >= activationThreshold;
}

//----------------------------------------------------------------------
/**
 * Compute/update and return the positive activations duty cycle of
 * this segment. This is a measure of how often this segment is
 * providing good predictions.
 *
 */
Real Segment::dutyCycle(UInt iteration, bool active, bool readOnly)
{
  {
    NTA_ASSERT(iteration > 0);
  }

  Real dutyCycle = 0.0;

  // For tier 0, compute it from total number of positive activations seen
  if (iteration <= _dutyCycleTiers[1]) {
    dutyCycle = ((Real) _positiveActivations) / iteration;
    if (!readOnly) {
      _lastPosDutyCycleIteration = iteration;
      _lastPosDutyCycle = dutyCycle;
    }
    return dutyCycle;
  }

  // How old is our update?
  UInt age = iteration - _lastPosDutyCycleIteration;

  // If it's already up to date we can return our cached value
  if ( age == 0 && !active)
    return _lastPosDutyCycle;

  // Figure out which alpha we're using
  Real alpha = 0;
  for (UInt tierIdx= _numTiers-1; tierIdx > 0; tierIdx--)
  {
    if (iteration > _dutyCycleTiers[tierIdx]) {
      alpha = _dutyCycleAlphas[tierIdx];
      break;
    }
  }

  // Update duty cycle
  dutyCycle = pow((Real64) (1.0 - alpha), (Real64)age) * _lastPosDutyCycle;
  if (active)
    dutyCycle += alpha;

  // Update the time we computed it
  if (!readOnly) {
    _lastPosDutyCycle = dutyCycle;
    _lastPosDutyCycleIteration = iteration;
  }

  return dutyCycle;
}

UInt Segment::computeActivity(const CState& activities, Real permConnected,
                              bool connectedSynapsesOnly) const

{
  {
    NTA_ASSERT(invariants());
  }

  UInt activity = 0;

  if (connectedSynapsesOnly) {
    for (UInt i = 0; i != size(); ++i)
      if (activities.isSet(_synapses[i].srcCellIdx())  &&  (_synapses[i].permanence() >= permConnected))
        activity++;
  } else {
    for (UInt i = 0; i != size(); ++i)
      if (activities.isSet(_synapses[i].srcCellIdx()))
        activity++;
  }

  return activity;
}

void
Segment::addSynapses(const std::set<UInt>& srcCells, Real initStrength,
                     Real permConnected)
{
  std::set<UInt>::const_iterator srcCellIdx = srcCells.begin();

  for (; srcCellIdx != srcCells.end(); ++srcCellIdx) {
    _synapses.push_back(InSynapse(*srcCellIdx, initStrength));
    if (initStrength >= permConnected)
      ++ _nConnected;
  }

  sort(_synapses, InSynapseOrder());
  NTA_ASSERT(invariants()); // will catch non-unique synapses
}

void Segment::decaySynapses(Real decay, std::vector<UInt>& removed,
              Real permConnected, bool doDecay)
{
  NTA_ASSERT(invariants());

  if (_synapses.empty())
    return;

  static std::vector<UInt> del;
  del.clear();                              // purge residual data

  for (UInt i = 0; i != _synapses.size(); ++i) {

    int wasConnected = (int) (_synapses[i].permanence() >= permConnected);

    if (_synapses[i].permanence() < decay) {

      removed.push_back(_synapses[i].srcCellIdx());
      del.push_back(i);

    } else if (doDecay) {
      _synapses[i].permanence() -= decay;
    }

    int isConnected = (int) (_synapses[i].permanence() >= permConnected);

    _nConnected += isConnected - wasConnected;
  }

  _removeSynapses(del);

  NTA_ASSERT(invariants());
}


//--------------------------------------------------------------------------------
/**
 * Subtract decay from each synapses' permanence value.
 * Synapses whose permanence drops below 0 are removed and their indices
 * are inserted into the "removed" list.
 *
 */
void Segment::decaySynapses2(Real decay, std::vector<UInt>& removed,
                    Real permConnected)
{
  NTA_ASSERT(invariants());

  if (_synapses.empty())
    return;

  static std::vector<UInt> del;
  del.clear();                              // purge residual data

  for (UInt i = 0; i != _synapses.size(); ++i) {

    // Remove synapse whose permanence will go to zero or below.
    if (_synapses[i].permanence() <= decay) {

      // If it was connected, reduce our connected count
      if (_synapses[i].permanence() >= permConnected)
        _nConnected--;

      // Add this synapse to list of synapses to be removed
      removed.push_back(_synapses[i].srcCellIdx());
      del.push_back(i);

    } else {

      _synapses[i].permanence() -= decay;

      // If it was connected and is now below permanence, reduce connected count
      if ( (_synapses[i].permanence() + decay >= permConnected)
           && (_synapses[i].permanence() < permConnected) )
        _nConnected--;
    }

  }

  _removeSynapses(del);

  NTA_ASSERT(invariants());
}

//-----------------------------------------------------------------------
/**
 * Sort order for InSynapse's. Cells are sorted in order of increasing
 * permanence.
 *
 */
struct InPermanenceOrder
{
  inline bool operator()(const InSynapse& a, const InSynapse& b) const
  {
    return a.permanence() < b.permanence();
  }
};

//-----------------------------------------------------------------------
/**
 * Sort order for list of source cell indices. Cells are sorted in order of
 * increasing source cell index.
 *
 */
struct InSrcCellOrder
{
  inline bool operator()(const UInt a, const UInt b) const
  {
    return a < b;
  }
};


//----------------------------------------------------------------------
/**
 * Free up some synapses in this segment. We always free up inactive
 * synapses (lowest permanence freed up first) before we start to free
 * up active ones.
 *
 * TODO: Implement stable tie breaker for the case where you have multiple
 * synapses with the same lowest permanence
 */
void Segment::freeNSynapses(UInt numToFree,
                            std::vector<UInt> &inactiveSynapseIndices,
                            std::vector<UInt> &inactiveSegmentIndices,
                            std::vector<UInt> &activeSynapseIndices,
                            std::vector<UInt> &activeSegmentIndices,
                            std::vector<UInt>& removed, UInt verbosity,
                            UInt nCellsPerCol, Real permMax)
{

  NTA_CHECK(inactiveSegmentIndices.size() == inactiveSynapseIndices.size());

  if (verbosity >= 4) {
    std::cout << "\nIn CPP freeNSynapses with numToFree = " << numToFree
    << ", inactiveSynapses = ";
    for (UInt i = 0; i<inactiveSynapseIndices.size(); i++)
    {
      printSynapse(inactiveSynapseIndices[i], nCellsPerCol);
    }
    std::cout << "\n";
  }

  //----------------------------------------------------------------------
  // Collect candidate synapses for deletion

  // We first choose from inactive synapses, in order of increasing permanence
  InSynapses candidates;
  for (UInt i = 0; i < inactiveSegmentIndices.size(); i++)
  {
    // Put in *segment indices*, not source cell indices
    candidates.push_back(InSynapse(inactiveSegmentIndices[i],
                                   _synapses[i].permanence()));
  }

  // If we need more, choose from active synapses in order of increasing
  // permanence values. This set has lower priority than inactive synapses
  // so we add a constant permanence value for sorting purposes
  if (candidates.size() < numToFree) {
    for (UInt i = 0; i < activeSegmentIndices.size(); i++)
    {
      // Put in *segment indices*, not source cell indices
      candidates.push_back(InSynapse(activeSegmentIndices[i],
                                     _synapses[i].permanence() + permMax));
    }
  }

  // Now sort the list of candidate synapses
  std::sort(candidates.begin(), candidates.end(), InPermanenceOrder());

  //----------------------------------------------------------------------
  // Create the final list of synapses we will remove
  static std::vector<UInt> del;
  del.clear();                              // purge residual data
  for (UInt i = 0; i < numToFree; i++)
  {
    del.push_back(candidates[i].srcCellIdx());
    UInt cellIdx = _synapses[candidates[i].srcCellIdx()].srcCellIdx();
    removed.push_back(cellIdx);
  }

  // Debug statements
  if (verbosity >= 4) {
    std::cout << "Removing these synapses: ";
    for (UInt i = 0; i < removed.size(); i++)
    {
      printSynapse(removed[i], nCellsPerCol);
    }
    std::cout << "\n";

    std::cout << "Segment BEFORE remove synapses: ";
    print(std::cout, nCellsPerCol);
    std::cout << "\n";
  }

  //----------------------------------------------------------------------
  // Remove the synapses
  if (numToFree > 0) {
    std::sort(del.begin(), del.end(), InSrcCellOrder());
    _removeSynapses(del);
  }

  // Debug statements
  if (verbosity >= 4)
  {
    std::cout << "Segment AFTER remove synapses: ";
    print(std::cout, nCellsPerCol);
    std::cout << "\n";
  }
}




void Segment::print(std::ostream& outStream, UInt nCellsPerCol) const
{
  outStream << (_seqSegFlag ? "True " : "False ")
            << "dc" << std::setprecision(4) << _lastPosDutyCycle << " ("
            << _positiveActivations << "/" << _totalActivations << ") ";
  for (UInt i = 0; i != _synapses.size(); ++i) {
    if (nCellsPerCol > 0) {
      UInt cellIdx = _synapses[i].srcCellIdx();
      UInt col =  (UInt) (cellIdx / nCellsPerCol);
      UInt cell = cellIdx - col*nCellsPerCol;
      outStream << "[" << col << "," << cell << "]"
                << std::setprecision(4) << _synapses[i].permanence()
                << " ";
    } else {
      outStream << _synapses[i];
    }
    if (i < _synapses.size() -1)
      std::cout << " ";
  }
}

namespace nta{
  namespace algorithms {
    namespace Cells4 {

      std::ostream& operator<<(std::ostream& outStream, const Segment& seg)
      {
        seg.print(outStream);
        return outStream;
      }

      std::ostream& operator<<(std::ostream& outStream, const CState& cstate)
      {
        cstate.print(outStream);
        return outStream;
      }

      std::ostream& operator<<(
          std::ostream& outStream, const CStateIndexed& cstate)
      {
        cstate.print(outStream);
        return outStream;
      }
    }
  }
}

