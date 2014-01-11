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
 * External algorithms that operate on SparseMatrix.
 */

#ifndef NTA_SM_ALGORITHMS_HPP
#define NTA_SM_ALGORITHMS_HPP

#include <vector>
#include <nta/utils/Random.hpp>

//--------------------------------------------------------------------------------
namespace nta {

  /**
   * A collection of algorithms that operate on SparseMatrix. They are put here 
   * instead of directly in the SparseMatrix because they are not as general 
   * as the SparseMatrix methods. They are usually tailored for a specific, sometimes
   * experimental, algorithm. This struct is a friend of SparseMatrix, so that it 
   * can access iterators on the indices and values of the non-zeros that are not 
   * made public in SparseMatrix. In the following methods, template parameter "SM"
   * stands for a SparseMatrix type.
   */
  struct SparseMatrixAlgorithms 
  {
    //--------------------------------------------------------------------------------
    /**
     * Computes the entropy rate of a sparse matrix, along the rows or the columns. 
     * This is defined as:
     * sum(-nz[i,j] * log2(nz[i,j]) * sum_of_row[i], for all i,j), i.e.
     * the usual definition of entropy, but weighted by the probability of the rows
     * or column, i.e. the probability of the conditional distributions.
     * 
     * A copy of the matrix passed in is performed, and the copy is normalized to 
     * give it the meaning of a joint distribution. This is pretty slow.
     *
     * TODO:
     * 
     * I don't think the matrix needs to be normalized (which means rowwise normalization). 
     You've already computed the "row sums", which are the per-row normalization factor, 
     and you can use this in the entropy calculation. i.e. if n is the norm of a single row 
     and x[i] is the original value and xn[i] = x[i]/n is the normalized value then 
     the partial contribution for that row is: 
     - n * sum xn[i] * ln xn[i] 
     = - n * sum x[i]/n * ln x[i]/n 
     = - sum x[i] *( ln x[i] - ln[n]) 
     = sum x[i] ln[n] - sum x[i] ln x[i] 
     = n ln [n] - sum x[i] ln x[i] 
     
     In other words, you compute the entropy based on the non-normalized matrix and then 
     add n ln[n] (There may be an error in this calculation, but in any case, I'm pretty 
     sure you don't actually need to normalize the matrix) 
     */
    template <typename SM>
    static typename SM::value_type entropy_rate(const SM& sm)
    {
      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      SM m(sm);
      
      std::vector<value_type> s(m.nRows());
      
      m.rowSums(s);
      nta::normalize(s);
      m.normalizeRows();
      
      value_type e = 0;

      Log2<value_type> log2_f;

      for (size_type i = 0; i != m.nRows(); ++i) {
        value_type ee = 0;
        const value_type* nz = m.nz_begin_(i);
        const value_type* nz_end = m.nz_end_(i);
        for (; nz != nz_end; ++nz) 
          ee += *nz * log2_f(*nz);
        e -= s[i] * ee;
      }
      
      return e;
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes an entropy on a "smoothed" SM, for each row and for each column.
     * Smoothes by simply adding 1 to each count as the entropy is calculated.
     */
    template <typename SM, typename OutputIter>
    static void matrix_entropy(const SM& sm, OutputIter row_out, OutputIter row_out_end,
                               OutputIter col_out, OutputIter col_out_end,
                               typename SM::value_type s = 1.0)
    {
      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      { // Pre-conditions
        NTA_CHECK((size_type)(row_out_end - row_out) == sm.nRows())
          << "entropy_smooth: Invalid size for output vector: " 
          << (size_type)(row_out_end - row_out)
          << " - Should be number of rows: " << sm.nRows();
        NTA_CHECK((size_type)(col_out_end - col_out) == sm.nCols())
          << "entropy_smooth: Invalid size for output vector: "
          << (size_type)(col_out_end - col_out)
          << " - Should be number of columns: " << sm.nCols();
      } // End pre-conditions

      size_type m = sm.nRows(), n = sm.nCols();

      std::vector<value_type> row_sums(m, (value_type) n * s);
      std::fill(sm.indb_, sm.indb_ + n, (size_type) 0);
      std::fill(sm.nzb_, sm.nzb_ + n, (value_type) m * s);

      for (size_type row = 0; row != m; ++row) {
        size_type *ind = sm.ind_[row], *ind_end = ind + sm.nnzr_[row];
        value_type *nz = sm.nz_[row];
        for (; ind != ind_end; ++ind, ++nz) {
          row_sums[row] += *nz;
          sm.nzb_[*ind] += *nz;
          sm.indb_[*ind] += (size_type) 1;
        }
      }

      Log2<value_type> log2_f;
      
      for (size_type c = 0; c != n; ++c) {
        value_type v = s / sm.nzb_[c];
        *(col_out + c) = - ((value_type)(m - sm.indb_[c]) * v * log2_f(v));
      }

      for (size_type row = 0; row != m; ++row, ++row_out) {
        size_type *ind = sm.ind_[row], *ind_end = ind + sm.nnzr_[row];
        value_type *nz = sm.nz_[row];
        value_type v = s / row_sums[row];
        *row_out = - ((value_type)(n - sm.nnzr_[row]) * v * log2_f(v));
        for (; ind != ind_end; ++ind, ++nz) {
          v = *nz + s;
          value_type val_row = v / row_sums[row];
          *row_out -= val_row * log2_f(val_row);
          value_type val_col = v / sm.nzb_[*ind];
          *(col_out + *ind) -= val_col * log2_f(val_col);
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Multiplies the 'X' matrix by the constant 'a', 
     * then adds 'b * X * Y' to it, in-place.
     *  for row in [0,nrows):
     *   for col in [0,ncols):
     *    X[row,col] = X[row,col]  * (a + b * Y[row,col])
     *
     * @param a [value_type] a coefficient
     * @param b [value_type] b coefficient
     * @param B [const SparseMatrix<size_type, value_type>] Y matrix
     *
     */
    template <typename SM1, typename SM2>
    static void 
    aX_plus_bX_elementMultiply_Y(const typename SM1::value_type &a, SM1 &Xoutput, 
                                 const typename SM1::value_type &b, const SM2& Y)
    {
      typedef typename SM1::size_type size_type;
      typedef typename SM1::value_type value_type;

      const size_type nrows = Xoutput.nRows();

      for (size_type row = 0; row != nrows; ++row) {

        value_type *nz_write = Xoutput.nz_begin_(row);
        size_type *ind_write = Xoutput.ind_begin_(row);
        const size_type *ind_x_begin = ind_write;

        const value_type *nz_x = Xoutput.nz_begin_(row);
        const size_type *ind_x = ind_x_begin;
        const size_type *ind_x_end = Xoutput.ind_end_(row);

        const typename SM2::value_type *nz_y = Y.nz_begin_(row);
        const typename SM2::size_type *ind_y = Y.ind_begin_(row);
        const typename SM2::size_type *ind_y_begin = ind_y;
        const typename SM2::size_type *ind_y_end = Y.ind_end_(row);

        while (ind_x != ind_x_end) {

          const size_type column = *(ind_x++);
          const value_type vx = *(nz_x++);
          value_type val = vx * a;
          ind_y = std::lower_bound(ind_y, ind_y_end, column);

          if (ind_y != ind_y_end && column == *ind_y) {
            const value_type vy = (value_type) nz_y[ind_y - ind_y_begin];
            val += vx * vy * b;
            ++ind_y;
          }

          // Could save this check, but it should usually
          // be predictable.
          if (!Xoutput.isZero_(val)) { 
            *ind_write++ = column;
            *nz_write++ = val; 
          }
        }

        Xoutput.nnzr_[row] = (size_type)(ind_write - ind_x_begin);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Used to speed up sparse pooler algorithm.
     *
     * TODO: describe algo.
     */
    template <typename SM, typename InIter1, typename OutIter>
    static void 
    kthroot_product(const SM& sm, 
                    typename SM::size_type ss, InIter1 x, OutIter y, 
                    const typename SM::value_type& min_input)
    {
      using namespace std;

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;
      
      {
        NTA_ASSERT(sm.nCols() % ss == 0)
          << "SparseMatrix kthroot_product: "
          << "Invalid segment size: " << ss
          << "Needs to be a divisor of nCols() = " << sm.nCols();
      }

      Log<value_type> log_f;
      Exp<value_type> exp_f;

      const size_type k = sm.nCols() / ss;
      const value_type log_min_input = logf(min_input);

      OutIter y_begin = y, y_end = y_begin + sm.nCols();

      for (size_type row = 0; row != sm.nRows(); ++row) {

        value_type sum = (value_type) 0.0f;
        size_type seg_begin = 0, seg_end = ss;
        size_type *ind = sm.ind_begin_(row), *ind_end = sm.ind_end_(row);
        for (; seg_begin != sm.nCols(); seg_begin += ss, seg_end += ss) {
          if (ind < ind_end && seg_begin <= *ind && *ind < seg_end) {
            size_type *c2 = seg_end == sm.nCols() ? ind_end : sm.pos_(row, seg_end);
            for (; ind != c2; ++ind) {
              value_type val = x[*ind];
              if (sm.isZero_(val)) 
                sum += log_min_input;
              else 
                sum += log_f(val);
            }
          } else {
            value_type max_value = - std::numeric_limits<value_type>::max();
            for (size_type i = seg_begin; i != seg_end; ++i)
              max_value = std::max(x[i], max_value);
            sum += log_f(std::max((value_type)1.0f - max_value, min_input));
            ind = seg_end == sm.nCols() ? ind_end : sm.pos_(row, seg_end);
          }
        }
	// On x86_64, there is a bug in glibc that makes expf very slow
	// (more than it should be), so we continue using exp on that 
	// platform as a workaround.
	// https://bugzilla.redhat.com/show_bug.cgi?id=521190
	// To force the compiler to use exp instead of expf, the return
	// type (and not the argument type!) needs to be double.
        *y = exp_f(sum / k);
        ++y;
      }
      if (positive_less_than(y_begin, y_end, min_input))
        std::fill(y_begin, y_end, (value_type) 0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of a sparse matrix and a sparse vector on the right. 
     * [x_begin, x_end) is the range of x that contains the non-zeros for x.
     * This function skips multiplying by zeros out of [x_begin, x_end).
     * This is used only in nta/math_research/shmm.cpp and direct unit testing 
     * is missing.
     *
     * TODO: check if we can't remove that and replace by incrementOuterWithNZ
     */
    template <typename SM, typename InputIterator1, typename InputIterator2>
    static void sparseRightVecProd(const SM& sm, 
                                   typename SM::size_type x_begin,
                                   typename SM::size_type x_end,
                                   InputIterator1 x,
                                   InputIterator2 y)
    {
      { // Pre-conditions
        sm.assert_valid_col_range_(x_begin, x_end, "sparseRightVecProd: Invalid range");
      } // End pre-conditions

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      for (size_type row = 0; row != sm.nRows(); ++row, ++y) {
        size_type nnzr = sm.nNonZerosOnRow(row);
        if (nnzr == 0) {
          *y = 0;
          continue;
        }
        size_type *ind = sm.ind_begin_(row), *ind_end = sm.ind_end_(row);
        size_type *p1 = std::lower_bound(ind, ind_end, x_begin);
        if (p1 == ind_end) {
          *y = 0;
          continue;
        }
        size_type *p2 = std::lower_bound(p1, ind_end, x_end);
        value_type *nz = sm.nz_begin_(row) + (p1 - ind);
        value_type val = 0;
        for (ind = p1; ind != p2; ++ind, ++nz)
          val += *nz * *(x + *ind);
        *y = val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Wrapper for iterator-based sparseRightVecProd that takes std::vectors.
     *
     * TODO: can we remove?
     */
    /*
    template <typename SM>
    static void sparseRightVecProd(const SM& sm, 
                                   typename SM::size_type x_begin,
                                   typename SM::size_type x_end,
                                   const std::vector<typename SM::value_type>& x,
                                   std::vector<typename SM::value_type>& y)
    {
      { // Pre-conditions
        NTA_ASSERT(x.size() == sm.nCols())
          << "sparseRightVecProd: Wrong size for x: " << x.size()
          << " when sparse matrix has: " << sm.nCols() << " columns";
        NTA_ASSERT(y.size() == sm.nRows())
          << "sparseRightVecProd: Wrong size for y: " << y.size()
          << " when sparse matrix has: " << sm.nRows() << " rows";
        sm.assert_valid_col_range_(x_begin, x_end, "sparseRightVecProd: Invalid range");
      } // End pre-conditions

      SparseMatrixAlgorithms::sparseRightVecProd(sm, x_begin, x_end, x.begin(), y.begin());
    }
    */

    //--------------------------------------------------------------------------------
    /**
     * Computes a smoothed version of all rows vec max prod, that is:
     *
     * for row in [0,nrows):
     *  y[row] = max((this[row,col] + k) * x[col], for col in [0,ncols))
     *
     */
    template <typename SM, typename InputIterator, typename OutputIterator>
    static void smoothVecMaxProd(const SM& sm, 
				 typename SM::value_type k,
				 InputIterator x, InputIterator x_end,
				 OutputIterator y, OutputIterator y_end)
    {
      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      { // Pre-conditions
	NTA_ASSERT((size_type)(x_end - x) == sm.nCols());
	NTA_ASSERT((size_type)(y_end - y) == sm.nRows());
      } // End pre-conditions

      // Compute k * x only once, and cache result in sm.nzb_
      for (size_type j = 0; j != sm.nCols(); ++j)
	sm.nzb_[j] = k * x[j];

      for (size_type row = 0; row != sm.nRows(); ++row) {

        value_type max_v = - std::numeric_limits<value_type>::max();
	size_type *ind = sm.ind_[row], *ind_end = ind + sm.nnzr_[row];
        value_type *nz = sm.nz_[row];

	for (size_type col = 0; col != sm.nCols(); ++col) {

	  value_type p = sm.nzb_[col];
	  if (ind != ind_end && col == *ind)
	    p += *nz++ * x[*ind++];
          if (p > max_v) 
            max_v = p; 
        }
	
        *y++ = max_v;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes a smoothed version of all rows vec arg max prod, that is:
     *
     * for row in [0,nrows):
     *  y[row] = argmax((this[row,col] + k) * x[col], for col in [0,ncols))
     *
     */
    template <typename SM, typename InputIterator, typename OutputIterator>
    static void smoothVecArgMaxProd(const SM& sm, 
				    typename SM::value_type k,
				    InputIterator x, InputIterator x_end,
				    OutputIterator y, OutputIterator y_end)
    {
      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      { // Pre-conditions
	NTA_ASSERT((size_type)(x_end - x) == sm.nCols());
	NTA_ASSERT((size_type)(y_end - y) == sm.nRows());
      } // End pre-conditions

      // Compute k * x only once, and cache result in sm.nzb_
      for (size_type j = 0; j != sm.nCols(); ++j)
	sm.nzb_[j] = k * x[j];

      for (size_type row = 0; row != sm.nRows(); ++row) {

	size_type arg_max = 0;
        value_type max_v = - std::numeric_limits<value_type>::max();
	size_type *ind = sm.ind_[row], *ind_end = ind + sm.nnzr_[row];
        value_type *nz = sm.nz_[row];

	for (size_type col = 0; col != sm.nCols(); ++col) {

	  value_type p = sm.nzb_[col];
	  if (ind != ind_end && col == *ind)
	    p += *nz++ * x[*ind++];
          if (p > max_v) {
            max_v = p; 
	    arg_max = col;
	  }
        }
	
        *y++ = arg_max;
      }
    }

    //--------------------------------------------------------------------------------
    //--------------------------------------------------------------------------------
    // LBP (Loopy Belief Propagation)
    //
    // This section contains algorithms that were written to speed-up LBP operations.
    //
    //--------------------------------------------------------------------------------

    /**
     * Adds a value to the non-zeros of a SparseMatrix.
     * If minFloor > 0, values < minFloor are replaced by minFloor.
     */
    template <typename SM>
    static void addToNZOnly(SM& A, double val, typename SM::value_type minFloor =0)
    {
      {
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      size_type M = A.nRows();

      if (minFloor == 0) {

        // Can introduce new zeros
        for (size_type row = 0; row != M; ++row) {

          value_type *nz = A.nz_begin_(row);
          value_type *nz_end = A.nz_end_(row);
          value_type *nz_dst = nz;

          for (; nz != nz_end; ++nz) {
            value_type v = *nz + val;
            if (!A.isZero_(v)) 
              *nz_dst++ = v;
          }

          A.nnzr_[row] = nz_dst - A.nz_begin_(row);
        }

      } else { // if minFloor != 0
        
        nta::Abs<value_type> abs_f;
        
        // Doesn't change the number of non-zeros
        for (size_type row = 0; row != M; ++row) {

          size_type *ind = A.ind_begin_(row);
          size_type *ind_end = ind + A.nnzr_[row];
          value_type *nz = A.nz_begin_(row);

          for (; ind != ind_end; ++ind, ++nz) {
            *nz += val;
            if (abs_f(*nz) < minFloor)
              *nz = minFloor;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds vector to non-zeros only, down the columns. If minFloor is > 0, any
     * element that drop below minFloor are replaced by minFloor.
     */
    template <typename SM, typename U>
    static void addToNZDownCols(SM& A, U begin, U end, 
                                typename SM::value_type minFloor =0)
    {
      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      {
        NTA_ASSERT((size_type)(end - begin) == A.nCols());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      if (minFloor == 0) {

        for (size_type row = 0; row != A.nRows(); ++row) {
          size_type *ind = A.ind_begin_(row);
          value_type *nz = A.nz_begin_(row);
          value_type *nz_end = A.nz_end_(row);
          for (; nz != nz_end; ++ind) {
            *nz += *(begin + *ind);
            if (!A.isZero_(*nz)) 
              ++nz;
          }
          A.nnzr_[row] = (size_type) (nz - A.nz_begin_(row));
        }

      } else { // if minFloor != 0

        nta::Abs<value_type> abs_f;

        for (size_type row = 0; row != A.nRows(); ++row) {
          size_type *ind = A.ind_begin_(row);
          value_type *nz = A.nz_begin_(row);
          value_type *nz_end = A.nz_end_(row);
          for (; nz != nz_end; ++ind, ++nz) {
            *nz += *(begin + *ind);
            if (abs_f(*nz) < minFloor) 
              *nz = minFloor;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds vector to non-zeros only, across the rows. If minFloor is > 0, any
     * element that drop below minFloor are replaced by minFloor.
     */
    template <typename SM, typename U>
    static void addToNZAcrossRows(SM& A, U begin, U end, 
                                  typename SM::value_type minFloor =0)
    {
      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      {
        NTA_ASSERT((size_type)(end - begin) == A.nRows());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      if (minFloor == 0) {

        // Can introduce new zeros
        for (size_type row = 0; row != A.nRows(); ++row) {
          size_type *ind = A.ind_begin_(row);
          value_type *nz = A.nz_begin_(row);
          value_type *nz_end = A.nz_end_(row);
          for (; nz != nz_end; ++ind) {
            *nz += *begin;
            if (!A.isZero_(*nz)) 
              ++nz;
          }
          A.nnzr_[row] = (size_type) (nz - A.nz_begin_(row));
          ++begin;
        }

      } else { // if minFloor != 0

        nta::Abs<value_type> abs_f;

        // Doesn't change the number of non-zeros
        for (size_type row = 0; row != A.nRows(); ++row) {
          size_type *ind = A.ind_begin_(row);
          value_type *nz = A.nz_begin_(row);
          value_type *nz_end = A.nz_end_(row);
          for (; nz != nz_end; ++ind, ++nz) {
            *nz += *begin;
            if (abs_f(*nz) < minFloor) 
              *nz = minFloor;
          }
          ++begin;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Replaces non-zeros by 1 - non-zero value. This can introduce new zeros, but
     * not any new zero.
     *
     * TODO: clarify.
     */
    template <typename SM>
    static void NZOneMinus(SM& A)
    {
      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      for (size_type row = 0; row != A.nRows(); ++row) {
        size_type *ind = A.ind_begin_(row);
        value_type *nz = A.nz_begin_(row);
        value_type *nz_end = A.nz_end_(row);
        for (; nz != nz_end; ++ind) {
          *nz = (value_type) 1.0 - *nz;
          if (!A.isZero_(*nz))
            ++nz;
        }
        A.nnzr_[row] = (size_type) (nz - A.nz_begin_(row));
      }
    }
    
    //--------------------------------------------------------------------------------
    /**
     * Adds the non-zeros of B to the non-zeros of A. Assumes that everywhere B has
     *  a non-zeros, A has a non-zero. Non-zeros of A that don't match up with a 
     *  non-zero of B are unaffected.  
     *
     * [[1 0 2]    +   [[3 0 0]     =    [[4 0 2]
     *  [0 3 0]]        [0 1 0]]          [0 4 0]]
     */
    template <typename SM>
    static void addNoAlloc(SM& A, const SM& B, typename SM::value_type minFloor =0)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(B.nonZeroIndicesIncluded(A));
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      nta::Abs<value_type> abs_f;

      size_type M = A.nRows();

      for (size_type row = 0; row != M; ++row) {

        size_type *ind_a = A.ind_begin_(row);
        size_type *ind_b = B.ind_begin_(row);
        size_type *ind_b_end = B.ind_end_(row);
        value_type *nz_a = A.nz_begin_(row);
        value_type *nz_b = B.nz_begin_(row);

        while (ind_b != ind_b_end) {
          if (*ind_a == *ind_b) {
            value_type a = *nz_a;
            value_type b = *nz_b;
            a += b;
            if (minFloor > 0 && abs_f(a) < minFloor) 
              a = minFloor;
            *nz_a = a;
            NTA_ASSERT(!A.isZero_(*nz_a));
            ++ind_a; ++nz_a;
            ++ind_b; ++nz_b;
          } else if (*ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Subtracts the non-zeros of B from the non-zeros of A. Assumes that everywhere B has
     *  a non-zeros, A has a non-zero. Non-zeros of A that don't match up with a 
     *  non-zero of B are unaffected.  
     *
     * [[1 0 2]    -   [[3 0 0]     =    [[-2 0 2]
     *  [0 3 0]]        [0 1 0]]          [0 2 0]]
     */
    template <typename SM>
    static void subtractNoAlloc(SM& A, const SM& B, typename SM::value_type minFloor =0)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(B.nonZeroIndicesIncluded(A));
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      nta::Abs<value_type> abs_f;

      size_type M = A.nRows();

      for (size_type row = 0; row != M; ++row) {

        size_type *ind_a = A.ind_begin_(row);
        size_type *ind_b = B.ind_begin_(row);
        size_type *ind_b_end = B.ind_end_(row);
        value_type *nz_a = A.nz_begin_(row);
        value_type *nz_b = B.nz_begin_(row);

        while (ind_b != ind_b_end) {
          if (*ind_a == *ind_b) {
            value_type a = *nz_a;
            value_type b = *nz_b;
            a -= b;
            if (minFloor > 0 && abs_f(a) < minFloor) 
              a = minFloor;
            *nz_a = a;
            NTA_ASSERT(!A.isZero_(*nz_a));
            ++ind_a; ++nz_a;
            ++ind_b; ++nz_b;
          } else if (*ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Copies the values of the non-zeros of B into A, where A and B have a non-zero
     * in the same location. Leaves the other non-zeros of A unchanged.
     *
     * TODO: move to SM copy, with parameter to re-use memory
     */
    template <typename SM>
    static void assignNoAlloc(SM& A, const SM&B)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
      }

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      const size_type M = A.nRows();

      for (size_type row = 0; row != M; ++row) {

        size_type *ind_a = A.ind_begin_(row);
        size_type *ind_b = B.ind_begin_(row);
        value_type *nz_a = A.nz_begin_(row);
        value_type *nz_a_end = A.nz_end_(row);
        value_type *nz_b = B.nz_begin_(row);
        value_type *nz_b_end = B.nz_end_(row);

        while (nz_a != nz_a_end && nz_b != nz_b_end)
          if (*ind_a == *ind_b) {
            *nz_a = *nz_b;
            ++ind_a; ++ind_b;
            ++nz_a; ++nz_b;
          } else if (*ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          } else if (*ind_b < *ind_a) {
            ++ind_b; ++nz_b;
          }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Copies the values of the non-zeros of B into A, only where A and B have a 
     * non-zero in the same location. The other non-zeros of A are left unchanged.
     * SM2 is assumed to be a binary matrix.
     * 
     * TODO: maybe a constructor of SM, or a copy method with an argument to re-use 
     * the memory.
     */
    template <typename SM, typename SM01>
    static void assignNoAllocFromBinary(SM& A, const SM01&B)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
      }

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      const size_type M = A.nRows();

      for (size_type row = 0; row != M; ++row) {

        size_type *ind_a = A.ind_begin_(row);
        typename SM01::Row::const_iterator ind_b = B.ind_begin_(row);
        typename SM01::Row::const_iterator ind_b_end = B.ind_end_(row);
	value_type *nz_a = A.nz_begin_(row);
	value_type *nz_a_end = A.nz_end_(row);

        while (nz_a != nz_a_end && ind_b != ind_b_end)
          if (*ind_a == *ind_b) {
            *nz_a = (value_type) 1;
            ++ind_a; ++ind_b;
            ++nz_a; 
          } else if (*ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          } else if (*ind_b < *ind_a) {
            ++ind_b;
          }
      }
    }
	  //--------------------------------------------------------------------------------
	  /**
	   * Adds a constant value on nonzeros of one SparseMatrix(B) to another (A).
	   */
	  template <typename SM, typename SM01>
	  static void addConstantOnNonZeros(SM& A, const  SM01& B,
										typename SM::value_type cval)
	  {
		  { // Pre-conditions
			  NTA_ASSERT(A.nRows() == B.nRows())
			  << "add: Wrong number of rows: " << A.nRows()
			  << " and " << B.nRows();
			  NTA_ASSERT(A.nCols() == B.nCols())
			  << "add: Wrong number of columns: " << A.nCols()
			  << " and " << B.nCols();
		  } // End pre-conditions
		  
		  typedef typename SM::size_type size_type;
		  typedef typename SM::value_type value_type;
		  
		  const size_type nrows = A.nRows();                    
		  for (size_type row = 0; row != nrows; ++row) {
			  
			  size_type *ind     = A.ind_begin_(row);
			  size_type *ind_end = A.ind_end_(row);
			  value_type *nz     = A.nz_begin_(row);
			  
			  typename SM01::Row::const_iterator ind_b = B.ind_begin_(row);
			  typename SM01::Row::const_iterator ind_b_end = B.ind_end_(row);
			  
			  std::vector<size_type> indb_;
			  std::vector<value_type> nzb_;
			  
			  while (ind != ind_end && ind_b != ind_b_end) {
				  if (*ind == *ind_b) {
					  value_type val = *nz++ + cval;
					  if (!A.isZero_(val)) {
						  indb_.push_back(*ind);
						  nzb_.push_back(val);
					  }
					  ++ind; ++ind_b;
				  } else if (*ind < *ind_b) {
					  indb_.push_back(*ind++);
					  nzb_.push_back(*nz++);
				  } else if (*ind_b < *ind) {
					  if (!A.isZero_(cval)) {
						  indb_.push_back(*ind_b++);
						  nzb_.push_back(cval);
					  }
				  }
			  }
			  
			  while (ind != ind_end) {
				  indb_.push_back(*ind++);
				  nzb_.push_back(*nz++);
			  }
			  
			  while (ind_b != ind_b_end) {
				  if (!A.isZero_(cval)) {
					  indb_.push_back(*ind_b++);
					  nzb_.push_back(cval);
				  }
			  }
			  
			  A.setRowFromSparse(row, indb_.begin(), indb_.end(), nzb_.begin());
		  }
	  }
	  
    //--------------------------------------------------------------------------------
    /**
     * Computes the sum of two SMs that are in log space.
     * A = log(exp(A) + exp(B)), but only for the non-zeros of B.
     * A and B are already in log space.
     * A has non-zeros everywhere that B does.
     * This assumes that the operation does not introduce new zeros.
     * Note: we follow the non-zeros of B, which can be less than the non-zeros
     * of A.
     * If minFloor > 0, any value that drops below minFloor becomes minFloor.
     */
    template <typename SM>
    static void logSumNoAlloc(SM& A, const SM& B, typename SM::value_type minFloor =0)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(B.nonZeroIndicesIncluded(A));
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      nta::Exp<value_type> exp_f;
      nta::Log<value_type> log_f;
      nta::Log1p<value_type> log1p_f;
      nta::Abs<value_type> abs_f;

      size_type M = A.nRows();
      value_type minExp = log_f(std::numeric_limits<value_type>::epsilon());

      for (size_type row = 0; row != M; ++row) {

        size_type *ind_a = A.ind_begin_(row);
        size_type *ind_b = B.ind_begin_(row);
        size_type *ind_b_end = B.ind_end_(row);
        value_type *nz_a = A.nz_begin_(row);
        value_type *nz_b = B.nz_begin_(row);

        while (ind_b != ind_b_end) {
          if (*ind_a == *ind_b) {
            value_type a = *nz_a;
            value_type b = *nz_b;
            if (a < b)
              std::swap(a,b);
            value_type d = b - a;
            if (d >= minExp) {
              a += log1p_f(exp_f(d));
              if (minFloor > 0 && abs_f(a) < minFloor) 
                a = minFloor;
              *nz_a = a;
            } else {
              *nz_a = a;
            }
            NTA_ASSERT(!A.isZero_(*nz_a));
            ++ind_a; ++nz_a;
            ++ind_b; ++nz_b;
          } else if (*ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds a constant to the non-zeros of A in log space.
     * Assumes that no new zeros are introduced.
     */
    template <typename SM>
    static void 
    logAddValNoAlloc(SM& A, 
                     typename SM::value_type val, typename SM::value_type minFloor =0)
    {
      {
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      nta::Exp<value_type> exp_f;
      nta::Log<value_type> log_f;
      nta::Log1p<value_type> log1p_f;
      nta::Abs<value_type> abs_f;

      size_type M = A.nRows();
      value_type minExp = log_f(std::numeric_limits<value_type>::epsilon());
      value_type b;

      for (size_type row = 0; row != M; ++row) {

        size_type *ind_a = A.ind_begin_(row);
        size_type *ind_a_end = A.ind_end_(row);
        value_type *nz_a = A.nz_begin_(row);

        while (ind_a != ind_a_end) {
          value_type a = *nz_a;
          
          // Put smaller value in b, larger in a
          if (a < val) {
            b = a;
            a = val;
          } else {
            b = val;
          }
          value_type d = b - a;
          if (d >= minExp) {
            a += log1p_f(exp_f(d));
            if (minFloor > 0 && abs_f(a) < minFloor) 
              a = minFloor;
            *nz_a = a;
          } else
            *nz_a = a;
          NTA_ASSERT(!A.isZero_(*nz_a));
          ++ind_a; ++nz_a;
        } 
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the diff of two SMs that are in log space.
     * A = log(exp(A) - exp(B)), but only for the non-zeros of B.
     * A and B are already in log space.
     * A has non-zeros everywhere that B does.
     * A > B in all non-zeros.
     * This assumes that the operation does not introduce new zeros.
     * Note: we follow the non-zeros of B, which can be less than the non-zeros
     * of A.
     * If minFloor > 0, any value that drops below minFloor becomes minFloor.
     */
    template <typename SM>
    static void logDiffNoAlloc(SM& A, const SM& B, typename SM::value_type minFloor =0)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(B.nonZeroIndicesIncluded(A));
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      // Important to use double here, because in float, there can be 
      // cancelation in log(1 - exp(b-a)), when a is very close to b.
      nta::Exp<double> exp_f;
      nta::Log<value_type> log_f;
      nta::Log1p<double> log1p_f;
      nta::Abs<double> abs_f;

      size_type M = A.nRows();
      value_type minExp = log_f(std::numeric_limits<value_type>::epsilon());
      
      // Two log values that are this close to each other should generate a difference
      //  of 0, which is -inf in log space, which we want to avoid
      double minDiff = -std::numeric_limits<double>::epsilon();
      value_type logOfZero = -1.0/std::numeric_limits<value_type>::epsilon();

      for (size_type row = 0; row != M; ++row) {

        size_type *ind_a = A.ind_begin_(row);
        size_type *ind_b = B.ind_begin_(row);
        size_type *ind_b_end = B.ind_end_(row);
        value_type *nz_a = A.nz_begin_(row);
        value_type *nz_b = B.nz_begin_(row);

        while (ind_b != ind_b_end) {
          if (*ind_a == *ind_b) {
            double a = *nz_a;
            double b = *nz_b;
            NTA_ASSERT(a >= b);
            double d = b - a;
            // If the values are too close to each other, generate log of 0 manually
            // We know d <= 0 at this point. 
            if (d >= minDiff)
              *nz_a = logOfZero;              
            else if (d >= minExp) {
              a += log1p_f(-exp_f(d));
              if (minFloor > 0 && abs_f(a) < minFloor) 
                a = minFloor;
              *nz_a = (value_type) a;
            } else {
              *nz_a = (value_type) a;
            }
            NTA_ASSERT(!A.isZero_(*nz_a));
            ++ind_a; ++nz_a;
            ++ind_b; ++nz_b;
          } else if (*ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Algorithm to compute piPrime in loopy belief propagation.
     *
     * The net operation performed is prod(col)/element, but it is performed in log mode
     *  and the mat argument is assumed to have already been converted to log mode. 
     * All values within mat are between 0 and 1 in normal space (-inf and -epsilon in log
     *  space).  
     *
     * This does a sum of each column, then places colSum-element into each
     *  location, insuring that no new zeros are introduced. Any result that 
     *  would have computed to 0 (within max_floor) will be replaced with max_floor
     */
    template <typename SM>
    static void LBP_piPrime(SM& mat, typename SM::value_type max_floor)
    {
      {
        NTA_ASSERT(max_floor < 0);
      }

      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      size_type M = mat.nRows();
      size_type N = mat.nCols();

      nta::Abs<value_type> abs_f;

      std::fill(mat.nzb_, mat.nzb_ + N, (value_type) 0);

      // Compute the column sums, place them into mat.nzb_
      for (size_type row = 0; row != M; ++row) {

        if (mat.nnzr_[row] == 0)
          continue;

        size_type *ind = mat.ind_begin_(row);
        size_type *ind_end = mat.ind_end_(row);
        value_type *nz = mat.nz_begin_(row);

        for (; ind != ind_end; ++ind, ++nz) 
          mat.nzb_[*ind] += *nz;
      }

      // Replace each element with colSum - element
      for (size_type row = 0; row != M; ++row) {
        
        if (mat.nnzr_[row] == 0)
          continue;

        size_type *ind = mat.ind_begin_(row);
        size_type *ind_end = mat.ind_end_(row);
        value_type *nz = mat.nz_begin_(row);
        
        value_type absFloor = abs_f(max_floor);
        
        for (; ind != ind_end; ++ind, ++nz) {

          value_type v = mat.nzb_[*ind] - *nz;
          
          if (abs_f(v) < absFloor)
            v = max_floor;
            
          *nz = v;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Copies the values of the non-zeros of B into A, only where A and B have a 
     * non-zero in the same location. The other non-zeros of A are left unchanged.
     */
    template <typename SM, typename STR3F>
    static void assignNoAlloc(SM& A, const STR3F& B, typename SM::size_type s)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
      }

      typedef typename SM::size_type size_type;
      typedef typename STR3F::col_index_type col_index_type;
      typedef typename SM::value_type value_type;

      const size_type M = A.nRows();

      for (size_type row = 0; row != M; ++row) {

        size_type *ind_a = A.ind_begin_(row);
        col_index_type *ind_b = B.ind_begin_(row);
        value_type *nz_a = A.nz_begin_(row);
        value_type *nz_a_end = A.nz_end_(row);
        value_type *nz_b = B.nz_begin_(s, row);
        value_type *nz_b_end = B.nz_end_(s, row);

        while (nz_a != nz_a_end && nz_b != nz_b_end)
          if (*ind_a == (size_type) *ind_b) {
            *nz_a = *nz_b;
            ++ind_a; ++ind_b;
            ++nz_a; ++nz_b;
          } else if (*ind_a < (size_type) *ind_b) {
            ++ind_a; ++nz_a;
          } else if ((size_type) *ind_b < *ind_a) {
            ++ind_b; ++nz_b;
          }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the sum in log space of A and B, where A is a slice of a STR3F 
     * and B is a SM. The operation is:
     * a = log(exp(a) + exp(b)), 
     * where a is a non-zero of slice s of A, and b is the corresponding non-zero of B
     * (in the same location). 
     *
     * The number of non-zeros of in A is unchanged, and if the absolute value
     * of a non-zero would fall below minFloor, it is replaced by minFloor.
     * A and B need to have the same dimensions.
     */
    template <typename SM, typename STR3F>
    static void logSumNoAlloc(STR3F& A, typename SM::size_type s, 
			      const SM& B, typename SM::value_type minFloor =0)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      typedef typename STR3F::col_index_type col_index_type;
      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      nta::Exp<value_type> exp_f;
      nta::Log<value_type> log_f;
      nta::Log1p<value_type> log1p_f;
      nta::Abs<value_type> abs_f;

      size_type M = (size_type) A.nRows();
      value_type minExp = log_f(std::numeric_limits<value_type>::epsilon());

      if (nta::Epsilon < minFloor) {
      
        for (size_type row = 0; row != M; ++row) {

          col_index_type *ind_a = A.ind_begin_(row);
          size_type *ind_b = B.ind_begin_(row);
          size_type *ind_b_end = B.ind_end_(row);
          value_type *nz_a = A.nz_begin_(s, row);
          value_type *nz_b = B.nz_begin_(row);

          while (ind_b != ind_b_end) {
            if ((size_type) *ind_a == *ind_b) {
              value_type a = *nz_a;
              value_type b = *nz_b;
              if (a < b)
                std::swap(a,b);
              value_type d = b - a;
              if (d >= minExp) {
                a += log1p_f(exp_f(d));
                if (abs_f(a) < minFloor) 
                  a = minFloor;
                *nz_a = a;
              } else {
                *nz_a = a;
              }
              ++ind_a; ++nz_a;
              ++ind_b; ++nz_b;
            } else if ((size_type) *ind_a < *ind_b) {
              ++ind_a; ++nz_a;
            }
          }
        }

      } else { // minFloor <= nta::Epsilon, i.e. essentially minFloor == 0

        for (size_type row = 0; row != M; ++row) {

          col_index_type *ind_a = A.ind_begin_(row);
          size_type *ind_b = B.ind_begin_(row);
          size_type *ind_b_end = B.ind_end_(row);
          value_type *nz_a = A.nz_begin_(s, row);
          value_type *nz_b = B.nz_begin_(row);

          while (ind_b != ind_b_end) {
            if ((size_type) *ind_a == *ind_b) {
              value_type a = *nz_a;
              value_type b = *nz_b;
              if (a < b)
                std::swap(a,b);
              value_type d = b - a;
              if (d >= minExp) {
                a += log1p_f(exp_f(d));
                *nz_a = a;
              } else {
                *nz_a = a;
              }
              ++ind_a; ++nz_a;
              ++ind_b; ++nz_b;
            } else if ((size_type) *ind_a < *ind_b) {
              ++ind_a; ++nz_a;
            }
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the diff in log space of A and B, where A is a slice of a STR3F 
     * and B is a SM. The operation is:
     * a = log(exp(a) - exp(b)), 
     * where a is a non-zero of slice s of A, and b is the corresponding non-zero of B
     * (in the same location). 
     *
     * The number of non-zeros of in A is unchanged, and if the absolute value
     * of a non-zero would fall below minFloor, it is replaced by minFloor.
     * A and B need to have the same dimensions.
     */
    template <typename SM, typename STR3F>
    static void logDiffNoAlloc(STR3F& A, typename SM::size_type s, 
			       const SM& B, typename SM::value_type minFloor =0)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      typedef typename STR3F::col_index_type col_index_type;
      typedef typename SM::size_type size_type;
      typedef typename SM::value_type value_type;

      // Important to use double here, because in float, there can be 
      // cancelation in log(1 - exp(b-a)), when a is very close to b.
      nta::Exp<double> exp_f;
      nta::Log<value_type> log_f;
      nta::Log1p<double> log1p_f;
      nta::Abs<double> abs_f;

      size_type M = (size_type) A.nRows();
      value_type minExp = log_f(std::numeric_limits<value_type>::epsilon());
      
      // Two log values that are this close to each other should generate a difference
      //  of 0, which is -inf in log space, which we want to avoid
      double minDiff = -std::numeric_limits<double>::epsilon();
      value_type logOfZero = ((value_type)-1.0)/std::numeric_limits<value_type>::epsilon();

      if (nta::Epsilon < minFloor) {

        for (size_type row = 0; row != M; ++row) {

          col_index_type *ind_a = A.ind_begin_(row);
          size_type *ind_b = B.ind_begin_(row);
          size_type *ind_b_end = B.ind_end_(row);
          value_type *nz_a = A.nz_begin_(s, row);
          value_type *nz_b = B.nz_begin_(row);

          while (ind_b != ind_b_end) {
            if ((size_type) *ind_a == *ind_b) {
              double a = *nz_a;
              double b = *nz_b;
              NTA_ASSERT(a >= b);
              double d = b - a;
              // If the values are too close to each other, generate log of 0 manually
              // We know d <= 0 at this point. 
              if (d >= minDiff)
                *nz_a = logOfZero;              
              else if (d >= minExp) {
                a += log1p_f(-exp_f(d));
                if (abs_f(a) < minFloor) 
                  a = minFloor;
                *nz_a = (value_type) a;
              } else {
                *nz_a = (value_type) a;
              }
              ++ind_a; ++nz_a;
              ++ind_b; ++nz_b;
            } else if ((size_type) *ind_a < *ind_b) {
              ++ind_a; ++nz_a;
            }
          }
        }

      } else { // minFloor <= nta::Epsilon, i.e. essentially minFloor == 0

        for (size_type row = 0; row != M; ++row) {

          col_index_type *ind_a = A.ind_begin_(row);
          size_type *ind_b = B.ind_begin_(row);
          size_type *ind_b_end = B.ind_end_(row);
          value_type *nz_a = A.nz_begin_(s, row);
          value_type *nz_b = B.nz_begin_(row);

          while (ind_b != ind_b_end) {
            if ((size_type) *ind_a == *ind_b) {
              double a = *nz_a;
              double b = *nz_b;
              NTA_ASSERT(a >= b);
              double d = b - a;
              // If the values are too close to each other, generate log of 0 manually
              // We know d <= 0 at this point. 
              if (d >= minDiff)
                *nz_a = logOfZero;              
              else if (d >= minExp) {
                a += log1p_f(-exp_f(d));
                *nz_a = (value_type) a;
              } else {
                *nz_a = (value_type) a;
              }
              ++ind_a; ++nz_a;
              ++ind_b; ++nz_b;
            } else if ((size_type) *ind_a < *ind_b) {
              ++ind_a; ++nz_a;
            }
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Updates A only where A and B have a non-zero in the same location, by copying
     * the corresponding non-zero of B. The other non-zeros of A are left unchanged. 
     */
    template <typename STR3F>
    static void assignNoAlloc(STR3F& A, typename STR3F::size_type slice_a,
			      const STR3F& B, typename STR3F::size_type slice_b)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
      }

      typedef typename STR3F::row_index_type row_index_type;
      typedef typename STR3F::col_index_type col_index_type;
      typedef typename STR3F::value_type value_type;

      for (row_index_type row = 0; row != A.nRows(); ++row) {

        col_index_type *ind_a = A.ind_begin_(row);
        col_index_type *ind_b = B.ind_begin_(row);
        value_type *nz_a = A.nz_begin_(slice_a, row);
        value_type *nz_a_end = A.nz_end_(slice_a, row);
        value_type *nz_b = B.nz_begin_(slice_b, row);
        value_type *nz_b_end = B.nz_end_(slice_b, row);

        while (nz_a != nz_a_end && nz_b != nz_b_end)
          if (*ind_a == *ind_b) {
            *nz_a = *nz_b;
            ++ind_a; ++ind_b;
            ++nz_a; ++nz_b;
          } else if (*ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          } else {
            ++ind_b; ++nz_b;
          }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the sum in log space of A and B, where A is a slice of a STR3F 
     * and B is another slice of another STR3F. The operation is:
     * a = log(exp(a) + exp(b)), 
     * where a is a non-zero of slice s of A, and b is the corresponding non-zero of B
     * (in the same location). 
     *
     * The number of non-zeros of in A is unchanged, and if the absolute value
     * of a non-zero would fall below minFloor, it is replaced by minFloor.
     * A and B need to have the same dimensions.
     */
    template <typename STR3F>
    static void logSumNoAlloc(STR3F& A, typename STR3F::size_type slice_a, 
			      const STR3F& B, typename STR3F::size_type slice_b,
			      typename STR3F::value_type minFloor =0)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      typedef typename STR3F::col_index_type col_index_type;
      typedef typename STR3F::size_type size_type;
      typedef typename STR3F::value_type value_type;

      nta::Exp<value_type> exp_f;
      nta::Log<value_type> log_f;
      nta::Log1p<value_type> log1p_f;
      nta::Abs<value_type> abs_f;

      size_type M = (size_type) A.nRows();
      value_type minExp = log_f(std::numeric_limits<value_type>::epsilon());

      for (size_type row = 0; row != M; ++row) {

        col_index_type *ind_a = A.ind_begin_(row);
        col_index_type *ind_b = B.ind_begin_(row);
        col_index_type *ind_b_end = B.ind_end_(row);
        value_type *nz_a = A.nz_begin_(slice_a, row);
        value_type *nz_b = B.nz_begin_(slice_b, row);

        while (ind_b != ind_b_end) {
          if (*ind_a == *ind_b) {
            value_type a = *nz_a;
            value_type b = *nz_b;
            if (a < b)
              std::swap(a,b);
            value_type d = b - a;
            if (d >= minExp) {
              a += log1p_f(exp_f(d));
              if (minFloor > 0 && abs_f(a) < minFloor) 
                a = minFloor;
              *nz_a = a;
            } else {
              *nz_a = a;
            }
            NTA_ASSERT(!A.isZero_(*nz_a));
            ++ind_a; ++nz_a;
            ++ind_b; ++nz_b;
          } else if ( *ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the diff in log space of A and B, where A is a slice of a STR3F 
     * and B is another slice of another STR3F. The operation is:
     * a = log(exp(a) - exp(b)), 
     * where a is a non-zero of slice s of A, and b is the corresponding non-zero of B
     * (in the same location). 
     *
     * The number of non-zeros of in A is unchanged, and if the absolute value
     * of a non-zero would fall below minFloor, it is replaced by minFloor.
     * A and B need to have the same dimensions.
     */
    template <typename STR3F>
    static void logDiffNoAlloc(STR3F& A, typename STR3F::size_type slice_a, 
			       const STR3F& B, typename STR3F::size_type slice_b,
			       typename STR3F::value_type minFloor =0)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      typedef typename STR3F::col_index_type col_index_type;
      typedef typename STR3F::size_type size_type;
      typedef typename STR3F::value_type value_type;

      // Important to use double here, because in float, there can be 
      // cancelation in log(1 - exp(b-a)), when a is very close to b.
      nta::Exp<double> exp_f;
      nta::Log<value_type> log_f;
      nta::Log1p<double> log1p_f;
      nta::Abs<double> abs_f;

      size_type M = (size_type) A.nRows();
      value_type minExp = log_f(std::numeric_limits<value_type>::epsilon());
      
      // Two log values that are this close to each other should generate a difference
      //  of 0, which is -inf in log space, which we want to avoid
      double minDiff = -std::numeric_limits<double>::epsilon();
      value_type logOfZero = ((value_type)-1.0)/std::numeric_limits<value_type>::epsilon();

      for (size_type row = 0; row != M; ++row) {

        col_index_type *ind_a = A.ind_begin_(row);
        col_index_type *ind_b = B.ind_begin_(row);
        col_index_type *ind_b_end = B.ind_end_(row);
        value_type *nz_a = A.nz_begin_(slice_a, row);
        value_type *nz_b = B.nz_begin_(slice_b, row);

        while (ind_b != ind_b_end) {
          if (*ind_a == *ind_b) {
            double a = *nz_a;
            double b = *nz_b;
            NTA_ASSERT(a >= b);
            double d = b - a;
            // If the values are too close to each other, generate log of 0 manually
            // We know d <= 0 at this point. 
            if (d >= minDiff)
              *nz_a = logOfZero;              
            else if (d >= minExp) {
              a += log1p_f(-exp_f(d));
              if (minFloor > 0 && abs_f(a) < minFloor) 
                a = minFloor;
              *nz_a = (value_type) a;
            } else {
              *nz_a = (value_type) a;
            }
            NTA_ASSERT(!A.isZero_(*nz_a));
            ++ind_a; ++nz_a;
            ++ind_b; ++nz_b;
          } else if (*ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    // END LBP
    //--------------------------------------------------------------------------------

    //--------------------------------------------------------------------------------
  }; // End class SparseMatrixAlgorithms

  //--------------------------------------------------------------------------------
  //--------------------------------------------------------------------------------
  // SUM OF LOGS AND DIFF OF LOGS APPROXIMATIONS
  //
  // This section contains two classes that allow to approximate addition of numbers
  // that are logarithms, in an efficient manner. The operations approximated are:
  // z = log(exp(x) + exp(y) and z = log(exp(x) - exp(y).
  // There are many pitfalls and tricks that make the implementation not trivial if 
  // it is to be efficient and accurate.
  //
  //--------------------------------------------------------------------------------
  // IMPLEMENTATION NOTES:
  // ====================
  //
  //  How to add/subtract in log domain:
  //  =================================
  //
  // We want to compute: log(exp(a) + exp(b)) or log(exp(a) - exp(b)). The first step is:
  //
  // log(exp(a) + exp(b)) = log(exp(a) * (1 + exp(b-a)))
  //                      = a + log(1 + exp(b-a))
  //
  // double logSum(double a, double b)
  // {
  //   if (a < b)
  //     swap(a,b); 
  //   if (!(a >= b))
  //     fprintf(stderr, "ERROR: logSum: %f %f\n", a, b);
  //   assert(a >= b);
  //
  //   return a + log1p(exp(b-a));
  // }  
  //
  // If your numerical library doesn't have the log1p(x) function, replace it with log(1+x).    
  //
  // This step saves a call to exp() and relies on log1p which is hopefully implemented 
  // efficiently, maybe even in hardware. However, we are going to speed-up this operation 
  // further by approximation. 
  //
  // Why a > b:
  // =========
  //
  // a needs to be > b, and that's because otherwise, in float, the exponential of a large 
  // number can overflow the range of float. In double, it doesn't matter till the number 
  // becomes even larger. So, mathematically, it doesn't matter that a > b, but in terms of 
  // floating point overflow, it matters.        
  //
  // Making logSum/logDiff fast (10X):
  // ================================     
  //
  // In LBP, we approximate the following two functions using a table. These functions, 
  // both of the form z = f(x,y) are slow: they do a lot of work, and they have multiple 
  // ifs that can cause the processor pipeline to stall. 
  //
  // value_type logSum(value_type a, value_type b)
  // {
  //   if (a < b)
  //     swap(a,b);
  //   value_type d = b - a;
  //   if (d >= minExp) {
  //     a += log1p(exp(d));
  //     if (fabs(a) < minFloor) 
  //       a = minFloor;  
  //   }
  //   return a;
  // }     
  //
  // value_type logDiff(value_type a, value_type b)
  // {                          
  //   assert(b < a);
  //   double d = b - a;
  //   if (d >= minDiff)
  //     a = logOfZero;              
  //   else if (d >= minExp) {
  //     a += log1p(-exp(d));
  //     if (fabs(a) < minFloor) 
  //       a = minFloor;   
  //   }
  //   return a;    
  // }                  
  //
  // The domain of f is known to be: [-14,14] x [-14,14]. 
  // The first idea was to create a 2D table to store a step function
  // as an approximation of f. However, this ended up taking too much memory and not 
  // being precise enough. Looking at the graphs of z, it became apparent that for both 
  // logSum and logDiff: 1) logSum is symmetric w.r.t. the line y = x, but logDiff is 
  // defined only for y < x, 2) any two slices for fixed y0 and y1 are related by a 
  // simple translation. Taking advantage of this last observation, an identity can be 
  // derived relating two slices. This can be used to store a step approximation for only 
  // one slice, discretized very finely, while computing the value z = f(x,y) for any other 
  // slice using the identity. Here is the derivation of the identity:
  //
  //     f(x,y) = log(exp(x) + exp(y))
  // f(x+u,y+u) = log(exp(x+u) + exp(y+u))
  //            = log(exp(x) + exp(y)) + u
  //            = f(x,y) + u
  //     f(x,y) = f(x+u,y+u) - u
  //
  // Choosing u = -y:
  //
  //     f(x,y) = f(x-y,0) + y   
  //
  // The same holds for log(exp(x) - exp(y)). 
  //
  // So, we approximate f(a,0) using a step function on [lb,ub], each value in a table 
  // storing the value of f(k*delta + lb), k integer positive and delta small. Note that 
  // f(a,0) is log(exp(a) + 1), continuous, with derivative the sigmoid 1/(1+exp(-a)). 
  // This derivative is strictly positive, with range ]0,1[ (f is monotonically increasing). 
  // For logDiff(a,0) = log(exp(x) - 1), there is a discontinuity at zero which is harder 
  // to approximate.
  //
  // Errors:
  // ======
  // The absolute error due to the step-wise approximation is directly bounded above by 
  // the size of the step delta, because the derivative is in ]0,1[ on the whole domain of f. 
  // In practice, this is true in double, but in float, the experimental absolute error is 
  // slightly above delta.    
  //
  // The relative error can be reduced by increasing the size of the table, and experimentally, 
  // it reduces to arbitrary level as the number of entries in the table is increased. Again, 
  // logDiff has higher relative error because of its singularity, but it can still be 
  // approximated reasonably within less than 50 MB.
  //
  // Implementation tricks:
  // =====================
  //
  // - when computing the table, use a double precision step, otherwise the steps 
  // can get out of step, resulting in a wrong approximation
  // - when computing the index in the table for a given (x,y), use float for the step, 
  // otherwise the speed is halved. This float precision is enough when evaluating the index.
  //
  //--------------------------------------------------------------------------------
  /**
   * Approximates a sum of logs operation we have in LBP with a table for speed.
   * A table of values (step function) is computed once, then accessed on subsequent 
   * calls. The values are used directly, rather than using interpolation.
   *
   * TODO: use asymptotes to reduce the size of the table
   */
  class LogSumApprox {
    
  public:
    // the values are stored in float to save space (4 bytes per value)
    typedef float value_type;

  private:
    value_type min_a, max_a;              // bounds of domain
    value_type step_a;                    // step along side of domain
    static std::vector<value_type> table; // table of approximant step function

    // Various constants used in the function
    value_type minFloor, minExp, logOfZero;
    double minDiff;
    bool trace;

    LogSumApprox(const LogSumApprox&);
    LogSumApprox& operator=(const LogSumApprox&);

    // Portable exp and log functions
    nta::Exp<double> exp_f;
    nta::Log1p<double> log1p_f;

  public:
    //--------------------------------------------------------------------------------
    /**
     * n is the size of the square domain on which we approximate, and the other
     * parameters are the bounds of the domain. n*n values are computed once
     * and stored in a table. 
     *
     * Errors:
     * ======
     * On darwin86:
     * Sum of logs table: 20000000 -28 28 5.6e-06 76MB
     * abs=4.03906228374e-06 rel=6.57921289158e-05
     *
     * On Windows:
     * Sum of logs table: 20000000 -28 28 2.8e-006 76MB
     * abs=3.41339533527e-006 rel=0.00028832192106
     */
    inline LogSumApprox(int n_ = 5000000, 
                        value_type min_a_ =-28, value_type max_a_ =28,
                        bool trace_ =false)
      : min_a(min_a_), max_a(max_a_),
        step_a((value_type)((max_a - min_a)/n_)),
        minFloor((value_type)(1.1 * 1e-6)),
        minExp(logf(std::numeric_limits<value_type>::epsilon())),
        logOfZero(((value_type)-1.0)/std::numeric_limits<value_type>::epsilon()),
        minDiff(-std::numeric_limits<double>::epsilon()),
        trace(trace_)
    {
      { // Pre-conditions
        NTA_ASSERT(min_a < max_a);
        NTA_ASSERT(0 < step_a);
      } // End pre-conditions

      if (table.empty()) {
        table.resize(n_);
        compute_table();
      }

      if (trace)
        std::cout << "Sum of logs table: " << table.size() << " "
                  << min_a << " " << max_a << " " << step_a << " "
                  << (4*table.size()/(1024*1024)) << "MB" << std::endl;
    }

    //--------------------------------------------------------------------------------
    /**
     * This function computes the slice of sum_of_logs(a,b) for b = 0, but when
     * the function will be called later, it will always be called with a and b
     * far from minFloor. The net result of that is that all the values in the table
     * should be greater than minFloor, which we enforce here. We replicate the code
     * of sum_of_logs_f (modified for minFloor) because sum_of_logs_f has asserts that 
     * wouldn't pass for b = 0. The step needs to be a double, or it gets out of sync 
     * to compute the intervals of the table.
     */
    inline void compute_table()
    {
      double a = min_a, step = step_a;
      
      for (size_t ia = 0; ia < table.size(); ++ia, a += step) 
        table[ia] = sum_of_logs_f((value_type)a,(value_type)0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the index corresponding to a,b in the table.
     */
    inline int index(value_type a, value_type b) const
    {
      return (int)((a - (b + min_a)) / step_a);
    }

    //--------------------------------------------------------------------------------
  private:
    /**
     * This is the exact function we approximate. It's of the form z = f(a,b).
     * Note that in real applications, a and b will be far from minFloor. 
     * Doesn't check pre-conditions, so it can be called for b = 0 when 
     * building the table of values.
     */
    inline value_type sum_of_logs_f(value_type a, value_type b) const
    {
      if (a < b)
        std::swap(a,b);
      value_type d = b - a;
      if (d >= minExp) {
        a += (value_type) log1p_f(exp_f(d));
        if (fabs(a) < minFloor) 
          a = minFloor;  
      }

      return a;
    }  

  public:
    //--------------------------------------------------------------------------------
    /**
     * Will crash if (a,b) outside of domain (faster).
     * Note that in real applications, a and b will be far from minFloor (see 
     * pre-conditions). 
     */
    inline value_type fast_sum_of_logs(value_type a, value_type b) const
    {
      { // Pre-conditions
        NTA_ASSERT(minFloor <= fabs(a)) << a;
        NTA_ASSERT(minFloor <= fabs(b)) << b;
      } // End pre-conditions

      value_type val = table[index(a,b)] + b;  

      if (fabs(val) < minFloor)
        val = minFloor;

      return val;
    }    

    //--------------------------------------------------------------------------------
    /**
     * Works with illimited range, but slower.
     * Note that in real applications, a and b will be far from minFloor (see 
     * pre-conditions). 
     */
    inline value_type sum_of_logs(value_type a, value_type b) const
    {          
      { // Pre-conditions
        NTA_ASSERT(minFloor <= fabs(a)) << a;
        NTA_ASSERT(minFloor <= fabs(b)) << b;
      } // End pre-conditions
      
      value_type val;

      if (-14 <= a && a < 14 && -14 <= b && b < 14)
        val = fast_sum_of_logs(a, b);
      else 
        val = sum_of_logs_f(a, b);

      return val;
    } 

    //--------------------------------------------------------------------------------
    /**
     * Computes sum of logs between a STR3F and a SM. This is a piece of the LBP
     * algorithm. Values closer to zero than minFloor are replaced by minFloor.
     */
    template <typename SM, typename STR3F>
    inline void logSum(STR3F& A, typename SM::size_type s, const SM& B)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(nta::Epsilon < minFloor);
      }

      typedef typename STR3F::col_index_type col_index_type;
      typedef typename SM::size_type size_type;
      
      size_type M = (size_type) A.nRows();

      for (size_type row = 0; row != M; ++row) {

        col_index_type *ind_a = A.ind_begin_(row);
        const size_type *ind_b = B.row_nz_index_begin(row);
        const size_type *ind_b_end = B.row_nz_index_end(row);
        value_type *nz_a = A.nz_begin_(s, row);
        const value_type *nz_b = B.row_nz_value_begin(row);

        while (ind_b != ind_b_end) {
          if ((size_type) *ind_a == *ind_b) {
            *nz_a = sum_of_logs(*nz_a, *nz_b);
            ++ind_a; ++nz_a;
            ++ind_b; ++nz_b;
          } else if ((size_type) *ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes sum of logs between a SM and a STR3F. Also a piece of LBP.
     * Values closer to zero than minFloor are replaced by minFloor.
     */
    template <typename SM, typename STR3F>
    inline void fastLogSum(STR3F& A, typename SM::size_type s, const SM& B)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(nta::Epsilon < minFloor);
      }

      typedef typename STR3F::col_index_type col_index_type;
      typedef typename SM::size_type size_type;
      
      size_type M = (size_type) A.nRows();

      for (size_type row = 0; row != M; ++row) {

        col_index_type *ind_a = A.ind_begin_(row);
        const size_type *ind_b = B.row_nz_index_begin(row);
        const size_type *ind_b_end = B.row_nz_index_end(row);
        value_type *nz_a = A.nz_begin_(s, row);
        const value_type *nz_b = B.row_nz_value_begin(row);

        while (ind_b != ind_b_end) {
          if ((size_type) *ind_a == *ind_b) {
            *nz_a = fast_sum_of_logs(*nz_a, *nz_b);
            ++ind_a; ++nz_a;
            ++ind_b; ++nz_b;
          } else if ((size_type) *ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          }
        }
      }
    }
  }; // End LogSumApprox

  //--------------------------------------------------------------------------------
  /**
   * See comments in LogSumApprox. This is the same idea, except that the function
   * approximated is a diff of logs, rather than a sum of logs.
   *
   * Errors:
   * ======
   * On darwin86:
   * Diff of logs table: 20000000 1e-06 28 1.4e-06 76MB
   * abs=2.56909073832e-05 rel=0.000589275477819
   *
   * On Windows:
   * Diff of logs table: 20000000 1e-006 28 1.4e-006 76MB
   * abs=2.56909073832e-005 rel=0.000589275477819
  */
  class LogDiffApprox {
    
  public:
    // The values are stored in float to save space (4 bytes per value)
    typedef float value_type;

  private:
    value_type min_a, max_a;              // bounds of domain
    value_type step_a;                    // step along side of domain
    static std::vector<value_type> table; // the approximating values themselves 

    // Various constants used in the function
    value_type minFloor, minExp, logOfZero;
    double minDiff;
    bool trace;

    LogDiffApprox(const LogDiffApprox&);
    LogDiffApprox& operator=(const LogDiffApprox&);

    nta::Exp<double> exp_f;
    nta::Log1p<double> log1p_f;

  public:
    //--------------------------------------------------------------------------------
    /**
     * n is the size of the square domain on which we approximate, and the other
     * parameters are the bounds of the domain. n*n values are computed once
     * and stored in a table.
     *
     * TODO: use asymptotes to reduce the size of the table
     */
    inline LogDiffApprox(int n_ = 5000000, 
                         value_type min_a_ =1e-10, value_type max_a_ =28,
                         bool trace_ =false)
      : min_a(min_a_), max_a(max_a_),
        step_a((value_type)((max_a - min_a)/n_)),
        minFloor((value_type)(1.1 * 1e-6)),
        minExp(logf(std::numeric_limits<value_type>::epsilon())),
        logOfZero(((value_type)-1.0)/std::numeric_limits<value_type>::epsilon()),
        minDiff(-std::numeric_limits<double>::epsilon()),
        trace(trace_)
    {
      { // Pre-conditions
        NTA_ASSERT(min_a < max_a);
        NTA_ASSERT(0 < step_a);
      } // End pre-conditions

      if (table.empty()) {
        table.resize(n_);
        compute_table();
      }

      if (trace)
        std::cout << "Diff of logs table: " << table.size() << " "
                  << min_a << " " << max_a << " " << step_a << " "
                  << (4*table.size()/(1024*1024)) << "MB" << std::endl;
    }

    //--------------------------------------------------------------------------------
    /**
     * See comments for LogSumApprox::compute_table().
     */
    inline void compute_table()
    {
      double a = min_a, step = step_a;
      
      for (size_t ia = 0; ia < table.size(); ++ia, a += step) 
        table[ia] = diff_of_logs_f((value_type)a,(value_type)0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the index corresponding to a,b in the table.
     */
    inline int index(value_type a, value_type b) const
    {
      return (int)((a - (b + min_a)) / step_a);
    }

  private:
    //--------------------------------------------------------------------------------
    /**
     * This is the exact function we approximate. It's of the form z = f(a,b).
     * Note that in real applications, a and b will be far from minFloor (see 
     * pre-conditions). Doesn't check pre-conditions so we can call it with b = 0
     * when building the table of values.
     */
    inline value_type diff_of_logs_f(value_type a, value_type b) const
    {
      double d = b - a;
      if (d >= minDiff)
        a = logOfZero;              
      else if (d >= minExp) {
        a += (value_type) log1p_f(-exp_f(d));
        if (fabs(a) < minFloor) 
          a = minFloor;   
      }

      return a;    
    }   

  public:
    //--------------------------------------------------------------------------------
    /**
     * Will crash if (a,b) outside of domain (faster).
     * Note that in real applications, a and b will be far from minFloor (see 
     * pre-conditions). 
     */
    inline value_type fast_diff_of_logs(value_type a, value_type b) const
    {
      { // Pre-conditions
        NTA_ASSERT(b < a);
        NTA_ASSERT(minFloor <= fabs(a)) << a;
        NTA_ASSERT(minFloor <= fabs(b)) << b;
      } // End pre-conditions

      value_type val = table[index(a,b)] + b;  

      if (fabs(val) < minFloor)
        val = minFloor;

      return val;
    }    

    //--------------------------------------------------------------------------------
    /**
     * Will fall back on calling function if (a,b) outside domain (slower).
     * Note that in real applications, a and b will be far from minFloor (see 
     * pre-conditions). 
     */
    inline value_type diff_of_logs(value_type a, value_type b) const
    {                   
      { // Pre-conditions
        NTA_ASSERT(b < a);
        NTA_ASSERT(minFloor <= fabs(a)) << a;
        NTA_ASSERT(minFloor <= fabs(b)) << b;
      } // End pre-conditions

      value_type val;

      if (-14 <= a && a < 14 && -14 <= b && b < 14)
        val = fast_diff_of_logs(a, b);
      else
        val = diff_of_logs_f(a, b);

      return val;
    } 

    //--------------------------------------------------------------------------------
    /**
     * Computes diff of logs between a STR3F and a SM. This is a piece of the LBP
     * algorithm. Values closer to zero than minFloor are replaced by minFloor.
     */
    template <typename SM, typename STR3F>
    inline void logDiff(STR3F& A, typename SM::size_type s, const SM& B)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(nta::Epsilon < minFloor);
      }

      typedef typename STR3F::col_index_type col_index_type;
      typedef typename SM::size_type size_type;
      
      size_type M = (size_type) A.nRows();

      for (size_type row = 0; row != M; ++row) {

        col_index_type *ind_a = A.ind_begin_(row);
        const size_type *ind_b = B.row_nz_index_begin(row);
        const size_type *ind_b_end = B.row_nz_index_end(row);
        value_type *nz_a = A.nz_begin_(s, row);
        const value_type *nz_b = B.row_nz_value_begin(row);

        while (ind_b != ind_b_end) {
          if ((size_type) *ind_a == *ind_b) {
            *nz_a = diff_of_logs(*nz_a, *nz_b);
            ++ind_a; ++nz_a;
            ++ind_b; ++nz_b;
          } else if ((size_type) *ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /** 
     * Computes diff of logs between a SM and a STR3F. Also a part of LBP.
     * Values closer to zero than minFloor are replaced by minFloor.
     */
    template <typename SM, typename STR3F>
    inline void fastLogDiff(STR3F& A, typename SM::size_type s, const SM& B)
    {
      {
        NTA_ASSERT(A.nRows() == B.nRows());
        NTA_ASSERT(A.nCols() == B.nCols());
        NTA_ASSERT(nta::Epsilon < minFloor);
      }

      typedef typename STR3F::col_index_type col_index_type;
      typedef typename SM::size_type size_type;
      
      size_type M = (size_type) A.nRows();

      for (size_type row = 0; row != M; ++row) {

        col_index_type *ind_a = A.ind_begin_(row);
        const size_type *ind_b = B.row_nz_index_begin(row);
        const size_type *ind_b_end = B.row_nz_index_end(row);
        value_type *nz_a = A.nz_begin_(s, row);
        const value_type *nz_b = B.row_nz_value_begin(row);

        while (ind_b != ind_b_end) {
          if ((size_type) *ind_a == *ind_b) {
            *nz_a = fast_diff_of_logs(*nz_a, *nz_b);
            ++ind_a; ++nz_a;
            ++ind_b; ++nz_b;
          } else if ((size_type) *ind_a < *ind_b) {
            ++ind_a; ++nz_a;
          }
        }
      }
    }
  }; // End LogDiffApprox



	

}; // End namespace nta

#endif // NTA_SM_ALGORITHMS_HPP
