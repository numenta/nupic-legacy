/*
  Maps
*/

%fragment("StdMapTraits","header",fragment="StdSequenceTraits")
{
  namespace swig {
    template <class PySeq, class K, class T >
    inline void
    assign(const PySeq& pyseq, std::map<K,T > *map) {
      typedef typename std::map<K,T>::value_type value_type;
      typename PySeq::const_iterator it = pyseq.begin();
      for (;it != pyseq.end(); ++it) {
	map->insert(value_type(it->first, it->second));
      }
    }

    template <class K, class T>
    struct traits_asptr<std::map<K,T> >  {
      typedef std::map<K,T> map_type;
      static int asptr(PyObject *obj, map_type **val) {
	int res = SWIG_ERROR;
	if (PyDict_Check(obj)) {
	  PyObject_var items = PyObject_CallMethod(obj,(char *)"items",NULL);
	  res = traits_asptr_stdseq<std::map<K,T>, std::pair<K, T> >::asptr(items, val);
	} else {
	  map_type *p;
	  res = SWIG_ConvertPtr(obj,(void**)&p,swig::type_info<map_type>(),0);
	  if (SWIG_IsOK(res) && val)  *val = p;
	}
	return res;
      }      
    };
      
    template <class K, class T >
    struct traits_from<std::map<K,T> >  {
      typedef std::map<K,T> map_type;
      typedef typename map_type::const_iterator const_iterator;
      typedef typename map_type::size_type size_type;
            
      static PyObject *from(const map_type& map) {
	swig_type_info *desc = swig::type_info<map_type>();
	if (desc && desc->clientdata) {
	  return SWIG_NewPointerObj(new map_type(map), desc, SWIG_POINTER_OWN);
	} else {
	  size_type size = map.size();
	  int pysize = (size <= (size_type) INT_MAX) ? (int) size : -1;
	  if (pysize < 0) {
	    SWIG_PYTHON_THREAD_BEGIN_BLOCK;
	    PyErr_SetString(PyExc_OverflowError,
			    "map size not valid in python");
	    SWIG_PYTHON_THREAD_END_BLOCK;
	    return NULL;
	  }
	  PyObject *obj = PyDict_New();
	  for (const_iterator i= map.begin(); i!= map.end(); ++i) {
	    swig::PyObject_var key = swig::from(i->first);
	    swig::PyObject_var val = swig::from(i->second);
	    PyDict_SetItem(obj, key, val);
	  }
	  return obj;
	}
      }
    };

    template <class ValueType>
    struct from_key_oper 
    {
      typedef const ValueType& argument_type;
      typedef  PyObject *result_type;
      result_type operator()(argument_type v) const
      {
	return swig::from(v.first);
      }
    };

    template <class ValueType>
    struct from_value_oper 
    {
      typedef const ValueType& argument_type;
      typedef  PyObject *result_type;
      result_type operator()(argument_type v) const
      {
	return swig::from(v.second);
      }
    };

    template<class OutIterator, class FromOper, class ValueType = typename OutIterator::value_type>
    struct PyMapIterator_T : PySwigIteratorClosed_T<OutIterator, ValueType, FromOper>
    {
      PyMapIterator_T(OutIterator curr, OutIterator first, OutIterator last, PyObject *seq)
	: PySwigIteratorClosed_T<OutIterator,ValueType,FromOper>(curr, first, last, seq)
      {
      }
    };


    template<class OutIterator,
	     class FromOper = from_key_oper<typename OutIterator::value_type> >
    struct PyMapKeyIterator_T : PyMapIterator_T<OutIterator, FromOper>
    {
      PyMapKeyIterator_T(OutIterator curr, OutIterator first, OutIterator last, PyObject *seq)
	: PyMapIterator_T<OutIterator, FromOper>(curr, first, last, seq)
      {
      }
    };

    template<typename OutIter>
    inline PySwigIterator*
    make_output_key_iterator(const OutIter& current, const OutIter& begin, const OutIter& end, PyObject *seq = 0)
    {
      return new PyMapKeyIterator_T<OutIter>(current, begin, end, seq);
    }

    template<class OutIterator,
	     class FromOper = from_value_oper<typename OutIterator::value_type> >
    struct PyMapValueIterator_T : PyMapIterator_T<OutIterator, FromOper>
    {
      PyMapValueIterator_T(OutIterator curr, OutIterator first, OutIterator last, PyObject *seq)
	: PyMapIterator_T<OutIterator, FromOper>(curr, first, last, seq)
      {
      }
    };
    

    template<typename OutIter>
    inline PySwigIterator*
    make_output_value_iterator(const OutIter& current, const OutIter& begin, const OutIter& end, PyObject *seq = 0)
    {
      return new PyMapValueIterator_T<OutIter>(current, begin, end, seq);
    }
  }
}

%define %swig_map_common(Map...)
  %swig_sequence_iterator(Map);
  %swig_container_methods(Map)

  %extend {
    mapped_type __getitem__(const key_type& key) const throw (std::out_of_range) {
      Map::const_iterator i = self->find(key);
      if (i != self->end())
	return i->second;
      else
	throw std::out_of_range("key not found");
    }
    
    void __delitem__(const key_type& key) throw (std::out_of_range) {
      Map::iterator i = self->find(key);
      if (i != self->end())
	self->erase(i);
      else
	throw std::out_of_range("key not found");
    }
    
    bool has_key(const key_type& key) const {
      Map::const_iterator i = self->find(key);
      return i != self->end();
    }
    
    PyObject* keys() {
      Map::size_type size = self->size();
      int pysize = (size <= (Map::size_type) INT_MAX) ? (int) size : -1;
      if (pysize < 0) {
	SWIG_PYTHON_THREAD_BEGIN_BLOCK;
	PyErr_SetString(PyExc_OverflowError,
			"map size not valid in python");
	SWIG_PYTHON_THREAD_END_BLOCK;
	return NULL;
      }
      PyObject* keyList = PyList_New(pysize);
      Map::const_iterator i = self->begin();
      for (int j = 0; j < pysize; ++i, ++j) {
	PyList_SET_ITEM(keyList, j, swig::from(i->first));
      }
      return keyList;
    }
    
    PyObject* values() {
      Map::size_type size = self->size();
      int pysize = (size <= (Map::size_type) INT_MAX) ? (int) size : -1;
      if (pysize < 0) {
	SWIG_PYTHON_THREAD_BEGIN_BLOCK;
	PyErr_SetString(PyExc_OverflowError,
			"map size not valid in python");
	SWIG_PYTHON_THREAD_END_BLOCK;
	return NULL;
      }
      PyObject* valList = PyList_New(pysize);
      Map::const_iterator i = self->begin();
      for (int j = 0; j < pysize; ++i, ++j) {
	PyList_SET_ITEM(valList, j, swig::from(i->second));
      }
      return valList;
    }
    
    PyObject* items() {
      Map::size_type size = self->size();
      int pysize = (size <= (Map::size_type) INT_MAX) ? (int) size : -1;
      if (pysize < 0) {
	SWIG_PYTHON_THREAD_BEGIN_BLOCK;
	PyErr_SetString(PyExc_OverflowError,
			"map size not valid in python");
	SWIG_PYTHON_THREAD_END_BLOCK;
	return NULL;
      }    
      PyObject* itemList = PyList_New(pysize);
      Map::const_iterator i = self->begin();
      for (int j = 0; j < pysize; ++i, ++j) {
	PyList_SET_ITEM(itemList, j, swig::from(*i));
      }
      return itemList;
    }
    
    // Python 2.2 methods
    bool __contains__(const key_type& key) {
      return self->find(key) != self->end();
    }

    %newobject key_iterator(PyObject **PYTHON_SELF);
    swig::PySwigIterator* key_iterator(PyObject **PYTHON_SELF) {
      return swig::make_output_key_iterator(self->begin(), self->begin(), self->end(), *PYTHON_SELF);
    }

    %newobject value_iterator(PyObject **PYTHON_SELF);
    swig::PySwigIterator* value_iterator(PyObject **PYTHON_SELF) {
      return swig::make_output_value_iterator(self->begin(), self->begin(), self->end(), *PYTHON_SELF);
    }

    %pythoncode {def __iter__(self): return self.key_iterator()}    
    %pythoncode {def iterkeys(self): return self.key_iterator()}
    %pythoncode {def itervalues(self): return self.value_iterator()}
    %pythoncode {def iteritems(self): return self.iterator()}
  }
%enddef

%define %swig_map_methods(Map...)
  %swig_map_common(Map)
  %extend {
    void __setitem__(const key_type& key, const mapped_type& x) throw (std::out_of_range) {
      (*self)[key] = x;
    }
  }
%enddef


%include <std/std_map.i>
