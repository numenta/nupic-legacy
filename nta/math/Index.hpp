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
 * Definition and implementation for Index class
 */

#ifndef NTA_INDEX_HPP
#define NTA_INDEX_HPP

//----------------------------------------------------------------------

#include <cstdarg>
#include <string.h> // for memcpy in gcc 4.4

#include <nta/math/utils.hpp>
#include <nta/math/math.hpp>
#include <nta/math/stl_io.hpp>

//----------------------------------------------------------------------

// Work around terrible Windows legacy issue - min and max global macros!!!
#ifdef max
#undef max
#endif

namespace nta {

  /**
   * @b Responsibility
   *  Index is a multi-dimensional index, consisting of a series of integers.
   *  It is a fixed size index, where the size is fixed at compile time. 
   *  The size is the parameter NDims of the template. UInt is the type
   *  of integers stored in the index.
   *
   * @b Rationale
   *  Index is useful when working multi-dimensional SparseTensors. 
   *
   * @b Notes
   *  NDims > 0 (that is, 0 is not allowed...)
   */
  template <typename UInt, const UInt NDims>
  class Index
  {
  public:
    typedef UInt value_type;
    typedef UInt* iterator;
    typedef const UInt* const_iterator;

    /**
     * Default constructor.
     * Creates an index initialized to zero.
     */
    inline Index()
    {
      memset(i_, 0, NDims*sizeof(value_type));
    }
  
    /**
     * Constructor from an array.
     * Creates an index that has the values in the given array.
     *
     * @param i [Uint[NDims] ] the values to initialize the index with
     */
    explicit inline Index(const UInt i[NDims])
    {
      memcpy(i_, i, NDims*sizeof(value_type));
    }
  
    /**
     * Constructor from a list.
     * Creates an index initialized with the values passed in the list.
     *
     * @param i0 [Uint...] the list of values to initialize the index with
     */
    explicit inline Index(UInt i0, ...)
    {
      i_[0] = i0;
    
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < NDims; ++k)
      {
        value_type v = va_arg(indices, value_type);
        i_[k] = v;
      }
      va_end(indices);
    }

    /**
     * Constructor from bounds and an ordinal.
     * This constructor builds the index that corresponds to the 
     * given ordinal, with the given bounds.
     *
     * @param bounds [Index] the bounds to use to compute the index
     * @param ordinal [UInt] the ordinal that will correspond to 
     *  this index
     */
    explicit inline Index(const Index& bounds, const value_type& ordinal) 
    {
      fromOrdinal(bounds, ordinal);
    }

    inline Index(const std::vector<UInt> idx)
    {
      for (UInt k = 0; k < NDims; ++k)
        i_[k] = idx[k];
    }

    /**
     * Copy constructor.
     *
     * @param from [Index] the index to copy
     */
    inline Index(const Index& from)
    {
      if (&from != this)
        memcpy(i_, from.i_, NDims*sizeof(value_type));
    }

    /**
     * Assignment operator.
     *
     * @param from [Index] the index to copy
     */
    inline Index& operator=(const Index& from)
    {
      if (&from != this)
        memcpy(i_, from.i_, NDims*sizeof(UInt));
      return *this;
    }

    inline iterator begin() { return i_; }
    inline iterator end() { return begin() + NDims; }
    inline const_iterator begin() const { return i_; }
    inline const_iterator end() const { return begin() + NDims; }
    inline UInt size() const { return NDims; }

    inline UInt max() const 
    {
      UInt M = 0;
      for (UInt i = 0; i < NDims; ++i)
        if (i_[i] > M)
          M = i_[i];
      return M;
    }
    
    /**
     * Indexing operator.
     *
     * @param idx [0 <= UInt < NDims] index
     * @retval [UInt&] the value at index 'idx'
     */
    inline UInt& operator[](const UInt idx)
    {
      {
        NTA_ASSERT(idx >= 0 && idx < NDims)
          << "Index::operator[] "
          << "Invalid index: " << idx
          << " - Should be in [0.." << NDims << ")";
      }
      
      return i_[idx];
    }

    /**
     * Const indexing operator.
     *
     * @param idx [0 <= UInt < NDims] index
     * @retval [const UInt] the value at index 'idx'
     */
    inline UInt operator[](const UInt& idx) const
    {
      {
        NTA_ASSERT(idx >= 0 && idx < NDims)
          << "Index::operator[] const "
          << "Invalid index: " << idx
          << " - Should be in [0.." << NDims << ")";
      }

      return i_[idx];
    }

    /**
     * Resets the whole index to all zeros.
     */
    inline void setToZero()
    {
      memset(i_, 0, NDims*sizeof(UInt));
    }
    
    /**
     * Returns whether the values in this index constitute a set or not
     * (there are no duplicates).
     */
    inline bool isSet() const 
    {
      std::set<UInt> s;
      for (UInt i = 0; i < NDims; ++i)
        s.insert(i_[i]);
      return s.size() == NDims;
    }

    /**
     * Increments this index, using bounds as the upper bound
     * for the iteration.
     *
     * @param bounds [Index] the upper bound
     * @retval bool whether we've reached the end of the iteration or not
     */
    inline bool increment(const Index& bounds)
    {
      int curr = NDims-1;
      ++i_[curr];
      while (i_[curr] >= bounds[curr]) {
        i_[curr] = 0;
        --curr;
        if (curr < 0)
          return false;
        else
          ++i_[curr];
      }
      return true;
    }

    /**
     * Increment this index, using lb and ub as lower and upper
     * bounds for the iteration.
     *
     * @param lb [index] the lower bound
     * @param ub [Index] the upper bound
     * @retval bool whether we've reached the end of the iteration or not
     */
    inline bool increment(const Index& lb, const Index& ub)
    {
      int curr = NDims-1;
      ++i_[curr];
      while (i_[curr] >= ub[curr]) {
        i_[curr] = lb[curr];
        --curr;
        if (curr < 0)
          return false;
        else
          ++i_[curr];
      }
      return true;
    }

    /**
     * Computes the ordinal corresponding to the "natural"
     * order for this index. For example, with bounds = [3, 2],
     * [0, 0] -> 0, [0, 1] -> 1, [1, 0] -> 2, [1, 1] -> 3, 
     * [2, 0] -> 4, [2, 1] -> 5.
     *
     * @param bounds [Index] the upper bound to use to compute
     *  the ordinal
     * @retval UInt the ordinal for this index
     */
    inline UInt ordinal(const Index& bounds) const
    {
      {
        NTA_ASSERT(indexGtZero(bounds));
      }
    
      if (NDims == 1) // do specialization
        return i_[0];
      
      UInt p = bounds[NDims-1], pos = i_[NDims-1];
      
      for (int k = NDims-2; k >= 1; p *= bounds[k], --k) 
        pos += i_[k] * p;
      pos += i_[0] * p;

      return pos;
    }

    inline void fromOrdinal(const Index& bounds, const value_type& ordinal)
    {
      {
        NTA_ASSERT(indexGtZero(bounds));
      }
      
      value_type o = ordinal, p = bounds.product() / bounds[0];
     //TODO optimize /  
      for (UInt k = 0; k < NDims-1; o %= p, p /= bounds[k+1], ++k) 
        i_[k] = o / p;
      i_[NDims-1] = o;
    }
    
    /**
     * Computes the stride for dimension dim of this Index.
     * If the Index is :[6, 7, 5, 4], then:
     * stride(0) = 7*5*4,
     * stride(1) = 5*4,
     * stride(2) = 4,
     * stride(3) = 1.
     *
     * @param dim [UInt] the dim for which we want the stride
     * @retval UInt the stride
     */
    inline UInt stride(const UInt& dim) const
    {
      if (dim == NDims-1)
        return 1;

      UInt s = i_[dim+1];
      for (UInt i = dim+2; i < NDims; ++i)
        s*= i_[i];
      return s;
    }

    /**
     * Computes the distance between two indices, with respect to 
     * a given upper bound. That is:
     * distance = other.ordinal(bounds) - this->ordinal(bounds).
     *
     * @param bounds [Index] the upper bound
     * @param other [Index] the second index
     * @retval UInt the distance between this and the second index
     */
    inline UInt distance(const Index& bounds, const Index& other) const
    {
      return other.ordinal(bounds) - ordinal(bounds);
    }

    /**
     * Computes the product of all the values in this index.
     * The result can be zero, if at least one of the indices
     * is zero. 
     * 
     * @retval UInt the product
     */
    inline UInt product() const
    {
      UInt n = i_[0];
      for (UInt k = 1; k < NDims; ++k)
        n *= i_[k];
      return n;
    }

    /**
     * Computes the complement of this index.
     *
     * For example:
     * (*this) [0, 2, 4] -(N=6)-> (idx) [1, 3, 5] 
     * (*this) [0, 2]    -(N=3)-> (idx) [1]
     * (*this) [0]       -(N=2)-> (idx) [1]
     * (*this) [0, 1]    -(N=3)-> (idx) [2]
     *
     * @param idx [Index<UInt, R>] the complement of this index
     */
    template <UInt R>
    inline void complement(Index<UInt, R>& idx) const
    {
      const UInt N = NDims + R;
      UInt k = 0, k1 = 0, k2 = 0;

      for (k = 0; k < NDims; ++k) {
        for (; k1 < i_[k]; ++k1) 
          idx[k2++] = k1;
        k1 = i_[k]+1;
      }

      while (k1 < N)
        idx[k2++] = k1++;
    }

    /**
     * Computes the projection of this index on to the dimensions
     * specified: 
     * idx2[k] = (*this)[dims[k]], for k in [0..R).
     *
     * @param dims [Index<UInt, R>] the dimensions to project onto
     * @param idx2 [Index<Uint, R>] the projection of this index
     */
    template <UInt R>
    inline void project(const Index<UInt, R>& dims, Index<UInt, R>& idx2) const
    {
      {
        NTA_ASSERT(R <= NDims)
          << "Index::project(): "
          << "Invalid number of dimensions to project on: " << R
          << " - Should be less than: " << NDims;

        for (UInt k = 0; k < R-1; ++k)
          NTA_ASSERT(dims[k] < dims[k+1])
            << "Index::project(): "
            << "Dimensions need to be in strictly increasing order, "
            << "passed: " << dims;

        NTA_ASSERT(0 <= dims[0] && dims[R-1] <= NDims)
            << "Index::project(): "
            << "Invalid dimensions: " << dims
            << " when projecting in: [0.." << R << ")";
      }

      for (UInt k = 0; k < R; ++k)
        idx2[k] = i_[dims[k]];
    }

    /**
     * Embeds the current index into an index of higher dimension:
     * idx2[dims[k]] = (*this)[k], for k in [0..R).
     *
     * @param dims [Index<Uint, R>] the dimensions to embed into
     * @param idx [Index<Uint, R2>] the embedding of this index
     */
    template <UInt R, UInt R2>
    inline void embed(const Index<UInt, R>& dims, Index<UInt, R2>& idx2) const
    {
      {
        NTA_ASSERT(R2 >= NDims) 
          << "Index::embed(): "
          << "Invalid number of dimensions to embed into: " << R2
          << " - Should be >= " << NDims;

        for (UInt k = 0; k < R-1; ++k)
          NTA_ASSERT(dims[k] < dims[k+1])
            << "Index::embed(): "
            << "Dimensions need to be in strictly increasing order, "
            << "passed: " << dims;

        NTA_ASSERT(0 <= dims[0] && dims[R-1] <= R2)
            << "Index::embed(): "
            << "Invalid dimensions: " << dims
            << " when embedding in: [0.." << R2 << ")";
      }

      for (UInt k = 0; k < R; ++k)
        idx2[dims[k]] = i_[k];
    }

    /**
     * Permutes this index according to the order specified in ind.
     * Examples:
     * [1 2 3 4 5] becomes [2 3 4 5 1] with ind = [1 2 3 4 0]
     * [1 2 3] becomes [3 1 2] with ind = [2 1 0]
     * 
     * @param ind [Index<UInt, NDims>] the new order
     * @param perm [Index<UInt, NDims>] the resulting permutation
     */
    inline void permute(const Index& ind, Index& perm) const
    {
      {
        checkPermutation_(ind);
      }

      for (UInt k = 0; k < NDims; ++k)
        perm[k] = i_[ind[k]];
    }

    inline Index permute(const Index& ind) const
    {
      {
        checkPermutation_(ind);
      }

      Index perm;
      permute(ind, perm);
      return perm;
    }

    /**
     * Finds the permutation that transforms this index into perm.
     * If this index is [1 2 3 4 5] and perm is [2 3 4 5 1], 
     * the permutation is [1 2 3 4 0]
     * Slow: O(NDims^2)
     */
    inline void findPermutation(Index& ind, const Index& perm) const
    {
      for (UInt k = 0; k < NDims; ++k)
        for (UInt k1 = 0; k1 < NDims; ++k1)
          if (perm[k1] == i_[k])
            ind[k1] = k;
    }
    
    inline Index findPermutation(const Index& perm) const
    {
      Index ind;
      findPermutation(ind, perm);
      return ind;
    }

    /**
     * Returns whether any of the values in this index is a zero.
     * (That is, the "index" cannot be used to describe the dimensions
     * of a tensor).
     */
    inline bool hasZero() const 
    {
      for (UInt i = 0; i < NDims; ++i)
        if (i_[i] == 0)
          return true;
      return false;
    }

    /**
     * Streaming operator (for debugging).
     */
    //template <typename I, UInt n>
    //NTA_HIDDEN friend std::ostream& operator<<(std::ostream&, const Index<I, n>&);
    UInt i_[NDims];
  private:

    /**
     * This method becomes empty and optimized away when assertions are turned off.
     */
    inline void checkPermutation_(const Index& ind) const
    {
#ifdef NTA_ASSERTIONS_ON
      std::set<UInt> s;
      for (UInt k = 0; k < NDims; ++k) {
        NTA_ASSERT(ind[k] >= 0 && ind[k] < NDims);
        s.insert(ind[k]);
      }
      NTA_ASSERT(s.size() == NDims);
#endif
    }
  };

  //--------------------------------------------------------------------------------
  template <typename I, UInt NDims>
  std::ostream& operator<<(std::ostream& outStream, const Index<I, NDims>& i)
  {
    outStream << "[";
    for (UInt k = 0; k < NDims; ++k)
      outStream << i.i_[k] << (k < NDims-1 ? "," : "");
    return outStream << "]";
  }

  template <typename I, UInt n1, UInt n2>
  inline Index<I, n1+n2> concatenate(const Index<I, n1>& i1, const Index<I, n2>& i2)
  {
    Index<I, n1+n2> newIndex;
    for (I k = 0; k < n1; ++k)
      newIndex[k] = i1[k];
    for (I k = 0; k < n2; ++k)
      newIndex[n1+k] = i2[k];
    return newIndex;
  }

  template <typename UInt>
  inline std::vector<UInt> concatenate(const std::vector<UInt>& i1, 
                                       const std::vector<UInt>& i2)
  {
    std::vector<UInt> newIndex(i1.size() + i2.size(), 0);
    for (UInt k = 0; k < i1.size(); ++k) 
      newIndex[k] = i1[k];
    for (UInt k = 0; k < i2.size(); ++k)
      newIndex[i1.size()+k] = i2[k];
    return newIndex;
  }

  template <typename Index>
  inline void setToZero(Index& idx)
  {
    const UInt NDims = (UInt)idx.size();
    for (UInt i = 0; i < NDims; ++i)
      idx[i] = 0;
  }

  /**
   * Returns whether the values in this index constitute a set or not
   * (there are no duplicates).
   */
  template <typename Index>
  inline bool isSet(const Index& idx)
  {
    std::set<typename Index::value_type> s;
    const UInt NDims = (UInt)idx.size();
    for (UInt i = 0; i < NDims; ++i)
      s.insert(idx[i]);
    return s.size() == NDims;
  }

  /**
   * Returns whether any of the values in this index is a zero.
   * (That is, the "index" cannot be used to describe the dimensions
   * of a tensor).
   */
  template <typename Index>
  inline bool hasZero(const Index& idx) 
  { 
    const UInt NDims = idx.size();
    for (UInt i = 0; i < NDims; ++i)
      if (idx[i] == 0)
        return true;
    return false;
  }

  template <typename Index>
  inline bool isZero(const Index& idx)
  {
    const UInt NDims = idx.size();
    for (UInt i = 0; i < NDims; ++i)
      if (idx[i] != 0)
        return false;
    return true;
  }
  
  template <typename Index>
  inline bool indexGtZero(const Index& idx)
  {
    const UInt NDims = idx.size();
    for (UInt i = 0; i < NDims; ++i)
      if (idx[i] <= 0)
        return false;
    return true;
  }
  
  /**
   * This is not the same as positiveInBounds.
   */
  template <typename Index1, typename Index2>
  inline bool indexLt(const Index1& i1, const Index2& i2)
  {
    {
      NTA_ASSERT(i1.size() == i2.size());
    }
    
    const UInt NDims = (UInt)i1.size();
    for (UInt k = 0; k < NDims; ++k) 
      if (i1[k] < i2[k])
        return true;
      else if (i1[k] > i2[k])
        return false;
    return false;
  }

  /**
   * This is not  the same as positiveInBounds.
   */
  template <typename Index1, typename Index2>
  inline bool indexLe(const Index1& i1, const Index2& i2)
  {
    {
      NTA_ASSERT(i1.size() == i2.size());
    }

    const UInt NDims = i1.size();
    for (UInt k = 0; k < NDims; ++k) 
      if (i1[k] < i2[k])
        return true;
      else if (i1[k] > i2[k])
        return false;
    return true;
  }

  template <typename Index1, typename Index2>
  inline bool indexEq(const Index1& i1, const Index2& i2)
  {
    {
      NTA_ASSERT(i1.size() == i2.size());
    }

    const UInt NDims = (UInt)i1.size();
    for (UInt k = 0; k < NDims; ++k) 
      if (i1[k] != i2[k])
        return false;
    return true;
  }

  /**
   * 0 is included, ub is excluded.
   */
  template <typename Index1, typename Index2>
  inline bool positiveInBounds(const Index1& idx, const Index2& ub)
  {
    {
      NTA_ASSERT(idx.size() == ub.size());
    }

    const UInt NDims = idx.size();
    for (UInt k = 0; k < NDims; ++k)
      if (idx[k] >= ub[k])
        return false;
    return true;
  }

  /**
   * lb is included, ub is excluded.
   */
  template <typename Index1, typename Index2, typename Index3>
  inline bool inBounds(const Index1& lb, const Index2& idx, const Index3& ub)
  {
    {
      NTA_ASSERT(idx.size() == lb.size());
      NTA_ASSERT(idx.size() == ub.size());
    }

    const UInt NDims = idx.size();
    for (UInt k = 0; k < NDims; ++k)
      if (idx[k] < lb[k] || idx[k] >= ub[k])
        return false;
    return true;
  }

  /**
   * Increments this index, using bounds as the upper bound
   * for the iteration.
   *
   * @param bounds [Index] the upper bound
   * @retval bool whether we've reached the end of the iteration or not
   */
  template <typename Index1, typename Index2>
  inline bool increment(const Index1& bounds, Index2& idx)
  {
    {
      NTA_ASSERT(bounds.size() == idx.size());
      NTA_ASSERT(positiveInBounds(idx, bounds));
    }
    
    int curr = (UInt)idx.size()-1;
    ++idx[curr];
    while (idx[curr] >= bounds[curr]) {
      idx[curr] = 0;
      --curr;
      if (curr < 0)
        return false;
      else
        ++idx[curr];
    }
    return true;
  }

  /**
   * Increment this index, using lb and ub as lower and upper
   * bounds for the iteration.
   *
   * @param lb [index] the lower bound
   * @param ub [Index] the upper bound
   * @retval bool whether we've reached the end of the iteration or not
   */
  template <typename Index1, typename Index2, typename Index3>
  inline bool increment(const Index1& lb, const Index2& ub, Index3& idx)
  {
    {
      inBounds(lb, idx, ub);
    }
    
    int curr = idx.size()-1;
    ++idx[curr];
    while (idx[curr] >= ub[curr]) {
      idx[curr] = lb[curr];
      --curr;
      if (curr < 0)
        return false;
      else
        ++idx[curr];
    }
    return true;
  }

  /**
   * Computes the ordinal corresponding to the "natural"
   * order for this index. For example, with bounds = [3, 2],
   * [0, 0] -> 0, [0, 1] -> 1, [1, 0] -> 2, [1, 1] -> 3, 
   * [2, 0] -> 4, [2, 1] -> 5.
   *
   * @param bounds [Index] the upper bound to use to compute
   *  the ordinal
   * @retval UInt the ordinal for this index
   */
  template <typename Index1, typename Index2>
  inline typename Index1::value_type ordinal(const Index1& bounds, const Index2& idx)
  {    
    {
      NTA_ASSERT(bounds.size() == idx.size());
      NTA_ASSERT(indexGtZero(bounds));
      NTA_ASSERT(positiveInBounds(idx, bounds));
    }

    const UInt NDims = (UInt)idx.size();
    typename Index1::value_type p = bounds[NDims-1], pos = idx[NDims-1];
      
    for (int k = NDims-2; k >= 1; p *= bounds[k], --k) 
      pos += idx[k] * p;
    pos += idx[0] * p;

    return pos;
  }

  template <typename Index1, typename Index2>
  inline void setFromOrdinal(const Index1& bounds, 
                             const typename Index1::value_type& ordinal, 
                             Index2& idx) 
  {
    {
      NTA_ASSERT(bounds.size() == idx.size());
      NTA_ASSERT(indexGtZero(bounds));
    }
    
    const UInt NDims = (UInt)bounds.size();
    typename Index1::value_type o = ordinal, p = product(bounds) / bounds[0];
   //TODO optimize double / use (slow!) 
    for (UInt k = 0; k < NDims-1; ++k) { 
      o %= p;
      p /= bounds[k];
      idx[k] = o / p;
    }
    idx[NDims-1] = o;
  }

  /**
   * Computes the complement of this index.
   * For example:
   * (*this) [0, 2, 4] -(N=6)-> (idx) [1, 3, 5] 
   * (*this) [0, 2]    -(N=3)-> (idx) [1]
   * (*this) [0]       -(N=2)-> (idx) [1]
   * (*this) [0, 1]    -(N=3)-> (idx) [2]
   *
   * @param idx [Index<UInt, R>] the complement of this index
   */
  template <typename Index, typename Index2>
  inline void complement(const Index& idx, Index2& c_idx) 
  {
    const UInt NDims = (UInt)idx.size();
    const UInt R = (UInt)c_idx.size();
    const UInt N = NDims + R;
    UInt k = 0, k1 = 0, k2 = 0;   

    for (k = 0; k < NDims; ++k) {
      for (; k1 < idx[k]; ++k1) 
        c_idx[k2++] = k1;
      k1 = idx[k]+1;
    }

    while (k1 < N)
      c_idx[k2++] = k1++;
  }

  /**
   * Computes the projection of this index on to the dimensions
   * specified: 
   * idx2[k] = (*this)[dims[k]], for k in [0..R).
   *
   * @param dims [Index<UInt, R>] the dimensions to project onto
   * @param idx2 [Index<Uint, R>] the projection of this index
   */
  template <typename Index1, typename Index2, typename Index3>
  inline void project(const Index1& dims, const Index2& idx, Index3& idx2)
  {
    const UInt NDims = (UInt)idx.size();
    const UInt R = (UInt)idx2.size();
    
    {
      NTA_ASSERT(idx2.size() == dims.size());

      NTA_ASSERT(R <= NDims)
        << "Index::project(): "
        << "Invalid number of dimensions to project on: " << R
        << " - Should be less than: " << NDims;

      for (UInt k = 0; k < R-1; ++k)
        NTA_ASSERT(dims[k] < dims[k+1])
          << "Index::project(): "
          << "Dimensions need to be in strictly increasing order, "
          << "passed: " << dims;

      NTA_ASSERT(0 <= dims[0] && dims[R-1] <= NDims)
        << "Index::project(): "
        << "Invalid dimensions: " << dims
        << " when projecting in: [0.." << R << ")";
    }

    for (UInt k = 0; k < R; ++k)
      idx2[k] = idx[dims[k]];
  }

  /**
   * Embeds the current index into an index of higher dimension:
   * idx2[dims[k]] = (*this)[k], for k in [0..R).
   * Note that if there are coordinates already set in idx2, 
   * they will stay there and not be reset to 0:
   * I6 i6;
   * I2 i2(2, 4), dims(1, 3);
   * I4 i4(1, 3, 5, 6), compDims;
   * embed(dims, i2, i6);
   * Test("Index embed 3", i6, I6(0, 2, 0, 4, 0, 0));
   * dims.complement(compDims);
   * embed(compDims, i4, i6);
   * Test("Index embed 4", i6, I6(1, 2, 3, 4, 5, 6));
   *
   * @param dims [Index<Uint, R>] the dimensions to embed into
   * @param idx [Index<Uint, R2>] the embedding of this index
   */
  template <typename Index1, typename Index2, typename Index3>
  inline void embed(const Index1& dims, const Index2& idx, Index3& idx2)
  {
    const UInt R = dims.size();
    const UInt NDims = idx.size();
    const UInt R2 = idx2.size();

    {
      NTA_ASSERT(idx.size() == dims.size());
      
      NTA_ASSERT(R2 >= NDims) 
        << "Index::embed(): "
        << "Invalid number of dimensions to embed into: " << R2
        << " - Should be >= " << NDims;

      for (UInt k = 0; k < R-1; ++k)
        NTA_ASSERT(dims[k] < dims[k+1])
          << "Index::embed(): "
          << "Dimensions need to be in strictly increasing order, "
          << "passed: " << dims;

      NTA_ASSERT(0 <= dims[0] && dims[R-1] <= R2)
        << "Index::embed(): "
        << "Invalid dimensions: " << dims
        << " when embedding in: [0.." << R2 << ")";
    }

    for (UInt k = 0; k < R; ++k)
      idx2[dims[k]] = idx[k];
  }

  /**
   * Permutes this index according to the order specified in ind.
   * Examples:
   * [1 2 3 4 5] becomes [2 3 4 5 1] with ind = [1 2 3 4 0]
   * [1 2 3] becomes [3 1 2] with ind = [2 1 0]
   * 
   * @param ind [Index<UInt, NDims>] the new order
   * @param perm [Index<UInt, NDims>] the resulting permutation
   */
  template <typename Index1, typename Index2, typename Index3>
  inline void permute(const Index1& ind, const Index2& idx, Index3& perm)
  {
    {
#ifdef NTA_ASSERTIONS_ON
      std::set<typename Index1::value_type> s;
      for (UInt k = 0; k < ind.size(); ++k) {
        NTA_ASSERT(ind[k] >= 0 && ind[k] < ind.size());
        s.insert(ind[k]);
      }
      NTA_ASSERT(s.size() == ind.size());
#endif
      NTA_ASSERT(ind.size() == idx.size());
      NTA_ASSERT(ind.size() == perm.size());
    }

    const UInt NDims = (UInt)idx.size();
    for (UInt k = 0; k < NDims; ++k)
      perm[k] = idx[ind[k]];
  }

  //--------------------------------------------------------------------------------
  template <typename UInt, UInt R>
  inline bool operator==(const Index<UInt, R>& i1, const Index<UInt, R>& i2)
  {
    return indexEq(i1, i2);
  }

  template <typename UInt, UInt R>
  inline bool operator!=(const Index<UInt, R>& i1, const Index<UInt, R>& i2)
  {
    return ! indexEq(i1, i2);
  }

  template <typename UInt, UInt R>
  inline bool operator<(const Index<UInt, R>& i1, const Index<UInt, R>& i2)
  {
    return indexLt(i1, i2);
  }

  template <typename UInt>
  inline bool operator<(const std::vector<UInt>& i1, const std::vector<UInt>& i2)
  {
    return indexLt(i1, i2);
  }

  template <typename UInt, UInt R>
  inline bool operator<(const Index<UInt, R>& i1, const std::vector<UInt>& i2)
  {
    return indexLt(i1, i2);
  }

  template <typename UInt, UInt R>
  inline bool operator<(const std::vector<UInt>& i1, const Index<UInt, R>& i2)
  {
    return indexLt(i1, i2);
  }

  template <typename UInt, UInt R>
  inline bool operator<=(const Index<UInt, R>& i1, const Index<UInt, R>& i2)
  {
    return indexLe(i1, i2);
  }

  template <typename UInt>
  inline bool operator<=(const std::vector<UInt>& i1, const std::vector<UInt>& i2)
  {
    return indexLe(i1, i2);
  }

  template <typename UInt, UInt R>
  inline bool operator<=(const Index<UInt, R>& i1, const std::vector<UInt>& i2)
  {
    return indexLe(i1, i2);
  }

  template <typename UInt, UInt R>
  inline bool operator<=(const std::vector<UInt>& i1, const Index<UInt, R>& i2)
  {
    return indexLe(i1, i2);
  }

  //--------------------------------------------------------------------------------

} // end namespace nta

#endif // NTA_INDEX_HPP
