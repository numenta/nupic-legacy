#ifndef NTA_NUMPY_VECTOR_HPP
#define NTA_NUMPY_VECTOR_HPP

#ifdef NTA_PYTHON_SUPPORT

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
 * Contains the NumpyArray class, a wrapper for Python numpy arrays.
 */

#include <nupic/types/Types.hpp> // For nupic::Real.
#include <algorithm> // For std::copy.
#include <numpy/arrayobject.h>

namespace nupic {

  extern int LookupNumpyDType(const size_t *);
  extern int LookupNumpyDType(const nupic::Byte *);
  extern int LookupNumpyDType(const nupic::Int16 *);
  extern int LookupNumpyDType(const nupic::UInt16 *);
  extern int LookupNumpyDType(const nupic::Int32 *);
  extern int LookupNumpyDType(const nupic::UInt32 *);
  extern int LookupNumpyDType(const nupic::Int64 *);
  extern int LookupNumpyDType(const nupic::UInt64 *);
  extern int LookupNumpyDType(const nupic::Real32 *);
  extern int LookupNumpyDType(const nupic::Real64 *);
#if defined(NTA_QUAD_PRECISION)
  extern int LookupNumpyDType(const nupic::Real128 *);
#endif
  /**
   * Concrete Numpy multi-d array wrapper who's implementation cannot be visible
   * due to the specifics of dynamically loading the Numpy C function API.
   */
  class NumpyArray
  {

    NumpyArray(const NumpyArray &); // Verboten.
    NumpyArray &operator=(const NumpyArray &); // Verboten.

  protected:
    const PyArrayObject *p_;
    int dtype_;

    const char *addressOf0() const;
    char *addressOf0();
    int stride(int i) const;

    NumpyArray(int nd, const int *dims, int dtype);
    NumpyArray(PyObject *p, int dtype, int requiredDimension=0);

  public:

    ///////////////////////////////////////////////////////////
    /// Destructor.
    ///
    /// Releases the reference to the internal numpy array.
    ///////////////////////////////////////////////////////////
    virtual ~NumpyArray();

    ///////////////////////////////////////////////////////////
    /// Initializes the numpy library.
    /// Called automatically when constructing a NumpyArray.
    ///////////////////////////////////////////////////////////
    static void init();

    ///////////////////////////////////////////////////////////
    /// The number of dimensions of the internal numpy array.
    ///
    /// Will always be 1, as enforced by the constructors.
    ///////////////////////////////////////////////////////////
    int numDimensions() const { return getRank(); }

    int getRank() const;

    ///////////////////////////////////////////////////////////
    /// Gets the size of the array along dimension i.
    ///
    /// Does not check the validity of the passed-in dimension.
    ///////////////////////////////////////////////////////////
    int dimension(int i) const;


    void getDims(int *) const;

    ///////////////////////////////////////////////////////////
    /// Gets the size of the array (along dimension 0).
    ///////////////////////////////////////////////////////////
    int size() const { return dimension(0); }

    ///////////////////////////////////////////////////////////
    /// Returns a PyObject that can be returned from C code to Python.
    ///
    /// The PyObject returned is a new reference, and the caller must
    /// dereference the object when done.
    /// The PyObject is produced by PyArray_Return (whatever that does).
    ///////////////////////////////////////////////////////////
    PyObject *forPython();

  };

  ///////////////////////////////////////////////////////////
  /// A wrapper for 1D numpy arrays of data type equaivalent to nupic::Real.
  ///
  /// Numpy is a Python extension written in C.
  /// Accessing numpy's C API directly is tricky but possible.
  /// Such access can be performed with SWIG typemaps,
  /// using a slow and feature-poor set of SWIG typemap definitions
  /// provided as an example with the numpy documentation.
  /// This class bypasses that method of access, in favor of
  /// a faster interface that nags (warns) about potential performance
  /// problems. This wrapper should only be used within Python bindings,
  /// as numpy data structures will only be passed in from Python code.
  /// For an example of its use, see the nupic::SparseMatrix Python bindings
  /// in nupic/python/bindings/math/SparseMatrix.i
  ///////////////////////////////////////////////////////////
  template<typename T=nupic::Real>
  class NumpyVectorT : public NumpyArray
  {

    NumpyVectorT(const NumpyVectorT<T> &); // Verboten.
    NumpyVectorT<T> &operator=(const NumpyVectorT<T> &); // Verboten.

  public:

    ///////////////////////////////////////////////////////////
    /// Create a new 1D numpy array of size n.
    ///////////////////////////////////////////////////////////
    NumpyVectorT(int n, const T& val=0)
      : NumpyArray(1, &n, LookupNumpyDType((const T *) 0))
    {
      std::fill(begin(), end(), val);
    }

    NumpyVectorT(int n, const T *val)
      : NumpyArray(1, &n, LookupNumpyDType((const T *) 0))
    {
      if(val) std::copy(val, val+n, begin());
    }

    ///////////////////////////////////////////////////////////
    /// Reference an existing 1D numpy array, or copy it if
    /// it differs in type.
    ///
    /// Produces a really annoying warning if this will do a slow copy.
    /// Do not use in this case. Make sure the data coming in is in
    /// the appropriate format (1D contiguous numpy array of type
    /// equivalent to nupic::Real). If nupic::Real is float,
    /// the incoming array should have been created with dtype=numpy.float32
    ///
    /// @note I do not believe the data is copied unless necessary.
    ///       This has not been confirmed.
    ///       This means that ownership has two very different semantics:
    ///       if the data is not copied, then any modifications to this
    ///       vector affect the original.
    ///       If the data is copied (slow), then any modifications do not
    ///       affect the original.
    ///////////////////////////////////////////////////////////
    NumpyVectorT(PyObject *p)
      : NumpyArray(p, LookupNumpyDType((const T *) 0), 1)
    {}

    virtual ~NumpyVectorT() {}

    T* begin() { return addressOf(0); }
    T* end() { return begin() + size(); }
    const T* begin() const { return addressOf(0); }
    const T* end() const { return begin() + size(); }

    ///////////////////////////////////////////////////////////
    /// Get a pointer to element i.
    ///
    /// Does not check the validity of the index.
    ///////////////////////////////////////////////////////////
    const T *addressOf(int i) const
    { return (const T *) (addressOf0() + i*stride(0)); }

    ///////////////////////////////////////////////////////////
    /// Get a non-const pointer to element i.
    ///
    /// Does not check the validity of the index.
    ///////////////////////////////////////////////////////////
    T *addressOf(int i)
    { return (T *) (addressOf0() + i*stride(0)); }

    ///////////////////////////////////////////////////////////
    /// Get the increment (in number of Reals) from one element
    /// to the next.
    ///////////////////////////////////////////////////////////
    int incr() const { return int(addressOf(1) - addressOf(0)); }

    inline T& get(int i) { return *addressOf(i); }
    inline T get(int i) const { return *addressOf(i); }
    inline void set(int i, const T& val) { *addressOf(i) = val; }
  };

  //--------------------------------------------------------------------------------
  template<typename T=nupic::Real>
  class NumpyMatrixT : public NumpyArray
  {
    NumpyMatrixT(const NumpyMatrixT &); // Verboten.
    NumpyMatrixT &operator=(const NumpyMatrixT &); // Verboten.

  public:

    typedef int size_type;

    ///////////////////////////////////////////////////////////
    /// Create a new 2D numpy array of size n.
    ///////////////////////////////////////////////////////////
    NumpyMatrixT(const int nRowsCols[2])
      : NumpyArray(2, nRowsCols, LookupNumpyDType((const T *) 0))
    {}

    NumpyMatrixT(PyObject *p)
      : NumpyArray(p, LookupNumpyDType((const T *) 0), 2)
    {}

    ///////////////////////////////////////////////////////////
    /// Destructor.
    ///
    /// Releases the reference to the internal numpy array.
    ///////////////////////////////////////////////////////////
    virtual ~NumpyMatrixT() {}

    int rows() const { return dimension(0); }
    int columns() const { return dimension(1); }
    int nRows() const { return dimension(0); }
    int nCols() const { return dimension(1); }

    inline const T *addressOf(int row, int col) const
    { return (const T *) (addressOf0() + row*stride(0) + col*stride(1)); }

    inline T *addressOf(int row, int col)
    { return (T *) (addressOf0() + row*stride(0) + col*stride(1)); }

    inline const T* begin(int row) const
    { return (const T*)(addressOf0() + row*stride(0)); }

    inline const T* end(int row) const
    { return (const T*)(addressOf0() + row*stride(0) + nCols()*stride(1)); }

    inline T* begin(int row)
    { return (T*)(addressOf0() + row*stride(0)); }

    inline T* end(int row)
    { return (T*)(addressOf0() + row*stride(0) + nCols()*stride(1)); }

    inline T& get(int i, int j) { return *addressOf(i,j); }
    inline T get(int i, int j) const { return *addressOf(i,j); }
    inline void set(int i, int j, const T& val) { *addressOf(i,j) = val; }
  };

  template<typename T=nupic::Real>
  class NumpyNDArrayT : public NumpyArray
  {
    NumpyNDArrayT(const NumpyNDArrayT &); // Verboten.
    NumpyNDArrayT &operator=(const NumpyNDArrayT &); // Verboten.

  public:
    NumpyNDArrayT(PyObject *p)
      : NumpyArray(p, LookupNumpyDType((const T *) 0))
    {}
    NumpyNDArrayT(int rank, const int *dims)
      : NumpyArray(rank, dims, LookupNumpyDType((const T *) 0))
    {}
    virtual ~NumpyNDArrayT() {}

    const T *getData() const { return (const T *) addressOf0(); }
    T *getData() { return (T *) addressOf0(); }
  };

  //--------------------------------------------------------------------------------
  typedef NumpyVectorT<> NumpyVector;
  typedef NumpyMatrixT<> NumpyMatrix;
  typedef NumpyNDArrayT<> NumpyNDArray;

  //--------------------------------------------------------------------------------
  template <typename T>
  inline T convertToValueType(PyObject *val)
  {
    return * nupic::NumpyNDArrayT<T>(val).getData();
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline PyObject* convertFromValueType(const T& value) {
    nupic::NumpyNDArrayT<T> ret(0, NULL);
    *ret.getData() = value;
    return ret.forPython();
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename T>
  inline PyObject* convertToPairOfLists(I i_begin, I i_end, T val)
  {
    const size_t n = (size_t) (i_end - i_begin);

    PyObject *indOut = PyTuple_New(n);
    // Steals the new references.
    for (size_t i = 0; i != n; ++i, ++i_begin)
      PyTuple_SET_ITEM(indOut, i, PyInt_FromLong(*i_begin));

    PyObject *valOut = PyTuple_New(n);
    // Steals the new references.
    for (size_t i = 0; i != n; ++i, ++val)
      PyTuple_SET_ITEM(valOut, i, PyFloat_FromDouble(*val));

    PyObject *toReturn = PyTuple_New(2);
    // Steals the index tuple reference.
    PyTuple_SET_ITEM(toReturn, 0, indOut);
    // Steals the index tuple reference.
    PyTuple_SET_ITEM(toReturn, 1, valOut);

    // Returns a single new reference.
    return toReturn;
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename T>
  inline PyObject* createPair32(I i, T v)
  {
    PyObject *result = PyTuple_New(2);
    PyTuple_SET_ITEM(result, 0, PyInt_FromLong(i));
    PyTuple_SET_ITEM(result, 1, PyFloat_FromDouble(v));
    return result;
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename T>
  inline PyObject* createPair64(I i, T v)
  {
    PyObject *result = PyTuple_New(2);
    PyTuple_SET_ITEM(result, 0, PyLong_FromLongLong(i));
    PyTuple_SET_ITEM(result, 1, PyFloat_FromDouble(v));
    return result;
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename T>
  inline PyObject* createTriplet32(I i1, I i2, T v1)
  {
    PyObject *result = PyTuple_New(3);
    PyTuple_SET_ITEM(result, 0, PyInt_FromLong(i1));
    PyTuple_SET_ITEM(result, 1, PyInt_FromLong(i2));
    PyTuple_SET_ITEM(result, 2, PyFloat_FromDouble(v1));
    return result;
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename T>
  inline PyObject* createTriplet64(I i1, I i2, T v1)
  {
    PyObject *result = PyTuple_New(3);
    PyTuple_SET_ITEM(result, 0, PyLong_FromLongLong(i1));
    PyTuple_SET_ITEM(result, 1, PyLong_FromLongLong(i2));
    PyTuple_SET_ITEM(result, 2, PyFloat_FromDouble(v1));
    return result;
  }

  //--------------------------------------------------------------------------------
  template <typename TIter>
  PyObject* PyInt32Vector(TIter begin, TIter end)
  {
    Py_ssize_t n = end - begin;
    PyObject *p = PyTuple_New(n);
    Py_ssize_t i = 0;
    for (TIter cur=begin; cur!=end; ++cur, ++i) {
      PyTuple_SET_ITEM(p, i, PyInt_FromLong(*cur));
    }

    return p;
  }

  //--------------------------------------------------------------------------------
  template <typename TIter>
  PyObject* PyInt64Vector(TIter begin, TIter end)
  {
    Py_ssize_t n = end - begin;
    PyObject *p = PyTuple_New(n);
    Py_ssize_t i = 0;
    for (TIter cur=begin; cur!=end; ++cur, ++i) {
      PyTuple_SET_ITEM(p, i, PyLong_FromLongLong(*cur));
    }

    return p;
  }

  //--------------------------------------------------------------------------------
  template <typename TIter>
  PyObject* PyFloatVector(TIter begin, TIter end)
  {
    Py_ssize_t n = end - begin;
    PyObject *p = PyTuple_New(n);
    Py_ssize_t i = 0;
    for (TIter cur=begin; cur!=end; ++cur, ++i) {
      PyTuple_SET_ITEM(p, i, PyFloat_FromDouble(*cur));
    }

    return p;
  }

  //--------------------------------------------------------------------------------

} // End namespace nupic.

#endif // NTA_PYTHON_SUPPORT

#endif

