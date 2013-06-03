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
 * Definition and implementation for SparseR3FTensor
 */

#ifndef NTA_SPARSE_R3F_TENSOR_HPP
#define NTA_SPARSE_R3F_TENSOR_HPP

#ifdef NUPIC2
#error "SparseR3FTensor should not be included in NuPIC2."
/* 
 * Only used in LoopyBeliefPropCD, which is not needed in NuPIC2
 */
#endif

#include <iostream>

#include <nta/math/math.hpp>

//--------------------------------------------------------------------------------
namespace nta {

  // Forward declarations
  struct SparseMatrixAlgorithms;
  class LogSumApprox;
  class LogDiffApprox;

  //--------------------------------------------------------------------------------
  /**                        
   * Sparse Rank 3 Fixed Tensor:
   * ==========================
   *
   * STR3F is a specialized sparse data structure that "groups" several
   * sparse matrices that all have their non-zeros in the same locations:
   * 
   * - stores a non-zeros *vector* at each (row,col) position instead of a scalar,
   *   making each non-zero located by three indices: a "slice" index, and inside
   *   that slice, a (row,col) position. All the slices have their non-zeros in the
   *   same locations,
   * - the number and positions of the non-zeros don't change after creation.
   *
   * Non-zeros are determined the same way as in SparseMatrix: a value whose abs
   * is less than nta::Epsilon is a zero.
   * 
   * Under these assumptions, storage is optimized:
   * - the non-zero elements are stored contiguously,
   * - overhead is reduced compared to SparseMatrix (which is more dynamic), because
   *   the locations of the non-zeros, which are the same in all slices, are stored
   *   only once, instead of being stored for each slice. 
   *
   * In contrast to SparseMatrix, this class is not dynamic, i.e. it is not possible 
   * to add or remove non-zeros after creation, and it is not possible to change 
   * the locations of the non-zeros either.
   */
  template <typename UI1 =nta::UInt32, // See just below for meaning of parameters
            typename UI2 =nta::UInt16, 
            typename T =nta::Real32,
            typename TT =nta::Real64>

  class SparseR3FTensor
  {
  public:
    typedef size_t        size_type;       // general counter type
    typedef UI1           row_index_type;  // separate row and col index types
    typedef UI2           col_index_type;  // for memory efficiency
    typedef T             value_type;      // type of the values of the non-zeros
    typedef TT            prec_value_type; // a more precise type for some computations

  private:
    // Dimensions
    // We use different types so we can optimize the memory consumption by 
    // using types that are as small as possible to store some indices 
    // (for example, it's usually the case that there will be less than 32768 columns).
    size_type       nslices_;   // generally expecting a small number of slices (<16?)
    row_index_type  nrows_;     // number of rows
    col_index_type  ncols_;     // number of columns
    size_type       nnzps_;     // number of non-zeros per slice

    // Data storage
    // We manage the memory ourselves instead of using the STL because we 
    // can save some memory that way, and because it's simple to use custom
    // allocation schemes, such as an aligned memory allocator that's required
    // for using SIMD instructions.
    size_type      *offsets_;   // offsets to beginning of rows
    col_index_type *ind_mem_;   // indices of the non-zeros, shared by all slices
    value_type     *nz_mem_;    // non-zero values, different for each slice
    value_type     *buff_;      // buffer, size == nCols()

    // Redundant data strutures to speed-up operations down the columns.
    // For each col, we store a list of offsets to each non-zero in the 
    // column of the first slice. The positions of the non-zeros for any
    // slice can be found by using the pointer to the beginning of the slice
    // and adding these indices.
    // Additionally, we precompute and store pointers to the non-zero values down
    // the columns for the fast slice (slice 0). That speeds-up the piPrime 
    // computations, which are essentially down the columns. It doubles
    // the memory size of the fast slice though.
    size_type      *c_offsets_; // number of non-zeros per column
    size_type      *c_ind_;     // indices of the non-zeros down the columns
    value_type    **c_ptrs_;    // column pointers

    // Portable functions used in various computations (from nta/math/math.hpp)
    nta::Exp<prec_value_type>   exp_f;
    nta::Log<prec_value_type>   log_f;
    nta::Log1p<prec_value_type> log1p_f; // log(1 + x)
    nta::Abs<prec_value_type>   abs_f;

    // 2 constants used in computations
    prec_value_type minExp;    // log(machine epsilon)
    prec_value_type logOfZero; // -1 / machine epsilon

    // SparseMatrixAlgorithms has additional algorithms on SparseR3FTensor that 
    // are specific to certain, maybe experimental, algorithms.
    friend struct SparseMatrixAlgorithms;

    // Those two classes are used to speed up log sum and log diff.
    friend class LogSumApprox;
    friend class LogDiffApprox;

    //--------------------------------------------------------------------------------
    /**
     * Self-explanatory macros that make the code easier to read.
     */
#define ST_R3_ITERATE_ON_ALL_ROWS                       \
    for (row_index_type r = 0; r != nRows(); ++r)     
    
#define ST_R3_ITERATE_ON_ROW                                            \
    col_index_type *ind = ind_begin_(r), *ind_end = ind_end_(r);        \
    value_type *nz = nz_begin_(s,r);                                    \
    for (; ind != ind_end; ++ind, ++nz)
    
#define ST_R3_ITERATE_ON_SLICE                                          \
    col_index_type *ind = ind_mem_, *ind_end = ind + nNonZerosPerSlice(); \
    value_type *nz = slice_nz_begin_(s);                                \
    for (; ind != ind_end; ++ind, ++nz)
    
#define ST_R3_ITERATE_ON_SLICE_NZ                                       \
    value_type *nz = slice_nz_begin_(s), *nz_end = slice_nz_end_(s);    \
    for (; nz != nz_end; ++nz)
    
#define ST_R3_ITERATE_ON_2_SLICES                               \
    size_type *ind = ind_begin_(r), *ind_end = ind_end_(r);     \
    value_type *nz_a = nz_begin_(slice_a, r);                   \
    value_type *nz_b = nz_begin_(slice_b, r);                   \
    for (; ind != ind_end; ++ind, ++nz_a, ++nz_b) 
    
#define ST_R3_ITERATE_ON_2_SLICES_NZ                    \
    value_type *nz_a = slice_nz_begin_(slice_a);        \
    value_type *nz_a_end = slice_nz_end_(slice_a);      \
    value_type *nz_b = slice_nz_begin_(slice_b);        \
    for (; nz_a != nz_a_end; ++nz_a, ++nz_b) 
    
    //--------------------------------------------------------------------------------
  public:

    /**
     * Needed for bindings.
     */
    inline SparseR3FTensor()
      : nslices_(0), nrows_(0), ncols_(0), nnzps_(0),
        offsets_(NULL), ind_mem_(NULL), nz_mem_(NULL),
        buff_(NULL),
        c_offsets_(NULL), c_ind_(NULL), c_ptrs_(NULL), 
        exp_f(), log_f(), log1p_f(), abs_f(),
        minExp(log_f(std::numeric_limits<value_type>::epsilon())),
        logOfZero(-1.0/std::numeric_limits<value_type>::epsilon())
    {}
  
    //--------------------------------------------------------------------------------
    /**
     * Receives (row,col) of non-zeros (from a SM or SM/01 getAllNonZeros)
     * for only one slice.
     * Initializes all the non-zeros to 1, in each slice: all the slices
     * start with 1 at the positions of the non-zeros.
     *
     * Parameters:
     * ==========
     * - fastSlice: index of the slice for which to make piPrime fast.
     *   Should be less than number of slices.
     * - topN: number of activations per column to consider in topNPiPrime. 
     *   Should be less than the number of columns.
     */
    template <typename InIt1, typename InIt2, typename InIt3> 
    SparseR3FTensor(size_type nslices, row_index_type nrows, col_index_type ncols,
                    InIt1 i, InIt1 i_end, InIt2 j, InIt2 j_end)
      : nslices_(0), nrows_(0), ncols_(0), nnzps_(0),
        offsets_(NULL), ind_mem_(NULL), nz_mem_(NULL),
        buff_(NULL),
        c_offsets_(NULL), c_ind_(NULL), c_ptrs_(NULL), 
        exp_f(), log_f(), log1p_f(), abs_f(),
        minExp(log_f(std::numeric_limits<value_type>::epsilon())),
        logOfZero(-1.0/std::numeric_limits<value_type>::epsilon())
    {
      {
        NTA_ASSERT(0 < nslices);
        NTA_ASSERT(0 < nrows);
        NTA_ASSERT(0 < ncols);
      }

      setAllNonZeros(nslices, nrows, ncols, i, i_end, j, j_end);
      initialize_col_nz_();
    }

    //--------------------------------------------------------------------------------
    inline ~SparseR3FTensor()
    {
      delete [] offsets_;
      offsets_ = NULL;

      delete [] ind_mem_;
      ind_mem_ = NULL;

      delete [] nz_mem_;
      nz_mem_ = NULL;

      delete [] buff_;
      buff_ = NULL;

      delete [] c_offsets_;
      c_offsets_ = NULL;
      
      delete [] c_ind_;
      c_ind_ = NULL;

      delete [] c_ptrs_;
      c_ptrs_ = NULL;
    }

    //--------------------------------------------------------------------------------
    inline const std::string getVersion() const 
    {
      return std::string("st_r3f_1.0");
    }

    //--------------------------------------------------------------------------------
    inline size_type nSlices() const 
    {
      return nslices_;
    }

    //--------------------------------------------------------------------------------
    inline row_index_type nRows() const 
    {
      return nrows_;
    }

    //--------------------------------------------------------------------------------
    inline col_index_type nCols() const 
    {
      return ncols_;
    }

    //--------------------------------------------------------------------------------
    /**
     * All the slices have the same number of non-zeros, in the same locations. 
     */
    inline size_type nNonZerosPerSlice() const
    {
      return nnzps_;
    }

    //--------------------------------------------------------------------------------
    /**
     * Total number of non-zeros in the whole SparseR3FTensor.
     */
    inline size_type nNonZeros() const
    {
      return nSlices() * nNonZerosPerSlice();
    }

    //--------------------------------------------------------------------------------
    /**
     * Number of non-zeros on a given row, which is the same for all slices.
     */
    inline size_type nNonZerosOnRow(row_index_type r) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_row_index_(r, "nNonZerosOnRow");
#endif

      return r == 0 ? offsets_[0] : offsets_[r] - offsets_[r-1];
    }

    //--------------------------------------------------------------------------------
    /**
     * Exact number of bytes taken up by an instance.
     */
    inline size_type nBytes() const 
    {
      size_type S = sizeof(SparseR3FTensor)
        + nRows() * sizeof(size_type)                   // offsets_
        + nNonZerosPerSlice() * sizeof(col_index_type)  // ind_mem_
        + nNonZeros() * sizeof(value_type)              // nz_mem_
        + nCols() * sizeof(value_type);                 // buff_
      
      // c_offsets_ and c_ind_ are optional
      if (c_offsets_) {
        S += nCols() * sizeof(size_type)                // c_offsets_
          + nNonZerosPerSlice() * sizeof(size_type);    // c_ind_
      }

      return S;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns all the non-zeros in given slice of this SparseR3FTensor.
     * The result is returned in three iterators, the first for the row indices,
     * then the col indices, and finally the values.
     *
     * In debug mode, we throw an assert if we find a non-zero value less than 
     * nta::Epsilon. This is very useful to track down precision issues.
     */
    template <typename OutIt1, typename OutIt2, typename OutIt3>
    inline void
    getAllNonZeros(size_type s, 
                   OutIt1 i, OutIt1 i_end, 
                   OutIt2 j, OutIt2 j_end,
                   OutIt3 nz_v, OutIt3 nz_v_end) const
    {
      {
        NTA_ASSERT(s < nSlices());
        NTA_ASSERT(i <= i_end);
        NTA_ASSERT(j <= j_end);
        NTA_ASSERT(nz_v <= nz_v_end);
      }

      ST_R3_ITERATE_ON_ALL_ROWS {
        ST_R3_ITERATE_ON_ROW {
          *i++ = r;
          *j++ = *ind;
          NTA_ASSERT(!isZero_(*nz))
            << "SparseR3FTensor::getAllNonZeros: "
            << "Zero at " << r << ", " << *ind << ": " << *nz
            << " epsilon= " << nta::Epsilon;
          *nz_v++ = *nz;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets non-zeros from list of positions (i,j) of non-zeros. The non-zero values
     * are set to 1 for all slices. The previous state is discarded. 
     *
     * If the flag "clean" is true, then we assume that the non-zeros are 
     * unique, in increasing lexicographic order, and have values > epsilon.
     * If "clean" is false, we sort the values and remove the non-zeros
     * below epsilon, which is a lot slower.
     *
     * In debug mode, we detect and throw an assert if the non-zeros are not in
     * strictly increasing lexicographic order.
     */
    template <typename InIt1, typename InIt2>
    inline void 
    setAllNonZeros(size_type nslices, row_index_type nrows, col_index_type ncols,
                   InIt1 i, InIt1 i_end, InIt2 j, InIt2 j_end, bool clean =true)
    {
      { // Pre-conditions
        const char* where = "SparseR3FTensor::setAllNonZeros: ";

        NTA_ASSERT(0 < nslices);
        NTA_ASSERT(0 < nrows);
        NTA_ASSERT(0 < ncols);

	ASSERT_INPUT_ITERATOR(InIt1);
	ASSERT_INPUT_ITERATOR(InIt2);

        NTA_ASSERT(i_end - i == j_end - j)
          << where << "Invalid range";

#ifdef NTA_ASSERTIONS_ON

        if (i != i_end && clean) {
          InIt1 ii = i; 
          InIt2 jj = j;
          NTA_ASSERT(*ii < *(ii+1) || (*ii == *(ii + 1) && *jj < *(jj + 1)))
            << where << "Repeated or out-of-order "
            << "non-zero indices: "
            << "(" << *ii << ", " << *jj << ") and "
            << "(" << *(ii+1) << ", " << *(jj+1) << ")";
          ++ii; ++jj;
          for (; ii < i_end; ++ii, ++jj)
            NTA_ASSERT(*(ii-1) < *ii || (*(ii-1) == *ii && *(jj-1) < *jj))
              << where << "Repeated or out-of-order " 
              << "non-zero indices: "
              << "(" << *(ii-1) << ", " << *(jj-1) << ") and "
              << "(" << *ii << ", " << *jj << ")";
        }

        InIt1 iii = i;
        InIt2 jjj = j;
        for (; iii != i_end; ++iii, ++jjj) {
          NTA_ASSERT(*iii < nrows)
            << where << "Invalid row index: " << *iii
            << " - Should be < number of rows: " << nrows;
          NTA_ASSERT(*jjj < ncols)
            << where << "Invalid col index: " << *jjj
            << " - Should be < number of cols: " << ncols;
        }
#endif
      } // End pre-conditions

      // Used only if not clean, to hold unique locations of non-zeros
      typedef std::pair<row_index_type, col_index_type> IJ;
      typedef std::set<IJ, lexicographic_2<row_index_type, col_index_type> > S;
      typename S::const_iterator it;
      S s;

      nslices_ = nslices;
      nrows_ = nrows;
      ncols_ = ncols;

      // Deallocate old offsets_ offsets and allocate new ones
      delete [] offsets_;
      offsets_ = new size_type [nRows()];
      std::fill(offsets_, offsets_ + nRows(), (size_type) 0);

      // If "clean", we assume the indices are passed in strictly
      // increasing lexicographic order and we leverage that to 
      // fill offsets_ more efficiently.
      if (clean) {

        nnzps_ = (size_type) (i_end - i);
        
        for (; i != i_end; ++i)
          ++ offsets_[*i];

      } else {

        // Get accurate count of non-zeros, global and per slice, slow.
        // Here, we can't assume that the locations of the non-zeros are 
        // unique, so we populate a set first, and then we use that set
        // to count the non-zeros per row.
        InIt1 ii = i; InIt2 jj = j;
        for (; ii != i_end; ++ii, ++jj) {
          IJ ij(*ii, *jj);
          it = s.find(ij);
          if (it == s.end()) {
            s.insert(ij);
            ++ offsets_[*ii];
          }
        }

        nnzps_ = s.size();
      }

      // Whether clean or not, adjust offsets
      for (row_index_type r = 1; r < nRows(); ++r)
        offsets_[r] += offsets_[r-1];

      size_type nz_mem_size = nSlices() * nNonZerosPerSlice();

      // Now we can deallocate old structures and allocate
      // new ones.
      delete [] ind_mem_;
      delete [] nz_mem_;
      ind_mem_ = new col_index_type [nNonZerosPerSlice()];
      nz_mem_ = new value_type [nz_mem_size];

      std::fill(nz_mem_, nz_mem_ + nz_mem_size, (value_type) 1.0);

      // If "clean", we can iterate over j directly, and the successive
      // values of *j are the columns of the non-zeros. We know where
      // to stop for each row because we have computed the offsets to 
      // the beginning of each row in offsets_.
      if (clean) {

        ST_R3_ITERATE_ON_ALL_ROWS {
          col_index_type *ind = ind_begin_(r), *ind_end = ind_end_(r);
          for (; ind != ind_end; ++ind, ++j)
            *ind = *j;
        }

      } else {

        // If not "clean", we iterate on the set of unique locations
        // we have created above, rather than on the passed in j.
        it = s.begin();

        ST_R3_ITERATE_ON_ALL_ROWS {
          col_index_type *ind = ind_begin_(r), *ind_end = ind_end_(r);
          for (; ind != ind_end; ++ind, ++it)
            *ind = it->second;
        }
      }

      // Finally, adjusts the size of the buffer, which is always the 
      // number of columns.
      delete [] buff_;
      buff_ = new value_type [nCols()];

      { // Post-conditions
        NTA_ASSERT(offsets_[nrows_ - 1] == nNonZerosPerSlice());
      } // End post-conditions
    }

    //--------------------------------------------------------------------------------
    /**
     * Discards current state and set new state from dense. The dense array
     * is used to find the location (row,col) of the non-zeros (which are the same
     * for all slices), but the values are actually disregarded. Instead, all the 
     * non-zeros in the new instance will be set to 1. The new number of rows and cols
     * are passed in. 
     */
    template <typename InputIterator>
    inline void 
    initializeFromDense(size_type nslices, row_index_type nrows, col_index_type ncols,
                        InputIterator x, InputIterator x_end)
    {
      {
        NTA_ASSERT(0 < nslices);
        NTA_ASSERT(0 < nrows);
        NTA_ASSERT(0 < ncols);
        NTA_ASSERT((size_type)(x_end - x) == nrows * ncols);
      }

      nslices_ = nslices;
      nrows_ = nrows;
      ncols_ = ncols;
      
      delete [] offsets_;
      delete [] ind_mem_;
      delete [] nz_mem_;
      delete [] buff_;

      buff_ = new value_type [nCols()];
      offsets_ = new size_type [nRows()];

      std::fill(offsets_, offsets_ + nRows(), (size_type) 0);

      nnzps_ = 0;
      InputIterator x_ptr = x;

      // Count number of non-zeros per row, and store in offsets_
      for (row_index_type r = 0; r != nRows(); ++r) 
        for (col_index_type c = 0; c != nCols(); ++c, ++x_ptr) 
          if (!isZero_(*x_ptr)) {
            ++ offsets_[r];
            ++ nnzps_;
          }

      // Adjust offsets_
      for (row_index_type r = 1; r < nRows(); ++r)
        offsets_[r] += offsets_[r-1];

      ind_mem_ = new col_index_type [nNonZerosPerSlice()];
      nz_mem_ = new value_type [nSlices() * nNonZerosPerSlice()];

      // All non-zeros in all slices start as "1"
      std::fill(nz_mem_, nz_mem_ + nSlices() * nNonZerosPerSlice(), (value_type) 1.0);
      
      // Set indices in ind_mem_
      col_index_type *ind = ind_mem_;

      for (row_index_type r = 0; r != nRows(); ++r) 
        for (col_index_type c = 0; c != nCols(); ++c, ++x) 
          if (!isZero_(*x)) 
            *ind++ = c;

      initialize_col_nz_();

      { // Post-conditions
        NTA_ASSERT(c_offsets_ && c_ind_ && c_ptrs_);
        NTA_ASSERT(offsets_[nrows_ - 1] == nNonZerosPerSlice());
      } // End post-conditions
    }

    //--------------------------------------------------------------------------------
    /**
     * Dumps given slice to dense storage. Fills the dense array with zeros, and then
     * sets the values of the non-zeros in the given slice. The dense array needs
     * to have nrows * ncols elements.
     */
    template <typename OutputIterator>
    inline void 
    toDense(size_type s, OutputIterator dense, OutputIterator dense_end) const
    {
      {
        assert_valid_slice_index_(s, "toDense");
        NTA_ASSERT((size_type)(dense_end - dense) == nRows() * nCols());
      }

      std::fill(dense, dense_end, 0);

      ST_R3_ITERATE_ON_ALL_ROWS {
        ST_R3_ITERATE_ON_ROW
          dense[r*nCols() + *ind] = *nz;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Loads non-zero values from dense array, for a given slice.
     * This looks only at the locations already stored for non-zeros. That is, it 
     * doesn't create new non-zeros, doesn't remove any either, just updates the 
     * values based on the dense array. The dense array needs to have nrows * ncols
     * elements.
     */
    template <typename InputIterator>
    inline void fromDense(size_type s, InputIterator dense, InputIterator dense_end)
    {    
      {
        assert_valid_slice_index_(s, "fromDense");
        NTA_ASSERT((size_type)(dense_end - dense) == nRows() * nCols());
      }

       ST_R3_ITERATE_ON_ALL_ROWS {
         ST_R3_ITERATE_ON_ROW
           *nz = dense[r*nCols() + *ind];
       }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the min for a given slice.
     */
    inline value_type min(row_index_type s) const
    {
      {
#ifdef NTA_ASSERTIONS_ON
        assert_valid_slice_index_(s, "min");
#endif
      }
      
      value_type min_val = std::numeric_limits<value_type>::max();

      ST_R3_ITERATE_ON_SLICE_NZ 
        if (*nz < min_val) 
          min_val = *nz;

      if (min_val == std::numeric_limits<value_type>::max())
        min_val = 0;

      return min_val;
    }
    
    //--------------------------------------------------------------------------------
    /**
     * Returns the max for a given slice.
     */
    inline value_type max(size_type s) const
    {
      {
#ifdef NTA_ASSERTIONS_ON
        assert_valid_slice_index_(s, "max");
#endif
      }

      value_type max_val = - std::numeric_limits<value_type>::max();

      ST_R3_ITERATE_ON_SLICE_NZ 
        if (*nz > max_val) 
          max_val = *nz;

      if (max_val == - std::numeric_limits<value_type>::max())
        max_val = 0;
      
      return max_val;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the sums of each row in a given slice.
     * Needs: sums_end - sums == nRows().
     */
    template <typename OutputIterator>
    inline void 
    rowSums(size_type s, OutputIterator sums, OutputIterator sums_end) const
    {
      { // Pre-conditions
#ifdef NTA_ASSERTIONS_ON
        assert_valid_slice_index_(s, "rowSums");
        NTA_ASSERT((row_index_type)(sums_end - sums) == nRows());
#endif
      } // End pre-conditions
      
      ST_R3_ITERATE_ON_ALL_ROWS {
        value_type v = 0;
        ST_R3_ITERATE_ON_ROW
          v += *nz;
        *sums++ = v;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns the sum of each column in a given slice. 
     * Needs: sums_end - sums == nCols().
     */
    template <typename OutputIterator>
    inline void 
    colSums(size_type s, OutputIterator sums, OutputIterator sums_end) const
    {
      { // Pre-conditions
#ifdef NTA_ASSERTIONS_ON
        assert_valid_slice_index_(s, "colSums");
        NTA_ASSERT((row_index_type)(sums_end - sums) == nCols());
#endif
      } // End pre-conditions
      
      std::fill(sums, sums_end, (value_type) 0);

      ST_R3_ITERATE_ON_SLICE 
        sums[*ind] += *nz;
    }
    
    //--------------------------------------------------------------------------------
    /**
     * Multiply given slice by given value in a given slice.
     */
    inline void multiply(size_type s, value_type k)
    {
      {
#ifdef NTA_ASSERTIONS_ON
        assert_valid_slice_index_(s, "multiply");
        NTA_ASSERT(!isZero_(k));
#endif
      }

      ST_R3_ITERATE_ON_SLICE_NZ
        *nz *= k;
    }

    //--------------------------------------------------------------------------------
    /**
     * Scale cols of a given slice by values from vector.
     */
    template <typename InputIterator>
    inline void scaleCols(size_type s, InputIterator x, InputIterator x_end)
    {
      {
#ifdef NTA_ASSERTIONS_ON
        assert_valid_slice_index_(s, "scaleCols");
        NTA_ASSERT((col_index_type)(x_end - x) == nCols());
        for (InputIterator it = x; it != x_end; ++it)
          NTA_ASSERT(!isZero_(*it));
#endif
      }
      
      ST_R3_ITERATE_ON_SLICE 
        *nz *= x[*ind];
    }

    //--------------------------------------------------------------------------------
    /**
     * Takes the exp of all the non-zeros in a given slice.
     */
    inline void elementNZExp(row_index_type s)
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_slice_index_(s, "elementNZExp");
#endif

      ST_R3_ITERATE_ON_SLICE_NZ 
        *nz = exp(*nz); // not using expf because of slowness on x86_64
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds a value to the non-zeros only in a given slice.
     * Values whose abs is less than minFloor are replaced by minFloor, so that
     * no new zero is introduced.
     */
    inline void NZAdd(size_type s, value_type val, value_type minFloor =0)
    {
      {
        NTA_ASSERT(s < nSlices());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
        NTA_ASSERT(nta::Epsilon < abs_f(val));
      }
        
      // Faster to do the operation, and then the tests.
      ST_R3_ITERATE_ON_SLICE_NZ 
        *nz += val;

      if (!isZero_(minFloor)) {
        ST_R3_ITERATE_ON_SLICE_NZ 
          if (abs_f(*nz) < minFloor)
            *nz = minFloor;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds vector to non-zeros only, down the columns in a given slice.
     * Values whose abs is less than minFloor are replaced by minFloor, so that
     * no new zero is introduced.
     */
    template <typename U>
    inline void NZAddDownCols(size_type s, U begin, U end, value_type minFloor =0)
    {
      {
        NTA_ASSERT(s < nSlices());
        NTA_ASSERT((col_index_type)(end - begin) == nCols());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      // Faster to do the operation, and then the tests.
      ST_R3_ITERATE_ON_SLICE 
        *nz += *(begin + *ind);

      if (!isZero_(minFloor)) {
        ST_R3_ITERATE_ON_SLICE_NZ
          if (abs_f(*nz) < minFloor) 
            *nz = minFloor;
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds vector to non-zeros only, across the rows in a given slice. 
     * Values whose abs is less than minFloor are replaced by minFloor, so that
     * no new zero is introduced.
     */
    template <typename U>
    inline void NZAddAcrossRows(size_type s, U begin, U end, value_type minFloor =0)
    {
      {
        NTA_ASSERT(s < nSlices());
        NTA_ASSERT((row_index_type)(end - begin) == nRows());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      ST_R3_ITERATE_ON_ALL_ROWS {
        ST_R3_ITERATE_ON_ROW 
          *nz += *begin;
        ++begin;
      }
      
      if (!isZero_(minFloor))
        ST_R3_ITERATE_ON_ALL_ROWS {
          ST_R3_ITERATE_ON_ROW {
            if (abs_f(*nz) < minFloor) 
              *nz = minFloor;
          }
          ++begin;
        }
    }

    //--------------------------------------------------------------------------------
    /**
     * Replaces non-zeros by 1 - non-zero value in a given slice. 
     */
    inline void NZOneMinus(size_type s)
    {
      {
        NTA_ASSERT(s < nSlices());
      }

      ST_R3_ITERATE_ON_SLICE_NZ 
        *nz = (value_type) 1.0 - *nz;
    }

    //--------------------------------------------------------------------------------
    /**
     * Negate the values of the non-zeros in a given slice.
     */
    inline void negate(size_type s)
    {
      {
        NTA_ASSERT(s < nSlices());
      }

      ST_R3_ITERATE_ON_SLICE_NZ
        *nz = - *nz;
    }
    
    //--------------------------------------------------------------------------------
    /**
     * Adds the non-zeros of slice b to the non-zeros of slice a. 
     * Values whose abs is less than minFloor are replaced by minFloor, so that
     * no new zero is introduced.
     */
    inline void add(size_type slice_a, size_type slice_b, value_type minFloor =0)
    {
      {
        NTA_ASSERT(slice_a < nSlices());
        NTA_ASSERT(slice_b < nSlices());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }
      
      ST_R3_ITERATE_ON_2_SLICES_NZ
        *nz_a += *nz_b;

      if (!isZero_(minFloor)) {
        size_type s = slice_a;
        ST_R3_ITERATE_ON_SLICE_NZ
          if (abs_f(*nz) < minFloor)
            *nz = minFloor;
      }
    }
    
    //--------------------------------------------------------------------------------
    /**
     * Subtracts the non-zeros of slice b from the non-zeros of slice a.
     * Values whose abs is less than minFloor are replaced by minFloor, so that
     * no new zero is introduced.
     */
    inline void subtract(size_type slice_a, size_type slice_b, value_type minFloor =0)
    {
      {
        NTA_ASSERT(slice_a < nSlices());
        NTA_ASSERT(slice_b < nSlices());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      ST_R3_ITERATE_ON_2_SLICES_NZ
        *nz_a -= *nz_b;

      if (!isZero_(minFloor)) {
        size_type s = slice_a;
        ST_R3_ITERATE_ON_SLICE_NZ
          if (abs_f(*nz) < minFloor)
            *nz = minFloor;
      }
    }
    
    //--------------------------------------------------------------------------------
    /**
     * Copies the values of the non-zeros of slice b into slice a.
     */
    inline void copySlice(size_type slice_a, size_type slice_b)
    {
      {
        NTA_ASSERT(slice_a < nSlices());
        NTA_ASSERT(slice_b < nSlices());
      }

      std::copy(slice_nz_begin_(slice_b), slice_nz_end_(slice_b), 
                slice_nz_begin_(slice_a));
    }

    //--------------------------------------------------------------------------------
    /**
     * Sets all the values in a given slice to a given, non-zero value. A value whose
     * abs is less than nta::Epsilon is a zero and will be ignored (this cannot be used
     * to set a slice to zero, which is not allowed).
     */
    inline void setSlice(size_type s, value_type val)
    {
      {
        NTA_ASSERT(s < nSlices());
        NTA_ASSERT(!isZero_(val));
      }

      if (!isZero_(val))
        std::fill(slice_nz_begin_(s), slice_nz_end_(s), val);
    }

    //--------------------------------------------------------------------------------
    /**
     * Adds a constant to the non-zeros in log space, in a given slice.
     * Values whose abs is less than minFloor are replaced by minFloor, so that
     * no new zero is introduced.
     */
    inline void logAddVal(size_type s, value_type val, value_type minFloor =0)
    {
      {
        NTA_ASSERT(s < nSlices());
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      if (!isZero_(minFloor)) {

        ST_R3_ITERATE_ON_SLICE_NZ {

          value_type a = *nz;
          value_type b = val;
          if (a < val) {
            b = a;
            a = val;
          } 
          value_type d = b - a;
          if (d >= minExp) {
            a += log1p_f(exp_f(d));
            if (abs_f(a) < minFloor) 
              a = minFloor;
            *nz = a;
          } else
            *nz = a;
        }
  
      } else {

        ST_R3_ITERATE_ON_SLICE_NZ {

          value_type a = *nz;
          value_type b = val;
          if (a < val) {
            b = a;
            a = val;
          } 
          value_type d = b - a;
          if (d >= minExp) {
            a += log1p_f(exp_f(d));
            *nz = a;
          } else
            *nz = a;
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Computes the sum of two slices that are in log space: a = log(exp(a) + exp(b)).
     * Values whose abs is less than minFloor are replaced by minFloor, so that
     * no new zero is introduced.
     */
    inline void logSum(size_type slice_a, size_type slice_b, value_type minFloor =0)
    {
      {
        NTA_ASSERT(slice_a < nSlices());
        NTA_ASSERT(slice_b < nSlices());
        NTA_ASSERT(slice_a != slice_b);
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      if (!isZero_(minFloor)) {

        ST_R3_ITERATE_ON_2_SLICES_NZ {

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
        }

      } else {

        ST_R3_ITERATE_ON_2_SLICES_NZ {

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
        }
      }
    }
    
    //--------------------------------------------------------------------------------
    /**
     * Computes the diff of two slices that are in log space: a = log(exp(a) - exp(b)).
     * Values whose abs is less than minFloor are replaced by minFloor, so that
     * no new zero is introduced.
     */
    inline void logDiff(size_type slice_a, size_type slice_b, value_type minFloor =0)
    {
      {
        NTA_ASSERT(slice_a < nSlices());
        NTA_ASSERT(slice_b < nSlices());
        NTA_ASSERT(slice_a != slice_b);
        NTA_ASSERT(minFloor == 0 || nta::Epsilon < minFloor);
      }

      // Important to use double here, because in float, there can be 
      // cancelation in log(1 - exp(b-a)), when a is very close to b.

      // Two log values that are this close to each other should generate a difference
      // of 0, which is -inf in log space, which we want to avoid
      double minDiff = -std::numeric_limits<double>::epsilon();

      if (!isZero_(minFloor)) {

        ST_R3_ITERATE_ON_2_SLICES_NZ {

          double a = *nz_a;
          double b = *nz_b;
          if (a < b)
            std::swap(a,b);
          double d = b - a;
          // If the values are too close to each other, generate log of 0 manually
          // We know d <= 0 at this point. 
          if (d >= minDiff)
            *nz_a = logOfZero;              
          else if (d >= minExp) {
            a += log1p_f(-exp_f(d));
            if (abs_f(a) < minFloor) 
              a = minFloor;
            *nz_a = a;
          } else {
            *nz_a = a;
          }
        }

      } else {

        ST_R3_ITERATE_ON_2_SLICES_NZ {

          double a = *nz_a;
          double b = *nz_b;
          if (a < b)
            std::swap(a,b);
          double d = b - a;
          // If the values are too close to each other, generate log of 0 manually
          // We know d <= 0 at this point. 
          if (d >= minDiff)
            *nz_a = logOfZero;              
          else if (d >= minExp) {
            a += log1p_f(-exp_f(d));
            *nz_a = a;
          } else {
            *nz_a = a;
          }
        }
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * Algorithm to compute piPrime in loopy belief propagation, for a given slice.
     *
     * The net operation performed is prod(col)/element, but it is performed in log mode
     * and the mat argument is assumed to have already been converted to log mode. 
     * All values within mat are between 0 and 1 in normal space (-inf and -epsilon in 
     * log space).
     *
     * This does a sum of each column, then places colSum-element into each
     * location, insuring that no new zeros are introduced. Any result that 
     * would have computed to 0 (within maxFloor) will be replaced with maxFloor
     */
    inline void piPrime_old(size_type s, value_type maxFloor)
    {
      {
        NTA_ASSERT(s < nSlices());
        NTA_ASSERT(maxFloor < -nta::Epsilon);
      }

      colSums(s, buff_, buff_ + nCols());

      ST_R3_ITERATE_ON_SLICE 
        *nz = std::min(maxFloor, buff_[*ind] - *nz);
    }

    //--------------------------------------------------------------------------------
    /** 
     * A faster version of piPrime, but it requires more memory.
     * All the values in the fast slice are assumed to be < -nta::Epsilon.
     */
    inline void piPrime(value_type maxFloor)
    {
      {
        NTA_ASSERT(c_offsets_ && c_ind_ && c_ptrs_);
        NTA_ASSERT(maxFloor < -nta::Epsilon);
      }

      for (size_type c = 0; c != nCols(); ++c) {

        size_type nnzc = nNonZerosOnCol(c);

        if (nnzc == 0)
          continue;
        
        value_type **begin = fast_slice_col_begin(c);
        value_type **it = begin;
        value_type **end = fast_slice_col_end(c);
        value_type sum = 0;

        for (it = begin; it != end; ++it) 
          sum += **it;

        for (it = begin; it != end; ++it)
          **it = std::min(maxFloor, sum - **it);
      }
    }
   
    //--------------------------------------------------------------------------------
    /**
     * A modified version of piPrime that sums only a limited number of the elements
     * of each col.
     *
     * Think of each column of the feedback matrix (the input to the piPrime calculation) 
     * as representing the feedback from the parents to the inputs. When multiple parents 
     * are active, we need to share the input's strength among them. This is done by 
     * computing the following for each parent of the input:
     *
     * piPrime going to parent j = product(parent[i].negativeFeedback for each i != j)
     *
     * The above is the piPrime value for an input going to parent j. When the piPrime 
     * value is high (near 1), then this results in all of the input's strength going to 
     * that parent (this comes into play in the bottom-up computations which come after 
     * the piPrime calculation). When the piPrime value is low (near 0), then this results 
     * in essentially none of the input's strength going to the parent.
     * 
     * The new piPrime calculation with the maxPiPrimeOutputs parameter says that instead 
     * of considering the strength of ALL of the input's parents, we can consider just 
     * the top N active parents. The top N active parents are the ones with the *lowest* 
     * negative feedback values. So, this is why we want to only consider the lowest N 
     * values in each column. Doing this lets as avoid some potential precision issues 
     * which can occur if we have too many parents for an input and the product of all 
     * those parents' negative feedback values can get too small for our available 
     * precision.
     * 
     * For a rationale on a biological level, you can think of a neuron as basically 
     * responding only to it's N strongest inputs.
     */

    /**
     * Caches for topNPiPrime:
     * 
     * For each column, cache pointers to top-N activations that we 
     * want to use.
     */
    /*
    std::vector<std::vector<value_type*> > topN;
    bool topNPiPrime_fast_reset;

    //--------------------------------------------------------------------------------
    inline void resetTopNPiPrimeCache()
    {
      topN.clear();
    }

    //--------------------------------------------------------------------------------
    inline void topNPiPrime(size_type s, value_type maxFloor, size_type N)
    {
      {
        NTA_ASSERT(s < nSlices());
        NTA_ASSERT(maxFloor < -nta::Epsilon);
        NTA_ASSERT(0 < N);
      }

      typedef typename std::pair<value_type*, value_type> P;
      typedef typename nta::less_2nd<value_type*, value_type> Order2nd;

      //value_type absFloor = abs_f(maxFloor);
      
      // Initialize data structures to iterate down the columns faster
      if (!c_offsets_)
        initialize_col_nz_();

      // Initialize caches that contain colum indices of top-N activations
      // for each column
      if (topN.empty()) {

        topN.resize(nCols());

        for (size_type c = 0; c != nCols(); ++c) {

          if (nNonZerosOnCol(c) == 0)
            continue;

          // sort only if more than N non-zeros
          std::vector<P> col;
          size_type *col_ind = col_ind_begin_(c);
          size_type *col_end = col_ind_end_(c);
          value_type *slice = slice_nz_begin_(s);
          
          for (; col_ind != col_end; ++col_ind) {
            value_type *ptr = slice + *col_ind;
            col.push_back(std::make_pair(ptr, *ptr));
          }

          size_type N_eff = std::min(N, nNonZerosOnCol(c));
          std::partial_sort(col.begin(), col.begin() + N_eff, col.end(), Order2nd());

          for (size_type i = 0; i != N_eff; ++i) 
            topN[c].push_back(col[i].first);
            
          std::sort(topN[c].begin(), topN[c].end());
        }
      }

      // Now, for each column, we can work with the top-N activations only
      for (size_type c = 0; c != nCols(); ++c) {

        if (nNonZerosOnCol(c) == 0)
          continue;

        const std::vector<value_type*>& topN_ind = topN[c];
        typename std::vector<value_type*>::const_iterator it;
        value_type sum = 0;

        for (it = topN_ind.begin(); it != topN_ind.end(); ++it)
          sum += **it;

        size_type *col_ind = col_ind_begin_(c);
        size_type *col_end = col_ind_end_(c);
        value_type *slice = slice_nz_begin_(s);

        for (; col_ind != col_end; ++col_ind) {
          value_type *ptr = slice + *col_ind;
          if (std::find(topN_ind.begin(), topN_ind.end(), ptr) != topN_ind.end())
            *ptr = sum - *ptr;
          else
            *ptr = sum;
        }
      }          
      
      ST_R3_ITERATE_ON_SLICE_NZ 
        if (*nz > maxFloor)
          *nz = maxFloor;
    }
    */

    //--------------------------------------------------------------------------------
    /**
     * The tie-breaker is useful when unit testing by comparing to argsort's behavior
     * in Python. 
     */
    struct less_ptr : public std::binary_function<bool, value_type*, value_type*>
    {
      inline bool operator()(value_type* a, value_type* b) const
      {
        if (*a < *b)
          return true;
        else if (fabs(*a - *b) < nta::Epsilon)
          if (a < b)
            return true;
        return false;
      }
    };
    
    //--------------------------------------------------------------------------------
    inline void resetTopNPiPrime(size_type topN)
    {
      {
        NTA_ASSERT(c_offsets_ && c_ind_ && c_ptrs_);
        NTA_ASSERT(0 < topN && topN <= nCols());
      }
      
      for (size_type c = 0; c != nCols(); ++c) {
        
        size_type nnzc = nNonZerosOnCol(c);

        if (nnzc <= topN) 
          continue;
        
        value_type **begin = fast_slice_col_begin(c);
        value_type **end = fast_slice_col_end(c);
        
        std::partial_sort(begin, begin + topN, end, less_ptr());
      }
    }

    //--------------------------------------------------------------------------------
    /**
     * All the values in the fast slice are assumed to be < -nta::Epsilon.
     */
    inline void topNPiPrime(value_type maxFloor, size_type topN)
    {
      {
        NTA_ASSERT(c_offsets_ && c_ind_ && c_ptrs_);
        NTA_ASSERT(0 < topN && topN <= nCols());
        NTA_ASSERT(maxFloor < -nta::Epsilon);
      }

      for (size_type c = 0; c != nCols(); ++c) {

        size_type nnzc = nNonZerosOnCol(c);
        
        if (nnzc == 0)
          continue;

        size_type N_eff = std::min(topN, nnzc);
        value_type **begin = fast_slice_col_begin(c);
        value_type **it = begin;
        value_type **end1 = it + N_eff;
        value_type **end2 = fast_slice_col_end(c);
        value_type sum = 0;
        
        for (it = begin; it != end1; ++it)
          sum += **it;

        NTA_ASSERT(sum <= maxFloor);

        for (it = begin; it != end1; ++it)
          **it = std::min(maxFloor, sum - **it);
        
        for (it = end1; it != end2; ++it)
          **it = sum;
      }          
    }

    //--------------------------------------------------------------------------------
    /**
     * For debugging, prints various technical information, for developers consumption
     * rather than average user.
     *
     * Can't use the name "print" itself as this will be wrapped automatically 
     * and "print" is reserved in Python.
     */
    inline void printDebug() const
    {
      std::cout << nrows_ << " " << ncols_ << " " << nslices_ << " "
                << nnzps_ << std::endl;
      std::cout << std::endl;

      for (size_type s = 0; s != nslices_; ++s) {
        ST_R3_ITERATE_ON_ALL_ROWS {
          ST_R3_ITERATE_ON_ROW {
            std::cout << *ind << "," << *nz << " ";
          }
          std::cout << std::endl;
        }
        std::cout << std::endl;
      }

      if (c_offsets_) {
        for (size_type c = 0; c != ncols_; ++c) {
          size_type *it = col_ind_begin_(c), *end = col_ind_end_(c);
          for (; it != end; ++it)
            std::cout << *it << " ";
          std::cout << std::endl;
        }
      }
    }
  
  private:
    //--------------------------------------------------------------------------------
    /**
     * This function decides which values will be regarded as zero (this is the same
     * logic as in SparseMatrix, and indeed throughout nta/math and nta/algorithms).
     */
    inline bool isZero_(value_type x) const
    {
      return fabs(x) < nta::Epsilon;
    }

    //--------------------------------------------------------------------------------
    /**
     * Methods used to validate indices in debug mode.
     */
    inline size_type 
    assert_valid_slice_index_(size_type s, const char* where) const
    {
      NTA_ASSERT(s < nSlices())
        << "SparseR3FTensor: " << where
        << ": Invalid slice index: " << s
        << " when number of slices is: " << nSlices();
      return s;
    }

    inline row_index_type 
    assert_valid_row_index_(row_index_type r, const char* where) const
    {
      NTA_ASSERT(r < nRows())
        << "SparseR3FTensor: " << where
        << ": Invalid row index: " << r
        << " when number of rows is: " << nRows();
      return r;
    }

    inline col_index_type 
    assert_valid_col_index_(col_index_type c, const char* where) const
    {
      NTA_ASSERT(c < nCols())
        << "SparseR3FTensor: " << where
        << ": Invalid col index: " << c
        << " when number of cols is: " << nCols();
      return c;
    }

    //--------------------------------------------------------------------------------
    /**
     * Methods used to access slices and rows.
     */
    inline col_index_type* ind_begin_(row_index_type r) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_row_index_(r, "ind_begin_");
#endif

      return ind_mem_ + (r == 0 ? 0 : offsets_[r-1]);
    }

    //--------------------------------------------------------------------------------
    inline col_index_type* ind_end_(row_index_type r) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_row_index_(r, "ind_end_");
#endif
      
      return ind_begin_(r) + nNonZerosOnRow(r);
    }

    //--------------------------------------------------------------------------------
    inline value_type* nz_begin_(size_type s, row_index_type r) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_slice_index_(s, "nz_begin_");
      assert_valid_row_index_(r, "nz_begin_");
#endif

      return nz_mem_ + s * nNonZerosPerSlice() + (r == 0 ? 0 : offsets_[r-1]);
    }

    //--------------------------------------------------------------------------------
    inline value_type* nz_end_(size_type s, row_index_type r) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_slice_index_(s, "nz_end_");
      assert_valid_row_index_(r, "nz_end_");
#endif

      return nz_begin_(s, r) + nNonZerosOnRow(r);
    }

    //--------------------------------------------------------------------------------
    inline value_type* slice_nz_begin_(size_type s) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_slice_index_(s, "slice_nz_begin_");
#endif

      return nz_mem_ + s * nNonZerosPerSlice();
    }

    //--------------------------------------------------------------------------------
    inline value_type* slice_nz_end_(size_type s) const
    {
#ifdef NTA_ASSERTIONS_ON
      assert_valid_slice_index_(s, "slice_nz_end_");
#endif

      return nz_mem_ + (s + 1) * nNonZerosPerSlice();
    }

    //--------------------------------------------------------------------------------
    /**
     * This works only if c_offsets_ has been initialized!
     */
    inline size_type nNonZerosOnCol(col_index_type c) const
    {
#ifdef NTA_ASSERTIONS_ON
      NTA_ASSERT(c_offsets_);
      assert_valid_col_index_(c, "nNonZerosOnCol");
#endif
      
      return c == 0 ? c_offsets_[0] : c_offsets_[c] - c_offsets_[c-1];
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns pointer to beginning of indices for non-zeros in given col.
     * This works only if c_offsets_ and c_ind_ have been initialized!
     */
    inline size_type* col_ind_begin_(size_type c) const
    {
#ifdef NTA_ASSERTIONS_ON
      {
        NTA_ASSERT(c_offsets_);
        assert_valid_col_index_(c, "col_ind_begin_");
      }
#endif
      
      return c == 0 ? c_ind_ : c_ind_ + c_offsets_[c-1];
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns pointer to one past the end of indices for non-zeros in given col.
     * This works only if c_offsets_ and c_ind_ have been initialized!
     */
    inline size_type* col_ind_end_(size_type c) const
    {
#ifdef NTA_ASSERTIONS_ON
      {
        NTA_ASSERT(c_offsets_);
        assert_valid_col_index_(c, "col_ind_end_");
      }
#endif
      
      return col_ind_begin_(c) + nNonZerosOnCol(c);
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns pointer to beginning of pointers for fast slice at given col.
     */
    inline value_type** fast_slice_col_begin(size_type c) const
    {
#ifdef NTA_ASSERTIONS_ON
      {
        NTA_ASSERT(c_ptrs_);
        NTA_ASSERT(c_offsets_);
        assert_valid_col_index_(c, "fast_slice_col_begin");
      }
#endif

      return c == 0 ? c_ptrs_ : c_ptrs_ + c_offsets_[c-1];
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns pointer to one past the end of pointers for fast slice at given col.
     */
    inline value_type** fast_slice_col_end(size_type c) const
    {
#ifdef NTA_ASSERTIONS_ON
      {
        NTA_ASSERT(c_ptrs_);
        NTA_ASSERT(c_offsets_);
        assert_valid_col_index_(c, "fast_slice_col_end");
      }
#endif

      return fast_slice_col_begin(c) + nNonZerosOnCol(c);
    }

  public:
    //--------------------------------------------------------------------------------
    /**
     * Initialize number of non-zeros per column and offsets to non-zeros down 
     * the columns. Allocates extra data structures. The extra allocations cost:
     * (nCols() + nNonZerosPerSlice()) * sizeof(size_type) bytes.
     *
     * When this is called, it will require extra memory while computing (for tmp).
     * That temporary memory costs: nNonZerosPerSlice() * sizeof(size_type) bytes.
     *
     * TODO: remove tmp. It should be possible to compute c_ind_ without tmp.
     */
    inline void initialize_col_nz_() 
    {
      // Can be called from initializeFromDense, that can be called 
      // to re-initialize object.
      if (c_offsets_) {
        delete [] c_offsets_;
        delete [] c_ind_;
        delete [] c_ptrs_;
      }

      std::vector<std::vector<size_type> > tmp(nCols());

      // Relies on indices of non-zeros being sorted in ind_mem_:
      // we iterate on ind_mem_ row by row, compute the displacement
      // of the current non-zero from the beginning of ind_mem, and store
      // that in the vector corresponding to the column of the non-zero.
      col_index_type *ind = ind_mem_, *ind_end = ind + nNonZerosPerSlice();
      for (; ind != ind_end; ++ind) 
        tmp[*ind].push_back((size_type)(ind - ind_mem_));
      
      // c_offsets_ stores offsets to the beginning of the indices 
      // of the non-zeros for each column. 
      // c_ind_ stores the indices of the non-zeros down each column.
      c_offsets_ = new size_type [nCols()];
      c_ind_ = new size_type [nNonZerosPerSlice()];

      // We store the number of non-zeros per column in c_offsets_
      // and the position of each non-zero when going down the columns
      // c_ind_.
      size_type *it = c_ind_;
      for (size_type i = 0; i != nCols(); ++i) {
        c_offsets_[i] = tmp[i].size();
        for (size_type j = 0; j != tmp[i].size(); ++j) 
          *it++ = tmp[i][j];
      }

      // Post-process c_offsets_ so that it contains the number of non-zeros 
      // up to that column, rather than the number of non-zeros on the column:
      // this is more useful when retrieving the non-zeros later.
      for (size_type i = 1; i != nCols(); ++i)
        c_offsets_[i] += c_offsets_[i-1];

      // Initialize pointers for fast slice: store them contiguously in an array,
      // by columns. The number of pointers/non-zeros per column can be obtained
      // with nNonZerosOnCol(col).
      c_ptrs_ = new value_type* [nNonZerosPerSlice()];
      value_type **i = c_ptrs_;
      value_type *slice = slice_nz_begin_(0);
      
      for (size_type c = 0; c != nCols(); ++c) {
        
        size_type *col_ind = col_ind_begin_(c);
        size_type *col_end = col_ind_end_(c);
        
        for (; col_ind != col_end; ++col_ind) 
          *i++ = slice + *col_ind;
      }
      
      { // Post-conditions
        NTA_ASSERT(c_offsets_ && c_ind_ && c_ptrs_);
        NTA_ASSERT(c_offsets_[ncols_ - 1] == nNonZerosPerSlice());
      } // End post-conditions
    }

    //--------------------------------------------------------------------------------
  private:
    SparseR3FTensor(const SparseR3FTensor&);
    SparseR3FTensor& operator=(const SparseR3FTensor&);
  };
  
  //--------------------------------------------------------------------------------
}; // end namespace nta

#endif //NTA_SPARSE_R3F_TENSOR_HPP
