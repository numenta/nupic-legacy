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
#include <cstring>
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
          /////////////////////////////////////////////////////////////////////////
          /// Initialize the Spatial Pooler
          ///
          /////////////////////////////////////////////////////////////////////////
          void initialize();
          std::string version() const {
            return std::string("SpatialPoolerV1");
          }
      };
    } // end namespace spatial_pooler
  } // end namespace algorithms
} // end namespace nta
#endif // NTA_spatial_pooler_HPP
