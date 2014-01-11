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

#ifndef NTA_flat_spatial_pooler_HPP
#define NTA_flat_spatial_pooler_HPP

#include <cstring>
#include <iostream>
#include <nta/algorithms/spatial_pooler.hpp>
#include <nta/types/types.hpp>
#include <string>
#include <vector>

using namespace std;

namespace nta {
  namespace algorithms {
    namespace spatial_pooler {


      /////////////////////////////////////////////////////////////////////////
      /// CLA flat spatial pooler implementation in C++.
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
     class FlatSpatialPooler : public SpatialPooler {
        public:
          FlatSpatialPooler() {}

          virtual ~FlatSpatialPooler() {}

          virtual void save(ostream& outStream);
          virtual void load(istream& inStream);
          
          virtual UInt version() const {
            return version_;
          };


          Real getMinDistance();
          void setMinDistance(Real minDistance);
          bool getRandomSP();
          void setRandomSP(bool randomSP);


          virtual void compute(UInt inputVector[], bool learn,
                               UInt activeVector[]);

          void addBonus_(vector<Real>& vec, Real bonus,
                         vector<UInt>& indices, bool replace);

          void selectVirginColumns_(vector<UInt>& virgin);

          void selectHighTierColumns_(vector<Real>& overlapsPct,
                                      vector<UInt> &highTier);


          virtual void initializeFlat(
            UInt numInputs,
            UInt numColumns,
            Real potentialPct = 0.5,
            Real localAreaDensity=0,
            UInt numActiveColumnsPerInhArea=10,
            UInt stimulusThreshold=0,
            Real synPermInactiveDec=0.01,
            Real synPermActiveInc=0.1,
            Real synPermConnected=0.1,
            Real minPctOverlapDutyCycles=0.001,
            Real minPctActiveDutyCycles=0.001,
            UInt dutyCyclePeriod=1000,
            Real maxBoost=10.0,
            Real minDistance=0.0,
            bool randomSP=false,
            Int seed=-1,
            UInt spVerbosity=0);

          //-------------------------------------------------------------------
          // Debugging helpers
          //-------------------------------------------------------------------

          // Print the creation parameters specific to this class
          void printFlatParameters();


        protected:
          Real minDistance_;
          bool randomSP_;

          vector<UInt> highTier_;
          vector<UInt> virgin_;

      };
    } // end namespace spatial_pooler
  } // end namespace algorithms
} // end namespace nta
#endif // NTA_flat_spatial_pooler_HPP
