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
#ifndef NTA_flat_spatial_pooler_HPP
#define NTA_flat_spatial_pooler_HPP

#include <nta/types/types.hpp>
// #include <nta/math/SparseMatrix.hpp>
// #include <nta/math/SparseBinaryMatrix.hpp>
#include <cstring>
#include <string>
#include <vector>
#include <map>
#include <nta/algorithms/spatial_pooler.hpp>
#include <iostream>

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

          ~FlatSpatialPooler() {}

          void somefunc() {}

          virtual UInt version() const {
            return version_;
          };


          Real getMinDistance();
          void setMinDistance(Real minDistance);
          bool getRandomSP();
          void setRandomSP(bool randomSP);


          void compute(UInt inputVector[], bool learn,
                       UInt activeVector[]);

          void selectVirginColumns_(vector<UInt>& virgin);

          void selectHighTierColumns_(vector<Real>& overlapsPct, vector<UInt> &highTier);


          virtual void initializeFlat(
            UInt numInputs, 
            UInt numColumns,
            Real localAreaDensity=0.1, 
            UInt numActiveColumnsPerInhArea=-1,
            UInt stimulusThreshold=0, 
            Real synPermInactiveDec=0.1, 
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


        protected:
          Real minDistance_;
          bool randomSP_;

        private:
          UInt version_;

      };
    } // end namespace spatial_pooler
  } // end namespace algorithms
} // end namespace nta
#endif // NTA_flat_spatial_pooler_HPP
