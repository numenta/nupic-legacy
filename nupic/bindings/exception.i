%{
#include <Python.h>
#include <iostream>

#include "nupic/types/Exception.hpp"
#include "nupic/py_support/PyHelpers.hpp"
%}

%exception
{
  // simplified from NuPIC 1.x exception_py.i and nupic_cpplibs/PythonExceptions.hpp
  try
  {
    $action
  }
  catch (const nupic::Exception & e)
  {
    // Don't replace the error message if it is already set
    if (!PyErr_Occurred())
    {
      // Create a RuntimeError Python exception object
      nupic::py::Tuple args(1);
      args.setItem(0, nupic::py::String(e.getMessage()));
      nupic::py::Instance ex(PyExc_RuntimeError, args);
  
      // Add a new attribute "stackTrace" if available
      if (e.getStackTrace())
      {
        ex.setAttr("stackTrace", nupic::py::String(e.getStackTrace()));
        //nupic::py::String st(ex.getAttr("stackTrace"));
        //NTA_DEBUG << "*** stackTrace: " << std::string(st);
        //NTA_ASSERT(!(std::string(st).empty()));
      }
  
      // Set the Python error. Equivalent to: "raise ex"
      PyErr_SetObject(PyExc_RuntimeError, ex);      
    }
    SWIG_fail;
  }

  catch (const std::exception & e)
  {
    // Don't replace the error message if it is already set
    if (!PyErr_Occurred()) 
      PyErr_SetString(PyExc_RuntimeError, const_cast<char *>(e.what()));
    SWIG_fail;
  }

  catch (...)
  {
    // Don't replace the error message if it is already set
    if (!PyErr_Occurred()) 
      PyErr_SetString(PyExc_RuntimeError, "Unknown error from C++ library");
    SWIG_fail;
  }
}

