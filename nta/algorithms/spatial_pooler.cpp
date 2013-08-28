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

#include <iostream>
#include <cstring>
#include <string>
#include <map>
#include <vector>
#include <nta/algorithms/spatial_pooler.hpp>

using namespace std;
using namespace nta;
using namespace nta::algorithms::spatial_pooler;

SpatialPooler::SpatialPooler(vector<UInt> inputDimensions,
  vector<UInt> columnDimensions,
  UInt potentialRadius=16,
  Real potentialPct=0.5,
  bool globalInhibition=true,
  Real localAreaDensity=-1.0,
  UInt numActiveColumnsPerInhArea=10,
  UInt stimulusThreshold=0,
  Real synPermInactiveDec=0.01,
  Real synPermActiveInc=0.1,
  Real synPermConnected=0.1,
  Real minPctOverlapDutyCycle=0.001,
  Real minPctActiveDutyCycle=0.001,
  UInt dutyCyclePeriod=1000,
  Real maxBoost=10.0,
  Int seed=1,
  UInt spVerbosity=0)
{
  initialize(inputDimensions, columnDimensions,potentialRadius, potentialPct, 
             globalInhibition, localAreaDensity, numActiveColumnsPerInhArea, 
             stimulusThreshold, synPermInactiveDec, synPermActiveInc, 
             synPermConnected, minPctOverlapDutyCycle, minPctActiveDutyCycle, 
             dutyCyclePeriod, maxBoost, seed, spVerbosity);
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

void SpatialPooler::setPermanence(UInt column, const vector<Real>& permanences)
{
  NTA_ASSERT(column < numColumns_);
  NTA_ASSERT(permanences.size() == numInputs_);
  permanences_.setRowFromDense(column, permanences);
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

  seed_(seed);

  potentialRadius_ = potentialRadius;
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

  inhibitionRadius_ = 0;

}

vector<UInt> SpatialPooler::compute(vector<UInt> inputVector, bool learn)
{
  vector<UInt> activeColumns(numColumns_, 0);
  return activeColumns;
}



void SpatialPooler::seed_(Int seed)
{
  return;
}

