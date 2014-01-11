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
 * Declaration of class SparseMatrix01UnitTest
 */

//----------------------------------------------------------------------

#include "SparseMatrixUnitTest.hpp"
#include <nta/math/SparseMatrix01.hpp>
#include <nta/utils/TRandom.hpp>

//----------------------------------------------------------------------

#ifndef NTA_SPARSE_MATRIX01UNIT_TEST_HPP
#define NTA_SPARSE_MATRIX01UNIT_TEST_HPP

// Work around terrible Windows legacy issue - min and max global macros!!!
#ifdef max
#undef max
#endif

namespace nta {
  
  template <typename Int, typename Float>
  struct Dense01
  {
    typedef std::vector<Float> Memory;
    typedef typename Memory::iterator iterator;
    typedef typename Memory::const_iterator const_iterator;

    Int nrows, ncols;
    Memory m;
    
    Dense01(Int nr, Int nc)
      : nrows(nr), ncols(nc), m(nr*nc, 0)
    {}

    Dense01(Int nr, Int nc, Int nzr, bool small =false, bool emptyRows =false)
      : nrows(nr), ncols(nc),
        m(nr*nc, 0)
    {
      ITER_2(nrows, ncols)
        at(i,j) = 1;
      
      if (nzr > 0 && ncols / nzr > 0) {
        ITER_2(nrows, ncols)
          if (j % (ncols / nzr) == 0) 
            at(i,j) = 0.0;
      }

      if (emptyRows) 
        for (Int i = 0; i < nrows; i += 2) 
          for (Int j = 0; j < ncols; ++j)
            at(i,j) = 0.0;
    }

    ~Dense01() {}

    inline iterator begin() { return m.begin(); }
    inline const_iterator begin() const { return m.begin(); }
    inline iterator begin(const Int i) { return m.begin() + i*ncols; }
    inline const_iterator begin(const Int i) const { return m.begin() + i*ncols; }
    
    inline Float& at(const Int i, const Int j) 
    {
      return *(m.begin() + i*ncols + j);
    }

    inline const Float& at(const Int i, const Int j) const
    {
      return *(m.begin() + i*ncols + j);
    }

	  template <typename InIter>
    inline void deleteRows(InIter del, InIter del_end)
    {
      Int nrows_new = nrows - (del_end - del);
      std::set<Int> del_set(del, del_end);
      std::vector<Float> new_m(nrows_new * ncols);
      UInt i1 = 0;
      for (UInt i = 0; i < nrows; ++i) {
        if (del_set.find(i) == del_set.end()) {
          for (UInt j = 0; j < ncols; ++j) 
            new_m[i1*ncols + j] = at(i,j);
          ++i1;
        }
      }
      std::swap(m, new_m);
      nrows = nrows_new;
    }

    template <typename InIter>
    inline void deleteColumns(InIter del, InIter del_end)
    {
      Int ncols_new = ncols - (del_end - del);
      std::set<Int> del_set(del, del_end);
      std::vector<Float> new_m(nrows * ncols_new);
      UInt j1 = 0;
      for (UInt j = 0; j < ncols; ++j) {
        if (del_set.find(j) == del_set.end()) {
          for (UInt i = 0; i < nrows; ++i) 
            new_m[i*ncols_new + j1] = at(i,j);
          ++j1;
        }
      }
      std::swap(m, new_m);
      ncols = ncols_new;
    }

    void fromCSR(std::stringstream& stream)
    {
      std::string tag;
      stream >> tag;
      Int nnz, nnzr, j;
      stream >> nrows >> ncols >> nnz >> nnzr;

      m.resize(nrows*ncols);
      std::fill(m.begin(), m.end(), Real(0));

      for (Int i = 0; i < nrows; ++i) {
        stream >> nnzr;
        for (Int k = 0; k < nnzr; ++k) {
          stream >> j;
          at(i,j) = 1;
        }
      }
    }

    Int nnz() const
    {
      Int n = 0;
      ITER_1(nrows*ncols)
        if (m[i] > 0)
          ++n;
      return n;
    }

    void clear()
    {
      std::fill(m.begin(), m.end(), Real(0));
    }

    Int nNonZerosRow(Int row) const
    {
      Int n = 0;
      for (Int j = 0; j < ncols; ++j)
        if (at(row,j) > 0)
          ++n;
      return n;
    }

    bool isZero() const
    {
      ITER_1(nrows*ncols)
        if (!nta::nearlyZero(m[i]))
          return false;
      return true;
    }
    
    template <typename InIter, typename OutIter>
    void vecDistSquared(InIter x, OutIter y)
    {
      for (Int i = 0; i < nrows; ++i) {
        Float val = 0;
        for (Int j = 0; j < ncols; ++j) 
          val += (at(i,j) - x[j]) * (at(i,j) - x[j]);
        y[i] = val;
      }
    }

    template <typename InIter, typename OutIter>
    void vecDist(InIter x, OutIter y)
    {
      for (Int i = 0; i < nrows; ++i) {
        Float val = 0;
        for (Int j = 0; j < ncols; ++j) 
          val += (at(i,j) - x[j]) * (at(i,j) - x[j]);
        y[i] = sqrt(val);
      }
    }

    template <typename InIter>
    Float rowDistSquared(const Int& row, InIter x)
    {
      Float val = 0;
      for (Int j = 0; j < ncols; ++j) 
        val += (x[j] - at(row,j)) * (x[j] - at(row,j));
      return val;
    }

    template <typename InIter, typename OutIter>
    void vecMaxProd(InIter x, OutIter y)
    {
      for (Int i = 0; i < nrows; ++i) {
        Float max = - std::numeric_limits<Float>::max();
        for (Int j = 0; j < ncols; ++j)
          if (at(i,j) * x[j] > max)
            max = at(i,j) * x[j];
        y[i] = max;
      }
    }

    template <typename InIter, typename OutIter>
    void rightVecProd(InIter x, OutIter y)
    {
      for (Int i = 0; i < nrows; ++i) {
        Float s = 0;
        for (Int j = 0; j < ncols; ++j)
          s += at(i,j) * x[j];
        y[i] = s;
      }
    }

    template <typename InIter>
    std::pair<Int, Float> closestEuclidean(InIter x)
    {
      Float val, min_val = std::numeric_limits<Float>::max();
      Int arg_i = 0;
    
      for (Int i = 0; i < nrows; ++i) {
        val = 0;
        for (Int j = 0; j < ncols; ++j) 
          val += (at(i,j) - x[j]) * (at(i,j) - x[j]);
        if (val < min_val) {
          min_val = val;
          arg_i = i;
        }
      }
    
      return make_pair(arg_i, sqrt(min_val));
    }

    template <typename InIter>
    std::pair<Int, Float> closestDot(InIter x)
    {
      Float val, max_val = - std::numeric_limits<Real>::max();
      Int arg_i = 0;
    
      for (Int i = 0; i < nrows; ++i) {
        val = 0;
        for (Int j = 0; j < ncols; ++j) 
          val += at(i,j) * x[j];
        if (val > max_val) {
          max_val = val;
          arg_i = i;
        }
      }

      return make_pair(arg_i, max_val);
    }

    template <typename InIter, typename OutIter>
    void rowMax(InIter x, OutIter y)
    {
      for (Int i = 0; i < nrows; ++i) {
        Int arg_j = 0;
        Float max_val = 0; //- std::numeric_limits<Float>::max();
        for (Int j = 0; j < ncols; ++j)
          if (at(i,j) > 0 && x[j] > max_val) {
            arg_j = j;
            max_val = x[j];
          }
        y[i] = Real(arg_j);
      }
    }

    template <typename InIter, typename OutIter>
    void rowProd(InIter x, OutIter y)
    {
      for (Int i = 0; i < nrows; ++i) {
        Float val = 1.0;
        for (Int j = 0; j < ncols; ++j)
          if (at(i,j) > 0)
            val *= x[j];
        y[i] = val;
      }
    }

    template <typename Int2, typename Float2>
    NTA_HIDDEN friend std::ostream& operator<<(std::ostream&, 
					       const Dense01<Int2, Float2>&);
  };

  template <typename Int, typename Float>
  std::ostream& operator<<(std::ostream& out, const Dense01<Int, Float>& d)
  {
    for (Int i = 0; i < d.nrows; ++i) {
      for (Int j = 0; j < d.ncols; ++j) 
        out << d.at(i,j) << " ";
      out << std::endl;
    }
    
    return out;
  }

  //--------------------------------------------------------------------------------
  class SparseMatrix01UnitTest : public Tester
  {
  public:
    SparseMatrix01UnitTest() {
      rng_ = new TRandom("sparse_matrix01_test");
    }
    virtual ~SparseMatrix01UnitTest() {
      delete rng_;
    }

    // Run all appropriate tests
    virtual void RunTests();

  private:

    //--------------------------------------------------------------------------------
    template <typename Int, typename Float>
    void ComparePair(std::pair<Int, Float> p1, std::pair<Int, Float> p2, 
                     const char* str)
    {
      Test(str, p1.first, p2.first);
      Test(str, p1.second, p2.second);
    }

    //--------------------------------------------------------------------------------
    template <typename InIter1, typename InIter2>
    void CompareVectors(UInt n, InIter1 y1, InIter2 y2, const char* str)
    {
      for (UInt i = 0; i < n; ++i, ++y1, ++y2) {
        if (!nta::nearlyZero(::fabs(*y2 - *y1)))
          Test(str, *y1, *y2);
      }
    }

    //--------------------------------------------------------------------------------
    template <typename Int, typename Float>
    void Compare(const Dense01<Int, Float>& dense, 
                 const SparseMatrix01<Int, Float>& sparse, 
                 const char* str)
    {
      Int nrows, ncols;
      nrows = sparse.nRows();
      ncols = sparse.nCols();

      Dense01<Int, Float> densified(nrows, ncols);
      sparse.toDense(densified.begin());

      if (nrows != dense.nrows) {
        std::stringstream str1;
        str1 << str << " nrows";
        Test(str1.str().c_str(), nrows, dense.nrows);
      }

      if (ncols != dense.ncols) {
        std::stringstream str2;
        str2 << str << " ncols";
        Test(str2.str().c_str(), ncols, dense.ncols);
      }

      if (sparse.nNonZeros() != dense.nnz()) {
        std::stringstream str3;
        str3 << str << " nnz";
        Test(str3.str().c_str(), sparse.nNonZeros(), dense.nnz());
      }

      if (sparse.isZero() != dense.isZero()) {
        std::stringstream str4;
        str4 << str << " isZero";
        Test(str4.str().c_str(), sparse.isZero(), dense.isZero());
      }
      
      for (Int i = 0; i < nrows; ++i) 
        if (sparse.nNonZerosRow(i) != dense.nNonZerosRow(i)) {
          std::stringstream str5;
          str5 << str << " nNonZerosRow(" << i << ")";
          Test(str5.str().c_str(), sparse.nNonZerosRow(i), dense.nNonZerosRow(i));
        }

      ITER_2(nrows, ncols) 
        if (!nta::nearlyZero(::fabs(densified.at(i,j) - dense.at(i,j))))
          Test(str, densified.at(i,j), dense.at(i,j));
    }

    //--------------------------------------------------------------------------------
    
    //void unit_test_construction();
    //void unit_test_fromDense();
    //void unit_test_csr();
    //void unit_test_compact();
    //void unit_test_getRowSparse();
    //void unit_test_addRow();
    //void unit_test_addUniqueFilteredRow();
    //void unit_test_addMinHamming();
    //void unit_test_deleteRows();
    //void unit_test_deleteColumns();
    //void unit_test_rowDistSquared();
    //void unit_test_vecDistSquared();
    //void unit_test_vecDist();
    //void unit_test_closestEuclidean();
    //void unit_test_closestDot();
    //void unit_test_vecMaxProd();
    //void unit_test_vecProd();
    //void unit_test_rowMax();
    //void unit_test_rowProd();
    //void unit_test_row_counts();
    //void unit_test_print();
    //void unit_test_numerical_accuracy();
    //
    //void unit_test_usage();

    // Use our own random number generator for reproducibility
    TRandom *rng_;

    // Default copy ctor and assignment operator forbidden by default
    SparseMatrix01UnitTest(const SparseMatrix01UnitTest&);
    SparseMatrix01UnitTest& operator=(const SparseMatrix01UnitTest&);

  }; // end class SparseMatrix01UnitTest
    
  //----------------------------------------------------------------------
} // end namespace nta

#endif // NTA_SPARSE_MATRIX01UNIT_TEST_HPP



