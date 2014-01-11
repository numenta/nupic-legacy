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
 * Declaration of class SparseMatrixUnitTest
 */

//----------------------------------------------------------------------

#include <nta/test/Tester.hpp>
#include <nta/math/DenseMatrix.hpp>
#include <nta/math/SparseMatrix.hpp>
#include <nta/utils/TRandom.hpp>
#include <set>
#include <limits>
#include <vector>
#include <cmath>

//----------------------------------------------------------------------

#ifndef NTA_SPARSE_MATRIX_UNIT_TEST_HPP
#define NTA_SPARSE_MATRIX_UNIT_TEST_HPP

namespace nta {
                
  using namespace std;

  //----------------------------------------------------------------------
  class SparseMatrixUnitTest : public Tester
  {
  public:
    SparseMatrixUnitTest() {
      rng_ = new TRandom("sparse_matrix_test");
    }
    
    virtual ~SparseMatrixUnitTest() {
      delete rng_;
    }

    // Run all appropriate tests
    virtual void RunTests();

  protected:

    //--------------------------------------------------------------------------------
    template <typename Int, typename Float>
    inline void ComparePair(const std::pair<Int, Float>& p1, 
                            const std::pair<Int, Float>& p2, 
                            const char* str)
    {
      {
        std::stringstream msg;
        msg << str << " indices: " << p1.first << " and " << p2.first;
        TEST(p1.first == p2.first);
      }
      
      {
        std::stringstream msg;
        msg << str << " values: " << p1.second << " and " << p2.second;
        TEST(nta::nearlyEqual(p1.second, p2.second));
      }
    }

    //--------------------------------------------------------------------------------
    template <typename InIter1, typename InIter2>
    inline void CompareVectors(UInt n, InIter1 y1, InIter2 y2, const char* str)
    {
      InIter1 y1_begin = y1;
      InIter2 y2_begin = y2;

      ITER_1(n) {
        if (!nta::nearlyZero(::fabs((double)(*y2 - *y1)))) 
          TEST(*y1 == *y2);
        ++y1; ++y2;
      }
    }

    //--------------------------------------------------------------------------------
    template <typename T>
    inline void Compare(const std::vector<std::pair<UInt, T> >& v1,
                        const std::vector<std::pair<UInt, T> >& v2,
                        const char* str)
    {
      {
        std::stringstream msg;
        msg << str << " sizes are different: " 
            << v1.size() << " and " << v2.size();
        TEST(v1.size() == v2.size());
      }
      
      ITER_1(v1.size()) {
        if (v1[i].first != v2[i].first) {
          std::stringstream msg;
          msg << str << " indices are different at: " << i 
              << " " << v1[i].first << " and " << v2[i].first;
        }
        if (!nta::nearlyEqual(v1[i].second, v2[i].second)) {
          std::stringstream msg;
          msg << str << " values are different at: " << i 
              << " " << v1[i].second << " and " << v2[i].second;
        }
      }
    }

    /*--------------------------------------------------------------------------------
     * @param str A string to be printed on a false comparison (not equal)
     *
     *
     */
    template <typename I, typename F, typename I2, typename F2, typename Z>
    inline void Compare(const Dense<I,F>& dense, 
                        const SparseMatrix<I,F,I2,F2,Z>& sparse, 
                        const char* str, F eps =nta::Epsilon)
    {
      I nrows, ncols;
      nrows = sparse.nRows();
      ncols = sparse.nCols();

      Dense<I,F> densified(nrows, ncols);
      sparse.toDense(densified.begin());

      if (nrows != dense.nrows) {
        std::stringstream str1;
        str1 << str << " nrows";
        Test(str1.str().c_str(), nrows, dense.nrows);
      }

      if (ncols != dense.ncols) {
        std::stringstream str2;
        str2 << str << " ncols";
        TESTEQUAL(ncols, dense.ncols);
      }

      if (sparse.nNonZeros() != dense.nNonZeros()) {
        std::stringstream str3;
        str3 << str << " nnz";
        TESTEQUAL(sparse.nNonZeros(), dense.nNonZeros());
      }

      if (sparse.isZero() != dense.isZero()) {
        std::stringstream str4;
        str4 << str << " isZero";
        TESTEQUAL(sparse.isZero(), dense.isZero());
      }
      
      for (I i = 0; i != nrows; ++i) {
        if (sparse.nNonZerosOnRow(i) != dense.nNonZerosOnRow(i)) {
          std::stringstream str5;
          str5 << str << " nNonZerosOnRow (" << i << ")";
          TESTEQUAL(sparse.nNonZerosOnRow(i), 
               dense.nNonZerosOnRow(i));
        }

        if (sparse.isRowZero(i) != dense.isRowZero(i)) {
          std::stringstream str7;
          str7 << str << " isRowZero (" << i << ")";
          TESTEQUAL(sparse.isRowZero(i), dense.isRowZero(i));
        }
      }

      std::vector<I> nnz_row_sparse(nrows), nnz_row_dense(nrows);
      sparse.nNonZerosPerRow(nnz_row_sparse.begin());
      dense.nNonZerosPerRow(nnz_row_dense.begin());
      CompareVectors(nrows, nnz_row_sparse.begin(), nnz_row_dense.begin(), 
                     "nNonZerosPerRow");

      for (I j = 0; j != ncols; ++j) {
        if (sparse.nNonZerosOnCol(j) != dense.nNonZerosOnCol(j)) {
          std::stringstream str6;
          str6 << str << " nNonZerosOnCol (" << j << ")";
          TESTEQUAL(sparse.nNonZerosOnCol(j), 
               dense.nNonZerosOnCol(j));
        }

        if (sparse.isColZero(j) != dense.isColZero(j)) {
          std::stringstream str7;
          str7 << str << " isColZero (" << j << ")";
          TESTEQUAL(sparse.isColZero(j), dense.isColZero(j));
        }
      }

      std::vector<I> nnz_col_sparse(ncols), nnz_col_dense(ncols);
      sparse.nNonZerosPerCol(nnz_col_sparse.begin());
      dense.nNonZerosPerCol(nnz_col_dense.begin());
      CompareVectors(ncols, nnz_col_sparse.begin(), nnz_col_dense.begin(), 
                     "nNonZerosPerCol");

      ITER_2(nrows, ncols) 
        if (::fabs(densified.at(i,j) - dense.at(i,j)) > eps) 
          TESTEQUAL(densified.at(i,j), dense.at(i,j));
    }

    //--------------------------------------------------------------------------------
    
    //void unit_test_construction();
    //void unit_test_copy();
    //void unit_test_dense();
    //void unit_test_csr();
    //void unit_test_compact();
    //void unit_test_threshold();
    //void unit_test_getRow();
    //void unit_test_getCol();
    //void unit_test_addRowCol();
    //void unit_test_resize();
    //void unit_test_deleteRows();
    //void unit_test_deleteCols();
    //void unit_test_set();
    //void unit_test_setRowColToZero();
    //void unit_test_transpose();
    //void unit_test_vecDist();
    //void unit_test_vecMaxProd();
    //void unit_test_vecProd();
    //void unit_test_axby();
    //void unit_test_axby_2();
    //void unit_test_axby_3();
    //void unit_test_rowMax();
    //void unit_test_maxima();
    //void unit_test_normalize();  
    //void unit_test_rowProd();
    //void unit_test_lerp();
    //void unit_test_small_values();
    //void unit_test_accumulate();
    //void unit_test_multiply();   
    //void unit_test_argMax();
    //void unit_test_argMin();
    //void unit_test_rowMax_2();
    //void unit_test_rowMin();
    //void unit_test_colMax();
    //void unit_test_colMin();
    //void unit_test_nNonZeros();
    //void unit_test_extract();
    //void unit_test_complex();
    //void unit_test_usage();
    //void unit_test_deleteRow();

    // Use our own random number generator for reproducibility
    TRandom *rng_;

    // Default copy ctor and assignment operator forbidden by default
    SparseMatrixUnitTest(const SparseMatrixUnitTest&);
    SparseMatrixUnitTest& operator=(const SparseMatrixUnitTest&);

    typedef Dense<UInt,Real> DenseMat;
    typedef SparseMatrix<UInt,Real,Int,Real> SparseMat;

  }; // end class SparseMatrixUnitTest
    
  //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_SPARSE_MATRIX_UNIT_TEST_HPP

