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
 * Definition for NearestNeighbor
 */

#ifndef NTA_NEAREST_NEIGHBOR_HPP
#define NTA_NEAREST_NEIGHBOR_HPP

#include <nta/math/SparseMatrix.hpp>
#include <nta/math/array_algo.hpp>

//----------------------------------------------------------------------
namespace nta {

  template <typename T>
  class NearestNeighbor : public T
  {
  public:     
    typedef T parent_type;
    typedef NearestNeighbor self_type;

    typedef typename parent_type::size_type size_type;
    typedef typename parent_type::difference_type difference_type;
    typedef typename parent_type::value_type value_type;
    typedef typename parent_type::prec_value_type prec_value_type;

    //--------------------------------------------------------------------------------
    // CONSTRUCTORS
    //--------------------------------------------------------------------------------
    inline NearestNeighbor()
      : parent_type()
    {}

    //--------------------------------------------------------------------------------
    /**
     * Constructor with a number of columns and a hint for the number
     * of rows. The SparseMatrix is empty.
     *
     * @param nrows [size_type >= 0] number of rows
     * @param ncols [size_type >= 0] number of columns
     *
     * @b Exceptions:
     *  @li nrows < 0 (check)
     *  @li ncols < 0 (check)
     *  @li Not enough memory (error)
     */
    inline NearestNeighbor(size_type nrows, size_type ncols)
      : parent_type(nrows, ncols)
    {}

    //--------------------------------------------------------------------------------
    /**
     * Constructor from a dense matrix passed as an array of value_type.
     * Uses the values in mat to initialize the SparseMatrix.
     *
     * @param nrows [size_type >= 0] number of rows
     * @param ncols [size_type >= 0] number of columns
     * @param dense [value_type** != NULL] initial array of values
     *
     * @b Exceptions:
     *  @li nrows <= 0 (check)
     *  @li ncols <= 0 (check)
     *  @li mat == NULL (check)
     *  @li NULL pointer in mat (check)
     *  @li Not enough memory (error)
     */
    template <typename InputIterator> 
    inline NearestNeighbor(size_type nrows, size_type ncols, InputIterator dense)
      : parent_type(nrows, ncols, dense)
    {}

    //--------------------------------------------------------------------------------
    /**
     * Constructor from a stream in CSR format (don't forget number of bytes after
     * 'csr' tag!).
     */
    inline NearestNeighbor(std::istream& inStream)
      : parent_type(inStream)
    {}

    //--------------------------------------------------------------------------------
    /**
     * Copy constructor.
     *
     * TODO copy part of a matrix?
     *
     * Copies the given NearestNeighbor into this one.
     */
    inline NearestNeighbor(const NearestNeighbor& other)
      : parent_type(other)
    {}

    //--------------------------------------------------------------------------------
    /**
     * Assignment operator.
     */
    inline NearestNeighbor& operator=(const NearestNeighbor& other)
    {
      parent_type::operator=(other);
      return *this;
    }

    //--------------------------------------------------------------------------------
    /**
     * A method that computes the powers of x and their sum, according to f.
     */
  private: 
    template <typename InputIterator, typename F>
    inline void 
    compute_powers_(value_type& Sp_x, value_type* p_x, InputIterator x, F f) 
    {
      const size_type ncols = this->nCols();
      InputIterator end1 = x + 4*(ncols/4), end2 = x + ncols;
      Sp_x = (value_type) 0;
      
      for (; x != end1; x += 4, p_x += 4) {
	*p_x = f(Sp_x, *x);
	*(p_x+1) = f(Sp_x, *(x+1));
	*(p_x+2) = f(Sp_x, *(x+2));
	*(p_x+3) = f(Sp_x, *(x+3));
      }

      for (; x != end2; ++x)
	*p_x++ = f(Sp_x, *x);
    }

    //--------------------------------------------------------------------------------
    /**
     * A method that computes the sum of powers of the difference between x
     * and a given row. 
     */ 
  private:
    template <typename InputIterator, typename F>
    inline value_type
    sum_of_p_diff_(size_type row, InputIterator x, value_type Sp_x, value_type *p_x, 
		   F f) const
    {
      size_type nnzr = this->nnzr_[row], j, *ind = this->ind_[row];
      value_type *nz = this->nz_[row];
      value_type val = Sp_x, val1 = 0, val2 = 0;
      size_type *end1 = ind + 4*(nnzr/4), *end2 = ind + nnzr;
      
      while (ind != end1) {
	j = *ind++;
	val1 = *nz++ - x[j];
	f(val, val1);
	val -= p_x[j];
	j = *ind++;
	val2 = *nz++ - x[j];
	f(val, val2);
	val -= p_x[j];
	j = *ind++;
	val1 = *nz++ - x[j];
	f(val, val1);
	val -= p_x[j];
	j = *ind++;
	val2 = *nz++ - x[j];
	f(val, val2);
	val -= p_x[j];
      }
      
      while (ind != end2) {
	j = *ind++;
	val1 = *nz++ - x[j];
	f(val, val1);
	val -= p_x[j];
      }

      // Accuracy issues because of the subtractions,
      // could return negative values
      if (val <= (value_type) 0)
	val = (value_type) 0;

      return val;
    }

    //--------------------------------------------------------------------------------
    /**
     * A method that computes the distance between x and the specified row,
     * parameterized on the norm function. Can be instantiated for L0, L1 and Lmax.
     * Here, we don't need to worry about taking a root, and there are no powers of x
     * to cache, as opposed to one_row_dist_2. The complexity is: nnzr*f().
     */
  private:
    template <typename InputIterator, typename F>
    inline value_type
    one_row_dist_1(size_type row, InputIterator x, F f) const
    {
      const size_type ncols = this->nCols();
      size_type *ind = this->ind_[row], *ind_end = ind + this->nnzr_[row], j = 0;
      value_type *nz = this->nz_[row], d = (value_type) 0.0;

      while (ind != ind_end) { 
	size_type j_end = *ind++;
	while (j != j_end)
	  f(d, x[j++]);
	f(d, x[j++] - *nz++);
      }
      
      if (j < ncols) 
	while (j != ncols) 
	  f(d, x[j++]);

      return d;
    }

    //--------------------------------------------------------------------------------
    /**
     * A method that computes the distance between x and the specified row,
     * parameterized on the norm function. Can be instantiated for L2 or Lp. 
     * Caches the powers of x in nzb_, so that we achieve complexity:
     * nnzr*(2*diff+abs+f.power()) + ncols*f.power(), instead of:
     * nnzr*(diff+abs+f.power()) + nrows*ncols*f.power().
     */
  private:
    template <typename InputIterator, typename F>
    inline value_type 
    one_row_dist_2(size_type row, InputIterator x, F f, 
		   bool take_root =false) const
    {
      value_type Sp_x = 0.0;

      const_cast<self_type*>(this)->compute_powers_(Sp_x, this->nzb_, x, f);
      value_type val = sum_of_p_diff_(row, x, Sp_x, this->nzb_, f);

      if (take_root)
	val = f.root(val);

      return val;
    }

    //--------------------------------------------------------------------------------
    /**
     * A method that computes the distances between x and all the rows in the matrix.
     * The method is parameterized on the norm to use, F.
     * Although it looks very similar to one_row_dist_1, the sums of powers are computed
     * once for all the rows here, where they would be computed for each row if
     * one_row_dist_1 was called. The complexity is: 
     * ncols*(pow) + nnz*(2*diff+f.power()) + nrows*f.root().
     */
  private:
    template <typename InputIterator, typename OutputIterator, typename F>
    inline void 
    all_rows_dist_(InputIterator x, OutputIterator y, F f, 
		   bool take_root =false) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::all_rows_dist_(): "
	  << "No vector stored yet";
      } // End pre-conditions

      const size_type nrows = this->nRows();
      OutputIterator y_begin = y, y_end = y + nrows;
      value_type Sp_x = 0.0;

      const_cast<self_type*>(this)->compute_powers_(Sp_x, this->nzb_, x, f);

      for (size_type i = 0; i != nrows; ++i, ++y) 
	*y = sum_of_p_diff_(i, x, Sp_x, this->nzb_, f);
      
      if (take_root)
	for (y = y_begin; y != y_end; ++y)
	  *y = f.root(*y);
    }

    //--------------------------------------------------------------------------------
    /**
     * A method that finds the k top nearest neighbor, as defined by F.
     */
  private:
    template <typename InputIterator, typename OutputIterator, typename F>
    inline void
    k_nearest_(InputIterator x, OutputIterator nn, F f, 
	       size_type k =1, bool take_root =false) const
    {
      { // Pre-conditions
	NTA_ASSERT(k >= 1)
	  << "NearestNeighbor::k_nearest_(): "
	  << "Invalid number of nearest rows: " << k
	  << " - Should be >= 1, default value is 1";

	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::k_nearest_(): "
	  << "No vector stored yet";
      }

      std::vector<value_type> b(this->nRows());
      all_rows_dist_(x, b.begin(), f, take_root);
      partial_sort_2nd(k, b, nn, std::less<value_type>());
    }

  public:
    //--------------------------------------------------------------------------------
    /**
     * Computes the distance between vector x and a given row
     * of this NearestNeighbor, using the L0 (Hamming) distance:
     * 
     * dist(row, x) = sum(| row[i] - x[i] | > epsilon)
     *
     * Computations are performed on the non-zeros only.
     * 
     * Non-mutating, O(nnzr)
     *
     * @param row [0 <= size_type < nrows] index of row to compute distance from
     * @param x [InputIterator<value_type>] x vector
     * @retval [value_type] distance from x to row of index 'row'
     * 
     * @b Exceptions:
     *  @li row < 0 || row >= nrows (check)
     */
    template <typename InputIterator>
    inline value_type rowL0Dist(size_type row, InputIterator x) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::rowL0Dist(): "
	  << "No vector stored yet";

	NTA_ASSERT(row >= 0 && row < this->nRows())
	  << "NearestNeighbor::rowL0Dist(): "
	  << "Invalid row index: " << row
	  << " - Should be >= 0 and < nrows = " << this->nRows();
      }

      return one_row_dist_1(row, x, Lp0<value_type>());
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the distance between vector x and a given row
     * of this NearestNeighbor, using the L1 (Manhattan) distance:
     * 
     * dist(row, x) = sum(| row[i] - x[i] |)
     *
     * Computations are performed on the non-zeros only.
     * 
     * Non-mutating, O(nnzr)
     *
     * @param row [0 <= size_type < nrows] index of row to compute distance from
     * @param x [InputIterator<value_type>] x vector
     * @retval [value_type] distance from x to row of index 'row'
     * 
     * @b Exceptions:
     *  @li row < 0 || row >= nrows (check)
     */
    template <typename InputIterator>
    inline value_type rowL1Dist(size_type row, InputIterator x) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::rowL1Dist(): "
	  << "No vector stored yet";

	NTA_ASSERT(row >= 0 && row < this->nRows())
	  << "NearestNeighbor::rowL1Dist(): "
	  << "Invalid row index: " << row
	  << " - Should be >= 0 and < nrows = " << this->nRows();
      }

      return one_row_dist_1(row, x, Lp1<value_type>());
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the distance between vector x and a given row
     * of this NearestNeighbor, using the Euclidean distance:
     * 
     * dist(row, x) = [ sum((row[i] - x[i])^2) ] ^ 1/2
     *
     * Computations are performed on the non-zeros only.
     * The square root is optional, controlled by parameter take_root.
     * 
     * Non-mutating, O(ncols + nnzr)
     *
     * @param row [0 <= size_type < nrows] index of row to compute distance from
     * @param x [InputIterator<value_type>] vector of the squared distances to x
     * @param take_root [bool (false)] whether to return the square root of the distance
     *  or the exact value (the square root of the sum of the sqaures). Default is to 
     *  return the square of the distance.
     * @retval [value_type] distance from x to row of index 'row'
     * 
     * @b Exceptions:
     *  @li row < 0 || row >= nrows (check)
     */
    template <typename InputIterator>
    inline value_type 
    rowL2Dist(size_type row, InputIterator x, bool take_root =false) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::rowL2Dist(): "
	  << "No vector stored yet";

	NTA_ASSERT(row >= 0 && row < this->nRows())
	  << "NearestNeighbor::rowL2Dist(): "
	  << "Invalid row index: " << row
	  << " - Should be >= 0 and < nrows = " << this->nRows();
      }

      return one_row_dist_2(row, x, Lp2<value_type>(), take_root);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the distance between vector x and a given row
     * of this NearestNeighbor, using the Lmax distance:
     * 
     * dist(row, x) = max(| row[i] - x[i] |)
     *
     * Computations are performed on the non-zeros only.
     * 
     * Non-mutating, O(nnzr)
     *
     * @param row [0 <= size_type < nrows] index of row to compute distance from
     * @param x [InputIterator<value_type>] x vector
     * @retval [value_type] distance from x to row of index 'row'
     * 
     * @b Exceptions:
     *  @li row < 0 || row >= nrows (check)
     */
    template <typename InputIterator>
    inline value_type rowLMaxDist(size_type row, InputIterator x) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::rowLMaxDist(): "
	  << "No vector stored yet";

	assert_valid_row_(row, "rowLMaxDist");
      } // End pre-conditions

      return one_row_dist_1(row, x, LpMax<value_type>());
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the distance between vector x and a given row
     * of this NearestNeighbor, using the Lp distance:
     * 
     * dist(row, x) = [ sum(|row[i] - x[i]|^p) ] ^ 1/p
     *
     * Computations are performed on the non-zeros only.
     * The square root is optional, controlled by parameter take_root.
     *
     * Non-mutating.
     *
     * @param row [0 <= size_type < nrows] index of row to compute distance from
     * @param x [InputIterator<value_type>] vector of the squared distances to x
     * @param take_root [bool (false)] whether to return the p-th power of the distance
     *  or the exact value (the p-th root of the sum of the p-powers). Default is to 
     *  return the p-th power of the distance.
     * @retval [value_type] distance from x to row of index 'row'
     * 
     * @b Exceptions:
     *  @li row < 0 || row >= nrows (check)
     */
    template <typename InputIterator>
    inline value_type 
    rowLpDist(value_type p, size_type row, InputIterator x, 
	      bool take_root =false) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::rowLpDist(): "
	  << "No vector stored yet";

	assert_valid_row_(row, "rowLpDist");

	NTA_ASSERT(p >= (value_type)0.0)
	  << "NearestNeighbor::rowLpDist():"
	  << "Invalid value for parameter p: " << p
	  << " - Only positive values (p >= 0) are supported";
      } // End pre-conditions

      if (p == (value_type)0.0)
	return rowL0Dist(row, x);

      if (p == (value_type)1.0)
	return rowL1Dist(row, x);

      if (p == (value_type)2.0)
	return rowL2Dist(row, x, take_root);

      return one_row_dist_2(row, x, Lp<value_type>(p), take_root);
    }
  
    //--------------------------------------------------------------------------------
    /**
     * Computes the distance between vector x and all the rows
     * of this NearestNeighbor, using the L0 (Hamming) distance:
     * 
     * dist(row, x) = sum(| row[i] - x[i] | > Epsilon)
     *
     * Computations are performed on the non-zeros only.
     * 
     * Non-mutating, O(nnzr)
     *
     * @param x [InputIterator<value_type>] x vector
     * @param y [OutputIterator<value_type>] vector of distances of x to each row
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void L0Dist(InputIterator x, OutputIterator y) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::L0Dist(): "
	  << "No vector stored yet";
      }

      const size_type nrows = this->nRows();
      Lp0<value_type> f;

      for (size_type i = 0; i != nrows; ++i, ++y) 
	*y = one_row_dist_1(i, x, f);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the distance between vector x and all the rows
     * of this NearestNeighbor, using the L1 (Manhattan) distance:
     * 
     * dist(row, x) = sum(| row[i] - x[i] |)
     *
     * Computations are performed on the non-zeros only.
     * 
     * Non-mutating, O(nnzr)
     *
     * @param x [InputIterator<value_type>] x vector
     * @param y [OutputIterator<value_type>] vector of distances of x to each row
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void L1Dist(InputIterator x, OutputIterator y) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::L1Dist(): "
	  << "No vector stored yet";
      }

      const size_type nrows = this->nRows(), ncols = this->nCols();
      value_type s = 0.0;
      Lp1<value_type> f;

      InputIterator x_ptr = x;
      for (size_type j = 0; j != ncols; ++j, ++x_ptr) 
	this->nzb_[j] = f(s, *x_ptr); 

      for (size_type i = 0; i != nrows; ++i, ++y) {
	size_type *ind = this->ind_[i], *ind_end = ind + this->nnzr_[i];
	value_type *nz = this->nz_[i], d = s;
	for (; ind != ind_end; ++ind, ++nz) {
	  size_type j = *ind;
	  f(d, x[j] - *nz);
	  d -= this->nzb_[j];
	}
        if (d <= (value_type) 0)
          d = (value_type) 0;
	*y = d;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the Euclidean distance between vector x
     * and each row of this NearestNeighbor. 
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InputIterator<value_type>] vector to compute the distance from
     * @param y [OutputIterator<value_type>] vector of the distances to x
     * @param take_root [bool (false)] whether to return the square root of the 
     *  distances
     *  or their exact value (the square root of the sum of the squares). Default is 
     *  to 
     *  return the square of the distances. 
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void L2Dist(InputIterator x, OutputIterator y, bool take_root =false) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::L2Dist(): "
	  << "No vector stored yet";
      }

      all_rows_dist_(x, y, Lp2<value_type>(), take_root);
    }
    
    //--------------------------------------------------------------------------------
    /**
     * Computes the Lmax distance between vector x and each row of this NearestNeighbor. 
     *
     * Non-mutating, O(nrows*ncols)
     *
     * @param x [InputIterator<value_type>] vector to compute the distance from
     * @param y [OutputIterator<value_type>] vector of the distances to x
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void LMaxDist(InputIterator x, OutputIterator y) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::LMaxDist(): "
	  << "No vector stored yet";
      }

      const size_type nrows = this->nRows();
      LpMax<value_type> f;
      
      for (size_type i = 0; i != nrows; ++i, ++y) 
	*y = one_row_dist_1(i, x, f);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the p-th power of the Lp distance between vector x
     * and each row of this NearestNeighbor. Puts the result 
     * in vector y. If take_root is true, we take the p-th root of the sums,
     * if not, y will contain the sum of the p-th powers only. 
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InputIterator<value_type>] vector to compute the distance from
     * @param y [OutputIterator<value_type>] vector of the squared distances to x
     * @param take_root [bool (false)] whether to return the p-th power of the distances
     *  or their exact value (the p-th root of the sum of the p-powers). Default is to 
     *  return the p-th power of the distances. 
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void 
    LpDist(value_type p, 
	   InputIterator x, OutputIterator y, bool take_root=false) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::LpDist(): "
	  << "No vector stored yet";
	
	NTA_ASSERT(p >= (value_type)0.0)
	  << "NearestNeighbor::LpDist():"
	  << "Invalid value for parameter p: " << p
	  << " - Only positive values (p >= 0) are supported";
      }
      
      if (p == (value_type)0.0) {
	L0Dist(x, y);
	return;
      }

      if (p == (value_type)1.0) {
	L1Dist(x, y);
	return;
      }

      if (p == (value_type)2.0) {
	L2Dist(x, y, take_root);
	return;
      }

      all_rows_dist_(x, y, Lp<value_type>(p), take_root);
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the row nearest to x, where nearest is defined as the row which has the 
     * smallest L0 (Hamming) distance to x. If k > 1, finds the k nearest rows to x.
     *
     * Non-mutating, O(nnz) + complexity of partial sort up to k if  k > 1.
     *
     * @param x [InputIterator<value_type>] vector to compute the distance from
     * @param nn [OutputIterator] the indices and distances of the nearest rows (pairs)
     * @param k [size_type > 0, (1)] the number of nearest rows to retrieve
     *
     * @b Exceptions:
     *  @li If k < 1.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void
    L0Nearest(InputIterator x, OutputIterator nn, size_type k =1) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::L0Nearest(): "
	  << "No vector stored yet";

	NTA_ASSERT(k >= 1)
	  << "NearestNeighbor::L0Nearest():"
	  << "Invalid number of nearest rows: " << k
	  << " - Should be >= 1, default is 1";
      }

      k_nearest_(x, nn, Lp0<value_type>(), k);
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the row nearest to x, where nearest is defined as the row which has the 
     * smallest L1 (Manhattan) distance to x. If k > 1, finds the k nearest rows to x.
     *
     * Non-mutating, O(nnz) + complexity of partial sort up to k if  k > 1.
     *
     * @param x [InputIterator<value_type>] vector to compute the distance from
     * @param nn [OutputIterator] the indices and distances of the nearest rows (pairs)
     * @param k [size_type > 0, (1)] the number of nearest rows to retrieve
     *
     * @b Exceptions:
     *  @li If k < 1.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void
    L1Nearest(InputIterator x, OutputIterator nn, size_type k =1) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::L1Nearest(): "
	  << "No vector stored yet";

	NTA_ASSERT(k >= 1)
	  << "NearestNeighbor::L1Nearest():"
	  << "Invalid number of nearest rows: " << k
	  << " - Should be >= 1, default is 1";
      }

      k_nearest_(x, nn, Lp1<value_type>(), k);
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the row nearest to x, where nearest is defined as the row which has the 
     * smallest L2 (Euclidean) distance to x. If k > 1, finds the k nearest rows to x.
     *
     * Non-mutating, O(nnz) + complexity of partial sort up to k if  k > 1.
     *
     * @param x [InputIterator<value_type>] vector to compute the distance from
     * @param nn [OutputIterator] the indices and distances of the nearest rows (pairs)
     * @param k [size_type > 0, (1)] the number of nearest rows to retrieve
     * @param take_root [bool (false)] whether to return the square root of the distances
     *  or their exact value (the square root of the sum of the squares). Default is to 
     *  return the square of the distances.  
     *
     * @b Exceptions:
     *  @li If k < 1.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void
    L2Nearest(InputIterator x, OutputIterator nn, size_type k =1, 
	      bool take_root =false) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::L2Nearest(): "
	  << "No vector stored yet";

	NTA_ASSERT(k >= 1)
	  << "NearestNeighbor::L2Nearest():"
	  << "Invalid number of nearest rows: " << k
	  << " - Should be >= 1, default is 1";
      }

      k_nearest_(x, nn, Lp2<value_type>(), k, take_root);
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the row nearest to x, where nearest is defined as the row which has the 
     * smallest Lmax distance to x. If k > 1, finds the k nearest rows to x.
     *
     * Non-mutating, O(nnz) + complexity of partial sort up to k if  k > 1.
     *
     * @param x [InputIterator<value_type>] vector to compute the distance from
     * @param nn [OutputIterator] the indices and distances of the nearest rows (pairs)
     * @param k [size_type > 0, (1)] the number of nearest rows to retrieve
     *
     * @b Exceptions:
     *  @li If k < 1.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void
    LMaxNearest(InputIterator x, OutputIterator nn, size_type k =1) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::LMaxNearest(): "
	  << "No vector stored yet";

	NTA_ASSERT(k >= 1)
	  << "NearestNeighbor::LMaxNearest():"
	  << "Invalid number of nearest rows: " << k
	  << " - Should be >= 1, default is 1";
      }
      
      std::vector<value_type> b(this->nRows());
      LMaxDist(x, b.begin());
      partial_sort_2nd(k, b, nn, std::less<value_type>());
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the row nearest to x, where nearest is defined as the row which has the 
     * smallest Lp distance to x. If k > 1, finds the k nearest rows to x.
     *
     * Non-mutating, O(nnz) + complexity of partial sort up to k if  k > 1.
     *
     * @param x [InputIterator<value_type>] vector to compute the distance from
     * @param nn [OutputIterator1] the indices and distances of the nearest rows (pairs)
     * @param k [size_type > 0, (1)] the number of nearest rows to retrieve
     * @param take_root [bool (false)] whether to return the p-th power of the distances
     *  or their exact value (the p-th root of the sum of the p-powers). Default is to 
     *  return the p-th power of the distances.
     *
     * @b Exceptions:
     *  @li If p < 0.
     *  @li If k < 1.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void
    LpNearest(value_type p, InputIterator x, OutputIterator nn, 
	      size_type k =1, bool take_root =false) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::LpNearest(): "
	  << "No vector stored yet";

	NTA_ASSERT(p >= (value_type)0.0)
	  << "NearestNeighbor::LpNearest():"
	  << "Invalid value for parameter p: " << p
	  << " - Only positive values (p >= 0) are supported";

	NTA_ASSERT(k >= 1)
	  << "NearestNeighbor::LpNearest():"
	  << "Invalid number of nearest rows: " << k
	  << " - Should be >= 1, default is 1";
      }

      if (p == (value_type)0.0) {
	L0Nearest(x, nn, k);
	return;
      }

      if (p == (value_type)1.0) {
	L1Nearest(x, nn, k);
	return;
      }

      if (p == (value_type)2.0) {
	L2Nearest(x, nn, k, take_root);
	return;
      }

      k_nearest_(x, nn, Lp<value_type>(p), k, take_root);
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator1, 
	      typename InputIterator2, 
	      typename OutputIterator>
    inline void 
    LpNearest(value_type p, InputIterator1 ind, InputIterator1 ind_end,
	      InputIterator2 nz, OutputIterator nn,
	      size_type k =1, bool take_root =false) const
    {
      std::vector<value_type> x(this->nCols());
      to_dense(ind, ind_end, nz, nz + (ind_end - ind), x.begin(), x.end());
      LpNearest(p, x.begin(), nn, k, take_root);
    }

    //--------------------------------------------------------------------------------  
    /**
     * Computes the "nearest-dot" distance between vector x
     * and each row in this NearestNeighbor. Returns the index of 
     * the row that maximizes the dot product as well as the 
     * value of this dot-product.
     *
     * Note that this equivalent to L2Nearest if all the vectors are 
     * normalized.
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InputIterator<value_type>] vector to compute the distance from
     * @retval [std::pair<size_type, value_type>] index of the row nearest
     *  to x, and value of the distance between x and that row
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator>
    inline std::pair<size_type, value_type> dotNearest(InputIterator x) const
    {
      {
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::dotNearest(): "
	  << "No vector stored yet";
      }

      size_type i, k, nnzr, *ind, end, nrows = this->nRows();
      value_type val, *nz; 

      size_type arg_i = 0;
      value_type max_v = - std::numeric_limits<value_type>::max();

      for (i = 0; i != nrows; ++i) {

	val = 0;
	nnzr = this->nnzr_[i];
	ind = this->ind_[i];
	nz = this->nz_[i];
	end = 4 * (nnzr / 4);

	for (k = 0; k != end; k += 4) 
	  val += nz[k] * x[ind[k]] + nz[k+1] * x[ind[k+1]]
	    + nz[k+2] * x[ind[k+2]] + nz[k+3] * x[ind[k+3]];

	for (k = end; k != nnzr; ++k)
	  val += nz[k] * x[ind[k]];

	if (val > max_v) {
	  arg_i = i;
	  max_v = val;
	}
      }

      return std::make_pair(arg_i, max_v);
    }

    //--------------------------------------------------------------------------------
    /**
     * EXPERIMENTAL 
     * This method computes the std dev of each component of the vectors, and 
     * scales them by that standard deviation before computing the norms.
     * Distance values are distorted by the standard deviation.
     */
    std::vector<value_type> stddev_;

    template <typename InputIterator, typename OutputIterator>
    inline void
    LpNearest_w(value_type p, InputIterator x, OutputIterator nn,
		size_type k =1, bool take_root =false)
    {
      { // Pre-conditions
	NTA_ASSERT(p >= (value_type)0.0)
	  << "NearestNeighbor::LpNearest_w():"
	  << "Invalid value for parameter p: " << p
	  << " - Only positive values (p >= 0) are supported";

	NTA_ASSERT(k >= 1)
	  << "NearestNeighbor::LpNearest_w():"
	  << "Invalid number of nearest rows: " << k
	  << " - Should be >= 1, default is 1";
      }

      const size_type nrows = this->nRows(), ncols = this->nCols();
      std::vector<value_type> e(ncols, 0), e2(ncols, 0);

      if (stddev_.empty()) {

	stddev_.resize(ncols, 0);
	
	for (size_type i = 0; i != nrows; ++i) {
	  size_type *ind = this->ind_[i], *ind_end = ind + this->nnzr_[i];
	  value_type *nz = this->nz_[i];
	  while (ind != ind_end) {
	    size_type idx = *ind++;
	    value_type val = *nz++;
	    e[idx] += val;
	    e2[idx] += val * val;
	  }
	}

	nta::Sqrt<value_type> sf;

	for (size_type j = 0; j != ncols; ++j) 
	  stddev_[j] = sf((e2[j] - e[j]*e[j]/nrows) / (nrows-1));
      }
	
      Lp<value_type> f(p);
      value_type Sp_x = 0;
      for (size_type j = 0; j != ncols; ++j) 
	this->nzb_[j] = f(Sp_x, x[j]/stddev_[j]);

      std::vector<value_type> b(nrows);
      
      for (size_type i = 0; i != nrows; ++i) {
	size_type *ind = this->ind_[i], *ind_end = ind + this->nnzr_[i];
	value_type *nz = this->nz_[i], d = Sp_x;
	while (ind != ind_end) {
	  size_type j = *ind++;
	  f(d, (*nz++ - x[j])/stddev_[j]);
	  d -= this->nzb_[j];
	}
	if (d <= (value_type) 0)
	  d = (value_type) 0;
	b[i] = d;
      }

      partial_sort_2nd(k, b, nn, std::less<value_type>());
    }

    //--------------------------------------------------------------------------------
    // RBF
    //--------------------------------------------------------------------------------
    template <typename InputIterator, typename OutputIterator>
    inline void rbf(value_type p, value_type k, 
		    InputIterator in_begin, OutputIterator out_begin) const
    {
     { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::rbf(): "
	  << "No vector stored yet";

	NTA_ASSERT(p >= (value_type)0.0)
	  << "NearestNeighbor::rbf():"
	  << "Invalid value for parameter p: " << p
	  << " - Only positive values (p >= 0) are supported";
      } // End pre-conditions

     LpDist(p, in_begin, out_begin, false);
     
     range_exp(k, out_begin, out_begin + this->nRows());
    }

    //--------------------------------------------------------------------------------
    // Proj nearest
    //--------------------------------------------------------------------------------
  private:
    template <typename InputIterator, typename OutputIterator, typename F>
    inline void
    proj_all_rows_dist_(InputIterator x, OutputIterator y, F f, 
			bool take_root =false) const
    {
      const size_type nrows = this->nRows();
      OutputIterator y_begin = y, y_end = y_begin + nrows;
      
      for (size_type row = 0; row != nrows; ++row, ++y) {
	size_type *ind = this->ind_[row];
	size_type *ind_end = ind + this->nNonZerosOnRow(row);
	value_type *nz = this->nz_[row], val = 0;
	for (; ind != ind_end; ++ind, ++nz) 
	  f(val, *nz - *(x + *ind));
	*y = val;
      }

      if (take_root) {
	for (y = y_begin; y != y_end; ++y)
	  *y = f.root(*y);
      }
    }

    //--------------------------------------------------------------------------------
  public:
    template <typename InputIterator, typename OutputIterator>
    inline void 
    projLpDist(value_type p, InputIterator x, OutputIterator y, 
	       bool take_root =false) const
    {
       { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::projLpDist(): "
	  << "No vector stored yet";

	NTA_ASSERT(p >= (value_type)0.0)
	  << "NearestNeighbor::projLpDist():"
	  << "Invalid value for parameter p: " << p
	  << " - Only positive values (p >= 0) are supported";
      } // End pre-conditions
       
       if (p == (value_type) 0.0) {
	 proj_all_rows_dist_(x, y, Lp0<value_type>(), take_root);
	 
       } else if (p == (value_type) 1.0) {
	 proj_all_rows_dist_(x, y, Lp1<value_type>(), take_root);
	 
       } else if (p == (value_type) 2.0) {
	 proj_all_rows_dist_(x, y, Lp2<value_type>(), take_root);

       } else {
	 proj_all_rows_dist_(x, y, Lp<value_type>(p), take_root);
       }
    }
    
    //--------------------------------------------------------------------------------
    /**
     * Finds the k-nearest neighbors to x, ignoring the zeros of each vector
     * stored in this matrix.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void 
    projLpNearest(value_type p, InputIterator x, OutputIterator nn,
		  size_type k =1, bool take_root =false) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::projLpNearest(): "
	  << "No vector stored yet";

	NTA_ASSERT(p >= (value_type)0.0)
	  << "NearestNeighbor::projLpNearest():"
	  << "Invalid value for parameter p: " << p
	  << " - Only positive values (p >= 0) are supported";

	NTA_ASSERT(k >= 1)
	  << "NearestNeighbor::projLpNearest():"
	  << "Invalid number of nearest rows: " << k
	  << " - Should be >= 1, default is 1";
      } // End pre-conditions

      std::vector<value_type> b(this->nRows());
      projLpDist(p, x, b.begin(), take_root);
      partial_sort_2nd(k, b, nn, std::less<value_type>());
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator1, 
	      typename InputIterator2, 
	      typename OutputIterator>
    inline void 
    projLpNearest(value_type p, InputIterator1 ind, InputIterator1 ind_end,
		  InputIterator2 nz, OutputIterator nn,
		  size_type k =1, bool take_root =false) const
    {
      std::vector<value_type> x(this->nCols());
      to_dense(ind, ind_end, nz, nz + (ind_end - ind), x.begin(), x.end());
      projLpNearest(p, x.begin(), nn, k, take_root);
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator, typename OutputIterator>
    inline void projRbf(value_type p, value_type k, 
			InputIterator in_begin, OutputIterator out_begin) const
    {
      { // Pre-conditions
	NTA_ASSERT(this->nRows() > 0)
	  << "NearestNeighbor::projRbf(): "
	  << "No vector stored yet";

	NTA_ASSERT(p >= (value_type)0.0)
	  << "NearestNeighbor::projRbf():"
	  << "Invalid value for parameter p: " << p
	  << " - Only positive values (p >= 0) are supported";
      } // End pre-conditions

      projLpDist(p, in_begin, out_begin, false);

      range_exp(k, out_begin, out_begin + this->nRows());
    }

  }; // end class NearestNeighbor

  //--------------------------------------------------------------------------------

} // end namespace nta

#endif // NTA_NEAREST_NEIGHBOR_HPP



