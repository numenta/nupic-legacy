/*
 * ---------------------------------------------------------------------
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
 * ---------------------------------------------------------------------
 */

#ifndef NTA_INSYNAPSE_HPP
#define NTA_INSYNAPSE_HPP

#include <nta/types/types.hpp>

#include <ostream>
#include <fstream>

using namespace nta;

//--------------------------------------------------------------------------------

namespace nta {
  namespace algorithms {
    namespace Cells4 {


      //--------------------------------------------------------------------------------
      //--------------------------------------------------------------------------------
      /**
       * The type of synapse contained in a Segment. It has the source cell index
       * of the synapse, and a permanence value. The source cell index is between
       * 0 and nCols * nCellsPerCol.
       */
      class InSynapse
      {
      private:
        UInt _srcCellIdx;
	typedef unsigned char synapse_t;
        synapse_t _permanence; // resolves to float
	static const synapse_t GRAIN = 255;

      public:
        inline InSynapse()
          : _srcCellIdx((UInt) -1),
            _permanence(0)
        {}

        inline InSynapse(UInt srcCellIdx, NTA_Real32 permanence)
          : _srcCellIdx(srcCellIdx),
            _permanence(static_cast<synapse_t>(permanence*GRAIN))
        {}

        inline InSynapse(const InSynapse& o)
          : _srcCellIdx(o._srcCellIdx),
            _permanence(o._permanence)
        {}

        inline InSynapse& operator=(const InSynapse& o)
        {
          _srcCellIdx = o._srcCellIdx;
          _permanence = o._permanence;
          return *this;
        }

        inline UInt srcCellIdx() const { return _srcCellIdx; } const
        inline NTA_Real32 permanence() { return static_cast<NTA_Real32>(_permanence/GRAIN); }
	inline NTA_Real32 permanence() const { return static_cast<NTA_Real32>(_permanence/GRAIN); }
	inline void permanence(NTA_Real32 val) { _permanence = static_cast<synapse_t>(val*GRAIN); } 
        inline void print(std::ostream& outStream) const;
      };

      //--------------------------------------------------------------------------------
#ifndef SWIG
      std::ostream& operator<<(std::ostream& outStream, const InSynapse& s);
#endif

      // end namespace
    }
  }
}

#endif // NTA_INSYNAPSE_HPP
