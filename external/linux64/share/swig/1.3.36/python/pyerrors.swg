/* -----------------------------------------------------------------------------
 * error manipulation
 * ----------------------------------------------------------------------------- */

SWIGRUNTIME PyObject*
SWIG_Python_ErrorType(int code) {
  PyObject* type = 0;
  switch(code) {
  case SWIG_MemoryError:
    type = PyExc_MemoryError;
    break;
  case SWIG_IOError:
    type = PyExc_IOError;
    break;
  case SWIG_RuntimeError:
    type = PyExc_RuntimeError;
    break;
  case SWIG_IndexError:
    type = PyExc_IndexError;
    break;
  case SWIG_TypeError:
    type = PyExc_TypeError;
    break;
  case SWIG_DivisionByZero:
    type = PyExc_ZeroDivisionError;
    break;
  case SWIG_OverflowError:
    type = PyExc_OverflowError;
    break;
  case SWIG_SyntaxError:
    type = PyExc_SyntaxError;
    break;
  case SWIG_ValueError:
    type = PyExc_ValueError;
    break;
  case SWIG_SystemError:
    type = PyExc_SystemError;
    break;
  case SWIG_AttributeError:
    type = PyExc_AttributeError;
    break;
  default:
    type = PyExc_RuntimeError;
  }
  return type;
}


SWIGRUNTIME void
SWIG_Python_AddErrorMsg(const char* mesg)
{
  PyObject *type = 0;
  PyObject *value = 0;
  PyObject *traceback = 0;

  if (PyErr_Occurred()) PyErr_Fetch(&type, &value, &traceback);
  if (value) {
    PyObject *old_str = PyObject_Str(value);
    PyErr_Clear();
    Py_XINCREF(type);
    PyErr_Format(type, "%s %s", PyString_AsString(old_str), mesg);
    Py_DECREF(old_str);
    Py_DECREF(value);
  } else {
    PyErr_SetString(PyExc_RuntimeError, mesg);
  }
}


