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

/** @file
 * A few types used in nta/math and nta/algorithms.
 */

#ifndef NTA_MATH_TYPES_HPP
#define NTA_MATH_TYPES_HPP

#include <limits>
#include <vector>
#include <set>
#include <algorithm> // sort

#include <nta/types/types.hpp>
#include <nta/utils/Log.hpp> 

/* This file is used by array_algo.hpp */

namespace nta {

  //--------------------------------------------------------------------------------
  // BYTE VECTOR
  //--------------------------------------------------------------------------------
  /**
   * This is a good compromise between speed and memory for the use cases we have.
   * Going to a real vector of bits is slower when accessing the individual bits,
   * but this vector of bytes can still be fed to the SSE with good results.
   */
  struct ByteVector : public std::vector<nta::Byte> 
  {
    inline ByteVector(size_t n =0)
      : std::vector<nta::Byte>(n, (nta::Byte)0)
    {}

    /**
     * Use these two functions when converting with a vector of int or float
     * since the byte represenation of the elements in a byte vector is _not_
     * the same as the byte representation of ints and floats.
     */
    template <typename It>
    inline ByteVector(It begin, size_t n)
      : std::vector<nta::Byte>(n, 0)
    {
      for (size_t i = 0; i != this->size(); ++i)
        (*this)[i] = *begin++ != 0;
    }

    template <typename It>
    inline void toDense(It begin, It end)
    {
      for (size_t i = 0; i != this->size(); ++i)
        *begin++ = (*this)[i] != 0;
    }
  };


  //--------------------------------------------------------------------------------
  // Buffer
  //--------------------------------------------------------------------------------
  /**
   * Allocated once, but only the first n positions are valid (std::vector does that!)
   * DON'T USE ANYMORE, but keeping it because a lot of code already depends on it.
   */
  template <typename T>
  struct Buffer : public std::vector<T>
  {
    typedef size_t size_type;
    typedef T value_type;

    size_type nnz;

    inline Buffer(size_type _s =0)
      : std::vector<T>(_s),
        nnz(0)
    {}

    inline void clear()
    {
      nnz = 0;
    }

    inline void adjust_nnz(size_t n) // call resize?
    {
      nnz = std::min(nnz, n);
    }

    inline bool empty() const 
    { 
      return nnz == 0; 
    }

    inline void push_back(const T& x)
    {
      (*this)[nnz++] = x;
    }

    inline typename std::vector<T>::iterator nnz_end() 
    { 
      return this->begin() + nnz; 
    }

    inline typename std::vector<T>::const_iterator nnz_end() const 
    { 
      return this->begin() + nnz; 
    }
  };

  //--------------------------------------------------------------------------------
  // Direct access with fast erase
  //--------------------------------------------------------------------------------
  // Records who has been set, so that resetting to zero is fast. Usage pattern
  // is to clear the board, do a bunch of sets, look at the board (to test for
  // membership for example), then reset the board in the next iteration. 
  // It trades memory for speed. T is adjustable to be bool (uses vector<bool>, 
  // 1 bit per element), or int, or ushort, or long, or even float. For 
  // a membership board (set), on darwin86, unsigned short is fastest on 8/11/2010.
  // The clear() method provides a kind of incremental reset.
  // Assumes the elements that are set are sparse, that there aren't many compared
  // to the size of the board.
  template <typename I, typename T>
  struct DirectAccess
  {
    typedef I size_type;
    typedef T value_type;

    std::vector<T> board;
    std::vector<size_type> who;

    inline void resize(size_type m, size_type n =0)
    {
      //m = 4 * (m / 4);
      board.resize(m, T());
      who.reserve(n == 0 ? m : n);

      assert(who.size() == 0);
    }

    inline void set(size_type w, const T& v = T(1))
    {
      assert(w < board.size());
      assert(v != T());
      assert(who.size() < who.capacity());

      if (board[w] == T()) { // that if doesn't doest much at all (verified)
        who.push_back(w);
        //assert(std::set<size_type>(who.begin(),who.end()).size() == who.size());
      }

      board[w] = v;
    }

    inline T get(size_type w) const
    {
      assert(w < board.size());

      return board[w];
    }

    // Only const operator because the non-const has annoying side-effects
    // that are easily unintended
    inline const T& operator[](size_type w) const
    {
      return board[w];
    }

    inline void increment(size_type w)
    {
      assert(w < board.size());

      if (board[w] == T()) {
        who.push_back(w);
        //assert(std::set<size_type>(who.begin(),who.end()).size() == who.size());
      }

      ++ board[w];
    }

    // If board[w] becomes T() again, we need to update who
    inline void decrement(size_type w)
    {
      assert(w < board.size());

      if (board[w] == T()) {
        who.push_back(w);
        //assert(std::set<size_type>(who.begin(),who.end()).size() == who.size());
      }

      -- board[w];
    
      // To make sure we keep the uniqueness invariant,
      // might be costly if not very sparse?
      if (board[w] == T()) {
        size_type i = 0;
        while (who[i] != w)
          ++i;
        std::swap(who[i], who[who.size()-1]);
        who.pop_back();
      }
    }

    // v can be anything, < 0, == 0, or > 0
    // If board[w] becomes T() again, we need to update who
    inline void update(size_type w, const value_type& v)
    {
      assert(w < board.size());

      if (board[w] == T()) {
        who.push_back(w);
        //assert(std::set<size_type>(who.begin(),who.end()).size() == who.size());
      }

      board[w] += v;

      // To make sure we keep the uniqueness invariant,
      // might be costly if not very sparse?
      if (board[w] == T()) {
        size_type i = 0;
        while (who[i] != w)
          ++i;
        std::swap(who[i], who[who.size()-1]);
        who.pop_back();
      }
    }
  
    // Clear by 4 is a little bit faster, but works only
    // if T() takes exactly 4 bytes.
    inline void clear()
    {
      size_type* w = &who[0], *w_end = w + who.size();
      //size_type* p = (size_type*) &board[0];
      while (w != w_end)
        //p[*w++] = 0;
        board[*w++] = T();
      who.resize(0);
    }

    // Keep only the value above a certain threshold.
    // Resort the who array optionally.
    // TODO: unit test more
    inline void threshold(const T& t, bool sorted =false)
    {
      int n = who.size();
      int i = 0;

      while (i < n) 
        if (board[who[i]] < t) 
          std::swap(who[i], who[--n]);
        else                                    
          ++i;

      who.resize(n);

      if (sorted)
        std::sort(who.begin(), who.end());
    }
  };

  //--------------------------------------------------------------------------------
  // Avoids cost of clearing the board by using multiple colors. Clears only
  // every 255 iterations.
  // Doesn't keep list of who's on for fast iteration like DirecAccess does.
  template <typename I, typename T>
  struct Indicator;

  template <typename I>
  struct Indicator<I, unsigned short>
  {
    typedef I size_type;

    std::vector<unsigned short> board;
    unsigned short color;

    inline void resize(size_type m)
    {
      color = 0;
      board.resize(m, color);
    }

    inline void set(size_type w)
    {
      NTA_ASSERT(w < board.size());

      board[w] = color;
    }

    inline bool is_on(size_type w) const
    {
      NTA_ASSERT(w < board.size());

      return board[w] == color;
    }

    inline bool operator[](size_type w) const
    {
      NTA_ASSERT(w < board.size());

      return is_on(w);
    }
  
    inline void clear()
    {
      if (color < std::numeric_limits<unsigned short>::max())
        ++color;
      else {
        color = 0;
        std::fill(board.begin(), board.end(), color);
      }
    }

    template <typename It>
    inline void set_from_sparse(It begin, It end)
    {
      NTA_ASSERT(begin <= end);

      this->clear();
      while (begin != end)
        this->set(*begin++);
    }
  };

  //--------------------------------------------------------------------------------
  /**
   * The first element of each pair is the index of a non-zero, and the second element
   * is the value of the non-zero.
   */
  template <typename T1, typename T2>
  struct SparseVector : public Buffer<std::pair<T1,T2> >
  {
    typedef T1 size_type;
    typedef T2 value_type;

    inline SparseVector(size_type s =0)
      : Buffer<std::pair<T1,T2> >(s)
    {}
  };

  //--------------------------------------------------------------------------------
}; // end namespace nta

#endif // NTA_MATH_TYPES_HPP
