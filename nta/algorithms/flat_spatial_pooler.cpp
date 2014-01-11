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
 * ----------------------------------------------------------------------
 */

/** @file
 * Implementation of FlatSpatialPooler
 */

#include <math.h>
#include <iostream>
#include <cstring>
#include <string>
#include <vector>
#include <nta/algorithms/spatial_pooler.hpp>
#include <nta/algorithms/flat_spatial_pooler.hpp>

using namespace std;
using namespace nta;
using namespace nta::algorithms::spatial_pooler;


Real FlatSpatialPooler::getMinDistance()
{
  return minDistance_;
}

void FlatSpatialPooler::setMinDistance(Real minDistance)
{
  minDistance_ = minDistance;
}

bool FlatSpatialPooler::getRandomSP()
{
  return randomSP_;
}

void FlatSpatialPooler::setRandomSP(bool randomSP)
{
  randomSP_ = randomSP;
}


void FlatSpatialPooler::compute(UInt inputArray[], bool learn,
                                UInt activeArray[])
{
  if (randomSP_) {
    learn = false;
  }

  updateBookeepingVars_(learn);
  calculateOverlap_(inputArray, overlaps_);
  calculateOverlapPct_(overlaps_, overlapsPct_);

  selectHighTierColumns_(overlapsPct_, highTier_);
  selectVirginColumns_(virgin_);
  
  if (spVerbosity_ > 2) {
    std::cout << "---------CPP FlatSpatialPooler::compute() ------------\n";
    std::cout << "iterationNum_ = " << iterationNum_ << std::endl;
    std::cout << "minDistance_  = " << minDistance_ << std::endl;
    std::cout << "overlapsPct:\n";
    printState(overlapsPct_);
    std::cout << "CPP highTier columns:\n";
    printState(highTier_);
    std::cout << "CPP virgin columns:\n";
    printState(virgin_);
    std::cout << "-----------------------------------------------------\n";
  }

  if (learn) {
    boostOverlaps_(overlaps_, boostedOverlaps_);
  } else {
    boostedOverlaps_.assign(overlaps_.begin(), overlaps_.end());
  }

  Real bonus = *max_element(boostedOverlaps_.begin(),
                            boostedOverlaps_.end()) + 1;

  // Ensure one of the high tier columns win
  // If learning is on, ensure an unlearned column wins
  if (learn) {
    addBonus_(boostedOverlaps_, bonus, virgin_, true);
  }
  addBonus_(boostedOverlaps_, bonus, highTier_, false);

  inhibitColumns_(boostedOverlaps_, activeColumns_);
  toDense_(activeColumns_, activeArray, numColumns_);

  if (learn) {
    adaptSynapses_(inputArray, activeColumns_);
    updateDutyCycles_(overlaps_, activeArray);
    bumpUpWeakColumns_();
    updateBoostFactors_();

    if (isUpdateRound_()) {
      updateInhibitionRadius_();
      updateMinDutyCycles_();
    }
  } else {
    stripNeverLearned_(activeArray);
  }
}

void FlatSpatialPooler::addBonus_(
    vector<Real>& vec, Real bonus, vector<UInt>& indices, bool replace)
{
  for (UInt i = 0; i < indices.size(); i++) {
    UInt index = indices[i];
    if (replace) {
      vec[index] = bonus;
    } else {
      vec[index] += bonus;
    }
  }
}

void FlatSpatialPooler::selectVirginColumns_(vector<UInt>& virgin)
{
  virgin.clear();
  for (UInt i = 0; i < numColumns_; i++) {
    if (activeDutyCycles_[i] == 0) {
      virgin.push_back(i);
    }
  }
}

void FlatSpatialPooler::selectHighTierColumns_(vector<Real>& overlapsPct,
                                               vector<UInt> &highTier)
{
  highTier.clear();
  for (UInt i = 0; i < numColumns_; i++) {
    if (overlapsPct[i] >= (1.0 - minDistance_)) {
      highTier.push_back(i);
    }
  }
}

void FlatSpatialPooler::initializeFlat(
    UInt numInputs, UInt numColumns,
    Real potentialPct, Real localAreaDensity,
    UInt numActiveColumnsPerInhArea, UInt stimulusThreshold,
    Real synPermInactiveDec, Real synPermActiveInc, Real synPermConnected,
    Real minPctOverlapDutyCycles, Real minPctActiveDutyCycles,
    UInt dutyCyclePeriod, Real maxBoost, Real minDistance, bool randomSP,
    Int seed, UInt spVerbosity)
{
  // call parent class initialize
  vector<UInt> inputDimensions, columnDimensions;
  inputDimensions.push_back(numInputs);
  columnDimensions.push_back(numColumns);

  initialize(
    inputDimensions,
    columnDimensions,
    numInputs,
    potentialPct,
    true,             // Global inhibition is always true in the flat pooler
    localAreaDensity,
    numActiveColumnsPerInhArea,
    stimulusThreshold,
    synPermInactiveDec,
    synPermActiveInc,
    synPermConnected,
    minPctOverlapDutyCycles,
    minPctActiveDutyCycles,
    dutyCyclePeriod,
    maxBoost,
    seed,
    spVerbosity);

  minDistance_ = minDistance;
  randomSP_ = randomSP;

  activeDutyCycles_.assign(numColumns_, 1);
  boostFactors_.assign(numColumns_, maxBoost);
  
  // For high tier to work we need to set the min duty cycles to be non-zero
  // This will ensure that columns with 0 active duty cycle get high boost
  // in the beginning.
  minOverlapDutyCycles_.assign(numColumns_, 1e-6);
  minActiveDutyCycles_.assign(numColumns_, 1e-6);

  if (spVerbosity_ > 0) {
    printFlatParameters();
  }

}


void FlatSpatialPooler::save(ostream& outStream)
{

  SpatialPooler::save(outStream);


  // Write a starting marker and version.
  outStream << "FlatSpatialPooler" << endl;

  outStream << minDistance_ << " "
            << randomSP_ << endl;

  outStream << "~FlatSpatialPooler" << endl;

}

void FlatSpatialPooler::load(istream& inStream)
{

  SpatialPooler::load(inStream);

  // Check the marker
  string marker;
  inStream >> marker;
  NTA_CHECK(marker == "FlatSpatialPooler");

  inStream >> minDistance_
           >> randomSP_;

  inStream >> marker;
  NTA_CHECK(marker == "~FlatSpatialPooler");
}


//----------------------------------------------------------------------
// Debugging helpers
//----------------------------------------------------------------------

// Print the creation parameters specific to this class
void FlatSpatialPooler::printFlatParameters()
{
  std::cout << "            CPP FlatSpatialPooler Parameters\n";
  std::cout
    << "minDistance                 = " << getMinDistance() << std::endl
    << "randomSP                    = " << getRandomSP() << std::endl;
}
