#ifndef NTA_PY_SPARSE_TENSOR_HPP
#define NTA_PY_SPARSE_TENSOR_HPP

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
 */


#include <py_support/NumpyVector.hpp>
#include <nupic/math/Index.hpp>
#include <nupic/math/Domain.hpp>
#include <nupic/math/SparseTensor.hpp>

#include <vector>
#include <sstream>

//--------------------------------------------------------------------------------
typedef std::vector<nupic::UInt32> TIV;

#define PYSPARSETENSOR_MAX_RANK 20

class PyTensorIndex;

inline std::ostream &operator<<(std::ostream &o, const PyTensorIndex &j);

//--------------------------------------------------------------------------------
class PyTensorIndex
{
  enum { maxRank = PYSPARSETENSOR_MAX_RANK };
  nupic::UInt32 index_[maxRank];
  nupic::UInt32 rank_;

public:
  typedef nupic::UInt32 value_type;
  typedef const nupic::UInt32 *const_iterator;
  typedef nupic::UInt32 *iterator;

  PyTensorIndex() : rank_(0) {}

  PyTensorIndex(const PyTensorIndex &x) : rank_(x.rank_)
  {
    ::memcpy(index_, x.index_, rank_*sizeof(nupic::UInt32));
  }

  PyTensorIndex(nupic::UInt32 i) : rank_(1)
  {
    index_[0] = i;
  }

  PyTensorIndex(nupic::UInt32 i, nupic::UInt32 j) : rank_(2)
  {
    index_[0] = i;
    index_[1] = j;
  }

  PyTensorIndex(nupic::UInt32 i, nupic::UInt32 j, nupic::UInt32 k) : rank_(3)
  {
    index_[0] = i;
    index_[1] = j;
    index_[2] = k;
  }

  PyTensorIndex(nupic::UInt32 i, nupic::UInt32 j, nupic::UInt32 k, nupic::UInt32 l) : rank_(4)
  {
    index_[0] = i;
    index_[1] = j;
    index_[2] = k;
    index_[3] = l;
  }

  PyTensorIndex(nupic::UInt32 i, nupic::UInt32 j, nupic::UInt32 k, nupic::UInt32 l, nupic::UInt32 m) : rank_(5)
  {
    index_[0] = i;
    index_[1] = j;
    index_[2] = k;
    index_[3] = l;
    index_[4] = m;
  }

  PyTensorIndex(nupic::UInt32 i, nupic::UInt32 j, nupic::UInt32 k, nupic::UInt32 l, nupic::UInt32 m, nupic::UInt32 n) : rank_(6)
  {
    index_[0] = i;
    index_[1] = j;
    index_[2] = k;
    index_[3] = l;
    index_[4] = m;
    index_[5] = n;
  }

  PyTensorIndex(const TIV &i) : rank_(i.size())
  {
    if (rank_ > maxRank) {
      char errBuf[512];
      snprintf(errBuf, 512, 
               "Tensors may not be constructed of rank greater than %d.", maxRank);
      rank_ = 0;
      throw std::runtime_error(errBuf);
    }
    std::copy(i.begin(), i.end(), index_);
  }

  template<typename T>
  PyTensorIndex(int nd, const T *d) : rank_(nd)
  {
    if (nd > maxRank) {
      char errBuf[512];
      snprintf(errBuf, 512, 
               "Tensors may not be constructed of rank greater than %d.", maxRank);
      rank_ = 0;
      throw std::runtime_error(errBuf);
    }
    if(d) std::copy(d, d+nd, index_);
    else std::fill(index_, index_+nd, 0);
  }
  
  PyTensorIndex(const PyTensorIndex& i1, const PyTensorIndex& i2)
    : rank_(i1.rank_ + i2.rank_)
  {
    if (rank_ > maxRank) {
      char errBuf[512];
      snprintf(errBuf, 512, 
               "Tensors may not be constructed of rank greater than %d.", maxRank);
      rank_ = 0;
      throw std::runtime_error(errBuf);
    }

    ::memcpy(index_, i1.index_, i1.rank_*sizeof(nupic::UInt32));
    ::memcpy(index_ + i1.rank_, i2.index_, i2.rank_*sizeof(nupic::UInt32));
  }
  
  PyTensorIndex &operator=(const PyTensorIndex &x)
  {
    rank_ = x.rank_;
    ::memcpy(index_, x.index_, rank_*sizeof(nupic::UInt32));
    return *this;
  }

  PyTensorIndex &operator=(const TIV &i)
  {
    if(i.size() > maxRank) {
      char errBuf[512];
      snprintf(errBuf, 512, 
               "Tensors may not be constructed of rank greater than %d.", maxRank);
      rank_ = 0;
      throw std::runtime_error(errBuf);
    }
    rank_ = i.size();
    std::copy(i.begin(), i.end(), index_);
    return *this;
  }

  nupic::UInt32 size() const { return rank_; }

  nupic::UInt32 operator[](nupic::UInt32 i) const
  {
    if(!(i < rank_)) throw std::invalid_argument("Index out of bounds.");
    return index_[i];
  }
  nupic::UInt32 &operator[](nupic::UInt32 i)
  {
    if(!(i < rank_)) throw std::invalid_argument("Index out of bounds.");
    return index_[i];
  }

  nupic::UInt32 __getitem__(int i) const { if(i < 0) i += rank_; return index_[i]; }
  void __setitem__(int i, nupic::UInt32 d) { if(i < 0) i += rank_; index_[i] = d; }
  nupic::UInt32 __len__() const { return rank_; }

  const nupic::UInt32 *begin() const { return index_; }
  nupic::UInt32 *begin() { return index_; }
  const nupic::UInt32 *end() const { return index_ + rank_; }
  nupic::UInt32 *end() { return index_ + rank_; }

  bool operator==(const PyTensorIndex &j) const
  {
    if(rank_ != j.rank_) return false;
    for(nupic::UInt32 i=0; i<rank_; ++i)
      { if(index_[i] != j.index_[i]) return false; }
    return true;
  }
  bool operator!=(const PyTensorIndex &j) const { return !((*this) == j); }
  bool operator<(const PyTensorIndex &j) const
  {
    const nupic::UInt32 n = rank_ <= j.rank_ ? rank_ : j.rank_;

    for (nupic::UInt32 k = 0; k < n; ++k)
      if (index_[k] < j.index_[k])
        return true;
      else if (index_[k] > j.index_[k])
        return false;
    if(n < j.rank_) return true;
    else return false;
    return false;
  }
  bool __eq__(const PyTensorIndex &j) const { return (*this) == j; }
  bool __ne__(const PyTensorIndex &j) const { return (*this) != j; }
  //  bool __lt__(const PyTensorIndex &j) const { return (*this) < j; }
  bool __gt__(const PyTensorIndex &j) const { return j < (*this); }

  bool operator==(const TIV &j) const
  {
    if(size() != j.size()) return false;
    for(nupic::UInt32 i=0; i<rank_; ++i)
      { if(index_[i] != j[i]) return false; }
    return true;
  }
  bool operator!=(const TIV &j) const { return !((*this) == j); }
  bool __eq__(const TIV &j) const { return (*this) == j; }
  bool __ne__(const TIV &j) const { return (*this) != j; }

  std::string __str__() const
  {
    std::stringstream s;
    s << "(";
    nupic::UInt32 n = rank_;
    if(n) {
      s << index_[0];
      for(nupic::UInt32 i=1; i<n; ++i) s << ", " << index_[i];
    }
    s << ")";
    return s.str();
  }

  TIV __getslice__(int i, int j) const
  {
    if(i < 0) i += rank_;
    if(j < 0) j += rank_;
    if(j == 2147483647) j = rank_;
    return TIV(index_ + i, index_ + j);
  }
  
  void __setslice__(int i, int j, const TIV &x)
  {
    if(i < 0) i += rank_;
    if(j < 0) j += rank_;
    if(j == 2147483647) j = rank_;
    std::copy(x.begin(), x.end(), index_ + i);
  }

  TIV asTuple() const
  { return TIV(index_, index_ + rank_); }

  TIV __getstate__() const { return asTuple(); }
};

//--------------------------------------------------------------------------------
inline PyTensorIndex concatenate(const PyTensorIndex& i1, const PyTensorIndex& i2)
{
  return PyTensorIndex(i1, i2);
}

//--------------------------------------------------------------------------------
inline std::ostream &operator<<(std::ostream &o, const PyTensorIndex &j) {
  o << "(";
  nupic::UInt32 n = j.size();
  if(n) {
    o << j[0];
    for(nupic::UInt32 i=1; i<n; ++i) o << "," << j[i];
  }
  o << ")";
  return o;
}

//--------------------------------------------------------------------------------
class PyDomain : public nupic::Domain<nupic::UInt32>
{
public:
  PyDomain(const TIV &lowerHalfSpace) : nupic::Domain<nupic::UInt32>(lowerHalfSpace) {}
  PyDomain(const TIV &lower, const TIV &upper)
    : nupic::Domain<nupic::UInt32>(lower, upper) {}

  PyTensorIndex getLowerBound() const
  {
    PyTensorIndex bounds(rank(), (const nupic::UInt32 *) 0);
    getLB(bounds);
    return bounds;
  }

  PyTensorIndex getUpperBound() const
  {
    PyTensorIndex bounds(rank(), (const nupic::UInt32 *) 0);
    getUB(bounds);
    return bounds;
  }

  std::vector<nupic::UInt32> __getitem__(int i) const
  {
    nupic::DimRange<nupic::UInt32> r = (*this)[i];
    nupic::UInt32 v[3];
    v[0] = r.getDim();
    v[1] = r.getLB();
    v[2] = r.getUB();
    return std::vector<nupic::UInt32>(v, v+3);
  }

  PyTensorIndex getDimensions() const
  {
    PyTensorIndex bounds(rank(), (const nupic::UInt32 *) 0);
    getDims(bounds);
    return bounds;
  }

  nupic::UInt32 getNumOpenDims() const { return getNOpenDims(); }

  PyTensorIndex getOpenDimensions() const
  {
    PyTensorIndex bounds(getNumOpenDims(), (const nupic::UInt32 *) 0);
    getOpenDims(bounds);
    return bounds;
  }

  //  PyTensorIndex getSliceBounds(const TIV &maxBounds) const
  PyTensorIndex getSliceBounds() const
  {
    PyTensorIndex bounds(getNumOpenDims(), (const nupic::UInt32 *) 0);
    nupic::UInt32 n = rank();
    nupic::UInt32 cur = 0;
    for(nupic::UInt32 i=0; i<n; ++i) {
      nupic::DimRange<nupic::UInt32> r = (*this)[i];
      if(!(r.getDim() == i)) throw std::invalid_argument("Out-of-order dims.");
      if(r.empty()) {}
      else {
        bounds[cur++] = r.getUB() - r.getLB();
      }
    }
    return bounds;
  }

  bool doesInclude(const TIV &x) const
  { return includes(x); }

  std::string __str__() const
  {
    std::stringstream s;
    s << "(";
    nupic::UInt32 n = rank();
    for(nupic::UInt32 i=0; i<n; ++i) {
      if(i) s << ", ";
      nupic::DimRange<nupic::UInt32> r = (*this)[i];
      s << "(" << r.getDim() << ", " << r.getLB() << ", " << r.getUB() << ")";
    }
    s << ")";
    return s.str();
  }
};

//--------------------------------------------------------------------------------
class PySparseTensor
{
  nupic::SparseTensor<PyTensorIndex, nupic::Real> tensor_;
  
public:
  PySparseTensor(const std::string &state);
  PySparseTensor(const TIV &bounds) : tensor_(PyTensorIndex(bounds)) {}
  PySparseTensor(const PyTensorIndex &bounds) : tensor_(bounds) {}
  PySparseTensor(/*const*/ PyObject *dense);

  nupic::UInt32 getRank() const { return tensor_.getRank(); }

  PyTensorIndex getBounds() const { return tensor_.getBounds(); }
  nupic::UInt32 getBound(const nupic::UInt32 dim) const { return tensor_.getBound(dim); }

  nupic::Real get(const TIV &i) const { return get(PyTensorIndex(i)); }
  nupic::Real get(const PyTensorIndex &i) const { return tensor_.get(i); }
  void set(const TIV &i, nupic::Real x) { set(PyTensorIndex(i), x); }
  void set(const PyTensorIndex &i, nupic::Real x) { tensor_.set(i, x); }
  void set(const TIV &i, PyObject *x) { set(PyTensorIndex(i), x); }
  void set(const PyTensorIndex &i, PyObject *x);

  nupic::UInt32 getNNonZeros() const { return tensor_.getNNonZeros(); }
  nupic::UInt32 nNonZeros() const { return tensor_.getNNonZeros(); }
 
  PySparseTensor reshape(const TIV &dims) const 
  {
    PySparseTensor t(dims);
    tensor_.reshape(t.tensor_);
    return t;
  }

  void resize(const TIV &dims)
  { tensor_.resize(PyTensorIndex(dims)); }

  void resize(const PyTensorIndex &dims)
  { tensor_.resize(dims); }

  PySparseTensor extract(nupic::UInt32 dim, const TIV &ind) const
  {
    std::set<nupic::UInt32> subset(ind.begin(), ind.end());
    PySparseTensor t(tensor_.getBounds());
    tensor_.extract(dim, subset, t.tensor_);
    return t;
  }

  void reduce(nupic::UInt32 dim, const TIV &ind)
  {
    std::set<nupic::UInt32> subset(ind.begin(), ind.end());
    tensor_.reduce(dim, subset);
  }
    
  PySparseTensor getSlice(const PyDomain &range) const
  {
    PyTensorIndex dims = range.getSliceBounds();
    PySparseTensor t(dims);
    tensor_.getSlice(range, t.tensor_);
    return t;
  }

  void setSlice(const PyDomain &range, const PySparseTensor &slice)
  {
    tensor_.setSlice(range, slice.tensor_);
  }

  void setZero(const PyDomain& range) 
  {
    tensor_.setZero(range);
  }

  void addSlice(nupic::UInt32 which, nupic::UInt32 src, nupic::UInt32 dst)
  {
    tensor_.addSlice(which, src, dst);
  }

  PySparseTensor factorMultiply(const TIV &dims, const PySparseTensor &B) const
  { return factorMultiply(PyTensorIndex(dims), B); }

  PySparseTensor factorMultiply(const PyTensorIndex &dims, const PySparseTensor &B) const
  {
    PySparseTensor C(getBounds());
    tensor_.factor_apply_fast(dims, B.tensor_, C.tensor_, std::multiplies<nupic::Real>());
    return C;
  }

  PySparseTensor outerProduct(const PySparseTensor& B) const
  {
    PySparseTensor C(PyTensorIndex(getBounds(), B.getBounds()));
    tensor_.outer_product_nz(B.tensor_, C.tensor_, std::multiplies<nupic::Real>());
    return C;
  }

  PySparseTensor innerProduct(const nupic::UInt32 dim1, const nupic::UInt32 dim2, const PySparseTensor& B) const
  {
    // Only works on rank 2 tensors right now
    if((getRank() != 2) || (B.getRank() != 2))
      throw std::invalid_argument("innerProduct only works for rank 2 tensors.");
    PySparseTensor C(PyTensorIndex(getBound(1-dim1),B.getBound(1-dim2)));
    tensor_.inner_product_nz(dim1, dim2, B.tensor_, C.tensor_, std::multiplies<nupic::Real>(), std::plus<nupic::Real>());
    return C;
  }

  PySparseTensor __add__(const PySparseTensor &B) const
  {
    PySparseTensor C(getBounds());
    tensor_.axby(1.0, B.tensor_, 1.0, C.tensor_);
    return C;
  }

  PySparseTensor __sub__(const PySparseTensor &B) const
  {
    PySparseTensor C(getBounds());
    tensor_.axby(1.0, B.tensor_, -1.0, C.tensor_);
    return C;
  }

  PySparseTensor factorAdd(const TIV &dims, const PySparseTensor &B) const
  { return factorAdd(PyTensorIndex(dims), B); }

  PySparseTensor factorAdd(const PyTensorIndex& dims, const PySparseTensor& B) const
  {
    PySparseTensor C(getBounds());
    tensor_.factor_apply_nz(dims, B.tensor_, C.tensor_, std::plus<nupic::Real>(), true);
    return C;
  }

  PySparseTensor getComplementBounds(const PyTensorIndex &dims) const
  {
    PyTensorIndex process(tensor_.getBounds());
    nupic::UInt32 n = dims.size();
    for(nupic::UInt32 i=0; i<n; ++i)
      process[dims[i]] = 0;

    n = process.size();
    PyTensorIndex remain(n - dims.size(), (const nupic::UInt32 *) 0);
    nupic::UInt32 cur = 0;
    for(nupic::UInt32 i=0; i<n; ++i) {
      nupic::UInt32 keep = process[i];
      if(keep) remain[cur++] = keep;
    }
    return remain;
  }

  PySparseTensor __mul__(const nupic::Real &x) const;
  PySparseTensor __neg__() const { return this->__mul__(-1.0); }

  double marginalize() const;

  PySparseTensor marginalize(const TIV &dims) const
  { return marginalize(PyTensorIndex(dims)); }

  PySparseTensor marginalize(const PyTensorIndex &dims) const
  {
    PySparseTensor B(getComplementBounds(dims));
    tensor_.accumulate_nz(dims, B.tensor_, std::plus<nupic::Real>(), nupic::Real(0.0f));
    return B;
  }
  
  PyTensorIndex argmax() const;
  nupic::Real max() const;

  PySparseTensor max(const TIV &dims) const
  { return this->max(PyTensorIndex(dims)); }

  PySparseTensor max(const PyTensorIndex &dims) const
  {
    PySparseTensor B(getComplementBounds(dims));
    tensor_.max(dims, B.tensor_);
    return B;
  }

  PyObject* tolist() const
  {
    const nupic::UInt32 rank = getRank();
    const nupic::UInt32 nnz = getNNonZeros();
    std::vector<PyTensorIndex> ind(nnz);
    nupic::NumpyVectorT<nupic::Real> val(nnz);
    tensor_.toList(ind.begin(), val.begin());
    PyObject* ind_list = PyTuple_New(nnz);
    for (nupic::UInt32 i = 0; i != nnz; ++i) {
      PyObject* idx = PyTuple_New(rank);
      for (nupic::UInt32 j = 0; j != rank; ++j)
	PyTuple_SET_ITEM(idx, j, PyInt_FromLong(ind[i][j]));
      PyTuple_SET_ITEM(ind_list, i, idx);
    }
    PyObject* toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, ind_list);
    PyTuple_SET_ITEM(toReturn, 1, val.forPython());
    return toReturn;
  }

  bool __eq__(const PySparseTensor &B) const 
  { return nupic::operator==(tensor_, B.tensor_); }
  bool __ne__(const PySparseTensor &B) const 
  { return nupic::operator==(tensor_, B.tensor_); }

  PyObject *toDense() const;

  PyObject *__str__() const;

  std::string __getstate__() const;

  PySparseTensor copy() const { return *this; }
};

//--------------------------------------------------------------------------------

#endif // __nta_PySparseTensor_hpp__

