%{
#include <Python.h>
#include <nta/types/Exception.hpp>
#include <py_support/PyHelpers.hpp>
#include <iostream>
%}

%exception
{
  // simplified from NuPIC 1.x exception_py.i and nupic_cpplibs/PythonExceptions.hpp
  try
  {
    $action
  }
  catch (const nta::Exception & e)
  {
    // Don't replace the error message if it is already set
    if (!PyErr_Occurred())
    {
      // Create a RuntimeError Python exception object
      nta::py::Tuple args(1);
      args.setItem(0, nta::py::String(e.getMessage()));
      nta::py::Instance ex(PyExc_RuntimeError, args);
  
      // Add a new attribute "stackTrace" if available
      if (e.getStackTrace())
      {
        ex.setAttr("stackTrace", nta::py::String(e.getStackTrace()));
        //nta::py::String st(ex.getAttr("stackTrace"));
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

