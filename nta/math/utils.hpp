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
 * Definitions for various utility functions
 */

#ifndef NTA_UTILS_HPP
#define NTA_UTILS_HPP

#include <assert.h>
#include <math.h>
#include <iostream>
#include <string>
#include <sstream>
#include <iterator>
#include <limits>
#include <numeric>
#include <algorithm>
#include <vector>
#include <list>
#include <map>
#include <stdexcept>
#include <cstdlib>

#include <boost/shared_array.hpp>

#include <nta/types/types.hpp>
#include <nta/utils/Log.hpp>

namespace nta {
    
  //--------------------------------------------------------------------------------
  /**
   * Computes the amount of padding required to align two adjacent blocks of memory.
   * If the first block has 17 bytes, and the second is a "vector" of 4 elements
   * of 4 bytes each, we need to align the start of the "vector" on a 4 bytes
   * boundary. The amount of padding required after the 17 bytes of the first
   * block is: 3 bytes, and 3 = 4 - 17 % 4, that is:
   * padding = second elem size - first total size % second elem size.
   *
   * Special case: if the first block of memory ends on a boundary of the second
   * block, no padding required. Example, first block has 16 bytes and second vector of
   * 4 bytes each: 16 % 4 = 0. 
   */
  template <typename SizeType>
  inline const SizeType padding(const SizeType& s1, const SizeType& s2)
  { 
    if(s2) {
      SizeType extra = s1 % s2;
      return extra == 0 ? 0 : s2 - extra;
    }
    else return 0;
  }

/*
  the following code is known to cause -Wstrict-aliasing warning, so silence it here
*/
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wstrict-aliasing"
  inline bool IsSystemLittleEndian()
    { static const char test[2] = { 1, 0 }; return (*(short *) test) == 1; }
#pragma GCC diagnostic pop // return back to defaults

  template<typename T>
  inline void SwapBytesInPlace(T *pxIn, Size n)
  {
    union SwapType { T x; unsigned char b[sizeof(T)]; };
    SwapType *px = reinterpret_cast<SwapType *>(pxIn);
    SwapType *pxend = px + n;
    const int stop = sizeof(T) / 2;
    for(; px!=pxend; ++px) {
      for(int j=0; j<stop; ++j) std::swap(px->b[j], px->b[sizeof(T)-j-1]);
    }
  }
  
  template<typename T>
  inline void SwapBytes(T *pxOut, Size n, const T *pxIn)
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

  /**
   * Calculates sizeof() types named by string names of types in nta/types/types.
   * Throws if the requested type cannot be found.
   * 
   * Supported type names include:
   * bool,
   * char, wchar_t,
   * NTA_Char, NTA_WChar, NTA_Byte,
   * float, double,
   * NTA_Real32, NTA_Real64, NTA_Real,
   * int, size_t,
   * NTA_Int32, NTA_UInt32, NTA_Int64, NTA_UInt64, NTA_Size
   *
   * @param name (string) Name of type to calculate sizeof() for.
   * @param isNumeric (bool&) set to true on exit if type name is a number. 
   * @retval Number of bytes per element of the specified type.
   */
  extern size_t GetTypeSize(const std::string &name, bool& isNumeric);

  /**
   * Calculates sizeof() types named by string names of types in nta/types/types.
   * Throws if the requested type cannot be found.
   * 
   * Supported type names include:
   * bool,
   * char, wchar_t,
   * NTA_Char, NTA_WChar, NTA_Byte,
   * float, double,
   * NTA_Real32, NTA_Real64, NTA_Real,
   * int, size_t,
   * NTA_Int32, NTA_UInt32, NTA_Int64, NTA_UInt64, NTA_Size
   *
   * @param name (string) Name of type to calculate sizeof() for.
   * @param isNumeric (bool&) set to true on exit if type name is a number. 
   * @retval Number of bytes per element of the specified type.
   */
  extern size_t GetTypeSize(NTA_BasicType type, bool& isNumeric);
  
  /**
   * Return a string representation of an NTA_BasicType
   * 
   * @param type the NTA_BasicType enum
   * @retval name of the type as a string
   */
  extern std::string GetTypeName(NTA_BasicType type);

  /**
   * Utility routine used by PrintVariableArray to print array of a certain type 
   */
  template <typename T>
  inline void utilsPrintArray_(std::ostream& out, const void* theBeginP, 
			       const void* theEndP)
  {
    const T* beginP = (T*)theBeginP;
    const T* endP = (T*)theEndP;
    
    for ( ; beginP != endP; ++beginP) 
      out << *beginP << " ";
  }

  /**
   * Utility routine for setting an array in memory of a certain type from a stream 
   *
   * @param in        the stream with values to put into the array
   * @param theBeginP pointer to start of array in memory
   * @param theEndP   pointer to end of array in memory
   * @retval          true if successfully set all values
   *
   */
  template <typename T>
  inline void utilsSetArray_(std::istream& in, void* theBeginP, void* theEndP)
  {
    T* beginP = (T*)theBeginP;
    T* endP = (T*)theEndP;
    
    for ( ; beginP != endP && in.good(); ++beginP) 
      in >> *beginP;
    if (beginP != endP && !in.eof())
      NTA_THROW << "UtilsSetArray() - error reading stream of values";
  }

  /**
   * Streams the contents of a variable array cast as the given type.   
   *
   * This is used by the NodeProcessor when returing the value of an node's outputs in
   * response to the "nodeOPrint" supervisor command, and also when returning the value of
   * a node's output or parameters to the tools in response to a watch request. 
   *
   * The caller must pass in either a dataType, elemSize, or both. If both are specified,
   * then this routine will assert that the elemSize agrees with the given dataType. If
   * dataType is not specified, then this routine will pick a most likely dataType given
   * the elemSize. 
   *
   * @param outStream [std::ostream] the stream to print to
   * @param beginP [Byte*] pointer to the start of the variable
   * @param endP   [Byte*] pointer to first byte past the end of the variable
   * @param dataType [std::string] the data type to print as (optional)
   * @retval [std::string] the actual type the variable was printed as. This will
   *         always be dataType, unless the dataType was unrecognized.  
   *
   * @b Exceptions:
   *  @li None.
   */
  extern std::string PrintVariableArray (std::ostream& outStream, const Byte* beginP, 
          const Byte* endP, const std::string& dataType="");
          
  /**
   * Sets the contents of a variable array cast as the given type.   
   *
   * This is used by the NodeProcessor when setting the value of an node's outputs in
   * response to the "nodeOSet" supervisor command. 
   *
   * @param inStream [std::istream] the stream to fetch the values from
   * @param beginP [Byte*] pointer to the start of the variable
   * @param endP   [Byte*] pointer to first byte past the end of the variable
   * @param dataType [std::string] the data type to set as 
   *
   * @b Exceptions:
   *  @li None.
   */
   extern void SetVariableArray (std::istream& inStream,  Byte* beginP, 
           Byte* endP, const std::string& dataType);
          
  //--------------------------------------------------------------------------------
  // Defines, used as code generators, to make the code more readable
  
#define NO_DEFAULTS(X) private: X(); X(const X&); X& operator=(const X&);

  /**
   * Puts Y in current scope
   * Iterates on whole Z, which must have begin() and end()
   */
#define LOOP(X, Y, Z)                           \
  X::iterator Y;                                \
    X::iterator Y##beginXX = (Z).begin();       \
    X::iterator Y##endXX = (Z).end();           \
    for (Y = Y##beginXX; Y != Y##endXX; ++Y)
  
  /**
   * Puts Y in current scope
   * Z must have begin()
   * Iterates on partial Z, between Z.begin() and Z.begin() + L
   */
#define PARTIAL_LOOP(X, Y, Z, L)                \
  X::iterator Y;                                \
    X::iterator Y##beginXX = (Z).begin();       \
    X::iterator Y##endXX = (Z).begin() + (L);   \
    for (Y = Y##beginXX; Y != Y##endXX; ++Y)
  
  /**
   * Puts Y in current scope
   * Iterates on whole Z, with a const_iterator
   */
#define CONST_LOOP(X, Y, Z)                     \
  X::const_iterator Y;                          \
    X::const_iterator Y##beginXX = (Z).begin(); \
    X::const_iterator Y##endXX = (Z).end();     \
    for (Y = Y##beginXX; Y != Y##endXX; ++Y)
  
  /**
   * Puts Y in current scope
   * Iterates from Y to Z by steps of 1
   */
#define ITER(X, Y, Z)                          \
  Size X##minXX = (Y), X##maxXX = (Z);         \
    for (Size X = X##minXX; X < X##maxXX; ++X)
  
  /**
   * Puts Y1 and Y2 in current scope
   * Iterates X1 from Y1 to Z1 and X2 from Y2 to Z2
   * X2 is the inner index
   */
#define ITER2(X1, X2, Y1, Y2, Z1, Z2)                         \
  UInt X1##minXX = (Y1),	X1##maxXX = (Z1),                   \
    X2##minXX = (Y2), X2##maxXX = (Z2);                       \
    for (Size X1 = X1##minXX; X1 < X1##maxXX; ++X1)           \
      for (Size X2 = X2##minXX; X2 < X2##maxXX; ++X2)
  
  /**
   * Iterates with a single index, from 0 to M.
   */
#define ITER_1(M)                               \
  for (UInt i = 0; i < M; ++i)   
  
  /**
   * Iterates over 2 indices, from 0 to M, and 0 to N.
   */
#define ITER_2(M, N)                          \
  for (UInt i = 0; i < M; ++i)                \
    for (UInt j = 0; j < N; ++j)         

  /**
   * Iterates over 3 indices, from 0 to M, 0 to N, and 0 to P.
   */
#define ITER_3(M, N, P)                          \
  for (UInt i = 0; i < M; ++i)                   \
    for (UInt j = 0; j < N; ++j)                 \
      for (UInt k = 0; k < P; ++k)
  
  /**
   * Iterates over 4 indices, from 0 to M, 0 to N, 0 to P and 0 to Q.
   */
#define ITER_4(M, N, P, Q)                         \
  for (UInt i = 0; i < M; ++i)                     \
    for (UInt j = 0; j < N; ++j)                   \
      for (UInt k = 0; k < P; ++k)                 \
        for (UInt l = 0; l < Q; ++l)

 /**
   * Iterates over 5 indices.
   */
#define ITER_5(M, N, P, Q, R)                        \
  for (UInt i = 0; i < M; ++i)                       \
    for (UInt j = 0; j < N; ++j)                     \
      for (UInt k = 0; k < P; ++k)                   \
        for (UInt l = 0; l < Q; ++l)                 \
          for (UInt m = 0; m < R; ++m)

 /**
   * Iterates over 6 indices.
   */
#define ITER_6(M, N, P, Q, R, S)                    \
  for (UInt i = 0; i < M; ++i)                      \
    for (UInt j = 0; j < N; ++j)                    \
      for (UInt k = 0; k < P; ++k)                  \
        for (UInt l = 0; l < Q; ++l)                \
          for (UInt m = 0; m < R; ++m)              \
            for (UInt n = 0; n < S; ++n)
  
  /**
   * Function object that takes a single argument, a pair (or at least
   * a class with the same interface as pair), and returns the pair's
   * first element. This is not part of the C++ standard, but usually
   * provided by implementations of STL. 
   */
  template <class Pair>
  struct select1st
    : public std::unary_function<Pair, typename Pair::first_type> 
  {
    inline const typename Pair::first_type& operator()(const Pair& x) const
    {
      return x.first;
    }
  };
 
  /**
   * Function object that takes a single argument, a pair (or at least
   * a class with the same interface as pair), and returns the pair's
   * second element. This is not part of the C++ standard, but usually
   * provided by implementations of STL. 
   */
  template <class Pair>
  struct select2nd 
    : public std::unary_function<Pair, typename Pair::second_type> 
  {
    inline const typename Pair::second_type& operator()(const Pair& x) const
    {
      return x.second;
    }
  };

}; // namespace std

#endif // NTA_UTILS_HPP

