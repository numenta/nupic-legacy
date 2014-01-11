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
 * Implementation of unit testing for class DenseTensor
 */  
              
//#include <nta/common/version.hpp>
#include <nta/math/stl_io.hpp>
#include "DenseTensorUnitTest.hpp"

using namespace std;  

namespace nta {
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestConstructor()
//  {
//    D3 d(D3::TensorIndex(4U, 4U, 4U));
//
//    {
//      ITER_3(3, 3, 3) {
//        D3::TensorIndex idx(i, j, k);
//        Test("DenseTensor bounds constructor", d.get(idx), (Real)0);
//      }
//       
//      Test("DenseTensor getNNonZeros 1", d.getNNonZeros(), (UInt)0);
//      Test("DenseTensor getBounds 1", d.getBounds(), D3::TensorIndex(4, 4, 4));
//    }
//
//    {    
//      ITER_3(3, 3, 3) {
//        D3::TensorIndex idx(i, j, k);
//        d.set(idx, Real(i*16+j*4+k));
//        Test("DenseTensor bounds get", d.get(idx), i*16+j*4+k);
//      }
//       
//      Test("DenseTensor getNNonZeros 1", d.getNNonZeros(), (UInt)3*3*3-1);
//      Test("DenseTensor getBounds 1", d.getBounds(), D3::TensorIndex(4, 4, 4));
//    }
//
//    D4 d4(5, 4, 3, 2);
//    Test("DenseTensor list constructor", d4.getBounds(), Index<UInt, 4>(5, 4, 3, 2));
//    ITER_4(5, 4, 3, 2) {
//      Index<UInt, 4> i4(i, j, k, l);
//      Test("DenseTensor list constructor", d4.get(i4), (Real)0);
//    }
//
//    I4 ub(5, 4, 3, 2);
//
//    ITER_4(5, 4, 3, 2)
//      d4(i, j, k, l) = Real(I4(i, j, k, l).ordinal(ub) + 1);
//
//    D4 d42(d4);
//    Test("DenseTensor copy constructor", d4, d42);
//
//    D4 d43 = d4;
//    Test("DenseTensor assingment operator 1", d4, d43);
//
//    d4 = d4;
//    Test("DenseTensor assingment operator 2", d4, d43);
//  }
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestGetSet()
//  {
//    I3 ub(5, 4, 3);
//    
//    D3 d3(ub), d32(ub);
//    
//    ITER_3(ub[0], ub[1], ub[2]) {
//      d3.set(I3(i, j, k), Real(i*ub[1]*ub[2]+j*ub[2]+k));
//      d32.set(i, j, k, d3.get(i, j, k));
//      Test("DenseTensor set", d3.get(i, j, k), d32.get(i, j, k));
//    }
//
//    Test("DenseTensor set 1", d3.getNNonZeros(), (UInt)ub[0]*ub[1]*ub[2]-1);
//
//    ITER_3(ub[0], ub[1], ub[2]) {
//      Test("DenseTensor get 1", d3.get(I3(i, j, k)), i*ub[1]*ub[2]+j*ub[2]+k);
//      Test("DenseTensor get 2", d3.get(i, j, k), d3.get(I3(i, j, k)));
//      Test("DenseTensor get 3", d3(i, j, k), d3.get(I3(i, j, k)));
//    }
//  }
//    
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestIsSymmetric()
//  {
//    D3 d31(5, 4, 3);
//    Test("DenseTensor isSymmetric 1", d31.isSymmetric(I3(0, 2, 1)), false);
//
//    D3 d32(5, 3, 3);
//    Test("DenseTensor isSymmetric 2", d32.isSymmetric(I3(0, 2, 1)), true);
//    Test("DenseTensor isSymmetric 3", d32.isSymmetric(I3(1, 2, 0)), false);
//
//    d32.set(0, 0, 1, (Real).5);
//    Test("DenseTensor isSymmetric 4", d32.isSymmetric(I3(0, 2, 1)), false);
//    
//    d32.set(0, 1, 0, (Real).5);
//    Test("DenseTensor isSymmetric 5", d32.isSymmetric(I3(0, 2, 1)), true);
//
//    D2 d21(5, 5);
//    for (UInt i = 0; i < 5; ++i)
//      for (UInt j = i; j < 5; ++j)
//        d21(j, i) = d21(i, j) = Real(i*5+j+1);
//
//    Test("DenseTensor isSymmetric 6", d21.isSymmetric(I2(1, 0)), true);
//  }
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestPermute()
//  {
//    {
//      D2 d2(3, 4), ref(4, 3);
//      
//      ITER_2(3, 4) {
//        d2.set(I2(i, j), Real(i*4+j+1));
//        ref.set(I2(j, i), d2.get(i, j));
//      }
//      
//      d2.permute(I2(1, 0));
//      Test("DenseTensor permute 1", d2, ref);
//    }
//
//    {
//      D3 d3(3, 4, 5);
//      ITER_3(3, 4, 5) 
//        d3.set(I3(i, j, k), Real(i*20+j*4+k+1));
//
//      D3 ref3(3, 5, 4);
//      ITER_3(3, 4, 5)
//        ref3.set(I3(i, k, j), d3.get(i, j, k));
//
//      d3.permute(I3(0, 2, 1));
//      Test("DenseTensor permute 2", d3, ref3);
//    }
//
//    {
//      D3 d3(3, 4, 5);
//      ITER_3(3, 4, 5) 
//        d3.set(I3(i, j, k), Real(i*20+j*4+k+1));
//
//      D3 ref3(4, 5, 3);
//      ITER_3(3, 4, 5)
//        ref3.set(I3(j, k, i), d3.get(i, j, k));
//
//      d3.permute(I3(1, 2, 0));
//      Test("DenseTensor permute 3", d3, ref3);
//    }
//
//    {
//      D3 d3(3, 4, 5);
//      ITER_3(3, 4, 5) 
//        d3.set(I3(i, j, k), Real(i*20+j*4+k+1));
//
//      D3 ref3(4, 3, 5);
//      ITER_3(3, 4, 5)
//        ref3.set(I3(j, i, k), d3.get(i, j, k));
//
//      d3.permute(I3(1, 0, 2));
//      Test("DenseTensor permute 4", d3, ref3);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestResize()
//  {
//    {   
//      D2 d2(3, 4);
//      ITER_2(3, 4) d2.set(I2(i, j), Real(i*4+j));
//
//      {
//        D2 ref(3, 4);
//        ITER_2(3, 4) ref.set(i, j, d2.get(i, j));
//        d2.resize(I2(3, 4));
//        Test("DenseTensor resize 0", d2, ref);
//      }
//
//      {
//        D2 ref(3, 5);
//        ITER_2(3, 4) ref.set(i, j, d2.get(i, j));
//        d2.resize(I2(3, 5));
//        Test("DenseTensor resize 1", d2, ref);
//      }
//
//      {
//        D2 ref(4, 5);
//        ITER_2(3, 4) ref.set(i, j, d2.get(i, j));
//        d2.resize(I2(4, 5));
//        Test("DenseTensor resize 2", d2, ref);
//      }
//
//      {
//        D2 ref(5, 6);
//        ITER_2(3, 4) ref.set(i, j, d2.get(i, j));
//        d2.resize(I2(5, 6));
//        Test("DenseTensor resize 3", d2, ref);
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestReshape()
//  {
//    {
//      D2 d2(3, 4), d2r(3, 4), ref(3, 4);
//      
//      ITER_2(3, 4) 
//        d2.set(I2(i, j), Real(i*4+j));
//      
//      ITER_2(3, 4)
//        ref.set(I2(i, j), Real(i*4+j));
//      
//      d2.reshape(d2r);
//      Test("DenseTensor reshape 0", d2r, ref);
//    }
//
//    {
//      D2 d2(3, 4), d2r(2, 6), ref(2, 6);
//      
//      ITER_2(3, 4) 
//        d2.set(I2(i, j), Real(i*4+j));
//      
//      ITER_2(2, 6)
//        ref.set(I2(i, j), Real(i*6+j));
//       
//      d2.reshape(d2r);
//      Test("DenseTensor reshape 1", d2r, ref);
//    }
//
//    {
//      D2 d2(3, 4);
//      D3 d3r(2, 2, 3), ref(2, 2, 3);
//      
//      ITER_2(3, 4)
//        d2.set(I2(i, j), Real(i*4+j));
//      
//      ITER_3(2, 2, 3)
//        ref.set(I3(i, j, k), Real(i*6+j*3+k));
//      
//      d2.reshape(d3r);
//      Test("DenseTensor reshape 2", d3r, ref);
//    }
//
//    {
//      D3 d3(2, 2, 3);
//      D2 d2r(3, 4), ref(3, 4);
//      
//      ITER_3(2, 2, 3)
//        d3.set(I3(i, j, k), Real(i*6+j*3+k));
//
//      ITER_2(3, 4)
//        ref.set(I2(i, j), Real(i*4+j));
//           
//      d3.reshape(d2r);
//      Test("DenseTensor reshape 3", d2r, ref);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestSlice()
//  { 
//    D3 d(D3::TensorIndex(5, 4, 3));
//
//    {
//      ITER_3(5, 4, 3) 
//        d.set(D3::TensorIndex(i, j, k), Real(i*16+j*4+k+1));
//    }
//
//    {
//      Domain<UInt> dom(D3::TensorIndex(5, 4, 3));
//      D3 d3(D3::TensorIndex(5, 4, 3));
//      d.getSlice(dom, d3);
//      Test("DenseTensor getSlice 1", (d == d3), true);
//    }
//
//    {
//      for (UInt u = 0; u < 5; ++u) {
//        D2 d2ref(D2::TensorIndex(4, 3));
//        ITER_2(4, 3)
//          d2ref.set(D2::TensorIndex(i, j), Real(u*16+i*4+j+1));
//          
//        Domain<UInt> dom(D3::TensorIndex(u, 0, 0), D3::TensorIndex(u, 4, 3));
//        D2 d2(D2::TensorIndex(4, 3));
//        d.getSlice(dom, d2);
//        Test("DenseTensor getSlice 2", (d2 == d2ref), true);
//      }
//    }
//
//    {
//      for (UInt u = 0; u < 4; ++u) {
//        D2 d2ref(D2::TensorIndex(5, 3));
//        ITER_2(5, 3)
//          d2ref.set(D2::TensorIndex(i, j), Real(i*16+u*4+j+1));
//          
//        Domain<UInt> dom(D3::TensorIndex(0, u, 0), D3::TensorIndex(5, u, 3));
//        D2 d2(D2::TensorIndex(5, 3));
//        d.getSlice(dom, d2);
//        Test("DenseTensor getSlice 3", (d2 == d2ref), true);
//      }
//    }
//
//    {
//      for (UInt u = 0; u < 3; ++u) {
//        D2 d2ref(D2::TensorIndex(5, 4));
//        ITER_2(5, 4)
//          d2ref.set(D2::TensorIndex(i, j), Real(i*16+j*4+u+1));
//          
//        Domain<UInt> dom(D3::TensorIndex(0, 0, u), D3::TensorIndex(5, 4, u));
//        D2 d2(D2::TensorIndex(5, 4));
//        d.getSlice(dom, d2);
//        Test("DenseTensor getSlice 4", (d2 == d2ref), true);
//      }
//    }
//
//    {
//      for (UInt u1 = 0; u1 < 4; ++u1)
//        for (UInt u2 = 0; u2 < 3; ++u2) {
//          D1 d1ref(D1::TensorIndex(5));
//          ITER_1(5)
//            d1ref.set(D1::TensorIndex(i), Real(i*16+u1*4+u2+1));
//            
//          Domain<UInt> dom(D3::TensorIndex(0, u1, u2), D3::TensorIndex(5, u1, u2));
//          D1 d1(D1::TensorIndex(5));
//          d.getSlice(dom, d1);
//          Test("DenseTensor getSlice 5", (d1 == d1ref), true);
//        }
//    }
//
//    {
//      for (UInt u1 = 0; u1 < 5; ++u1)
//        for (UInt u2 = 0; u2 < 3; ++u2) {
//          D1 d1ref(D1::TensorIndex(4));
//          ITER_1(4)
//            d1ref.set(D1::TensorIndex(i), Real(u1*16+i*4+u2+1));
//            
//          Domain<UInt> dom(D3::TensorIndex(u1, 0, u2), D3::TensorIndex(u1, 4, u2));
//          D1 d1(D1::TensorIndex(4));
//          d.getSlice(dom, d1);
//          Test("DenseTensor getSlice 6", (d1 == d1ref), true);
//        }
//    }
//
//    {
//      for (UInt u1 = 0; u1 < 5; ++u1)
//        for (UInt u2 = 0; u2 < 4; ++u2) {
//          D1 d1ref(D1::TensorIndex(3));
//          ITER_1(3)
//            d1ref.set(D1::TensorIndex(i), Real(u1*16+u2*4+i+1));
//            
//          Domain<UInt> dom(D3::TensorIndex(u1, u2, 0), D3::TensorIndex(u1, u2, 3));
//          D1 d1(D1::TensorIndex(3));
//          d.getSlice(dom, d1);
//          Test("DenseTensor getSlice 7", (d1 == d1ref), true);
//        }
//    }   
//  }
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestElementApply()
//  {
//    I4 ub4(5, 4, 3, 2);
//    D4 dA(ub4), dB(ub4), dC(ub4), dref(ub4);
//      
//    ITER_4(ub4[0], ub4[1], ub4[2], ub4[3]) {
//      Index<UInt, 4> idx(i, j, k, l);
//      dA.set(idx, Real(i*5*3*7+j*3*7+k*7+l+1));
//      dB.set(idx, Real(i*5*3*7+j*3*7+k*7+l+2));
//    }
//
//    ITER_4(ub4[0], ub4[1], ub4[2], ub4[3]) {
//      Index<UInt, 4> idx(i, j, k, l);
//      dref.set(idx, dA.get(idx) + dB.get(idx));
//    }
//
//    dA.element_apply(dB, dC, std::plus<Real>());
//    Test("DenseTensor element_apply 1", (dC == dref), true);
//
//    ITER_4(ub4[0], ub4[1], ub4[2], ub4[3]) {
//      Index<UInt, 4> idx(i, j, k, l);
//      dref.set(idx, dA.get(idx) + dB.get(idx));
//    }
//
//    dA.element_apply(dB, dA, std::plus<Real>());
//    Test("DenseTensor element_apply 2", (dA == dref), true);      
//
//    ITER_4(ub4[0], ub4[1], ub4[2], ub4[3]) {
//      Index<UInt, 4> idx(i, j, k, l);
//      dref.set(idx, dA.get(idx) * dB.get(idx));
//    }      
//      
//    dA.element_apply(dB, dC, nta::Multiplies<Real>());
//    Test("DenseTensor element_apply 3", (dC == dref), true);
//
//    ITER_4(ub4[0], ub4[1], ub4[2], ub4[3]) {
//      Index<UInt, 4> idx(i, j, k, l);
//      dref.set(idx, dA.get(idx) * dB.get(idx));
//    }
//    
//    dA.element_apply(dB, dA, nta::Multiplies<Real>());
//    Test("DenseTensor element_apply 4", (dA == dref), true);   
//
//    ITER_4(ub4[0], ub4[1], ub4[2], ub4[3]) {
//      Index<UInt, 4> idx(i, j, k, l);
//      dref.set(idx, dA.get(idx) * dA.get(idx));
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestFactorApply()
//  {
//    { 
//      D2 d2(3, 4), c(3, 4), ref(3, 4);
//        
//      ITER_2(3, 4) d2.set(I2(i, j), Real(i*4+j+1));
//
//      {    
//        ITER_2(3, 4) ref.set(I2(i, j), Real((i*4+j+1) * (j+2)));
//        D1 d1(4); ITER_1(4) d1.set(I1((UInt)i), Real(i+2));
//        d2.factor_apply(I1(1), d1, c, nta::Multiplies<Real>());
//        Test("DenseTensor factor_apply 1", c, ref);
//      }
//
//      {
//        ITER_2(3, 4) ref.set(I2(i, j), Real((i*4+j+1) * (i+2)));
//        D1 d1(3); ITER_1(3) d1.set(I1((UInt)i), Real(i+2));
//        d2.factor_apply(I1((UInt)0), d1, c, nta::Multiplies<Real>());
//        Test("DenseTensor factor_apply 2", c, ref);
//      }
//    }    
//      
//    {
//      I3 ub(4, 2, 3);
//      D3 d3(ub), c(ub), ref(ub);
//        
//      ITER_3(ub[0], ub[1], ub[2]) 
//        { I3 i3(i, j, k); d3.set(i3, Real(i3.ordinal(ub))); }
//
//      {
//        D1 d1(ub[0]); ITER_1(ub[0]) d1.set(I1((UInt)i), Real(i+2));
//        ITER_3(ub[0], ub[1], ub[2]) 
//          { I3 i3(i, j, k); ref.set(i3, Real(i3.ordinal(ub)*(i+2))); }
//        d3.factor_apply(I1((UInt)0), d1, c, nta::Multiplies<Real>());
//        Test("DenseTensor factor_apply 3", c, ref);
//      }
//
//      {
//        D1 d1(ub[1]); ITER_1(ub[1]) d1.set(I1((UInt)i), Real(i+2));
//        ITER_3(ub[0], ub[1], ub[2]) 
//          { I3 i3(i, j, k); ref.set(i3, Real(i3.ordinal(ub)*(j+2))); }
//        d3.factor_apply(I1((UInt)1), d1, c, nta::Multiplies<Real>());
//        Test("DenseTensor factor_apply 4", c, ref);
//      }
//
//      {
//        D1 d1(ub[2]); ITER_1(ub[2]) d1.set(I1((UInt)i), Real(i+2));
//        ITER_3(ub[0], ub[1], ub[2]) 
//        { I3 i3(i, j, k); ref.set(i3, Real(i3.ordinal(ub)*(k+2))); }
//        d3.factor_apply(I1((UInt)2), d1, c, nta::Multiplies<Real>());
//        Test("DenseTensor factor_apply 5", c, ref);
//      }    
//
//      {    
//        D2 d2(ub[1], ub[2]); 
//        ITER_2(ub[1], ub[2]) d2.set(I2(i, j), Real(i*ub[2]+j+2));
//        ITER_3(ub[0], ub[1], ub[2]) 
//          { I3 i3(i, j, k); ref.set(i3, Real(i3.ordinal(ub)*(j*ub[2]+k+2))); }
//        d3.factor_apply(I2(1, 2), d2, c, nta::Multiplies<Real>());
//        Test("DenseTensor factor_apply 6", c, ref);
//      }
//
//      {
//        D2 d2(ub[0], ub[2]); 
//        ITER_2(ub[0], ub[2]) d2.set(I2(i, j), Real(i*ub[2]+j+2));
//        ITER_3(ub[0], ub[1], ub[2]) 
//          { I3 i3(i, j, k); ref.set(i3, Real(i3.ordinal(ub)*(i*ub[2]+k+2))); }
//        d3.factor_apply(I2(0, 2), d2, c, nta::Multiplies<Real>());
//        Test("DenseTensor factor_apply 7", c, ref);
//      }
//
//      {
//        D2 d2(ub[0], ub[1]); 
//        ITER_2(ub[0], ub[1]) d2.set(I2(i, j), Real(i*ub[1]+j+2));
//        ITER_3(ub[0], ub[1], ub[2]) 
//          { I3 i3(i, j, k); ref.set(i3, Real(i3.ordinal(ub)*(i*ub[1]+j+2))); }
//        d3.factor_apply(I2(0, 1), d2, c, nta::Multiplies<Real>());
//        Test("DenseTensor factor_apply 8", c, ref);
//      }   
//      
//      {
//        D3 d32(ub[0], ub[1], ub[2]);
//        ITER_3(ub[0], ub[1], ub[2]) { 
//          I3 i3(i, j, k); 
//          d32.set(i3, Real(i3.ordinal(ub)+1)); 
//          ref.set(i3, Real(i3.ordinal(ub) * (i3.ordinal(ub)+1)));
//        }
//        d3.factor_apply(I3(0, 1, 2), d32, c, nta::Multiplies<Real>());
//        Test("DenseTensor factor_apply 9", c, ref);
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestAccumulate()
//  {
//    {
//      D2 d2(3, 4); ITER_2(3, 4) d2.set(I2(i, j), Real(i*4+j+1));
//
//      {
//        D1 d1(3), ref(3); 
//        ITER_2(3, 4) ref.set(I1((UInt)i), ref.get(I1((UInt)i)) + d2.get(I2(i, j)));
//        d2.accumulate(I1((UInt)1), d1, std::plus<Real>());
//        Test("DenseTensor accumulate 1", d1, ref);
//      }
//
//      {
//        D1 d1(4), ref(4); 
//        ITER_2(3, 4) ref.set(I1((UInt)j), ref.get(I1((UInt)j)) + d2.get(I2(i, j)));
//        d2.accumulate(I1((UInt)0), d1, std::plus<Real>());
//        Test("DenseTensor accumulate 2", d1, ref);
//      }
//    }
//
//    {
//      D3 d3(3, 4, 5); ITER_3(3, 4, 5) d3.set(I3(i, j, k), Real(i*4*5+j*5+k+1));
//      
//      {
//        D2 d2(4, 5), ref(4, 5);
//        ITER_3(3, 4, 5) ref.set(I2(j, k), ref.get(I2(j, k)) + d3.get(I3(i, j, k)));
//        d3.accumulate(I1((UInt)0), d2, std::plus<Real>());
//        Test("DenseTensor accumulate 3", d2, ref);
//      }
//   
//      {
//        D2 d2(3, 5), ref(3, 5);
//        ITER_3(3, 4, 5) ref.set(I2(i, k), ref.get(I2(i, k)) + d3.get(I3(i, j, k)));
//        d3.accumulate(I1((UInt)1), d2, std::plus<Real>());
//        Test("DenseTensor accumulate 4", d2, ref);
//      }
//
//      {
//        D2 d2(3, 4), ref(3, 4);
//        ITER_3(3, 4, 5) ref.set(I2(i, j), ref.get(I2(i, j)) + d3.get(I3(i, j, k)));
//        d3.accumulate(I1((UInt)2), d2, std::plus<Real>());
//        Test("DenseTensor accumulate 5", d2, ref);
//      }
//
//      {
//        D1 d1(3), ref(3);
//        ITER_3(3, 4, 5) ref.set(I1((UInt)i), ref.get(I1((UInt)i)) + d3.get(I3(i, j, k)));
//        d3.accumulate(I2(1, 2), d1, std::plus<Real>());
//        Test("DenseTensor accumulate 6", d1, ref);
//      }
//
//      {
//        D1 d1(4), ref(4);
//        ITER_3(3, 4, 5) ref.set(I1((UInt)j), ref.get(I1((UInt)j)) + d3.get(I3(i, j, k)));
//        d3.accumulate(I2(0, 2), d1, std::plus<Real>());
//        Test("DenseTensor accumulate 7", d1, ref);
//      }
//      
//      {
//        D1 d1(5), ref(5);
//        ITER_3(3, 4, 5) ref.set(I1((UInt)k), ref.get(I1((UInt)k)) + d3.get(I3(i, j, k)));
//        d3.accumulate(I2(0, 1), d1, std::plus<Real>());
//        Test("DenseTensor accumulate 8", d1, ref);
//      }
//    }
//
//    { // Max
//      D2 d2(3, 4); ITER_2(3, 4) d2.set(I2(i, j), Real(i*4+j+1));
//   
//      {   
//        D1 d1(3), ref(3); 
//        ref.set(I1((UInt)0), 4);
//        ref.set(I1((UInt)1), 8);
//        ref.set(I1((UInt)2), 12);
//        d2.accumulate(I1((UInt)1), d1, nta::Max<Real>());
//        Test("DenseTensor max 1", d1, ref);
//      }
//    
//      {    
//        D1 d1(4), ref(4); 
//        ref.set(I1((UInt)0), 9);
//        ref.set(I1((UInt)1), 10);
//        ref.set(I1((UInt)2), 11);
//        ref.set(I1((UInt)3), 12);
//        d2.accumulate(I1((UInt)0), d1, nta::Max<Real>());
//        Test("DenseTensor max 2", d1, ref);
//      }
//    }
//
//    { // multiplication
//      D2 d2(3, 4); ITER_2(3, 4) d2.set(i, j, (Real)(i*4+j+1));
//      
//      D1 d1(3), ref(3);
//      ref.setAll(1);
//      ITER_2(3, 4) ref.set(i, d2(i, j) * ref(i));
//      d2.accumulate(I1((UInt)1), d1, nta::Multiplies<Real>(), 1);
//      Test("DenseTensor accumulate 9", d1, ref);
//    }
//  }  
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestOuterProduct()
//  {
//    D1 v1(4), v2(3);
//    ITER_1(4) v1.set(i, (Real)(i+1));
//    ITER_1(3) v2.set(i, (Real)(i+1));
//
//    D2 m(4, 3), ref(4, 3);
//    ITER_2(4, 3) ref.set(i, j, v1(i) * v2(j));
//    v1.outer_product(v2, m, nta::Multiplies<Real>());
//    Test("DenseTensor outer_product 1", m, ref);
//
//    D3 d3(4, 3, 4), ref3(4, 3, 4);
//    ITER_3(4, 3, 4) ref3.set(i, j, k, m(i, j) * v1(k));
//    m.outer_product(v1, d3, nta::Multiplies<Real>());
//    Test("DenseTensor outer_product 2", d3, ref3);
//
//    D4 d4(4, 3, 4, 3), ref4(4, 3, 4, 3);
//    ITER_4(4, 3, 4, 3) ref4.set(i, j, k, l, m(i, j) + m(k, l));
//    m.outer_product(m, d4, std::plus<Real>());
//    Test("DenseTensor outer_product 3", d4, ref4);
//  }
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestContract()
//  {
//    D3 d3(4, 3, 3);        
//    ITER_3(4, 3, 3) d3.set(i, j, k, (Real)(i*9+j*3+k+1));
//
//    {
//      D1 d1(4), ref(4);
//      ITER_2(4, 3) ref.set(i, (Real)(ref(i) + d3(i, j, j)));
//      d3.contract(1, 2, d1, std::plus<Real>());
//      Test("DenseTensor contract 1", d1, ref);
//    }
//
//    {
//      D1 d1(4), ref(4);
//      ref.setAll(1);
//      ITER_2(4, 3) ref.set(i, (Real)(ref(i) * d3(i, j, j)));
//      d3.contract(1, 2, d1, nta::Multiplies<Real>(), 1);
//      Test("DenseTensor contract 1", d1, ref);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void DenseTensorUnitTest::unitTestInnerProduct()
//  {
//    D2 d2A(3, 4), d2B(4, 3), d2C(3, 3), d2ref(3, 3);     
//    
//    ITER_2(3, 4) 
//      d2A(i, j) = d2B(j, i) = Real(i*4+j+1);
//
//    ITER_3(3, 4, 3)
//      d2ref(i, k) += d2A(i, j) * d2B(j, k);
//                  
//    d2A.inner_product(1, 0, d2B, d2C, nta::Multiplies<Real>(), std::plus<Real>(), 0);
//    Test("DenseTensor inner product 1", d2C, d2ref);
//
//    D4 o(3, 4, 4, 3); 
//    d2A.outer_product(d2B, o, nta::Multiplies<Real>());
//
//    D2 d2D(3, 3);
//    o.contract(1, 2, d2D, std::plus<Real>());
//    Test("DenseTensor inner product 2", d2C, d2D);
//
//    D3 d3A(3, 4, 5), d3B(3, 3, 5);
//    ITER_3(3, 4, 5) d3A.set(i, j, k, (Real)(I3(i, j, k).ordinal(I3(3, 4, 5)) + 1));
//    d2A.inner_product(1, 1, d3A, d3B, nta::Multiplies<Real>(), std::plus<Real>());
//
//    D5 o2(3, 4, 3, 4, 5);
//    d2A.outer_product(d3A, o2, nta::Multiplies<Real>());
//    
//    D3 d3D(3, 3, 5);
//    o2.contract(1, 3, d3D, std::plus<Real>());
//    Test("DenseTensor inner product 3", d3B, d3D);
//  }
//
  //--------------------------------------------------------------------------------
  void DenseTensorUnitTest::RunTests()
  {

    //unitTestConstructor();
    //unitTestGetSet();
    //unitTestIsSymmetric();
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
  } 

  //--------------------------------------------------------------------------------
  
} // namespace nta


