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
 * Definition and implementation for SparseRLEMatrix
 */

#ifndef NTA_SPARSE_RLE_MATRIX_HPP
#define NTA_SPARSE_RLE_MATRIX_HPP

#include <sstream>
#include <cstdio>
#include <zlib.h>

#include <nta/math/math.hpp>

//--------------------------------------------------------------------------------
namespace nta {
  
  //--------------------------------------------------------------------------------
  /**
   * A matrix where only the positions and values of runs of non-zeros are stored.
   * Optionally compresses values using zlib (off by default).
   *
   * WATCH OUT! That the Index type doesn't become too small to store parameters
   * of the matrix, such as total number of non-zeros.
   * 
   * TODO: run length encode different values, which can be valuable when
   * quantizing vector components. This could be another data structure.
   */
  template <typename Index, typename Value>
  class SparseRLEMatrix
  {
  public:
    typedef unsigned long ulong_size_type;
    typedef Index size_type;
    typedef Value value_type;

  private:
    typedef typename std::vector<size_type> IndexVector;
    typedef typename std::vector<value_type> ValueVector;
    typedef typename std::pair<IndexVector, ValueVector> Row;

    bool compress_;
    std::vector<Row> data_;
    IndexVector indb_;
    ValueVector nzb_;
    std::vector<uLong> c_;

  public:
    //--------------------------------------------------------------------------------
    inline SparseRLEMatrix()
      : compress_(false),
	data_(),
	indb_(),
	nzb_(),
	c_()
    {}

    //--------------------------------------------------------------------------------
    inline SparseRLEMatrix(std::istream& inStream)
      : compress_(false),
	data_(),
	indb_(),
	nzb_(),
	c_()
    {
      fromCSR(inStream);
    }

    //--------------------------------------------------------------------------------
    template <typename InputIterator>
    inline SparseRLEMatrix(InputIterator begin, InputIterator end)
      : compress_(false),
	data_(),
	indb_(),
	nzb_(),
	c_()
    {
      fromDense(begin, end);
    }

    //--------------------------------------------------------------------------------
    inline ~SparseRLEMatrix()
    {
      data_.clear();
      indb_.clear();
      nzb_.clear();
      c_.clear();
    }

    //--------------------------------------------------------------------------------
    inline const std::string getVersion() const
    {
      return std::string("sm_rle_1.0");
    }

    //--------------------------------------------------------------------------------
    inline ulong_size_type capacity() const
    {
      ulong_size_type n = 0;
      for (size_type i = 0; i != data_.size(); ++i) 
	n += data_[i].second.capacity();
      return n;
    }

    //--------------------------------------------------------------------------------
    inline ulong_size_type nBytes() const
    {
      ulong_size_type n = sizeof(SparseRLEMatrix);
      n += data_.capacity() * sizeof(Row);
      for (size_type i = 0; i != nRows(); ++i)
	n += data_[i].first.capacity() * sizeof(size_type)
	  + data_[i].second.capacity() * sizeof(value_type);
      n += indb_.capacity() * sizeof(size_type);
      n += nzb_.capacity() * sizeof(value_type);
      n += c_.capacity() * sizeof(uLong);
      return n;
    }

    //--------------------------------------------------------------------------------
    inline bool isCompressed() const
    {
      return compress_;
    }

    //--------------------------------------------------------------------------------
    inline ulong_size_type nRows() const
    {
      return data_.size();
    }

    //--------------------------------------------------------------------------------
    inline size_type nCols() const
    {
      return indb_.size();
    }

    //--------------------------------------------------------------------------------
    inline size_type nNonZerosOnRow(ulong_size_type row) const
    {
      { // Pre-conditions
	NTA_ASSERT(0 <= row && row < nRows())
	  << "SparseRLEMatrix::nNonZerosOnRow: "
	  << "Invalid row index: " << row;
      } // End pre-conditions

      size_type n = 0;
      for (size_type j = 1; j < data_[row].first.size(); j += 2) 
	n += data_[row].first[j] - data_[row].first[j-1];
      return n;
    }

    //--------------------------------------------------------------------------------
    inline ulong_size_type nNonZeros() const
    {
      ulong_size_type n = 0;
      for (ulong_size_type i = 0; i != data_.size(); ++i)
	n += nNonZerosOnRow(i);
      return n;
    }

    //--------------------------------------------------------------------------------
    /**
     * Adjusts the size of the internal vectors so that their capacity matches
     * their size.
     */
    inline void compact()
    {
      if (capacity() == nNonZeros() 
	  && data_.capacity() == data_.size()
	  && indb_.capacity() == indb_.size())
	return;

      std::stringstream buffer;
      toCSR(buffer);
      clear();
      fromCSR(buffer);

      NTA_ASSERT(capacity() == nNonZeros());
    }

    //--------------------------------------------------------------------------------
    /**
     * Compress data using compression algorithm.
     */
    inline void compressData()
    {
      if (compress_)
	return;

      if (c_.empty())
	c_.resize(nRows(), 0);

      for (ulong_size_type i = 0; i != nRows(); ++i)
	compressRow_(i);

      compress_ = true;
    }

    //--------------------------------------------------------------------------------
    inline void decompressData()
    {
      if (!compress_)
	return;

      if (c_.empty())
	c_.resize(nRows(), 0);
      
      for (ulong_size_type i = 0; i != nRows(); ++i) {
	uLongf dstLen = decompressRow_(i);
	size_type n = dstLen / sizeof(value_type);
	ValueVector new_vector(nzb_.begin(), nzb_.begin() + n);
	data_[i].second.swap(new_vector);
	c_[i] = 0;
      }

      compress_ = false;
    }

    //--------------------------------------------------------------------------------
    /**
     * Deallocates memory used by this instance.
     */
    inline void clear()
    {
      std::vector<Row> empty;
      data_.swap(empty);
      IndexVector empty_indb;
      indb_.swap(empty_indb);
      ValueVector empty_nzb;
      nzb_.swap(empty_nzb);
      std::vector<uLong> empty_c;
      c_.swap(empty_c);
      compress_ = false;

      NTA_ASSERT(nBytes() == sizeof(SparseRLEMatrix));
    }

    //--------------------------------------------------------------------------------
    /**
     * Appends a row to this matrix.
     */
    template <typename InputIterator>
    inline void 
    appendRow(InputIterator begin, InputIterator end)
    {
      { // Pre-conditions
	NTA_ASSERT(begin <= end)
	  << "SparseRLEMatrix::appendRow: "
	  << "Invalid range";
      } // End pre-conditions

      // Resize matrix if needed
      if (indb_.size() < (size_type)(end - begin)) {
	size_type ncols = (size_type) (end - begin);
	indb_.resize(ncols);
	nzb_.resize(ncols);
      }
	  
      typename IndexVector::iterator indb = indb_.begin();
      typename ValueVector::iterator nzb = nzb_.begin();
      InputIterator it = begin;
      
      // Find positions and values of non-zeros
      while (it != end) {
	while (it != end && nta::nearlyZero(*it))
	  ++it;
	if (it != end) {
	  *indb++ = (size_type)(it - begin);
	  while (it != end && !nta::nearlyZero(*it))
	    *nzb++ = (value_type) *it++;
	  *indb++ = (size_type)(it - begin);
	}
      }

      data_.resize(data_.size() + 1);
      Row& row = data_[data_.size() - 1];
      IndexVector& ind = row.first;
      ValueVector& nz = row.second;
      size_type ind_size = (size_type)(indb - indb_.begin());
      size_type nz_size = (size_type)(nzb - nzb_.begin());
      ind.reserve(ind_size);
      nz.reserve(nz_size);
      ind.insert(ind.end(), indb_.begin(), indb_.begin() + ind_size);
      nz.insert(nz.end(), nzb_.begin(), nzb_.begin() + nz_size);
      c_.push_back(0);

      if (compress_)
	compressRow_(data_.size()-1);
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    inline void 
    getRowToDense(ulong_size_type r, OutputIterator begin, OutputIterator end) const
    {
      { // Pre-conditions
	NTA_ASSERT(0 <= r && r < nRows())
	  << "SparseRLEMatrix::getRow: "
	  << "Invalid row index: " << r;

	NTA_ASSERT((size_type)(end - begin) == nCols())
	  << "SparseRLEMatrix::getRow: "
	  << "Not enough memory";
      } // End pre-conditions
   
      const Row& row = data_[r];
      const IndexVector& ind = row.first;
      size_type n = ind.size();
      typename ValueVector::const_iterator nz;

      if (compress_) {
	const_cast<SparseRLEMatrix&>(*this).decompressRow_(r);
	nz = nzb_.begin();
      } else 
	nz = data_[r].second.begin();
      
      size_type j = 0;
      for (size_type i = 0; i+1 < n; i += 2) {
	for (; j != ind[i]; ++j)
	  *(begin + j) = (value_type) 0;
	for (; j != ind[i+1]; ++j) 
	  *(begin + j) = *nz++;
      }
      for (; j < nCols(); ++j)
	*(begin + j) = (value_type) 0;
    }

    //--------------------------------------------------------------------------------
    /**
     * Returns index of first row within <distance> of argument, or nRows() if none.
     */
    template <typename InputIterator>
    inline ulong_size_type 
    firstRowCloserThan(InputIterator begin, InputIterator end, nta::Real32 distance) const
    {
      {
	NTA_ASSERT(begin <= end);
      }
      
      nta::Real32 d2 = distance * distance;

      for (ulong_size_type r = 0; r != nRows(); ++r) {

	const Row& row = data_[r];
	const IndexVector& ind = row.first;
	size_type n = ind.size();
	typename ValueVector::const_iterator nz;
	
	if (compress_) {
	  const_cast<SparseRLEMatrix&>(*this).decompressRow_(r);
	  nz = nzb_.begin();
	} else {
	  nz = data_[r].second.begin();
	}

	nta::Real32 d = 0;
	size_type j = 0;
	for (size_type i = 0; i+1 < n && d < d2; i += 2) {
	  for (; j != ind[i]; ++j)
	    d += *(begin + j) * *(begin + j);
	  for (; j != ind[i+1] && d < d2; ++j) {
	    nta::Real32 v = *(begin + j) - *nz++;
	    d += v * v;
	  }
	}
	for (; j < nCols() && d < d2; ++j)
	  d += *(begin + j) * *(begin + j);
	
	if (d < d2)
	  return r;
      }

      return nRows();
    }

    //--------------------------------------------------------------------------------
    inline ulong_size_type CSRSize() const
    {
      char buffer[32];

      std::stringstream b;
      b << getVersion() << " "
	<< nRows() << " " << nCols() << " "
	<< (compress_ ? "1" : "0") << " ";

      ulong_size_type n = b.str().size();
      
      for (ulong_size_type row = 0; row != nRows(); ++row) {

	size_type n1 = data_[row].first.size();
	n += sprintf(buffer, "%d ", n1);

	for (size_type j = 0; j != n1; ++j) 
	  n += sprintf(buffer, "%d ", data_[row].first[j]);
	
	if (compress_) {
	  const_cast<SparseRLEMatrix&>(*this).decompressRow_(row);
	  ulong_size_type n2 = nNonZerosOnRow(row);
	  for (size_type j = 0; j != n2; ++j) 
	    n += sprintf(buffer, "%.15g ", (double) nzb_[j]);
	} else {
	  ulong_size_type n2 = nNonZerosOnRow(row);
	  for (size_type j = 0; j != n2; ++j) 
	    n += sprintf(buffer, "%.15g ", (double) data_[row].second[j]);
	}
      }

      return n;
    }

    //--------------------------------------------------------------------------------
    inline void toCSR(std::ostream& outStream) const
    {
      { // Pre-conditions
	NTA_ASSERT(outStream.good())
	  << "SparseRLEMatrix::toCSR: Bad stream";
      } // End pre-conditions
   
      outStream << getVersion() << " "
		<< nRows() << " " << nCols() << " "
		<< (compress_ ? "1" : "0") << " "
		<< std::setprecision(15);
      
      for (ulong_size_type i = 0; i != nRows(); ++i) {
	outStream << data_[i].first;
	size_type nnzr = nNonZerosOnRow(i);
	if (compress_) {
	  const_cast<SparseRLEMatrix&>(*this).decompressRow_(i);
	  for (size_type k = 0; k != nnzr; ++k)
	    outStream << (double) nzb_[k] << " ";
	} else {
	  for (size_type k = 0; k != nnzr; ++k)
	    outStream << (double) data_[i].second[k] << " ";
	}
      }
    }

    //--------------------------------------------------------------------------------
    inline void fromCSR(std::istream& inStream)
    {
      { // Pre-conditions
	NTA_ASSERT(inStream.good())
	  << "SparseRLEMatrix::fromCSR: Bad stream";
      } // End pre-conditions
   
      std::string version;
      inStream >> version;
      
      NTA_CHECK(version == getVersion())
	<< "SparseRLEMatrix::fromCSR: Unknown version: " 
	<< version;
      
      ulong_size_type nrows = 0;
      inStream >> nrows;
      data_.resize(nrows);

      size_type ncols = 0;
      inStream >> ncols;
      indb_.resize(ncols);
      nzb_.resize(ncols);      

      int compressVal = 0;
      inStream >> compressVal;
      compress_ = compressVal == 1;

      if (compress_)
	c_.resize(nRows(), 0);
      
      for (ulong_size_type i = 0; i != nrows; ++i) {
	inStream >> data_[i].first;
	data_[i].second.resize(nNonZerosOnRow(i));
	size_type k2 = 0;
	for (size_type k = 0; k < data_[i].first.size(); k += 2) {
	  for (size_type j = data_[i].first[k]; j != data_[i].first[k+1]; ++j) {
	    double val;
	    inStream >> val;
	    data_[i].second[k2++] = (value_type) val;
	  }
	}
	/*
	NTA_CHECK(data_[i].first.size() <= 2*nCols())
	  << "SparseRLEMatrix::fromCSR: "
	  << "Too many indices";
	*/
	NTA_CHECK(data_[i].second.size() <= nCols())
	  << "SparseRLEMatrix::fromCSR: "
	  << "Too many values";
	for (size_type j = 0; j != data_[i].first.size(); ++j) {
	  size_type idx = data_[i].first[j];
	  NTA_CHECK(idx <= nCols())
	    << "SparseRLEMatrix::fromCSR: "
	    << "Invalid index: " << idx;
	  if (1 < j)
	    NTA_CHECK(data_[i].first[j-1] < idx)
	      << "SparseRLEMatrix::fromCSR: "
	      << "Invalid index: " << idx
	      << " - Indices need to be in strictly increasing order";
	}
	NTA_CHECK(data_[i].second.size() == nNonZerosOnRow(i))
	  << "SparseRLEMatrix::fromCSR: "
	  << "Mismatching number of indices and values";
	if (compress_)
	  compressRow_(i);
      }
    }

    //--------------------------------------------------------------------------------
    template <typename OutputIterator>
    inline void toDense(OutputIterator begin, OutputIterator end) const
    {
      { // Pre-conditions
	NTA_ASSERT((size_type)(end - begin) == nRows() * nCols())
	  << "SparseRLEMatrix::toDense: "
	  << "Not enough memory";
      } // End pre-conditions
   
      for (ulong_size_type row = 0; row != data_.size(); ++row)
	getRowToDense(row, begin + row*nCols(), begin + (row+1)*nCols());
    }

    //--------------------------------------------------------------------------------
    /**
     * Clears this instance and creates a new one from dense.
     */
    template <typename InputIterator>
    inline void fromDense(ulong_size_type nrows, size_type ncols,
			  InputIterator begin, InputIterator end) 
    {
      { // Pre-conditions
	NTA_ASSERT((ulong_size_type)(end - begin) >= nrows * ncols)
	  << "SparseRLEMatrix::fromDense: "
	  << "Not enough memory";
      } // End pre-conditions
      
      clear();

      for (ulong_size_type row = 0; row != nrows; ++row) 
	appendRow(begin + row * ncols, begin + (row+1) * ncols);
    }

    //--------------------------------------------------------------------------------
    inline void print(std::ostream& outStream) const
    {
      { // Pre-conditions
	NTA_CHECK(outStream.good())
	  << "SparseRLEMatrix::print: Bad stream";
      } // End pre-conditions

      std::vector<value_type> buffer(nCols());

      for (ulong_size_type row = 0; row != nRows(); ++row) {
	getRowToDense(row, buffer.begin(), buffer.end());
	for (size_type col = 0; col != nCols(); ++col)
	  outStream << buffer[col] << " ";
	outStream << std::endl;
      }
    }

    //--------------------------------------------------------------------------------
    inline void debugPrint() const
    {
      std::cout << "n rows= " << nRows()
		<< " n cols= " << nCols() 
		<< " n nz= " << nNonZeros()
		<< " n bytes= " << nBytes() << std::endl;
      std::cout << "this= " << sizeof(SparseRLEMatrix)
		<< " Row= " << sizeof(Row)
		<< " size= " << sizeof(size_type)
		<< " value= " << sizeof(value_type)
		<< " uLong= " << sizeof(uLong) << std::endl;
      std::cout << "data= " << data_.capacity() << " " << data_.size() << std::endl;
      std::cout << "indb= " << indb_.capacity() << " " << indb_.size() << std::endl;
      std::cout << "nzb= " << nzb_.capacity() << " " << nzb_.size() << std::endl;
      std::cout << "c= " << c_.capacity() << " " << c_.size() << std::endl;
      for (ulong_size_type i = 0; i != nRows(); ++i)
	std::cout << "row " << i << ": first: " 
		  << data_[i].first.capacity() << " " 
		  << data_[i].first.size() << " second: "
		  << data_[i].second.capacity() << " "
		  << data_[i].second.size() << std::endl;
      for (size_type row = 0; row != nRows(); ++row) {
	std::cout << data_[row].first << std::endl;
	for (size_type i = 0; i != data_[row].second.size(); ++i)
	  std::cout << (float) data_[row].second[i] << " ";
	std::cout << std::endl;
      }
    }
    
  private:

    //--------------------------------------------------------------------------------
    inline void compressRow_(ulong_size_type row)
    {
      { // Pre-conditions
	NTA_ASSERT(0 <= row && row < nRows())
	  << "SparseRLEMatrix::compressRow_: "
	  << "Invalid row index: " << row;
      } // End pre-conditions

      nzb_.resize(nCols() + 10);
      std::fill(nzb_.begin(), nzb_.end(), (value_type) 0);

      uLongf dstLen = nzb_.size() * sizeof(value_type);
      uLong srcLen = data_[row].second.size() * sizeof(value_type);

      // This gives some iterator related failure in debug mode on Windows,
      // but it works in release mode.
      compress((Bytef*)(&*nzb_.begin()), &dstLen, 
	       (Bytef*)(&*data_[row].second.begin()), srcLen);
      
      c_[row] = dstLen;
      size_type n = dstLen / sizeof(value_type) + 1;
      ValueVector new_vector(nzb_.begin(), nzb_.begin() + n);
      data_[row].second.swap(new_vector);
    }

    //--------------------------------------------------------------------------------
    inline uLongf decompressRow_(ulong_size_type row)
    {
      { // Pre-conditions
	NTA_ASSERT(0 <= row && row < nRows())
	  << "SparseRLEMatrix::decompressRow_: "
	  << "Invalid row index: " << row;
      } // End pre-conditions

      uLongf dstLen = nzb_.size() * sizeof(value_type);
      
      // This gives some iterator related failure in debug mode on Windows,
      // but it works in release mode.
      uncompress((Bytef*)(&*nzb_.begin()), &dstLen, 
		 (Bytef*)(&*data_[row].second.begin()), (uLong) c_[row]);
      
      return dstLen;
    }

    //--------------------------------------------------------------------------------
 

    SparseRLEMatrix(const SparseRLEMatrix&);
    SparseRLEMatrix& operator=(const SparseRLEMatrix&);

  }; // end class SparseRLEMatrix

  //--------------------------------------------------------------------------------
} // end namespace nta

#endif // NTA_SPARSE_RLE_MATRIX_HPP
