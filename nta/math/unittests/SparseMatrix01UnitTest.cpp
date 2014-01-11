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
 * Implementation of unit testing for class SparseMatrix01
 */         
              
//#include <nta/common/version.hpp>

#include <nta/math/array_algo.hpp>
#include "SparseMatrix01UnitTest.hpp"

#include <boost/timer.hpp>
    
using namespace std;     

namespace nta {
       
#define TEST_LOOP(M)                                  \
  for (nrows = 0, ncols = M, zr = 15;                 \
       nrows < M;                                     \
       nrows += M/10, ncols -= M/10, zr = ncols/10)   \

#define M 256
//
//  //--------------------------------------------------------------------------------
//  void GenerateRand01Vector(Random *r, const UInt nnzr, vector<Real>& v)
//  {
//    UInt ncols = (UInt)v.size();
//    do {
//      fill(v.begin(), v.end(), Real(0));
//      UInt pos = r->getUInt32(ncols / nnzr);
//      v[pos] = 1;
//      for (UInt i = 1; i < nnzr; ++i)
//        v[pos += (r->getUInt32(ncols / nnzr)) + 1] = 1;
//    } while (accumulate(v.begin(), v.end(), (Real)0) != nnzr);
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_construction()
//  {
//    // Tests:
//    // all constructors, destructors, nNonZeros, nCols, nRows
//    // toDense, compact, isZero, nNonZerosRow
//    UInt ncols, nrows, zr;    
//
//    { // Rectangular shape, no zeros
//      nrows = 3; ncols = 4;
//      Dense01<UInt, Real> dense(nrows, ncols, 0);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      Compare(dense, sm, "ctor 1");
//      Test("isZero 1", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 1 - compact");
//      Test("isZero 1 - compact", sm.isZero(), false);
//    }    
//
//    { // Rectangular shape, zeros
//      nrows = 3; ncols = 4;
//      Dense01<UInt, Real> dense(nrows, ncols, 2);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      Compare(dense, sm, "ctor 2");
//      Test("isZero 2", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 2 - compact");
//      Test("isZero 2 - compact", sm.isZero(), false);
//    }   
//      
//    { // Rectangular the other way, no zeros     
//      nrows = 4; ncols = 3;
//      Dense01<UInt, Real> dense(nrows, ncols, 0);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      Compare(dense, sm, "ctor 3");
//      Test("isZero 3", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 3 - compact");
//      Test("isZero 3 - compact", sm.isZero(), false);
//    }
//
//    { // Rectangular the other way, zeros
//      nrows = 6; ncols = 5;
//      Dense01<UInt, Real> dense(nrows, ncols, 2);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      Compare(dense, sm, "ctor 4");
//      Test("isZero 4", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 4 - compact");
//      Test("isZero 4 - compact", sm.isZero(), false);
//    }
//
//    { // Empty rows in the middle and zeros
//      nrows = 3; ncols = 4;
//      Dense01<UInt, Real> dense(nrows, ncols, 2, false, true);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      Compare(dense, sm, "ctor 5");
//      Test("isZero 5", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 5 - compact");
//      Test("isZero 5 - compact", sm.isZero(), false);
//    }
//
//    { // Empty rows in the middle and zeros
//      nrows = 7; ncols = 5;
//      Dense01<UInt, Real> dense(nrows, ncols, 2, false, true);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      Compare(dense, sm, "ctor 6");
//      Test("isZero 6", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 6 - compact");
//      Test("isZero 6 - compact", sm.isZero(), false);
//    }  
//
//    { // Small values, zeros and empty rows
//      nrows = 7; ncols = 5;
//      Dense01<UInt, Real> dense(nrows, ncols, 2, true, true);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      Compare(dense, sm, "ctor 7");
//      Test("isZero 7", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 7 - compact");
//      Test("isZero 7 - compact", sm.isZero(), false);
//    }    
//
//    { // Small values, zeros and empty rows, other constructor
//      nrows = 10; ncols = 10;
//      Dense01<UInt, Real> dense(nrows, ncols, 2, true, true);
//      SparseMatrix01<UInt, Real> sm(ncols);
//      for (UInt i = 0; i < nrows; ++i)
//        sm.addRow(dense.begin(i));
//      Compare(dense, sm, "ctor 8");
//      Test("isZero 8", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 8 - compact");
//      Test("isZero 8 - compact", sm.isZero(), false);
//    }
//
//    { // Small values, zeros and empty rows, other constructor
//      nrows = 10; ncols = 10;
//      Dense01<UInt, Real> dense(nrows, ncols, 2, true, true);
//      SparseMatrix01<UInt, Real> sm(ncols, 0);
//      for (UInt i = 0; i < nrows; ++i)
//        sm.addRow(dense.begin(i));
//      Compare(dense, sm, "ctor 9");
//      Test("isZero 9", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 9 - compact");
//      Test("isZero 9 - compact", sm.isZero(), false);
//    }
//
//    { // Small values, zeros and empty rows, other constructor
//      nrows = 10; ncols = 10;   
//      Dense01<UInt, Real> dense(nrows, ncols, 2, true, true);
//      SparseMatrix01<UInt, Real> sm(ncols, 2);
//      for (UInt i = 0; i < nrows; ++i)
//        sm.addRow(dense.begin(i));
//      Compare(dense, sm, "ctor 10");
//      Test("isZero 10", sm.isZero(), false);   
//      sm.compact();
//      Compare(dense, sm, "ctor 10 - compact");
//      Test("isZero 10 - compact", sm.isZero(), false);
//    }
//    
//    { // Empty
//      Dense01<UInt, Real> dense(10, 10, 10);
//      SparseMatrix01<UInt, Real> sm(10, 10, dense.begin(), 0);
//      Compare(dense, sm, "ctor from empty dense - non compact");
//      Test("isZero 11", sm.isZero(), true);     
//      sm.compact();
//      Compare(dense, sm, "ctor from empty dense - compact");
//      Test("isZero 11 - compact", sm.isZero(), true); 
//    }
//
//    { // Empty, other constructor
//      Dense01<UInt, Real> dense(10, 10, 10);
//      SparseMatrix01<UInt, Real> sm(10);
//      for (UInt i = 0; i < nrows; ++i)
//        sm.addRow(dense.begin(i));
//      Compare(dense, sm, "ctor from empty dense - non compact");
//      Test("isZero 12", sm.isZero(), true); 
//      sm.compact();
//      Compare(dense, sm, "ctor from empty dense - compact");
//      Test("isZero 12 - compact", sm.isZero(), true); 
//    }
//
//    { // Full
//      Dense01<UInt, Real> dense(10, 10, 0);
//      SparseMatrix01<UInt, Real> sm(10, 10, dense.begin(), 0);
//      Compare(dense, sm, "ctor from full dense - non compact");
//      Test("isZero 13", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor from full dense - compact");
//      Test("isZero 13 - compact", sm.isZero(), false);
//    }
//
//    { // Various rectangular sizes
//      TEST_LOOP(M) {
//            
//        Dense01<UInt, Real> dense(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm(ncols, nrows);
//      
//        for (UInt i = 0; i < nrows; ++i)
//          sm.addRow(dense.begin(i));
//      
//        {
//          stringstream str;
//          str << "ctor " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense, sm, str.str().c_str());
//        }
//
//        sm.compact();
//
//        {
//          stringstream str;
//          str << "ctor " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          Compare(dense, sm, str.str().c_str());
//        }
//      }
//    }
//
//    try {
//      SparseMatrix01<int, Real> sme1(0, 0);
//      Test("SparseMatrix01::SparseMatrix01(Int, Int) exception 1", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix01::SparseMatrix01(Int, Int) exception 1", true, true);
//    }
//
//    try {
//      SparseMatrix01<int, Real> sme1(-1, 0);
//      Test("SparseMatrix01::SparseMatrix01(Int, Int) exception 2", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix01::SparseMatrix01(Int, Int) exception 2", true, true);
//    }
//
//    try {
//      SparseMatrix01<int, Real> sme1(1, -1);
//      Test("SparseMatrix01::SparseMatrix01(Int, Int) exception 3", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix01::SparseMatrix01(Int, Int) exception 3", true, true);
//    }
//
//    std::vector<Real> mat(16, 0);
//    
//    try {
//      SparseMatrix01<int, Real> sme1(-1, 1, mat.begin(), 0);
//      Test("SparseMatrix01::SparseMatrix01(Int, Int, Iter) exception 1", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix01::SparseMatrix01(Int, Iter) exception 1", true, true);
//    }    
//
//    try {
//      SparseMatrix01<int, Real> sme1(1, -1, mat.begin(), 0);
//      Test("SparseMatrix01::SparseMatrix01(Int, Int, Iter) exception 2", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix01::SparseMatrix01(Int, Iter) exception 2", true, true);
//    }
//     
//    try {
//      SparseMatrix01<int, Real> sme1(1, 0, mat.begin(), 0);
//      Test("SparseMatrix01::SparseMatrix01(Int, Int, Iter) exception 3", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix01::SparseMatrix01(Int, Iter) exception 3", true, true);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_csr()
//  {
//    UInt nrows, ncols, zr;
//                  
//    {
//      TEST_LOOP(M) {
//                  
//        Dense01<UInt, Real> dense3(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm3(nrows, ncols, dense3.begin(), 0);
//        
//        stringstream buf;
//        sm3.toCSR(buf);
//        sm3.fromCSR(buf);
//    
//        {  
//          stringstream str;
//          str << "toCSR/fromCSR A " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense3, sm3, str.str().c_str());
//        }   
//
//        SparseMatrix01<UInt, Real> sm4(ncols, nrows);
//        stringstream buf1;
//        sm3.toCSR(buf1);
//        sm4.fromCSR(buf1);
//  
//        {
//          stringstream str;
//          str << "toCSR/fromCSR B " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense3, sm4, str.str().c_str());
//        }
//
//        sm4.decompact();
//        stringstream buf2;
//        sm3.toCSR(buf2);
//        sm4.fromCSR(buf2);
//
//        {  
//          stringstream str;
//          str << "toCSR/fromCSR C " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense3, sm4, str.str().c_str());
//        }
//
//        stringstream buf3;
//        sm4.toCSR(buf3);
//        sm4.fromCSR(buf3);
//
//        {
//          stringstream str;
//          str << "toCSR/fromCSR D " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense3, sm4, str.str().c_str());
//        }
//      }
//    }
//
//    { // Is resizing happening correctly?
//      Dense01<UInt, Real> dense(3, 4, 2);
//      SparseMatrix01<UInt, Real> sm(3, 4, dense.begin(), 0);
//      
//      { // Smaller size
//        stringstream buf1, buf2;
//        buf1 << "csr01 0 3 3 9 0 3 0 1 2 3 0 1 2 3 0 1 2";
//        sm.fromCSR(buf1);
//
//        buf2 << "csr01 3 3 9 0 3 0 1 2 3 0 1 2 3 0 1 2";
//        dense.fromCSR(buf2);
//        Compare(dense, sm, "fromCSR/redim/1");
//      }
//
//      { // Larger size
//        stringstream buf1, buf2;
//        buf1 << "csr01 0 4 5 20 0 "
//          "5 0 1 2 3 4 "
//          "5 0 1 2 3 4 "
//          "5 0 1 2 3 4 "
//          "5 0 1 2 3 4";
//        sm.fromCSR(buf1);
//        buf2 << "csr01 4 5 20 0 "
//          "5 0 1 2 3 4 "
//          "5 0 1 2 3 4 "
//          "5 0 1 2 3 4 "
//          "5 0 1 2 3 4";
//        dense.fromCSR(buf2);
//        Compare(dense, sm, "fromCSR/redim/2");
//      }
//
//      { // Empty rows
//        stringstream buf1, buf2;
//        buf1 << "csr01 0 4 5 15 0 "
//          "5 0 1 2 3 4 "
//          "0 "
//          "5 0 1 2 3 4 "
//          "5 0 1 2 3 4";
//        sm.fromCSR(buf1);
//        buf2 << "csr01 4 5 15 0 "
//          "5 0 1 2 3 4 "
//          "0 "
//          "5 0 1 2 3 4 "
//          "5 0 1 2 3 4";
//        dense.fromCSR(buf2);
//        Compare(dense, sm, "fromCSR/redim/3");
//      }
//    }
//
//    // Exceptions
//    SparseMatrix01<int, Real> sme1(1, 1);
//
//    { 
//      stringstream s1;
//      s1 << "ijv";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix01::fromCSR() exception 1", true, false);
//      } catch (runtime_error&) {
//        Test("SparseMatrix01::fromCSR() exception 1", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr01 0 -1";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix01::fromCSR() exception 2", true, false);
//      } catch (runtime_error&) {
//        Test("SparseMatrix01::fromCSR() exception 2", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr01 0 1 -1";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix01::fromCSR() exception 3", true, false);
//      } catch (runtime_error&) {
//        Test("SparseMatrix01::fromCSR() exception 3", true, true);
//      }
//    }
//   
//    {
//      stringstream s1;
//      s1 << "csr01 0 1 0";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix01::fromCSR() exception 4", true, false);
//      } catch (runtime_error&) {
//        Test("SparseMatrix01::fromCSR() exception 4", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr01 0 4 3 -1";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix01::fromCSR() exception 5", true, false);
//      } catch (runtime_error&) {
//        Test("SparseMatrix01::fromCSR() exception 5", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr01 0 4 3 15";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix01::fromCSR() exception 6", true, false);
//      } catch (runtime_error&) {
//        Test("SparseMatrix01::fromCSR() exception 6", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr01 0 2 3 1 5";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix01::fromCSR() exception 7", true, false);
//      } catch (runtime_error&) {
//        Test("SparseMatrix01::fromCSR() exception 7", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr01 0 2 3 1 0 1 -1";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix01::fromCSR() exception 8", true, false); 
//      } catch (runtime_error&) {
//        Test("SparseMatrix01::fromCSR() exception 8", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr01 0 2 3 1 0 1 4";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix01::fromCSR() exception 9", true, false);
//      } catch (runtime_error&) {
//        Test("SparseMatrix01::fromCSR() exception 9", true, true);
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_fromDense()
//  {
//    UInt ncols, nrows, zr;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//  
//    Dense01<UInt, Real> dense(nrows, ncols, zr);
//    SparseMatrix01<UInt, Real> sm4(ncols, nrows);
//    sm4.fromDense(nrows, ncols, dense.begin());
//    Compare(dense, sm4, "fromDense 1");
//
//    SparseMatrix01<UInt, Real> sm5(nrows, ncols, dense.begin(), 0);
//    Dense01<UInt, Real> dense2(nrows+1, ncols+1, zr+1);
//    sm5.fromDense(nrows+1, ncols+1, dense2.begin());
//    Compare(dense2, sm5, "fromDense 2");
//
//    sm5.decompact();
//    sm5.fromDense(nrows, ncols, dense.begin());
//    Compare(dense, sm5, "fromDense 3");
//
//    sm5.compact();
//    sm5.fromDense(nrows+1, ncols+1, dense2.begin());
//    Compare(dense2, sm5, "fromDense 4");
//
//    std::vector<Real> mat((nrows+1)*(ncols+1), 0);
//  
//    sm5.toDense(mat.begin());
//    sm5.fromDense(nrows+1, ncols+1, mat.begin());
//    Compare(dense2, sm5, "toDense 1");
//  
//    {
//      TEST_LOOP(M) {
//      
//        Dense01<UInt, Real> dense3(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm3(nrows, ncols, dense3.begin(), 0);
//        std::vector<Real> mat3(nrows*ncols, 0);
//
//        sm3.toDense(mat3.begin());
//        sm3.fromDense(nrows, ncols, mat3.begin());
//
//        {
//          stringstream str;
//          str << "toDense/fromDense A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense3, sm3, str.str().c_str());
//        }
//
//        sm3.compact();
//
//        {
//          stringstream str;
//          str << "toDense/fromDense B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          Compare(dense3, sm3, str.str().c_str());
//        }
//      }
//    }
//
//    { // What happens if dense matrix is full?
//      nrows = ncols = 10; zr = 0;
//      Dense01<UInt, Real> dense(nrows, ncols, zr);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      std::vector<Real> mat3(nrows*ncols, 0);
//      
//      sm.toDense(mat3.begin());
//      sm.fromDense(nrows, ncols, mat3.begin());
//    
//      Compare(dense, sm, "toDense/fromDense from dense");
//    }  
//
//    { // What happens if dense matrix is empty?
//      nrows = ncols = 10; zr = 10;
//      Dense01<UInt, Real> dense(nrows, ncols, zr);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      std::vector<Real> mat3(nrows*ncols, 0);
//      
//      sm.toDense(mat3.begin());
//      sm.fromDense(nrows, ncols, mat3.begin());
//    
//      Compare(dense, sm, "toDense/fromDense from dense");
//    }
//
//    { // What happens if there are empty rows?
//      nrows = ncols = 10; zr = 2;
//      Dense01<UInt, Real> dense(nrows, ncols, zr);
//      for (UInt i = 0; i < ncols; ++i) 
//        dense.at(2,i) = dense.at(4,i) = dense.at(9,i) = 0;
//        
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      std::vector<Real> mat3(nrows*ncols, 0);
//    
//      sm.toDense(mat3.begin());
//      sm.fromDense(nrows, ncols, mat3.begin());
//    
//      Compare(dense, sm, "toDense/fromDense from dense");
//    }
//
//    { // Is resizing happening correctly?
//      Dense01<UInt, Real> dense(3, 4, 2);
//      SparseMatrix01<UInt, Real> sm(3, 4, dense.begin(), 0);
//
//      Dense01<UInt, Real> dense2(5, 5, 4);
//      sm.fromDense(5, 5, dense2.begin());
//      Compare(dense2, sm, "fromDense/redim/1");
//
//      Dense01<UInt, Real> dense3(2, 2, 2);
//      sm.fromDense(2, 2, dense3.begin());
//      Compare(dense3, sm, "fromDense/redim/2");
//
//      Dense01<UInt, Real> dense4(10, 10, 8);
//      sm.fromDense(10, 10, dense4.begin());
//      Compare(dense4, sm, "fromDense/redim/3");
//    }
//    
//    // Exceptions
//    SparseMatrix01<int, Real> sme1(1, 1);
//    
//    try {
//      sme1.fromDense(-1, 0, dense.begin());
//      Test("SparseMatrix01::fromDense() exception 1", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix01::fromDense() exception 1", true, true);
//    }
//
//    try {
//      sme1.fromDense(1, 0, dense.begin());
//      Test("SparseMatrix01::fromDense() exception 2", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix01::fromDense() exception 2", true, true);
//    }
//
//    try {
//      sme1.fromDense(1, -1, dense.begin());
//      Test("SparseMatrix01::fromDense() exception 3", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix01::fromDense() exception 3", true, true);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_compact()
//  {
//    UInt ncols, nrows, zr;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    Dense01<UInt, Real> dense(nrows, ncols, zr);
//    SparseMatrix01<UInt, Real> sm4(nrows, ncols, dense.begin(), 0);
//  
//    sm4.decompact();
//    Compare(dense, sm4, "decompact 1");
//  
//    sm4.compact();
//    Compare(dense, sm4, "compact 1");
//
//    sm4.decompact();
//    Compare(dense, sm4, "decompact 2");
//  
//    sm4.compact();
//    Compare(dense, sm4, "compact 2");
//
//    sm4.decompact();
//    sm4.decompact();
//    Compare(dense, sm4, "decompact twice");
//  
//    sm4.compact();
//    sm4.compact();
//    Compare(dense, sm4, "compact twice");
//
//    SparseMatrix01<UInt, Real> sm5(nrows, ncols, dense.begin(), 0);
//
//    {
//      TEST_LOOP(M) {
//
//        Dense01<UInt, Real> dense3(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm3(nrows, ncols, dense3.begin(), 0);
//
//        sm3.decompact();
//      
//        {
//          stringstream str;
//          str << "compact/decompact A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense3, sm3, str.str().c_str());
//        }
//
//        sm3.compact();
//
//        {
//          stringstream str;
//          str << "compact/decompact B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          Compare(dense3, sm3, str.str().c_str());
//        }
//      }
//    }
//
//    {
//      nrows = ncols = 10; zr = 0;
//      Dense01<UInt, Real> dense(nrows, ncols, zr);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//      std::vector<Real> mat3(nrows*ncols, 0);
//    
//      sm.decompact();
//      Compare(dense, sm, "decompact on dense");
//
//      sm.compact();
//      Compare(dense, sm, "compact on dense");
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_getRowSparse()
//  {
//    UInt ncols, nrows, zr, i, k;
//  
//    {
//      TEST_LOOP(M) {
//        
//        Dense01<UInt, Real> dense(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//
//        for (i = 0; i < nrows; ++i) {
//          
//          stringstream str;
//          str << "getRowSparse A " << nrows << "X" << ncols 
//              << "/" << zr << " " << i;
//  
//          vector<UInt> ind; ;
//          sm.getRowSparse(i, back_inserter(ind));
//          
//          std::vector<Real> d(ncols, 0);
//          for (k = 0; k < ind.size(); ++k)
//            d[ind[k]] = 1.0;
//          
//          CompareVectors(ncols, d.begin(), dense.begin(i), str.str().c_str());
//        }
//      }  
//    }  
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_addRow()
//  {
//    // addRow, compact
//    UInt nrows, ncols, zr;   
//  
//    {
//      TEST_LOOP(M) {
//
//        Dense01<UInt, Real> dense(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm(ncols, 1);
//
//        for (UInt i = 0; i < nrows; ++i) {
//          sm.addRow(dense.begin(i));
//          sm.compact();
//        }
//      
//        sm.decompact();
//      
//        {
//          stringstream str;
//          str << "addRow A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense, sm, str.str().c_str());
//        }
//      
//        sm.compact();
//
//        {
//          stringstream str;
//          str << "addRow B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          Compare(dense, sm, str.str().c_str());
//        }
//      }
//    }
//    
//    // These tests compiled conditionally, because they are 
//    // based on asserts rather than checks
//
//#ifdef NTA_ASSERTIONS_ON
//
//    { // "Dirty" rows tests
//      UInt ncols = 4;
//      SparseMatrix01<UInt, Real> sm(ncols, 1);
//      std::vector<UInt> dirty_col(ncols);
//
//      // Duplicate zeros (assertion)
//      for (UInt i = 0; i < ncols; ++i)
//        dirty_col[i] = 0;
//      try {
//        sm.addRow(ncols, dirty_col.begin());
//        Test("SparseMatrix dirty cols 1", true, false);
//      } catch (std::exception& e) {
//        Test("SparseMatrix dirty cols 1", true, true);
//      }
//
//      // Out of order indices (assertion)
//      dirty_col[0] = 3;
//      try {
//        sm.addRow(ncols, dirty_col.begin());
//        Test("SparseMatrix dirty cols 2", true, false);
//      } catch (std::exception& e) {
//        Test("SparseMatrix dirty cols 2", true, true);
//      }
//
//      // Indices out of range (assertion)
//      dirty_col[0] = 9;
//      try {
//        sm.addRow(ncols, dirty_col.begin());
//        Test("SparseMatrix dirty cols 3", true, false);
//      } catch (std::exception& e) {
//        Test("SparseMatrix dirty cols 3", true, true);
//      }
//    }
//#endif
//  }
//
//  //--------------------------------------------------------------------------------
//  /**
//   * The vector of all zeros is indistinguishable from the vector where the maxima
//   * are the first elements of each section!
//   */
//  void SparseMatrix01UnitTest::unit_test_addUniqueFilteredRow()
//  {
//    UInt nreps = 1000;
//    std::vector<UInt> boundaries(2);
//    boundaries[0] = 4; boundaries[1] = 8;
//    UInt nnzr = (UInt)boundaries.size(), ncols = boundaries[nnzr-1];
//    SparseMatrix01<UInt, Real> sm01(ncols,1,nnzr);
//    std::vector<Real> x(ncols), v(ncols);
//    UInt winner, winner_ref;
//
//    typedef map<vector<Real>, pair<UInt, UInt> > Check;
//    Check control; Check::iterator it;    
//    
//    for (UInt i = 0; i < nreps; ++i) {
//      
//      for (UInt j = 0; j < ncols; ++j)   
//        x[j] = rng_->getReal64();
//
//      winnerTakesAll2(boundaries, x.begin(), v.begin());
//
//      it = control.find(v);  
//      if (it == control.end()) { 
//        winner_ref = (UInt)control.size();
//        control[v] = make_pair(winner_ref, 1);   
//      } else {   
//        winner_ref = control[v].first;
//        control[v].second += 1;      
//      }    
//
//      winner = sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//      Test("SparseMatrix01 addUniqueFilteredRow 1", winner, winner_ref);
//    }
//      
//    Test("SparseMatrix01 addUniqueFilteredRow 2", sm01.nRows(), control.size());
//
//    SparseMatrix01<UInt, Real>::RowCounts rc = sm01.getRowCounts();
//      
//    for (UInt i = 0; i < rc.size(); ++i) {
//      sm01.getRow(rc[i].first, x.begin());
//      Test("SparseMatrix01 addUniqueFilteredRow 3", rc[i].second, control[x].second);
//    }
//
//    /*
//      x[0]=.5;x[1]=.7;x[2]=.3;x[3]=.1;x[4]=.7;x[5]=.1;x[6]=.1;x[7]=0;
//      sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//      cout << sm01 << endl;    
//    
//      x[0]=.9;x[1]=.7;x[2]=.3;x[3]=.1;x[4]=.9;x[5]=.1;x[6]=.1;x[7]=0;
//      sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//      cout << sm01 << endl;
//
//      x[0]=.0;x[1]=.7;x[2]=.3;x[3]=.9;x[4]=.9;x[5]=.1;x[6]=.1;x[7]=.95;
//      sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//      cout << sm01 << endl;
//
//      x[0]=.0;x[1]=.7;x[2]=.3;x[3]=.9;x[4]=.9;x[5]=.1;x[6]=.1;x[7]=.95;
//      sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//      cout << sm01 << endl;
//    */
//  }
//   
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_addMinHamming()
//  {
//    UInt nreps = 1000;
//    std::vector<UInt> boundaries(8);
//    boundaries[0] = 4;
//    for (UInt i = 1; i < boundaries.size(); ++i)
//      boundaries[i] = boundaries[i-1] + 1 + rng_->getUInt32(boundaries[0]-1);
//    UInt nnzr = (UInt)boundaries.size(), ncols = boundaries[nnzr-1];
//    SparseMatrix01<UInt, UInt> sm01(ncols,1,nnzr);
//    std::vector<UInt> x(ncols), v(ncols);
//    UInt winner, winner_ref, hamming, min_hamming, max_distance;
//
//    typedef map<vector<UInt>, pair<UInt, UInt> > Check;
//    Check control; Check::iterator it, arg_it;    
//    
//    for (UInt i = 0; i < nreps; ++i) {
//      
//      max_distance = rng_->getUInt32(nnzr);
//
//      for (UInt j = 0; j < ncols; ++j)   
//        x[j] = rng_->getUInt32(100);
//
//      winnerTakesAll2(boundaries, x.begin(), v.begin());
//
//      min_hamming = std::numeric_limits<UInt>::max();
//      arg_it = control.begin();
//      
//      for (it = control.begin(); it != control.end(); ++it) {
//	hamming = 0;
//	for (UInt k = 0; k < ncols; ++k) {
//	  if ((it->first)[k] != v[k]) {
//	    ++hamming;
//	  }
//	}
//	if (hamming < min_hamming) {
//	  min_hamming = hamming;
//	  arg_it = it;
//	}
//      }   
//      
//      if (min_hamming <= max_distance) {
//	++ (arg_it->second.second);
//	winner_ref = arg_it->second.first;
//      } else {
//	winner_ref = (UInt)control.size();
//	control[v] = std::make_pair(winner_ref, 1);
//      }
//
//      winner = sm01.addMinHamming(boundaries.begin(), x.begin(), max_distance);
//      Test("SparseMatrix01 addMinHamming 1", winner, winner_ref);
//      if (winner != winner_ref) {
//	cout << winner << " - " << winner_ref << endl << endl;
//	for (UInt k = 0; k < ncols; ++k)
//	  cout << v[k] << " ";
//	cout << endl << endl;
//	cout << sm01 << endl; 
//      }
//    }
//      
//    Test("SparseMatrix01 addMinHamming 2", sm01.nRows(), control.size());
//
//    SparseMatrix01<UInt, Real>::RowCounts rc = sm01.getRowCounts();
//      
//    for (UInt i = 0; i < rc.size(); ++i) {
//      sm01.getRow(rc[i].first, x.begin());
//      Test("SparseMatrix01 addMinHamming 3", rc[i].second, control[x].second);
//    }
//
//    /*
//    x[0]=.5;x[1]=.7;x[2]=.3;x[3]=.1;x[4]=.7;x[5]=.1;x[6]=.1;x[7]=0;
//    sm01.addMinHamming(boundaries.begin(), x.begin(), 2);
//    cout << sm01 << endl;    
//
//    sm01.addMinHamming(boundaries.begin(), x.begin(), 2);
//    cout << sm01 << endl;    
//    
//    x[0]=.9;x[1]=.7;x[2]=.3;x[3]=.1;x[4]=.9;x[5]=.1;x[6]=.1;x[7]=0;
//    sm01.addMinHamming(boundaries.begin(), x.begin(), 2);
//    cout << sm01 << endl;
//
//    x[0]=.0;x[1]=.7;x[2]=.3;x[3]=.9;x[4]=.9;x[5]=.1;x[6]=.1;x[7]=.95;
//    sm01.addMinHamming(boundaries.begin(), x.begin(), 2);
//    cout << sm01 << endl;
//
//    x[0]=.0;x[1]=.7;x[2]=.3;x[3]=.9;x[4]=.9;x[5]=.1;x[6]=.1;x[7]=.95;
//    sm01.addMinHamming(boundaries.begin(), x.begin(), 2);
//    cout << sm01 << endl;
//    */
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_deleteRows()
//  {     
//    { // Empty matrix
//      UInt nrows = 3, ncols = 3;
//    
//      { // Empty matrix, empty del
//	SparseMatrix01<UInt, Real> sm(ncols, nrows);
//	vector<UInt> del;
//	sm.deleteRows(del.begin(), del.end());
//	Test("SparseMatrix01::deleteRows() 1", sm.nRows(), UInt(0));
//      }
//
//      { // Empty matrix, 1 del
//	SparseMatrix01<UInt, Real> sm(ncols, nrows);
//	vector<UInt> del(1); del[0] = 0;
//	sm.deleteRows(del.begin(), del.end());
//	Test("SparseMatrix01::deleteRows() 2", sm.nRows(), UInt(0));
//      }
//
//      { // Empty matrix, many dels
//	SparseMatrix01<UInt, Real> sm(ncols, nrows);
//	vector<UInt> del(2); del[0] = 0; del[1] = 2;
//	sm.deleteRows(del.begin(), del.end());
//	Test("SparseMatrix01::deleteRows() 3", sm.nRows(), UInt(0));
//      }
//    } // End empty matrix
//
//    {
//      UInt nrows, ncols, zr;
//
//      TEST_LOOP(M) {
//
//	Dense01<UInt, Real> dense(nrows, ncols, zr);   
//
//	{ // Empty del
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	  vector<UInt> del;
//	  sm.deleteRows(del.begin(), del.end());
//	  Test("SparseMatrix01::deleteRows() 4", sm.nRows(), nrows);
//	}
//
//	{ // Rows of all zeros 1
//	  Dense01<UInt, Real> dense2(nrows, ncols, zr);
//	  ITER_1(nrows) {
//	    if (i % 2 == 0) {
//	      for (UInt j = 0; j < ncols; ++j)
//		dense2.at(i,j) = 0;
//	    }
//	  }   
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense2.begin(), 0);
//	  vector<UInt> del;
//	  if (nrows > 2) {
//	    for (UInt i = 2; i < nrows-2; i += 2)    
//	      del.push_back(i);
//	    sm.deleteRows(del.begin(), del.end());
//	    dense2.deleteRows(del.begin(), del.end());
//	    Compare(dense2, sm, "SparseMatrix01::deleteRows() 5A");
//	  }
//	}
//	
//	{ // Rows of all zeros 2
//	  Dense01<UInt, Real> dense2(nrows, ncols, zr);
//	  ITER_1(nrows) {
//	    if (i % 2 == 0) {
//	      for (UInt j = 0; j < ncols; ++j)
//		dense2.at(i,j) = 0;
//	    }
//	  }
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense2.begin(), 0);
//	  vector<UInt> del;
//	  if (nrows > 2) {
//	    for (UInt i = 1; i < nrows-2; i += 2)    
//	      del.push_back(i);
//	    sm.deleteRows(del.begin(), del.end());
//	    dense2.deleteRows(del.begin(), del.end());
//	    Compare(dense2, sm, "SparseMatrix01::deleteRows() 5B");
//	  }
//	}
//
//	{ // Many dels contiguous
//	  if (nrows > 2) {
//            SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//            Dense01<UInt, Real> dense2(nrows, ncols, zr);
//            vector<UInt> del;
//	    for (UInt i = 2; i < nrows-2; ++i)    
//	      del.push_back(i);
//	    sm.deleteRows(del.begin(), del.end());
//	    dense2.deleteRows(del.begin(), del.end());
//	    Compare(dense2, sm, "SparseMatrix01::deleteRows() 6A");
//	  }
//	}
//
//        { // Make sure we stop at the end of the dels!
//          if (nrows > 2) {
//            SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//            Dense01<UInt, Real> dense2(nrows, ncols, zr);
//            UInt* del = new UInt[nrows-1];
//	    for (UInt i = 0; i < nrows-1; ++i)    
//              del[i] = i + 1;
//	    sm.deleteRows(del, del + nrows-2);
//	    dense2.deleteRows(del, del + nrows-2);
//	    Compare(dense2, sm, "SparseMatrix01::deleteRows() 6B");
//            delete [] del;
//	  }
//        }
//
//	{ // Many dels discontiguous
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	  Dense01<UInt, Real> dense2(nrows, ncols, zr);
//	  vector<UInt> del;
//	  for (UInt i = 0; i < nrows; i += 2)
//	    del.push_back(i);
//	  sm.deleteRows(del.begin(), del.end());
//	  dense2.deleteRows(del.begin(), del.end());
//	  Compare(dense2, sm, "SparseMatrix01::deleteRows() 7");
//	}
//
//	{ // All rows
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	  vector<UInt> del; 
//	  for (UInt i = 0; i < nrows; ++i)
//	    del.push_back(i);
//	  sm.deleteRows(del.begin(), del.end());
//	  Test("SparseMatrix01::deleteRows() 8", sm.nRows(), UInt(0));
//	}
//
//	{ // More than all rows => exceptions in assert mode
//          /*
//	    SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	    vector<UInt> del; 
//	    for (UInt i = 0; i < 2*nrows; ++i)
//	    del.push_back(i);
//	    sm.deleteRows(del.begin(), del.end());
//	    Test("SparseMatrix01::deleteRows() 9", sm.nRows(), UInt(0));
//          */
//	}
//
//	{ // Several dels in a row till empty
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	  for (UInt i = 0; i < nrows; ++i) {
//	    vector<UInt> del(1); del[0] = 0;
//	    sm.deleteRows(del.begin(), del.end());
//	    Test("SparseMatrix01::deleteRows() 10", sm.nRows(), UInt(nrows-i-1));
//	  }
//      	}
//      }
//    } 
//	
//    { // Test with unique rows
//      UInt nrows = 10;
//      std::vector<UInt> boundaries(2);
//      boundaries[0] = 4; boundaries[1] = 8;
//      UInt nnzr = (UInt)boundaries.size(), ncols = boundaries[nnzr-1];
//      SparseMatrix01<UInt, Real> sm01(ncols,1,nnzr);
//      std::vector<Real> x(ncols);
//
//      for (UInt i = 0; i < nrows; ++i) {
//
//	for (UInt j = 0; j < ncols; ++j)   
//	  x[j] = rng_->getReal64();
//
//	sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//      }
//
//      SparseMatrix01<UInt, Real>::RowCounts rc = sm01.getRowCounts();
//      vector<UInt> del; del.push_back(1); del.push_back(3); 
//      UInt nrows_new = sm01.nRows() - del.size();	
//      sm01.deleteRows(del.begin(), del.end());
//      Test("SparseMatrix01::deleteRows 11", sm01.nRows(), nrows_new);
//      rc = sm01.getRowCounts();
//      UInt s = (UInt)rc.size();
//      Test("SparseMatrix01::deleteRows 12", s, nrows_new);
//			
//      // Remove last row
//      del.clear();
//      del.push_back(sm01.nRows()-1);
//      sm01.deleteRows(del.begin(), del.end());
//      nrows_new -= 1;
//      Test("SparseMatrix01::deleteRows 13", sm01.nRows(), nrows_new);
//      rc = sm01.getRowCounts();
//      s = (UInt)rc.size();
//      Test("SparseMatrix01::deleteRows 14", s, nrows_new);	
//    }
//
//    { // Delete with threshold
//      UInt nrows = 20;
//      std::vector<UInt> boundaries(2);
//      boundaries[0] = 4; boundaries[1] = 8;
//      UInt nnzr = (UInt)boundaries.size(), ncols = boundaries[nnzr-1];
//      SparseMatrix01<UInt, Real> sm01(ncols,1,nnzr);
//      std::vector<Real> x(ncols);
//
//      for (UInt i = 0; i < nrows; ++i) {
//
//	for (UInt j = 0; j < ncols; ++j)   
//	  x[j] = rng_->getReal64();
//
//	sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//      }
//
//      nrows = sm01.nRows();
//      UInt keep = 0, threshold = 2;
//      vector<pair<UInt, UInt> > rc = sm01.getRowCounts();
//      for (UInt i = 0; i < rc.size(); ++i)
//        if (rc[i].second >= threshold)
//          ++keep;
//      vector<pair<UInt, UInt> > del_rows;
//      sm01.deleteRows(threshold, back_inserter(del_rows));
//      Test("SparseMatrix01::deleteRows(threshold) 15", del_rows.size(), nrows - keep);
//      Test("SparseMatrix01::deleteRows(threshold) 16", sm01.nRows(), keep);
//    }
//
//    { // Delete with threshold - make sure counts are adjusted
//      std::vector<UInt> boundaries(2);
//      boundaries[0] = 2; boundaries[1] = 4;
//      UInt nnzr = (UInt)boundaries.size(), ncols = boundaries[nnzr-1];
//      SparseMatrix01<UInt, Real> sm01(ncols,1,nnzr);
//      std::vector<Real> x(ncols);
//
//      x[0] = 1; x[1] = 0; x[2] = 0; x[3] = 1;
//      sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//
//      x[0] = 0; x[1] = 1; x[2] = 0; x[3] = 1;
//      sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//
//      x[0] = 0; x[1] = 1; x[2] = 0; x[3] = 1;
//      sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//
//      vector<pair<UInt, UInt> > del_rows;
//      sm01.deleteRows(2, back_inserter(del_rows));
//      
//      Test("SparseMatrix01::deleteRows(threshold) 17", sm01.nRows(), UInt(1));
//      SparseMatrix01<UInt, Real>::RowCounts rc = sm01.getRowCounts();
//      UInt idx = rc[0].first, count = rc[0].second;
//      Test("SparseMatrix01::deleteRows(threshold) 18", idx, UInt(0));
//      Test("SparseMatrix01::deleteRows(threshold) 19", count, UInt(2));
//
//      x[0] = 1; x[1] = 0; x[2] = 0; x[3] = 1;
//      sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//
//      x[0] = 1; x[1] = 0; x[2] = 0; x[3] = 1;
//      sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//
//      x[0] = 1; x[1] = 0; x[2] = 0; x[3] = 1;
//      sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//
//      sm01.deleteRows(3, back_inserter(del_rows));
//
//      Test("SparseMatrix01::deleteRows(threshold) 20", sm01.nRows(), UInt(1));
//      rc = sm01.getRowCounts();
//      idx = rc[0].first, count = rc[0].second;
//      Test("SparseMatrix01::deleteRows(threshold) 21", idx, UInt(0));
//      Test("SparseMatrix01::deleteRows(threshold) 22", count, UInt(3));
//    }
//  }
// 
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_deleteColumns()
//  {    
//    { // Empty matrix
//      UInt nrows = 3, ncols = 3;
//    
//      { // Empty matrix, empty del
//	SparseMatrix01<UInt, Real> sm(ncols, nrows);
//	vector<UInt> del;
//	sm.deleteColumns(del.begin(), del.end());
//	Test("SparseMatrix01::deleteColumns() 1", sm.nCols(), UInt(3));
//      }
//
//      { // Empty matrix, 1 del
//	SparseMatrix01<UInt, Real> sm(ncols, nrows);
//	vector<UInt> del(1); del[0] = 0;
//	sm.deleteColumns(del.begin(), del.end());
//	Test("SparseMatrix01::deleteColumns() 2", sm.nCols(), UInt(2));
//      }        
//                                                  
//      { // Empty matrix, many dels
//	SparseMatrix01<UInt, Real> sm(ncols, nrows);
//	vector<UInt> del(2); del[0] = 0; del[1] = 2;
//	sm.deleteColumns(del.begin(), del.end());
//	Test("SparseMatrix01::deleteColumns() 3", sm.nCols(), UInt(1));
//      }
//    } // End empty matrix     
//     
//    {
//      UInt nrows, ncols, zr;   
//    
//      TEST_LOOP(M) {
//
//	Dense01<UInt, Real> dense(nrows, ncols, zr);   
// 
//	{ // Empty del
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	  vector<UInt> del;
//	  sm.deleteColumns(del.begin(), del.end());
//	  Test("SparseMatrix01::deleteColumns() 4", sm.nCols(), ncols);
//	}
//
//	{ // Many dels contiguous
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	  Dense01<UInt, Real> dense2(nrows, ncols, zr);
//	  vector<UInt> del;
//	  if (ncols > 2) {
//	    for (UInt i = 2; i < ncols-2; ++i)    
//	      del.push_back(i);
//	    sm.deleteColumns(del.begin(), del.end());
//	    dense2.deleteColumns(del.begin(), del.end());
//	    Compare(dense2, sm, "SparseMatrix01::deleteColumns() 6");
//	  }
//	}
//      
//	{ // Many dels discontiguous
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	  Dense01<UInt, Real> dense2(nrows, ncols, zr);
//	  vector<UInt> del;
//	  for (UInt i = 0; i < ncols; i += 2)
//	    del.push_back(i);
//	  sm.deleteColumns(del.begin(), del.end());
//	  dense2.deleteColumns(del.begin(), del.end());
//	  Compare(dense2, sm, "SparseMatrix01::deleteColumns() 7");
//	}
//
//	{ // All rows
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	  vector<UInt> del; 
//	  for (UInt i = 0; i < ncols; ++i)
//	    del.push_back(i);
//	  sm.deleteColumns(del.begin(), del.end());
//	  Test("SparseMatrix01::deleteColumns() 8", sm.nCols(), UInt(0));
//	}
//
//	{ // More than all rows => exception in assert mode
//          /*
//	    SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	    vector<UInt> del; 
//	    for (UInt i = 0; i < 2*ncols; ++i)
//	    del.push_back(i);
//	    sm.deleteColumns(del.begin(), del.end());
//	    Test("SparseMatrix01::deleteColumns() 9", sm.nCols(), UInt(0));
//          */
//	}
//
//	{ // Several dels in a row till empty
//	  SparseMatrix01<UInt, Real> sm(nrows, ncols, dense.begin(), 0);
//	  for (UInt i = 0; i < ncols; ++i) {
//	    vector<UInt> del(1); del[0] = 0;
//	    sm.deleteColumns(del.begin(), del.end());
//	    Test("SparseMatrix01::deleteColumns() 10", sm.nCols(), UInt(ncols-i-1));
//	  }
//	}
//      }
//    } 
//	
//    // Test with unique rows
//    {
//      UInt nrows = 10;   
//      std::vector<UInt> boundaries(2);
//      boundaries[0] = 4; boundaries[1] = 8;
//      UInt nnzr = (UInt)boundaries.size(), ncols = boundaries[nnzr-1];
//      SparseMatrix01<UInt, Real> sm01(ncols,1,nnzr);
//      std::vector<Real> x(ncols);
//
//      for (UInt i = 0; i < nrows; ++i) {
//
//	for (UInt j = 0; j < ncols; ++j)   
//	  x[j] = rng_->getReal64();
//
//	sm01.addUniqueFilteredRow(boundaries.begin(), x.begin());
//      }
//			
//      nrows = sm01.nRows();
//      SparseMatrix01<UInt, Real>::RowCounts rc = sm01.getRowCounts();
//      vector<UInt> del; del.push_back(1); del.push_back(3); del.push_back(5);
//      UInt ncols_new = sm01.nCols() - del.size();	
//      sm01.deleteColumns(del.begin(), del.end());
//      Test("SparseMatrix01::deleteColumns 11", sm01.nCols(), ncols_new);
//      Test("SparseMatrix01::deleteColumns 12", sm01.getRowCounts().size(), nrows);	
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_vecDistSquared()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    Dense01<UInt, Real> dense(nrows, ncols, 2);
//
//    vector<Real> x(ncols, 0), yref(nrows, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = Real(i);
//
//    dense.vecDistSquared(x.begin(), yref.begin());
//
//    SparseMatrix01<UInt, Real> smc(nrows, ncols, dense.begin(), 0);
//    vector<Real> y(nrows, 0);
//    smc.vecDistSquared(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecDistSquared compact 1");
//
//    SparseMatrix01<UInt, Real> smnc(ncols, nrows);
//    for (UInt i = 0; i < nrows; ++i)
//      smnc.addRow(dense.begin(i));
//    fill(y.begin(), y.end(), Real(0));
//    smnc.vecDistSquared(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecDistSquared non-compact");
//
//    smnc.compact();
//    fill(y.begin(), y.end(), Real(0));
//    smnc.vecDistSquared(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecDistSquared compact 2");
//
//    {
//      TEST_LOOP(M) {
//
//        Dense01<UInt, Real> dense2(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm2(nrows, ncols, dense2.begin(), 0);
//
//        vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        dense2.vecDistSquared(x2.begin(), yref2.begin());
//        fill(y2.begin(), y2.end(), Real(0));
//        sm2.vecDistSquared(x2.begin(), y2.begin());
//        {
//          stringstream str;
//          str << "vecDistSquared A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//
//        sm2.compact();
//        fill(y2.begin(), y2.end(), Real(0));
//        sm2.vecDistSquared(x2.begin(), y2.begin());
//        {
//          stringstream str;
//          str << "vecDistSquared B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      }
//    }
//
//    // test with back inserter
//    std::vector<Real> x2(16), y2;
//    SparseMatrix01<UInt, Real> sm(1, 16);
//    for (UInt i = 0; i < 10; ++i) {
//      for (UInt j = 0; j < 16; ++j)
//        x2[j] = Real(rng_->getUInt32(10));
//      sm.addRow(x2.begin());
//    }
//    sm.vecDistSquared(x2, back_inserter(y2));
//    Test("SparseMatrix01 back inserter", y2.size() > 0, true);
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_vecDist()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    Dense01<UInt, Real> dense(nrows, ncols, 2);
//
//    vector<Real> x(ncols, 0), yref(nrows, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = Real(i);
//
//    dense.vecDist(x.begin(), yref.begin());
//
//    SparseMatrix01<UInt, Real> smc(nrows, ncols, dense.begin(), 0);
//    vector<Real> y(nrows, 0);
//    smc.vecDist(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecDist compact 1");
//
//    SparseMatrix01<UInt, Real> smnc(ncols, nrows);
//    for (UInt i = 0; i < nrows; ++i)
//      smnc.addRow(dense.begin(i));
//    fill(y.begin(), y.end(), Real(0));
//    smnc.vecDist(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecDist non-compact");
//
//    smnc.compact();
//    fill(y.begin(), y.end(), Real(0));
//    smnc.vecDist(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecDist compact 2");
//
//    {
//      TEST_LOOP(M) {
//
//        Dense01<UInt, Real> dense2(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm2(nrows, ncols, dense2.begin(), 0);
//
//        vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        dense2.vecDist(x2.begin(), yref2.begin());
//        fill(y2.begin(), y2.end(), Real(0));
//        sm2.vecDist(x2.begin(), y2.begin());
//        {
//          stringstream str;
//          str << "vecDist A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//   
//        sm2.compact();
//        fill(y2.begin(), y2.end(), Real(0));
//        sm2.vecDist(x2.begin(), y2.begin());
//        {
//          stringstream str;
//          str << "vecDist B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_vecMaxProd()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    Dense01<UInt, Real> dense(nrows, ncols, zr);
//
//    vector<Real> x(ncols), y(nrows, 0), yref(nrows, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = Real(i);
//
//    dense.vecMaxProd(x.begin(), yref.begin());
//
//    SparseMatrix01<UInt, Real> smnc(ncols, nrows);
//    for (UInt i = 0; i < nrows; ++i)
//      smnc.addRow(dense.begin(i));
//    smnc.vecMaxProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecMaxProd non compact 1");
//
//    smnc.compact();
//    fill(y.begin(), y.end(), Real(0));
//    smnc.vecMaxProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecMaxProd compact 1");
//
//    SparseMatrix01<UInt, Real> smc(nrows, ncols, dense.begin(), 0);
//    fill(y.begin(), y.end(), Real(0));
//    smc.vecMaxProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecMaxProd compact 2");
//
//    {
//      TEST_LOOP(M) {
//
//        Dense01<UInt, Real> dense2(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm2(nrows, ncols, dense2.begin(), 0);
//
//        vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        dense2.vecMaxProd(x2.begin(), yref2.begin());
//        sm2.vecMaxProd(x2.begin(), y2.begin());
//        {
//          stringstream str;
//          str << "vecMaxProd A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//
//        sm2.compact();
//        fill(y2.begin(), y2.end(), Real(0));
//        sm2.vecMaxProd(x2.begin(), y2.begin());
//        {
//          stringstream str;
//          str << "vecMaxProd B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_vecProd()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    Dense01<UInt, Real> dense(nrows, ncols, zr);
//
//    vector<Real> x(ncols), y(nrows, 0), yref(nrows, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = Real(i);
//
//    dense.rightVecProd(x.begin(), yref.begin());
//
//    SparseMatrix01<UInt, Real> smnc(ncols, nrows);
//    for (UInt i = 0; i < nrows; ++i)
//      smnc.addRow(dense.begin(i));
//    smnc.rightVecProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "rightVecProd non compact 1");
//
//    smnc.compact();
//    fill(y.begin(), y.end(), Real(0));
//    smnc.rightVecProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "rightVecProd compact 1");
//
//    SparseMatrix01<UInt, Real> smc(nrows, ncols, dense.begin(), 0);
//    fill(y.begin(), y.end(), Real(0));
//    smc.rightVecProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "rightVecProd compact 2");
//
//    {
//      TEST_LOOP(M) {
//
//        Dense01<UInt, Real> dense2(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm2(nrows, ncols, dense2.begin(), 0);
//
//        vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        dense2.rightVecProd(x2.begin(), yref2.begin());
//        sm2.rightVecProd(x2.begin(), y2.begin());
//        {
//          stringstream str;
//          str << "rightVecProd A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//
//        sm2.compact();
//        fill(y2.begin(), y2.end(), Real(0));
//        sm2.rightVecProd(x2.begin(), y2.begin());
//        {
//          stringstream str;
//          str << "rightVecProd B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_rowDistSquared()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    Dense01<UInt, Real> dense(nrows, ncols, zr);
//    SparseMatrix01<UInt, Real> sm4c(nrows, ncols, dense.begin(), 0);
//
//    vector<Real> x(ncols, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = Real(20*i + 1);
//
//    Real res1, res2;
//
//    { // compact, b = 0
//      res1 = dense.rowDistSquared(3, x.begin());
//      res2 = sm4c.rowDistSquared(3, x.begin());
//      Test("rowDistSquared, b = 0", res1, res2);
//    }
//
//    { // compact, a = 0, with reallocation
//      res1 = dense.rowDistSquared(2, x.begin());
//      res2 = sm4c.rowDistSquared(2, x.begin());
//      Test("rowDistSquared, a = 0 /1", res1, res2);
//    }
//
//    { // compact, a = 0, without reallocation
//      res1 = dense.rowDistSquared(3, x.begin());
//      res2 = sm4c.rowDistSquared(3, x.begin());
//      Test("rowDistSquared, a = 0 /2", res1, res2);
//    }
//
//    { // compact, a != 0,  b != 0, without reallocation
//      res1 = dense.rowDistSquared(3, x.begin());
//      res2 = sm4c.rowDistSquared(3, x.begin());
//      Test("rowDistSquared, a, b != 0 /1", res1, res2);
//    }
//
//    { // compact, a != 0,  b != 0, with reallocation
//      res1 = dense.rowDistSquared(4, x.begin());
//      res2 = sm4c.rowDistSquared(4, x.begin());
//      Test("rowDistSquared, a, b != 0 /2", res1, res2);
//    }
//
//    {
//      TEST_LOOP(M) {
//
//        Dense01<UInt, Real> dense2(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm2(nrows, ncols, dense2.begin(), 0);
//
//        vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        for (i = 0; i < nrows; i += 5) {
//
//          res1 = dense2.rowDistSquared(i, x2.begin());
//          res2 = sm2.rowDistSquared(i, x2.begin());
//          {
//            stringstream str;
//            str << "rowDistSquared " << nrows << "X" << ncols << "/" << zr
//                << " - non compact";
//            Test(str.str().c_str(), res1, res2);
//          }
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_closestEuclidean()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    Dense01<UInt, Real> dense(nrows, ncols, zr);
//
//    vector<Real> x(ncols, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = Real(20*i);
//
//    pair<UInt, Real> res(0, 0), ref = dense.closestEuclidean(x.begin());
//
//    SparseMatrix01<UInt, Real> smc(nrows, ncols, dense.begin(), 0);
//    res = smc.closestEuclidean(x.begin());
//    ComparePair(res, ref, "closestEuclidean compact 1");
//
//    SparseMatrix01<UInt, Real> smnc(ncols, nrows);
//    res.first = 0; res.second = 0;
//    for (UInt i = 0; i < nrows; ++i)
//      smnc.addRow(dense.begin(i));
//    res = smnc.closestEuclidean(x.begin());
//    ComparePair(res, ref, "closestEuclidean non compact");
//
//    smnc.compact();
//    res.first = 0; res.second = 0;
//    res = smnc.closestEuclidean(x.begin());
//    ComparePair(res, ref, "closestEuclidean compact 2");
//  
//    {
//      TEST_LOOP(M) {
//
//        Dense01<UInt, Real> dense2(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm2(nrows, ncols, dense2.begin(), 0);
//
//        vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        ref = dense2.closestEuclidean(x2.begin());
//        res.first = 0; res.second = 0;
//        res = sm2.closestEuclidean(x2.begin());
//        {    
//          stringstream str;
//          str << "closestEuclidean A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          ComparePair(res, ref, str.str().c_str());
//        }
//
//        sm2.compact();
//        res.first = 0; res.second = 0;
//        res = sm2.closestEuclidean(x2.begin());
//        {
//          stringstream str;
//          str << "closestEuclidean B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          ComparePair(res, ref, str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_closestDot()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    Dense01<UInt, Real> dense(nrows, ncols, zr);
//
//    vector<Real> x(ncols, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = Real(20*i);
//
//    pair<UInt, Real> res(0, 0), ref = dense.closestDot(x.begin());
//
//    SparseMatrix01<UInt, Real> smc(nrows, ncols, dense.begin(), 0);
//    res = smc.closestDot(x.begin());
//    ComparePair(res, ref, "closestDot compact 1");
//
//    {
//      TEST_LOOP(M) {
//
//        Dense01<UInt, Real> dense2(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm2(nrows, ncols, dense2.begin(), 0);
//
//        vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        ref = dense2.closestDot(x2.begin());
//        res.first = 0; res.second = 0;
//        res = sm2.closestDot(x2.begin());
//        {
//          stringstream str;
//          str << "closestDot A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          ComparePair(res, ref, str.str().c_str());
//        }
//
//        sm2.compact();
//        res.first = 0; res.second = 0;
//        res = sm2.closestDot(x2.begin());
//        {
//          stringstream str;
//          str << "closestDot B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          ComparePair(res, ref, str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_rowMax()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//  
//    Dense01<UInt, Real> dense(nrows, ncols, zr);
//    SparseMatrix01<UInt, Real> sm4c(nrows, ncols, dense.begin(), 0);
//
//    {
//      TEST_LOOP(M) {
//        
//        Dense01<UInt, Real> dense2(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm2(nrows, ncols, dense2.begin(), 0);
//
//        vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        dense2.rowMax(x2.begin(), y2.begin());
//        sm2.rowMax(x2.begin(), yref2.begin());
//      
//        {
//          stringstream str;
//          str << "rowMax A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      
//        sm2.compact();
//        dense2.rowMax(x2.begin(), y2.begin());
//        sm2.rowMax(x2.begin(), yref2.begin());
//        {
//          stringstream str;
//          str << "rowMax B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_rowProd()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;      
//    zr = 2;
//
//    Dense01<UInt, Real> dense(nrows, ncols, zr);
//    SparseMatrix01<UInt, Real> sm4c(nrows, ncols, dense.begin(), 0);
//
//    {   
//      TEST_LOOP(M) {
//
//        Dense01<UInt, Real> dense2(nrows, ncols, zr);
//        SparseMatrix01<UInt, Real> sm2(nrows, ncols, dense2.begin(), 0);
//
//        vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = rng_->getReal64();
//
//        sm2.decompact();
//        dense2.rowProd(x2.begin(), y2.begin());
//        sm2.rowProd(x2.begin(), yref2.begin());
//      
//        {     
//          stringstream str;
//          str << "rowProd A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }      
//               
//        sm2.compact();
//        dense2.rowProd(x2.begin(), y2.begin());
//        sm2.rowProd(x2.begin(), yref2.begin());
//        {
//          stringstream str;
//          str << "rowProd B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      }
//    }
//
//  
//  }   
//
//  //--------------------------------------------------------------------------------
//  struct RowCounter : public map<vector<Real>, UInt>
//  {
//    inline void addRow(vector<Real>& v) {
//         
//      iterator it = find(v);
//      if (it == end())
//        (*this)[v] = 1;
//      else
//        ++ it->second;
//    }    
//
//    inline void checkRowCounts(Tester& t, SparseMatrix01<UInt, Real>& sm01,
//                               const char* str)
//    {
//      stringstream buf;
//      buf << "SparseMatrix01 row counts nrows " << str;
//      t.Test(buf.str(), sm01.nRows(), size());
//      SparseMatrix01<UInt, Real>::RowCounts rc = sm01.getRowCounts();
//      for (UInt i = 0; i < rc.size(); ++i) {
//        vector<Real> v(sm01.nCols(), 0);
//        sm01.getRow(rc[i].first, v.begin());
//        const_iterator it = find(v);
//        stringstream buf1;
//        buf1 << "SparseMatrix01 row counts not found " << str;
//        t.Test(buf1.str(), it != end(), true);
//        stringstream buf2;
//        buf2 << "SparseMatrix01 row counts equal counts " << str;
//        t.Test(buf2.str(), rc[i].second, it->second);
//      }  
//    }
//  };
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_row_counts()
//  {
//    { // Testing the comparison function
//      const UInt rowSize = 4;
//      UInt row1[rowSize], row2[rowSize];
//      
//      RowCompare<UInt> comp(rowSize);
//      
//      for (UInt i = 0; i < rowSize; ++i) 
//        row1[i] = row2[i] = i;
//      
//      Test("SparseMatrix01 row counts 1", comp(row1, row2), false);
//      
//      row2[1] = 3; row2[2] = 5; row2[3] = 7;
//      Test("SparseMatrix01 row counts 2", comp(row1, row2), false);
//      Test("SparseMatrix01 row counts 3", comp(row2, row1), true);
//    }   
//
//    { // Testing the comparison function with a set
//      UInt ncols, nrows, nchildren, w, n;
//      nchildren = 5; w = 8;
//      nrows = 5; ncols = w * nchildren;
//      n = 1000;
//
//      vector<UInt> boundaries(nchildren, 0);
//      
//      boundaries[0] = rng_->getUInt32(w) + 1;
//      for (UInt i = 1; i < nchildren-1; ++i) 
//        boundaries[i] = boundaries[i-1] + (rng_->getUInt32(w) + 1);
//      boundaries[nchildren-1] = ncols;
//
//      typedef std::set<UInt*, RowCompare<UInt> > SetType;
//      RowCompare<UInt> comp(nchildren);
//      SetType myset(comp);
//
//      vector<UInt*> v;
//
//      for (UInt i = 0; i < n; ++i) {
//        vector<Real> x(ncols);
//        for (UInt j = 0; j < ncols; ++j)
//          x[j] = rng_->getReal64();
//        vector<Real> binrow(ncols);
//        winnerTakesAll(boundaries, x.begin(), binrow.begin());
//        UInt* comp = new UInt[nchildren];
//        v.push_back(comp);
//        UInt k = 0;
//        for (UInt j = 0; j < ncols; ++j)
//          if (binrow[j] > 0)
//            comp[k++] = j;
//        myset.insert(comp);
//      }
//   
//      for (UInt i = 0; i < v.size(); ++i) 
//        Test("SparseMatrix01 row counts 4", (myset.find(v[i]) != myset.end()), true);
//
//      for (UInt i = 0; i < v.size(); ++i)
//        delete [] v[i];
//    }
//
//    {
//      UInt ncols = 16, nnzr = 9, nreps = 10;
//
//      RowCounter control;
//      SparseMatrix01<UInt, Real> sm(ncols, 1, nnzr);
//    
//      for (UInt n = 0; n < nreps; ++n) {
//        vector<Real> v(ncols, 0);    
//        GenerateRand01Vector(rng_, nnzr, v);
//        sm.addRow(v.begin());     
//        control.addRow(v);
//      }       
//  
//      control.checkRowCounts(*this, sm, "1");
//
//      Test("SparseMatrix01 row counts ", sm.getRowCounts().size() > 0, true);
//
//      // checking that counts are intact after decompact and recompact
//      // that manipulate row pointers
//      sm.decompact();    
//
//      control.checkRowCounts(*this, sm, "2");
//
//      for (UInt n = 0; n < nreps; ++n) {
//        vector<Real> v(ncols, 0);
//        GenerateRand01Vector(rng_, nnzr, v);
//        sm.addRow(v.begin());
//        control.addRow(v);
//      }    
//
//      sm.compact();
//
//      control.checkRowCounts(*this, sm, "3");
//
//      // checking that counts are correct when initializing sparse matrix
//      // from stream
//      stringstream buf;
//      sm.toCSR(buf);
//      SparseMatrix01<UInt, Real> sm2(ncols, 1, nnzr);
//      sm2.fromCSR(buf);
//
//      control.checkRowCounts(*this, sm2, "4");
//    }
//  }    
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_print()
//  {
//    UInt nrows, ncols, zr;    
//    nrows = 225; ncols = 31; zr = 30;
//
//    TEST_LOOP(M) {
//      std::stringstream buf1, buf2;
//           
//      Dense01<UInt, Real> d(nrows, ncols, zr);
//      SparseMatrix01<UInt, Real> sm(nrows, ncols, d.begin(), 0);
//      
//      std::vector<Real> d2(nrows*ncols);
//      sm.toDense(d2.begin());
//      for (UInt i = 0; i < nrows; ++i) {
//        for (UInt j = 0; j < ncols; ++j)
//          buf1 << d2[i*ncols+j] << " ";
//        buf1 << endl;
//      }     
//   
//      sm.print(buf2);
//      Test("SparseMatrix01 print 1", buf1.str(), buf2.str());
//    }
//  }   
//
//  //--------------------------------------------------------------------------------
//  /* Performance
//     UInt nrows = 30000, ncols = 128, zr = 0;   
//     Dense01<UInt, Real> d(nrows, ncols, zr);       
//     SparseMatrix01<UInt, Real> sm01(nrows, ncols, d.begin(), 0);
//     std::vector<Real> x(ncols, 1), y(nrows, 0);
//     sm01.compact();                               
//                
//     { // 3000 iterations, 30000x128, 69.6% of total time, darwin86
//     // 22.6 without hand unrolling by 4 of loop on k
//     // 15.62s straight loops
//     // 15.61s with tree-vectorize, straight loops
//     // 14.85s with iterator++ instead of indexing into x
//     // 14.79s with iterator++ and 4-unrolled loop on i
//     // 14.75s with compact
//     // 14.89s with pointer while, 4-unrolled loop on i   
//     // 14.82s with pointer while, 2-unrolled loop on i
//     // 14.78s with pointer while, not unrolled loop on i
//     // 12.39s with pre-fetching x into nzb_
//     boost::timer t;   
//     ITER_1(3000) 
//     sm01.rowProd(x.begin(), y.begin());
//     cout << t.elapsed() << endl;   
//     }
//  */  
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrix01UnitTest::unit_test_numerical_accuracy()
//  {
//    UInt nrows, ncols, zr;
//
//    { // Tests for accuracy/numerical stability/underflows
//      nrows = 1; zr = 0;
//      
//      for (ncols = 1; ncols < 128; ++ncols) {
//        vector<Real> y_d_prod(nrows), y_d_sum(nrows);
//        vector<float> y_f_prod(nrows), y_f_sum(nrows);
//
//        { // Real
//          Dense01<UInt, Real> dense_d(nrows, ncols, zr);
//          ITER_2(nrows, ncols)
//	    dense_d.at(i,j) = 1;//Real(i*ncols+j + 1e-6)/Real(nrows*ncols);
//          SparseMatrix01<UInt, Real> sm_d(nrows, ncols, dense_d.begin(), 0);
//          vector<Real> x_d(ncols);
//          ITER_1(ncols)
//            x_d[i] = Real(ncols-i + 1e-5)/Real(ncols);
//          sm_d.rowProd(x_d.begin(), y_d_prod.begin());
//          sm_d.rightVecProd(x_d.begin(), y_d_sum.begin());
//        }      
//
//        { // float
//          Dense01<UInt, float> dense_f(nrows, ncols, zr);
//          ITER_2(nrows, ncols)
//	    dense_f.at(i,j) = 1;//10*float(i*ncols+j + 1e-6)/float(nrows*ncols);
//          SparseMatrix01<UInt, float> sm_f(nrows, ncols, dense_f.begin(), 0);
//          vector<float> x_f(ncols);
//          ITER_1(ncols)
//            x_f[i] = float(ncols-i + 1e-5)/float(ncols);
//          sm_f.rowProd(x_f.begin(), y_f_prod.begin());
//	  cout << setprecision(15) << "unsorted: " << y_f_prod[0];
//	  sort(x_f.begin(), x_f.end());
//	  sm_f.rowProd(x_f.begin(), y_f_prod.begin());
//	  cout << " sorted: " << y_f_prod[0] << endl;
//          sm_f.rightVecProd(x_f.begin(), y_f_sum.begin());
//        }
//
//        Real prod_rel_err = fabs((y_d_prod[0] - y_f_prod[0]) / y_d_prod[0]);
//        Real sum_rel_err = fabs((y_d_sum[0] - y_f_sum[0]) / y_d_sum[0]);
//        
//        cout << setprecision(0);
//        cout << "ncols = " << ncols 
//          // << " Real = " << float(y_d_prod[0])
//          // << " float = " << y_f[0]
//          // << " error = " << (y_d[0] - y_f[0])
//             << " prod: " << prod_rel_err;
//        cout << " sum: " << sum_rel_err
//             << endl;
//      }
//    }
//  }         
//
//	//--------------------------------------------------------------------------------
//  /**
//   * A generator function object, that generates random numbers between 0 and 256.
//   * It also has a threshold to control the sparsity of the vectors generated. 
//   */
//  template <typename T>
//  struct rand_init 
//  {
//    Random *r_;
//    int threshold_;
//    
//    inline rand_init(Random *r, int threshold =100)
//      : r_(r), threshold_(threshold)
//    {}
//    
//    inline T operator()() 
//    { 
//      return T(r_->getUInt32(100) > threshold_ ? 0 : 1 + r_->getUInt32(255));
//    }
//  };
//  
//  
//  //--------------------------------------------------------------------------------
//  // THERE IS NO addRow WRITTEN YET for Dense01
//  // THERE IS NO rowProd WRITTEN YET for Dense01
//  void SparseMatrix01UnitTest::unit_test_usage()
//  {
//    /*
//    SparseMatrix01<size_t, float>* sm = 
//      new SparseMatrix01<size_t, float>(16,0);
//
//    Dense01<size_t, float>* smDense =
//      new Dense01<size_t, float>(16,0);
//
//    for (long int a = 0; a < 1000000; ++a) {
//
//      size_t r = 1000;
//      while(r==1000 || r==5)
//	r = rng_->get() % 18;
//      
//      if (r == 0) {
//
//	sm->compact();
//	// no compact for Dense
//
//      } else if (r == 1) {    
//
//	sm->decompact();
//	// no decompact for Dense
//
//      } else if (r == 2) {
//
//	vector<size_t> del;
//	if (rng_->get() % 100 < 90) {
//	  for (size_t ii = 0; ii < sm->nRows() / 4; ++ii)
//	    del.push_back(2*ii);
//	  sm->deleteRows(del.begin(), del.end());
//	  smDense->deleteRows(del.begin(), del.end());
//	} else {
//	  for (size_t ii = 0; ii < sm->nRows(); ++ii)
//	    del.push_back(ii);
//	  sm->deleteRows(del.begin(), del.end());
//	  smDense->deleteRows(del.begin(), del.end());
//	}
//	Compare(*smDense, *sm, "deleteRows");
//
//      } else if (r == 3) {    
//
//	vector<size_t> del;
//	if (rng_->get() % 100 < 90) {
//	  for (size_t ii = 0; ii < sm->nCols() / 4; ++ii)
//	    del.push_back(2*ii);
//	  sm->deleteColumns(del.begin(), del.end());
//	  smDense->deleteColumns(del.begin(), del.end());
//	} else {
//	  for (size_t ii = 0; ii < sm->nCols(); ++ii)
//	    del.push_back(ii);
//	  sm->deleteColumns(del.begin(), del.end());
//	  smDense->deleteColumns(del.begin(), del.end());
//	}
//	Compare(*smDense, *sm, "deleteColumns");
//
//      }  
//      else if (r == 4) {
//	
//	vector<float> new_row(sm->nCols(), 0);
//	size_t n = rng_->get() % 16;
//	for (size_t z = 0; z < n; ++z) {			
//	  if (rng_->get() % 100 < 90) {
//	    for (size_t ii = 0; ii < new_row.size(); ++ii)
//	      new_row[ii] = (float) (rng_->get() % 100 > 70 ? 0 : rng_->get() % 256);
//	  } 
//	  sm->addRow(new_row.begin());
//	  // THERE IS NO addRow WRITTEN YET
//	  //smDense->addRow(ne_row.begin());
//	  //Compare(*smDense, *sm, "addRow");
//	}
//	
//      } else if (r == 5) {
//	
//	size_t nrows = rng_->get() % 32, ncols = rng_->get() % 32+1;	
//	delete sm;
//	delete smDense;
//	sm = new SparseMatrix01<size_t, float>(ncols, nrows);
//	smDense = new Dense01<size_t, float>(ncols, nrows);
//	Compare(*smDense, *sm, "constructor(ncols,nrows)");
//
//      } else if (r == 6) {
//	
//	delete sm;
//	delete smDense;
//	sm = new SparseMatrix01<size_t, float>(16,0);
//	smDense = new Dense01<size_t, float>(16,0);
//	Compare(*smDense, *sm, "constructor(16,0)");
//	
//      } else if (r == 8) {				
//
//	vector<float> x(sm->nCols()), y(sm->nRows());
//	generate(x.begin(), x.end(), rand_init<float>(rng_, 50));
//	sm->vecDistSquared(x.begin(), y.begin());
//	smDense->vecDistSquared(x.begin(), y.begin());
//	Compare(*smDense, *sm, "vecDistSquared");
//
//      } else if (r == 9) {
//	  
//	if(sm->nCols()==smDense->ncols && sm->nRows()==smDense->nrows){
//	  vector<float> x(sm->nCols()), y(sm->nRows());
//	 // vector<float> xDense(smDense->ncols), yDense(smDense->nrows);
//	  generate(x.begin(), x.end(), rand_init<float>(rng_, 50));
//	  //xDense=x;
//	  sm->vecDist(x.begin(), y.begin());
//	  smDense->vecDist(x.begin(), y.begin());
//	  //Compare(*smDense, *sm, "vecDist");
//	}
//
//      } else if(r == 10) {
//
//	if(sm->nRows() > 0) {
//	  vector<float> x(sm->nCols());
//	  generate(x.begin(), x.end(), rand_init<float>(rng_, 50));
//	  size_t randInt = rng_->get() % sm->nRows();
//	  sm->rowDistSquared(randInt, x.begin());
//	  smDense->rowDistSquared(randInt, x.begin());
//	  Compare(*smDense, *sm, "rowDistSquared");
//	}
//	  
//      } else if (r == 11) {
//	  
//	vector<float> x(sm->nCols());
//	generate(x.begin(), x.end(), rand_init<float>(rng_, 50));
//	sm->closestEuclidean(x.begin());
//	smDense->closestEuclidean(x.begin());
//	Compare(*smDense, *sm, "closestEuclidean");
//
//      } else if (r== 12) {
//
//	vector<float> x(sm->nCols());
//	generate(x.begin(), x.end(), rand_init<float>(rng_, 50));
//	for (size_t n = 0; n < sm->nCols(); ++n)	
//	  x.push_back(float(rng_->get() % 256));
//	sm->closestDot(x.begin()); 
//	smDense->closestDot(x.begin());
//	Compare(*smDense, *sm, "closestDot");
//
//      } else if (r == 13) {
//
//	if(sm->nCols()==smDense->ncols && sm->nRows()==smDense->nrows){
//	  vector<float> x(sm->nCols()), y(sm->nRows());
//	  generate(x.begin(), x.end(), rand_init<float>(rng_, 50));
//	  sm->rightVecProd(x.begin(), y.begin());
//	  smDense->rightVecProd(x.begin(), y.begin());
//	  Compare(*smDense, *sm, "rightVecProd");
//    }
//
//      } else if (r == 14) {
//	  
//	if(sm->nCols()==smDense->ncols && sm->nRows()==smDense->nrows){
//	  vector<float> x(sm->nCols()), y(sm->nRows());
//	  generate(x.begin(), x.end(), rand_init<float>(rng_, 50));
//	  sm->vecMaxProd(x.begin(), y.begin());
//	  smDense->vecMaxProd(x.begin(), y.begin());
//	  Compare(*smDense, *sm, "vecMaxProd");
//	}
//	  
//      } else if (r == 15) {
//	  
//	if(sm->nCols()==smDense->ncols && sm->nRows()==smDense->nrows){
//	  vector<float> x(sm->nCols()), y(sm->nRows());
//	  generate(x.begin(), x.end(), rand_init<float>(rng_, 50));
//	  sm->rowMax(x.begin(), y.begin());
//	  smDense->rowMax(x.begin(), y.begin()); 
//	  Compare(*smDense, *sm, "rowMax");
//	}
//
//      } else if (r == 16) {
//	  
//	if(sm->nCols()==smDense->ncols && sm->nRows()==smDense->nrows){
//	  vector<float> x(sm->nCols()), y(sm->nRows());
//	  generate(x.begin(), x.end(), rand_init<float>(rng_, 50));
//	  sm->rowProd(x.begin(), y.begin()); 
//	  smDense->rowProd(x.begin(), y.begin()); 
//	  Compare(*smDense, *sm, "rowProd(x.begin(), y.begin())");
//	}
//	  
//      } else if (r == 17) {
//	  
//	vector<float> x(sm->nCols()), y(sm->nRows());
//	generate(x.begin(), x.end(), rand_init<float>(rng_, 50));
//	float theRandom = float(rng_->get() % 256);
//	sm->rowProd(x.begin(), y.begin(),  theRandom);
//	// THERE IS NO rowProd WRITTEN YET
//	//smDense->rowProd(x.begin(), y.begin(), theRandom);
//	//Compare(*smDense, *sm, "rowProd(x.begin(), y.begin(),  float(rng_->get() % 256))");
//      } 
//
//    }
//    
//    // transpose(SparseMatrix01<size_type, value_type, DTZ>& tr) 
//    // vecDistSquared(InIter x, OutIter y) 
//    // minVecDistSquared(InIter x, 
//    // vecDist(InIter x, OutIter y) 
//    // value_type rowDistSquared( size_type& row, InIter x) 
//    // pair<size_type, value_type> closestEuclidean(InIter x) 
//    // pair<size_type, value_type> closestDot(InIter x) 
//    // rightVecProd(InIter x, OutIter y) 
//    // vecMaxProd(InIter x, OutIter y) 
//    // vecMaxProd01(InIter x, OutIter y) 
//    // axby_2( size_type& row, value_type a, value_type b, InIter x)
//    // axby_3(value_type a, value_type b, InIter x)
//    // rowMax(OutIter maxima)      
//    // colMax(OutIter maxima) 
//    // normalizeRows(bool exact =false)
//    // value_type accumulate_nz( size_type& row, binary_functor f, 
//    // value_type accumulate( size_type& row, binary_functor f, 
//    // multiply( SparseMatrix01& B, SparseMatrix01& C) 
//    // size_type findRow( size_type nnzr, IndIt ind_it, NzIt nz_it)
//    // findRows(F f, MatchIt m_it) 
//    // map( SparseMatrix01& B, SparseMatrix01& C) 
//    */
//  } 
//
  //--------------------------------------------------------------------------------
  void SparseMatrix01UnitTest::RunTests()
  {         
           
    //unit_test_construction();   
    //unit_test_fromDense();      
    //unit_test_csr();
    //unit_test_compact();
    //unit_test_getRowSparse();
    //unit_test_addRow();
    //unit_test_addUniqueFilteredRow();
    //unit_test_addMinHamming();
    //unit_test_deleteRows();
    //unit_test_deleteColumns();
    //unit_test_rowDistSquared();
    //unit_test_vecDistSquared();
    //unit_test_vecDist();
    //unit_test_closestEuclidean();
    //unit_test_closestDot();
    //unit_test_vecMaxProd();
    //unit_test_vecProd();
    //unit_test_rowMax();
    //unit_test_rowProd();
    //unit_test_row_counts();
    //unit_test_print();
    ////unit_test_usage();
    ////unit_test_numerical_accuracy();
  } 

  //--------------------------------------------------------------------------------
  
} // namespace nta


