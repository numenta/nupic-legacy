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
 * Implementation of unit testing for class Index
 */     
              
//#include <nta/common/version.hpp>
#include <nta/math/array_algo.hpp>

#include "IndexUnitTest.hpp"

#include <boost/timer.hpp>       
   
using namespace std;  

namespace nta {
//
//  //--------------------------------------------------------------------------------
//  void IndexUnitTest::unitTestFixedIndex()
//  {
//    { // Default constructor
//      const I5 i0;
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index default constructor", i0[i], (UInt)0);
//    }
//
//    { // Constructor from array
//      UInt idx[5];
//      for (UInt i = 0; i < 5; ++i)
//        idx[i] = i+1;
//      const I5 i1(idx);
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index constructor from array", i1[i], i+1);
//    }
//        
//    { // Constructor with ellipsis
//      const I5 i2(5, 4, 3, 2, 1);
//      for (int i = 5; i > 0; --i)
//        Test("Index constructor from list", i2[5-i], (UInt)i);
//    }
//
//    { // Copy constructor
//      const I5 idx1;
//      const I5 idx2(idx1);
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index copy constructor 1", idx2[i], (UInt)0);
//      
//      const I5 i3(5, 4, 3, 2, 1);
//      I5 i4(i3);
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index copy constructor 2", i4[i], i3[i]);
//    }
//
//    { // Assignment operator
//      const I5 idx1;
//      const I5 idx2 = idx1;
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index assignment operator 1", idx2[i], (UInt)0);
//
//      const I5 i3(5, 4, 3, 2, 1);
//      I5 i4 = i3;
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index assignment operator 2", i4[i], i3[i]);
//    }
//
//    { // Operator[]
//      I5 i3(5, 4, 3, 2, 1);
//      for (UInt i = 0; i < 5; ++i)
//        i3[i] = i+1;
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index operator[]", i3[i], i+1);
//
//      const I5 i4(5, 4, 3, 2, 1);
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index operator[] const", i4[i], 5-i);
//    }  
//
//    { // begin(), end()
//      I5 idx(5, 4, 3, 2, 1);
//      Test("Index begin", *idx.begin(), (I5::value_type)5);
//      Test("Index end", *(idx.end()-1), (I5::value_type)1);
//      UInt i = 5;
//      for (I5::iterator it = idx.begin(); it != idx.end(); ++it, --i)
//        Test("Index iterator", *it, (I5::value_type)i);
//    }
//
//    { // size()
//      I5 idx(5, 4, 3, 2, 1);
//      Test("Index size", idx.size(), (UInt)5);
//    }
//
//    {
//      // Incrementing along one dimension only
//      I5 lb2(6, 7, 0, 3, 4), ub(6, 7, 5, 3, 4), idx;
//      idx = lb2;
//      Test("Index stride 0", ub.stride(0), (UInt)(7*5*3*4));
//      Test("Index stride 1", ub.stride(1), (UInt)(5*3*4));
//      Test("Index stride 2", ub.stride(2), (UInt)(3*4));
//      Test("Index stride 3", ub.stride(3), (UInt)(4));
//      Test("Index stride 4", ub.stride(4), (UInt)1);
//      UInt ord = idx.ordinal(ub);
//      UInt n = 0;
//      do {
//        Test("Index inc one dim", idx.ordinal(ub), ord);
//        Test("Index inc one dim dist", lb2.distance(ub, idx), n*ub.stride(2));
//        ord += ub.stride(2);
//        ++n;
//      } while (idx.increment(lb2, ub));
//    }
//
//    { // operator==
//      I5 i1(5, 4, 3, 2, 1);
//      I5 i2(1, 2, 3, 4, 5);
//      Test("Index operator== 1 ", ! (i1 == i2), true);
//        
//      I5 i3(5, 4, 3, 2, 1);
//      Test("Index operator== 2 ", (i1 == i3), true);
//    }
//
//    { // operator!=
//      I5 i1(5, 4, 3, 2, 1);
//      I5 i2(1, 2, 3, 4, 5);
//      Test("Index operator!= 1 ", (i1 != i2), true);
//        
//      I5 i3(5, 4, 3, 2, 1);
//      Test("Index operator!= 2 ", ! (i1 != i3), true);
//    }
//
//    { // ordinal/setFromOrdinal         
//      I1 ub((UInt)5);
//      for (UInt i = 0; i < 5; ++i) {
//        I1 i1((UInt)i);
//        Test("Index<1> ordinal 1", ordinal(ub, i1), i);
//        I1 i2; setFromOrdinal(ub, i, i2);
//        Test("Index<1> setFromOrdinal 1", i1, i2);
//      }                 
//    }
//    
//    { // increment/ordinal
//      UInt i = 0;
//      I1 i1, i2, ub((UInt)5);
//      do {
//        Test("Index<1> increment 2", ordinal(ub, i1), i);
//        setFromOrdinal(ub, i, i2);
//        Test("Index<1> setFromOrdinal 2", i1, i2);
//        ++i;
//      } while (increment(ub, i1));
//    }
//
//    { // increment/ordinal/setFromOrdinal
//      I5 ub(6, 7, 5, 3, 4), idx;
//      UInt i = 0;
//      do {   
//        UInt n = ordinal(ub, idx);
//        I5 idx2(ub, n);
//        Test("Index increment/ordinal 1", idx, idx2);
//        Test("Index increment/ordinal 2", n, i);
//        I5 idx3;
//        setFromOrdinal(ub, i, idx3);
//        Test("Index increment/setFromOrdinal 1", idx, idx3);
//        ++i;
//      } while (increment(ub, idx));
//    }
//     
//    { // incrementing between bounds 
//      I5 lb(4, 5, 3, 1, 2), ub(6, 7, 5, 3, 4), idx(lb);
//      do {
//      } while (increment(lb, ub, idx));   
//    }
//
//    { // incrementing between bounds, over and under => exceptions
//      I5 lb(4, 5, 3, 1, 3), ub(6, 7, 5, 3, 4);
//      I5 idx1(1, 1, 1, 1, 1);
//      I5 idx2(8, 8, 8, 8, 8);
//    }
//
//    { // setToZero
//      I5 i1;
//      setToZero(i1);
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index setToZero 1", i1[i], (UInt)0);
//
//      I5 i2(5, 4, 3, 2, 1);
//      setToZero(i2);  
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index setToZero 2", i2[i], (UInt)0);
//
//      setToZero(i2);
//      for (UInt i = 0; i < 5; ++i)
//        Test("Index setToZero 2", i2[i], (UInt)0);
//    }
//
//    { // isSet
//      I5 i3(5, 4, 3, 2, 1);
//      Test("Index isSet 1", isSet(i3), true);
//      i3[0] = 1;
//      Test("Index isSet 2", isSet(i3), false);
//    }
//
//    { // product
//      Test("Index product 1", product(I1((UInt)5)), (UInt)5);
//      Test("Index product 2", product(I1((UInt)0)), (UInt)0);
//      Test("Index product 3", product(I2(4, 5)), (UInt)4*5);
//      Test("Index product 4", product(I2(4, 0)), (UInt)0);
//      Test("Index product 5", product(I2(0, 5)), (UInt)0);
//      Test("Index product 6", product(I2(0, 0)), (UInt)0);
//      Test("Index product 7", product(I3(9, 7, 3)), (UInt)9*7*3);
//      Test("Index product 8", product(I3(9, 7, 0)), (UInt)0);
//      Test("Index product 9", product(I3(9, 0, 3)), (UInt)0);
//      Test("Index product 10", product(I3(0, 7, 3)), (UInt)0);
//      Test("Index product 11", product(I3(0, 0, 3)), (UInt)0);
//      Test("Index product 12", product(I3(9, 0, 0)), (UInt)0);
//      Test("Index product 13", product(I3(0, 7, 0)), (UInt)0);
//      Test("Index product 14", product(I3(0, 0, 0)), (UInt)0);
//    }
//
//    { // complement
//      {           
//        I3 i3(0, 2, 4), c;
//        complement(i3, c);
//        Test("Index complement 1", c, I3(1, 3, 5));
//      }
//
//      {
//        I2 i2(0, 2); 
//        I1 c;
//        complement(i2, c);
//        Test("Index complement 2", c, I1(1));
//      }
//       
//      {
//        I1 i1((UInt)0), c; 
//        complement(i1, c);
//        Test("Index complement 3", c, I1(1));
//      }
//
//      {
//        I2 i2(0, 1);    
//        I1 c;
//        complement(i2, c);
//        Test("Index complement 4", c, I1(2));
//      }
//
//      {
//        I2 i2(0, 2);
//        I4 c;
//        complement(i2, c);
//        Test("Index complement 5", c, I4(1, 3, 4, 5));
//      }
//    }
//
//    
//
//    { // project
//      const I3 i3(9, 7, 3);
//
//      I3 i3p;
//      const I3 dims3(0, 1, 2);
//      project(dims3, i3, i3p);
//      Test("Index project 1A", i3p[0], (UInt)9);
//      Test("Index project 2A", i3p[1], (UInt)7);
//      Test("Index project 3A", i3p[2], (UInt)3);
//
//      I2 i2;
//      const I2 dims1(0, 2);
//      project(dims1, i3, i2);
//      Test("Index project 4A", i2[0], (UInt)9);
//      Test("Index project 5A", i2[1], (UInt)3);
//
//      const I3 i4(3, 2, 1);
//      I1 i1;
//      for (UInt i = 0; i < 3; ++i) {
//        const I1 dims2(i);
//        project(dims2, i4, i1);
//        Test("Index project 6", i4[i], (UInt)3-i);
//      }
//    }
//    
//    { // embed 
//      {
//        I3 i3A(1, 2, 3), dims(0, 1, 2), i3B;
//        embed(dims, i3A, i3B);
//        Test("Index embed 0A", i3A, i3B);
//      }
//
//      {
//        I6 i6;
//        const I3 dims(1, 3, 5), i3(9, 7, 3); 
//        embed(dims, i3, i6);     
//        Test("Index embed 1A", i6, I6(0, 9, 0, 7, 0, 3));
//
//        I6 i6B;
//        //embed(dims, i6, i6B);
//        //Test("Index embed 1B", i6, i6B);
//      }
//
//      {
//        I6 i6;
//        const I3 dims(0, 2, 4), i3(9, 7, 3); 
//        embed(dims, i3, i6);
//        Test("Index embed 2", i6, I6(9, 0, 7, 0, 3, 0));
//      }
//
//      {
//        I6 i6;
//        I2 i2(2, 4), dims(1, 3);
//        I4 i4(1, 3, 5, 6), compDims;
//        embed(dims, i2, i6);
//        Test("Index embed 3", i6, I6(0, 2, 0, 4, 0, 0));
//        dims.complement(compDims);
//        embed(compDims, i4, i6);
//        Test("Index embed 4", i6, I6(1, 2, 3, 4, 5, 6));
//      }
//
//      { // embed is the reciprocal of project
//        I6 i6;
//        
//        {
//          I3 dims(1, 3, 5), i3A(9, 7, 3), i3B; 
//          embed(dims, i3A, i6);     
//          project(dims, i6, i3B);
//          Test("Index embed 5", i3A, i3B);
//        }
//
//        {
//          I3 dims(0, 2, 4), i3A(9, 7, 3), i3B; 
//          embed(dims, i3A, i6);
//          project(dims, i6, i3B);
//          Test("Index embed 6", i3A, i3B);
//        }
//      }
//    }
//
//    {
//      I5 i00;
//      I5 i0(1, 2, 3, 4, 5);
//      I5 i1(2, 3, 4, 5, 6);
//      I5 i2(3, 4, 5, 6, 7);
//
//      Test("Index operator< 1", (i0 < i0), false);
//      Test("Index operator< 2", (i0 < i1), true);
//      Test("Index operator< 3", !(i1 < i0), true);
//      Test("Index operator< 4", (i1 < i2), true);
//      Test("Index operator< 5", (i0 < i2), true);
//      Test("Index operator< 6", (i00 < i0), true);
//
//      std::map<I3, UInt> m;
//      I3 idx, ub(9, 7, 3);
//      do {
//        m[idx] = idx.ordinal(ub);
//      } while (idx.increment(ub));
//      Test("Index operator< 7", m.size(), (UInt)9*7*3);
//
//      std::map<I3, UInt>::const_iterator it;
//      UInt i;
//      for (i = 0, it = m.begin(); i < 9*7*3; ++i, ++it) {
//        Test("Index operator< 8", I3(ub, i), it->first);
//        Test("Index operator< 9", i, it->second);
//      }
//    }
//
//    { // <=
//      I5 i00;
//      I5 i0(1, 2, 3, 4, 5);
//      I5 i1(2, 3, 4, 5, 6);
//      I5 i2(3, 4, 5, 6, 7);
//        
//      Test("Index operator<= 1", (i0 <= i0), true);
//      Test("Index operator<= 2", (i0 <= i1), true);
//      Test("Index operator<= 3", (i1 <= i2), true);
//      Test("Index operator<= 4", (i0 <= i2), true);
//      Test("Index operator<= 5", (i00 <= i0), true);
//    }
//
//    { // concatenation
//      I5 i0(1, 2, 3, 4, 5);
//      I5 i1(6, 7, 8, 9, 10);
//      Index<UInt, 10> i2 = concatenate(i0, i1);
//      for (UInt i = 1; i <= 10; ++i)
//        Test("Index concatenation", i2[i-1], i);
//    }
//
//    { // permutations
//      I5 i5(1, 2, 3, 4, 5), ind(1, 2, 3, 4, 0);
//      I5 perm = i5.permute(ind);
//      Test("Index permutation 1", perm, I5(2, 3, 4, 5, 1));
//      I5 ind2 = i5.findPermutation(perm);
//      Test("Index permutation 2", ind2, ind);
//    }
//
//    { // positiveInBounds
//      I3 ub(1, 3, 4);
//      Test("Index positiveInBounds 4", positiveInBounds(I3(0,0,0), ub), true);
//      Test("Index positiveInBounds 1", positiveInBounds(I3(0,2,3), ub), true);
//      Test("Index positiveInBounds 1", positiveInBounds(I3(0,3,3), ub), false);
//      Test("Index positiveInBounds 2", positiveInBounds(I3(0,2,4), ub), false);
//      Test("Index positiveInBounds 3", positiveInBounds(I3(4,5,6), ub), false);
//      Test("Index positiveInBounds 3", positiveInBounds(I3(1,2,3), ub), false);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  template <typename IndexA, typename IndexB>
//  inline bool Compare(const IndexA& ia, const IndexB& ib)
//  {
//    return std::equal(ia.begin(), ia.end(), ib.begin());
//  }
//
//  //--------------------------------------------------------------------------------
//  template <UInt R>
//  inline std::vector<UInt> MakeVIdx(const Index<UInt, R>& fidx)
//  {
//    std::vector<UInt> vidx(fidx.size());
//    for (UInt i = 0; i < fidx.size(); ++i)
//      vidx[i] = fidx[i];
//    return vidx;
//  }
//
//  //--------------------------------------------------------------------------------
//  void IndexUnitTest::unitTestDynamicIndex()
//  {
//    typedef std::vector<UInt> Idx;
//        
//    {   
//      Idx i3(5); i3[0] = 5; i3[1] = 4; i3[2] = 3; i3[3] = 2; i3[4] = 1;
//      setToZero(i3);  
//      for (UInt i = 0; i < 5; ++i)
//        Test("Dynamic Index setToZero", i3[i], (UInt)0);
//    }
//
//    {
//      Idx i3(5); i3[0] = 5; i3[1] = 4; i3[2] = 3; i3[3] = 2; i3[4] = 1;
//      Test("Dynamic Index isSet 1", isSet(i3), true);
//      i3[0] = 4;
//      Test("Dynamic Index isSet 2", isSet(i3), false);
//    }
//
//    {
//      Idx i(3), ub(3), j(3), iprev(3);
//      ub[0] = 3; ub[1] = 2; ub[2] = 5;
//      setToZero(i);  
//      UInt n = 0;
//      do {
//        Test("Dynamic Index ordinal", ordinal(ub, i), n);
//        setFromOrdinal(ub, n, j);
//        Test("Dynamic Index setFromOrdinal", Compare(i, j), true);
//        if (n > 0)
//          Test("Dynamic Index operator<", (iprev < i), true);
//        iprev = i;
//        ++n;
//      } while (increment(ub, i));
//    }
//
//    { 
//      Idx i3(3); i3[0] = 9; i3[1] = 7; i3[2] = 3;
//      Test("Dynamic Index product", product(i3), (UInt)9*7*3);
//    }
//
//    {
//      Idx i3(3), c(3); i3[0] = 0; i3[1] = 2; i3[2] = 4;
//      complement(i3, c);
//      Test("Dynamic Index complement 1", Compare(c, I3(1, 3, 5)), true);
//    }
//
//    { 
//      Idx i3(3); i3[0] = 9; i3[1] = 7; i3[2] = 3;
//
//      Idx i3p(3);
//      const I3 dims3(0, 1, 2);
//      project(dims3, i3, i3p);
//      Test("Dynamic Index project 1", i3p[0], (UInt)9);
//      Test("Dynamic Index project 2", i3p[1], (UInt)7);
//      Test("Dynamic Index project 3", i3p[2], (UInt)3);
//
//      Idx i2(2);   
//      const I2 dims1(0, 2);   
//      project(dims1, i3, i2);
//      Test("Dynamic Index project 4", i2[0], (UInt)9);
//      Test("Dynamic Index project 5", i2[1], (UInt)3);
//
//      I3 i4(3); i4[0] = 3; i4[1] = 2; i4[2] = 1;
//      Idx i1(1);
//      for (UInt i = 0; i < 3; ++i) {
//        const I1 dims2(i);
//        project(dims2, i4, i1);
//        Test("Dynamic Index project 6", i4[i], (UInt)3-i);
//      }
//    }   
//
//    {   
//      Idx i1(3); i1[0] = 5; i1[1] = 4; i1[2] = 3;
//      Idx i2(3); i2[0] = 2; i2[1] = 1; i2[2] = 0;
//      Idx i3(6);   
//      i3 = concatenate(i1, i2);
//      for (int i = 5; i >= 0; --i)
//        Test("Dynamic Index concatenate", i3[5-i], (UInt)i);
//    }       
//       
//    { // permutations
//      Idx i5(5); i5[0] = 1; i5[1] = 2; i5[2] = 3; i5[3] = 4; i5[4] = 5;
//      Idx ind(5); ind[0] = 1; ind[1] = 2; ind[2] = 3; ind[3] = 4; ind[4] = 0;
//      Idx perm(5); 
//      nta::permute(ind, i5, perm);
//      Test("Dynamic Index permutation 1", Compare(perm, I5(2, 3, 4, 5, 1)), true);
//    }
//
//    { // Can it be a key in a std::map?
//      Idx i00(5); setToZero(i00);
//      Idx i0(5); i0 = MakeVIdx(I5(1, 2, 3, 4, 5));
//      Idx i1(5); i1 = MakeVIdx(I5(2, 3, 4, 5, 6));
//      Idx i2(5); i2 = MakeVIdx(I5(3, 4, 5, 6, 7));
//
//      Test("Dynamic Index operator< 1", (i0 < i0), false);
//      Test("Dynamic Index operator< 2", (i0 < i1), true);
//      Test("Dynamic Index operator< 3", !(i1 < i0), true);
//      Test("Dynamic Index operator< 4", (i1 < i2), true);
//      Test("Dynamic Index operator< 5", (i0 < i2), true);
//      Test("Dynamic Index operator< 6", (i00 < i0), true);
//
//      std::map<std::vector<UInt>, UInt> m;
//      Idx idx(3); I3 ub(9, 7, 3);
//      do {
//        m[idx] = ordinal(ub, idx);
//      } while (increment(ub, idx));
//      Test("Dynamic Index operator< 7", m.size(), (UInt)9*7*3);
//
//      std::map<std::vector<UInt>, UInt>::const_iterator it;
//      UInt i;
//      for (i = 0, it = m.begin(); i < 9*7*3; ++i, ++it) {
//        Test("Dynamic Index operator< 8", indexEq(I3(ub, i), it->first), true);
//        Test("Dynamic Index operator< 9", i, it->second);
//      }
//    }   
//  }
//
  //--------------------------------------------------------------------------------
  void IndexUnitTest::RunTests()
  {

    //unitTestFixedIndex();
    //unitTestDynamicIndex();
  }

  //--------------------------------------------------------------------------------
  
} // namespace nta


