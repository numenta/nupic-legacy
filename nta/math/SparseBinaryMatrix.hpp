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
 * Definition and implementation for SparseBinaryMatrix
 */

#ifndef NTA_SPARSE_BINARY_MATRIX_HPP
#define NTA_SPARSE_BINARY_MATRIX_HPP

#include <sstream>

#include <nta/math/math.hpp>
#include <nta/math/stl_io.hpp>
#include <nta/math/array_algo.hpp>

//--------------------------------------------------------------------------------
namespace nta {

  //--------------------------------------------------------------------------------
  /**
   * A matrix of 0 and 1, where only the indices of the 1s are stored.
   *
   * WATCH OUT! That the U type doesn't become too small to store parameters
   * of the matrix, such as total number of non-zeros.
   *
   */
  template <typename UI1 =nta::UInt32, typename UI2 =nta::UInt32>
  class SparseBinaryMatrix
  {
  public:
    typedef UI1 size_type;
    typedef UI2 nz_index_type;
    typedef std::vector<nz_index_type> Row;

  private:
    nz_index_type ncols_;    
    std::vector<Row> ind_;  // indices of the non-zeros
    Row buffer_;

  public:
    //--------------------------------------------------------------------------------
    inline SparseBinaryMatrix()
      : ncols_(0),
        ind_(),
        buffer_() { }

    inline SparseBinaryMatrix(std::istream& inStream)
      : ncols_(0),
        ind_(),
        buffer_()
    {
      fromCSR(inStream);
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline SparseBinaryMatrix(size_type nrows, size_type ncols,
                              InputIterator begin, InputIterator end)
      : ncols_(0),
        ind_(),
        buffer_()
    {
      fromDense(nrows, ncols, begin, end);
    }

    //--------------------------------------------------------------------------------
    inline SparseBinaryMatrix(size_type ncols)
      : ncols_(0),
        ind_(),
        buffer_()
    {
      nCols(ncols);
      buffer_.resize(nCols());
    }

    //--------------------------------------------------------------------------------
    inline SparseBinaryMatrix(size_type nrows, size_type ncols)
      : ncols_(ncols),
        ind_(nrows),
        buffer_(ncols)
    {}

    //--------------------------------------------------------------------------------
    inline SparseBinaryMatrix(const SparseBinaryMatrix& o)
      : ncols_(0),
        ind_(),
        buffer_()
    {
      copy(o);
    }

    //--------------------------------------------------------------------------------
    inline SparseBinaryMatrix& operator=(const SparseBinaryMatrix& o)
    {
      if (&o != this) 
        copy(o);

      return *this;
    }

    //--------------------------------------------------------------------------------
    inline void copy(const SparseBinaryMatrix& o)
    {
      ind_.clear();
      ind_.resize(o.nRows());
      for (size_type r = 0; r != o.nRows(); ++r)
        ind_[r].insert(ind_[r].end(), o.ind_[r].begin(), o.ind_[r].end());
      nCols(o.nCols());
      buffer_.resize(nCols());
    }

    //--------------------------------------------------------------------------------
    inline ~SparseBinaryMatrix()
    {
      ind_.clear();
      ncols_ = 0;
      buffer_.clear();
    }

    //--------------------------------------------------------------------------------
    /**
     * Fills this matrix with random rows that all have the same number of non-zeros.
     * Discards the current state of this matrix, if any.
     */
    inline void randomInitialize(size_type nnz, size_type seed =0)
    {
      NTA_ASSERT(nRows());
      NTA_ASSERT(nCols());
      NTA_ASSERT(nnz);

      nta::Random rng(seed);

      for (size_type i = 0; i != nCols(); ++i)
        buffer_[i] = i;
      
      for (size_type i = 0; i != nRows(); ++i) {
        ind_[i].resize(nnz);
        std::random_shuffle(buffer_.begin(), buffer_.end(), rng);
        std::copy(buffer_.begin(), buffer_.begin() + nnz, ind_[i].begin());
      }

      NTA_ASSERT(nRows());
      NTA_ASSERT(nCols());
      NTA_ASSERT(buffer_.size() == nCols());
      NTA_ASSERT(nNonZeros() == nRows() * nnz);
#ifdef NTA_ASSERTIONS_ON
      for (size_type i = 0; i != nRows(); ++i)
        NTA_ASSERT(nNonZerosOnRow(i) == nnz);
#endif
    }

    //--------------------------------------------------------------------------------
    inline const std::string getVersion(bool binary =false) const 
    {
      if (binary)
        return std::string("sm_01_1.0_bin");
      else
        return std::string("sm_01_1.0");
    }

    //--------------------------------------------------------------------------------
    inline size_type nRows() const { return ind_.size(); }

    //--------------------------------------------------------------------------------
    inline nz_index_type nCols() const { return ncols_; }

    //--------------------------------------------------------------------------------
    inline size_type capacity() const 
    {
      size_type n = 0;
      for (size_type i = 0; i != nRows(); ++i)
	n += ind_[i].capacity();
      return n;
    }

    //--------------------------------------------------------------------------------
    inline size_type nBytes() const
    {
      size_type n = sizeof(SparseBinaryMatrix);
      n += ind_.capacity() * sizeof(Row);
      for (size_type i = 0; i != nRows(); ++i)
	n += ind_[i].capacity() * sizeof(nz_index_type);
      n += buffer_.capacity() * sizeof(nz_index_type);
      return n;
    }

    //--------------------------------------------------------------------------------
    /**
     * Adjusts row storage to be exactly the size required to store the indices 
     * of the non-zeros.
     */
    inline void compact() 
    {
      if (capacity() == nNonZeros()
	  && buffer_.size() == buffer_.capacity())
	return;

      for (size_type i = 0; i != nRows(); ++i) {
	if (ind_[i].capacity() != ind_[i].size()) {
	  Row buffer;
	  buffer.reserve(ind_[i].size());
	  buffer.insert(buffer.end(), ind_[i].begin(), ind_[i].end());
	  ind_[i].swap(buffer);
	}
      }

      Row sized_row(nCols());
      buffer_.swap(sized_row);

      NTA_ASSERT(capacity() == nNonZeros());
    }

    //--------------------------------------------------------------------------------
    /**
     * Deallocates memory used by this instance. Doesn't change the number of rows
     * or columns.
     */
    inline void clear()
    {
      std::vector<Row> empty;
      ind_.swap(empty);
      Row empty2;
      buffer_.swap(empty2);
      ncols_ = 0;

      NTA_ASSERT(nBytes() == sizeof(SparseBinaryMatrix));
    }

    //--------------------------------------------------------------------------------
    /**
     * If the new size is (0,0), this is equivalent to calling clear().
     * If the new size is smaller than the old one, some non-zeros are discarded. 
     * If the new size is larger than the old one, the non-zeros are unchanged.
     */
    inline void resize(size_type new_nrows, size_type new_ncols)
    {
      if (new_nrows == 0 && new_ncols == 0) {
        clear();
        return;
      }

      if (new_ncols < nCols()) {
        typename Row::iterator c;
        for (size_type i = 0; i != nRows(); ++i) {
          c = std::lower_bound(ind_[i].begin(), ind_[i].end(), new_ncols);
          ind_[i].erase(c, ind_[i].end());
        }
      }

      ncols_ = new_ncols;
      buffer_.resize(new_ncols);

      if (new_nrows < nRows()) {

        ind_.erase(ind_.begin() + new_nrows, ind_.end());

      } else if (new_nrows > nRows()) {
        
        ind_.resize(new_nrows);

      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns a binary vector of size nRows, which contains true if the corresponding
     * row is zero, false otherwise. Also returns number of zero rows.
     */
    template <typename OutputIterator>
    inline size_type 
    zeroRowsIndicator(OutputIterator it, OutputIterator it_end) const
    {
      {
        NTA_ASSERT((size_type)(it_end - it) == nRows());
      }

      size_type counter = 0;
      for (size_type r = 0; r != nRows(); ++r, ++it) 
        if (ind_[r].size() == 0) {
          *it = true;
          ++counter;
        } else {
          *it = false;
        }
      return counter;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns a binary vector of size nRows, which contains true if the corresponding
     * row is non-zeros, false otherwise. Also returns number of non-zero rows.
     */
    template <typename OutputIterator>
    inline size_type 
    nonZeroRowsIndicator(OutputIterator it, OutputIterator it_end) const
    {
      {
        NTA_ASSERT((size_type)(it_end - it) == nRows());
      }

      size_type counter = 0;
      for (size_type r = 0; r != nRows(); ++r, ++it) 
        if (!ind_[r].empty()) {
          *it = true;
          ++ counter;
        } else {
          *it = false;
        }
      return counter;
    }

    //--------------------------------------------------------------------------------
    inline size_type nNonZerosOnRow(size_type row) const 
    { 
      { // Pre-conditions
        NTA_ASSERT(/*0 <= row &&*/ row < nRows())
          << "SparseBinaryMatrix::nNonZerosOnRow: "
          << "Invalid row index: " << row
          << " - Should be 0 <= and < n rows = " << nRows();
      } // End pre-conditions
      
      return ind_[row].size(); 
    }

    //--------------------------------------------------------------------------------
    inline size_type nNonZeros() const
    {
      size_type n = 0;
      for (size_type i = 0; i != nRows(); ++i)
        n += nNonZerosOnRow(i);
      return n;
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    inline void nNonZerosPerRow(OutputIterator begin, OutputIterator end) const 
    { 
      { // Pre-conditions
	NTA_ASSERT((size_type)(end - begin) == nRows())
	  << "SparseBinaryMatrix::nNonZerosPerRow: "
	  << "Not enough memory";
      } // End pre-conditions

      for (size_type row = 0; row != nRows(); ++row)
	*begin++ = nNonZerosOnRow(row);
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    inline void nNonZerosPerCol(OutputIterator begin, OutputIterator end) const
    {
      { // Pre-conditions
	NTA_ASSERT((size_type)(end - begin) == nCols())
	  << "SparseBinaryMatrix::nNonZerosPerCol: "
	  << "Not enough memory";
      } // End pre-conditions

      typename std::vector<Row>::const_iterator row;
      typename Row::const_iterator j;

      std::fill(begin, end, (size_type) 0);
      for (row = ind_.begin(); row != ind_.end(); ++row) 
	for (j = row->begin(); j != row->end(); ++j)
	  *(begin + *j) += 1;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of non-zeros in a specified range of a given row.
     */
    inline size_type
    nNonZerosInRowRange(size_type row, size_type col_begin, size_type col_end) const
    {
      { // Pre-conditions
        NTA_ASSERT(row < nRows());
        NTA_ASSERT(col_end <= nCols());
        NTA_ASSERT(col_begin <= col_end);
      } // End pre-conditions

      typename Row::const_iterator c1, c2;  
      c1 = std::lower_bound(ind_[row].begin(), ind_[row].end(), col_begin);
      if (col_end == nCols())
        c2 = ind_[row].end();
      else
        c2 = std::lower_bound(c1, ind_[row].end(), col_end);
      
      return (size_type) (c2 - c1);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of non-zeros in a box defined by the indices of the first 
     * and one past the last row, and the first and one past the last column, i.e.
     * the box is: [row_begin, row_end) X [col_begin, col_end).
     *
     * @param row_begin [0 <= size_type <= row_end] the first row of the box to look into
     * @param row_end [row_begin <= size_type <= nrows] one past the end of the last row
     *  of the box to look into
     * @param col_begin [0 <= size_type <= col_end] the first col of the box to look into
     * @param col_end [col_begin <= size_type <= ncols] one past the end of the last col
     *  of the box to look into
     * @retval [0 <= size_type <= box size] number of non-zeros found in the box,
     *  where box size = (row_end - row_begin) * (col_end - col_begin)
     *
     * @b Complexity:
     *  @li O(2 * (row_end - row_begin) * log(nnzr))
     *  
     * @b Exceptions:
     *  @li If (row_begin, row_end) not a valid row range (assert)
     *  @li If (col_begin, col_end) not a valid col range (assert)
     */
    inline
    size_type nNonZerosInBox(size_type row_begin, size_type row_end,
			     size_type col_begin, size_type col_end) const
    {
      { // Pre-conditions
        NTA_ASSERT(row_end <= nRows() && row_begin <= row_end);
        NTA_ASSERT(col_end <= nCols() && col_begin <= col_end);
      } // End pre-conditions

      size_type count = 0;

      for (size_type row = row_begin; row != row_end; ++row) 
	count += nNonZerosInRowRange(row, col_begin, col_end);

      return count;
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator, typename Summary>
    inline void 
    nNonZerosPerBox(InputIterator row_inds_begin, InputIterator row_inds_end, 
		    InputIterator col_inds_begin, InputIterator col_inds_end, 
		    Summary& summary) const
    {
      { // Pre-conditions
	ASSERT_VALID_RANGE(row_inds_begin, row_inds_end, 
                           "SparseBinaryMatrix nNonZerosPerBox");
	ASSERT_VALID_RANGE(col_inds_begin, col_inds_end, 
                           "SparseBinaryMatrix nNonZerosPerBox");
	// Other pre-conditions checked in nNonZerosInBox
      } // End pre-conditions

      size_type n_i = (size_type)(row_inds_end - row_inds_begin);
      size_type n_j = (size_type)(col_inds_end - col_inds_begin);
      summary.resize(n_i, n_j);

      size_type box_i = 0, prev_row = 0;
      for (InputIterator row = row_inds_begin; row != row_inds_end; ++row, ++box_i) {
	size_type prev_col = 0, box_j = 0;
	for (InputIterator col = col_inds_begin; col != col_inds_end; ++col, ++box_j) {
	  summary.set(box_i, box_j, nNonZerosInBox(prev_row, *row, prev_col, *col));
	  prev_col = *col;
	}
	prev_row = *row;
      }
    }
    
    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    void rowSums(OutputIterator begin, OutputIterator end) const
    {
      nNonZerosPerRow(begin, end);
    }
    
    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    void colSums(OutputIterator begin, OutputIterator end) const
    {
      nNonZerosPerCol(begin, end);
    }

    //--------------------------------------------------------------------------------
    inline size_type get(size_type row, size_type col) const
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= row &&*/ row < nRows())
	  << "SparseBinaryMatrix::get: Invalid row index: " << row
	  << " - Should be < number of rows: " << nRows();

	NTA_ASSERT(/*0 <= col &&*/ col < nCols())
	  << "SparseBinaryMatrix::get: Invalid col index: " << col
	  << " - Should be < number of columns: " << nCols();
      } // End pre-conditions

      typename Row::const_iterator it =
	std::lower_bound(ind_[row].begin(), ind_[row].end(), col);

      if (it == ind_[row].end() || *it != col)
	return (size_type) 0;
      else
	return (size_type) 1;
    }

    //--------------------------------------------------------------------------------
    /**
     * Like get(i,j), but where n = i*ncols + j
     */
    inline size_type get_linear(size_type n) const
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= n &&*/ n < nRows() * nCols())
	  << "SparseBinaryMatrix::get_linear: "
	  << "Invalid index: " << n
	  << " - Should be < n rows * n cols: " << nRows() * nCols();
      } // End pre-conditions

      return get(n / nCols(), n % nCols());
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the indices (i,j) of all the non-zeros, in lexicographic order (ordered
     * by increasing row, then by increasing column).
     */
    template <typename OutputIterator1>
    inline void getAllNonZeros(OutputIterator1 nz_i, OutputIterator1 nz_j) const 
    {
      for (size_type i = 0; i != nRows(); ++i) {
	const Row& row = ind_[i];
	for (size_type k = 0; k != row.size(); ++k) {
	  *nz_i++ = i;
	  *nz_j++ = row[k];
	}
      }
    }

    //--------------------------------------------------------------------------------
    struct lexicographic_order 
      : public std::binary_function<bool, 
				    std::pair<size_type, size_type>,
				    std::pair<size_type, size_type> >
    {
      inline bool operator()(const std::pair<size_type,size_type>& a,
			     const std::pair<size_type,size_type>& b) const
      {
	if (a.first < b.first)
	  return true;
	else if (a.first == b.first)
	  if (a.second < b.second)
	    return true;
	return false;
      }
    };

    //--------------------------------------------------------------------------------
    /**
     * Clear this instance and create a new one that has non-zeros only at the 
     * positions passed in.
     *
     * If the flag "clean" is true, then we assume that the non-zeros are 
     * unique, in increasing lexicographic order, and have values > epsilon.
     * If "clean" is false, we sort the values and remove the non-zeros
     * below epsilon, which is a lot slower.
     */
    template <typename InputIterator1, typename InputIterator2>
    inline void setAllNonZeros(size_type nrows, nz_index_type ncols,
			       InputIterator1 nz_i, InputIterator1 nz_i_end,
			       InputIterator2 nz_j, InputIterator2 nz_j_end,
			       bool clean =true)
    {
      { // Pre-conditions
        const char* where = "SparseBinaryMatrix::setAllNonZeros: ";

	ASSERT_INPUT_ITERATOR(InputIterator1);
	ASSERT_INPUT_ITERATOR(InputIterator2);

	NTA_ASSERT(nz_j_end - nz_j == nz_i_end - nz_i)
	  << where << "Invalid range";

#ifdef NTA_ASSERTIONS_ON

        if (nz_i_end != nz_i && clean) {
          InputIterator1 ii = nz_i, iip = ii;
          InputIterator2 jj = nz_j, jjp = jj;
          ++ii; ++jj;
          for (; ii != nz_i_end; iip = ii, jjp = jj, ++ii, ++jj) {
            NTA_ASSERT(*iip < *ii || *jjp < *jj)
              << where
              << "Repeated or out-of-order non-zero indices: " 
              << "(" << *iip << ", " << *jjp << ") and (" 
              << *ii << ", " << *jj << ")";
          }
        }

        InputIterator1 iii = nz_i;
        InputIterator2 jjj = nz_j;
        for (; iii != nz_i_end; ++iii, ++jjj) {
          NTA_ASSERT(*iii < nrows)
            << where << "Invalid row index: " << *iii
            << " - Should be < number of rows: " << nrows;
          NTA_ASSERT(*jjj < ncols)
            << where << "Invalid col index: " << *jjj
            << " - Should be < number of cols: " << ncols;
        }
#endif
      } // End pre-conditions

      clear();
      ncols_ = ncols;
      ind_.resize(nrows);
      buffer_.resize(ncols);

      std::vector<size_type> nnzr(nrows, 0);

      if (clean) {

        for (InputIterator1 it = nz_i; it != nz_i_end; ++it) 
          ++ nnzr[*it];
        
        for (size_type i = 0; i != nrows; ++i) {
	  ind_[i].resize(nnzr[i]);
	  for (size_type k = 0; k != nnzr[i]; ++k) 
	    ind_[i][k] = *nz_j++;
	}

      } else {

        typedef std::pair<size_type, size_type> IJ;
        typedef std::set<IJ, lexicographic_2<size_type, size_type> > S;
        typename S::const_iterator it;
        S s;

	for (; nz_i != nz_i_end; ++nz_i, ++nz_j) {
          IJ ij(*nz_i, *nz_j);
          it = s.find(ij);
          if (it == s.end()) {
            s.insert(ij);
            ++ nnzr[*nz_i];
          }
        }
        
        it = s.begin();

	for (size_type i = 0; i != nrows; ++i)
	  for (size_type k = 0; k != nnzr[i]; ++k, ++it) 
	    ind_[i].push_back(it->second);
      }
    }

    //--------------------------------------------------------------------------------
    template <typename value_type>
    inline void set(size_type row, size_type col, value_type val) 
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= row &&*/ row < nRows())
	  << "SparseBinaryMatrix::set: Invalid row index: " << row
	  << " - Should be < number of rows: " << nRows();
	
	NTA_ASSERT(/*0 <= col &&*/ col < nCols())
	  << "SparseBinaryMatrix::set: Invalid col index: " << col
	  << " - Should be < number of columns: " << nCols();
       } // End pre-conditions

      typename Row::iterator it;
      it = std::lower_bound(ind_[row].begin(), ind_[row].end(), col);

      if (nta::nearlyZero(val)) {

	if (it != ind_[row].end() && *it == col)
	  ind_[row].erase(it);

      } else {

	if (it == ind_[row].end())
	  ind_[row].push_back(col);
	else if (*it != col)
	  ind_[row].insert(it, col);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets multiple places in a row to a given value.
     */
    template <typename value_type, typename It>
    inline void set(size_type row, It ind, It ind_end, value_type val)
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= row &&*/ row < nRows())
	  << "SparseBinaryMatrix::set: Invalid row index: " << row
	  << " - Should be < number of rows: " << nRows();
      }

      for (; ind != ind_end; ++ind)
	set(row, *ind, val);
    }

    //--------------------------------------------------------------------------------
    /**
     * For each row, set multiple places to a given value.
     */
    template <typename value_type, typename It>
    inline void setForAllRows(It ind, It ind_end, value_type val)
    {
      for (size_type row = 0; row != nRows(); ++row) 
	set(row, ind, ind_end, val);
    }

    //--------------------------------------------------------------------------------
    inline typename Row::const_iterator ind_begin_(const size_type row) const
    {
      return ind_[row].begin();
    }

    //--------------------------------------------------------------------------------
    inline typename Row::const_iterator ind_end_(const size_type row) const
    {
      return ind_[row].end();
    }

    //--------------------------------------------------------------------------------
    inline const Row& getSparseRow(size_type row) const
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= row &&*/ row < nRows())
	  << "SparseBinaryMatrix::getSparseRow: Invalid row index: " << row
	  << " - Should be < number of rows: " << nRows();
      } // End pre-conditions

      return ind_[row];
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline void appendSparseRow(InputIterator begin, InputIterator end)
    {
      { // Pre-conditions
	sparse_row_invariants_(begin, end, "appendSparseRow");
      } // End pre-conditions

      ind_.resize(nRows()+1);
      Row& row = ind_[ind_.size()-1];
      row.insert(row.end(), begin, end);
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline void appendDenseRow(InputIterator begin, InputIterator end)
    {
      { // Pre-conditions
	NTA_ASSERT((size_type)(end - begin) == nCols())
	  << "SparseBinaryMatrix::appendDenseRow: "
	  << "Invalid vector size: " << (size_type)(end - begin)
	  << " - Should be equal to number of columns: " << nCols();
      } // End pre-conditions
      
      ind_.resize(nRows()+1);
      Row& row = ind_[ind_.size()-1];
      for (nz_index_type j = 0; j != nCols(); ++j, ++begin)
	if (!nta::nearlyZero(*begin))
	  row.push_back(j);
    }

    //--------------------------------------------------------------------------------
    inline void appendEmptyCols(size_type n)
    {
      ncols_ += n;
      buffer_.resize(ncols_);
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline void appendSparseCol(InputIterator ind, InputIterator ind_end)
    {
      { // Pre-conditions
	NTA_ASSERT((size_type)(ind_end - ind) <= nRows())
	  << "SparseBinaryMatrix::appendSparseCol: "
	  << "Invalid vector size: " << (size_type)(ind_end - ind)
	  << " - Should be less than number of rows: " << nRows();
      } // End pre-conditions

      for (; ind != ind_end; ++ind) 
        ind_[*ind].push_back(ncols_);
      
      ++ ncols_;
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline void 
    replaceSparseRow(size_type row, InputIterator begin, InputIterator end)
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= row &&*/ row < nRows())
	  << "SparseBinaryMatrix::replaceSparseRow: Invalid row index: " << row
	  << " - Should be < number of rows: " << nRows();
      
	sparse_row_invariants_(begin, end, "replaceSparseRow");
      } // End pre-conditions

      size_type n = (size_type)(end - begin);
      ind_[row].resize(n);

      for (nz_index_type i = 0; i != n; ++i)
	ind_[row][i] = *begin++;
   }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline size_type 
    findRowSparse(InputIterator begin, InputIterator end) const
    {
      { // Pre-conditions
	sparse_row_invariants_(begin, end, "findRowSparse");
      } // End pre-conditions

      size_type nnzr = (size_type)(end - begin);

      for (size_type row = 0; row != nRows(); ++row) {
	if (nNonZerosOnRow(row) != nnzr)
	  continue;
	if (std::equal(begin, end, ind_[row].begin()))
	  return row;
      }

      return nRows();
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline size_type 
    findRowDense(InputIterator begin, InputIterator end) const
    {
      { // Pre-conditions
	NTA_ASSERT((size_type)(end - begin) == nCols())
	  << "SparseBinaryMatrix::findRowDense: "
	  << "Invalid vector size: " << (size_type)(end - begin);
      } // End pre-conditions

      Row& buffer = const_cast<Row&>(buffer_);
      size_type k = 0;
      for (nz_index_type j = 0; j != nCols(); ++j)
	if (!nta::nearlyZero(*(begin + j)))
	  buffer[k++] = j;

      return findRowSparse(buffer_.begin(), buffer_.begin() + k);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the index and Hamming distance of the closest row in this matrix.
     */
    template <typename InputIterator>
    inline std::pair<size_type, size_type> 
    minHammingDistance(InputIterator begin, InputIterator end) const
    {
      { // Pre-conditions
	sparse_row_invariants_(begin, end, "minHammingDistance");
      } // End pre-conditions
      
      size_type min_row = 0;
      size_type min_d = std::numeric_limits<size_type>::max();
      
      for (size_type row = 0; row != nRows(); ++row) {

	size_type d = 0;
	InputIterator it = begin;
	typename Row::const_iterator begin1 = ind_[row].begin();
	typename Row::const_iterator end1 = ind_[row].end();
	
	while (begin1 != end1 && it != end && d < min_d) {
	  if (*begin1 < *it) {
	    ++d;
	    ++begin1;
	  } else if (*it < *begin1) {
	    ++d;
	    ++it;
	  } else {
	    ++begin1;
	    ++it;
	  }
	}

	if (min_d <= d) 
	  continue;

	d += (size_type)(end1 - begin1);
	d += (size_type)(end - it);

	if (d < min_d) {
	  min_row = row;
	  min_d = d;
	}
      }
      
      return std::make_pair(min_row, min_d);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns index of first row whose Hamming distance to vector is less
     * than value.
     */
    template <typename InputIterator>
    inline size_type
    firstRowCloserThan(InputIterator begin, InputIterator end, size_type distance) const
    {
      { // Pre-conditions
	sparse_row_invariants_(begin, end, "firstRowCloserThan");
      } // End pre-conditions
      
      for (size_type row = 0; row != nRows(); ++row) {

	size_type d = 0;
	InputIterator it = begin;
	typename Row::const_iterator begin1 = ind_[row].begin();
	typename Row::const_iterator end1 = ind_[row].end();
	
	while (begin1 != end1 && it != end && d < distance) {
	  if (*begin1 < *it) {
	    ++d;
	    ++begin1;
	  } else if (*it < *begin1) {
	    ++d;
	    ++it;
	  } else {
	    ++begin1;
	    ++it;
	  }
	}

	if (distance <= d)
	  continue;

	d += (size_type)(end1 - begin1);
	d += (size_type)(end - it);

	if (d < distance) 
	  return row;
      }
      
      return nRows();
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline size_type
    firstRowCloserThan_dense(InputIterator begin, InputIterator end, 
			     size_type distance) const
    {
      size_type nnzr = 0;
      nz_index_type n = (nz_index_type)(end - begin);
      for (nz_index_type i = 0; i != n; ++i)
	if (begin[i] > 0)
	  (const_cast<SparseBinaryMatrix&>(*this)).buffer_[nnzr++] = i;

      return firstRowCloserThan(buffer_.begin(), buffer_.begin() + nnzr, distance);
    }

    //--------------------------------------------------------------------------------
    inline void setRangeToZero(size_type row, size_type begin, size_type end)
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= row &&*/ row < nRows())
	  << "SparseBinaryMatrix::setRange: "
	  << "Invalid row: " << row;
	NTA_ASSERT(/*0 <= begin &&*/ begin <= end && end <= nCols())
	  << "SparseBinaryMatrix::setRange: "
	  << "Invalid range: " << begin << ":" << end;
      } // End pre-conditions

      Row& the_row = ind_[row];
      typename Row::iterator it1, it2;
      it1 = std::lower_bound(the_row.begin(), the_row.end(), begin);
      it2 = std::lower_bound(it1, the_row.end(), end);
      the_row.erase(it1, it2);
    }

    //--------------------------------------------------------------------------------
    inline void setRangeToOne(size_type row, size_type begin, size_type end)
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= row &&*/ row < nRows())
	  << "SparseBinaryMatrix::setRange: "
	  << "Invalid row: " << row;
	NTA_ASSERT(/*0 <= begin &&*/ begin <= end && end <= nCols())
	  << "SparseBinaryMatrix::setRange: "
	  << "Invalid range: " << begin << ":" << end;
       } // End pre-conditions
       
       rowToDense(row, buffer_.begin(), buffer_.end());
       for (nz_index_type j = begin; j != end; ++j)
	 buffer_[j] = (size_type) 1;
       rowFromDense(row, buffer_.begin(), buffer_.end());
    }

    //--------------------------------------------------------------------------------
    inline void transpose()
    {
      std::vector<Row> tind(nCols());

      for (size_type row = 0; row != nRows(); ++row) 
	for (nz_index_type k = 0; k != ind_[row].size(); ++k)
	  tind[ind_[row][k]].push_back(row);
    
      ncols_ = nRows();
      ind_.swap(tind);
    }

    //--------------------------------------------------------------------------------
    inline void logicalNot()
    {
      for (size_type row = 0; row != nRows(); ++row) {

	size_type nnzr = ind_[row].size();
	Row new_row;
	new_row.reserve(nCols() - nnzr);

	nz_index_type k1 = 0;

	for (nz_index_type k = 0; k < nnzr; ++k1) 
	  if (k1 != ind_[row][k])
	    new_row.push_back(k1);
	  else 
	    ++k;
	
	for (; k1 != nCols(); ++k1) 
	  new_row.push_back(k1);

	ind_[row].swap(new_row);
      }
    }

    //--------------------------------------------------------------------------------
    inline void logicalOr(const SparseBinaryMatrix& o)
    {     
      { // Pre-conditions
	NTA_ASSERT(o.nRows() == nRows())
	  << "SparseBinaryMatrix::logicalOr: "
	  << "Mismatch in number of rows: " << nRows()
	  << " and: " << o.nRows();

	NTA_ASSERT(o.nCols() == nCols())
	  << "SparseBinaryMatrix::logicalOr: "
	  << "Mismatch in number of cols: " << nCols()
	  << " and: " << o.nCols();
      } // End pre-conditions

      for (size_type row = 0; row != nRows(); ++row) {

	size_type k = sparseOr(nCols(), ind_[row], o.ind_[row], buffer_);
	replaceSparseRow(row, buffer_.begin(), buffer_.begin() + k);
      }
    }

    //--------------------------------------------------------------------------------
    inline void logicalAnd(const SparseBinaryMatrix& o)
    {     
      { // Pre-conditions
	NTA_ASSERT(o.nRows() == nRows())
	  << "SparseBinaryMatrix::logicalAnd: "
	  << "Mismatch in number of rows: " << nRows()
	  << " and: " << o.nRows();

	NTA_ASSERT(o.nCols() == nCols())
	  << "SparseBinaryMatrix::logicalAnd: "
	  << "Mismatch in number of cols: " << nCols()
	  << " and: " << o.nCols();
      } // End pre-conditions

      for (size_type row = 0; row != nRows(); ++row) {

	size_type k = sparseAnd(nCols(), ind_[row], o.ind_[row], ind_[row]);
	ind_[row].resize(k);
	//replaceSparseRow(row, buffer_.begin(), buffer_.begin() + k);
      }
    }

    //--------------------------------------------------------------------------------
    inline void inside()
    {
      size_type nrows = nRows();
      nz_index_type ncols = nCols();
      std::vector<size_type> filled(nrows * ncols, 0);
      typename std::vector<size_type>::iterator it, it_end;

      for (size_type r = 0; r != nrows; ++r) {
	it = filled.begin() + r * ncols;
	it_end = it + ncols;
	fillLine_(r, it, it_end, false);
	fillLine_(r, it, it_end, true);
      }

      std::vector<size_type> filled2(nrows * ncols, 0);
      transpose();

      for (nz_index_type r = 0; r != ncols; ++r) {
	it = filled2.begin() + r * nrows;
	it_end = it + nrows;
	fillLine_(r, it, it_end, false);
	fillLine_(r, it, it_end, true);
      }

      for (size_type r = 0; r != nrows; ++r) {
	for (nz_index_type c = 0; c != ncols; ++c) {
	  if (filled[r*ncols + c] + filled2[c*nrows + r] > 2)
	    filled[r*ncols + c] = (size_type) 1;
	  else
	    filled[r*ncols + c] = (size_type) 0;
	}
      }
      
      fromDense(nrows, ncols, filled.begin(), filled.end());
    }

    //--------------------------------------------------------------------------------
    inline void edges(size_type insideBorder =1)
    {
      size_type nrows = nRows();
      nz_index_type ncols = nCols();

      SparseBinaryMatrix b(*this);
      b.inside();
      b.logicalOr(*this);

      std::vector<size_type> edges(nrows * ncols, 0);
      std::vector<size_type> buffer(nrows * ncols);
      b.toDense(buffer.begin(), buffer.end());

      for (size_type i = 0; i != insideBorder; ++i) {

	std::vector<size_type> new_edges(nrows * ncols, 0);

	for (size_type r = 0; r != nrows; ++r) 
	  for (nz_index_type c = 0; c != ncols; ++c)
	    if (buffer[r*ncols + c] == 1
		&& (c == 0 || c == ncols - 1 
		    || buffer[r*ncols + c-1] == 0 || buffer[r*ncols + c+1] == 0))
	      new_edges[r*ncols + c] = 1;

	for (nz_index_type c = 0; c != ncols; ++c)
	  for (size_type r = 0; r != nrows; ++r) 
	    if (buffer[r*ncols + c] == 1
		&& (r == 0 || r == nrows - 1 
		    || buffer[(r-1)*ncols + c] == 0 || buffer[(r+1) * ncols + c] == 0))
	      new_edges[r*ncols + c] = 1;

	add(edges, new_edges);
	subtract(buffer, new_edges);
      }

      fromDense(nrows, ncols, edges.begin(), edges.end());
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the number of bits that match between dense vector x and each
     * row of this sparse binary matrix. Returns a vector with an integer count
     * (the number of bits that match) for each row. Vector x is a binary vector
     * whose elements take the value 0 or 1 only.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void 
    overlap(InputIterator x, InputIterator x_end, 
            OutputIterator y, OutputIterator y_end) const
    {
      {
        NTA_ASSERT((size_type)(x_end - x) == nCols());
        NTA_ASSERT((size_type)(y_end - y) == nRows());
      }

      typename Row::const_iterator it, end;

      for (size_type i = 0; i != nRows(); ++i, ++y) {
        size_type count = 0;
        end = ind_[i].end();
        for (it = ind_[i].begin(); it != end; ++it)
          count += x[*it];
        *y = count;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * For a given x vector (binary 0/1) and maxDistance, computes the overlap 
     * between x and each row of this matrix, and decides whether this overlap 
     * is acceptable or not.
     * As soon as a non-acceptable (too big) overlap has been determined, false 
     * is returned.
     * The max allowed overlap changes from row to row and is computed as:
     * (1 - maxDistance) * max(n non-zeros on row, sum of x),
     * where the sum of x is the number of non-zero elements in x (x is binary
     * with values only 0 and 1 for any element).
     */
    template <typename InputIterator>
    inline bool 
    maxAllowedOverlap(nta::Real32 maxDistance, InputIterator x, InputIterator x_end) const
    {
       {
         NTA_ASSERT((size_type)(x_end - x) == nCols());
       }

       nta::Real32 k = 1.0 - maxDistance;

       // Compute the number of 1's in x, same as the sum of x
       size_type c_sum = 0;
       for (InputIterator x_it = x; x_it != x_end; ++x_it)
         c_sum += *x_it;

       typename Row::const_iterator it, end;
       
       for (size_type i = 0; i != nRows(); ++i) {

         // Compute max allowed overlap
         size_type ls = std::max(nNonZerosOnRow(i), c_sum);
         nta::Real32 max_ov = k * ls;
         
         // Compute overlap between row i and vector x,
         // but exit early, as soon as we determine that 
         // the overlap is more than the max allowed overlap
         size_type ov = 0;
         end = ind_[i].end();
         for (it = ind_[i].begin(); it != end; ++it) {
           ov += x[*it];
           if (ov > max_ov) 
             return false;
         }         
       }
       
       return true;
    }

    //--------------------------------------------------------------------------------
    inline size_type CSRSize() const
    {
      std::stringstream b;
      char buffer[32];

      b << getVersion() << " "
	<< nRows() << " " 
	<< nCols() << " ";

      size_type n = b.str().size();

      for (size_type row = 0; row != nRows(); ++row) {
	size_type nnzr = nNonZerosOnRow(row);
	n += sprintf(buffer, "%d ", nnzr);
	for (nz_index_type j = 0; j != nnzr; ++j)
	  n += sprintf(buffer, "%d ", ind_[row][j]);
      }

      return n;
    }

    //--------------------------------------------------------------------------------
    inline void fromCSR(std::istream& inStream)
    {
      const std::string where = "SparseBinaryMatrix::readState: ";

      { // Pre-conditions
	NTA_CHECK(inStream.good())
	  << where << "Bad stream";
      } // End pre-conditions

      std::string tag;
      inStream >> tag;

      if (tag == getVersion()) {
      
        size_type nrows = 0;
        inStream >> nrows;

        ind_.clear();
        ind_.resize(nrows);

        size_type ncols = 0;
        inStream >> ncols;
        nCols(ncols);
      
        buffer_.resize(nCols());
    
        for (size_type row = 0; row != nrows; ++row) {
          inStream >> ind_[row];
          for (nz_index_type k = 0; k < ind_[row].size(); ++k) {
            NTA_CHECK(/*0 <= ind_[row][k] &&*/ ind_[row][k] < nCols())
              << where << "Invalid value: " << ind_[row][k]
              << " for prototype # " << row;
            if (k > 0)
            {
              NTA_CHECK(ind_[row][k-1] < ind_[row][k])
                << where << "Index values need to be "
                << "in strictly increasing order (no duplicates)";
            }
          }
        }

      } else if (tag == "sm_csr_1.5") {
        
        size_type total_n_bytes = 0;
        inStream >> total_n_bytes;

        size_type nrows = 0;
        inStream >> nrows;
      
        ind_.clear();
        ind_.resize(nrows);

        size_type ncols = 0;
        inStream >> ncols;
        nCols(ncols);
      
        buffer_.resize(nCols());

        size_type nnz = 0;
        inStream >> nnz;
    
        for (size_type row = 0; row != nrows; ++row) {
          size_type nnzr = 0;
          inStream >> nnzr;
          ind_[row].resize(nnzr);
          for (size_type k = 0; k != nnzr; ++k) {
            size_type col = 0;
            double value;
            inStream >> col >> value;
            ind_[row][k] = col;
          }
            
          for (nz_index_type k = 0; k < ind_[row].size(); ++k) {
            NTA_CHECK(/*0 <= ind_[row][k] &&*/ ind_[row][k] < nCols())
              << where << "Invalid value: " << ind_[row][k]
              << " for prototype # " << row;
            if (k > 0){
              NTA_CHECK(ind_[row][k-1] < ind_[row][k])
                << where << "Index values need to be "
                << "in strictly increasing order (no duplicates)";
            }
          }
        }
      } else {
        std::cout << "Unknown format for sparse binary matrix: " 
                  << tag << std::endl;
        exit(-1);
      }
    }

    //--------------------------------------------------------------------------------
    inline void toCSR(std::ostream& outStream) const
    {
      { // Pre-conditions
	NTA_CHECK(outStream.good())
	  << "SparseBinaryMatrix::toCSR: Bad stream";
      } // End pre-conditions

      outStream << getVersion() << " "
		<< nRows() << " " 
		<< nCols() << " ";

      for (size_type row = 0; row != nRows(); ++row) 
	outStream << ind_[row];
    }

    /* KEEP - KEEP - KEEP - KEEP - KEEP - KEEP - KEEP - KEEP - KEEP - KEEP - KEEP
     *
     * DOESN'T WORK ON WIN32, BUT FINE ON DARWIN86 AND LINUX64
     *
    //--------------------------------------------------------------------------------
    inline size_type binarySize() const
    {
      Log10<float> log10_f;

      std::stringstream b;
      b << getVersion(true) << " "
	<< nRows() << " "
	<< nCols() << " ";

      size_type n = b.str().size();

      for (size_type row = 0; row != nRows(); ++row) {
	size_type nnzr = nNonZerosOnRow(row);
	n += (size_type) log10_f((float)nnzr) + 2 + nnzr * sizeof(size_type);
      }

      return n;
    }
    */

    //--------------------------------------------------------------------------------
    inline void fromBinary(std::istream& inStream)
    {
      const std::string where = "SparseBinaryMatrix::fromBinary: ";
  
      { // Pre-conditions
	NTA_CHECK(inStream.good())
	  << where << "Bad stream";
      } // End pre-conditions
      
      std::string version;
      inStream >> version;
      NTA_CHECK(version == getVersion(true))
	<< where << "Unknown format: " << version;
      
      size_type nrows = 0;
      inStream >> nrows;

      //NTA_CHECK(0 <= nrows)
      //<< where << "Invalid number of rows: " << nrows;
      
      ind_.clear();
      ind_.resize(nrows);

      size_type ncols = 0;
      inStream >> ncols;
      nCols(ncols);
      
      buffer_.resize(nCols());

      for (size_type row = 0; row != nRows(); ++row) {
	size_type n = 0;
	inStream >> n;
	//NTA_CHECK(0 <= n)
	// << where << "Invalid row size: " << n;
	ind_[row].resize(n);
	inStream.ignore(1);
	nta::binary_load(inStream, ind_[row].begin(), ind_[row].end());
      }
    }

    //--------------------------------------------------------------------------------
    inline void toBinary(std::ostream& outStream) const
    {
      { // Pre-conditions
	NTA_CHECK(outStream.good())
	  << "SparseBinaryMatrix::toBinary: Bad stream";
      } // End pre-conditions

      outStream << getVersion(true) << " "
		<< nRows() << " "
		<< nCols() << " ";

      for (size_type row = 0; row != nRows(); ++row) {
	outStream << ind_[row].size() << " ";
	nta::binary_save(outStream, ind_[row].begin(), ind_[row].end());
      }
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline void 
    fromSparseVector(size_type nrows, size_type ncols, 
		     InputIterator begin, InputIterator end,
		     size_type offset =0)
    {
      { // Pre-conditions
	/*
	NTA_ASSERT(0 <= nrows)
	  << "SparseBinaryMatrix::fromSparseVector: "
	  << "Invalid number of rows: " << nrows;

	NTA_ASSERT(0 <= ncols)
	  << "SparseBinaryMatrix::fromSparseVector: "
	  << "Invalid number of columns: " << ncols;
	*/

	NTA_ASSERT((size_type)(end - begin) <= nrows * ncols)
	  << "SparseBinaryMatrix::fromSparseVector: "
	  << "Invalid number of non-zero indices: "
	  << (size_type)(end - begin)
	  << "when nrows is: " << nrows << "ncols is: " << ncols;

	for (InputIterator it = begin; it != end; ++it) 
	  NTA_ASSERT(*it <= nrows * ncols)
	    << "SparseBinaryMatrix::fromSparseVector: "
	    << "Invalid index: " << *it
	    <<  " in sparse vector - Should be < " << nrows * ncols;
      
	for (size_type i = 1; i < (size_type)(end - begin); ++i)
	  NTA_ASSERT(*(begin + i - 1) < *(begin + i))
	    << "SparseBinaryMatrix::fromSparseVector: "
	    << "Indices need to be in strictly increasing order";
      } // End pre-conditions

      nCols(ncols);
      ind_.clear();
      ind_.resize(nrows);
      buffer_.resize(nCols());

      for (; begin != end; ++begin) {
	size_type idx = *begin - offset;
	size_type row = idx / ncols;
	size_type col = idx % ncols;
	ind_[row].push_back(col);
      }
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    inline size_type
    toSparseVector(OutputIterator begin, OutputIterator end,
		   size_type offset =0) const
    {
      { // Pre-conditions
	NTA_ASSERT(nNonZeros() <= (size_type)(end - begin))
	  << "SparseBinaryMatrix::toSparseVector: "
	  << "Not enough memory";
      } // End pre-conditions

      OutputIterator begin1 = begin;

      for (size_type row = 0; row != nRows(); ++row) 
	for (nz_index_type k = 0; k != nNonZerosOnRow(row); ++k)
	  *begin++ = row * nCols() + ind_[row][k] + offset;

      return (size_type)(begin - begin1);
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline void 
    rowFromDense(size_type row, InputIterator begin, InputIterator end)
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= row &&*/ row < nRows())
	  << "SparseBinaryMatrix::rowFromDense: "
	  << "Invalid row index: " << row;
	NTA_ASSERT((size_type)(end - begin) == nCols())
	  << "SparseBinaryMatrix::rowFromDense: "
	  << "Invalid vector size";
      } // End pre-conditions

      ind_[row].clear();
      for (InputIterator it = begin; it != end; ++it)
	if (!nearlyZero(*it))
	  ind_[row].push_back((size_type)(it - begin));
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    inline void
    rowToDense(size_type row, OutputIterator begin, OutputIterator end) const
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= row &&*/ row < nRows())
	  << "SparseBinaryMatrix::rowToDense: "
	  << "Invalid row index: " << row;

	NTA_ASSERT((size_type)(end - begin) == nCols())
	  << "SparseBinaryMatrix::rowToDense: "
	  << "Not enough memory";
      } // End pre-conditions

      typedef typename std::iterator_traits<OutputIterator>::value_type value_type;

      std::fill(begin, end, (value_type) 0);
      typename Row::const_iterator it;
      for (it = ind_[row].begin(); it != ind_[row].end(); ++it)
	*(begin + *it) = (value_type) 1;
    }
    
    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    inline void 
    getRow(size_type row, OutputIterator begin, OutputIterator end) const
    {
      rowToDense(row, begin, end);
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    inline void 
    getColToDense(size_type col, OutputIterator dense, OutputIterator dense_end) const
    {
      {
        NTA_ASSERT(col < nCols());
        NTA_ASSERT((size_type)(dense_end - dense) == nRows());
      }

      for (size_type i = 0; i != nRows(); ++i, ++dense) {
        typename Row::const_iterator where;
        where = std::lower_bound(ind_[i].begin(), ind_[i].end(), col);
        *dense = (where != ind_[i].end() && *where == col);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Set a slice at dst_first_row, dst_first_col, whose shape and contents
     * are src.
     */
    template <typename Other>
    inline void 
    setSlice(size_type dst_first_row, size_type dst_first_col, const Other& src)
    {
      { // Pre-conditions
        // Not checking number of rows and columns of other,
        // because Other might not have rows and columns,
        // or might create them dynamically when set is invoked
        //other.assert_valid_domain_(dst, "get"); //not always on Other!
      } // End pre-conditions

      for (size_type row = 0; row != (size_type) src.nRows(); ++row) {
	for (size_type col = 0; col != (size_type) src.nCols(); ++col) {
	  set(row + dst_first_row, col + dst_first_col, src.get(row,col));
	}
      }
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline void 
    fromDense(size_type nrows, size_type ncols, 
	      InputIterator begin, InputIterator end)
    {
      { // Pre-conditions
	/*
	NTA_ASSERT(0 <= nrows)
	  << "SparseBinaryMatrix::fromDense: "
	  << "Invalid number of rows: " << nrows;

	NTA_ASSERT(0 <= ncols)
	  << "SparseBinaryMatrix::fromDense: "
	  << "Invalid number of columns: " << ncols;
	*/

	NTA_ASSERT(ncols < std::numeric_limits<size_type>::max())
	  << "SparseBinaryMatrix: Too many columns: " << ncols;

	NTA_ASSERT(nrows * ncols <= (size_type)(end - begin))
	  << "SparseBinaryMatrix::fromDense: "
	  << "Invalid number of rows and columns: "
	  << nrows << " and: " << ncols
	  << " when storage has size: " 
	  << (size_type)(end - begin);
      } // End pre-conditions

      clear();

      nCols(ncols);
      ind_.resize(nrows);
      buffer_.resize(nCols());

      for (size_type row = 0; row != nrows; ++row) 
	for (nz_index_type col = 0; col != nCols(); ++col) 
	  if (*begin++ != 0) 
	    ind_[row].push_back(col);
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    inline void 
    toDense(OutputIterator begin, OutputIterator end) const
    {
      { // Pre-conditions
	NTA_ASSERT(nRows() * nCols() <= (size_type)(end - begin))
	  << "SparseBinaryMatrix::toDense: "
	  << "Not enough memory: " << (size_type)(end - begin)
	  << " - Should be at least: " << nRows()* nCols();
      } // End pre-conditions

      std::fill(begin, end, (size_type) 0);
      for (size_type row = 0; row != nRows(); ++row) {
	OutputIterator p = begin + row * nCols();
	for (nz_index_type k = 0; k != ind_[row].size(); ++k)
	  *(p + ind_[row][k]) = (size_type) 1;
      }
    }

    //--------------------------------------------------------------------------------
    inline void print(std::ostream& outStream) const
    {
      { // Pre-conditions
	NTA_CHECK(outStream.good())
	  << "SparseBinaryMatrix::print: Bad stream";
      } // End pre-conditions

      Row buffer(nCols());

      for (size_type row = 0; row != nRows(); ++row) {
	std::fill(buffer.begin(), buffer.end(), (size_type) 0);
	for (nz_index_type k = 0; k != ind_[row].size(); ++k) 
	  buffer[ind_[row][k]] = (size_type) 1;
	for (nz_index_type col = 0; col != nCols(); ++col)
	  outStream << buffer[col] << " ";
	outStream << std::endl;
      }
    }

    //--------------------------------------------------------------------------------
    inline bool equals(const SparseBinaryMatrix& o) const
    {
      if (o.nRows() != nRows() || o.nCols() != nCols())
	return false;
      for (size_type row = 0; row != nRows(); ++row) {
	if (o.nNonZerosOnRow(row) != nNonZerosOnRow(row))
	  return false;
	if (!std::equal(ind_[row].begin(), ind_[row].end(), o.ind_[row].begin()))
	  return false;
      }
      return true;
    }

    //--------------------------------------------------------------------------------
    /**
     * Matrix vector multiplication, optimized because we know that the values
     * of all the non-zeros are 1: there is no need to do multiplications.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void rightVecSumAtNZ(InputIterator x, InputIterator x_end,
				OutputIterator y, OutputIterator y_end) const
    {
      { // Pre-conditions
	NTA_ASSERT((size_type)(x_end - x) >= nCols())
	  << "SparseBinaryMatrix::rightVecSumAtNZ: "
	  << " Invalid input vector size: " << (size_type)(x_end - x)
	  << " - Should >= number of colums: " << nCols();

	NTA_ASSERT((size_type)(y_end - y) >= nRows())
	  << "SparseBinaryMatrix::rightVecSumAtNZ: "
	  << "Invalid output vector size: " << (size_type)(y_end - y)
	  << " - Should >= number of rows: " << nRows();
      } // End pre-conditions

      typedef typename std::iterator_traits<OutputIterator>::value_type value_type;
      typename std::vector<Row>::const_iterator row;
      typename Row::const_iterator j;

      for (row = ind_.begin(); row != ind_.end(); ++row, ++y) { 
	value_type val = 0;
	for (j = row->begin(); j != row->end(); ++j)
	  val += value_type(x[*j]);
	*y = val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Matrix vector multiplication, optimized because we know that the values
     * of all the non-zeros are 1: there is no need to do multiplications.
     */
    template <typename InputIterator, typename T1, typename T2>
    inline void 
    rightVecSumAtNZ(InputIterator x, InputIterator x_end, SparseVector<T1,T2>& y) const
    {
      { // Pre-conditions
	NTA_ASSERT((size_type)(x_end - x) >= nCols())
	  << "SparseBinaryMatrix::rightVecSumAtNZ: "
	  << " Invalid input vector size: " << (size_type)(x_end - x)
	  << " - Should >= number of colums: " << nCols();
      } // End pre-conditions

      typedef T2 value_type;
      size_type k = 0;

      for (size_type i = 0; i != nRows(); ++i) {
        const Row& row = ind_[i];
        const size_type nnzr = row.size();
        value_type s = 0;
        for (size_type j = 0; j != nnzr; ++j)
          s += (value_type) x[row[j]];
        if (s != 0)
          y[k++] = std::make_pair(i, s);
      }

      y.nnz = k;
    }

    //--------------------------------------------------------------------------------
    /**
     * Matrix vector multiplication, optimized because we know that the values
     * of all the non-zeros are 1: there is no need to do multiplications.
     */
    template <typename T, typename T1, typename T2>
    inline void 
    rightVecSumAtNZ(const Buffer<T>& x, SparseVector<T1,T2>& y) const
    {
      typedef T2 value_type;
      size_type k = 0;

      for (size_type i = 0; i != nRows(); ++i) {
        value_type s = (value_type) dot(ind_[i], x);
        if (s != 0)
          y[k++] = std::make_pair(i, s);
      }

      y.nnz = k;
    }

    //--------------------------------------------------------------------------------
    /**
     * Matrix vector multiplication on the left side, optimized because we know that 
     * the values of all the non-zeros are 1: there is no need to do multiplications.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void leftVecSumAtNZ(InputIterator x, InputIterator x_end,
			       OutputIterator y, OutputIterator y_end) const
    {
      { // Pre-conditions
	NTA_ASSERT((size_type)(x_end - x) >= nRows())
	  << "SparseBinaryMatrix::leftVecSumAtNZ: "
	  << " Invalid input vector size: " << (size_type)(x_end - x)
	  << " - Should be  >= number of rows: " << nRows();

	NTA_ASSERT((size_type)(y_end - y) >= nCols())
	  << "SparseBinaryMatrix::leftVecSumAtNZ: "
	  << "Invalid output vector size: " << (size_type)(y_end - y)
	  << " - Should be >= number of columns: " << nCols();
      } // End pre-conditions

      typedef typename std::iterator_traits<OutputIterator>::value_type value_type;
      typename std::vector<Row>::const_iterator row;
      typename Row::const_iterator j;

      std::fill(y, y_end, (value_type) 0.0);

      for (row = ind_.begin(); row != ind_.end(); ++row, ++x) {
	value_type val(*x);
	for (j = row->begin(); j != row->end(); ++j)
	  y[*j] += val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the max of the values of x corresponding to non-zeros, for each row.
     * The operation is:
     *
     *  for row in [0,nrows):
     *   y[row] = max(x[col], for col in [0,ncols) s.t. this[row,col] != 0)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] output vector (size = number of rows)
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void rightVecMaxAtNZ(InputIterator x, OutputIterator y) const
    {
      typedef typename std::iterator_traits<OutputIterator>::value_type value_type;
      
      for (size_type row = 0; row != nRows(); ++row) {
        value_type max_val = - std::numeric_limits<value_type>::max();
	const Row& the_row = ind_[row];
	for (size_type k = 0; k != the_row.size(); ++k) {
          if (x[the_row[k]] > max_val)
            max_val = x[the_row[k]];
        }
        *y++ = max_val != - std::numeric_limits<value_type>::max() ? max_val : (value_type) 0;
      }
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator, typename OutputIterator>
    inline void vecMaxProd(InputIterator x, InputIterator x_end,
			   OutputIterator y, OutputIterator y_end) const
    {
      { // Pre-conditions
	NTA_ASSERT((size_type)(x_end - x) >= nCols())
	  << "SparseBinaryMatrix::vecMaxProd: "
	  << " Invalid input vector size: " << (size_type)(x_end - x)
	  << " - Should >= number of columns: " << nRows();

	NTA_ASSERT((size_type)(y_end - y) >= nRows())
	  << "SparseBinaryMatrix::vecMaxProd: "
	  << "Invalid output vector size: " << (size_type)(y_end - y)
	  << " - Should >= number of rows: " << nCols();
      } // End pre-conditions

      rightVecMaxAtNZ(x, y);
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the arg max of the values of x corresponding to non-zeros, for each row.
     * The operation is:
     *
     *  for row in [0,nrows):
     *   y[row] = argmax(x[col], for col in [0,ncols) s.t. this[row,col] != 0)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] output vector (size = number of rows)
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void rightVecArgMaxAtNZ(InputIterator x, OutputIterator y) const
    {
      typedef typename std::iterator_traits<OutputIterator>::value_type value_type;
      
      for (size_type row = 0; row != nRows(); ++row) {
        value_type max_val = - std::numeric_limits<value_type>::max();
        size_type max_ind = 0;
	const Row& the_row = ind_[row];
	for (size_type k = 0; k != the_row.size(); ++k) {
          value_type val = x[the_row[k]];
          if (val > max_val) {
            max_val = val;
            max_ind = the_row[k];
          }
        }
        *y++ = (value_type) max_ind; 
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the max of the values of x corresponding to non-zeros, for each column.
     * The operation is:
     *
     *  for col in [0,ncols):
     *   y[col] = max(x[row], for row in [0,nrows) s.t. this[row,col] != 0)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of rows)
     * @param y [OutputIterator<value_type>] output vector (size = number of columns)
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void leftVecMaxAtNZ(InputIterator x, OutputIterator y) const
    {
      typedef typename std::iterator_traits<OutputIterator>::value_type value_type;

      std::fill(y, y + nCols(), (value_type) - std::numeric_limits<value_type>::max());

      for (size_type row = 0; row != nRows(); ++row) {
	const Row& the_row = ind_[row];
	for (size_type k = 0; k != the_row.size(); ++k) {
          if (x[row] > y[the_row[k]])
            y[the_row[k]] = x[row];
        }
      }

      for (size_type i = 0; i != nCols(); ++i)
        if (y[i] == (value_type) - std::numeric_limits<value_type>::max())
	  y[i] = 0;
    }

  private:
    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline void sparse_row_invariants_(InputIterator begin, InputIterator end,
				       const char* where) const
    {
      NTA_ASSERT(0 <= end - begin)
	<< "SparseBinaryMatrix::" << where << ": "
	<< "Mismatched iterators";

      NTA_ASSERT((size_type)(end - begin) <= nCols())
	<< "SparseBinaryMatrix::" << where << ": "
	<< "Invalid sparse vector size: " << (size_type)(end - begin)
	<< " - Should be less than number of columns: " << nCols();
    
      for (InputIterator it = begin; it != end; ++it) 
	NTA_ASSERT(/*0 <= *it &&*/ *it <= nCols())
	  << "SparseBinaryMatrix::" << where << ": "
	  << "Invalid index: " << *it
	  << " - Should be >= 0 and < number of columns:" << nCols();
      
      for (size_type i = 1; i < (size_type)(end - begin); ++i)
	NTA_ASSERT(*(begin + i - 1) < *(begin + i))
	  << "SparseBinaryMatrix::" << where << ": "
	  << "Invalid indices: " << *(begin + i - 1)
	  << " and: " << *(begin + i)
	  << " - Indices need to be in strictly increasing order";
    }

    //--------------------------------------------------------------------------------
    inline void nCols(size_type ncols)
    {
      { // Pre-conditions
	/*
	NTA_CHECK(0 < ncols)
	  << "SparseBinaryMatrix::nCols: "
	  << "Invalid number of columns: " << ncols
	  << " - Should be > 0";
	*/
	
	NTA_CHECK(ncols < std::numeric_limits<nz_index_type>::max())
	  << "SparseBinaryMatrix::nCols: "
	  << "Invalid number of columns: " << ncols
	  << " - Should be less than " 
	  << std::numeric_limits<nz_index_type>::max();
      } // End pre-conditions
      
      ncols_ = (nz_index_type) ncols;
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    inline void fillLine_(size_type row, OutputIterator out, OutputIterator out_end, 
			  bool reverse =false)
    {
      { // Pre-conditions
	NTA_ASSERT(/*0 <= row &&*/ row < nRows())
	  << "SparseBinaryMatrix::fillLine_: "
	  << "Invalid row index: " << row;

	NTA_ASSERT(nCols() <= (size_type)(out_end - out))
	  << "SparseBinaryMatrix::fillLine_: "
	  << "Insufficient memory for result";
      } // End pre-conditions

      if (reverse) {
	int i = (int) ind_[row].size() - 1;
	while (i-1 >= 0) {
	  if (ind_[row][i] - 1 == ind_[row][i-1])
	    --i;
	  else {
	    int begin = (int)(ind_[row][i] - 1);
	    int end = (int)(ind_[row][i-1]);
	    for (int k = begin; k != end; --k)
	      out[k] += 1;
	    i -= 2;
	  }
	}
      } else {
	size_type i = 0;
	while ((size_type)(i+1) < ind_[row].size()) {
	  if (ind_[row][i] + 1 == ind_[row][i+1])
	    ++i;
	  else {
	    size_type begin = ind_[row][i] + 1;
	    size_type end = ind_[row][i+1];
	    for (size_type k = begin; k != end; ++k)
	      out[k] += 1;
	    i += 2;
	  }
	}
      }
    }

    //--------------------------------------------------------------------------------
  }; // end class SparseBinaryMatrix

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline std::ostream& operator<<(std::ostream& out_stream,
                                  const SparseBinaryMatrix<T1,T2>& x) 
  {
    if (io_control.sparse_io == AS_DENSE) {
      x.print(out_stream);
    } else if (io_control.sparse_io == CSR)
      x.toCSR(out_stream);
    else if (io_control.sparse_io == BINARY)
      x.toBinary(out_stream);
    return out_stream;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline std::istream& operator>>(std::istream& in_stream,
                                  SparseBinaryMatrix<T1,T2>& x) 
  {
    if (io_control.sparse_io == CSR)
      x.fromCSR(in_stream);
    else if (io_control.sparse_io == BINARY)
      x.fromBinary(in_stream);
    return in_stream;
  }

  //--------------------------------------------------------------------------------
}; // end namespace nta

#endif //NTA_SPARSE_BINARY_MATRIX_HPP
