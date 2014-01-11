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

#ifndef NTA_OUTSYNAPSE_HPP
#define NTA_OUTSYNAPSE_HPP

#include <nta/types/types.hpp>
#include <nta/utils/Log.hpp> // NTA_ASSERT

using namespace nta;

namespace nta {
  namespace algorithms {
    namespace Cells4 {


      class Cells4;
      //--------------------------------------------------------------------------------
      //--------------------------------------------------------------------------------
      /**
       * The type of synapse we use to propagate activation forward. It contains
       * indices for the *destination* cell, and the *destination* segment on that cell.
       * The cell index is between 0 and nCols * nCellsPerCol.
       */
      class OutSynapse
      {
      public:

      private:
        UInt _dstCellIdx;
        UInt _dstSegIdx;  // index in _segActivity

      public:
        OutSynapse(UInt dstCellIdx =(UInt) -1,
                          UInt dstSegIdx =(UInt) -1
                   //Cells4* cells =NULL
                   )
          : _dstCellIdx(dstCellIdx),
            _dstSegIdx(dstSegIdx)
        {
          // TODO: FIX this
          //NTA_ASSERT(invariants(cells));
        }

        OutSynapse(const OutSynapse& o)
          : _dstCellIdx(o._dstCellIdx),
            _dstSegIdx(o._dstSegIdx)
        {}

        OutSynapse& operator=(const OutSynapse& o)
        {
          _dstCellIdx = o._dstCellIdx;
          _dstSegIdx = o._dstSegIdx;
          return *this;
        }

        UInt dstCellIdx() const { return _dstCellIdx; }
        UInt dstSegIdx() const { return _dstSegIdx; }

        /**
         * Checks whether this outgoing synapses is going to given destination
         * or not.
         */
        bool goesTo(UInt dstCellIdx, UInt dstSegIdx) const
        {
          return _dstCellIdx == dstCellIdx && _dstSegIdx == dstSegIdx;
        }

        /**
         * Need for is_in/not_in tests.
         */
        bool equals(const OutSynapse& o) const
        {
          return _dstCellIdx == o._dstCellIdx && _dstSegIdx == o._dstSegIdx;
        }

        /**
         * Checks that the destination cell index and destination segment index
         * are in range.
         */
        bool invariants(Cells4* cells =NULL) const;
      };

      //--------------------------------------------------------------------------------
      bool operator==(const OutSynapse& a, const OutSynapse& b);


      // End namespace
    }
  }
}

#endif // NTA_OUTSYNAPSE_HPP

