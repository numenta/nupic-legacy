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
 * Definitions for the PyArrayBase class
  * 
  * A PyArrayBase object is a Python compatible wrapper around an nupic::Array object
  * 
  * It delegates everything to its Array and exposes a Python facade that
  * includes: indexed access with operator[], len() support, An Array contains:
  * - a pointer to a buffer
  * - a length
  * - a type
  * - a flag indicating whether or not the object owns the buffer. 
  */

#ifndef NTA_PY_ARRAY_HPP
#define NTA_PY_ARRAY_HPP

#include <py_support/PyHelpers.hpp>
#include <nupic/types/Types.h>
#include <nupic/ntypes/Array.hpp>
#include <nupic/ntypes/ArrayRef.hpp>

namespace nupic
{
// -------------------------------------
//
//  G E T   B A S I C   T Y P E
//
// -------------------------------------

NTA_BasicType getBasicType(NTA_Byte);
NTA_BasicType getBasicType(NTA_Int16);
NTA_BasicType getBasicType(NTA_UInt16);
NTA_BasicType getBasicType(NTA_Int32);
NTA_BasicType getBasicType(NTA_UInt32);
NTA_BasicType getBasicType(NTA_Int64);
NTA_BasicType getBasicType(NTA_UInt64);
NTA_BasicType getBasicType(NTA_Real32);
NTA_BasicType getBasicType(NTA_Real64);

// -------------------------------------
//
//  A R R A Y    2   N U M P Y
//
// -------------------------------------
// Wrap an Array object with a numpy array PyObject
PyObject * array2numpy(const ArrayBase & a);

// -------------------------------------
//
//  P Y   A R R A Y   B A S E
//
// -------------------------------------
//template<typename T, typename A>
//class PyArrayBase : public A
//{
//public:
//  PyArrayBase();
//  //PyArrayBase(A * a);
//  //PyArrayBase(ArrayBase * a);
//    
//  NTA_BasicType getType();
//  T __getitem__(int i) const;
//  void __setitem__(int i, T x);
//  size_t __len__() const;
//  std::string __repr__() const;
//  std::string __str__() const;
//  PyObject * asNumpyArray() const;
//};

// -------------------------------------
//
//  P Y   A R R A Y
//
// -------------------------------------
template<typename T>
class PyArray : public Array //public PyArrayBase<T, Array>
{
public:
  PyArray();
  PyArray(size_t count);
  //PyArray(Array * a);    
  //PyArray(ArrayBase * a);    

  NTA_BasicType getType();
  T __getitem__(int i) const;
  void __setitem__(int i, T x);
  size_t __len__() const;
  std::string __repr__() const;
  std::string __str__() const;
  PyObject * asNumpyArray() const;
};


// -------------------------------------
//
//  P Y   A R R A Y   R E F
//
// -------------------------------------
template<typename T>
class PyArrayRef : public ArrayRef
{
public:
  PyArrayRef();
  PyArrayRef(const ArrayRef & a);
  
  NTA_BasicType getType();
  T __getitem__(int i) const;
  void __setitem__(int i, T x);
  size_t __len__() const;
  std::string __repr__() const;
  std::string __str__() const;
  PyObject * asNumpyArray() const;
};


}

#endif

