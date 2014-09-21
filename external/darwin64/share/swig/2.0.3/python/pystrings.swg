/* ------------------------------------------------------------
 *  utility methods for char strings 
 * ------------------------------------------------------------ */
%fragment("SWIG_AsCharPtrAndSize","header",fragment="SWIG_pchar_descriptor") {
SWIGINTERN int
SWIG_AsCharPtrAndSize(PyObject *obj, char** cptr, size_t* psize, int *alloc)
{
%#if PY_VERSION_HEX>=0x03000000
  if (PyUnicode_Check(obj))
%#else  
  if (PyString_Check(obj))
%#endif
  {
    char *cstr; Py_ssize_t len;
%#if PY_VERSION_HEX>=0x03000000
    if (!alloc && cptr) {
        /* We can't allow converting without allocation, since the internal
           representation of string in Python 3 is UCS-2/UCS-4 but we require
           a UTF-8 representation.
           TODO(bhy) More detailed explanation */
        return SWIG_RuntimeError;
    }
    obj = PyUnicode_AsUTF8String(obj);
    PyBytes_AsStringAndSize(obj, &cstr, &len);
    if(alloc) *alloc = SWIG_NEWOBJ;
%#else
    PyString_AsStringAndSize(obj, &cstr, &len);
%#endif
    if (cptr) {
      if (alloc) {
	/* 
	   In python the user should not be able to modify the inner
	   string representation. To warranty that, if you define
	   SWIG_PYTHON_SAFE_CSTRINGS, a new/copy of the python string
	   buffer is always returned.

	   The default behavior is just to return the pointer value,
	   so, be careful.
	*/ 
%#if defined(SWIG_PYTHON_SAFE_CSTRINGS)
	if (*alloc != SWIG_OLDOBJ) 
%#else
	if (*alloc == SWIG_NEWOBJ) 
%#endif
	  {
	    *cptr = %new_copy_array(cstr, len + 1, char);
	    *alloc = SWIG_NEWOBJ;
	  }
	else {
	  *cptr = cstr;
	  *alloc = SWIG_OLDOBJ;
	}
      } else {
        %#if PY_VERSION_HEX>=0x03000000
        assert(0); /* Should never reach here in Python 3 */
        %#endif
	*cptr = SWIG_Python_str_AsChar(obj);
      }
    }
    if (psize) *psize = len + 1;
%#if PY_VERSION_HEX>=0x03000000
    Py_XDECREF(obj);
%#endif
    return SWIG_OK;
  } else {
    swig_type_info* pchar_descriptor = SWIG_pchar_descriptor();
    if (pchar_descriptor) {
      void* vptr = 0;
      if (SWIG_ConvertPtr(obj, &vptr, pchar_descriptor, 0) == SWIG_OK) {
	if (cptr) *cptr = (char *) vptr;
	if (psize) *psize = vptr ? (strlen((char *)vptr) + 1) : 0;
	if (alloc) *alloc = SWIG_OLDOBJ;
	return SWIG_OK;
      }
    }
  }
  return SWIG_TypeError;
}
}

%fragment("SWIG_FromCharPtrAndSize","header",fragment="SWIG_pchar_descriptor") {
SWIGINTERNINLINE PyObject *
SWIG_FromCharPtrAndSize(const char* carray, size_t size)
{
  if (carray) {
    if (size > INT_MAX) {
      swig_type_info* pchar_descriptor = SWIG_pchar_descriptor();
      return pchar_descriptor ? 
	SWIG_NewPointerObj(%const_cast(carray,char *), pchar_descriptor, 0) : SWIG_Py_Void();
    } else {
%#if PY_VERSION_HEX >= 0x03000000
      return PyUnicode_FromStringAndSize(carray, %numeric_cast(size,int));
%#else
      return PyString_FromStringAndSize(carray, %numeric_cast(size,int));
%#endif
    }
  } else {
    return SWIG_Py_Void();
  }
}
}


