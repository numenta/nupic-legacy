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
 * Declaration of class DenseMatrix
 */

//----------------------------------------------------------------------

#ifndef NTA_DENSE_MATRIX_HPP
#define NTA_DENSE_MATRIX_HPP

#include <vector>

#include <nta/utils/TRandom.hpp>
#include <nta/math/SparseMatrix.hpp>


namespace nta {

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename Int, typename Float>
  struct Dense
  {
    typedef std::vector<Float> Memory;
    typedef typename Memory::iterator iterator;
    typedef typename Memory::const_iterator const_iterator;

    Int nrows, ncols;
    Memory m;
    
    Dense(Int nr = 0, Int nc = 0)
      : nrows(nr), ncols(nc), m(nr*nc, 0)
    {}

    Dense(Int nr, Int nc, Int nzr, bool small =false, bool emptyRows =false, 
	  TRandom* r = 0)
      : nrows(nr), ncols(nc),
        m(nr*nc, 0)
    {
      if (small)
      {
        NTA_CHECK(r != 0) 
	  << "Random number generator required for Dense() constructor"
	  << " when small is true";
      }
      ITER_2(nrows, ncols)
        if (!small) {
          at(i,j) = Real(10*i+j+1); // none zero, positive
        } else {
          at(i,j) = 5 * nta::Epsilon * r->getReal64();
          if (nta::nearlyZero(at(i,j)))
            at(i,j) = 0.0;
        }
      
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

    ~Dense() {}

  
    inline iterator begin() { return m.begin(); }
    inline const_iterator begin() const { return m.begin(); }
    inline iterator begin(const Int i) { return m.begin() + i*ncols; }
    inline const_iterator begin(const Int i) const { return m.begin() + i*ncols; }
    
    // row i, column j
    inline Float& at(const Int i, const Int j) 
    {
      return *(m.begin() + i*ncols + j);
    }

    inline const Float& at(const Int i, const Int j) const
    {
      return *(m.begin() + i*ncols + j);
    }

    inline void copy(const Dense& other)
    {
      nrows = other.nrows;
      ncols = other.ncols;
      std::vector<Float> new_m(other.m);
      std::swap(m, new_m);
    }

    template <typename InIter>
    inline void addRow(InIter begin)
    {
      Int nrows_new = nrows + 1;
      std::vector<Float> new_m(nrows_new * ncols);
      for (Int i = 0; i < nrows; ++i) 
	for (Int j = 0; j < ncols; ++j) 
	  new_m[i*ncols+j] = at(i,j);
      Int k = nrows*ncols;
      for (Int j = 0; j < ncols; ++j, ++begin)
	new_m[k+j] = *begin;
      std::swap(m, new_m);
      nrows = nrows_new;
    }
    
    template <typename InIter>
    inline void deleteRows(InIter del, InIter del_end)
    {
      Int nrows_new = nrows - (del_end - del);
      std::set<Int> del_set(del, del_end);
      std::vector<Float> new_m(nrows_new * ncols);
      Int i1 = 0;
      for (Int i = 0; i < nrows; ++i) {
        if (del_set.find(i) == del_set.end()) {
          for (Int j = 0; j < ncols; ++j) 
            new_m[i1*ncols + j] = at(i,j);
          ++i1;
        }
      }
      std::swap(m, new_m);
      nrows = nrows_new;
    }

    template <typename InIter>
    inline void deleteCols(InIter del, InIter del_end)
    {
      Int ncols_new = ncols - (del_end - del);
      std::set<Int> del_set(del, del_end);
      std::vector<Float> new_m(nrows * ncols_new);
      Int j1 = 0;
      for (Int j = 0; j < ncols; ++j) {
        if (del_set.find(j) == del_set.end()) {
          for (Int i = 0; i < nrows; ++i) 
            new_m[i*ncols_new + j1] = at(i,j);
          ++j1;
        }
      }
      std::swap(m, new_m);
      ncols = ncols_new;
    }

    inline void resize(const Int new_nrows, const Int new_ncols)
    {
      std::vector<Float> new_m(new_nrows * new_ncols);
      Int row_m = std::min(new_nrows, nrows);
      Int col_m = std::min(new_ncols, ncols);
      ITER_2(row_m, col_m)
	new_m[i*new_ncols + j] = at(i,j);
      std::swap(m, new_m);
      nrows = new_nrows;
      ncols = new_ncols;
    }

    inline void setRowToZero(Int row)
    {
      for (Int j = 0; j != ncols; ++j)
	at(row,j) = 0;
    }

    inline void setColToZero(Int col)
    {
      for (Int i = 0; i != nrows; ++i)
	at(i,col) = 0;
    }

    void fromCSR(std::stringstream& stream)
    {
      std::string tag;
      stream >> tag;
      Int nnz, nnzr, j;
      Float val;
      stream >> nrows >> ncols >> nnz;

      m.resize(nrows*ncols);
      std::fill(m.begin(), m.end(), Real(0));

      for (Int i = 0; i < nrows; ++i) {
        stream >> nnzr;
        for (Int k = 0; k < nnzr; ++k) {
          stream >> j >> val;
          if (!nta::nearlyZero(val))
            at(i,j) = val;
          else
            at(i,j) = 0;
        }
      }
    }

    void clear()
    {
      std::fill(m.begin(), m.end(), Real(0));
    }

    //--------------------------------------------------------------------------------
    // TESTS
    //--------------------------------------------------------------------------------

    bool isZero() const
    {
      ITER_1(nrows*ncols)
        if (!nta::nearlyZero(m[i]))
          return false;
      return true;
    }

    inline Int nRows(){ return nrows;}
    inline Int nCols(){ return ncols;}

    Int nNonZerosOnRow(Int row) const
    {
      Int n = 0;
      ITER_1(ncols)
        if (!nta::nearlyZero(at(row,i)))
          ++n;
      return n;
    }

    Int nNonZerosOnCol(Int col) const
    {
      Int n = 0;
      ITER_2(nrows, ncols)
	if (!nta::nearlyZero(at(i,j)) && j == col)
	  ++n;
      return n;
    }

    bool isRowZero(Int row) const
    {
      return nNonZerosOnRow(row) == 0;
    }

    bool isColZero(Int col) const
    {
      return nNonZerosOnCol(col) == 0;
    }
    
    Int nNonZeros() const
    {
      Int n = 0;
      ITER_1(nrows)
	n += nNonZerosOnRow(i);
      return n;
    }

    template <typename OutIter>
    void nNonZerosPerRow(OutIter it) const
    {
      ITER_1(nrows) 
	*it++ = nNonZerosOnRow(i);
    }

    template <typename OutIter>
    void nNonZerosPerCol(OutIter it) const
    {
      std::fill(it, it + ncols, 0);

      ITER_2(nrows, ncols) 
	if (!nta::nearlyZero(at(i,j)))
	  *(it + j) += 1;
    }

    //--------------------------------------------------------------------------------

    void transpose(Dense<Int, Float>& tr) const
    {
      ITER_2(nrows, ncols)
        tr.at(j,i) = at(i,j);
    }

    template <typename InIter, typename OutIter>
    void vecMaxProd(InIter x, OutIter y) const
    {
      for (Int i = 0; i < nrows; ++i) {
        Float max = - std::numeric_limits<Float>::max();
        for (Int j = 0; j < ncols; ++j) {
          Float val = at(i,j) * x[j];
          if (val > max) 
            max = val;
        }
        y[i] = max;
      }
    }

    template <typename InIter, typename OutIter>
    void rightVecProd(InIter x, OutIter y) const
    {
      for (Int i = 0; i < nrows; ++i) {
        Float s = 0;
        for (Int j = 0; j < ncols; ++j)
          s += at(i,j) * x[j];
        y[i] = s;
      }
    }

    template <typename InIter>
    Float rowLpDist(Float p, Int row, InIter x, bool take_root =false) const
    {
      if (p == 0.0) 
	return rowL0Dist(row, x);

      Float val = 0;
      for (Int j = 0; j != ncols; ++j) 
        val += ::pow(::fabs(x[j] - at(row,j)), p);
      if (take_root)
	val = ::pow(val, 1.0/p);
      return val;
    }  

    template <typename InIter>
    Float rowL0Dist(Int row, InIter x) const
    {
      Float val = 0;
      for (Int j = 0; j != ncols; ++j) 
        val += ::fabs(x[j] - at(row,j)) > nta::Epsilon;
      return val;
    }

    template <typename InIter>
    Float rowLMaxDist(Int row, InIter x) const
    {
      Float val = 0;
      for (Int j = 0; j != ncols; ++j) 
        val = std::max(::fabs(x[j] - at(row,j)), val);
      return val;
    }

    template <typename InIter, typename OutIter>
    void LpDist(Float p, InIter x, OutIter y, bool take_root =false) const
    {
      if (p == 0.0) {
	L0Dist(x, y);
	return;
      }

      for (Int i = 0; i != nrows; ++i) {
        Float val = 0;
        for (Int j = 0; j != ncols; ++j) 
          val += ::pow(::fabs(x[j] - at(i,j)), p);
        y[i] = take_root ? ::pow(val, 1.0/p) : val;
      }
    }

    template <typename InIter, typename OutIter>
    void L0Dist(InIter x, OutIter y) const
    {
      for (Int i = 0; i != nrows; ++i) {
        Float val = 0;
        for (Int j = 0; j != ncols; ++j) 
          val += ::fabs(x[j] - at(i,j)) > nta::Epsilon;
        y[i] = val;
      }
    }

    template <typename InIter, typename OutIter>
    void LMaxDist(InIter x, OutIter y) const
    {
      for (Int i = 0; i != nrows; ++i) {
        Float val = 0;
        for (Int j = 0; j != ncols; ++j) 
	  val = std::max(val, ::fabs(x[j] - at(i,j)));
        y[i] = val;
      }
    }

    template <typename InIter, typename OutIter>
    inline void
    LpNearest(Float p, InIter x, OutIter nn, Int k =1, bool take_root =false) const
    {
      if (p == 0.0) {
	L0Nearest(x, nn, k);
	return;
      }

      std::vector<std::pair<Int, Float> > dists(nrows);

      for (Int i = 0; i != nrows; ++i) {
	dists[i].first = i;
	dists[i].second = 0;
      }

      for (Int i = 0; i < nrows; ++i) {
        Float val = 0;
        for (Int j = 0; j < ncols; ++j) 
          val += ::pow(::fabs(x[j] - at(i,j)), p);
        dists[i].second = take_root ? ::pow(val, 1.0/p) : val;
      }

      std::partial_sort(dists.begin(), dists.begin() + k, dists.end(), 
			predicate_compose<std::less<Float>, nta::select2nd<std::pair<Int, Float> > >());

      for (Int i = 0; i != nrows; ++i, ++nn) {
	nn->first = dists[i].first;
	nn->second = dists[i].second;
      }
    }

    template <typename InIter, typename OutIter>
    inline void
    L0Nearest(InIter x, OutIter nn, Int k =1, bool take_root =false) const
    {
      std::vector<std::pair<Int, Float> > dists(nrows);

      for (Int i = 0; i != nrows; ++i) {
	dists[i].first = i;
	dists[i].second = 0;
      }

      for (Int i = 0; i < nrows; ++i) {
        Float val = 0;
        for (Int j = 0; j < ncols; ++j) 
          val += ::fabs(x[j] - at(i,j)) > nta::Epsilon;
        dists[i].second = val;
      }

      std::partial_sort(dists.begin(), dists.begin() + k, dists.end(),  predicate_compose<std::less<Float>, nta::select2nd<std::pair<Int, Float> > >());

      for (Int i = 0; i != nrows; ++i, ++nn) {
	nn->first = dists[i].first;
	nn->second = dists[i].second;
      }
    }

    template <typename InIter, typename OutIter>
    inline void
    LMaxNearest(InIter x, OutIter nn, Int k =1, bool take_root =false) const
    {
      std::vector<std::pair<Int, Float> > dists(nrows);

      for (Int i = 0; i != nrows; ++i) {
	dists[i].first = i;
	dists[i].second = 0;
      }

      for (Int i = 0; i < nrows; ++i) {
        Float val = 0;
        for (Int j = 0; j < ncols; ++j) 
          val = std::max(val, ::fabs(x[j] - at(i,j)));
        dists[i].second = val;
      }

      std::partial_sort(dists.begin(), dists.begin() + k, dists.end(), 
			predicate_compose<std::less<Float>, nta::select2nd<std::pair<Int, Float> > >());

      for (Int i = 0; i != nrows; ++i, ++nn) {
	nn->first = dists[i].first;
	nn->second = dists[i].second;
      }
    }

    template <typename InIter>
    std::pair<Int, Float> dotNearest(InIter x) const
    {
      Float val, max_val = - std::numeric_limits<Float>::max();
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

    template <typename InIter>
    void axby(Int r, Float a, Float b, InIter x) 
    {
      for (Int j = 0; j < ncols; ++j)
        at(r,j) = a * at(r,j)  + b * x[j];

      threshold(r, nta::Epsilon);
    }  

    template <typename InIter>
    void axby(Float a, Float b, InIter x) 
    {
      ITER_2(nrows, ncols)
        at(i,j) = a * at(i,j)  + b * x[j];

      threshold(nta::Epsilon);
    }  

    template <typename InIter, typename OutIter>
    void xMaxAtNonZero(InIter x, OutIter y) const
    {
      for (Int i = 0; i < nrows; ++i) {
        Int arg_j = 0;
        Float max_val = - std::numeric_limits<Float>::max();
        for (Int j = 0; j < ncols; ++j)
          if (at(i,j) > 0 && x[j] > max_val) {
            arg_j = j;
            max_val = x[j];
          }
        y[i] = Float(arg_j);
      }
    }

    void normalizeRows(bool exact =false)
    {
      for (Int i = 0; i != nrows; ++i) {
	
        Float val = 0;
        bool oneMore = false;

        for (Int j = 0; j != ncols; ++j) 
          val += at(i,j);

        if (!nta::nearlyZero(val))
          for (Int j = 0; j != ncols; ++j) {
            at(i,j) /= val;
            if (nta::nearlyZero(at(i,j)))
              oneMore = true;
          }

        if (oneMore && exact) {

          threshold(i, nta::Epsilon);

          val = 0;

          for (Int j = 0; j != ncols; ++j) 
            val += at(i,j);

          if (!nta::nearlyZero(val))
            for (Int j = 0; j != ncols; ++j) 
              at(i,j) /= val;
        }
      }
    }

    void normalizeCols(bool exact =false)
    {
      for (Int j = 0; j != ncols; ++j) {
	
        Float val = 0;
        bool oneMore = false;

        for (Int i = 0; i != nrows; ++i) 
          val += at(i,j);

        if (!nta::nearlyZero(val))
          for (Int i = 0; i != nrows; ++i) {
            at(i,j) /= val;
            if (nta::nearlyZero(at(i,j))) {
	      at(i,j) = 0;
              oneMore = true;
	    }
          }

        if (oneMore && exact) {

          val = 0;

          for (Int i = 0; i != nrows; ++i) 
            val += at(i,j);

          if (!nta::nearlyZero(val))
            for (Int i = 0; i != nrows; ++i) 
              at(i,j) /= val;
        }
      }
    }

    template <typename InIter, typename OutIter>
    void rowProd(InIter x, OutIter y) const
    {
      for (Int i = 0; i < nrows; ++i) {
        Float val = 1.0;
        for (Int j = 0; j < ncols; ++j)
          if (at(i,j) > 0)
            val *= x[j];
        y[i] = val;
      }
    }

    void threshold(Int row, Float thres)
    {
      for (Int j = 0; j < ncols; ++j)
        if (::fabs(at(row,j)) <= thres)
          at(row,j) = 0;
    }

    void threshold(Float thres)
    {
      for (Int i = 0; i < nrows; ++i) 
        threshold(i, thres);
    }

    void lerp(Float a, Float b, const Dense<Int, Float>& B)
    {
      ITER_2(nrows, ncols)
	at(i,j) = a * at(i,j) + b * B.at(i,j);
      
      threshold(nta::Epsilon);
    }
   
    template <typename InIter, typename binary_functor>
    void apply(InIter x, binary_functor f)
    {
      ITER_2(nrows, ncols)
        at(i,j) = f(at(i,j), x[j]);
    }

    template <typename binary_functor>
    void apply(const Dense<Int, Float>& B, Dense<Int, Float>& C, binary_functor f)
    {
      ITER_2(nrows, ncols)
        C.at(i,j) = f(at(i,j), B.at(i,j));
    }
    
    template <typename binary_functor>
    Float accumulate_nz(const Int row, binary_functor f, const Float& init =0)
    {
      Float r = init;
      for (Int j = 0; j < ncols; ++j)
        if (!nta::nearlyZero(at(row,j)))
	  r = f(r, at(row,j));
      return r;
    }

    template <typename binary_functor>
    Float accumulate(const Int row, binary_functor f, const Float& init =0)
    {
      Float r = init;
      for (Int j = 0; j != ncols; ++j)
        r = f(r, at(row,j));
      return r;
    }
	
    void multiply(const Dense& B, Dense& C)
    {
      ITER_2(C.nrows, C.ncols) {
	C.at(i,j) = 0;
	for(Int k=0; k<ncols; k++) {
	  C.at(i,j) += at(i,k) * B.at(k,j);
	}
      }
    }

    inline void setZero(Int i, Int j)
    {
      at(i,j) = 0;
    }

    inline void setNonZero(Int i, Int j, const Float& val)
    {
      at(i,j) = val;
    }

    inline void set(Int i, Int j, const Float& val)
    {
      at(i,j) = val;
    }
  
    template <typename InIter>
    inline void add(Int row, InIter x)
    {
      for (Int j = 0; j < ncols; ++j)
	at(row, j) += *x++;
    }
  
    inline void add(const Dense& B)
    {
      for(Int i=0; i<nrows; i++)
	for(Int j=0; j<ncols; j++)
	  at(i,j) += B.at(i,j);
    }

    template <typename InIter, typename OutIter>
    inline void vecMaxAtNZ(InIter x, OutIter y) const
    {
      Float currentMax;
      
      for(Int i=0; i<nrows; i++) {
	currentMax=0;
	for(Int j=0; j<ncols; j++) {
	  if (at(i,j) > currentMax) 
	    currentMax = at(i,j);
	}
	*y = currentMax;
      }
    }
  
    template <typename InIter, typename OutIter>
    inline void rowProd(InIter x, OutIter y, Float lb) const
    {
      Float curProduct;
      InIter x_begin=x;
      
      for(Int i=0; i<nrows; i++) {
        curProduct=1;
	x = x_begin;
	for(Int j=0; j<ncols; j++) {
	  if (at(i,j) != 0)
	    curProduct *= *x;
	  x++;
	}
	
	if(curProduct<lb) {
	  *y = curProduct;
	} else {
	  *y = lb;
	}
	y++;
      }
    }

    template <typename OutIter>
    inline void getRowToDense(Int r, OutIter dense) const
    {
      for (Int j = 0; j != ncols; ++j)
	*dense++ = at(r,j);     
    }
    
    template <typename OutIter>
    inline void getColToDense(Int c, OutIter dense) const
    {
      for (Int i = 0; i != nrows; ++i)
	*dense++ = at(i,c);
    }

    template <typename OutIter1, typename OutIter2>
    inline void getRowToSparse(Int r, OutIter1 indIt, OutIter2 nzIt) const
    {
      for(Int j=0; j<ncols; j++) {
	if (at(r,j) != 0) {
	  *indIt++ = j;
	  *nzIt++ = at(r,j);
	}
      }
    }

    template <typename OutIter1, typename OutIter2>
    inline void getColToSparse(Int c, OutIter1 indIt, OutIter2 nzIt) const
    {
      for(Int j=0; j<nrows; j++) {
	if (at(j,c) != 0) {
	  *indIt++ = j;
	  *nzIt++ = at(j,c);
	}
      }
    }
    
    template <typename IndIt, typename NzIt>
    inline Int findRow(const Int nnzr, IndIt ind_it, NzIt nz_it)
    {
      IndIt ind_it_begin = ind_it, ind_it_end = ind_it+nnzr;
      NzIt nz_it_begin = nz_it;
      
      for (Int i=0; i<nrows; ++i) {
	ind_it = ind_it_begin;
	nz_it = nz_it_begin;
	while (ind_it != ind_it_end) {
	  if (at(i, *ind_it) != *nz_it)
	    break;
	  ++ind_it;
	  ++nz_it;
	}
	if (ind_it == ind_it_end)
	  return i;
      }
      
      return nrows;
    }

    inline void max(Int& max_i, Int& max_j, Float& max_val) const
    {
      max_i = 0, max_j = 0;
      max_val = - std::numeric_limits<Float>::max();

      ITER_2(nrows, ncols)
	if (!nta::nearlyZero(at(i,j)) && at(i,j) > max_val) {
	  max_val = at(i,j);
	  max_i = i;
	  max_j = j;
	}
      
      if (max_val == -std::numeric_limits<Float>::max())
	max_val = 0;
    }

    inline void min(Int& min_i, Int& min_j, Float& min_val) const
    {
      min_i = 0, min_j = 0;
      min_val = std::numeric_limits<Float>::max();

      ITER_2(nrows, ncols)
	if (!nta::nearlyZero(at(i,j)) && at(i,j) < min_val) {
	  min_val = at(i,j);
	  min_i = i;
	  min_j = j;
	}

      if (min_val == std::numeric_limits<Float>::max())
	min_val = 0;
    }

    template <typename Maxima>
    inline void rowMax(Maxima maxima) const
    {
      for (Int i = 0; i != nrows; ++i) {
	maxima[i].first = 0;
	maxima[i].second = - std::numeric_limits<Float>::max();
	for (Int j = 0; j != ncols; ++j) {
	  if (!nta::nearlyZero(at(i,j)) && at(i,j) > maxima[i].second) {
	      maxima[i].first = j;
	      maxima[i].second = at(i,j);
	  }
	}
      }
    }

    template <typename Minima>
    inline void rowMin(Minima minima) const
    {
      for (Int i = 0; i != nrows; ++i) {
	minima[i].first = 0;
	minima[i].second = std::numeric_limits<Float>::max();
	for (Int j = 0; j != ncols; ++j) {
	  if (!nta::nearlyZero(at(i,j)) && at(i,j) < minima[i].second) {
	    minima[i].first = j;
	    minima[i].second = at(i,j);
	  }
	}
      }
    }

    template <typename Maxima>
    inline void colMax(Maxima maxima) const
    {
      for (Int j = 0; j != ncols; ++j) {
	maxima[j].first = 0;
	maxima[j].second = - std::numeric_limits<Float>::max();
	for (Int i = 0; i != nrows; ++i) {
	  if (!nta::nearlyZero(at(i,j)) && at(i,j) > maxima[j].second) {
	    maxima[j].first = i;
	    maxima[j].second = at(i,j);
	  }
	}
	if (maxima[j].second == - std::numeric_limits<Float>::max())
	  maxima[j].second = 0;
      }
    }

    template <typename Minima>
    inline void colMin(Minima minima) const
    {
      for (Int j = 0; j != ncols; ++j) {
	minima[j].first = 0;
	minima[j].second = std::numeric_limits<Float>::max();
	for (Int i = 0; i != nrows; ++i) {
	  if (!nta::nearlyZero(at(i,j)) && at(i,j) < minima[j].second) {
	    minima[j].first = i;
	    minima[j].second = at(i,j);
	  }
	}
	if (minima[j].second == std::numeric_limits<Float>::max())
	  minima[j].second = 0;
      }
    }
  };

  //--------------------------------------------------------------------------------
  template <typename Int, typename Float>
  std::ostream& operator<<(std::ostream& out, const Dense<Int, Float>& d)
  {
    for (Int i = 0; i < d.nrows; ++i) {
      for (Int j = 0; j < d.ncols; ++j) 
        out << d.at(i,j) << " ";
      out << std::endl;
    }
    
    return out;
  }

  //--------------------------------------------------------------------------------
} // end namespace nta

#endif // NTA_DENSE_MATRIX_HPP
