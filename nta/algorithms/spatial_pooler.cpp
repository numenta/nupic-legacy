/*----------------------------------------------------------------------
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
 * ----------------------------------------------------------------------
 */

/** @file
 * Implementation of SpatialPooler
 */

#include <math.h>
#include <iostream>
#include <cstring>
#include <string>
#include <map>
#include <vector>
#include <nta/algorithms/spatial_pooler.hpp>

using namespace std;
using namespace nta;
using namespace nta::algorithms::spatial_pooler;

SpatialPooler::SpatialPooler() { }

UInt SpatialPooler::getPotentialRadius() 
{ 
  return potentialRadius_; 
}

void SpatialPooler::setPotentialRadius(UInt potentialRadius)
{ 
  potentialRadius_ = potentialRadius; 
}

Real SpatialPooler::getPotentialPct() 
{ 
  return potentialPct_; 
}

void SpatialPooler::setPotentialPct(Real potentialPct)
{ 
  potentialPct_ = potentialPct; 
}

          
bool SpatialPooler::getGlobalInhibition() 
{ 
  return globalInhibition_; 
}

void SpatialPooler::setGlobalInhibition(bool globalInhibition)
{ 
  globalInhibition_ = globalInhibition; 
}

UInt SpatialPooler::getNumActiveColumnsPerInhArea()
{ 
  return numActiveColumnsPerInhArea_; 
}

void SpatialPooler::setNumActiveColumnsPerInhArea(UInt 
  numActiveColumnsPerInhArea) 
{ 
  numActiveColumnsPerInhArea_ = numActiveColumnsPerInhArea; 
}

Real SpatialPooler::getLocalAreaDensity()
{
  return localAreaDensity_;
}

void SpatialPooler::setLocalAreaDensity(Real localAreaDensity)
{
  localAreaDensity_ = localAreaDensity;
}

UInt SpatialPooler::getStimulusThreshold()
{
  return stimulusThreshold_;
}

void SpatialPooler::setStimulusThreshold(UInt stimulusThreshold)
{
  stimulusThreshold_ = stimulusThreshold;
}

UInt SpatialPooler::getInhibitionRadius()
{
  return inhibitionRadius_;
}

void SpatialPooler::setInhibitionRadius(UInt inhibitionRadius)
{
  inhibitionRadius_ = inhibitionRadius;
}

UInt SpatialPooler::getDutyCyclePeriod()
{
  return dutyCyclePeriod_;
}

void SpatialPooler::setDutyCyclePeriod(UInt dutyCyclePeriod)
{
  dutyCyclePeriod_ = dutyCyclePeriod;
}

Real SpatialPooler::getMaxBoost()
{
  return maxBoost_;
}

void SpatialPooler::setMaxBoost(Real maxBoost)
{
  maxBoost_ = maxBoost;
}

UInt SpatialPooler::getIterationNum()
{
  return iterationNum_;
}

void SpatialPooler::setIterationNum(UInt iterationNum)
{
  iterationNum_ = iterationNum;
}

UInt SpatialPooler::getIterationLearnNum()
{
  return iterationLearnNum_;
}

void SpatialPooler::setIterationLearnNum(UInt iterationLearnNum)
{
  iterationLearnNum_ = iterationLearnNum;
}

UInt SpatialPooler::getSpVerbosity()
{
  return spVerbosity_;
}

void SpatialPooler::setSpVerbosity(UInt spVerbosity)
{
  spVerbosity_ = spVerbosity;
}

UInt SpatialPooler::getUpatePeriod()
{
  return updatePeriod_;
}

void SpatialPooler::setUpdatePeriod(UInt updatePeriod)
{
  updatePeriod_ = updatePeriod;
}

Real SpatialPooler::getSynPermTrimThreshold()
{
  return synPermTrimThreshold_;
}

void SpatialPooler::setSynPermTrimThreshold(Real synPermTrimThreshold)
{
  synPermTrimThreshold_ = synPermTrimThreshold;
}

Real SpatialPooler::getSynPermActiveInc()
{
  return synPermActiveInc_;
}

void SpatialPooler::setSynPermActiveInc(Real synPermActiveInc)
{
  synPermActiveInc_ = synPermActiveInc;
}

Real SpatialPooler::getSynPermInactiveDec()
{
  return synPermInactiveDec_;
}

void SpatialPooler::setSynPermInactiveDec(Real synPermInactiveDec)
{
  synPermInactiveDec_ = synPermInactiveDec;
}

Real SpatialPooler::getSynPermBelowStimulusInc()
{
  return synPermBelowStimulusInc_;
}

void SpatialPooler::setSynPermBelowStimulusInc(Real synPermBelowStimulusInc)
{
  synPermBelowStimulusInc_ = synPermBelowStimulusInc;
}

Real SpatialPooler::getSynPermConnected()
{
  return synPermConnected_; 
}

void SpatialPooler::setSynPermConnected(Real synPermConnected)
{
  synPermConnected_ = synPermConnected;
}

Real SpatialPooler::getMinPctOverlapDutyCycles()
{
  return minPctOverlapDutyCycles_;
}

void SpatialPooler::setMinPctOverlapDutyCycles(Real minPctOverlapDutyCycles)
{
  minPctOverlapDutyCycles_ = minPctOverlapDutyCycles;
}

Real SpatialPooler::getMinPctActiveDutyCycles()
{
  return minPctActiveDutyCycles_;
}

void SpatialPooler::setMinPctActiveDutyCycles(Real minPctActiveDutyCycles)
{
  minPctActiveDutyCycles_ = minPctActiveDutyCycles;
}

vector<Real> SpatialPooler::getBoostFactors() 
{
  return boostFactors_;
}

void SpatialPooler::setBoostFactors(const vector<Real>& boostFactors) 
{
  NTA_ASSERT(boostFactors.size() == numColumns_);
  boostFactors_.assign(boostFactors.begin(), boostFactors.end());
}

vector<Real> SpatialPooler::getOverlapDutyCycles()
{
  return overlapDutyCycles_;
}

void SpatialPooler::setOverlapDutyCycles(const vector<Real>& overlapDutyCycles)
{
  NTA_ASSERT(overlapDutyCycles.size() == numColumns_);
  overlapDutyCycles_.assign(overlapDutyCycles.begin(), overlapDutyCycles.end());
}

vector<Real> SpatialPooler::getActiveDutyCycles()
{
  return activeDutyCycles_;
}

void SpatialPooler::setActiveDutyCycles(const vector<Real>& activeDutyCycles)
{
  NTA_ASSERT(activeDutyCycles.size() == numColumns_);
  activeDutyCycles_.assign(activeDutyCycles.begin(), activeDutyCycles.end());
}

vector<Real> SpatialPooler::getMinOverlapDutyCycles()
{
  return minOverlapDutyCycles_;
}

void SpatialPooler::setMinOverlapDutyCycles(const vector<Real>& minOverlapDutyCycles)
{
  NTA_ASSERT(minOverlapDutyCycles.size() == numColumns_);
  minOverlapDutyCycles_.assign(minOverlapDutyCycles.begin(), 
                               minOverlapDutyCycles.end());
}

vector<Real> SpatialPooler::getMinActiveDutyCycles()
{
  return minActiveDutyCycles_;
}
void SpatialPooler::setMinActiveDutyCycles(const vector<Real>& minActiveDutyCycles)
{
  NTA_ASSERT(minActiveDutyCycles.size() == numColumns_);
  minActiveDutyCycles_.assign(minActiveDutyCycles.begin(), 
                               minActiveDutyCycles.end());
}

vector<UInt> SpatialPooler::getPotential(UInt column) 
{
  NTA_ASSERT(column < numColumns_);
  vector<UInt> potential(numInputs_,0);
  potentialPools_.getRow(column, potential.begin(), potential.end());
  return potential;
}

void SpatialPooler::setPotential(UInt column, const vector<UInt>& potential) 
{
  NTA_ASSERT(potential.size() == numInputs_);
  NTA_ASSERT(column < numColumns_);
  potentialPools_.rowFromDense(column, potential.begin(), potential.end());
}

vector<Real> SpatialPooler::getPermanence(UInt column)
{
  NTA_ASSERT(column < numColumns_);
  vector<Real> perm(numInputs_,0);
  permanences_.getRowToDense(column, perm);
  return perm;
}

void SpatialPooler::setPermanence(UInt column, vector<Real>& permanences)
{
  NTA_ASSERT(column < numColumns_);
  NTA_ASSERT(permanences.size() == numInputs_);
  updatePermanencesForColumn_(permanences, column, false);
}

vector<UInt> SpatialPooler::getConnected(UInt column) 
{
  NTA_ASSERT(column < numColumns_);
  vector<UInt> connected(numInputs_,0);
  connectedSynapses_.getRow(column,connected.begin(),connected.end());
  return connected;
}

vector<UInt> SpatialPooler::getConnectedCounts() 
{
  return connectedCounts_;
}



void SpatialPooler::initialize(vector<UInt> inputDimensions,
  vector<UInt> columnDimensions,
  UInt potentialRadius,
  Real potentialPct,
  bool globalInhibition,
  Real localAreaDensity,
  UInt numActiveColumnsPerInhArea,
  UInt stimulusThreshold,
  Real synPermInactiveDec,
  Real synPermActiveInc,
  Real synPermConnected,
  Real minPctOverlapDutyCycles,
  Real minPctActiveDutyCycles,
  UInt dutyCyclePeriod,
  Real maxBoost,
  Int seed,
  UInt spVerbosity) {

  numInputs_ = 1;
  for (size_t i = 0; i < inputDimensions.size(); ++i)
  {  
    numInputs_ *= inputDimensions[i];
    inputDimensions_.push_back(inputDimensions[i]);
  }

  numColumns_ = 1;
  for (size_t i = 0; i < inputDimensions.size(); ++i)
  {
    numColumns_ *= columnDimensions[i];
    columnDimensions_.push_back(columnDimensions[i]);
  }

  NTA_ASSERT(numColumns_ > 0);
  NTA_ASSERT(numInputs_ > 0);
  NTA_ASSERT(numActiveColumnsPerInhArea > 0 || localAreaDensity > 0);
  NTA_ASSERT(localAreaDensity < 0 ||
    localAreaDensity > 0 && localAreaDensity <= 0.5);
  NTA_ASSERT(potentialPct > 0 && potentialPct <= 1);

  seed_(seed);

  potentialRadius_ = potentialRadius > numInputs_ ? numInputs_ : 
                                                    potentialRadius;
  potentialPct_ = potentialPct;
  globalInhibition_ = globalInhibition;
  numActiveColumnsPerInhArea_ = numActiveColumnsPerInhArea;
  localAreaDensity_ = localAreaDensity;
  stimulusThreshold_ = stimulusThreshold;
  synPermInactiveDec_ = synPermInactiveDec;
  synPermActiveInc_ = synPermActiveInc;
  synPermBelowStimulusInc_ = synPermConnected / 10.0;
  synPermConnected_ = synPermConnected;
  minPctOverlapDutyCycles_ = minPctOverlapDutyCycles;
  minPctActiveDutyCycles_ = minPctActiveDutyCycles;
  dutyCyclePeriod_ = dutyCyclePeriod;
  maxBoost_ = maxBoost;
  spVerbosity_ = spVerbosity;
  synPermMin_ = 0.0;
  synPermMax_ = 1.0;
  synPermTrimThreshold_ = synPermActiveInc / 2.0;
  NTA_ASSERT(synPermTrimThreshold_ < synPermConnected_);
  updatePeriod_ = 50;
  initConnectedPct_ = 0.5;
  version_ = 1.0;
  iterationNum_ = 0;
  iterationLearnNum_ = 0;


  potentialPools_.resize(numColumns_, numInputs_);
  permanences_.resize(numColumns_, numInputs_);
  connectedSynapses_.resize(numColumns_, numInputs_);
  connectedCounts_.resize(numColumns_);

  overlapDutyCycles_.assign(numColumns_, 0);
  activeDutyCycles_.assign(numColumns_, 0);
  minOverlapDutyCycles_.assign(numColumns_, 0);
  minActiveDutyCycles_.assign(numColumns_, 0);
  boostFactors_.assign(numColumns_, 1);
  overlaps.assign(numColumns_, 0);

  inhibitionRadius_ = 0;

  for (UInt i = 0; i < numColumns_; ++i)
  {
    vector<UInt> potential = mapPotential1D_(i,true);
    vector<Real> perm = initPermanence_(potential, initConnectedPct_);
    potentialPools_.rowFromDense(i,potential.begin(),potential.end());
    updatePermanencesForColumn_(perm,i,true);
  }

  updateInhibitionRadius_();

}

Real SpatialPooler::real_rand()
{
  return ((double)rand()/(double)RAND_MAX);
}

vector<UInt> SpatialPooler::compute(vector<UInt> inputVector, bool learn)
{
  // TODO: implement stub
  vector<UInt> activeColumns(numColumns_, 0);
  return activeColumns;
}

vector<UInt> SpatialPooler::mapPotential1D_(UInt column, bool wrapAround)
{
  vector<UInt> potential(numInputs_,0);
  vector<Int> indices;
  for (Int i = -potentialRadius_ + column; i <= Int(potentialRadius_ + column); 
       i++)
    {
      if (wrapAround) {
        indices.push_back((i + numInputs_) % numInputs_);
      } else if (i >= 0 && i < Int(numInputs_)) {
        indices.push_back(i);
      }
    }

  random_shuffle(indices.begin(),indices.end(),rgen_);
  Int numPotential = Int(round(indices.size() * potentialPct_));
  for (Int i = 0; i < numPotential; i++) {
    potential[indices[i]] = 1;
  }
  
  return potential;
}

Real SpatialPooler::initPermConnected_()
{
  return synPermConnected_ + real_rand() * synPermActiveInc_ / 4.0;
}

Real SpatialPooler::initPermUnconnected_()
{
  return synPermConnected_ * real_rand();
}

vector<Real> SpatialPooler::initPermanence_(vector<UInt>& potential, 
                                            Real connectedPct)
{
  vector<Real> perm(numInputs_, 0);
  for (UInt i = 0; i < numInputs_; i++) {
    if (potential[i] < 1) {
      continue;
    }

    if (real_rand() < connectedPct) {
      perm[i] = initPermConnected_();
    } else {
      perm[i] = initPermUnconnected_();
    } 
    perm[i] = perm[i] < synPermTrimThreshold_ ? 0 : perm[i];
  }

  return perm;
}

void SpatialPooler::clip_(vector<Real>& perm, bool trim=false)
{
  Real minVal = trim ? synPermTrimThreshold_ : synPermMin_;
  for (UInt i = 0; i < perm.size(); i++)
  {
    perm[i] = perm[i] > synPermMax_ ? synPermMax_ : perm[i];
    perm[i] = perm[i] < minVal ? synPermMin_ : perm[i];
  }
}


void SpatialPooler::updatePermanencesForColumn_(vector<Real>& perm, UInt column,
                                                bool raisePerm)
{
  vector<UInt> connected(numInputs_,0);

  UInt numConnected;
  if (raisePerm) {
    vector<UInt> potential = getPotential(column);
    raisePermanencesToThreshold_(perm,potential);
  }

  numConnected = 0;
  for (UInt i = 0; i < perm.size(); ++i)
  {
    if (perm[i] > synPermConnected_) {
      connected[i] = 1;
      ++numConnected;
    }
  }

  clip_(perm, true);
  connectedSynapses_.rowFromDense(column,connected.begin(), connected.end());
  permanences_.setRowFromDense(column, perm);
  connectedCounts_[column] = numConnected;
}

UInt SpatialPooler::countConnected_(vector<Real>& perm)
{
  UInt numConnected = 0;
  for (UInt i = 0; i < perm.size(); i++) {
     if (perm[i] > synPermConnected_) {
       ++numConnected;
     }
   }
  return numConnected;
}

UInt SpatialPooler::raisePermanencesToThreshold_(vector<Real>& perm, 
                                                 vector<UInt>& potential)
{
  clip_(perm);
  UInt numConnected;
  while (true) 
  {
    numConnected = countConnected_(perm);
    if (numConnected >= stimulusThreshold_)
      break;

    for (UInt i = 0; i < numInputs_; i++) {
      if (potential[i] > 0) {
        perm[i] += synPermBelowStimulusInc_;
      }
    }
  }
  return numConnected;
}

void SpatialPooler::updateInhibitionRadius_()
{
  // TODO: implement
  return;
}

void SpatialPooler::updateMinDutyCycles_()
{
  // TODO: implement
  return;
}

void SpatialPooler::updateMinDutyCyclesGlobal_()
{
  // TODO: implement
  return;
}

void SpatialPooler::updateMinDutyCyclesLocal_()
{
  // TODO: implement
  return;
}

void SpatialPooler::updateDutyCycles_(vector<UInt>& overlaps, 
                       vector<UInt>& activeColumns)
{
  // TODO: implement
  return;
}

void SpatialPooler::avgColumnsPerInput_()
{
  // TODO: implement
  return;
}

void SpatialPooler::avgConnectedSpanForColumn1D_(UInt column)
{
  // TODO: implement
  return;
}

void SpatialPooler::avgConnectedSpanForColumn2D_(UInt column)
{
  // TODO: implement
  return;
}

void SpatialPooler::avgConnectedSpanForColumnND_(UInt column)
{
  // TODO: implement
  return;
}

void SpatialPooler::adaptSynapses_(vector<UInt>& inputVector, 
                    vector<UInt>& activeColumns)
{
  // TODO: implement
  return;
}

void SpatialPooler::bumpUpWeakColumns_()
{
  // TODO: implement
  return;
}

void SpatialPooler::updateDutyCyclesHelper_(vector<Real>& dutyCycles, 
                                     vector<UInt> newValues, 
                                     UInt period)
{
  // TODO: implement
  return;
}

void SpatialPooler::updateBoostFactors_()
{
  // TODO: implement
  return;
}

void SpatialPooler::updateBookeepingVars_(bool learn)
{
  // TODO: implement
  return;
}

void SpatialPooler::calculateOverlap_(vector<UInt>& inputVector,
                                      vector<UInt>& overlaps)
{
  overlaps.assign(numColumns_,0);
  connectedSynapses_.rightVecSumAtNZ(inputVector.begin(),inputVector.end(),
    overlaps.begin(),overlaps.end());
  if (stimulusThreshold_ > 0) {
    for (UInt i = 0; i < numColumns_; i++) {
      if (overlaps[i] < stimulusThreshold_) {
        overlaps[i] = 0;
      }
    }
  }
  return;
}

void SpatialPooler::calculateOverlapPct_(vector<UInt>& overlaps,
                                         vector<Real>& overlapPct)
{
  overlapPct.assign(numColumns_,0);
  for (UInt i = 0; i < numColumns_; i++) {
    overlapPct[i] = ((Real) overlaps[i]) / connectedCounts_[i];
  }
}

// Makes a copy of overlaps
void SpatialPooler::inhibitColumns_(vector<UInt>& overlaps, 
                     vector<UInt>& activeColumns)
{
  Real density = localAreaDensity_;
  if (localAreaDensity_ < 0) {
    UInt inhibitionArea = pow((Real) (2 * inhibitionRadius_ + 1),
                              (Real) columnDimensions_.size());
    inhibitionArea = min(inhibitionArea, numColumns_);
    density = ((Real) numActiveColumnsPerInhArea_) / inhibitionArea;
    density = min(density, (Real) 0.5);
  }

  vector<Real> overlapsReal;
  overlapsReal.resize(numColumns_);
  for (UInt i = 0; i < numColumns_; i++) {
    overlapsReal[i] = overlaps[i] + 0.1 * real_rand();
  }

  if (globalInhibition_ || 
      inhibitionRadius_ > max_element(columnDimensions_)) {
    inhibitColumnsGlobal_(overlapsReal, density, activeColumns);
  } else {
    inhibitColumnsLocal_(overlapsReal, density, activeColumns);
  }
}

void SpatialPooler::inhibitColumnsGlobal_(vector<Real>& overlaps, Real density,
                           vector<UInt>& activeColumns)
{
  UInt numActive = (UInt) density * numColumns_;
  activeColumns_.assign(0, numColumns_);
  vector<pair<UInt, Real> > winners(0, numActive);  
  for (UInt i = 0; i < numColumns_; i++) {
    if (is_winner_(activeColumns_[i], winners)) {
      add_to_winners_(i,activeColumns_[i], winners);
    }
  }

  for (UInt i = 0; i < numActive; i++) {
    activeColumns_[winners[i]] = 1;
  }
}

void SpatialPooler::inhibitColumnsLocal_(vector<Real>& overlaps, Real density,
                           vector<UInt>& activeColumns)
{
  // TODO: implement
  return;
}

void SpatialPooler::getNeighbors1D_(UInt column, vector<UInt>& dimensions, 
                     UInt radius, bool wrapAround)
{
  // TODO: implement
  return;
}

void SpatialPooler::getNeighbors2D_(UInt column, vector<UInt>& dimensions, 
                     UInt radius, bool wrapAround)
{
  // TODO: implement
  return;
}

void SpatialPooler::getNeighborsND_(UInt column, vector<UInt>& dimensions, 
                     UInt radius, bool wrapAround)
{
  // TODO: implement
  return;
}

bool SpatialPooler::isUpdateRound_()
{
  // TODO: implement
  return true;
}


void SpatialPooler::seed_(Int seed)
{
  rgen_ = Random(seed);
}

