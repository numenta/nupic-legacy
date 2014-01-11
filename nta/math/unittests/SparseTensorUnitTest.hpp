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
 * Declaration of class SparseTensorUnitTest
 */

//----------------------------------------------------------------------

#ifndef NTA_SPARSE_TENSOR_UNIT_TEST_HPP
#define NTA_SPARSE_TENSOR_UNIT_TEST_HPP

#include <nta/test/Tester.hpp>
#include <nta/math/SparseTensor.hpp>
//#include <nta/foundation/TRandom.hpp>

namespace nta {

  //--------------------------------------------------------------------------------
  /**
   * @b Responsibility
   *  A dense multi-dimensional array. It stores all its values, as opposed to 
   *  a SparseTensor that stores only the non-zero values.
   *
   * @b Rationale
   *  This class is used for unit testing. SparseTensor results are compared
   *  with DenseTensor results. Methods are usually simpler on DenseTensor. 
   */
  template <typename Index, typename Float>
  class DenseTensor
  {
  public:
    typedef Index TensorIndex;
    typedef typename Index::value_type UInt;
    typedef Float* iterator;
    typedef const Float* const_iterator;
  
    explicit inline DenseTensor(UInt ub0, ...)
      : bounds_(),
        vals_(NULL)
    {
      bounds_[0] = ub0;
      va_list indices;
      va_start(indices, ub0);
      for (UInt k = 1; k < getRank(); ++k)
        bounds_[k] = (UInt) va_arg(indices, unsigned int); 
      va_end(indices);
      vals_ = new Float[product(bounds_)];
      memset(vals_, 0, product(bounds_)*sizeof(Float));

      {
        NTA_ASSERT(indexGtZero(bounds_))
          << "DenseTensor::DenseTensor(Uint...): "
          << "Invalid bounds: " /*<< bounds_*/
          << " - They are defining a null tensor";
      }
    }

    explicit inline DenseTensor(const Index& bounds)
      : bounds_(bounds),
        vals_(new Float[product(bounds)])
    {
      memset(vals_, 0, product(bounds)*sizeof(Float));

      NTA_ASSERT(indexGtZero(bounds_))
        << "DenseTensor::DenseTensor(Index): "
        << "Invalid bounds: " << bounds_
        << " - They are defining a null tensor";
    }

    inline DenseTensor(const DenseTensor& other)
      : bounds_(other.bounds_),
        vals_(NULL)
    {
      this->operator=(other);
    }

    inline DenseTensor& operator=(const DenseTensor& other)
    {
      if (&other != this) {
        bounds_ = other.bounds_;
        const UInt M = product(bounds_);
        delete[] vals_;
        vals_ = new Float[M * sizeof(Float)];
        for (UInt i = 0; i < M; ++i)
          vals_[i] = other.vals_[i];
      }

      return *this;
    }

    ~DenseTensor()
    {
      delete [] vals_;
    }

    inline iterator begin() { return vals_; }
    inline iterator end() { return vals_ + product(bounds_); }
    inline const_iterator begin() const { return vals_; }
    inline const_iterator end() const { return vals_ + product(bounds_); }

    inline UInt getNNonZeros() const 
    {
      UInt n = 0;
      UInt M = product(bounds_);
      for (UInt i = 0; i < M; ++i)
        if (!nta::nearlyZero(vals_[i]))
          ++n;
      return n;
    }

    inline UInt getRank() const { return bounds_.size(); }
    inline bool isZero() const { return getNNonZeros() == 0; }
    inline bool isDense() const { return getNNonZeros() == product(bounds_); }
    inline bool isSparse() const { return getNNonZeros() != product(bounds_); }
    inline Index getBounds() const { return bounds_; }
    inline void clear() { memset(vals_, 0, product(bounds_) * sizeof(Float)); }

    inline Index getNewIndex() const
    {
      return getBounds();
    }

    inline Index getNewZeroIndex() const 
    {
      Index idx = getBounds();
      setToZero(idx);
      return idx;
    }

    inline bool isSymmetric(const Index& perm) const
    {
      Index idx = getNewZeroIndex(), idx2 = getNewZeroIndex();
      
      nta::permute(perm, bounds_, idx2);
      if (bounds_ != idx2)
        return false;

      do {
        nta::permute(perm, idx, idx2);
        if (!nta::nearlyZero(get(idx) - get(idx2)))
          return false;
      } while (increment(bounds_, idx));
      
      return true;
    }

    inline bool isAntiSymmetric(const Index& perm) const
    {
      Index idx = getNewZeroIndex(), idx2 = getNewZeroIndex();
      
      nta::permute(perm, bounds_, idx2);
      if (bounds_ != idx2)
        return false;

      do {
        nta::permute(perm, idx, idx2);
        if (!nta::nearlyZero(get(idx) - get(idx2)))
          return false;
      } while (increment(bounds_, idx));

      return true;
    }

    inline void fastSet(const UInt& idx, const Float& val)
    {
      vals_[idx] = val;
    }    

    inline void set(const Index& idx, const Float& val)
    {
      NTA_ASSERT(positiveInBounds(idx, getBounds()))
        << "DenseTensor::set(): "
        << "Invalid index: " << idx
        << " - Should be positive, <= " << getBounds();

      vals_[ordinal(bounds_, idx)] = val;
    }

    inline void set(UInt i0, ...)
    {
      Index idx = getNewZeroIndex();
      idx[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        idx[k] = (UInt) va_arg(indices, unsigned int); 
      const Float val = (Float) va_arg(indices, double);
      va_end(indices);
      set(idx, val);
    }

    inline void setAll(const Float& val)
    {
      const UInt M = product(bounds_);
      for (UInt i = 0; i < M; ++i)
        vals_[i] = val;
    }

    inline Float fastGet(const UInt& idx) const
    {
      return vals_[idx];
    }

    inline const Float get(const Index& idx) const
    {
      NTA_ASSERT(positiveInBounds(idx, getBounds()))
        << "DenseTensor::get(): "
        << "Invalid index: " << idx
        << " - Should be positive, <= " << getBounds();

      return vals_[ordinal(bounds_, idx)];
    }

    inline const Float get(UInt i0, ...)
    {
      Index idx = getNewZeroIndex();
      idx[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        idx[k] = (UInt) va_arg(indices, unsigned int); 
      va_end(indices);
      return get(idx);
    }

    inline const Float operator()(UInt i0, ...) const
    {
      Index idx = getNewZeroIndex();
      idx[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        idx[k] = (UInt) va_arg(indices, unsigned int); 
      va_end(indices);
      return get(idx);
    }

    inline Float& operator()(UInt i0, ...)
    {
      Index idx = getNewZeroIndex();
      idx[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        idx[k] = (UInt) va_arg(indices, unsigned int); 
      va_end(indices);

      NTA_ASSERT(positiveInBounds(idx, getBounds()))
        << "DenseTensor::get(): "
        << "Invalid index: " << idx
        << " - Should be positive, <= " << getBounds();

      return vals_[ordinal(bounds_, idx)];
    }

    template <typename binary_functor>
    inline Float update(const Index& idx, const Float& val, binary_functor f)
    {
      const UInt i = ordinal(bounds_, idx);
      vals_[i] = f(vals_[i], val);
      return vals_[i];
    }

    inline void toDense(Float* array) const
    {
      memcpy(array, vals_, product(bounds_) * sizeof(Float));
    }

    inline void fromDense(Float* array)
    {
      memcpy(vals_, array, product(bounds_) * sizeof(Float));
    }

    inline void permute(const Index& ind)
    {
      {
        NTA_ASSERT(ind.isSet());
      }

      Float* buf = new Float[product(bounds_)];
      Index idx = getNewZeroIndex(), perm = getNewIndex(), newBounds = getNewIndex();
      nta::permute(ind, bounds_, newBounds);

      do {
        nta::permute(ind, idx, perm);
        buf[ordinal(newBounds, perm)] = vals_[ordinal(bounds_, idx)];
      } while (increment(bounds_, idx));

      memcpy(vals_, buf, product(bounds_) * sizeof(Float));
      bounds_ = newBounds;
      delete [] buf;
    }

    inline void resize(const Index& newBounds)
    {
      {
        NTA_ASSERT(indexGtZero(newBounds));
      }

      if (newBounds == bounds_)
        return;

      const UInt M = product(newBounds);
      Float* buf = new Float[M];
      memset(buf, 0, M * sizeof(Float));
      Index idx = getNewZeroIndex();
      
      do {
        buf[ordinal(newBounds, idx)] = vals_[ordinal(bounds_, idx)];
      } while (increment(bounds_, idx));
      
      delete [] vals_;   
      vals_ = new Float[M];
      memcpy(vals_, buf, M * sizeof(Float));
      bounds_ = newBounds;
      delete [] buf;
    }

    inline void resize(UInt i0, ...)
    {
      Index newBounds = getNewIndex();
      newBounds[0] = i0;
      va_list indices;
      va_start(indices, i0);
      for (UInt k = 1; k < getRank(); ++k)
        newBounds[k] = (UInt) va_arg(indices, unsigned int);
      va_end(indices);

      resize(newBounds);
    }

    template <typename IndexB>
    inline void reshape(DenseTensor<IndexB, Float>& B)
    {
      {
        NTA_ASSERT(indexGtZero(B.getBounds()));
        NTA_ASSERT(product(B.getBounds()) == product(getBounds()));
        NTA_ASSERT((void*)&B != (void*)this);
      }

      const UInt M = product(bounds_);
      IndexB newBounds = B.getBounds(), idx2 = B.getNewIndex();

      for (UInt i = 0; i < M; ++i) {
        setFromOrdinal(newBounds, i, idx2);
        B.fastSet(i, vals_[i]);
      } 
    }
    
    template <typename IndexB>
    inline void getSlice(const Domain<UInt>& range, 
                         DenseTensor<IndexB, Float>& B,
                         bool clearYesNo =true) const
    {
      {
        NTA_ASSERT(range.rank() == getRank());
        
        NTA_ASSERT(B.getRank() == range.getNOpenDims())
          << "DenseTensor::getSlice(): "
          << "Invalid range: " << range
          << " - Range should have a number of open dims"
          << " equal to the rank of the slice ("
          << B.getRank() << ")";
      }

      if (clearYesNo)
        B.clear();

      Index idx = getNewZeroIndex();
      IndexB sliceIdx = B.getNewIndex(), openDims = B.getNewIndex();
      range.getOpenDims(openDims);

      do {
        if (range.includes(idx)) {
          project(openDims, idx, sliceIdx);
          for (UInt k = 0; k < B.getRank(); ++k)
            sliceIdx[k] -= range[openDims[k]].getLB();
          B.set(sliceIdx, get(idx));
        }
      } while (increment(getBounds(), idx));
    }

    template <typename binary_functor>
    inline void element_apply(const DenseTensor& B, DenseTensor& C, binary_functor f)
    {
      {
        NTA_ASSERT(getBounds() == B.getBounds())
          << "DenseTensor::element_apply(): "
          << "A and B have different bounds: "
          << getBounds() << " and " << B.getBounds()
          << " - Bounds need to be the same";

        NTA_ASSERT(getBounds() == C.getBounds())
          << "DenseTensor::element_apply(): "
          << "A and C have different bounds: "
          << getBounds() << " and " << C.getBounds()
          << " - Bounds need to be the same";
      }

      std::transform(begin(), end(), B.begin(), C.begin(), f);
    }

    template <typename unary_functor>
    inline void element_apply(unary_functor f)
    {
      const UInt M = product(bounds_);
      for (UInt i = 0; i < M; ++i)
        vals_[i] = f(vals_[i]);
    }

    /**
     * In place factor apply (mutating)
     */
    template <typename IndexB, typename binary_functor>
    inline void factor_apply(const IndexB& dims,
                             const DenseTensor<IndexB, Float>& B, 
                             binary_functor f)
    {
      {
        NTA_ASSERT(getRank() > 1); 
        NTA_ASSERT(B.getRank() >= 1);
        NTA_ASSERT(B.getRank() <= getRank());
      }

      Index idx = getNewZeroIndex();
      IndexB idx2 = B.getNewZeroIndex();
      const UInt M = product(bounds_);

      for (UInt i = 0; i < M; ++i, increment(bounds_, idx)) {
        project(dims, idx, idx2);
        UInt j = ordinal(B.getBounds(), idx2);
        vals_[i] = f(vals_[i], B.fastGet(j));
      }
    }

    /**
     * Binary factor apply (non-mutating)
     */
    template <typename IndexB, typename IndexC, typename binary_functor>
    inline void factor_apply(const IndexB& dims,
                             const DenseTensor<IndexB, Float>& B,
                             DenseTensor<IndexC, Float>& C, 
                             binary_functor f) const
    {
      {
        NTA_ASSERT(getRank() > 1); 
        NTA_ASSERT(B.getRank() >= 1);
        NTA_ASSERT(B.getRank() <= getRank());
      }

      Index idx = getNewZeroIndex();
      IndexB idx2 = B.getNewZeroIndex();
      const UInt M = product(bounds_);

      for (UInt i = 0; i < M; ++i, increment(bounds_, idx)) {
        project(dims, idx, idx2);
        UInt j = ordinal(B.getBounds(), idx2);
        C.fastSet(i, f(vals_[i], B.fastGet(j)));
      }
    }
    
    /**
     * Works on the non-zeros only, avoiding the zeros. 
     * For multiplication, this is the right one to use, otherwise
     * there will be multiplication by a zero, and the product will
     * be zero, even if init != 0.
     * For multiplication, use this one, AND init = 1.
     */
    template <typename Index2, typename IndexB, typename binary_functor>
    inline void accumulate_nz(const Index2& dims,
                              DenseTensor<IndexB, Float>& B, 
                              binary_functor f, const Float& init =0)
    {
      {
        NTA_ASSERT(dims.size() == getRank() - B.getRank());
        NTA_ASSERT(getRank() > B.getRank());
      }

      B.setAll(init);

      Index idx = getNewZeroIndex();
      IndexB compDims = B.getNewIndex(), idx2 = B.getNewIndex();
      complement(dims, compDims);
      
      do {
        Float val = get(idx);
        if (!nta::nearlyZero(val)) {
          project(compDims, idx, idx2);
          B.update(idx2, val, f);
        }
      } while (increment(bounds_, idx));
    }

    /**
     * Works on all the values, including the eventual zeros.
     * For multiplication, this will produce zeros in the output
     * as soon as a zero is encountered, even if init != 0.
     */
    template <typename Index2, typename IndexB, typename binary_functor>
    inline void accumulate(const Index2& dims,
                           DenseTensor<IndexB, Float>& B, 
                           binary_functor f, const Float& init =0)
    {
      {
        NTA_ASSERT(dims.size() == getRank() - B.getRank());
        NTA_ASSERT(getRank() > B.getRank());
      }

      B.setAll(init);

      Index idx = getNewZeroIndex();
      IndexB compDims = B.getNewIndex(), idx2 = B.getNewIndex();
      complement(dims, compDims);

      do {
        project(compDims, idx, idx2);
        B.update(idx2, get(idx), f);
      } while (increment(bounds_, idx));
    }

    template <typename IndexB, typename IndexC, typename binary_functor>
    inline void outer_product(const DenseTensor<IndexB, Float>& B,
                              DenseTensor<IndexC, Float>& C,
                              binary_functor f)
    {
      {
        NTA_ASSERT(getRank() + B.getRank() == C.getRank());
      }

      C.clear();
      Index idx1 = getNewZeroIndex();
      IndexB idx2 = B.getNewZeroIndex();

      do {
        setToZero(idx2);
        do {
          IndexC idx3 = concatenate(idx1, idx2);
          C.set(idx3, f(get(idx1), B.get(idx2)));
        } while (increment(B.getBounds(), idx2));
      } while (increment(bounds_, idx1));
    }

    template <typename IndexB, typename binary_functor>
    inline void contract(const UInt dim1, const UInt dim2,
                         DenseTensor<IndexB, Float>& B,
                         binary_functor f, const Float& init =0)
    {
      {
        NTA_ASSERT(B.getRank() == getRank() - 2);
        NTA_ASSERT(getRank() > 2);
        NTA_ASSERT(dim1 < getRank() && dim2 < getRank() && dim1 != dim2);
        NTA_ASSERT(bounds_[dim1] == bounds_[dim2]);
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

   template <typename IndexB, typename IndexC,
             typename binary_functor1, typename binary_functor2>
   inline void inner_product(const UInt dim1, const UInt dim2,
                             const DenseTensor<IndexB, Float>& B,
                             DenseTensor<IndexC, Float>& C,
                             binary_functor1 f, binary_functor2 g, 
                             const Float& init =0)
    {
      {
        NTA_ASSERT(getRank() + B.getRank() - 2 == C.getRank());

        NTA_ASSERT(getRank() + B.getRank() > 2)
          << "DenseTensor::inner_product(): "
          << "Trying to take inner product of two tensors of rank : " 
          << getRank() << " and: " << B.getRank()
          << " - But need sum of ranks > 2";

        NTA_ASSERT(dim1 < getRank())
          << "DenseTensor::inner_product(): "
          << " - Dimension 1 must be less than tensor A's rank: " 
          << getRank();

        NTA_ASSERT(dim2 < B.getRank())
          << "DenseTensor::inner_product(): "
          << " - Dimension 2 must be less than tensor B's rank: " 
          << B.getRank();

        NTA_ASSERT(bounds_[dim1] == B.getBounds()[dim2])
          << "DenseTensor::inner_product(): "
          << "Using dim: " << dim1
          << " and dim: " << dim2
          << " but they have different size: " << bounds_[dim1]
          << " and " << bounds_[dim2]
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
            IndexC idxc = concatenate(pit1, pit2);
            C.update(idxc, f(get(idx1), B.get(idx2)), g);
            }
        } while (increment(B.getBounds(), idx2));
      } while (increment(bounds_, idx1)); 
    }
  
    // for debugging
    template <typename Idx, typename F>
    NTA_HIDDEN friend std::ostream& operator<<(std::ostream&, const DenseTensor<Idx, F>&);

    template <typename Idx, typename F>
    NTA_HIDDEN friend bool operator==(const DenseTensor<Idx, F>&, const DenseTensor<Idx, F>&);

  private:
    Index bounds_;
    Float* vals_;

    // Need at least the bounds at construction time
    DenseTensor();
  };

  template <typename Idx, typename F>
  inline std::ostream& operator<<(std::ostream& outStream, const DenseTensor<Idx, F>& dense)
  {
    typedef typename Idx::value_type UI;

    if (dense.getRank() == 1 
        && dense.getBounds()[0] <= 16) 
      {
        outStream << dense.getBounds()[0] << ": ";
        for (UI i = 0; i < dense.getBounds()[0]; ++i)
          outStream << dense.vals_[i] << " ";
        outStream << std::endl;
      } 
    else if (dense.getRank() == 2 
             && dense.getBounds()[0] <= 16 
             && dense.getBounds()[1] <= 16) 
      {
        for (UI i = 0; i < dense.getBounds()[0]; ++i) {
          for (UI j = 0; j < dense.getBounds()[1]; ++j) 
            outStream << dense.get(Idx(i, j)) << " ";
          outStream << std::endl;
        }
      }
    else {
      Idx idx = dense.getNewZeroIndex();
      do {
        outStream << idx << ": " << dense.get(idx) << std::endl;
      } while (increment(dense.bounds_, idx));
    }
    return outStream;
  }

  template <typename Idx, typename F>
  inline bool operator==(const DenseTensor<Idx, F>& A, const DenseTensor<Idx, F>& B)
  {
    typedef typename Idx::value_type UI;

    if (A.getBounds() != B.getBounds())
      return false;
    
    const UI M = A.getBounds().product();
    
    for (UI i = 0; i < M; ++i)
      if (!nta::nearlyZero(A.vals_[i] - B.vals_[i]))
        return false;

    return true;
  }

  template <typename Idx, typename F>
  inline bool operator!=(const DenseTensor<Idx, F>& A, const DenseTensor<Idx, F>& B)
  {
    return ! (A == B);
  }

  //----------------------------------------------------------------------
  class SparseTensorUnitTest : public Tester
  {
  public:
    SparseTensorUnitTest() {
      //rng_ = new TRandom("sparse_tensor_test");
    }
    virtual ~SparseTensorUnitTest() {
      //delete rng_;
    }

    // Run all appropriate tests
    virtual void RunTests();

  private:    
    typedef Index<UInt, 1> I1;
    typedef Index<UInt, 2> I2;
    typedef Index<UInt, 3> I3;
    typedef Index<UInt, 4> I4;
    typedef Index<UInt, 5> I5;
    typedef Index<UInt, 6> I6;

    typedef DenseTensor<I6, Real> D6;
    typedef DenseTensor<I5, Real> D5;
    typedef DenseTensor<I4, Real> D4;
    typedef DenseTensor<I3, Real> D3;
    typedef DenseTensor<I2, Real> D2;
    typedef DenseTensor<I1, Real> D1;

    typedef SparseTensor<I6, Real> S6;
    typedef SparseTensor<I5, Real> S5;
    typedef SparseTensor<I4, Real> S4;
    typedef SparseTensor<I3, Real> S3;
    typedef SparseTensor<I2, Real> S2;
    typedef SparseTensor<I1, Real> S1;

    //void unitTestConstruction();
    //void unitTestGetSet();
    //void unitTestExtract();
    //void unitTestReduce();
    //void unitTestNonZeros();
    //void unitTestIsSymmetric();    
    //void unitTestToFromDense();
    //void unitTestPermute();
    //void unitTestResize();
    //void unitTestReshape();
    //void unitTestSlice();
    //void unitTestElementApply();
    //void unitTestFactorApply();
    //void unitTestAccumulate();
    //void unitTestOuterProduct();
    //void unitTestContract();   
    //void unitTestInnerProduct();
    //void unitTestIntersection();    
    //void unitTestUnion();
    //void unitTestDynamicIndex();
    //void unitTestToFromStream();
    //void unitTestNormalize();
    //void unitTestMaxSum();
    //void unitTestAxby();
    //void unitTestMultiply();
    //void unitTestPerformance();
    //void unitTestNumericalStability();

    // Use our own random number generator for reproducibility
    //TRandom *rng_;

    // Default copy ctor and assignment operator forbidden by default
    SparseTensorUnitTest(const SparseTensorUnitTest&);
    SparseTensorUnitTest& operator=(const SparseTensorUnitTest&);

  }; // end class SparseTensorUnitTest
    
  //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_SPARSE_TENSOR_UNIT_TEST_HPP



