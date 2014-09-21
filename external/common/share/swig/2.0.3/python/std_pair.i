/*
  Pairs
*/
%include <pystdcommon.swg>

//#define SWIG_STD_PAIR_ASVAL

%fragment("StdPairTraits","header",fragment="StdTraits") {
  namespace swig {
#ifdef SWIG_STD_PAIR_ASVAL
    template <class T, class U >
    struct traits_asval<std::pair<T,U> >  {
      typedef std::pair<T,U> value_type;

      static int get_pair(PyObject* first, PyObject* second,
			  std::pair<T,U> *val)
      {
	if (val) {
	  T *pfirst = &(val->first);
	  int res1 = swig::asval((PyObject*)first, pfirst);
	  if (!SWIG_IsOK(res1)) return res1;
	  U *psecond = &(val->second);
	  int res2 = swig::asval((PyObject*)second, psecond);
	  if (!SWIG_IsOK(res2)) return res2;
	  return res1 > res2 ? res1 : res2;
	} else {
	  T *pfirst = 0;
	  int res1 = swig::asval((PyObject*)first, 0);
	  if (!SWIG_IsOK(res1)) return res1;
	  U *psecond = 0;
	  int res2 = swig::asval((PyObject*)second, psecond);
	  if (!SWIG_IsOK(res2)) return res2;
	  return res1 > res2 ? res1 : res2;
	}	
      }

      static int asval(PyObject *obj, std::pair<T,U> *val) {
	int res = SWIG_ERROR;
	if (PyTuple_Check(obj)) {
	  if (PyTuple_GET_SIZE(obj) == 2) {
	    res = get_pair(PyTuple_GET_ITEM(obj,0),PyTuple_GET_ITEM(obj,1), val);
	  }
	} else if (PySequence_Check(obj)) {
	  if (PySequence_Size(obj) == 2) {
	    swig::SwigVar_PyObject first = PySequence_GetItem(obj,0);
	    swig::SwigVar_PyObject second = PySequence_GetItem(obj,1);
	    res = get_pair(first, second, val);
	  }
	} else {
	  value_type *p;
	  res = SWIG_ConvertPtr(obj,(void**)&p,swig::type_info<value_type>(),0);
	  if (SWIG_IsOK(res) && val)  *val = *p;
	}
	return res;
      }
    };

#else
    template <class T, class U >
    struct traits_asptr<std::pair<T,U> >  {
      typedef std::pair<T,U> value_type;

      static int get_pair(PyObject* first, PyObject* second,
			  std::pair<T,U> **val) 
      {
	if (val) {
	  value_type *vp = %new_instance(std::pair<T,U>);
	  T *pfirst = &(vp->first);
	  int res1 = swig::asval((PyObject*)first, pfirst);
	  if (!SWIG_IsOK(res1)) return res1;
	  U *psecond = &(vp->second);
	  int res2 = swig::asval((PyObject*)second, psecond);
	  if (!SWIG_IsOK(res2)) return res2;
	  *val = vp;
	  return SWIG_AddNewMask(res1 > res2 ? res1 : res2);
	} else {
	  T *pfirst = 0;
	  int res1 = swig::asval((PyObject*)first, pfirst);
	  if (!SWIG_IsOK(res1)) return res1;
	  U *psecond = 0;
	  int res2 = swig::asval((PyObject*)second, psecond);
	  if (!SWIG_IsOK(res2)) return res2;
	  return res1 > res2 ? res1 : res2;
	}	
      }

      static int asptr(PyObject *obj, std::pair<T,U> **val) {
	int res = SWIG_ERROR;
	if (PyTuple_Check(obj)) {
	  if (PyTuple_GET_SIZE(obj) == 2) {
	    res = get_pair(PyTuple_GET_ITEM(obj,0),PyTuple_GET_ITEM(obj,1), val);
	  }
	} else if (PySequence_Check(obj)) {
	  if (PySequence_Size(obj) == 2) {
	    swig::SwigVar_PyObject first = PySequence_GetItem(obj,0);
	    swig::SwigVar_PyObject second = PySequence_GetItem(obj,1);
	    res = get_pair(first, second, val);
	  }
	} else {
	  value_type *p;
	  res = SWIG_ConvertPtr(obj,(void**)&p,swig::type_info<value_type>(),0);
	  if (SWIG_IsOK(res) && val)  *val = p;
	}
	return res;
      }
    };

#endif
    template <class T, class U >
    struct traits_from<std::pair<T,U> >   {
      static PyObject *from(const std::pair<T,U>& val) {
	PyObject* obj = PyTuple_New(2);
	PyTuple_SetItem(obj,0,swig::from(val.first));
	PyTuple_SetItem(obj,1,swig::from(val.second));
	return obj;
      }
    };
  }
}

%define %swig_pair_methods(pair...)
%extend {      
%pythoncode {def __len__(self): return 2
def __repr__(self): return str((self.first, self.second))
def __getitem__(self, index): 
  if not (index % 2): 
    return self.first
  else:
    return self.second
def __setitem__(self, index, val):
  if not (index % 2): 
    self.first = val
  else:
    self.second = val}
}
%enddef

%include <std/std_pair.i>

