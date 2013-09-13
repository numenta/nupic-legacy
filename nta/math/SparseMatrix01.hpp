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
 * Definition and implementation for SparseMatrix01 class
 */

#ifndef NTA_SPARSE_MATRIX01_HPP
#define NTA_SPARSE_MATRIX01_HPP

//----------------------------------------------------------------------

#include <nta/types/types.hpp>
#include <nta/ntypes/MemParser.hpp>
#include <nta/ntypes/MemStream.hpp>
#include <nta/math/math.hpp>

#include <string.h> // for memset in gcc 4.4
#include <set>
#include <map>

//----------------------------------------------------------------------

// Work around terrible Windows legacy issue - min and max global macros!!!
#ifdef max
#undef max
#endif

namespace nta {

  //--------------------------------------------------------------------------------
  template <typename Int>
  struct RowCompare
  {
    RowCompare(Int rowSize_) 
      : rowSize(rowSize_) 
    {}

    inline bool operator()(Int* row1, Int* row2) const
    {
      for (Int i = 0; i < rowSize; ++i)
        if (row1[i] > row2[i])
          return true;
        else if (row1[i] < row2[i])
          return false;
      return false;
    }

    Int rowSize;
  };

  //--------------------------------------------------------------------------------
  /**
   * @b Responsibility:
   *  A sparse matrix class dedicated to supporting Numenta's algorithms.
   *  This is not a general sparse matrix. It's tuned specifically for 
   *  speed, and to support Numenta's algorithms. 
   *
   * @b Rationale:
   *  It is not a fully general sparse matrix class. Instead, it is intended
   *  to support Numenta's algorithms as efficiently as possible.
   *
   * @b Resource/Ownerships:
   *  This class manages its own memory. 
   * 
   * @b Invariants:
   *
   * @b Notes:
   *  Note 1: SparseMatrix has a limitation to max<unsigned long> columns, or 
   *   rows or non-zeros.
   */
  template <typename Int, typename Float>
  class SparseMatrix01
  {
  public:
    typedef Int size_type;
    typedef Float value_type;

  private:
    /// number of rows >= 0
    size_type nrows_; 

    /// max number of rows allocated >= 8
    size_type nrows_max_; 

    /// number of colums > 0
    size_type ncols_; 

    /// array of number of non-zeros per row 
    size_type* nzr_; 

    /// array of arrays of indices of non-zeros, per row
    size_type** ind_; 

    /// buffer array of indices
    size_type* indb_; 

    /// buffer array of non-zeros
    value_type* nzb_; 

    /// whether this matrix is allocated contiguously or not
    bool compact_; 

    // Number of non-zeros per row, used when working with unique rows.
    // This is used to block the arity of the row comparison functor,
    // for speed. (could be retrieved from the map, that stores an instance
    // of RowCompare that contains this data).
    // This is used as a flag that we are working with unique rows and that
    // counts_ has been initialized properly. If nnzr_ > 0, we are working
    // with unique rows.
    size_type nnzr_;
    
    // Map that contains a pair<row index, count> for each row. 
    // The count is the number of times a row has been seen, when working 
    // with unique rows. 
    typedef std::pair<size_type, size_type> Row_Count;
    typedef std::map<size_type*, Row_Count, RowCompare<size_type> > Counts;
    Counts counts_;

    //--------------------------------------------------------------------------------
    /**
     * We try to limit reallocations of SparseMatrix01 instances
     * by forbidding the copy constructor and assingment operators.
     * We also forbid the default constructor, which would create
     * empty matrices of little use.
     */
    NO_DEFAULTS(SparseMatrix01);

    //--------------------------------------------------------------------------------
    /**
     * Decides whether val is not zero or not, by testing if val is
     * outside closed ball [-nta::Epsilon .. +nta::Epsilon].
     *
     * @param val [value_type] the value to test
     * @retval [bool] whether val is different from zero or not
     */
    inline bool isNotZero_(const value_type& val) const 
    { 
      return !nta::nearlyZero(val);
    }

    //--------------------------------------------------------------------------------
    /**
     * Decides whether val is zero or not, by testing if val is
     * inside open ball (-nta::Epsilon .. +nta::Epsilon).
     *
     * @param val [value_type] the value to test
     * @retval [bool] whether val is zero or not
     */
    inline bool isZero_(const value_type& val) const 
    { 
      return nta::nearlyZero(val);
    }

    //--------------------------------------------------------------------------------
    /**
     * Allocates data structures of the SparseMatrix01.
     * Mutating, allocates memory.
     *
     * @param nrows_max [size_type >= 0] max number of rows to allocate
     * @param ncols [size_type > 0] number of columns for this matrix
     *
     * @b Exceptions:
     *  @li nrows_max < 0 (assert)
     *  @li ncols <= 0 (assert)
     *  @li Not enough memory (error)
     */
    inline void allocate_(const size_type& nrows_max, const size_type& ncols)
    {
      { // Pre-conditions
        NTA_ASSERT(nrows_max >= 0)
          << "SparseMatrix01::allocate_(): "
          << "Invalid nrows_max = " << nrows_max
          << " - Should be >= 0";
        
        NTA_ASSERT(ncols > 0)
          << "SparseMatrix01::allocate_(): "
          << "Invalid ncols = " << ncols
          << " - Should be > 0";
      }
        
      nrows_max_ = std::max<size_type>(8, nrows_max);
      ncols_ = ncols;

      try {
        nzr_ = new size_type[nrows_max_];
        ind_ = new size_type*[nrows_max_];
        indb_ = new size_type[ncols_];
        nzb_ = new value_type[ncols_];

      } catch (std::exception&) {
        
        NTA_THROW << "SparseMatrix01::allocate_(): "
                  << "Could not allocate enough memory:"
                  << " nrows_max = " << nrows_max
                  << " ncols = " << ncols;
      }
      
      memset(nzr_, 0, nrows_max_ * sizeof(size_type));
      memset(ind_, 0, nrows_max_ * sizeof(size_type*));
      memset(indb_, 0, ncols_ * sizeof(size_type));
      memset(nzb_, 0, ncols_ * sizeof(value_type));
    }

    //--------------------------------------------------------------------------------
    /**
     * Deallocates data structures of the SparseMatrix01.
     */
    inline void deallocate_()
    {
      if (!nzr_)
	return;
			
      if (!isCompact()) {
	size_type **ind = ind_, **ind_end = ind_ + nRows();
	while (ind != ind_end) 
          delete [] *ind++;
      } else {
        delete [] ind_[0];
      }

      delete [] ind_;
      ind_ = NULL;
      delete [] nzr_;
      nzr_ = NULL;
      delete [] indb_;
      indb_ = NULL;
      delete [] nzb_;
      nzb_ = NULL;

      nrows_ = ncols_ = nrows_max_ = 0;
    }

    //--------------------------------------------------------------------------------
    inline void swapCountKeys_(size_type* old_ptr, size_type* new_ptr)
    {
      typename Counts::iterator it = counts_.find(old_ptr);
      const Row_Count row_val = it->second;
      counts_.erase(it);
      counts_[new_ptr] = row_val;
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds a row stored in ind.
     * Returns the index of the newly added row.
     * 
     * WARNING: send in values without duplicates, in increasing order of indices
     *
     * ind needs to be a contiguous array of memory
     */
    template <typename InIter>
    inline size_type addRow_(const size_type nnzr, InIter ind)
    {
      size_type row_num = nRows();

      if (isCompact()) 
        decompact();

      // Allocate possibly one more row in all cases,
      // even if nnzr == 0 (identically zero row)
      if (row_num == nrows_max_-1) {
        
        size_type *nzr_new = NULL, **ind_new = NULL;
        nrows_max_ *= 2;
        nzr_new = new size_type[nrows_max_];
        ind_new = new size_type*[nrows_max_];
        memcpy(nzr_new, nzr_, row_num * sizeof(size_type));
        memcpy(ind_new, ind_, row_num * sizeof(size_type*));
        delete [] nzr_;
        delete [] ind_;
        nzr_ = nzr_new;
        ind_ = ind_new;
      } 

      // Can be a row of zeros, in which case nzr_[row_num] == 0
      nzr_[row_num] = nnzr; 
      ind_[row_num] = new size_type[nnzr];

      InIter ind_it = ind, ind_end = ind + nnzr;
      size_type *target_ind = ind_[row_num];
      while (ind_it != ind_end) {
        *target_ind = *ind_it;
        ++target_ind; ++ind_it;
      }

      ++nrows_;
      return row_num;
    }

    //--------------------------------------------------------------------------------
    /**
     * Compacts a row from nzb_ to (nzr_[r], ind_[r], nz_[r]).
     * Mutating, allocates memory.
     *
     * @param r [0 <= size_type < nrows] row index
     *
     * @b Exceptions:
     *  @li r < 0 || r >= nrows_ (assert)
     *  @li Not enough memory (error)
     */
    inline void compactRow_(const size_type& r) 
    {
      { // Pre-conditions
        // assert because private (likely to be checked already)
        // and for speed
        NTA_ASSERT(r >= 0 && r < nRows())
          << "SparseMatrix01::compactRow_(): "
          << "Invalid row index: " << r
          << " - Should be >= 0 and < " << nRows();
      }

      size_type *old_row_ptr = NULL, *new_row_ptr = NULL;
      size_type* indb_it = indb_;
      value_type* nzb_it = nzb_, nzb_end = nzb_ + nCols();

      while (nzb_it != nzb_end) 
        if (isNotZero_(*nzb_it++))
          *indb_it++ = nzb_it - nzb_;

      size_type nnzr = indb_it - indb_;
    
      if (nnzr > nzr_[r]) { // more non-zeros, need more memory
        
        if (isCompact()) // as late as possible, but... 
          decompact(); // changes ind_[r] and nz_[r]!!! but not nzr_[r]
        
        old_row_ptr = ind_[r];
        new_row_ptr = new size_type[nnzr];

        if (hasUniqueRows()) 
          swapCountKeys_(old_row_ptr, new_row_ptr);

        delete [] ind_[r]; // recycle, or delete later
      }
      
      // We are paying here, with two copies each call
      // to axby, because we don't have nnzr_max per row
      memcpy(ind_[r], indb_, nnzr * sizeof(size_type));
      nzr_[r] = nnzr; // maybe a different value
    }

  public:
    //--------------------------------------------------------------------------------
    /**
     * Constructor with a number of columns and a hint for the number
     * of rows. The SparseMatrix01 is empty.
     *
     * @param ncols [size_type > 0] number of columns
     * @param hint [size_type (16) >= 0] hint for the initial number of rows
     *
     * @b Exceptions:
     *  @li ncols <= 0 (check)
     *  @li hint < 0 (check)
     *  @li Not enough memory (error)
     */
    SparseMatrix01(const size_type& ncols, 
		   const size_type& hint =16, 
		   const size_type& nnzr =0)
      
      : nrows_(0), nrows_max_(0), ncols_(0),
        nzr_(0), ind_(0), indb_(0), nzb_(0),
        compact_(false),
        nnzr_(nnzr),
        counts_(RowCompare<size_type>(nnzr))
    {
      { // Pre-conditions
        NTA_CHECK(ncols > 0)
          << "SparseMatrix01::SparseMatrix01(ncols, hint): "
          << "Invalid number of columns: " << ncols
          << " - Should be > 0";

        NTA_CHECK(hint >= 0)
          << "SparseMatrix01::SparseMatrix01(ncols, hint): "
          << "Invalid hint: " << hint
          << " - Should be >= 0";
      }

      allocate_(hint, ncols);
    }

    //--------------------------------------------------------------------------------
    /**
     * Constructor from a dense matrix passed as an array of value_type.
     * Uses the values in mat to initialize the SparseMatrix01.
     *
     * @param nrows [size_type > 0] number of rows
     * @param ncols [size_type > 0] number of columns
     * @param mat [value_type** != NULL] initial array of values
     *
     * @b Exceptions:
     *  @li nrows <= 0 (check)
     *  @li ncols <= 0 (check)
     *  @li mat == NULL (check)
     *  @li NULL pointer in mat (check)
     *  @li Not enough memory (error)
     */
    template <typename InIter>
    SparseMatrix01(const size_type& nrows, 
		   const size_type& ncols, 
		   InIter mat, 
		   const size_type& nnzr) 

      : nrows_(0), nrows_max_(0), ncols_(0),
        nzr_(0), ind_(0), indb_(0), nzb_(0),
        compact_(false),
        nnzr_(nnzr),
        counts_(RowCompare<size_type>(nnzr))
    {
      { // Pre-conditions
        NTA_CHECK(nrows >= 0)
          << "SparseMatrix01::SparseMatrix01(nrows, ncols, mat): "
          << "Invalid number of rows: " << nrows
          << " - Should be >= 0";
        
        NTA_CHECK(ncols > 0)
          << "SparseMatrix01::SparseMatrix01(nrows, ncols, mat): "
          << "Invalid number of columns: " << ncols
          << " - Should be > 0";
      }

      fromDense(nrows, ncols, mat);
    }

    //--------------------------------------------------------------------------------
    /**
     * Destructor.
     */
    ~SparseMatrix01()
    {
      deallocate_();
    }

    //--------------------------------------------------------------------------------
    /**
     * Whether this matrix is zero or not.
     * Non-mutating, O(nrows).
     * This is computed, rather than maintained incrementally.
     *
     * @retval [bool] whether the matrix is zero or not
     */
    inline bool isZero() const { return nNonZeros() == 0; }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of rows in this SparseMatrix01.
     * Non-mutating, O(1).
     * 
     * @retval [size_type >= 0] number of rows
     */
    inline const size_type nRows() const { return nrows_; }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of colums in this SparseMatrix01.
     * Non-mutating, O(1).
     * 
     * @retval [size_type >= 0] number of columns
     */
    inline const size_type nCols() const { return ncols_; }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of non-zeros in this SparseMatrix01.
     * Non-mutating, O(nnz).
     * This is computed rather than stored and maintained incrementally.
     * This is slow, but we can't add the nzr_[i] because there might
     * be less non-zeros... So far, nobody has seen this method
     * on the critical path in a profile.
     * 
     * @retval [size_type >= 0] number of non-zeros
     */
    inline const size_type nNonZeros() const 
    {
      size_type nnz = 0, nrows = nRows();
      for (size_type i = 0; i < nrows; ++i) 
        nnz += nzr_[i];
      return nnz;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of non-zeros on 'row'-th row.
     * Non-mutating, O(nnzr).
     * This is slow, we rescan the line rather than returning nzr_[row],
     * because there might be small discrepancies. nzr_[row] really
     * represents how many elements are allocated, but there might be 
     * some elements that fall below epsilon in some cases.
     * 
     * @param row [SizeType >= 0 < nrows] index of the row to access
     * @retval [size_type >= 0] number of non-zeros on 'row'-th row
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nRows() (assert)
     */
    inline const size_type nNonZerosRow(const size_type& row) const 
    { 
      {
        NTA_ASSERT(0 <= row && row < nRows())
          << "SparseMatrix01::nNonZerosRow(): "
          << "Invalid row index: " << row
          << " - Should be >= 0 and < " << nRows();
      }
        
      return nzr_[row];
    }

    //--------------------------------------------------------------------------------
    inline bool hasUniqueRows() const
    {
      return nnzr_ > 0;
    }

    //--------------------------------------------------------------------------------
    inline bool isCompact() const
    {
      return compact_;
    }

    //--------------------------------------------------------------------------------
    /**
     * Exports this SparseMatrix01 to pre-allocated dense array of value_types.
     * Non-mutating, O(nnz).
     *
     * WARNING: does not update nnzr_, needed when counting rows
     * 
     * @param dense [value_type** != NULL] array in which to put the values
     *
     * @b Exceptions:
     *  @li dense == NULL (check)
     *  @li dense has NULL pointer (check)
     */
    template <typename OutIter>
    inline void toDense(OutIter dense) const
    {
      size_type nrows = nRows(), ncols = nCols();

      std::fill(dense, dense + nrows*ncols, (value_type)0);

      ITER_2(nrows, nzr_[i])
        *(dense + i*ncols + ind_[i][j]) = 1;
    }

    //--------------------------------------------------------------------------------
    /**
     * Populates this SparseMatrix01 from a dense array of value_types.
     * Mutating, discards the previous state of this SparseMatrix01.
     *
     * @param nrows [size_type > 0] number of rows in dense array
     * @param ncols [size_type > 0] number of columns in dense array
     * @param dense [value_type** != NULL] dense array of values
     *
     * WARNING: does not update nnzr_, needed when counting rows
     *
     * @b Exceptions:
     *  @li nrows <= 0 (check)
     *  @li ncols <= 0 (check)
     *  @li dense == NULL (check)
     *  @li dense has NULL pointer (check)
     *  @li Not enough memory (error)
     */
    template <typename InIter>
    inline void fromDense(const size_type& nrows, const size_type& ncols, InIter dense)
    {
      { // Pre-conditions
        NTA_CHECK(nrows >= 0)                  
          << "SparseMatrix01::fromDense(): "
          << "Invalid number of rows: " << nrows
          << " - Should be >= 0";

        NTA_CHECK(ncols > 0)
          << "SparseMatrix01::fromDense(): "
          << "Invalid number of columns: " << ncols
          << " - Should be > 0";
      }

      if (nzr_)
        deallocate_();

      allocate_(nrows, ncols);
      nrows_ = 0;

      for (size_type i = 0; i < nrows; ++i) 
        addRow(dense + i*ncols);
    }

    //--------------------------------------------------------------------------------
    /**
     * Populates this SparseMatrix01 from a stream in csr format.
     * The pairs (index, value) can be in any order for each row.
     * Mutating, discards the previous state of this SparseMatrix01.
     * Can handle large sparse matrices.
     *
     * @b Format:
     *  'csr' nrows ncols nnz
     *  nnzr1 j1 val1 j2 val2 ...
     *  nnzr2 ...
     *
     * The order of the (j, val) tuples doesn't matter.
     *
     * @param inStream [std::istream] the stream to initialize from
     * @retval [std::istream] the stream after the matrix has been read
     *
     * @b Exceptions:
     *  @li Bad stream (check)
     *  @li Stream does not start with 'csr' tag (check)
     *  @li nrows < 0 in stream (check)
     *  @li ncols <= 0 in stream (check)
     *  @li nnz < 0 || nnz > nrows * ncols in stream (check)
     *  @li nnzr < 0 || nnzr > ncols for any row (check)
     *  @li column index j < 0 || >= ncols for any row (check)
     *  @li Not enough memory (error)
     */
    inline std::istream& fromCSR(std::istream& inStreamParam)
    {
      const char* where = "SparseMatrix01::fromCSR(): ";

      { // Pre-conditions
        NTA_CHECK(inStreamParam.good())
          << where << "Bad stream";
      }

      std::string tag;
      inStreamParam >> tag;
      NTA_CHECK(tag == "csr01")
        << where
        << "Stream is not in csr format"
        << " - Should start with 'csr01' tag";

      // Read our stream data into a MemParser object for faster parsing. 
      long totalBytes;
      inStreamParam >> totalBytes;
      if (totalBytes < 0)
        totalBytes = 0;
      MemParser inStream(inStreamParam, totalBytes);

      size_type i, j, k, nrows, ncols, nnz, nnzr;

      inStream >> nrows >> ncols >> nnz >> nnzr;

      {
        NTA_CHECK(nrows >= 0)
          << where
          << "Invalid number of rows: " << nrows
          << " - Should be >= 0";

        NTA_CHECK(ncols > 0)
          << where
          << "Invalid number of columns: " << ncols
          << " - Should be > 0";

        NTA_CHECK(nnz >= 0 && nnz <= nrows * ncols)
          << where
          << "Invalid number of non-zeros: " << nnz
          << " - Should be >= 0 && nrows * ncols = " << nrows * ncols;

        NTA_CHECK(nnzr >= 0 && nnzr <= ncols)
          << where
          << "Invalid number of non-zeros per row: " << nnzr
          << " - Should be >= 0 && ncols = " << ncols;
      }
      
      if (nzr_) 
        deallocate_();

      allocate_(nrows, ncols);   
      nrows_ = 0;
      nnzr_ = nnzr;

      std::vector<size_type> counts(nrows, 1);
      if (hasUniqueRows()) {
        size_type count = 1;
        for (i = 0; i < nrows; ++i) {
          inStream >> count;
          counts[i] = count;
        }
      }

      for (i = 0; i < nrows; ++i) {

        size_type *indb_it = indb_;
        inStream >> nzr_[i];

        {
          NTA_CHECK(nzr_[i] >= 0 && nzr_[i] <= ncols)
            << where
            << "Invalid number of non-zeros: " << nzr_[i]
            << " - Should be >= 0 && < ncols = " << ncols;
        }

        for (k = 0; k < nzr_[i]; ++k) {
          
          inStream >> j;
          
          {
            NTA_CHECK(j >= 0 && j < ncols)
              << where
              << "Invalid index: " << j
              << " - Should be >= 0 and < ncols = " << ncols;
          }

          *indb_it++ = j;
        }

        addRow(size_type(indb_it - indb_), indb_);
      }

      typename Counts::iterator it;
      for (it = counts_.begin(); it != counts_.end(); ++it)
        it->second.second = counts[it->second.first];

      compact();

      return inStreamParam;
    }

    //--------------------------------------------------------------------------------
    /**
     * Exports this SparseMatrix01 to a stream in csr format.
     *
     * @param out [std::ostream] the stream to write this matrix to
     * @retval [std::ostream] the stream with the matrix written to it
     *
     * @b Exceptions:
     *  @li Bad stream (check)
     */
    inline std::ostream& toCSR(std::ostream& out) const 
    {
      { // Pre-conditions
        NTA_CHECK(out.good())
          << "SparseMatrix01:toCSR(): "
          << "Bad stream";
      }
      
      out << "csr01 ";
      
      OMemStream outStream;
      outStream << nRows() << " " 
                << nCols() << " " 
                << nNonZeros() << " "
                << nnzr_ << " ";
      
      if (hasUniqueRows()) {
        std::vector<size_type> counts(counts_.size());
        typename Counts::const_iterator it;
        for (it = counts_.begin(); it != counts_.end(); ++it)
          counts[it->second.first] = it->second.second;
        typename std::vector<size_type>::const_iterator it_v;
        for (it_v = counts.begin(); it_v != counts.end(); ++it_v)
          outStream << *it_v << " ";
        //outStream << it->second.first << " " << it->second.second << " ";
      } 

      size_type i, nrows = nRows();
      for (i = 0; i < nrows; ++i) {
        outStream << nzr_[i] << " ";
        size_type* ind_it = ind_[i], *ind_end = ind_it + nzr_[i];
        while (ind_it != ind_end)
          outStream << *ind_it++ << " ";
      }

      // Write total # of bytes, followed by data. 
      // This facilitates faster parsing of the
      // data directly from a memory buffer in fromCSR() 
      out << outStream.pcount() << " ";
      out.write(outStream.str(), UInt(outStream.pcount()));
      return out;
    }

    //--------------------------------------------------------------------------------
    /**
     * Compatible with SparseMatrix from CSR.
     */
    inline std::ostream& toCSRFull(std::ostream& out) const 
    {
      { // Pre-conditions
        NTA_CHECK(out.good())
          << "SparseMatrix01:toCSR(): "
          << "Bad stream";
      }
      
      out << "csr ";
      
      OMemStream buf;
      buf << nRows() << " " << nCols() << " " << nNonZeros() << " "; 

      size_type i, nrows = nRows();
      for (i = 0; i < nrows; ++i) {
        buf << nzr_[i] << " ";
        size_type* ind_it = ind_[i], *ind_end = ind_it + nzr_[i];
        while (ind_it != ind_end)
          buf << *ind_it++ << " 1 ";
      }

      // Write total # of bytes, followed by data. 
      // This facilitates faster parsing of the
      // data directly from a memory buffer in fromCSR() 
      out << buf.pcount() << " ";
      out.write(buf.str(), UInt(buf.pcount()));
      return out;
    }

    //--------------------------------------------------------------------------------
    /**
     * Compacts the memory for this SparseMatrix01. 
     * This reduces the number of cache misses, and can
     * make a sizable runtime difference (up to 30% on shona,
     * depending on the operation).
     * All the non-zeros are allocated contiguously.
     * Non-mutating algorithms can run on the compact representation.
     *
     * Mutating, O(nnz)
     *
     * @b Exceptions:
     *  @li Not eneough memory (error)
     */
    inline void compact()
    {
      if (nRows() == 0) {
        compact_ = true;
        return;
      }
      
      size_type i, nnz = nNonZeros(), top, *indp = NULL, nrows = nRows();
      size_type* old_ind = ind_[0];

      // Allocate contiguous storage for the whole 
      // sparse matrix
      indp = new size_type[nnz];
      
      // Copy the old row to the new location ...
      // ... and delete the old location if we 
      // were allocated separately (not compact)
      for (top = 0, i = 0; i < nrows; ++i) {
      
        memcpy(indp + top, ind_[i], nzr_[i] * sizeof(size_type)); 

        if (hasUniqueRows())
          swapCountKeys_(ind_[i], indp + top);

        if (!isCompact()) 
          delete [] ind_[i];

        ind_[i] = indp + top;
        top += nzr_[i];
      }

      if (compact_) 
        delete [] old_ind;
      
      compact_ = true;
    }
 
    //--------------------------------------------------------------------------------
    /**
     * "De-compacts" this SparseMatrix01, that is, each row 
     * is allocated separately. All the non-zeros inside a given row
     * are still allocated contiguously. This is more efficient
     * when changing the number of non-zeros on each row (rather than
     * reallocating the whole contiguous array of all the non-zeros
     * in the SparseMatrix01. We decompact before mutating the non-zeros,
     * and we recompact once the non-zeros don't change anymore.
     *
     * Mutating, O(nnz)
     *
     * @b Exceptions:
     *  @li Not enough memory (error)
     */
    inline void decompact()
    {
      size_type i, nnzr, nrows = nRows();
      size_type* old_ind = ind_[0];
    
      for (i = 0; i < nrows; ++i) {
        
        nnzr = nzr_[i];
        size_type* ind = new size_type[nnzr];
        memcpy(ind, ind_[i], nnzr*sizeof(size_type));

        if (nnzr_ > 0) {
          Row_Count row_val = counts_[ind_[i]];
          counts_.erase(ind_[i]);
          counts_[ind] = row_val;
        }

        if (!isCompact()) 
          delete [] ind_[i];
        
        ind_[i] = ind;
      }
    
      if (isCompact()) 
        delete [] old_ind;
    
      compact_ = false;
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds a row to this SparseMatrix01. The iterator
     * iterates over the values in increasing
     * order of indices. The iterator needs to span 
     * ncols values.
     *
     * Mutating, can increase the number of non-zeros, O(nnzr + K)
     *
     * @param x [InIter<value_type>] input iterator for row values.
     *  x needs to be a contiguous array in memory, like std::vector.
     *
     * @b Exceptions:
     *  @li Not enough memory (error)
     */
    template <typename InIter>
    inline size_type addRow(InIter x)
    {
      size_type *indb_it = indb_;
      InIter x_it = x, x_end = x + nCols();

      // TODO: what if numbers are negative?
      while (x_it != x_end) {
        if (*x_it > 0) 
          *indb_it++ = size_type(x_it - x);
        ++x_it;
      }

      return addRow(size_type(indb_it - indb_), indb_);
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds a row to this SparseMatrix01, from an iterator on indices of 
     * non-zeros. If x is already a row in this SparseMatrix01, 
     * and this sparse matrix is set up to work with unique rows, it is not 
     * added, but its count is incremented. Otherwise, x is added to
     * this sparse matrix.
     *
     * x needs to be a contiguous array in memory, like std::vector.
     *
     * @param nnzr [size_type >= 0] the number of non-zeros in x
     * @param x [InIter<size_type>] itertor to the beginning of a contiguous array
     *  containing the indices of the non-zeros.
     * @retval size_type the index of the row
     */
    template <typename InIter>
    inline size_type addRow(const size_type nnzr, InIter x_begin)
    {
      size_type j = 0, ncols = nCols(), prev = 0, row_index = 0;
      InIter jj = x_begin;

      { // Pre-conditions
        NTA_ASSERT(nnzr >= 0)
          << "SparseMatrix01::addRow(): "
          << "Passed nnzr = " << nnzr
          << " - Should be >= 0";

        NTA_ASSERT(nnzr <= nCols())
          << "SparseMatrix01::addRow(): "
          << "Passed nnzr = " << nnzr
          << " but there are only " << nCols() << " columns";

        /* Too noisy
        if (nnzr == 0)
          NTA_WARN
            << "SparseMatrix01::addRow(): "
            << "Passed nnzr = 0 - Won't do anything";
        */

        for (j = 0; j < nnzr; ++j, ++jj) {
          NTA_ASSERT(0 <= *jj && *jj < ncols)
            << "SparseMatrix01::addRow(): "
            << "Invalid column index: " << *jj 
            << " - Should be >= 0 and < " << ncols;
          
          if (j > 0) {
            NTA_ASSERT(prev < *jj)
              << "SparseMatrix01::addRow(): "
              << "Indices need to be in strictly increasing order, "
              << "found: " << prev << " followed by: " << *jj;
          }
          prev = *jj;
        }
      } // End pre-conditions

      if (nnzr_ == 0) {
        
        row_index = addRow_(nnzr, x_begin);

      } else { // unique, counted rows
        
        // TODO: speed up by inserting and looking at returned iterator?
        typename Counts::iterator it = counts_.find(&*x_begin);
        
        if (it != counts_.end()) {
          ++(it->second.second);
          row_index = it->second.first;
        } else {
          row_index = addRow_(nnzr, x_begin);
          counts_[ind_[row_index]] = std::make_pair(row_index, 1);
        }
      } // end unique, counted rows

      return row_index;
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the max value inside each segment defined by the boundaries, 
     * records a "1" in indb_ at the corresponding position, e.g.:
     * 
     * boundaries = 3 6 9
     * x = .7 .3 .4 .2 .8 .1 .5 .5 .7
     * gives:
     * binarized x = 1 0 0 0 1 0 0 0 1 (not actually computed or stored)
     * and indb_ = 0 4 8 (the indices of the 1s)
     *
     * WARNING: this works if this SparseMatrix01 is set up to work
     * with unique rows only.
     *
     * @param boundaries [InIter1<UInt>] iterator to beginning of a contiguous
     *  array that contains the boundaries for the filtering operation
     * @param x [InIter2<value_type>] iterator to beginning of input vector
     *
     * @b Exceptions:
     *  @li If matrix is not set up to handle unique rows.
     *  @li If first boundary is zero.
     *  @li If boundaries are not in strictly increasing order.
     *  @li If last boundary is not equal to the number of columns.
     */
    template <typename InIter1, typename InIter2>
    inline void winnerTakesAll(InIter1 boundaries, InIter2 x)
    {
      { // Pre-conditions
        const char* where = "SparseMatrix01::winnerTakesAll(): ";
        
        // This works only with unique, counted rows (nnzr_ != 0)
        NTA_ASSERT(nnzr_ != 0)
          << where
          << "Attempting to call this method on a SparseMatrix01 "
          << "that was not set up to work with unique rows";
        
        // First boundary cannot be zero
        NTA_ASSERT(*boundaries > 0)
          << where 
          << "Zero is not allowed for first boundary";
        
        // Boundaries need to be passed in strictly increasing
        // order
        for (size_type i = 1; i < nnzr_; ++i)
          NTA_ASSERT(boundaries[i-1] < boundaries[i])
            << where
            << "Passed invalid boundaries: " << boundaries[i-1]
            << " and " << boundaries[i]  
            << " at " << i-1 << " and " << i
            << " out of " << nCols()
            << " - Boundaries need to be passed in strictly increasing order";

        // The last boundary is the number of columns
        NTA_ASSERT(nCols() == boundaries[nnzr_-1])
          << where
          << "Wrong boundaries passed in, last boundary "
          << "should be number of columns (" << nCols() << ") "
          << "but found: " << boundaries[nnzr_-1];
      } // End pre-conditions

      /*
      size_type i, k, row_index = 0;
      value_type val, max_v = 0; //- std::numeric_limits<value_type>::max();
      
      for (i = 0, k = 0; i < nnzr_; ++i) {
        indb_[i] = i == 0 ? 0 : boundaries[i-1];
        for (max_v = 0; k < boundaries[i]; ++k, ++x) {
          val = *x;
          if (val > max_v) {
            indb_[i] = k;
            max_v = val;
          } 
        }
      }
      */

      value_type val, max_v = 0;//- std::numeric_limits<value_type>::max();
      InIter1 b_it = boundaries, b_end = boundaries + nnzr_;
      InIter2 it_x = x, x_end = x;
      size_type* indb_it = indb_;

      for (; b_it != b_end; ++b_it, ++indb_it) {
        max_v = 0;
        x_end = x + *b_it;
        *indb_it = size_type(it_x - x);
        for (; it_x != x_end; ++it_x) {
          val = *it_x;
          if (val > max_v) {
            *indb_it = size_type(it_x - x);
            max_v = val;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Filters a row using the given boundaries and adds a new row 
     * based on that filtered vector if it was not seen before.
     * The filtering operation consists in replacing the max value of x
     * by 1 and the other values by 0 in the each segment defined by 
     * the boundaries.
     * That is, if x = [.5 .7 .3 .2 .6 .3 0 .9] and boundaries = [4 8],
     * the result of filtering is: [0 1 0 0 0 0 0 1]: 
     * .7 is the max in the segment [0..4) , 
     * and .9 is the max in in the segment [4..8)
     *
     * WARNING: this works if this SparseMatrix01 is set up to work
     * with unique rows only.
     *
     * @param boundaries [InIter1<UInt>] iterator to beginning of a contiguous
     *  array that contains the boundaries for the filtering operation
     * @param x [InIter2<value_type>] iterator to beginning of input vector
     *
     * @b Exceptions:
     *  @li If matrix is not set up to handle unique rows.
     *  @li If first boundary is zero.
     *  @li If boundaries are not in strictly increasing order.
     *  @li If last boundary is not equal to the number of columns.
     */
    template <typename InIter1, typename InIter2>
    inline size_type addUniqueFilteredRow(InIter1 boundaries, InIter2 x)
    {
      size_type row_index = 0;

      winnerTakesAll(boundaries, x);

      // TODO: make sure we have really found nnzr non-zeros:
      // a vector of all zeros will yield for indices of the non-zeros
      // the indices of the first elements of each child,
      // which would be indistinguishable from the vectors were the
      // first positions for each child are really the maxima! 
      // And we don't want to remember indices of actual zeros. 
        
      // TODO: speed up by inserting and looking at returned iterator?
      typename Counts::iterator it = counts_.find(indb_);
      
      if (it != counts_.end()) {
        ++ (it->second.second);
        row_index = it->second.first;
      } else {
        row_index = addRow_(nnzr_, indb_);
        counts_[ind_[row_index]] = std::make_pair(row_index, 1);
      }
      
      return row_index;
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the closest coincidence to x according to Hamming distance.
     * If the closest distance is less than maxDistance, the count of the 
     * corresponding coincidence is incremented by one, otherwise, 
     * a new coincidence is inserted in the matrix, with a count of 1.
     *
     * WARNING: this works if this SparseMatrix01 is set up to work
     * with unique rows only.
     *
     * @param boundaries [InIter1<UInt>] iterator to beginning of a contiguous
     *  array that contains the boundaries for the filtering operation
     * @param x [InIter2<value_type>] iterator to beginning of input vector
     * @param maxDistance max distance to closest coincidence that will trigger
     *  the insertion of a new coincidence
     *
     * @b Exceptions:
     *  @li If matrix is not set up to handle unique rows.
     *  @li If first boundary is zero.
     *  @li If boundaries are not in strictly increasing order.
     *  @li If last boundary is not equal to the number of columns.
     */
    template <typename InIter1, typename InIter2>
    inline size_type addMinHamming(InIter1 boundaries, InIter2 x, 
				   const value_type& maxDistance)
    {
      size_type row_index = 0;
      size_type hamming, min_hamming, *ind, *ind_end, *indb;
      typename Counts::iterator it, it_end, arg_it;

      // Binarize x into indb_
      winnerTakesAll(boundaries, x);

      // Find Hamming-closest row
      min_hamming = nnzr_; //std::numeric_limits<size_type>::max();
      arg_it = it = counts_.begin(); it_end = counts_.end();

      while (it != it_end) {
	hamming = 0;
	ind = it->first; ind_end = ind + nnzr_; indb = indb_;
	while (ind != ind_end && hamming < min_hamming) {
	  hamming += *ind != *indb; // this works because nnzr_ = constant
	  ++ind; ++indb;
	}
	if (hamming < min_hamming) {
	  arg_it = it;
	  min_hamming = hamming;
	}
	++it;
      }

      // So far, we have counted the mismatching segments
      // the Hamming distance is twice that number
      if (2*min_hamming <= maxDistance) {
	++ (arg_it->second.second);
	row_index = arg_it->second.first;
      } else {
	row_index = addRow_(nnzr_, indb_);
	counts_[ind_[row_index]] = std::make_pair(row_index, 1);
      }

      return row_index;
    }

    //--------------------------------------------------------------------------------
    /*
    template <typename InIter>
    inline size_type addWithThreshold(InIter x, const value_type& threshold)
    {
      size_type row_index = 0, *indb = indb_;

      for (InIter x_end = x + nCols(); x != x_end; ++x) {
	value_type val = *x;
	if (val > threshold) {
	  *indb = val;
	  ++indb;
	}
      }
      
      typename Counts::iterator it = counts_.find(indb_);
      
      if (it != counts_.end()) {
        ++ (it->second.second);
        row_index = it->second.first;
      } else {
        row_index = addRow_(nnzr_, indb_);
        counts_[ind_[row_index]] = std::make_pair(row_index, 1);
      }
      
      return row_index;
    }
    */

    //--------------------------------------------------------------------------------
    /**
     * Deletes specified rows.
     * The indices of the rows are passed in a range [del..del_end).
     * The range can be contiguous (std::vector) or not (std::list, std::map).
     * The matrix can end up empty if all the rows are removed.
     * If the list of rows to remove is empty, the matrix is unchanged.
     *
     * WARNING: the row indices need to be passed with duplicates,
     * in strictly increasing order. 
     *
     * @param del [InIter<size_type>] iterator to the beginning of the range
     *  that contains the indices of the rows to be deleted
     * @param del_end [InIter<size_type>] iterator to one past the end of the 
     *  range that contains the indices of the rows to be deleted
     *
     * @b Exceptions:
     *  @li If a row index < 0 || >= nRows().
     *  @li If row indices are not passed in strictly increasing order.
     *  @li If del_end - del < 0 || del_end - del > nRows().
     */
    template <typename InIter>
    inline void deleteRows(InIter del_it, InIter del_end)
    {
      ptrdiff_t n_del = del_end - del_it;

      // Here because pre-conditions will fail if nRows == 0
      if (n_del <= 0 || nRows() == 0)
        return;
			
      { // Pre-conditions
        if (n_del > 0) {
          
          NTA_ASSERT(n_del <= (ptrdiff_t)nRows())
            << "SparseMatrix01::deleteRows(): "
            << " Passed more indices of rows to delete"
            << " than there are rows";

          InIter d = del_it, d_next = del_it + 1;
          while (d < del_end - 1) {
            NTA_ASSERT(0 <= *d && *d < nRows())
              << "SparseMatrix01::deleteRows(): "
              << "Invalid row index: " << *d
              << " - Row indices should be between 0 and " << nRows();
            NTA_ASSERT(*d < *d_next)
              << "SparseMatrix01::deleteRows(): "
              << "Invalid row indices " << *d << " and " << *d_next
              << " - Row indices need to be passed "
              << "in strictly increasing order";
            ++d; ++d_next;
          }
            
          NTA_ASSERT(0 <= *d && *d < nRows())
            << "SparseMatrix01::deleteRows(): "
            << "Invalid row index: " << *d
            << " - Row indices should be between 0 and " << nRows();

        } else if (n_del == 0) {
          
          /* Too noisy
          NTA_WARN 
            << "SparseMatrix01::deleteRows(): "
            << "Nothing to delete";
          */

        } else if (n_del < 0) {

          /* Too noisy
          NTA_WARN
            << "SparseMatrix01::deleteRows(): "
            << "Invalid pointers - Won't do anything";
          */
        }
      }

      if (isCompact())
        decompact();

      size_type *nzr_old = nzr_, *nzr_it = nzr_;
      size_type **ind_old = ind_, **ind_it = ind_;
      
      for (size_type i_old = 0; i_old < nrows_; ++i_old) {
        if (del_it != del_end && i_old == *del_it) {
	  if (hasUniqueRows()) {
	    counts_.erase(*ind_old);
	  }
	  // DON'T delete here: it would require updating nrows_max_
	  // and we don't have the time anyway.
	  //delete [] *ind_old++;
	  ++ind_old;
	  ++nzr_old;
          ++del_it;
        } else {
          *nzr_it++ = *nzr_old++;
          *ind_it++ = *ind_old++;
        }
      }

      nrows_ = size_type(nzr_it - nzr_);
    }

    //--------------------------------------------------------------------------------
    /**
     * Deletes rows whose count is < threshold.
     *
     * @b Exceptions:
     */
    template <typename OutIter>
    inline void deleteRows(const size_type& threshold, OutIter del_it)
    {
      {
        NTA_ASSERT(hasUniqueRows())
          << "SparseMatrix01::deleteRows(threshold): "
          << "Sparse matrix needs to be in unique rows mode";
      }

      size_type offset = 0;
      std::vector<size_type> to_del, row_counts;
      row_counts = getRowCountsSorted();

      for (size_type i = 0; i < row_counts.size(); ++i) {
        if (row_counts[i] < threshold) {
          to_del.push_back(i);
          *del_it++ = std::make_pair(i, row_counts[i]);
          ++offset;
        } else {
          counts_[ind_[i]].first -= offset;
        }
      }

      deleteRows(to_del.begin(), to_del.end());
    }

    //--------------------------------------------------------------------------------
    /**
     * Deletes specified columns.
     * The indices of the columns are passed in a range [del..del_end).
     * The range can be contiguous (std::vector) or not (std::list, std::map).
     * The matrix can end up empty if all the columns are removed.
     * If the list of columns to remove is empty, the matrix is unchanged.
     *
     * WARNING: the columns indices need to be passed with duplicates,
     * in strictly increasing order. 
     *
     * @param del [InIter<size_type>] iterator to the beginning of the range
     *  that contains the indices of the columns to be deleted
     * @param del_end [InIter<size_type>] iterator to one past the end of the 
     *  range that contains the indices of the columns to be deleted
     *
     * @b Exceptions:
     *  @li If a column index < 0 || >= nCols().
     *  @li If column indices are not passed in strictly increasing order.
     *  @li If del_end - del < 0 || del_end - del > nCols().
     */
    template <typename InIter>
    inline void deleteColumns(InIter del_it, InIter del_end)
    {
      ptrdiff_t n_del = del_end - del_it;
			
      if (n_del <= 0 || nCols() == 0)
        return;

      { // Pre-conditions
        if (n_del > 0) {
          
          NTA_ASSERT(n_del <= (ptrdiff_t)nCols())
            << "SparseMatrix01::deleteColumns(): "
            << " Passed more indices of rows to delete"
            << " than there are columns";

          InIter d = del_it, d_next = del_it + 1;
          while (d < del_end - 1) {
            NTA_ASSERT(0 <= *d && *d < nCols())
              << "SparseMatrix01::deleteColumns(): "
              << "Invalid column index: " << *d
              << " - Column indices should be between 0 and " << nCols();
            NTA_ASSERT(*d < *d_next)
              << "SparseMatrix01::deleteColumns(): "
              << "Invalid column indices " << *d << " and " << *d_next
              << " - Column indices need to be passed "
              << "in strictly increasing order";
            ++d; ++d_next;
          }
            
          NTA_ASSERT(0 <= *d && *d < nCols())
            << "SparseMatrix01::deleteColumns(): "
            << "Invalid column index: " << *d
            << " - Column indices should be between 0 and " << nCols();

        } else if (n_del == 0) {
          
          /* Too noisy
          NTA_WARN 
            << "SparseMatrix01::deleteColumns(): "
            << "Nothing to delete";
          */

        } else if (n_del < 0) {

          /* Too noisy
          NTA_WARN
            << "SparseMatrix01::deleteColumns(): "
            << "Invalid pointers - Won't do anything";
          */
        }
      }

      InIter d;
      size_type i, j, *ind, *ind_old, *ind_end;

      for (i = 0; i < nRows(); ++i) {
        
        j = 0;
        d = del_it;
        ind = ind_[i]; ind_old = ind; ind_end = ind + nzr_[i];
        
        while (ind_old != ind_end && d != del_end) {
          if (*d == *ind_old) {
            ++d; ++j;
            ++ind_old;
          } else if (*d < *ind_old) {
            ++d; ++j;
          } else {
            *ind++ = *ind_old++ - j;
          }
        }
        
        while (ind_old != ind_end) 
          *ind++ = *ind_old++ - j;
        
        nzr_[i] = size_type(ind - ind_[i]);
      }

      ncols_ -= std::max(size_type(0), size_type(n_del));
    }

    //--------------------------------------------------------------------------------
    /**
     * The data structure returned by getRowCounts(), that contains row indices and 
     * counts. The first integer is the index of the row, the second is the number 
     * of times that row was inserted in the matrix. In "unique rows" mode, rows
     * are inserted once if they are not yet in the matrix, and then a running count
     * is incremented each the same row is presented for insertion afterwards. The count
     * starts with a value of 1 the first time the row is encountered. The index is the 
     * number of rows of the matrix at the time the row is inserted. 
     */
    typedef std::vector<Row_Count> RowCounts;

    //--------------------------------------------------------------------------------
    /**
     * This function can be called only if the matrix has been set up to work
     * with unique rows (nnzr_ > 0, the matrix was constructed with a fixed 
     * number of non-zeros per row).
     *
     * WARNING: the row counts are not in any particular order!
     *
     * Non-mutating.
     *
     * @b Exceptions:
     *  @li If calling  but matrix was not initialized properly by declaring 
     *      the number of non-zeros per row (error).
     */
    inline RowCounts getRowCounts() const
    {
      {
        NTA_ASSERT(nnzr_ > 0)
          << "SparseMatrix01::getRowCounts(): "
          << "Called for unique rows, but matrix is not set up to work"
          << " with unique rows";
      }

      RowCounts rc;
      typename Counts::const_iterator it;

      for (it = counts_.begin(); it != counts_.end(); ++it)
        rc.push_back(it->second);

      return rc;
    }

    //--------------------------------------------------------------------------------
    /**
     * This function can be called only if the matrix has been set up to work
     * with unique rows (nnzr_ > 0, the matrix was constructed with a fixed 
     * number of non-zeros per row).
     * 
     * Non-mutating.
     *
     * @b Exceptions:
     *  @li If calling  but matrix was not initialized properly by declaring 
     *      the number of non-zeros per row (error).
     */
    inline std::vector<size_type> getRowCountsSorted() const
    {
      {
        NTA_ASSERT(nnzr_ > 0)
          << "SparseMatrix01::getRowCountsSorted(): "
          << "Called for unique rows, but matrix is not set up to work"
          << " with unique rows";
      }
      
      std::vector<size_type> rc(counts_.size(), 0);
      typename Counts::const_iterator it;

      for (it = counts_.begin(); it != counts_.end(); ++it)
        rc[it->second.first] = it->second.second;

      return rc;
    }

    //--------------------------------------------------------------------------------
    /**
     * Stores r-th row of this sparse matrix in provided iterators.
     * The iterators need to point to enough storage.
     * Non-mutating, O(nnzr)
     *
     * @param r [0 <= size_type < nrows] row index
     * @param indIt [OutIter1<size_type>] output iterator for indices
     * @param nzIt [OutIter2<value_type>] output iterator for non-zeros
     *
     * @b Exceptions:
     *  @li r < 0 || r >= nrows (check)
     */
    template <typename OutIter1>
    inline void getRowSparse(const size_type& r, OutIter1 indIt) const
    {
      { // Pre-conditions
        NTA_ASSERT(r >= 0 && r < nRows())
          << "SparseMatrix01::getRowSparse(): "
          << "Invalid row index: " << r
          << " - Should be >= 0 and < " << nRows();
      }
      
      size_type *ind = ind_[r], *ind_end = ind + nzr_[r];

      // Won't do anything to the iterators
      // if row r has only zeros
      while (ind != ind_end)
        *indIt++ = *ind++;
    }

    //--------------------------------------------------------------------------------
    /** 
     */
    template <typename OutIter>
    inline void getRow(const size_type& r, OutIter x_begin) const
    {
      { // Pre-conditions
        NTA_ASSERT(r >= 0 && r < nRows())
          << "SparseMatrix01::getRow(): "
          << "Invalid row index: " << r
          << " - Should be >= 0 and < " << nRows();
      }

      OutIter it = x_begin, it_end = x_begin + nCols();
      size_type *ind = ind_[r], *ind_end = ind + nzr_[r];

      while (it != it_end)
        *it++ = 0;

      while (ind != ind_end)
        *(x_begin + *ind++) = 1;
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the square of the distance between vector x
     * and each row of this SparseMatrix01. Puts the result 
     * in vector y.
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InIter<value_type>] vector to compute the distance from
     * @param y [OutIter<value_type>] vector of the squared distances to x
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InIter, typename OutIter>
    inline void vecDistSquared(InIter x, OutIter y) const
    {
      size_type i, j, k, nnzr, *ind, nrows = nRows(), ncols = nCols();
      value_type val1, val;
      value_type *sq_x = nzb_, Ssq_x = 0;

      for (j = 0; j < ncols; ++j) 
        Ssq_x += sq_x[j] = x[j] * x[j]; 

      for (i = 0; i < nrows; ++i) {

        val = Ssq_x;
        nnzr = nzr_[i];
        ind = ind_[i];
        
        for (k = 0; k < nnzr; ++k) {
          j = ind[k];
          val1 = value_type(1.0 - x[j]);
          val += val1 * val1 - sq_x[j];
        }

        // Accuracy issues because of the subtractions,
        // could return negative values
        if (val <= nta::Epsilon)
          val = 0;
        
        { // Post-condition
          NTA_ASSERT(val >= 0)
            << "SparseMatrix01::vecDistSquare(): "
            << "Negative value in post-condition";
        }

        *y++ = val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the Euclidean distance between vector x
     * and each row of this SparseMatrix01. Puts the result
     * in vector y.
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InIter<value_type>] vector to compute the distance from
     * @param y [OutIter<value_type>] vector of the squared distances to x
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InIter, typename OutIter>
    inline void vecDist(InIter x, OutIter y) const
    {
      nta::Sqrt<value_type> s;

      vecDistSquared(x, y);
      
      ITERATE_ON_ALL_ROWS {
        *y = s(*y);
	++y;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the distance between vector x and a given row
     * of this SparseMatrix01. Returns the result as a value_type.
     *
     * Non-mutating, O(ncols + nnzr) !!!
     *
     * @param row [0 <= size_type < nrows] index of row to compute distance from
     * @param x [InIter<value_type>] vector of the squared distances to x
     * @retval [value_type] distance from x to row of index 'row'
     * 
     * @b Exceptions:
     *  @li row < 0 || row >= nrows (check)
     */
    template <typename InIter>
    inline value_type rowDistSquared(const size_type& row, InIter x) const
    {
      { // Pre-conditions
        NTA_ASSERT(row >= 0 && row < nRows())
          << "SparseMatrix01::rowDistSquared(): "
          << "Invalid row index: " << row
          << " - Should be >= 0 and < nrows = " << nRows();
      }

      size_type j, k, nnzr, *ind, ncols = nCols();
      value_type val1, val;
      value_type *sq_x = nzb_, Ssq_x = 0;

      for (j = 0; j < ncols; ++j) 
        Ssq_x += sq_x[j] = x[j] * x[j]; 

      val = Ssq_x;
      nnzr = nzr_[row];
      ind = ind_[row];
      
      for (k = 0; k < nnzr; ++k) {
        j = ind[k];
        val1 = value_type(1.0 - x[j]);
        val += val1 * val1 - sq_x[j];
      }

      // Accuracy issues because of the subtractions,
      // could return negative values
      if (val <= nta::Epsilon)
        val = 0;
      
      { // Post-condition
        NTA_ASSERT(val >= 0)
          << "SparseMatrix01::rowDistSquared(): "
          << "Negative value in post-condition";
      }
      
      return val;
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the Euclidean distance between vector x and 
     * each row of this SparseMatrix01. Returns the index of the row
     * that minimizes the Euclidean distance and the value of this 
     * distance.
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InIter<value_type>] vector to compute the distance from
     * @retval [std::pair<size_type, value_type>] index of the row closest
     *  to x, and value of the distance between x and that row
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InIter>
    inline std::pair<size_type, value_type> closestEuclidean(InIter x) const
    {
      size_type i, j, k, arg_i, nnzr, *ind, nrows = nRows(), ncols = nCols();
      value_type val, val1, min_v; 
      value_type *sq_x = nzb_, Ssq_x = 0;

      // Pre-computing the sum of the squares of x and 
      // modifying it with only the non-zeros of each row
      // is a huge performance improvement, but shows some 
      // floating-point accuracy problems when working in float.
      // It's ok when working in double.
      for (i = 0; i < ncols; ++i)
        Ssq_x += sq_x[i] = x[i] * x[i];

      arg_i = 0;
      min_v = std::numeric_limits<value_type>::max();

      for (i = 0; i < nrows; ++i) {

        val = Ssq_x;
        nnzr = nzr_[i];
        ind = ind_[i];

        for (k = 0; k < nnzr; ++k) { 
          j = ind[k];
          val1 = value_type(1.0 - x[j]);
          val += val1 * val1 - sq_x[j];
        }

        if (val < min_v) {
          arg_i = i;
          min_v = val;
        }
      }

      // Accuracy issues because of the subtractions,
      // could return negative values
      if (min_v <= nta::Epsilon)
        min_v = 0;

      { // Post-condition
        NTA_ASSERT(min_v >= 0)
          << "SparseMatrix01::closestEuclidean(): "
          << "Negative value in post-condition";
      }

      nta::Sqrt<value_type> s;
      return std::make_pair(arg_i, s(min_v));
    }

    //--------------------------------------------------------------------------------
    template <typename InIter>
    inline std::pair<size_type, value_type> closest01(InIter x) const
    {
      size_type i, j, k, arg_i, nnzr, *ind, nrows = nRows(), ncols = nCols();
      value_type val, min_v; 
      value_type *sq_x = nzb_, Ssq_x = 0;

      // Pre-computing the sum of the squares of x and 
      // modifying it with only the non-zeros of each row
      // is a huge performance improvement, but shows some 
      // floating-point accuracy problems when working in float.
      // It's ok when working in double.
      for (i = 0; i < ncols; ++i)
        Ssq_x += sq_x[i] = (x[i] > 0);

      arg_i = 0;
      min_v = std::numeric_limits<value_type>::max();

      for (i = 0; i < nrows; ++i) {

        val = Ssq_x;
        nnzr = nzr_[i];
        ind = ind_[i];

        for (k = 0; k < nnzr; ++k) {
          j = ind[k];
          val += ((x[j] > 0) ? 0 : 1) - sq_x[j];
        }

        if (val < min_v) {
          arg_i = i;
          min_v = val;
        }
      }

      { // Post-condition
        NTA_ASSERT(min_v >= 0)
          << "SparseMatrix01::closest01(): "
          << "Negative value in post-condition";
      }

      nta::Sqrt<value_type> s;
      return std::make_pair(arg_i, s(min_v));
    }

    //--------------------------------------------------------------------------------  
    /**
     * Computes the "closest-dot" distance between vector x
     * and each row in this SparseMatrix01. Returns the index of 
     * the row that maximizes the dot product as well as the 
     * value of this dot-product.
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InIter<value_type>] vector to compute the distance from
     * @retval [std::pair<size_type, value_type>] index of the row closest
     *  to x, and value of the distance between x and that row
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InIter>
    inline std::pair<size_type, value_type> closestDot(InIter x) const
    {
      size_type i, k, arg_i, nnzr, *ind, end, nrows = nRows();
      value_type val, max_v; 
      
      // cache prod of the nz? 
      // compute prod of all the x only once?
      
      arg_i = 0;
      max_v = - std::numeric_limits<value_type>::max();

      for (i = 0; i < nrows; ++i) {

        val = 0;
        nnzr = nzr_[i];
        ind = ind_[i];
        end = 4 * (nnzr / 4);

        for (k = 0; k < end; k += 4) 
          val +=  x[ind[k]] + x[ind[k+1]] + x[ind[k+2]] + x[ind[k+3]];

        for (k = end; k < nnzr; ++k)
          val += x[ind[k]];

        if (val > max_v) {
          arg_i = i;
          max_v = val;
        }
      }

      return std::make_pair(arg_i, max_v);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of vector x by this SparseMatrix01
     * on the right side, and puts the result in vector y.
     * 
     * Non-mutating, O(nnz)
     *
     * @param x [InIter<value_type>] input vector
     * @param y [OutIter<value_type>] result of the multiplication
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InIter, typename OutIter>
    inline void rightVecProd(InIter x, OutIter y) const
    {
      size_type i, nnzr, *ind, *end1, *end2, nrows = nRows();
      value_type val, a, b;

      //memcpy(nzb_, &*x, nCols()*sizeof(value_type));

      for (i = 0; i < nrows; ++i, ++y) { 

        val = 0;
        nnzr = nzr_[i]; 
        ind = ind_[i];
        end1 = ind + 4*(nnzr/4);
        end2 = ind + nnzr;
      
        while (ind != end1) {
          a = x[*ind++];
          b = x[*ind++];
          val += a + b;
          a = x[*ind++];
          b = x[*ind++];
          val += a + b;
        }

        while (ind != end2) 
          val += x[*ind++];
      
        *y = val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the max prod between each element of vector x
     * and each non-zero of each row of this SparseMatrix01.
     * Puts the max for each row in vector y.
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InIter<value_type>] input vector
     * @param y [OutIter<value_type>] result 
     * 
     * @b Exceptions:
     *  @li None
     */
    template<typename InIter, typename OutIter>
    inline void vecMaxProd(InIter x, OutIter y) const
    {
      size_type i, *ind, *ind_end, nrows = nRows();
      value_type max_v, p;

      //memcpy(nzb_, &*x, nCols()*sizeof(value_type));
      
      for (i = 0; i < nrows; ++i, ++y) {

        ind = ind_[i];
        ind_end = ind + nzr_[i]; 
        max_v = 0; //nnzr == 0 ? 0 : x[ind[0]];

        while (ind != ind_end) {
          p = x[*ind++];
          if (p > max_v) 
            max_v = p; 
        }
        
        *y = max_v;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the index of the max value of x, where that 
     * value is at the index of a non-zero. Does that for each
     * row, stores the resulting index in y for each row.
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InIter<value_type>] input vector
     * @param y [OutIter<value_type>] output vector
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InIter, typename OutIter>
    inline void rowMax(InIter x, OutIter y) const
    {
      size_type i, j, nnzr, *ind, *end, arg_j, nrows = nRows();
      value_type val, max_val;

      for (arg_j = 0, i = 0; i < nrows; ++i, ++y) {

        nnzr = nzr_[i];
        ind = ind_[i];
        end = ind + nnzr;
      
        max_val = 0; //- std::numeric_limits<value_type>::max();

        while (ind != end) {
          j = *ind;
          val = x[j];
          if (val > max_val) {
            arg_j = j;
            max_val = val;
          }
          ++ind;
        }
        *y = value_type(arg_j);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of the values in x corresponding to the non-zeros 
     * for each row.
     * Stores the result in y.
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InIter<value_type>] input vector
     * @param y [OutIter<value_type>] output vector
     * 
     * @b Exceptions:
     *  @li None
     */
    template <typename InIter, typename OutIter>
    inline void rowProd(InIter x, OutIter y) const
    {
      size_type i, *end1, *end2, nnzr, *ind, nrows = nRows();
      value_type val, a, b;

      // Pre-fetch x into nzb_ to minimize cache misses
      // Also, copying x into nzb_ on the stack frees a register
      // that can be used below for a and b
      //memcpy(nzb_, &*x, nCols()*sizeof(value_type));

      for (i = 0; i < nrows; ++i, ++y) {
      
        nnzr = nzr_[i];
        ind = ind_[i];

        end1 = ind + 4*(nnzr/4);
        end2 = ind + nnzr;

        val = 1.0;

        // Using a and b to use more registers
        while (ind != end1) { // != faster than ind < end1
          a = x[*ind++];
          b = x[*ind++];
          val *= a * b;
          a = x[*ind++];
          b = x[*ind++];
          val *= a * b;
        }

        while (ind != end2)
          val *= x[*ind++];

        *y = val;
      }

      /*
        for (k = 0; k < end1; k += 4)
        val *= x[ind[k]] * x[ind[k+1]] * x[ind[k+2]] * x[ind[k+3]];
        
        for (k = end1; k < nnzr; ++k)
        val *= x[ind[k]];
      */

      /* Slow
         while (ind < end1) {
         val *= x[*ind]; ++ind;
         val *= x[*ind]; ++ind;
         val *= x[*ind]; ++ind;
         val *= x[*ind]; ++ind;
         }
      */
      
      /* 30% faster, but wrong result, because of order
         while (ind < end1) 
         val *= x[*ind++] * x[*ind++] * x[*ind++] * x[*ind++];
      */
    }

    //--------------------------------------------------------------------------------
    /**
     * This is used in prediction to clamp the results to lb in case of underflow.
     */
    template <typename InIter, typename OutIter>
    inline void rowProd(InIter x, OutIter y, const value_type& lb) const
    {
      size_type i, k, nnzr, end, *ind, nrows = nRows();
      double val;

      for (i = 0; i < nrows; ++i) {
      
        nnzr = nzr_[i];
        ind = ind_[i];
        val = 1;
        end = 4*(nnzr / 4);
      
        k = 0;
        while (k < end && val > lb) {
          val *= x[ind[k]] * x[ind[k+1]] * x[ind[k+2]] * x[ind[k+3]];
          k += 4;
        }
      
        if (val > lb)
          for (k = end; k < nnzr; ++k)
            val *= x[ind[k]];
      
        if (val > lb)
          *y++ = (value_type) val;  
        else
          *y++ = lb;
      }
    }

    //--------------------------------------------------------------------------------
    inline void print(std::ostream& outStream) const
    {
      size_type i, j, k;
      for (i = 0; i < nRows(); ++i) {
        if (nzr_[i] > 0) {
          for (j = 0, k = 0; j < nCols(); ++j) {
            if (k < nzr_[i] && ind_[i][k] == j) {
              outStream << "1 ";
              ++k;
            } else {
              outStream << "0 ";
            }
          }
        }
        outStream << std::endl;
      }
    }
  };

  //--------------------------------------------------------------------------------
  template <typename I, typename F>
  inline std::ostream& operator<<(std::ostream& outStream, 
				  const SparseMatrix01<I, F>& A)
  {
    A.print(outStream);
    return outStream;
  }

  //--------------------------------------------------------------------------------

} // end namespace nta

#endif // NTA_SPARSE_MATRIX01_HPP

