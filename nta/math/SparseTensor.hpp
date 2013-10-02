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
 * Definition and implementation for SparseTensors class
 */

#ifndef NTA_SPARSE_TENSOR_HPP
#define NTA_SPARSE_TENSOR_HPP

#ifdef NUPIC2
#include <nta/math/utils.hpp>
#else
#include <nta/common/utils.hpp>
#endif


#include <nta/math/math.hpp>
#include <nta/math/array_algo.hpp>
#include <nta/math/stl_io.hpp>
#include <nta/math/Domain.hpp>


//----------------------------------------------------------------------

#ifdef WIN32
#undef min
#undef max
#endif

/* FAST TENSOR */
/*
#include <ext/hash_map>
#include <nta/math/GPL_Hash2.hpp>

template <typename Index>
struct HashIndex
{
  inline size_t operator()(const Index& idx) const
  {
    return 1543 * idx[1] + idx[0];
  }
};
*/

//----------------------------------------------------------------------

namespace nta {

  /**
   * @b Description
   * SparseTensor models a multi-dimensional array, with an arbitrary
   * number of dimensions, and arbitrary size for each dimension,
   * where only certain elements are not zero. "Not zero" is defined as 
   * being outside the closed ball [-nta::Epsilon..nta::Epsilon].
   * Zero elements are not stored. Non-zero elements are stored in
   * a data structure that provides logarithmic insertion and retrieval.
   * A number of operations on tensors are implemented as efficiently as 
   * possible, oftentimes having complexity not worse than the number
   * of non-zeros in the tensor. There is no limit to the number of 
   * dimensions that can be specified for a sparse tensor. 
   *
   * SparseTensor is parameterized on the type of Index used to index 
   * the non-zeros, and on the type of the non-zeros themselves (Float).
   * The numerical type used as the second template parameter needs 
   * to be functionally equivalent to float, but can be int or double.
   * It doesn't work with complex numbers yet (have to modify nearlyZero_
   * to look at the modulus).
   *
   * The implementation relies on a Unique, Sorted Associative NZ,
   * that is map (rather than hash_map, we need the Indices to be sorted).
   *
   * Examples:
   * 1) SparseTensor<Index<UInt, 2>, float>:
   *  defines a sparse tensor of dimension 2 (a matrix), storing floats.
   *  The type of Index is the efficient, compile-time sized Index.
   *
   * 2) SparseTensor<std::vector<UInt>, float>:
   *  defines the same sparse tensor as 1), but using std::vector<UInt>
   *  for the index, which is not as fast.
   *
   * 3) SparseTensor<Index<UInt, 4> double>:
   *  defines a sparse tensor of rank 4 (4 dimensions), storing doubles.
   *
   * @b Responsibility
   *  An efficient multi-dimensional sparse data structure
   *
   * @b Rationale
   *  Numenta algorithms require very large data structure that are 
   *  sparse, and those data structures cannot be handled efficiently
   *  with contiguous storage in memory.
   *
   * @b Resource @Ownership
   *  SparseTensor owns the keys used to index the non-zeros, as
   *  well as the values of the non-zeros themselves.
   *
   * @b Notes
   * Note 1: in preliminary testing, using Index<UInt, Rank> was
   *  about 20 times faster than using std::vector<UInt>.
   * 
   * Note 2: some operations are very slow, depending on the properties
   *  of the functors used. Watch out that you are using the
   *  right one for your functor.
   *
   * Note 3: SparseTensor is limited to max<unsigned long> columns, or rows
   *  or non-zeros.
   * 
   */
  template <typename Index, typename Float>
  class SparseTensor
  {
  public:
    typedef Index TensorIndex;
    typedef typename Index::value_type UInt;
    typedef std::map<Index, Float> NZ; 
    //typedef __gnu_cxx::hash_map<Index, Float, HashIndex<Index> > NZ;
    //typedef hash_map<Index, Float, HashIndex<Index> > NZ;
    typedef typename NZ::iterator iterator;
    typedef typename NZ::const_iterator const_iterator;

    /**
     * SparseTensor constructor from list of bounds.
     * The constructed instance is identically zero.
     * Each of the integers passed in represents the size of 
     * this sparse tensor along a given dimension. There
     * need to be as many integers passed in as this tensor
     * has dimensions. All the integers need to be > 0.
     *
     * Note: 
     *  This constructor will not work with Index = std::vector
     *
     * @param ub [UInt >= 0] the size of this tensor along one dimension
     */
    explicit inline SparseTensor(UInt ub0, ...)
      : bounds_(), nz_()
    {
      bounds_[0] = ub0;
      va_list indices;
      va_start(indices, ub0);
      for (UInt k = 1; k < getRank(); ++k)
        bounds_[k] = (UInt) va_arg(indices, unsigned int); 
      va_end(indices);

      {
        NTA_ASSERT(indexGeZero(bounds_))
          << "SparseTensor::SparseTensor(UInt...):"
          << "Invalid bounds: " << bounds_
          << " - Should be >= 0";
      }
    }

    /**
     * SparseTensor constructor from Index that contains the bounds.
     * The constructed instance is identically zero.
     * The size of the Index becomes the rank of this sparse tensor,
     * that is, its number of dimensions.
     * The values of each element of the index need to be > 0.
     *
     * @param bounds [Index] the bounds of each dimension
     */
    explicit inline SparseTensor(const Index& bounds)
      : bounds_(bounds), nz_()
    {
      {
        NTA_ASSERT(indexGeZero(bounds_))
          << "SparseTensor::SparseTensor(Index):"
          << "Invalid bounds: " << bounds_
          << " - Should be >= 0";
      }
    }

    /**
     * SparseTensor copy constructor
     */
    inline SparseTensor(const SparseTensor& other)
      : bounds_(other.getBounds()), nz_()
    {
      this->operator=(other);
    }
  
    /**
     * Assignment operator
     */
    inline SparseTensor& operator=(const SparseTensor& other)
    {
      if (&other != this) {
        bounds_ = other.bounds_;
        nz_ = other.nz_;
      }
      return *this;
    }

    /**
     * Swaps the contents of two tensors.
     * The two tensors need to have the same rank, but they don't
     * need to have the same dimensions.
     * 
     * @param B [SparseTensor<Index, Float>] the tensor to swap with
     */
    inline void swap(SparseTensor<Index, Float>& B)
    {
      {
        NTA_ASSERT(B.getRank() == getRank());
      }
      
      std::swap(bounds_, B.bounds_);
      nz_.swap(B.nz_);
    }

    /**
     * Returns the rank of this tensor.
     * The rank is the number of dimensions of this sparse tensor,
     * it is an integer >= 1.
     *
     * Examples:
     * A tensor of rank 0 is a scalar (not possible here).
     * A tensor of rank 1 is a vector.
     * A tensor of rank 2 is a matrix.
     *
     * @retval UInt [ > 0 ] the rank of this sparse tensor
     */
    inline const UInt getRank() const { return (UInt)bounds_.size(); }

    /**
     * Returns the bounds of this tensor, that is the size of this tensor
     * along each of its dimensions.
     * Tensor indices start at zero along all dimensions.
     * The product of the bounds is the total number of elements that
     * this sparse tensor can store.
     *
     * Examples:
     * A 3 long vector has bounds Index(3).
     * A 10x10 matrix has bounds: Index(10, 10).
     *
     * @retval Index the upper bound for this sparse tensor
     */
    inline const Index getBounds() const { return bounds_; }

    /**
     * Returns the upper bound of this sparse tensor along
     * the given dimension.
     *
     * Example:
     * A 3x4x5 tensor has:
     * - getBound(0) == 3, getBound(1) == 4, getBound(2) == 5.
     *
     * @param dim [0 <= UInt < getRank()] the dimension
     * @retval [UInt >= 0] the upper of this tensor along dim
     */
    inline const UInt getBound(const UInt& dim) const 
    { 
      NTA_ASSERT(0 <= dim && dim < getRank());
      return getBounds()[dim]; 
    }

    /**
     * Returns the domain of this sparse tensor, where the lower bound
     * is zero and the upper bound is the upper bound.
     * 
     * Example:
     * A 3x2x4 tensor has domain { [0..3), [0..2), [0..4) }.
     *
     * @retval [Domain<UInt>] the domain for this tensor
     */
    inline Domain<UInt> getDomain() const
    {
      return Domain<UInt>(getNewZeroIndex(), getBounds());
    }

    /**
     * Returns the total size of this sparse tensor,
     * that is, the total number of non-zeros that can be stored.
     * It is the product of the bounds.
     *
     * Example:
     * A 3x3 matrix has a size of 9.
     *
     * @retval UInt [ > 0 ] the size of this sparse tensor
     */
    inline const UInt getSizeElts() const 
    { 
      NTA_ASSERT(!isNull());
      return product(getBounds()); 
    }

    /**
     * Returns the size of a sub-space of this sparse tensor,
     * designated by dims.
     *
     * Example:
     * A 3x4 matrix has a size of 4 along the columns and 3 
     * along the rows.
     */
    template <typename Index2>
    inline const UInt getSizeElts(const Index2& dims) const
    {
      {
        NTA_ASSERT(dims.size() <= getRank());
      }

      UInt n = 1;
      for (UInt k = 0; k < dims.size(); ++k)
        n *= getBound(dims[k]);
      return n;
    }

    /**
     * Returns the number of non-zeros in this sparse tensor.
     *
     * Invariant:
     * getNNonZeros() + getNZeros() == product(getBounds())
     *
     * @retval UInt [ >= 0 ] the number of non-zeros in this sparse tensor
     */
    inline const UInt getNNonZeros() const 
    { 
      return (UInt)nz_.size(); 
    }

    inline const UInt nNonZeros() const 
    { 
      return (UInt)nz_.size(); 
    }

    /**
     * Returns the number of zeros in this sparse tensor.
     *
     * Invariant:
     * getNZeros() + getNNonZeros() == product(getBounds())
     *
     * @retval UInt [ >= 0 ] the number of zeros in this sparse tensor
     */
    inline const UInt getNZeros() const 
    {
      return getSizeElts() - getNNonZeros(); 
    }
    
    /**
     * Returns the number of non-zeros in a domain of this sparse tensor.
     * Does not work with a domain that has closed dimensions.
     * The domain needs to have the same rank as this sparse tensor. 
     *
     * @param dom [Domain<UInt>] the domain to scan for non-zeros
     * @retval UInt [ >= 0 ] the number of non-zeros in dom
     */
    inline const UInt getNNonZeros(const Domain<UInt>& dom) const
    {
      {
        NTA_ASSERT(!dom.hasClosedDims());
        //NTA_ASSERT(getDomain().includes(dom));
      }
      
      // I can reduce the domain ub by 1 to find the upper_bound
      // but I still have to check for domain inclusion

      UInt nnz = 0;
      Index lb = getNewIndex(), ub = getNewIndex();

      if (dom == getDomain())
        return getNNonZeros();

      dom.getLB(lb); dom.getIterationLast(ub);
      const_iterator it = begin(); 
      const_iterator e = end(); 

      for (; it != e; ++it) {
        if (dom.includes(it->first)) 
          ++nnz;
      }

      return nnz;
    }

    /**
     * Returns the number of zeros in a domain of this sparse tensor.
     * Doens't work if the domain has closed dimensions.
     * The domain needs to have the same rank as this sparse tensor.
     *
     * @param dom [Domain<UInt>] the domain to scan for zeros
     * @retval UInt [ >= 0 ] the number of zeros in dom
     */
    inline const UInt getNZeros(const Domain<UInt>& dom) const
    {
      return dom.size_elts() - getNNonZeros(dom);
    }

    /**
     * Returns the number of non-zeros in designated sub-spaces of 
     * this sparse tensor. The sub-spaces are designated by dims.
     * The B tensor collects the results.
     *
     * Complexity: O(number of non-zeros)
     *
     * Example:
     * If A is a 11x13 sparse tensor:
     * - A.getNNonZeros(I1(1), B) returns the number of non-zeros
     *   per row in A, and B is a vector of size 11.
     * - A.getNNonZeros(I1(0), B) returns the number of non-zeros
     *   per column of A, and B is a vector of size 13.
     *
     * @param dims [Index2] the dimensions along which to count the non-zeros
     * @param B [SparseTensor<IndexB, Float>] the sparse tensor of the number
     *  of non-zeros per sub-space
     */
    template <typename Index2, typename IndexB>
    inline void getNNonZeros(const Index2& dims, SparseTensor<IndexB, Float>& B) const
    {
      {
        NTA_ASSERT(dims.size() + B.getRank() == getRank());
      }

      B.clear();

      IndexB compDims = B.getNewIndex(), idxB = B.getNewIndex();
      complement(dims, compDims);
      
      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it) {
        project(compDims, it->first, idxB);
        B.update(idxB, (Float)1, std::plus<Float>());
      }
    }

    /**
     * Returns the number of zeros in designated sub-spaces of 
     * this sparse tensor. See getNNonZeros doc.
     */
    template <typename Index2, typename IndexB>
    inline void getNZeros(const Index2& dims, SparseTensor<IndexB, Float>& B) const
    {
      {
        NTA_ASSERT(dims.size() + B.getRank() == getRank());
      }
      
      IndexB compDims = B.getNewIndex(), idxB = B.getNewIndex();
      complement(dims, compDims);
      
      B.setAll((Float)getSizeElts(dims));

      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it) {
        project(compDims, it->first, idxB);
        B.update(idxB, (Float)1, std::minus<Float>());
      }
    }

    /**
     * Returns true if this SparseTensor is the "empty" tensor,
     * that is, a SparseTensor with no value (like a matrix without
     * rows).
     */
    inline bool isNull() const
    {
      return product(getBounds()) == 0;
    }

    /**
     * Returns true if there is no non-zero in this tensor, false otherwise.
     *
     * @retval bool whether this sparse tensor is identically zero or not
     */
    inline bool isZero() const 
    { 
      return getNNonZeros() == 0; 
    }

    /**
     * Returns true if the domain inside this sparse tensor is identically
     * zero.
     * Doens't work if the domain has closed dimensions.
     * The domain needs to have the same rank as this sparse tensor.
     *
     * @param dom [Domain<UInt>] the domain to look at
     * @retval bool whether this sparse tensor is zero inside dom
     */
    inline bool isZero(const Domain<UInt>& dom) const
    {
      return getNNonZeros(dom) == 0;
    }

    /**
     * Returns true if there are no zeros in this tensor, false otherwise.
     * The tensor is dense if it contains no zero.
     *
     * @retval bool whether this tensor is dense or not
     */
    inline bool isDense() const 
    { 
      return getNNonZeros() == getSizeElts(); 
    }

    /**
     * Returns true if the domain inside this sparse tensor is dense.
     * Doens't work if the domain has closed dimensions.
     * The domain needs to have the same rank as this sparse tensor.
     *
     * @param dom [Domain<UInt>] the domain to look at
     * @retval bool whether this sparse tensor is dense inside dom
     */
    inline bool isDense(const Domain<UInt>& dom) const
    {
      return getNNonZeros(dom) == dom.size_elts();
    }

    /**
     * Returns true if there are zeros in this tensor, false otherwise.
     * The tensor is sparse if it contains at least one zero.
     *
     * @retval bool whether this tensor is sparse or not
     */
    inline bool isSparse() const 
    { 
      return getNNonZeros() != getSizeElts(); 
    }

    /**
     * Returns true if the domain inside this sparse tensor is sparse.
     * Doens't work if the domain has closed dimensions.
     * The domain needs to have the same rank as this sparse tensor.
     *
     * @param dom [Domain<UInt>] the domain to look at
     * @retval bool whether this sparse tensor is sparse inside dom
     */
    inline bool isSparse(const Domain<UInt>& dom) const
    {
      return getNNonZeros(dom) != dom.size_elts();
    }

    /**
     * Returns the fill rate for this tensor, that is, the ratio of the 
     * number of non-zeros to the total number of elements in this tensor.
     * 
     * @retval Float the fill rate
     */
    inline const Float getFillRate() const 
    { 
      return Float(getNNonZeros()) / Float(getSizeElts()); 
    }

    /**
     * Returns the fill rate for this tensor inside the given domain, that is,
     * the ratio of the number of non-zeros in the given domain to the 
     * size of the domain.
     *
     * @retval Float the fill rate inside the given domain
     */
    inline const Float getFillRate(const Domain<UInt>& dom) const
    {
      return Float(getNNonZeros(dom)) / Float(dom.size_elts());
    }

    /**
     * Returns the fill rate for sub-spaces of this sparse tensor.
     */
    template <typename Index2, typename IndexB>
    inline void getFillRate(const Index2& dims, SparseTensor<IndexB, Float>& B) const
    {
      getNNonZeros(dims, B);
      B.element_apply_fast(bind2nd(std::divides<Float>(), (Float)getSizeElts(dims)));
    }

    /**
     * Returns whether this sparse tensor is positive or not, that is,
     * whether all its coefficients are > nta::Epsilon (there are no
     * zeros in this tensor, and all the elements have positive values).
     *
     * Complexity: O(number of non-zeros)
     */
    inline bool isPositive() const
    {
      if (getNZeros() > 0)
        return false;

      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it)
        if (strictlyNegative(it->second))
          return false;
      return true;
    }

    /**
     * Returns whether this sparse tensor is non-negative or not,
     * that is, whether all its coefficients are >= -nta::Epsilon
     * (there can be zeros in this tensor, but all the non-zeros
     * have positive values).
     *
     * Complexity: O(number of non-zeros)
     */
    inline bool isNonNegative() const
    {
      if (nz_.empty())
        return true;

      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it)
        if (strictlyNegative(it->second))
          return false;
      return true;
    }

    /**
     * Returns the set of values in this SparseTensor and how 
     * many times each of them appears.  
     *
     * Complexity: O(number of non-zeros) with some log for 
     * the insertion in the result map... 
     */
    inline std::map<Float, UInt> values() const
    {
      std::map<Float, UInt> vals;

      if (!isDense())
        vals[0] = getNZeros();

      const_iterator it, e;
      typename std::map<Float, UInt>::iterator found;
      for (it = begin(), e = end(); it != e; ++it) {
        found = vals.find(it->second);
        if (found == vals.end())
          vals[it->second] = 1;
        else
          ++ vals[it->second];
      }

      return vals;
    }

    /**
     * Makes this tensor the tensor zero, that is, all the non-zeros
     * are removed.
     */
    inline void clear() { nz_.clear(); }

    /**
     * Creates a new Index that has the rank of this sparse tensor.
     * The initial value of this Index is the bounds of this tensor.
     * 
     * Note:
     * To accomodate both Index<UInt, X> and std::vector<UInt> as 
     * indices, we can't allocate memory ourselves, so when we 
     * need an index, we create a copy of the bounds, and either
     * do nothing, or set it to zero, or set to some specified
     * set of values. 
     *
     * @retval Index a new Index, that contains the values of the bounds
     *  for this sparse tensor
     */
    inline Index getNewIndex() const
    {
      return getBounds();
    }

    /**
     * Creates a new Index that has the rank of this sparse tensor
     * and sets it to zero (see note in getNewIndex()).
     *
     * @retval Index a new Index, initialized to zero
     */
    inline Index getNewZeroIndex() const 
    {
      Index idx = getBounds();
      setToZero(idx);
      return idx;
    }

    /**
     * Creates a new Index that has the rank of this sparse tensor
     * and sets it to the specified values (see note in getNewIndex()).
     *
     * @retval Index a new Index, initialized to the values passed
     */
    inline Index getNewIndex(UInt i0, ...) const
    {
      Index idx = getBounds();
      idx[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        idx[k] = (UInt) va_arg(indices, unsigned int); 
      va_end(indices);
      return idx;
    }

    /**
     * Computes whether this tensor is symmetric or not.
     * A tensor is symmetric w.r.t. a permutation of the dimensions iff:
     * A[ijkl...] = A[permutation(ijkl...)].
     * This implies that the bounds of the permuted dimensions need to 
     * be the same. If they are not, the tensor is not symmetric.
     * The Index passed in needs to have the same size as the rank
     * of this sparse tensor.
     *
     * Complexity: O(number of non-zeros)
     *
     * @param perm [Index] the permutation to use to evaluate whether 
     *  this sparse tensor is symmetric or not
     * @retval bool whether this sparse tensor is symmetric w.r.t. the 
     *  given permutation
     */
    inline bool isSymmetric(const Index& perm) const
    {
      {
        NTA_ASSERT(perm.size() == getRank());
        NTA_ASSERT(isSet(perm));
      }
      
      Index idx2 = getNewZeroIndex();
      
      nta::permute(perm, bounds_, idx2);
      if (bounds_ != idx2)
        return false;

      const_iterator it, e;

      for (it = begin(), e = end(); it != e; ++it) {
        nta::permute(perm, it->first, idx2);
        if (!nearlyZero_(it->second - get(idx2)))
          return false;
      }

      return true;
    }

    /**
     * Computes whether this tensor is anti-symmetric or not.
     * A tensor is anti-symmetric w.r.t. to a permutation of the 
     * dimensions iff:
     * A[ijkl...] = -A[permutation(ijkl...)]
     * This implies that the upper bounds of the permuted dimensions
     * need to be the same, or the tensor is not anti-symmetric.
     * The Index passed in needs to have the same size as the rank
     * of this sparse tensor.
     *
     * Complexity: O(number of non-zeros)
     *
     * @param perm [Index] the permutation to use to evaluate anti-symmetry
     * @retval bool whether this sparse tensor is anty-symmetric w.r.t.
     *  the given permutation or not
     */
    inline bool isAntiSymmetric(const Index& perm) const
    {
      {
        NTA_ASSERT(perm.size() == getRank());
        NTA_ASSERT(isSet(perm));
      }

      Index idx2 = getNewZeroIndex();
      
      nta::permute(perm, bounds_, idx2);
      if (bounds_ != idx2)
        return false;

      const_iterator it, e;

      for (it = begin(), e = end(); it != e; ++it) {
        nta::permute(perm, it->first, idx2);
        if (!nearlyZero_(it->second + get(idx2)))
          return false;
      }

      return true;
    }
  
    /**
     * Sets the element at idx to val. Handles zeros by not storing
     * them, or by erasing non-zeros that become zeros when val = 0.
     * The Index idx needs to be >= 0 and < getBounds().
     *
     * Complexity: O(log(number of non-zeros))
     *
     * @param idx [Index] the index of the element to set
     * @param val [Float] the value to set for the element at index
     */
    inline void set(const Index& idx, const Float& val)
    {
      {
        NTA_ASSERT(positiveInBounds(idx, getBounds()))
          << "SparseTensor::set(idx, val): "
          << "Invalid index: " << idx
          << " - Should be >= 0 and strictly less than: " << bounds_;
      }
    
      if (nearlyZero_(val)) {
        iterator it = nz_.find(idx);
        if (it != end()) 
          nz_.erase(it);
      } else 
        nz_[idx] = val;
    }

    /**
     * Sets the element at idx to val. Calls set(Index, Float).
     */
    inline void set(UInt i0, ...)
    {
      Index idx = getNewIndex();
      idx[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        idx[k] = (UInt) va_arg(indices, unsigned int); 
      const Float val = (Float) va_arg(indices, double);
      va_end(indices);
      set(idx, val);
    }

    /**
     * Sets all the elements inside the dom to val.
     * Handles zeros correctly (i.e. does not store them).
     *
     * @param dom [Domain<UInt>] the domain inside which to set values
     * @param val [Float] the value to set inside dom
     */
    inline void set(const Domain<UInt>& dom, const Float& val)
    {
      if (nearlyZero_(val)) {
        setZero(dom);
      } else {
        setNonZero(dom, val);
      }
    }

    /**
     * Sets the element at idx to zero, that is, removes it 
     * from the internal storage.
     *
     * Complexity: O(log(number of non-zeros))
     *
     * @param idx [Index] the index of the element to set to zero
     */
    inline void setZero(const Index& idx)
    {
      {
        NTA_ASSERT(positiveInBounds(idx, getBounds()))
          << "SparseTensor::setZero(idx): "
          << "Invalid index: " << idx
          << " - Should be >= 0 and strictly less than: " << bounds_;
      }
    
      iterator it = nz_.find(idx);
      if (it != end()) 
        nz_.erase(it);
    }

    /**
     * Sets the element at idx to zero. Calls setZero(Index).
     */
    inline void setZero(UInt i0, ...)
    {
      Index idx = getNewIndex();
      idx[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        idx[k] = (UInt) va_arg(indices, unsigned int); 
      va_end(indices);
      setZero(idx);
    }

    /**
     * Sets to zero all the elements in Domain dom.
     *
     * @param dom [Domain<UInt>] the domain to set to zero
     */
    inline void setZero(const Domain<UInt>& dom)
    {
      {
        NTA_ASSERT(getDomain().includes(dom))
          << "SparseTensor::setZero(Domain): "
          << "Domain argument: " << dom
          << " is invalid"
          << " - Should be included in: " << getDomain();
      }

      iterator it = begin(), d, e = end();
      while (it != e) {
        if (dom.includes(it->first)) {
          d = it;
          ++it; // increment before erase
          nz_.erase(d);
        } else {
          ++it;
        }
      }
    }

    /**
     * Sets element at idx to val, where |val| > nta::Epsilon.
     * 
     * Use if you know what you do: even f(non-zero, non-zero)
     * can be "zero", if it falls below nta::Epsilon. 
     *
     * Complexity: O(log(number of non-zeros))
     *
     * @param idx [Index] the index of the element to set to val
     * @param val [Float] the value to set for the element at idx
     */
    inline void setNonZero(const Index& idx, const Float& val)
    {
      {
        NTA_ASSERT(positiveInBounds(idx, getBounds()))
          << "SparseTensor::setNonZero(idx, val): "
          << "Invalid index: " << idx
          << " - Should be >= 0 and strictly less than: " << bounds_;

        NTA_ASSERT(!nearlyZero_(val))
          << "SparseTensor::setNonZero(idx, val): "
          << "Invalid zero value: " << val
          << " at index: " << idx
          << " - Should be non-zero (> " << nta::Epsilon << ")";
      }
    
      nz_[idx] = val;
    }

    /**
     * Sets all the values inside dom to val.
     * Works only if |val| > nta::Epsilon. 
     * 
     * @param dom [Domain<UInt>] the domain inside which to set values
     * @param val [Float] the value to set inside dom
     */
    inline void setNonZero(const Domain<UInt>& dom, const Float& val)
    {
      {
        NTA_ASSERT(!nearlyZero_(val));
      }

      Index lb = getNewIndex(), ub = getNewIndex(), idx = getNewIndex();
      dom.getLB(lb); dom.getUB(ub);
      
      idx = lb;
      do {
        setNonZero(idx, val);
      } while (increment(lb, ub, idx));
    }

    /**
     * Updates the value of this tensor at idx in place, using f and val:
     * A[idx] = f(A[idx], val) (val as second argument).
     *
     * Handles zeros properly.
     *
     * Complexity: O(log(number of non-zeros))
     */
    template <typename binary_functor>
    inline Float update(const Index& idx, const Float& val, binary_functor f)
    {
      {
        NTA_ASSERT(positiveInBounds(idx, getBounds()))
          << "SparseTensor::update(idx, val, f(x, y)): "
          << "Invalid index: " << idx
          << " - Should be >= 0 and strictly less than: " << bounds_;
      }
      
      Float res = 0;

      iterator it = nz_.find(idx);
      if (it != end()) {
        res = f(it->second, val);
        if (nearlyZero_(res)) 
          nz_.erase(it);
        else
          it->second = res;
      }
      else {
        res = f(0, val);
        if (!nearlyZero_(res))
          nz_[idx] = res;
      }
      
      return res;
    }

    /**
     * TODO: unit test
     */
    inline void add(const Index& idx, const Float& val)
    {
      std::pair<iterator, bool> r = nz_.insert(std::make_pair(idx, val));

      if (!r.second) 
        r.first->second += val;
    }

    /**
     * Sets all the values in this tensor to val. 
     * Makes this sparse tensor dense if |val| > nta::Epsilon.
     * Otherwise, removes all the values in this sparse tensor
     *
     * Complexity: O(product of bounds) (worst case, if |val| > nta::Epsilon)
     */
    inline void setAll(const Float& val)
    {
      if (nearlyZero_(val)) {
        nz_.clear();
        return;
      }

      Index idx = getNewZeroIndex();
      do {
        nz_[idx] = val;
      } while (increment(bounds_, idx));
    }

    /**
     * Returns the value of the element at idx.
     *
     * Complexity: O(log(number of non-zeros))
     */
    inline Float get(const Index& idx) const
    {
      {     
        NTA_ASSERT(positiveInBounds(idx, getBounds()))
          << "SparseTensor::get(idx): "
          << "Invalid index: " << idx
          << " - Should be >= 0 and strictly less than: " << bounds_;
      }

      const_iterator it = nz_.find(idx);
      if (it != nz_.end())
        return it->second;
      else
        return Float(0);
    }

    /**
     * Returns the value of the element at idx.
     * Calls get(Index).
     */
    inline const Float get(UInt i0, ...)
    {
      Index idx = getNewIndex();
      idx[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        idx[k] = (UInt) va_arg(indices, unsigned int); 
      va_end(indices);
      return get(idx);
    }

    /**
     * Returns the element at idx.
     * Calls get(Index).
     * not providing the other one, because we need to control for zero,
     * we can't just blindly pass a reference
     */
    inline const Float operator()(UInt i0, ...) const
    {
      Index idx = getNewIndex();
      idx[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        idx[k] = (UInt) va_arg(indices, unsigned int); 
      va_end(indices);
      return get(idx);
    }

    /**
     * Extract sub-spaces along dimension dim, and put result
     * in B. Only the non-zeros who dim-th coordinate is in ind
     * are kept and stored in B.
     *
     * This operation reduces the size of this SparseTensor
     * along dimension dim to the number of elements in ind.
     * This operation reduces the size of this SparseTensor
     * along dimension dim to the number of elements in ind.
     * If ind is full, returns this SparseTensor unmodified.
     * If ind is empty, throws an exception, because I can't
     * reduce a SparseTensor to have a size along any dimension
     * of zero. You need to detect that ind is empty before 
     * calling reduce. 
     *
     * Returns the null tensor (not a tensor) if ind is empty,
     * i.e. 
     *
     * dim = 0 indicates that some rows will be removed... 
     */
    inline void extract(UInt dim, const std::set<UInt>& ind, SparseTensor& B) const
    {
      {
        NTA_ASSERT(&B != this)
          << "SparseTensor::extract(): "
          << "Cannot extract to self";

        NTA_ASSERT(0 <= dim && dim < getRank())
          << "SparseTensor::extract(): "
          << "Invalid dimension: " << dim
          << " - Should be between 0 and rank = " << getRank();

        typename std::set<UInt>::const_iterator i, e;
        for (i = ind.begin(), e = ind.end(); i != e; ++i)
          NTA_ASSERT(0 <= *i && *i < getBound(dim))
            << "SparseTensor::extract(): "
            << "Invalid set member: " << *i
            << " - Should be between 0 and bound (" << getBound(dim)
            << ") for dim: " << dim;
      }
      
      if (ind.empty())  {
        B.bounds_[dim] = 0;
        return;
      }

      if (ind.size() == getBound(dim)) {
        B = *this;
        return;
      }

      B.clear();
      Index bounds = getNewIndex();
      bounds[dim] = (UInt)ind.size();
      B.resize(bounds);

      std::vector<UInt> ind_v(getBound(dim));
      {
        UInt j = 0;
        typename std::set<UInt>::const_iterator i, e;
        for (j = 0, i = ind.begin(), e = ind.end(); i != e; ++i, ++j)
          ind_v[*i] = j;
      }

      const_iterator i, e;
      for (i = begin(), e = end(); i != e; ++i) 
        if (ind.find(i->first[dim]) != ind.end()) {
          Index idx = i->first;
          idx[dim] = ind_v[idx[dim]]; 
          B.setNonZero(idx, i->second);
        }
    }

    /**
     * In place (mutating) reduce.
     *
     * Keeps only the sub-spaces (rows or columns for a matrix)
     * whose coordinate is a member of ind. Reduces the size
     * of the tensor along dimension dim to the size of ind. 
     * Yields the null tensor if ind is empty.
     * Does not change the tensor if ind is full. 
     *
     * Examples:
     * S2.reduce(0, set(1, 3)) keeps rows 1 and 3 of the matrix,
     *  eliminates the other rows.
     * S2.reduce(1, set(1, 3)) keeps columns 1 and 3 of the matrix,
     *  eliminates the other columns.
     */
    inline void reduce(UInt dim, const std::set<UInt>& ind)
    {
      {
        NTA_ASSERT(0 <= dim && dim < getRank())
          << "SparseTensor::reduce(): "
          << "Invalid dimension: " << dim
          << " - Should be between 0 and rank = " << getRank();

        typename std::set<UInt>::const_iterator i, e;
        for (i = ind.begin(), e = ind.end(); i != e; ++i)
          NTA_ASSERT(0 <= *i && *i < getBound(dim))
            << "SparseTensor::reduce(): "
            << "Invalid set member: " << *i
            << " - Should be between 0 and bound (" << getBound(dim)
            << ") for dim: " << dim;
      }

      if (ind.empty()) {
        bounds_[dim] = 0;
        return;
      }
      
      if (ind.size() == getBound(dim))
        return;

      std::vector<UInt> ind_v(getBound(dim));
      {
        UInt j = 0;
        typename std::set<UInt>::const_iterator i, e;
        for (j = 0, i = ind.begin(), e = ind.end(); i != e; ++i, ++j)
          ind_v[*i] = j;
      }
      
      NZ keep;

      iterator i, e;
      for (i = begin(), e = end(); i != e; ++i) 
        if (ind.find(i->first[dim]) != ind.end()) {
          Index idx = i->first;
          idx[dim] = ind_v[idx[dim]]; 
          keep[idx] = i->second;
        }

      nz_ = keep;

      Index bounds = getNewIndex();
      bounds[dim] = (UInt)ind.size();
      resize(bounds);
    }

    /**
     * Extract slices or sub-arrays from this tensor, of 
     * any dimensions, and within any bounds. Slices can be 
     * of any dimension <= getRank(). Slices are not allocated
     * by this function, so an optional clearYesNo parameter
     * is provided to remove all the existing non-zeros from
     * the slice (B). When the range is not as big as the 
     * cartesian product of the bounds of this tensor, 
     * a sub-array tensor is extracted.
     *
     * Examples:
     * If A has dimensions [(0, 10), (0, 20), (0, 30)]
     * - slice with Domain = ((0, 0, 0), (10, 20, 30)) gives A
     * - slice with Domain = ((0, 0, 10), (10, 20, 30)) gives 
     *   the subarray of A reduced to indices 10 to 29 along 
     *   the third dimension
     * - slice with Domain = ((0, 0, 10), (10, 20, 10)) gives
     *   the matrix (0,10) by (0, 20) obtained when the third index
     *   is blocked to 10.
     *
     * Complexity: O(number of non-zeros in slice)
     *
     * @param range [Domain<UInt>] the range to extract from this 
     *  tensor.
     * @param B [SparseTensor<IndexB, Float>] the resulting 
     *  slice
     * @param clearYesNo [bool] whether to clear B before 
     *  slicing or not
     */
    template <typename IndexB>
    inline void getSlice(const Domain<UInt>& range, 
                         SparseTensor<IndexB, Float>& B) const
    {
      { 
        NTA_ASSERT(range.rank() == getRank());
        
        NTA_ASSERT(B.getRank() == range.getNOpenDims())
          << "SparseTensor::slice(): "
          << "Invalid range: " << range
          << " - Range should have a number of open dims"
          << " equal to the rank of the slice ("
          << B.getRank() << ")";
      }

      // Always clear, so we extract a zero slice
      // if we don't hit any non-zero
      B.clear();

      IndexB sliceIndex = B.getNewIndex(), openDims = B.getNewIndex();
      range.getOpenDims(openDims);
      const_iterator it = begin(); 
      const_iterator e = end(); 

      for (; it != e; ++it) 
        if (range.includes(it->first)) {
          project(openDims, it->first, sliceIndex);
          for (UInt k = 0; k < B.getRank(); ++k)
            sliceIndex[k] -= range[openDims[k]].getLB();
          B.set(sliceIndex, it->second);
        }
    }

    template <typename IndexB>
    inline void setSlice(const Domain<UInt>& range, 
                         const SparseTensor<IndexB, Float>& B)
    {
      { 
        NTA_ASSERT(range.rank() == getRank());
        
        NTA_ASSERT(B.getRank() == range.getNOpenDims())
          << "SparseTensor::setSlice(): "
          << "Invalid range: " << range
          << " - Range should have a number of open dims"
          << " equal to the rank of the slice ("
          << B.getRank() << ")";
      }

      // If the slice is empty, call setZero on range
      // (processing below is based on non-zeros exclusively)
      if (B.isZero()) {
        setZero(range);
        return;
      }

      Index idx = getNewIndex();
      IndexB openDims = B.getNewIndex();
      for (UInt i = 0; i < range.rank(); ++i)
        if (range[i].empty())
          idx[range[i].getDim()] = range[i].getLB();
      range.getOpenDims(openDims);
      typename SparseTensor<IndexB, Float>::const_iterator it, e;
      it = B.begin();
      e = B.end(); 

      for (; it != e; ++it)  {
        embed(openDims, it->first, idx);
        for (UInt k = 0; k < B.getRank(); ++k)
          idx[k] += range[openDims[k]].getLB();
        set(idx, it->second);
      }
    }

    template <typename OutputIterator1, typename OutputIterator2>
    inline void toList(OutputIterator1 indices, OutputIterator2 values) const
    {
      for (const_iterator it = begin(); it != end(); ++it) {
	*indices = it->first;
	*values = it->second;
	++indices; ++values;
      }
    }

    /**
     * Returns whether the element at idx is zero or not.
     * 
     * Complexity: O(log(number of non-zeros))
     */
    inline bool isZero(const Index& idx) const
    {
      {
        NTA_ASSERT(positiveInBounds(idx, getBounds()))
          << "SparseTensor::isZero(idx): "
          << "Invalid index: " << idx
          << " - Should be >= 0 and strictly less than: " << bounds_;
      }

      return nz_.find(idx) == nz_.end();
    }

    /**
     * Returns whether the element at idx is zero or not.
     * Calls isZero(Index).
     */
    inline bool isZero(UInt i0, ...) const
    {
      Index idx = getNewIndex();
      idx[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        idx[k] = (UInt) va_arg(indices, unsigned int); 
      va_end(indices);
      return isZero(idx);
    }

    /**
     * Copies this sparse tensor to the given array of Floats.
     * Sets the array to zero first, then copies only the non-zeros.
     *
     * Complexity: O(number of non-zeros)
     */
    template <typename OutIter>
    inline void toDense(OutIter array) const
    {
      {
        NTA_ASSERT(!isNull());
      }
      
      memset(array, 0, product(getBounds()) * sizeof(Float));
      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it) 
        *(array + ordinal(getBounds(), it->first)) = it->second;
    }

    /**
     * Copies the non-zeros from array into this sparse tensor.
     * Clears this tensor first if the flag is true.  
     *
     * Complexity: O(size * log(size)) ??
     */
    template <typename InIter>
    inline void fromDense(InIter array, bool clearYesNo =true)
    {
      {
        NTA_ASSERT(!isNull());
      }

      if (clearYesNo)
        clear();

      Index idx = getNewIndex();
      const UInt M = product(getBounds());
      for (UInt i = 0; i < M; ++i) {
        setFromOrdinal(bounds_, i, idx);
        set(idx, *array++);
      }
    }

    /**
     * Copies the non-zeros from this tensor to the given output iterator.
     *
     * Complexity: O(number of non-zeros)
     */
    template <typename OutIter>
    inline void toIdxVal(OutIter iv) const
    {
      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it, ++iv)
        *iv = std::make_pair(it->first, it->second);
    }

    /**
     * Copies the values from the input iterator into this sparse tensor.
     * Clear this tensor first, optionally. 
     */
    template <typename InIter>
    inline void fromIdxVal(const UInt& nz, InIter iv, bool clearYesNo =true)
    {
      if (clearYesNo)
        clear();

      for (UInt i = 0; i < nz; ++i, ++iv)
        set(iv->first, iv->second);
    } 

    /**
     * Copies the values from the input iterator into this sparse tensor,
     * assuming that only non-zeros are passed.
     * Clear this tensor first, optionally.
     */
    template <typename InIter>
    inline void fromIdxVal_nz(const UInt& nz, InIter iv, bool clearYesNo =true)
    {
      if (clearYesNo)
        clear();

      for (UInt i = 0; i < nz; ++i, ++iv)
        setNonZero(iv->first, iv->second);
    } 

    /**
     * Updates some of the values in this sparse tensor, the indices and 
     * values to use for the update being passed in the input iterator. 
     * Uses binary functor f to carry out the update. 
     */
    template <typename InIter, typename binary_functor>
    inline void updateFromIdxVal(const UInt& nz, InIter iv, binary_functor f)
    {
      for (UInt i = 0; i < nz; ++i, ++iv)
        update(iv->first, iv->second, f);
    }

    /**
     * Outputs the non-zeros of this sparse tensor to a stream.
     * Only non-zeros are put to the stream. 
     */
    inline void toStream(std::ostream& outStream) const
    {
      {
        NTA_ASSERT(outStream.good());
      }

      outStream << getRank() << "  ";

      for (UInt i = 0; i < getRank(); ++i)
        outStream << getBounds()[i] << "  ";

      outStream << getNNonZeros() << "  ";

      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it) {
        for (UInt i = 0; i < getRank(); ++i)
          outStream << (it->first)[i] << " ";
        outStream << it->second << " ";
      }
    }

    /**
     * Reads values for this sparse tensor from a stream.
     * Works even if the stream contains zeros (calls set).
     */
    inline void fromStream(std::istream& inStream)
    {
      {
        NTA_ASSERT(inStream.good());
      }
      
      clear();

      UInt rank, nnz;
      Index idx = getNewIndex();
      Float val;

      inStream >> rank;
      NTA_ASSERT(rank > 0);
      NTA_ASSERT(rank == bounds_.size());

      for (UInt i = 0 ; i < rank; ++i) {
        inStream >> bounds_[i];
        NTA_ASSERT(bounds_[i] > 0);
      }

      inStream >> nnz;
      NTA_ASSERT(nnz >= 0);

      for (UInt i = 0; i < nnz; ++i) {
        for (UInt j = 0; j < rank; ++j) {
          inStream >> idx[j];
          NTA_ASSERT(idx[j] >= 0 && idx[j] < bounds_[j]);
        }
        inStream >> val;
        set(idx, val);
      }
    }

    /**
     * Returns an iterator to the beginning of the non-zeros 
     * in this tensor. Iterator iterate only over the non-zeros.
     */
    inline iterator begin() { return nz_.begin(); }

    /**
     * Returns an iterator to one past the end of the non-zeros 
     * in this tensor. Iterator iterate only over the non-zeros.
     */
    inline iterator end() { return nz_.end(); }

    /**
     * Returns a const iterator to the beginning of the non-zeros 
     * in this tensor. Iterator iterate only over the non-zeros.
     */
    inline const_iterator begin() const { return nz_.begin(); }

    /**
     * Returns a const iterator to one past the end of the non-zeros 
     * in this tensor. Iterator iterate only over the non-zeros.
     */
    inline const_iterator end() const { return nz_.end(); }

    inline std::pair<iterator, iterator> equal_range(const Index& idx)
    {
      return nz_.equal_range(idx);
    }

    inline std::pair<const_iterator, const_iterator> 
    equal_range(const Index& idx) const
    {
      return nz_.equal_range(idx);
    }

    /**
     * Permute the dimensions of each element of this tensor.
     *
     * Complexity: O(number of non-zeros)
     */
    inline void permute(const Index& ind)
    {
      {
        NTA_ASSERT(isSet(ind));
      }

      Index idx = getNewIndex(), newBounds = getNewIndex();
      nta::permute(ind, bounds_, newBounds);

      NZ newMap;
      
      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it) {
        nta::permute(ind, it->first, idx);
        newMap[idx] = it->second;
      }

      nz_ = newMap;
      bounds_ = newBounds;
    }

    /**
     * Change the bounds of this tensor, while keeping the dimensionality.
     */
    inline void resize(const Index& newBounds)
    {
      {
        NTA_ASSERT(indexGeZero(newBounds));
      }

      if (newBounds == bounds_)
        return;

      bool shrink = false;
      ITER_1(bounds_.size())
        if (newBounds[i] < bounds_[i])
          shrink = true;

      if (shrink) {
        const_iterator it, e;
        for (it = begin(), e = end(); it != e; ++it) 
          if (!positiveInBounds(it->first, newBounds)) {
            const_iterator d = it;
            ++it;
            nz_.erase(d->first);
          }
      }

      bounds_ = newBounds;
    }

    /**
     */
    inline void resize(const UInt& dim, const UInt& newSize)
    {
      {
        NTA_ASSERT(0 <= dim && dim < getRank());
      }

      Index newBounds(getNewIndex());
      newBounds[dim] = newSize;
      resize(newBounds);
    }

    /**
     * Produces a tensor B that has the same non-zeros as this one
     * but the given dimensions (the dimensions of B). Tensor B
     * needs to provide as much storage as this sparse tensor.
     * 
     * Complexity: O(number of non-zeros)
     *
     * @parameter B [SparseTensor<IndexB, Float>] the target
     *  sparse tensor
     */
    template <typename IndexB>
    inline void reshape(SparseTensor<IndexB, Float>& B) const
    {
      {
        NTA_ASSERT(indexGtZero(B.getBounds()));
        NTA_ASSERT(!isNull());
        NTA_ASSERT(product(B.getBounds()) == product(getBounds()));
        NTA_ASSERT((void*)&B != (void*)this);
      }

      B.clear();

      IndexB newBounds = B.getBounds(), idx2 = B.getNewIndex();

      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it) {
        setFromOrdinal(newBounds, ordinal(getBounds(), it->first), idx2);
        B.setNonZero(idx2, it->second);
      } 
    }

    /**
     * A small class to carry information about two non-zeros 
     * in an intersection or union or sparse tensors of arbitraty
     * (possibly different) ranks. If the ranks are different,
     * IndexA and IndexB will have different sizes.
     */
    template <typename IndexA, typename IndexB>
    class Elt
    {
    public:
      inline Elt(const IndexA& ia, const Float a, const IndexB& ib, const Float b)
        : index_a_(ia), index_b_(ib), a_(a), b_(b)
      {}

      inline Elt(const Elt& o)
        : index_a_(o.index_a_), index_b_(o.index_b_), a_(o.a_), b_(o.b_)
      {}

      inline Elt& operator=(const Elt& o) 
      {
        index_a_ = o.index_a_; index_b_ = o.index_b_;
        a_ = o.a_; b_ = o.b_;
        return *this;
      }

      inline const IndexA getIndexA() const { return index_a_; }
      inline const IndexB getIndexB() const { return index_b_; }
      inline const Float getValA() const { return a_; }
      inline const Float getValB() const { return b_; }

      inline std::ostream& print(std::ostream& outStream) const 
      {
        return outStream << getIndexA() << " " << getValA() << " "
                         << getIndexB() << " " << getValB();
      }

    private:
      IndexA index_a_;
      IndexB index_b_;
      Float a_, b_;
    };

    /**
     * A data structure to hold the non-zero intersection of two tensors
     * of different dimensionalities.
     */
    template <typename IndexA, typename IndexB>
    struct NonZeros : public std::vector<Elt<IndexA, IndexB> >
    {};

    /**
     * Computes the set of indices where this tensor and B have
     * common non-zeros, when A and B have the same rank.
     *
     * Complexity: O(smaller number of non-zeros between this and B)
     */
    inline void nz_intersection(const SparseTensor& B, std::vector<Index>& inter) const
    {
      inter.clear();

      const_iterator it1 = begin(), end1 = end();
      const_iterator it2 = B.begin(), end2 = B.end();
      
      while (it1 != end1 && it2 != end2) { 
        if (it1->first == it2->first) {
          inter.push_back(it1->first); 
          ++it1; ++it2;
        } else if (it2->first < it1->first) {
          ++it2;
        } else {
          ++it1;
        }
      }
    } 
    
    /**
     * Computes the set of indices where the projection of this tensor
     * on dims and B have common non-zeros. A and B have different Ranks.
     *
     * Complexity: O(number of non-zeros)
     */
    template <typename IndexB>
    inline void nz_intersection(const IndexB& dims,
                                const SparseTensor<IndexB, Float>& B,
                                NonZeros<Index, IndexB>& inter) const
    {
      {
        NTA_ASSERT(B.getRank() <= getRank())
          << "SparseTensor::nz_intersection(): "
          << "Invalid tensor ranks: " << getRank()
          << "  " << B.getRank()
          << " - Tensor B's rank needs to be <= this rank: " << getRank();
      }

      inter.clear();

      const_iterator it1, end1;
      IndexB idxB = B.getNewIndex();
      
      for (it1 = begin(), end1 = end(); it1 != end1; ++it1) {
        project(dims, it1->first, idxB);
        Float b = B.get(idxB);
        if (!nearlyZero_(b)) 
          inter.push_back(Elt<Index, IndexB>(it1->first, it1->second, idxB, b));
      }
    }

    /**
     * Computes the set of indices where this tensor or B have
     * a non-zero.
     *
     * Complexity: O(sum of number of non-zeros in this and B)
     */
    inline void nz_union(const SparseTensor& B, std::vector<Index>& u) const
    {
      u.clear();
      
      const_iterator it1 = begin(), end1 = end();
      const_iterator it2 = B.begin(), end2 = B.end();
      
      while (it1 != end1 && it2 != end2) { 
        if (it1->first == it2->first) {
          u.push_back(it1->first); 
          ++it1; ++it2;
        } else if (it2->first < it1->first) {
          u.push_back(it2->first);
          ++it2;
        } else {
          u.push_back(it1->first);
          ++it1;
        }
      }

      for (; it1 != end1; ++it1)
        u.push_back(it1->first);
      
      for (; it2 != end2; ++it2)
        u.push_back(it2->first);
    } 

    /**
     * Computes the set of indices where the projection of this tensor
     * on dims and B have at least one non-zero.
     *
     * Complexity: O(product of bounds)
     *
     * Note: wish I could find a faster way to compute that union
     */
    template <typename IndexB>
    inline void nz_union(const IndexB& dims,
                         const SparseTensor<IndexB, Float>& B,
                         NonZeros<Index, IndexB>& u) const
    {
      {
        NTA_ASSERT(B.getRank() <= getRank())
          << "SparseTensor::nz_union(): "
          << "Invalid tensor ranks: " << getRank() 
          << "  " << B.getRank()
          << " - Tensor B's rank needs to be <= this rank: " << getRank();
      }

      u.clear();

      Index idxa = getNewZeroIndex();
      IndexB idxb = B.getNewIndex();
      
      do {
        project(dims, idxa, idxb);
        Float a = get(idxa), b = B.get(idxb);
        if (! nearlyZero_(a) || ! nearlyZero_(b)) 
          u.push_back(Elt<Index, IndexB>(idxa, a, idxb, b));
      } while (increment(bounds_, idxa));
    }
   
    /**
     * Applies the unary functor f to each non-zero element
     * in this sparse tensor, assuming that no new non-zero
     * is introduced. This works for scaling, for example, if 
     * the scaling value is not zero.
     *
     * @WARNING: this is pretty dangerous, since it doesn't 
     * check that f introduces new zeros!!! 
     */
    template <typename unary_function>
    inline void element_apply_nz(unary_function f)
    {
      {
        NTA_ASSERT(f(0) == 0);
        NTA_ASSERT(f(1) != 0);
        NTA_ASSERT(f(2) != 0);
      }

      iterator i, e;
      for (i = begin(), e = end(); i != e; ++i)
        i->second = f(i->second);
    }

    /**
     * Applies the unary functor f to each non-zero element 
     * in this tensor:
     * 
     * A[i] = f(A[i]), with f(0) == 0.
     *
     * Assumes (and checks) that f(0) == 0. The non-zeros 
     * can change. New non-zeros can be introduced, but this
     * function iterates on the non-zeros only.
     */
    template <typename unary_function>
    inline void element_apply_fast(unary_function f)
    {
      {
        NTA_ASSERT(f(0) == 0)
          << "SparseTensor::element_apply(unary_functor): "
          << "Binary functor should do: f(0) == 0";
      }

      // Can introduce new zeros! if we know nothing about 
      // the functor      

      iterator it, d, e;
      it = begin(); e = end();
      while (it != e) {
        Float val = f(it->second);
        if (nearlyZero_(val)) { // check zero _after_ applying functor
          d = it;
          ++it; // increment before erasing!
          nz_.erase(d);
        }
        else {
          it->second = val;
          ++it;
        }
      }
    }   

    /**
     * Applies the unary functor f to all elements in this tensor,
     * as if it were a dense tensor. This is useful when f(0) != 0, but it is 
     * slow because it doesn't take advantage of the sparsity.
     *
     * A[i] = f(A[i])
     *
     * Complexity: O(product of the bounds)
     */
    template <typename unary_functor>
    inline void element_apply(unary_functor f)
    {
      Index idx = getNewZeroIndex();
      do {
        // Writing it that way allows to use boost::lambda expressions
        // for f, which is really, really convenient
        Float val = get(idx);
        val = f(val);
        set(idx, val); // doesn't invalidate iterator
      } while (increment(bounds_, idx));
    }

    /**
     * Applies the binary functor f to couple of elements from this tensor
     * and tensor B, at the same element, where no element of the couple is zero. 
     * The result is stored in tensor C. 
     *
     * C[i] = f(A[i], B[i]), where A[i] != 0 AND B[i] != 0.
     *
     * This works for f = multiplication, where f(x, 0) == f(0, x) == 0, for all x. 
     * It doesn't work for addition.
     *
     * Complexity: O(smaller number of non-zeros between this and B)
     */
    template <typename binary_functor>
    inline void element_apply_fast(const SparseTensor& B, SparseTensor& C, 
                                   binary_functor f, bool clearYesNo =true) const
    {
      {
        NTA_ASSERT(getBounds() == B.getBounds())
          << "SparseTensor::element_apply_fast(): "
          << "A and B have different bounds: "
          << getBounds() << " and " << B.getBounds()
          << " - Bounds need to be the same";

        NTA_ASSERT(getBounds() == C.getBounds())
          << "SparseTensor::element_apply_fast(): "
          << "A and C have different bounds: "
          << getBounds() << " and " << C.getBounds()
          << " - Bounds need to be the same";

        NTA_ASSERT(f(0, 1) == 0 && f(1, 0) == 0 && f(0, 0) == 0)
          << "SparseTensor::element_apply_fast(): "
          << "Binary functor should do: f(x, 0) == f(0, x) == 0 for all x";
      }

      if (clearYesNo)
        C.clear();

      const_iterator it1, end1, it2, end2;
      it1 = begin(); end1 = end();
      it2 = B.begin(); end2 = B.end();

      while (it1 != end1 && it2 != end2) 
        if (it1->first == it2->first) {
          C.set(it1->first, f(it1->second, it2->second));
          ++it1; ++it2;
        } else if (it2->first < it1->first) {
          ++it2;
        } else {
          ++it1;
        }
    }

    /**
     * Applies the binary functor f to couple of elements from this tensor
     * and tensor B, at the same index, assuming that f(0, 0) == 0.
     * The result is stored in tensor C. 
     *
     * C[i] = f(A[i], B[i]), where A[i] != 0 OR B[i] != 0
     *
     * This works for f = multiplication, and f = addition.
     * It does not work if f(0, 0) != 0.
     *
     * Complexity: O(sum of number of non-zeros between this and B)
     */
    template <typename binary_functor>
    inline void element_apply_nz(const SparseTensor& B, SparseTensor& C, 
                                 binary_functor f, bool clearYesNo =true) const
    {
      {
        NTA_ASSERT(getBounds() == B.getBounds())
          << "SparseTensor::element_apply_nz(): "
          << "A and B have different bounds: "
          << getBounds() << " and " << B.getBounds()
          << " - Bounds need to be the same";

        NTA_ASSERT(getBounds() == C.getBounds())
          << "SparseTensor::element_apply_nz(): "
          << "A and C have different bounds: "
          << getBounds() << " and " << C.getBounds()
          << " - Bounds need to be the same";

        NTA_ASSERT(f(0, 0) == 0)
          << "SparseTensor::element_apply_nz(): "
          << "Binary functor should do: f(0, 0) == 0";
      }

      if (clearYesNo)
        C.clear();

      const_iterator 
        it1 = begin(), it2 = B.begin(), 
        end1 = end(), end2 = B.end();

      // Any of the set() can introduce new zeros!
      while (it1 != end1 && it2 != end2) 
        if (it1->first == it2->first) {
          C.set(it1->first, f(it1->second, it2->second));
          ++it1; ++it2;
        } else if (it2->first < it1->first) {
          C.set(it2->first, f(0, it2->second));
          ++it2;
        } else {
          C.set(it1->first, f(it1->second, 0));
          ++it1;
        }
    
      for (; it1 != end1; ++it1)
        C.set(it1->first, f(it1->second, 0));

      for (; it2 != end2; ++it2)
        C.set(it2->first, f(0, it2->second));
    }

    /**
     * Applies the binary functor f to couple of elements from this tensor
     * and tensor B, at the same index, without assuming anything on f.
     * The result is stored in tensor C. 
     *
     * C[i] = f(A[i], B[i])
     *
     * This works in all cases, even if f(0, 0) != 0. It does not take
     * advantage of the sparsity.
     *
     * Complexity: O(product of the bounds)
     */
    template <typename binary_functor>
    inline void element_apply(const SparseTensor& B, SparseTensor& C, 
                              binary_functor f) const
    {
      {
        NTA_ASSERT(getBounds() == B.getBounds())
          << "SparseTensor::element_apply(): "
          << "A and B have different bounds: "
          << getBounds() << " and " << B.getBounds()
          << " - Bounds need to be the same";

        NTA_ASSERT(getBounds() == C.getBounds())
          << "SparseTensor::element_apply(): "
          << "A and C have different bounds: "
          << getBounds() << " and " << C.getBounds()
          << " - Bounds need to be the same";
      }

      Index idx = getNewZeroIndex();
      do {
        C.set(idx, f(get(idx), B.get(idx)));
      } while (increment(bounds_, idx));
    }

    /**
     * In place factor apply (mutating)
     *
     * A[i] = f(A[i], B[j]), 
     *  where j = projection of i on dims, 
     *  and A[i] != 0 AND B[j] != 0.
     *
     * This works for multiplication, but not for addition, and not if f(0, 0) == 0.
     *
     * Complexity: O(smaller number of non-zeros between this and B)
     */
    template <typename IndexB, typename binary_functor>
    inline void factor_apply_fast(const IndexB& dims, 
                                  const SparseTensor<IndexB, Float>& B,
                                  binary_functor f) 
    {
      {
        NTA_ASSERT(getRank() > 1)
          << "SparseTensor::factor_apply_fast() (in place): "
          << "A rank is: " << getRank()
          << " - Should be > 1";

        NTA_ASSERT(B.getRank() >= 1)
          << "SparseTensor::factor_apply_fast() (in place): "
          << "B rank is: " << B.getRank()
          << " - Should be >= 1";

        NTA_ASSERT(B.getRank() <= getRank())
          << "SparseTensor::factor_apply_fast() (in place): "
          << "A rank is: " << getRank()
          << " B rank is: " << B.getRank()
          << " - B rank should <= A rank";
      }

      NonZeros<Index, IndexB> inter;
      nz_intersection(dims, B, inter);

      // Need to clear everything so that zeros are handled properly, 
      // but we have all the values of this tensor in the intersection...
      clear();
      
      // We have to call set instead of setNonZero, because
      // even the multiplication of two non-zeros can result
      // in a "zero" from the point of view of SparseMatrix
      // that is, a value such that |value| <= nta::Epsilon
      typename NonZeros<Index, IndexB>::const_iterator it, e;
      for (it = inter.begin(), e = inter.end(); it != e; ++it)
        set(it->getIndexA(), f(it->getValA(), it->getValB()));
    }

    /**
     * In place factor apply on non-zeros (mutating).
     * Works for addition and multiplication.
     */
    template <typename IndexB, typename binary_functor>
    inline void factor_apply_nz(const IndexB& dims,
                                const SparseTensor<IndexB, Float>& B, 
                                binary_functor f) 
    {
      {
        NTA_ASSERT(getRank() > 1)
          << "SparseTensor::factor_apply_nz(): "
          << "A rank is: " << getRank()
          << " - Should be > 1";

        NTA_ASSERT(B.getRank() >= 1)
          << "SparseTensor::factor_apply_nz(): "
          << "B rank is: " << B.getRank()
          << " - Should be >= 1";

        NTA_ASSERT(B.getRank() <= getRank())
          << "SparseTensor::factor_apply_nz(): "
          << "A rank is: " << getRank()
          << " B rank is: " << B.getRank()
          << " - B rank should <= A rank";

        NTA_ASSERT(f(0, 0) == 0)
          << "SparseTensor::factor_apply_nz(): "
          << "Binary functor should do: f(0, 0) == 0";
      }

      // This is unfortunately quite slow, because projection
      // is a surjection...
      NonZeros<Index, IndexB> u;
      nz_union(dims, B, u);

      // Calling set because f(a, b) can fall below nta::Epsilon
      typename NonZeros<Index, IndexB>::const_iterator it, e;
      for (it = u.begin(), e = u.end(); it != e; ++it) 
        set(it->getIndexA(), f(it->getValA(), it->getValB()));
    }

    /**
     * Binary factor apply (non-mutating)
     *
     * C[i] = f(A[i], B[j]), 
     *  where j = projection of i on dims, 
     *  and A[i] != 0 AND B[j] != 0.
     *
     * This works for multiplication, but not for addition, and not if f(0, 0) == 0.
     *
     * Complexity: O(smaller number of non-zeros between this and B)
     */
    template <typename IndexB, typename binary_functor>
    inline void factor_apply_fast(const IndexB& dims,
                                  const SparseTensor<IndexB, Float>& B, 
                                  SparseTensor<Index, Float>& C, 
                                  binary_functor f, 
                                  bool clearYesNo =true) const
    {
      {
        NTA_ASSERT(getRank() > 1)
          << "SparseTensor::factor_apply_fast(): "
          << "A rank is: " << getRank()
          << " - Should be > 1";

        NTA_ASSERT(B.getRank() >= 1)
          << "SparseTensor::factor_apply_fast(): "
          << "B rank is: " << B.getRank()
          << " - Should be >= 1";

        NTA_ASSERT(B.getRank() <= getRank())
          << "SparseTensor::factor_apply_fast(): "
          << "A rank is: " << getRank()
          << " B rank is: " << B.getRank()
          << " - B rank should <= A rank";

        NTA_ASSERT(f(0, 1) == 0 && f(1, 0) == 0 && f(0, 0) == 0)
          << "SparseTensor::factor_apply_fast(): "
          << "Binary functor should do: f(0, x) == f(x, 0) == 0 for all x";
      }

      if (clearYesNo)
        C.clear();

      NonZeros<Index, IndexB> inter;
      nz_intersection(dims, B, inter);
      
      // Calling set because f(a, b) can fall below nta::Epsilon
      typename NonZeros<Index, IndexB>::const_iterator it, e;
      for (it = inter.begin(), e = inter.end(); it != e; ++it) 
        C.set(it->getIndexA(), f(it->getValA(), it->getValB()));
    }

    /**
     * C[i] = f(A[i], B[j]), 
     *  where j = projection of i on dims, 
     *  and A[i] != 0 OR B[j] != 0.
     *
     * This works for addition, but not if f(0, 0) != 0.
     *
     * Complexity: O(sum of number of non-zeros between this and B)
     */
    template <typename IndexB, typename binary_functor>
    inline void factor_apply_nz(const IndexB& dims,
                                const SparseTensor<IndexB, Float>& B, 
                                SparseTensor<Index, Float>& C, 
                                binary_functor f,
                                bool clearYesNo =true) const
    {
      {
        NTA_ASSERT(getRank() > 1)
          << "SparseTensor::factor_apply_nz(): "
          << "A rank is: " << getRank()
          << " - Should be > 1";

        NTA_ASSERT(B.getRank() >= 1)
          << "SparseTensor::factor_apply_nz(): "
          << "B rank is: " << B.getRank()
          << " - Should be >= 1";

        NTA_ASSERT(B.getRank() <= getRank())
          << "SparseTensor::factor_apply_nz(): "
          << "A rank is: " << getRank()
          << " B rank is: " << B.getRank()
          << " - B rank should <= A rank";

        NTA_ASSERT(&C != this)
          << "SparseTensor::factor_apply_nz(): "
          << "Can't store result in A";

        NTA_ASSERT(f(0, 0) == 0)
          << "SparseTensor::factor_apply_nz(): "
          << "Binary functor should do: f(0, 0) == 0";
      }

      if (clearYesNo)
        C.clear();

      // This is unfortunately quite slow, because projection
      // is a surjection...
      NonZeros<Index, IndexB> u;
      nz_union(dims, B, u);

      // Calling set because f(a, b) can fall below nta::Epsilon
      typename NonZeros<Index, IndexB>::const_iterator it, e;
      for (it = u.begin(), e = u.end(); it != e; ++it) 
        C.set(it->getIndexA(), f(it->getValA(), it->getValB()));
    }
    
    /**
     * C[i] = f(A[i], B[j]), 
     *  where j = projection of i on dims.
     *
     * There is no restriction on f, it works even if f(0, 0) != 0.
     * Doesn't take advantage of the sparsity.
     *
     * Complexity: O(product of bounds)
     */
    template <typename IndexB, typename binary_functor>
    inline void factor_apply(const IndexB& dims,
                             const SparseTensor<IndexB, Float>& B, 
                             SparseTensor<Index, Float>& C, 
                             binary_functor f) const
    {
      {
        NTA_ASSERT(getRank() > 1)
          << "SparseTensor::factor_apply(): "
          << "A rank is: " << getRank()
          << " - Should be > 1";

        NTA_ASSERT(B.getRank() >= 1)
          << "SparseTensor::factor_apply(): "
          << "B rank is: " << B.getRank()
          << " - Should be >= 1";

        NTA_ASSERT(B.getRank() <= getRank())
          << "SparseTensor::factor_apply(): "
          << "A rank is: " << getRank()
          << " B rank is: " << B.getRank()
          << " - B rank should <= A rank";
      }

      Index idx = getNewZeroIndex();
      IndexB idxB = B.getNewIndex();

      // Calling set because f(a, b) can fall below nta::Epsilon
      do {
        project(dims, idx, idxB);
        C.set(idx, f(get(idx), B.get(idxB)));
      } while (increment(bounds_, idx));
    }
  
    /**
     * C[j] = f(C[j], A[i]),
     *  where j = projection of i on L dims.
     * 
     * Works only on the non-zeros, assumes f(0, 0) = 0 ??
     * Use this version AND init = 1 for multiplication.
     *
     * Complexity: O(number of non-zeros)
     *
     * Examples:
     * If s2 is a 2D sparse tensor with dimensions (4, 5),
     * and s1 a 1D sparse tensor (vector), then:
     * - accumulate_nz(I1(0), s1, plus<float>(), 0)
     *  accumulates vertically, and s1 has size 5.
     * - accumulate_nz(I1(1), s1, plus<float>(), 0)
     *  accumulates horizontally, and s1 has size 4.
     */
    template <typename Index2, typename IndexB, typename binary_functor>
    inline void accumulate_nz(const Index2& dims,
                              SparseTensor<IndexB, Float>& B, 
                              binary_functor f, const Float& init =0) const
    {
      {
        NTA_ASSERT(dims.size() == getRank() - B.getRank());

        NTA_ASSERT(B.getRank() < getRank())
          << "SparseTensor::accumulate_nz(): "
          << "A rank is: " << getRank()
          << " B rank is: " << B.getRank()
          << " - B rank should <= A rank";
      }

      B.setAll(init);

      IndexB compDims = B.getNewIndex(), idxB = B.getNewIndex();
      complement(dims, compDims);
      
      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it) {
        project(compDims, it->first, idxB);
        B.update(idxB, it->second, f);
      }
    }

    /**
     * B[j] = f(B[j], A[i]),
     *  where j = projection of i on L dims.
     * 
     * Works on all the values, including the zeros, so it is
     * inappropriate for multiplication, since the zeros will
     * produce zeros in the output, even if init != 0.
     * 
     * No restriction on f, doesn't take advantage of the sparsity.
     *
     * Complexity: O(product of bounds)
     */
    template <typename Index2, typename IndexB, typename binary_functor>
    inline void accumulate(const Index2& dims,
                           SparseTensor<IndexB, Float>& B, 
                           binary_functor f, const Float& init =0) const
    {
      {
        NTA_ASSERT(dims.size() == getRank() - B.getRank());

        NTA_ASSERT(B.getRank() < getRank())
          << "SparseTensor::accumulate(): "
          << "A rank is: " << getRank()
          << " B rank is: " << B.getRank()
          << " - B rank should < A rank";
      }

      B.setAll(init);
      
      Index idx = getNewZeroIndex();
      IndexB compDims = B.getNewIndex(), idxB = B.getNewIndex();
      complement(dims, compDims);
      
      do {
        project(compDims, idx, idxB);
        B.update(idxB, get(idx), f);
      } while (increment(bounds_, idx));
    }

    /**
     * In place (mutating) normalize.
     *
     * Examples:
     * S2.normalize(I1(UInt(0))): normalize vertically
     * S2.normalize(I1(UInt(1))): normalize horizontally
     */
    template <typename Index2>
    inline void normalize(const Index2& dims)
    {
      {
        NTA_ASSERT(dims.size() < getRank())
          << "SparseTensor::normalize(Index): "
          << " - Wrong ranks";
      }

      std::vector<UInt> compDims(getRank() - dims.size());
      complement(dims, compDims);

      std::vector<UInt> compBounds(getRank() - dims.size());
      project(compDims, getBounds(), compBounds);

      SparseTensor<std::vector<UInt>, Float> C(compBounds);

      accumulate_nz(dims, C, std::plus<Float>(), 0);
      // factor_apply_fast works only on the non-zeros, so it won't attempt
      // to divide by zero!
      factor_apply_fast(compDims, C, std::divides<Float>());
    }

    /**
     * Computes the outer product of this sparse tensor and B, puts the result
     * in C:
     *
     * C[i.j] = f(A[i], B[j]).
     * Cijkpq = f(Aijk, Bpq)
     *
     * Works only the non-zeros, assumes f(0, 0) = f(x, 0) = f(0, x) = 0.
     * Works for multiplication, but not for addition.
     *
     * Complexity: O(square of total number of non-zeros)
     */
    template <typename IndexB, typename IndexC, typename binary_functor>
    inline void outer_product_nz(const SparseTensor<IndexB, Float>& B,
                                 SparseTensor<IndexC, Float>& C,
                                 binary_functor f) const
    {
      {
        NTA_ASSERT(C.getRank() == B.getRank() + getRank());
        
        NTA_ASSERT(f(0, 0) == 0)
          << "SparseTensor::outer_product_nz(): "
          << "Binary functor should do: f(0, 0) = 0";
      }
      
      C.clear();
      
      const_iterator it1, end1;
      typename SparseTensor<IndexB, Float>::const_iterator it2, end2;
      
      end1 = end(); end2 = B.end();
      
      for (it1 = begin(); it1 != end1; ++it1) 
        for (it2 = B.begin(); it2 != end2; ++it2) 
          C.set(concatenate(it1->first, it2->first), f(it1->second, it2->second));
    }
    
    /**
     * Computes the outer product of this sparse tensor and B, puts the result
     * in C:
     *
     * C[i.j] = f(A[i], B[j]).
     *
     * Doesn't assume anything on f, works in all cases, but remarkably slow.
     *
     * Complexity: O(square of product of bounds)
     */
    template <typename IndexB, typename IndexC, typename binary_functor>
    inline void outer_product(const SparseTensor<IndexB, Float>& B,
                              SparseTensor<IndexC, Float>& C,
                              binary_functor f) const
    {
      {
        NTA_ASSERT(getRank() + B.getRank() == C.getRank());
      }
      
      C.clear();
      
      Index idxA = getNewZeroIndex(), ubA = getBounds();
      IndexB idxB = B.getNewZeroIndex(), ubB = B.getBounds();
      
      do {
        setToZero(idxB);
        do {
          C.set(concatenate(idxA, idxB), f(get(idxA), B.get(idxB)));
        } while (increment(ubB, idxB));
      } while (increment(ubA, idxA));
    }
    
    /**
     * Computes the contraction of this sparse tensor along the two 
     * given dimensions:
     *
     * B[ikl...] = accumulate using f(j, A[ijkl...j...]),
     *  where j shows at positions dim1 and dim2 of A.
     * Cikq = f(Aiuk, Buq)
     *
     * Works only on the non-zeros, assumes f(0, 0) = 0 ??
     *
     * Complexity: O(number of non-zeros)
     */
    template <typename IndexB, typename binary_functor>
    inline void contract_nz(const UInt dim1, const UInt dim2,
                            SparseTensor<IndexB, Float>& B,
                            binary_functor f, const Float& init =0) const
    {
      { // Pre-conditions
        NTA_ASSERT(B.getRank() == getRank() - 2)
          << "SparseTensor::contract_nz(): "
          << "Tensor B has rank: " << B.getRank()
          << " - B needs to have rank: " << getRank() - 2;
        
        NTA_ASSERT(getRank() > 2)
          << "SparseTensor::contract_nz(): "
          << "Trying to contract tensor of rank: " << getRank()
          << " - Can contract only tensors or rank > 2";
        
        NTA_ASSERT(dim1 < getRank() && dim2 < getRank() && dim1 != dim2)
          << "SparseTensor::contract_nz(): "
          << "Trying to contract along dimensions: " << dim1 << " and " << dim2
          << " - Dimensions must be different and less than tensor rank= " 
          << getRank();
        
        NTA_ASSERT(bounds_[dim1] == bounds_[dim2])
          << "SparseTensor::contract_nz(): "
          << "Using dim: " << dim1
          << " and dim: " << dim2
          << " but they have different sizes: " << bounds_[dim1]
          << " and " << bounds_[dim2]
          << " - Can contract only dimensions that have the same size";
        
        NTA_ASSERT(f(0, 1) == 0 && f(1, 0) == 0 && f(0, 0) == 0)
          << "SparseTensor::contract_nz(): "
          << "Binary functor should do: f(0, x) == f(x, 0) == 0 for all x";
      }
      
      IndexB compDims = B.getNewIndex(), idxB = B.getNewIndex();
      std::vector<UInt> dims(2); dims[0] = dim1; dims[1] = dim2;
      complement(dims, compDims);
      
      B.clear();

      // Can't use setAll, because of if
      const_iterator it, e;
      for (it = begin(), e = end(); it != e; ++it) {
        if (it->first[dim1] == it->first[dim2]) {
          project(compDims, it->first, idxB);
          B.set(idxB, init);
        }
      }
      
      for (it = begin(), e = end(); it != e; ++it) {
        if (it->first[dim1] == it->first[dim2]) {
          project(compDims, it->first, idxB);
          B.update(idxB, it->second, f);
        }
      }
    }
                            
    /**
     * Computes the contraction of this sparse tensor along the two 
     * given dimensions:
     *
     * B[ikl...] = accumulate using f(j, A[ijkl...j...]),
     *  where j shows at positions dim1 and dim2 of A.
     *
     * No assumption on f.
     *
     * Complexity: O(product of bounds)
     */
    template <typename IndexB, typename binary_functor>
    inline void contract(const UInt dim1, const UInt dim2, 
                         SparseTensor<IndexB, Float>& B,
                         binary_functor f, const Float& init =0) const
    {
      {
        NTA_ASSERT(B.getRank() == getRank() - 2);

        NTA_ASSERT(getRank() > 2)
          << "SparseTensor::contract(): "
          << "Trying to contract tensor of rank: " << getRank()
          << " - Can contract only tensors or rank > 2";

        NTA_ASSERT(dim1 < getRank() && dim2 < getRank() && dim1 != dim2)
          << "SparseTensor::contract_nz(): "
          << "Trying to contract along dimensions: " << dim1 << " and " << dim2
          << " - Dimensions must be different and less than tensor rank: " 
          << getRank();

        NTA_ASSERT(bounds_[dim1] == bounds_[dim2])
          << "SparseTensor::contract(): "
          << "Using dim: " << dim1
          << " and dim: " << dim2
          << " but they have different size: " << bounds_[dim1]
          << " and " << bounds_[dim2]
          << " - Can contract only dimensions that have the same size";
      }
      
      Index idx = getNewZeroIndex();
      IndexB compDims = B.getNewIndex(), it2 = B.getNewIndex();
      std::vector<UInt> dims(2); dims[0] = dim1; dims[1] = dim2;
      complement(dims, compDims);
      
      B.setAll(init);

      do {
        if (idx[dim1] == idx[dim2]) {
          project(compDims, idx, it2);
          B.update(it2, get(idx), f);
        }
      } while (increment(bounds_, idx));
    }

    /**
     * Computes the inner product of this sparse tensor and B, put the result
     * in C:
     *
     * C[k] = accumulate using g(product using f of B[i], C[j])
     *
     * Works only on the non-zeros.
     *
     * Complexity: O(square of number of non-zeros in one dim)
     */
    template <typename IndexB, typename IndexC, 
              typename binary_functor1, typename binary_functor2>
    inline void inner_product_nz(const UInt dim1, const UInt dim2,
                                 const SparseTensor<IndexB, Float>& B,
                                 SparseTensor<IndexC, Float>& C,
                                 binary_functor1 f, binary_functor2 g, 
                                 const Float& init =0) const
    {
      {
        NTA_ASSERT(B.getRank() + getRank() - 2 == C.getRank());

        NTA_ASSERT(getRank() + B.getRank() > 2)
          << "SparseTensor::inner_product_nz(): "
          << "Trying to take inner product of two tensors of rank : " 
          << getRank() << " and: " << B.getRank()
          << " - But need sum of ranks > 2";

        NTA_ASSERT(dim1 < getRank())
          << "SparseTensor::inner_product_nz(): "
          << " - Dimension 1 must be less than tensor A's rank: " 
          << getRank();

        NTA_ASSERT(dim2 < B.getRank())
          << "SparseTensor::inner_product_nz(): "
          << " - Dimension 2 must be less than tensor B's rank: " 
          << B.getRank();

        NTA_ASSERT(bounds_[dim1] == B.getBounds()[dim2])
          << "SparseTensor::inner_product_nz(): "
          << "Using dim: " << dim1
          << " and dim: " << dim2
          << " but they have different size: " << bounds_[dim1]
          << " and " << B.getBounds()[dim2]
          << " - Can take inner product only along dimensions that have the same size";
      }

      std::vector<UInt>  
        pit1(getRank()-1, 0), pit2(B.getRank()-1, 0),
        d1(1, dim1), d2(1, dim2), 
        compDims1(getRank()-1), compDims2(B.getRank()-1); 
      
      complement(d1, compDims1);
      complement(d2, compDims2);

      C.clear();
      
      const_iterator it1, e1;
      typename SparseTensor<IndexB, Float>::const_iterator it2, e2;

      for (it1 = begin(), e1 = end(); it1 != e1; ++it1)
        for (it2 = B.begin(), e2 = B.end(); it2 != e2; ++it2) {
           if (it1->first[dim1] == it2->first[dim2]) {
             C.set(concatenate(pit1, pit2), init);
           }
        }

      for (it1 = begin(), e1 = end(); it1 != e1; ++it1)
        for (it2 = B.begin(), e2 = B.end(); it2 != e2; ++it2) {
           if (it1->first[dim1] == it2->first[dim2]) {
             project(compDims1, it1->first, pit1);
             project(compDims2, it2->first, pit2);
             C.update(concatenate(pit1, pit2), f(it1->second, it2->second), g);
           }
        }
    }

    /**
     * Computes the inner product of this sparse tensor and B, put the result
     * in C:
     *
     * C[k] = accumulate using g(product using f of B[i], C[j])
     * Aijk, Bpq, i, p
     * Tijkpq = f(Aijk, Bpq)
     * Cikq = g(Tiukuq)
     *
     * Complexity: O( ?? )
     */
    template <typename IndexB, typename IndexC,
              typename binary_functor1, typename binary_functor2>
    inline void inner_product(const UInt dim1, const UInt dim2,
                              const SparseTensor<IndexB, Float>& B,
                              SparseTensor<IndexC, Float>& C,
                              binary_functor1 f, binary_functor2 g, 
                              const Float& init =0) const
    {
      {
        NTA_ASSERT(getRank() + B.getRank() - 2 == C.getRank());

        NTA_ASSERT(getRank() + B.getRank() > 2)
          << "SparseTensor::inner_product(): "
          << "Trying to take inner product of two tensors of rank : " 
          << getRank() << " and: " << B.getRank()
          << " - But need sum of ranks > 2";

        NTA_ASSERT(dim1 < getRank())
          << "SparseTensor::inner_product(): "
          << " - Dimension 1 must be less than tensor A's rank: " 
          << getRank();

        NTA_ASSERT(dim2 < B.getRank())
          << "SparseTensor::inner_product(): "
          << " - Dimension 2 must be less than tensor B's rank: " 
          << B.getRank();

        NTA_ASSERT(bounds_[dim1] == B.getBounds()[dim2])
          << "SparseTensor::inner_product(): "
          << "Using dim: " << dim1
          << " and dim: " << dim2
          << " but they have different size: " << bounds_[dim1]
          << " and " << B.getBounds()[dim2]
          << " - Can take inner product only along dimensions that have the same size";
      }

      Index idx1 = getNewZeroIndex();
      IndexB idx2 = B.getNewZeroIndex();

      std::vector<UInt>  
        pit1(getRank()-1, 0), pit2(B.getRank()-1, 0),
        d1(1, dim1), d2(1, dim2), 
        compDims1(getRank()-1), compDims2(B.getRank()-1);
      
      complement(d1, compDims1);
      complement(d2, compDims2);

      C.setAll(init);

      do {
        setToZero(idx2);
        do {
          if (idx1[dim1] == idx2[dim2]) {
            project(compDims1, idx1, pit1);
            project(compDims2, idx2, pit2);
            C.update((concatenate(pit1, pit2)), f(get(idx1), B.get(idx2)), g);
          }
        } while (increment(B.getBounds(), idx2));
      } while (increment(bounds_, idx1)); 
    }

    /**
     * Another type of product.
     */
    template <typename Index1A, typename IndexB, typename IndexC,
              typename binary_functor1, typename binary_functor2>
    inline void product3(const Index1A& dimsA, const Index1A& dimsB,
                         const SparseTensor<IndexB, Float>& B,
                         SparseTensor<IndexC, Float>& C,
                         binary_functor1 f) const
    {
      {
        NTA_ASSERT(dimsA.size() == dimsB.size());
        NTA_ASSERT(dimsA.size() <= getRank());
        NTA_ASSERT(dimsB.size() <= B.getRank());
      }

      std::vector<UInt> 
        idx1a(dimsA.size()),
        bounds1A(dimsA.size()),
        lbA(getRank(), 0), 
        ubA(getBounds().begin(), getBounds().end()),
        lbB(B.getRank(), 0), 
        ubB(B.getBounds().begin(), B.getBounds().end()),
        dimsSliceA(getRank() - dimsA.size()),
        dimsSliceB(B.getRank() - dimsB.size()),
        boundsSliceA(getRank() - dimsA.size()),
        boundsSliceB(B.getRank() - dimsB.size()),
        boundsRes(boundsSliceA.size() + boundsSliceB.size());

      complement(dimsA, dimsSliceA);
      complement(dimsB, dimsSliceB);
      project(dimsA, getBounds(), bounds1A);
      project(dimsSliceA, getBounds(), boundsSliceA);
      project(dimsSliceB, B.getBounds(), boundsSliceB);
      boundsRes = concatenate(boundsSliceA, boundsSliceB);
      
      SparseTensor<std::vector<UInt>, Float> 
        sliceA(boundsSliceA), 
        sliceB(boundsSliceB),
        res(boundsRes);

      setToZero(idx1a);

      do {
        
        for (UInt k = 0; k < dimsA.size(); ++k) { // embed
          lbA[dimsA[k]] = ubA[dimsA[k]] = idx1a[k];
          lbB[dimsB[k]] = ubB[dimsB[k]] = idx1a[k];
        }

        slice(Domain<UInt>(lbA, ubA), sliceA);
        B.slice(Domain<UInt>(lbB, ubB), sliceB);
        outer_product_nz(sliceA, sliceB, res, f);

        std::vector<UInt> 
          idxRes(dimsSliceA.size() + dimsSliceB.size(), 0);
        
        do {
          IndexC idxC = C.getNewZeroIndex();
          
          embed(dimsSliceA, idxRes, idxC);
          embed(dimsSliceB, idxRes, idxC);
          embed(dimsA, idx1a, idxC);
          C.set(idxC, res.get(idxC));

        } while (increment(boundsRes, idxRes));

      } while (increment(bounds1A, idx1a));
    }
       
    /**
     * Streaming operator.
     * See print().
     */
    template <typename I, typename F>
    NTA_HIDDEN friend std::ostream& operator<<(std::ostream&, const SparseTensor<I, F>&);

    /**
     * Whether two sparse tensors are equal or not.
     * To be equal, they need to have the same number of dimensions,
     * the same size along each dimensions, and the same non-zeros.
     * Equality of floating point numbers is controlled by nta::Epsilon.
     */
    template <typename I, typename F>
    NTA_HIDDEN friend bool operator==(const SparseTensor<I, F>&, const SparseTensor<I, F>&);

    /**
     * Whether two sparse tensors are different or not.
     * See operator==.
     */
    template <typename I, typename F>
    NTA_HIDDEN friend bool operator!=(const SparseTensor<I, F>&, const SparseTensor<I, F>&);

    /**
     * Prints out this tensor to a stream.
     * There are special formats for dim 1, 2 and 3, and beyond that
     * only the non-zeros are printed out, with their indices.
     */
    inline void print(std::ostream& outStream) const
    {
      if (getRank() == 1) {
        for (UInt i = 0; i < bounds_[0]; ++i) {
          const_iterator it = nz_.find(getNewIndex(i));
          outStream << (it != end() ? it->second : 0) << " ";
        }
        outStream << std::endl;
        return;
      }

      if (getRank() == 2) {
        for (UInt i = 0; i < bounds_[0]; ++i) {
          for (UInt j = 0; j < bounds_[1]; ++j) {
            const_iterator it = nz_.find(getNewIndex(i, j));
            outStream << (it != end() ? it->second : 0) << " ";
          }
          outStream << std::endl;
        }
        return;
      } 
    
      if (getRank() == 3) {
        for (UInt i = 0; i < bounds_[0]; ++i) {
          for (UInt j = 0; j < bounds_[1]; ++j) {
            for (UInt k = 0; k < bounds_[2]; ++k) {
              const_iterator it = nz_.find(getNewIndex(i, j, k));
              outStream << (it != end() ? it->second : 0) << " ";
            }
            outStream << std::endl;
          }
          outStream << std::endl;
        }
        return;
      }

      for (const_iterator it = begin(); it != end(); ++it)
        outStream << it->first << ": " << it->second << std::endl;
    }

    //--------------------------------------------------------------------------------
    /**
     * Find the max of some sub-space of this sparse tensor.
     *
     * Complexity: O(number of non-zeros)
     * 
     * Examples:
     * If s2 is a 2D sparse tensor of size (4, 5), and s1 a 1D, then:
     * - s2.max(I1(0), s1) finds the max of each column of s2 and puts
     *   it in the corresponding element of s1. s1 has size 5.
     * - s2.max(I1(1), s1) finds the max of each row of s2 and puts it
     *   in the correspondin element of s1. s1 has size 4.
     */
    template <typename Index2, typename IndexB>
    inline void max(const Index2& dims, SparseTensor<IndexB, Float>& B) const
    {
      accumulate_nz(dims, B, nta::Max<Float>(), 0);
    }

    /**
     * Finds the max of this sparse tensor, and the index
     * of this min.
     * This funcion needed because SparseTensor doesn't 
     * specialize to a scalar properly.
     */
    inline const std::pair<Index, Float> max() const
    {
      if (isZero())
        return std::make_pair(getNewZeroIndex(), Float(0));

      const_iterator min_it = 
        std::max_element(begin(), end(), 
			 predicate_compose<std::less<Float>, 
			 nta::select2nd<std::pair<Index, Float> > >());
      
      return std::make_pair(min_it->first, min_it->second);
    }

    /**
     * Returns the sum of all the non-zeros in this sparse tensor.
     * This funcion needed because SparseTensor doesn't 
     * specialize to a scalar properly.
     */
    inline const Float sum() const
    {
      Float sum = 0;
      const_iterator i, e;
      for (i = begin(), e = end(); i != e; ++i)
        sum += i->second;
      return sum;
    }

    /**
     * Wrapper for accumulate with plus.
     */
    template <typename Index2, typename IndexB>
    inline void sum(const Index2& dims, SparseTensor<IndexB, Float>& B) const
    {
      accumulate_nz(dims, B, std::plus<Float>()); 
    }

    /**
     * Adds a slice to another.
     */
    inline void addSlice(UInt which, UInt src, UInt dst)
    {
      TensorIndex lb(getBounds()), ub(getBounds());
      lb[which] = ub[which] = src;
      TensorIndex srcIndex = getNewZeroIndex();
      srcIndex[which] = src;

      do {
	TensorIndex dstIndex(srcIndex);
	dstIndex[which] = dst;
	set(dstIndex, get(dstIndex) + get(srcIndex));
      } while (increment(lb, ub, srcIndex));
    }

    /**
     * Adds two sparse tensors of the same rank and dimensions.
     * This is an element-wise addition.
     */
    inline void axby(const Float& a, const SparseTensor& B, const Float& b,
                     SparseTensor& C) const
    {
      C.clear();

      const_iterator 
        it1 = begin(), it2 = B.begin(), 
        end1 = end(), end2 = B.end();
      
      while (it1 != end1 && it2 != end2) 
        if (it1->first == it2->first) {
          C.set(it1->first, a*it1->second + b*it2->second);
          ++it1; ++it2;
        } else if (it2->first < it1->first) {
          C.set(it2->first, b*it2->second);
          ++it2;
        } else {
          C.set(it1->first, a*it1->second);
          ++it1;
        }
      
      for (; it1 != end1; ++it1)
        C.set(it1->first, a*it1->second);
      
      for (; it2 != end2; ++it2)
        C.set(it2->first, b*it2->second);
    }

    inline void add(const SparseTensor& B)
    {
      if (B.isZero())
        return;

      element_apply_nz(B, *this, std::plus<Float>(), false);
    }

    /**
     * Scales this sparse tensor by an arbitrary scalar a.
     */
    inline void multiply(const Float& a)
    {
      if (a == 1.0)
        return;

      element_apply_fast(std::bind2nd(std::multiplies<Float>(), a));
    }

    /**
     * Scales this sparse tensor and put the result in B, leaving
     * this spare tensor unchanged.
     */
    inline void multiply(const Float& a, SparseTensor& B) const
    {
      if (a == 1.0) {
        B = *this;
        return;
      }
      
      B.clear();

      const_iterator i = begin(), e = end();
      while (i != e) {
        B.set(i->first, a * i->second);
        ++i;
      }
    }

    template <typename IndexB>
    inline void factor_multiply(const IndexB& dims,
                                const SparseTensor<IndexB, Float>& B, 
                                SparseTensor<Index, Float>& C) const
    {
      factor_apply_fast(dims, B, C, std::multiplies<Float>(), true);
    }

    template <typename IndexB, typename IndexC>
    inline void outer_multiply(const SparseTensor<IndexB, Float> B,
                               SparseTensor<IndexC, Float>& C) const
    {
      outer_product_nz(B, C, std::multiplies<Float>());
    }

    template <typename Index2, typename IndexB>
    inline void marginalize(const Index2& dims, SparseTensor<IndexB, Float>& B) const
    {
      accumulate_nz(dims, B, std::plus<Float>(), Float(0));
    }

    /**
     * Normalize by adding up the non-zeros across the whole tensor.
     * Doesn't do anything if the sum of the tensor non-zeros adds up
     * to 0. 
     */
    inline void normalize(const Float& tolerance =nta::Epsilon)
    {
      Float s = sum();
      
      if (s > tolerance)
        multiply(Real(1./s));
      else
        setAll(0.0);
    }

    //--------------------------------------------------------------------------------
  private:
    Index bounds_; 
    NZ nz_; 

    inline bool nearlyZero_(const Float& val) const 
    {
      return nearlyZero(val); 
    }

    // I need at least the bounds at construction time
    SparseTensor();

    friend class SparseTensorUnitTest;
  };

  //--------------------------------------------------------------------------------
  template <typename I, typename F>
  inline std::ostream& operator<<(std::ostream& outStream, const SparseTensor<I, F>& s)
  {
    s.print(outStream);
    return outStream;
  }

  template <typename I, typename F>
  inline bool operator==(const SparseTensor<I, F>& A, const SparseTensor<I, F>& B)
  {
    if (A.getBounds() != B.getBounds())
      return false;

    if (A.getNNonZeros() != B.getNNonZeros())
      return false;
    
    typename SparseTensor<I, F>::const_iterator it1, it2;
    for (it1 = A.begin(), it2 = B.begin(); it1 != A.end(); ++it1, ++it2)
      if (!nearlyEqual(it1->second, it2->second))
        return false;

    return true;
  }

  template <typename I, typename F>
  inline bool operator!=(const SparseTensor<I, F>& A, const SparseTensor<I, F>& B)
  {
    return ! (A == B);
  }

  //--------------------------------------------------------------------------------

} // end namespace nta

#endif // NTA_SPARSE_TENSOR_HPP


