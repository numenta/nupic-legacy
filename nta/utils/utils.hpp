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

/** @file 
 * Utility functions
 */

#ifndef NTA_UTILS_HPP
#define NTA_UTILS_HPP

#include <nta/types/types.hpp>

namespace utils 
{
  inline bool isSystemLittleEndian()
  {
    static const char test[2] = { 1, 0 };
    return (*(short *) test) == 1;
  }

  template<typename T>
  inline void swapBytesInPlace(T *pxIn, nta::Size n)
  {
    union SwapType { T x; unsigned char b[sizeof(T)]; };
    SwapType *px = reinterpret_cast<SwapType *>(pxIn);
    SwapType *pxend = px + n;
    const int stop = sizeof(T) / 2;
    for(; px!=pxend; ++px)
    {
      for(int j=0; j<stop; ++j) std::swap(px->b[j], px->b[sizeof(T)-j-1]);
    }
  }
  
  template<typename T>
  inline void swapBytes(T *pxOut, nta::Size n, const T *pxIn)
  {
    NTA_ASSERT(pxOut != pxIn) << "Use swapBytesInPlace() instead.";
    NTA_ASSERT(!(((pxOut > pxIn) && (pxOut < (pxIn+n))) ||
      ((pxIn > pxOut) && (pxIn < (pxOut+n))))) << "Overlapping ranges not supported.";
    
    union SwapType { T x; unsigned char b[sizeof(T)]; };
    const SwapType *px0 = reinterpret_cast<SwapType *>(pxIn);
    const SwapType *pxend = px0 + n;
    SwapType *px1 = reinterpret_cast<SwapType *>(pxOut);
    for(; px0!=pxend; ++px0, ++px1) {
      for(int j=0; j<sizeof(T); ++j) px1->b[j] = px0->b[sizeof(T)-j-1];
    }
  }
  
} // end of namespace nta

#endif

