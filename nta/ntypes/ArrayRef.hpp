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

// ---
//
// Definitions for the ArrayRef class
//  
// It is a sub-class of ArrayBase that doesn't own its buffer
//
// ---

#ifndef NTA_ARRAY_REF_HPP
#define NTA_ARRAY_REF_HPP

#include <nta/ntypes/ArrayBase.hpp>
#include <nta/utils/Log.hpp>

namespace nta
{
  class ArrayRef : public ArrayBase
  {
  public:
    ArrayRef(NTA_BasicType type, void * buffer, size_t count) : ArrayBase(type)
    {
      setBuffer(buffer, count);
    }
    
    explicit ArrayRef(NTA_BasicType type) : ArrayBase(type)
    {
    }

    ArrayRef(const ArrayRef & other) : ArrayBase(other)
    {
    }
  
    void invariant()
    {
      if (own_)
        NTA_THROW << "ArrayRef mmust not own its buffer";
    }
  private:
    // Hide base class method (invalid for ArrayRef)
    void allocateBuffer(void * buffer, size_t count);
  };
}

#endif

