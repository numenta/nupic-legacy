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
 * Definitions for the Spatial Pooler
 */

#ifndef NTA_spatial_pooler_HPP
#define NTA_spatial_pooler_HPP

#include <cstring>
#include <iostream>
#include <nta/math/SparseBinaryMatrix.hpp>
#include <nta/math/SparseMatrix.hpp>
#include <nta/types/types.hpp>
#include <string>
#include <vector>

using namespace std;

namespace nta {
  namespace algorithms {
    namespace spatial_pooler {

      /**
       * CLA spatial pooler implementation in C++.
       *
       * ### Description
       * The Spatial Pooler is responsible for creating a sparse distributed
       * representation of the input. Given an input it computes a set of sparse
       * active columns and simultaneously updates its permanences, duty cycles,
       * etc.
       * 
       * The primary public interfaces to this function are the "initialize"
       * and "compute" methods.
       *
       * Example usage:
       * 
       *     SpatialPooler sp;
       *     sp.initialize(inputDimensions, columnDimensions, <parameters>);
       *     while (true) {
       *        <get input vector>
       *        sp.compute(inputVector, learn, activeColumns)
       *        <do something with output>
       *     }
       *     
       */
      class SpatialPooler {
        public:
          SpatialPooler();

          virtual ~SpatialPooler() {}

          /**
          Initialize the spatial pooler using the given parameters.
          
          @param inputDimensions A list of integers representing the 
                dimensions of the input vector. Format is [height, width,
                depth, ...], where each value represents the size of the
                dimension. For a topology of one dimesion with 100 inputs
                use [100]. For a two dimensional topology of 10x5
                use [10,5].
         
          @param columnDimensions A list of integers representing the
                dimensions of the columns in the region. Format is [height,
                width, depth, ...], where each value represents the size of
                the dimension. For a topology of one dimesion with 2000
                columns use 2000, or [2000]. For a three dimensional
                topology of 32x64x16 use [32, 64, 16]. 
             
          @param potentialRadius This parameter deteremines the extent of the 
                input that each column can potentially be connected to. This
                can be thought of as the input bits that are visible to each
                column, or a 'receptive field' of the field of vision. A large
                enough value will result in global coverage, meaning
                that each column can potentially be connected to every input
                bit. This parameter defines a square (or hyper square) area: a
                column will have a max square potential pool with sides of
                length (2 * potentialRadius + 1). 

          @param potentialPct The percent of the inputs, within a column's
                potential radius, that a column can be connected to. If set to
                1, the column will be connected to every input within its
                potential radius. This parameter is used to give each column a
                unique potential pool when a large potentialRadius causes
                overlap between the columns. At initialization time we choose
                ((2*potentialRadius + 1)^(# inputDimensions) * potentialPct)
                input bits to comprise the column's potential pool.

          @param globalInhibition If true, then during inhibition phase the 
                winning columns are selected as the most active columns from the
                region as a whole. Otherwise, the winning columns are selected
                with resepct to their local neighborhoods. Global inhibition
                boosts performance significantly but there is no topology at the
                output.
                
          @param localAreaDensity The desired density of active columns within 
                a local inhibition area (the size of which is set by the
                internally calculated inhibitionRadius, which is in turn
                determined from the average size of the connected potential
                pools of all columns). The inhibition logic will insure that at
                most N columns remain ON within a local inhibition area, where
                N = localAreaDensity * (total number of columns in inhibition
                area). If localAreaDensity is set to a negative value output
                sparsity will be determined by the numActivePerInhArea. 

          @param numActivePerInhArea An alternate way to control the sparsity of 
                active columns. If numActivePerInhArea is specified then
                localAreaDensity must less than 0, and vice versa. When 
                numActivePerInhArea > 0, the inhibition logic will insure that
                at most 'numActivePerInhArea' columns remain ON within a local
                inhibition area (the size of which is set by the internally
                calculated inhibitionRadius). When using this method, as columns
                learn and grow their effective receptive fields, the
                inhibitionRadius will grow, and hence the net density of the
                active columns will *decrease*. This is in contrast to the
                localAreaDensity method, which keeps the density of active
                columns the same regardless of the size of their receptive
                fields.
                
          @param stimulusThreshold This is a number specifying the minimum 
                number of synapses that must be active in order for a column to
                turn ON. The purpose of this is to prevent noisy input from
                activating columns. 
                
          @param synPermInactiveDec The amount by which the permanence of an 
                inactive synapse is decremented in each learning step. 

          @param synPermActiveInc The amount by which the permanence of an 
                active synapse is incremented in each round. 

          @param synPermConnected The default connected threshold. Any synapse 
                whose permanence value is above the connected threshold is
                a "connected synapse", meaning it can contribute to
                the cell's firing.
                
          @param minPctOvlerapDutyCycle A number between 0 and 1.0, used to set 
                a floor on how often a column should have at least
                stimulusThreshold active inputs. Periodically, each column looks
                at the overlap duty cycle of all other column within its
                inhibition radius and sets its own internal minimal acceptable
                duty cycle to: minPctDutyCycleBeforeInh * max(other columns'
                duty cycles). On each iteration, any column whose overlap duty
                cycle falls below this computed value will get all of its
                permanence values boosted up by synPermActiveInc. Raising all
                permanences in response to a sub-par duty cycle before
                inhibition allows a cell to search for new inputs when either
                its previously learned inputs are no longer ever active, or when
                the vast majority of them have been "hijacked" by other columns.

          @param minPctActiveDutyCycle A number between 0 and 1.0, used to set 
                a floor on how often a column should be activate. Periodically,
                each column looks at the activity duty cycle of all other
                columns within its inhibition radius and sets its own internal
                minimal acceptable duty cycle to:
                
                    minPctDutyCycleAfterInh * max(other columns' duty cycles).

                On each iteration, any column whose duty cycle after inhibition
                falls below this computed value will get its internal boost
                factor increased.

          @param dutyCyclePeriod The period used to calculate duty cycles. 
                Higher values make it take longer to respond to changes in
                boost. Shorter values make it potentially more unstable and
                likely to oscillate.
                
          @param maxBoost The maximum overlap boost factor. Each column's
                overlap gets multiplied by a boost factor before it gets
                considered for inhibition. The actual boost factor for a column
                is a number between 1.0 and maxBoost. A boost factor of 1.0 is
                used if the duty cycle is >= minOverlapDutyCycle, maxBoost is
                used if the duty cycle is 0, and any duty cycle in between is
                linearly extrapolated from these 2 endpoints.

          @param seed Seed for our random number generator. If seed is < 0
                a randomly generated seed is used. The behavior of the spatial
                pooler is deterministic once the seed is set.

          @param spVerbosity spVerbosity level: 0, 1, 2, or 3

           */
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

          /**
          This is the main workshorse method of the SpatialPooler class. This
          method takes an input vector and computes the set of output active
          columns. If 'learn' is set to True, this method also performs
          learning.
    
          @param inputVector An array of integer 0's and 1's that comprises
                the input to the spatial pooler. The length of the 
                array must match the total number of input bits implied by
                the constructor (also returned by the method getNumInputs). In
                cases where the input is multi-dimensional, inputVector is a
                flattened array of inputs.
                
          @param learn A boolean value indicating whether learning should be 
                performed. Learning entails updating the permanence values of
                the synapses, duty cycles, etc. Learning is typically on but
                setting learning to 'off' is useful for analyzing the current
                state of the SP. For example, you might want to feed in various
                inputs and examine the resulting SDR's. Note that if learning
                is off, boosting is turned off and columns that have never won
                will be removed from activeVector.  TODO: we may want to keep
                boosting on even when learning is off.
                
          @param activeArray An array representing the winning columns after
                inhinition. The size of the array is equal to the number of
                columns (also returned by the method getNumColumns). This array
                will be populated with 1's at the indices of the active columns,
                and 0's everywhere else. In the case where the output is
                multi-dimensional, activeVector represents a flattened array
                of outputs.
           */
          virtual void compute(UInt inputVector[], bool learn,
                               UInt activeVector[]);

          /**
           * Get the version number of this spatial pooler
           * @returns Integer version number
           */
          virtual UInt version() const {
            return version_;
          };

          /**
          Save (serialize) the current state of the spatial pooler to the
          specified output stream.
    
          @param outStream A valid ostream.
           */
          virtual void save(ostream& outStream);

          /**
          Load (deserialize) and initialize the spatial pooler from the
          specified input stream.
    
          @param inStream A valid istream.
           */
          virtual void load(istream& inStream);

          /**
          Returns the number of bytes that a save operation would result in.
          Note: this method is currently somewhat inefficient as it just does
          a full save into an ostream and counts the resulting size.
    
          @returns Integer number of bytes
           */
          virtual UInt persistentSize();

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

          /**
          Print the main SP creation parameters to stdout. 
           */
          void printParameters();


          ///////////////////////////////////////////////////////////
          //
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


          void seed_(UInt64 seed);

          //-------------------------------------------------------------------
          // Debugging helpers
          //-------------------------------------------------------------------

          // Print the given UInt array in a nice format
          void printState(vector<UInt> &state);

          // Print the given Real array in a nice format
          void printState(vector<Real> &state);

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

          vector<UInt> overlaps_;
          vector<Real> overlapsPct_;
          vector<Real> boostedOverlaps_;
          vector<UInt> activeColumns_;
          vector<Real> tieBreaker_;

          UInt version_;
          Random rng_;

      };
    } // end namespace spatial_pooler
  } // end namespace algorithms
} // end namespace nta
#endif // NTA_spatial_pooler_HPP
