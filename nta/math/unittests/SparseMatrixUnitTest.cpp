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
 * Implementation of unit testing for class SparseMatrix
 */  
              
//#include <nta/common/version.hpp>
#include <nta/math/stl_io.hpp>
#include "SparseMatrixUnitTest.hpp"
    
using namespace std;  

namespace nta {         
   
#define TEST_LOOP(M)                                  \
  for (nrows = 0, ncols = M, zr = 15;                 \
       nrows < M;                                     \
       nrows += M/10, ncols -= M/10, zr = ncols/10)   \

#define M 64
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_construction()
//  {
//    UInt ncols, nrows, zr;
//
//    { // Deallocate an empty matrix
//      SparseMat sm;
//      Test("empty matrix 1", sm.isZero(), true);
//    }
//
//    { // Compact and deallocate an empty matrix
//      SparseMat sm;
//      Test("empty matrix 2", sm.isZero(), true);
//      sm.compact();     
//      Test("empty matrix 2 - compact", sm.isZero(), true);
//    }
//
//    { // De-compact and deallocate an empty matrix
//      SparseMat sm;
//      Test("empty matrix 3", sm.isZero(), true);
//      sm.decompact();     
//      Test("empty matrix 3 - decompact", sm.isZero(), true);
//    }
//
//    { // De-compact/compact and deallocate an empty matrix
//      SparseMat sm;
//      Test("empty matrix 4", sm.isZero(), true);
//      sm.decompact();     
//      Test("empty matrix 4 - decompact", sm.isZero(), true);
//      sm.compact();
//      Test("empty matrix 4 - compact", sm.isZero(), true);
//    }
//
//    { // Compact and deallocate an empty matrix
//      SparseMat sm(0, 0);
//      Test("empty matrix 5", sm.isZero(), true);
//      sm.compact();     
//      Test("empty matrix 5 - compact", sm.isZero(), true);
//    }
//
//    { // De-compact and deallocate an empty matrix
//      SparseMat sm(0, 0);
//      Test("empty matrix 6", sm.isZero(), true);
//      sm.decompact();     
//      Test("empty matrix 6 - decompact", sm.isZero(), true);
//    }
//
//    { // De-compact/compact and deallocate an empty matrix
//      SparseMat sm(0, 0);
//      Test("empty matrix 7", sm.isZero(), true);
//      sm.decompact();     
//      Test("empty matrix 7 - decompact", sm.isZero(), true);
//      sm.compact();
//      Test("empty matrix 7 - compact", sm.isZero(), true);
//    }
//
//    { // Rectangular shape, no zeros
//      nrows = 3; ncols = 4;
//      DenseMat dense(nrows, ncols, 0);
//      SparseMat sm(nrows, ncols, dense.begin());
//      Compare(dense, sm, "ctor 1");
//      Test("isZero 1", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 1 - compact");
//      Test("isZero 1 - compact", sm.isZero(), false);
//    }
//
//    { // Rectangular shape, zeros
//      nrows = 3; ncols = 4;
//      DenseMat dense(nrows, ncols, 2);
//      SparseMat sm(nrows, ncols, dense.begin());
//      Compare(dense, sm, "ctor 2");
//      Test("isZero 2", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 2 - compact");
//      Test("isZero 2 - compact", sm.isZero(), false);
//    }
//  
//    { // Rectangular the other way, no zeros     
//      nrows = 4; ncols = 3;
//      DenseMat dense(nrows, ncols, 0);
//      SparseMat sm(nrows, ncols, dense.begin());
//      Compare(dense, sm, "ctor 3");
//      Test("isZero 3", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 3 - compact");
//      Test("isZero 3 - compact", sm.isZero(), false);
//    }
//
//    { // Rectangular the other way, zeros
//      nrows = 6; ncols = 5;
//      DenseMat dense(nrows, ncols, 2);
//      SparseMat sm(nrows, ncols, dense.begin());
//      Compare(dense, sm, "ctor 4");
//      Test("isZero 4", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 4 - compact");
//      Test("isZero 4 - compact", sm.isZero(), false);
//    }
//
//    { // Empty rows in the middle and zeros
//      nrows = 3; ncols = 4;
//      DenseMat dense(nrows, ncols, 2, false, true);
//      SparseMat sm(nrows, ncols, dense.begin());
//      Compare(dense, sm, "ctor 5");
//      Test("isZero 5", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 5 - compact");
//      Test("isZero 5 - compact", sm.isZero(), false);
//    }       
//
//    { // Empty rows in the middle and zeros
//      nrows = 7; ncols = 5;
//      DenseMat dense(nrows, ncols, 2, false, true);
//      SparseMat sm(nrows, ncols, dense.begin());
//      Compare(dense, sm, "ctor 6");
//      Test("isZero 6", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 6 - compact");
//      Test("isZero 6 - compact", sm.isZero(), false);
//    }     
//    
//    { // Small values, zeros and empty rows
//      nrows = 7; ncols = 5;
//      DenseMat dense(nrows, ncols, 2, true, true, rng_);
//      SparseMat sm(nrows, ncols, dense.begin());
//      Compare(dense, sm, "ctor 7");
//      Test("isZero 7", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 7 - compact");
//      Test("isZero 7 - compact", sm.isZero(), false);
//    } 
//
//    { // Small values, zeros and empty rows, other constructor
//      nrows = 10; ncols = 10;
//      DenseMat dense(nrows, ncols, 2, true, true, rng_);
//      SparseMat sm(0, ncols);
//      for (UInt i = 0; i < nrows; ++i)
//        sm.addRow(dense.begin(i));
//      Compare(dense, sm, "ctor 8");
//      Test("isZero 8", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 8 - compact");
//      Test("isZero 8 - compact", sm.isZero(), false);
//    }       
//
//    { // Zero first row
//      nrows = 10; ncols = 10;
//      DenseMat dense(nrows, ncols, 2, true, true, rng_);
//      for (UInt i = 0; i < ncols; ++i)
//	dense.at(0, i) = 0;
//      SparseMat sm(0, ncols);
//      for (UInt i = 0; i < nrows; ++i)
//        sm.addRow(dense.begin(i));
//      Compare(dense, sm, "ctor 8B");
//      Test("isZero 8B", sm.isZero(), false);
//      sm.compact();
//      Compare(dense, sm, "ctor 8B - compact");
//      Test("isZero 8B - compact", sm.isZero(), false);
//    } 
//
//    { // Small values, zeros and empty rows, other constructor
//      nrows = 10; ncols = 10;
//      DenseMat dense(nrows, ncols, 2, true, true, rng_);
//      SparseMat sm(0, ncols);
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
//      DenseMat dense(nrows, ncols, 2, true, true, rng_);
//      SparseMat sm(0, ncols);
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
//      DenseMat dense(10, 10, 10);
//      SparseMat sm(10, 10, dense.begin());
//      Compare(dense, sm, "ctor from empty dense - non compact");
//      Test("isZero 11", sm.isZero(), true); 
//      sm.compact();
//      Compare(dense, sm, "ctor from empty dense - compact");
//      Test("isZero 11 - compact", sm.isZero(), true); 
//    }
//
//    { // Empty, other constructor
//      DenseMat dense(10, 10, 10);
//      SparseMat sm(0, 10);
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
//      DenseMat dense(10, 10, 0);
//      SparseMat sm(10, 10, dense.begin());
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
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sm(nrows, ncols, dense.begin());
//
//	sm.decompact();
//      
//        {
//          std::stringstream str;
//          str << "ctor A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense, sm, str.str().c_str());
//        }
//
//        sm.compact();
//
//        {
//          std::stringstream str;
//          str << "ctor B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          Compare(dense, sm, str.str().c_str());
//        }
//      }
//    }
//
//    /*
//    try {
//      SparseMatrix<size_t, Real> sme1(-1, 0);
//      Test("SparseMatrix::SparseMatrix(Int, Int) exception 2", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix::SparseMatrix(Int, Int) exception 2", true, true);
//    }
//
//    try {
//      SparseMatrix<size_t, Real> sme1(1, -1);
//      Test("SparseMatrix::SparseMatrix(Int, Int) exception 3", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix::SparseMatrix(Int, Int) exception 3", true, true);
//    }
//
//    try {
//      SparseMatrix<size_t, Real> sme1(1, -1);
//      Test("SparseMatrix::SparseMatrix(Int, Int) exception 4", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix::SparseMatrix(Int, Int) exception 4", true, true);
//    }
//
//    std::vector<Real> mat(16, 0);
//    
//    try {
//      SparseMatrix<size_t, Real> sme1(-1, 1, mat.begin());
//      Test("SparseMatrix::SparseMatrix(Int, Int, Iter) exception 1", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix::SparseMatrix(Int, Iter) exception 1", true, true);
//    }
//
//    try {
//      SparseMatrix<size_t, Real> sme1(1, -1, mat.begin());
//      Test("SparseMatrix::SparseMatrix(Int, Int, Iter) exception 2", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix::SparseMatrix(Int, Iter) exception 2", true, true);
//    }
//    */
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_copy()
//  {
//    {
//      SparseMat sm, sm2;
//      DenseMat dense, dense2;
//      sm2.copy(sm);
//      dense2.copy(dense);
//      Compare(dense2, sm2, "SparseMatrix::copy - empty matrix");
//    }
//
//    {
//      SparseMat sm(0,0), sm2;
//      DenseMat dense(0,0), dense2;
//      sm2.copy(sm);
//      dense2.copy(dense);
//      Compare(dense2, sm2, "SparseMatrix::copy - empty matrix 2");
//    }
//
//    {
//      SparseMat sm(5, 4), sm2;
//      DenseMat dense(5, 4), dense2;
//      sm2.copy(sm);
//      dense2.copy(dense);
//      Compare(dense2, sm2, "SparseMatrix::copy - empty matrix 3");
//    }
//
//    {
//      DenseMat dense(5, 4, 2, false, false), dense2;
//      SparseMat sm(5, 4, dense.begin()), sm2;
//      sm2.copy(sm);
//      dense2.copy(dense);
//      Compare(dense2, sm2, "SparseMatrix::copy - 1");
//    }
//
//    {
//      DenseMat dense(5, 4, 2, false, true), dense2;
//      SparseMat sm(5, 4, dense.begin()), sm2;
//      sm2.copy(sm);
//      dense2.copy(dense);
//      Compare(dense2, sm2, "SparseMatrix::copy - 1");
//    }
//
//    {
//      DenseMat dense(5, 4, 2, true, false, rng_), dense2;
//      SparseMat sm(5, 4, dense.begin()), sm2;
//      sm2.copy(sm);
//      dense2.copy(dense);
//      Compare(dense2, sm2, "SparseMatrix::copy - 1");
//    }
//
//    {
//      DenseMat dense(5, 4, 2, true, true, rng_), dense2;
//      SparseMat sm(5, 4, dense.begin()), sm2;
//      sm2.copy(sm);
//      dense2.copy(dense);
//      Compare(dense2, sm2, "SparseMatrix::copy - 1");
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  /**
//   * TC: Dense::toCSR matches SparseMatrix::toCSR (in stress test)
//   * TC: Dense::fromCSR matches SparseMatrix::fromCSR (in stress test)
//   * TC: reading in smaller matrix resizes the sparse matrix correctly
//   * TC: reading in larger matrix resizes the sparse matrix correctly
//   * TC: empty rows are stored correctly in stream
//   * TC: empty rows are read correctly from stream
//   * TC: empty matrix is written and read correctly
//   * TC: values below epsilon are handled correctly in toCSR
//   * TC: values below epsilon are handled correctly in fromCSR
//   * TC: toCSR exception if bad stream
//   * TC: fromCSR exception if bad stream
//   * TC: fromCSR exception if bad 'csr' tag
//   * TC: fromCSR exception if nrows < 0
//   * TC: fromCSR exception if ncols <= 0
//   * TC: fromCSR exception if nnz < 0 or nnz > nrows * ncols
//   * TC: fromCSR exception if nnzr < 0 or nnzr > ncols
//   * TC: fromCSR exception if j < 0 or j >= ncols
//   * TC: stress test
//   * TC: allocate_ exceptions
//   * TC: addRow exceptions
//   * TC: compact exceptions
//   */
//  void SparseMatrixUnitTest::unit_test_csr()
//  {
//    UInt ncols, nrows, zr;
//     
//    { // Empty matrix 
//      // ... is written correctly
//      SparseMat sm(3, 4);
//      std::stringstream buf;
//      sm.toCSR(buf);
//      Test("SparseMatrix::toCSR empty", buf.str() == "sm_csr_1.5 12 3 4 0 0 0 0 ", true);
//    
//      // ... is read correctly
//      SparseMat sm2;
//      sm2.fromCSR(buf);
//      std::stringstream buf2;
//      buf2 << "csr 3 4 0 0 0 0";
//      DenseMat dense;
//      dense.fromCSR(buf2);
//      Compare(dense, sm2, "fromCSR/empty");
//    }     
//
//    { // Is resizing happening correctly?
//      DenseMat dense(3, 4, 2);
//      SparseMat sm(3, 4, dense.begin());   
//      
//      { // When reading in smaller size matrix?
//        std::stringstream buf1, buf2;
//        buf1 << "csr -1 3 3 9 3 0 1 1 2 2 3 3 0 11 1 12 2 13 3 0 21 1 22 2 23";
//        sm.fromCSR(buf1);
//        buf2 << "csr    3 3 9 3 0 1 1 2 2 3 3 0 11 1 12 2 13 3 0 21 1 22 2 23";
//        dense.fromCSR(buf2);
//        Compare(dense, sm, "fromCSR/redim/1");
//      }
//
//      { // When reading in larger size matrix?
//        std::stringstream buf1, buf2;
//        buf1 << "csr -1 4 5 20 "
//          "5 0 1  1 2  2 3  3  4 4  5 "
//          "5 0 11 1 12 2 13 3 14 4 15 "
//          "5 0 21 1 22 2 23 3 24 4 25 "
//          "5 0 31 1 32 2 33 3 34 4 35";
//        sm.fromCSR(buf1);
//        buf2 << "csr    4 5 20 "
//          "5 0 1  1 2  2 3  3  4 4  5 "
//          "5 0 11 1 12 2 13 3 14 4 15 "
//          "5 0 21 1 22 2 23 3 24 4 25 "
//          "5 0 31 1 32 2 33 3 34 4 35";
//        dense.fromCSR(buf2);
//        Compare(dense, sm, "fromCSR/redim/2");
//      }
//
//      { // Empty rows are read in correctly
//        std::stringstream buf1, buf2;
//        buf1 << "csr -1 4 5 15 "
//          "5 0 1  1 2  2 3  3  4 4  5 "
//          "0 "
//          "5 0 21 1 22 2 23 3 24 4 25 "
//          "5 0 31 1 32 2 33 3 34 4 35";
//        sm.fromCSR(buf1);
//        buf2 << "csr    4 5 15 "
//          "5 0 1  1 2  2 3  3  4 4  5 "
//          "0 "
//          "5 0 21 1 22 2 23 3 24 4 25 "
//          "5 0 31 1 32 2 33 3 34 4 35";
//        dense.fromCSR(buf2);
//        Compare(dense, sm, "fromCSR/redim/3");
//      }
//    }
//
//    { // Initialize fromDenseMat then again fromCSR
//      DenseMat dense(3, 4, 2);
//      SparseMat sm(3, 4, dense.begin());
//      std::stringstream buf1;
//      buf1 << "csr -1 3 3 9 3 0 1 1 2 2 3 3 0 11 1 12 2 13 3 0 21 1 22 2 23";
//      sm.fromCSR(buf1);
//    }
//
//    { // ... and vice-versa, fromCSR, followed by fromDense
//      DenseMat dense(3, 4, 2);
//      SparseMat sm(3, 4);
//      std::stringstream buf1;
//      buf1 << "csr -1 3 3 9 3 0 1 1 2 2 3 3 0 11 1 12 2 13 3 0 21 1 22 2 23";
//      sm.fromCSR(buf1);
//      sm.fromDense(3, 4, dense.begin());
//    }
//
//    { // Values below epsilon
//
//      // ... are written correctly (not written)
//      nrows = 128; ncols = 256;
//      UInt nnz = ncols/2;
//      DenseMat dense(nrows, ncols, nnz, true, true, rng_);
//      ITER_2(128, 256)
//        dense.at(i,j) /= 1000;
//      SparseMat sm(nrows, ncols, dense.begin());
//      std::stringstream buf;
//      sm.toCSR(buf);
//      std::string tag; buf >> tag;
//      buf >> nrows >> ncols >> nnz;
//      ITER_1(nrows) {
//        buf >> nnz;
//        UInt j; Real val;
//        ITER_1(nnz) {
//          buf >> j >> val;
//          if (nta::nearlyZero(val))
//            Test("SparseMatrix::toCSR/small values", true, false);
//        }
//      }
//
//      // ... are read correctly
//      std::stringstream buf1;
//      buf1 << "csr -1 3 4 6 "
//	   << "2 0 " << nta::Epsilon/2 << " 1 1 "
//	   << "2 0 " << nta::Epsilon/2 << " 1 " << nta::Epsilon/2 << " "
//	   << "2 0 1 1 1";
//      SparseMat sm2(4, 4);
//      sm2.fromCSR(buf1);
//    }
//
//    { // stress test, matching against Dense::toCSR and Dense::fromCSR
//      TEST_LOOP(M) {
//
//        DenseMat dense3(nrows, ncols, zr);
//        SparseMat sm3(nrows, ncols, dense3.begin());
//     
//        std::stringstream buf;
//        sm3.toCSR(buf);
//        sm3.fromCSR(buf);
//    
//        {  
//          std::stringstream str;
//          str << "toCSR/fromCSR A " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense3, sm3, str.str().c_str());
//        }   
//
//        SparseMat sm4(nrows, ncols);
//        std::stringstream buf1;
//        sm3.toCSR(buf1);
//        sm4.fromCSR(buf1);
//  
//        {
//          std::stringstream str;
//          str << "toCSR/fromCSR B " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense3, sm4, str.str().c_str());
//        }
//
//        sm4.decompact();
//        std::stringstream buf2;
//        sm3.toCSR(buf2);
//        sm4.fromCSR(buf2);
//
//        {  
//          std::stringstream str;
//          str << "toCSR/fromCSR C " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense3, sm4, str.str().c_str());
//        }
//
//        std::stringstream buf3;
//        sm4.toCSR(buf3);
//        sm4.fromCSR(buf3);
//
//        {
//          std::stringstream str;
//          str << "toCSR/fromCSR D " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense3, sm4, str.str().c_str());
//        }
//      }
//    }
//
//    /*
//    // Exceptions
//    SparseMatrix<size_t, Real> sme1(1, 1);
//
//    { 
//      stringstream s1;
//      s1 << "ijv";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix::fromCSR() exception 1", true, false);
//      } catch (std::runtime_error&) {
//        Test("SparseMatrix::fromCSR() exception 1", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr -1 -1";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix::fromCSR() exception 2", true, false);
//      } catch (std::runtime_error&) {
//        Test("SparseMatrix::fromCSR() exception 2", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr -1 1 -1";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix::fromCSR() exception 3", true, false);
//      } catch (std::runtime_error&) {
//        Test("SparseMatrix::fromCSR() exception 3", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr -1 1 0";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix::fromCSR() exception 4", true, false);
//      } catch (std::runtime_error&) {
//        Test("SparseMatrix::fromCSR() exception 4", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr -1 4 3 -1";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix::fromCSR() exception 5", true, false);
//      } catch (std::runtime_error&) {
//        Test("SparseMatrix::fromCSR() exception 5", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr -1 4 3 15";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix::fromCSR() exception 6", true, false);
//      } catch (std::runtime_error&) {
//        Test("SparseMatrix::fromCSR() exception 6", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr -1 2 3 1 5"; 
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix::fromCSR() exception 7", true, false);
//      } catch (std::runtime_error&) {
//        Test("SparseMatrix::fromCSR() exception 7", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr -1 2 3 1 0 1 -1";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix::fromCSR() exception 8", true, false);
//      } catch (std::runtime_error&) {
//        Test("SparseMatrix::fromCSR() exception 8", true, true);
//      }
//    }
//
//    {
//      stringstream s1;
//      s1 << "csr -1 2 3 1 0 1 4";
//      try {
//        sme1.fromCSR(s1);
//        Test("SparseMatrix::fromCSR() exception 9", true, false);
//      } catch (std::runtime_error&) {
//        Test("SparseMatrix::fromCSR() exception 9", true, true);
//      }
//    }
//    */
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_dense()
//  {
//    UInt ncols = 5, nrows = 7, zr = 2;
//    
//    DenseMat dense(nrows, ncols, zr);
//    DenseMat dense2(nrows+1, ncols+1, zr+1);
//   
//    { // fromDense
//      SparseMat sparse(nrows, ncols);
//      sparse.fromDense(nrows, ncols, dense.begin());
//      Compare(dense, sparse, "fromDenseMat 1");
//    }
//    
//    { // fromDense
//      SparseMat sparse(nrows, ncols, dense.begin());
//
//      sparse.fromDense(nrows+1, ncols+1, dense2.begin());
//      Compare(dense2, sparse, "fromDenseMat 2");
//      
//      sparse.decompact();
//      sparse.fromDense(nrows, ncols, dense.begin());
//      Compare(dense, sparse, "fromDenseMat 3");
//      
//      sparse.compact();
//      sparse.fromDense(nrows+1, ncols+1, dense2.begin());
//      Compare(dense2, sparse, "fromDenseMat 4");
//      
//      std::vector<Real> mat((nrows+1)*(ncols+1), 0);
//      
//      sparse.toDense(mat.begin());
//      sparse.fromDense(nrows+1, ncols+1, mat.begin());
//      Compare(dense2, sparse, "toDenseMat 1");
//    }
//  
//    {
//      TEST_LOOP(M) {
//      
//        DenseMat dense3(nrows, ncols, zr);
//        SparseMat sm3(nrows, ncols, dense3.begin());
//        std::vector<Real> mat3(nrows*ncols, 0);
//
//        sm3.toDense(mat3.begin());
//        sm3.fromDense(nrows, ncols, mat3.begin());
//
//        {
//          std::stringstream str;
//          str << "toDense/fromDenseMat A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense3, sm3, str.str().c_str());
//        }
//
//        sm3.compact();
//
//        {
//          std::stringstream str;
//          str << "toDense/fromDenseMat B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          Compare(dense3, sm3, str.str().c_str());
//        }
//      }
//    }
//
//    { // What happens if dense matrix is full?
//      nrows = ncols = 10; zr = 0;
//      DenseMat dense(nrows, ncols, zr);
//      SparseMat sm(nrows, ncols, dense.begin());
//      std::vector<Real> mat3(nrows*ncols, 0);
//    
//      sm.toDense(mat3.begin());
//      sm.fromDense(nrows, ncols, mat3.begin());
//    
//      Compare(dense, sm, "toDense/fromDenseMat from dense");
//    }
//
//    { // What happens if dense matrix is empty?
//      nrows = ncols = 10; zr = 10;
//      DenseMat dense(nrows, ncols, zr);
//      SparseMat sm(nrows, ncols, dense.begin());
//      std::vector<Real> mat3(nrows*ncols, 0);
//    
//      sm.toDense(mat3.begin());
//      sm.fromDense(nrows, ncols, mat3.begin());
//    
//      Compare(dense, sm, "toDense/fromDenseMat from dense");
//    }
//
//    { // What happens if there are empty rows?
//      nrows = ncols = 10; zr = 2;
//      DenseMat dense(nrows, ncols, zr);
//      for (UInt i = 0; i < ncols; ++i) 
//        dense.at(2,i) = dense.at(4,i) = dense.at(9,i) = 0;
//        
//      SparseMat sm(nrows, ncols, dense.begin());
//      std::vector<Real> mat3(nrows*ncols, 0);
//    
//      sm.toDense(mat3.begin());
//      sm.fromDense(nrows, ncols, mat3.begin());
//    
//      Compare(dense, sm, "toDense/fromDenseMat from dense");
//    }
//
//    { // Is resizing happening correctly?
//      DenseMat dense(3, 4, 2);
//      SparseMat sm(3, 4, dense.begin());
//
//      DenseMat dense2(5, 5, 4);
//      sm.fromDense(5, 5, dense2.begin());
//      Compare(dense2, sm, "fromDense/redim/1");
//
//      DenseMat dense3(2, 2, 2);
//      sm.fromDense(2, 2, dense3.begin());
//      Compare(dense3, sm, "fromDense/redim/2");
//
//      DenseMat dense4(10, 10, 8);
//      sm.fromDense(10, 10, dense4.begin());
//      Compare(dense4, sm, "fromDense/redim/3");
//    }
//
//    /*    
//    // Exceptions
//    SparseMatrix<size_t, Real> sme1(1, 1);
//    
//    try {
//      sme1.fromDense(-1, 0, dense.begin());
//      Test("SparseMatrix::fromDense() exception 1", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix::fromDense() exception 1", true, true);
//    }
//
//    try {
//      sme1.fromDense(1, -1, dense.begin());
//      Test("SparseMatrix::fromDense() exception 3", true, false);
//    } catch (std::exception&) {
//      Test("SparseMatrix::fromDense() exception 3", true, true);
//    }
//    */
//  }
//  
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_compact()
//  {
//    UInt ncols, nrows, zr;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    DenseMat dense(nrows, ncols, zr);
//    SparseMat sm4(nrows, ncols, dense.begin());
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
//    SparseMat sm5(nrows, ncols, dense.begin());
//    DenseMat dense2(nrows+1, ncols+1, zr+1);
//    sm5.fromDense(nrows+1, ncols+1, dense2.begin());
//    sm5.compact();
//    Compare(dense2, sm5, "compact 3");
//
//    {
//      TEST_LOOP(M) {
//      
//        DenseMat dense3(nrows, ncols, zr);
//        SparseMat sm3(nrows, ncols, dense3.begin());
//
//        sm3.decompact();
//      
//        {
//          std::stringstream str;
//          str << "compact/decompact A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense3, sm3, str.str().c_str());
//        }
//
//        sm3.compact();
//
//        {
//          std::stringstream str;
//          str << "compact/decompact B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          Compare(dense3, sm3, str.str().c_str());
//        }
//      }
//    }
//
//    {
//      nrows = ncols = 10; zr = 0;
//      DenseMat dense(nrows, ncols, zr);
//      SparseMat sm(nrows, ncols, dense.begin());
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
//  void SparseMatrixUnitTest::unit_test_threshold()
//  {
//    UInt nrows = 7, ncols = 5, zr = 2;
//  
//    if (0) { // Visual tests
//
//      DenseMat dense(nrows, ncols, zr);
//      SparseMat sparse(nrows, ncols, dense.begin());
//
//      cout << "Before thresholding at 50" << endl;
//      cout << sparse << endl;
//      sparse.threshold(50);
//      cout << "After:" << endl;
//      cout << sparse << endl;
//    }
//
//    {
//      SparseMat sm;
//      DenseMat dense;
//      sm.threshold(Real(1.0));
//      dense.threshold(Real(1.0));
//      Compare(dense, sm, "threshold 0A");
//    }
//
//    {
//      SparseMat sm(0, 0);
//      DenseMat dense(0, 0);
//      sm.threshold(Real(1.0));
//      dense.threshold(Real(1.0));
//      Compare(dense, sm, "threshold 0B");
//    }
//
//    {
//      SparseMat sm(nrows, ncols);
//      DenseMat dense(nrows, ncols);
//      sm.threshold(Real(1.0));
//      dense.threshold(Real(1.0));
//      Compare(dense, sm, "threshold 0C");
//    }
//
//    {
//      DenseMat dense(nrows, ncols, zr);
//      for (UInt i = 0; i < nrows; ++i)
//	for (UInt j = 0; j < ncols; ++j)
//	  dense.at(i,j) = rng_->getReal64();
//
//      SparseMat sm4c(nrows, ncols, dense.begin());
//      
//      dense.threshold(Real(.8));
//      sm4c.threshold(Real(.8));
//      Compare(dense, sm4c, "threshold 1");
//      
//      sm4c.decompact();
//      sm4c.compact();
//      dense.threshold(Real(.7));
//      sm4c.threshold(Real(.7));
//      Compare(dense, sm4c, "threshold 2");
//    }
//
//    {
//      TEST_LOOP(M) {
//
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sm(nrows, ncols, dense.begin());
//
//	sm.decompact();
//        dense.threshold(Real(.8));                     
//        sm.threshold(Real(.8));
//      
//        {
//          std::stringstream str;
//          str << "threshold A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense, sm, str.str().c_str());
//        }  
//      
//        sm.compact();
//	dense.threshold(Real(.7));                     
//        sm.threshold(Real(.7));
//   
//        {
//          std::stringstream str;
//          str << "threshold B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          Compare(dense, sm, str.str().c_str());
//        }
//      }  
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_getRow()
//  {
//    UInt nrows = 5, ncols = 7, zr = 3, i = 0, k = 0;
//    
//    if (0) { // Tests for visual inspection
//      DenseMat dense(nrows, ncols, zr);
//      SparseMat sparse(nrows, ncols, dense.begin());
//      cout << sparse << endl;
//      for (i = 0; i != nrows; ++i) {
//	std::vector<Real> dense_row(ncols);
//	sparse.getRowToDense(i, dense_row.begin());
//	cout << dense_row << endl;
//      }
//    }
//
//    {
//      TEST_LOOP(M) {
//        
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sm(nrows, ncols, dense.begin());
//
//        for (i = 0; i < nrows; ++i) {
//          
//          std::stringstream str;
//          str << "getRowToSparseMat A " << nrows << "X" << ncols 
//              << "/" << zr << " " << i;
//  
//          std::vector<UInt> ind; std::vector<Real> nz;
//          sm.getRowToSparse(i, back_inserter(ind), back_inserter(nz));
//          
//          std::vector<Real> d(ncols, 0);
//          for (k = 0; k < ind.size(); ++k)
//            d[ind[k]] = nz[k];
//          
//          CompareVectors(ncols, d.begin(), dense.begin(i), str.str().c_str());
//        }
//      }  
//    }  
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_getCol()
//  {
//    UInt nrows = 5, ncols = 7, zr = 3, i = 0, k = 0;
//    
//    if (0) { // Tests for visual inspection
//      DenseMat dense(nrows, ncols, zr);
//      SparseMat sparse(nrows, ncols, dense.begin());
//      cout << sparse << endl;
//      for (i = 0; i != ncols; ++i) {
//	std::vector<Real> dense_col(nrows);
//	sparse.getColToDense(i, dense_col.begin());
//	cout << dense_col << endl;
//      }
//    }
//
//    {
//      TEST_LOOP(M) {
//        
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sm(nrows, ncols, dense.begin());
//
//        for (i = 0; i < nrows; ++i) {
//          
//          std::stringstream str;
//          str << "getRowToSparseMat A " << nrows << "X" << ncols 
//              << "/" << zr << " " << i;
//  
//          std::vector<UInt> ind; std::vector<Real> nz;
//          sm.getRowToSparse(i, back_inserter(ind), back_inserter(nz));
//          
//          std::vector<Real> d(ncols, 0);
//          for (k = 0; k < ind.size(); ++k)
//            d[ind[k]] = nz[k];
//          
//          CompareVectors(ncols, d.begin(), dense.begin(i), str.str().c_str());
//        }
//      }  
//    }  
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_transpose()
//  {  
//    UInt ncols, nrows, zr;
//
//    {
//       nrows = 8; ncols = 4; zr = ncols - 2;
//       Dense<UInt, double> dense(nrows, ncols, zr, false, true);
//       Dense<UInt, double> dense2(ncols, nrows);
//       SparseMatrix<UInt, double> sm(nrows, ncols, dense.begin());
//       SparseMatrix<UInt, double> sm2(ncols, nrows);
//       dense.transpose(dense2);
//       sm.transpose(sm2);
//       Compare(dense2, sm2, "transpose 1");
//    }
//
//    {    
//      for (nrows = 1, zr = 15; nrows < 256; nrows += 25, zr = ncols/10) {
//        
//        ncols = nrows;
//
//        DenseMat dense(nrows, ncols, zr);
//        DenseMat dense2(ncols, nrows, zr);
//        SparseMat sm(nrows, ncols, dense.begin());
//        SparseMat sm2(ncols, nrows, dense2.begin());
//        
//        {
//          std::stringstream str;
//          str << "transpose A " << nrows << "X" << ncols << "/" << zr;
//          
//          dense.transpose(dense2);
//          sm.transpose(sm2);
//          
//          Compare(dense2, sm2, str.str().c_str());
//        }
//
//        {
//          std::stringstream str;
//          str << "transpose B " << nrows << "X" << ncols << "/" << zr;
//          
//          dense2.transpose(dense);
//          sm2.transpose(sm);
//          
//          Compare(dense, sm, str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_addRowCol()
//  {
//    // addRow, compact
//    UInt nrows = 5, ncols = 7, zr = 3;
//
//    if (0) { // Visual, keep
//      
//      { // Add dense row
//	DenseMat dense(nrows, ncols, zr);
//	SparseMat sparse(nrows, ncols, dense.begin());
//	
//	for (UInt i = 0; i != nrows; ++i) {
//	  std::vector<Real> nz;
//	  dense.getRowToDense(i, back_inserter(nz));
//	  sparse.addRow(nz.begin());
//	}
//	   
//	cout << sparse << endl;
//      }
//
//      { // Add sparse row
//	DenseMat dense(nrows, ncols, zr);
//	SparseMat sparse(nrows, ncols, dense.begin());
//	
//	for (UInt i = 0; i != nrows; ++i) {
//	  std::vector<UInt> ind;   
//	  std::vector<Real> nz;
//	  dense.getRowToSparse(i, back_inserter(ind), back_inserter(nz));
//	  sparse.addRow(ind.begin(), ind.end(), nz.begin());
//	}
//	
//	cout << sparse << endl;
//      }
//
//      { // Add dense col
//	DenseMat dense(nrows, ncols, zr);
//	SparseMat sparse(nrows, ncols, dense.begin());
//	
//	for (UInt i = 0; i != ncols; ++i) {
//	  std::vector<Real> nz;
//	  dense.getColToDense(i, back_inserter(nz));
//	  cout << "Adding: " << nz << endl;
//	  sparse.addCol(nz.begin());
//	}
//	
//	cout << "After adding columns:" << endl;
//	cout << sparse << endl;
//      }
//
//      { // Add sparse col
//	DenseMat dense(nrows, ncols, zr);
//	SparseMat sparse(nrows, ncols, dense.begin());
//	
//	for (UInt i = 0; i != ncols; ++i) {
//	  std::vector<UInt> ind; 
//	  std::vector<Real> nz;
//	  dense.getColToSparse(i, back_inserter(ind), back_inserter(nz));
//	  sparse.addCol(ind.begin(), ind.end(), nz.begin());
//	}
//	
//	cout << sparse << endl;
//      }
//    }
//
//    /*
//    TEST_LOOP(M) {
//    
//      { // Add dense row
//	DenseMat dense(nrows, ncols, zr);
//	SparseMat sparse(nrows, ncols, dense.begin());
//	
//	for (UInt i = 0; i != nrows; ++i) {
//	  std::vector<Real> nz;
//	  dense.getRowToDense(i, back_inserter(nz));
//	  sparse.addRow(nz.begin());
//	}
//	   
//	{
//          std::stringstream str;
//          str << "addRow A " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense, sparse, str.str().c_str());
//        }
//      }
//
//      { // Add sparse row
//	DenseMat dense(nrows, ncols, zr);
//	SparseMat sparse(nrows, ncols, dense.begin());
//	
//	for (UInt i = 0; i != nrows; ++i) {
//	  std::vector<UInt> ind;   
//	  std::vector<Real> nz;
//	  dense.getRowToSparse(i, back_inserter(ind), back_inserter(nz));
//	  sparse.addRow(ind.begin(), ind.end(), nz.begin());
//	}
//	
//	{
//          std::stringstream str;
//          str << "addRow B " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense, sparse, str.str().c_str());
//        }
//      }
//
//      { // Add dense col
//	DenseMat dense(nrows, ncols, zr);
//	SparseMat sparse(nrows, ncols, dense.begin());
//	
//	for (UInt i = 0; i != ncols; ++i) {
//	  std::vector<Real> nz;
//	  dense.getColToDense(i, back_inserter(nz));
//	  sparse.addCol(nz.begin());
//	}
//	
//	{
//          std::stringstream str;
//          str << "addCol A " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense, sparse, str.str().c_str());
//        }
//      }
//
//      { // Add sparse col
//	DenseMat dense(nrows, ncols, zr);
//	SparseMat sparse(nrows, ncols, dense.begin());
//	
//	for (UInt i = 0; i != ncols; ++i) {
//	  std::vector<UInt> ind; 
//	  std::vector<Real> nz;
//	  dense.getColToSparse(i, back_inserter(ind), back_inserter(nz));
//	  sparse.addCol(ind.begin(), ind.end(), nz.begin());
//	}
//
//	{
//          std::stringstream str;
//          str << "addCol B " << nrows << "X" << ncols << "/" << zr;
//          Compare(dense, sparse, str.str().c_str());
//        }
//      }
//    }
//    */
//
//    {
//      TEST_LOOP(M) {
//
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sparse(0, ncols);
//
//        for (UInt i = 0; i < nrows; ++i) {
//          sparse.addRow(dense.begin(i));
//          sparse.compact();
//        }
//      
//        sparse.decompact();
//      
//        {
//          std::stringstream str;
//          str << "addRow C " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense, sparse, str.str().c_str());
//        }
//      
//        sparse.compact();
//
//        {
//          std::stringstream str;
//          str << "addRow D " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          Compare(dense, sparse, str.str().c_str());
//        }
//      }
//    }
//
//    { // Test that negative numbers are handled correctly
//      nrows = 4; ncols = 8; zr = 2;
//      DenseMat dense(nrows, ncols, zr);
//      SparseMat sparse(0, ncols);
//      for (UInt i = 0; i < nrows; ++i)
//        for (UInt j = 0; j < ncols; ++j)
//          dense.at(i,j) *= -1;
//
//      for (UInt i = 0; i < nrows; ++i) {
//        sparse.addRow(dense.begin(i));
//        sparse.compact();
//      }
//
//      {
//        std::stringstream str;
//        str << "addRow w/ negative numbers A " 
//            << nrows << "X" << ncols << "/" << zr
//            << " - compact";
//        Compare(dense, sparse, str.str().c_str());
//      }
//      
//      sparse.decompact();
//
//      {
//        std::stringstream str;
//        str << "addRow w/ negative numbers A " 
//            << nrows << "X" << ncols << "/" << zr
//            << " - non compact";
//        Compare(dense, sparse, str.str().c_str());
//      }
//    }
//    
//    // These tests compiled conditionally, because they are 
//    // based on asserts rather than checks
//
//#ifdef NTA_ASSERTIONS_ON
//
//    /*
//    { // "Dirty" rows tests
//      UInt ncols = 4;
//      SparseMat sm(0, ncols);
//      std::vector<std::pair<UInt, Real> > dirty_col(ncols);
//
//      // Duplicate zeros (assertion)
//      for (UInt i = 0; i < ncols; ++i)
//        dirty_col[i] = make_pair(0, 0);
//      try {
//        sm.addRow(dirty_col.begin(), dirty_col.end());
//        Test("SparseMatrix dirty cols 1", true, false);
//      } catch (std::exception&) {
//        Test("SparseMatrix dirty cols 1", true, true);
//      }
//
//      // Out of order indices (assertion)
//      dirty_col[0].first = 3;
//      try {
//        sm.addRow(dirty_col.begin(), dirty_col.end());
//        Test("SparseMatrix dirty cols 2", true, false);
//      } catch (std::exception&) {
//        Test("SparseMatrix dirty cols 2", true, true);
//      }
//
//      // Indices out of range (assertion)
//      dirty_col[0].first = 9;
//      try {
//        sm.addRow(dirty_col.begin(), dirty_col.end());
//        Test("SparseMatrix dirty cols 3", true, false);
//      } catch (std::exception&) {
//        Test("SparseMatrix dirty cols 3", true, true);
//      }       
//
//      // Passed in zero (assertion)
//      dirty_col[0].second = 0;
//      try {
//        sm.addRow(dirty_col.begin(), dirty_col.end());
//        Test("SparseMatrix dirty cols 4", true, false);
//      } catch (std::exception&) {
//        Test("SparseMatrix dirty cols 4", true, true);
//      }
//    }  
//    */  
//#endif
//  }     
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_resize()
//  {
//    SparseMat sm;
//    DenseMat dense;
//
//    sm.resize(3,3); dense.resize(3,3);
//    ITER_2(3,3) {
//      sm.setNonZero(i,j,Real(i*3+j+1));
//      dense.at(i,j) = Real(i*3+j+1);
//    }
//    Compare(dense, sm, "SparseMatrix::resize() 1");
//
//    sm.resize(1,1);
//    dense.resize(1,1);
//    Compare(dense, sm, "SparseMatrix::resize() 2");
//
//    sm.resize(3,3);
//    dense.resize(3,3);
//    Compare(dense, sm, "SparseMatrix::resize() 3");
//
//    sm.resize(3,4);
//    dense.resize(3,4);
//    ITER_1(3) {
//      sm.setNonZero(i,3,1);
//      dense.at(i,3) = 1;
//    }
//    Compare(dense, sm, "SparseMatrix::resize() 4");
//
//    sm.resize(4,4);
//    dense.resize(4,4);
//    ITER_1(4) {
//      sm.setNonZero(3,i,2);
//      dense.at(3,i) = 2;
//    }
//    Compare(dense, sm, "SparseMatrix::resize() 5");
//
//    sm.resize(5,5);
//    dense.resize(5,5);
//    ITER_1(5) {
//      sm.setNonZero(4,i,3);
//      sm.setNonZero(i,4,4);
//      dense.at(4,i) = 3;
//      dense.at(i,4) = 4;
//    }
//    Compare(dense, sm, "SparseMatrix::resize() 6");
//
//    sm.resize(7,5);
//    dense.resize(7,5);
//    ITER_1(5) {
//      sm.setNonZero(6,i,5);
//      dense.at(6,i) = 5;
//    }      
//    Compare(dense, sm, "SparseMatrix::resize() 7");
//   
//    sm.resize(7, 7);              
//    dense.resize(7,7);          
//    ITER_1(7) {   
//      sm.setNonZero(i,6,6);
//      dense.at(i,6) = 6;   
//    }
//    Compare(dense, sm, "SparseMatrix::resize() 8");
//
//    // Stress test to see the interaction with deleteRows and deleteCols
//    for (UInt i = 0; i < 20; ++i) {
//      sm.resize(rng_->getUInt32(256), rng_->getUInt32(256));
//      vector<UInt> del_r;	
//      for (UInt ii = 0; ii < sm.nRows()/4; ++ii)
//	del_r.push_back(2*ii);
//      sm.deleteRows(del_r.begin(), del_r.end());
//      vector<UInt> del_c;	
//      for (UInt ii = 0; ii < sm.nCols()/4; ++ii)
//	del_c.push_back(2*ii);
//      sm.deleteCols(del_c.begin(), del_c.end());
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_deleteRows()
//  {
//    { // Empty matrix
//      UInt nrows = 3, ncols = 3;
//      
//      { // Empty matrix, empty del
//        SparseMat sm;
//        vector<UInt> del;
//        sm.deleteRows(del.begin(), del.end());
//        Test("SparseMatrix::deleteRows() 1", sm.nRows(), UInt(0));
//      }
//
//      { // Empty matrix, empty del
//        SparseMat sm(0,0);
//        vector<UInt> del;
//        sm.deleteRows(del.begin(), del.end());
//        Test("SparseMatrix::deleteRows() 2", sm.nRows(), UInt(0));
//      }
//
//      { // Empty matrix, empty del
//        SparseMat sm(nrows, ncols);
//        vector<UInt> del;
//        sm.deleteRows(del.begin(), del.end());
//        Test("SparseMatrix::deleteRows() 3", sm.nRows(), UInt(nrows));
//      }
//
//      { // Empty matrix, 1 del
//        SparseMat sm(nrows, ncols);
//        vector<UInt> del(1); del[0] = 0;
//        sm.deleteRows(del.begin(), del.end());
//        Test("SparseMatrix::deleteRows() 4", sm.nRows(), UInt(2));
//      }
//
//      { // Empty matrix, many dels
//        SparseMat sm(nrows, ncols);
//        vector<UInt> del(2); del[0] = 0; del[1] = 2;
//        sm.deleteRows(del.begin(), del.end());
//        Test("SparseMatrix::deleteRows() 5", sm.nRows(), UInt(1));
//      }
//    } // End empty matrix
//
//    { // matrix with only 1 row
//      { // 1 row, 1 del
//	SparseMat sm(0, 3);
//	vector<UInt> del(1); del[0] = 0;
//	std::vector<Real> v(3); v[0] = 1.5; v[1] = 2.5; v[2] = 3.5;
//
//	sm.addRow(v.begin());
//	sm.deleteRows(del.begin(), del.end());
//	Test("SparseMatrix::deleteRows() 1 row A", sm.nRows(), UInt(0));
//
//	// Test that it is harmless to delete an empty matrix
//	sm.deleteRows(del.begin(), del.end());
//	Test("SparseMatrix::deleteRows() 1 row B", sm.nRows(), UInt(0));
//
//	sm.addRow(v.begin());
//	sm.deleteRows(del.begin(), del.end());
//	Test("SparseMatrix::deleteRows() 1 row C", sm.nRows(), UInt(0));
//
//	// Again, test that it is harmless to delete an empty matrix
//	sm.deleteRows(del.begin(), del.end());
//	Test("SparseMatrix::deleteRows() 1 row D", sm.nRows(), UInt(0));
//      }
//
//      { // PLG-68: was failing when adding again because 
//	// deleteRows was not updating nrows_max_ properly
//	SparseMatrix<size_t, double> tam;
//	vector<double> x(4), del(1, 0);    
//	x[0] = .5; x[1] = .75; x[2] = 1.0; x[3] = 1.25;
//	
//	tam.resize(1, 4);
//	tam.elementRowApply(0, std::plus<double>(), x.begin());
//	tam.deleteRows(del.begin(), del.end());
//	
//	tam.resize(1, 4);
//	tam.elementRowApply(0, std::plus<double>(), x.begin());
//      }
//    }
//
//    {
//      UInt nrows, ncols, zr;
//
//      TEST_LOOP(M) {
//
//        DenseMat dense(nrows, ncols, zr);   
//   
//        { // Empty del
//          SparseMat sm(nrows, ncols, dense.begin());
//          vector<UInt> del;
//          sm.deleteRows(del.begin(), del.end());
//          Test("SparseMatrix::deleteRows() 6A", sm.nRows(), nrows);
//        }
//
//        { // Rows of all zeros 1
//          if (nrows > 2) {
//            DenseMat dense2(nrows, ncols, zr);
//            ITER_1(nrows) {
//              if (i % 2 == 0) {
//                for (UInt j = 0; j < ncols; ++j)
//                  dense2.at(i,j) = 0;
//              }
//            }
//            SparseMat sm(nrows, ncols, dense2.begin());
//            vector<UInt> del;
//            for (UInt i = 2; i < nrows-2; i += 2)    
//              del.push_back(i);
//            sm.deleteRows(del.begin(), del.end());
//            dense2.deleteRows(del.begin(), del.end());
//            Compare(dense2, sm, "SparseMatrix::deleteRows() 6B");
//          }
//        }
//
//        { // Rows of all zeros 2
//          if (nrows > 2) {
//            DenseMat dense2(nrows, ncols, zr);
//            ITER_1(nrows) {
//              if (i % 2 == 0) {
//                for (UInt j = 0; j < ncols; ++j)
//                  dense2.at(i,j) = 0;
//              }
//            }
//            SparseMat sm(nrows, ncols, dense2.begin());
//            vector<UInt> del;
//            for (UInt i = 1; i < nrows-2; i += 2)    
//              del.push_back(i);
//            sm.deleteRows(del.begin(), del.end());
//            dense2.deleteRows(del.begin(), del.end());
//            Compare(dense2, sm, "SparseMatrix::deleteRows() 6C");
//          }
//        }
//
//        { // Many dels contiguous
//          if (nrows > 2) {
//            SparseMat sm(nrows, ncols, dense.begin());
//            DenseMat dense2(nrows, ncols, zr);
//            vector<UInt> del;
//            for (UInt i = 2; i < nrows-2; ++i)    
//              del.push_back(i);
//            sm.deleteRows(del.begin(), del.end());
//            dense2.deleteRows(del.begin(), del.end());
//            Compare(dense2, sm, "SparseMatrix::deleteRows() 6D");
//          }
//        }
//
//        { // Make sure we stop at the end of the dels!
//          if (nrows > 2) {
//            SparseMat sm(nrows, ncols, dense.begin());
//            DenseMat dense2(nrows, ncols, zr);
//            UInt* del = new UInt[nrows-1];
//	          for (UInt i = 0; i < nrows-1; ++i)    
//              del[i] = i + 1;
//	          sm.deleteRows(del, del + nrows-2);
//	          dense2.deleteRows(del, del + nrows-2);
//	          Compare(dense2, sm, "SparseMatrix::deleteRows() 6E");
//            delete [] del;
//	        }
//        }
//
//        { // Many dels discontiguous
//          SparseMat sm(nrows, ncols, dense.begin());
//          DenseMat dense2(nrows, ncols, zr);
//          vector<UInt> del;
//          for (UInt i = 0; i < nrows; i += 2)
//            del.push_back(i);
//          sm.deleteRows(del.begin(), del.end());
//          dense2.deleteRows(del.begin(), del.end());
//          Compare(dense2, sm, "SparseMatrix::deleteRows() 7");
//        }
//
//        { // All rows
//          SparseMat sm(nrows, ncols, dense.begin());
//          vector<UInt> del; 
//          for (UInt i = 0; i < nrows; ++i)
//            del.push_back(i);
//          sm.deleteRows(del.begin(), del.end());
//          Test("SparseMatrix::deleteRows() 8", sm.nRows(), UInt(0));
//        }
//
//	/*
//        { // More than all rows => exception in assert mode
//          SparseMat sm(nrows, ncols, dense.begin());
//          vector<UInt> del; 
//          for (UInt i = 0; i < 2*nrows; ++i)
//            del.push_back(i);
//          sm.deleteRows(del.begin(), del.end());
//          Test("SparseMatrix::deleteRows() 9", sm.nRows(), UInt(0));
//        }
//	*/
//
//        { // Several dels in a row till empty
//          SparseMat sm(nrows, ncols, dense.begin());
//          for (UInt i = 0; i < nrows; ++i) {
//            vector<UInt> del(1); del[0] = 0;
//            sm.deleteRows(del.begin(), del.end());
//            Test("SparseMatrix::deleteRows() 10", sm.nRows(), UInt(nrows-i-1));
//          }
//        }
//
//        { // deleteRows and re-resize it
//          SparseMat sm(nrows, ncols, dense.begin());
//          vector<UInt> del(1); del[0] = nrows-1;
//          sm.deleteRows(del.begin(), del.end());
//          sm.resize(nrows, ncols);
//          Test("SparseMatrix::deleteRows() 11", sm.nRows(), UInt(nrows));
//        }
//      }
//    }
//  }
//   
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_deleteCols()
//  {    
//    { // Empty matrix
//      UInt nrows = 3, ncols = 3;
//      
//      { // Empty matrix, empty del
//        SparseMat sm(nrows, ncols);
//        vector<UInt> del;
//        sm.deleteCols(del.begin(), del.end());
//        Test("SparseMatrix::deleteCols() 1", sm.nCols(), UInt(3));
//      }     
//
//      { // Empty matrix, 1 del
//        SparseMat sm(nrows, ncols);
//        vector<UInt> del(1); del[0] = 0;
//        sm.deleteCols(del.begin(), del.end());
//        Test("SparseMatrix::deleteCols() 2", sm.nCols(), UInt(2));
//      }        
//                                                    
//      { // Empty matrix, many dels
//        SparseMat sm(nrows, ncols);
//        vector<UInt> del(2); del[0] = 0; del[1] = 2;
//        sm.deleteCols(del.begin(), del.end());
//        Test("SparseMatrix::deleteCols() 3", sm.nCols(), UInt(1));
//      }
//    } // End empty matrix  
//
//    { // For visual inspection
//      UInt nrows = 3, ncols = 5;
//      DenseMat dense(nrows, ncols, 2);
//      SparseMat sm(nrows, ncols, dense.begin());      
//      //cout << sm << endl;
//      vector<UInt> del; del.push_back(0);
//      sm.deleteCols(del.begin(), del.end());
//      //cout << sm << endl;
//      sm.deleteCols(del.begin(), del.end());
//      //cout << sm << endl;
//    }   
//
//    { // deleteCols on matrix of all-zeros
//      SparseMat sm(7, 3);
//      vector<Real> row(3, 0);
//      for (UInt i = 0; i < 7; ++i)
//	sm.addRow(row.begin());
//      //cout << sm << endl << endl;
//      vector<UInt> del(1, 0);
//      sm.deleteCols(del.begin(), del.end());
//      //cout << sm << endl;
//    }
//
//    {
//      UInt nrows, ncols, zr;   
//      
//      TEST_LOOP(M) {
//
//        DenseMat dense(nrows, ncols, zr);   
//   
//        { // Empty del
//          SparseMat sm(nrows, ncols, dense.begin());
//          vector<UInt> del;
//          sm.deleteCols(del.begin(), del.end());
//          Test("SparseMatrix::deleteCols() 4", sm.nCols(), ncols);
//        }
//
//        { // Many dels contiguous
//          SparseMat sm(nrows, ncols, dense.begin());
//          DenseMat dense2(nrows, ncols, zr);
//          vector<UInt> del;
//          if (ncols > 2) {
//            for (UInt i = 2; i < ncols-2; ++i)    
//              del.push_back(i);
//            sm.deleteCols(del.begin(), del.end());
//            dense2.deleteCols(del.begin(), del.end());
//            Compare(dense2, sm, "SparseMatrix::deleteCols() 6");
//          }
//        }
//        
//        { // Many dels discontiguous
//          SparseMat sm(nrows, ncols, dense.begin());
//          DenseMat dense2(nrows, ncols, zr);
//          vector<UInt> del;
//          for (UInt i = 0; i < ncols; i += 2)
//            del.push_back(i);
//          sm.deleteCols(del.begin(), del.end());
//          dense2.deleteCols(del.begin(), del.end());
//          Compare(dense2, sm, "SparseMatrix::deleteCols() 7");
//        }
//
//        { // All rows
//          SparseMat sm(nrows, ncols, dense.begin());
//          vector<UInt> del; 
//          for (UInt i = 0; i < ncols; ++i)
//            del.push_back(i);
//          sm.deleteCols(del.begin(), del.end());
//          Test("SparseMatrix::deleteCols() 8", sm.nCols(), UInt(0));
//        }
//
//        { // More than all rows => exception in assert mode
//          /*
//          SparseMat sm(nrows, ncols, dense.begin());
//          vector<UInt> del; 
//          for (UInt i = 0; i < 2*ncols; ++i)
//            del.push_back(i);
//          sm.deleteCols(del.begin(), del.end());
//          Test("SparseMatrix::deleteCols() 9", sm.nCols(), UInt(0));
//          */
//        }
//
//        { // Several dels in a row till empty
//          SparseMat sm(nrows, ncols, dense.begin());
//          for (UInt i = 0; i < ncols; ++i) {
//            vector<UInt> del(1); del[0] = 0;
//            sm.deleteCols(del.begin(), del.end());
//            Test("SparseMatrix::deleteCols() 10", sm.nCols(), UInt(ncols-i-1));
//          }
//        }
//
//        { // deleteCols and re-resize it
//          SparseMat sm(nrows, ncols, dense.begin());
//          vector<UInt> del(1); del[0] = ncols-1;
//          sm.deleteCols(del.begin(), del.end());
//          sm.resize(nrows, ncols);
//          Test("SparseMatrix::deleteCols() 11", sm.nCols(), UInt(ncols));
//        }
//      }
//    } 
//  }
//  
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_set()
//  {     
//    UInt nrows, ncols, nnzr;
//
//    if (0) { // Visual tests
//
//      // setZero
//      nrows = 5; ncols = 7; nnzr = 3;
//      DenseMat dense(nrows, ncols, nnzr);
//      SparseMat sparse(nrows, ncols, dense.begin());
//      
//      cout << "Initial matrix" << endl;
//      cout << sparse << endl;
//      
//      cout << endl << "Setting all elements to zero one by one" << endl;
//      ITER_2(nrows, ncols) 
//	sparse.setZero(i, j);
//      cout << "After:" << endl << sparse << endl;
//
//      // setNonZero
//      cout << endl << "Setting all elements one by one to:" << endl;
//      cout << dense << endl;
//      ITER_2(nrows, ncols) {
//	sparse.setNonZero(i, j, dense.at(i,j)+1);
//	dense.at(i,j) = dense.at(i,j) + 1;
//      }
//      cout << "After:" << endl << sparse << endl;
//
//      // set
//      cout << endl << "Setting all elements" << endl;
//      ITER_2(nrows, ncols) {
//	Real val = (Real) ((i+j) % 5); 
//	sparse.set(i, j, val);
//	dense.at(i,j) = val;
//      }
//      cout << "After:" << endl << sparse << endl;
//      cout << "Should be:" << endl << dense << endl;
//
//    } // End visual tests
//    
//    // Automated tests for set(i,j,val), which exercises both 
//    // setNonZero and setToZero
//    for (nrows = 1; nrows < 64; nrows += 3)
//      for (ncols = 1; ncols < 64; ncols += 3)
//        {      
//          SparseMat sm(nrows, ncols);
//          DenseMat dense(nrows, ncols);   
//
//          ITER_2(nrows, ncols) {
//	    Real val = Real((i*ncols+j+1)%5);
//            sm.set(i, j, val);
//            dense.at(i, j) = val;
//          }
//          bool correct = true;
//          ITER_2(nrows, ncols) {  
//	    Real val = Real((i*ncols+j+1)%5);
//            if (sm.get(i, j) != val)
//              correct = false;
//	  }
//          Test("SparseMatrix set/get 1", correct, true);
//
//          ITER_1(nrows) {
//            dense.at(i, 0) = Real(i+1);
//            sm.set(i, 0, Real(i+1));
//          }
//          Compare(dense, sm, "SparseMatrix set/get 2");
//
//          ITER_1(ncols) {
//            dense.at(0, i) = Real(i+1);
//            sm.set(0, i, Real(i+1));
//          }
//          Compare(dense, sm, "SparseMatrix set/get 3");
//
//          sm.set(nrows-1, ncols-1, 1);
//          dense.at(nrows-1, ncols-1) = 1;
//          Compare(dense, sm, "SparseMatrix set/get 4");
//          sm.set(nrows-1, ncols-1, 2);
//          dense.at(nrows-1, ncols-1) = 2;
//          Compare(dense, sm, "SparseMatrix set/get 5");
//
//          for (UInt k = 0; k != 20; ++k) {
//            UInt i = rng_->getUInt32(nrows);
//            UInt j = rng_->getUInt32(ncols);
//            Real val = Real(1+rng_->getUInt32());
//            sm.set(i, j, Real(val));
//            Test("SparseMatrix set/get 7", sm.get(i, j), val);
//          }
//        }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_setRowColToZero()
//  {
//    UInt nrows, ncols, zr;
//
//    if (0) { // Visual tests
//
//      // setRowToZero
//      nrows = 5; ncols = 7; zr = 3;
//      DenseMat dense(nrows, ncols, zr);
//      SparseMat sparse(nrows, ncols, dense.begin());
//      
//      cout << "Initial matrix" << endl;
//      cout << sparse << endl;
//      
//      cout << endl << "Setting all rows to zero" << endl;
//      for (UInt i = 0; i != nrows; ++i) {
//	cout << "isRowZero(" << i << ")= "
//	     << (sparse.isRowZero(i) ? "YES" : "NO") 
//	     << endl;
//	sparse.setRowToZero(i);
//	cout << "Zeroing row " << i << ":" << endl 
//	     << sparse << endl;
//	cout << "isRowZero(" << i << ")= "
//	     << (sparse.isRowZero(i) ? "YES" : "NO") 
//	     << endl;
//	cout << endl;
//      }
//
//      // setColToZero
//      cout << endl << "Setting all columns to zero - 1" << endl;
//      ITER_2(nrows, ncols) 
//	sparse.set(i, j, dense.at(i,j));
//      cout << "Initially: " << endl << sparse << endl;
//      for (UInt j = 0; j != ncols; ++j) {
//	cout << "isColZero(" << j << ")= "
//	     << (sparse.isColZero(j) ? "YES" : "NO") 
//	     << endl;
//	sparse.setColToZero(j);
//	cout << "Zeroing column " << j << ":" << endl 
//	     << sparse << endl;
//	cout << "isColZero(" << j << ")= "
//	     << (sparse.isColZero(j) ? "YES" : "NO") 
//	     << endl;
//	cout << endl;   
//      }
//      
//      // Again, with a dense matrix, so we can see what happens 
//      // to the first and last columns
//      cout << endl << "Setting all columns to zero - 2" << endl;
//      ITER_2(nrows, ncols)
//	sparse.set(i,j,(Real)(i+j));
//      cout << "Initially: " << endl << sparse << endl;
//      for (UInt j = 0; j != ncols; ++j) {
//	cout << "isColZero(" << j << ")= "
//	     << (sparse.isColZero(j) ? "YES" : "NO") 
//	     << endl;
//	sparse.setColToZero(j);
//	cout << "Zeroing column " << j << ":" << endl 
//	     << sparse << endl;
//	cout << "isColZero(" << j << ")= "
//	     << (sparse.isColZero(j) ? "YES" : "NO") 
//	     << endl;
//	cout << endl;
//      }
//    } // End visual tests
//    
//    // Automated tests
//    for (nrows = 0; nrows < 16; nrows += 3)
//      for (ncols = 0; ncols < 16; ncols += 3)
//	for (zr = 0; zr < 16; zr += 3) 
//	  {
//	    { // compact - remove rows
//	      DenseMat dense(nrows, ncols, zr);
//	      SparseMat sparse(nrows, ncols, dense.begin());
//	
//	      for (UInt i = 0; i != nrows; ++i) {
//		sparse.setRowToZero(i);
//		dense.setRowToZero(i);
//		Compare(dense, sparse, "SparseMatrix setRowToZero 1");
//	      }
//	    }
//      
//	    { // decompact - remove rows
//	      DenseMat dense(nrows, ncols, zr);
//	      SparseMat sparse(nrows, ncols, dense.begin());
//	      sparse.decompact();
//
//	      for (UInt i = 0; i != nrows; ++i) {
//		sparse.setRowToZero(i);
//		dense.setRowToZero(i);
//		Compare(dense, sparse, "SparseMatrix setRowToZero 2");
//	      }
//	    }
//
//	    { // compact - remove columns
//	      DenseMat dense(nrows, ncols, zr);
//	      SparseMat sparse(nrows, ncols, dense.begin());
//
//	      for (UInt j = 0; j != ncols; ++j) {
//		sparse.setColToZero(j);
//		dense.setColToZero(j);
//		Compare(dense, sparse, "SparseMatrix setColToZero 1");
//	      }
//	    }
//        
//	    { // decompact - remove columns
//	      DenseMat dense(nrows, ncols, zr);
//	      SparseMat sparse(nrows, ncols, dense.begin());
// 
//	      for (UInt j = 0; j != ncols; ++j) {
//		sparse.setColToZero(j);
//		dense.setColToZero(j);
//		Compare(dense, sparse, "SparseMatrix setColToZero 2");
//	      }
//	    }
//	  }
//  }
// 
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_vecMaxProd()
//  {     
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    DenseMat dense(nrows, ncols, zr);
//
//    std::vector<Real> x(ncols), y(nrows, 0), yref(nrows, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = Real(i);
//
//    dense.vecMaxProd(x.begin(), yref.begin());
//
//    SparseMat smnc(nrows, ncols, dense.begin());
//    smnc.decompact();
//    smnc.vecMaxProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecMaxProd non compact 1");
//
//    smnc.compact();
//    std::fill(y.begin(), y.end(), Real(0));
//    smnc.vecMaxProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecMaxProd compact 1");
//
//    SparseMat smc(nrows, ncols, dense.begin());
//    std::fill(y.begin(), y.end(), Real(0));
//    smc.vecMaxProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "vecMaxProd compact 2");
//
//    {
//      TEST_LOOP(M) {
//
//        Dense<UInt, double> dense2(nrows, ncols, zr);
//        SparseMatrix<UInt, double> sm2(nrows, ncols, dense2.begin());
//
//        std::vector<double> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        dense2.vecMaxProd(x2.begin(), yref2.begin());
//        sm2.vecMaxProd(x2.begin(), y2.begin());
//        {
//          std::stringstream str;
//          str << "vecMaxProd A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//
//        sm2.compact();
//        std::fill(y2.begin(), y2.end(), Real(0));
//        sm2.vecMaxProd(x2.begin(), y2.begin());
//        {
//          std::stringstream str;
//          str << "vecMaxProd B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_vecProd()
//  {      
//    UInt ncols = 5, nrows = 7, zr = 2;
//   
//    DenseMat dense(nrows, ncols, zr);
//          
//    std::vector<Real> x(ncols), y(nrows, 0), yref(nrows, 0);
//    for (UInt i = 0; i < ncols; ++i)
//      x[i] = Real(i);
//
//    dense.rightVecProd(x.begin(), yref.begin());
//
//    SparseMat smnc(nrows, ncols, dense.begin());
//    smnc.decompact();
//    smnc.rightVecProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "rightVecProd non compact 1");
//
//    smnc.compact();
//    std::fill(y.begin(), y.end(), Real(0));
//    smnc.rightVecProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "rightVecProd compact 1");
//
//    SparseMat smc(nrows, ncols, dense.begin());
//    std::fill(y.begin(), y.end(), Real(0));
//    smc.rightVecProd(x.begin(), y.begin());
//    CompareVectors(nrows, y.begin(), yref.begin(), "rightVecProd compact 2");
//
//    {
//      TEST_LOOP(M) {
//
//        Dense<UInt, double> dense2(nrows, ncols, zr);
//        SparseMatrix<UInt, double> sm2(nrows, ncols, dense2.begin());
//
//        std::vector<double> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (UInt i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        dense2.rightVecProd(x2.begin(), yref2.begin());
//        sm2.rightVecProd(x2.begin(), y2.begin());
//        {
//          std::stringstream str;
//          str << "rightVecProd A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//
//        sm2.compact();
//        std::fill(y2.begin(), y2.end(), Real(0));
//        sm2.rightVecProd(x2.begin(), y2.begin());
//        {
//          std::stringstream str;
//          str << "rightVecProd B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_axby()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    DenseMat dense(nrows, ncols, zr);
//    SparseMat sm4c(nrows, ncols, dense.begin());
//
//    std::vector<Real> x(ncols, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = Real(20*i + 1);
//
//    { // compact, b = 0
//      dense.axby(3, .5, 0, x.begin());
//      sm4c.axby(3, .5, 0, x.begin());
//      Compare(dense, sm4c, "axby, b = 0");
//    }
//
//    { // compact, a = 0, with reallocation
//      dense.axby(2, 0, .5, x.begin());
//      sm4c.axby(2, 0, .5, x.begin());
//      Compare(dense, sm4c, "axby, a = 0 /1");
//    }
//
//    { // compact, a = 0, without reallocation
//      dense.axby(3, 0, .5, x.begin());
//      sm4c.axby(3, 0, .5, x.begin());
//      Compare(dense, sm4c, "axby, a = 0 /2");
//    }
//
//    { // compact, a != 0,  b != 0, without reallocation
//      dense.axby(3, .5, .5, x.begin());
//      sm4c.axby(3, .5, .5, x.begin());
//      Compare(dense, sm4c, "axby, a, b != 0 /1");
//    }
//
//    { // compact, a != 0,  b != 0, with reallocation
//      dense.axby(4, .5, .5, x.begin());
//      sm4c.axby(4, .5, .5, x.begin());
//      Compare(dense, sm4c, "axby, a, b != 0 /2");
//    }
//
//    {
//      TEST_LOOP(M) {
//
//        Dense<UInt, double> dense2(nrows, ncols, zr);
//        SparseMatrix<UInt, double> sm2(nrows, ncols, dense2.begin());
//
//        std::vector<double> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        for (i = 0; i < nrows; i += 5) {
//
//          dense2.axby(i, (Real).6, (Real).4, x2.begin());
//          sm2.axby(i, (Real).6, (Real).4, x2.begin());
//          {
//            std::stringstream str;
//            str << "axby " << nrows << "X" << ncols << "/" << zr
//                << " - non compact";
//            Compare(dense2, sm2, str.str().c_str());
//          }
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_axby_3()
//  {
//    UInt ncols, nrows, zr, i;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    DenseMat dense(nrows, ncols, zr);
//    SparseMat sm4c(nrows, ncols, dense.begin());
//
//    std::vector<Real> x(ncols, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = i % 2 == 0 ? Real(20*i + 1) : Real(0);
//
//    { // compact, b = 0
//      dense.axby(.5, 0, x.begin());
//      sm4c.axby(.5, 0, x.begin());
//      Compare(dense, sm4c, "axby, b = 0");
//    }
//
//    { // compact, a = 0, with reallocation
//      dense.axby(0, .5, x.begin());
//      sm4c.axby(0, .5, x.begin());
//      Compare(dense, sm4c, "axby, a = 0 /1");
//    }
//
//    { // compact, a = 0, without reallocation
//      dense.axby(0, .5, x.begin());
//      sm4c.axby(0, .5, x.begin());
//      Compare(dense, sm4c, "axby, a = 0 /2");
//    }
//
//    { // compact, a != 0,  b != 0, without reallocation
//      dense.axby(.5, .5, x.begin());
//      sm4c.axby(.5, .5, x.begin());
//      Compare(dense, sm4c, "axby, a, b != 0 /1");
//    }
//
//    { // compact, a != 0,  b != 0, with reallocation
//      dense.axby(.5, .5, x.begin());
//      sm4c.axby(.5, .5, x.begin());
//      Compare(dense, sm4c, "axby, a, b != 0 /2");
//    }
//
//    {
//      TEST_LOOP(M) {
//
//        Dense<UInt, double> dense2(nrows, ncols, zr);
//        SparseMatrix<UInt, double> sm2(nrows, ncols, dense2.begin());
//
//        std::vector<double> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = i % 2 == 0 ? Real(i) : Real(0);
//
//        dense2.axby((Real).6, (Real).4, x2.begin());
//        sm2.axby((Real).6, (Real).4, x2.begin());
//        {
//          std::stringstream str;
//          str << "axby " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense2, sm2, str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_rowMax()
//  {
//    UInt ncols, nrows, zr, i;
//
//    {
//      TEST_LOOP(M) {
//
//        DenseMat dense2(nrows, ncols, zr);
//        SparseMat sm2(nrows, ncols, dense2.begin());
//
//        std::vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        dense2.threshold(Real(1./nrows));
//        dense2.xMaxAtNonZero(x2.begin(), y2.begin());
//        sm2.threshold(Real(1./nrows));
//        sm2.vecMaxAtNZ(x2.begin(), yref2.begin());
//      
//        {
//          std::stringstream str;
//          str << "xMaxAtNonZero A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      
//        sm2.compact();
//        dense2.xMaxAtNonZero(x2.begin(), y2.begin());
//        sm2.vecMaxAtNZ(x2.begin(), yref2.begin());
//        {
//          std::stringstream str;
//          str << "xMaxAtNonZero B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_maxima()
//  {
//    UInt ncols, nrows, zr;
//  
//    {
//      TEST_LOOP(M) {
//
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sparse(nrows, ncols, dense.begin());
//        
//        std::vector<std::pair<UInt, Real> > 
//          rowMaxDense(nrows), rowMaxSparse(nrows),
//          colMaxDense(ncols), colMaxSparse(ncols);
//
//        dense.rowMax(rowMaxDense.begin());
//        dense.colMax(colMaxDense.begin());
//        sparse.rowMax(rowMaxSparse.begin());
//        sparse.colMax(colMaxSparse.begin());
//
//        {
//          std::stringstream str;
//          str << "rowMax " << nrows << "X" << ncols << "/" << zr;
//          Compare(rowMaxDense, rowMaxSparse, str.str().c_str());
//        }
//        
//        {
//          std::stringstream str;
//          str << "colMax " << nrows << "X" << ncols << "/" << zr;
//          Compare(colMaxDense, colMaxSparse, str.str().c_str());
//        }
//      }       
//    }
//  }       
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_normalize()
//  {
//    UInt nrows = 7, ncols = 5, zr = 2;
//         
//    DenseMat dense(nrows, ncols, zr);
//    SparseMat sparse(nrows, ncols, dense.begin());
//         
//    if (0) { // Visual tests
//
//      cout << "Before normalizing rows: " << endl;
//      cout << sparse << endl;   
//      dense.normalizeRows();   
//      sparse.normalizeRows();
//      cout << "After normalizing rows: " << endl;
//      cout << "Sparse: " << endl << sparse << endl;
//      cout << "Dense: " << endl << dense << endl;
//
//      cout << "Before normalizing columns: " << endl;
//      cout << sparse << endl;
//      dense.normalizeCols();
//      sparse.normalizeCols();
//      cout << "After normalizing columns: " << endl;
//      cout << "Sparse: " << endl << sparse << endl;
//      cout << "Dense: " << endl << dense << endl;
//      
//    }
//
//    if (1) // Automated tests
//    {
//      TEST_LOOP(M) {
//
//        Dense<UInt, double> dense2(nrows, ncols, zr);
//        SparseMatrix<UInt, double> sm2(nrows, ncols, dense2.begin());
//    
//        dense2.threshold(double(1./nrows));
//        dense2.normalizeRows(true);
//        sm2.decompact();
//        sm2.threshold(double(1./nrows));
//        sm2.normalizeRows(true);
//      
//        {
//          std::stringstream str;
//          str << "normalizeRows A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          Compare(dense2, sm2, str.str().c_str());
//        }
//      
//        dense2.normalizeRows(true);
//        sm2.compact();
//        sm2.normalizeRows(true);
//        
//        {
//          std::stringstream str;
//          str << "normalizeRows B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          Compare(dense2, sm2, str.str().c_str());
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_rowProd()
//  {
//    UInt ncols, nrows, zr, i;
//
//    {
//      TEST_LOOP(M) {
//
//        Dense<UInt, double> dense2(nrows, ncols, zr);
//        SparseMatrix<UInt, double> sm2(nrows, ncols, dense2.begin());
//
//        std::vector<double> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = double(i)/double(ncols);
//
//        sm2.decompact();
//        dense2.threshold(1./double(nrows));
//        dense2.rowProd(x2.begin(), y2.begin());
//        sm2.threshold(1./double(nrows));
//        sm2.rightVecProdAtNZ(x2.begin(), yref2.begin());
//      
//        {
//          std::stringstream str;
//          str << "rowProd A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }      
//               
//        sm2.compact();
//        dense2.rowProd(x2.begin(), y2.begin());
//        sm2.rightVecProdAtNZ(x2.begin(), yref2.begin());
//        {
//          std::stringstream str;
//          str << "rowProd B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y2.begin(), yref2.begin(), str.str().c_str());
//        }
//      }
//    }
//  }   
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_lerp()
//  {
//    UInt ncols, nrows, zr;
//    nrows = 5; ncols = 7; zr = 4;
//
//    {
//      DenseMat dense(nrows, ncols, zr);
//      DenseMat denseB(nrows, ncols, zr);
//      for (UInt i = 0; i < nrows; ++i)
//        for (UInt j = 0; j < ncols; ++j)
//          denseB.at(i,j) += 2;
//      
//      SparseMat sm(nrows, ncols, dense.begin());
//      SparseMat smB(nrows, ncols, denseB.begin());
//      
//      Real a, b;
//      a = b = 1;            
//
//      dense.lerp(a, b, denseB);   
//      sm.lerp(a, b, smB);
//
//      std::stringstream str;
//      str << "lerp " << nrows << "X" << ncols << "/" << zr
//          << " " << a << " " << b;
//      Compare(dense, sm, str.str().c_str());
//    }
//
//    {
//      TEST_LOOP(M) {
//        
//        DenseMat dense(nrows, ncols, zr);
//        DenseMat denseB(nrows, ncols, zr);
//        for (UInt i = 0; i < nrows; ++i)
//          for (UInt j = 0; j < ncols; ++j)
//            denseB.at(i,j) += 2;                  
//        
//        SparseMat sm(nrows, ncols, dense.begin());
//        SparseMat smB(nrows, ncols, denseB.begin());
//        
//        for (Real a = -2; a < 2; a += 1) {
//          for (Real b = -2; b < 2; b += 1) {
//            dense.lerp(a, b, denseB);
//            sm.lerp(a, b, smB);
//            std::stringstream str;
//            str << "lerp " << nrows << "X" << ncols << "/" << zr
//                << " " << a << " " << b;
//            Compare(dense, sm, str.str().c_str());
//          }
//        }    
//      }
//    }
//
//#ifdef NTA_ASSERTIONS_ON
//    nrows = 5; ncols = 7; zr = 4;
//    // Exceptions
//    {
//      DenseMat dense(nrows, ncols, zr);
//      DenseMat denseB(nrows+1, ncols, zr);
//      SparseMat sm(nrows, ncols, dense.begin());
//      SparseMat smB(nrows+1, ncols, denseB.begin());
//      
//      try {
//        sm.lerp(1, 1, smB);
//        Test("lerp exception 1", 0, 1);
//      } catch (std::runtime_error&) {
//        Test("lerp exception 1", 1, 1);
//      }
//    }
//
//    {
//      DenseMat dense(nrows, ncols, zr);
//      DenseMat denseB(nrows, ncols+1, zr);
//      SparseMat sm(nrows, ncols, dense.begin());
//      SparseMat smB(nrows, ncols+1, denseB.begin());
//      
//      try {
//        sm.lerp(1, 1, smB);
//        Test("lerp exception 2", 0, 1);
//      } catch (std::runtime_error&) {
//        Test("lerp exception 2", 1, 1);
//      }
//    }
//#endif
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_small_values()
//  {
//    UInt nrows, ncols, zr;
//
//    {
//      nrows = 200; ncols = 100; zr = ncols - 64;
//      DenseMat dense(nrows, ncols, zr, true, true, rng_);
//      SparseMat sm(nrows, ncols, dense.begin());
//      DenseMat A(nrows, ncols);
//
//      sm.toDense(A.begin());
//      sm.fromDense(nrows, ncols, A.begin());     
//      Compare(dense, sm, "to/from Dense, small values");
//    }
//       
//    {
//      nrows = 200; ncols = 100; zr = ncols - 64;
//      DenseMat dense(nrows, ncols, zr, true, true, rng_);
//      SparseMat sm(nrows, ncols, dense.begin());
//      std::stringstream str1;
//      sm.toCSR(str1);
//      sm.fromCSR(str1);
//      Compare(dense, sm, "to/from CSR, small values");
//    }
//
//    {
//      nrows = 200; ncols = 100; zr = ncols - 64;
//      DenseMat dense(nrows, ncols, zr, true, true, rng_);
//      SparseMat sm(nrows, ncols, dense.begin());
//      sm.compact();
//      Compare(dense, sm, "compact, small values");
//    }
//
//    {
//      nrows = 200; ncols = 100; zr = ncols - 64;
//      Dense<UInt, double> dense(nrows, ncols, zr, true, true, rng_);
//      SparseMatrix<UInt, double> sm(nrows, ncols, dense.begin());
//      sm.threshold(4 * nta::Epsilon);
//      dense.threshold(4 * nta::Epsilon);
//      Compare(dense, sm, "threshold, small values 1");
//      sm.threshold(2 * nta::Epsilon);
//      dense.threshold(2 * nta::Epsilon);
//      Compare(dense, sm, "threshold, small values 2");
//    }
//
//    {
//      nrows = 200; ncols = 100; zr = ncols - 64;
//      Dense<UInt, double> dense(nrows, ncols, zr, true, true, rng_);
//      SparseMatrix<UInt, double> sm(nrows, ncols, dense.begin());
//      Compare(dense, sm, "addRow, small values");
//    }
//
//    {
//       nrows = 8; ncols = 4; zr = ncols - 2;
//       Dense<UInt, double> dense(nrows, ncols, zr, true, true, rng_);
//       Dense<UInt, double> dense2(ncols, nrows);
//       SparseMatrix<UInt, double> sm(nrows, ncols, dense.begin());
//       SparseMatrix<UInt, double> sm2(ncols, nrows);
//       dense.transpose(dense2);
//       sm.transpose(sm2);
//       Compare(dense2, sm2, "transpose, small values");
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_accumulate()
//  {
//    UInt nrows = 7, ncols = 5, zr = 2;
//
//    if (0) { // Visual tests
//      
//      Dense<UInt,double> dense(nrows, ncols, zr);
//      SparseMatrix<UInt,double> sparse(nrows, ncols, dense.begin());
//      
//      std::vector<double> row_sums(nrows), col_sums(ncols);
//      
//      cout << sparse << endl;
//
//      sparse.accumulateAllRowsNZ(row_sums.begin(), std::plus<double>());
//      sparse.accumulateAllColsNZ(col_sums.begin(), std::plus<double>());
//      
//      cout << "Row sums = " << row_sums << endl;
//      cout << "Col sums = " << col_sums << endl;
//    }
//
//    /*
//    TEST_LOOP(M) {
//
//      Dense<UInt, double> denseA(nrows, ncols, zr);
//      SparseMatrix<UInt, double> smA(nrows, ncols, denseA.begin());
//      
//      for (UInt r = 0; r < nrows; r += 5) {
//        
//        {
//          double r1 = denseA.accumulate(r, multiplies<double>(), 1);
//          double r2 = smA.accumulateRowNZ(r, multiplies<double>(), 1);
//          std::stringstream str;
//          str << "accumulateRowNZ * " << nrows << "X" << ncols << "/" << zr;
//          Test(str.str().c_str(), r1, r2);
//        }
//        
//        {
//          double r1 = denseA.accumulate(r, multiplies<double>(), 1);
//          double r2 = smA.accumulate(r, multiplies<double>(), 1);
//          std::stringstream str;
//          str << "accumulate * " << nrows << "X" << ncols << "/" << zr;
//          Test(str.str().c_str(), r1, r2);
//        }
//
//        {
//          double r1 = denseA.accumulate(r, plus<double>());
//          double r2 = smA.accumulateRowNZ(r, plus<double>());
//          std::stringstream str;
//          str << "accumulateRowNZ + " << nrows << "X" << ncols << "/" << zr;
//          Test(str.str().c_str(), r1, r2);
//        }
//    
//        {
//          double r1 = denseA.accumulate(r, plus<double>());
//          double r2 = smA.accumulate(r, plus<double>());
//          std::stringstream str;
//          str << "accumulate + " << nrows << "X" << ncols << "/" << zr;
//          Test(str.str().c_str(), r1, r2);
//        }
//
//        {     
//          double r1 = denseA.accumulate(r, nta::Max<double>, 0);
//          double r2 = smA.accumulateRowNZ(r, nta::Max<double>, 0);
//          std::stringstream str;
//          str << "accumulateRowNZ max " << nrows << "X" << ncols << "/" << zr;
//          Test(str.str().c_str(), r1, r2);
//        }
//
//        {
//          double r1 = denseA.accumulate(r, nta::Max<double>, 0);
//          double r2 = smA.accumulate(r, nta::Max<double>, 0);
//          std::stringstream str;
//          str << "accumulate max " << nrows << "X" << ncols << "/" << zr;
//          Test(str.str().c_str(), r1, r2);
//        }     
//      }         
//    }    
//    */                                   
//  }    
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_multiply()
//  {
//    UInt nrows, ncols, zr, nrows1, ncols1, ncols2, zr1, zr2;
//       
//    if (0) { // Visual test, keep  
//      
//      DenseMat dense(4, 5, 2);
//      SparseMat sparse1(dense.nRows(), dense.nCols(), dense.begin());
//      SparseMat sparse2(sparse1);
//      sparse2.transpose();
//      SparseMat sparse3(0,0);
//      
//      cout << sparse1 << endl << endl << sparse2 << endl << endl;
//      sparse1.multiply(sparse2, sparse3);
//      cout << sparse3 << endl;
//      
//      return;
//    }
//
//    TEST_LOOP(M) {
//
//      nrows1 = nrows; ncols1 = ncols; zr1 = zr;
//      ncols2 = 2*nrows+1; zr2 = zr1;
//    
//      Dense<UInt, double> denseA(nrows1, ncols1, zr1);
//      SparseMatrix<UInt, double> smA(nrows1, ncols1, denseA.begin());
//        
//      Dense<UInt, double> denseB(ncols1, ncols2, zr2);
//      SparseMatrix<UInt, double> smB(ncols1, ncols2, denseB.begin());
//        
//      Dense<UInt, double> denseC(nrows1, ncols2, zr2);
//      SparseMatrix<UInt, double> smC(nrows1, ncols2, denseC.begin());
//               
//      {
//        denseC.clear();       
//        denseA.multiply(denseB, denseC);
//        smA.multiply(smB, smC);
//          
//        std::stringstream str;
//        str << "multiply " << nrows << "X" << ncols << "/" << zr;
//        Compare(denseC, smC, str.str().c_str());
//      }         
//    }                               
//  }    
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_argMax() 
//  {
//    UInt ncols, nrows, zr;
//    UInt m_i_sparse, m_j_sparse, m_i_dense, m_j_dense;
//    Real m_val_sparse, m_val_dense;
//
//    {
//      TEST_LOOP(M) {
//
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sparse(nrows, ncols, dense.begin());
//
//	dense.max(m_i_dense, m_j_dense, m_val_dense);
//
//        sparse.decompact();
//	sparse.max(m_i_sparse, m_j_sparse, m_val_sparse);
//      
//        {
//          std::stringstream str;
//          str << "argMax A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (m_i_sparse != m_i_dense
//	      || m_j_sparse != m_j_dense
//	      || !nta::nearlyEqual(m_val_sparse, m_val_dense))
//	    Test(str.str().c_str(), 0, 1);
//        }      
//               
//        sparse.compact();
//	sparse.max(m_i_sparse, m_j_sparse, m_val_sparse);
//
//        {
//          std::stringstream str;
//          str << "argMax B " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (m_i_sparse != m_i_dense
//	      || m_j_sparse != m_j_dense
//	      || !nta::nearlyEqual(m_val_sparse, m_val_dense))
//	    Test(str.str().c_str(), 0, 1);
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_argMin() 
//  {
//    UInt ncols, nrows, zr;
//    UInt m_i_sparse, m_j_sparse, m_i_dense, m_j_dense;
//    Real m_val_sparse, m_val_dense;
//
//    {
//      TEST_LOOP(M) {
//   
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sparse(nrows, ncols, dense.begin());
//
//	dense.min(m_i_dense, m_j_dense, m_val_dense);
//
//        sparse.decompact();
//	sparse.min(m_i_sparse, m_j_sparse, m_val_sparse);
//      
//        {
//          std::stringstream str;
//          str << "argMin A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (m_i_sparse != m_i_dense
//	      || m_j_sparse != m_j_dense
//	      || !nta::nearlyEqual(m_val_sparse, m_val_dense)) {
//	    Test(str.str().c_str(), 0, 1);
//	  }
//        }      
//               
//        sparse.compact();
//	sparse.min(m_i_sparse, m_j_sparse, m_val_sparse);
//
//        {
//          std::stringstream str;
//          str << "argMin B " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (m_i_sparse != m_i_dense
//	      || m_j_sparse != m_j_dense
//	      || !nta::nearlyEqual(m_val_sparse, m_val_dense))
//	    Test(str.str().c_str(), 0, 1);
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_rowMax_2() 
//  {
//    UInt ncols, nrows, zr;
//
//    {
//      TEST_LOOP(M) {
//   
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sparse(nrows, ncols, dense.begin());
//	std::vector<std::pair<UInt, Real> > optima_sparse(nrows), optima_dense(nrows);
//
//	dense.rowMax(optima_dense.begin());
//
//        sparse.decompact();
//
//	for (UInt i = 0; i != nrows; ++i) {
//
//	  std::pair<UInt,Real> res_sparse;
//	  sparse.rowMax(i, res_sparse.first, res_sparse.second);
//
//	  std::stringstream str;
//          str << "rowMax 2 A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (optima_dense[i].first != res_sparse.first
//	      || !nearlyEqual(optima_dense[i].second, res_sparse.second))
//	    Test(str.str().c_str(), 0, 1);   
//	}
//
//	sparse.rowMax(optima_sparse.begin());
//      
//        {
//          std::stringstream str;
//          str << "rowMax 2 B " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  for (UInt i = 0; i != nrows; ++i) {
//	    if (optima_dense[i].first != optima_sparse[i].first
//		|| !nta::nearlyEqual(optima_dense[i].second, optima_sparse[i].second))
//	      Test(str.str().c_str(), 0, 1);
//	  }
//        }      
//               
//        sparse.compact();
//
//	for (UInt i = 0; i != nrows; ++i) {
//
//	  std::pair<UInt,Real> res_sparse;
//	  sparse.rowMax(i, res_sparse.first, res_sparse.second);
//
//	  std::stringstream str;
//          str << "rowMax 2 C " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (optima_dense[i].first != res_sparse.first
//	      || !nearlyEqual(optima_dense[i].second, res_sparse.second))
//	      Test(str.str().c_str(), 0, 1);
//	}
//
//	sparse.rowMax(optima_sparse.begin());
//
//        {
//          std::stringstream str;
//          str << "rowMax 2 D " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  for (UInt i = 0; i != nrows; ++i) {
//	    if (optima_dense[i].first != optima_sparse[i].first
//		|| !nta::nearlyEqual(optima_dense[i].second, optima_sparse[i].second))
//	      Test(str.str().c_str(), 0, 1);
//	  }
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_rowMin() 
//  {
//    UInt ncols, nrows, zr;
//
//    {
//      TEST_LOOP(M) {
//   
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sparse(nrows, ncols, dense.begin());
//	std::vector<std::pair<UInt, Real> > optima_sparse(nrows), optima_dense(nrows);
//
//	dense.rowMin(optima_dense.begin());
//
//        sparse.decompact();
//
//	for (UInt i = 0; i != nrows; ++i) {
//
//	  std::pair<UInt,Real> res_sparse;
//	  sparse.rowMin(i, res_sparse.first, res_sparse.second);
//
//	  std::stringstream str;
//          str << "rowMin A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (optima_dense[i].first != res_sparse.first
//	      || !nearlyEqual(optima_dense[i].second, res_sparse.second))
//	      Test(str.str().c_str(), 0, 1);
//	}
//
//	sparse.rowMin(optima_sparse.begin());
//      
//        {
//          std::stringstream str;
//          str << "rowMin B " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  for (UInt i = 0; i != nrows; ++i) {
//	    if (optima_dense[i].first != optima_sparse[i].first
//		|| !nta::nearlyEqual(optima_dense[i].second, optima_sparse[i].second))
//	      Test(str.str().c_str(), 0, 1);
//	  }
//        }      
//               
//        sparse.compact();
//
//	for (UInt i = 0; i != nrows; ++i) {
//
//	  std::pair<UInt,Real> res_sparse;
//	  sparse.rowMin(i, res_sparse.first, res_sparse.second);
//
//	  std::stringstream str;
//          str << "rowMin C " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (optima_dense[i].first != res_sparse.first
//	      || !nearlyEqual(optima_dense[i].second, res_sparse.second))
//	      Test(str.str().c_str(), 0, 1);
//	}
//
//	sparse.rowMin(optima_sparse.begin());
//
//        {
//          std::stringstream str;
//          str << "rowMin D " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  for (UInt i = 0; i != nrows; ++i) {
//	    if (optima_dense[i].first != optima_sparse[i].first
//		|| !nta::nearlyEqual(optima_dense[i].second, optima_sparse[i].second))
//	      Test(str.str().c_str(), 0, 1);
//	  }
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_colMax() 
//  {
//    UInt ncols = 7, nrows = 9, zr = 3;
//
//    if (0) {
//      DenseMat dense(nrows, ncols, zr);
//      SparseMat sparse(nrows, ncols, dense.begin());
//      cout << sparse << endl;
//      for (UInt j = 0; j != ncols; ++j) {
//	UInt col_max_i;
//	Real col_max;
//	sparse.colMax(j, col_max_i, col_max);
//	cout << j << " " << col_max_i << " " << col_max << endl;
//      }
//    }
//
//    {
//      TEST_LOOP(M) {
//   
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sparse(nrows, ncols, dense.begin());
//	std::vector<std::pair<UInt, Real> > optima_sparse(ncols), optima_dense(ncols);
//
//	dense.colMax(optima_dense.begin());
//
//        sparse.decompact();
//
//	for (UInt j = 0; j != ncols; ++j) {
//
//	  std::pair<UInt,Real> res_sparse;
//	  sparse.colMax(j, res_sparse.first, res_sparse.second);
//
//	  std::stringstream str;
//          str << "colMax A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (optima_dense[j].first != res_sparse.first
//	      || !nearlyEqual(optima_dense[j].second, res_sparse.second))
//	    Test(str.str().c_str(), 0, 1);	  
//	}
//
//	sparse.colMax(optima_sparse.begin());
//      
//        {
//          std::stringstream str;
//          str << "colMax B " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  for (UInt j = 0; j != ncols; ++j) {
//	    if (optima_dense[j].first != optima_sparse[j].first
//		|| !nta::nearlyEqual(optima_dense[j].second, optima_sparse[j].second))
//	      Test(str.str().c_str(), 0, 1);
//	  }
//        }      
//               
//        sparse.compact();
//
//	for (UInt i = 0; i != ncols; ++i) {
//
//	  std::pair<UInt,Real> res_sparse;
//	  sparse.colMax(i, res_sparse.first, res_sparse.second);
//
//	  std::stringstream str;
//          str << "colMax C " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (optima_dense[i].first != res_sparse.first
//	      || !nearlyEqual(optima_dense[i].second, res_sparse.second))
//	    Test(str.str().c_str(), 0, 1);
//	}
//
//	sparse.colMax(optima_sparse.begin());
//
//        {
//          std::stringstream str;
//          str << "colMax D " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  for (UInt i = 0; i != ncols; ++i) {
//	    if (optima_dense[i].first != optima_sparse[i].first
//		|| !nta::nearlyEqual(optima_dense[i].second, optima_sparse[i].second))
//	      Test(str.str().c_str(), 0, 1);
//	  }
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_colMin() 
//  {
//    UInt ncols, nrows, zr;
//
//    {
//      TEST_LOOP(M) {
//   
//        DenseMat dense(nrows, ncols, zr);
//        SparseMat sparse(nrows, ncols, dense.begin());
//	std::vector<std::pair<UInt, Real> > optima_sparse(ncols), optima_dense(ncols);
//
//	dense.colMin(optima_dense.begin());
//
//        sparse.decompact();
//
//	for (UInt i = 0; i != ncols; ++i) {
//
//	  std::pair<UInt,Real> res_sparse;
//	  sparse.colMin(i, res_sparse.first, res_sparse.second);
//
//	  std::stringstream str;
//          str << "rowMax 2 A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (optima_dense[i].first != res_sparse.first
//	      || !nearlyEqual(optima_dense[i].second, res_sparse.second))
//	    Test(str.str().c_str(), 0, 1);
//	}
//
//	sparse.colMin(optima_sparse.begin());
//      
//        {
//          std::stringstream str;
//          str << "rowMax 2 B " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  for (UInt i = 0; i != ncols; ++i) {
//	    if (optima_dense[i].first != optima_sparse[i].first
//		|| !nta::nearlyEqual(optima_dense[i].second, optima_sparse[i].second))
//	      Test(str.str().c_str(), 0, 1);
//	  }
//        }      
//               
//        sparse.compact();
//
//	for (UInt i = 0; i != ncols; ++i) {
//
//	  std::pair<UInt,Real> res_sparse;
//	  sparse.colMin(i, res_sparse.first, res_sparse.second);
//
//	  std::stringstream str;
//          str << "rowMax 2 C " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  if (optima_dense[i].first != res_sparse.first
//	      || !nearlyEqual(optima_dense[i].second, res_sparse.second))
//	    Test(str.str().c_str(), 0, 1);
//	}
//
//	sparse.colMin(optima_sparse.begin());
//
//        {
//          std::stringstream str;
//          str << "rowMax 2 D " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//	  for (UInt i = 0; i != ncols; ++i) {
//	    if (optima_dense[i].first != optima_sparse[i].first
//		|| !nta::nearlyEqual(optima_dense[i].second, optima_sparse[i].second))
//	      Test(str.str().c_str(), 0, 1);
//	  }
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_nNonZeros()
//  {
//    UInt ncols, nrows, zr;
//
//    TEST_LOOP(M) {
//      
//      DenseMat dense(nrows, ncols, zr);
//      SparseMat sparse(nrows, ncols, dense.begin());
//
//      UInt n_s, n_d;
//
//      {
//	std::vector<UInt> nrows_s(nrows), nrows_d(nrows);
//	std::vector<UInt> ncols_s(ncols), ncols_d(ncols);
//
//	sparse.decompact();
//      
//	n_d = dense.nNonZeros();
//	n_s = sparse.nNonZeros();
//
//	{
//	  std::stringstream str;
//	  str << "nNonZeros A1 " << nrows << "X" << ncols << "/" << zr
//	      << " - non compact";
//	  if (n_d != n_s)
//	    Test(str.str().c_str(), 0, 1);
//	}
//
//	for (UInt i = 0; i != nrows; ++i) {
//
//	  n_d = dense.nNonZerosOnRow(i);
//	  n_s = sparse.nNonZerosOnRow(i);
//
//	  {
//	    std::stringstream str;
//	    str << "nNonZeros B1 " << nrows << "X" << ncols << "/" << zr
//		<< " - non compact";
//	    if (n_d != n_s)
//	      Test(str.str().c_str(), 0, 1);
//	  }    
//	}
//
//	for (UInt i = 0; i != ncols; ++i) {
//
//	  n_d = dense.nNonZerosOnCol(i);
//	  n_s = sparse.nNonZerosOnCol(i);
//
//	  {
//	    std::stringstream str;
//	    str << "nNonZeros C1 " << nrows << "X" << ncols << "/" << zr
//		<< " - non compact";
//	    if (n_d != n_s) 
//	      Test(str.str().c_str(), 0, 1);
//	  }
//	}
//
//	dense.nNonZerosPerRow(nrows_d.begin());
//	sparse.nNonZerosPerRow(nrows_s.begin());
//
//	{
//	  std::stringstream str;
//	  str << "nNonZeros D1 " << nrows << "X" << ncols << "/" << zr
//	      << " - non compact";
//	  CompareVectors(nrows, nrows_d.begin(), nrows_s.begin(), str.str().c_str());
//	}
//
//	dense.nNonZerosPerCol(ncols_d.begin());
//	sparse.nNonZerosPerCol(ncols_s.begin());
//
//	{
//	  std::stringstream str;
//	  str << "nNonZeros E1 " << nrows << "X" << ncols << "/" << zr
//	      << " - non compact";
//	  CompareVectors(ncols, ncols_d.begin(), ncols_s.begin(), str.str().c_str());
//	}
//      }
//      
//      {
//	std::vector<UInt> nrows_s(nrows), nrows_d(nrows);
//	std::vector<UInt> ncols_s(ncols), ncols_d(ncols);
//	sparse.compact();
//      
//	n_d = dense.nNonZeros();
//	n_s = sparse.nNonZeros();
//
//	{
//	  std::stringstream str;
//	  str << "nNonZeros A2 " << nrows << "X" << ncols << "/" << zr
//	      << " - compact";
//	  if (n_d != n_s)
//	    Test(str.str().c_str(), 0, 1);
//	}
//
//	for (UInt i = 0; i != nrows; ++i) {
//
//	  n_d = dense.nNonZerosOnRow(i);
//	  n_s = sparse.nNonZerosOnRow(i);
//
//	  {
//	    std::stringstream str;
//	    str << "nNonZeros B2 " << nrows << "X" << ncols << "/" << zr
//		<< " - compact";
//	    if (n_d != n_s)
//	      Test(str.str().c_str(), 0, 1);
//	  }
//	}
//
//	for (UInt i = 0; i != ncols; ++i) {
//
//	  n_d = dense.nNonZerosOnCol(i);
//	  n_s = sparse.nNonZerosOnCol(i);
//
//	  {
//	    std::stringstream str;
//	    str << "nNonZeros C2 " << nrows << "X" << ncols << "/" << zr
//		<< " - compact";
//	    if (n_d != n_s)
//	      Test(str.str().c_str(), 0, 1);
//	  }     
//	}
//
//	dense.nNonZerosPerRow(nrows_d.begin());
//	sparse.nNonZerosPerRow(nrows_s.begin());
//
//	{
//	  std::stringstream str;
//	  str << "nNonZeros D2 " << nrows << "X" << ncols << "/" << zr
//	      << " - compact";
//	  CompareVectors(nrows, nrows_d.begin(), nrows_s.begin(), str.str().c_str());
//	}
//
//	dense.nNonZerosPerCol(ncols_d.begin());
//	sparse.nNonZerosPerCol(ncols_s.begin());
//
//	{
//	  std::stringstream str;
//	  str << "nNonZeros E2 " << nrows << "X" << ncols << "/" << zr
//	      << " - compact";
//	  CompareVectors(ncols, ncols_d.begin(), ncols_s.begin(), str.str().c_str());
//	}
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_extract()
//  {
//    if (1) { // Visual tests
//      
//      DenseMat dense(5, 7, 2);
//      SparseMat sparse(5, 7, dense.begin());
//
//      /*
//      cout << "Sparse:" << endl << sparse << endl;
//
//      { // Extract domain    
//	Domain2D dom(0,4,0,4);
//	SparseMatrix<UInt,UInt> extracted(4,4);
//	sparse.get(dom, extracted);
//	cout << extracted << endl;
//      }         
//      */
//    }
//  }
//    
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_deleteRow()
//  {
//    // This is regression test for an off-by-one memory corruption bug 
//    // found in deleteRow the symptom of the bug is a seg fault so there
//    // is no explicit test here. 
//    { 
//      SparseMat* sm = new SparseMat(11, 1);
//      sm->deleteRow(3);
//      delete sm;
//
//      sm = new SparseMat(11, 1);
//      sm->deleteRow(3);
//      delete sm;
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  /**
//   * A generator function object, that generates random numbers between 0 and 256.
//   * It also has a threshold to control the sparsity of the vectors generated. 
//   */
//  template <typename T>
//  struct rand_init 
//  {
//    Random *r_;
//    T threshold_;
//    
//    inline rand_init(Random *r, T threshold =100)
//      : r_(r), threshold_(threshold)
//    {}
//    
//    inline T operator()() 
//    { 
//      return T((T)(r_->getUInt32(100)) > threshold_ ? 0 : .001 + (r_->getReal64()));
//    }
//  };
//
//  //--------------------------------------------------------------------------------
//  void SparseMatrixUnitTest::unit_test_usage()
//  {
//    using namespace std;
//
//    typedef UInt size_type;
//    typedef double value_type;
//    typedef SparseMatrix<size_type,value_type> SM;
//    typedef Dense<size_type,value_type> DM;
//
//    size_type maxMatrixSize = 30;
//    size_type nrows = 20, ncols = 30, nzr = 20;
//
//    DM* dense = new DM(nrows, ncols, nzr, true, true, rng_);
//    SM* sparse = new SM(nrows, ncols, dense->begin());
//
//    for (long int a = 0; a < 10000; ++a) {
//	  
//      // Rectify to stop propagation of small errors
//      ITER_2(sparse->nRows(), sparse->nCols())
//	if (::fabs(dense->at(i,j) - sparse->get(i,j)) < 1e-6)
//	  dense->at(i,j) = sparse->get(i,j);
//
//      size_type r = rng_->getUInt32(37);
//
//      if (r == 0) {
//	
//	sparse->compact();
//	// no compact for Dense
//
//      } else if (r == 1) {
//
//	sparse->decompact();
//	// no decompact for Dense
//
//      } else if (r == 2) {
//
//	if (rng_->getReal64() < 0.90) {
//	  size_type nrows = sparse->nRows() + rng_->getUInt32(4);
//	  size_type ncols = sparse->nCols() + rng_->getUInt32(4);
//	  sparse->resize(nrows, ncols);
//	  dense->resize(nrows, ncols);
//	  Compare(*dense, *sparse, "resize, bigger");
//	
//	} else {
//	  if (sparse->nRows() > 2 && sparse->nCols() > 2) {
//	    size_type nrows = rng_->getUInt32(sparse->nRows());
//	    size_type ncols = rng_->getUInt32(sparse->nCols());
//	    sparse->resize(nrows, ncols);
//	    dense->resize(nrows, ncols);
//	    Compare(*dense, *sparse, "resize, smaller");
//	  }
//	}
//	
//      } else if (r == 3) {
//	
//	vector<size_type> del;
//	
//	if (rng_->getReal64() < 0.90) {
//	  for (size_type ii = 0; ii < sparse->nRows() / 4; ++ii)
//	    del.push_back(2*ii);
//	  sparse->deleteRows(del.begin(), del.end());
//	  dense->deleteRows(del.begin(), del.end());
//	} else {
//	  for (size_type ii = 0; ii < sparse->nRows(); ++ii)
//	    del.push_back(ii);
//	  sparse->deleteRows(del.begin(), del.end());
//	  dense->deleteRows(del.begin(), del.end());
//	}
//
//	Compare(*dense, *sparse, "deleteRows");
//
//      } else if (r == 4) {    
//	
//	vector<size_type> del;
//	if (rng_->getReal64() < 0.90) {
//	  for (size_type ii = 0; ii < sparse->nCols() / 4; ++ii)
//	    del.push_back(2*ii);
//	  sparse->deleteCols(del.begin(), del.end());
//	  dense->deleteCols(del.begin(), del.end());
//	} else {
//	  for (size_type ii = 0; ii < sparse->nCols(); ++ii)
//	    del.push_back(ii);
//	  sparse->deleteCols(del.begin(), del.end());
//	  dense->deleteCols(del.begin(), del.end());
//	}
//	Compare(*dense, *sparse, "deleteCols");
//
//      } else if (r == 5) {
//
//	SM sparse2(1, 1);
//	DM sm2Dense(1, 1);
//	Compare(sm2Dense,sparse2, "constructor(1, 1)");
//	
//	sparse2.copy(*sparse);
//	sparse->copy(sparse2);
//	
//	sm2Dense.copy(*dense);
//	dense->copy(sm2Dense);
//	Compare(*dense, *sparse, "copy");
//
//      } else if (r == 6) {
//
//	vector<value_type> row(sparse->nCols());
//	size_type n = rng_->getUInt32(16);
//	for (size_type z = 0; z < n; ++z) {			
//	  if (rng_->getReal64() < 0.90) 
//	    generate(row.begin(), row.end(), rand_init<value_type>(rng_, 70));
//	  sparse->addRow(row.begin());
//	  dense->addRow(row.begin());
//	  Compare(*dense, *sparse, "addRow");
//	}
//
//      } else if (r == 7) {
//
//	if (sparse->nRows() > 0 && sparse->nCols() > 0) {
//	  size_type m = sparse->nRows() * sparse->nCols() / 2;
//	  for (size_type z = 0; z < m; ++z) {
//	    size_type i = rng_->getUInt32(sparse->nRows());
//	    size_type j = rng_->getUInt32(sparse->nCols());
//	    value_type v = 1+value_type(rng_->getReal64());
//	    sparse->setNonZero(i, j, v);
//	    dense->setNonZero(i, j, v);
//	    Compare(*dense, *sparse, "setNonZero");
//	  }
//	}
//
//      } else if (r == 8) {
//    
//	value_type v = value_type(128 + rng_->getUInt32(128));
//	sparse->threshold(v);
//	dense->threshold(v);
//	Compare(*dense, *sparse, "threshold");
//
//      } else if (r == 9) {
//
//	if (sparse->nCols() > 0 && sparse->nRows() > 0) {
//	  
//	  SM B(0, sparse->nCols());
//	  DM BDense(0, dense->ncols);
//	  
//	  vector<value_type> row(sparse->nCols());
//
//	  for (size_type iii = 0; iii < sparse->nRows(); ++iii) {
//
//	    if (rng_->getUInt32(100) < 90) 
//	      generate(row.begin(), row.end(), rand_init<value_type>(rng_, 70));
//	    else
//	      fill(row.begin(), row.end(), value_type(0));
//
//	    B.addRow(row.begin());
//	    BDense.addRow(row.begin());
//	  }
//	  
//	  value_type r1=value_type(rng_->getUInt32(5)), r2=value_type(rng_->getUInt32(5));
//	  
//	  sparse->lerp(r1, r2, B);
//	  dense->lerp(r1, r2, BDense);
//	  Compare(*dense, *sparse, "lerp", 1e-4);
//	}
//	
//      } else if (r == 10) {
//
//	delete sparse;
//	delete dense;
//	size_type nrows = rng_->getUInt32(maxMatrixSize), ncols = rng_->getUInt32(maxMatrixSize);
//	sparse = new SM(ncols, nrows);
//	dense = new DM(ncols, nrows);
//	Compare(*dense, *sparse, "constructor(rng_->get() % 32, rng_->get() % 32)");
//
//      } else if (r == 11) {
//
//	delete sparse;
//	delete dense;
//	sparse = new SM();
//	dense = new DM();
//	Compare(*dense, *sparse, "constructor()");
//	
//      } else if (r == 12) {
//	
//	delete sparse;
//	delete dense;
//	sparse = new SM(0,0);
//	dense = new DM(0,0);
//	Compare(*dense, *sparse, "constructor(0,0)");
//	
//      } else if (r == 13) {
//	
//	SM sm2(sparse->nRows(), sparse->nCols());
//	DM sm2Dense(dense->nrows, dense->ncols);
//	Compare(sm2Dense, sm2, "constructor(dense->nRows(), dense->nCols())");
//	
//	ITER_2(sm2.nRows(), sm2.nCols()) {
//	  value_type r = 1+rng_->getUInt32(256);
//	  sm2.setNonZero(i,j, r);
//	  sm2Dense.setNonZero(i,j, r);
//	}
//	sparse->elementApply(sm2, std::plus<value_type>());
//	dense->add(sm2Dense);
//	Compare(*dense, *sparse, "add");
//
//      } else if (r == 14) {
//
//	if (sparse->nRows() > 0) {
//	  vector<value_type> row(sparse->nCols());	
//	  generate(row.begin(), row.end(), rand_init<value_type>(rng_, 70));
//	  size_type r = rng_->getUInt32(sparse->nRows());
//	  sparse->elementRowApply(r, std::plus<value_type>(), row.begin());
//	  dense->add(r, row.begin());
//	  Compare(*dense, *sparse, "add(randomR, row.begin())");
//	}	
//	
//      } else if (r == 15) {
//	  
//	SM B(sparse->nCols(), sparse->nRows());
//	DM BDense(dense->ncols, dense->nrows);
//	Compare(BDense, B, "constructor(sm->nCols(), sm->nRows())");
//	sparse->transpose(B);
//	dense->transpose(BDense);
//	Compare(*dense, *sparse, "transpose");
//	  
//      } else if (r == 16) {	
//
//	/*
//	vector<value_type> x(sparse->nCols()), y(sparse->nRows());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	sparse->L2Dist(x.begin(), y.begin());
//	dense->L2Dist(x.begin(), y.begin());
//	Compare(*dense, *sparse, "L2Dist", 1e-4);
//	*/
//
//      } else if (r == 17) {
//
//	/*
//	vector<value_type> x(sparse->nCols());
//	pair<size_type, value_type> closest;
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	sparse->L2Nearest(x.begin(), closest);
//	dense->L2Nearest(x.begin(), closest);
//	Compare(*dense, *sparse, "L2Nearest", 1e-4);
//	*/
//
//      } else if (r == 18) {
//	  
//	/*
//	vector<value_type> x(sparse->nCols()), y(sparse->nRows());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	sparse->vecDist(x.begin(), y.begin());
//	dense->vecDist(x.begin(), y.begin());
//	Compare(*dense, *sparse, "vecDist", 1e-4);
//	*/
//
//      } else if(r == 19) {
//
//	/*
//	if(sparse->nRows() > 0) {
//	  vector<value_type> x(sparse->nCols());
//	  generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	  size_type randInt=rng_->get() % sparse->nRows();
//	  sparse->rowDistSquared(randInt, x.begin());
//	  dense->rowDistSquared(randInt, x.begin());
//	  Compare(*dense, *sparse, "rowDistSquared", 1e-4);
//	}
//	*/
//	  
//      } else if (r == 20) {
//	  
//	/*
//	vector<value_type> x(sparse->nCols());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	sparse->closestEuclidean(x.begin());
//	dense->closestEuclidean(x.begin());
//	Compare(*dense, *sparse, "closestEuclidean", 1e-4);
//	*/
//
//      } else if (r== 21) {
//
//	/*
//	vector<value_type> x(sparse->nCols());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	for (size_type n = 0; n < sparse->nCols(); ++n)	
//	  x.push_back(value_type(rng_->get() % 256));
//	sparse->dotNearest(x.begin());
//	dense->dotNearest(x.begin());
//	Compare(*dense, *sparse, "dotNearest", 1e-4);
//	*/
//
//      } else if (r == 22) {
//
//	vector<value_type> x(sparse->nCols()), y(sparse->nRows());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	sparse->rightVecProd(x.begin(), y.begin());
//	dense->rightVecProd(x.begin(), y.begin());
//	Compare(*dense, *sparse, "rightVecProd", 1e-4);
//
//      } else if (r == 23) {
//	  
//	vector<value_type> x(sparse->nCols()), y(sparse->nRows());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	sparse->vecMaxProd(x.begin(), y.begin());
//	dense->vecMaxProd(x.begin(), y.begin());
//	Compare(*dense, *sparse, "vecMaxProd", 1e-4);
//	  
//      } else if (r == 24) {
//
//	vector<value_type> x(sparse->nCols()), y(sparse->nRows());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	sparse->vecMaxAtNZ(x.begin(), y.begin());
//	dense->vecMaxAtNZ(x.begin(), y.begin());
//	Compare(*dense, *sparse, "vecMaxAtNZ", 1e-4);
//	  
//      } else if (r == 25) {
//
//	if (sparse->nRows() > 0) {
//	  vector<value_type> x(sparse->nCols());
//	  generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	  size_type row = rng_->getUInt32(sparse->nRows());
//	  value_type r1=value_type(rng_->getUInt32(256)), r2=value_type(rng_->getUInt32(256));
//	  sparse->axby(row, r1, r2, x.begin());
//	  dense->axby(row, r1, r2, x.begin());
//	  Compare(*dense, *sparse, "axby", 1e-4);
//	}
//
//      } else if (r == 26) {
//
//	vector<value_type> x(sparse->nCols());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	value_type r1=value_type(rng_->getUInt32(256)), r2=value_type(rng_->getUInt32(256));
//	sparse->axby(r1, r2, x.begin());
//	dense->axby(r1, r2, x.begin());
//	Compare(*dense, *sparse, "axby 2", 1e-4);
//
//      } else if (r == 27) {
//	  
//	/*
//	vector<value_type> x(sparse->nCols()), y(sparse->nRows());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	sparse->rowMax(x.begin(), y.begin()); 
//	dense->rowMax(x.begin(), y.begin()); 
//	Compare(*dense, *sparse, "rowMax");
//	*/
//    
//      } else if (r == 28) {
//	     
//	vector< pair<size_type, value_type> > y(sparse->nRows());
//	sparse->rowMax(y.begin());  
//	dense->rowMax(y.begin());  
//	Compare(*dense, *sparse, "rowMax 2");
//	  
//      } else if (r == 29) {
//	  
//	vector< pair<size_type, value_type> > y(sparse->nCols());
//	sparse->colMax(y.begin());
//	dense->colMax(y.begin());
//	Compare(*dense, *sparse, "colMax");
//	  
//      } else if (r == 30) {
//	  
//	bool exact = true;
//	sparse->normalizeRows(exact);
//	dense->normalizeRows(exact);
//	Compare(*dense, *sparse, "normalizeRows", 1e-4);
//
//      } else if (r == 31) {
//	  
//	vector<value_type> x(sparse->nCols()), y(sparse->nRows());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	sparse->rightVecProdAtNZ(x.begin(), y.begin()); 
//	dense->rowProd(x.begin(), y.begin()); 
//	Compare(*dense, *sparse, "rowProd", 1e-4);
//	  
//      } else if (r == 32) {
//	  
//	vector<value_type> x(sparse->nCols()), y(sparse->nRows());
//	generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	value_type theRandom=value_type(rng_->getUInt32(256));
//	sparse->rightVecProdAtNZ(x.begin(), y.begin(), theRandom);
//	dense->rowProd(x.begin(), y.begin(), theRandom);
//	Compare(*dense, *sparse, "rowProd 2", 1e-4);
//
//      } else if (r == 33) {
//	  
//	//size_type row;
//	//value_type init;
//	
//	if (sparse->nRows() != 0) {
//
//	  /*
//	  row = rng_->get() % sparse->nRows();
//	  init = (rng_->get() % 32768)/32768.0 + .001;
//	  
//	  size_type switcher = rng_->get() % 4;
//
//	  if (switcher == 0) {
//	    sparse->accumulateRowNZ(row, multiplies<value_type>(), init);
//	    dense->accumulateRowNZ(row, multiplies<value_type>(), init);
//	    Compare(*dense, *sparse, "accumulateRowNZ with multiplies", 1e-4);
//	  } else if (switcher == 1) {
//	    sparse->accumulateRowNZ(row, plus<value_type>(), init);
//	    dense->accumulateRowNZ(row, plus<value_type>(), init);
//	    Compare(*dense, *sparse, "accumulateRowNZ with plus", 1e-4);
//	  } else if (switcher == 2) {
//	    sparse->accumulateRowNZ(row, minus<value_type>(), init);
//	    dense->accumulateRowNZ(row, minus<value_type>(), init);
//	    Compare(*dense, *sparse, "accumulateRowNZ with minus", 1e-4);
//	  } else if (switcher == 3) {
//	    sparse->accumulateRowNZ(row, nta::Max<value_type>, init);
//	    dense->accumulateRowNZ(row, nta::Max<value_type>, init);
//	    Compare(*dense, *sparse, "accumulateRowNZ with Max", 1e-4);
//	  }
//	  */
//	}
//
//      } else if (r == 34) {
//	  
//	//size_type row;
//	//value_type init;
//
//	if (sparse->nRows() != 0) {
//	  /*
//	  row = rng_->get() % sparse->nRows();
//	  init = (rng_->get() % 32768)/32768.0 + .001;
//	  
//	  size_type switcher = rng_->get() % 4;
//
//	  if (switcher == 0) {
//	    sparse->accumulate(row, multiplies<value_type>(), init);
//	    dense->accumulate(row, multiplies<value_type>(), init);
//	    Compare(*dense, *sparse, "accumulateRowNZ with multiplies", 1e-4);
//	  } else if (switcher == 1) {
//	    sparse->accumulate(row, plus<value_type>(), init);
//	    dense->accumulate(row, plus<value_type>(), init);
//	    Compare(*dense, *sparse, "accumulateRowNZ with plus", 1e-4);
//	  } else if (switcher == 2) {
//	    sparse->accumulate(row, minus<value_type>(), init);
//	    dense->accumulate(row, minus<value_type>(), init);
//	    Compare(*dense, *sparse, "accumulateRowNZ with minus", 1e-4);
//	  } else if (switcher == 3) {
//	    sparse->accumulate(row, nta::Max<value_type>, init);
//	    dense->accumulate(row, nta::Max<value_type>, init);
//	    Compare(*dense, *sparse, "accumulateRowNZ with Max", 1e-4);
//	  }
//	  */
//	}
//	
//      } else if (r == 35) {
//	 
//	if(dense->ncols > 0 && dense->nrows > 0) {
//  
//	  size_type randomTemp = rng_->getUInt32(maxMatrixSize);
//	  SM B(0, randomTemp);	
//	  SM C(sparse->nRows(), randomTemp);
//	  DM BDense(0, randomTemp);
//	  DM CDense(dense->nrows, randomTemp);
//		  
//	  vector<value_type> x(randomTemp);
//	  
//	  for (size_type n=0; n < sparse->nCols(); n++) {	
//	    generate(x.begin(), x.end(), rand_init<value_type>(rng_, 50));
//	    B.addRow(x.begin());
//	    BDense.addRow(x.begin());
//	  }
//	  
//	  sparse->multiply( B, C);
//	  dense->multiply( BDense, CDense);
//	  Compare(*dense, *sparse, "multiply", 1e-4);
//	}
//	
//      } else if (r == 36) {
//	    
//	if (sparse->nRows() > 0 && sparse->nCols() > 0) {
//	  
//	  vector<size_type> indices, indicesDense;
//	  vector<value_type> values, valuesDense;
//	  
//	  size_type r = rng_->getUInt32(sparse->nRows());
//
//	  sparse->getRowToSparse(r, back_inserter(indices), 
//				 back_inserter(values));
//	  
//	  dense->getRowToSparse(r, back_inserter(indicesDense),
//				back_inserter(valuesDense));
//	  
//	  sparse->findRow((size_type)indices.size(), 
//			  indices.begin(), 
//			  values.begin());
//
//	  dense->findRow((size_type)indicesDense.size(), 
//			 indicesDense.begin(), 
//			 valuesDense.begin());
//
//	  CompareVectors((size_type)indices.size(), indices.begin(), 
//			 indicesDense.begin(),
//			 "findRow indices");
//
//	  CompareVectors((size_type)values.size(), values.begin(), 
//			 valuesDense.begin(),
//			 "findRow values");
//	}
//      }    
//    }
//    
//    delete sparse;
//    delete dense;
//  } 
//     
  //--------------------------------------------------------------------------------
  void SparseMatrixUnitTest::RunTests()
  {

    //unit_test_construction();  
    //unit_test_copy();
    //unit_test_dense();
    //unit_test_csr();
    //unit_test_compact(); 
    //unit_test_threshold();   
    //unit_test_addRowCol();    
    //unit_test_resize();
    //unit_test_deleteRows();    
    //unit_test_deleteCols();
    //unit_test_set();
    //unit_test_setRowColToZero();
    //unit_test_getRow();  
    //unit_test_getCol();
    //unit_test_vecMaxProd();
    //unit_test_vecProd();    
    //unit_test_axby();
    //unit_test_axby_3();
    //unit_test_rowMax();
    //unit_test_maxima();
    //unit_test_normalize();
    //unit_test_rowProd();
    //unit_test_lerp();
    //unit_test_accumulate();
    //unit_test_transpose();
    //unit_test_multiply();
    //unit_test_small_values();
    //unit_test_argMax();
    //unit_test_argMin();
    //unit_test_rowMax_2();
    //unit_test_rowMin();
    //unit_test_colMax();
    //unit_test_colMin();
    //unit_test_nNonZeros();
    //unit_test_extract();
    //unit_test_deleteRow();
    ////unit_test_usage();
  } 

  //--------------------------------------------------------------------------------
  
} // namespace nta


