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
 * Implementation of unit testing for class SparseTensor
 */      
              
#include "SparseTensorUnitTest.hpp"

#include <boost/tuple/tuple.hpp>
#include <boost/timer.hpp>
#include <boost/lambda/lambda.hpp>

using namespace std;      
using namespace boost; 
using namespace boost::lambda;    

namespace nta {
//
//  //--------------------------------------------------------------------------------
//  template <typename I, typename I2, typename F>
//  inline bool Compare(const SparseTensor<I, F>& A, const DenseTensor<I2, F>& B)
//  {
//    bool ok = true;
//    
//    if (A.getRank() != B.getRank()) {
//      NTA_WARN << "Ranks are different: " << A.getRank() << " and " << B.getRank();
//      ok = false;
//    }
//    
//    if (A.isZero() != B.isZero()) {
//      NTA_WARN << "isZero problem";
//      ok = false;
//    }
//    
//    if (A.isDense() != B.isDense()) {
//      NTA_WARN << "Density problem";
//      ok = false;
//    }
//
//    if (A.isSparse() != B.isSparse()) {
//      NTA_WARN << "Sparsity problem";
//      ok = false;
//    }
//
//    if (A.getBounds() != B.getBounds()) {
//      NTA_WARN << "Bounds are different: "
//               << A.getBounds()
//               << " and " << B.getBounds();
//      ok = false;   
//    }
//    
//    if (A.getNNonZeros() != B.getNNonZeros()) {
//      NTA_WARN << "Number of non-zeros are different: "
//               << A.getNNonZeros() 
//               << " and " << B.getNNonZeros();
//      ok = false;        
//    }
//
//    std::vector<boost::tuple<I, F, F> > diffs;
//    I idx = A.getNewZeroIndex();
//    I2 idxB = B.getNewZeroIndex();
//    do {
//      F val_A = A.get(idx);
//      F val_B = B.get(idxB);
//      if (!nta::nearlyZero(val_A - val_B)) 
//        diffs.push_back(make_tuple(idx, val_A, val_B));
//      increment(B.getBounds(), idxB);
//    } while (increment(A.getBounds(), idx));
//
//    if (!diffs.empty()) {
//      NTA_WARN << "There are " << diffs.size() << " differences between A and B: ";
//      for (UInt i = 0; i < diffs.size(); ++i) 
//        NTA_WARN << "Index: " << get<0>(diffs[i]) 
//                 << " A (sparse) = " << get<1>(diffs[i])
//                 << " B (dense) = " << get<2>(diffs[i]);
//      ok = false;
//    }
//    
//    return ok;
//  }
//
//  //--------------------------------------------------------------------------------
//  template <typename I, typename I2>
//  inline bool Compare(const std::vector<I>& A, const std::vector<I2>& B)
//  {
//    return std::equal(A.begin(), A.end(), B.begin());
//  }
//
//  //--------------------------------------------------------------------------------
//  struct Threshold
//  {
//    Threshold(const Real& threshold_) : threshold(threshold_) {}
//    Real threshold;
//    inline Real operator()(const Real& x) const 
//    { return x > threshold ? 0 : x; }
//  };
//   
//  //--------------------------------------------------------------------------------
//  struct Plus3
//  {
//    inline Real operator()(const Real& x) const 
//    { return x + 3; }
//  };
//
//  //--------------------------------------------------------------------------------
//  struct BinaryPlus3
//  {
//    inline Real operator()(const Real& x, const Real& y) const 
//    { return x + y + 3; }
//  };
//
//  //--------------------------------------------------------------------------------
//  template <typename Index, typename F>
//  inline void GenerateRand01(Random *r, UInt nnz, SparseTensor<Index, F>& s) 
//  {
//    const Index& ub = s.getBounds();
//    Index idx;
//    for (UInt i = 0; i < nnz; ++i) {
//      for (UInt n = 0; n < idx.size(); ++n)
//        idx[n] = r->getUInt32(ub[n]);
//      F val = F(r->getReal64());
//      s.set(idx, val);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  template <typename Index, typename F>
//  inline void GenerateRandRand01(Random *r, SparseTensor<Index, F>& s) 
//  {
//    const Index& ub = s.getBounds();
//    const UInt nnz = 1 + (r->getUInt32(product(ub)));
//    Index idx;
//    for (UInt i = 0; i < nnz; ++i) {
//      for (UInt n = 0; n < idx.size(); ++n)
//        idx[n] = r->getUInt32(ub[n]);
//      F val = F(r->getReal64());
//      s.set(idx, val);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  template <typename Index, typename F>
//  inline void GenerateOrdered(SparseTensor<Index, F>& s)
//  {
//    const Index& ub = s.getBounds();
//    Index idx;
//    typename Index::value_type o;
//    do {
//      o = ordinal(ub, idx);
//      s.set(idx, Real(o+1));
//    } while (increment(ub, idx));
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestConstruction()
//  {
//    I3 ub(5, 4, 3);
//
//    { 
//      S3 s3(ub);
//  
//      ITER_3(ub[0], ub[1], ub[2]) 
//        Test("SparseTensor bounds list constructor", s3.get(i, j, k), (Real)0);
//       
//      Test("SparseTensor getRank 1", s3.getRank(), (UInt)3);
//      Test("SparseTensor getNNonZeros 2", s3.getNNonZeros(), (UInt)0);
//      Test("SparseTensor isZero 3", s3.isZero(), true);
//      Test("SparseTensor isDense 4", s3.isDense(), false);
//      Test("SparseTensor getBounds 5", s3.getBounds(), I3(ub[0], ub[1], ub[2]));
//
//      ITER_3(ub[0], ub[1], ub[2]) {
//        s3.set(I3(i, j, k), Real(i*ub[1]*ub[2]+j*ub[2]+k));
//        Test("SparseTensor bounds set/get 6", s3.get(i, j, k), i*ub[1]*ub[2]+j*ub[2]+k);
//      }
//
//      Test("SparseTensor getNNonZeros 7", s3.getNNonZeros(), (UInt)ub[0]*ub[1]*ub[2]-1);
//      Test("SparseTensor isZero 8", s3.isZero(), false);
//      Test("SparseTensor isDense 9", s3.isDense(), false);
//
//      s3.set(I3(0, 0, 0), 1);
//      Test("SparseTensor getNNonZeros 10", s3.getNNonZeros(), (UInt)ub[0]*ub[1]*ub[2]);
//      Test("SparseTensor isZero 11", s3.isZero(), false);
//      Test("SparseTensor isDense 12", s3.isDense(), true);
//
//      s3.clear();
//      Test("SparseTensor getNNonZeros 71", s3.getNNonZeros(), (UInt)0);
//      Test("SparseTensor isZero 81", s3.isZero(), true);
//      Test("SparseTensor isDense 91", s3.isDense(), false);
//    }
//
//    { 
//      I3 i3(ub);
//      S3 s3(i3);
//  
//      ITER_3(ub[0], ub[1], ub[2]) 
//        Test("SparseTensor bounds vector constructor", s3.get(i, j, k), (Real)0);
//       
//      Test("SparseTensor getRank 25", s3.getRank(), (UInt)3);
//      Test("SparseTensor getNNonZeros 26", s3.getNNonZeros(), (UInt)0);
//      Test("SparseTensor isZero 27", s3.isZero(), true);
//      Test("SparseTensor isDense 28", s3.isDense(), false);
//      Test("SparseTensor getBounds 29", s3.getBounds(), I3(ub[0], ub[1], ub[2]));
//
//      ITER_3(ub[0], ub[1], ub[2]) {
//        s3.set(I3(i, j, k), Real(i*ub[1]*ub[2]+j*ub[2]+k));
//        Test("SparseTensor bounds set/get 30", s3.get(i, j, k), i*ub[1]*ub[2]+j*ub[2]+k);
//      }
//
//      Test("SparseTensor getNNonZeros 31", s3.getNNonZeros(), (UInt)ub[0]*ub[1]*ub[2]-1);
//      Test("SparseTensor isZero 32", s3.isZero(), false);
//      Test("SparseTensor isDense 33", s3.isDense(), false);
//
//      s3.set(I3(0, 0, 0), 1);
//      Test("SparseTensor getNNonZeros 34", s3.getNNonZeros(), (UInt)ub[0]*ub[1]*ub[2]);
//      Test("SparseTensor isZero 35", s3.isZero(), false);
//      Test("SparseTensor isDense 36", s3.isDense(), true);
//    }
//
//    { 
//      I3 ub3(ub);
//      S3 s3(ub3);
//
//      ITER_3(ub[0], ub[1], ub[2]) 
//        s3.set(I3(i, j, k), Real(i*ub[1]*ub[2]+j*ub[2]+k));
//
//      S3 s32(s3);
//
//      ITER_3(ub[0], ub[1], ub[2]) {
//        Test("SparseTensor bounds set/get 37", s32.get(i, j, k), i*ub[1]*ub[2]+j*ub[2]+k);
//      }
//
//      Test("SparseTensor getNNonZeros 38", s32.getNNonZeros(), (UInt)ub[0]*ub[1]*ub[2]-1);
//      Test("SparseTensor isZero 39", s32.isZero(), false);
//      Test("SparseTensor isDense 40", s32.isDense(), false);
//      Test("SparseTensor getBounds 41", s32.getBounds(), I3(ub[0], ub[1], ub[2]));
//    }
//
//    { 
//      I3 ub3(ub);
//      S3 s3(ub3);
//
//      ITER_3(ub[0], ub[1], ub[2]) 
//        s3.set(I3(i, j, k), Real(i*ub[1]*ub[2]+j*ub[2]+k));
//
//      S3 s32 = s3;
//
//      ITER_3(ub[0], ub[1], ub[2]) {
//        Test("SparseTensor bounds set/get 42", s32.get(i, j, k), i*ub[1]*ub[2]+j*ub[2]+k);
//      }
//
//      Test("SparseTensor getNNonZeros 43", s32.getNNonZeros(), (UInt)ub[0]*ub[1]*ub[2]-1);
//      Test("SparseTensor isZero 44", s32.isZero(), false);
//      Test("SparseTensor isDense 45", s32.isDense(), false);
//      Test("SparseTensor getBounds 46", s32.getBounds(), I3(ub[0], ub[1], ub[2]));
//    }
//
//    {
//      I3 ub3(ub);
//      S3 s3A(ub3), s3B(ub3), ref(ub3);
//
//      ITER_3(ub[0], ub[1], ub[2]) {
//        ref.set(I3(i, j, k), Real(i*ub[1]*ub[2]+j*ub[2]+k));
//        s3A.set(I3(i, j, k), Real(i*ub[1]*ub[2]+j*ub[2]+k));
//      }
//
//      s3A.swap(s3B);
//      Test("SparseTensor swap 1", s3B == ref, true);
//      Test("SparseTensor swap 2", s3A.isZero(), true);
//    }
//
//    // Constructing a dimension 6, just to be sure, we had a bug
//    // with va_arg(indices, UInt) (ellipsis setters/getters) 
//    // that showed up in dimension 6 on 64 bits only, because of the specific sizes
//    // of the integer types used... 
//    I6 ub6(5, 4, 3, 2, 3, 4);
//    D6 d6(ub6);
//    S6 s6(ub6);
//    
//    UInt c = 1;
//    ITER_6(ub6[0], ub6[1], ub6[2], ub6[3], ub6[4], ub6[5]) {
//      d6.set(I6(i, j, k, l, m, n), Real(c));
//      s6.set(I6(i, j, k, l, m, n), Real(c));
//      ++c;
//    }
//
//    Test("SparseTensor dim 6 set/get 1", Compare(s6, d6), true);
//
//    // This could catch uninitialized values, that used to be a problem
//    // on shona, revealed by valgrind only
//    bool correct = true;
//    ITER_6(ub6[0], ub6[1], ub6[2], ub6[3], ub6[4], ub6[5]) 
//      if (s6.get(I6(i, j, k, l, m, n)) > 2000
//          || d6.get(I6(i, j, k, l, m, n)) > 2000) {
//        correct = false;
//        break;
//      }
//    
//    Test("SparseTensor dim 6 set/get 2", correct, true);
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestGetSet()
//  {
//    I3 ub(5, 4, 3);
//
//    // These tests compiled conditionally, because they are 
//    // based on asserts rather than checks
//    
//#ifdef NTA_ASSERTIONS_ON
//
//    { // out of bounds
//      S3 s3(ub);
//      try {
//        s3.set(I3(5, 4, 4), 1);
//        Test("Set out of bounds 1", 1, 0);
//      } catch (...) {
//        Test("Set out of bounds 1", 1, 1);
//      }
//      try {
//        s3.setZero(I3(5, 4, 4));
//        Test("Set out of bounds 2", 1, 0);
//      } catch (...) {
//        Test("Set out of bounds 2", 1, 1);
//      }
//      try {
//        s3.setNonZero(I3(5, 4, 4), 1);
//        Test("Set out of bounds 3", 1, 0);
//      } catch (...) {
//        Test("Set out of bounds 3", 1, 1);
//      }
//      try {
//        s3.get(I3(5, 4, 4));
//        Test("Get out of bounds 4", 1, 0);
//      } catch (...) {
//        Test("Get out of bounds 4", 1, 1);
//      }
//      try {
//        s3.update(I3(5, 4, 4), 1, std::plus<Real>());
//        Test("update out of bounds 5", 1, 0);
//      } catch (...) {
//        Test("update out of bounds 5", 1, 1);
//      }
//      try {
//        s3.isZero(I3(5, 4, 4));
//        Test("isZero out of bounds 6", 1, 0);
//      } catch (...) {
//        Test("isZero out of bounds 6", 1, 1);
//      }
//    }
//
//#endif
//
//    { 
//      S3 s3(ub), s32(ub), s33(ub);
//
//      ITER_3(ub[0], ub[1], ub[2]) {
//        s3.set(I3(i, j, k), Real(i*ub[1]*ub[2]+j*ub[2]+k));
//        s32.set(I3(i, j, k), Real(s3.get(i, j, k)));
//        //s33(i, j, k) = s3(i, j, k);
//      }
//
//      Test("SparseTensor set 1", s3.getNNonZeros(), (UInt)ub[0]*ub[1]*ub[2]-1);
//      Test("SparseTensor set 2", s3.isZero(), false);
//      Test("SparseTensor set 3", s3.isDense(), false);
//      Test("SparseTensor set 4", s32.getNNonZeros(), (UInt)ub[0]*ub[1]*ub[2]-1);
//      Test("SparseTensor set 5", s32.isZero(), false);
//      Test("SparseTensor set 6", s32.isDense(), false);
//      //Test("SparseTensor set 7", s33.getNNonZeros(), (UInt)ub[0]*ub[1]*ub[2]-1);
//      //Test("SparseTensor set 8", s33.isZero(), false);
//      //Test("SparseTensor set 9", s33.isDense(), false);
//
//
//      ITER_3(ub[0], ub[1], ub[2]) {
//        Test("SparseTensor get 1", s3.get(I3(i, j, k)), i*ub[1]*ub[2]+j*ub[2]+k);
//        Test("SparseTensor get 2", s3.get(i, j, k), s3.get(I3(i, j, k)));
//        Test("SparseTensor get 3", s3(i, j, k), s3.get(I3(i, j, k)));
//      }
//
//      // setZero
//      UInt n = ub[0]*ub[1]*ub[2]-1;
//      ITER_3(ub[0], ub[1], ub[2]) {
//        s3.setZero(i, j, k);
//        Test("SparseTensor setZero 1", s3.getNNonZeros(), n);
//        Test("SparseTensor setZero 2", s3.get(I3(i, j, k)), (Real)0);
//        Test("SparseTensor setZero 3", s3.isZero(I3(i, j, k)), true);
//        Test("SparseTensor setZero 4", s3.isZero(i, j, k), true);
//        s32.setZero(i, j, k);
//        Test("SparseTensor setZero 5", s32.getNNonZeros(), n);
//        Test("SparseTensor setZero 6", s32.get(I3(i, j, k)), (Real)0);
//        Test("SparseTensor setZero 7", s32.isZero(I3(i, j, k)), true);
//        Test("SparseTensor setZero 8", s32.isZero(i, j, k), true);
//        --n;
//      }
//
//      n = 1;
//      ITER_3(ub[0], ub[1], ub[2]) {
//        s3.setNonZero(I3(i, j, k), Real(n));
//        Test("SparseTensor setNonZero 1", s3.getNNonZeros(), n);
//        Test("SparseTensor setNonZero 2", s3.get(I3(i, j, k)), (Real)n);
//        Test("SparseTensor setNonZero 3", s3.isZero(I3(i, j, k)), false);
//        Test("SparseTensor setNonZero 4", s3.isZero(i, j, k), false);
//        s32.setNonZero(I3(i, j, k), (Real)n);
//        Test("SparseTensor setNonZero 5", s32.getNNonZeros(), n);
//        Test("SparseTensor setNonZero 6", s32.get(I3(i, j, k)), (Real)n);
//        Test("SparseTensor setNonZero 7", s32.isZero(I3(i, j, k)), false);
//        Test("SparseTensor setNonZero 8", s32.isZero(i, j, k), false);
//        ++n;
//      }
//
//      // setZero(Domain)
//      {
//        s3.setAll(0);
//        for (UInt i = 0; i < ub[0]; ++i)
//          s3.setZero(Domain<UInt>(I3(i,0,0), I3(i,ub[1],ub[2])));
//        Test("SparseTensor setZero(Domain) 1", s3.isZero(), true);
//
//        s3.setAll(1);
//        for (UInt i = 0; i < ub[0]; ++i)
//          s3.setZero(Domain<UInt>(I3(i,0,0), I3(i,ub[1],ub[2])));
//        Test("SparseTensor setZero(Domain) 2", s3.isZero(), true);
//
//        GenerateRandRand01(rng_, s3);
//        for (UInt i = 0; i < ub[0]; ++i)
//          s3.setZero(Domain<UInt>(I3(i,0,0), I3(i,ub[1],ub[2])));
//        Test("SparseTensor setZero(Domain) 3", s3.isZero(), true);
//      }
//    }
//    
//    {
//      S2 s2(4, 5);
//      D2 d2(4, 5);
//
//      ITER_2(4, 5) {
//       s2.update(I2(i, j), Real(i*5+j), std::plus<Real>());
//        d2.set(i, j, Real(i*5+j));
//      }
//
//      Test("SparseTensor update 01", Compare(s2, d2), true);
//
//      ITER_2(4, 5) {
//        s2.update(I2(i, j), Real(s2.get(i, j)), nta::Multiplies<Real>());
//        d2.set(i, j, Real(d2.get(i, j) * d2.get(i, j)));
//      }
//
//      Test("SparseTensor update 02", Compare(s2, d2), true);
//    }
//
//    {  
//      S3 s3(ub);
//      D3 d3(ub);
//      
//      ITER_3(ub[0], ub[1], ub[2]) {
//        s3.update(I3(i, j, k), Real(i*ub[1]*ub[2]+j*ub[2]+k), std::plus<Real>());
//        d3.set(i, j, k, (Real)(i*ub[1]*ub[2]+j*ub[2]+k));
//      }    
//
//      Test("SparseTensor update 1", Compare(s3, d3), true);
//
//      ITER_3(ub[0], ub[1], ub[2]) {
//        s3.update(I3(i, j, k), s3.get(i, j, k), std::plus<Real>());
//        d3.set(i, j, k, (Real)(d3.get(i, j, k) + d3.get(i, j, k)));
//      }   
//
//      Test("SparseTensor update 2", Compare(s3, d3), true);
//    
//      ITER_3(ub[0], ub[1], ub[2]) {    
//        s3.update(I3(i, j, k), s3.get(i, j, k), nta::Multiplies<Real>());
//        d3.set(i, j, k, (Real)(d3.get(i, j, k) * d3.get(i, j, k)));
//      }   
//
//      Test("SparseTensor update 3", Compare(s3, d3), true);
//    }
//
//    {
//      S3 s3(ub), ref(ub);
//
//      Test("SparseTensor clear 1", s3, ref);
//      
//      ITER_3(ub[0], ub[1], ub[2]) 
//        s3.set(I3(i, j, k), (Real)(i*ub[1]*ub[2]+j*ub[2]+k));
//      
//      s3.clear();
//      Test("SparseTensor clear 2", s3, ref);
//
//      s3.clear();
//      Test("SparseTensor clear 3", s3, ref);
//
//      ITER_3(ub[0], ub[1], ub[2]) 
//        s3.set(I3(i, j, k), (Real)(i*ub[1]*ub[2]+j*ub[2]+k));
//    }
//
//    { // setAll
//      I4 ub4(5, 4, 3, 2);
//      S4 s4(ub4);
//      
//      Test("SparseTensor setAll 1", s4.isZero(), true);
//      
//      s4.setAll(0);
//      Test("SparseTensor setAll 2A", s4.isZero(), true);
//      Test("SparseTensor setAll 2B", s4.getNNonZeros(), (UInt)0);
//
//      s4.setAll(nta::Epsilon/2);
//      Test("SparseTensor setAll 3A", s4.isZero(), true);
//      Test("SparseTensor setAll 3B", s4.getNNonZeros(), (UInt)0);
//
//      s4.setAll(nta::Epsilon);
//      Test("SparseTensor setAll 4A", s4.isZero(), true);
//      Test("SparseTensor setAll 4B", s4.getNNonZeros(), (UInt)0);
//
//      s4.setAll(2*nta::Epsilon);
//      Test("SparseTensor setAll 4A", s4.isZero(), false);
//      Test("SparseTensor setAll 4B", s4.getNNonZeros(), (UInt)ub4.product());
//
//      I4 i4;
//      do {
//        Test("SparseTensor setAll 4C", s4.get(i4), 2*nta::Epsilon);
//      } while (i4.increment(ub4));
//
//      s4.setAll(1.5);
//      Test("SparseTensor setAll 5A", s4.isZero(), false);
//      Test("SparseTensor setAll 5B", s4.getNNonZeros(), (UInt)ub4.product());
//
//      i4.setToZero();
//      do {
//        Test("SparseTensor setAll 5C", s4.get(i4), 1.5);
//      } while (i4.increment(ub4));
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestExtract()
//  {
//    { // Dim 2
//      I2 ub2(5, 7);
//      S2 s2A(ub2), s2B(ub2);
//      std::set<UInt> some;
//
//      GenerateRandRand01(rng_, s2A);
//
//      // Extract with full set
//      for (UInt i = 0; i < ub2[0]; ++i)
//        some.insert(i);
//
//      s2A.extract(0, some, s2B);
//
//      // Extract to some values    
//      some.clear();
//      some.insert(0); some.insert(3); 
//
//      s2A.extract(0, some, s2B);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  /**
//   * TC1: All zeros tensor should be reduced to all zeros tensor with non empty ind
//   * TC2: All zeros tensor is reduce to null tensor with empty ind
//   * TC3: Full tensor should be reduced appropriately with non empty ind
//   *      Indices should be updated properly.
//   *      UInt should be updated properly.
//   * TC4: Full tensor is reduced to null tensor with empty ind
//   * TC5: Sparse tensor should be reduced appropriately with non-empty ind
//   *      Indices should be updated properly.
//   *      UInt should be updated properly.
//   * TC6: Sparse tensor is reduced to null tensor if ind is empty
//   */
//  void SparseTensorUnitTest::unitTestReduce()
//  {
//    I2 ub2(5, 6);
//    S2 s2A(ub2), s2B(ub2);
//    std::set<UInt> ind;
//
//    { // TC1
//      ind.insert(UInt(1));
//      s2A.reduce(0, ind);  
//      Test("SparseTensor reduce 1A", s2A.isZero(), true);
//      // Let's make sure we can call it twice, and stay invariant
//      Test("SparseTensor reduce 1B", s2A.isZero(), true);
//
//      s2A.reduce(1, ind);
//      Test("SparseTensor reduce 1C", s2A.isZero(), true);
//    }      
//    
//    { // TC2
//      ind.clear();
//      s2A.reduce(0, ind);
//      Test("SparseTensor reduce 2A", s2A.isNull(), true);
//      // Let's make sure we can call it twice, and stay invariant
//      Test("SparseTensor reduce 2B", s2A.isNull(), true);
//
//      s2A.resize(0, ub2[0]);
//      s2A.reduce(1, ind);
//      Test("SparseTensor reduce 2C", s2A.isNull(), true);
//    }
//
//    { // TC3
//      s2A.resize(ub2);
//      GenerateOrdered(s2A);
//
//      ind.insert(UInt(1)); ind.insert(UInt(3));
//      s2A.reduce(0, ind);
//      s2A.reduce(1, ind);
//    }
//
//    { // TC4
//      s2A.resize(ub2);
//      GenerateOrdered(s2A);
//      ind.clear();
//      s2A.reduce(0, ind);
//      Test("SparseTensor reduce 10A", s2A.isNull(), true);
//
//      s2A.resize(ub2);
//      GenerateOrdered(s2A);
//      ind.clear();
//      s2A.reduce(1, ind);
//      Test("SparseTensor reduce 10B", s2A.isNull(), true);
//    }
//
//    { // TC5
//      s2A.resize(ub2);
//      GenerateRandRand01(rng_, s2A);
//      ind.insert(1); ind.insert(3);
//      s2A.reduce(0, ind);
//    }
//
//    { // TC 6
//      s2A.resize(ub2);
//      ind.clear();
//      GenerateRandRand01(rng_, s2A);
//      s2A.reduce(0, ind);
//      Test("SparseTensor reduce 11A", s2A.isNull(), true);
//    }
//   
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestNonZeros()
//  {
//    I2 ub2(11, 13);
//
//    { // Global tests (no domain)
//      { // Empty tensor
//        S2 s2(ub2);
//        Test("SparseTensor getNNonZeros() 1", s2.getNNonZeros(), (UInt)0);
//        Test("SparseTensor getNZeros() 1", s2.getNZeros(), ub2.product());
//        Test("SparseTensor isZero() 1", s2.isZero(), true);
//        Test("SparseTensor isSparse() 1", s2.isSparse(), true);
//        Test("SparseTensor isDense() 1", s2.isDense(), false);
//        Test("SparseTensor getFillRate() 1", s2.getFillRate(), (Real)0);
//        Test("SparseTensor isPositive() 1", s2.isPositive(), false);
//        Test("SparseTensor isNonNegative() 1", s2.isNonNegative(), true);
//      }
//       
//      { // Full (dense) tensor 1
//        S2 s2(ub2); s2.setAll(1);
//        Test("SparseTensor getNNonZeros() 2", s2.getNNonZeros(), ub2.product());
//        Test("SparseTensor getNZeros() 2", s2.getNZeros(), (UInt)0);
//        Test("SparseTensor isZero() 2", s2.isZero(), false);
//        Test("SparseTensor isSparse() 2", s2.isSparse(), false);
//        Test("SparseTensor isDense() 2", s2.isDense(), true);
//        Test("SparseTensor getFillRate() 2", s2.getFillRate(), (Real)1);
//        Test("SparseTensor isPositive() 2", s2.isPositive(), true);
//        Test("SparseTensor isNonNegative() 2", s2.isNonNegative(), true);
//      }  
//
//      { // Full (dense) tensor 2 (negative tensor) 
//        S2 s2(ub2); s2.setAll(-1);
//        Test("SparseTensor getNNonZeros() 3", s2.getNNonZeros(), ub2.product());
//        Test("SparseTensor getNZeros() 3", s2.getNZeros(), (UInt)0);
//        Test("SparseTensor isZero() 3", s2.isZero(), false);
//        Test("SparseTensor isSparse() 3", s2.isSparse(), false);
//        Test("SparseTensor isDense() 3", s2.isDense(), true);
//        Test("SparseTensor getFillRate() 3", s2.getFillRate(), (Real)1);
//        Test("SparseTensor isPositive() 3", s2.isPositive(), false);
//        Test("SparseTensor isNonNegative() 3", s2.isNonNegative(), false);
//      }  
//
//      { // Full (dense) tensor 2 (mixed positive and negative tensor) 
//        S2 s2(ub2); 
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) s2.set(i2, Real(o+1)); else s2.set(i2, Real(-1)); 
//        } 
//        Test("SparseTensor getNNonZeros() 4", s2.getNNonZeros(), ub2.product());
//        Test("SparseTensor getNZeros() 4", s2.getNZeros(), (UInt)0);
//        Test("SparseTensor isZero() 4", s2.isZero(), false);
//        Test("SparseTensor isSparse() 4", s2.isSparse(), false);
//        Test("SparseTensor isDense() 4", s2.isDense(), true);
//        Test("SparseTensor getFillRate() 4", s2.getFillRate(), (Real)1);
//        Test("SparseTensor isPositive() 4", s2.isPositive(), false);
//        Test("SparseTensor isNonNegative() 4", s2.isNonNegative(), false);
//      }  
//
//      { // Sparse tensor 1
//        S2 s2(ub2); 
//        UInt nnz = 0;
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) { s2.set(i2, Real(o+1)); ++nnz; }
//        } 
//        Test("SparseTensor getNNonZeros() 5", s2.getNNonZeros(), nnz);
//        Test("SparseTensor getNZeros() 5", s2.getNZeros(), ub2.product() - nnz);
//        Test("SparseTensor isZero() 5", s2.isZero(), false);
//        Test("SparseTensor isSparse() 5", s2.isSparse(), true);
//        Test("SparseTensor isDense() 5", s2.isDense(), false);
//        Real fr = (Real)nnz / (Real)ub2.product();
//        Test("SparseTensor getFillRate() 5", s2.getFillRate(), fr);
//        Test("SparseTensor isPositive() 5", s2.isPositive(), false);
//        Test("SparseTensor isNonNegative() 5", s2.isNonNegative(), true);
//      }  
//
//      { // Sparse tensor 2 (negative tensor)
//        S2 s2(ub2); 
//        UInt nnz = 0;
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) { s2.set(i2, -1); ++nnz; }
//        } 
//        Test("SparseTensor getNNonZeros() 6", s2.getNNonZeros(), nnz);
//        Test("SparseTensor getNZeros() 6", s2.getNZeros(), ub2.product() - nnz);
//        Test("SparseTensor isZero() 6", s2.isZero(), false);
//        Test("SparseTensor isSparse() 6", s2.isSparse(), true);
//        Test("SparseTensor isDense() 6", s2.isDense(), false);
//        Real fr = (Real)nnz / (Real)ub2.product();
//        Test("SparseTensor getFillRate() 6", s2.getFillRate(), fr);
//        Test("SparseTensor isPositive() 6", s2.isPositive(), false);
//        Test("SparseTensor isNonNegative() 6", s2.isNonNegative(), false);
//      }  
//
//      { // Sparse tensor 3 (mixed positive and negative tensor)
//        S2 s2(ub2); 
//        UInt nnz = 0;
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) { 
//            if (o % 3 == 0)
//              s2.set(i2, -1); 
//            else
//              s2.set(i2, Real(o));
//            ++nnz; 
//          }
//        } 
//        Test("SparseTensor getNNonZeros() 7", s2.getNNonZeros(), nnz);
//        Test("SparseTensor getNZeros() 7", s2.getNZeros(), ub2.product() - nnz);
//        Test("SparseTensor isZero() 7", s2.isZero(), false);
//        Test("SparseTensor isSparse() 7", s2.isSparse(), true);
//        Test("SparseTensor isDense() 7", s2.isDense(), false);
//        Real fr = (Real)nnz / (Real)ub2.product();
//        Test("SparseTensor getFillRate() 7", s2.getFillRate(), fr);
//        Test("SparseTensor isPositive() 7", s2.isPositive(), false);
//        Test("SparseTensor isNonNegative() 7", s2.isNonNegative(), false);
//      }  
//    }
//
//    { // Domain tests (with full domain)
//      Domain<UInt> d2(I2(0, 0), ub2);
//
//      { // Empty tensor
//        S2 s2(ub2);
//        Test("SparseTensor getNNonZeros(d2) 1", s2.getNNonZeros(d2), (UInt)0);
//        Test("SparseTensor getNZeros(d2) 1", s2.getNZeros(d2), ub2.product());
//        Test("SparseTensor isZero(d2) 1", s2.isZero(d2), true);
//        Test("SparseTensor isSparse(d2) 1", s2.isSparse(d2), true);
//        Test("SparseTensor isDense(d2) 1", s2.isDense(d2), false);
//        Test("SparseTensor getFillRate(d2) 1", s2.getFillRate(d2), (Real)0);
//      }
//       
//      { // Full (dense) tensor 1
//        S2 s2(ub2); s2.setAll(1);
//        Test("SparseTensor getNNonZeros(d2) 2", s2.getNNonZeros(d2), ub2.product());
//        Test("SparseTensor getNZeros(d2) 2", s2.getNZeros(d2), (UInt)0);
//        Test("SparseTensor isZero(d2) 2", s2.isZero(d2), false);
//        Test("SparseTensor isSparse(d2) 2", s2.isSparse(d2), false);
//        Test("SparseTensor isDense(d2) 2", s2.isDense(d2), true);
//        Test("SparseTensor getFillRate(d2) 2", s2.getFillRate(d2), (Real)1);
//      }  
//
//      { // Full (dense) tensor 2 (negative tensor) 
//        S2 s2(ub2); s2.setAll(-1);
//        Test("SparseTensor getNNonZeros(d2) 3", s2.getNNonZeros(d2), ub2.product());
//        Test("SparseTensor getNZeros(d2) 3", s2.getNZeros(d2), (UInt)0);
//        Test("SparseTensor isZero(d2) 3", s2.isZero(d2), false);
//        Test("SparseTensor isSparse(d2) 3", s2.isSparse(d2), false);
//        Test("SparseTensor isDense(d2) 3", s2.isDense(d2), true);
//        Test("SparseTensor getFillRate(d2) 3", s2.getFillRate(d2), (Real)1);
//      }  
//
//      { // Full (dense) tensor 2 (mixed positive and negative tensor) 
//        S2 s2(ub2); 
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) s2.set(i2, Real(o+1)); else s2.set(i2, Real(-1)); 
//        } 
//        Test("SparseTensor getNNonZeros(d2) 4", s2.getNNonZeros(d2), ub2.product());
//        Test("SparseTensor getNZeros(d2) 4", s2.getNZeros(d2), (UInt)0);
//        Test("SparseTensor isZero(d2) 4", s2.isZero(d2), false);
//        Test("SparseTensor isSparse(d2) 4", s2.isSparse(d2), false);
//        Test("SparseTensor isDense(d2) 4", s2.isDense(d2), true);
//        Test("SparseTensor getFillRate(d2) 4", s2.getFillRate(d2), (Real)1);
//      }  
//
//      { // Sparse tensor 1
//        S2 s2(ub2); 
//        UInt nnz = 0;
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) { s2.set(i2, Real(o+1)); ++nnz; }
//        } 
//        Test("SparseTensor getNNonZeros(d2) 5", s2.getNNonZeros(d2), nnz);
//        Test("SparseTensor getNZeros(d2) 5", s2.getNZeros(d2), ub2.product() - nnz);
//        Test("SparseTensor isZero(d2) 5", s2.isZero(d2), false);
//        Test("SparseTensor isSparse(d2) 5", s2.isSparse(d2), true);
//        Test("SparseTensor isDense(d2) 5", s2.isDense(d2), false);
//        Real fr = (Real)nnz / (Real)d2.size_elts();
//        Test("SparseTensor getFillRate(d2) 5", s2.getFillRate(d2), fr);
//      }  
//
//      { // Sparse tensor 2 (negative tensor)
//        S2 s2(ub2); 
//        UInt nnz = 0;
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) { s2.set(i2, -1); ++nnz; }
//        } 
//        Test("SparseTensor getNNonZeros(d2) 6", s2.getNNonZeros(d2), nnz);
//        Test("SparseTensor getNZeros(d2) 6", s2.getNZeros(d2), ub2.product() - nnz);
//        Test("SparseTensor isZero(d2) 6", s2.isZero(d2), false);
//        Test("SparseTensor isSparse(d2) 6", s2.isSparse(d2), true);
//        Test("SparseTensor isDense(d2) 6", s2.isDense(d2), false);
//        Real fr = (Real)nnz / (Real)d2.size_elts();
//        Test("SparseTensor getFillRate(d2) 6", s2.getFillRate(d2), fr);
//      }     
//
//      { // Sparse tensor 3 (mixed positive and negative tensor)
//        S2 s2(ub2); 
//        UInt nnz = 0;
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) { 
//            if (o % 3 == 0)
//              s2.set(i2, -1); 
//            else
//              s2.set(i2, Real(o));
//            ++nnz; 
//          }
//        } 
//        Test("SparseTensor getNNonZeros(d2) 7", s2.getNNonZeros(d2), nnz);
//        Test("SparseTensor getNZeros(d2) 7", s2.getNZeros(d2), ub2.product() - nnz);
//        Test("SparseTensor isZero(d2) 7", s2.isZero(d2), false);
//        Test("SparseTensor isSparse(d2) 7", s2.isSparse(d2), true);
//        Test("SparseTensor isDense(d2) 7", s2.isDense(d2), false);
//        Real fr = (Real)nnz / (Real)d2.size_elts();
//        Test("SparseTensor getFillRate(d2) 7", s2.getFillRate(d2), fr);
//      }  
//    }
//
//    { // Domain tests (with partial domain)
//      Domain<UInt> d2p(I2(1, 2), I2(ub2[0]/2 ,ub2[1]/2));
//
//      { // Empty tensor
//        S2 s2(ub2);
//        Test("SparseTensor getNNonZeros(d2p) 1", s2.getNNonZeros(d2p), (UInt)0);
//        Test("SparseTensor getNZeros(d2p) 1", s2.getNZeros(d2p), d2p.size_elts());
//        Test("SparseTensor isZero(d2p) 1", s2.isZero(d2p), true);
//        Test("SparseTensor isSparse(d2p) 1", s2.isSparse(d2p), true);
//        Test("SparseTensor isDense(d2p) 1", s2.isDense(d2p), false);
//        Test("SparseTensor getFillRate(d2p) 1", s2.getFillRate(d2p), (Real)0);
//      }
//       
//      { // Full (dense) tensor 1
//        S2 s2(ub2); s2.setAll(1);
//        Test("SparseTensor getNNonZeros(d2p) 2", s2.getNNonZeros(d2p), d2p.size_elts());
//        Test("SparseTensor getNZeros(d2p) 2", s2.getNZeros(d2p), (UInt)0);
//        Test("SparseTensor isZero(d2p) 2", s2.isZero(d2p), false);
//        Test("SparseTensor isSparse(d2p) 2", s2.isSparse(d2p), false);
//        Test("SparseTensor isDense(d2p) 2", s2.isDense(d2p), true);
//        Test("SparseTensor getFillRate(d2p) 2", s2.getFillRate(d2p), (Real)1);
//      }  
//
//      { // Full (dense) tensor 2 (negative tensor) 
//        S2 s2(ub2); s2.setAll(-1);
//        Test("SparseTensor getNNonZeros(d2p) 3", s2.getNNonZeros(d2p), d2p.size_elts());
//        Test("SparseTensor getNZeros(d2p) 3", s2.getNZeros(d2p), (UInt)0);
//        Test("SparseTensor isZero(d2p) 3", s2.isZero(d2p), false);
//        Test("SparseTensor isSparse(d2p) 3", s2.isSparse(d2p), false);
//        Test("SparseTensor isDense(d2p) 3", s2.isDense(d2p), true);
//        Test("SparseTensor getFillRate(d2p) 3", s2.getFillRate(d2p), (Real)1);
//      }  
//
//      { // Full (dense) tensor 2 (mixed positive and negative tensor) 
//        S2 s2(ub2); 
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) s2.set(i2, Real(o+1)); else s2.set(i2, Real(-1)); 
//        } 
//        Test("SparseTensor getNNonZeros(d2p) 4", s2.getNNonZeros(d2p), d2p.size_elts());
//        Test("SparseTensor getNZeros(d2p) 4", s2.getNZeros(d2p), (UInt)0);
//        Test("SparseTensor isZero(d2p) 4", s2.isZero(d2p), false);
//        Test("SparseTensor isSparse(d2p) 4", s2.isSparse(d2p), false);
//        Test("SparseTensor isDense(d2p) 4", s2.isDense(d2p), true);
//        Test("SparseTensor getFillRate(d2p) 4", s2.getFillRate(d2p), (Real)1);
//      }  
//
//      { // Sparse tensor 1
//        S2 s2(ub2); 
//        UInt nnz = 0;
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) { s2.set(i2, Real(o+1)); if (d2p.includes(i2)) ++nnz; }
//        } 
//        Test("SparseTensor getNNonZeros(d2p) 5", s2.getNNonZeros(d2p), nnz);
//        Test("SparseTensor getNZeros(d2p) 5", s2.getNZeros(d2p), d2p.size_elts() - nnz);
//        Test("SparseTensor isZero(d2p) 5", s2.isZero(d2p), false);
//        Test("SparseTensor isSparse(d2p) 5", s2.isSparse(d2p), true);
//        Test("SparseTensor isDense(d2p) 5", s2.isDense(d2p), false);
//        Real fr = (Real)nnz / (Real)d2p.size_elts();
//        Test("SparseTensor getFillRate(d2p) 5", s2.getFillRate(d2p), fr);
//      }  
//
//      { // Sparse tensor 2 (negative tensor)
//        S2 s2(ub2); 
//        UInt nnz = 0;
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) { s2.set(i2, -1); if (d2p.includes(i2)) ++nnz; }
//        } 
//        Test("SparseTensor getNNonZeros(d2p) 6", s2.getNNonZeros(d2p), nnz);
//        Test("SparseTensor getNZeros(d2p) 6", s2.getNZeros(d2p), d2p.size_elts() - nnz);
//        Test("SparseTensor isZero(d2p) 6", s2.isZero(d2p), false);
//        Test("SparseTensor isSparse(d2p) 6", s2.isSparse(d2p), true);
//        Test("SparseTensor isDense(d2p) 6", s2.isDense(d2p), false);
//        Real fr = (Real)nnz / (Real)d2p.size_elts();
//        Test("SparseTensor getFillRate(d2p) 6", s2.getFillRate(d2p), fr);
//      }  
//
//      { // Sparse tensor 3 (mixed positive and negative tensor)
//        S2 s2(ub2); 
//        UInt nnz = 0;
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt o = i2.ordinal(ub2);
//          if (o % 2 == 0) { 
//            if (o % 3 == 0)
//              s2.set(i2, -1); 
//            else
//              s2.set(i2, Real(o));
//            if (d2p.includes(i2))
//              ++nnz; 
//          }
//        } 
//        Test("SparseTensor getNNonZeros(d2p) 7", s2.getNNonZeros(d2p), nnz);
//        Test("SparseTensor getNZeros(d2p) 7", s2.getNZeros(d2p), d2p.size_elts() - nnz);
//        Test("SparseTensor isZero(d2p) 7", s2.isZero(d2p), false);
//        Test("SparseTensor isSparse(d2p) 7", s2.isSparse(d2p), true);
//        Test("SparseTensor isDense(d2p) 7", s2.isDense(d2p), false);
//        Real fr = (Real)nnz / (Real)d2p.size_elts();
//        Test("SparseTensor getFillRate(d2p) 7", s2.getFillRate(d2p), fr);
//      }  
//    }
//
//    { // Sparse tensor - domain contains only zeros
//      S2 s2(ub2);
//      ITER_2(ub2[0], ub2[1]) {
//        I2 i2(i, j);
//        UInt o = i2.ordinal(ub2);
//        if (j > ub2[1]/2 && o % 2 == 0)
//          s2.set(i2, Real(o+1));
//      }
//      Domain<UInt> d2e(I2(1, 1), I2(ub2[0]/2, ub2[0]/2));
//      Test("SparseTensor getNNonZeros(d2e)", s2.getNNonZeros(d2e), (UInt)0);
//      Test("SparseTensor getNZeros(d2e)", s2.getNZeros(d2e), d2e.size_elts());
//      Test("SparseTensor isZero(d2e)", s2.isZero(d2e), true);
//      Test("SparseTensor isSparse(d2e)", s2.isSparse(d2e), true);
//      Test("SparseTensor isDense(d2e)", s2.isDense(d2e), false);
//      Test("SparseTensor getFillRate(d2e)", s2.getFillRate(d2e), (Real)0);
//    }
//
//    { // Sparse tensor - domain is dense
//      S2 s2(ub2);
//      UInt nnz = 0;
//      ITER_2(ub2[0], ub2[1]) {
//        I2 i2(i, j);
//        UInt o = i2.ordinal(ub2);
//        if (j > ub2[1]/2) {
//          s2.set(i2, Real(o+1));
//          ++nnz;
//        }      
//      }
//      Domain<UInt> d2f(I2(0, ub2[1]/2+1), I2(ub2[0], ub2[1]));
//      Test("SparseTensor getNNonZeros(d2f)", s2.getNNonZeros(d2f), nnz);
//      Test("SparseTensor getNZeros(d2f)", s2.getNZeros(d2f), (UInt)0);
//      Test("SparseTensor isZero(d2f)", s2.isZero(d2f), false);
//      Test("SparseTensor isSparse(d2f)", s2.isSparse(d2f), false);
//      Test("SparseTensor isDense(d2f)", s2.isDense(d2f), true);
//      Test("SparseTensor getFillRate(d2f)", s2.getFillRate(d2f), (Real)1);
//    }
//
//    { // getNNonZeros per sub-space, sparse tensor
//      S2 s2(ub2); 
//      S1 s1ref1nz(ub2[0]), s1ref2nz(ub2[1]);
//      S1 s1ref1z(ub2[0]), s1ref2z(ub2[1]);
//      ITER_2(ub2[0], ub2[1]) {
//        I2 i2(i, j);
//        UInt o = i2.ordinal(ub2);
//        if (o % 2 == 0) {
//          s2.set(i2, Real(o+1));
//          s1ref1nz.update(I1(UInt(i)), Real(1), std::plus<Real>());
//          s1ref2nz.update(I1(UInt(j)), Real(1), std::plus<Real>());
//        } else {
//          s1ref1z.update(I1(UInt(i)), Real(1), std::plus<Real>());
//          s1ref2z.update(I1(UInt(j)), Real(1), std::plus<Real>());
//        }    
//      }
//
//      // Non-zeros/zeros per row
//      S1 s11nz(ub2[0]), s11z(ub2[0]), fr1(ub2[0]), fr1ref(ub2[0]);    
//      s2.getNNonZeros(I1(UInt(1)), s11nz);
//      Test("SparseTensor sub-space getNNonZeros 1", s11nz == s1ref1nz, true);
//      s2.getNZeros(I1(UInt(1)), s11z);
//      Test("SparseTensor sub-space getNZeros 1", s11z == s1ref1z, true);
//      s2.getFillRate(I1(UInt(1)), fr1);
//      fr1ref = s11nz;
//      fr1ref.element_apply_fast(bind2nd(divides<Real>(), ub2[1]));
//      Test("SparseTensor sub-space getFillRate 1", fr1 == fr1ref, true);
//
//      // Non-zeros/zeros per column
//      S1 s12nz(ub2[1]), s12z(ub2[1]), fr2(ub2[1]), fr2ref(ub2[1]); 
//      s2.getNNonZeros(I1(UInt(0)), s12nz);
//      Test("SparseTensor sub-space getNZeros 2", s12nz == s1ref2nz, true);
//      s2.getNZeros(I1(UInt(0)), s12z);
//      Test("SparseTensor sub-space getNZeros 2", s12z == s1ref2z, true);
//      s2.getFillRate(I1(UInt(0)), fr2);
//      fr2ref = s12nz;
//      fr2ref.element_apply_fast(bind2nd(divides<Real>(), ub2[0]));
//      Test("SparseTensor sub-space getFillRate 2", fr2 == fr2ref, true);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestIsSymmetric()
//  {
//    { // isSymmetric
//      S3 s31(5, 4, 3);
//      Test("SparseTensor isSymmetric 1", s31.isSymmetric(I3(0, 2, 1)), false);
//
//      S3 s32(5, 3, 3);
//      Test("SparseTensor isSymmetric 2", s32.isSymmetric(I3(0, 2, 1)), true);
//      Test("SparseTensor isSymmetric 3", s32.isSymmetric(I3(1, 2, 0)), false);
//    
//      s32.set(I3(0, 0, 1), (Real).5);
//      Test("SparseTensor isSymmetric 4", s32.isSymmetric(I3(0, 2, 1)), false);
//    
//      s32.set(I3(0, 1, 0), (Real).5);
//      Test("SparseTensor isSymmetric 5", s32.isSymmetric(I3(0, 2, 1)), true);
//
//      S2 s21(5, 5);
//      for (UInt i = 0; i < 5; ++i)
//        for (UInt j = i; j < 5; ++j) {
//          s21.set(I2(i, j), (Real)(i*5+j+1));
//          s21.set(I2(j, i), s21(i, j));
//        }
//
//      Test("SparseTensor isSymmetric 6", s21.isSymmetric(I2(1, 0)), true);
//    }
//
//    { // isAntiSymmetric
//      S3 s31(5, 4, 3);
//      Test("SparseTensor isAntiSymmetric 1", s31.isAntiSymmetric(I3(0, 2, 1)), false);
//
//      S3 s32(5, 3, 3);
//      Test("SparseTensor isAntiSymmetric 2", s32.isAntiSymmetric(I3(0, 2, 1)), true);
//      Test("SparseTensor isAntiSymmetric 3", s32.isAntiSymmetric(I3(1, 2, 0)), false);
//
//      s32.set(I3(0, 0, 1), (Real).5);
//      Test("SparseTensor isAntiSymmetric 4", s32.isAntiSymmetric(I3(0, 2, 1)), false);
//    
//      s32.set(I3(0, 1, 0), (Real)-.5);
//      Test("SparseTensor isAntiSymmetric 5", s32.isAntiSymmetric(I3(0, 2, 1)), true);
//
//      S2 s21(5, 5);
//      for (UInt i = 0; i < 5; ++i)
//        for (UInt j = i; j < 5; ++j) {
//          s21.set(I2(i, j), (Real)(i*5+j+1));
//          s21.set(I2(j, i), - s21(i, j));
//        }
//
//      Test("SparseTensor isAntiSymmetric 6", s21.isAntiSymmetric(I2(1, 0)), false);
//
//      for (UInt i = 0; i < 5; ++i)
//        s21.set(I2(i, i), (Real) 0);
//
//      Test("SparseTensor isAntiSymmetric 7", s21.isAntiSymmetric(I2(1, 0)), true);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestToFromDense()
//  {
//    I4 ub(5, 4, 3, 2);
//    
//    {
//      S4 s4(ub);
//      D4 d4(ub);
//
//      ITER_4(ub[0], ub[1], ub[2], ub[3]) {
//        I4 idx(i, j, k, l);
//        s4.setNonZero(idx, Real(idx.ordinal(ub)+1));
//      }  
//        
//      Real array[5*4*3*2];
//      s4.toDense(array);
//      d4.clear();
//      d4.fromDense(array);
//      Test("SparseTensor toDense 2", Compare(s4, d4), true);
//    }
//
//    {   
//      S4 s4(ub);
//      D4 d4(ub);
//      
//      ITER_4(ub[0], ub[1], ub[2], ub[3]) {
//        I4 idx(i, j, k, l);
//        d4.set(idx, Real(idx.ordinal(ub)+1));
//      }
//      
//      Real array[5*4*3*2];
//      d4.toDense(array);
//      s4.clear();
//      s4.fromDense(array);
//      Test("SparseTensor fromDense 2", Compare(s4, d4), true);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestPermute()
//  {
//    D2 d2(5, 4);
//    S2 s2(5, 4);
//    
//    ITER_2(5, 4) {
//      d2.set(I2(i, j), Real(i*4+j+1));
//      s2.set(I2(i, j), Real(i*4+j+1));
//    }
//        
//    d2.permute(I2(1, 0));
//    s2.permute(I2(1, 0));
//    
//    Test("SparseTensor permute 1", Compare(s2, d2), true);
//
//    D3 d3(5, 4, 3);
//    S3 s3(5, 4, 3);
//    
//    ITER_3(5, 4, 3) {
//      d3.set(I3(i, j, k), (i*12+j*3+k) % 2 == 0 ? Real(i*12*j*3+k) : Real(0));
//      s3.set(I3(i, j, k), d3.get(i, j, k));
//    }
//    
//    d3.permute(I3(1, 0, 2));
//    s3.permute(I3(1, 0, 2));
//    
//    Test("SparseTensor permute 2", Compare(s3, d3), true);
//
//    d3.permute(I3(2, 0, 1));
//    s3.permute(I3(2, 0, 1));
//    
//    Test("SparseTensor permute 3", Compare(s3, d3), true);
//
//    d3.permute(I3(1, 2, 0));
//    s3.permute(I3(1, 2, 0));
//    
//    Test("SparseTensor permute 4", Compare(s3, d3), true);
//
//    d3.permute(I3(2, 1, 0));
//    s3.permute(I3(2, 1, 0));
//    
//    Test("SparseTensor permute 5", Compare(s3, d3), true);
//
//    d3.permute(I3(0, 2, 1));
//    s3.permute(I3(0, 2, 1));
//    
//    Test("SparseTensor permute 6", Compare(s3, d3), true);
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestResize()
//  {
//    {   
//      D2 d2(3, 4); S2 s2(3, 4);
//      ITER_2(3, 4) {
//        d2.set(I2(i, j), Real(i*4+j));
//        s2.set(I2(i, j), d2(i, j));
//      }
//
//      {
//        d2.resize(I2(3, 4));
//        s2.resize(I2(3, 4));
//        Test("SparseTensor resize 0", Compare(s2, d2), true);
//      }
//
//      {
//        d2.resize(I2(3, 5));
//        s2.resize(I2(3, 5));
//        Test("SparseTensor resize 1", Compare(s2, d2), true);
//      }
//
//      {
//        d2.resize(I2(4, 5));
//        s2.resize(I2(4, 5));
//        Test("SparseTensor resize 2", Compare(s2, d2), true);
//      }
//
//      {
//        d2.resize(I2(5, 6));
//        s2.resize(I2(5, 6));
//        Test("SparseTensor resize 3", Compare(s2, d2), true);
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestReshape()
//  {
//    {
//      D2 d2(3, 4), d2r(3, 4);
//      S2 s2(3, 4), s2r(3, 4);
//      
//      ITER_2(3, 4) {
//        d2.set(I2(i, j), Real(i*4+j));
//        s2.set(I2(i, j), d2(i, j));
//      }
//      
//      d2.reshape(d2r);
//      s2.reshape(s2r);
//      Test("SparseTensor reshape 0", Compare(s2r, d2r), true);
//    }
//
//    {
//      D2 d2(3, 4), d2r(2, 6);
//      S2 s2(3, 4), s2r(2, 6);
//      
//      ITER_2(3, 4) {
//        d2.set(I2(i, j), Real(i*4+j));
//        s2.set(I2(i, j), d2(i, j));
//      }
//  
//      d2.reshape(d2r);
//      s2.reshape(s2r);
//      Test("SparseTensor reshape 1", Compare(s2r, d2r), true);
//    }
//
//    {
//      D2 d2(3, 4); S2 s2(3, 4);
//      D3 d3r(2, 2, 3); S3 s3r(2, 2, 3);
//      
//      ITER_2(3, 4) {
//        d2.set(I2(i, j), Real(i*4+j));
//        s2.set(I2(i, j), d2(i, j));
//      }
//      
//      d2.reshape(d3r);
//      s2.reshape(s3r);
//      Test("SparseTensor reshape 2", Compare(s3r, d3r), true);
//    }
//
//    {
//      D3 d3(2, 2, 3); S3 s3(2, 2, 3);
//      D2 d2r(3, 4); S2 s2r(3, 4);
//      
//      ITER_3(2, 2, 3) {
//        d3.set(I3(i, j, k), Real(i*6+j*3+k));
//        s3.set(I3(i, j, k), d3(i, j, k));
//      }
//      
//      d3.reshape(d2r);
//      s3.reshape(s2r);
//      Test("SparseTensor reshape 3", Compare(s2r, d2r), true);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestSlice()
//  {
//    { // All possible slicings in 3D
//      I3 ub(5, 4, 3);
//      S3 s3(ub);
//      
//      ITER_3(ub[0], ub[1], ub[2]) {
//        I3 i3(i, j, k);
//        s3.set(i3, (Real)(i3.ordinal(ub)));
//      }
//      
//      for (UInt m = 1; m <= 2; ++m) {
//      
//        { // Extract a vector from the S3
//          S1 s1(ub[0]/m), ref(ub[0]/m);
//          ITER_2(ub[1], ub[2]) {
//            for (UInt n = 0; n < ub[0]/m; ++n) 
//              ref.set(I1((UInt)n), Real(n*ub[2]*ub[1] + i*ub[2]+j));
//            Domain<UInt> d(I3(0, i, j), I3(ub[0]/m, i, j));
//            s3.getSlice(d, s1);
//            Test("SparseTensor getSlice 1", s1, ref);
//          }
//        }
//
//        { // Extract a vector from the S3
//          S1 s1(ub[1]/m), ref(ub[1]/m);
//          ITER_2(ub[0], ub[2]) {
//            for (UInt n = 0; n < ub[1]/m; ++n)
//              ref.set(I1((UInt)n), Real(i*ub[2]*ub[1] + n*ub[2]+j));
//            Domain<UInt> d(I3(i, 0, j), I3(i, ub[1]/m, j));
//            s3.getSlice(d, s1);
//            Test("SparseTensor getSlice 2", s1, ref);
//          }
//        }
//
//        { // Extract a vector from the S3
//          S1 s1(ub[2]/m), ref(ub[2]/m);
//          ITER_2(ub[0], ub[1]) {
//            for (UInt n = 0; n < ub[2]/m; ++n)
//              ref.set(I1((UInt)n), Real(i*ub[2]*ub[1] + j*ub[2]+n));
//            Domain<UInt> d(I3(i, j, 0), I3(i, j, ub[2]/m));
//            s3.getSlice(d, s1);
//            Test("SparseTensor getSlice 3", s1, ref);
//          }
//        }
//      }
//
//      { // Extract a S2 from the S3
//        S2 s2(ub[1], ub[2]), ref(ub[1], ub[2]);
//        for (UInt n = 0; n < ub[0]; ++n) {
//          Domain<UInt> d(I3(n, 0, 0), I3(n, ub[1], ub[2]));
//          ITER_2(ub[1], ub[2])
//            ref.set(I2(i, j), (Real)(n*ub[2]*ub[1]+i*ub[2]+j));
//          s3.getSlice(d, s2);
//          Test("SparseTensor getSlice 4", s2, ref);
//        }
//      }
//
//      { // Extract a S2 from the S3
//        S2 s2(ub[0], ub[2]), ref(ub[0], ub[2]);
//        for (UInt n = 0; n < ub[1]; ++n) {
//          Domain<UInt> d(I3(0, n, 0), I3(ub[0], n, ub[2]));
//          ITER_2(ub[0], ub[2])
//            ref.set(I2(i, j), (Real)(i*ub[1]*ub[2]+n*ub[2]+j));
//          s3.getSlice(d, s2);
//          Test("SparseTensor getSlice 5", s2, ref);
//        }
//      }
//
//      { // Extract a S2 from the S3
//        S2 s2(ub[0], ub[1]), ref(ub[0], ub[1]);
//        for (UInt n = 0; n < ub[2]; ++n) {
//          Domain<UInt> d(I3(0, 0, n), I3(ub[0], ub[1], n));
//          ITER_2(ub[0], ub[1])
//            ref.set(I2(i, j), (Real)(i*ub[1]*ub[2]+j*ub[2]+n));
//          s3.getSlice(d, s2);
//          Test("SparseTensor getSlice 6", s2, ref);
//        }
//      }
//
//      { // Extract a S3 from the S3
//        S3 s32(ub[0], ub[1], ub[2]), ref(ub[0], ub[1], ub[2]);
//        Domain<UInt> d(I3(0, 0, 0), I3(ub[0], ub[1], ub[2]));
//        ITER_3(ub[0], ub[1], ub[2])
//          ref.set(I3(i, j, k), (Real)(i*ub[2]*ub[1]+j*ub[2]+k));
//        s3.getSlice(d, s32);
//        Test("SparseTensor getSlice 7", s32, ref);
//      }
//    } 
//    
//    { // Make sure the slice is correctly situated   
//      I2 ub2(4, 5);
//      S2 s2a(ub2), s2b(I2(2, 2)); GenerateOrdered(s2a);
//      Domain<UInt> d2(I2(2, 2), I2(4, 4));
//      s2a.getSlice(d2, s2b);
//    }
//  
//    { // Make sure the slice is correctly situated
//      I2 ub2(4, 5);
//      S2 s2a(ub2), s2b(I2(2, 2)); GenerateOrdered(s2b);
//      Domain<UInt> d2(I2(2, 2), I2(4, 4));
//      s2a.setSlice(d2, s2b);
//    }
//
//    { // Random slicings, including slices that do not start at zero
//      I4 ub4(5, 4, 3, 2);
//      UInt nreps = 10;
//
//      S4 s4A(ub4); D4 d4A(ub4);
//
//      ITER_4(ub4[0], ub4[1], ub4[2], ub4[3]) {
//        I4 i4(i, j, k, l);
//        Real val = i4.ordinal(ub4) % 2 == 0 ? Real(0) : Real(i4.ordinal(ub4)+1);
//        d4A.set(i4, val);
//        s4A.set(i4, val);
//      }
//
//      for (UInt i = 0; i < nreps; ++i) {
//        
//        I4 lb, ub;
//        for (UInt j = 0; j < 4; ++j) {
//          lb[j] = rng_->getUInt32(ub4[j]);
//          ub[j] = rng_->getUInt32(ub4[j]);
//          if (ub[j] < lb[j])
//            ub[j] = lb[j];
//        }
//
//        Domain<UInt> d(lb, ub);
//
//        switch (d.getNOpenDims()) {
//        
//        case 4: 
//          {
//            S4 s4B(ub4); D4 d4B(ub4);
//            // put garbage in the slices
//            s4A.getSlice(d, s4B); d4A.getSlice(d, d4B);
//            Test("SparseTensor getSlice 8-1", Compare(s4B, d4B), true);
//            break;
//          }
//          
//        case 3:   
//          {
//            UInt M = ub.max();
//            I3 ub3(M, M, M);
//            S3 s3B(ub3); D3 d3B(ub3);
//            s4A.getSlice(d, s3B); d4A.getSlice(d, d3B);
//            Test("SparseTensor getSlice 8-2", Compare(s3B, d3B), true);
//            break;
//          }
//
//        case 2:
//          {
//            UInt M = ub.max();
//            I2 ub2(M, M);
//            S2 s2B(ub2); D2 d2B(ub2);
//            s4A.getSlice(d, s2B); d4A.getSlice(d, d2B);
//            Test("SparseTensor getSlice 8-3", Compare(s2B, d2B), true);
//            break;
//          }
//
//        case 1:
//          {
//            UInt M = ub.max();
//            I1 ub1(M);
//            S1 s1B(ub1); D1 d1B(ub1);
//            s4A.getSlice(d, s1B); d4A.getSlice(d, d1B);
//            Test("SparseTensor getSlice 8-4", Compare(s1B, d1B), true);
//            break;
//          }
//        default: { break; }
//        }
//      }
//    }
//
//    // setSlice
//    {    
//      I3 ub3(3, 3, 2);   
//      S3 s3A(ub3);
//
//      // Setting 1D slices of zeros on empty
//      S1 empty(ub3[2]);
//      for (UInt i = 0; i < ub3[0]; ++i) 
//        s3A.setSlice(Domain<UInt>(I3(i,i,0), I3(i,i,ub3[2])), empty);
//      Test("SparseTensor setSlice 1", s3A.isZero(), true);
//
//      // Setting 1D slices of zeros on non-empty
//      GenerateRandRand01(rng_, s3A);    
//      for (UInt i = 0; i < ub3[0]; ++i) 
//        for (UInt j = 0; j < ub3[1]; ++j)
//          s3A.setSlice(Domain<UInt>(I3(i,j,0), I3(i,j,ub3[2])), empty);
//      Test("SparseTensor setSlice 2", s3A.isZero(), true);
//
//      // Setting 2D slices of zeros on empty
//      s3A.setAll(0);
//      S2 empty2(ub3[1], ub3[2]);
//      for (UInt i = 0; i < ub3[0]; ++i) 
//        s3A.setSlice(Domain<UInt>(I3(i,0,0), I3(i,ub3[1],ub3[2])), empty2);
//      Test("SparseTensor setSlice 3", s3A.isZero(), true);
//
//      // Setting 2D slices of zeros on non-empty
//      GenerateRandRand01(rng_, s3A);
//      for (UInt i = 0; i < ub3[0]; ++i) 
//        s3A.setSlice(Domain<UInt>(I3(i,0,0), I3(i,ub3[1],ub3[2])), empty2);
//      Test("SparseTensor setSlice 4", s3A.isZero(), true);
//
//      // Setting 3D slice of zeros on empty
//      s3A.setAll(0);
//      S3 empty3(ub3);
//      s3A.setSlice(Domain<UInt>(I3(0,0,0), ub3), empty3);
//      Test("SparseTensor setSlice 5", s3A.isZero(), true);
//
//      // Setting 3D slice of zeros on non-empty
//      GenerateRandRand01(rng_, s3A);
//      s3A.setSlice(Domain<UInt>(I3(0,0,0), ub3), empty3);
//      Test("SparseTensor setSlice 6", s3A.isZero(), true);
//         
//      // Setting 1D slices of non-zeros
//      S1 s1(ub3[2]); s1.setAll(1);
//      for (UInt i = 0; i < ub3[0]; ++i) 
//        s3A.setSlice(Domain<UInt>(I3(i,i,0), I3(i,i,ub3[2])), s1);
//      I3 idx;
//      do {
//        if (idx[0] == idx[1])
//          Test("SparseTensor setSlice 7", s3A.get(idx), (Real)1);
//        else
//          Test("SparseTensor setSlice 8", s3A.isZero(idx), true);
//      } while (increment(ub3, idx));
//      
//      s3A.setAll(0); setToZero(idx);
//
//      // Setting 2D slices of non-zeros
//      S2 s2(ub3[1], ub3[2]); s2.setAll(1);
//      for (UInt i = 0; i < ub3[0]-1; ++i)
//        s3A.setSlice(Domain<UInt>(I3(i,0,0), I3(i,ub3[1],ub3[2])), s2);
//      do {
//        if (idx[0] < ub3[0]-1)
//          Test("SparseTensor setSlice 9", s3A.get(idx), (Real)1);
//        else
//          Test("SparseTensor setSlice 10", s3A.isZero(idx), true);
//      } while (increment(ub3, idx));
//
//      s3A.setAll(0); setToZero(idx);
//
//      // Setting a 3D slice of non-zeros
//      S3 s3(ub3); s3.setAll(1);
//      s3A.setSlice(Domain<UInt>(I3(0,0,0), ub3), s3);
//      Test("SparseTensor setSlice 11", s3A == s3, true);
//    }
//
//    { // setSlice of all zeros in 4D
//      I4 ub4(2, 3, 2, 3);
//      S4 s4A(ub4);
//      s4A.set(I4(0,0,1,0), 3.5);
//      s4A.set(I4(0,1,1,2), Real(4.7)); // will stay [1] != [3]
//      s4A.set(I4(1,1,0,2), Real(7.8)); // will stay [1] != [3]
//      s4A.set(I4(1,1,1,1), Real(9.3));
//      S2 s2(I2(2, 2));
//      for (UInt i = 0; i < 3; ++i)
//        s4A.setSlice(Domain<UInt>(I4(0,i,0,i), I4(2,i,2,i)), s2);
//      Test("SparseTensor setSlice 12", s4A.getNNonZeros(), (UInt)2);
//      Test("SparseTensor setSlice 13", s4A.get(I4(0,1,1,2)), (Real)4.7);
//      Test("SparseTensor setSlice 14", s4A.get(I4(1,1,0,2)), (Real)7.8);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestElementApply()
//  {
//    I3 ub(3, 4, 2);
//    
//    S3 s3A(ub), s3B(ub), s3C(ub);
//    D3 d3A(ub), d3B(ub), d3C(ub);
//    
//    ITER_3(ub[0], ub[1], ub[2]) {
//      Real v = Real(i*ub[1]*ub[2]+j*ub[2]+k);
//      if (I3(i, j, k).ordinal(ub) % 2 == 0) {
//        s3A.set(I3(i, j, k), v);
//        d3A.set(I3(i, j, k), v);
//      } else {
//        s3B.set(I3(i, j, k), v+1);
//        d3B.set(I3(i, j, k), v+1);
//      }
//    }    
//
//    { // Test with functor that introduces new zeros
//      // (to exercise deletion in map/set and iterator invalidation)
//      s3A.element_apply(bind2nd(nta::Multiplies<Real>(), 0));
//      Test("SparseTensor unary element_apply 5", s3A.isZero(), true);
//      d3A.element_apply(bind2nd(nta::Multiplies<Real>(), 0));
//    }
//
//    { // unary element_apply
//      s3A.element_apply(Threshold(3));
//      d3A.element_apply(Threshold(3));
//      Test("SparseTensor unary element_apply 3A", Compare(s3A, d3A), true);
//
//      d3A.element_apply(Threshold(3));
//      s3A.element_apply_fast(Threshold(3));
//      Test("SparseTensor unary element_apply 3B", Compare(s3A, d3A), true);
//
//      d3A.element_apply(Plus3());
//      s3A.element_apply(Plus3());
//      Test("SparseTensor unary element_apply 4A", Compare(s3A, d3A), true);
//
//      /*
//      try {   
//        s3A.element_apply_fast(Plus3());
//        Test("SparseTensor unary element_apply 4B", 0, 1);
//      } catch (std::runtime_error& e) {
//        Test("SparseTensor unary element_apply 4B", 1, 1);
//      }
//      */
//    }
//
//    { // element_apply_fast
//      d3A.element_apply(d3B, d3C, nta::Multiplies<Real>());
//      s3A.element_apply_fast(s3B, s3C, nta::Multiplies<Real>());
//      Test("SparseTensor element_apply_fast 1", Compare(s3C, d3C), true);
//
//      /*
//      try {
//        s3A.element_apply_fast(s3B, s3C, std::plus<Real>());
//        Test("SparseTensor element_apply_fast 2", 0, 1);
//      } catch (std::runtime_error& e) {
//        Test("SparseTensor element_apply_fast 2", 1, 1);
//      }
//      */
//    }
//
//    { // element_apply_nz
//      d3A.element_apply(d3B, d3C, std::plus<Real>());
//      s3A.element_apply_nz(s3B, s3C, std::plus<Real>());
//      Test("SparseTensor element_apply_nz 1", Compare(s3C, d3C), true);
//
//      d3A.element_apply(d3B, d3C, nta::Multiplies<Real>());
//      s3A.element_apply_nz(s3B, s3C, nta::Multiplies<Real>());
//      Test("SparseTensor element_apply_nz 2", Compare(s3C, d3C), true);
//
//      /*
//      try {
//        s3A.element_apply_nz(s3B, s3C, BinaryPlus3());
//        Test("SparseTensor element_apply_nz 3", 0, 1);
//      } catch (std::runtime_error& e) {
//        Test("SparseTensor element_apply_nz 3", 1, 1);
//      }
//      */
//    }
//
//    { // general element_apply
//      d3A.element_apply(d3B, d3C, std::plus<Real>());
//      s3A.element_apply(s3B, s3C, std::plus<Real>());
//      Test("SparseTensor element_apply 1", Compare(s3C, d3C), true);
//
//      d3A.element_apply(d3B, d3A, std::plus<Real>());
//      s3A.element_apply(s3B, s3A, std::plus<Real>());
//      Test("SparseTensor element_apply 2", Compare(s3A, d3A), true);
//
//      d3A.element_apply(d3B, d3C, nta::Multiplies<Real>());
//      s3A.element_apply(s3B, s3C, nta::Multiplies<Real>());
//      Test("SparseTensor element_apply 3", Compare(s3C, d3C), true);
//
//      d3A.element_apply(d3B, d3A, nta::Multiplies<Real>());
//      s3A.element_apply(s3B, s3A, nta::Multiplies<Real>());
//      Test("SparseTensor element_apply 4", Compare(s3A, d3A), true);
//      
//      s3A.element_apply(s3B, s3C, BinaryPlus3());
//      d3A.element_apply(d3B, d3C, BinaryPlus3());
//      Test("SparseTensor element_apply 5", Compare(s3A, d3A), true);
//    }
//
//    { // With lots of zeros
//      I2 ub(3, 4);
//          
//      S2 s2(ub), sc2(ub);
//      D2 d2(ub), dc2(ub);
//
//      s2.set(I2(1, 1), (Real)1);
//      d2.set(I2(1, 1), (Real)1);
//        
//      S2 s2B(ub); s2B.set(I2(2, 2), (Real)1);
//      D2 d2B(ub); d2B.set(I2(2, 2), (Real)1);
//
//      d2.element_apply(d2B, dc2, nta::Multiplies<Real>());
//      s2.element_apply_fast(s2B, sc2, nta::Multiplies<Real>());
//      Test("SparseTensor element_apply 5A1", Compare(sc2, dc2), true);
//      Test("SparseTensor element_apply 5A2", sc2.isZero(), true);
//      Test("SparseTensor element_apply 5A3", dc2.isZero(), true);
//   
//      s2.element_apply_nz(s2B, sc2, nta::Multiplies<Real>());
//      Test("SparseTensor element_apply 6A1", Compare(sc2, dc2), true);
//      Test("SparseTensor element_apply 6A2", sc2.isZero(), true);
//
//      s2.element_apply(s2B, sc2, nta::Multiplies<Real>());
//      Test("SparseTensor element_apply 7A1", Compare(sc2, dc2), true);
//      Test("SparseTensor element_apply 7A2", sc2.isZero(), true);
//
//      d2.element_apply(d2B, dc2, std::plus<Real>());
//      s2.element_apply_nz(s2B, sc2, std::plus<Real>());
//      Test("SparseTensor element_apply 8A1", Compare(sc2, dc2), true);
//      Test("SparseTensor element_apply 8A2", sc2.getNNonZeros(), (UInt)2);
//      Test("SparseTensor element_apply 8A3", dc2.getNNonZeros(), (UInt)2);
//
//      d2.element_apply(d2B, dc2, std::plus<Real>());
//      s2.element_apply(s2B, sc2, std::plus<Real>());
//      Test("SparseTensor element_apply 9A1", Compare(sc2, dc2), true);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestFactorApply()
//  {
//    { // 2X1
//      I2 ub(7, 5);
//
//      S2 s2(ub), sc2(ub);
//      D2 d2(ub), dc2(ub);
//        
//      ITER_2(ub[0], ub[1]) {
//        if (I2(i, j).ordinal(ub) % 2 == 0) {
//          d2.set(I2(i, j), Real(i*ub[1]+j));
//          s2.set(I2(i, j), Real(i*ub[1]+j));
//        }
//      }
//
//      for (UInt n = 0; n < 2; ++n) {
//        
//        S1 s1(ub[n]); 
//        D1 d1(ub[n]); 
//        
//        ITER_1(ub[n]) {
//          if (i % 2 == 0) {
//            s1.set(I1((UInt)i), Real(i+2));
//            d1.set(I1((UInt)i), Real(i+2));
//          }
//        }
//
//        d2.factor_apply(I1(n), d1, dc2, nta::Multiplies<Real>());
//        s2.factor_apply_fast(I1(n), s1, sc2, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 1A", Compare(sc2, dc2), true);
//
//        d2.factor_apply(I1(n), d1, dc2, nta::Multiplies<Real>());
//        s2.factor_apply_nz(I1(n), s1, sc2, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 1B", Compare(sc2, dc2), true);
//
//        d2.factor_apply(I1(n), d1, dc2, nta::Multiplies<Real>());
//        s2.factor_apply(I1(n), s1, sc2, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 1C", Compare(sc2, dc2), true);
//        
//        d2.factor_apply(I1(n), d1, d2, nta::Multiplies<Real>());
//        s2.factor_apply(I1(n), s1, s2, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 2A", Compare(s2, d2), true);
//
//        d2.factor_apply(I1(n), d1, dc2, std::plus<Real>());
//        s2.factor_apply_nz(I1(n), s1, sc2, std::plus<Real>());
//        Test("SparseTensor factor_apply 3A", Compare(sc2, dc2), true);
//
//        d2.factor_apply(I1(n), d1, dc2, std::plus<Real>());
//        s2.factor_apply(I1(n), s1, sc2, std::plus<Real>());
//        Test("SparseTensor factor_apply 3B", Compare(sc2, dc2), true);
//
//        d2.factor_apply(I1(n), d1, d2, std::plus<Real>());
//        s2.factor_apply(I1(n), s1, s2, std::plus<Real>());
//        Test("SparseTensor factor_apply 4A", Compare(s2, d2), true);
//      }
//
//      {
//        s2.clear();
//        d2.clear();
//        s2.set(1, 1, (Real)1);   
//        d2.set(1, 1, (Real)1);
//        
//        S1 s1(ub[1]); s1.set(2, (Real)1);
//        D1 d1(ub[1]); d1.set(2, (Real)1);
//
//        d2.factor_apply(I1(1), d1, dc2, nta::Multiplies<Real>());
//        s2.factor_apply_fast(I1(1), s1, sc2, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 5A1", Compare(sc2, dc2), true);
//        Test("SparseTensor factor_apply 5A2", sc2.isZero(), true);
//        Test("SparseTensor factor_apply 5A3", dc2.isZero(), true);
//
//        s2.factor_apply_nz(I1(1), s1, sc2, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 6A1", Compare(sc2, dc2), true);
//        Test("SparseTensor factor_apply 6A2", sc2.isZero(), true);
//
//        s2.factor_apply(I1(1), s1, sc2, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 7A1", Compare(sc2, dc2), true);
//        Test("SparseTensor factor_apply 7A2", sc2.isZero(), true);
//
//        d2.factor_apply(I1(1), d1, dc2, std::plus<Real>());
//        s2.factor_apply_nz(I1(1), s1, sc2, std::plus<Real>());
//        Test("SparseTensor factor_apply 8A1", Compare(sc2, dc2), true);
//
//        d2.factor_apply(I1(1), d1, dc2, std::plus<Real>());
//        s2.factor_apply(I1(1), s1, sc2, std::plus<Real>());
//        Test("SparseTensor factor_apply 9A1", Compare(sc2, dc2), true);
//      }
//    }
//
//    {
//      I3 ub(5, 4, 3);
//      D3 d3(ub), dc3(ub);
//      S3 s3(ub), sc3(ub);
//        
//      ITER_3(ub[0], ub[1], ub[2]) { 
//        I3 i3(i, j, k); 
//        if (i3.ordinal(ub) % 2 == 0) {
//          d3.set(i3, Real(i3.ordinal(ub))); 
//          s3.set(i3, Real(i3.ordinal(ub))); 
//        }
//      }
//
//      // 3X1
//      for (UInt n = 0; n < 3; ++n) {
//
//        D1 d1(ub[n]); 
//        S1 s1(ub[n]);
//        
//        ITER_1(ub[n]) {
//          if (n % 2 == 0) {
//            d1.set(I1((UInt)i), Real(i+2));
//            s1.set(I1((UInt)i), Real(i+2));
//          }
//        }
//        
//        d3.factor_apply(I1((UInt)n), d1, dc3, nta::Multiplies<Real>());
//        s3.factor_apply_fast(I1((UInt)n), s1, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 10A", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I1((UInt)n), d1, dc3, nta::Multiplies<Real>());
//        s3.factor_apply_nz(I1((UInt)n), s1, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 10B", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I1((UInt)n), d1, dc3, nta::Multiplies<Real>());
//        s3.factor_apply(I1((UInt)n), s1, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 10C", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I1((UInt)n), d1, d3, nta::Multiplies<Real>());
//        s3.factor_apply(I1((UInt)n), s1, s3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 11A", Compare(s3, d3), true);
//
//        d3.factor_apply(I1((UInt)n), d1, dc3, std::plus<Real>());
//        s3.factor_apply_nz(I1((UInt)n), s1, sc3, std::plus<Real>());
//        Test("SparseTensor factor_apply 12A", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I1((UInt)n), d1, dc3, std::plus<Real>());
//        s3.factor_apply(I1((UInt)n), s1, sc3, std::plus<Real>());
//        Test("SparseTensor factor_apply 12B", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I1((UInt)n), d1, d3, std::plus<Real>());
//        s3.factor_apply(I1((UInt)n), s1, s3, std::plus<Real>());
//        Test("SparseTensor factor_apply 13A", Compare(s3, d3), true);
//      }
//
//      { // 3X2   
//        I2 ub2(ub[1], ub[2]);
//        D2 d2(ub2); 
//        S2 s2(ub2);
//        
//        ITER_2(ub[1], ub[2]) {
//          if (I2(i, j).ordinal(ub2) % 2 == 0) {
//            d2.set(I2(i, j), Real(i*ub[2]+j+2));
//            s2.set(I2(i, j), Real(i*ub[2]+j+2));
//          }
//        }
//        
//        d3.factor_apply(I2(1, 2), d2, dc3, nta::Multiplies<Real>());
//        s3.factor_apply_fast(I2(1, 2), s2, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 14A", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I2(1, 2), d2, dc3, nta::Multiplies<Real>());
//        s3.factor_apply_nz(I2(1, 2), s2, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 14B", Compare(sc3, dc3), true);
//        
//        d3.factor_apply(I2(1, 2), d2, dc3, nta::Multiplies<Real>());
//        s3.factor_apply(I2(1, 2), s2, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 14C", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I2(1, 2), d2, d3, nta::Multiplies<Real>());
//        s3.factor_apply(I2(1, 2), s2, s3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 15A", Compare(s3, d3), true);
//
//        d3.factor_apply(I2(1, 2), d2, dc3, std::plus<Real>());
//        s3.factor_apply_nz(I2(1, 2), s2, sc3, std::plus<Real>());
//        Test("SparseTensor factor_apply 16A", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I2(1, 2), d2, dc3, std::plus<Real>());
//        s3.factor_apply(I2(1, 2), s2, sc3, std::plus<Real>());
//        Test("SparseTensor factor_apply 16B", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I2(1, 2), d2, d3, std::plus<Real>());
//        s3.factor_apply(I2(1, 2), s2, s3, std::plus<Real>());
//        Test("SparseTensor factor_apply 17A", Compare(s3, d3), true);
//      }
//
//      { // 3X2   
//        I2 ub2(ub[0], ub[2]);
//        D2 d2(ub2); 
//        S2 s2(ub2);
//        
//        ITER_2(ub[0], ub[2]) {
//          if (I2(i, j).ordinal(ub2) % 2 == 0) {
//            d2.set(I2(i, j), Real(i*ub[2]+j+2));
//            s2.set(I2(i, j), Real(i*ub[2]+j+2));
//          }
//        }
//        
//        d3.factor_apply(I2(0, 2), d2, dc3, nta::Multiplies<Real>());
//        s3.factor_apply(I2(0, 2), s2, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 18", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I2(0, 2), d2, d3, nta::Multiplies<Real>());
//        s3.factor_apply(I2(0, 2), s2, s3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 19", Compare(s3, d3), true);
//
//        d3.factor_apply(I2(0, 2), d2, dc3, std::plus<Real>());
//        s3.factor_apply(I2(0, 2), s2, sc3, std::plus<Real>());
//        Test("SparseTensor factor_apply 20", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I2(0, 2), d2, d3, std::plus<Real>());
//        s3.factor_apply(I2(0, 2), s2, s3, std::plus<Real>());
//        Test("SparseTensor factor_apply 21", Compare(s3, d3), true);
//      }
//
//      { // 3X2   
//        I2 ub2(ub[0], ub[1]);
//        D2 d2(ub2); 
//        S2 s2(ub2);
//        
//        ITER_2(ub[0], ub[1]) {
//          if (I2(i, j).ordinal(ub2) % 2 == 0) {
//            d2.set(I2(i, j), Real(i*ub[2]+j+2));
//            s2.set(I2(i, j), Real(i*ub[2]+j+2));
//          }
//        }
//        
//        d3.factor_apply(I2(0, 1), d2, dc3, nta::Multiplies<Real>());
//        s3.factor_apply(I2(0, 1), s2, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 22", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I2(0, 1), d2, d3, nta::Multiplies<Real>());
//        s3.factor_apply(I2(0, 1), s2, s3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 23", Compare(s3, d3), true);
//
//        d3.factor_apply(I2(0, 1), d2, dc3, std::plus<Real>());
//        s3.factor_apply(I2(0, 1), s2, sc3, std::plus<Real>());
//        Test("SparseTensor factor_apply 24", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I2(0, 1), d2, d3, std::plus<Real>());
//        s3.factor_apply(I2(0, 1), s2, s3, std::plus<Real>());
//        Test("SparseTensor factor_apply 25", Compare(s3, d3), true);
//      }
//
//      { // 3X3
//        D3 d32(ub);    
//        S3 s32(ub);
//
//        ITER_3(ub[0], ub[1], ub[2]) { 
//          I3 i3(i, j, k); 
//          if (i3.ordinal(ub) % 2 == 0) {
//            d32.set(i3, Real(i3.ordinal(ub)+1));     
//            s32.set(i3, Real(i3.ordinal(ub)+1));
//          }
//        }
//
//        d3.factor_apply(I3(0, 1, 2), d32, dc3, nta::Multiplies<Real>());
//        s3.factor_apply_fast(I3(0, 1, 2), s32, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 26A", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I3(0, 1, 2), d32, dc3, nta::Multiplies<Real>());
//        s3.factor_apply_nz(I3(0, 1, 2), s32, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 26B", Compare(sc3, dc3), true);
//        
//        d3.factor_apply(I3(0, 1, 2), d32, dc3, nta::Multiplies<Real>());
//        s3.factor_apply(I3(0, 1, 2), s32, sc3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 26C", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I3(0, 1, 2), d32, d3, nta::Multiplies<Real>());
//        s3.factor_apply(I3(0, 1, 2), s32, s3, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 27A", Compare(s3, d3), true);
//
//        d3.factor_apply(I3(0, 1, 2), d32, dc3, std::plus<Real>());
//        s3.factor_apply_nz(I3(0, 1, 2), s32, sc3, std::plus<Real>());
//        Test("SparseTensor factor_apply 28A", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I3(0, 1, 2), d32, dc3, std::plus<Real>());
//        s3.factor_apply(I3(0, 1, 2), s32, sc3, std::plus<Real>());
//        Test("SparseTensor factor_apply 28B", Compare(sc3, dc3), true);
//
//        d3.factor_apply(I3(0, 1, 2), d32, d3, std::plus<Real>());
//        s3.factor_apply(I3(0, 1, 2), s32, s3, std::plus<Real>());
//        Test("SparseTensor factor_apply 29A", Compare(s3, d3), true);
//      }
//    }           
//    
//    { // Random multiplications
//      for (UInt m = 0; m < 10; ++m) {
//
//        I4 ub4;
//        for (UInt j = 0; j < 4; ++j) ub4[j] = 1 + (rng_->getUInt32(5));
//
//        S4 s4A(ub4), s4C(ub4); D4 d4A(ub4), d4C(ub4);
//        ITER_4(ub4[0], ub4[1], ub4[2], ub4[3]) {
//          I4 i4(i, j, k, l);
//          UInt v = i4.ordinal(ub4);
//          if (v % 2 == 0) {
//            d4A.set(i4, rng_->getReal64());
//            s4A.set(i4, d4A.get(i4));
//          }
//        }
//
//        I3 ub3(ub4[1], ub4[2], ub4[3]);
//           
//        S3 s3B(ub3); D3 d3B(ub3);
//        ITER_3(ub3[0], ub3[1], ub3[2]) {
//          I3 i3(i, j, k);
//          UInt v = i3.ordinal(ub3);
//          if (v % 2 == 1) {
//            d3B.set(i3, rng_->getReal64());
//            s3B.set(i3, d3B.get(i3));
//          }
//        }
//
//        I3 dim3(1, 2, 3);
//        d4A.factor_apply(dim3, d3B, d4C, nta::Multiplies<Real>());
//        s4A.factor_apply_fast(dim3, s3B, s4C, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 30A", Compare(s4C, d4C), true);
//
//        s4C.clear();
//
//        s4A.factor_apply_nz(dim3, s3B, s4C, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 30B", Compare(s4C, d4C), true);
//
//        s4A.factor_apply(dim3, s3B, s4C, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply 30C", Compare(s4C, d4C), true);
//      }
//    }
//
//    { // In-place factor apply
//      // Dims 2 and 1
//      for (UInt m = 0; m < 10; ++m) {
//
//        I2 ub2;
//        for (UInt j = 0; j < 2; ++j) 
//          ub2[j] = 1 + (rng_->getUInt32(5));
//
//        S2 s2A(ub2); D2 d2A(ub2);
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt v = i2.ordinal(ub2);
//          if (v % 2 == 0) {
//            d2A.set(i2, rng_->getReal64());
//            s2A.set(i2, d2A.get(i2));
//          }
//        }
//
//        I1 ub1(ub2[1]);
//        
//        S1 s1B(ub1); D1 d1B(ub1);
//        ITER_1(ub1[0]) {
//          if (i % 2 == 1) {
//            d1B.set(I1((UInt)i), rng_->getReal64());
//            s1B.set(I1((UInt)i), d1B.get(i));
//          }
//        }  
//
//        I1 dim1(1);
//        d2A.factor_apply(dim1, d1B, nta::Multiplies<Real>());
//        s2A.factor_apply_fast(dim1, s1B, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply (in place) 31A", Compare(s2A, d2A), true);
//      }
//
//      // Dims 4 and 2
//      for (UInt m = 0; m < 10; ++m) {
//
//        I4 ub4;
//        for (UInt j = 0; j < 4; ++j) 
//          ub4[j] = 1 + (rng_->getUInt32(5));
//
//        S4 s4A(ub4); D4 d4A(ub4);
//        ITER_4(ub4[0], ub4[1], ub4[2], ub4[3]) {
//          I4 i4(i, j, k, l);
//          UInt v = i4.ordinal(ub4);
//          if (v % 2 == 0) {
//            d4A.set(i4, rng_->getReal64());
//            s4A.set(i4, d4A.get(i4));
//          }
//        }    
//
//        I2 ub2(ub4[1], ub4[2]);
//        
//        S2 s2B(ub2); D2 d2B(ub2);
//        ITER_2(ub2[0], ub2[1]) {
//          I2 i2(i, j);
//          UInt v = i2.ordinal(ub2);
//          if (v % 2 == 1) {
//            d2B.set(i2, rng_->getReal64());
//            s2B.set(i2, d2B.get(i2));
//          }
//        }
//
//        I2 dim2(1, 2);
//        d4A.factor_apply(dim2, d2B, nta::Multiplies<Real>());
//        s4A.factor_apply_fast(dim2, s2B, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply (in place) 31A", Compare(s4A, d4A), true);
//      }
//    }
//
//    { // factor mult of mat by mat of all 1
//      I2 ub(11, 13);
//      S2 A(ub), B(ub), C(ub), Aref(ub);
//
//      for (UInt i = 0; i < 20; ++i) {
//        GenerateRandRand01(rng_, A);
//        GenerateRandRand01(rng_, C); // noise in C
//        Aref = A;
//        B.setAll(Real(1));
//      
//        I2 dims(0, 1);
//        A.factor_apply_fast(dims, B, C, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply_fast K11", C == Aref, true);
//
//        C.clear();
//        A.factor_apply_nz(dims, B, C, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply_nz K12", C == Aref, true);
//      }
//    }
//
//    { // factor mult of 1 x mat by mat of all 1
//      I3 ub3(1, 11, 13);
//      S3 A(ub3), Aref(ub3), C(ub3);
//      I2 ub2(ub3[1], ub3[2]);
//      S2 B(ub2);
//      
//      for (UInt i = 0; i < 20; ++i) {
//        GenerateRandRand01(rng_, A);
//        Aref = A;
//        B.setAll(Real(1));
//        GenerateRandRand01(rng_, C); // noise in C
//
//        I2 dims(1, 2);
//        A.factor_apply_fast(dims, B, C, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply_fast K21", C == Aref, true);
//
//        C.clear();
//        A.factor_apply_nz(dims, B, C, nta::Multiplies<Real>());
//        Test("SparseTensor factor_apply_nz K22", C == Aref, true);
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestAccumulate()
//  {
//    {
//      I2 ub(3, 4);
//      D2 d2(ub); ITER_2(ub[0], ub[1]) d2.set(I2(i, j), Real(i*4+j+1));
//      S2 s2(ub); ITER_2(ub[0], ub[1]) s2.set(I2(i, j), Real(i*4+j+1));
//
//      for (UInt n = 0; n < 2; ++n) {
//        D1 d1(ub[n]); S1 s1(ub[n]); 
//        d2.accumulate(I1((UInt)(1-n)), d1, std::plus<Real>());
//        s2.accumulate(I1((UInt)(1-n)), s1, std::plus<Real>());
//        Test("SparseTensor accumulate 1", Compare(s1, d1), true);
//      }
//    }
//
//    {
//      I3 ub3(3, 4, 5);
//
//      D3 d3(ub3); 
//      S3 s3(ub3); 
//      
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        if (I3(i, j, k).ordinal(ub3) % 2 == 0) {
//          s3.set(I3(i, j, k), Real(i*4*5+j*5+k+1));
//          d3.set(I3(i, j, k), Real(i*4*5+j*5+k+1));
//        }
//      }
//      
//      {
//        D2 d2(4, 5); S2 s2(4, 5);
//        d3.accumulate(I1((UInt)0), d2, std::plus<Real>());
//        s3.accumulate(I1((UInt)0), s2, std::plus<Real>());
//        Test("SparseTensor accumulate 2", Compare(s2, d2), true);
//      }
//
//      {
//        D2 d2(3, 5); S2 s2(3, 5);
//        d3.accumulate(I1((UInt)1), d2, std::plus<Real>());
//        s3.accumulate(I1((UInt)1), s2, std::plus<Real>());
//        Test("SparseTensor accumulate 3", Compare(s2, d2), true);
//      }
//
//      {
//        D2 d2(3, 4); S2 s2(3, 4);
//        d3.accumulate(I1((UInt)2), d2, std::plus<Real>());
//        s3.accumulate(I1((UInt)2), s2, std::plus<Real>());
//        Test("SparseTensor accumulate 4", Compare(s2, d2), true);
//      }
//   
//      {
//        D1 d1(3); S1 s1(3);
//        d3.accumulate(I2(1, 2), d1, std::plus<Real>());
//        s3.accumulate(I2(1, 2), s1, std::plus<Real>());
//        Test("SparseTensor accumulate 5", Compare(s1, d1), true);
//      }
//
//      {
//        D1 d1(4); S1 s1(4);
//        d3.accumulate(I2(0, 2), d1, std::plus<Real>());
//        s3.accumulate(I2(0, 2), s1, std::plus<Real>());
//        Test("SparseTensor accumulate 6", Compare(s1, d1), true);
//      }
//
//      {
//        D1 d1(5); S1 s1(5);
//        d3.accumulate(I2(0, 1), d1, std::plus<Real>());
//        s3.accumulate(I2(0, 1), s1, std::plus<Real>());
//        Test("SparseTensor accumulate 7", Compare(s1, d1), true);
//      }
//    }
//
//    { // Max
//      D2 d2(3, 4); ITER_2(3, 4) d2.set(I2(i, j), Real(i*4+j+1));
//      S2 s2(3, 4); ITER_2(3, 4) s2.set(I2(i, j), Real(i*4+j+1));
//
//      {
//        D1 d1(3); S1 s1(3);
//        d2.accumulate(I1((UInt)1), d1, nta::Max<Real>());
//        s2.accumulate(I1((UInt)1), s1, nta::Max<Real>());
//        Test("SparseTensor max 1", Compare(s1, d1), true);
//      }   
//
//      {
//        D1 d1(4); S1 s1(4);
//        d2.accumulate(I1((UInt)0), d1, nta::Max<Real>());
//        s2.accumulate(I1((UInt)0), s1, nta::Max<Real>());
//        Test("SparseTensor max 2", Compare(s1, d1), true);
//      }
//    }
//
//    { // Multiplication
//      I2 ub2(7, 5);
//      D2 d2(ub2); S2 s2(ub2); 
//
//      ITER_2(ub2[0], ub2[1]) {
//        if (I2(i, j).ordinal(ub2) % 2 == 0) {
//          d2.set(i, j, (Real)(i*4+j+1));
//          s2.set(i, j, (Real)(i*4+j+1));
//        }
//      }
//      
//      D1 d1(ub2[0]); S1 s1(ub2[0]);
//
//      d2.accumulate_nz(I1((UInt)1), d1, nta::Multiplies<Real>(), 1);
//      s2.accumulate_nz(I1((UInt)1), s1, nta::Multiplies<Real>(), 1);
//      Test("SparseTensor accumulate 9A", Compare(s1, d1), true);
//
//      d1.clear(); s1.clear();
//
//      d2.accumulate(I1((UInt)1), d1, nta::Multiplies<Real>(), 1);
//      s2.accumulate(I1((UInt)1), s1, nta::Multiplies<Real>(), 1);
//      Test("SparseTensor accumulate 9B", Compare(s1, d1), true);
//    }
//
//    { // Random tensor values
//      { // Dims 2 and 1
//        for (UInt z = 0; z < 10; ++z) {
//          I2 ub2;
//          for (UInt i = 0; i < ub2.size(); ++i)
//            ub2[i] = 1 + (rng_->getUInt32(5));
//        
//          S2 s2A(ub2); D2 d2A(ub2);
//          ITER_2(ub2[0], ub2[1]) {
//            I2 i2(i, j);
//            UInt o = i2.ordinal(ub2);
//            if (o % 2 == 0) {
//              s2A.set(i2, (Real)(o+1)); //Real(rng_->get() % 32768 / 32768.0));
//              d2A.set(i2, s2A.get(i2));
//            }
//          }
//        
//          I1 dims1((UInt)0), ub1(ub2[dims1[0]]);
//          I1 compDims; dims1.complement(compDims);
//          S1 s1C(ub1); D1 d1C(ub1);
//        
//          s2A.accumulate_nz(compDims, s1C, nta::Multiplies<Real>(), 1);
//          d2A.accumulate_nz(compDims, d1C, nta::Multiplies<Real>(), 1);
//          Test("SparseTensor accumulate 10A", Compare(s1C, d1C), true);
//        }
//      }
//
//      { // Dims 4 and 2
//        for (UInt z = 0; z < 10; ++z) {
//          I4 ub4;
//          for (UInt i = 0; i < 4; ++i)
//            ub4[i] = 1 + (rng_->getUInt32(5));
//
//          S4 s4A(ub4); D4 d4A(ub4);
//          ITER_4(ub4[0], ub4[1], ub4[2], ub4[3]) {
//            I4 i4(i, j, k, l);
//            UInt o = i4.ordinal(ub4);
//            if (o % 2 == 0) {
//              s4A.set(i4, rng_->getReal64());
//              d4A.set(i4, s4A.get(i4));
//            }
//          }
//      
//          I2 dims2(0, 1), ub2(ub4[dims2[0]], ub4[dims2[1]]);
//          I2 compDims; dims2.complement(compDims);
//          S2 s2C(ub2); D2 d2C(ub2);
//      
//          s4A.accumulate_nz(compDims, s2C, std::plus<Real>(), 0);
//          d4A.accumulate(compDims, d2C, std::plus<Real>(), 0);
//          Test("SparseTensor accumulate 11A", Compare(s2C, d2C), true);
//
//          s2C.clear();
//          s4A.accumulate(compDims, s2C, std::plus<Real>(), 0);
//          Test("SparseTensor accumulate 11B", Compare(s2C, d2C), true);
//
//          s2C.clear();
//          s4A.accumulate_nz(compDims, s2C, nta::Multiplies<Real>(), 1);
//          d4A.accumulate_nz(compDims, d2C, nta::Multiplies<Real>(), 1);
//          Test("SparseTensor accumulate 11C", Compare(s2C, d2C), true);
//
//          s2C.clear();
//          s4A.accumulate_nz(compDims, s2C, nta::Multiplies<Real>(), 1);
//          Test("SparseTensor accumulate 11D", Compare(s2C, d2C), true);
//        
//          s2C.clear();
//          s4A.accumulate_nz(compDims, s2C, nta::Max<Real>());
//          d4A.accumulate(compDims, d2C, nta::Max<Real>());
//          Test("SparseTensor accumulate 11E", Compare(s2C, d2C), true);
//
//          s2C.clear();
//          s4A.accumulate(compDims, s2C, nta::Max<Real>());
//          Test("SparseTensor accumulate 11F", Compare(s2C, d2C), true);
//        }
//      }
//    }
//
//    { // accumulate and boost::lambda: check that it compiles and 
//      // returns appropriate result for lerp 
//      I1 ub1(5);
//      S1 s1A(ub1), s1B(ub1); GenerateOrdered(s1A); GenerateOrdered(s1B);
//      s1A.element_apply(1 - _1);
//      for (UInt i = 0; i < s1B.getBound(0); ++i)
//        s1B.set(I1(UInt(i)), 1 - s1B.get(I1(UInt(i))));
//      Test("SparseTensor accumulate with lambda 1", s1A == s1B, true);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestOuterProduct()
//  {
//    I1 ub1A((UInt) 13); I1 ub1B((UInt) 7);
//    D1 d1A(ub1A), d1B(ub1B);
//    S1 s1A(ub1A), s1B(ub1B);
//
//    D2 d2(ub1A[0], ub1B[0]); S2 s2(d2.getBounds());
//      
//    ITER_1(ub1A[0]) {
//      if (i % 4 == 0) {
//        d1A.set(I1(UInt(i)), (Real)(i+1));
//        s1A.set(I1(UInt(i)), d1A(i));
//      }
//    }
//    
//    ITER_1(ub1B[0]) {
//      if (i % 2 == 0) {
//        d1B.set(I1(UInt(i)), (Real)(i+1));
//        s1B.set(I1(UInt(i)), d1B(i));
//      }
//    }
//    
//    //1X1
//    d1A.outer_product(d1B, d2, nta::Multiplies<Real>());
//    s1A.outer_product_nz(s1B, s2, nta::Multiplies<Real>());
//    Test("SparseTensor outer_product 1A", Compare(s2, d2), true);
//
//    d1A.outer_product(d1B, d2, nta::Multiplies<Real>());
//    s1A.outer_product(s1B, s2, nta::Multiplies<Real>());
//    Test("SparseTensor outer_product 1B", Compare(s2, d2), true);
//
//    // 2X1
//    D3 d3(ub1A[0], ub1B[0], ub1A[0]); S3 s3(ub1A[0], ub1B[0], ub1A[0]);
//
//    d2.outer_product(d1A, d3, nta::Multiplies<Real>());
//    s2.outer_product_nz(s1A, s3, nta::Multiplies<Real>());
//    Test("SparseTensor outer_product 2A", Compare(s3, d3), true);
//
//    d2.outer_product(d1A, d3, nta::Multiplies<Real>());
//    s2.outer_product(s1A, s3, nta::Multiplies<Real>());
//    Test("SparseTensor outer_product 2B", Compare(s3, d3), true);
//
//    // 2X2
//    D4 d4(ub1A[0], ub1B[0], ub1A[0], ub1B[0]); 
//    S4 s4(ub1A[0], ub1B[0], ub1A[0], ub1B[0]);
//
//    d2.outer_product(d2, d4, std::plus<Real>());
//    s2.outer_product(s2, s4, std::plus<Real>());
//    Test("SparseTensor outer_product 3A", Compare(s4, d4), true);
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestContract()
//  {
//    I3 ub3(4, 3, 3);
//
//    D3 d3(ub3); S3 s3(ub3);       
//    
//    ITER_3(ub3[0], ub3[1], ub3[2]) {
//      if (I3(i, j, k).ordinal(ub3) % 2 == 0) {
//        d3.set(I3(i, j, k), (Real)(I3(i, j, k).ordinal(ub3)+1));
//        s3.set(I3(i, j, k), d3(i, j, k));
//      }   
//    }
//
//    {
//      D1 d1(ub3[0]); S1 s1(ub3[0]);
//
//      d3.contract(1, 2, d1, nta::Multiplies<Real>(), 1);
//      s3.contract_nz(1, 2, s1, nta::Multiplies<Real>(), 1);
//      Test("SparseTensor contract 1A", Compare(s1, d1), true);
//
//      d3.contract(1, 2, d1, nta::Multiplies<Real>(), 1);
//      s3.contract(1, 2, s1, nta::Multiplies<Real>(), 1);
//      Test("SparseTensor contract 1B", Compare(s1, d1), true);
//    }
//
//    {
//      D1 d1(ub3[0]); S1 s1(ub3[0]);
//      
//      d3.contract(1, 2, d1, std::plus<Real>());
//      s3.contract(1, 2, s1, std::plus<Real>());
//      Test("SparseTensor contract 1", Compare(s1, d1), true);
//    }   
//  }
//
// //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestInnerProduct()
//  {
//    D2 d2A(3, 4), d2B(4, 3), d2C(3, 3);     
//    S2 s2A(3, 4), s2B(4, 3), s2C(3, 3);
//    
//    ITER_2(3, 4) {
//      if (I2(i, j).ordinal(I2(3, 4)) % 2 == 0) {
//        d2A(i, j) = d2B(j, i) = Real(i*4+j+1);
//        s2A.set(I2(i, j), d2A(i, j));
//        s2B.set(I2(j, i), d2A(i, j));    
//      }    
//    }
//    
//    d2A.inner_product(1, 0, d2B, d2C, nta::Multiplies<Real>(), std::plus<Real>(), 0);
//    s2A.inner_product_nz(1, 0, s2B, s2C, nta::Multiplies<Real>(), std::plus<Real>(), 0);
//    Test("SparseTensor inner product 1A", Compare(s2C, d2C), true);
//
//    d2A.inner_product(1, 0, d2B, d2C, nta::Multiplies<Real>(), std::plus<Real>(), 0);
//    s2A.inner_product(1, 0, s2B, s2C, nta::Multiplies<Real>(), std::plus<Real>(), 0);
//    Test("SparseTensor inner product 1B", Compare(s2C, d2C), true);
//
//    S4 o(3, 4, 4, 3); 
//    s2A.outer_product(s2B, o, nta::Multiplies<Real>());
//
//    S2 s2D(3, 3);
//    o.contract(1, 2, s2D, std::plus<Real>());
//    Test("SparseTensor inner product 2", s2C, s2D);
//
//    S3 s3A(3, 4, 5), s3B(3, 3, 5);
//    ITER_3(3, 4, 5) s3A.set(I3(i, j, k), (Real)(I3(i, j, k).ordinal(I3(3, 4, 5)) + 1));
//    s2A.inner_product(1, 1, s3A, s3B, nta::Multiplies<Real>(), std::plus<Real>());
//
//    S5 o2(3, 4, 3, 4, 5);
//    s2A.outer_product(s3A, o2, nta::Multiplies<Real>());
//    
//    S3 s3D(3, 3, 5);
//    o2.contract(1, 3, s3D, std::plus<Real>());
//    Test("SparseTensor inner product 3", s3B, s3D);
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestIntersection()
//  {
//    I3 ub3(2, 3, 4);
//
//    { // empty/empty
//      S3 s3A(ub3), s3B(ub3);
//      std::vector<I3> inter;
//      s3A.nz_intersection(s3B, inter);
//      Test("SparseTensor nz_intersection 1", inter.empty(), true);
//    }
//
//    { // full/empty
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2])
//        s3A.set(I3(i, j, k), (Real) I3(i, j, k).ordinal(ub3)+1);
//      std::vector<I3> inter;
//      s3A.nz_intersection(s3B, inter);
//      Test("SparseTensor nz_intersection 2A", inter.empty(), true);
//
//      inter.clear();
//      s3B.nz_intersection(s3A, inter);
//      Test("SparseTensor nz_intersection 2B", inter.empty(), true);
//    }
//
//    { // full/full
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        s3A.set(I3(i, j, k), (Real) I3(i, j, k).ordinal(ub3)+1);
//        s3B.set(I3(i, j, k), (Real) I3(i, j, k).ordinal(ub3)+1);
//      }
//      std::vector<I3> inter1, inter2;
//      s3A.nz_intersection(s3B, inter1);
//      Test("SparseTensor nz_intersection 3A", inter1.size(), ub3.product());
//
//      s3B.nz_intersection(s3A, inter2);
//      Test("SparseTensor nz_intersection 3B", inter2.size(), ub3.product());
//
//      Test("SparseTensor nz_intersection 3C", Compare(inter1, inter2), true);
//    }
//   
//    { // 1 zero/1 zero
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        s3A.set(I3(i, j, k), (Real) I3(i, j, k).ordinal(ub3));
//        s3B.set(I3(i, j, k), (Real) I3(i, j, k).ordinal(ub3));
//      }
//      std::vector<I3> inter1, inter2;
//      s3A.nz_intersection(s3B, inter1);
//      Test("SparseTensor nz_intersection 4A", inter1.size(), ub3.product()-1);
//
//      s3B.nz_intersection(s3A, inter2);
//      Test("SparseTensor nz_intersection 4B", inter2.size(), ub3.product()-1);
//
//      Test("SparseTensor nz_intersection 4C", Compare(inter1, inter2), true);
//    }
//
//    { // 1 out of 2, mismatching
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        UInt n = I3(i, j, k).ordinal(ub3);
//        UInt n1 = n % 2 == 0 ? n : 0;
//        UInt n2 = n % 2 == 0 ? 0 : n;
//        s3A.set(I3(i, j, k), (Real) n1);
//        s3B.set(I3(i, j, k), (Real) n2);
//      }     
//      std::vector<I3> inter;
//      s3A.nz_intersection(s3B, inter);   
//      Test("SparseTensor nz_intersection 5", inter.empty(), true);
//    }
//
//    { // 1 out of 2, matching
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        UInt n = I3(i, j, k).ordinal(ub3);
//        n = n % 2 == 0 ? n : 0;
//        s3A.set(I3(i, j, k), (Real) n);
//        s3B.set(I3(i, j, k), (Real) n);
//      }
//      std::vector<I3> inter1, inter2;
//      s3A.nz_intersection(s3B, inter1);
//      Test("SparseTensor nz_intersection 6A", inter1.size(), (ub3.product()-1)/2);
//
//      s3B.nz_intersection(s3A, inter2);
//      Test("SparseTensor nz_intersection 6B", inter2.size(), (ub3.product()-1)/2);
//
//      Test("SparseTensor nz_intersection 6C", Compare(inter1, inter2), true);
//    }
//
//    { // 1 out of 4, matching
//      S3 s3A(ub3), s3B(ub3);     
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        UInt n = I3(i, j, k).ordinal(ub3);     
//        UInt nA = n % 2 == 0 ? n : 0;
//        UInt nB = n % 4 == 0 ? n : 0;
//        s3A.set(I3(i, j, k), (Real) nA);
//        s3B.set(I3(i, j, k), (Real) nB);
//      }
//
//      std::vector<I3> inter1, inter2;
//      s3A.nz_intersection(s3B, inter1);
//      Test("SparseTensor nz_intersection 7A", inter1.size(), (ub3.product()-1)/4);
//  
//      s3B.nz_intersection(s3A, inter2);
//      Test("SparseTensor nz_intersection 7B", inter2.size(), (ub3.product()-1)/4);
//
//      Test("SparseTensor nz_intersection 7C", Compare(inter1, inter2), true);
//    }
//
//    // projections
//    I2 ub2(2, 5);  
//
//    { // Intersection between a non-empty S2 and a non-empty S1
//      S2 s2A(ub2); S1 s1B(ub2[1]);
//      s1B.set(1, (Real)1);
//      s1B.set(3, (Real)2);
//      ITER_2(ub2[0], ub2[1]) s2A.set(I2(i, j), (Real)(I2(i, j).ordinal(ub2)+1));
//      
//      S2::NonZeros<I2, I1> inter1, ans;
//      inter1.push_back(S2::Elt<I2, I1>(I2(0, 0), 1, I1(1), 2)); // fake, to see if we clean up
//      I2 i2; I1 i1;
//      do {
//        i2.project(I1(1), i1);
//        if (!nearlyZero(s2A.get(i2)) && !nearlyZero(s1B.get(i1)))
//          ans.push_back(S2::Elt<I2, I1>(i2, s2A.get(i2), i1, s1B.get(i1)));
//      } while (i2.increment(ub2));
//
//      s2A.nz_intersection(I1(1), s1B, inter1);
//
//      Test("SparseTensor nz_intersection 8A", inter1.size(), ans.size());
//      for (UInt i = 0; i < ans.size(); ++i) {
//        Test("SparseTensor nz_intersection 8B", inter1[i].getIndexA(), ans[i].getIndexA());
//        Test("SparseTensor nz_intersection 8C", inter1[i].getIndexB(), ans[i].getIndexB());
//        Test("SparseTensor nz_intersection 8D", inter1[i].getValA(), ans[i].getValA());
//        Test("SparseTensor nz_intersection 8E", inter1[i].getValB(), ans[i].getValB());
//      }
//    }
//
//    { // Intersection between an empty S2 and a non-empty S1
//      S2 s2A(ub2); S1 s1B(ub2[1]);
//      s1B.set(1, (Real)1);
//      s1B.set(3, (Real)2);
//
//      S2::NonZeros<I2, I1> inter1;
//      inter1.push_back(S2::Elt<I2, I1>(I2(0, 0), 1, I1(1), 2)); // fake, to see if we clean up
//
//      s2A.nz_intersection(I1(1), s1B, inter1);
//
//      Test("SparseTensor nz_intersection 9A", inter1.empty(), true);
//    }
//
//    { // Intersection between an empty S1 and a non-empty S2
//      S2 s2A(ub2); S1 s1B(ub2[1]);
//      ITER_2(ub2[0], ub2[1]) s2A.set(I2(i, j), (Real)(I2(i, j).ordinal(ub2)+1));
//
//      S2::NonZeros<I2, I1> inter1;
//      inter1.push_back(S2::Elt<I2, I1>(I2(0, 0), 1, I1(1), 2)); // fake, to see if we clean up
//
//      s2A.nz_intersection(I1(1), s1B, inter1);
//
//      Test("SparseTensor nz_intersection 10A", inter1.empty(), true);
//    }
//
//    { // Intersection between an empty S2 and an empty S1
//      S2 s2A(ub2); S1 s1B(ub2[1]);
//
//      S2::NonZeros<I2, I1> inter1;
//      inter1.push_back(S2::Elt<I2, I1>(I2(0, 0), 1, I1(1), 2)); // fake, to see if we clean up
//
//      s2A.nz_intersection(I1(1), s1B, inter1);
//
//      Test("SparseTensor nz_intersection 11A", inter1.empty(), true);
//    }
//
//    { // Intersection between a full S2 and a full S1
//      S2 s2A(ub2); S1 s1B(ub2[1]);
//      ITER_1(ub2[1]) s1B.set(I1(i), (Real)i+1);
//      ITER_2(ub2[0], ub2[1]) s2A.set(I2(i, j), (Real)(I2(i, j).ordinal(ub2)+1));
//      
//      S2::NonZeros<I2, I1> inter1, ans;
//      inter1.push_back(S2::Elt<I2, I1>(I2(0, 0), 1, I1(1), 2)); // fake, to see if we clean up
//      I2 i2; I1 i1;
//      do {
//        i2.project(I1(1), i1);
//        if (!nearlyZero(s2A.get(i2)) && !nearlyZero(s1B.get(i1)))
//          ans.push_back(S2::Elt<I2, I1>(i2, s2A.get(i2), i1, s1B.get(i1)));
//      } while (i2.increment(ub2));
//
//      s2A.nz_intersection(I1(1), s1B, inter1);
//
//      Test("SparseTensor nz_intersection 12A", inter1.size(), ans.size());
//      for (UInt i = 0; i < ans.size(); ++i) {
//        Test("SparseTensor nz_intersection 12B", inter1[i].getIndexA(), ans[i].getIndexA());
//        Test("SparseTensor nz_intersection 12C", inter1[i].getIndexB(), ans[i].getIndexB());
//        Test("SparseTensor nz_intersection 12D", inter1[i].getValA(), ans[i].getValA());
//        Test("SparseTensor nz_intersection 12E", inter1[i].getValB(), ans[i].getValB());
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestUnion()
//  {
//    I3 ub3(2, 3, 4);
//
//    { // empty/empty
//      S3 s3A(ub3), s3B(ub3);
//      std::vector<I3> u;
//      s3A.nz_union(s3B, u);
//      Test("SparseTensor nz_union 1", u.empty(), true);
//    }
//
//    { // full/empty
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2])
//        s3A.set(I3(i, j, k), (Real) I3(i, j, k).ordinal(ub3)+1);
//   
//      std::vector<I3> u1, u2;
//      s3A.nz_union(s3B, u1);
//      Test("SparseTensor nz_union 2A", u1.size(), ub3.product());
//
//      s3B.nz_union(s3A, u2);
//      Test("SparseTensor nz_union 2B", u2.size(), ub3.product());
//
//      Test("SparseTensor nz_union 2C", Compare(u1, u2), true);
//    }
//
//    { // full/full
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        s3A.set(I3(i, j, k), (Real) I3(i, j, k).ordinal(ub3)+1);
//        s3B.set(I3(i, j, k), (Real) I3(i, j, k).ordinal(ub3)+1);
//      }
//      
//      std::vector<I3> u1, u2;
//      s3A.nz_union(s3B, u1);
//      Test("SparseTensor nz_union 3A", u1.size(), ub3.product());
//
//      s3B.nz_union(s3A, u2);
//      Test("SparseTensor nz_union 3B", u2.size(), ub3.product());
//
//      Test("SparseTensor nz_union 3C", Compare(u1, u2), true);
//    }
//   
//    { // 1 zero/1 zero
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        s3A.set(I3(i, j, k), (Real) I3(i, j, k).ordinal(ub3));
//        s3B.set(I3(i, j, k), (Real) I3(i, j, k).ordinal(ub3));
//      }
//      
//      std::vector<I3> u1, u2;
//      s3A.nz_union(s3B, u1);
//      Test("SparseTensor nz_union 4A", u1.size(), ub3.product()-1);
//
//      s3B.nz_union(s3A, u2);
//      Test("SparseTensor nz_union 4B", u2.size(), ub3.product()-1);
//
//      Test("SparseTensor nz_union 4C", Compare(u1, u2), true);
//    }
//
//    { // 1 out of 2, mismatching
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        UInt n = I3(i, j, k).ordinal(ub3);
//        UInt n1 = n % 2 == 0 ? n : 0;
//        UInt n2 = n % 2 == 0 ? 0 : n;
//        s3A.set(I3(i, j, k), (Real) n1);
//        s3B.set(I3(i, j, k), (Real) n2);
//      }
//      
//      std::vector<I3> u1, u2;
//      s3A.nz_union(s3B, u1);
//      Test("SparseTensor nz_union 5A", u1.size(), ub3.product()-1);
//
//      s3B.nz_union(s3A, u2);
//      Test("SparseTensor nz_union 5B", u2.size(), ub3.product()-1);
//
//      Test("SparseTensor nz_union 5C", Compare(u1, u2), true);
//    }
//
//    { // 1 out of 2, matching
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        UInt n = I3(i, j, k).ordinal(ub3);
//        n = n % 2 == 0 ? n : 0;
//        s3A.set(I3(i, j, k), (Real) n);
//        s3B.set(I3(i, j, k), (Real) n);
//      }
//
//      std::vector<I3> u1, u2;
//      s3A.nz_union(s3B, u1);
//      Test("SparseTensor nz_union 6A", u1.size(), (ub3.product()-1)/2);
//
//      s3B.nz_union(s3A, u2);
//      Test("SparseTensor nz_union 6B", u2.size(), (ub3.product()-1)/2);
//
//      Test("SparseTensor nz_union 6C", Compare(u1, u2), true);
//    }
//
//    { // 1 out of 4, matching
//      S3 s3A(ub3), s3B(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        UInt n = I3(i, j, k).ordinal(ub3);
//        UInt nA = n % 2 == 0 ? n : 0;
//        UInt nB = n % 4 == 0 ? n : 0;
//        s3A.set(I3(i, j, k), (Real) nA);
//        s3B.set(I3(i, j, k), (Real) nB);
//      }
//
//      std::vector<I3> u1, u2;
//      s3A.nz_union(s3B, u1);
//      Test("SparseTensor nz_union 7A", u1.size(), (ub3.product()-1)/2);
//  
//      s3B.nz_union(s3A, u2);
//      Test("SparseTensor nz_union 7B", u2.size(), (ub3.product()-1)/2);
//
//      Test("SparseTensor nz_union 7C", Compare(u1, u2), true);
//    }   
//
//    // projections
//    I2 ub2(2, 5);     
//
//    { // Union between a non-empty S2 and a non-empty S1
//      S2 s2A(ub2); S1 s1B(ub2[1]);
//      s1B.set(1, (Real)1);
//      s1B.set(3, (Real)2);
//      ITER_2(ub2[0], ub2[1]) s2A.set(I2(i, j), (Real)(I2(i, j).ordinal(ub2)+1));
//      
//      S2::NonZeros<I2, I1> u1, ans;
//      u1.push_back(S2::Elt<I2, I1>(I2(0, 0), 1, I1(1), 2)); // fake, to see if we clean up
//      I2 i2; I1 i1;
//      do {
//        i2.project(I1(1), i1);
//        if (!nearlyZero(s2A.get(i2)) || !nearlyZero(s1B.get(i1)))
//          ans.push_back(S2::Elt<I2, I1>(i2, s2A.get(i2), i1, s1B.get(i1)));
//      } while (i2.increment(ub2));
//
//      s2A.nz_union(I1(1), s1B, u1);
//
//      Test("SparseTensor nz_union 8A", u1.size(), ans.size());
//      for (UInt i = 0; i < ans.size(); ++i) {
//        Test("SparseTensor nz_union 8B", u1[i].getIndexA(), ans[i].getIndexA());
//        Test("SparseTensor nz_union 8C", u1[i].getIndexB(), ans[i].getIndexB());
//        Test("SparseTensor nz_union 8D", u1[i].getValA(), ans[i].getValA());
//        Test("SparseTensor nz_union 8E", u1[i].getValB(), ans[i].getValB());
//      }
//    }   
//
//    { // Union between an empty S2 and a non-empty S1
//      S2 s2A(ub2); S1 s1B(ub2[1]);
//      s1B.set(1, (Real)1);  
//      s1B.set(3, (Real)2);
//
//      S2::NonZeros<I2, I1> u1, ans;
//      u1.push_back(S2::Elt<I2, I1>(I2(0, 0), 1, I1(1), 2)); // fake, to see if we clean up
//      I2 i2; I1 i1;
//      do {
//        i2.project(I1(1), i1);
//        if (!nearlyZero(s2A.get(i2)) || !nearlyZero(s1B.get(i1)))
//          ans.push_back(S2::Elt<I2, I1>(i2, s2A.get(i2), i1, s1B.get(i1)));
//      } while (i2.increment(ub2));
//
//      s2A.nz_union(I1(1), s1B, u1);
//
//      Test("SparseTensor nz_union 9A", u1.size(), ub2[0] * s1B.getNNonZeros());
//      for (UInt i = 0; i < ans.size(); ++i) {
//        Test("SparseTensor nz_union 9B", u1[i].getIndexA(), ans[i].getIndexA());
//        Test("SparseTensor nz_union 9C", u1[i].getIndexB(), ans[i].getIndexB());
//        Test("SparseTensor nz_union 9D", u1[i].getValA(), ans[i].getValA());
//        Test("SparseTensor nz_union 9E", u1[i].getValB(), ans[i].getValB());
//      }
//    }
//
//    { // Union between an empty S1 and a non-empty S2
//      S2 s2A(ub2); S1 s1B(ub2[1]);
//      ITER_2(ub2[0], ub2[1]) s2A.set(I2(i, j), (Real)(I2(i, j).ordinal(ub2)+1));
//
//      S2::NonZeros<I2, I1> u1, ans;
//      u1.push_back(S2::Elt<I2, I1>(I2(0, 0), 1, I1(1), 2)); // fake, to see if we clean up
//      I2 i2; I1 i1;
//      do {
//        i2.project(I1(1), i1);
//        if (!nearlyZero(s2A.get(i2)) || !nearlyZero(s1B.get(i1)))
//          ans.push_back(S2::Elt<I2, I1>(i2, s2A.get(i2), i1, s1B.get(i1)));
//      } while (i2.increment(ub2));
//
//      s2A.nz_union(I1(1), s1B, u1);
//
//      Test("SparseTensor nz_union 10A", u1.size(), s2A.getNNonZeros());
//      for (UInt i = 0; i < ans.size(); ++i) {
//        Test("SparseTensor nz_union 10B", u1[i].getIndexA(), ans[i].getIndexA());
//        Test("SparseTensor nz_union 10C", u1[i].getIndexB(), ans[i].getIndexB());
//        Test("SparseTensor nz_union 10D", u1[i].getValA(), ans[i].getValA());
//        Test("SparseTensor nz_union 10E", u1[i].getValB(), ans[i].getValB());
//      }
//    }
//
//    { // Union between an empty S2 and an empty S1
//      S2 s2A(ub2); S1 s1B(ub2[1]);
//
//      S2::NonZeros<I2, I1> u1;
//      u1.push_back(S2::Elt<I2, I1>(I2(0, 0), 1, I1(1), 2)); // fake, to see if we clean up
//
//      s2A.nz_union(I1(1), s1B, u1);
//
//      Test("SparseTensor nz_union 11A", u1.empty(), true);
//    }
//
//    { // Union between a full S2 and a full S1
//      S2 s2A(ub2); S1 s1B(ub2[1]);
//      ITER_1(ub2[1]) s1B.set(I1(i), (Real)i+1);
//      ITER_2(ub2[0], ub2[1]) s2A.set(I2(i, j), (Real)(I2(i, j).ordinal(ub2)+1));
//      
//      S2::NonZeros<I2, I1> u1, ans;
//      u1.push_back(S2::Elt<I2, I1>(I2(0, 0), 1, I1(1), 2)); // fake, to see if we clean up
//      I2 i2; I1 i1;    
//      do {
//        i2.project(I1(1), i1);
//        if (!nearlyZero(s2A.get(i2)) || !nearlyZero(s1B.get(i1)))
//          ans.push_back(S2::Elt<I2, I1>(i2, s2A.get(i2), i1, s1B.get(i1)));
//      } while (i2.increment(ub2));
//
//      s2A.nz_union(I1(1), s1B, u1);  
//
//      Test("SparseTensor nz_union 12A", u1.size(), ans.size());
//      for (UInt i = 0; i < ans.size(); ++i) {
//        Test("SparseTensor nz_union 12B", u1[i].getIndexA(), ans[i].getIndexA());
//        Test("SparseTensor nz_union 12C", u1[i].getIndexB(), ans[i].getIndexB());
//        Test("SparseTensor nz_union 12D", u1[i].getValA(), ans[i].getValA());
//        Test("SparseTensor nz_union 12E", u1[i].getValB(), ans[i].getValB());
//      }
//    }   
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestDynamicIndex()
//  {
//    typedef SparseTensor<std::vector<UInt>, double> DST;
//
//    { // Construction/set/get/update/clear
//      std::vector<UInt> i3(3);
//      i3[0] = 4; i3[1] = 5; i3[2] = 6;
//
//      DST st(i3);
//      Test("SparseTensor dynamic getRank 1", st.getRank(), (UInt)3);
//      Test("SparseTensor dynamic getNNonZeros 2", st.getNNonZeros(), (UInt)0);
//      Test("SparseTensor dynamic isZero 3", st.isZero(), true);
//      Test("SparseTensor dynamic isDense 4", st.isDense(), false);
//      Test("SparseTensor dynamic getBounds 5", Compare(st.getBounds(), i3), true);
//
//      DST st2(st);
//      Test("SparseTensor dynamic 6", st == st2, true);
//
//      DST st3 = st;
//      Test("SparseTensor dynamic 7", st3 == st, true);
//
//      st3.clear();
//      Test("SparseTensor dynamic 8", st3 == st, true);
//
//      std::vector<UInt> perm(3); 
//      perm[0] = 1; perm[1] = 2; perm[2] = 0;
//      Test("SparseTensor dynamic 9", st.isSymmetric(perm), false);
//      Test("SparseTensor dynamic 10", st.isAntiSymmetric(perm), false);
//
//      std::vector<UInt> idx = st.getNewZeroIndex();
//      do {
//        long o = ordinal(st.getBounds(), idx);
//        if (o % 2 == 0) {
//          st.set(idx, o);
//          Test("SparseTensor dynamic 11A", st.get(idx), o);
//          Test("SparseTensor dynamic 11B", st.isZero(idx), o == 0);
//          st.setZero(idx);
//          Test("SparseTensor dynamic 11C", st.get(idx), (double)0);
//          Test("SparseTensor dynamic 11D", st.isZero(idx), true);
//          if (o > 0) {
//            st.setNonZero(idx, o);
//            Test("SparseTensor dynamic 11E", st.get(idx), o);
//            Test("SparseTensor dynamic 11F", st.isZero(idx), false);
//          }
//          Test("SparseTensor dynamic 1G", 
//               st.update(idx, (double)-o, std::plus<double>()), (double)0);
//          Test("SparseTensor dynamic 11H", st.get(idx), (double)0);
//          Test("SparseTensor dynamic 11I", st.isZero(idx), true);
//          Test("SparseTensor dynamic 11J", 
//               st.update(idx, (double)o, std::plus<double>()), (double)o);
//          Test("SparseTensor dynamic 11K", st.get(idx), (double)o);
//          Test("SparseTensor dynamic 11L", st.isZero(idx), o == 0);
//        }
//      } while (increment(st.getBounds(), idx));
//      
//      Test("SparseTensor dynamic 12", st.getNNonZeros(), product(st.getBounds())/2-1);
//      Test("SparseTensor dynamic 13", st.isZero(), false);
//      Test("SparseTensor dynamic 14", st.isDense(), false);
//      
//      st.setAll(1);
//      Test("SparseTensor dynamic 15", st.getNNonZeros(), product(st.getBounds()));
//      Test("SparseTensor dynamic 16", st.isZero(), false);
//      Test("SparseTensor dynamic 17", st.isDense(), true);
//      
//      st.clear();
//      Test("SparseTensor dynamic 18", st.getNNonZeros(), (UInt)0);
//      Test("SparseTensor dynamic 19", st.isZero(), true);
//      Test("SparseTensor dynamic 20", st.isDense(), false);
//    }
//
//    { // getSlice
//      std::vector<UInt> ub3(3); ub3[0] = 4; ub3[1] = 5; ub3[2] = 3;
//      DST s3(ub3);
//      ITER_3(ub3[0], ub3[1], ub3[2]) {
//        std::vector<UInt> i3(3);
//        i3[0] = i; i3[1] = j; i3[2] = k;
//        UInt o = ordinal(ub3, i3);
//        s3.set(i3, (double)o);
//      }
//      std::vector<UInt> ub2(2); ub2[0] = 4; ub2[1] = 5;
//      DST s2(ub2), ref(ub2);
//      for (UInt n = 0; n < ub3[2]; ++n) {
//        Domain<UInt> d(I3(0, 0, n), I3(ub3[0], ub3[1], n));
//        ITER_2(ub3[0], ub3[1]) {
//          std::vector<UInt> idx(2); idx[0] = i; idx[1] = j;
//          UInt o = i*ub3[1]*ub3[2]+j*ub3[2]+n;
//          ref.set(idx, (double)o);
//        }
//        s3.getSlice(d, s2);
//        Test("SparseTensor dynamic getSlice", s2, ref);
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestToFromStream()
//  {
//    I2 ub2(4, 4);
//    S2 s2(ub2), ref(ub2);
//    
//    ITER_2(ub2[0], ub2[1]) {
//      I2 i2(i, j);
//      UInt o = i2.ordinal(ub2);
//      if (o % 2 == 0) {
//        s2.set(i2, Real(o));
//        ref.set(i2, Real(o));
//      }
//    }
//
//    stringstream str;
//    s2.toStream(str);
//    s2.clear();
//    s2.fromStream(str);
//
//    Test("SparseTensor to/fromStream 1", s2 == ref, true);
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestNormalize()
//  {   
//    I2 ub2(4, 3);
//    S2 s2(ub2);
//    
//    { // Matrix of zeros should "normalize" to zeros
//      s2.normalize(I1(UInt(0)));
//      Test("SparseTensor normalize zero 1", s2.isZero(), true);
//      
//      s2.normalize(I1(UInt(0)));
//      Test("SparseTensor normalize zero 2", s2.isZero(), true);
//      
//      s2.normalize();
//      Test("SparseTensor normalize zero 3", s2.isZero(), true);
//    }
//
//    { // Matrix of 1s should normalize to uniform value
//      s2.setAll(1.0);
//      s2.normalize(I1(UInt(0))); // sum along columns
//      map<Real, UInt> vals = s2.values();
//      Test("SparseTensor normalize uniform 1A", vals.size(), 1u);
//      bool t = nearlyEqual(vals.begin()->first, Real(1./ub2[0]));
//      Test("SparseTensor normalize uniform 1B", t, true);
//      Test("SparseTensor normalize uniform 1C", vals.begin()->second, product(ub2));
//
//      s2.setAll(1.0);
//      s2.normalize(I1(UInt(1))); // sum along rows
//      vals = s2.values();
//      Test("SparseTensor normalize uniform 2A", vals.size(), 1u);
//      t = nearlyEqual(vals.begin()->first, Real(1./ub2[1]));
//      Test("SparseTensor normalize uniform 2B", t, true);
//      Test("SparseTensor normalize uniform 2C", vals.begin()->second, product(ub2));
//
//      s2.setAll(1.0);
//      s2.normalize();
//      vals = s2.values();
//      Test("SparseTensor normalize uniform 3A", vals.size(), 1u);
//      t = nearlyEqual(vals.begin()->first, Real(1./(ub2[0]*ub2[1])));
//      Test("SparseTensor normalize uniform 3B", t, true);
//      Test("SparseTensor normalize uniform 3C", vals.begin()->second, product(ub2));
//    }
//    
//    { // Matrix with empty rows should not crash
//      s2.setAll(1.0);
//      for (UInt i = 0; i < ub2[1]; ++i)
//        s2.set(I2(0, i), 0);
//      
//      s2.normalize(I1(UInt(1)));
//    }
//
//    { // Matrix with empty cols should not crash
//      s2.setAll(1.0);
//      for (UInt i = 0; i < ub2[0]; ++i)
//        s2.set(I2(i, 0), 0);
//      
//      s2.normalize(I1(UInt(0)));
//    }
//
//    { // Matrix with some non-zeros should normalize properly along rows
//      GenerateRandRand01(rng_, s2);
//      s2.normalize(I1(UInt(0)));
//    }
//
//    { // Matrix with some non-zeros should normalize properly along cols
//      GenerateRandRand01(rng_, s2);
//      s2.normalize(I1(UInt(1)));
//    }
//
//    { // Matrix with some non-zeros should normalize properly
//      GenerateRandRand01(rng_, s2);
//      s2.normalize();
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestMaxSum()
//  {
//    {
//      I2 ub2(4, 5);
//      S2 s2(ub2);
//      S1 s1_max_row(ub2[0]), s1_max_col(ub2[1]);
//      Real M, S;
//      M = 0; S = 0;
//      I2 idxmax;
//
//      ITER_2(ub2[0], ub2[1]) {
//        I2 i2(i, j);
//        UInt o = i2.ordinal(ub2);
//        if (o % 2 == 0) {
//          s2.set(i2, Real(o));
//          s1_max_row.update(I1((UInt)i), Real(o), nta::Max<Real>());
//          s1_max_col.update(I1((UInt)j), Real(o), nta::Max<Real>());
//          if (o > M) { M = Real(o); idxmax = i2; }
//          S += o;
//        }      
//      }       
//
//      S1 s10(ub2[1]);  
//      s2.max(I1((UInt)0), s10); // max of each column, in a vector
//      Test("SparseTensor max 1", s10 == s1_max_col, true);
//     
//      S1 s11(ub2[0]);
//      s2.max(I1((UInt)1), s11); // max of each row, in a vector
//      Test("SparseTensor max 2", s11 == s1_max_row, true);
//
//      std::pair<I2, Real> MM = s2.max();
//      Test("SparseTensor max 1A", MM.first, idxmax);
//      Test("SparseTensor max 1B", MM.second, M);
//
//      Real SS = s2.sum();
//      Test("SparseTensor sum 1", S, SS);
//    }
//
//    { // specific tensor 
//      S2 s2(I2(2, 1));
//      s2.set(I2(0,0), 70);
//      s2.set(I2(1,0), 10);
//      Test("SparseTensor max 3", s2.max().first, I2(0,0));
//      Test("SparseTensor max 4", s2.max().second, Real(70));
//    }  
//
//    { // empty tensor
//      S2 s2(I2(2, 1));
//      Test("SparseTensor max 5", s2.max().first, s2.getNewZeroIndex());
//      Test("SparseTensor max 6", s2.max().second, Real(0));
//    }
//
//    { // empty tensor
//      S2 s2(I2(2, 1));
//      Test("SparseTensor sum 2", s2.sum(), 0);
//    }
//  }     
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestAxby()
//  {
//  
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestMultiply()
//  {
//    I2 ub(4, 5); I2 idx;
//    S2 A(ub), C(ub), Cref(ub);
//
//    for (UInt i = 0; i < 20; ++i) {
//
//      // Catches -1, 0 and 1
//      // Important to test zero, because it triggers deletion
//      // from the map, which invalidates iterator!
//      for (Real k = -2; k < 2.25; k += .25) {
//        {
//          GenerateRandRand01(rng_, A); 
//          Cref.clear();
//          setToZero(idx);
//          do {
//            Cref.set(idx, k * A.get(idx));
//          } while (increment(ub, idx));
//          A.multiply(k);
//          Test("SparseTensor in place * k", A, Cref);
//        }
//      
//        {
//          GenerateRandRand01(rng_, A); 
//          GenerateRandRand01(rng_, C); // noise in C
//          Cref.clear();
//          setToZero(idx);
//          do {
//            Cref.set(idx, k * A.get(idx));
//          } while (increment(ub, idx));
//          A.multiply(k, C);
//          Test("SparseTensor * k", C, Cref);
//        }
//      }
//    }
//
//    { // very large multiplied by very small
//      S1 s1(I1(5));
//      s1.set(I1(3), Real(1e12));
//      s1.multiply(Real(1e-12));
//      Test("SparseTensor multiply micromegas", s1.sum(), Real(1.0));
//    }
//  }   
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestPerformance()
//  {
//    /*
//    typedef Index<unsigned long, 4> IL4;
//    typedef SparseTensor<IL4, Real> SL4;
//   
//    IL4 ub(100000, 100000, 100000, 100000);
//    SL4 a(ub), b(ub), c(ub);    
//    UInt nnz = 500000;      
//    GenerateRand01(rng_, nnz, a);
//    GenerateRand01(rng_, nnz, b);
//
//    timer t;  
//    a.add(b, c);         
//    */
//  }    
//
//  //--------------------------------------------------------------------------------
//  void SparseTensorUnitTest::unitTestNumericalStability()
//  {
//    ITER_1(1) {
//      S2 m(I2(20, 20));
//      GenerateRandRand01(rng_, m);
//      m.normalize(I1(UInt(1)));
//      S1 v(I1(UInt(20))), ref(I1(UInt(20)));
//      m.sum(I1(UInt(1)), v);
//      v.element_apply(1 - _1);
//      S1::const_iterator it1, it2;
//      for (it1 = v.begin(), it2 = ref.begin(); it1 != v.end(); ++it1, ++it2)
//        if (!nearlyEqual(it1->second, it2->second))
//          Test("SparseTensor numerical stability", true, false);
//    }
//  }
//
  //--------------------------------------------------------------------------------
  void SparseTensorUnitTest::RunTests()
  {
    //
    //unitTestConstruction();
    //unitTestGetSet();
    //unitTestExtract();
    //unitTestReduce();
    //unitTestNonZeros();
    //unitTestIsSymmetric();
    //unitTestToFromDense();   
    //unitTestPermute();
    //unitTestResize();
    //unitTestReshape();   
    //unitTestSlice();           
    //unitTestElementApply();  
    //unitTestFactorApply();
    //unitTestAccumulate();   
    //unitTestOuterProduct();      
    //unitTestContract();   
    //unitTestInnerProduct();   
    //unitTestIntersection();
    //unitTestUnion();
    //unitTestDynamicIndex();
    //unitTestToFromStream();
    //unitTestNormalize();
    //unitTestMaxSum();
    //unitTestAxby();
    //unitTestMultiply();
    ////unitTestNumericalStability();
    ////unitTestPerformance();
  } 

  //--------------------------------------------------------------------------------
  
} // namespace nta


