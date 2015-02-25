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


#include "PyHelpers.hpp"

// Nested namespace nupic::py
namespace nupic { namespace py
{
  static bool runningUnderPython = false;
  
  void setRunningUnderPython()
  {
    runningUnderPython = true;
  }
  
  // ---
  // Get the stack trace from a Python tracebak object
  // ---
  static std::string getTraceback(PyObject * p)
  {
    if (!p)
      return "";

    std::stringstream ss;

    PyTracebackObject * tb = (PyTracebackObject *)p;
    NTA_CHECK(PyTraceBack_Check(tb));

    while (tb)
    {
      PyCodeObject * c = tb->tb_frame->f_code;
      std::string filename(PyString_AsString(c->co_filename));
      std::string function(PyString_AsString(c->co_name));
      int lineno = tb->tb_lineno;
      // Read source line from the file (assumes line is shorter than 256)
      char line[256];
      std::ifstream f(filename.c_str());
      for (int i = 0; i < lineno; ++i)
      {
        f.getline(line, 256);
      }

      ss << "  File \" " 
         << filename
         << ", line " << lineno << ", in " 
         << function
         << std::endl
         << std::string(line)
         << std::endl;
      
      tb = tb->tb_next;
    }

    return ss.str();
  }

  void checkPyError(int lineno)
  {
    if (!PyErr_Occurred())
      return;

    PyObject * exceptionClass = NULL; 
    PyObject * exceptionValue = NULL; 
    PyObject * exceptionTraceback = NULL; 

    // Get the Python exception info
    PyErr_Fetch(&exceptionClass,
                &exceptionValue,
                &exceptionTraceback);

    if (!exceptionValue)
    {
      NTA_THROW << "Python exception raised. Unable to extract info";
    }

    // Normalize the exception value to make sure
    // it is an instance of the exception class
    // (Python often goes crazy with exception values)
    PyErr_NormalizeException(&exceptionClass,
                             &exceptionValue,
                             &exceptionTraceback);
    
    std::string exception;
    std::string traceback;
    if (exceptionValue)
    {
      // Extract the exception message as a string
      PyObject * sExcValue = PyObject_Str(exceptionValue);
      exception = std::string(PyString_AsString(sExcValue));
      traceback = getTraceback(exceptionTraceback);

      Py_XDECREF(sExcValue);
    }

    // If running under Python restore the fetched exception so it can
    // be handled at the Python interpreter level
    
    if (runningUnderPython)
    {
      PyErr_Restore(exceptionClass, exceptionValue, exceptionTraceback);
    }
    else 
    {
      //PyErr_Clear();
      Py_XDECREF(exceptionClass);
      Py_XDECREF(exceptionTraceback);
      Py_XDECREF(exceptionValue);
    }

    // Throw a correponding C++ exception
    throw nupic::Exception(__FILE__, lineno, exception, traceback);
  }

  // ---
  // Implementation of Ptr class
  // ---
  Ptr::Ptr(PyObject * p, bool allowNULL) : p_(p), allowNULL_(allowNULL)
  {
    if (!p && !allowNULL)
      NTA_THROW << "The PyObject * is NULL";
  }

  Ptr::~Ptr()
  {
    Py_XDECREF(p_);
  }

  PyObject * Ptr::release()
  {
    PyObject * result = p_;
    p_ = NULL;
    return result;
  }

  std::string Ptr::getTypeName()
  {
    if (!p_)
      return "(NULL)";

    // Do not wrap t in a Ptr object because it will break
    // the tracing macros (with recursive calls)
    PyObject * t = PyObject_Type(p_);
    std::string result(((PyTypeObject *)t)->tp_name);
    Py_DECREF(t);

    if (PyString_Check(p_)) 
    {
      result += "\"" + std::string(PyString_AsString(p_)) + "\"";
    }
    return result;
  }

  void Ptr::assign(PyObject * p)
  {
    // Identity check
    if (p == p_)
      return;

    // Check for NULL and allow NULL
    NTA_CHECK(p || allowNULL_);
    
    // Verify that the new object type matches the current type
    // unless one of them is NULL
    if (p && p_)
    {        
      NTA_CHECK(PyObject_Type(p_) == PyObject_Type(p));
    }

    // decrease ref count of the existing pointer if not NULL
    Py_XDECREF(p_);
    
    // Assign the new pointer
    p_ = p;
    
    // increment the ref count of the new pointer if not NULL
    Py_XINCREF(p_);
  }

  Ptr::operator PyObject *() 
  {
    return p_; 
  }

  Ptr::operator const PyObject *() const 
  { 
    return p_; 
  }

  bool Ptr::isNULL()
  {
    return p_ == NULL;
  }


  // ---
  // Implementation of String class
  // ---
  String::String(const std::string & s, bool allowNULL) : 
        Ptr(createString_(s.c_str(), s.size()), allowNULL)
  {
  }
    
  String::String(const char * s, size_t size, bool allowNULL) :
      Ptr(createString_(s, size), allowNULL)
  {
  }

  String::String(const char * s, bool allowNULL) :
    Ptr(createString_(s), allowNULL)
  {
  }

  String::String(PyObject * p) : Ptr(p)
  {
    NTA_CHECK(PyString_Check(p));
  }

  String::operator const char * ()
  {
    if (!p_)
      return NULL;

    return PyString_AsString(p_);
  }

  PyObject * String::createString_(const char * s, size_t size)
  {
    if (size == 0)
    {
      NTA_CHECK(s) << "The input string must not be NULL when size == 0";
      size = ::strlen(s);
    }
    return PyString_FromStringAndSize(s, size);
  }

  // --- 
  // Implementation of Int class
  // ---
  Int::Int(long n) : Ptr(PyInt_FromLong(n))
  {
  }
  
  Int::Int(PyObject * p) : Ptr(p)
  {
    NTA_CHECK(PyInt_Check(p));
  }

  Int::operator long()
  {
    NTA_CHECK(p_);
    return PyInt_AsLong(p_);
  }


  // --- 
  // Implementation of Long class
  // ---
  Long::Long(long n) : Ptr(PyInt_FromLong(n))
  {
  }
  
  Long::Long(PyObject * p) : Ptr(p)
  {
    NTA_CHECK(PyLong_Check(p) || PyInt_Check(p));
  }

  Long::operator long()
  {
    NTA_CHECK(p_);
    return PyInt_AsLong(p_);
  }

  // --- 
  // Implementation of UnsignedLong class
  // ---
  UnsignedLong::UnsignedLong(unsigned long n) : Ptr(PyInt_FromLong((long)n))
  {
  }
  
  UnsignedLong::UnsignedLong(PyObject * p) : Ptr(p)
  {
    NTA_CHECK(PyLong_Check(p) || PyInt_Check(p));
  }

  UnsignedLong::operator unsigned long()
  {
    NTA_CHECK(p_);
    return (unsigned long)PyInt_AsLong(p_);
  }

  // --- 
  // Implementation of LongLong class
  // ---
  LongLong::LongLong(long long n) : Ptr(PyLong_FromLongLong(n))
  {
  }
  
  LongLong::LongLong(PyObject * p) : Ptr(p)
  {
    NTA_CHECK(PyLong_Check(p) || PyInt_Check(p));
  }

  LongLong::operator long long()
  {
    NTA_CHECK(p_);
    return PyLong_AsLongLong(p_);
  }


  // --- 
  // Implementation of UnsignedLongLong class
  // ---
  UnsignedLongLong::UnsignedLongLong(unsigned long long n) : 
    Ptr(PyLong_FromUnsignedLongLong(n))
  {
  }
  
  UnsignedLongLong::UnsignedLongLong(PyObject * p) : Ptr(p)
  {
    NTA_CHECK(PyLong_Check(p) || PyInt_Check(p));
  }

  UnsignedLongLong::operator unsigned long long()
  {
    NTA_CHECK(p_);
    return PyLong_AsUnsignedLongLong(p_);
  }

  // --- 
  // Implementation of Float class
  // ---
  Float::Float(const char * n) : Ptr(PyFloat_FromString(String(n), NULL))
  {
  }

  Float::Float(double n) : Ptr(PyFloat_FromDouble(n))
  {
  }
  
  Float::Float(PyObject * p) : Ptr(p)
  {
    NTA_CHECK(PyFloat_Check(p));
  }

  Float::operator double()
  {
    NTA_CHECK(p_);

    return PyFloat_AsDouble(p_);
  }

  double Float::getMax()
  {
    return PyFloat_GetMax();
  }

  double Float::getMin()
  {
    return PyFloat_GetMin();
  }

  // --- 
  // Implementation of Tuple class
  // ---
  Tuple::Tuple(PyObject * p) :
    Ptr(p),
    size_(PyTuple_Size(p))
  {
  }
  
  Tuple::Tuple(Py_ssize_t size) :
    Ptr(PyTuple_New(size)),
    size_(size)
  {
  }

  void Tuple::assign(PyObject * p)
  {
    Ptr::assign(p);
    size_ = PyTuple_Size(p);
  }

  PyObject * Tuple::getItem(Py_ssize_t index)
  {
    NTA_CHECK(index < size_);
    PyObject * p = PyTuple_GetItem(p_, index);
    NTA_CHECK(p);
    // Increment refcount of borrowed item (caller must DECREF)
    Py_INCREF(p);
    return p;
  }

  PyObject * Tuple::fastGetItem(Py_ssize_t index)
  {
    NTA_ASSERT(index < getCount());
    PyObject * p = PyTuple_GET_ITEM(p_, index);
    NTA_ASSERT(p);
    return p;
  }

  void Tuple::setItem(Py_ssize_t index, PyObject * item)
  {
    NTA_CHECK(item);
    NTA_CHECK(index < getCount());

    // Increment refcount, so caller still needs to DECREF the item
    // eventhough PyTuple_SetItem steals the reference
    Py_INCREF(item);

    //! item reference is stolen here
    int res = PyTuple_SetItem(p_, index, item);
    NTA_CHECK(res == 0);
  }

  Py_ssize_t Tuple::getCount()
  {
    return PyTuple_Size(p_);
  }

  // --- 
  // Implementation of List class
  // ---
  List::List(PyObject * p) : Ptr(p)
  {
  }


  List::List() : Ptr(PyList_New(0))
  {
  }

  PyObject * List::getItem(Py_ssize_t index)
  {
    NTA_CHECK(index < getCount());
    PyObject * p = PyList_GetItem(p_, index);
    NTA_CHECK(p);
    // Increment refcount of borrowed item (caller must DECREF)
    Py_INCREF(p);
    return p;
  }

  PyObject * List::fastGetItem(Py_ssize_t index)
  {
    NTA_ASSERT(index < getCount());
    PyObject * p = PyList_GET_ITEM(p_, index);
    NTA_ASSERT(p);
    return p;
  }

  void List::setItem(Py_ssize_t index, PyObject * item)
  {
    NTA_CHECK(item);
    NTA_CHECK(index < getCount());

    // Increment refcount, so caller still needs to DECREF the item
    // eventhough PyList_SetItem steals the reference
    Py_INCREF(item);

    //! item reference is stolen here
    int res = PyList_SetItem(p_, index, item);
    NTA_CHECK(res == 0);
  }

  void List::append(PyObject * item)
  {
    NTA_CHECK(item);

    int res = PyList_Append(p_, item);
    NTA_CHECK(res == 0);
  }

  Py_ssize_t List::getCount()
  {
    return PyList_Size(p_);
  }

  // --- 
  // Implementation of Dict class
  // ---
  Dict::Dict() : Ptr(PyDict_New())
  {
  }

  Dict::Dict(PyObject * dict) : Ptr(dict)
  {
    NTA_CHECK(PyDict_Check(dict));
  }

  PyObject * Dict::getItem(const std::string & name, PyObject * defaultItem)
  {
    // PyDict_GetItem() returns a borrowed reference
    PyObject * pItem = PyDict_GetItem(p_, String(name));
    if (!pItem)
      return defaultItem;

    // Increment ref count, so the caller has to call DECREF
    Py_INCREF(pItem);

    return pItem;
  }

  void Dict::setItem(const std::string & name, PyObject * pItem)
  {
    int res = PyDict_SetItem(p_, String(name), pItem);
    NTA_CHECK(res == 0);
  }


  // --- 
  // Implementation of Module class
  // ---
  Module::Module(const std::string & moduleName) :
      Ptr(createModule_(moduleName))
  {
  }
  
  // Invoke a module method. Equivalent to:
  // return module.method(*args, **kwargs)
  // This code is identical to Instance::invoke
  PyObject * Module::invoke(std::string method, 
                    PyObject * args,
                    PyObject * kwargs)
  {
    NTA_CHECK(p_);
    PyObject * pMethod = getAttr(method);
    NTA_CHECK(PyCallable_Check(pMethod));

    Ptr m(pMethod);
    PyObject * result = PyObject_Call(m, args, kwargs);
    checkPyError(__LINE__);
    NTA_CHECK(result);
    return result;
  }

  // Get an module attribute. Equivalent to:
  //
  // return module.name
  // This code is identical to Instance::getAttr
  PyObject * Module::getAttr(std::string name)
  {
    NTA_CHECK(p_);
    PyObject * attr = PyObject_GetAttrString(p_, name.c_str());
    checkPyError(__LINE__);
    NTA_CHECK(attr);
    return attr;
  }

  PyObject * Module::createModule_(const std::string & moduleName)
  {
    String name(moduleName);
    // Import the module
    PyObject * pModule = PyImport_Import(name);
    checkPyError(__LINE__);

    if (pModule == NULL || !(PyModule_Check(pModule)))
    {
      NTA_THROW << "Unable to import module: " << moduleName;
    }
    return pModule;
  }

  // --- 
  // Implementation of Class class
  // ---
  // Wraps a Python class object and allows invoking class methods
  // The constructor is equivalent the following Python code:
  //
  // from moduleName import className
  Class::Class(const std::string & moduleName, const std::string & className) :
      Ptr(createClass_(Module(moduleName), className))
  {
  }
  
  Class::Class(PyObject * pModule, const std::string & className) :
    Ptr(createClass_(pModule, className))
  {
  }

  // The invoke() method is equivalent the following Python code
  // which invokes a class method:
  //
  // return className.method(*args, **kwargs)
  PyObject * Class::invoke(std::string method, 
                    PyObject * args,
                    PyObject * kwargs)
  {
    NTA_CHECK(p_);
    PyObject * pMethod = PyObject_GetAttrString(p_, method.c_str());
    //printPythonError();      
    NTA_CHECK(pMethod);
    NTA_CHECK(PyCallable_Check(pMethod));

    Ptr m(pMethod);
    PyObject * result = PyObject_Call(m, args, kwargs);
    checkPyError(__LINE__);

    return result;
  }

  PyObject * Class::createClass_(PyObject * pModule, const std::string & className)
  {
    // Get the node class from the module (as a new reference)
    PyObject * pClass = PyObject_GetAttrString(pModule, className.c_str());
    NTA_CHECK(pClass && PyType_Check(pClass));

    return pClass;
  }

  // --- 
  // Implementation of Instance class
  // ---
  // Wraps an instance of a Python object
  
  // A constructor that takes an existing PyObject * (can be NULL too)
  Instance::Instance(PyObject * p) : Ptr(p, p == NULL)
  {
  }

  // A constructor that instantiates an instance of the requested
  // class from the requested module. Equivalent to the follwoing:
  //
  // from moduleName import className
  // instance = className(*args, **kwargs)
  Instance::Instance(const std::string & moduleName, 
             const std::string & className,
             PyObject * args,
             PyObject * kwargs) :
      Ptr(createInstance_(Class(moduleName, className),
                            args,
                            kwargs))
  {
  }
  
  Instance::Instance(PyObject * pClass,                
             PyObject * args,
             PyObject * kwargs) :
    Ptr(createInstance_(pClass, args, kwargs))
  {
  }

  // Return true if the instance has attribute 'name' and false otherwise
  bool Instance::hasAttr(std::string name)
  {
    checkPyError(__LINE__);
    NTA_CHECK(p_);
    return PyObject_HasAttrString(p_, name.c_str()) != 0;
  }

  // Get an instance attribute. Equivalent to:
  //
  // return instance.name
  PyObject * Instance::getAttr(std::string name)
  {
    NTA_CHECK(p_);
    PyObject * attr = PyObject_GetAttrString(p_, name.c_str());
    checkPyError(__LINE__);
    NTA_CHECK(attr);

    return attr;
  }

  // Set an instance attribute. Equivalent to:
  //
  // return instance.name = value
  void Instance::setAttr(std::string name, PyObject * value)
  {
    NTA_CHECK(p_);
    int rc = PyObject_SetAttrString(p_, name.c_str(), value);
    checkPyError(__LINE__);
    NTA_CHECK(rc != -1);
  }


  // Return a string representation of an instance. Equivalent to:
  //
  // return str(instance)
  PyObject * Instance::toString()
  {
    NTA_CHECK(p_);
    PyObject * s = PyObject_Str(p_);
    checkPyError(__LINE__);
    NTA_CHECK(s);

    return s;
  }

  // Invoke an instance method. Equivalent to:
  //
  // return instance.method(*args, **kwargs)
  PyObject * Instance::invoke(std::string method, 
                    PyObject * args,
                    PyObject * kwargs)
  {
    NTA_CHECK(p_);
    PyObject * pMethod = getAttr(method);
    NTA_CHECK(PyCallable_Check(pMethod));

    Ptr m(pMethod);
    PyObject * result = PyObject_Call(m, args, kwargs);
    checkPyError(__LINE__);
    NTA_CHECK(result);
    return result;
  }

  PyObject * Instance::createInstance_(PyObject * pClass,
                             PyObject * args,
                             PyObject * kwargs)
  {
    NTA_CHECK(pClass && PyCallable_Check(pClass));
    NTA_CHECK(args && PyTuple_Check(args));
    NTA_CHECK(!kwargs || PyDict_Check(kwargs));
    
    PyObject * pInstance = PyObject_Call(pClass, args, kwargs);
    checkPyError(__LINE__);
    NTA_CHECK(pInstance);

    return pInstance;
  }

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



