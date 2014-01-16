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
 * Definition and implementation for SparseMatrix class
 */

#ifndef NTA_SPARSE_MATRIX_HPP
#define NTA_SPARSE_MATRIX_HPP

//----------------------------------------------------------------------

#include <iomanip>
#include <cstdio> // sprintf
#include <boost/unordered_set.hpp>

#include <nta/math/utils.hpp>
#include <nta/ntypes/MemParser.hpp>
#include <nta/ntypes/MemStream.hpp>

#include <nta/math/math.hpp>
#include <nta/math/array_algo.hpp>
#include <nta/math/stl_io.hpp>

//--------------------------------------------------------------------------------

namespace nta {

  struct SparseMatrixAlgorithms;

  //--------------------------------------------------------------------------------
  /**
   * @b Responsibility:
   *  A sparse matrix class dedicated to supporting Numenta's algorithms.
   *  This is not a general purpose sparse matrix. It's tuned primarily
   *  to support Numenta's algorithms.
   *
   * @b Rationale:
   *  It is not a fully general sparse matrix class. Instead, it is intended
   *  to support Numenta's algorithms as efficiently as possible.
   *  SparseMatrix is optimized for speed. Therefore argument checks for its
   *  members are performed as asserts that are compiled out in the optimized
   *  builds. Similarly, the Python wrapper for SparseMatrix does not contain
   *  argument checks, that would also slow down the code.
   *
   * @b Resource/Ownerships:
   *  This class manages its own memory.
   *
   * @b Invariants:
   *  1. Values of non-zeros are > nta::Epsilon.
   *  2. Indices of non-zeros in any row are unique.
   *  3. Indices of non-zeros in any row are sorted in increasing order.
   *
   * @b Notes:
   *  Note 1: SparseMatrix has a limitation to max<unsigned long> columns, or
   *   rows or non-zeros.
   *  Note 3: Non-zeros are stored in increasing order of indices on the rows
   *
   */

  /*
   * Implementation notes:
   * ====================
   * SparseMatrix does lots of memory manipulations. It has two "modes":
   * - in compact mode, all the rows are allocated in two blocks of memory,
   * one for the indices of the non-zeros, and one for the values of those
   * non-zeros. Those blocks are stored at ind_[0] and nz_[0].
   * - in non-compact mode, the rows are allocated separately, and pointers
   * to their memory are stored in ind_[i] and nz_[i].
   * The compact mode makes computations faster by avoiding cache misses.
   * The non-compact mode is needed when modifying the numbers of non-zeros
   * on a row: if memory was allocated for 4 non-zeros, and a lerp operation
   * introduces a new non-zero, we need to allocated more space, and that
   * wouldn't work in compact mode.
   * 1. nnzr_ is used as a indicator of whether memory has been allocated for a row
   * or not. If nnzr_[i] == 0, NEVER access ind_[i] or nz_[i], they might not
   * even be initialized.
   * 2. When compact, ind_[0] and nz_[0] point to the memory allocated for the whole
   * matrix, and ind_[i]/nz_[i] point *inside* that memory, so they don't need
   * to be de-allocated one by one.
   * When not compact,  each ind_[i]/nz_[i] points to its, separately allocated
   * chunk of memory, and needs to be de-allocated separately.
   * 3. nrows_max_ controls the allocation of nnzr_, ind_ and nz_, but not of the
   * rows themselves. We can't pre-allocated memory for rows, since that would
   * be wasteful.
   * 4. Real_stor is distinguished from Real_prec so that we can carry out
   * computations in double, but store only floats: it works better to avoid
   * propagation of small errors, and it makes a difference on some platforms.
   * Typically, we can compute the intermediate results in double for a dot
   * product between a row stored in float and a vector in float, and store
   * the final result in float rather than double to save space.
   */
  template <typename UI        =nta::UInt32,
            typename Real_stor =nta::Real32,
            typename I         =nta::Int32,
            typename Real_prec =nta::Real64,
            typename DTZ       =nta::DistanceToZero<Real_stor> >
  class SparseMatrix
  {
    // TODO find boost config flag to enable ullong as UnsignedInteger
    //BOOST_CLASS_REQUIRE(UI, boost, UnsignedIntegerConcept);
    BOOST_CLASS_REQUIRE(I, boost, SignedIntegerConcept);

  public:
    typedef UI        size_type;       // unsigned integral for sizes
    typedef I         difference_type; // signed integral for differences
    typedef Real_stor value_type;      // floating-point storage type
    typedef Real_prec prec_value_type; // floating-point precision type

    typedef SparseMatrix<UI, Real_stor, I, Real_prec, DTZ> self_type;

    typedef const size_type* const_row_nz_index_iterator;
    typedef const value_type* const_row_nz_value_iterator;

    typedef size_type* row_nz_index_iterator;
    typedef value_type* row_nz_value_iterator;

    typedef ijv<size_type, value_type> IJV;

  protected:
    size_type nrows_;          // number of rows
    size_type nrows_max_;      // max size of nnzr_, ind_ and nz_
    size_type ncols_;          // number of columns
    size_type *nnzr_;          // number of non-zeros on each row
    size_type *ind_mem_;       // memory of indices when compact
    value_type *nz_mem_;       // memory of values when compact
    size_type **ind_;          // indices of non-zeros on each row
    value_type **nz_;          // values of non-zeros on each row
    //size_type *row_alloc_;
    size_type *indb_;          // buffer for indices of non-zeros
    value_type *nzb_;          // buffer for values of non-zeros
    IsNearlyZero<DTZ> isZero_; // test for zero/non-zero

    friend struct SparseMatrixAlgorithms;

    //--------------------------------------------------------------------------------
    // Macros
    //--------------------------------------------------------------------------------

    /**
     * These macros make code a lot more readable and streamline common tasks.
     */

    // Iterate on all rows, the row index is 'row'
#define ITERATE_ON_ALL_ROWS                             \
    const size_type nrows = nRows();                    \
    for (size_type row = 0; row != nrows; ++row)

    // Iterate on a single row, with two pointers: 'ind' and 'nz'
#define ITERATE_ON_ROW                                          \
    size_type *ind = ind_begin_(row), *ind_end = ind_end_(row); \
    value_type *nz = nz_begin_(row);                            \
    for (; ind != ind_end; ++ind, ++nz)

    // Iterate on all cols, the col index is 'col'
#define ITERATE_ON_ALL_COLS                             \
    const size_type ncols = nCols();                    \
    for (size_type col = 0; col != ncols; ++col)

    // Iterate on all the rows inside [begin_row, end_row)
#define ITERATE_ON_BOX_ROWS                                     \
    for (size_type row = begin_row; row != end_row; ++row)

    // Iterate on all the columns inside [begin_col end_col)
#define ITERATE_ON_BOX_COLS                                             \
    size_type *ind = NULL, *ind_end = NULL;                             \
    value_type *nz = nz_begin_(row) + pos_(row, begin_col, end_col, ind, ind_end); \
    for (; ind != ind_end; ++ind, ++nz)

    //--------------------------------------------------------------------------------
    // ASSERTS
    //--------------------------------------------------------------------------------

    /**
     * These common asserts also make the code more streamlined and more readable.
     */
    inline void assert_not_zero_value_(const value_type& val, const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON
      NTA_ASSERT(!isZero_(val))
        << "SparseMatrix " << where << ": Zero value should be != 0";
#endif
    }

    inline void assert_valid_row_(size_type row, const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON
      NTA_ASSERT(row >= 0 && row < nRows())
        << "SparseMatrix " << where
        << ": Invalid row index: " << row
        << " - Should be >= 0 and < " << nRows();
#endif
    }

    inline void assert_valid_col_(size_type col, const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON
      NTA_ASSERT(col >= 0 && col < nCols())
        << "SparseMatrix " << where
        << ": Invalid col index: " << col
        << " - Should be >= 0 and < " << nCols();
#endif
    }

    inline void assert_valid_row_col_(size_type row, size_type col,
                                      const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_row_(row, where);
      assert_valid_col_(col, where);
#endif
    }

    inline void assert_valid_row_ptr_(size_type row, size_type* ptr,
                                      const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON
      NTA_ASSERT(ind_begin_(row) <= ptr && ptr <= ind_end_(row))
        << "SparseMatrix " << where
        << ": Invalid row pointer";
#endif
    }

    inline void assert_valid_row_range_(size_type row_begin, size_type row_end,
                                        const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_row_(row_begin, where);
      if (row_begin < row_end)
        assert_valid_row_(row_end-1, where);
      NTA_ASSERT(row_begin <= row_end)
        << "SparseMatrix " << where
        << ": Invalid row range: [" << row_begin
        << ".." << row_end << "): "
        << "- Beginning should be <= end of range";
#endif
    }

    inline void assert_valid_col_range_(size_type col_begin, size_type col_end,
                                        const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_col_(col_begin, where);
      if (col_begin < col_end)
        assert_valid_col_(col_end-1, where);
      NTA_ASSERT(col_begin <= col_end)
        << "SparseMatrix " << where
        << ": Invalid col range: [" << col_begin
        << ".." << col_end << "): "
        << "- Beginning should be <= end of range";
#endif
    }

    inline void assert_valid_box_(size_type row_begin, size_type row_end,
                                  size_type col_begin, size_type col_end,
                                  const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_row_range_(row_begin, row_end, where);
      assert_valid_col_range_(col_begin, col_end, where);
#endif
    }

    template <typename It>
    inline void assert_valid_row_it_range_(It begin, It end, const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON
      // Could be input or output iterator
      ASSERT_VALID_RANGE(begin, end, where);
      while (begin != end) {
        assert_valid_row_(*begin, where);
        ++begin;
      }
#endif
    }

    template <typename It>
    inline void assert_valid_col_it_range_(It begin, It end, const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON
      // Could be input or output iterator
      ASSERT_VALID_RANGE(begin, end, where);
      while (begin != end) {
        assert_valid_col_(*begin, where);
        ++begin;
      }
#endif
    }

    template <typename InputIterator1>
    inline void
    assert_valid_sorted_index_range_(size_type m,
                                     InputIterator1 ind_it, InputIterator1 ind_end,
                                     const char* where) const
    {
#ifdef NTA_ASSERTIONS_ON

      ASSERT_INPUT_ITERATOR(InputIterator1);

      NTA_ASSERT(ind_end - ind_it >= 0)
        << "SparseMatrix " << where << ": Invalid iterators";

      for (size_type j = 0, prev = 0; ind_it != ind_end; ++ind_it, ++j) {

        size_type index = *ind_it;

        NTA_ASSERT(0 <= index && index < m)
          << "SparseMatrix " << where
          << ": Invalid index: " << index
          << " - Should be >= 0 and < " << m;

        if (j > 0) {
          NTA_ASSERT(prev < index)
            << "SparseMatrix " << where
            << ": Indices need to be in strictly increasing order"
            << " without duplicates, found: " << prev
            << " and " << index;
        }

        prev = index;
      }
#endif
    }

    template <typename InputIterator1, typename InputIterator2>
    inline void
    assert_valid_ivp_range_(size_type m,
                            InputIterator1 ind_it, InputIterator1 ind_end,
                            InputIterator2 nz_it,
                            const char* where) const
    {

#ifdef NTA_ASSERTIONS_ON

      ASSERT_INPUT_ITERATOR(InputIterator1);
      ASSERT_INPUT_ITERATOR(InputIterator2);

      NTA_ASSERT(ind_end - ind_it >= 0)
        << "SparseMatrix " << where << ": Invalid iterators";

      for (size_type j = 0, prev = 0; ind_it != ind_end; ++ind_it, ++nz_it, ++j) {

        size_type index = *ind_it;

        NTA_ASSERT(0 <= index && index < m)
          << "SparseMatrix " << where
          << ": Invalid index: " << index
          << " - Should be >= 0 and < " << m;

        NTA_ASSERT(!isZero_(*nz_it))
          << "SparseMatrix " << where
          << ": Passed zero at index: " << j
          << " - Should pass non-zeros only";

        if (j > 0) {
          NTA_ASSERT(prev < index)
            << "SparseMatrix " << where
            << ": Indices need to be in strictly increasing order"
            << " without duplicates, found: " << prev
            << " and " << index;
        }

        prev = index;
      }
#endif
    }

    //--------------------------------------------------------------------------------
    // PROTECTED METHODS
    //--------------------------------------------------------------------------------

    //--------------------------------------------------------------------------------
    inline void invariants() const
    {
      const char* where = "SparseMatrix::invariants: ";

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          NTA_ASSERT(!isZero_(*nz))
            << where
            << "Near zero value: " << *nz
            << " at (" << row << ", " << *ind << ") "
            << "nta::Epsilon= " << nta::Epsilon;
          NTA_ASSERT(row < nRows())
            << where
            << "Invalid row index: " << row
            << " nRows= " << nRows();
          NTA_ASSERT(*ind < nCols())
            << where
            << "Invalid col index: " << *ind
            << " nCols= " << nCols();
        }

        assert_valid_sorted_index_range_(nCols(), ind_begin_(row), ind_end_(row), where);
      }

      //assert(nnzr_ && ind_ && nz_ && indb_ && nzb_);
      //assert(nrows_max_ >= nrows_);

      //for (size_type i = nrows_; i < nrows_max_; ++i)
      //assert(ind_[i] == 0 && nz_[i] == 0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Reallocates the internal indb_ and nzb_ buffers, which have the same size
     * as the number of columns. They are good for row operations only.
     *
     * @param ncols [0 <= size_type] the new number of columns to use to allocate
     *  the buffers
     *
     * @b Complexity:
     *  @li O(2*ncols) + memory allocation
     *
     * @b Exceptions:
     *  @li If ncols < 0 (assert)
     *
     * TODO: remove initialization of buffers
     */
    inline void reAllocateBuffers_(size_type ncols)
    {
      { // Pre-conditions
        NTA_ASSERT(0 <= ncols)
          << "SparseMatrix reAllocateBuffers_: "
          << "Bad ncols: " << ncols;
      } // End pre-conditions

      delete [] indb_;
      delete [] nzb_;

      indb_ = new size_type[ncols];
      nzb_ = new value_type[ncols];

      //std::fill(indb_, indb_ + ncols, (size_type)0);
      //std::fill(nzb_, nzb_ + ncols, (value_type)0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Allocates data structures of the SparseMatrix. This method in fact
     * allocates only nnzr_, ind_ and nz_, but not the contents of the rows
     * themselves. These need to be allocated separately. Also allocates
     * internal buffers.
     *
     * @param nrows_max [0 <= size_type] max number of rows to allocate
     * @param ncols [0 <= size_type] number of columns for this matrix
     *
     * @b Complexity:
     *  @li O(3*nrows_max + 2*ncols) + memory allocation
     *
     * @b Exceptions:
     *  @li If nrows_max < 0 or ncols < 0 (assert)
     *
     * TODO: allocate max of nrows,ncols for buffers
     * TODO: remove initialization of buffers
     */
    inline void allocate_(size_type nrows_max, size_type ncols)
    {
      { // Pre-conditions
        NTA_ASSERT(0 <= nrows_max)
          << "SparseMatrix allocate_: Bad nrows_max: " << nrows_max;
        NTA_ASSERT(0 <= ncols)
          << "SparseMatrix allocate_: Bad ncols: " << ncols;
      } // End pre-conditions

      nrows_max_ = std::max<size_type>(8, nrows_max);

      nnzr_ = new size_type [nrows_max_];
      ind_ = new size_type* [nrows_max_];
      nz_ = new value_type* [nrows_max_];

      std::fill(nnzr_, nnzr_ + nrows_max_, (size_type)0);
      std::fill(ind_, ind_ + nrows_max_, (size_type*)0);
      std::fill(nz_, nz_ + nrows_max_, (value_type*)0);

      indb_ = new size_type [ncols];
      nzb_ = new value_type [ncols];
    }

    //--------------------------------------------------------------------------------
    /**
     * Deallocates data structures of the SparseMatrix.
     *
     * Can be called multiple times.
     * Sets ncols_, nrows_ and nrows_max_ to 0.
     * nnzr_ indicates whether memory has been allocated for
     * the rows or not, when not compact. When compact,
     * all the memory is allocated in one block.
     *
     * @b Complexity:
     *  @li Worst case: O(nrows) if not compact
     *  @li Best case: O(1) if compact
     *
     * @b Exceptions:
     *  @li None.
     */
    inline void deallocate_()
    {
      if (isCompact()) {
        // when compact, the memory is
        // all deallocated from ind_mem_ and nz_mem_
        delete [] ind_mem_;
        delete [] nz_mem_;

        ind_mem_ = 0;
        nz_mem_ = 0;

      } else {

        ITERATE_ON_ALL_ROWS {

          delete [] ind_[row];  // when not compact, we deallocate
          delete [] nz_[row];   // each row separately

          ind_[row] = 0;
          nz_[row] = 0;
        }
      }

      delete [] ind_;
      ind_ = 0;
      delete [] nz_;
      nz_ = 0;
      delete [] nnzr_;
      nnzr_ = 0;
      delete [] indb_;
      indb_ = 0;
      delete [] nzb_;
      nzb_ = 0;

      nrows_ = ncols_ = nrows_max_ = 0;
    }

    //--------------------------------------------------------------------------------
    /**
     * Reserve enough memory for new_nrow rows.
     *
     * @param new_nrow [0 <= size_type] the desired new number of rows
     *
     * @b Complexity:
     *  @li Worst case: O(6*new_nrow) if new_nrow > nrows_max_ - 1
     *  @li Average: amortized, if new_nrow <= nrows_max_ - 1
     *
     * @b Exceptions:
     *  @li If new_nrow < 0 (assert)
     */
    inline void reserve_(size_type new_nrow)
    {
      { // Pre-conditions
        NTA_ASSERT(0 <= new_nrow)
          << "SparseMatrix reserve_: Bad new number of rows: " << new_nrow;
      } // End pre-conditions

      if (new_nrow > nrows_max_-1) {

        nrows_max_ = std::max<size_type>(2 * nrows_max_, new_nrow);

        size_type *nnzr_new = new size_type[nrows_max_];
        size_type **ind_new = new size_type*[nrows_max_];
        value_type **nz_new = new value_type*[nrows_max_];

        std::copy(nnzr_, nnzr_ + nrows_, nnzr_new);
        std::copy(ind_, ind_ + nrows_, ind_new);
        std::copy(nz_, nz_ + nrows_, nz_new);

        std::fill(nnzr_new + nrows_, nnzr_new + nrows_max_, (size_type)0);
        std::fill(ind_new + nrows_, ind_new + nrows_max_, (size_type*)0);
        std::fill(nz_new + nrows_, nz_new + nrows_max_, (value_type*)0);

        delete [] nnzr_;
        delete [] ind_;
        delete [] nz_;

        nnzr_ = nnzr_new;
        ind_ = ind_new;
        nz_ = nz_new;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Compacts a row from a buffer to (nzr_[r], ind_[r], nz_[r]).
     * This will weed out the zeros in the buffer, if any, and keep
     * the non-zeros sorted in increasing order of indices.
     *
     * @param row [0 < size_type <= nrows] the row to set
     * @param nz_begin [InputIterator] iterator to beginning of range
     *  containing non-zero values
     * @param nz_end [InputIterator] iterator to one past the end of range
     *  containing non-zero values
     *
     * @b Complexity:
     *  @li O(4*nnzr)
     *
     * @b Exceptions:
     *  @li If r < 0 || r >= nrows (assert)
     *  @li If nz_end < nz_begin: range empty or invalid (assert)
     *  @li If ncols < nz_end - nz_begin (assert)
     *  @li Not enough memory (error)
     */
    template <typename InputIterator>
    inline void set_row_(size_type row, InputIterator nz_begin, InputIterator nz_end)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);

        assert_valid_row_(row, "set_row_");

        NTA_ASSERT(nz_begin <= nz_end)
          << "SparseMatrix set_row_: Invalid or empty input range";

        NTA_ASSERT((size_type)(nz_end - nz_begin) <= nCols())
          << "SparseMatrix set_row_: Range too large, has: "
          << (size_type)(nz_end - nz_begin) << " elements "
          << " - Should be less than number of columns: " << nCols();
      } // End pre-conditions

      size_type *indb_it = indb_;
      InputIterator nz_it = nz_begin;
      value_type* nzb_it = nzb_;

      // First, compact row in place in indb_, nzb_,
      // and figure out number of non-zeros
      // Keep increasing order of non-zero indices
      // Non-zeros might move, or change in number
      while (nz_it != nz_end) {
        value_type val = *nz_it;
        if (!isZero_(val)) {
          *indb_it = size_type(nz_it - nz_begin);
          *nzb_it = val;
          ++indb_it; ++nzb_it;
        }
        ++nz_it;
      }

      size_type nnzr = size_type(indb_it - indb_);

      if (nnzr > nnzr_[row]) {

        // There are more non-zeros than we have allocated
        // memory for, so we need to de-compact the storage
        // (changes ind_[r] and nz_[r] but not nnzr_[r])
        if (isCompact())
          decompact();

        delete [] ind_[row];
        delete [] nz_[row];

        ind_[row] = new size_type[nnzr];
        nz_[row] = new value_type[nnzr];
      }

      nnzr_[row] = nnzr;
      std::copy(indb_, indb_ + nnzr, ind_[row]);
      std::copy(nzb_, nzb_ + nnzr, nz_[row]);
    }

    //--------------------------------------------------------------------------------
    /**
     * Decompacts a row to nzb_ buffer.
     *
     * @param row [0 <= size_type < nrows] the row to transfer to nzb_
     *
     * @b Complexity:
     *  @li O(ncols + nnzr)
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     */
    inline void to_nzb_(size_type row)
    {
      { // Pre-conditions
        assert_valid_row_(row, "to_nzb_");
      } // End pre-conditions

      std::fill(nzb_, nzb_ + nCols(), (value_type)0);

      size_type *ind = ind_begin_(row), *ind_end = ind_end_(row);
      value_type *nz = nz_begin_(row);

      for (; ind != ind_end; ++ind, ++nz)
        *(nzb_ + *ind) = *nz;
    }

    //--------------------------------------------------------------------------------
    /**
     * Erases the non-zero at ind_it on the given row.
     * Copies the row on [ind_it + 1..end) to [ind_it..end-1), erasing
     * the value at ind_it, without decompacting the storage.
     * It leaves zeros at the end of the row, that can be eliminated with
     * a further call to compact().
     *
     * @param row [0 <= size_type < nrows] the row on which to erase
     * @param ind_it [size_type* != NULL] pointer to the beginning of the range
     *  to erase
     *
     * @b Complexity:
     *  @li Worst case: O(2*nnzr)
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     *  @li If ind_it not valid pointer on row (assert)
     *  @li If nnzr_[row] == 0 (assert)
     */
    inline void erase_(size_type row, size_type *ind_it)
    {
      { // Pre-conditions
        assert_valid_row_(row, "erase_");
        assert_valid_row_ptr_(row, ind_it, "erase_");
        NTA_ASSERT(nnzr_[row] > 0)
          << "SparseMatrix erase_: Empty row #" << row;
      } // End pre-conditions

      value_type *nz_it = nz_begin_(row) + (ind_it - ind_begin_(row));

      std::copy(ind_it + 1, ind_end_(row), ind_it);
      std::copy(nz_it + 1, nz_end_(row), nz_it);

      -- nnzr_[row];
    }

    //--------------------------------------------------------------------------------
    /**
     * Internal functions that allow to separate the internal storage
     * from the rest of the code, in case we would need to change that internal
     * storage. Also allows to do more tests, in case the arguments would be out
     * of range. Better to not use them unless you really know what you are doing
     * and are sure that you are not violating the assumptions SparseMatrix relies on
     * (non-zeros are > nta::Epsilon, unique, and sorted always).
     */
    inline size_type* ind_begin_(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "ind_begin_");
      } // End pre-conditions

      return ind_[row];
    }

    inline size_type* ind_end_(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "ind_end_");
      } // End pre-conditions

      return ind_[row] + nnzr_[row];
    }

    inline value_type* nz_begin_(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "nz_begin_");
      } // End pre-conditions

      return nz_[row];
    }

    inline value_type* nz_end_(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "nz_end_");
      } // End pre-conditions

      return nz_[row] + nnzr_[row];
    }

    inline size_type index_(size_type row, size_type offset) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "index_");
        NTA_ASSERT(0 <= offset && offset < nnzr_[row])
          << "SparseMatrix index_: "
          << "Invalid offset value: " << offset
          << " - Should be in [0.." << nnzr_[row] << ") "
          << "for row: " << row;
      } // End pre-conditions

      return ind_[row][offset];
    }

    inline value_type value_(size_type row, size_type offset) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "value_");
        NTA_ASSERT(0 <= offset && offset < nnzr_[row])
          << "SparseMatrix value_: "
          << "Invalid offset value: " << offset
          << " - Should be in [0.." << nnzr_[row] << ") "
          << "for row: " << row;
      } // End pre-conditions

      return nz_[row][offset];
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the position of the given column in the given row, using
     * a binary search, if (row, col) is a non-zero, or the position
     * where an element for col should be inserted on that row.
     *
     * @param row [0 <= size_type < nrows] the index of the row to search
     * @param col [0 <= size_type < ncols] the index of the column to find
     * @retval [size_type*] pointer to the non-zero if present,
     *  or pointer to the position where a non-zero for that col
     *  should be inserted
     *
     * @b Complexity:
     *  @li Worst case: O(log(nnzr))
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     *  @li If col < 0 || col >= ncols (assert)
     */
    inline size_type* pos_(size_type row, size_type col) const
    {
      { // Pre-conditions
        assert_valid_row_col_(row, col, "pos_");
      } // End pre-conditions

      return std::lower_bound(ind_begin_(row), ind_end_(row), col);
    }

    //--------------------------------------------------------------------------------
    /**
     * For a given row, and a given [begin, end) interval of column indices,
     * sets two pointers corresponding to [begin, end) and returns the offset
     * corresponding to begin on that row. This is useful when iterating on
     * the columns of a box of matrix indices.
     *
     * @param row [0 <= size_type < nrows] the index of the row to search
     * @param col [0 <= size_type <= ncols] the index of the column to find
     *
     * @b Complexity:
     *  @li Worst case: O(2*log(nnzr))
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     *  @li If col < 0 || col > ncols (assert)
     */
    inline difference_type pos_(size_type row, size_type begin, size_type end,
                                size_type*& begin_ptr, size_type*& end_ptr) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "pos_ 2");
        assert_valid_col_range_(begin, end, "pos_ 2");
      } // End pre-conditions

      size_type *b = ind_begin_(row), *e = ind_end_(row);

      begin_ptr = std::lower_bound(b, e, begin);
      end_ptr = end == nCols() ? e : std::lower_bound(begin_ptr, e, end);

      return (difference_type)(begin_ptr - b);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the offset of the element at (row, col) if it is a non-zero,
     * or -1 if (row, col) is a zero.
     *
     * @param row [0 <= size_type < nrows] the index of the row to search
     * @param col [0 <= size_type < ncols] the index of the column to find
     * @retval [difference_type] the offset of (row, col) if it's a non-zero
     *  or -1 otherwise
     *
     * @b Complexity:
     *  @li Worst case: O(log(nnzr))
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     *  @li If col < 0 || col >= ncols (assert)
     */
    inline difference_type col_(size_type row, size_type col) const
    {
      { // Pre-conditions
        assert_valid_row_col_(row, col, "col_");
      } // End pre-conditions

      const size_type *begin = ind_begin_(row), *end = ind_end_(row);
      const size_type *where = std::lower_bound(begin, end, col);

      if (where != end && *where == col)
        return difference_type(where - begin);
      else
        return difference_type(-1);
    }

    //--------------------------------------------------------------------------------
    /**
     * Given a row and a hint, inserts the value at the given hint on the row.
     * Works only if the value passed is a non-zero, and if the position
     * at which that non-zero will be inserted was a zero previously.
     *
     * @param row [0 <= size_type < nrows] the row on which to insert
     * @param col [0 <= size_type < ncols] the col on which to insert
     * @param hint [size_type*] a hint for the insertion
     * @param val [value_type != 0] the non-zero value to insert
     *
     * @b Complexity:
     *  @li Worst case: O(nnz + 4*nnzr) (if need to decompact)
     *  @li Average case: O(4*nnzr) (if already non-compact)
     *
     * @b Exceptions:
     *  @li If (i,j) not valid (row,col) (assert)
     *  @li If hint not valid pointer for given row (assert)
     *  @li If val is zero
     *  @li If this[i,j] is not zero
     */
    inline void insertNewNonZero_(size_type i, size_type j,
                                  size_type *hint, const value_type& val)
    {
      { // Pre-conditions
        assert_valid_row_col_(i, j, "insertNewNonZero_");
        assert_valid_row_ptr_(i, hint, "insertNewNonZero_");
        assert_not_zero_value_(val, "insertNewNonZero_");
        NTA_ASSERT(isZero_(get(i,j)))
          << "SparseMatrix: Can't call insertNewNonZero_ when element "
          << "at that position is not a zero";
      } // End pre-conditions

      size_type *ind = ind_begin_(i), *ind_end = ind_end_(i), *indb = indb_;
      value_type* nz = nz_begin_(i), *nzb = nzb_;

      while (ind != hint) {
        *indb = *ind;
        *nzb = *nz;
        ++ind; ++nz;
        ++indb; ++nzb;
      }

      *indb = j;
      *nzb = val;
      ++indb; ++nzb;

      while (ind != ind_end) {
        *indb = *ind;
        *nzb = *nz;
        ++ind; ++nz;
        ++indb; ++nzb;
      }

      if (isCompact())
        decompact();

      delete [] ind_[i];
      delete [] nz_[i];

      nnzr_[i] += 1;
      ind_[i] = new size_type [nnzr_[i]];
      nz_[i] = new value_type [nnzr_[i]];
      std::copy(indb_, indb_ + nnzr_[i], ind_[i]);
      std::copy(nzb_, nzb_ + nnzr_[i], nz_[i]);
    }

  public:
    //--------------------------------------------------------------------------------
    // CONSTRUCTORS
    //--------------------------------------------------------------------------------

    /**
     * Default constructor, creates an empty matrix with no rows and no columns.
     */
    inline SparseMatrix()
      : nrows_(0), nrows_max_(0), ncols_(0),
        nnzr_(0), ind_mem_(0), nz_mem_(0),
        ind_(0), nz_(0),
        indb_(0), nzb_(0),
        isZero_()
    {
      allocate_(0,0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Constructor with a number of columns and a hint for the number
     * of rows. The SparseMatrix is empty.
     *
     * @param nrows [0 <= size_type] number of rows
     * @param ncols [0 <= size_type] number of columns
     *
     * @b Exceptions:
     *  @li If nrows < 0 (check)
     *  @li If ncols < 0 (check)
     *  @li Not enough memory (error)
     */
    inline SparseMatrix(size_type nrows, size_type ncols)
      : nrows_(0), nrows_max_(0), ncols_(0),
        nnzr_(0), ind_mem_(0), nz_mem_(0),
        ind_(0), nz_(0),
        indb_(0), nzb_(0),
        isZero_()
    {
      { // Pre-conditions
        NTA_CHECK(nrows >= 0)
          << "SparseMatrix::SparseMatrix(nrows, ncols): "
          << "Invalid number of rows: " << nrows
          << " - Should be >= 0";

        NTA_CHECK(ncols >= 0)
          << "SparseMatrix::SparseMatrix(nrows, ncols): "
          << "Invalid number of columns: " << ncols
          << " - Should be >= 0";
      } // End pre-conditions

      allocate_(nrows, ncols);
      nrows_ = nrows;
      ncols_ = ncols;
    }

    //--------------------------------------------------------------------------------
    /**
     * Constructor from a dense matrix passed as an array of value_type.
     * Uses the values in mat to initialize the SparseMatrix.
     *
     * @param nrows [0 <= size_type] number of rows
     * @param ncols [0 <= size_type] number of columns
     * @param dense [value_type** != NULL] initial array of values
     *
     * @b Complexity:
     *  @li See fromDense.
     *
     * @b Exceptions:
     *  @li If nrows <= 0 (check)
     *  @li If ncols <= 0 (check)
     *  @li If mat == NULL (check)
     *  @li If NULL pointer in mat (check)
     *  @li Not enough memory (error)
     */
    template <typename InputIterator>
    inline SparseMatrix(size_type nrows, size_type ncols, InputIterator dense)
      : nrows_(0), nrows_max_(0), ncols_(0),
        nnzr_(0), ind_mem_(0), nz_mem_(0),
        ind_(0), nz_(0),
        indb_(0), nzb_(0),
        isZero_()
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);

        NTA_CHECK(nrows >= 0)
          << "SparseMatrix::SparseMatrix(nrows, ncols, dense): "
          << "Invalid number of rows: " << nrows
          << " - Should be >= 0";

        NTA_CHECK(ncols >= 0)
          << "SparseMatrix::SparseMatrix(nrows, ncols, dense): "
          << "Invalid number of columns: " << ncols
          << " - Should be >= 0";
      } // End pre-conditions

      fromDense(nrows, ncols, dense);
    }

    //--------------------------------------------------------------------------------
    /**
     * Constructor from a stream in CSR format.
     * See fromCSR for details of the CSR format.
     *
     * @param inStream [std::istream] the input stream
     *
     * @b Complexity:
     *  @li See fromCSR.
     *
     * @b Exceptions;
     *  @li See fromCSR.
     */
    inline SparseMatrix(std::istream& inStream)
      : nrows_(0), nrows_max_(0), ncols_(0),
        nnzr_(0), ind_mem_(0), nz_mem_(0),
        ind_(0), nz_(0),
        indb_(0), nzb_(0),
        isZero_()
    {
      fromCSR(inStream);
    }

    //--------------------------------------------------------------------------------
    /**
     * Copy constructor.
     * The current state is discarded and other is copied. The dimensions and number
     * of non-zeros might change.
     *
     * @param other [SparseMatrix] the SparseMatrix to copy
     *
     * @b Complexity:
     *  @li O(2*nnz)
     *
     * @b Exceptions:
     *  @li None.
     */
    inline SparseMatrix(const SparseMatrix& other)
      : nrows_(0), nrows_max_(0), ncols_(0),
        nnzr_(0), ind_mem_(0), nz_mem_(0),
        ind_(0), nz_(0),
        indb_(0), nzb_(0),
        isZero_()
    {
      copy(other);
    }

    //--------------------------------------------------------------------------------
    /**
     * Constructs a SparseMatrix by copying some rows/cols from another one.
     * The number of rows and cols is the same as other, but only the non-zeros
     * of the specified rows/cols are copied.
     * The vector passed is a binary vector with 1 at the indices of the
     * rows/cols that need to be copied and 0 elsewhere.
     */
    template <typename InputIterator>
    inline SparseMatrix(const SparseMatrix& other,
                        InputIterator take, InputIterator take_end,
                        int rowCol =1) // cols
      : nrows_(0), nrows_max_(0), ncols_(0),
        nnzr_(0), ind_mem_(0), nz_mem_(0),
        ind_(0), nz_(0),
        indb_(0), nzb_(0),
        isZero_()
    {
      { // Pre-conditions
        NTA_ASSERT(rowCol == 0 || rowCol == 1)
          << "SparseMatrix: constructor from set of rows/cols: "
          << "Invalid flag: " << rowCol
          << " - Should be 0 for rows, or 1 for cols";
      } // End pre-conditions

      if (rowCol == 0)
        initializeWithRows(other, take, take_end);
      else if (rowCol == 1)
        initializeWithCols(other, take, take_end);
    }

    //--------------------------------------------------------------------------------
    /**
     * Deallocates this instance and initializes its non-zeros only it with the
     * non-zeros of specified rows from other. The number of rows and cols is
     * the same as other.
     * The vector passed is a binary vector with 1 at the indices of the
     * rows that need to be copied and 0 elsewhere.
     */
    template <typename InputIterator>
    inline void initializeWithRows(const SparseMatrix& other,
                                   InputIterator take, InputIterator take_end)
    {
      { // Pre-conditions
        NTA_ASSERT((size_type)(take_end - take) == other.nRows())
          << "SparseMatrix::initializeWithRows: "
          << "Wrong size for vector of indices";
      } // End pre-conditions

      deallocate_();
      allocate_(other.nRows(), other.nCols());
      nrows_ = other.nRows();
      ncols_ = other.nCols();

      for (size_type row = 0; take != take_end; ++take, ++row) {
        if (*take == 1) {
          nnzr_[row] = other.nnzr_[row];
          ind_[row] = new size_type [nnzr_[row]];
          nz_[row] = new value_type [nnzr_[row]];
          std::copy(other.ind_begin_(row), other.ind_end_(row), ind_[row]);
          std::copy(other.nz_begin_(row), other.nz_end_(row), nz_[row]);
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Deallocates this instance and initializes its non-zeros only it with the
      * non-zeros of specified cols from other. The number of rows and cols is
     * the same as other.
     * The vector passed is a binary vector with 1 at the indices of the
     * cols that need to be copied and 0 elsewhere.
     */
    template <typename InputIterator>
    inline void initializeWithCols(const SparseMatrix& other,
                                   InputIterator take, InputIterator take_end)
    {
      { // Pre-conditions
        NTA_ASSERT((size_type)(take_end - take) == other.nCols())
          << "SparseMatrix::initializeWithRows: "
          << "Wrong size for vector of indices";
      } // End pre-conditions

      deallocate_();
      allocate_(other.nRows(), other.nCols());
      nrows_ = other.nRows();
      ncols_ = other.nCols();

      for (size_type row = 0; row != nRows(); ++row) {
        size_type *o_ind = other.ind_begin_(row);
        size_type *o_ind_end = other.ind_end_(row);
        value_type *o_nz = other.nz_begin_(row);
        size_type *s_ind = other.indb_;
        value_type *s_nz = other.nzb_;
        for (; o_ind != o_ind_end; ++o_ind, ++o_nz) {
          if (take[*o_ind] == 1) {
            *s_ind++ = *o_ind;
            *s_nz++ = *o_nz;
          }
        }
        nnzr_[row] = (size_type)(s_ind - other.indb_);
        ind_[row] = new size_type [nnzr_[row]];
        nz_[row] = new value_type [nnzr_[row]];
        std::copy(other.indb_, other.indb_ + nnzr_[row], ind_[row]);
        std::copy(other.nzb_, other.nzb_ + nnzr_[row], nz_[row]);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Initialize a sparse matrix with a fixed number of non-zeros on each row.
     *
     * mode = 0 means uniform distribution of the non-zeros, all starting at 1.
     */
    inline void
    initializeWithFixedNNZR(size_type nnzr, value_type v =1,
                            size_type mode =0, size_type seed =42)
    {
      {
        NTA_ASSERT(nnzr <= nCols());
      }

      nta::Random rng(seed);

      size_type nrows = nRows(), ncols = nCols();

      deallocate_();
      allocate_(nrows, ncols);
      nrows_ = nrows;
      ncols_ = ncols;

      std::vector<size_type> col_ind(ncols);

      for (size_type c = 0; c != ncols; ++c)
        col_ind[c] = c;

      for (size_type r = 0; r != nrows; ++r) {

        std::random_shuffle(col_ind.begin(), col_ind.end(), rng);
        std::sort(col_ind.begin(), col_ind.begin() + nnzr);
        nnzr_[r] = nnzr;
        ind_[r] = new size_type [nnzr];
        std::copy(col_ind.begin(), col_ind.begin() + nnzr, ind_[r]);
        nz_[r] = new value_type [nnzr];
        std::fill(nz_[r], nz_[r] + nnzr, (value_type) v);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Assignment operator.
     * The current state is discarded and other is copied. The dimensions and number
     * of non-zeros might change.
     *
     * @param other [SparseMatrix] the SparseMatrix to copy
     *
     * @b Complexity:
     *  @li O(2*nnz)
     *
     * @b Exceptions:
     *  @li None.
     */
    inline SparseMatrix& operator=(const SparseMatrix& other)
    {
      if (this != &other)
        copy(other);
      return *this;
    }

    //--------------------------------------------------------------------------------
    /**
     * Copies the given sparse matrix into this one.
     * The current state is discarded and other is copied. The dimensions and number
     * of non-zeros might change.
     *
     * @param other [SparseMatrix] the SparseMatrix to copy
     *
     * @b Complexity:
     *  @li O(2*nnz)
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename UI2, typename R2, typename I2, typename RP2, typename DTZ2>
    inline void copy(const SparseMatrix<UI2,R2,I2,RP2,DTZ2>& other)
    {
      deallocate_();
      allocate_(2*other.nRows(), other.nCols());
      nrows_ = other.nRows();
      ncols_ = other.nCols();

      size_type nnz = other.nNonZeros();
      ind_mem_ = new size_type[nnz];
      nz_mem_ = new value_type[nnz];
      size_type *indp = ind_mem_;
      value_type *nzp = nz_mem_;

      ITERATE_ON_ALL_ROWS {
        nnz = other.nNonZerosOnRow(row);
        nnzr_[row] = nnz;
        ind_[row] = indp;
        nz_[row] = nzp;
        std::copy(other.row_nz_index_begin(row), other.row_nz_index_end(row), indp);
        std::copy(other.row_nz_value_begin(row), other.row_nz_value_end(row), nzp);
        indp += nnz;
        nzp += nnz;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Destructor.
     * Internal data structures are freed. Pointers and data members are set to 0.
     *
     * @b Complexity:
     *  @li Worst case: O(nrows) if not compact
     *  @li Best case: O(1) if compact
     *
     * @b Exceptions:
     *  @li None.
     */
    inline ~SparseMatrix()
    {
      deallocate_();
    }

    //--------------------------------------------------------------------------------
    // TESTS
    //--------------------------------------------------------------------------------
    /**
     * Returns whether this sparse matrix is zero or not. It is zero if it does not
     * contain a single non-zero.
     *
     * @retval [bool] whether the matrix is zero or not
     *
     * @b Complexity:
     *  @li O(nrows)
     *
     * @b Exceptions:
     *  @li None.
     */
    inline bool isZero() const { return nNonZeros() == 0; }

    //--------------------------------------------------------------------------------
    /**
     * Returns the function used to determine whether a value is zero or not
     * in this sparse matrix.
     *
     * @retval [IsNearlyZero<DTZ>&] the zero test function
     *
     * @b Exceptions:
     *  @li None.
     */
    inline const IsNearlyZero<DTZ>& getIsNearlyZeroFunction() const
    {
      return isZero_;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns whether this sparse matrix is stored "compactly" or not.
     * When stored "compactly", all the non-zeros are in a single block
     * of memory. When not stored "compactly", each row is a contiguous
     * chunk of memory, but the rows are located at separate memory addresses.
     * Methods compact()/decompact() can be used to switch from one mode
     * to the other.
     * Having all the non-zeros stored in one single, contiguous array in memory
     * can speed up some operations by favoring cache coherence.
     *
     * @retval [bool] whether this matrix is stored "compactly" or not
     *
     * @b Complexity:
     *  @li O(1)
     *
     * @b Exceptions:
     *  @li None.
     */
    inline bool isCompact() const { return ind_mem_ != 0; }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of rows in this SparseMatrix.
     *
     * @retval [0 <= size_type] the current number of rows
     *
     * @b Complexity:
     *  @li O(1)
     *
     * @b Exceptions:
     *  @li None.
     */
    inline size_type nRows() const { return nrows_; }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of colums in this SparseMatrix.
     *
     * @retval [0 <= size_type] the current number of columns
     *
     * @b Complexity:
     *  @li O(1)
     *
     * @b Exceptions:
     *  @li None.
     */
    inline size_type nCols() const { return ncols_; }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of bytes used by this SparseMatrix.
     */
    inline size_type nBytes() const
    {
      size_type n =
        7 * sizeof(size_type)
        + 3 * sizeof(value_type)
        + nCols() * (sizeof(size_type) + sizeof(value_type));

      for (size_type i = 0; i != nRows(); ++i)
        n += (nNonZerosOnRow(i) + 2) * (sizeof(size_type) + sizeof(value_type));

      return n;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of non-zeros on 'row'-th row.
     *
     * @param row [0 <= size_type < nrows] index of the row to access
     * @retval [0 <= size_type <= ncols] number of non-zeros on 'row'-th row
     *
     * @b Complexity:
     *  @li O(1)
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     *  @li If nnzr < 0 || nnzr > ncols (post assert)
     */
    inline size_type nNonZerosOnRow(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "nNonZerosOnRow");
      } // End pre-conditions

      size_type nnzr = nnzr_[row];

      { // Post-conditions
        NTA_ASSERT(0 <= nnzr && nnzr <= nCols())
          << "SparseMatrix nNonZerosOnRow: "
          << "post-condition: nnzr = " << nnzr
          << " when ncols = " << nCols();
      } // End post-conditions

      return nnzr;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of non-zeros on 'col'-th column.
     *
     * @param col [0 <= size_type < ncols] index of the column to access
     * @retval [0 <= size_type <= nrows] number of non-zeros on 'col'-th column
     *
     * @b Complexity:
     *  @li O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols (assert)
     *  @li If nnzc < 0 || nnzc >= nrows (post assert)
     */
    inline size_type nNonZerosOnCol(size_type col) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "nNonZerosOnCol");
      } // End pre-conditions

      size_type nnzc = 0;

      ITERATE_ON_ALL_ROWS
        if (col_(row, col) >= 0)
          ++nnzc;

      { // Post-conditions
        NTA_ASSERT(0 <= nnzc && nnzc <= nRows())
          << "SparseMatrix nNonZerosOnCol: "
          << "post-condition: nnzc = " << nnzc
          << " when nrows = " << nRows();
      } // End post-conditions

      return nnzc;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of non-zeros in this SparseMatrix.
     *
     * @retval [0 <= size_type < nrows * ncols] number of non-zeros
     *
     * @b Complexity:
     *  @li O(nrows)
     *
     * @b Exceptions:
     *  @li If nnz < 0 || nnz > nrows * ncols (post assert)
     */
    inline size_type nNonZeros() const
    {
      size_type nnz = 0;

      ITERATE_ON_ALL_ROWS
        nnz += nNonZerosOnRow(row);

      { // Post-conditions
        NTA_ASSERT(0 <= nnz && nnz <= nRows() * nCols())
          << "SparseMatrix nNonZeros: "
          << "post-condition: Invalid nnz = " << nnz
          << " when nrows = " << nRows()
          << " and ncols = " << nCols();
      } // End post-conditions

      return nnz;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of non-zeros on each row of this SparseMatrix,
     * for all rows simultaneously.
     *
     * @param it [OutputIterator] an iterator to storage for the number of non-zeros
     *  per row (needs nrows space).
     *
     * @b Complexity:
     *  @li O(nrows)
     *
     * @b Exceptions:
     *  @li If it is not an OutputIterator on size_type.
     */
    template <typename OutputIterator>
    inline void nNonZerosPerRow(OutputIterator it) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator, size_type);
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        *it = nNonZerosOnRow(row);
        ++it;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of non-zeros on each column of this SparseMatrix,
     * for all columns simultaneously.
     *
     * @param it [OutputIterator] an iterator to storage for the number of non-zeros
     *  per column (needs ncols space).
     *
     * @b Complexity:
     *  @li O(ncols + nnz)
     *
     * @b Exceptions:
     *  @li If it is not an OutputIterator on size_type.
     */
    template <typename OutputIterator>
    inline void nNonZerosPerCol(OutputIterator it) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator, size_type);
      } // End pre-conditions

      std::fill(it, it + nCols(), 0);

      ITERATE_ON_ALL_ROWS {
        size_type *ind = ind_begin_(row), *end = ind_end_(row);
        while (ind != end)
          ++ *(it + *ind++);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns true if row is all zeros, false otherwise.
     *
     * @param row [0 <= size_type < nrows] the row
     * @retval [bool] whether the row is all zeros or not
     *
     * @b Complexity:
     *  @li O(1)
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     */
    inline bool isRowZero(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "isRowZero");
      } // End pre-conditions

      return nNonZerosOnRow(row) == 0;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns true if column col is all zeros, false otherwise.
     *
     * @param col [0 <= size_type < ncols] the column
     * @retval [bool] whether the column is all zeros or not
     *
     * @b Complexity:
     *  @li Worst case: O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols (assert)
     */
    inline bool isColZero(size_type col) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "isColZero");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS
        if (col_(row, col) >= 0)
          return false;

      return true;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of rows that are not zero, i.e. that have at least one
     * non-zero.
     *
     * @retval [0 <= size_type <= nrows] the numbef or non-zero rows
     *
     * @b Complexity:
     *  @li O(nrows)
     *
     * @b Exceptions:
     *  @li None.
     */
    inline size_type nNonZeroRows() const
    {
      size_type count = 0;

      ITERATE_ON_ALL_ROWS
        if (nnzr_[row] > 0)
          ++ count;

      return count;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of columns that are not zero, i.e. that have at least one
     * non-zero.
     *
     * @retval [0 <= size_type <= ncols] the number of non-zero columns
     *
     * @b Complexity:
     *  @li O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li None.
     */
    inline size_type nNonZeroCols() const
    {
      const size_type ncols = nCols();

      size_type count = 0;

      for (size_type col = 0; col != ncols; ++col)
        if (!isColZero(col))
          ++ count;

      return count;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of zero rows, i.e. the number of rows that don't have any
     * non-zero.
     *
     * @retval [0 <= size_type < nrows] the number of zero rows
     *
     * @b Complexity:
     *  @li O(1)
     *
     * @b Exceptions:
     *  @li None.
     */
    inline size_type nZeroRows() const
    {
      return nRows() - nNonZeroRows();
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of zero cols, i.e. the number of columns that don't have
     * any non-zero.
     *
     * @retval [0 <= size_type < ncols] the number of zero columns
     *
     * @b Complexity:
     *  @li O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li None.
     */
    inline size_type nZeroCols() const
    {
      return nCols() - nNonZeroCols();
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the column and value of the first non-zero on the given row.
     *
     * @param row [0 <= size_type < nrows] the row index
     * @retval [pair<size_type, value_type>] the index and value of the first
     *  non-zero on the given row
     *
     * @b Complexity:
     *  @li O(1)
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     */
    inline std::pair<size_type, value_type> firstNonZeroOnRow(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "firstNonZeroOnRow");
      } // End pre-conditions

      if (isRowZero(row))
        return std::make_pair(nRows(), 0);

      return std::make_pair(ind_[row][0], nz_[row][0]);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the column and value of the last non-zero on the given row.
     *
     * @param row [0 <= size_type < nrows] the row index
     * @retval [pair<size_type, value_type>] the index and value of the last
     *  non-zero on the given row
     *
     * @b Complexity:
     *  @li O(1)
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     */
    inline std::pair<size_type, value_type> lastNonZeroOnRow(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "lastNonZeroOnRow");
      } // End pre-conditions

      if (isRowZero(row))
        return std::make_pair(nRows(), 0);

      const size_type idx = nnzr_[row] - 1;

      return std::make_pair(ind_[row][idx], nz_[row][idx]);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of columns between the first and the last non-zero on the
     * given row.
     *
     * @retval [0 <= size_type < ncols] the number of columns between the first
     *  and the last non-zero on the given row
     *
     * @b Complexity:
     *  @li O(1)
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     */
    inline size_type rowBandwidth(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "rowBandwidth");
      } // End pre-conditions

      if (isRowZero(row))
        return 0;

      if (nNonZerosOnRow(row) == 1)
        return 1;

      return ind_[row][nnzr_[row] - 1] - ind_[row][0];
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of columns between the first and the last non-zero on each
     * row, for all rows simultaneously.
     *
     * @param it [OutputIterator] an iterator on the container that will receive
     *  the row bandwidth values
     *
     * @b Complexity:
     *  @li O(nrows)
     *
     * @b Exceptions:
     *  @li If it is not an OutputIterator on size_type.
     */
    template <typename OutputIterator>
    inline void rowBandwidths(OutputIterator it) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator, size_type);
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        *it = rowBandwidth(row);
        ++it;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the row and value of the first non-zero on the given column.
     *
     * @param col [0 <= size_type < ncols] the column index
     * @retval [pair<size_type, value_type>] the index and value of the first
     *  non-zero on the given column
     *
     * @b Complexity:
     *  @li Worst case: O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols (assert)
     */
    inline std::pair<size_type, value_type> firstNonZeroOnCol(size_type col) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "firstNonZeroOnCol");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        size_type *j = pos_(row, col);
        if (j != ind_end_(row) && *j == col)
          return std::make_pair(row, nz_[row][j - ind_begin_(row)]);
      }

      return std::make_pair(nCols(), 0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the row and value of the last non-zero on the given column.
     *
     * @param col [0 <= size_type < ncols] the column index
     * @retval [pair<size_type, value_type>] the index and value of the last
     *  non-zero on the given column
     *
     * @b Complexity:
     *  @li Worst case: O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols (assert)
     */
    inline std::pair<size_type, value_type> lastNonZeroOnCol(size_type col) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "lastNonZeroOnCol");
      } // End pre-conditions

      for (int row = (int) nRows() - 1; row != -1; --row) {
        size_type *j = pos_(row, col);
        if (j != ind_end_(row) && *j == col)
          return std::make_pair((size_type) row, nz_[row][j - ind_begin_(row)]);
      }

      return std::make_pair(nCols(), 0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of rows between the first and the last non-zero on the
     * given column.
     *
     * @param col [0 <= size_type < ncols] the column index
     * @retval [pair<size_type, value_type>] the index and value of the last
     *  non-zero on the given column
     *
     * @b Complexity:
     *  @li Worst case: O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols (assert)
     */
    inline size_type colBandwidth(size_type col) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "colBandwidth");
      } // End pre-conditions

      int first = -1, last = -1;

      const int nrows(nRows());

      for (int row = 0; row != nrows && first == -1; ++row) {
        size_type *j = pos_(row, col);
        if (j != ind_end_(row) && *j == col) {
          first = row;
        }
      }

      if (first == -1)
        return size_type(0);

      for (int row = nrows - 1; row != -1 && last == -1; --row) {
        size_type *j = pos_(row, col);
        if (j != ind_end_(row) && *j == col) {
          last = row;
        }
      }

      if (first == last)
        return size_type(1);

      return size_type(last - first);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of rows between the last and the first non-zero of each
     * column, for all columns simultaneously.
     *
     * @param it [OutputIterator] iterator to the beginning of the range that will
     *  receive the column bandwidths. It will iterate nCols() times.
     *
     * @b Complexity:
     *  @li O(ncols * nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator>
    inline void colBandwidths(OutputIterator it) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator, size_type);
      } // End pre-conditions

      const size_type ncols = nCols();
      for (size_type col = 0; col != ncols; ++col, ++it)
        *it = colBandwidth(col);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns true if on the given row, there are non-zeros in the range
     * [col_begin, col_end).
     */
    inline bool
    nonZerosInRowRange(size_type row, size_type col_begin, size_type col_end) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "intersectsRowRange");
        assert_valid_col_range_(col_begin, col_end, "intersectsRowRange");
      } // End pre-conditions

      if (nNonZerosOnRow(row) == 0)
        return false;

      if (col_begin > ind_[row][nnzr_[row]-1] || col_end < ind_[row][0])
        return false;

      return true;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns number of non-zeros in specified range of a given row.
     */
    inline
    size_type
    nNonZerosInRowRange(size_type row, size_type col_begin, size_type col_end) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "nNonZerosInRowRange");
        assert_valid_col_range_(col_begin, col_end, "nNonZerosInRowRange");
      } // End pre-conditions

      if (!nonZerosInRowRange(row, col_begin, col_end))
        return 0;

      size_type *c1 = pos_(row, col_begin);
      size_type *c2 = col_end == nCols() ? ind_end_(row)
        : std::lower_bound(c1, ind_end_(row), col_end);

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
        assert_valid_row_range_(row_begin, row_end, "nNonZerosInBox");
        assert_valid_col_range_(col_begin, col_end, "nNonZerosInBox");
      } // End pre-conditions

      size_type count = 0;

      for (size_type row = row_begin; row != row_end; ++row)
        count += nNonZerosInRowRange(row, col_begin, col_end);

      return count;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of non-zeros for each box in a collection of boxes that
     * partitions the matrix.
     * The indices of the rows and columns that partition the matrix are passed in
     * two ranges.
     * The result is put into an object of type Summary that must have a resize
     * and a set methods.
     *
     * @param row_inds_begin [InputIterator] iterator to beginning of range that contains
     *  the row indices to use
     * @param row_inds_end [InputIterator] iterator to one past the end of the range
     *  that contain the row indices to use
     * @param col_inds_begin [InputIterator] iterator to beginning of range that contains
     *  the col indices to use
     * @param col_inds_end [InputIterator] iterator to one past the end of the range
     *  that contain the col indices to use
     * @param summary [Summary&] storage for the result, must have resize and set methods
     *
     * @b Complexity:
     *  @li O(2 * (row_end - row_begin) * log(nnzr))
     *
     * @b Exceptions:
     *  @li If [row_inds_begin, row_inds_end] not a valid iterator range
     *  @li If [col_inds_begin, col_inds_end] not a valid iterator range
     *  @li Exceptions of nNonZerosInBox
     */
    template <typename InputIterator, typename Summary>
    inline void
    nNonZerosPerBox(InputIterator row_inds_begin, InputIterator row_inds_end,
                    InputIterator col_inds_begin, InputIterator col_inds_end,
                    Summary& summary) const
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);
        ASSERT_VALID_RANGE(row_inds_begin, row_inds_end, "SparseMatrix nNonZerosPerBox");
        ASSERT_VALID_RANGE(col_inds_begin, col_inds_end, "SparseMatrix nNonZerosPerBox");
        // Other pre-conditions checked in nNonZerosInBox
      } // End pre-conditions

      size_type n_i = (size_type)(row_inds_end - row_inds_begin);
      size_type n_j = (size_type)(col_inds_end - col_inds_begin);
      summary.resize(n_i, n_j);

      size_type box_i = 0, prev_row = 0;
      for (InputIterator row = row_inds_begin; row != row_inds_end; ++row, ++box_i) {
        size_type prev_col = 0, box_j = 0;
        for (InputIterator col = col_inds_begin; col != col_inds_end; ++col, ++box_j) {
          value_type nnzib = (value_type) nNonZerosInBox(prev_row, *row, prev_col, *col);
          summary.set(box_i, box_j, nnzib);
          prev_col = *col;
        }
        prev_row = *row;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns true if this matrix is symmetric, false otherwise.
     *
     * @retval [bool] true if this matrix is symmetric, false otherwise
     *
     * @b Complexity:
     *  @li O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li None.
     */
    inline bool isSymmetric() const
    {
      if (nRows() != nCols())
        return false;

      ITERATE_ON_ALL_ROWS {
        size_type *ind = ind_begin_(row);
        size_type *ind_end = ind_end_(row);
        value_type *nz = nz_begin_(row);
        for (; ind != ind_end && *ind < row; ++ind, ++nz)
          if (get(*ind, row) != *nz)
            return false;
      }

      return true;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns whether this matrix is binary or not (the non-zeros are all the same
     * value). In that case, better to use a 0/1 sparse matrix.
     */
    inline bool isBinary() const
    {
      value_type nnz0 = 0;

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          if (nnz0 == 0)
            nnz0 = *nz;
          else if (*nz != nnz0)
            return false;
        }
      }

      return true;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns a list of the indices of all the non-zero (empty) rows.
     *
     * @param it [OutputIterator] iterator to the beginning of the range that will
     *  receive the indices of the non-zero rows. It will iterate at most nRows() times.
     *
     * @b Complexity:
     *  @li O(nrows)
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator>
    inline void nonZeroRows(OutputIterator it) const
    {
      ITERATE_ON_ALL_ROWS
        if (!this->isRowZero(row))
          *it++ = row;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns a list of the indices of all the zero (empty) rows.
     *
     * @param it [OutputIterator] iterator to the beginning of the range that will
     *  receive the indices of the zero rows. It will iterate at most nRows() times.
     *
     * @b Complexity:
     *  @li O(nrows)
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator>
    inline void zeroRows(OutputIterator it) const
    {
      ITERATE_ON_ALL_ROWS
        if (this->isRowZero(row))
          *it++ = row;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns a list of the indices of all the non-zero (empty) columns.
     *
     * @param it [OutputIterator] iterator to the beginning of the range that will
     *  receive the indices of the non-zero columns. It will iterate at most nCols() times.
     *
     * @b Complexity:
     *  @li O(ncols)
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator>
    inline void nonZeroCols(OutputIterator it) const
    {
      ITERATE_ON_ALL_COLS
        if (!this->isColZero(col))
          *it++ = col;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns a list of the indices of all the zero (empty) columns.
     *
     * @param it [OutputIterator] iterator to the beginning of the range that will
     *  receive the indices of the zero columns. It will iterate at most nCols() times.
     *
     * @b Complexity:
     *  @li O(ncols)
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator>
    inline void zeroCols(OutputIterator it) const
    {
      ITERATE_ON_ALL_COLS
        if (this->isColZero(col))
          *it++ = col;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns a list of the indices of all the zero (empty) rows that are also
     * zero columns. If the matrix is not square and the row index doesn't exist
     * as a column, then that row is ignored.
     *
     * @param it [OutputIterator] iterator to the beginning of the range that will
     *  receive the indices of the zero columns. It will iterate at most nCols() times.
     *
     * @b Complexity:
     *  @li O(nrows)
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator>
    inline void zeroRowCol(OutputIterator it) const
    {
      ITERATE_ON_ALL_ROWS {
        if (isRowZero(row)) {
          if (row < nCols() && isColZero(row))
            *it++ = row;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * For a matrix that has as many rows as columns, returns the list of indices
     * that correspond to a zero row and a zero column simultaneously.
     * These correspond to isolate vertices if the matrix is seen as a graph.
     */
    template <typename OutputIterator>
    inline size_type zeroRowAndCol(OutputIterator it) const
    {
      { // Pre-conditions
        NTA_ASSERT(nRows() == nCols())
          << "SparseMatrix zeroRowAndCol: Matrix needs to be square";
      } // End pre-conditions

      size_type count = 0;

      for (size_type i = 0; i != nRows(); ++i)
        if (isRowZero(i))
          if (isColZero(i)) {
            *it++ = i;
            ++count;
          }

      return count;
    }

    //--------------------------------------------------------------------------------
    // EQUALITY
    //--------------------------------------------------------------------------------

    /**
     * Tests whether two instances of class SparseMatrix are equal or not.
     * Two matrices are considered different if any of the following conditions
     * is met:
     *
     * - the number of rows is different
     * - the number of columns is different
     * - the number of non-zeros is different
     * - any non-zero is different
     *
     * @param B [SparseMatrix] the matrix to compare to
     * @retval [bool] whether the two matrices are equal or not
     *
     * @b Complexity:
     *  @li O(nrows + nnz)
     *
     * @b Exceptions:
     *  @li None.
     */
    inline bool equals(const SparseMatrix& B) const
    {
      if (B.nRows() != nRows())
        return false;
      if (B.nCols() != nCols())
        return false;
      if (B.nNonZeros() != nNonZeros())
        return false;

      for (size_type i = 0; i != nRows(); ++i) {

        if (nnzr_[i] != B.nnzr_[i])
          return false;

        size_type *ind = ind_[i], *ind_end = ind + nnzr_[i];
        size_type *ind_b = B.ind_[i];
        value_type *nz = nz_[i], *nz_b = B.nz_[i];

        while (ind != ind_end) {
          if (*ind != *ind_b)
            return false;
          if (*nz != *nz_b)
            return false;
          ++ind; ++ind_b;
          ++nz; ++nz_b;
        }
      }

      return true;
    }

    //--------------------------------------------------------------------------------
    /**
     * Checks whether the non-zeros on a given row are in the same location for
     * two sparse matrices.
     */
    inline bool sameRowNonZeroIndices(size_type row, const SparseMatrix& B) const
    {
      {
        NTA_ASSERT(0 <= row && row < nRows())
          << "SparseMatrix::sameRowNonZeroIndices: "
          << "Invalid row index: " << row
          << " - SparseMatrix has only: " << nRows() << " rows";

        NTA_ASSERT(0 <= row && row < B.nRows())
          << "SparseMatrix::sameRowNonZeroIndices: "
          << "Invalid row index: " << row
          << " - B matrix has only: " << nRows() << " rows";
      }

      if (nNonZerosOnRow(row) != B.nNonZerosOnRow(row))
        return false;

      size_type *ind = ind_[row], *ind_end = ind + nnzr_[row];
      size_type *ind_b = B.ind_[row];

      for (; ind != ind_end; ++ind, ++ind_b)
        if (*ind != *ind_b)
          return false;

      return true;
    }

    //--------------------------------------------------------------------------------
    /**
     * Checks whether two sparse matrices have all their zeros in the same locations.
     */
    inline bool sameNonZeroIndices(const SparseMatrix& B) const
    {
      {
        NTA_ASSERT(nRows() <= B.nRows());
        NTA_ASSERT(nCols() <= B.nCols());
      }

      ITERATE_ON_ALL_ROWS
        if (!sameRowNonZeroIndices(row, B))
          return false;

      return true;
    }

    //--------------------------------------------------------------------------------
    /**
     * Checks whether the indices of the non-zeros on row of this SM are a subset of the
     * indices of the non-zeros of the same row of the B sparse matrix.
     * In the case of a row of zeros in this SM, that means the set of indices of
     * non-zeros is empty, and the empty set is always included in the set of
     * non-zeros of B.
     */
    inline bool nonZeroIndicesIncluded(size_type row, const SparseMatrix& B) const
    {
      { // Pre-conditions
        NTA_ASSERT(0 <= row && row < nRows())
          << "SparseMatrix::sameRowNonZeroIndices: "
          << "Invalid row index: " << row
          << " - SparseMatrix has only: " << nRows() << " rows";

        NTA_ASSERT(0 <= row && row < B.nRows())
          << "SparseMatrix::sameRowNonZeroIndices: "
          << "Invalid row index: " << row
          << " - B matrix has only: " << nRows() << " rows";
      } // End pre-conditions

      if (nNonZerosOnRow(row) > B.nNonZerosOnRow(row))
        return false;

      size_type *ind = ind_begin_(row), *ind_end = ind_end_(row);
      size_type *ind_b = B.ind_begin_(row);

      size_type n = 0;

      while (ind != ind_end) {
        if (*ind == *ind_b) {
          ++n;
          ++ind; ++ind_b;
        } else if (*ind < *ind_b) {
          return false;
        } else if (*ind_b < *ind) {
          ++ind_b;
        }
      }

      return n == nNonZerosOnRow(row);
    }

    //--------------------------------------------------------------------------------
    /**
     * Checks whether the locations of the non-zeros of this sparse matrix are included
     * in the locations of the non-zeros of the B sparse matrix.
     */
    inline bool nonZeroIndicesIncluded(const SparseMatrix& B) const
    {
      {
        NTA_ASSERT(nRows() <= B.nRows());
        NTA_ASSERT(nCols() <= B.nCols());
      }

      ITERATE_ON_ALL_ROWS
        if (!nonZeroIndicesIncluded(row, B))
          return false;

      return true;
    }

    //--------------------------------------------------------------------------------
    // COMPACT/DECOMPACT
    //--------------------------------------------------------------------------------

    /**
     * Compacts the memory for this SparseMatrix.
     * This reduces the number of cache misses, and can
     * make a sizable runtime difference (up to 30% on shona,
     * depending on the operation).
     * All the non-zeros are allocated contiguously.
     * Non-mutating algorithms can run on the compact representation.
     *
     * @b Complexity:
     *  @li O(2*nnz)
     *
     * @b Exceptions:
     *  @li Not eneough memory (error)
     */
    inline void compact()
    {
      if (isCompact())
        return;

      size_type nnz = nNonZeros();

      ind_mem_ = new size_type[nnz];
      size_type *indp = ind_mem_;

      nz_mem_ = new value_type[nnz];
      value_type *nzp = nz_mem_;

      ITERATE_ON_ALL_ROWS {

        nnz = nnzr_[row];
        std::copy(ind_[row], ind_[row] + nnz, indp);
        std::copy(nz_[row], nz_[row] + nnz, nzp);

        delete [] ind_[row];
        delete [] nz_[row];

        ind_[row] = indp;
        nz_[row] = nzp;
        indp += nnz;
        nzp += nnz;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * "De-compacts" this SparseMatrix, that is, each row
     * is allocated separately. All the non-zeros inside a given row
     * are still allocated contiguously. This is more efficient
     * when changing the number of non-zeros on each row (rather than
     * reallocating the whole contiguous array of all the non-zeros
     * in the SparseMatrix. We decompact before mutating the non-zeros,
     * and we recompact once the non-zeros don't change anymore.
     *
     * @b Complexity:
     *  @li O(2*nnz)
     *
     * @b Exceptions:
     *  @li Not enough memory (error)
     */
    inline void decompact()
    {
      if (!isCompact())
        return;

      ITERATE_ON_ALL_ROWS {
        size_type nnzr = nnzr_[row];
        if (nnzr > 0) {
          size_type* new_ind = new size_type[nnzr];
          value_type* new_nz = new value_type[nnzr];
          std::copy(ind_[row], ind_[row] + nnzr, new_ind);
          std::copy(nz_[row], nz_[row] + nnzr, new_nz);
          ind_[row] = new_ind;
          nz_[row] = new_nz;
        } else {
          ind_[row] = 0;
          nz_[row] = 0;
        }
      }

      delete [] ind_mem_;
      delete [] nz_mem_;
      ind_mem_ = 0;
      nz_mem_ = 0;
    }

    //--------------------------------------------------------------------------------
    // IMPORT/EXPORT
    //--------------------------------------------------------------------------------

    //--------------------------------------------------------------------------------
    /**
     * Populates this SparseMatrix from a dense array of value_type.
     * The dense array needs to be in row-major order, contiguous.
     * The non-zeros are stored in increasing order of column index
     * in the rows of this sparse matrix. The previous state of this
     * matrix is discarded.
     *
     * @param nrows [0 <= size_type] number of rows in dense array
     * @param ncols [0 <= size_type] number of columns in dense array
     * @param dense [InputIterator] dense array of values
     *
     * @b Exceptions:
     *  @li If nrows < 0 (check)
     *  @li If ncols < 0 (check)
     *  @li Not enough memory (error)
     */
    template <typename InputIterator>
    inline void fromDense(size_type nrows, size_type ncols, InputIterator dense)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);

        NTA_CHECK(nrows >= 0)
          << "SparseMatrix::fromDense(): "
          << "Invalid number of rows: " << nrows
          << " - Should be >= 0";

        NTA_CHECK(ncols >= 0)
          << "SparseMatrix::fromDense(): "
          << "Invalid number of columns: " << ncols
          << " - Should be > 0";
      } // End pre-conditions

      deallocate_();
      allocate_(nrows, ncols);
      nrows_ = 0;
      ncols_ = ncols;

      for (size_type i = 0; i != nrows; ++i, dense += ncols)
        addRow(dense);
    }

    //--------------------------------------------------------------------------------
    /**
     * Exports this SparseMatrix to a pre-allocated dense array of value_type.
     * OutputIterator needs to be an iterator into a contiguous array of memory.
     *
     * Non-mutating, O(nrows*ncols)
     *
     * @param dense [OutputIterator] iterator to contiguous array of memory
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename OutputIterator>
    inline void toDense(OutputIterator dense) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator, value_type);
      } // End pre-conditions

      const size_type ncols = nCols();

      ITERATE_ON_ALL_ROWS
        getRowToDense(row, dense + row*ncols);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the number of bytes of the string returned by toCSR.
     */
    inline size_type CSRSize() const
    {
      char buffer[64];

      size_type n =
        sprintf(buffer, "sm_csr_1.5 %lu %lu %lu ",
                (unsigned long) nRows(),
                (unsigned long) nCols(),
                (unsigned long) nNonZeros());

      ITERATE_ON_ALL_ROWS {
        n += sprintf(buffer, "%lu ", (unsigned long) nNonZerosOnRow(row));
        ITERATE_ON_ROW {
          n += sprintf(buffer, "%lu ", (unsigned long) *ind);
          n += sprintf(buffer, "%.15g ", *nz);
        }
      }

      n += sprintf(buffer, "%lu ", (unsigned long) n - 5);

      return n;
    }

    //--------------------------------------------------------------------------------
    /**
     * Populates this SparseMatrix from a stream in csr format.
     * The pairs (index, value) can be in any order for each row.
     * Mutating, discards the previous state of this SparseMatrix.
     * Can handle large sparse matrices.
     *
     * @b Format:
     *  'csr' totalbytes nrows ncols nnz
     *  nnzr1 j1 val1 j2 val2 ...
     *  nnzr2 ...
     *
     * Don't forget number of bytes (totalbytes) after 'csr' tag!
     *
     * where nnzr is the total number of non-zeros in the matrix,
     *       nnzr1 is the number of non-zeros on the first row,
     *       j1 is the column index of the first non-zeroon the first row,
     *       val1 is the value of the first non-zero on the first row.
     *
     * @param inStream [std::istream] the stream to initialize from
     * @retval [std::istream] the stream after the matrix has been read
     *
     * WARNING: for each row, the indices must be in increasing order,
     * without duplicates, and no zeros.
     *
     * WARNING: values in the stream smaller than epsilon will be rounded out
     *
     * WARNING: doesn't work if float == complex (because of MemStream)
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
     *
     * TODO save distance from isZero_??
     */
    inline std::istream&
    fromCSR(std::istream& inStreamParam, bool zero_permissive=false)
    {
      const char* where = "SparseMatrix::fromCSR(): ";

      { // Pre-conditions
        NTA_CHECK(inStreamParam.good())
          << where << "Bad stream";
      } // End pre-conditions

      std::string tag;
      inStreamParam >> tag;
      NTA_CHECK(tag == "csr" || tag == "sm_csr_1.5")
        << where
        << "Stream is not in csr format"
        << " - Should start with 'csr' or 'sm_csr_1.5' tag";

      // Read our stream data into a MemParser object for faster parsing.
      long totalBytes;
      inStreamParam >> totalBytes;
      if (totalBytes < 0)
        totalBytes = 0;

#ifdef WIN32 // On Windows, don't use MemParser, it's slow.

      size_type i, j, k, nrows, ncols, nnz, nnzr;
      i = j = k = nrows = ncols = nnz = nnzr = 0;
      nta::Real64 val = 0;

      inStreamParam >> nrows >> ncols >> nnz;

      {
        NTA_CHECK(nrows >= 0)
          << where
          << "Invalid number of rows: " << nrows
          << " - Should be >= 0";

        NTA_CHECK(ncols >= 0)
          << where
          << "Invalid number of columns: " << ncols
          << " - Should be > 0";

        NTA_CHECK(nnz >= 0 && (double) nnz <= (double) nrows * ncols)
          << where
          << "Invalid number of non-zeros: " << nnz
          << " - Should be >= 0 && nrows * ncols = " << (double) nrows * ncols;
      }

      deallocate_();
      allocate_(nrows, ncols);
      nrows_ = 0;
      ncols_ = ncols;

      for (i = 0; i != nrows; ++i) {

        inStreamParam >> nnzr;

        {
          NTA_CHECK(nnzr >= 0 && nnzr <= ncols)
            << where
            << "Invalid number of non-zeros: " << nnzr
            << " - Should be >= 0 && < ncols = " << ncols;
        }

        size_type* indb_it = indb_;
        value_type* nzb_it = nzb_;

        for (k = 0; k != nnzr; ++k) {

          inStreamParam >> j >> val;
          value_type val1 = (value_type)val;

          {
            NTA_CHECK(j >= 0 && j < ncols)
              << where
              << "Invalid index: " << j
              << " - Should be >= 0 and < ncols = " << ncols;
          }

          if (zero_permissive) {
            *indb_it++ = j;
            *nzb_it++ = val1;
          } else {
            if (!isZero_(val1)) {
              *indb_it++ = j;
              *nzb_it++ = val1;
            }
          }
        }

        // addRow checks that there are no duplicates, no zeros,
        // and that we stay in strictly increasing order
        addRow(indb_, indb_it, nzb_, zero_permissive);
      }

#endif
#ifndef WIN32 // On Unix, MemParser is faster.

      MemParser inStream(inStreamParam, totalBytes);

      size_type i, j, k, nrows, ncols, nnz, nnzr;
      nta::Real64 val; // always largest possible type, then cast

      inStream >> nrows >> ncols >> nnz;

      {
        NTA_CHECK(nrows >= 0)
          << where
          << "Invalid number of rows: " << nrows
          << " - Should be >= 0";

        NTA_CHECK(ncols >= 0)
          << where
          << "Invalid number of columns: " << ncols
          << " - Should be > 0";

        NTA_CHECK(nnz >= 0 && (double) nnz <= (double) nrows * ncols)
          << where
          << "Invalid number of non-zeros: " << nnz
          << " - Should be >= 0 && nrows * ncols = " << (double) nrows * ncols;
      }

      deallocate_();
      allocate_(nrows, ncols);
      nrows_ = 0;
      ncols_ = ncols;

      for (i = 0; i != nrows; ++i) {

        inStream >> nnzr;

        {
          NTA_CHECK(nnzr >= 0 && nnzr <= ncols)
            << where
            << "Invalid number of non-zeros: " << nnzr
            << " - Should be >= 0 && < ncols = " << ncols;
        }

        size_type* indb_it = indb_;
        value_type* nzb_it = nzb_;

        for (k = 0; k != nnzr; ++k) {

          inStream >> j >> val;
          // This cast allows to handle integers in float TAMs.
          value_type vval = (value_type) val;

          {
            NTA_CHECK(j >= 0 && j < ncols)
              << where
              << "Invalid index: " << j
              << " - Should be >= 0 and < ncols = " << ncols;
          }

          if (zero_permissive) {
            *indb_it++ = j;
            *nzb_it++ = vval;
          } else {
            if (!isZero_(vval)) {
              *indb_it++ = j;
              *nzb_it++ = vval;
            }
          }
        }

        // addRow checks that there are no duplicates, no zeros,
        // and that we stay in strictly increasing order
        addRow(indb_, indb_it, nzb_, zero_permissive);
      }
#endif

      return inStreamParam;
    }

    //--------------------------------------------------------------------------------
    /**
     * Exports this SparseMatrix to a stream in csr format.
     * The non-zeros are in row-major order, in increasing order of indices.
     *
     * @b Format:
     *  'csr' totalbytes nrows ncols nnz
     *  nnzr1 j1 val1 j2 val2 ...
     *  nnzr2 ...
     *
     * where totalbytes is the total number of bytes that follow in the csr description
     *       nnzr is the total number of non-zeros in the matrix,
     *       nnzr1 is the number of non-zeros on the first row,
     *       j1 is the column index of the first non-zero on the first row,
     *       val1 is the value of the first non-zero on the first row.
     *
     * WARNING: doesn't work if float == complex (because of MemStream)
     *
     * @param out [std::ostream] the stream to write this matrix to
     * @retval [std::ostream] the stream with the matrix written to it
     *
     * @b Exceptions:
     *  @li Bad stream (check)
     *
     * TODO read distance from isZero_??
     */
    inline std::ostream& toCSR(std::ostream& out) const
    {
      { // Pre-conditions
        NTA_CHECK(out.good())
          << "SparseMatrix::toCSR(): Bad stream";
      } // End pre-conditions

      out << "sm_csr_1.5 ";

      OMemStream buf;
      buf << std::setprecision(15);
      buf << nRows() << ' '
          << nCols() << ' '
          << nNonZeros() << ' ';

      ITERATE_ON_ALL_ROWS {
        buf << nnzr_[row] << ' ';
        ITERATE_ON_ROW {
          buf << *ind << ' ' << *nz << ' ';
        }
      }

      // Write total # of bytes, followed by data.
      // This facilitates faster parsing of the
      // data directly from a memory buffer in fromCSR()
      out << buf.pcount() << ' ';
      out.write(buf.str(), UInt(buf.pcount()));
      return out;
    }

    //--------------------------------------------------------------------------------
    /**
     * Reads this SparseMatrix from binary representation.
     *
     * WARNING this is not platform independent!
     *
     * TODO handle type information?
     * TODO persist isZero_ ??
     */
    inline void fromBinary(std::istream& inStream)
    {
#ifdef NTA_PLATFORM_win32
      std::cout << "fromBinary not supported on win32" << std::endl;
      exit(-1);
#endif

      { // Pre-conditions
        NTA_CHECK(inStream.good())
          << "SparseMatrix::fromBinary: Bad stream";
      } // End pre-conditions

      const char* where = "SparseMatrix::fromBinary ";

      std::string version;
      inStream >> version;

      NTA_CHECK(version == "sm_bin_1.5")
        << "SparseMatrix::fromBinary: Bad version: " << version;

      int littleEndian;
      size_type s1, s2, s3, s4;
      inStream >> littleEndian >> s1 >> s2 >> s3 >> s4;

      {
        NTA_CHECK(s1 == sizeof(size_type))
          << where << "Bad size_type: " << s1;

        NTA_CHECK(s2 == sizeof(value_type))
          << where << "Bad value_type: " << s2;

        NTA_CHECK(s3 == sizeof(difference_type))
          << where << "Bad difference_type: " << s3;

        NTA_CHECK(s4 == sizeof(prec_value_type))
          << where << "Bad prec_value_type: " << s4;
      }

      size_type nrows, nrows_max, ncols, nnz;
      nrows = nrows_max = ncols = nnz = 0;

      inStream >> nrows >> nrows_max >> ncols >> nnz;

      {
        NTA_CHECK(0 <= nrows)
          << where << "Bad number of rows: " << nrows;
        NTA_CHECK(0 <= nrows_max)
          << where << "Bad max number of rows: " << nrows_max;
        NTA_CHECK(nrows <= nrows_max)
          << where << "Number of rows: " << nrows
          << " should be less than max number of rows: " << nrows_max;
        NTA_CHECK(0 <= ncols)
          << where << "Bad number of columns: " << ncols;
        NTA_CHECK(0 <= nnz)
          << where << "Bad number of non-zeros: " << nnz;
      }

      deallocate_();

      nrows_ = nrows;
      nrows_max_ = nrows_max;
      ncols_ = ncols;

      allocate_(nrows_max, ncols);

      ind_mem_ = new size_type [nnz];
      nz_mem_ = new value_type [nnz];

      char separator;
      inStream.read(&separator, 1);
      nta::binary_load(inStream, nnzr_, nnzr_ + nrows_max_);
      nta::binary_load(inStream, ind_mem_, ind_mem_ + nnz);
      nta::binary_load(inStream, nz_mem_, nz_mem_ + nnz);

      bool littleEndian_bool = littleEndian == 1;

      if (littleEndian_bool != IsSystemLittleEndian()) {
        SwapBytesInPlace(nnzr_, nrows_max_);
        SwapBytesInPlace(ind_mem_, nnz);
        SwapBytesInPlace(nz_mem_, nnz);
      }

      size_type *curr_ind_ptr = ind_mem_;
      value_type *curr_nz_ptr = nz_mem_;

      for (size_type row = 0; row != nrows_; ++row) {
        ind_[row] = curr_ind_ptr;
        nz_[row] = curr_nz_ptr;
        curr_ind_ptr += nnzr_[row];
        curr_nz_ptr += nnzr_[row];
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Writes a compact binary representation of this SparseMatrix.
     *
     * WARNING this is not platform independent!
     *
     * TODO persist type information?
     * TODO persist isZero_ ??
     */
    inline void toBinary(std::ostream& outStream)
    {
#ifdef NTA_PLATFORM_win32
      std::cout << "toBinary not supported on win32" << std::endl;
      exit(-1);
#endif

      { // Pre-conditions
        NTA_CHECK(outStream.good())
          << "SparseMatrix::toBinary: Bad stream";
      } // End pre-conditions

      if (!isCompact())
        compact();

      const size_type nnz = nNonZeros();

      outStream << "sm_bin_1.5 "
                << (int) IsSystemLittleEndian() << ' '
                << sizeof(size_type) << ' '
                << sizeof(value_type) << ' '
                << sizeof(difference_type) << ' '
                << sizeof(prec_value_type) << ' '
                << nrows_ << ' '
                << nrows_max_ << ' '
                << ncols_ << ' '
                << nnz << ' ';

      nta::binary_save(outStream, nnzr_, nnzr_ + nrows_max_);
      nta::binary_save(outStream, ind_mem_, ind_mem_ + nnz);
      nta::binary_save(outStream, nz_mem_, nz_mem_ + nnz);
    }

    //--------------------------------------------------------------------------------
    // RESIZE/RESHAPE/ADD/REMOVE
    //--------------------------------------------------------------------------------

    /**
     * Resizes this sparse matrix with rows and/or columns of zeros.
     * The new numbers of rows and/or columns can be larger or smaller
     * than the current numbers of rows and/or columns.
     * If setToZero is true, the matrix is reset to zero.
     *
     * @param new_nrows [size_type > 0] the new number of rows
     * @param new_ncols [size_type > 0] the new number of columns
     *
     * @b Exceptions:
     *  @li None.
     */
    inline void resize(size_type new_nrows, size_type new_ncols, bool setToZero =false)
    {
      { // Pre-conditions
        NTA_ASSERT(0 <= new_nrows)
          << "SparseMatrix resize: "
          << "New number of rows: " << new_nrows
          << " should be positive";

        NTA_ASSERT(0 <= new_ncols)
          << "SparseMatrix resize: "
          << "New number of columns: " << new_ncols
          << " should be positive";
      } // End pre-conditions

      const size_type nrows = nRows();

      if (new_nrows > nrows_max_-1)
        reserve_(new_nrows);

      if (new_nrows < nrows) {

        if (isCompact())
          decompact();

        for (size_type row = new_nrows; row != nrows; ++row) {
          delete [] ind_[row];
          delete [] nz_[row];
          ind_[row] = 0;
          nz_[row] = 0;
          nnzr_[row] = 0;
        }
      }

      if (new_ncols < nCols()) {
        ITERATE_ON_ALL_ROWS {
          size_type k = 0, *ind = ind_[row];
          while (k < nnzr_[row] && ind[k] < new_ncols)
            ++k;
          nnzr_[row] = k;
        }
      }

      // Avoid re-allocating the buffers as much as possible,
      // but also shrink them if the matrix really shrinks
      if (new_ncols > ncols_ || new_ncols < ncols_/2)
        reAllocateBuffers_(new_ncols);

      nrows_ = new_nrows;
      ncols_ = new_ncols;

      if (setToZero)
        this->setToZero();
    }

    //--------------------------------------------------------------------------------
    /**
     * Reshapes this matrix to the new number of rows and columns specified.
     * The new number of elements in the matrix must be the same as the old
     * number of elements:
     * new_nrows * new_ncols = nrows * ncols.
     *
     * @param new_nrows [size_type] the new number of rows
     * @param new_ncols [size_type] the new number of columns
     */
    inline void reshape(size_type new_nrows, size_type new_ncols)
    {
      { // Pre-conditions
        NTA_ASSERT(0 <= new_nrows)
          << "SparseMatrix reshape: "
          << "New number of rows: " << new_nrows
          << " should be positive";

        NTA_ASSERT(0 <= new_ncols)
          << "SparseMatrix reshape: "
          << "New number of columns: " << new_ncols
          << " should be positive";

        NTA_ASSERT((double) new_nrows * new_ncols == (double) nRows() * nCols())
          << "SparseMatrix reshape: "
          << "New number of elements must be equal to "
          << "old number of elements";
      } // End pre-conditions

      if (!isCompact())
        compact();

      const size_type old_nrows = nRows();
      const size_type old_ncols = nCols();

      size_type *ind_it = ind_mem_;
      value_type *nz_it = nz_mem_;
      size_type count = 0, last_row = 0;

      size_type *old_nnzr = new size_type [old_nrows];
      std::copy(nnzr_, nnzr_ + old_nrows, old_nnzr);

      nrows_max_ = std::max<size_type>(8, new_nrows);

      delete [] nnzr_;
      nnzr_ = new size_type [nrows_max_];
      delete [] ind_;
      ind_ = new size_type* [nrows_max_];
      delete [] nz_;
      nz_ = new value_type* [nrows_max_];

      std::fill(nnzr_, nnzr_ + nrows_max_, (size_type)0);
      std::fill(ind_, ind_ + nrows_max_, (size_type*)0);
      std::fill(nz_, nz_ + nrows_max_, (value_type*)0);

      delete [] indb_;
      indb_ = new size_type [new_ncols];
      delete [] nzb_;
      nzb_ = new value_type [new_ncols];

      std::fill(indb_, indb_ + new_ncols, (size_type)0);
      std::fill(nzb_, nzb_ + new_ncols, (value_type)0);

      for (size_type row = 0; row != old_nrows; ++row) {
        size_type *ind_end = ind_it + old_nnzr[row];
        while (ind_it != ind_end) {
          size_type old_idx = row * old_ncols + *ind_it;
          size_type new_row = old_idx / new_ncols;
          size_type new_col = old_idx % new_ncols;
          *ind_it = new_col;
          if (new_row != last_row) {
            nnzr_[last_row] = count;
            last_row = new_row;
            count = 0;
          }
          ++ind_it; ++nz_it;
          ++count;
        }
      }

      nnzr_[last_row] = count;

      size_type *ind_ptr = ind_mem_;
      value_type *nz_ptr = nz_mem_;

      for (size_type row = 0; row != new_nrows; ++row) {
        ind_[row] = ind_ptr;
        ind_ptr += nnzr_[row];
        nz_[row] = nz_ptr;
        nz_ptr += nnzr_[row];
      }

      delete [] old_nnzr;
      old_nnzr = 0;

      nrows_ = new_nrows;
      ncols_ = new_ncols;
    }

    //--------------------------------------------------------------------------------
    /**
     * Deletes the row at the index specified. The resulting matrix has one less row.
     */
    void deleteRow(size_type del_row)
    {
      { // Pre-conditions
        assert_valid_row_(del_row, "deleteRow");
      } // End pre-conditions

      if (isCompact())
        decompact();

      const size_type nrows = nRows();

      nnzr_[del_row] = 0;
      delete [] ind_[del_row];
      ind_[del_row] = 0;
      delete [] nz_[del_row];
      nz_[del_row] = 0;

      for (size_type row = del_row + 1; row != nrows; ++row) {
        nnzr_[row-1] = nnzr_[row];
        ind_[row-1] = ind_[row];
        nz_[row-1] = nz_[row];
      }

      nnzr_[nrows-1] = 0;
      ind_[nrows-1] = 0;
      nz_[nrows-1] = 0;

      -- nrows_;
    }

    //--------------------------------------------------------------------------------
    /**
     * Deletes specified rows.
     * The indices of the rows are passed in a range [del..del_end).
     * The range can be contiguous (std::vector) or not (std::list, std::map).
     * The matrix can end up empty if all the rows are removed.
     * If the list of rows to remove is empty, the matrix is unchanged.
     *
     * WARNING: the row indices need to be passed without duplicates,
     * in strictly increasing order.
     *
     * @param del [InputIterator<size_type>] iterator to the beginning of the range
     *  that contains the indices of the rows to be deleted
     * @param del_end [InputIterator<size_type>] iterator to one past the end of the
     *  range that contains the indices of the rows to be deleted
     *
     * @b Exceptions:
     *  @li If a row index < 0 || >= nrows.
     *  @li If row indices are not passed in strictly increasing order.
     *  @li If del_end - del < 0 || del_end - del > nrows.
     *
     * TODO add option to pass indices in any order, with repetitions
     */
    template <typename InputIterator>
    inline void deleteRows(InputIterator del_it, InputIterator del_end)
    {
      ptrdiff_t n_del = del_end - del_it;

      if (n_del <= 0 || nRows() == 0)
        return;

      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);

        if (n_del > 0) {

          NTA_CHECK(n_del <= (ptrdiff_t)nRows())
            << "SparseMatrix::deleteRows(): "
            << " Passed more indices of rows to delete"
            << " than there are rows";

#ifdef NTA_ASSERTIONS_ON // to avoid compilation of loop

          InputIterator d = del_it, d_next = del_it + 1;
          while (d < del_end - 1) {
            NTA_CHECK(0 <= *d && *d < nRows())
              << "SparseMatrix::deleteRows(): "
              << "Invalid row index: " << *d
              << " - Row indices should be between 0 and " << nRows();
            NTA_CHECK(*d < *d_next)
              << "SparseMatrix::deleteRows(): "
              << "Invalid row indices " << *d << " and " << *d_next
              << " - Row indices need to be passed "
              << "in strictly increasing order";
            ++d; ++d_next;
          }

          NTA_CHECK(0 <= *d && *d < nRows())
            << "SparseMatrix::deleteRows(): "
            << "Invalid row index: " << *d
            << " - Row indices should be between 0 and " << nRows();
#endif
        }
        /* Too noisy
           else if (n_del == 0) {

           NTA_WARN
           << "SparseMatrix::deleteRows(): "
           << "Nothing to delete";

           } else if (n_del < 0) {

           NTA_WARN
           << "SparseMatrix::deleteRows(): "
           << "Invalid pointers - Won't do anything";
           }
        */
      } // End pre-conditions

      if (isCompact())
        decompact();

      const size_type nrows = nRows();
      size_type i_new = 0;

      for (size_type i_old = 0; i_old != nrows; ++i_old) {
        if (del_it != del_end && i_old == *del_it) {
          nnzr_[i_old] = 0;
          delete [] ind_[i_old];
          delete [] nz_[i_old];
          ++del_it;
        } else {
          nnzr_[i_new] = nnzr_[i_old];
          ind_[i_new] = ind_[i_old];
          nz_[i_new] = nz_[i_old];
          ++i_new;
        }
      }

      nrows_ = i_new;

      for (; i_new != nrows_max_; ++i_new) {
        nnzr_[i_new] = 0;
        ind_[i_new] = 0;
        nz_[i_new] = 0;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Deletes all the rows whose indices are specified in the container.
     */
    template <typename Container>
    inline void deleteRows(const Container& c)
    {
      deleteRows(c.begin(), c.end());
    }

    //--------------------------------------------------------------------------------
    /**
     * Deletes column at specified index. The resulting matrix has one less column.
     */
    void deleteCol(size_type del_col)
    {
      { // Pre-conditions
        assert_valid_col_(del_col, "deleteCol");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {

        if (isRowZero(row))
          continue;

        size_type *ind = ind_begin_(row), *ind_end = ind_end_(row);
        value_type *nz = nz_begin_(row);
        size_type *lb = std::lower_bound(ind, ind_end, del_col);

        if (lb != ind_end && *lb == del_col) {

          nz += lb - ind + 1;
          ind = lb + 1;
          while (ind != ind_end) {
            *(ind - 1) = *ind - 1;
            *(nz - 1) = *nz;
            ++ind; ++nz;
          }

          -- nnzr_[row];

        } else if (lb != ind_end) {

          ind = lb;
          while (ind != ind_end) {
            -- *ind;
            ++ind;
          }
        }
      }

      // This is wrong if del_col is larger
      // than the actual number of row, but that condition
      // is caught by the pre-conditions when compiling
      // with assertions on.
      -- ncols_;
    }

    //--------------------------------------------------------------------------------
    /**
     * Deletes specified columns.
     * The indices of the columns are passed in a range [del..del_end).
     * The range can be contiguous (std::vector) or not (std::list, std::map).
     * The matrix can end up empty if all the columns are removed.
     * If the list of columns to remove is empty, the matrix is unchanged.
     *
     * WARNING: the columns indices need to be passed without duplicates,
     * in strictly increasing order.
     *
     * @param del [InputIterator<size_type>] iterator to the beginning of the range
     *  that contains the indices of the columns to be deleted
     * @param del_end [InputIterator<size_type>] iterator to one past the end of the
     *  range that contains the indices of the columns to be deleted
     *
     * @b Exceptions:
     *  @li If a column index < 0 || >= ncols.
     *  @li If column indices are not passed in strictly increasing order.
     *  @li If del_end - del < 0 || del_end - del > ncols.
     */
    template <typename InputIterator>
    inline void deleteCols(InputIterator del_it, InputIterator del_end)
    {
      ptrdiff_t n_del = del_end - del_it;

      if (n_del <= 0 || nCols() == 0)
        return;

      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);

        if (n_del > 0) {

          NTA_ASSERT(n_del <= (ptrdiff_t)nCols())
            << "SparseMatrix::deleteCols(): "
            << " Passed more indices of columns to delete"
            << " than there are columns";

#ifdef NTA_ASSERTIONS_ON // to avoid compilation of loop

          InputIterator d = del_it, d_next = del_it + 1;
          while (d < del_end - 1) {
            NTA_ASSERT(0 <= *d && *d < nCols())
              << "SparseMatrix::deleteCols(): "
              << "Invalid column index: " << *d
              << " - Col indices should be between 0 and " << nCols();
            NTA_ASSERT(*d < *d_next)
              << "SparseMatrix::deleteCols(): "
              << "Invalid column indices " << *d << " and " << *d_next
              << " - Col indices need to be passed "
              << "in strictly increasing order";
            ++d; ++d_next;
          }

          NTA_ASSERT(0 <= *d && *d < nCols())
            << "SparseMatrix::deleteCols(): "
            << "Invalid column index: " << *d
            << " - Col indices should be between 0 and " << nCols();
#endif
        }
        /* Too noisy
           else if (n_del == 0) {

           NTA_WARN
           << "SparseMatrix::deleteCols(): "
           << "Nothing to delete";

           } else if (n_del < 0) {

           NTA_WARN
           << "SparseMatrix::deleteCols(): "
           << "Invalid pointers - Won't do anything";
           }
        */
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {

        size_type j = 0;
        InputIterator d = del_it;
        size_type *ind = ind_[row], *ind_old = ind, *ind_end = ind + nnzr_[row];
        value_type *nz = nz_[row], *nz_old = nz;

        while (ind_old != ind_end && d != del_end) {
          if (*d == *ind_old) {
            ++d; ++j;
            ++ind_old;
            ++nz_old;
          } else if (*d < *ind_old) {
            ++d; ++j;
          } else {
            *ind++ = *ind_old++ - j;
            *nz++ = *nz_old++;
          }
        }

        while (ind_old != ind_end) {
          *ind++ = *ind_old++ - j;
          *nz++ = *nz_old++;
        }

        nnzr_[row] = size_type(ind - ind_[row]);
      }

      // This is wrong if there are indices to delete larger
      // than the actual number of row, but that condition
      // is caught by the pre-conditions when compiling
      // with assertions on.
      ncols_ -= size_type(n_del);
    }

    //--------------------------------------------------------------------------------
    /**
     * Deletes all columns whose indices are specified in the container.
     */
    template <typename Container>
    inline void deleteCols(const Container& c)
    {
      deleteCols(c.begin(), c.end());
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds a row of non-zeros to this SparseMatrix, from two iterators, one on
     * a container of indices, the other on a container of values corresponding
     * to those indices.
     *
     * WARNING: the iterators need to point to the first element of a contiguous
     * array of memory, something like std::vector rather than std::list.
     *
     * WARNING: send in non-zeros without duplicate indices,
     * in increasing order of indices, without zeros.
     * No check is done for duplicates, orders or zeros in
     * NDEBUG mode. No check is done for zeros/non-zeros only!!!!!
     *
     * @param nnzr [0 <= size_type] number of non-zeros passed in
     * @param ind [InputIterator1<size_type>] input iterator for indices of non-zeros
     * @param nz [InputIterator2<value_type>] input iterator for values of non-zeros
     *
     * @b Exceptions:
     *  @li Not enough memory (error)
     *  @li nnzr <= 0
     *  @li Index of non-zero out of bounds (< 0 or > ncols)
     *  @li Indices of non-zeros not in increasing order
     *  @li Duplicates in indices
     *  @li Zero passed in
     */
    template <typename InputIterator1, typename InputIterator2>
    inline size_type
    addRow(InputIterator1 ind_it, InputIterator1 ind_end, InputIterator2 nz_it,
           bool zero_permissive =false)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator1);
        ASSERT_INPUT_ITERATOR(InputIterator2);

        if (!zero_permissive)
          assert_valid_ivp_range_(nCols(), ind_it, ind_end, nz_it, "addRow");
      } // End pre-conditions

      const size_type row_num = nRows();
      const size_type nnzr = (size_type) (ind_end - ind_it);

      if (isCompact())
        decompact();

      if (row_num > nrows_max_-1)
        reserve_(row_num);

      nnzr_[row_num] = nnzr;

      if (nnzr > 0) {

        ind_[row_num] = new size_type[nnzr];
        nz_[row_num] = new value_type[nnzr];

        size_type* ind_ptr = ind_[row_num];
        value_type* nz_ptr = nz_[row_num];

        while (ind_it != ind_end) {
          *ind_ptr = *ind_it;
          *nz_ptr = *nz_it;
          ++ind_ptr; ++nz_ptr;
          ++ind_it; ++nz_it;
        }

      } else {

        ind_[row_num] = 0;
        nz_[row_num] = 0;
      }

      ++nrows_;
      return row_num;
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds a row to this SparseMatrix, from an iterator into a dense container.
     * The iterator needs to span ncols values.
     *
     * Mutating, can increase the number of non-zeros, O(nnzr + K)
     *
     * @param x [InputIterator<value_type>] input iterator for row values
     *
     * @b Exceptions:
     *  @li Not enough memory (error)
     *
     * TODO add flag for case where row is already "clean"
     */
    template <typename InputIterator>
    inline size_type addRow(InputIterator x_begin)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);
      } // End pre-conditions

      size_type *indb_it = indb_;
      value_type val, *nzb_it = nzb_;
      InputIterator x_it = x_begin, x_end = x_begin + nCols();

      while (x_it != x_end) {
        val = *x_it;
        if (!isZero_(val)) {
          *indb_it = size_type(x_it - x_begin);
          *nzb_it = val;
          ++indb_it; ++nzb_it;
        }
        ++x_it;
      }

      return addRow(indb_, indb_it, nzb_);
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds a column to this SparseMatrix, from two input iterators, one for the
     * indices of the non-zeros, and one for the value of the non-zeros.
     *
     * Mutating, can increase the number of non-zeros, O(nnzr + K)
     *
     * @param ind_it [InputIterator<size_type>] input iterator for indices
     *  of non-zeros
     * @ param nz_it [InputIterator<value_type>] input iterator for values
     *  of non-zeros
     *
     * @b Exceptions:
     *  @li Not enough memory (error)
     *
     * TODO add flag for case where row is already "clean"
     * TODO return new number of columns, as in addRow
     */
    template <typename InputIterator1, typename InputIterator2>
    inline void
    addCol(InputIterator1 ind_it, InputIterator1 ind_end, InputIterator2 nz_it)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator1);
        ASSERT_INPUT_ITERATOR(InputIterator2);
        assert_valid_ivp_range_(nRows(), ind_it, ind_end, nz_it, "addCol");
      } // End pre-conditions

      if (isCompact())
        decompact();

      while (ind_it != ind_end) {
        size_type row = *ind_it;
        size_type old_nnzr = nnzr_[row];
        size_type new_nnzr = old_nnzr + 1;
        size_type *new_ind = new size_type [new_nnzr];
        value_type * new_nz = new value_type [new_nnzr];
        std::copy(ind_[row], ind_[row] + old_nnzr, new_ind);
        std::copy(nz_[row], nz_[row] + old_nnzr, new_nz);
        delete [] ind_[row];
        ind_[row] = new_ind;
        delete [] nz_[row];
        nz_[row] = new_nz;
        ind_[row][old_nnzr] = nCols();
        nz_[row][old_nnzr] = *nz_it;
        ++ nnzr_[row];
        ++ind_it; ++nz_it;
      }

      ++ ncols_;
      reAllocateBuffers_(ncols_);
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds a column to this SparseMatrix, from an input iterator on a dense
     * array of values.
     *
     * Mutating, can increase the number of non-zeros, O(nnzr + K)
     *
     * @param x_begin [InputIterator<size_type>] input iterator for values
     *
     * @b Exceptions:
     *  @li Not enough memory (error)
     *
     * TODO add flag for case where row is already "clean"
     */
    template <typename InputIterator>
    inline void addCol(InputIterator x_begin)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);
      } // End pre-conditions

      if (isCompact())
        decompact();

      bool new_non_zeros = false;

      ITERATE_ON_ALL_ROWS {
        value_type val = *x_begin;
        if (! isZero_(val)) {
          new_non_zeros = true;
          size_type old_nnzr = nnzr_[row];
          size_type new_nnzr = old_nnzr + 1;
          size_type *new_ind = new size_type [new_nnzr];
          value_type * new_nz = new value_type [new_nnzr];
          std::copy(ind_[row], ind_[row] + old_nnzr, new_ind);
          std::copy(nz_[row], nz_[row] + old_nnzr, new_nz);
          delete [] ind_[row];
          ind_[row] = new_ind;
          delete [] nz_[row];
          nz_[row] = new_nz;
          ind_[row][old_nnzr] = nCols();
          nz_[row][old_nnzr] = val;
          ++ nnzr_[row];
        }
        ++x_begin;
      }

      if (new_non_zeros) {
        ++ ncols_;
        reAllocateBuffers_(ncols_);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Appends the rows of another sparse matrix to this one.
     * The number of row in the resulting matrix is the sum of the number of rows
     * in this matrix before append, and the other matrix. If the other matrix
     * has more columns, this matrix is resized.
     */
    inline void append(const self_type& other, bool zero_permissive =false)
    {
      if (other.nCols() > this->nCols())
        this->resize(nRows(), other.nCols());

      for (size_type row = 0; row != other.nRows(); ++row)
        this->addRow(other.ind_begin_(row),
                     other.ind_end_(row),
                     other.nz_begin_(row),
                     zero_permissive);
    }

    //--------------------------------------------------------------------------------
    /**
     * Duplicates given row. The duplicated row is a new row at the end of the
     * matrix.
     */
    inline void duplicateRow(size_type row)
    {
      { // Pre-conditions
        assert_valid_row_(row, "duplicateRow");
      } // End pre-conditions

      addRow(ind_begin_(row), ind_end_(row), nz_begin_(row));
    }

    //--------------------------------------------------------------------------------
    // SET/GET
    //--------------------------------------------------------------------------------

    /**
     * Sets the value at (i, j) to 0.
     * Doesn't reallocate memory, and doesn't decompact the internal
     * storage of the non-zeros.
     *
     * @b Complexity:
     *  @li O(log(nnzr) + 2*nnzr)
     *
     * @b Exceptions:
     *  @li If i < 0 or i >= nrows
     *  @li If j < 0 or j >= ncols
     */
    inline void setZero(size_type row, size_type col, bool resizeYesNo=false)
    {
      { // Pre-conditions
        if (!resizeYesNo)
          assert_valid_row_col_(row, col, "setZero");
      } // End pre-conditions

      if (resizeYesNo)
        resize(std::max(row+1, nRows()), std::max(row+1, nCols()));

      size_type *it = pos_(row, col);

      if (it != ind_end_(row) && *it == col)
        erase_(row, it);
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets diagonal to zero.
     * For a rectangular matrix, this is the pseudo-diagonal on the square
     * sub-matrix of side min(nRows, nCols).
     *
     * @b Complexity:
     *  @li O(min(nrows, ncols) * (log(nnzr) + 2*nnzr))
     */
    inline void setDiagonalToZero()
    {
      size_type m = std::min(nRows(), nCols());

      for (size_type i = 0; i != m; ++i)
        setZero(i, i);
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets the diagonal or pseudo-diagonal to given value.
     */
    inline void setDiagonalToVal(const value_type& val)
    {
      size_type m = std::min(nRows(), nCols());

      for (size_type i = 0; i != m; ++i)
        set(i, i, val);
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets diagonal to a give vector.
     */
    template <typename InIter>
    inline void setDiagonal(InIter begin)
    {
      size_type m = std::min(nRows(), nCols());

      for (size_type i = 0; i != m; ++i)
        set(i, i, *begin++);
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets the value at (i, j) to val, when val != 0.
     * Decompacts the internal storage of this sparse matrix if needed.
     * Resizes this sparse matrix if resizeYesNo == true, but that will only
     * grow the matrix, NEVER reducs its dimensions.
     *
     * @param i [0 <= size_type < nrows] the row index
     * @param j [0 <= size_type < ncols] the col index
     * @param val [value_type != 0] the value to set at (i,j)
     * @param resizeYesNo [bool] whether to increase the size of this matrix or not
     *
     * @b Complexity:
     *  @li Worst case: O(nrows + log(nnzr) + nnz + 4*nnzr) (if decompact in resize)
     *
     * @b Exceptions:
     *  @li If i < 0 or i >= nrows (assert)
     *  @li If j < 0 or j >= ncols (assert)
     *  @li If val == 0 (assert)
     */
    inline void setNonZero(size_type i, size_type j, const value_type& val,
                           bool resizeYesNo=false)
    {
      { // Pre-conditions
        if (!resizeYesNo)
          assert_valid_row_col_(i,j,"setNonZero");
        assert_not_zero_value_(val, "setNonZero");
      } // End pre-conditions

      if (resizeYesNo)
        resize(std::max(i+1, nRows()), std::max(j+1, nCols()));

      size_type *ind = ind_begin_(i), *ind_end = ind_end_(i);
      size_type *it = pos_(i, j);

      if (it != ind_end && *it == j) {

        // We have found a non-zero at j, and
        // we can modifty it in place, without changing
        // the memory allocation. We don't need to
        // decompact the representation.
        nz_[i][it - ind] = val;

      } else {

        insertNewNonZero_(i, j, it, val);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets the value at (i, j) to val.
     * If resizeYesNo is true, will increase the size of this matrix appropriately,
     * but will NEVER reduces its dimensions.
     *
     * @param i [0 <= size_type < nrows] the row index
     * @param j [0 <= size_type < ncols] the col index
     * @param val [value_type] the value to set at (i,j)
     * @param resizeYesNo [bool] whether to increase the size of this matrix or not
     *
     * @b Complexity:
     *  @li Worst case: O(nrows + log(nnzr) + nnz + 4*nnzr) (if decompact in resize)
     *
     * @b Exceptions:
     *  @li If i < 0 or i >= nrows
     *  @li If j < 0 or j >= ncols
     */
    inline void set(size_type i, size_type j, const value_type& val,
                    bool resizeYesNo=false)
    {
      { // Pre-conditions
        if (!resizeYesNo)
          assert_valid_row_col_(i,j,"set");
      } // End pre-conditions

      if (resizeYesNo)
        resize(std::max(i+1, nRows()), std::max(j+1, nCols()));

      if (isZero_(val))
        setZero(i, j);
      else
        setNonZero(i, j, val);
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets all the elements in given box to zero.
     */
    inline void setBoxToZero(size_type row_begin, size_type row_end,
                             size_type col_begin, size_type col_end)
    {
      { // Pre-conditions
        assert_valid_row_range_(row_begin, row_end, "setBoxToZero");
        assert_valid_col_range_(col_begin, col_end, "setBoxToZero");
      } // End pre-conditions

      for (size_type row = row_begin; row != row_end; ++row) {
        size_type *ind = NULL, *ind_end = NULL;
        difference_type offset = pos_(row, col_begin, col_end, ind, ind_end);
        if (ind != ind_end_(row)) {
          value_type *nz = nz_begin_(row) + offset;
          std::copy(ind_end, ind_end_(row), ind);
          std::copy(nz + (ind_end - ind), nz_end_(row), nz);
          nnzr_[row] -= ind_end - ind;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets all the elements in given box to given value.
     */
    inline void setBox(size_type row_begin, size_type row_end,
                       size_type col_begin, size_type col_end,
                       const value_type& val)
    {
      { // Pre-conditions
        assert_valid_row_range_(row_begin, row_end, "setBox");
        assert_valid_col_range_(col_begin, col_end, "setBox");
      } // End pre-conditions

      if (isZero_(val))
        setBoxToZero(row_begin, row_end, col_begin, col_end);

      size_type box_ncols = col_end - col_begin;

      for (size_type row = row_begin; row != row_end; ++row) {

        size_type *ind_begin = NULL, *ind_end = NULL;
        difference_type offset = pos_(row, col_begin, col_end, ind_begin, ind_end);
        value_type *nz_begin = nz_begin_(row) + offset;

        if ((size_type)(ind_end - ind_begin) == box_ncols) {

          std::fill(nz_begin, nz_begin + box_ncols, val);

        } else {

          decompact();

          std::copy(ind_begin_(row), ind_begin, indb_);
          std::copy(nz_begin_(row), nz_begin, nzb_);
          size_type *indb = indb_ + offset;
          value_type *nzb = nzb_ + offset;
          for (size_type col = col_begin; col != col_end; ++col) {
            *indb++ = col;
            *nzb++ = val;
          }
          std::copy(ind_end, ind_end_(row), indb);
          std::copy(nz_begin + (ind_end - ind_begin), nz_end_(row), nzb);

          size_type new_nnzr = (size_type)(indb - indb_ + ind_end_(row) - ind_end);

          delete [] ind_[row];
          delete [] nz_[row];
          ind_[row] = new size_type [new_nnzr];
          nz_[row] = new value_type [new_nnzr];
          std::copy(indb_, indb_ + new_nnzr, ind_[row]);
          std::copy(nzb_, nzb_ + new_nnzr, nz_[row]);
          nnzr_[row] = new_nnzr;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Increments (i,j) by delta.
     * Optionally resize the matrix if (i,j) out of current bounds.
     */
    inline void increment(size_type i, size_type j, value_type delta =1,
                          bool resizeYesNo =false)
    {
      { // Pre-conditions
        if (!resizeYesNo)
          assert_valid_row_col_(i,j,"increment");
      } // End pre-conditions

      if (isZero_(delta))
        return;

      if (resizeYesNo)
        resize(std::max(i+1, nRows()), std::max(j+1, nCols()));

      size_type *ind = ind_begin_(i), *ind_end = ind_end_(i);
      size_type *it = pos_(i,j);

      if (it != ind_end && *it == j) {
        nz_[i][it - ind] += delta;
      } else {
        insertNewNonZero_(i, j, it, delta);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Increments (i,j) with delta != 0.
     */
    inline void incrementWNZ(size_type i, size_type j, value_type delta =1,
                             bool resizeYesNo =false)
    {
      { // Pre-conditions
        if (!resizeYesNo)
          assert_valid_row_col_(i,j,"increment");
        NTA_ASSERT(!isZero_(delta))
          << "SparseMatrix incrementWNZ: Expects non-zero delta only";
      } // End pre-conditions

      if (resizeYesNo)
        resize(std::max(i+1, nRows()), std::max(j+1, nCols()));

      size_type *ind = ind_begin_(i), *ind_end = ind_end_(i);
      size_type *it = pos_(i,j);

      if (it != ind_end && *it == j) {
        nz_[i][it - ind] += delta;
      } else {
        insertNewNonZero_(i, j, it, delta);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Expects sorted ranges of indices, possibly non-contiguous.
     */
    template <typename InputIterator>
    inline void incrementOnOuterWNZ(InputIterator i_begin, InputIterator i_end,
                                    InputIterator j_begin, InputIterator j_end,
                                    value_type delta =1)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);
        assert_valid_sorted_index_range_(nRows(), i_begin, i_end,
                                         "incrementOnOuterWNZ");
        assert_valid_sorted_index_range_(nCols(), j_begin, j_end,
                                         "incrementOnOuterWNZ");
        NTA_ASSERT(!isZero_(delta))
          << "SparseMatrix incrementOnOuterWNZ: Expects non-zero delta only";
      } // End pre-conditions

      for (InputIterator i = i_begin; i != i_end; ++i) {
        for (InputIterator j = j_begin; j != j_end; ++j) {
          size_type *ind = ind_begin_(*i), *ind_end = ind_end_(*i);
          size_type *it = std::lower_bound(ind, ind_end, *j);
          if (it != ind_end && *it == *j) {
            nz_[*i][it - ind] += delta;
          } else {
            insertNewNonZero_(*i,*j,it,delta);
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Expects sorted ranges of indices, possibly non-contiguous.
     */
    template <typename InputIterator>
    inline void incrementOnOuterWNZWThreshold(InputIterator i_begin, InputIterator i_end,
                                              InputIterator j_begin, InputIterator j_end,
                                              value_type threshold,
                                              value_type delta =1)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);
        assert_valid_sorted_index_range_(nRows(), i_begin, i_end,
                                         "incrementOnOuterWNZ");
        assert_valid_sorted_index_range_(nCols(), j_begin, j_end,
                                         "incrementOnOuterWNZ");
        NTA_ASSERT(!isZero_(delta))
          << "SparseMatrix incrementOnOuterWNZ: Expects non-zero delta only";
      } // End pre-conditions

      for (InputIterator i = i_begin; i != i_end; ++i) {
        for (InputIterator j = j_begin; j != j_end; ++j) {
          size_type *ind = ind_begin_(*i), *ind_end = ind_end_(*i);
          for (size_type *it = ind; it != ind_end; ++it)
            if (*it == *j && nz_[*i][it - ind] > threshold)
              nz_[*i][it - ind] += delta;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the value of the element at row index i and column index j.
     *
     * @param row [0 <= size_type < nrows] the row index
     * @param col [0 <= size_type < ncols] the col index
     * @retval [value_type] the value at (row, col)
     *
     * @b Complexity:
     *  @li O(log(nnzr))
     *
     * @b Exceptions:
     *  @li If row < 0 or row >= nrows
     *  @li If col < 0 or col >= ncols
     */
    inline value_type get(size_type row, size_type col) const
    {
      { // Pre-conditions
        assert_valid_row_col_(row, col, "get");
      } // End pre-conditions

      difference_type offset = col_(row, col);

      if (offset >= 0)
        return nz_[row][offset];

      return value_type(0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Not documented. Don't use, unless you really, really know what you are doing
     */
    inline const_row_nz_index_iterator row_nz_index_begin(size_type row) const
    {
      return ind_begin_(row);
    }

    /**
     * Not documented. Don't use, unless you really, really know what you are doing
     */
    inline const_row_nz_index_iterator row_nz_index_end(size_type row) const
    {
      return ind_end_(row);
    }

    /**
     * Not documented. Don't use, unless you really, really know what you are doing
     */
    inline const_row_nz_value_iterator row_nz_value_begin(size_type row) const
    {
      return nz_begin_(row);
    }

    /**
     * Not documented. Don't use, unless you really, really know what you are doing
     */
    inline const_row_nz_value_iterator row_nz_value_end(size_type row) const
    {
      return nz_end_(row);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns all the non-zeros in this sparse matrix, with their indices,
     * as ijv instances.
     */
    template <typename OutputIterator>
    inline void getAllNonZeros(OutputIterator ijv_iterator) const
    {
      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          ijv_iterator->i(row);
          ijv_iterator->j(*ind);
          NTA_ASSERT(!isZero_(*nz))
            << "SparseMatrix::getAllNonZeros (ijv): "
            << "Zero at " << row << ", " << *ind << ": " << *nz
            << " epsilon= " << nta::Epsilon;
          ijv_iterator->v(*nz);
          ++ijv_iterator;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns all non-zeros inside the rectangular area specified.
     * The rectangular area has shape [row_begin, row_end) X [col_begin, col_end).
     */
    template <typename OutputIterator>
    inline void getAllNonZeros(size_type row_begin, size_type row_end,
                               size_type col_begin, size_type col_end,
                               OutputIterator ijv_iterator) const
    {
      ITERATE_ON_ALL_ROWS {
        if (row >= row_begin && row < row_end) {
          ITERATE_ON_ROW {
            if (*ind >= col_begin && *ind < col_end) {
              ijv_iterator->i(row);
              ijv_iterator->j(*ind);
              NTA_ASSERT(!isZero_(*nz))
                << "SparseMatrix::getAllNonZeros (rect): "
                << "Zero at " << row << ", " << *ind << ": " << *nz
                << " epsilon= " << nta::Epsilon;
              ijv_iterator->v(*nz);
              ++ijv_iterator;
            }
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns all the non-zeros in this matrix to three ranges, one for the row
     * indices of the non-zeros, one for the col indices, and one for the value
     * of the non-zeros.
     */
    template <typename OutputIterator1, typename OutputIterator2>
    inline void getAllNonZeros(OutputIterator1 nz_i, OutputIterator1 nz_j,
                               OutputIterator2 nz_val) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator1, size_type);
        ASSERT_OUTPUT_ITERATOR(OutputIterator2, value_type);
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          *nz_i = row;
          *nz_j = *ind;
          NTA_ASSERT(!isZero_(*nz))
            << "SparseMatrix::getAllNonZeros (3 lists): "
            << "Zero at " << row << ", " << *ind << ": " << *nz
            << " epsilon= " << nta::Epsilon;
          *nz_val = *nz;
          ++nz_i; ++nz_j;
          ++nz_val;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Clears this matrix and sets all the non-zeros from the passed in list.
     * In contrast to set(i,j,v), we don't systemacially weed-out the values
     * too close to zero, because this function can be used internally by other
     * classes or algorithms, and it would be too slow to always check
     * the non-zeros.
     *
     * If the flag "clean" is true, then we assume that the non-zeros are
     * unique, in increasing lexicographic order, and have values > epsilon.
     * If "clean" is false, we sort the values and remove the non-zeros
     * below epsilon, which is a lot slower.
     *
     * In debug mode, we detect and throw an assert if zeros are passed
     * or if the non-zeros are not in order, or if there are duplicate locations
     * for non-zeros.
     */
    template <typename InputIterator1, typename InputIterator2>
    inline void setAllNonZeros(size_type nrows, size_type ncols,
                               InputIterator1 i_begin, InputIterator1 i_end,
                               InputIterator1 j_begin, InputIterator1 j_end,
                               InputIterator2 v_begin, InputIterator2 v_end,
                               bool clean =true)
    {
      { // Pre-conditions
        const char* where = "SparseMatrix::setAllNonZeros: ";

        ASSERT_INPUT_ITERATOR(InputIterator1);
        ASSERT_INPUT_ITERATOR(InputIterator2);

        NTA_ASSERT(i_end - i_begin == j_end - j_begin)
          << where << "Inconsistent index ranges";
        NTA_ASSERT(v_end - v_begin == i_end - i_begin)
          << where << "Inconsistent value range";

        ASSERT_VALID_RANGE(i_begin, i_end, where);
        for (InputIterator1 ii = i_begin; ii != i_end; ++ii)
          NTA_ASSERT(*ii < nrows)
            << where << "Invalid row index: " << *ii
            << " - Should be >= 0 and < " << nrows;

        ASSERT_VALID_RANGE(j_begin, j_end, where);
        for (InputIterator1 jj = j_begin; jj != j_end; ++jj)
          NTA_ASSERT(*jj < ncols)
            << where << "Invalid col index: " << *jj
            << " - Should be >= 0 and < " << ncols;

#ifdef NTA_ASSERTIONS_ON

        if (clean) {

          for (InputIterator2 it_v = v_begin; it_v != v_end; ++it_v)
            NTA_ASSERT(!isZero_(*it_v))
              << where << "Passed in zero: " << *it_v
              << " epsilon= " << nta::Epsilon;

          if (i_begin != i_end) {
            InputIterator1 ii = i_begin, jj = j_begin, iip = ii, jjp = jj;
            InputIterator2 vv = v_begin, vvp = vv;
            ++ii; ++jj;
            for (; ii != i_end; ++ii, ++jj, ++vv) {
              NTA_ASSERT(*iip < *ii || *jjp < *jj)
                << where
                << "Passed in duplicate or out-of-order non-zeros: "
                << *vvp << " and " << *vv
                << ", (" << *iip << ", " << *jjp << ") and ("
                << *ii << ", " << *jj << ")";
              iip = ii; jjp = jj; vvp = vv;
            }
          }
        }

#endif
      } // End pre-conditions

      // Used only if not clean, to hold unique locations of non-zeros
      typedef std::set<IJV, typename IJV::lexicographic> S;
      typename S::const_iterator it;
      S s;

      InputIterator1 it_i = i_begin, it_j = j_begin;
      InputIterator2 it_v = v_begin;

      deallocate_();
      allocate_(nrows,ncols);
      nrows_ = nrows;
      ncols_ = ncols;

      size_type nnz = 0;

      if (clean) {

        nnz = (size_type)(i_end - i_begin);
        for (; it_i != i_end; ++it_i)
          ++ nnzr_[*it_i];

      } else {

        for (; it_i != i_end; ++it_i, ++it_j, ++it_v)
          if (!isZero_(*it_v)) {
            IJV ijv(*it_i, *it_j, *it_v);
            it = s.find(ijv);
            if (it == s.end()) {
              s.insert(ijv);
              ++ nnzr_[*it_i];
            }
          }

        nnz = s.size();
      }

      ind_mem_ = new size_type [nnz];
      nz_mem_ = new value_type [nnz];
      size_type *ind_ptr = ind_mem_;
      value_type *nz_ptr = nz_mem_;

      it_i = i_begin; it_j = j_begin; it_v = v_begin;

      if (clean) {

        for (size_type i = 0; i != nrows; ++i) {
          ind_[i] = ind_ptr;
          nz_[i] = nz_ptr;
          for (size_type k = 0; k != nnzr_[i]; ++k) {
            *ind_ptr++ = *it_j;
            *nz_ptr++ = *it_v;
            ++it_j;
            ++it_v;
          }
        }

      } else {

        it = s.begin();

        for (size_type i = 0; i != nrows; ++i) {
          ind_[i] = ind_ptr;
          nz_[i] = nz_ptr;
          for (size_type k = 0; k != nnzr_[i]; ++k, ++it) {
            *ind_ptr++ = it->j();
            *nz_ptr++ = it->v();
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the non-zeros in a sub-matrix. The positions of the non-zeros are
     * relative to the (0,0) of this matrix.
     */
    template <typename OutputIterator1, typename OutputIterator2>
    inline void getNonZerosInBox(size_type row_begin, size_type row_end,
                                 size_type col_begin, size_type col_end,
                                 OutputIterator1 nz_i, OutputIterator1 nz_j,
                                 OutputIterator2 nz_v) const
    {
      { // Pre-conditions
        assert_valid_row_range_(row_begin, row_end, "getNonZerosInBox");
        assert_valid_col_range_(col_begin, col_end, "getNonZerosInBox");
      } // End pre-conditions

      for (size_type row = row_begin; row != row_end; ++row) {
        if (!nonZerosInRowRange(row, col_begin, col_end))
          continue;
        size_type *c1 = pos_(row, col_begin);
        size_type *c2 = col_end == nCols() ? ind_end_(row) : pos_(row, col_end);
        value_type *nz = nz_begin_(row) + (c1 - ind_begin_(row));
        for (size_type *col = c1; col != c2; ++col) {
          *nz_i++ = row;
          *nz_j++ = *col;
          NTA_ASSERT(!isZero_(*nz))
            << "SparseMatrix::getNonZerosInBox: "
            << "Zero at " << row << ", " << *col << ": " << *nz
            << " epsilon= " << nta::Epsilon;
          *nz_v++ = *nz++;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Sort all values according to predicate. Return values and i,j indices.
     */
    template <typename OutputIterator, typename StrictWeakOrdering>
    inline size_type
    getNonZerosSorted(OutputIterator out_begin, int n =-1,
                      StrictWeakOrdering o = IJV::greater_value()) const
    {
      if (nNonZeros() == 0)
        return 0;

      if (n < 0 || (size_type) n > nNonZeros())
        n = nNonZeros();

      std::vector<IJV> ijvs(nNonZeros());
      getAllNonZeros(ijvs.begin());
      std::partial_sort(ijvs.begin(), ijvs.begin() + n, ijvs.end(), o);
      std::copy(ijvs.begin(), ijvs.begin() + n, out_begin);

      return n;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the row indices and values of the non-zeros on the diagonal.
     */
    template <typename OutputIterator>
    inline size_type getDiagonalToSparse(OutputIterator out) const
    {
      { // Pre-conditions
        //boost::function_requires<boost::OutputIterator<OutputIterator,
        //  std::pair<size_type, value_type> > >;
      } // End pre-conditions

      size_type count = 0;

      ITERATE_ON_ALL_ROWS {
        difference_type offset = col_(row, row);
        if (offset >= 0) {
          *out = std::make_pair(row, nz_[row][offset]);
          ++out; ++count;
        }
      }

      return count;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the diagonal as a dense vector.
     */
    template <typename OutputIterator>
    inline void getDiagonalToDense(OutputIterator out) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator, value_type);
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        difference_type offset = col_(row, row);
        if (offset >= 0) {
          *out = nz_[row][offset];
        } else {
          *out = 0;
        }
        ++out;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Set from 3 ranges, one for the row indices, one for the column indices
     * and one for the values.
     * For example, calling with [0,0,1,1], [0,1,0,1] and a 4-long flat list
     * sets those values at [0,0], [0,1], [1,0], [1,1].
     */
    template <typename InputIterator1, typename InputIterator2>
    inline void setElements(InputIterator1 i_begin, InputIterator1 i_end,
                            InputIterator1 j_begin,
                            InputIterator2 v_begin)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator1);
        ASSERT_INPUT_ITERATOR(InputIterator2);
        assert_valid_row_it_range_(i_begin, i_end, "setElements");
      } // End pre-conditions

      while (i_begin != i_end) {
        set(*i_begin, *j_begin, value_type(*v_begin));
        ++i_begin; ++j_begin; ++v_begin;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Get from 2 ranges, one for the row indices, one for the column indices,
     * returning the values in the third range.
     * This returns in v the values of the zeros as well as the non-zeros,
     * with indices corresponding to a flattening of the indices specified.
     * For example, calling with [0,0,1,1], [0,1,0,1] returns a flat list
     * of the elements at [0,0], [0,1], [1,0], [1,1].
     */
    template <typename InputIterator1, typename OutputIterator1>
    inline void getElements(InputIterator1 i_begin, InputIterator1 i_end,
                            InputIterator1 j_begin,
                            OutputIterator1 v_begin) const
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator1);
        ASSERT_OUTPUT_ITERATOR(OutputIterator1, value_type);
        assert_valid_row_it_range_(i_begin, i_end, "getElements");
      } // End pre-conditions

      while (i_begin != i_end) {
        *v_begin = get(*i_begin, *j_begin);
        ++i_begin; ++j_begin; ++v_begin;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Set on the outer product of the ranges passed in. The first range contains
     * the indices of the rows, the second the indices of the columns. The values
     * to set are taken from the SparseMatrix passed in.
     */
    template <typename InputIterator1, typename Other>
    inline void setOuter(InputIterator1 i_begin, InputIterator1 i_end,
                         InputIterator1 j_begin, InputIterator1 j_end,
                         const Other& values)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator1);
        NTA_ASSERT((size_type)values.nRows() >= (size_type)(i_end - i_begin))
          << "SparseMatrix setOuter: "
          << "Matrix to set has too few rows: " << values.nRows()
          << " - Should be at least: " << (size_type)(i_end - i_begin);
        NTA_ASSERT((size_type)values.nCols() >= (size_type)(j_end - j_begin))
          << "SparseMatrix setOuter: "
          << "Matrix to set has too few columns: " << values.nCols()
          << " - Should be at least: " << (size_type)(j_end - j_begin);
        assert_valid_row_it_range_(i_begin, i_end, "setOuter");
        assert_valid_col_it_range_(i_begin, i_end, "setOuter");
      } // End pre-conditions

      InputIterator1 j_begin_cache = j_begin;

      for (size_type ii = 0; i_begin != i_end; ++ii, ++i_begin) {
        j_begin = j_begin_cache;
        for (size_type jj = 0; j_begin != j_end; ++jj, ++j_begin) {
          this->set(*i_begin, *j_begin, values.get(ii, jj));
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Get on the outer product of the ranges passed in. The first range contains
     * the row indices, the second range the column indices. For example, calling
     * getOuter with [1,3,5],[1,3,5] returns the 9 values at [1,1], [1,3], [1,5],
     * [3,1], [3,3], [3,5], [5,1], [5,3], [5,5].
     */
    template <typename InputIterator1, typename InputIterator2, typename Other>
    inline void getOuter(InputIterator1 i_begin, InputIterator1 i_end,
                         InputIterator2 j_begin, InputIterator2 j_end,
                         Other& values) const
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator1);
        ASSERT_INPUT_ITERATOR(InputIterator2);
        assert_valid_row_it_range_(i_begin, i_end, "getOuter");
        assert_valid_col_it_range_(i_begin, i_end, "getOuter");
      } // End pre-conditions

      InputIterator1 j_begin_cache = j_begin;
      size_t nrows = (size_t)(i_end - i_begin);
      size_t ncols = (size_t)(j_end - j_begin);

      values.resize(nrows, ncols); // assumes Other has resize()

      for (size_type ii = 0; i_begin != i_end; ++ii, ++i_begin) {
        j_begin = j_begin_cache;
        for (size_type jj = 0; j_begin != j_end; ++jj, ++j_begin) {
          values.set(ii, jj, this->get(*i_begin, *j_begin));
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * A more convenient form of getOuter, useful for example, when we can't
     * subtract the iterators to know the sizes of the ranges.
     */
    template <typename Container1, typename Container2, typename Other>
    inline void
    getOuter(const Container1& c1, const Container2& c2, Other& other) const
    {
      typedef typename Container1::const_iterator iterator1;
      typedef typename Container2::const_iterator iterator2;

      iterator1 i_begin = c1.begin(), i_end = c1.end();
      iterator2 j_begin = c2.begin(), j_end = c2.end(), j_begin_cache = j_begin;

      other.resize(c1.size(), c2.size()); // assumes Other has resize()

      for (size_type ii = 0; i_begin != i_end; ++ii, ++i_begin) {
        j_begin = j_begin_cache;
        for (size_type jj = 0; j_begin != j_end; ++jj, ++j_begin)
          other.set(ii, jj, this->get(*i_begin, *j_begin));
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

      size_type nrows = src.nRows(), ncols = src.nCols();
      for (size_type row = 0; row != nrows; ++row) {
        for (size_type col = 0; col != ncols; ++col) {
          set(row + dst_first_row, col + dst_first_col, src.get(row,col));
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Gets a slice from this to a new SparseMatrix. The relative positions
     * of the non-zero elements are preserved. For example, calling this
     * method with (0,2,0,2) returns a the sub-matrix [0:2] X [0:2], both
     * zeros and non-zeros.
     *
     * This method is not fast.
     *
     * @param src [Domain2D] the source domain to extract from this sparse matrix
     * @retval [SparseMatrix] the extracted slice
     *
     * TODO faster method, when Other as the same type as this, and where we
     * can access the internals, instead of going through get/set. Use at least
     * row-wise bulk operations.
     */
    template <typename Other>
    inline void
    getSlice(size_type src_first_row, size_type src_row_end,
             size_type src_first_col, size_type src_col_end,
             Other& other) const
    {
      { // Pre-conditions
        assert_valid_row_col_(src_first_row, src_first_col, "getSlice");
        assert_valid_row_col_(src_row_end-1, src_col_end-1, "getSlice");
        NTA_ASSERT(src_first_row <= src_row_end)
          << "SparseMatrix getSlice"
          << ": Invalid row range: [" << src_first_row
          << ".." << src_row_end << "): "
          << "- Beginning should be <= end of range";
        NTA_ASSERT(src_first_col <= src_col_end)
          << "SparseMatrix getSlice"
          << ": Invalid column range: [" << src_first_col
          << ".." << src_col_end << "): "
          << "- Beginning should be <= end of range";
      } // End pre-conditions

      // Assumes Other has resize()
      other.resize(src_row_end - src_first_row, src_col_end - src_first_col);

      for (size_type row = src_first_row; row != src_row_end; ++row) {
        for (size_type col = src_first_col; col != src_col_end; ++col) {
          const value_type v = this->get(row, col);
          other.set(row - src_first_row, col - src_first_col, v);
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * This is an optimized getSlice that works only for SparseMatrix objects, and
     * bypass the call to set().
     */
    inline void getSlice2(size_type src_first_row, size_type src_row_end,
                          size_type src_first_col, size_type src_col_end,
                          SparseMatrix& other) const
    {
      { // Pre-conditions
        assert_valid_row_col_(src_first_row, src_first_col, "getSlice2");
        assert_valid_row_col_(src_row_end-1, src_col_end-1, "getSlice2");
        NTA_ASSERT(src_first_row <= src_row_end)
          << "SparseMatrix getSlice2"
          << ": Invalid row range: [" << src_first_row
          << ".." << src_row_end << "): "
          << "- Beginning should be <= end of range";
        NTA_ASSERT(src_first_col <= src_col_end)
          << "SparseMatrix getSlice2"
          << ": Invalid column range: [" << src_first_col
          << ".." << src_col_end << "): "
          << "- Beginning should be <= end of range";
      } // End pre-conditions

      size_type o_nrows = src_row_end - src_first_row;
      size_type o_ncols = src_col_end - src_first_col;

      other.resize(o_nrows, o_ncols);
      other.ind_mem_ = NULL;
      other.nz_mem_ = NULL;
      other.nrows_ = o_nrows;
      other.ncols_ = o_ncols;

      size_type orow = 0;

      for (size_type row = src_first_row; row != src_row_end; ++row, ++orow) {
        for (size_type col = src_first_col; col != src_col_end; ++col) {
          size_type *ind = NULL, *ind_end = NULL;
          difference_type offset = pos_(row, src_first_col, src_col_end, ind, ind_end);
          value_type *nz = nz_begin_(row) + offset;
          size_type nnzr = ind_end - ind;
          if (nnzr > other.nnzr_[orow]) {
            if (other.isCompact())
              other.decompact();
            delete [] other.ind_[orow];
            delete [] other.nz_[orow];
            other.ind_[orow] = new size_type[nnzr];
            other.nz_[orow] = new value_type[nnzr];
          }
          other.nnzr_[orow] = nnzr;
          size_type *o_ind = other.ind_begin_(orow);
          value_type *o_nz = other.nz_begin_(orow);
          for (; ind != ind_end; ++ind, ++nz, ++o_ind, ++o_nz) {
            *o_ind = *ind - src_first_col;
            *o_nz = *nz;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Set a whole row to zero. This is fast.
     *
     * @param row [0 <= size_type < nrows] the row to set to zero
     *
     * @b Complexity:
     *  @li O(1)
     *
     * @b Exceptions:
     *  @li If row < 0 or row >= nrows
     */
    inline void setRowToZero(size_type row)
    {
      { // Pre-conditions
        assert_valid_row_(row, "setRowToZero");
      } // End pre-conditions

      nnzr_[row] = 0;
    }

    //--------------------------------------------------------------------------------
    inline void setRowToVal(size_type row, value_type val)
    {
      { // Pre-conditions
        assert_valid_row_(row, "setRowToVal");
      } // End pre-conditions

      for (size_type col = 0; col != nCols(); ++col)
        set(row, col, val);
    }

    //--------------------------------------------------------------------------------
    /**
     * Set a whole column to zero.
     *
     * @param col [0 <= size_type < ncols] the index of the column to set to 0
     *
     * @b Complexity:
     *  @li O(nrows*(log(nnzr) + nnzr))
     *
     * @b Exceptions:
     *  @li If col < 0 or col >= ncols
     */
    inline void setColToZero(size_type col)
    {
      { // Pre-conditions
        assert_valid_col_(col, "setColToZero");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS
        setZero(row, col);
    }

    //--------------------------------------------------------------------------------
    inline void setColToVal(size_type col, value_type val)
    {
      { // Pre-conditions
        assert_valid_col_(col, "setColToVal");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS
        set(row, col, val);
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets the whole sparse matrix to zero, without changing its number of rows
     * or columns. Deallocates memory.
     */
    inline void setToZero()
    {
      if (isCompact())
        decompact();

      ITERATE_ON_ALL_ROWS {
        delete [] ind_[row];
        delete [] nz_[row];
        ind_[row] = 0;
        nz_[row] = 0;
        nnzr_[row] = 0;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Set multiple rows to zero simultaneously.
     */
    template <typename InputIterator>
    inline void setRowsToZero(InputIterator it, InputIterator end)
    {
      for (; it != end; ++it)
        nnzr_[*it] = 0;
    }

    //--------------------------------------------------------------------------------
    /**
     * Set multiple columns to 0 simultaneously.
     * This is more efficient than setting
     * those columns to zero one by one.
     */
    template <typename InputIterator>
    inline void setColsToZero(InputIterator it, InputIterator end)
    {
      {
        // check that column indices in strictly increasing order
      }

      boost::unordered_set<size_type> skip(it, end);

      ITERATE_ON_ALL_ROWS {
        size_type k = 0;
        size_type *row_ind = ind_[row];
        value_type *row_nz = nz_[row];
        ITERATE_ON_ROW {
          if (skip.find(*ind) == skip.end()) {
            row_ind[k] = *ind;
            row_nz[k] = *nz;
            ++k;
          }
        }
        nnzr_[row] = k;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets whole matrix to outer product of x and y. The old value of the matrix
     * is lost.
     *
     * this = outer(x,y)
     */
    inline void setFromOuter(const std::vector<value_type>& x,
                             const std::vector<value_type>& y,
                             bool keepMemory =false)
    {
      if (!keepMemory) {
        deallocate_();
        allocate_(x.size(), y.size());
        nrows_ = x.size();
        ncols_ = y.size();
      } else {
        NTA_ASSERT(nrows_ == x.size())
          << "setFromOuter, keeping memory: Wrong number of rows";
        NTA_ASSERT(ncols_ == y.size())
          << "setFromOuter, keeping memory: Wrong number of columns";
        compact();
      }

      typename std::vector<value_type>::const_iterator it;
      size_type *indb = indb_;
      value_type *nzb = nzb_;

      for (it = y.begin(); it != y.end(); ++it)
        if (!isZero_(*it)) {
          *indb++ = (size_type)(it - y.begin());
          *nzb++ = *it;
        }

      size_type nnzr = (size_type)(indb - indb_);
      size_type *indb_end = indb;
      size_type k = 0;

      for (it = x.begin(); it != x.end(); ++it) {
        size_type row = (size_type)(it - x.begin());
        if (isZero_(*it)) {
          nnzr_[row] = 0;
          continue;
        }
        if (!keepMemory) {
          ind_[row] = new size_type[nnzr];
          nz_[row] = new value_type[nnzr];
        } else {
          ind_[row] = ind_mem_ + k * nnzr;
          nz_[row] = nz_mem_ + k * nnzr;
        }
        indb = indb_;
        nzb = nzb_;
        size_type *ind = ind_[row];
        value_type *nz = nz_[row];
        while (indb != indb_end) {
          value_type val = *it * *nzb;
          if (!isZero_(val)) {
            *ind++ = *indb;
            *nz++ = val;
          }
          ++indb; ++nzb;
        }
        nnzr_[row] = (size_type)(ind - ind_[row]);
        if (nnzr_[row] > 0)
          ++k;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * this = outer(x,y) .* b
     */
    inline void
    setFromElementMultiplyWithOuter(const std::vector<value_type>& x,
                                    const std::vector<value_type>& y,
                                    const SparseMatrix& b)
    {
      deallocate_();
      allocate_(x.size(), y.size());
      nrows_ = x.size();
      ncols_ = y.size();

      typename std::vector<value_type>::const_iterator it;
      size_type *indb = indb_;
      value_type *nzb = nzb_;

      for (it = y.begin(); it != y.end(); ++it)
        if (!isZero_(*it)) {
          *indb++ = (size_type)(it - y.begin());
          *nzb++ = *it;
        }

      size_type nnzr = (size_type)(indb - indb_);
      size_type *indb_end = indb;

      for (it = x.begin(); it != x.end(); ++it) {
        size_type row = (size_type)(it - x.begin());
        if (isZero_(*it) || b.nNonZerosOnRow(row) == 0)
          continue;
        ind_[row] = new size_type[nnzr];
        nz_[row] = new value_type[nnzr];
        indb = indb_;
        nzb = nzb_;
        size_type *ind_a = ind_begin_(row);
        size_type *ind_b = b.ind_begin_(row);
        size_type *ind_b_end = b.ind_end_(row);
        value_type *nz_a = nz_begin_(row);
        value_type *nz_b = b.nz_begin_(row);
        while (indb != indb_end && ind_b != ind_b_end) {
          if (*indb == *ind_b) {
            value_type val = *it * *nzb * *nz_b;
            if (!isZero_(val)) {
              *ind_a++ = *indb;
              *nz_a++ = val;
            }
            ++indb; ++nzb;
            ++ind_b; ++nz_b;
          } else if (*indb < *ind_b) {
            ++indb; ++nzb;
          } else if (*ind_b < *indb) {
            ++ind_b; ++nz_b;
          }
        }
        nnzr_[row] = (size_type)(ind_a - ind_begin_(row));
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Compacts a row from a buffer to (nzr_[r], ind_[r], nz_[r]).
     * This will weed out the zeros in the buffer, if any, and keeps
     * the non-zeros sorted in increasing order of indices.
     *
     * @b Complexity:
     *  @li O(nrows + 4*nnzr)
     *
     * @b Exceptions:
     *  @li Not enough memory (error)
     */
    template <typename InputIterator>
    inline void setRowFromDense(size_type row, InputIterator begin)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);
      } // End pre-conditions

      set_row_(row, begin, begin + nCols());
    }

    //--------------------------------------------------------------------------------
    inline void setRowFromDense(size_type row, const std::vector<value_type>& x)
    {
      { // Pre-conditions
        NTA_ASSERT(x.size() == nCols())
          << "setRowFromDense: Need vector with as many elements as "
          << "number of colums= " << nCols();
      } // End pre-conditions

      set_row_(row, x.begin(), x.end());
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets a whole row from a sparse (index, value) representation. Expects non-zeros
     * only, with column indices in increasing order, without repeition.
     *
     * @param row [0 <= size_type < nrows] the row to set
     * @param ind_it [InputIterator<size_type>] iterator to the beginning of a range
     *  containing the indices of the non-zeros
     * @param ind_end [InputIterator<size_type>] iterator to one past the end of
     *  range the contains the indices of the non-zeros
     * @param nz_it [InputIterator<value_type>] iterator to the beginning of the range
     *  containing the values of the non-zeros
     *
     * @b Complexity:
     *  @li O(2*nnzr)
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows
     *  @li If any column index out of range
     *
     * TODO faster by assuming that the sparse data received is "right"
     */
    template <typename InputIterator1, typename InputIterator2>
    inline void setRowFromSparse(size_type row,
                                 InputIterator1 ind_it, InputIterator1 ind_end,
                                 InputIterator2 nz_it)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator1);
        ASSERT_INPUT_ITERATOR(InputIterator2);

        assert_valid_row_(row, "setRowFromSparse");
        assert_valid_sorted_index_range_(nCols(), ind_it, ind_end, "setRowFromSparse");

        for (InputIterator2 nz = nz_it; nz != nz_it + (ind_end - ind_it); ++nz)
          NTA_ASSERT(!isZero_(*nz))
            << "SparseMatrix setRowFromSparse: Expecing only non-zeros";
      } // End pre-conditions

      size_type new_nnzr = (size_type)(ind_end - ind_it);

      if (new_nnzr > nnzr_[row]) {
        if (isCompact())
          decompact();
        delete [] ind_[row];
        delete [] nz_[row];
        ind_[row] = new size_type [new_nnzr];
        nz_[row] = new value_type [new_nnzr];
      }

      std::copy(ind_it, ind_end, ind_[row]);
      std::copy(nz_it, nz_it + new_nnzr, nz_[row]);
      nnzr_[row] = new_nnzr;
    }

    //--------------------------------------------------------------------------------
    /**
     * Uses the same init value for all the non-zeros.
     */
    template <typename InputIterator1>
    inline void setRowFromSparseWInitVal(size_type row,
                                         InputIterator1 ind_it, InputIterator1 ind_end,
                                         value_type init_val)
    {
      { // Pre-conditions
        NTA_ASSERT(init_val != 0);
        ASSERT_INPUT_ITERATOR(InputIterator1);

        assert_valid_row_(row, "setRowFromSparseWInitVal");
        assert_valid_sorted_index_range_(nCols(), ind_it, ind_end,
                                         "setRowFromSparseWInitVal");
      } // End pre-conditions

      size_type new_nnzr = (size_type)(ind_end - ind_it);

      if (new_nnzr > nnzr_[row]) {
        if (isCompact())
          decompact();
        delete [] ind_[row];
        delete [] nz_[row];
        ind_[row] = new size_type [new_nnzr];
        nz_[row] = new value_type [new_nnzr];
      }

      std::copy(ind_it, ind_end, ind_[row]);
      std::fill(nz_[row], nz_[row] + new_nnzr, init_val);
      nnzr_[row] = new_nnzr;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns r-th row of this sparse matrix, to a contiguous array of memory.
     * If the row does not contain any non-zero, the memory pointed to by it
     * is set to zero.
     *
     * @param r [0 <= size_type < nrows] row index
     * @param it [OutputIterator<value_type>] output iterator pointing to
     *  the beginning of contiguous memory for the values of the non-zeros
     *
     * @b Complexity:
     *  @li O(ncols + nnzr)
     *
     * @b Exceptions:
     *  @li r < 0 || r >= nrows (check)
     *
     * TODO single pass rather than ncols + nnzr?
     */
    template <typename OutputIterator>
    inline void getRowToDense(size_type row, OutputIterator it) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator, value_type);
        assert_valid_row_(row, "getRowToDense");
      } // End pre-conditions

      std::fill(it, it + nCols(), (value_type)0);

      ITERATE_ON_ROW {
        *(it + *ind) = *nz;
      }
    }

    //--------------------------------------------------------------------------------
    inline void getRowToDense(size_type row, std::vector<value_type>& dense) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "getRowToDense");
      } // End pre-conditions

      typename std::vector<value_type>::iterator it = dense.begin();

      std::fill(it, it + nCols(), (value_type)0);

      ITERATE_ON_ROW {
        *(it + *ind) = *nz;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Stores r-th row of this sparse matrix in provided iterators.
     * The first iterator will contain the indices of the non-zeros, the second
     * will contain the values of those non-zeros.
     * The iterators need to point to enough storage.
     * The iterators are not modified if the row does not contain any non-zero.
     *
     * @param row [0 <= size_type < nrows] row index
     * @param indIt [OutputIterator1<size_type>] output iterator pointing to
     *  the beginning of container for the indices of the non-zeros
     * @param nzIt [OutputIterator2<value_type>] output iterator pointing to
     *  the beginning of container for the values of the on-zeros
     *
     * @b Complexity:
     *  @li O(2*nnzr)
     *
     * @b Exceptions:
     *  @li row < 0 || row >= nrows (check)
     */
    template <typename OutputIterator1, typename OutputIterator2>
    inline size_type
    getRowToSparse(size_type row, OutputIterator1 indIt, OutputIterator2 nzIt) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator1, size_type);
        ASSERT_OUTPUT_ITERATOR(OutputIterator2, value_type);
        assert_valid_row_(row, "getRowToSparse");
      } // End pre-conditions

      ITERATE_ON_ROW {
        *indIt = *ind;
        *nzIt = *nz;
        ++indIt; ++nzIt;
      }

      return nNonZerosOnRow(row);
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator1>
    inline size_type
    getRowIndicesToSparse(size_type row, OutputIterator1 indIt) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator1, size_type);
        assert_valid_row_(row, "getRowIndicesToSparse");
      } // End pre-conditions

      ITERATE_ON_ROW
        *indIt++ = *ind;

      return nNonZerosOnRow(row);
    }

    //--------------------------------------------------------------------------------
    /**
     * Stores r-th row of this sparse matrix in provided iterator on pairs.
     *
     * @param row [0 <= size_type < nrows] row index
     * @param idxValIt [OutputIterator1<size_type>] output iterator pointing to
     *  the beginning of container for the pairs (index,value) of the non-zeros
     *
     * @b Complexity:
     *  @li O(nnzr)
     *
     * @b Exceptions:
     *  @li row < 0 || row >= nrows (check)
     */
    template <typename OutputIterator1>
    inline size_type getRowToSparse(size_type row, OutputIterator1 idxValIt) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "getRowToSparse(pair<idx,val>)");
      } // End pre-conditions

      ITERATE_ON_ROW {
        *idxValIt = std::make_pair(*ind, *nz);
        ++idxValIt;
      }

      return nNonZerosOnRow(row);
    }

    //--------------------------------------------------------------------------------
    /**
     * Copies a row from one SparseMatrix to another.
     */
    inline void copyRow(size_type dst_row, size_type src_row, SparseMatrix& other)
    {
      { // Pre-conditions
        assert_valid_row_(dst_row, "copyRow");
        other.assert_valid_row_(src_row, "copyRow");
      } // End pre-conditions

      if (&other == this && src_row == dst_row)
        return;

      size_type new_nnzr = other.nNonZerosOnRow(src_row);

      if (new_nnzr > nNonZerosOnRow(dst_row)) {
        if (isCompact())
          decompact();
        delete [] ind_[dst_row];
        delete [] nz_[dst_row];
        ind_[dst_row] = new size_type [new_nnzr];
        nz_[dst_row] = new value_type [new_nnzr];
      }

      std::copy(other.ind_[src_row], other.ind_[src_row] + new_nnzr, ind_[dst_row]);
      std::copy(other.nz_[src_row], other.nz_[src_row] + new_nnzr, nz_[dst_row]);
      nnzr_[dst_row] = new_nnzr;
    }

    //--------------------------------------------------------------------------------
    /**
     * Exports a given column of this SparseMatrix to a pre-allocated dense array.
     * OutputIterator needs to be an iterator into a contiguous array of memory.
     *
     * @param col [0 <= size_type < ncols] the column to export
     * @param dense [OutputIterator] iterator to contiguous array of memory
     *
     * @b Complexity:
     *  @li O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li if col < 0 || col >= ncols (assert)
     */
    template <typename OutputIterator>
    inline void getColToDense(size_type col, OutputIterator dense) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator, value_type);
        assert_valid_col_(col, "getColToDense");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        const difference_type offset = col_(row, col);
        *dense = offset >= 0 ? *(nz_begin_(row) + offset) : value_type(0);
        ++dense;
      }
    }

    //--------------------------------------------------------------------------------
    inline void getColToDense(size_type col, std::vector<value_type>& dense) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "getColToDense");
      } // End pre-conditions

      typename std::vector<value_type>::iterator it = dense.begin();

      ITERATE_ON_ALL_ROWS {
        const difference_type offset = col_(row, col);
        *it = offset >= 0 ? *(nz_begin_(row) + offset) : value_type(0);
        ++it;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Exports a given column of this SparseMatrix to a pre-allocated dense array.
     * OutputIterator needs to be an iterator into a contiguous array of memory.
     *
     * @param col [0 <= size_type < ncols] the column to export
     * @param dense [OutputIterator] iterator to contiguous array of memory
     *
     * @b Complexity:
     *  @li O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li if col < 0 || col >= ncols (assert)
     */
    template <typename OutputIterator1, typename OutputIterator2>
    inline size_type
    getColToSparse(size_type col, OutputIterator1 indIt, OutputIterator2 nzIt) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator1, size_type);
        ASSERT_OUTPUT_ITERATOR(OutputIterator2, value_type);
        assert_valid_col_(col, "getColToSparse");
      } // End pre-conditions

      size_type count = 0;

      ITERATE_ON_ALL_ROWS {
        const difference_type offset = col_(row, col);
        if (offset >= 0) {
          *indIt = row;
          *nzIt = *(nz_begin_(row) + offset);
          ++indIt; ++nzIt;
          ++count;
        }
      }

      return count;
    }

    //--------------------------------------------------------------------------------
    /**
     * Stores r-th column of this sparse matrix in provided iterators.
     * The first iterator will contain the indices of the non-zeros, the second
     * will contain the values of those non-zeros.
     * The iterators need to point to enough storage.
     * The iterators are not modified if the row does not contain any non-zero.
     *
     * @param r [0 <= size_type < ncols] column index
     * @param idxValIt [OutputIterator1] an iterator pointing to beginning of container
     *  to store pairs of (index,values) for the non-zeros of this column
     *
     * @b Complexity:
     *  @li O(nrows * log(nnzr))
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols (assert)
     */
    template <typename OutputIterator1>
    inline size_type getColToSparse(size_type col, OutputIterator1 idxValIt) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "getColToSparse(pair<idx,val>)");
      } // End pre-conditions

      size_type count = 0;

      ITERATE_ON_ALL_ROWS {
        const difference_type offset = col_(row, col);
        if (offset >= 0) {
          *idxValIt = std::make_pair(row, *(nz_begin_(row) + offset));
          ++idxValIt;
          ++count;
        }
      }

      return count;
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator1>
    inline void setColFromDense(size_type col, InputIterator1 it)
    {
      { // Pre-conditions
        assert_valid_col_(col, "setColFromDense");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        this->set(row, col, *it);
        ++it;
      }
    }

    //--------------------------------------------------------------------------------
    inline void setColFromDense(size_type col, const std::vector<value_type>& x)
    {
      { // Pre-conditions
        NTA_ASSERT(x.size() == nRows())
          << "SparseMatrix setColFromDense std: "
          << "Need vector with as many elements as "
          << "number of rows= " << nRows();
      } // End pre-conditions

      setColFromDense(col, x.begin());
    }

    //--------------------------------------------------------------------------------
    // FILTERING
    //--------------------------------------------------------------------------------

    /**
     * Filter methods are like the STL remove_if algorithms, but the point is that
     * they handle removal "efficiently", without reallocating memories: the rows
     * are shrunk in place as needed.
     */

    /**
     * Removes non-zeros on the given row according to unary predicate f.
     *
     * @param row [0 <= size_type < nrows] the row index
     * @param f [unary_predicate] a predicate that returns true if the element
     *  is to be kept, false if the element is to be set to zero
     *
     * @b Complexity:
     *  @li O(nnzr * f1)
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows
     */
    template <typename UnaryFunction>
    inline void filterRow(size_type row, const UnaryFunction& f1)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, bool, value_type);
        assert_valid_row_(row, "filterRow");
      } // End pre-conditions

      size_type nnzr1 = nnzr_[row], nnzr2 = 0, *ind = ind_begin_(row);
      value_type *nz = nz_begin_(row);

      for (size_type k = 0; k != nnzr1; ++k)
        if (f1(nz[k])) {
          ind[nnzr2] = ind[k];
          nz[nnzr2] = nz[k];
          ++nnzr2;
        }

      nnzr_[row] = nnzr2;
    }

    //--------------------------------------------------------------------------------
    template <typename UnaryFunction,
              typename OutputIterator1,
              typename OutputIterator2>
    inline size_type
    filterRow(size_type row, const UnaryFunction& f1,
              OutputIterator1 cut_ind, OutputIterator2 cut_nz)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, bool, value_type);
        assert_valid_row_(row, "filterRow");
      } // End pre-conditions

      size_type nnzr1 = nnzr_[row], nnzr2 = 0, *ind = ind_begin_(row);
      value_type *nz = nz_begin_(row);

      size_type count = 0;

      for (size_type k = 0; k != nnzr1; ++k)
        if (f1(nz[k])) {
          ind[nnzr2] = ind[k];
          nz[nnzr2] = nz[k];
          ++nnzr2;
        } else {
          *cut_ind++ = ind[k];
          *cut_nz++ = nz[k];
          ++count;
        }

      nnzr_[row] = nnzr2;

      return count;
    }

    //--------------------------------------------------------------------------------
    /**
     * Removes non-zeros on the given col according to unary predicate f.
     *
     * @param row [0 <= size_type < ncols] the col index
     * @param f [unary_predicate] a predicate that returns true if the element
     *  is to be kept, false if the element is to be set to zero
     *
     * @b Complexity:
     *  @li O(nrows * log(nnzr) * f1)
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols
     */
    template <typename UnaryFunction>
    inline void filterCol(size_type col, const UnaryFunction& f1)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, bool, value_type);
        assert_valid_col_(col, "filterCol");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        size_type *ind_it = pos_(row, col);
        if (ind_it != ind_end_(row) && *ind_it == col) {
          size_type offset = size_type(ind_it - ind_begin_(row));
          if (!f1(nz_[row][offset]))
            erase_(row, ind_it);
        }
      }
    }


    //--------------------------------------------------------------------------------
    /**
     * Removes non-zeros in the whole matrix according to unary predicate f.
     * This operation leaves zeros at the end of the rows, resulting
     * in wasted storage. To avoid this, compact() can be called.
     *
     * @param f [unary_predicate] a predicate that returns true if the element
     *  is to be kept, false if the element is to be set to zero
     *
     * @b Complexity:
     *  @li O(nnz * f1)
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename UnaryFunction>
    inline void filter(const UnaryFunction& f1)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, bool, value_type);
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS
        filterRow(row, f1);
    }

    //--------------------------------------------------------------------------------
    template <typename UnaryFunction,
              typename OutputIterator1,
              typename OutputIterator2>
    inline size_type filter(const UnaryFunction& f1,
                            OutputIterator1 cut_i,
                            OutputIterator1 cut_j,
                            OutputIterator2 cut_nz)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, bool, value_type);
      } // End pre-conditions

      size_type count = 0;
      std::vector<size_type> indb(nCols());
      ITERATE_ON_ALL_ROWS {
        size_type c = filterRow(row, f1, indb.begin(), cut_nz);
        for (size_type i = 0; i != c; ++i) {
          *cut_i++ = row;
          *cut_j++ = indb[i];
        }
        count += c;
      }

      return count;
    }

    //--------------------------------------------------------------------------------
    // PERMUTATIONS
    //--------------------------------------------------------------------------------
    /**
     * Permutes the rows of this sparse matrix. The permutation is given as an array,
     * where each element of the array indicates which row should take the place
     * of the row at the element's index: [3,2,1,0] indicates that after the
     * the permutation, the first row should be the old row 3, the second the old
     * row 2...
     */
    template <typename InIter>
    inline void permuteRows(InIter p)
    {
      std::vector<size_type> nnzr_old(nnzr_, nnzr_ + nrows_);
      std::vector<size_type*> ind_old(ind_, ind_ + nrows_);
      std::vector<value_type*> nz_old(nz_, nz_ + nrows_);

      for (size_type row = 0; row != nRows(); ++row, ++p) {
        nnzr_[row] = nnzr_old[*p];
        ind_[row] = ind_old[*p];
        nz_[row] = nz_old[*p];
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Permutes the cols of this sparse matrix. The permutation is given as an array,
     * where each element of the array indicates which col should take the place
     * of the col at the element's index: [3,2,1,0] indicates that after
     * the permutation, the first col should be the old col 3, the second the old
     * col 2...
     *
     * rp = [ind.index(i) for i in p if i in ind]
     * new_ind = [p.index(i) for i in p if i in ind]
     * new_val = [val[i] for i in rp]
     *
     * or:
     *
     * for i in p:
     *  if i in ind:
     *   new_ind += p.index(i),
     *   new_val += val[ind.index(i)],
     *
     */
    template <typename InIter>
    inline void permuteCols(InIter p)
    {
      InIter p_begin = p, p_end = p + nCols();

      for (size_type row = 0; row != nRows(); ++row) {
        size_type* indb_end = indb_ + nNonZerosOnRow(row);
        std::copy(ind_begin_(row), ind_end_(row), indb_);
        std::copy(nz_begin_(row), nz_end_(row), nzb_);
        size_type *ind = ind_begin_(row);
        value_type *nz = nz_begin_(row);
        for (InIter i = p_begin; i != p_end; ++i) {
          size_type* w = std::lower_bound(indb_, indb_end, *i);
          if (w != indb_end && *w == *i) {
            *ind = size_type(std::find(p_begin, p_end, *i) - p_begin);
            *nz = *(nzb_ + (w - indb_));
            ++ind; ++nz;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * After applying this function,
     * A[i, j] = (0 <= i-n < nRows) ? A_[i-n, j] : 0
     */
    void shiftRows(int n)
    {
      if (n == 0)
        return;

      const size_type nrows = nRows();

      if ((size_type) ::abs(n) >= nrows)
        {
          setToZero();
          return;
        }

      size_type beginSource, endSource, beginDest,
        beginDelete, endDelete, beginZero, endZero;

      if (n > 0) {
        beginSource = 0;
        endSource = nrows - n;
        beginDest = n;
        beginDelete = endSource;
        endDelete = nrows;
        beginZero = beginSource;
        endZero = beginDest;
      } else {
        const size_type ln = -n;
        beginSource = ln;
        endSource = nrows;
        beginDest = 0;
        beginDelete = 0;
        endDelete = beginSource;
        beginZero = nrows - ln;
        endZero = endSource;
      }

      // Clear out the destination.
      if (!isCompact()) {
        for (size_type i = beginDelete; i != endDelete; ++i) {
          if (nnzr_[i]) { // Not safe to delete if no NZs?
            delete[] ind_[i]; ind_[i] = 0;
            delete[] nz_[i]; nz_[i] = 0;
            nnzr_[i] = 0;
          }
        }
      } else {
        std::fill(ind_ + beginDelete, ind_ + endDelete, (size_type *) 0);
        std::fill(nz_ + beginDelete, nz_ + endDelete, (value_type *) 0);
        std::fill(nnzr_ + beginDelete, nnzr_ + endDelete, (size_type) 0);
      }

      if (beginSource < beginDest) {
        // TODO: Make work for non-POD data.
        size_type nMove = (endSource - beginSource);
        std::copy(nnzr_ + beginSource, nnzr_ + beginSource + nMove, nnzr_ + beginDest);
        std::copy(ind_ + beginSource, ind_ + beginSource + nMove, ind_ + beginDest);
        std::copy(nz_ + beginSource, nz_ + beginSource + nMove, nz_ + beginDest);

        //         ::memmove(ind_ + beginDest, ind_ + beginSource,
        //             nMove * sizeof(ind_[0]));
        //         ::memmove(nz_ + beginDest, nz_ + beginSource,
        //             nMove * sizeof(nz_[0]));
        //         ::memmove(nnzr_ + beginDest, nnzr_ + beginSource,
        //             nMove * sizeof(nnzr_[0]));
      } else {
        std::copy(ind_ + beginSource, ind_ + endSource, ind_ + beginDest);
        std::copy(nz_ + beginSource, nz_ + endSource, nz_ + beginDest);
        std::copy(nnzr_ + beginSource, nnzr_ + endSource, nnzr_ + beginDest);
      }

      std::fill(ind_ + beginZero, ind_ + endZero, (size_type *) 0);
      std::fill(nz_ + beginZero, nz_ + endZero, (value_type *) 0);
      std::fill(nnzr_ + beginZero, nnzr_ + endZero, (size_type) 0);
    }

    //---------------------------------------------------------------------
    /**
     * After applying this function,
     * A[i, j] = (0 <= j-n < nCols) ? A_[i, j-n] : 0
     */
    void shiftCols(int n)
    {
      if (n == 0)
        return;

      const size_type ncols = nCols();
      if ((size_type) ::abs(n) >= ncols)
        {
          setToZero();
          return;
        }

      const size_type nrows = nRows();

      if (n > 0) {

        const size_type max = ncols - n;

        for (size_type row = 0; row != nrows; ++row) {

          size_type *ind_write = ind_begin_(row);
          const size_type *ind_begin = ind_write;
          const size_type *ind_end =
            std::lower_bound(ind_begin,
                             const_cast<const size_type *>(ind_end_(row)), max);

          for(; ind_write != ind_end; ++ind_write)
            *ind_write += n;

          nnzr_[row] = ind_write - ind_begin;
        }
      } else {

        size_type ln = -n;

        for (size_type row = 0; row != nrows; ++row) {

          size_type *ind_write = ind_begin_(row);
          const size_type *ind_end = ind_end_(row);

          const size_type *ind_begin =
            std::lower_bound(const_cast<const size_type *>(ind_write), ind_end, ln);
          size_type offset = ind_begin - ind_write;

          std::copy(ind_begin, ind_end, ind_write);

          value_type *nz_write = nz_begin_(row);
          const value_type *nz_begin = nz_write + offset;
          const value_type *nz_end = nz_end_(row);

          std::copy(nz_begin, nz_end, nz_write);

          nnzr_[row] -= offset;
          ind_end -= offset;
          for(; ind_write != ind_end; ++ind_write)
            *ind_write -= ln;
        }
      }
    }

    //--------------------------------------------------------------------------------
    // APPLY
    //--------------------------------------------------------------------------------

    /**
     * Apply methods are like STL's transform algorithm, with a unary or a binary
     * functor.
     */

    /**
     * Applies given unary functor to non-zeros on the specified row:
     *
     *  this[row,k] = f1(this[row,k])
     *
     * where:
     *  k in {row} X [0,ncols) s.t. this[row,k] != 0
     *
     * @param row [0 <= size_type < nrows] the row on which to apply f
     * @param f [F] a unary functor to apply to each non-zero on the row
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows
     *
     * TODO test speed of nta::apply/std::transform
     * TODO threshold and apply in the same loop by assining to new position
     * with an offset
     */
    template <typename UnaryFunction>
    inline void elementRowNZApply(size_type row, const UnaryFunction& f1)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, value_type, value_type);
        assert_valid_row_(row, "elementRowNZApply");
      } // End pre-conditions

      size_type *ind = ind_begin_(row), *ind_end = ind_end_(row);
      value_type *nz = nz_begin_(row);
      size_type offset = 0;

      for (; ind != ind_end; ++ind, ++nz) {
        value_type val = f1(*nz);
        if (isZero_(val)) {
          ++ offset;
        } else {
          *(nz - offset) = val;
          *(ind - offset) = *ind;
        }
      }

      nnzr_[row] -= offset;
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies given functor to non-zeros on the specified column:
     *
     *  this[row,col] = f1(this[row,col])
     *
     * where:
     *  row,col in [0,nrows) X {col} s.t. this[row,col] != 0
     *
     * @param col [0 <= size_type < ncols] the column on which to apply f
     * @param f [F] a unary functor to apply to each non-zero on the column
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols
     */
    template <typename UnaryFunction>
    inline void elementColNZApply(size_type col, const UnaryFunction& f1)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, value_type, value_type);
        assert_valid_col_(col, "elementColNZApply");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        const difference_type offset = col_(row, col);
        if (offset >= 0) {
          value_type *nz = nz_begin_(row) + offset;
          *nz = f1(*nz);
          if (isZero_(*nz))
            erase_(row, ind_begin_(row) + offset);
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies given functor to non-zeros on the whole matrix:
     *
     *  this[row,col] = f1(this[row,col])
     *
     * where:
     *  row,col in [0,nrows) X [0,ncols) s.t. this[row,col] != 0
     *
     * @param f [F] a unary functor to apply to each non-zero
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename UnaryFunction>
    inline void elementNZApply(const UnaryFunction& f1)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, value_type, value_type);
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS
        elementRowNZApply(row, f1);
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies given functor to all the elements of the given row, the zeros as well
     * as the non-zeros:
     *
     *  this[row,col] = f1(this[row,col])
     *
     * where:
     *  row,col in {row} X [0,ncols)
     *
     * @param row [0 <= size_type < nrows] the row to process
     * @param f [F] a unary functor to apply to each element on the row
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows.
     *
     * TODO remove projection to buffer by iterating over non-zeros only
     */
    template <typename UnaryFunction>
    inline void elementRowApply(size_type row, const UnaryFunction& f1)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, value_type, value_type);
        assert_valid_row_(row, "elementRowApply");
      } // End pre-conditions

      to_nzb_(row);

      value_type *nzb = nzb_, *nzb_end = nzb_ + nCols();

      for (; nzb != nzb_end; ++nzb)
        *nzb = f1(*nzb);

      set_row_(row, nzb_, nzb_ + nCols());
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies given unary function to all the elements on the given column, the zeros
     * as well as the non-zeros:
     *
     *  this[row,col] = f1(this[row,col])
     *
     * where:
     *  row,col in [0,nrows) X {col}
     *
     * @param col [0 <= size_type < ncols] the column to process
     * @param f1 [unary_function] a unary function to apply to each element of the
     *  column
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols
     *
     * TODO faster?
     */
    template <typename UnaryFunction>
    inline void elementColApply(size_type col, const UnaryFunction& f1)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, value_type, value_type);
        assert_valid_col_(col, "elementColApply");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS
        set(row, col, f1(get(row, col)));
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies give unary function to all the elements in this sparse matrix, the
     * zeros as well as the non-zeros:
     *
     *  this[row,col] = f1(this[row,col])
     *
     * where:
     *  row,col in [0,nrows) X [0,ncols)
     *
     * @param f1 [unary function] a unary function to apply to each element
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename UnaryFunction>
    inline void elementApply(const UnaryFunction& f1)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, value_type, value_type);
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS
        elementRowApply(row, f1);
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies given binary functor f to the elements of a row and the given vector:
     *
     *  this[row,k] = f2(this[row,k], x[k])
     *
     * where:
     *  row,k in {row} X [0,ncols) s.t. this[row,k] != 0
     *
     * @param row [0 <= size_type < nrows] the row to process
     * @param f2 [binary function] a binary functor
     * @param x_begin [InputIterator] a forward iterator to the vector to use,
     *  a dense vector of size ncols
     *
     * @b Exceptions:
     *  @li If row is not in range.
     */
    template <typename BinaryFunction, typename InputIterator>
    inline void
    elementRowNZApply(size_type row, const BinaryFunction& f2, InputIterator x_begin)
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_INPUT_ITERATOR(InputIterator);
        assert_valid_row_(row, "elementRowNZApply");
      } // End pre-conditions

      size_type *ind = ind_begin_(row), *ind_end = ind_end_(row);
      value_type *nz = nz_begin_(row);
      size_type offset = 0;

      for (; ind != ind_end; ++ind, ++nz) {
        value_type val = f2(*nz, *(x_begin + *ind));
        if (isZero_(val)) {
          ++ offset;
        } else {
          *(nz - offset) = val;
          *(ind - offset) = *ind;
        }
      }

      nnzr_[row] -= offset;
    }

    //--------------------------------------------------------------------------------
    /**
     * Apply binary functor to x and each non-zero of a given row, and put the result
     * in y. This assumes that f2(0, x) = 0,
     */
    template <typename BinaryFunction, typename InputIterator, typename OutputIterator>
    inline void
    elementRowNZApply(size_type row, const BinaryFunction& f2,
                      InputIterator x, OutputIterator y) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_INPUT_ITERATOR(InputIterator);
        assert_valid_row_(row, "elementRowNZApply");
      } // End pre-conditions

      if (nnzr_[row] == 0) {
        std::fill(y, y + nCols(), (value_type) 0);
        return;
      }

      size_type *ind = ind_begin_(row), *ind_end = ind_end_(row);
      value_type *nz = nz_begin_(row);

      for (size_type col = 0; col != nCols(); ++col, ++y, ++x) {
        if (ind != ind_end && *ind == col) {
          *y = f2(*nz, *x);
          ++ind; ++nz;
        } else {
          *y = 0;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies given binary functor f to all the elements of a row and the given vector:
     *
     *  this[row,col] = f2(this[row,col], x[col])
     *
     * where:
     *  row,col in {row} X [0,ncols)
     *
     * @param row [0 <= size_type < nrows] the row to process
     * @param f2 [binary function] a binary functor
     * @param x_begin [InputIterator] a forward iterator to the vector to use,
     *  a dense vector of size ncols
     *
     * @b Exceptions:
     *  @li If row is not in range.
     */
    template <typename BinaryFunction, typename InputIterator>
    inline void
    elementRowApply(size_type row, const BinaryFunction& f2, InputIterator x_begin)
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_INPUT_ITERATOR(InputIterator);
        assert_valid_row_(row, "elementRowApply");
      } // End pre-conditions

      value_type *nzb_end = nzb_ + nCols();

      to_nzb_(row);

      for (value_type *nzb = nzb_; nzb != nzb_end; ++nzb, ++x_begin)
        *nzb = f2(*nzb, *x_begin);

      set_row_(row, nzb_, nzb_ + nCols());
    }

    //--------------------------------------------------------------------------------
    /**
     * Apply binary functor to each element of a given row and x, and put the result
     * in y.
     */
    template <typename BinaryFunction, typename InputIterator, typename OutputIterator>
    inline void
    elementRowApply(size_type row, const BinaryFunction& f2,
                    InputIterator x, OutputIterator y) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_INPUT_ITERATOR(InputIterator);
        assert_valid_row_(row, "elementRowApply");
      } // End pre-conditions

      if (nnzr_[row] == 0) {
        InputIterator x_end = x + nCols();
        for (; x != x_end; ++x, ++y)
          *y = f2(0, *x);
        return;
      }

      size_type *ind = ind_begin_(row), *ind_end = ind_end_(row);
      value_type *nz = nz_begin_(row);

      for (size_type col = 0; col != nCols(); ++col, ++y, ++x) {
        if (ind != ind_end && *ind == col) {
          *y = f2(*nz, *x);
          ++ind; ++nz;
        } else {
          *y = f2(0, *x);
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies given binary functor f to the non-zeros of a col and the given vector:
     *
     *  this[row,col] = f2(this[row,col], x[col])
     *
     * where:
     *  row,col in [0,nrows) X {col} s.t. this[row,col] != 0
     *
     * @param col[0 <= size_type < ncols] the col to process
     * @param f2 [binary function] a binary functor
     * @param x_begin [InputIterator] a forward iterator to the vector to use,
     *  a dense vector of size nrows
     *
     * @b Exceptions:
     *  @li If col is not in range.
     */
    template <typename BinaryFunction, typename InputIterator>
    inline void
    elementColNZApply(size_type col, const BinaryFunction& f2, InputIterator x_begin)
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_INPUT_ITERATOR(InputIterator);
        assert_valid_col_(col, "elementColNZApply");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        const difference_type offset = col_(row, col);
        if (offset >= 0) {
          value_type *nz = nz_begin_(row) + offset;
          *nz = f2(*nz, *x_begin);
          if (isZero_(*nz))
            erase_(row, ind_begin_(row) + offset);
        }
        ++x_begin;
      }
    }

    //--------------------------------------------------------------------------------
    template <typename BinaryFunction, typename InputIterator, typename OutputIterator>
    inline void
    elementColNZApply(size_type col, const BinaryFunction& f2,
                      InputIterator x, OutputIterator y) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_INPUT_ITERATOR(InputIterator);
        assert_valid_col_(col, "elementColNZApply");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        const difference_type offset = col_(row, col);
        *y = offset >= 0 ? f2(*(nz_begin_(row) + offset), *x) : 0;
        ++x; ++y;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies given binary functor f to all the elements of a col and the given vector:
     *
     *  this[row,col] = f2(this[row,col], x[col])
     *
     * where:
     *  row,col in [0,nrows) X {col}
     *
     * @param col [0 <= size_type < ncols] the col to process
     * @param f2 [binary function] a binary functor
     * @param x_begin [InputIterator] a forward iterator to the vector to use,
     *  a dense vector of size nrows
     *
     * @b Exceptions:
     *  @li If col is not in range.
     */
    template <typename BinaryFunction, typename InputIterator>
    inline void
    elementColApply(size_type col, const BinaryFunction& f2, InputIterator x_begin)
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_INPUT_ITERATOR(InputIterator);
        assert_valid_col_(col, "elementColApply");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        set(row, col, f2(get(row, col), *x_begin));
        ++x_begin;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies given functor to non-zeros of this sparse matrix and other:
     *
     *  this[row,col] = f2(this[row,col], other[row,col])
     *
     * where:
     *  row,col in [0,nrows) X [0,ncols) s.t. this[row,col] != 0
     *
     * This works for functors such as *, where x * 0 = 0,
     * and therefore there it no need to work on the zeros of the sparse matrix.
     * The resulting sparse matrix has at most the same number of non-zeros
     * as the initial sparse matrix, but maybe less.
     */
    template <typename BinaryFunction>
    inline void
    elementNZApply(const SparseMatrix& other, const BinaryFunction& f2)
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        NTA_ASSERT(other.nRows() == nRows())
          << "SparseMatrix elementNZApply: Number of rows don't match: "
          << nRows() << " and " << other.nRows();
        NTA_ASSERT(other.nCols() == nCols())
          << "SparseMatrix elementNZApply: Number of columns don't match: "
          << nCols() << " and " << other.nCols();
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        size_type nnzr2 = 0;
        ITERATE_ON_ROW {
          value_type val = f2(*nz, other.get(row, *ind));
          if (!isZero_(val)) {
            ind_[row][nnzr2] = *ind;
            nz_[row][nnzr2] = val;
            ++nnzr2;
          }
        }
        nnzr_[row] = nnzr2;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies given functor to all elements of this sparse matrix
     * (zeros and non-zeros), and to the corresponding elements of other:
     *
     *  this[row,col] = f2(this[row,col], other[row,col])
     *
     * where:
     *  row,col in [0,nrows) X [0,ncols)
     *
     * This works for any functor. The resulting matrix may have more or less
     * non-zeros than the initial one.
     */
    template <typename BinaryFunction>
    inline void
    elementApply(const SparseMatrix& other, const BinaryFunction& f2)
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        NTA_ASSERT(other.nRows() == nRows())
          << "SparseMatrix elementApply: Number of rows don't match: "
          << nRows() << " and " << other.nRows();
        NTA_ASSERT(other.nCols() == nCols())
          << "SparseMatrix elementApply: Number of columns don't match: "
          << nCols() << " and " << other.nCols();

      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        const_cast<SparseMatrix&>(other).to_nzb_(row);
        elementRowApply(row, f2, other.nzb_);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies unary function to outer product of two ranges passed in:
     *
     *  this[row,col] = f1(this[row,col])
     *
     * where:
     *  row,col in [row range) X [col range)
     */
    template <typename InputIterator, typename UnaryFunction>
    inline void
    applyOuter(InputIterator row_begin, InputIterator row_end,
               InputIterator col_begin, InputIterator col_end,
               const UnaryFunction& f1)
    {
      { // Pre-conditions
        ASSERT_UNARY_FUNCTION(UnaryFunction, value_type, value_type);
        ASSERT_INPUT_ITERATOR(InputIterator);
      } // End pre-conditions

      for (InputIterator row = row_begin; row != row_end; ++row) {
        for (InputIterator col = col_begin; col != col_end; ++col) {
          size_type i = *row, j = *col;
          set(i, j, f1(get(i, j)));
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Applies binary function to outer product of two ranges passed in:
     *
     *  this[i,j] = f2(this[i,j], other[ii, jj])
     *
     * where:
     *  i,j in [row range) X [col range)
     *  and ii = i - row_begin, jj = j - col_begin
     *
     * Note: the get is "dense" on other but enumerated on this?
     */
    template <typename InputIterator, typename BinaryFunction, typename Other>
    inline void
    applyOuter(InputIterator row_begin, InputIterator row_end,
               InputIterator col_begin, InputIterator col_end,
               const BinaryFunction& f2, const Other& other)
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_INPUT_ITERATOR(InputIterator);
      } // End pre-conditions

      size_type i_other = 0;
      for (InputIterator row = row_begin; row != row_end; ++row, ++i_other) {
        size_type j_other = 0;
        for (InputIterator col = col_begin; col != col_end; ++col, ++j_other) {
          size_type i = *row, j = *col;
          set(i, j, f2(get(i,j), other.get(i_other, j_other)));
        }
      }
    }

    //--------------------------------------------------------------------------------
    // ACCUMULATE
    //--------------------------------------------------------------------------------

    /**
     * Accumulates the non-zeros of the given row, using the binary functor f2:
     *
     *  result = init
     *  for k in [0,ncols) s.t. this[row,k] != 0:
     *   result = f2(result, this[row,k])
     *
     * @param row [0 <= size_type < nrows] the target row
     * @param f2 [BinaryFunction] the binary functor to use for the accumulation
     * @param init [value_type (0)] an optional initial value
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows
     *
     * TODO Compare to performance of std::accumulate, look at assembly.
     */
    template <typename BinaryFunction>
    inline value_type accumulateRowNZ(size_type row, const BinaryFunction& f2,
                                      const value_type& init =0) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        assert_valid_row_(row, "accumulateRowNZ");
      } // End pre-conditions

      value_type *nz = nz_begin_(row);
      value_type *nz_end1 = nz + 4*(nnzr_[row] / 4), *nz_end2 = nz_end_(row);
      value_type result = init;

      for (; nz != nz_end1; nz += 4) {
        result = f2(result, *nz);
        result = f2(result, *(nz+1));
        result = f2(result, *(nz+2));
        result = f2(result, *(nz+3));
      }

      for (; nz != nz_end2; ++nz)
        result = f2(result, *nz);

      return result;

      //return std::accumulate(nz_begin_(row), nz_end_(row), init, f);
    }

    //--------------------------------------------------------------------------------
    /**
     * Accumulates the non-zeros on all the rows of this SparseMatrix,
     * using the binary functor f2, and puts the result to an iterator:
     *
     *  result[i] = init
     *  for for k in [0,ncols) s.t. this[i,k] != 0:
     *   result[i] = f2(result, this[i,k])
     *
     * where:
     *  i in [0,nrows)
     *
     * @param result [OutputIterator] the results
     * @param f2 [BinaryFunction] the binary functor to use for the accumulation
     * @param init [value_type (0)] an optional initial value
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator, typename BinaryFunction>
    inline void accumulateAllRowsNZ(OutputIterator result, const BinaryFunction& f2,
                                    const value_type& init =0) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        *result = accumulateRowNZ(row, f2, init);
        ++result;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Accumulates all the values on the given row, using the binary functor f2:
     *
     * result = init
     * for col in [0,ncols):
     *  result = f2(result, this[row,col])
     *
     * @param row [0 <= size_type < nrows] the target row
     * @param f2 [BinaryFunction] the binary functor to use for the accumulation
     * @param init [value_type (0)] an optional initial value
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows
     */
    template <typename BinaryFunction>
    inline value_type accumulateRow(size_type row, const BinaryFunction& f2,
                                    const value_type& init =0) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        assert_valid_row_(row, "accumulateRow");
      } // End pre-conditions

      size_type col = 0;
      value_type result = init;

      ITERATE_ON_ROW {
        size_type ind_end2 = *ind;
        while (col != ind_end2) {
          result = f(result, value_type(0));
          ++col;
        }
        result = f2(result, *nz);
      }

      return result;
    }

    //--------------------------------------------------------------------------------
    /**
     * Accumulates the non-zeros on all the rows of this SparseMatrix,
     * using the binary functor f2, and puts the result to an iterator:
     *
     *  result[i] = init
     *  for for k in [0,ncols):
     *   result[i] = f2(result, this[i,k])
     *
     * where:
     *  i in [0,nrows)
     *
     * @param result [OutputIterator] the results
     * @param f2 [F] the binary functor to use for the accumulation
     * @param init [value_type (0)] an optional initial value
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator, typename BinaryFunction>
    inline void accumulateAllRows(OutputIterator result, const BinaryFunction& f2,
                                  const value_type& init =0) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_OUTPUT_ITERATOR(OutputIterator, value_type);
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        *result = accumulateRow(row, f2, init);
        ++result;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Accumulates the non-zeros of the given column, using the binary functor f2:
     *
     *  result = init
     *  for row in [0,nrows):
     *   result = f2(result, this[row,col]) s.t. this[row,col] != 0
     *
     * @param col [0 <= size_type < ncols] the target column
     * @param f2 [BinaryFunction] the binary functor to use for the accumulation
     * @param init [value_type (0)] an optional initial value
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols
     */
    template <typename BinaryFunction>
    inline value_type accumulateColNZ(size_type col, const BinaryFunction& f2,
                                      const value_type& init =0) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        assert_valid_col_(col, "accumulateColNZ");
      } // End pre-conditions

      value_type result = init;

      ITERATE_ON_ALL_ROWS {
        const difference_type offset = col_(row, col);
        if (offset >= 0)
          result = f2(result, value_(row, offset));
      }

      return result;
    }

    //--------------------------------------------------------------------------------
    /**
     * Accumulates the non-zeros on all the columns of this SparseMatrix
     * using the binary functor f2, and puts the result to an iterator:
     *
     *  result[col] = init
     *  for row in [0,nrows):
     *   result[col] = f2(result, this[row,col]) s.t. this[row,col] != 0
     *
     * where:
     *  col in [0,ncols)
     *
     * @param result [OutputIterator] the results
     * @param f2 [F] the binary functor to use for the accumulation
     * @param init [value_type (0)] an optional initial value
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator, typename BinaryFunction>
    inline void accumulateAllColsNZ(OutputIterator result, const BinaryFunction& f2,
                                    const value_type& init =0) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_OUTPUT_ITERATOR(OutputIterator, value_type);
      } // End pre-conditions

      std::fill(result, result + nCols(), (value_type)init);

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          value_type& res = result[*ind];
          res = f2(res, *nz);
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Accumulates all the values on the given column, using the binary functor f2:
     *
     *  result[col] = init
     *  for row in [0,nrows):
     *   result[col] = f2(result, this[row,col])
     *
     * @param row [0 <= size_type < ncols] the target column
     * @param f2 [BinaryFunction] the binary functor to use for the accumulation
     * @param init [value_type (0)] an optional initial value
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols
     */
    template <typename BinaryFunction>
    inline value_type accumulateCol(size_type col, const BinaryFunction& f2,
                                    const value_type& init =0) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        assert_valid_col_(col, "accumulate");
      } // End pre-conditions

      value_type result = init;

      ITERATE_ON_ALL_ROWS {
        const difference_type offset = col_(row, col);
        if (offset >= 0)
          result = f2(result, value_(row, offset));
        else
          result = f2(result, value_type(0));
      }

      return result;
    }

    //--------------------------------------------------------------------------------
    /**
     * Accumulates the non-zeros on all the columns of this SparseMatrix,
     * using the binary functor f2, and puts the result to an iterator:
     *
     *  result[col] = init
     *  for row in [0,nrows):
     *   result[col] = f2(result, this[row,col])
     *
     * where:
     *  col in [0,ncols)
     *
     * @param result [OutputIterator] the results
     * @param f2 [BinaryFunction] the binary functor to use for the accumulation
     * @param init [value_type (0)] an optional initial value
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator, typename BinaryFunction>
    inline void accumulateAllCols(OutputIterator result, const BinaryFunction& f2,
                                  const value_type& init =0) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
        ASSERT_OUTPUT_ITERATOR(OutputIterator, value_type);
      } // End pre-conditions

      const size_type ncols = nCols();

      std::fill(result, result + nCols(), (value_type)init);

      ITERATE_ON_ALL_ROWS {
        size_type *ind = ind_begin_(row);
        value_type *nz = nz_begin_(row);
        for (size_type col = 0; col != ncols; ++col) {
          if (col == *ind) {
            value_type& res = result[*ind];
            res = f(res, *nz);
            ++ind; ++nz;
          } else {
            result[col] = f(result[col], value_type(0));
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Accumulate all the non-zeros in this matrix using the binary functor f2,
     * starting with an initial value of init:
     *
     *  result = init
     *  for row,col in [0,nrows) X [0,ncols):
     *   if this[row,col] != 0:
     *    result = f2(result, this[row,col])
     *
     * @b Complexity:
     *  @li O(nnz)
     *
     * @b Exceptions:
     *  @li If f2 is not a binary functor.
     */
    template <typename BinaryFunction>
    inline value_type accumulateNZ(BinaryFunction f2, const value_type& init) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
      } // End pre-conditions

      value_type result = init;

      ITERATE_ON_ALL_ROWS
        result = accumulateRowNZ(row, f2, result);

      return result;
    }

    //--------------------------------------------------------------------------------
    /**
     * Accumulate all the elements in this matrix using the binary functor f2,
     * starting with an initial value of init, iterating over the non-zeros as well
     * as the zeros:
     *
     *  result = init
     *  for row,col in [0,nrows) X [0,ncols):
     *    result = f2(result, this[row,col])
     *
     * @b Complexity:
     *  @li O(nrows*ncols)
     *
     * @b Exceptions:
     *  @li If f2 is not a binary functor.
     */
    template <typename BinaryFunction>
    inline value_type accumulate(BinaryFunction f2, const value_type& init) const
    {
      { // Pre-conditions
        ASSERT_BINARY_FUNCTION(BinaryFunction, value_type, value_type, value_type);
      } // End pre-conditions

      value_type result = init;

      ITERATE_ON_ALL_ROWS
        result = accumulateRow(row, f2, result);

      return result;
    }

    //--------------------------------------------------------------------------------
    // TRANSPOSE
    //--------------------------------------------------------------------------------
    /**
     * Computes the transpose of this sparse matrix, storing the result
     * in tr. Discards the previous value of tr.
     *
     * Non-mutating, O(2*nnz)
     *
     * @param tr [SparseMatrix<size_type, value_type>] the transpose sparse matrix
     *
     * @b Exceptions:
     *  @li Not enough memory (error)
     */
    inline void transpose(SparseMatrix& tr) const
    {
      using namespace std;

      vector<vector<size_type> > tind(nCols());
      vector<vector<value_type> > tnz(nCols());

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          tind[*ind].push_back(row);
          tnz[*ind].push_back(*nz);
        }
      }

      size_type nnz = nNonZeros();
      size_type tnrows = nCols();
      size_type tncols = nRows();

      tr.deallocate_();
      tr.allocate_(tnrows, tncols);
      tr.nrows_ = tnrows;
      tr.ncols_ = tncols;

      tr.ind_mem_ = new size_type[nnz];
      size_type *indp = tr.ind_mem_;
      tr.nz_mem_ = new value_type[nnz];
      value_type *nzp = tr.nz_mem_;

      for (size_type row = 0; row != tnrows; ++row) {
        const vector<size_type>& rind = tind[row];
        const vector<value_type>& rnz = tnz[row];
        size_type nk = (size_type) rind.size();
        tr.nnzr_[row] = nk;
        tr.ind_[row] = indp;
        tr.nz_[row] = nzp;
        for (size_type k = 0; k != nk; ++k) {
          *indp++ = rind[k];
          *nzp++ = rnz[k];
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * In place transpose.
     */
    inline void transpose()
    {
      using namespace std;

      vector<vector<size_type> > tind(nCols());
      vector<vector<value_type> > tnz(nCols());

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          tind[*ind].push_back(row);
          tnz[*ind].push_back(*nz);
        }
      }

      size_type nnz = nNonZeros();
      size_type tnrows = nCols();
      size_type tncols = nRows();

      deallocate_();
      allocate_(tnrows, tncols);
      ind_mem_ = new size_type [nnz];
      nz_mem_ = new value_type [nnz];

      nrows_ = tnrows;
      ncols_ = tncols;

      size_type *indp = ind_mem_;
      value_type *nzp = nz_mem_;

      for (size_type row = 0; row != tnrows; ++row) {
        const vector<size_type>& rind = tind[row];
        const vector<value_type>& rnz = tnz[row];
        size_type nk = rind.size();
        nnzr_[row] = nk;
        ind_[row] = indp;
        nz_[row] = nzp;
        for (size_type k = 0; k != nk; ++k) {
          *indp++ = rind[k];
          *nzp++ = rnz[k];
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds this matrix to its transpose. This creates symmetric matrices.
     */
    inline void addToTranspose(SparseMatrix& sm) const
    {
      { // Pre-conditions
        NTA_ASSERT(nRows() == nCols())
          << "SparseMatrix addToTranspose: "
          << "Matrix needs to be square";
      } // End pre-conditions

      SparseMatrix tmp(nCols(), nCols());
      this->transpose(tmp);
      sm.copy(*this);
      sm.add(tmp);
    }

    //--------------------------------------------------------------------------------
    /**
     * Inline version, that adds this to its transpose.
     */
    inline void addToTranspose()
    {
      { // Pre-conditions
        NTA_ASSERT(nRows() == nCols())
          << "SparseMatrix addToTranspose: "
          << "Matrix needs to be square";
      } // End pre-conditions

      SparseMatrix tmp(nCols(), nCols());
      this->transpose(tmp);
      this->add(tmp);
    }

    //--------------------------------------------------------------------------------
    // THRESHOLD
    //--------------------------------------------------------------------------------

    /**
     * Removes the non-zeros on this row that are below the given threshold.
     *
     * this[row,col] = this[row,col] >= threshold
     *  for col in [0,ncols) s.t. this[row,col] != 0
     *
     * @param row [0 <= size_type < nrows] the row to threshold
     * @param threshold [value_type] the threshold to use
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows
     */
    inline void
    thresholdRow(size_type row, const value_type& threshold =nta::Epsilon)
    {
      { // Pre-conditions
        assert_valid_row_(row, "thresholdRow");
      } // End pre-conditions

      filterRow(row, std::bind2nd(std::greater_equal<value_type>(), threshold));
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator1, typename OutputIterator2>
    inline size_type thresholdRow(size_type row,
                                  const value_type& threshold,
                                  OutputIterator1 cut_j,
                                  OutputIterator2 cut_nz)
    {
      { // Pre-conditions
        assert_valid_row_(row, "thresholdRow");
      } // End pre-conditions

      return filterRow(row,
                       std::bind2nd(std::greater_equal<value_type>(),threshold),
                       cut_j, cut_nz);
    }

    //--------------------------------------------------------------------------------
    /**
     * Removes non-zeros on the given column that are below a threshold.
     *
     * this[row,col] = this[row,col] >= threshold
     *  for row in [0,nrows) s.t. this[row,col] != 0
     *
     * @param col [0 <= size_type < ncols] the column index
     * @param thresold [value_type] the threshold to apply
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols
     */
    inline
    void thresholdCol(size_type col, const value_type& threshold =nta::Epsilon)
    {
      { // Pre-conditions
        assert_valid_col_(col, "thresholdCol");
      } // End pre-conditions

      filterCol(col, std::bind2nd(std::greater_equal<value_type>(), threshold));
    }

    //--------------------------------------------------------------------------------
    /**
     * Removes non-zeros that are below a given threshold.
     *
     * this[row,col] = this[row,col] >= threshold
     *  for row,col in [0,nrows) X [0,ncols) s.t. this[row,col] != 0
     *
     * @param thresold [value_type] the threshold to apply
     *
     * @b Exceptions:
     *  @li None.
     */
    inline void threshold(const value_type& threshold =nta::Epsilon)
    {
      filter(std::bind2nd(std::greater_equal<value_type>(),threshold));
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator1, typename OutputIterator2>
    inline size_type threshold(const value_type& threshold,
                               OutputIterator1 cut_i,
                               OutputIterator1 cut_j,
                               OutputIterator2 cut_nz)
    {
      return filter(std::bind2nd(std::greater_equal<value_type>(),threshold),
                    cut_i, cut_j, cut_nz);
    }

    //--------------------------------------------------------------------------------
    // CLIP
    //--------------------------------------------------------------------------------

    /**
     * Clips a row with the value passed in: if a non-zero is greater than the value
     * then it is replaced by the value. Otherwise, the non-zero is left unchanged.
     *
     * this[row,col] = min(val, this[row,col])
     *  for col in [0,ncols) s.t. this[row,col] != 0
     *
     * @param row [0 <= size_type < nrows] the row on which to operate
     * @param val [value_type] the value to use for clipping
     *
     * @b Complexity:
     *  @li O(nnzr)
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert).
     */
    inline
    void clipRow(size_type row, value_type val, bool above =true)
    {
      { // Pre-conditions
        assert_valid_row_(row, "clipRow");
      } // End pre-conditions

      if (above)
        elementRowNZApply(row, ClipAbove<value_type>(val));
      else
        elementRowNZApply(row, ClipBelow<value_type>(val));
    }

    //--------------------------------------------------------------------------------
    /**
     * Clip row both above and below given values.
     */
    inline void
    clipRowAboveAndBelow(size_type row, value_type a, value_type b)
    {
      { // Pre-conditions
        assert_valid_row_(row, "clipRowAboveAndBelow");
        NTA_ASSERT(a <= b);
      } // End pre-conditions

      elementRowNZApply(row, ClipBelow<value_type>(a));
      elementRowNZApply(row, ClipAbove<value_type>(b));
    }

    //--------------------------------------------------------------------------------
    /**
     * Clips a column with the value passed in: if a non-zero is greater than the
     * value then it is replaced by the value. Otherwise, the non-zero is left
     * unchanged.
     *
     * this[row,col] = min(val, this[row,col])
     *  for row in [0,nrows) s.t. this[row,col] != 0
     *
     * @param col [0 <= size_type < ncols] the col on which to operate
     * @param val [value_type] the value to use for clipping
     *
     * @b Complexity:
     *  @li O(nnzr)
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols (assert).
     */
    inline
    void clipCol(size_type col, value_type val, bool above =true)
    {
      { // Pre-conditions
        assert_valid_col_(col, "clipCol");
      } // End pre-conditions

      if (above)
        elementColNZApply(col, ClipAbove<value_type>(val));
      else
        elementColNZApply(col, ClipBelow<value_type>(val));
    }

    //--------------------------------------------------------------------------------
    /**
     * Clips col both above and below given values.
     */
    inline void
    clipColAboveAndBelow(size_type col, value_type a, value_type b)
    {
      { // Pre-conditions
        assert_valid_col_(col, "clipColAboveAndBelow");
        NTA_ASSERT(a <= b);
      } // End pre-conditions

      elementColNZApply(col, ClipBelow<value_type>(a));
      elementColNZApply(col, ClipAbove<value_type>(b));
    }

    //--------------------------------------------------------------------------------
    /**
     * Clip whole matrix: all values above val become val. Values below val are
     * unchanged.
     *
     * this[row,col] = min(val, this[row,col])
     *  for row,col in [0,nrows) X [0,ncols) s.t. this[row,col] != 0
     *
     * @param val [value_type] the value to use for clipping
     *
     * @b Complexity:
     *  @li O(nnzr)
     */
    inline void clip(value_type val, bool above =true)
    {
      ITERATE_ON_ALL_ROWS
        clipRow(row, val, above);
    }

    //--------------------------------------------------------------------------------
    /**
     * Clips whole matrix below and above given values.
     */
    inline void clipAboveAndBelow(value_type a, value_type b)
    {
      ITERATE_ON_ALL_ROWS
        clipRowAboveAndBelow(row, a, b);
    }

    //--------------------------------------------------------------------------------
    // FIND
    //--------------------------------------------------------------------------------

    // TODO: find with values returned

    /**
     * Counts the elements that satisfy the passed unary predicate
     * inside the box [begin_row, end_row) X [begin_col, end_col).
     *
     * @param begin_row [0 <= size_type < nrows] the start row of the box
     * @param end_row [0 <= size_type <= nrows] one past the last row of the box
     * @param begin_col [0 <= size_type < ncols] the start col of the box
     * @param end_col [0 <= size_type <= ncols] one past the last col of the box
     * @param f1 [UnaryPredicate] the unary predicate to use for testing elements
     * @retval [0 <= size_type < nrows*ncols] the count of elemens that satisfy
     *  the unary predicate
     *
     * @b Complexity:
     *  @li Worst case: O(nnz in box + 2 * n box rows * log(nnzr)) (if f1(0) == true)
     *  @li Best case: O(nnz in box) (if f1(0) == false)
     *
     * @b Exceptions:
     *  @li If box invalid (assert)
     *  @li If predicate not unary (compile time)
     */
    template <typename UnaryPredicate>
    inline size_type
    countWhere(size_type begin_row, size_type end_row,
               size_type begin_col, size_type end_col,
               const UnaryPredicate& f1) const
    {
      { // Pre-conditions
        ASSERT_UNARY_PREDICATE(UnaryPredicate, value_type);
        assert_valid_box_(begin_row, end_row, begin_col, end_col, "countWhere");
      } // End pre-conditions

      size_type count = 0;

      ITERATE_ON_BOX_ROWS {
        ITERATE_ON_BOX_COLS {
          if (f1(*nz))
            ++count;
        }
      }

      if (f1(0))
        count += (end_row-begin_row)*(end_col-begin_col)
          - nNonZerosInBox(begin_row, end_row, begin_col, end_col);

      { // Post-conditions
        NTA_ASSERT(0 <= count && count <= (end_row-begin_row)*(end_col-begin_col))
          << "SparseMatrix countWhere: "
          << "post-condition: Found count = " << count
          << " when box has size = " << (end_row-begin_row)*(end_col-begin_col);
      } // End post-conditions

      return count;
    }

    //--------------------------------------------------------------------------------
    /**
     * Find the elements that satisfy the passed unary predicate inside the box
     * [begin_row, end_row) X [begin_col, end_col) and return their indices.
     * The indices returned are relative to (0,0) in this matrix. To adjust indices,
     * subtract begin_row and begin_col afterwards.
     *
     * @param begin_row [0 <= size_type < nrows] the start row of the box
     * @param end_row [0 <= size_type <= nrows] one past the last row of the box
     * @param begin_col [0 <= size_type < ncols] the start col of the box
     * @param end_col [0 <= size_type <= ncols] one past the last col of the box
     * @param f1 [UnaryPredicate] the unary predicate to use for testing elements
     * @param row_it [OutputIterator] iterator to the beginning of the container
     *  that will contain the row indices of the selected elements
     * @param col_it [OutputIterator] iterator to the beginning of the container
     *  that will contain the col indices of the selected elements
     *
     * @b Complexity:
     *  @li Worst case: O(box size) (if f1(0) == true)
     *  @li Best case: O(nnz in box) (if f1(0) == false)
     *
     * @b Exceptions:
     *  @li If box invalid (assert)
     *  @li If predicate not unary (compile time)
     *  @li If row_it or col_it not output iterator (compile time)
     */
    template <typename UnaryPredicate, typename OutputIterator1>
    inline void
    findIndices(size_type begin_row, size_type end_row,
                size_type begin_col, size_type end_col,
                const UnaryPredicate& f1,
                OutputIterator1 row_it, OutputIterator1 col_it) const
    {
      { // Pre-conditions
        ASSERT_UNARY_PREDICATE(UnaryPredicate, value_type);
        ASSERT_OUTPUT_ITERATOR(OutputIterator1, size_type);
        assert_valid_box_(begin_row, end_row, begin_col, end_col, "findIndices");
      } // End pre-conditions

      if (!f1(0)) {

        ITERATE_ON_BOX_ROWS {
          ITERATE_ON_BOX_COLS {
            value_type v = *nz;
            if (f1(v)) {
              *row_it = row;
              *col_it = *ind;
              ++row_it; ++col_it;
            }
          }
        }

      } else {

        ITERATE_ON_BOX_ROWS {
          size_type j = begin_col;
          ITERATE_ON_BOX_COLS {
            size_type l = *ind;
            for (; j != l; ++j) {
              *row_it = row;
              *col_it = j;
              ++row_it; ++col_it;
            }
            value_type v = *nz;
            if (f1(v)) {
              *row_it = row;
              *col_it = *ind;
              ++row_it; ++col_it;
            }
            ++j;
          }
          size_type l = std::min(end_col, nCols());
          for (; j != l; ++j) {
            *row_it = row;
            *col_it = j;
            ++row_it; ++col_it;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Counts all the elements in the box [begin_row,end_row) X [begin_col,end_col)
     * inside this matrix whose value is the passed value.
     *
     * @param begin_row [0 <= size_type < nrows] the start row of the box
     * @param end_row [0 <= size_type <= nrows] one past the last row of the box
     * @param begin_col [0 <= size_type < ncols] the start col of the box
     * @param end_col [0 <= size_type <= ncols] one past the last col of the box
     * @param value [value_type] the value
     * @retval [0 <= size_type < nrows*ncols] the count of elements that match
     *  value
     *
     * @b Complexity:
     *  @li See findIndices.
     *
     * @b Exceptions:
     *  @li If box invalid (assert)
     */
    inline size_type countWhereEqual(size_type begin_row, size_type end_row,
                                     size_type begin_col, size_type end_col,
                                     const value_type& value) const
    {
      { // Pre-conditions
      } // End pre-conditions

      return countWhere(begin_row, end_row, begin_col, end_col,
                        std::bind2nd(std::equal_to<value_type>(), value));
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds all the elements in the box [begin_row,end_row) X [begin_col,end_col)
     * inside this matrix whose value is the passed value.
     * The indices returned are relative to (0,0) in this matrix. To adjust indices,
     * subtract begin_row and begin_col afterwards.
     *
     * @param begin_row [0 <= size_type < nrows] the start row of the box
     * @param end_row [0 <= size_type <= nrows] one past the last row of the box
     * @param begin_col [0 <= size_type < ncols] the start col of the box
     * @param end_col [0 <= size_type <= ncols] one past the last col of the box
     * @param row_it [OutputIterator1] iterator for row indices of the matches
     * @param col_it [OutputIterator1] iterator for col indices of the matches
     * @param value [value_type] the value
     *
     * @b Complexity:
     *  @li See findIndices.
     *
     * @b Exceptions:
     *  @li If OutputIterator1 not an output iterator.
     *  @li If OutputIterator2 not an output iterator.
     */
    template <typename OutputIterator1>
    inline void whereEqual(size_type begin_row, size_type end_row,
                           size_type begin_col, size_type end_col,
                           const value_type& value,
                           OutputIterator1 row_it, OutputIterator1 col_it) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator1, size_type);
      } // End pre-conditions

      findIndices(begin_row, end_row, begin_col, end_col,
                  std::bind2nd(std::equal_to<value_type>(), value),
                  row_it, col_it);
    }

    //--------------------------------------------------------------------------------
    /**
     * Counts all the elements in the box [begin_row,end_row) X [begin_col,end_col)
     * inside this matrix whose value is greater than the passed value.
     *
     * @param begin_row [0 <= size_type < nrows] the start row of the box
     * @param end_row [0 <= size_type <= nrows] one past the last row of the box
     * @param begin_col [0 <= size_type < ncols] the start col of the box
     * @param end_col [0 <= size_type <= ncols] one past the last col of the box
     * @param value [value_type] the value
     * @retval [0 <= size_type < nrows*ncols] the count of elements that match
     *  value
     *
     * @b Complexity:
     *  @li See findIndices.
     *
     * @b Exceptions:
     *  @li If box invalid (assert)
     */
    inline size_type countWhereGreater(size_type begin_row, size_type end_row,
                                       size_type begin_col, size_type end_col,
                                       const value_type& value) const
    {
      { // Pre-conditions
      } // End pre-conditions

      return countWhere(begin_row, end_row, begin_col, end_col,
                        std::bind2nd(std::greater<value_type>(), value));
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds all the elements in the box [begin_row,end_row) X [begin_col,end_col)
     * inside this matrix whose value is greater than the passed value.
     * The indices returned are relative to (0,0) in this matrix. To adjust indices,
     * subtract begin_row and begin_col afterwards.
     *
     * @param begin_row [0 <= size_type < nrows] the start row of the box
     * @param end_row [0 <= size_type <= nrows] one past the last row of the box
     * @param begin_col [0 <= size_type < ncols] the start col of the box
     * @param end_col [0 <= size_type <= ncols] one past the last col of the box
     * @param row_it [OutputIterator1] iterator for row indices of the matches
     * @param col_it [OutputIterator1] iterator for col indices of the matches
     * @param value [value_type] the value
     *
     * @b Complexity:
     *  @li See findIndices.
     *
     * @b Exceptions:
     *  @li If OutputIterator1 not an output iterator.
     *  @li If OutputIterator2 not an output iterator.
     */
    template <typename OutputIterator1>
    inline void whereGreater(size_type begin_row, size_type end_row,
                             size_type begin_col, size_type end_col,
                             const value_type& value,
                             OutputIterator1 row_it, OutputIterator1 col_it) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator1, size_type);
      } // End pre-conditions

      findIndices(begin_row, end_row, begin_col, end_col,
                  std::bind2nd(std::greater<value_type>(), value),
                  row_it, col_it);
    }

    //--------------------------------------------------------------------------------
    /**
     * Counts all the elements in the box [begin_row,end_row) X [begin_col,end_col)
     * inside this matrix whose value is greater than the passed value.
     *
     * @param begin_row [0 <= size_type < nrows] the start row of the box
     * @param end_row [0 <= size_type <= nrows] one past the last row of the box
     * @param begin_col [0 <= size_type < ncols] the start col of the box
     * @param end_col [0 <= size_type <= ncols] one past the last col of the box
     * @param value [value_type] the value
     * @retval [0 <= size_type < nrows*ncols] the count of elements that match
     *  value
     *
     * @b Complexity:
     *  @li See findIndices.
     *
     * @b Exceptions:
     *  @li If box invalid (assert)
     */
    inline size_type countWhereGreaterEqual(size_type begin_row, size_type end_row,
                                            size_type begin_col, size_type end_col,
                                            const value_type& value) const
    {
      { // Pre-conditions
      } // End pre-conditions

      return countWhere(begin_row, end_row, begin_col, end_col,
                        std::bind2nd(std::greater_equal<value_type>(), value));
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds all the elements in the box [begin_row,end_row) X [begin_col,end_col)
     * inside this matrix whose value is greater than the passed value.
     * The indices returned are relative to (0,0) in this matrix. To adjust indices,
     * subtract begin_row and begin_col afterwards.
     *
     * @param begin_row [0 <= size_type < nrows] the start row of the box
     * @param end_row [0 <= size_type <= nrows] one past the last row of the box
     * @param begin_col [0 <= size_type < ncols] the start col of the box
     * @param end_col [0 <= size_type <= ncols] one past the last col of the box
     * @param row_it [OutputIterator1] iterator for row indices of the matches
     * @param col_it [OutputIterator1] iterator for col indices of the matches
     * @param value [value_type] the value
     *
     * @b Complexity:
     *  @li See findIndices.
     *
     * @b Exceptions:
     *  @li If OutputIterator1 not an output iterator.
     *  @li If OutputIterator2 not an output iterator.
     */
    template <typename OutputIterator1>
    inline void whereGreaterEqual(size_type begin_row, size_type end_row,
                                  size_type begin_col, size_type end_col,
                                  const value_type& value,
                                  OutputIterator1 row_it, OutputIterator1 col_it) const
    {
      { // Pre-conditions
        ASSERT_OUTPUT_ITERATOR(OutputIterator1, size_type);
      } // End pre-conditions

      findIndices(begin_row, end_row, begin_col, end_col,
                  std::bind2nd(std::greater_equal<value_type>(), value),
                  row_it, col_it);
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds a row that matches the passed iterators in this SparseMatrix.
     * Returns a row index in [0..nrows) if the row is found, nrows otherwise.
     *
     * TODO find row with predicate
     * TODO find columns
     */
    template <typename IndIt, typename NzIt>
    inline size_type findRow(size_type nnzr, IndIt ind_it, NzIt nz_it)
    {
      { // Pre-conditions
        NTA_ASSERT(nnzr >= 0)
          << "SparseMatrix::findRow(): "
          << "Passed in " << nnzr << " non-zeros";

        NTA_ASSERT(nnzr <= nCols())
          << "SparseMatrix::findRow(): "
          << "Passed in " << nnzr << " non-zeros "
          << "but there are only " << nCols() << " columns";

#ifdef NTA_ASSERTIONS_ON // to avoid compilation of loop
        IndIt jj = ind_it;
        NzIt nn = nz_it;
        size_type j = 0, prev = 0;
        for (j = 0; j != nnzr; ++j, ++jj, ++nn) {
          NTA_ASSERT(0 <= *jj && *jj < nCols())
            << "SparseMatrix::findRow(): "
            << "Invalid column index"
            << " - Should be >= 0 and < " << nCols();
          NTA_ASSERT(!isZero_(*nn))
            << "SparseMatrix::findRow(): "
            << "Passed zero at index: " << *jj
            << " - Should pass non-zeros only";
          if (j > 0) {
            NTA_ASSERT(prev < *jj)
              << "SparseMatrix::findRow(): "
              << "Indices need to be in strictly increasing order";
          }
          prev = *jj;
        }
#endif
      }

      for (size_type i = 0; i != nnzr; ++i, ++ind_it, ++nz_it) {
        indb_[i] = *ind_it;
        nzb_[i] = *nz_it;
      }

      ITERATE_ON_ALL_ROWS {
        if (nnzr == nnzr_[row]) {
          size_type j = 0, *ind = ind_[row];
          value_type *nz = nz_[row];
          while ((j != nnzr) && (indb_[j] == ind[j]) && (nearlyEqual(nzb_[j], nz[j])))
            ++j;
          if (j == nnzr)
            return row;
        }
      }

      return nrows;
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds all the rows in this SparseMatrix that match with the given functor.
     * Returns a row index in [0..nrows) if the row is found, nrows otherwise.
     */
    template <typename F, typename MatchIt>
    inline void findAllRows(F f, MatchIt m_it) const
    {
      for (size_type i = 0; i != nRows(); ++i) {
        if (f(ind_[i], ind_[i] + nnzr_[i], nz_[i])) {
          *m_it = i;
          ++m_it;
        }
      }
    }

    //--------------------------------------------------------------------------------
    // MIN, MAX
    //--------------------------------------------------------------------------------

    /**
     * Finds the extremum among the non-zeros of this SparseMatrix, where
     * the extremum is defined by a binary function.
     */
    template <typename BinaryFunction>
    inline void
    extremumNZ(size_type& ext_row, size_type& ext_col, value_type& ext_val,
               const BinaryFunction& f2) const
    {
      ext_row = ext_col = 0;

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          value_type val = *nz;
          if (f2(val, ext_val)) {
            ext_val = val;
            ext_row = row;
            ext_col = *ind;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the row, column and value of the maximum among the non-zeros
     * of the SparseMatrix.
     *
     * @param max_i [0 <= size_type& < nrows] row of the max
     * @param max_j [0 <= size_type& < ncols] column of the max
     * @param max_val [value_type&] value of the max
     *
     * @b Exceptions:
     *  @li None
     */
    inline void max(size_type& max_row, size_type& max_col, value_type& max_val) const
    {
      max_val = - std::numeric_limits<value_type>::max();
      extremumNZ(max_row, max_col, max_val, std::greater<value_type>());

      if (max_val == - std::numeric_limits<value_type>::max())
        max_val = 0;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the row, column and value of the minimum among the non-zeros
     * of the SparseMatrix.
     *
     * @param min_i [0 <= size_type& < nrows] row of the min
     * @param min_j [0 <= size_type& < ncols] column of the min
     * @param min_val [value_type&] value of the min
     *
     * @b Exceptions:
     *  @li None
     */
    inline void min(size_type& min_row, size_type& min_col, value_type& min_val) const
    {
      min_val = std::numeric_limits<value_type>::max();
      extremumNZ(min_row, min_col, min_val, std::less<value_type>());

      if (min_val == std::numeric_limits<value_type>::max())
        min_val = 0;
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds an extremum (according to f2) among the non-zeros on the given row.
     */
    template <typename BinaryFunction>
    inline void
    rowExtremumNZ(size_type row, size_type& idx, value_type& ext_val,
                  const BinaryFunction& f2) const
    {
      idx = 0;

      ITERATE_ON_ROW {
        value_type val = *nz;
        if (f2(val, ext_val)) {
          ext_val = val;
          idx = *ind;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the maximum value and its position for a given row.
     *
     * @param row_index [0 <= size_type < nrows] the row index
     * @retval [std::pair<size_type,value_type>] the position and value of the maximum
     *  for row row_index
     *
     * @b Exceptions:
     *  @li If row_index < 0 || row_index >= nrows
     */
    inline void rowMax(size_type row, size_type& row_max_j, value_type& row_max) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "rowMax");
      }

      row_max = - std::numeric_limits<value_type>::max();

      rowExtremumNZ(row, row_max_j, row_max, std::greater<value_type>());

      if (row_max == - std::numeric_limits<value_type>::max())
        row_max = value_type(0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the minimum value and its position for a given row.
     *
     * @param row [0 <= size_type < nrows] the row index
     * @retval [std::pair<size_type,value_type>] the position and value of the minimum
     *  for row row
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows
     */
    inline void rowMin(size_type row, size_type& row_min_j, value_type& row_min) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "rowMin");
      } // End pre-conditions

      row_min = std::numeric_limits<value_type>::max();

      rowExtremumNZ(row, row_min_j, row_min, std::less<value_type>());

      if (row_min == std::numeric_limits<value_type>::max())
        row_min = value_type(0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the row-wise maxima of this sparse matrix. The maximum for each row
     * and its index are found simultaneously.
     * Maxima is a std::vector<std::pair<size_type, value_type> > or
     * equivalent that allows direct indexing (operator[]).
     * There are as many pairs in that array as there are rows in the sparse matrix.
     * The first element in each pair is the column index of the maximum for each row,
     * and the second element is the value of that maximum.
     *
     * @param maxima [OutputIterator] the vector of the row-wise maxima (index, value)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename Maxima>
    inline void rowMax(Maxima maxima) const
    {
      ITERATE_ON_ALL_ROWS
        rowMax(row, maxima[row].first, maxima[row].second);
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the row-wise maxima of this sparse matrix, for all rows simultaneously.
     */
    template <typename OutputIterator1, typename OutputIterator2>
    inline void rowMax(OutputIterator1 indices, OutputIterator2 values) const
    {
      ITERATE_ON_ALL_ROWS {
        rowMax(row, *indices, *values);
        ++indices; ++values;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the row-wise minima of this sparse matrix. The minimum for each row
     * and its index are found simultaneously. This is the minimum among the non-zeros
     * of the row.
     * Minima is a std::vector<std::pair<size_type, value_type> > or
     * equivalent that allows direct indexing (operator[]).
     * There are as many pairs in that array as there are rows in the sparse matrix.
     * The first element in each pair is the column index of the minimum for each row,
     * and the second element is the value of that minimum.
     *
     * @param minima [OutputIterator] the vector of the row-wise minima (index, value)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename Minima>
    inline void rowMin(Minima minima) const
    {
      ITERATE_ON_ALL_ROWS
        rowMin(row, minima[row].first, minima[row].second);
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the row-wise minima of this sparse matrix for all rows simultaneously.
     */
    template <typename OutputIterator1, typename OutputIterator2>
    inline void rowMin(OutputIterator1 indices, OutputIterator2 values) const
    {
      ITERATE_ON_ALL_ROWS {
        rowMin(row, *indices, *values);
        ++indices; ++values;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the extremum according to binary predicate f2 among all the non-zeros
     * of the given column.
     */
    template <typename BinaryFunction>
    inline void
    colExtremumNZ(size_type col, size_type& idx, value_type& ext_val,
                  const BinaryFunction& f2) const
    {
      idx = 0;

      ITERATE_ON_ALL_ROWS {
        size_type *ind_it = pos_(row, col);
        if (ind_it != ind_end_(row) && *ind_it == col) {
          size_type offset = size_type(ind_it - ind_begin_(row));
          value_type val = nz_[row][offset];
          if (f2(val, ext_val)) {
            ext_val = val;
            idx = row;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the maximum value and its position for a given column.
     *
     * @param col_index [0 <= size_type < ncols] the column index
     * @retval [std::pair<size_type,value_type>] the position and value of the maximum
     *  for col col_index
     *
     * @b Exceptions:
     *  @li If col_index < 0 || col_index >= ncols.
     */
    inline void colMax(size_type col, size_type& col_max_i, value_type& col_max) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "colMax");
      } // End pre-conditions

      col_max = - std::numeric_limits<value_type>::max();

      colExtremumNZ(col, col_max_i, col_max, std::greater<value_type>());

      if (col_max == - std::numeric_limits<value_type>::max())
        col_max = 0;
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the minimum value and its position for a given column.
     *
     * @param col [0 <= size_type < ncols] the column index
     * @retval [std::pair<size_type,value_type>] the position and value of the minimum
     *  for col col
     *
     * @b Exceptions:
     *  @li NoneIf col < 0 || col >= ncols.
     */
    inline void colMin(size_type col, size_type& col_min_i, value_type& col_min) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "colMin");
      }

      col_min = std::numeric_limits<value_type>::max();

      colExtremumNZ(col, col_min_i, col_min, std::less<value_type>());

      if (col_min == std::numeric_limits<value_type>::max())
        col_min = 0;
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the column-wise maxima of this sparse matrix and their positions.
     * Maxima is a std::vector<std::pair<size_type, value_type> > or
     * equivalent that allows direct indexing (operator[]).
     * There are as many pairs in that array as
     * there are columns in the sparse matrix. The first element in each pair is
     * the column index of the maximum for each column, and the second element
     * is the value of that maximum.
     *
     * @param maxima [OutputIterator] the vector of the column-wise maxima
     *  (index, value)
     *
     * @b Exceptions:
     *  @li None
     *
     * TODO write a colExtremumNZ that does many columns simultaneously?
     */
    template <typename Maxima>
    inline void colMax(Maxima maxima) const
    {
      const size_type ncols = nCols();

      std::pair<size_type, value_type> init_p(0, - std::numeric_limits<value_type>::max());
      std::fill(maxima, maxima + ncols, init_p);

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {

          const size_type col = *ind;
          const value_type val = *nz;

          if (val > maxima[col].second) {
            maxima[col].first = row;
            maxima[col].second = val;
          }
        }
      }

      for (size_type j = 0; j != ncols; ++j) {
        if (maxima[j].second == - std::numeric_limits<value_type>::max())
          maxima[j].second = 0;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the column-wise maxima for this sparse matrix, for all columns
     * simultaneously.
     */
    template <typename OutputIterator1, typename OutputIterator2>
    inline void colMax(OutputIterator1 indices, OutputIterator2 maxima) const
    {
      const size_type ncols = nCols();

      std::fill(indices, indices + ncols, 0);
      std::fill(maxima, maxima + ncols, - std::numeric_limits<value_type>::max());

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {

          const size_type col = *ind;
          const value_type val = *nz;

          if (val > maxima[col]) {
            indices[col] = row;
            maxima[col] = val;
          }
        }
      }

      for (size_type j = 0; j != ncols; ++j) {
        if (maxima[j] == - std::numeric_limits<value_type>::max())
          maxima[j] = 0;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the column-wise minima of this sparse matrix and their positions.
     * Maxima is a std::vector<std::pair<size_type, value_type> > or
     * equivalent that allows direct indexing (operator[]).
     * There are as many pairs in that array as
     * there are columns in the sparse matrix. The first element in each pair is
     * the column index of the minimum for each column, and the second element
     * is the value of that minimum.
     *
     * @param minima [OutputIterator] the vector of the column-wise minima
     *  (index, value)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename Minima>
    inline void colMin(Minima minima) const
    {
      const size_type ncols = nCols();

      std::pair<size_type, value_type> init_p(0, std::numeric_limits<value_type>::max());
      std::fill(minima, minima + ncols, init_p);

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {

          const size_type col = *ind;
          const value_type val = *nz;

          if (val < minima[col].second) {
            minima[col].first = row;
            minima[col].second = val;
          }
        }
      }

      for (size_type j = 0; j != ncols; ++j) {
        if (minima[j].second == std::numeric_limits<value_type>::max())
          minima[j].second = 0;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Finds the column-wise minima for this sparse matrix, for all columns
     * simultaneously.
     */
    template <typename OutputIterator1, typename OutputIterator2>
    inline void colMin(OutputIterator1 indices, OutputIterator2 minima) const
    {
      const size_type ncols = nCols();

      std::fill(indices, indices + ncols, 0);
      std::fill(minima, minima + ncols, std::numeric_limits<value_type>::max());

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {

          const size_type col = *ind;
          const value_type val = *nz;

          if (val < minima[col]) {
            indices[col] = row;
            minima[col] = val;
          }
        }
      }

      for (size_type j = 0; j != ncols; ++j) {
        if (minima[j] == std::numeric_limits<value_type>::max())
          minima[j] = 0;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the position and value of the minimum non-zero in the specified box.
     */
    inline void boxMin(size_type begin_row, size_type end_row,
                       size_type begin_col, size_type end_col,
                       size_type& min_row, size_type& min_col, value_type& min_val) const
    {
      { // Pre-conditions
        assert_valid_row_range_(begin_row, end_row, "boxMin");
        assert_valid_col_range_(begin_col, end_col, "boxMin");
      } // End pre-conditions

      min_row = begin_row;
      min_col = begin_col;
      min_val = std::numeric_limits<value_type>::max();

      ITERATE_ON_BOX_ROWS {
        ITERATE_ON_BOX_COLS {
          if (*nz < min_val) {
            min_row = row;
            min_col = *ind;
            min_val = *nz;
          }
        }
      }

      if (min_val == std::numeric_limits<value_type>::max())
        min_val = (value_type) 0;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the position and value of the maximum non-zero in the specified box.
     */
    inline void boxMax(size_type begin_row, size_type end_row,
                       size_type begin_col, size_type end_col,
                       size_type& max_row, size_type& max_col, value_type& max_val) const
    {
      { // Pre-conditions
        assert_valid_row_range_(begin_row, end_row, "boxMax");
        assert_valid_col_range_(begin_col, end_col, "boxMax");
      } // End pre-conditions

      max_row = begin_row;
      max_col = begin_col;
      max_val = - std::numeric_limits<value_type>::max();

      ITERATE_ON_BOX_ROWS {
        ITERATE_ON_BOX_COLS {
          if (*nz > max_val) {
            max_row = row;
            max_col = *ind;
            max_val = *nz;
          }
        }
      }

      if (max_val == - std::numeric_limits<value_type>::max())
        max_val = (value_type) 0;
    }

    //--------------------------------------------------------------------------------
    inline std::pair<size_type, size_type> argmax() const
    {
      size_type max_row = 0, max_col = 0;
      value_type m = - std::numeric_limits<value_type>::max();

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          if (*nz > m) {
            m = *nz;
            max_row = row;
            max_col = *ind;
          }
        }
      }

      return std::make_pair(max_row, max_col);
    }

    //--------------------------------------------------------------------------------
    inline std::pair<size_type, size_type> argmin() const
    {
      size_type min_row = 0, min_col = 0;
      value_type m = std::numeric_limits<value_type>::max();

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          if (*nz < m) {
            m = *nz;
            min_row = row;
            min_col = *ind;
          }
        }
      }

      return std::make_pair(min_row, min_col);
    }

    //--------------------------------------------------------------------------------
    // NORMALIZATION
    //--------------------------------------------------------------------------------
    /**
     * Normalize given row such that the sum of the row after normalization is val.
     * For sparse matrices, a single pass of normalization might introduce new zeros,
     * causing the sum after that pass of normalization to be != val. If needed,
     * exact can be set to true, resulting in two passes of normalization instead
     * of a single one.
     *
     * @param row [0 <= size_type < nrows] the row to normalize
     * @param val [value_type != 0 (1)] the value to normalize to, default is 1
     * @param exact [bool (false)] whether to normalize twice or not
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows (assert)
     *  @li If val == 0 (assert)
     *
     * TODO expose perturbation?
     */
    inline
    value_type normalizeRow(size_type row, const value_type& val =1.0, bool exact =false)
    {
      { // Pre-conditions
        assert_valid_row_(row, "normalizeRow");
        assert_not_zero_value_(val, "normalizeRow");
      } // End pre-conditions

      value_type sum = rowSum(row);

      if (isZero_(sum))
        return sum;

      elementRowNZApply(row, nta::MultipliesByVal<value_type>(val / sum));

      if (exact)
        normalizeRow(row, val, false);

      return sum;
    }

    //--------------------------------------------------------------------------------
    /**
     * Normalize given col such that the sum of the col after normalization is val.
     * For sparse matrices, a single pass of normalization might introduce new zeros,
     * causing the sum after that pass of normalization to be != val. If needed,
     * exact can be set to true, resulting in two passes of normalization instead
     * of a single one.
     *
     * @param col [0 <= size_type < ncols] the col to normalize
     * @param val [value_type != 0 (=1)] the value to normalize to, default is 1
     * @param exact [bool (false)] whether to normalize twice or not
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols (assert)
     *  @li If val == 0 (assert)
     *
     * TODO expose perturbation?
     */
    inline
    value_type normalizeCol(size_type col, const value_type& val =1.0, bool exact =false)
    {
      { // Pre-conditions
        assert_valid_col_(col, "normalizeCol");
        assert_not_zero_value_(val, "normalizeCol");
      } // End pre-conditions

      value_type sum = colSum(col);

      if (isZero_(sum))
        return sum;

      elementColNZApply(col, nta::MultipliesByVal<value_type>(val / sum));

      if (exact)
        normalizeCol(col, val, false);

      return sum;
    }

    //--------------------------------------------------------------------------------
    /**
     * Normalizes all the rows of this SparseMatrix.
     * There is an issue when normalizing sparse matrices where the result after
     * normalization could not equal 1, because some values disappear below
     * the threshold used to determine whether a number is a zero or not.
     *
     * @param val [value_type != 0 (=1)] the value to use in the normalization
     * @param exact [bool (false)]: whether to make the rows exactly sum to val
     *  after normalization or not
     *
     * @b Exceptions:
     *  @li None
     */
    inline void normalizeRows(const value_type& val =1.0, bool exact =false)
    {
      { // Pre-conditions
        assert_not_zero_value_(val, "normalizeRows");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS
        normalizeRow(row, val, exact);
    }

    //--------------------------------------------------------------------------------
    /**
     * Normalizes all the columns of this SparseMatrix.
     * There is an issue when normalizing sparse matrices where the result after
     * normalization could not equal 1, because some values disappear below
     * the threshold used to determine whether a number is a zero or not.
     *
     * @param val [value_type != 0] the value that should be used in the normalization
     * @param exact [bool (false)]: whether to make the rows exactly sum to val
     *  after normalization or not
     *
     * @b Exceptions:
     *  @li None
     */
    inline void normalizeCols(const value_type& val =1.0, bool exact =false)
    {
      { // Pre-conditions
        assert_not_zero_value_(val, "normalizeCols");
      } // End pre-conditions

      const size_type ncols = nCols();

      colSums(nzb_);

      value_type *nz = nzb_, *nz_end = nzb_ + ncols;
      while (nz != nz_end) {
        value_type& col_sum = *nz;
        if (!isZero_(col_sum))
          col_sum = val / col_sum;
        else
          col_sum = (value_type) 1;
        ++nz;
      }

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          *nz *= nzb_[*ind];
        }
        thresholdRow(row, nta::Epsilon);
      }

      if (exact)
        normalizeCols(val, false);
    }

    //--------------------------------------------------------------------------------
    /**
     * Normalize whole matrix such that the sum of all the elements after normalization
     * sums to val.
     * For sparse matrices, a single pass of normalization might introduce new zeros,
     * causing the sum after that pass of normalization to be != val. If needed,
     * exact can be set to true, resulting in two passes of normalization instead
     * of a single one.
     *
     * @param val [value_type != 0 (1)] the value to normalize to, default is 1
     * @param exact [bool (false)] whether to normalize twice or not
     *
     * @b Exceptions:
     *  @li If val == 0 (assert)
     *
     * TODO expose perturbation?
     */
    inline void normalize(const value_type& val =1.0, bool exact =false)
    {
      { // Pre-conditions
        assert_not_zero_value_(val, "normalize");
      } // End pre-conditions

      value_type k = val / sum();

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          *nz *= k;
        }
        thresholdRow(row, nta::Epsilon);
      }

      if (exact)
        normalize(val, false);
    }

    //--------------------------------------------------------------------------------
    /**
     * Normalize so that the max is val.
     */
    inline void normalize_max(const value_type& val =1.0)
    {
      { // Pre-conditions
        assert_not_zero_value_(val, "normalize");
      } // end PRE-conditions

      value_type max_val = std::numeric_limits<value_type>::max();

      {
        ITERATE_ON_ALL_ROWS {
          ITERATE_ON_ROW {
            if (*nz > max_val) {
              max_val = *nz;
            }
          }
        }
      }

      value_type k = val / max_val;

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          *nz *= k;
        }
        thresholdRow(row, nta::Epsilon);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Normalize block by defined by outer product of range.
     * If the range is [0,3,5], then the block is defined by [0,3,5] X [0,3,5],
     * and only the intersection of those rows and columns will participate in the
     * normalization.
     * This implementation uses a linear scan of the rows.
     */
    template <typename InputIterator>
    inline void
    normalizeBlockByRows(InputIterator begin, InputIterator end,
                         const value_type& val=-1.0, const value_type& eps_n =1e-6)
    {
      { // Pre-conditions
        assert_valid_sorted_index_range_(nRows(), begin, end, "normalizeBlockByRows");
        assert_not_zero_value_(val, "normalizeBlockByRows");
      } // End pre-conditions

      using namespace std;

      vector<value_type*> nz_ptrs(nCols());

      for (InputIterator i = begin; i != end; ++i) {
        size_type row = *i;
        size_type *ind = ind_begin_(row);
        size_type *ind_end = ind_end_(row);
        value_type *nz = nz_begin_(row);
        InputIterator j = begin;
        value_type s = 0;
        size_type k = 0;
        while (j != end && ind != ind_end) {
          size_type col = *j;
          if (col == *ind) {
            s += *nz;
            nz_ptrs[k++] = nz;
            ++ind; ++nz; ++j;
          } else if (col < *ind) {
            s += eps_n;
            ++j;
          } else if (*ind < col) {
            ++ind; ++nz;
          }
        }
        s += size_type(end - j) * eps_n;
        if (val > 0)
          s /= val;
        for (size_type i = 0; i != k; ++i)
          *(nz_ptrs[i]) /= s;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Normalize block by defined by outer product of range.
     * If the range is [0,3,5], then the block is defined by [0,3,5] X [0,3,5],
     * and only the intersection of those rows and columns will participate in the
     * normalization.
     * This implementation uses a binary search on the rows.
     */
    template <typename InputIterator>
    inline void
    normalizeBlockByRows_binary(InputIterator begin, InputIterator end,
                                const value_type& val=-1.0, const value_type& eps_n =1e-6)
    {
      { // Pre-conditions
        assert_valid_sorted_index_range_(nRows(), begin, end,
                                         "normalizeBlockByRows_binary");
        assert_not_zero_value_(val, "normalizeBlockByRows_binary");
      } // End pre-conditions

      using namespace std;

      vector<value_type*> nz_ptrs(nCols());

      for (InputIterator i = begin; i != end; ++i) {
        size_type row = *i;
        size_type *ind_begin = ind_begin_(row);
        size_type *ind_end = ind_end_(row);
        size_type *p = ind_begin;
        value_type *nz_begin = nz_begin_(row);
        value_type s = 0;
        size_type k = 0;
        for (InputIterator j = begin; j != end; ++j) {
          p = std::lower_bound(p, ind_end, *j);
          value_type *ptr = nz_begin + (p - ind_begin);
          if (p != ind_end && *p == *j) {
            s += *ptr;
            nz_ptrs[k++] = ptr;
          } else {
            s += eps_n;
          }
        }
        if (val > 0)
          s /= val;
        for (size_type i = 0; i != k; ++i)
          *(nz_ptrs[i]) /= s;
      }
    }

    //--------------------------------------------------------------------------------
    // SCALING
    //--------------------------------------------------------------------------------

    /**
     * Scales each row by the corresponding element of a vector.
     */
    template <typename InIter>
    inline void scaleRows(InIter s_begin)
    {
      { // Pre-conditions
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        value_type val = *s_begin;
        if (isZero_(val)) {
          nnzr_[row] = 0;
        } else {
          ITERATE_ON_ROW
            *nz *= val;
        }
        ++s_begin;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Scales each column by the corresponding element of a vector.
     */
    template <typename InIter>
    inline void scaleCols(InIter s_begin)
    {
      { // Pre-conditions
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW
          *nz *= s_begin[*ind];
      }
    }

    //--------------------------------------------------------------------------------
    // SUMS AND PRODS
    //--------------------------------------------------------------------------------

    /**
     * Computes the sum of the non-zeros for a given row:
     *
     *  result = sum(this[row,col], for col in [0,ncols))
     *
     * @param row [0 <= size_type < nrows] the index of the row to sum
     * @param [value_type] the sum of the row
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows.
     */
    inline value_type rowSum(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "rowSum");
      } // End pre-conditions

      if (isRowZero(row))
        return value_type(0);
      else
        return accumulateRowNZ(row, std::plus<value_type>(), (value_type)0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the sum of each row in the SparseMatrix:
     *
     *  sums[row] = sum(this[row,col], for col in [0,ncols))
     *
     * where:
     *  row in [0,nrows)
     *
     * @param sums [OutputIterator] iterator to storage for the sum of each row
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator>
    inline void rowSums(OutputIterator sums, value_type init =0) const
    {
      accumulateAllRowsNZ(sums, std::plus<value_type>(), (value_type)init);
    }

    //--------------------------------------------------------------------------------
    inline void rowSums(std::vector<value_type>& sums) const
    {
      { // Pre-conditions
        NTA_ASSERT(sums.size() == nRows())
          << "rowSums: Wrong size for vector";
      } // End pre-conditions

      rowSums(sums.begin());
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of the non-zeros for a given row:
     *
     *  result = prod(this[row,col], for col in [0,ncols) s.t. this[row,col] != 0)
     *
     * @param row [0 <= size_type < nrows] the index of the row to multiply
     * @param [value_type] the product of the row
     *
     * @b Exceptions:
     *  @li If row < 0 || row >= nrows.
     */
    inline value_type rowProd(size_type row) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "rowProd");
      } // End pre-conditions

      if (isRowZero(row))
        return value_type(0);
      else
        return accumulateRowNZ(row, std::multiplies<value_type>(), (value_type)1);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the prod of each row in the SparseMatrix:
     *
     *  prods[row] = prod(this[row,col], for col in [0,ncols), s.t. this[row,col] != 0)
     *
     * where:
     *  row in [0,nrows)
     *
     * @param prods [OutputIterator] iterator to storage for the prod of each row
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator>
    inline void rowProds(OutputIterator prods) const
    {
      ITERATE_ON_ALL_ROWS {
        *prods = rowProd(row);
        ++prods;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the sum of the non-zeros for a given column:
     *
     *  result = sum(this[row,col], for row in [0,nrows))
     *
     * @param col [0 <= size_type < ncols] the index of the column to sum
     * @param [value_type] the sum of the column
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols.
     */
    inline value_type colSum(size_type col) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "colSum");
      } // End pre-conditions

      return accumulateColNZ(col, std::plus<value_type>(), (value_type)0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the sum of each column in the SparseMatrix:
     *
     *  sums[col] = sum(this[row,col], for row in [0,nrows))
     *
     * where:
     *  col in [0,ncols)
     *
     * @param sums [OutputIterator] iterator to storage for the sum of each column
     *
     * @b Exceptions:
     *  @li None.
     */
    template <typename OutputIterator>
    inline void colSums(OutputIterator sums, value_type init =0) const
    {
      accumulateAllColsNZ(sums, std::plus<value_type>(), (value_type)init);
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds several rows. Which rows to add is specified by a sparse binary vector.
     */
    template <typename InIt, typename OutIt>
    inline void addRows(InIt indicator, InIt indicator_end,
                        OutIt result, OutIt result_end) const
    {
      {
        NTA_ASSERT((size_type)(indicator_end - indicator) == nRows());
        NTA_ASSERT(nCols() <= (size_type)(result_end - result));
      }

      std::fill(result, result + nCols(), (value_type) 0);

      for (size_type r = 0; indicator != indicator_end; ++indicator, ++r) {

        if (! *indicator)
          continue;

        size_type *ind = ind_[r], *ind_end = ind + nnzr_[r];
        value_type *nz = nz_[r];

        for (; ind != ind_end; ++ind, ++nz)
          result[*ind] += *nz;
      }
    }

    //--------------------------------------------------------------------------------
    template <typename InIt, typename OutIt>
    inline void addListOfRows(InIt whichRows, InIt whichRows_end,
                              OutIt result, OutIt result_end) const
    {
      {
        NTA_ASSERT(nCols() <= (size_type)(result_end - result));
      }

      std::fill(result, result + nCols(), (value_type) 0);

      for (; whichRows != whichRows_end; ++whichRows) {

        size_type r = *whichRows;
        size_type *ind = ind_[r], *ind_end = ind + nnzr_[r];
        value_type *nz = nz_[r];

        for (; ind != ind_end; ++ind, ++nz)
          result[*ind] += *nz;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of the non-zeros for a given column:
     *
     *  result = prod(this[row,col], for row in [0,nrows), s.t. this[row,col] != 0)
     *
     * @param row [size_type] the index of the column to multiply
     * @param [value_type] the product of the column
     *
     * @b Exceptions:
     *  @li If col < 0 || col >= ncols.
     */
    inline value_type colProd(size_type col) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "colProd");
      } // End pre-conditions

      if (isColZero(col))
        return value_type(0);
      else
        return accumulateColNZ(col, std::multiplies<value_type>(), (value_type)1);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the prod of each column in the SparseMatrix:
     *
     *  prods[col] = prod(this[row,col], for row in [0,nrows), s.t. this[row,col] != 0)
     *
     * where:
     *  col in [0,ncols)
     *
     * @param prods [OutputIterator] iterator to storage for the prod of each column
     *
     * @b Exceptions:
     *  @li None.
     *
     * TODO make faster
     */
    template <typename OutputIterator>
    inline void colProds(OutputIterator prods) const
    {
      OutputIterator prods_end = prods + nCols();
      size_type col = 0;
      while (prods != prods_end) {
        *prods = colProd(col);
        ++prods;
        ++col;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the sum of all the non-zeros in this matrix:
     *
     *  result = sum(this[row,col], for row,col in [0,nrows) X [0,ncols))
     *
     * @b Complexity:
     *  @li O(nnz)
     */
    inline value_type sum() const
    {
      return accumulateNZ(std::plus<value_type>(), (value_type)0);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of all the non-zeros in this matrix:
     *
     *  result = prod(this[row,col], for row,col in [0,nrows) X [0,ncols))
     *
     * @b Complexity:
     *  @li O(nnz)
     */
    inline value_type prod() const
    {
      if (isZero())
        return value_type(0);
      else
        return accumulateNZ(std::multiplies<value_type>(), value_type(1));
    }

    //--------------------------------------------------------------------------------
    // AXBY/LERP
    //--------------------------------------------------------------------------------

    /**
     * Computes axby between given row and vector x, with coefficients a and b:
     *
     *  for col in [0,ncols):
     *   this[row,col] = a * this[row,col] + b * x[col]
     *
     * This version does not look at the values of a and b to
     * optimize the number of operations.
     *
     * TODO optimize depending on a and b
     *
     * @param row [0 <= size_type < nrows] index of the row to operate on
     * @param a [value_type] coefficient that multiplies matrix row
     * @param b [value_type] coefficient that multiplies vector x
     * @param x [InputIterator<value_type>] input vector, a contiguous array in memory,
     *  like std::vector, not std::list
     *
     * @b Exceptions:
     *  @li row < 0 || row >= nrows (assert)
     *  @li Not enough memory (error)
     */
    template <typename InputIterator>
    inline void axby(size_type row, value_type a, value_type b, InputIterator x)
    {
      { // Pre-conditions
        assert_valid_row_(row, "axby");
      } // End pre-conditions

      size_type nnzr = nnzr_[row], *ind = ind_[row], ncols = nCols();
      size_type *end1 = ind + 4*(nnzr/4), *end2 = ind + nnzr;
      value_type *nz = nzb_;
      InputIterator end_x1 = x + 4*(ncols/4), end_x2 = x + ncols;

      if (a == 1.0 && b == 1.0) {

        for (; x != end_x1; x += 4, nz += 4) {
          *nz = *x; *(nz+1) = *(x+1);
          *(nz+2) = *(x+2); *(nz+3) = *(x+3);
        }

        while (x != end_x2)
          *nz++ = *x++;

        nz = nz_[row];

        for (; ind != end1; ind += 4, nz += 4) {
          nzb_[*ind] += *nz; nzb_[*(ind+1)] += *(nz+1);
          nzb_[*(ind+2)] += *(nz+2); nzb_[*(ind+3)] += *(nz+3);
        }

        while (ind != end2)
          nzb_[*ind++] += *nz++;

      } else if (a == 1.0 && b == -1.0) {

        for (; x != end_x1; x += 4, nz += 4) {
          *nz = *x; *(nz+1) = *(x+1);
          *(nz+2) = *(x+2); *(nz+3) = *(x+3);
        }

        while (x != end_x2)
          *nz++ = *x++;

        nz = nz_[row];

        for (; ind != end1; ind += 4, nz += 4) {
          nzb_[*ind] -= *nz; nzb_[*(ind+1)] -= *(nz+1);
          nzb_[*(ind+2)] -= *(nz+2); nzb_[*(ind+3)] -= *(nz+3);
        }

        while (ind != end2)
          nzb_[*ind++] -= *nz++;

      } else {

        // Doing this first allows us to "initialize" nzb_
        // to receive additions for the non-zeros later
        for (; x != end_x1; x += 4, nz += 4) {
          *nz = b * *x; *(nz+1) = b * *(x+1);
          *(nz+2) = b * *(x+2); *(nz+3) = b * *(x+3);
        }

        while (x != end_x2)
          *nz++ = b * *x++;

        // We switch over to pointing to the non-zeros
        // (we were pointing in nzb_!)
        nz = nz_[row];

        for (; ind != end1; ind += 4, nz += 4) {
          nzb_[*ind] += a * *nz; nzb_[*(ind+1)] += a * *(nz+1);
          nzb_[*(ind+2)] += a * *(nz+2); nzb_[*(ind+3)] += a * *(nz+3);
        }

        while (ind != end2)
          nzb_[*ind++] += a * *nz++;
      }

      set_row_(row, nzb_, nzb_ + nCols());
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes linear combination of each row and vector x, with coefficients a and b:
     *
     *  for row in [0,nrows):
     *   for col in [0,ncols):
     *    this[row,col] = a * this[row,col] + b * x[col]
     *
     *
     * @param a [value_type] coefficient that multiplies matrix row
     * @param b [value_type] coefficient that multiplies vector x
     * @param x [InputIterator<value_type>] input vector
     *
     * @b Exceptions:
     *  @li Not enough memory (error)
     */
    template <typename InputIterator>
    inline void axby(value_type a, value_type b, InputIterator x)
    {
      for (size_type i = 0; i != nRows(); ++i)
        axby(i, a, b, x);
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the linear interpolation of this sparse matrix and B,
     * with coefficients a and b respectively, in place:
     *
     *  for row in [0,nrows):
     *   for col in [0,ncols):
     *    this[row,col] = a * this[row,col] + b * B[row,col]
     *
     * @param a [value_type] a coefficient
     * @param b [value_type] b coefficient
     * @param B [const SparseMatrix<size_type, value_type>] B matrix
     *
     * TODO: add flag so B can be transposed?
     *
     * @b Exceptions
     *  @li If this matrix and B don't have the same number of rows.
     *  @li If this matrix and B don't have the same number of columns.
     */
    inline void lerp(value_type a, value_type b, const SparseMatrix& B)
    {
      { // Pre-conditions
        NTA_ASSERT(B.nRows() == this->nRows())
          << "SparseMatrix::lerp(): "
          << " B matrix has " << B.nRows() << " rows"
          << " when this matrix has " << this->nRows() << " rows"
          << " - Both matrices need to have the same number of rows";

        NTA_ASSERT(B.nCols() == this->nCols())
          << "SparseMatrix::lerp(): "
          << " B matrix has " << B.nCols() << " columns"
          << " when this matrix has " << this->nCols() << " columns"
          << " - Both matrices need to have the same number of columns";
      } // End pre-conditions

      const size_type nrows = nRows();
      const size_type ncols = nCols();

      for (size_type i = 0; i != nrows; ++i) {

        std::fill(nzb_, nzb_ + ncols, (value_type)0);

        size_type *ind = ind_[i];
        value_type *nz = nz_[i], *nz_end = nz + nnzr_[i];

        if (a != 0)
          while (nz != nz_end)
            nzb_[*ind++] = a * *nz++;

        ind = B.ind_[i];
        nz = B.nz_[i];
        nz_end = nz + B.nnzr_[i];

        if (b != 0)
          while (nz != nz_end)
            nzb_[*ind++] += b * *nz++;

        set_row_(i, nzb_, nzb_ + nCols());
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds two rows of a matrix together. The first argument is the source row,
     * and the second is the destination row:
     *
     *  for col in [0,ncols):
     *   this[dst_row,col] += this[src_row,col]
     *
     * @param src_row [0 <= size_type < nrows] index of the source row
     * @param dst_row [0 <= size_type < nrows] index of the destination row
     *
     * @b Complexity:
     *  @li O(nnzr)
     *
     * @b Exceptions:
     *  @li if src_row < 0 || src_row > nrows (assert)
     *  @li if dst_row < 0 || dst_row > nrows (assert)
     */
    void addTwoRows(size_type src_row, size_type dst_row)
    {
      { // Pre-conditions
        assert_valid_row_(src_row, "addTwoRows");
        assert_valid_row_(dst_row, "addTwoRows");
      } // End pre-conditions

      if (isRowZero(src_row))
        return;

      size_type *ind_src = ind_begin_(src_row);
      size_type *ind_dst = ind_begin_(dst_row);
      size_type *ind_src_end = ind_end_(src_row);
      size_type *ind_dst_end = ind_end_(dst_row);

      value_type *nz_src = nz_begin_(src_row);
      value_type *nz_dst = nz_begin_(dst_row);

      size_type k = 0;

      while (ind_src != ind_src_end && ind_dst != ind_dst_end) {
        size_type i_src = *ind_src, i_dst = *ind_dst;
        if (i_src == i_dst) {
          value_type val = *nz_src + *nz_dst;
          if (!isZero_(val)) {
            indb_[k] = i_src;
            nzb_[k] = val;
            ++k;
          }
          ++ind_src; ++ind_dst;
          ++nz_src; ++nz_dst;
        } else if (i_src < i_dst) {
          indb_[k] = i_src;
          nzb_[k] = *nz_src;
          ++ind_src; ++nz_src;
          ++k;
        } else {
          indb_[k] = i_dst;
          nzb_[k] = *nz_dst;
          ++ind_dst; ++nz_dst;
          ++k;
        }
      }

      size_type *ind = NULL, *ind_end = ind;
      value_type *nz = NULL;

      if (ind_src == ind_src_end) {
        ind = ind_dst;
        ind_end = ind_dst_end;
        nz = nz_dst;
      } else {
        ind = ind_src;
        ind_end = ind_src_end;
        nz = nz_src;
      }

      while (ind != ind_end) {
        indb_[k] = *ind;
        nzb_[k] = *nz;
        ++ind; ++nz;
        ++k;
      }

      if (isCompact())
        decompact();

      delete [] ind_[dst_row];
      delete [] nz_[dst_row];

      nnzr_[dst_row] = k;
      ind_[dst_row] = new size_type [nnzr_[dst_row]];
      nz_[dst_row] = new value_type [nnzr_[dst_row]];
      std::copy(indb_, indb_ + nnzr_[dst_row], ind_[dst_row]);
      std::copy(nzb_, nzb_ + nnzr_[dst_row], nz_[dst_row]);
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds two cols of a matrix together. The first argument is the source col,
     * and the second is the destination col:
     *
     *  for row in [0,nrows):
     *   this[row,dst_col] += this[row,src_col]
     *
     * @param src_col [0 <= size_type < ncols] index of the source col
     * @param dst_col [0 <= size_type < ncols] index of the destination col
     *
     * @b Complexity:
     *  @li O(nnzr)
     *
     * @b Exceptions:
     *  @li if src_col < 0 || src_col > ncols (assert)
     *  @li if dst_col < 0 || dst_col > ncols (assert)
     */
    void addTwoCols(size_type src_col, size_type dst_col)
    {
      { // Pre-conditions
        assert_valid_col_(src_col, "addTwoCols");
        assert_valid_col_(dst_col, "addTwoCols");
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {

        size_type *ind_begin = ind_begin_(row), *ind_end = ind_end_(row);
        size_type *p_src = std::lower_bound(ind_begin, ind_end, src_col);

        if (p_src != ind_end && *p_src == src_col) {

          size_type *p_dst = dst_col > src_col ?
            std::lower_bound(p_src, ind_end, dst_col) :
            std::lower_bound(ind_begin, p_src, dst_col);

          if (*p_dst != dst_col) {
            insertNewNonZero_(row, dst_col, p_dst, nz_[row][p_src - ind_begin]);
          } else {
            value_type* nz = nz_[row];
            nz[p_dst - ind_begin] += nz[p_src - ind_begin];
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    // ADD
    //--------------------------------------------------------------------------------
    /**
     * Adds one SparseMatrix to another.
     */
    inline void add(const SparseMatrix& other)
    {
      { // Pre-conditions
        NTA_ASSERT(other.nRows() == nRows())
          << "add: Wrong number of rows: " << other.nRows()
          << " and " << nRows();
        NTA_ASSERT(other.nCols() == nCols())
          << "add: Wrong number of columns: " << other.nCols()
          << " and " << nCols();
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {

        size_type *ind = ind_begin_(row);
        size_type *ind_end = ind_end_(row);
        value_type *nz = nz_begin_(row);
        size_type *ind_b = other.ind_begin_(row);
        size_type *ind_b_end = other.ind_end_(row);
        value_type *nz_b = other.nz_begin_(row);
        size_type *indb = indb_;
        value_type *nzb = nzb_;

        while (ind != ind_end && ind_b != ind_b_end) {
          if (*ind == *ind_b) {
            value_type val = *nz++ + *nz_b++;
            if (!isZero_(val)) {
              *indb++ = *ind;
              *nzb++ = val;
            }
            ++ind; ++ind_b;
          } else if (*ind < *ind_b) {
            *indb++ = *ind++;
            *nzb++ = *nz++;
          } else if (*ind_b < *ind) {
            *indb++ = *ind_b++;
            *nzb++ = *nz_b++;
          }
        }

        while (ind != ind_end) {
          *indb++ = *ind++;
          *nzb++ = *nz++;
        }

        while (ind_b != ind_b_end) {
          *indb++ = *ind_b++;
          *nzb++ = *nz_b++;
        }

        size_type nnzr = (size_type)(indb - indb_);

        if (nnzr > nnzr_[row]) {
          decompact();
          delete [] ind_[row];
          delete [] nz_[row];
          ind_[row] = new size_type [nnzr];
          nz_[row] = new value_type [nnzr];
        }

        std::copy(indb_, indb_ + nnzr, ind_[row]);
        std::copy(nzb_, nzb_ + nnzr, nz_[row]);
        nnzr_[row] = nnzr;
      }
    }

    //--------------------------------------------------------------------------------
    // MULTIPLY
    //--------------------------------------------------------------------------------

    /**
     * Multiplies this sparse matrix by B and puts the result into C.
     * Multiplication occurs on the right of this SparseMatrix.
     * B's number of rows needs to be the same as A's number of columns.
     * C will have this->nrows rows and B.ncols columns.
     *
     *  for row,col in [0,A.nrows) X [0,B.ncols):
     *   C[row,col] = sum(A[row,k] * B[k,col], for k in [0,A.ncols))
     *
     * @param B [SparseMatrix] the matrix to multiply by this one
     * @param C [SparseMatrix] the result of the multiplication
     *
     * @b Exceptions:
     *  @li If this->ncols != B.nrows
     */
    inline void multiply(const SparseMatrix& B, SparseMatrix& C) const
    {
      { // Pre-conditions
        NTA_ASSERT(nCols() == B.nRows())
          << "SparseMatrix::multiply(): "
          << "A matrix's number of columns (" << nCols() << ") "
          << "should be the same as B matrix's number of rows ("
          << B.nRows() << ")";
      } // End pre-conditions

      C.resize(nRows(), B.nCols());

      size_type nrowsB = B.nRows();
      size_type nrowsC = C.nRows();
      size_type ncolsC = C.nCols();

      std::vector<size_type> front;
      front.resize(nrowsB);

      for (size_type iC = 0; iC < nrowsC; ++iC) {

        size_type nnzrA = nnzr_[iC];
        size_type *indA = ind_[iC];
        value_type *nzA = nz_[iC];

        std::fill(front.begin(), front.end(), (size_type)0);
        std::fill(C.nzb_, C.nzb_ + ncolsC, (value_type)0);

        for (size_type jC = 0; jC != ncolsC; ++jC) {
          for (size_type kA = 0; kA != nnzrA; ++kA) {

            size_type k = indA[kA];
            size_type nnzrB = B.nnzr_[k];
            size_type *indB = B.ind_[k];
            value_type *nzB = B.nz_[k];

            if (nnzrB > 0) {

              size_type kB = front[k];
              for (; kB != nnzrB && indB[kB] < jC; ++kB);

              if (kB < nnzrB && indB[kB] == jC) {
                C.nzb_[jC] += nzA[kA] * nzB[kB];
                front[k] = kB;
              }
            }
          }
        }

        C.set_row_(iC, C.nzb_, C.nzb_ + C.nCols());
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Element by element multiplication of two sparse matrices, in place.
     */
    inline void elementMultiply(const SparseMatrix& b)
    {
      { // Pre-conditions
        NTA_ASSERT(b.nRows() == nRows())
          << "elementMultiply needs same number of rows in both matrices";
        NTA_ASSERT(b.nCols() == nCols())
          << "elementMultiply needs same number of columns in both matrices";
      } // End pre-conditions

      ITERATE_ON_ALL_ROWS {
        if (nNonZerosOnRow(row) == 0 || b.nNonZerosOnRow(row) == 0)
          nnzr_[row] = 0;
        else {
          size_type *ind_a = ind_begin_(row);
          size_type *ind_a_end = ind_end_(row);
          size_type *ind_a_2 = ind_a;
          value_type *nz_a = nz_begin_(row);
          value_type *nz_a_2 = nz_a;
          size_type *ind_b = b.ind_begin_(row);
          size_type *ind_b_end = b.ind_end_(row);
          value_type *nz_b = b.nz_begin_(row);
          while (ind_a != ind_a_end && ind_b != ind_b_end) {
            if (*ind_a == *ind_b) {
              value_type val = *nz_a * *nz_b;
              if (!isZero_(val)) {
                *ind_a_2++ = *ind_a;
                *nz_a_2++ = val;
              }
              ++ind_a; ++nz_a;
              ++ind_b; ++nz_b;
            } else if (*ind_a < *ind_b) {
              ++ind_a; ++nz_a;
            } else if (*ind_b < *ind_a) {
              ++ind_b; ++nz_b;
            }
          }
          nnzr_[row] = (size_type)(ind_a_2 - ind_begin_(row));
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Element by element multiplication of two matrices, but not in place.
     */
    inline void elementMultiply(const SparseMatrix& m, SparseMatrix& result) const
    {
      { // Pre-conditions
        NTA_ASSERT(m.nRows() == nRows())
          << "elementMultiply needs same number of rows in both matrices";
        NTA_ASSERT(m.nCols() == nCols())
          << "elementMultiply needs same number of columns in both matrices";
      } // End pre-conditions

      result.resize(nRows(), nCols());
      result.setToZero();

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          size_type col = *ind;
          result.set(row, col, *nz * m.get(row,col));
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Element by element multiplication of two sparse matrices, in place.
     */
    inline void elementMultiply(value_type* dense)
    {
      ITERATE_ON_ALL_ROWS {
        size_type offset = 0;
        ITERATE_ON_ROW {
          size_type col = *ind;
          value_type val = *nz * *(dense + row * nCols() + col);
          if (isZero_(val)) {
            ++offset;
          } else {
            *(nz - offset) = val;
            *(ind - offset) = col;
          }
        }
        nnzr_[row] -= offset;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Element by element multiplication of two sparse matrices, not in place.
     */
    inline void elementMultiply(value_type* dense, SparseMatrix& result) const
    {
      result.resize(nRows(), nCols());
      result.setToZero();

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          size_type col = *ind;
          result.set(row, col, *nz * *(dense + row * nCols() + col));
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     *  for row,col in [0,A.nrows) X [0,B.ncols):
     *   C[row,col] = sum(A[row,k] * B[k,col], for k in [0,A.ncols))
     *
     * @b Complexity:
     *  @li O(B.ncols * nnz)
     */
    template <typename Dense>
    inline void rightDenseMatProd(const Dense& B, Dense& C) const
    {
      typedef typename Dense::size_type size_type2;

      ITERATE_ON_ALL_ROWS {
        for (size_type2 col = 0 ; col != B.nCols(); ++col) {
          value_type val = 0;
          ITERATE_ON_ROW
            val += *nz * B.get(*ind,col);
          C.set(row,col,val);
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     *  for row,col in [0,A.nrows) X [0,B.ncols):
     *   C[row,col] = sum(A[row,k] * B[k,col], for k in [0,A.ncols))
     *
     * @b Complexity:
     *  @li O(B.ncols * nnz)
     */
    template <typename Dense>
    inline void rightDenseMatProdAtNZ(const Dense& B, Dense& C) const
    {
      typedef typename Dense::size_type size_type2;

      ITERATE_ON_ALL_ROWS {
        for (size_type2 col = 0 ; col != B.nCols(); ++col) {
          value_type val = 0;
          size_type *ind = ind_begin_(row), *ind_end = ind_end_(row);
          for (; ind != ind_end; ++ind)
            val += B.get(*ind,col);
          C.set(row,col,val);
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     */
    template <typename Dense>
    inline void denseMatExtract(const Dense& B, Dense& C) const
    {
      typedef typename Dense::size_type size_type2;

      ITERATE_ON_ALL_ROWS {
        for (size_type2 col = 0 ; col != B.nCols(); ++col) {
          if (nNonZerosOnRow(row) == 1)
            C.set(row,col,B.get(*(ind_[row]),col));
          else
            C.set(row,col,0);
        }
      }
    }

    //--------------------------------------------------------------------------------
    // MATRIX VECTOR PRODUCTS
    //--------------------------------------------------------------------------------

    //--------------------------------------------------------------------------------
    /**
     * Computes the dot product of a single row of this SparseMatrix by vector x
     * and puts the result (a scalar) in y.
     *
     *  y = sum(this[row,col] * x[col], for col in [0,ncols))
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] result (scalar)
     *
     * @b Exceptions:
     *  @li If row is not a valid row index.
     */
    template <typename InputIterator>
    inline value_type rightVecProd(size_type row, InputIterator x) const
    {
      { // Pre-conditions
        assert_valid_row_(row, "rightVecProd for single row");
      } // End pre-conditions

      const size_type nnzr = nnzr_[row];

      if (nnzr == 0)
        return 0;

      value_type a, b, val = 0;
      size_type *ind = ind_begin_(row);
      size_type *end1 = ind + 4*(nnzr/4), *end2 = ind_end_(row);
      value_type *nz = nz_begin_(row);

      while (ind != end1) {
        a = *nz++ * x[*ind++];
        b = *nz++ * x[*ind++];
        val += a + b;
        a = *nz++ * x[*ind++];
        b = *nz++ * x[*ind++];
        val += a + b;
      }

      while (ind != end2)
        val += *nz++ * x[*ind++];

      return val;
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the standard product of vector x by this SparseMatrix on the right
     * side and puts the result in vector y:
     *
     *  for row in [0,nrows):
     *   y[row] = sum(this[row,col] * x[col], for col in [0,ncols))
     *
     * x and y need to be iterators to contiguous arrays in memory
     * (like std::vector, not like std::list).
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] result (size = number of rows)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void rightVecProd(InputIterator x, OutputIterator y) const
    {
      ITERATE_ON_ALL_ROWS {
        *y = rightVecProd(row, x);
        ++y;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the standard product of vector x by this SparseMatrix on the right
     * side and puts the result in vector y:
     *
     *  for row in set of rows:
     *   y[row] = sum(this[row,col] * x[col], for col in [0,ncols))
     *
     * x and y need to be iterators to contiguous arrays in memory
     * (like std::vector, not like std::list).
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] result (size = number of rows)
     *
     * @b Exceptions:
     *  @li If a row index in the range is not a valid row index.
     */
    template <typename InputIterator, typename InputIterator2, typename OutputIterator>
    inline void rightVecProd(InputIterator2 begin, InputIterator2 end,
                             InputIterator x, OutputIterator y) const
    {
      { // Pre-conditions
        assert_valid_row_it_range_(begin, end, "rightVecProd for several rows");
      } // End pre-conditions

      for (InputIterator2 i = begin; i != end; ++i, ++y)
        *y = rightVecProd(*i, x);
    }

    //--------------------------------------------------------------------------------
    /**
     * Dot product of the given row and the passed in vector. This takes an STL
     * std::vector directly, providing nicer syntax in later algorithm, but it doesn't
     * do anything special beyond computing a dot product.
     */
    inline value_type
    rightVecProd(size_type row, const std::vector<value_type>& x) const
    {
      return rightVecProd(row, x.begin());
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the standard product of vector x by this SparseMatrix on the right
     * side and puts the result in vector y:
     *
     *  for row in [0,nrows):
     *   y[row] = sum(this[row,col] * x[col], for col in [0,ncols))
     *
     * Can't reuse the exact name 'rightvecprod' because of name collision!
     */
    inline void rightVecProd(const std::vector<value_type>& x,
                             std::vector<value_type>& y) const
    {
      if (y.size() < nRows())
        y.resize(nRows());

      rightVecProd(x.begin(), y.begin());
    }

    //--------------------------------------------------------------------------------
    /**
     * "Block" right vec prod: produces a matrix, whose values are the result of
     * multiplying each block of this sparse matrix by a subset of vector x. This
     * is in effect treating this matrix as if it were a collection of smaller
     * matrices, corresponding to the blocks.
     *
     * The block size needs to be in (0,ncols]. In particular, it cannot be 0.
     * The block size also needs to be a divisor of the number of columns.
     *
     *  for row in [0,nrows):
     *   for block in [0,ncols/block_size):
     *    block_begin = block * block_size
     *    block_end = block_begin + block_size
     *    y[row,block] = sum(this[row,col] * x[col], for col in [block_begin, block_end))
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] result (size = number of rows X number
     *  of blocks)
     *
     * @b Exceptions:
     *  @li If block_size <= 0 or block_size > ncols.
     *  @li If ncols % block_size != 0.
     */
    template <typename InputIterator>
    inline void
    blockRightVecProd(size_type block_size, InputIterator x, SparseMatrix& C) const
    {
      {
        NTA_ASSERT(0 < block_size && block_size <= nCols())
          << "blockRightVecProd: Invalid block size: " << block_size
          << " - Needs to be > 0 and <= nCols = " << nCols();
        NTA_ASSERT(nCols() % block_size == 0)
          << "blockRightVecProd: Invalid block size: " << block_size
          << " - Needs to be a divisor of nCols = " << nCols();
      }

      const size_type nrows = nRows();

      C.resize(nRows(), nCols() / block_size);

      for (size_type i = 0; i != nrows; ++i) {

        size_type *ind = ind_begin_(i);
        value_type *nz = nz_begin_(i);
        size_type block_end = block_size;
        size_type end = nCols() + block_end;
        size_type block_idx = 0;

        while (block_end != end) {
          value_type val = 0;
          while (*ind < block_end)
            val += *nz++ * x[*ind++];
          block_end += block_size;
          C.set(i, block_idx++, val);
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the standard product of vector x by a column of this SparseMatrix
     * and puts the result in y.
     *
     *   y[col] = sum(this[row,col] * x[row], for row in [0,nrows))
     *
     * x and y need to be iterators to contiguous arrays in memory
     * (like std::vector, not like std::list).
     *
     * Non-mutating, O()
     *
     * @param x [InputIterator<value_type>] input vector (size = number of rows)
     * @param y [OutputIterator<value_type>] result (scalard)
     *
     * @b Exceptions:
     *  @li If col is not a valid column index.
     */
    template <typename InputIterator>
    inline value_type leftVecProd(size_type col, InputIterator x) const
    {
      { // Pre-conditions
        assert_valid_col_(col, "leftVecProd for one col");
      } // End pre-conditions

      value_type y = 0;

      ITERATE_ON_ALL_ROWS {

        value_type x_val = x[row];

        if (isZero_(x_val) || nnzr_[row] == 0)
          continue;

        size_type *p = std::lower_bound(ind_begin_(row), ind_end_(row), col);

        if (p != ind_end_(row) && *p == col)
          y += *(nz_begin_(row) + (p - ind_begin_(row))) * x_val;
      }

      return y;
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the standard product of vector x by this SparseMatrix on the left
     * side and puts the result in vector y:
     *
     *  for col in [0,ncols):
     *   y[col] = sum(this[row,col] * x[row], for row in [0,nrows))
     *
     * x and y need to be iterators to contiguous arrays in memory
     * (like std::vector, not like std::list).
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of rows)
     * @param y [OutputIterator<value_type>] result (size = number of columns)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void leftVecProd(InputIterator x, OutputIterator y) const
    {
      std::fill(y, y + nCols(), (value_type) 0);

      ITERATE_ON_ALL_ROWS {

        value_type val = x[row];

        if (isZero_(val))
          continue;

        ITERATE_ON_ROW
          y[*ind] += *nz * val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the standard product of vector x by this SparseMatrix on the left
     * side and puts the result in vector, for some columns only:
     *
     *  for col in set of cols:
     *   y[col] = sum(this[row,col] * x[row], for row in [0,nrows))
     *
     * x and y need to be iterators to contiguous arrays in memory
     * (like std::vector, not like std::list).
     *
     * This version uses a linear scan of the rows.
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of rows)
     * @param y [OutputIterator<value_type>] result (size = number of columns)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename InputIterator2, typename OutputIterator>
    inline void leftVecProd(InputIterator2 begin, InputIterator2 end,
                            InputIterator x, OutputIterator y) const
    {
      { // Pre-conditions
        assert_valid_col_it_range_(begin, end, "leftVecProd");
      } // End pre-conditions

      size_type c = 0;
      for (InputIterator2 i = begin; i != end; ++i, ++c)
        indb_[*i] = c;
      std::fill(y, y + c, (value_type) 0);

      ITERATE_ON_ALL_ROWS {

        value_type val = x[row];
        size_type *ind = ind_begin_(row);
        size_type *ind_end = ind_end_(row);
        value_type *nz = nz_begin_(row);
        InputIterator2 j = begin;
        while (j != end && ind != ind_end) {
          size_type col = *j;
          if (col == *ind) {
            y[indb_[col]] += *nz * val;
            ++ind; ++nz; ++j;
          } else if (col < *ind) {
            ++j;
          } else if (*ind < col) {
            ++ind; ++nz;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the standard product of vector x by this SparseMatrix on the left
     * side and puts the result in vector y, for some columns only:
     *
     *  for col in set of cols:
     *   y[col] = sum(this[row,col] * x[row], for row in [0,nrows))
     *
     * x and y need to be iterators to contiguous arrays in memory
     * (like std::vector, not like std::list).
     *
     * This version uses a binary search for the columns.
     *
     * Non-mutating, O(nnz)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of rows)
     * @param y [OutputIterator<value_type>] result (size = number of columns)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename InputIterator2, typename OutputIterator>
    inline void leftVecProd_binary(InputIterator2 begin, InputIterator2 end,
                                   InputIterator x, OutputIterator y) const
    {
      { // Pre-conditions
        assert_valid_sorted_index_range_(nCols(), begin, end, "leftVecProd_binary");
      } // End pre-conditions

      size_type c = 0;
      for (InputIterator2 i = begin; i != end; ++i, ++c)
        indb_[*i] = c;
      std::fill(y, y + c, (value_type) 0);

      ITERATE_ON_ALL_ROWS {

        value_type val = x[row];
        size_type *ind_begin = ind_begin_(row);
        size_type *ind_end = ind_end_(row);
        size_type *p = ind_begin;
        value_type *nz_begin = nz_begin_(row);
        for (InputIterator2 j = begin; j != end; ++j) {
          size_type col = *j;
          p = std::lower_bound(p, ind_end, col);
          if (p != ind_end && *p == col)
            y[indb_[col]] += *(nz_begin + (p - ind_begin)) * val;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes dot product of given col and given x, where x is an instance
     * of STL's std::vector (useful in C++).
     */
    inline value_type
    leftVecProd(size_type col, const std::vector<value_type>& x) const
    {
      return leftVecProd(col, x.begin());
    }

    //--------------------------------------------------------------------------------
    /**
     * Left vec prod of x and this matrix, putting the result into y, where x and y
     * are instances of STL's std::vector (useful in C++).
     */
    inline void
    leftVecProd(const std::vector<value_type>& x, std::vector<value_type>& y) const
    {
      if (y.size() < nCols())
        y.resize(nCols());

      leftVecProd(x.begin(), y.begin());
    }

    //--------------------------------------------------------------------------------
    // AtNZ operations, i.e. treating the sparse matrix as a 0/1 binary
    // sparse matrix, never looking at the actual values of the non-zeros.
    //--------------------------------------------------------------------------------

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of the values in x corresponding to the non-zeros
     * of each row. Stores the result in y for each row. The operation is:
     *
     *  for row in [0,nrows):
     *   y[row] = prod(x[col], for col in [0,ncols) s.t. this[row,col] != 0)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] output vector (size = number of rows)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void rightVecProdAtNZ(InputIterator x, OutputIterator y) const
    {
      ITERATE_ON_ALL_ROWS {

        size_type nnzr = nnzr_[row];
        size_type *ind = ind_[row];
        size_type *end1 = ind + 4*(nnzr/4), *end2 = ind + nnzr;
        value_type val = 1.0;

        for (; ind != end1; ind += 4)
          val *= x[*ind] * x[*(ind+1)] * x[*(ind+2)] * x[*(ind+3)];

        while (ind != end2)
          val *= x[*ind++];

        *y++ = val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of the values in x corresponding to the non-zeros
     * of each col. Stores the result in y for each col. The operation is:
     *
     *  for col in [0,ncols):
     *   y[col] = prod(x[row], for row in [0,nrows) s.t. this[row,col] != 0)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of rows)
     * @param y [OutputIterator<value_type>] output vector (size = number of columns)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void leftVecProdAtNZ(InputIterator x, OutputIterator y) const
    {
      std::fill(y, y + nCols(), (value_type) 1.0);

      ITERATE_ON_ALL_ROWS {

        size_type *ind = ind_begin_(row), *ind_end = ind_end_(row);
        value_type val = x[row];

        while (ind != ind_end)
          y[*ind++] *= val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds the values of x corresponding to non-zeros, for each row.
     * The operation is:
     *
     *  for row in [0,nrows):
     *   y[row] = sum(x[col], for col in [0,ncols) s.t. this[row,col] != 0)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] output vector (size = number of rows)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void rightVecSumAtNZ(InputIterator x, OutputIterator y) const
    {
      ITERATE_ON_ALL_ROWS {

        size_type nnzr = nnzr_[row];
        size_type *ind = ind_[row];
        size_type *end1 = ind + 4*(nnzr/4), *end2 = ind + nnzr;
        value_type val = 0.0;

        for (; ind != end1; ind += 4)
          val += x[*ind] + x[*(ind+1)] + x[*(ind+2)] + x[*(ind+3)];

        while (ind != end2)
          val += x[*ind++];

        *y++ = val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Same as above, except that we add to the sum only if the value of the non-zero
     * is greater than the given threshold.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void rightVecSumAtNZGtThreshold(InputIterator x, OutputIterator y,
                                           value_type threshold) const
    {
      ITERATE_ON_ALL_ROWS {

        size_type nnzr = nnzr_[row];
        size_type *ind = ind_[row];
        value_type *nz = nz_[row];
        value_type val = 0.0;

        for (size_type i = 0; i != nnzr; ++i)
          if (nz[i] > threshold)
            val += x[ind[i]];

        *y++ = val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds the values of x corresponding to non-zeros, for each column.
     * The operation is:
     *
     *  for col in [0,ncols):
     *   y[col] = sum(x[row], for row in [0,nrows) s.t. this[row,col] != 0)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of rows)
     * @param y [OutputIterator<value_type>] output vector (size = number of columns)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void leftVecSumAtNZ(InputIterator x, OutputIterator y) const
    {
      std::fill(y, y + nCols(), (value_type) 0.0);

      ITERATE_ON_ALL_ROWS {

        size_type *ind = ind_begin_(row), *ind_end = ind_end_(row);
        value_type val = x[row];

        while (ind != ind_end)
          y[*ind++] += val;
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
      ITERATE_ON_ALL_ROWS {
        value_type max_val = - std::numeric_limits<value_type>::max();
        ITERATE_ON_ROW {
          if (x[*ind] > max_val)
            max_val = x[*ind];
        }
        *y++ = max_val != - std::numeric_limits<value_type>::max() ? max_val : (value_type) 0;
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
      std::fill(y, y + nCols(), (value_type) - std::numeric_limits<value_type>::max());

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          if (x[row] > y[*ind])
            y[*ind] = x[row];
        }
      }

      for (size_type i = 0; i != nCols(); ++i)
        if (y[i] == (value_type) - std::numeric_limits<value_type>::max())
          y[i] = 0;
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of the values in x corresponding to the non-zeros
     * of each row. Stores the result in y for each row. The operation is:
     *
     *  for row in [0,nrows):
     *   y[row] = max(lb, prod(x[col], for col in [0,ncols) s.t. this[row,col] != 0))
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] output vector (size = number of rows)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void rightVecProdAtNZ(InputIterator x, OutputIterator y,
                                 const value_type& lb) const
    {
      size_type k, nnzr, end, *ind;
      double val;

      ITERATE_ON_ALL_ROWS {

        nnzr = nnzr_[row];
        ind = ind_[row];
        val = 1;
        end = 4*(nnzr / 4);

        for (k = 0; k < end && val > lb; k += 4)
          val *= x[ind[k]] * x[ind[k+1]] * x[ind[k+2]] * x[ind[k+3]];

        if (val > lb)
          for (k = end; k != nnzr; ++k)
            val *= x[ind[k]];

        if (val > lb)
          *y++ = val;
        else
          *y++ = lb;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the max value of vector x corresponding to a non-zero of each
     * row of this SparseMatrix. For each row, this max is stored in y:
     *
     *  for row in [0,nrows):
     *   y[row] = max(x[col], for col in [0,ncols) s.t. this[row,col] != 0)
     *
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] result (size = number of rows)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void vecMaxAtNZ(InputIterator x, OutputIterator y) const
    {
      ITERATE_ON_ALL_ROWS {

        value_type max_v = - std::numeric_limits<value_type>::max();

        ITERATE_ON_ROW {
          value_type a = x[*ind];
          if (a > max_v)
            max_v = a;
        }

        *y++ = max_v == - std::numeric_limits<value_type>::max() ? 0 : max_v;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the index of the max value of x, where that
     * value is at the index of a non-zero. Does that for each
     * row, stores the resulting index in y for each row:
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
    inline void vecArgMaxAtNZ(InputIterator x, OutputIterator y) const
    {
      size_type j, arg_j = 0;
      value_type val, max_val;

      ITERATE_ON_ALL_ROWS {

        arg_j = 0;
        max_val = - std::numeric_limits<value_type>::max();

        ITERATE_ON_ROW {
          j = *ind;
          val = x[j];
          if (val > max_val) {
            arg_j = j;
            max_val = val;
          }
        }

        *y++ = arg_j;
      }
    }

    //--------------------------------------------------------------------------------
    // End AtNZ operations
    //--------------------------------------------------------------------------------

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of all the values in vector x by all the non zero values
     * on each row of this sparse matrix:
     *
     *  for row in [0,nrows):
     *   y[row] =
     *    prod(this[row,col] * x[col], for col in [0,ncols) s.t. this[row,col] != 0)
     *
     * @param x [InputIterator<value_type>] input vector (size = number or columns)
     * @param y [OutputIterator<value_type>] output vector (size = number of rows)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void rowVecProd(InputIterator x, OutputIterator y) const
    {
      typedef typename std::iterator_traits<OutputIterator>::value_type OVT;

      ITERATE_ON_ALL_ROWS {
        prec_value_type val = (prec_value_type) 1.0;
        ITERATE_ON_ROW
          val *= ((prec_value_type)*nz) * ((prec_value_type)x[*ind]);
        *y++ = (OVT) val;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the product of all the values in vector x by all the non zero values
     * on each row of this sparse matrix:
     *
     *  for row in [0,nrows):
     *   y[row] =
     *    max(lb,
     *        prod(this[row,col] * x[col], for col in [0,ncols) s.t. this[row,col] != 0))
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] output vector (size = number of rows)
     * @param lb [value_type] lower bound to use as a floor
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void rowVecProd(InputIterator x, OutputIterator y,
                           const value_type& lb) const
    {
      ITERATE_ON_ALL_ROWS {
        prec_value_type val = (prec_value_type) 1.0;
        ITERATE_ON_ROW
          val *= *nz * x[*ind];
        *y++ = val > lb ? val : lb;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the max prod between each element of vector x and each non-zero
     * of each row of this SparseMatrix. Puts the max for each row in vector y:
     *
     *  for row in [0,nrows):
     *   y[row] =
     *    max(this[row,col] * x[col], for col in [0,ncols) s.t. this[row,col] != 0)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] result (size = number of fows)
     *
     * @b Exceptions:
     *  @li None
     */
    template <typename InputIterator, typename OutputIterator>
    inline void vecMaxProd(InputIterator x, OutputIterator y) const
    {
      ITERATE_ON_ALL_ROWS {

        value_type max_v = nnzr_[row] == 0 ? 0 : nz_[row][0] * x[ind_[row][0]];

        ITERATE_ON_ROW {
          value_type p = *nz * x[*ind];
          if (p > max_v)
            max_v = p;
        }

        *y++ = max_v;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the arg of the max prod between each element of vector x and
     * each non-zero of each row of this SparseMatrix. Puts the max for each row
     * in vector y:
     *
     *  for row in [0,nrows):
     *   y[row] =
     *    argmax(this[row,col] * x[col], for col in [0,ncols) s.t. this[row,col] != 0)
     *
     * @param x [InputIterator<value_type>] input vector (size = number of columns)
     * @param y [OutputIterator<value_type>] result (size = number of fows)
     *
     * @b Exceptions:
     *  @li None
     *
     * TODO: problem doesn't work with matrix that contains negative numbers,
     * because in that case, 0 could be a legit value.
     */
    template <typename InputIterator, typename OutputIterator>
    inline void vecArgMaxProd(InputIterator x, OutputIterator y) const
    {
      ITERATE_ON_ALL_ROWS {

        size_type max_i = 0;
        value_type max_v = - std::numeric_limits<value_type>::max();

        ITERATE_ON_ROW {
          value_type p = *nz * x[*ind];
          if (!isZero_(p) && p >= max_v) {
            max_v = p;
            max_i = *ind;
          }
        }

        *y++ = max_i;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * For each row i of this SparseMatrix, finds this row in B, and if it is found
     * as row j of B, puts a 1 at (i, j) in C.
     * Assumes that the rows of B are unique.
     */
    inline void map(const SparseMatrix& B, SparseMatrix& C) const
    {
      {
        NTA_ASSERT(C.nRows() == 0);
        NTA_ASSERT(nCols() == B.nCols());
        NTA_ASSERT(C.nCols() == B.nRows());
      }

      nzb_[0] = (value_type) 1;
      bool matched = false;

      for (size_type i = 0; i != this->nRows(); ++i) {

        matched = false;
        for (size_type i2 = 0; i2 != B.nRows(); ++i2) {
          if (nnzr_[i] == B.nnzr_[i2]) {
            size_type j = 0, nnzr = nnzr_[i];
            while ((j < nnzr) && (ind_[i][j] == B.ind_[i2][j])
                   && (nearlyEqual(nz_[i][j], B.nz_[i2][j])))
              ++j;
            if (j == nnzr) {
              indb_[0] = i2;
              matched = true;
              break;
            }
          }
        }
        if (matched)
          C.addRow(indb_, indb_ + 1, nzb_);
      }
    }

    //--------------------------------------------------------------------------------
    // OUTER PRODUCT
    //--------------------------------------------------------------------------------

    //--------------------------------------------------------------------------------
    /**
     * Increments this sparse matrix with outer product of two passed vectors.
     *
     * this += outer(x,y)
     */
    template <typename InputIterator>
    inline void
    incrementWithOuterProduct(InputIterator x_begin, InputIterator x_end,
                              InputIterator y_begin, InputIterator y_end)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);
        NTA_ASSERT((size_type)(x_end - x_begin) == nRows())
          << "incrementWithOuterProduct: Wrong size for x vector: "
          << (size_type)(x_end - x_begin)
          << " - Should be = nrows = " << nRows();
        NTA_ASSERT((size_type)(y_end - y_begin) == nCols())
          << "incrementWithOuterProduct: Wrong size for y vector: "
          << (size_type)(y_end - y_begin)
          << " - Should be = ncols = " << nCols();
      } // End pre-conditions

      std::vector<size_type> ind(nCols());
      std::vector<value_type> nz(nCols());
      typename std::vector<size_type>::iterator ind_it = ind.begin();
      typename std::vector<value_type>::iterator nz_it = nz.begin();

      for (InputIterator y = y_begin; y != y_end; ++y) {
        value_type val = *y;
        if (!isZero_(val)) {
          *ind_it++ = (size_type)(y - y_begin);
          *nz_it++ = val;
        }
      }

      typename std::vector<size_type>::iterator ind_end = ind_it;

      for (InputIterator x = x_begin; x != x_end; ++x) {
        value_type val1 = *x;
        if (isZero_(val1))
          continue;
        size_type row = (size_type)(x - x_begin);
        ind_it = ind.begin();
        nz_it = nz.begin();
        for (; ind_it != ind_end; ++ind_it, ++nz_it)
          increment(row, *ind_it, val1 * *nz_it);
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * this += outer(x,y)
     */
    inline void
    incrementWithOuterProduct(const std::vector<value_type>& x,
                              const std::vector<value_type>& y)
    {
      incrementWithOuterProduct(x.begin(), x.end(), y.begin(), y.end());
    }

    //--------------------------------------------------------------------------------
    /**
     * Increments all the elements whose position is in the cross product of the
     * two ranges by val.
     *
     * this += val * (outer(x,y) != 0)
     */
    template <typename InputIterator>
    inline void
    incrementOnOuterProductVal(InputIterator row_begin, InputIterator row_end,
                               InputIterator col_begin, InputIterator col_end,
                               const value_type& val)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);
      } // End pre-conditions

      this->applyOuter(row_begin, row_end, col_begin, col_end, nta::PlusVal(val));
    }

    //--------------------------------------------------------------------------------
    /**
     * Increments all the elements whose position is in the cross product of the
     * two ranges by val.
     *
     * this += val * (outer(x,y) != 0)
     */
    inline void
    incrementOnOuterProductVal(const std::vector<size_type>& rows,
                               const std::vector<size_type>& cols,
                               const value_type& val =1.0)
    {
      for (size_type i = 0; i != rows.size(); ++i)
        for (size_type j = 0; j != cols.size(); ++j)
          set(rows[i], cols[j], get(rows[i], cols[j]) + val);
    }

    //--------------------------------------------------------------------------------
    /**
     * Increments the elements whose position is in the cross product of the
     * two ranges with the values from the given matrix.
     *
     * this += other .* (outer(x,y) != 0)
     */
    template <typename InputIterator, typename Other>
    inline void
    incrementOnOuterProductMat(InputIterator row_begin, InputIterator row_end,
                               InputIterator col_begin, InputIterator col_end,
                               const Other& other)
    {
      { // Pre-conditions
        ASSERT_INPUT_ITERATOR(InputIterator);
      } // End pre-conditions

      this->applyOuter(row_begin, row_end, col_begin, col_end,
                       nta::Plus<value_type>(), other);
    }

    //--------------------------------------------------------------------------------
    // SORT
    //--------------------------------------------------------------------------------
    template <typename StrictWeakOrdering>
    inline void
    stable_sort_rows(size_type row_begin, size_type row_end, StrictWeakOrdering o)
    {
      if (isCompact())
        decompact();

      const size_type nrows = nRows();
      std::vector<size_type> sorted(nrows);
      for (size_type row = 0; row != nrows; ++row)
        sorted[row] = row;
      std::stable_sort(sorted.begin(), sorted.end(), o);
      std::vector<size_type> tmp_nnzr(nrows);
      std::vector<size_type*> tmp_ind(nrows);
      std::vector<value_type*> tmp_nz(nrows);
      for (size_type row = 0; row != nrows; ++row) {
        tmp_nnzr[row] = nnzr_[sorted[row]];
        tmp_ind[row] = ind_[sorted[row]];
        tmp_nz[row] = nz_[sorted[row]];
      }
      std::copy(tmp_nnzr.begin(), tmp_nnzr.end(), nnzr_);
      std::copy(tmp_ind.begin(), tmp_ind.end(), ind_);
      std::copy(tmp_nz.begin(), tmp_nz.end(), nz_);
    }

    //--------------------------------------------------------------------------------
  private:
    class AscendingNNZ
    {
    public:
      AscendingNNZ(const SparseMatrix& sm) :sm_(sm) {}
      AscendingNNZ(const AscendingNNZ& other) : sm_(other.sm_) {}
      //AscendingNNZ& operator=(const AscendingNNZ& other)
      //{ sm_ = other.sm_; return *this; }

      inline bool operator()(const size_type& row1, const size_type& row2) const
      {
        return sm_.nNonZerosOnRow(row1) < sm_.nNonZerosOnRow(row2);
      }

    private:
      const SparseMatrix& sm_;
      AscendingNNZ();
    };

  public:
    inline void sortRowsAscendingNNZ()
    {
      stable_sort_rows(0, nRows(), AscendingNNZ(*this));
    }

    //--------------------------------------------------------------------------------
    // PRINT
    //--------------------------------------------------------------------------------
    /**
     * Print mehod. Prints the matrix in a dense representation.
     */
    inline void
    print(std::ostream& outStream, size_type precision=2, size_type width=6) const
    {
      size_type i, j, k;
      for (i = 0; i != nRows(); ++i) {
        for (j = 0, k = 0; j != nCols(); ++j) {
          outStream.width(width);
          outStream.precision(precision);
          outStream << (k < nnzr_[i] && ind_[i][k] == j ? nz_[i][k++] : 0) << " ";
        }
        if (i < nRows()-1)
          outStream << std::endl;
      }
    }

    //--------------------------------------------------------------------------------
    // SPECIFICS
    //--------------------------------------------------------------------------------

    // MANUAL SPECIFICS

    /**
     * Replaces the non-zeros by the specified value.
     */
    inline void replaceNZ(const value_type& val =1.0)
    {
      elementNZApply(nta::AssignVal(val));
    }

    /**
     * Returns the product of the non-zeros on the diagonal.
     */
    inline value_type diagNZProd() const
    {
      value_type res = 1.0;
      ITERATE_ON_ALL_ROWS {
        difference_type offset = col_(row, row);
        if (offset >= 0)
          res *= nz_[row][offset];
      }
      return res;
    }

    /**
     * Returns the sum of the non-zeros on the diagonal.
     */
    inline value_type diagSum() const
    {
      value_type res = 0.0;
      ITERATE_ON_ALL_ROWS {
        difference_type offset = col_(row, row);
        if (offset >= 0)
          res += nz_[row][offset];
      }
      return res;
    }

    /**
     * Returns the sum of the logs of the non-zeros on the diagonal.
     */
    inline value_type diagNZLogSum() const
    {
      nta::Log<value_type> nta_log;
      value_type res = 0.0;
      ITERATE_ON_ALL_ROWS {
        difference_type offset = col_(row, row);
        if (offset >= 0)
          res += nta_log(nz_[row][offset]);
      }
      return res;
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the sum of the logs of the NZ for each row.
     */
    template <typename OutputIterator>
    inline void logRowSums(OutputIterator out, OutputIterator out_end) const
    {
      {
        NTA_ASSERT((size_type)(out_end - out) == nRows())
          << "SparseMatrix::logRowSums: Invalid size for output vector";
      }

      nta::Log<value_type> log_f;

      ITERATE_ON_ALL_ROWS {
        value_type s = 0;
        ITERATE_ON_ROW {
          s +=log_f(*nz);
        }
        *out++ = s;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the sum of the logs of the NZ for each column.
     */
    template <typename OutputIterator>
    inline void logColSums(OutputIterator out, OutputIterator out_end) const
    {
      {
        NTA_ASSERT((size_type)(out_end - out) == nCols())
          << "SparseMatrix::logColSums: Invalid size for output vector";
      }

      nta::Log<value_type> log_f;

      nta::zero(out, out_end);

      ITERATE_ON_ALL_ROWS {
        ITERATE_ON_ROW {
          out[*ind] += log_f(*nz);
        }
      }
    }

    //--------------------------------------------------------------------------------
    // GENERATED SPECIFICS
    //--------------------------------------------------------------------------------

    inline void rowNegate(size_type idx)
    {
      elementRowNZApply(idx, nta::Negate<value_type>());
    }

    inline void colNegate(size_type idx)
    {
      elementColNZApply(idx, nta::Negate<value_type>());
    }

    inline void negate()
    {
      elementNZApply(nta::Negate<value_type>());
    }

    inline void rowAbs(size_type idx)
    {
      elementRowNZApply(idx, nta::Abs<value_type>());
    }

    inline void colAbs(size_type idx)
    {
      elementColNZApply(idx, nta::Abs<value_type>());
    }

    inline void abs()
    {
      elementNZApply(nta::Abs<value_type>());
    }

    inline void elementRowSquare(size_type idx)
    {
      elementRowNZApply(idx, nta::Square<value_type>());
    }

    inline void elementColSquare(size_type idx)
    {
      elementColNZApply(idx, nta::Square<value_type>());
    }

    inline void elementSquare()
    {
      elementNZApply(nta::Square<value_type>());
    }

    inline void elementRowCube(size_type idx)
    {
      elementRowNZApply(idx, nta::Cube<value_type>());
    }

    inline void elementColCube(size_type idx)
    {
      elementColNZApply(idx, nta::Cube<value_type>());
    }

    inline void elementCube()
    {
      elementNZApply(nta::Cube<value_type>());
    }

    inline void elementRowNZInverse(size_type idx)
    {
      elementRowNZApply(idx, nta::Inverse<value_type>());
    }

    inline void elementColNZInverse(size_type idx)
    {
      elementColNZApply(idx, nta::Inverse<value_type>());
    }

    inline void elementNZInverse()
    {
      elementNZApply(nta::Inverse<value_type>());
    }

    inline void elementRowSqrt(size_type idx)
    {
      elementRowNZApply(idx, nta::Sqrt<value_type>());
    }

    inline void elementColSqrt(size_type idx)
    {
      elementColNZApply(idx, nta::Sqrt<value_type>());
    }

    inline void elementSqrt()
    {
      elementNZApply(nta::Sqrt<value_type>());
    }

    inline void elementRowNZLog(size_type idx)
    {
      elementRowNZApply(idx, nta::Log<value_type>());
    }

    inline void elementColNZLog(size_type idx)
    {
      elementColNZApply(idx, nta::Log<value_type>());
    }

    inline void elementNZLog()
    {
      elementNZApply(nta::Log<value_type>());
    }

    inline void elementRowNZExp(size_type idx)
    {
      elementRowNZApply(idx, nta::Exp<value_type>());
    }

    inline void elementColNZExp(size_type idx)
    {
      elementColNZApply(idx, nta::Exp<value_type>());
    }

    inline void elementNZExp()
    {
      elementNZApply(nta::Exp<value_type>());
    }

    //--------------------------------------------------------------------------------
    inline void elementRowMultiply(size_type row, const value_type& val)
    {
      elementRowNZApply(row, nta::MultipliesByVal(val));
    }

    template <typename InputIterator>
    inline void elementRowMultiply(size_type row, InputIterator x)
    {
      elementRowNZApply(row, std::multiplies<value_type>(), x);
    }

    template <typename InputIterator, typename OutputIterator>
    inline void
    elementRowMultiply(size_type row, InputIterator x, OutputIterator y) const
    {
      elementRowNZApply(row, std::multiplies<value_type>(), x, y);
    }

    inline void
    elementRowMultiply(size_type row, const std::vector<value_type>& x,
                       std::vector<value_type>& y) const
    {
      elementRowMultiply(row, x.begin(), y.begin());
    }

    //--------------------------------------------------------------------------------

    inline void elementColMultiply(size_type col, const value_type& val)
    {
      elementColNZApply(col, nta::MultipliesByVal(val));
    }

    template <typename InputIterator>
    inline void elementColMultiply(size_type col, InputIterator x)
    {
      elementColNZApply(col, std::multiplies<value_type>(), x);
    }

    template <typename InputIterator, typename OutputIterator>
    inline void
    elementColMultiply(size_type col, InputIterator x, OutputIterator y) const
    {
      elementColNZApply(col, std::multiplies<value_type>(), x, y);
    }

    inline void
    elementColMultiply(size_type col, const std::vector<value_type>& x,
                       std::vector<value_type>& y) const
    {
      elementColMultiply(col, x.begin(), y.begin());
    }

    //--------------------------------------------------------------------------------

    inline void multiply(const value_type& val)
    {
      elementNZApply(nta::MultipliesByVal(val));
    }

    inline void elementRowDivide(size_type idx, const value_type& val)
    {
      elementRowNZApply(idx, nta::DividesByVal(val));
    }

    inline void elementColDivide(size_type idx, const value_type& val)
    {
      elementColNZApply(idx, nta::DividesByVal(val));
    }

    inline void divide(const value_type& val)
    {
      { // Pre-conditions
        NTA_ASSERT(!isZero_(val))
          << "divide: Division by zero";
      } // End pre-conditions

      elementNZApply(nta::DividesByVal(val));
    }

    inline void elementRowNZPow(size_type idx, const value_type& val)
    {
      elementRowNZApply(idx, nta::PowVal(val));
    }

    inline void elementColNZPow(size_type idx, const value_type& val)
    {
      elementColNZApply(idx, nta::PowVal(val));
    }

    inline void elementNZPow(const value_type& val)
    {
      elementNZApply(nta::PowVal(val));
    }

    inline void elementRowNZLogk(size_type idx, const value_type& val)
    {
      elementRowNZApply(idx, nta::LogkVal(val));
    }

    inline void elementColNZLogk(size_type idx, const value_type& val)
    {
      elementColNZApply(idx, nta::LogkVal(val));
    }

    inline void elementNZLogk(const value_type& val)
    {
      elementNZApply(nta::LogkVal(val));
    }

    template <typename InputIterator>
    inline void elementRowAdd(size_type idx, InputIterator x)
    {
      elementRowApply(idx, std::plus<value_type>(), x);
    }

    template <typename InputIterator>
    inline void elementRowSubtract(size_type idx, InputIterator x)
    {
      elementRowApply(idx, std::minus<value_type>(), x);
    }

    template <typename InputIterator>
    inline void elementRowDivide(size_type idx, InputIterator x)
    {
      elementRowNZApply(idx, std::divides<value_type>(), x);
    }

    template <typename InputIterator>
    inline void elementColAdd(size_type idx, InputIterator x)
    {
      elementColApply(idx, std::plus<value_type>(), x);
    }

    template <typename InputIterator>
    inline void elementColSubtract(size_type idx, InputIterator x)
    {
      elementColApply(idx, std::minus<value_type>(), x);
    }

    template <typename InputIterator>
    inline void elementColDivide(size_type idx, InputIterator x)
    {
      elementColNZApply(idx, std::divides<value_type>(), x);
    }

    inline void rowAdd(size_type idx, const value_type& val)
    {
      elementRowApply(idx, nta::PlusVal(val));
    }

    inline void colAdd(size_type idx, const value_type& val)
    {
      elementColApply(idx, nta::PlusVal(val));
    }

    inline void add(const value_type& val)
    {
      elementApply(nta::PlusVal(val));
    }

    inline void elementNZAdd(const value_type& val)
    {
      elementNZApply(nta::PlusVal(val));
    }

    inline void rowSubtract(size_type idx, const value_type& val)
    {
      elementRowApply(idx, nta::MinusVal(val));
    }

    inline void colSubtract(size_type idx, const value_type& val)
    {
      elementColApply(idx, nta::MinusVal(val));
    }

    inline void subtract(const value_type& val)
    {
      elementApply(nta::MinusVal(val));
    }

    inline void elementNZMultiply(const SparseMatrix& other)
    {
      elementMultiply(other);
    }

    inline void elementNZDivide(const SparseMatrix& other)
    {
      elementNZApply(other, nta::Divides<value_type>());
    }

    inline void subtract(const SparseMatrix& other)
    {
      elementApply(other, nta::Minus<value_type>());
    }

    //--------------------------------------------------------------------------------
    // OPERATORS
    //--------------------------------------------------------------------------------

    inline void operator +=(const value_type& val)
    {
      add(val);
    }

    //--------------------------------------------------------------------------------
    inline void operator -=(const value_type& val)
    {
      subtract(val);
    }

    //--------------------------------------------------------------------------------
    inline void operator *=(const value_type& val)
    {
      multiply(val);
    }

    //--------------------------------------------------------------------------------
    inline void operator /=(const value_type& val)
    {
      divide(val);
    }

    //--------------------------------------------------------------------------------

  }; // end class SparseMatrix

  //--------------------------------------------------------------------------------
  template <typename I,typename F,typename I2,typename F2,typename ZeroTest>
  inline std::ostream& operator<<(std::ostream& out_stream,
                                  const SparseMatrix<I,F,I2,F2,ZeroTest>& x)
  {
    if (io_control.sparse_io == AS_DENSE) {
      x.print(out_stream, 2, 5);
    } else if (io_control.sparse_io == CSR)
      x.toCSR(out_stream);
    else if (io_control.sparse_io == BINARY)
      const_cast<SparseMatrix<I,F,I2,F2,ZeroTest>&>(x).toBinary(out_stream);
    return out_stream;
  }

  //--------------------------------------------------------------------------------
  template <typename I,typename F,typename I2,typename F2,typename ZeroTest>
  inline std::istream& operator>>(std::istream& in_stream,
                                  SparseMatrix<I,F,I2,F2,ZeroTest>& x)
  {
    if (io_control.sparse_io == CSR)
      x.fromCSR(in_stream);
    else if (io_control.sparse_io == BINARY)
      x.fromBinary(in_stream);
    return in_stream;
  }

  //--------------------------------------------------------------------------------
  /**
   * Equality operator for SparseMatrix.
   */
  template <typename I,typename F,typename I2,typename F2,typename ZeroTest>
  inline
  bool operator==(const SparseMatrix<I,F,I2,F2,ZeroTest>& A,
                  const SparseMatrix<I,F,I2,F2,ZeroTest>& B)
  {
    return A.equals(B);
  }

  template <typename I,typename F,typename I2,typename F2,typename ZeroTest>
  inline
  bool operator!=(const SparseMatrix<I,F,I2,F2,ZeroTest>& A,
                  const SparseMatrix<I,F,I2,F2,ZeroTest>& B)
  {
    return !A.equals(B);
  }

  //--------------------------------------------------------------------------------

} // end namespace nta

#endif // NTA_SPARSE_MATRIX_HPP

