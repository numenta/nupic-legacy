#ifndef NTA_WRAPPED_VECTOR_HPP
#define NTA_WRAPPED_VECTOR_HPP

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
 
#include <nupic/types/Types.hpp>

#include <algorithm>
#include <vector>
#include <stdexcept>
#include <string>
#include <sstream>
#include <iterator>

namespace nupic {

template<typename T>
inline std::string tts(const T x) {
  std::ostringstream s;
  s << x;
  return s.str();
}

template<typename T>
class WrappedVectorIter //: public random_access_iterator<T, int> 
{
public:
  int n_;
  int incr_;
  T *p_;

  typedef T value_type;
//  typedef int size_type;
//  typedef ptrdiff_t difference_type;
  typedef std::random_access_iterator_tag iterator_category;
  typedef int difference_type;
  typedef T *pointer;
//  typedef const T *const_pointer;
  typedef T &reference;
//  typedef const T &const_reference;

  WrappedVectorIter(int n, int incr, T *p) : n_(n), incr_(incr), p_(p) {}

  int size() const { return n_; }
  T operator[](int i) const { return *(p_ + (i*incr_)); }
  T &operator[](int i) { return *(p_ + (i*incr_)); }

  /// Slices without bounds-checking.
  WrappedVectorIter<T> slice(int i, int j) const {
    if(j >= i) return WrappedVectorIter(j - i, incr_, p_ + i*incr_);
    else return WrappedVectorIter(i - j, -incr_, p_ + i*incr_);
  }

  WrappedVectorIter<T> slice(int start, int /*stop*/, int step, int length) const {
    return WrappedVectorIter(length, incr_*step, p_ + start*incr_);
  }

  WrappedVectorIter<T> end() const { return slice(n_, n_); }

  WrappedVectorIter<T> reversed() const {
    return WrappedVectorIter(n_, -incr_, p_ + (n_-1)*incr_);
  }

  /// Advance
  WrappedVectorIter<T> operator+(int n) const { return slice(n, n_-n); }
  WrappedVectorIter<T> operator+(size_t n) const { return slice(int(n), n_-int(n)); }
  /// Advance in-place
  WrappedVectorIter<T> &operator+=(int n) { *this = slice(n, n_-n); return *this; }
  WrappedVectorIter<T> &operator+=(size_t n) { *this = slice(int(n), n_-int(n)); return *this; }
  /// Prefix increment
  WrappedVectorIter<T> &operator++() { *this = slice(1, n_-1); return *this; }
  /// Postfix increment
  WrappedVectorIter<T> operator++(int) { WrappedVectorIter<T> a = *this; *this = slice(1, n_-1); return a; }
  /// Move back
  WrappedVectorIter<T> operator-(int n) const { return slice(-n, n_+n); }
  WrappedVectorIter<T> operator-(size_t n) const { return slice(-int(n), n_+int(n)); }
  /// Move back in-place
  WrappedVectorIter<T> &operator-=(int n) { *this = slice(-n, n_+n); return *this; }
  WrappedVectorIter<T> &operator-=(size_t n) { *this = slice(-int(n), n_+int(n)); return *this; }
  /// Prefix decrement
  WrappedVectorIter<T> &operator--() { *this = slice(-1, n_+1); return *this; }
  /// Postfix decrement
  WrappedVectorIter<T> operator--(int) { WrappedVectorIter<T> a = slice(-1, n_+1); *this = slice(-1, n_+1); return a; }
  /// Difference between two iterators
  int operator-(const WrappedVectorIter<T> &i) const { return int((p_ - i.p_) / incr_); }

  /// Dereference
  T operator*() const { return *p_; }
  /// Dereference, non-const
  T &operator*() { return *p_; }
  /// Cast to pointer
  operator const T *() const { return p_; }
  /// Cast to pointer, non-const
  operator T *() { return p_; }
  /// Access as pointer
  const T *operator->() const { return p_; }
  /// Access as pointer, non-const
  T *operator->() { return p_; }
  
  /// Not-equal comparison
  bool neq(const T *p) const { return p_ != p; }
  /// Equal comparison
  bool eq(const T *p) const { return p_ == p; }
  /// Less-than, considering increment direction
  bool le(const T *p) const { return (incr_ >= 0) ? (p_ < p) : (p < p_); }
  /// LEQ, considering increment direction
  bool leq(const T *p) const { return (incr_ >= 0) ? (p_ <= p) : (p <= p_); }
  /// Greater-than, considering increment direction
  bool ge(const T *p) const { return (incr_ >= 0) ? (p_ > p) : (p > p_); }
  /// GEQ, considering increment direction
  bool geq(const T *p) const { return (incr_ >= 0) ? (p_ >= p) : (p >= p_); }

  bool operator!=(const WrappedVectorIter<T> &x) const { return neq(x.p_); }
  bool operator==(const WrappedVectorIter<T> &x) const { return eq(x.p_); }
  bool operator<(const WrappedVectorIter<T> &x) const { return le(x.p_); }
  bool operator<=(const WrappedVectorIter<T> &x) const { return leq(x.p_); }
  bool operator>(const WrappedVectorIter<T> &x) const { return ge(x.p_); }
  bool operator>=(const WrappedVectorIter<T> &x) const { return geq(x.p_); }

  template<typename T2>
  void copyFrom(int dim, int incr, const T2 *in) {
    const int n = n_, inc1 = incr_, inc2 = incr;
    T *p1 = p_;
    const T2 *p2 = in;
    for(int i=0; i<n; ++i) { *p1 = *p2; p1 += inc1; p2 += inc2; }
  }

  template<typename T2>
  void into(int dim, int incr, T2 *out) const {
    const int n = n_, inc1 = incr_, inc2 = incr;
    const T *p1 = p_;
    T2 *p2 = out;
    for(int i=0; i<n; ++i) { *p2 = *p1; p1 += inc1; p2 += inc2; }
  }
};

/// Simple, namespace-less wrapper for Vector.
/// Designed to mirror Python functionality and to be 
/// very easy to wrap using SWIG.
/// Most operations should disappear through inlining.
/// Does not own its pointer or guarantee its safety in 
/// any way (similar to the way Vector references 
/// memory managed elsewhere).
class WrappedVector {
  WrappedVectorIter<nupic::Real> p_;
  nupic::Real *own_;
  void free() { if(own_) { delete own_; own_ = 0; } }

public:
  /// Extremely dangerous constructor! Only use for unit testing!
  WrappedVector(int n) : p_(n, 1, new nupic::Real[n]), own_(0) { own_ = p_.p_; }

public:
  void checkIndex(int i) const {
    if(!((i >= 0) && (i < p_.n_)))
      throw std::invalid_argument("Index " + tts(i) + " out of bounds.");
  }

  void checkBeginEnd(int begin, int end) const {
    if(end > begin) {
      if(!(begin >= 0)) 
        throw std::invalid_argument("Begin " + tts(begin) + " out of bounds.");
      if(!(end <= p_.n_)) 
        throw std::invalid_argument("End " + tts(end) + " out of bounds.");
    }
    else if(end == begin) {
      if(!((begin >= 0) && (end <= p_.n_)))
        throw std::invalid_argument("Out of bounds.");
    }
    else if(end < begin) {
      if(!(end >= (-1))) 
        throw std::invalid_argument("End " + tts(end) + " out of bounds.");
      if(!(begin < p_.n_)) 
        throw std::invalid_argument("Begin " + tts(begin) + " out of bounds.");
    }
  }

public:
  typedef WrappedVectorIter<nupic::Real> iterator;

  WrappedVector() : p_(0, 1, 0), own_(0) {}
  WrappedVector(const WrappedVectorIter<nupic::Real> &p) : p_(p), own_(0) {}
  WrappedVector(int size, nupic::Real *p) : p_(size, 1, p), own_(0) {}
  
//  WrappedVector(const nupic::Belief &b) : p_(b.size(), 1, const_cast<nupic::Real *>(b.ptr())), own_(0) {}
  WrappedVector(const std::vector<nupic::Real> &v) : p_(int(v.size()), 1, const_cast<nupic::Real *>(&(v[0]))), own_(0) {}
  WrappedVector(const WrappedVector &v) : p_(v.p_), own_(0) {}
  WrappedVector &operator=(const WrappedVector &v) { this->free(); p_ = v.p_; own_ = 0; return *this; }
  
  ~WrappedVector() { this->free(); }
  
  WrappedVector wvector(size_t lag=0) const { return *this; }

  void clear() { this->free(); p_.n_ = 0; p_.incr_ = 1; p_.p_ = 0; }
  void setPointer(int n, int incr, nupic::Real *p) { this->free(); p_.n_ = n; p_.incr_ = incr; p_.p_ = p; }
  void setPointer(int n, nupic::Real *p) { this->free(); p_.n_ = n; p_.incr_ = 1; p_.p_ = p; }

  // Returns the beginning address of the underlying
  // data buffer as an integer.
  int getBufPtrAsInt(void) { return (int)(long)(p_.p_); }

  iterator begin() { return p_; }
  iterator end() { return p_.end(); }

  nupic::Size __len__() const { return p_.size(); }

  template<typename T>
  void adjust(T &endPoint) const {
    T n = (T) p_.size();
    if(endPoint < 0) endPoint += n;
    else if(endPoint > n) endPoint = n;
  }

  nupic::Real __getitem__(int i) const {
    adjust(i); 
    checkIndex(i); 
    return p_[i]; 
  }

  void __setitem__(int i, nupic::Real x) {
    adjust(i);
    checkIndex(i); 
    p_[i] = x; 
  }

  std::string __repr__() const {
    std::ostringstream s;
    s << "[";
    const nupic::Real *p = p_.p_;
    int nm1 = p_.n_-1;
    for(int i=0; i<nm1; ++i) {
      s << (*p) << ", ";
      p += p_.incr_;
    }
    if(p_.n_) s << (*p);
    s << "]";
    return s.str();
  }

  std::string __str__() const { return __repr__(); }

  WrappedVector slice(int i, int j) const {
    return p_.slice(i, j);
  }

  /// These are meant to come from PySlice_GetIndicesEx.
  WrappedVector slice(int start, int stop, int step, int length) const {
    return p_.slice(start, stop, step, length);
  }

  /// Copied reference is reversed.
  WrappedVector __reversed__() const { return p_.reversed(); }

  /// Reverse in-place.
  void reverse() { p_ = p_.reversed(); }

  /// Sort the elements in place.
  void sort(bool descending=false) {
    std::sort(begin(), end());
    if(descending) reverse();
  }

//  WrappedVector &
  void __iadd__(const WrappedVector &v) {
    if(!(p_.n_ == v.p_.n_)) 
      throw std::invalid_argument("Sizes must match: " +
        tts(p_.n_) + " " + tts(v.p_.n_));
    const int n = p_.n_, inc1 = p_.incr_, inc2 = v.p_.incr_;
    nupic::Real *p1 = p_.p_;
    const nupic::Real *p2 = v.p_.p_;
    for(int i=0; i<n; ++i) { *p1 += *p2; p1 += inc1; p2 += inc2; }
//    return *this;
  }

//  WrappedVector &
  void __imul__(const WrappedVector &v) {
    if(!(p_.n_ == v.p_.n_)) 
      throw std::invalid_argument("Sizes must match: " +
        tts(p_.n_) + " " + tts(v.p_.n_));
    const int n = p_.n_, inc1 = p_.incr_, inc2 = v.p_.incr_;
    nupic::Real *p1 = p_.p_;
    const nupic::Real *p2 = v.p_.p_;
    for(int i=0; i<n; ++i) { *p1 *= *p2; p1 += inc1; p2 += inc2; }
//    return *this;
  }

  /// Copy the elements of v into this vector.
  /// Sizes must match exactly.
  void copyFrom(const WrappedVector &v) {
    int n = v.p_.n_;
    if(!(p_.n_ == n)) 
      throw std::invalid_argument("Sizes must match: " +
        tts(p_.n_) + " " + tts(n));
    p_.copyFrom(n, v.p_.incr_, v.p_.p_);
  }

  template<typename T2>
  void copyFromT(int n, int incr, const T2 *p) {
    if(!(p_.n_ == n)) 
      throw std::invalid_argument("Sizes must match: " +
        tts(p_.n_) + " " + tts(n));
    p_.copyFrom(n, incr, p);
  }

  template<typename T2>
  void copyIntoT(int n, int incr, T2 *p) const {
    p_.into(n, incr, p);
  }

  void setSlice(int i, int j, const WrappedVector &v) {
    checkBeginEnd(i, j);
    int n = v.p_.n_;
    if(!(n == abs(j-i))) throw std::invalid_argument("Sizes must match.");
    p_.slice(i, j).copyFrom(n, v.p_.incr_, v.p_.p_);
  }

  /// Can function as its own iterator.
  WrappedVector __iter__() const { return *this; }

  /// Iterator functionality.
  WrappedVector next() const { return p_ + 1; }

  void fill(nupic::Real x) {
    const int n = p_.n_, inc1 = p_.incr_;
    nupic::Real *p1 = p_.p_;
    for(int i=0; i<n; ++i) { *p1 = x; p1 += inc1; }
  }

  int argmax() const {
    const int n = p_.n_, inc1 = p_.incr_;
    if(!(n >= 1))
      throw std::runtime_error("Cannot call argmax on a 0-length vector.");
    const nupic::Real *p1 = p_.p_;
    int mi = 0;
    nupic::Real mv = *p1; p1 += inc1;
    for(int i=1; i<n; ++i) { 
      nupic::Real x = *p1; p1 += inc1;
      if(x > mv) { mi = i; mv = x; }
    }
    return mi;
  }

  nupic::Real sum() const {
    const int n = p_.n_, inc1 = p_.incr_;
    const nupic::Real *p1 = p_.p_;
    nupic::Real sum = 0;
    for(int i=0; i<n; ++i) { 
      nupic::Real x = *p1; p1 += inc1;
      sum += x;
    }
    return sum;
  }

  nupic::Real sumSq() const {
    const int n = p_.n_, inc1 = p_.incr_;
    const nupic::Real *p1 = p_.p_;
    nupic::Real sum = 0;
    for(int i=0; i<n; ++i) { 
      nupic::Real x = *p1; p1 += inc1;
      sum += x*x;
    }
    return sum;
  }
    
  bool any() const {
    const int n = p_.n_, inc1 = p_.incr_;
    const nupic::Real *p1 = p_.p_;
    for(int i=0; i<n; ++i) { 
      nupic::Real x = *p1; p1 += inc1;
      if(x) return true;
    }
    return false;
  }

  nupic::Real all() const {
    const int n = p_.n_, inc1 = p_.incr_;
    const nupic::Real *p1 = p_.p_;
    for(int i=0; i<n; ++i) { 
      nupic::Real x = *p1; p1 += inc1;
      if(!x) return false;
    }
    return true;
  }
};

} // End namespace nupic.

#endif


