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
 * Definitions for the Spatial Pooler
 */
#ifndef NTA_spatial_pooler_HPP
#define NTA_spatial_pooler_HPP

#include <nta/types/types.hpp>
#include <nta/math/SparseMatrix.hpp>
#include <nta/math/SparseBinaryMatrix.hpp>
#include <cstring>
#include <string>
#include <vector>
#include <iostream>

using namespace std;

namespace nta {
  namespace algorithms {
    namespace spatial_pooler {

      /////////////////////////////////////////////////////////////////////////
      /// CLA spatial pooler implementation in C++.
      ///
      /// @b Responsibility
      /// The Spatial Pooler is responsible for creating a sparse distributed
      /// representation of the input. It computes the set of active columns.
      /// It maintains the state of the proximal dendrites between the columns
      /// and the inputs bits and keeps track of the activity and overlap
      /// duty cycles
      ///
      /// @b Description
      /// Todo.
      ///
      /////////////////////////////////////////////////////////////////////////
      class SpatialPooler {
        public:
          SpatialPooler();

          ~SpatialPooler() {}

          virtual UInt version() const {
            return version_;
          };

          virtual void compute(UInt inputVector[], bool learn,
                       UInt activeVector[]);

          UInt getNumColumns();
          UInt getNumInputs();

          UInt getPotentialRadius();
          void setPotentialRadius(UInt potentialRadius);

          Real getPotentialPct();
          void setPotentialPct(Real potentialPct);

          bool getGlobalInhibition();
          void setGlobalInhibition(bool globalInhibition);
          
          Int getNumActiveColumnsPerInhArea();
          void setNumActiveColumnsPerInhArea(UInt numActiveColumnsPerInhArea);
          
          Real getLocalAreaDensity();
          void setLocalAreaDensity(Real localAreaDensity);
          
          UInt getStimulusThreshold();
          void setStimulusThreshold(UInt stimulusThreshold);
          
          UInt getInhibitionRadius();
          void setInhibitionRadius(UInt inhibitionRadius);
          
          UInt getDutyCyclePeriod();
          void setDutyCyclePeriod(UInt dutyCyclePeriod);
          
          Real getMaxBoost();
          void setMaxBoost(Real maxBoost);
          
          UInt getIterationNum();
          void setIterationNum(UInt iterationNum);
          
          UInt getIterationLearnNum();
          void setIterationLearnNum(UInt iterationLearnNum);
          
          UInt getSpVerbosity();
          void setSpVerbosity(UInt spVerbosity);
          
          UInt getUpdatePeriod();
          void setUpdatePeriod(UInt updatePeriod);
          
          Real getSynPermTrimThreshold();
          void setSynPermTrimThreshold(Real synPermTrimThreshold);
          
          Real getSynPermActiveInc();
          void setSynPermActiveInc(Real synPermActiveInc);

          Real getSynPermInactiveDec();
          void setSynPermInactiveDec(Real synPermInactiveDec);

          Real getSynPermBelowStimulusInc();
          void setSynPermBelowStimulusInc(Real synPermBelowStimulusInc);

          Real getSynPermConnected();
          void setSynPermConnected(Real setSynPermConnected);

          Real getMinPctOverlapDutyCycles();
          void setMinPctOverlapDutyCycles(Real minPctOverlapDutyCycles);

          Real getMinPctActiveDutyCycles();
          void setMinPctActiveDutyCycles(Real minPctActiveDutyCycles);

          void getBoostFactors(Real boostFactors[]);
          void setBoostFactors(Real boostFactors[]);

          void getOverlapDutyCycles(Real overlapDutyCycles[]);
          void setOverlapDutyCycles(Real overlapDutyCycles[]);

          void getActiveDutyCycles(Real activeDutyCycles[]);
          void setActiveDutyCycles(Real activeDutyCycles[]);

          void getMinOverlapDutyCycles(Real minOverlapDutyCycles[]);
          void setMinOverlapDutyCycles(Real minOverlapDutyCycles[]);

          void getMinActiveDutyCycles(Real minActiveDutyCycles[]);
          void setMinActiveDutyCycles(Real minActiveDutyCycles[]);

          void getPotential(UInt column, UInt potential[]);
          void setPotential(UInt column, UInt potential[]);
          
          void getPermanence(UInt column, Real permanence[]);
          void setPermanence(UInt column, Real permanence[]);

          void getConnectedSynapses(UInt column, UInt connectedSynapses[]);

          void getConnectedCounts(UInt connectedCounts[]);


          // Implementation methods. all methods below this line are
          // NOT part of the public API

          void stripNeverLearned_(UInt activeArray[]);


          void toDense_(vector<UInt>& sparse, 
                       UInt dense[],
                       UInt n);

          void boostOverlaps_(vector<UInt>& overlaps, 
                              vector<Real>& boostedOverlaps);
          void range_(Int start, Int end, UInt ubound, bool wrapAround,
                           vector<UInt>& rangeVector);

          vector<UInt> mapPotential1D_(UInt column, bool wrapAround);
          Real initPermConnected_();
          Real initPermNonConnected_();
          vector<Real> initPermanence_(vector<UInt>& potential, 
                                       Real connectedPct);
          void clip_(vector<Real>& perm, bool trim);
          void updatePermanencesForColumn_(vector<Real>& perm, UInt column,
                                           bool raisePerm=true);
          UInt countConnected_(vector<Real>& perm);
          UInt raisePermanencesToThreshold_(vector<Real>& perm, 
                                            vector<UInt>& potential);
                        
          void calculateOverlap_(UInt inputVector[],
                                 vector<UInt>& overlap);
          void calculateOverlapPct_(vector<UInt>& overlaps,
                                    vector<Real>& overlapPct);


          bool isWinner_(Real score, vector<pair<UInt, Real> >& winners,
                               UInt numWinners);

          void addToWinners_(UInt index, Real score, 
                                    vector<pair<UInt, Real> >& winners);

          void inhibitColumns_(vector<Real>& overlaps, 
                               vector<UInt>& activeColumns);
          void inhibitColumnsGlobal_(vector<Real>& overlaps, Real density,
                                     vector<UInt>& activeColumns);
          void inhibitColumnsLocal_(vector<Real>& overlaps, Real density,
                                     vector<UInt>& activeColumns);

          void getNeighbors1D_(UInt column, vector<UInt>& dimensions, 
                               UInt radius, bool wrapAround,
                               vector<UInt>& neighbors);
          void getNeighbors2D_(UInt column, vector<UInt>& dimensions, 
                               UInt radius, bool wrapAround,
                               vector<UInt>& neighbors);
          void cartesianProduct_(vector<vector<UInt> >& vecs, 
                                      vector<vector<UInt> >& product);

          void getNeighborsND_(UInt column, vector<UInt>& dimensions, 
                               UInt radius, bool wrapAround,
                               vector<UInt>& neighbors);  

          void adaptSynapses_(UInt inputVector[], 
                              vector<UInt>& activeColumns);
          void bumpUpWeakColumns_();     

          void updateInhibitionRadius_();
          Real avgColumnsPerInput_();
          Real avgConnectedSpanForColumn1D_(UInt column);
          Real avgConnectedSpanForColumn2D_(UInt column);
          Real avgConnectedSpanForColumnND_(UInt column);
          void updateMinDutyCycles_();
          void updateMinDutyCyclesGlobal_();
          void updateMinDutyCyclesLocal_();
          static  void updateDutyCyclesHelper_(vector<Real>& dutyCycles, 
                                               vector<UInt>& newValues, 
                                               UInt period);
          void updateDutyCycles_(vector<UInt>& overlaps, 
                                 UInt activeArray[]);
          void updateBoostFactors_();
          void updateBookeepingVars_(bool learn);

          bool isUpdateRound_();

          
          virtual void initialize(vector<UInt> inputDimensions,
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
            Real minPctOverlapDutyCycles=0.001,
            Real minPctActiveDutyCycles=0.001,
            UInt dutyCyclePeriod=1000,
            Real maxBoost=10.0,
            Int seed=1,
            UInt spVerbosity=0);

          void seed_(UInt64 seed);

        protected:
          UInt numInputs_;
          UInt numColumns_;
          vector<UInt> columnDimensions_;
          vector<UInt> inputDimensions_;
          UInt potentialRadius_;
          Real potentialPct_;
          Real initConnectedPct_;
          bool globalInhibition_;
          Int numActiveColumnsPerInhArea_;
          Real localAreaDensity_;
          UInt stimulusThreshold_;
          UInt inhibitionRadius_;
          UInt dutyCyclePeriod_;
          Real maxBoost_;
          UInt iterationNum_;
          UInt iterationLearnNum_;
          UInt spVerbosity_;
          UInt updatePeriod_;

          Real synPermMin_;
          Real synPermMax_;
          Real synPermTrimThreshold_;
          Real synPermInactiveDec_;
          Real synPermActiveInc_;
          Real synPermBelowStimulusInc_;
          Real synPermConnected_;

          vector<Real> boostFactors_;
          vector<Real> overlapDutyCycles_;
          vector<Real> activeDutyCycles_;
          vector<Real> minOverlapDutyCycles_;
          vector<Real> minActiveDutyCycles_;

          Real minPctOverlapDutyCycles_;
          Real minPctActiveDutyCycles_;

          SparseMatrix<UInt,Real,Int,Real64> permanences_;
          SparseBinaryMatrix<UInt,UInt> potentialPools_;
          SparseBinaryMatrix<UInt, UInt> connectedSynapses_;
          vector<UInt> connectedCounts_;

          vector<UInt> overlaps;
          vector<UInt> activeColumns;


          vector<UInt> overlaps_;
          vector<Real> overlapsPct_;
          vector<Real> boostedOverlaps_;
          vector<UInt> activeColumns_;

        private:
          UInt version_;
          Random rng_;

      };
    } // end namespace spatial_pooler
  } // end namespace algorithms
} // end namespace nta
#endif // NTA_spatial_pooler_HPP
