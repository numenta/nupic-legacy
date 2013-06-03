
/* Add PyOS_snprintf for old Pythons */
#if PY_VERSION_HEX < 0x02020000
# if defined(_MSC_VER) || defined(__BORLANDC__) || defined(_WATCOM)
#  define PyOS_snprintf _snprintf
# else
#  define PyOS_snprintf snprintf
# endif
#endif

/* A crude PyString_FromFormat implementation for old Pythons */
#if PY_VERSION_HEX < 0x02020000

#ifndef SWIG_PYBUFFER_SIZE
# define SWIG_PYBUFFER_SIZE 1024
#endif

static PyObject *
PyString_FromFormat(const char *fmt, ...) {
  va_list ap;
  char buf[SWIG_PYBUFFER_SIZE * 2];
  int res;
  va_start(ap, fmt);
  res = vsnprintf(buf, sizeof(buf), fmt, ap);
  va_end(ap);
  return (res < 0 || res >= (int)sizeof(buf)) ? 0 : PyString_FromString(buf);
}
#endif

/* Add PyObject_Del for old Pythons */
#if PY_VERSION_HEX < 0x01060000
# define PyObject_Del(op) PyMem_DEL((op))
#endif
#ifndef PyObject_DEL
# define PyObject_DEL PyObject_Del
#endif

/* A crude PyExc_StopIteration exception for old Pythons */
#if PY_VERSION_HEX < 0x02020000
# ifndef PyExc_StopIteration
#  define PyExc_StopIteration PyExc_RuntimeError
# endif
# ifndef PyObject_GenericGetAttr
#  define PyObject_GenericGetAttr 0
# endif
#endif
/* Py_NotImplemented is defined in 2.1 and up. */
#if PY_VERSION_HEX < 0x02010000
# ifndef Py_NotImplemented
#  define Py_NotImplemented PyExc_RuntimeError
# endif
#endif


/* A crude PyString_AsStringAndSize implementation for old Pythons */
#if PY_VERSION_HEX < 0x02010000
# ifndef PyString_AsStringAndSize
#  define PyString_AsStringAndSize(obj, s, len) {*s = PyString_AsString(obj); *len = *s ? strlen(*s) : 0;}
# endif
#endif

/* PySequence_Size for old Pythons */
#if PY_VERSION_HEX < 0x02000000
# ifndef PySequence_Size
#  define PySequence_Size PySequence_Length
# endif
#endif


/* PyBool_FromLong for old Pythons */
#if PY_VERSION_HEX < 0x02030000
static
PyObject *PyBool_FromLong(long ok)
{
  PyObject *result = ok ? Py_True : Py_False;
  Py_INCREF(result);
  return result;
}
#endif

/* Py_ssize_t for old Pythons */
/* This code is as recommended by: */
/* http://www.python.org/dev/peps/pep-0353/#conversion-guidelines */
#if PY_VERSION_HEX < 0x02050000 && !defined(PY_SSIZE_T_MIN)
typedef int Py_ssize_t;
# define PY_SSIZE_T_MAX INT_MAX
# define PY_SSIZE_T_MIN INT_MIN
#endif
