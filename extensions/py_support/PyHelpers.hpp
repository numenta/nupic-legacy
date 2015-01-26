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

#ifndef NTA_PY_HELPERS_HPP
#define NTA_PY_HELPERS_HPP

// The Python.h #include MUST always be #included first in every
// compilation unit (.c or .cpp file). That means that PyHelpers.hpp
// must be #included first and transitively every .hpp file that 
// #includes directly or indirectly PyHelpers.hpp must be #included
// first.
#include <Python.h>
#include <frameobject.h>

#include <nupic/utils/Log.hpp>
#include <iostream>
#include <fstream>

// ===
// ---------------------------------
//
//   P Y   H E L P E R S
//
// ---------------------------------
//
// The PyHelpers module contain C++ classes that wrap Python C-API
// objects and allows working with Python C-API in a safe and user 
// friendly manner. Please refer to the Python C-API docs for general
// background: http://docs.python.org/c-api/
//
// The purpose of this module is to support internally the C++ PyNode
// class and it implements exactly the classes needed by PyNode. 
// It is not a comprehensive wrapper around the Python C-API.
// 
//The follwoing classes are implemented in the
// namespac nupic::py
//
// Ptr:
//   A class that manages a PyObject pointer and serves as base class
//   for all other helper objects
// 
// Int, Long, LongLong, UnsignedLong, UnsignedLongLong: 
//   Integral types that match the corresponding C integral types and
//   map to either the Python int or Python long types. They provide
//   constructors and conversion operators that were chosen to reflect
//   the underlying Python C API functions (e.g. PyInt_FromLong() and
//   PyInt_AsLong()).
//
// Float:
//   A floating point number class that maps a double precision C double
//   to a Python float. It provides a constructor and conversion operator.
//   Python has just one floating point type (not including numpy and 
//   the complex type).
// 
// String: 
//   A string type that maps to the Python string and provides
//   a constractor and conversion operator for the C char * type.
//
// Tuple, Dict:
//   Sequence types that map to the Python tuple and dict. They provide
//   a safe getItem() and setItem() that don't borrow or steal references.
//
// Module, Class, Instance:
//   Types for working with the Python object system. Module is for importing
//   modules. Class is for invoking class methods and Instance is for 
//   instantiating objects and invoking their methods.
// ===

// Nested namespace nupic::py
namespace nupic { namespace py
{
  void setRunningUnderPython();
  
  
  void checkPyError(int lineno);

  // A RAII class to hold a PyObject *
  // It decrements the refCount when it 
  // is destroyed.
  //
  // Ptr objects can be passed directly to Python C API calls.
  // Most functions just use the object and when the function 
  // returns the refCount stays the same. Some functions take
  // ownership of the PyObject pointer. In this case you should
  // call release().
  //
  // The Ptr class also serves as the base class for all the other helper
  // classes that rely on it to manage the underlying PyObject * and
  // just add type checks and type-specific constructors, conversion
  // operator and special methods.
  //
  // In general, the specific sub-classes should be used to store Python
  // objects (e.g use PyDict to store a dict object). You should use PyPtr
  // directly only when storing Python objects that don't have a 
  // corresponding PyHelpers sub-class.
  class Ptr
  {
  public:
    // Constructor of the Ptr class
    //
    // PyObject * p   - the managed pointer (ref count not incremented)
    // bool allowNULL - If false (default) p must not be NULL
    //
    Ptr(PyObject * p, bool allowNULL = false);

    virtual ~Ptr();

    // Relinquish ownership of this object. Call release()
    // if you pass the Ptr to a function that takes ownership
    // like PyTuple_SetItem()
    PyObject * release();
    std::string getTypeName();
    void assign(PyObject * p);
    operator PyObject *();
    operator const PyObject *() const;
    bool isNULL();
  private:
    // This constructors MUST never be implemented to maintain 
    // the integrity of the Ptr class. As a RAII class you don't
    // want copies sharing (and later releasing) the same pointer.
    Ptr();
    Ptr(const Ptr &);

  protected:  
    PyObject * p_;
    bool allowNULL_;
  };


  // String 
  class String : public Ptr
  {
  public:
    explicit String(const std::string & s, bool allowNULL = false);
    explicit String(const char * s, size_t size, bool allowNULL = false);
    explicit String(const char * s, bool allowNULL = false);
    explicit String(PyObject * p);

    operator const char * ();

  private:
    PyObject * createString_(const char * s, size_t size = 0);
  };

  // Int 
  class Int : public Ptr
  {
  public:
    Int(long n);
    Int(PyObject * p);
    operator long();
  };

  // Long 
  class Long : public Ptr
  {
  public:
    Long(long n);
    Long(PyObject * p);
    operator long();
  };

  // UnsignedLong 
  class UnsignedLong : public Ptr
  {
  public:
    UnsignedLong(unsigned long n);
    UnsignedLong(PyObject * p);
    operator unsigned long();
  };

  // LongLong 
  class LongLong : public Ptr
  {
  public:
    LongLong(long long n);
    LongLong(PyObject * p);
    operator long long();
  };

  // UnsignedLongLong 
  class UnsignedLongLong : public Ptr
  {
  public:
    UnsignedLongLong(unsigned long long n);
    UnsignedLongLong(PyObject * p);
    operator unsigned long long();
  };


  // Float 
  class Float : public Ptr
  {
  public:
    Float(const char * n);
    Float(double n);
    Float(PyObject * p);
    operator double();
    static double getMax();
    static double getMin();
  };

  // Tuple
  class Tuple : public Ptr
  {
  public:
    Tuple(Py_ssize_t size = 0);
    Tuple(PyObject * p);
    void assign(PyObject *);
    
    PyObject * getItem(Py_ssize_t index);
    
    // The fast version of getItem() doesn't do bounds checking
    // and doesn't increment the ref count of returned item. The original
    // tuple still owns the item. If you try to access out of bounds item
    // you will crash (or worse). If you assign the returned item to a py::Ptr
    // or a sub-class you MUST call release() to prevent the py::Ptr from
    // decrementing the ref count
    PyObject * fastGetItem(Py_ssize_t index);
    void setItem(Py_ssize_t index, PyObject * item);
    Py_ssize_t getCount();
  private:
    Py_ssize_t size_;
  };

  // List
  class List : public Ptr
  {
  public:
    List();
    List(PyObject *);
    PyObject * getItem(Py_ssize_t index);

    // The fast version of getItem() doesn't do bounds checking
    // and doesn't increment the ref count of returned item. The original
    // list still owns the item. If you try to access out of bounds item
    // you will crash (or worse). If you assign the returned item to a py::Ptr
    // or a sub-class you MUST call release() to prevent the py::Ptr from
    // decrementing the ref count
    PyObject * fastGetItem(Py_ssize_t index);
    void setItem(Py_ssize_t index, PyObject * item);
    void append(PyObject * item);
    Py_ssize_t getCount();
  };

  // Dict
  class Dict : public Ptr
  {
  public:
    Dict();
    Dict(PyObject * dict);
    PyObject * getItem(const std::string & name, PyObject * defaultItem = NULL);
    void setItem(const std::string & name, PyObject * pItem);
  };

  // Module 
  //
  // Wraps a Python module object and can import by name
  // The Python interpreter sys.path must contain the
  // requested module.
  class Module : public Ptr
  {
  public:
    Module(const std::string & moduleName);
    
    // Invoke a module method. Equivalent to:
    // return module.method(*args, **kwargs)
    // This code is identical to Instance::invoke
    PyObject * invoke(std::string method, 
                      PyObject * args,
                      PyObject * kwargs = NULL);
    // Get an module attribute. Equivalent to:
    //
    // return module.name
    // This code is identical to Instance::getAttr
    PyObject * getAttr(std::string name);
  private:
    PyObject * createModule_(const std::string & moduleName);
  };

  // Class 
  //
  // Wraps a Python class object and allows invoking class methods
  class Class : public Ptr
  {
  public:
    // The constructor is equivalent the following Python code:
    //
    // from moduleName import className
    Class(const std::string & moduleName, const std::string & className);
    Class(PyObject * pModule, const std::string & className);

    // The invoke() method is equivalent the following Python code
    // which invokes a class method:
    //
    // return className.method(*args, **kwargs)
    PyObject * invoke(std::string method, 
                      PyObject * args,
                      PyObject * kwargs = NULL);
  private:
    PyObject * createClass_(PyObject * pModule, const std::string & className);
  };


  // Instance 
  //
  // Wraps an instance of a Python object
  class Instance : public Ptr
  {
  public:
    // A constructor that takes an existing PyObject * (can be NULL too)
    Instance(PyObject * p = NULL);

    // A constructor that instantiates an instance of the requested
    // class from the requested module. Equivalent to the follwoing:
    //
    // from moduleName import className
    // instance = className(*args, **kwargs)
    Instance(const std::string & moduleName, 
               const std::string & className,
               PyObject * args,
               PyObject * kwargs = NULL);

    Instance(PyObject * pClass,                
               PyObject * args,
               PyObject * kwargs = NULL);

    // Return true if the instance has attribute 'name' and false otherwise
    bool hasAttr(std::string name);

    // Get an instance attribute. Equivalent to:
    //
    // return instance.name
    PyObject * getAttr(std::string name);

    // Set an instance attribute. Equivalent to:
    //
    // return instance.name = value
    void setAttr(std::string name, PyObject * value);

    // Return a string representation of an instance. Equivalent to:
    //
    // return str(instance)
    PyObject * toString();

    // Invoke an instance method. Equivalent to:
    //
    // return instance.method(*args, **kwargs)
    PyObject * invoke(std::string method, 
                      PyObject * args,
                      PyObject * kwargs = NULL);
  private:
    PyObject * createInstance_(PyObject * pClass,
                               PyObject * args,
                               PyObject * kwargs);
  };

  //// ---
  //// Raise a Python RuntimeError exception from C++ with
  //// an error message and an optional stack trace. The 
  //// stack trace will be added as a custom attribute of the
  //// exception object. 
  //// ---
  //void setPyError(const char * message, const char * stackTrace = NULL)
  //{
  //  // Create a RuntimeError Python exception object
  //  Tuple args(1);
  //  args.setItem(0, py::String(message));
  //  Instance e(PyExc_RuntimeError, args);

  //  // Add a new attribute "stackTrace" if available
  //  if (stackTrace)
  //  {
  //    e.setAttr("stackTrace", py::String(stackTrace));
  //  }

  //  // Set the Python error. Equivalent to: "raise e"
  //  PyErr_SetObject(PyExc_RuntimeError, e);
  //}



} } // end of nupic::py namespace

#endif // NTA_PY_HELPERS_HPP

