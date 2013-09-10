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
#include <map>
#include <iostream>

using namespace std;

namespace nta {
  namespace algorithms {
    namespace spatial_pooler {

      typedef struct {
        UInt index;
        Real score;
      } scoreCard;


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

          UInt version() const {
            return version_;
          };

          Real real_rand();

          vector<UInt> compute(vector<UInt> inputVector, bool learn);

          UInt getPotentialRadius();
          void setPotentialRadius(UInt potentialRadius);

          Real getPotentialPct();
          void setPotentialPct(Real potentialPct);

          bool getGlobalInhibition();
          void setGlobalInhibition(bool globalInhibition);
          
          UInt getNumActiveColumnsPerInhArea();
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

          void range_(Int start, Int end, UInt ubound, bool wrapAround,
                           vector<UInt>& rangeVector);

          vector<UInt> mapPotential1D_(UInt column, bool wrapAround);
          Real initPermConnected_();
          Real initPermUnconnected_();
          vector<Real> initPermanence_(vector<UInt>& potential, 
                                       Real connectedPct);
          void clip_(vector<Real>& perm, bool trim);
          void updatePermanencesForColumn_(vector<Real>& perm, UInt column,
                                           bool raisePerm=false);
          UInt countConnected_(vector<Real>& perm);
          UInt raisePermanencesToThreshold_(vector<Real>& perm, 
                                            vector<UInt>& potential);
         
               
          void calculateOverlap_(vector<UInt>& inputVector,
                                 vector<UInt>& overlap);
          void calculateOverlapPct_(vector<UInt>& overlaps,
                                    vector<Real>& overlapPct);


          bool is_winner_(Real score, vector<scoreCard>& winners,
                               UInt numWinners);

          void add_to_winners_(UInt index, Real score, 
                                    vector<scoreCard>& winners);

          void inhibitColumns_(vector<UInt> overlaps, 
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

          void adaptSynapses_(vector<UInt>& inputVector, 
                              vector<UInt>& activeColumns);
          void bumpUpWeakColumns_();     

          void updateInhibitionRadius_();
          void avgColumnsPerInput_();
          void avgConnectedSpanForColumn1D_(UInt column);
          void avgConnectedSpanForColumn2D_(UInt column);
          void avgConnectedSpanForColumnND_(UInt column);
          void updateMinDutyCycles_();
          void updateMinDutyCyclesGlobal_();
          void updateMinDutyCyclesLocal_();
          static  void updateDutyCyclesHelper_(vector<Real>& dutyCycles, 
                                               vector<UInt> newValues, 
                                               UInt period);
          void updateDutyCycles_(vector<UInt>& overlaps, 
                                 vector<UInt>& activeColumns);
          void updateBoostFactors_();
          void updateBookeepingVars_(bool learn);
          bool isUpdateRound_();

          /**
           * Initialize.
           *
           * @param inputDimensions A vector representing the dimensions of the 
                                    input vector. Format is [height, width, 
                                    depth, ...], where each value represents the 
                                    size of the dimension. For a topology of one 
                                    dimesion with 100 inputs use [100]. For a 
                                    two dimensional topology of 10x5 use [10,5].
           * @param columnDimensions A vector representing the dimensions of the 
                                     columns in the region. Format is [height, 
                                     width, depth, ...], where each value 
                                      represents the size of the dimension. For 
                                      a topology of one dimesion with 2000 
                                      columns use [2000]. For a three 
                                      dimensional topology of 32x64x16 use [32, 
                                      64, 16]. 
           * @param potentialRadius Deteremines the extent of the input that 
                                    each column can potentially be connected to. 
                                    This can be thought of as the input bits 
                                    that are visible to each column, or a 
                                    'receptiveField' of the field of vision. 
                                    A large enough value will result in the 
                                    'global coverage', meaning that each column 
                                    can potentially be connected to every input 
                                    bit. This parameter defines a square (or 
                                    hyper square) area: a column will have a max 
                                    square potential pool with sides of length 2 
                                    * potentialRadius + 1. 
           * @param potentialPct The percent of the inputs, within a column's
                                  potential radius, that a column can be 
                                  connected to. If set to 1, the column will be 
                                  connected to every input within its potential 
                                  radius. This parameter is used to give each 
                                  column a unique potential pool when a large 
                                  potentialRadius causes overlap between the 
                                  columns. At initialization time we choose 
                                  ((2*potentialRadius + 1)^(# inputDimensions) 
                                  * potentialPct) input bits to comprise the 
                                  column's potential pool.
           * @param globalInhibition If true, then during inhibition phase the 
                                    winning columns are selected as the most 
                                    active columns from the region as a whole. 
                                    Otherwise, the winning columns are selected 
                                    with resepct to their local neighborhoods.
           * @param localAreaDensity The desired density of active columns 
                                     within a local inhibition area (the size of 
                                     which is set by the internally calculated 
                                     inhibitionRadius, which is in turn 
                                     determined from the average size of the 
                                     connected potential pools of all columns). 
                                     The inhibition logic will insure that at 
                                     most N columns remain ON within a local 
                                     inhibition area, where N = 
                                     localAreaDensity * (total number of
                                     columns in  inhibition area).
           * @param numActiveColumnsPerInhArea An alternate way to control the 
                                    density of the active columns. If 
                                    numActivePerInhArea is specified then
                                    localAreaDensity must be -1, and vice versa. 
                                    When using numActivePerInhArea, the 
                                    inhibition logic will insure that at most 
                                    'numActivePerInhArea' columns remain ON 
                                    within a local inhibition area (the size of
                                    which is set by the internally calculated
                                    inhibitionRadius, which is in turn 
                                    determined from the average size of the 
                                    connected receptive fields of all columns). 
                                    When using this method, as columns 
                                    learn and grow their effective receptive 
                                    fields, the inhibitionRadius will grow, and 
                                    hence the net density of the active columns 
                                    will *decrease*. This is in contrast to the 
                                    localAreaDensity method, which keeps the 
                                    density of active columns the same 
                                    regardless of the size of their receptive 
                                    fields.
           * @param stimulusThreshold This is a number specifying the minimum 
                                    number of synapses that must be on in order 
                                    for a columns to turn ON. The purpose of 
                                    this is to prevent noise input from 
                                    activating columns. Specified as a percent 
                                    of a fully grown synapse.
           * @param synPermInactiveDec The amount by which an inactive synapse 
                                    is decremented in each round. Specified as 
                                    a percent of a fully grown synapse.
           * @param synPermActiveInc The amount by which an active synapse is 
                                    incremented in each round. Specified as a 
                                    percent of a fully grown synapse.
           * @param synPermConnected The default connected threshold. Any 
                                    synapse whose permanence value is above the 
                                    connected threshold is a "connected 
                                    synapse", meaning it can contribute to the 
                                    cell's firing.
           * @param minPctOverlapDutyCycle A number between 0 and 1.0, used to 
                                    set a floor on how often a column should 
                                    have at least stimulusThreshold active 
                                    inputs. Periodically, each column looks at 
                                    the overlap duty cycle of all other column 
                                    within its inhibition radius and sets its 
                                    own internal minimal acceptable duty cycle 
                                    to: minPctOverlapDutyCycle * max(other 
                                    columns'  duty cycles). On each iteration, 
                                    any column whose overlap duty cycle falls 
                                    below this computed value will  get all of 
                                    its permanence values boosted. Raising all 
                                    permanences in response to a sub-par duty 
                                    cycle before  inhibition allows a column to 
                                    search for new inputs when either its
                                    previously learned inputs are no longer ever 
                                    active, or when the vast majority of them 
                                    have been "hijacked" by other columns.
           * @param minPctActiveDutyCycle A number between 0 and 1.0, used to 
                                    set a floor on how often a column should be 
                                    active. Periodically, each column looks at 
                                    the activity duty cycle of all other columns 
                                    within its inhibition radius and sets its 
                                    own internal minimal acceptable duty cycle 
                                    to: minPctActiveDutyCycle * max(other 
                                    columns' duty cycles). On each iteration, 
                                    any column whose duty cycle after inhibition 
                                    falls below this computed value will get its 
                                    internal boost factor increased.
           * @param dutyCyclePeriod The period used to calculate duty cycles. 
                                    Higher values make it take longer to respond 
                                    to changes. Shorter values make it more 
                                    unstable and likely to oscillate.
           * @param maxBoost The maximum overlap boost factor. Each column's
                            overlap gets multiplied by a boost factor before it 
                            gets considered for inhibition. The actual boost 
                            factor for a column is number between 1.0 and 
                            maxBoost. A boost factor of 1.0 is used if the duty 
                            cycle is >= minOverlapDutyCycle, maxBoost is used 
                            if the duty cycle is 0, and any duty cycle in 
                            between is linearly extrapolated from these 2 
                            endpoints.
           * @param seed    Seed for our own pseudo-random number generator.
           * @param spVerbosity spVerbosity level: 0, 1, 2, or 3
           */
          void initialize(vector<UInt> inputDimensions,
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

          void seed_(Int seed);


        private:
          UInt numInputs_;
          UInt numColumns_;
          vector<UInt> columnDimensions_;
          vector<UInt> inputDimensions_;
          UInt potentialRadius_;
          Real potentialPct_;
          Real initConnectedPct_;
          bool globalInhibition_;
          UInt numActiveColumnsPerInhArea_;
          Real localAreaDensity_;
          UInt stimulusThreshold_;
          UInt inhibitionRadius_;
          UInt dutyCyclePeriod_;
          Real maxBoost_;
          UInt iterationNum_;
          UInt iterationLearnNum_;
          UInt spVerbosity_;
          UInt version_;
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

          Random rgen_;

      };
    } // end namespace spatial_pooler
  } // end namespace algorithms
} // end namespace nta
#endif // NTA_spatial_pooler_HPP
