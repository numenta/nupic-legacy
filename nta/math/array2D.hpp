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
 * A dense matrix with contiguous storage.
 */

#ifndef NTA_ARRAY2D_HPP
#define NTA_ARRAY2D_HPP

/*
 * This is only used in svm. Including it in NuPIC2 for the time being.
 */

// separate allocation
// separate storage type and computation type
// try to separate algorithms and write them for all types of matrices??
// optimize kernels depending on cache sizes?

//--------------------------------------------------------------------------------
/**
 * A fixed size matrix, allocated as a single contiguous chunk of memory.
 */
template <typename S, typename T>
class array2D
{
public:
  typedef S size_type;
  typedef T value_type;
  typedef value_type* iterator;
  typedef const value_type* const_iterator;
  
  size_type nrows_, ncols_;
  iterator d; // __attribute__ ((aligned (16)));
  iterator d_end; // __attribute__ ((aligned (16)));
  
  inline array2D()
    : nrows_(0), ncols_(0), d(0), d_end(0)
  {}

  inline array2D(size_type m_, size_type n_)
    : nrows_(m_), ncols_(n_), 
      d(new value_type[m_ * n_]), d_end(d + m_ * n_)
  {}

  inline array2D(size_type m_, size_type n_, const value_type& init_val)
    : nrows_(m_), ncols_(n_), 
      d(new value_type[m_ * n_]), d_end(d + m_ * n_)
  {
    for (iterator i = begin(); i != end(); ++i)
      *i = init_val;
  }

	inline array2D(size_type m_, size_type n_, value_type* array)
		: nrows_(m_), ncols_(n_),
			d(new value_type[m_ * n_]), d_end(d + m_ * n_)
	{
		size_type n = size();
		for (size_type i = 0; i != n; ++i)
			*(d+i) = *(array + i);
	}

  inline array2D(const array2D& b)
    : nrows_(b.nrows_), ncols_(b.ncols_),
      d(new value_type [b.nelts()]), d_end(d + b.nelts())
  {
    this->copy(b);
  }

  inline ~array2D()
  {
    delete [] d;
    d = d_end = 0;
  }

  inline array2D& operator=(const array2D& b)
  {
    if (this != &b) 
      this->copy(b);
    return *this;
  }

  inline void copy(const array2D& b)
  {
    if (nelts() != b.nelts()) {
      delete [] d;
      nrows_ = b.nrows_;
      ncols_ = b.ncols_;
      size_type n = nrows_ * ncols_;
      d = new value_type [n];
      d_end = d + n;
    }

    const_iterator b_it, b_end;
    iterator this_it = this->begin();

    for (b_it = b.begin(), b_end = b.end(); b_it != b_end; ++b_it, ++this_it)
      *this_it = *b_it;
  }

	template <typename It>
	inline void	copy(It array_it)
	{
		size_type n = size();
		for (size_type i = 0; i != n; ++i, ++array_it)
			*(d+i) = *array_it;
	}

  inline size_type nrows() const { return nrows_; }
  inline size_type ncols() const { return ncols_; }
  inline size_type nelts() const { return d_end - d; }
  inline size_type size() const { return d_end - d; }

  inline iterator begin() { return d; }
  inline iterator end() { return d_end; }
  inline const_iterator begin() const { return d; }
  inline const_iterator end() const { return d_end; }
  inline iterator begin(size_type i) { return d + i*ncols_; }
  inline iterator end(size_type i) { return d + (i+1)*ncols_; }
  inline const_iterator begin(size_type i) const { return d + i*ncols_; }
  inline const_iterator end(size_type i) const { return d + (i+1)*ncols_; }

  inline const value_type operator()(size_type i, size_type j) const
  {
    return d[i*ncols_+j];
  }

  inline value_type& operator()(size_type i, size_type j)
  {
    return d[i*ncols_+j];
  }

  inline const value_type at(size_type i, size_type j) const
  {
    return d[i*ncols_+j];
  }

  inline value_type at(size_type i, size_type j)
  {
    return d[i*ncols_+j];
  }

  template <typename It>
  inline void getRow(size_type row, It v_it) const
  {
    const_iterator it = begin(row), it_end = end(row);
    while (it != it_end) {
      *v_it = *it;
      ++v_it; ++it;
    }
  }

  template <typename It>
  inline void setRow(size_type row, It v_it)
  {
    iterator it = begin(row), it_end = end(row);
    while (it != it_end) {
      *it = *v_it;
      ++it; ++v_it;
    }
  }

  template <typename It>
  inline void getColumn(size_type col, It v_it) const
  {
    for (size_type i = 0; i < nrows(); ++i, ++v_it) 
      *v_it = this->operator()(i, col);
  }

  template <typename It>
  inline void setColumn(size_type col, It v_it)
  {
    for (size_type i = 0; i < nrows(); ++i, ++v_it) 
      this->operator()(i, col) = *v_it;
  }

  inline void operator+=(const value_type& val)
  {
    for (iterator it = begin(); it != end(); ++it)
      *it += val;
  }

  inline void operator-=(const value_type& val)
  {
    for (iterator it = begin(); it != end(); ++it)
      *it -= val;
  }

  inline void operator*=(const value_type& val)
  {
    for (iterator it = begin(); it != end(); ++it)
      *it *= val;
  }

  inline void operator/=(const value_type& val)
  {
    for (iterator it = begin(); it != end(); ++it)
      *it /= val;
  }

  inline T trace() const
  {
    size_type step = ncols_ + 1;
    const_iterator it = begin(), it_end = end() + step;
    T t = *it; ++it;
    for (; it != it_end; it += step)
      t += *it;
    return t;
  }

  /**
   * Multiply row r by vector x.
   */
  template <typename It>
  inline T row_mult(size_type r, It x_it) const
  {
    const_iterator it = begin(r), it_end = end(r);
    value_type val = *it * *x_it; ++x_it; ++it;

    while (it != it_end) {
      val = *it * *x_it;
      ++x_it; ++it;
    }

    return val;
  }

  template <typename stream_type>
  inline void save(stream_type& outStream) const
  {
    outStream << nrows() << ' ' << ncols() << ' ';
    const_iterator it = begin(), it_end = end();
    while (it != it_end) {
      outStream << *it << ' ';
      ++it; 
    }
  }

  template <typename stream_type>
  inline void load(stream_type& inStream)
  {
    inStream >> nrows_ >> ncols_;
    assert(nrows_ >= 0);
    assert(ncols_ >= 0);
    size_type n = nrows_ * ncols_;
    delete [] d;
    d = new value_type[n];
    d_end = d + n;
    iterator it = d;
    while (it != d_end) {
      inStream >> *it;
      ++it;
    }
  }
};

//--------------------------------------------------------------------------------
template <typename stream_type, typename S, typename T>
inline stream_type& operator<<(stream_type& out, const array2D<S,T>& m)
{
  typedef typename array2D<S,T>::const_iterator const_iterator;
  const_iterator it = m.begin(), end = m.end(), row_end = it;

  while (it != end) {
    row_end += m.ncols();
    while (it != row_end) {
      out << *it << ' ';
      ++it;
    }
    out << '\n';
  }

  return out;
}

//--------------------------------------------------------------------------------
template <typename stream_type, typename S, typename T>
inline stream_type& operator<<(stream_type& out, const array2D<S,T*>& m)
{
  typedef typename array2D<S,T>::const_iterator const_iterator;
  const_iterator it = m.begin(), end = m.end(), row_end = it;

  while (it != end) {
    row_end += m.ncols();
    while (it != row_end) {
      out << *it << '/' << **it << ' ';
      ++it;
    }
    out << '\n';
  }

  return out;
}

//--------------------------------------------------------------------------------
template <typename stream_type, typename S, typename T>
inline void print(stream_type& out, const array2D<S,T>& v, S m1, S n1, S m2, S n2)
{
  if (m2 > v.nrows())
    m2 = v.nrows();

  if (m1 >= m2)
    return;

  if (n2 > v.ncols())
    n2 = v.ncols();
  
  if (n1 >= n2)
    return;

  for (S i = m1; i < m2; ++i) {
    for (S j = n1; j < n2; ++j)
      out << v(i,j) << ' ';
    out << " ... \n";
  }
  out << " ...";
}

//--------------------------------------------------------------------------------
#endif // NTA_ARRAY2D_HPP
