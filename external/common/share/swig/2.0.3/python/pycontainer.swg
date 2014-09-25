/* -----------------------------------------------------------------------------
 * pycontainer.swg
 *
 * Python sequence <-> C++ container wrapper
 *
 * This wrapper, and its iterator, allows a general use (and reuse) of
 * the mapping between C++ and Python, thanks to the C++ templates.
 *
 * Of course, it needs the C++ compiler to support templates, but
 * since we will use this wrapper with the STL containers, that should
 * be the case.
 * ----------------------------------------------------------------------------- */

%{
#include <iostream>
%}


#if !defined(SWIG_NO_EXPORT_ITERATOR_METHODS)
# if !defined(SWIG_EXPORT_ITERATOR_METHODS)
#  define SWIG_EXPORT_ITERATOR_METHODS SWIG_EXPORT_ITERATOR_METHODS
# endif
#endif

%include <pyiterators.swg>

/**** The PySequence C++ Wrap ***/

%insert(header) %{
#include <stdexcept>
%}

%include <std_except.i>

%fragment(SWIG_Traits_frag(swig::SwigPtr_PyObject),"header",fragment="StdTraits") {
namespace swig {
  template <>  struct traits<SwigPtr_PyObject > {
    typedef value_category category;
    static const char* type_name() { return  "SwigPtr_PyObject"; }
  };
  
  template <>  struct traits_from<SwigPtr_PyObject> {
    typedef SwigPtr_PyObject value_type;
    static PyObject *from(const value_type& val) {
      PyObject *obj = static_cast<PyObject *>(val);
      Py_XINCREF(obj);
      return obj;
    }
  };
  
  template <> 
  struct traits_check<SwigPtr_PyObject, value_category> {
    static bool check(SwigPtr_PyObject) {
      return true;
    }
  };
  
  template <>  struct traits_asval<SwigPtr_PyObject > {   
    typedef SwigPtr_PyObject value_type;
    static int asval(PyObject *obj, value_type *val) {
      if (val) *val = obj;
      return SWIG_OK;
    }
  };
}
}

%fragment(SWIG_Traits_frag(swig::SwigVar_PyObject),"header",fragment="StdTraits") {
namespace swig {
  template <>  struct traits<SwigVar_PyObject > {
    typedef value_category category;
    static const char* type_name() { return  "SwigVar_PyObject"; }
  };
  
  template <>  struct traits_from<SwigVar_PyObject> {
    typedef SwigVar_PyObject value_type;
    static PyObject *from(const value_type& val) {
      PyObject *obj = static_cast<PyObject *>(val);
      Py_XINCREF(obj);
      return obj;
    }
  };
  
  template <> 
  struct traits_check<SwigVar_PyObject, value_category> {
    static bool check(SwigVar_PyObject) {
      return true;
    }
  };
  
  template <>  struct traits_asval<SwigVar_PyObject > {   
    typedef SwigVar_PyObject value_type;
    static int asval(PyObject *obj, value_type *val) {
      if (val) *val = obj;
      return SWIG_OK;
    }
  };
} 
}

%fragment("SwigPySequence_Base","header")
{
%#include <functional>

namespace std {
  template <>
  struct less <PyObject *>: public binary_function<PyObject *, PyObject *, bool>
  {
    bool
    operator()(PyObject * v, PyObject *w) const
    { 
      bool res;
      SWIG_PYTHON_THREAD_BEGIN_BLOCK;
      res = PyObject_RichCompareBool(v, w, Py_LT) ? true : false;
      /* This may fall into a case of inconsistent
               eg. ObjA > ObjX > ObjB
               but ObjA < ObjB
      */
      if( PyErr_Occurred() && PyErr_ExceptionMatches(PyExc_TypeError) )
      {
        /* Objects can't be compared, this mostly occurred in Python 3.0 */
        /* Compare their ptr directly for a workaround */
        res = (v < w);
        PyErr_Clear();
      }
      SWIG_PYTHON_THREAD_END_BLOCK;
      return res;
    }
  };

  template <>
  struct less <swig::SwigPtr_PyObject>: public binary_function<swig::SwigPtr_PyObject, swig::SwigPtr_PyObject, bool>
  {
    bool
    operator()(const swig::SwigPtr_PyObject& v, const swig::SwigPtr_PyObject& w) const
    {
      return std::less<PyObject *>()(v, w);
    }
  };

  template <>
  struct less <swig::SwigVar_PyObject>: public binary_function<swig::SwigVar_PyObject, swig::SwigVar_PyObject, bool>
  {
    bool
    operator()(const swig::SwigVar_PyObject& v, const swig::SwigVar_PyObject& w) const
    {
      return std::less<PyObject *>()(v, w);
    }
  };

}

namespace swig {
  template <> struct traits<PyObject *> {
    typedef value_category category;
    static const char* type_name() { return "PyObject *"; }
  };  

  template <>  struct traits_asval<PyObject * > {   
    typedef PyObject * value_type;
    static int asval(PyObject *obj, value_type *val) {
      if (val) *val = obj;
      return SWIG_OK;
    }
  };

  template <> 
  struct traits_check<PyObject *, value_category> {
    static bool check(PyObject *) {
      return true;
    }
  };

  template <>  struct traits_from<PyObject *> {
    typedef PyObject * value_type;
    static PyObject *from(const value_type& val) {
      Py_XINCREF(val);
      return val;
    }
  };
  
}

namespace swig {
  inline size_t
  check_index(ptrdiff_t i, size_t size, bool insert = false) {
    if ( i < 0 ) {
      if ((size_t) (-i) <= size)
	return (size_t) (i + size);
    } else if ( (size_t) i < size ) {
      return (size_t) i;
    } else if (insert && ((size_t) i == size)) {
      return size;
    }
    
    throw std::out_of_range("index out of range");
  }

  inline size_t
  slice_index(ptrdiff_t i, size_t size) {
    if ( i < 0 ) {
      if ((size_t) (-i) <= size) {
	return (size_t) (i + size);
      } else {
	throw std::out_of_range("index out of range");
      }
    } else {
      return ( (size_t) i < size ) ? ((size_t) i) : size;
    }
  }

  template <class Sequence, class Difference>
  inline typename Sequence::iterator
  getpos(Sequence* self, Difference i)  {
    typename Sequence::iterator pos = self->begin();
    std::advance(pos, check_index(i,self->size()));
    return pos;
  }

  template <class Sequence, class Difference>
  inline typename Sequence::const_iterator
  cgetpos(const Sequence* self, Difference i)  {
    typename Sequence::const_iterator pos = self->begin();
    std::advance(pos, check_index(i,self->size()));
    return pos;
  }

  template <class Sequence, class Difference>
  inline Sequence*
  getslice(const Sequence* self, Difference i, Difference j) {
    typename Sequence::size_type size = self->size();
    typename Sequence::size_type ii = swig::check_index(i, size);
    typename Sequence::size_type jj = swig::slice_index(j, size);

    if (jj > ii) {
      typename Sequence::const_iterator vb = self->begin();
      typename Sequence::const_iterator ve = self->begin();
      std::advance(vb,ii);
      std::advance(ve,jj);
      return new Sequence(vb, ve);
    } else {
      return new Sequence();
    }
  }

  template <class Sequence, class Difference, class InputSeq>
  inline void
  setslice(Sequence* self, Difference i, Difference j, const InputSeq& v) {
    typename Sequence::size_type size = self->size();
    typename Sequence::size_type ii = swig::check_index(i, size, true);
    typename Sequence::size_type jj = swig::slice_index(j, size);
    if (jj < ii) jj = ii;
    size_t ssize = jj - ii;
    if (ssize <= v.size()) {
      typename Sequence::iterator sb = self->begin();
      typename InputSeq::const_iterator vmid = v.begin();
      std::advance(sb,ii);
      std::advance(vmid, jj - ii);
      self->insert(std::copy(v.begin(), vmid, sb), vmid, v.end());
    } else {
      typename Sequence::iterator sb = self->begin();
      typename Sequence::iterator se = self->begin();
      std::advance(sb,ii);
      std::advance(se,jj);
      self->erase(sb,se);
      self->insert(sb, v.begin(), v.end());
    }
  }

  template <class Sequence, class Difference>
  inline void
  delslice(Sequence* self, Difference i, Difference j) {
    typename Sequence::size_type size = self->size();
    typename Sequence::size_type ii = swig::check_index(i, size, true);
    typename Sequence::size_type jj = swig::slice_index(j, size);
    if (jj > ii) {
      typename Sequence::iterator sb = self->begin();
      typename Sequence::iterator se = self->begin();
      std::advance(sb,ii);
      std::advance(se,jj);
      self->erase(sb,se);
    }
  }
}
}

%fragment("SwigPySequence_Cont","header",
	  fragment="StdTraits",
	  fragment="SwigPySequence_Base",
	  fragment="SwigPyIterator_T")
{
namespace swig
{
  template <class T>
  struct SwigPySequence_Ref
  {
    SwigPySequence_Ref(PyObject* seq, int index)
      : _seq(seq), _index(index)
    {
    }
    
    operator T () const
    {
      swig::SwigVar_PyObject item = PySequence_GetItem(_seq, _index);
      try {
	return swig::as<T>(item, true);
      } catch (std::exception& e) {
	char msg[1024];
	sprintf(msg, "in sequence element %d ", _index);
	if (!PyErr_Occurred()) {
	  ::%type_error(swig::type_name<T>());
	}
	SWIG_Python_AddErrorMsg(msg);
	SWIG_Python_AddErrorMsg(e.what());
	throw;
      }
    }

    SwigPySequence_Ref& operator=(const T& v)
    {
      PySequence_SetItem(_seq, _index, swig::from<T>(v));
      return *this;
    }

  private:
    PyObject* _seq;
    int _index;
  };

  template <class T>
  struct SwigPySequence_ArrowProxy
  {
    SwigPySequence_ArrowProxy(const T& x): m_value(x) {}
    const T* operator->() const { return &m_value; }
    operator const T*() const { return &m_value; }
    T m_value;
  };

  template <class T, class Reference >
  struct SwigPySequence_InputIterator
  {
    typedef SwigPySequence_InputIterator<T, Reference > self;

    typedef std::random_access_iterator_tag iterator_category;
    typedef Reference reference;
    typedef T value_type;
    typedef T* pointer;
    typedef int difference_type;

    SwigPySequence_InputIterator()
    {
    }

    SwigPySequence_InputIterator(PyObject* seq, int index)
      : _seq(seq), _index(index)
    {
    }

    reference operator*() const
    {
      return reference(_seq, _index);
    }

    SwigPySequence_ArrowProxy<T>
    operator->() const {
      return SwigPySequence_ArrowProxy<T>(operator*());
    }

    bool operator==(const self& ri) const
    {
      return (_index == ri._index) && (_seq == ri._seq);
    }

    bool operator!=(const self& ri) const
    {
      return !(operator==(ri));
    }

    self& operator ++ ()
    {
      ++_index;
      return *this;
    }

    self& operator -- ()
    {
      --_index;
      return *this;
    }

    self& operator += (difference_type n)
    {
      _index += n;
      return *this;
    }

    self operator +(difference_type n) const
    {
      return self(_seq, _index + n);
    }

    self& operator -= (difference_type n)
    {
      _index -= n;
      return *this;
    }

    self operator -(difference_type n) const
    {
      return self(_seq, _index - n);
    }

    difference_type operator - (const self& ri) const
    {
      return _index - ri._index;
    }

    bool operator < (const self& ri) const
    {
      return _index < ri._index;
    }

    reference
    operator[](difference_type n) const
    {
      return reference(_seq, _index + n);
    }

  private:
    PyObject* _seq;
    difference_type _index;
  };

  template <class T>
  struct SwigPySequence_Cont
  {
    typedef SwigPySequence_Ref<T> reference;
    typedef const SwigPySequence_Ref<T> const_reference;
    typedef T value_type;
    typedef T* pointer;
    typedef int difference_type;
    typedef int size_type;
    typedef const pointer const_pointer;
    typedef SwigPySequence_InputIterator<T, reference> iterator;
    typedef SwigPySequence_InputIterator<T, const_reference> const_iterator;

    SwigPySequence_Cont(PyObject* seq) : _seq(0)
    {
      if (!PySequence_Check(seq)) {
	throw std::invalid_argument("a sequence is expected");
      }
      _seq = seq;
      Py_INCREF(_seq);
    }

    ~SwigPySequence_Cont()
    {
      Py_XDECREF(_seq);
    }

    size_type size() const
    {
      return static_cast<size_type>(PySequence_Size(_seq));
    }

    bool empty() const
    {
      return size() == 0;
    }

    iterator begin()
    {
      return iterator(_seq, 0);
    }

    const_iterator begin() const
    {
      return const_iterator(_seq, 0);
    }

    iterator end()
    {
      return iterator(_seq, size());
    }

    const_iterator end() const
    {
      return const_iterator(_seq, size());
    }

    reference operator[](difference_type n)
    {
      return reference(_seq, n);
    }

    const_reference operator[](difference_type n)  const
    {
      return const_reference(_seq, n);
    }

    bool check(bool set_err = true) const
    {
      int s = size();
      for (int i = 0; i < s; ++i) {
	swig::SwigVar_PyObject item = PySequence_GetItem(_seq, i);
	if (!swig::check<value_type>(item)) {
	  if (set_err) {
	    char msg[1024];
	    sprintf(msg, "in sequence element %d", i);
	    SWIG_Error(SWIG_RuntimeError, msg);
	  }
	  return false;
	}
      }
      return true;
    }

  private:
    PyObject* _seq;
  };

}
}

%define %swig_sequence_iterator(Sequence...)
#if defined(SWIG_EXPORT_ITERATOR_METHODS)
  class iterator;
  class reverse_iterator;
  class const_iterator;
  class const_reverse_iterator;

  %typemap(out,noblock=1,fragment="SwigPySequence_Cont")
    iterator, reverse_iterator, const_iterator, const_reverse_iterator {
    $result = SWIG_NewPointerObj(swig::make_output_iterator(%static_cast($1,const $type &)),
				 swig::SwigPyIterator::descriptor(),SWIG_POINTER_OWN);
  }
  %typemap(out,noblock=1,fragment="SwigPySequence_Cont")
    std::pair<iterator, iterator>, std::pair<const_iterator, const_iterator> {
    $result = PyTuple_New(2);
    PyTuple_SetItem($result,0,SWIG_NewPointerObj(swig::make_output_iterator(%static_cast($1,const $type &).first),
						 swig::SwigPyIterator::descriptor(),SWIG_POINTER_OWN));
    PyTuple_SetItem($result,1,SWIG_NewPointerObj(swig::make_output_iterator(%static_cast($1,const $type &).second),
						 swig::SwigPyIterator::descriptor(),SWIG_POINTER_OWN));    
  }

  %fragment("SwigPyPairBoolOutputIterator","header",fragment=SWIG_From_frag(bool),fragment="SwigPySequence_Cont") {}

  %typemap(out,noblock=1,fragment="SwigPyPairBoolOutputIterator")
    std::pair<iterator, bool>, std::pair<const_iterator, bool> {
    $result = PyTuple_New(2);
    PyTuple_SetItem($result,0,SWIG_NewPointerObj(swig::make_output_iterator(%static_cast($1,const $type &).first),
					       swig::SwigPyIterator::descriptor(),SWIG_POINTER_OWN));    
    PyTuple_SetItem($result,1,SWIG_From(bool)(%static_cast($1,const $type &).second));
  }

  %typemap(in,noblock=1,fragment="SwigPySequence_Cont")
    iterator(swig::SwigPyIterator *iter = 0, int res),
    reverse_iterator(swig::SwigPyIterator *iter = 0, int res),
    const_iterator(swig::SwigPyIterator *iter = 0, int res),
    const_reverse_iterator(swig::SwigPyIterator *iter = 0, int res) {
    res = SWIG_ConvertPtr($input, %as_voidptrptr(&iter), swig::SwigPyIterator::descriptor(), 0);
    if (!SWIG_IsOK(res) || !iter) {
      %argument_fail(SWIG_TypeError, "$type", $symname, $argnum);
    } else {
      swig::SwigPyIterator_T<$type > *iter_t = dynamic_cast<swig::SwigPyIterator_T<$type > *>(iter);
      if (iter_t) {
	$1 = iter_t->get_current();
      } else {
	%argument_fail(SWIG_TypeError, "$type", $symname, $argnum);
      }
    }
  }

  %typecheck(%checkcode(ITERATOR),noblock=1,fragment="SwigPySequence_Cont")
    iterator, reverse_iterator, const_iterator, const_reverse_iterator {
    swig::SwigPyIterator *iter = 0;
    int res = SWIG_ConvertPtr($input, %as_voidptrptr(&iter), swig::SwigPyIterator::descriptor(), 0);
    $1 = (SWIG_IsOK(res) && iter && (dynamic_cast<swig::SwigPyIterator_T<$type > *>(iter) != 0));
  }

  %fragment("SwigPySequence_Cont");

  %newobject iterator(PyObject **PYTHON_SELF);
  %extend  {
    swig::SwigPyIterator* iterator(PyObject **PYTHON_SELF) {
      return swig::make_output_iterator(self->begin(), self->begin(), self->end(), *PYTHON_SELF);
    }

    %pythoncode {def __iter__(self): return self.iterator()}
  }
#endif //SWIG_EXPORT_ITERATOR_METHODS
%enddef


/**** The python container methods  ****/


%define %swig_container_methods(Container...)

  %newobject __getslice__;

  %extend {
    bool __nonzero__() const {
      return !(self->empty());
    }

    /* Alias for Python 3 compatibility */
    bool __bool__() const {
      return !(self->empty());
    }

    size_type __len__() const {
      return self->size();
    }
  }
%enddef

%define %swig_sequence_methods_common(Sequence...)
  %swig_sequence_iterator(%arg(Sequence))
  %swig_container_methods(%arg(Sequence))
  
  %fragment("SwigPySequence_Base");

  %extend {
    value_type pop() throw (std::out_of_range) {
      if (self->size() == 0)
	throw std::out_of_range("pop from empty container");
      Sequence::value_type x = self->back();
      self->pop_back();
      return x;
    }

    /* typemap for slice object support */
    %typemap(in) PySliceObject* {
      $1 = (PySliceObject *) $input;
    }
    %typemap(typecheck,precedence=SWIG_TYPECHECK_POINTER) PySliceObject* {
      $1 = PySlice_Check($input);
    }

    Sequence* __getslice__(difference_type i, difference_type j) throw (std::out_of_range) {
      return swig::getslice(self, i, j);
    }

    void __setslice__(difference_type i, difference_type j, const Sequence& v) 
      throw (std::out_of_range, std::invalid_argument) {
      swig::setslice(self, i, j, v);
    }

    void __delslice__(difference_type i, difference_type j) throw (std::out_of_range) {
      swig::delslice(self, i, j);
    }

    void __delitem__(difference_type i) throw (std::out_of_range) {
      self->erase(swig::getpos(self,i));
    }


    /* Overloaded methods for Python 3 compatibility 
     * (Also useful in Python 2.x)
     */
    Sequence* __getitem__(PySliceObject *slice) throw (std::out_of_range) {
      Py_ssize_t i, j, step;
      if( !PySlice_Check(slice) ) {
        SWIG_Error(SWIG_TypeError, "Slice object expected.");
        return NULL;
      }
      PySlice_GetIndices(slice, self->size(), &i, &j, &step);
      return swig::getslice(self, i, j);
    }

    void __setitem__(PySliceObject *slice, const Sequence& v)
      throw (std::out_of_range, std::invalid_argument) {
      Py_ssize_t i, j, step;
      if( !PySlice_Check(slice) ) {
        SWIG_Error(SWIG_TypeError, "Slice object expected.");
        return;
      }
      PySlice_GetIndices(slice, self->size(), &i, &j, &step);
      swig::setslice(self, i, j, v);
    }

    void __delitem__(PySliceObject *slice)
      throw (std::out_of_range) {
      Py_ssize_t i, j, step;
      if( !PySlice_Check(slice) ) {
        SWIG_Error(SWIG_TypeError, "Slice object expected.");
        return;
      }
      PySlice_GetIndices(slice, self->size(), &i, &j, &step);
      swig::delslice(self, i,j);
    }
     
  }
%enddef

%define %swig_sequence_methods(Sequence...)
  %swig_sequence_methods_common(%arg(Sequence))
  %extend {
    const value_type& __getitem__(difference_type i) const throw (std::out_of_range) {
      return *(swig::cgetpos(self, i));
    }

    void __setitem__(difference_type i, const value_type& x) throw (std::out_of_range) {
      *(swig::getpos(self,i)) = x;
    }

    void append(const value_type& x) {
      self->push_back(x);
    }
 }
%enddef

%define %swig_sequence_methods_val(Sequence...)
  %swig_sequence_methods_common(%arg(Sequence))
  %extend {
    value_type __getitem__(difference_type i) throw (std::out_of_range) {
      return *(swig::cgetpos(self, i));
    }

    void __setitem__(difference_type i, value_type x) throw (std::out_of_range) {
      *(swig::getpos(self,i)) = x;
    }

    void append(value_type x) {
      self->push_back(x);
    }
 }
%enddef



//
// Common fragments
//

%fragment("StdSequenceTraits","header",
	  fragment="StdTraits",
	  fragment="SwigPySequence_Cont")
{
namespace swig {
  template <class SwigPySeq, class Seq>
  inline void
  assign(const SwigPySeq& swigpyseq, Seq* seq) {
    // seq->assign(swigpyseq.begin(), swigpyseq.end()); // not used as not always implemented
    typedef typename SwigPySeq::value_type value_type;
    typename SwigPySeq::const_iterator it = swigpyseq.begin();
    for (;it != swigpyseq.end(); ++it) {
      seq->insert(seq->end(),(value_type)(*it));
    }
  }

  template <class Seq, class T = typename Seq::value_type >
  struct traits_asptr_stdseq {
    typedef Seq sequence;
    typedef T value_type;

    static int asptr(PyObject *obj, sequence **seq) {
      if (obj == Py_None || SWIG_Python_GetSwigThis(obj)) {
	sequence *p;
	if (::SWIG_ConvertPtr(obj,(void**)&p,
			      swig::type_info<sequence>(),0) == SWIG_OK) {
	  if (seq) *seq = p;
	  return SWIG_OLDOBJ;
	}
      } else if (PySequence_Check(obj)) {
	try {
	  SwigPySequence_Cont<value_type> swigpyseq(obj);
	  if (seq) {
	    sequence *pseq = new sequence();
	    assign(swigpyseq, pseq);
	    *seq = pseq;
	    return SWIG_NEWOBJ;
	  } else {
	    return swigpyseq.check() ? SWIG_OK : SWIG_ERROR;
	  }
	} catch (std::exception& e) {
	  if (seq) {
	    if (!PyErr_Occurred()) {
	      PyErr_SetString(PyExc_TypeError, e.what());
	    }
	  }
	  return SWIG_ERROR;
	}
      }
      return SWIG_ERROR;
    }
  };

  template <class Seq, class T = typename Seq::value_type >
  struct traits_from_stdseq {
    typedef Seq sequence;
    typedef T value_type;
    typedef typename Seq::size_type size_type;
    typedef typename sequence::const_iterator const_iterator;

    static PyObject *from(const sequence& seq) {
%#ifdef SWIG_PYTHON_EXTRA_NATIVE_CONTAINERS
      swig_type_info *desc = swig::type_info<sequence>();
      if (desc && desc->clientdata) {
	return SWIG_NewPointerObj(new sequence(seq), desc, SWIG_POINTER_OWN);
      }
%#endif
      size_type size = seq.size();
      if (size <= (size_type)INT_MAX) {
	PyObject *obj = PyTuple_New((int)size);
	int i = 0;
	for (const_iterator it = seq.begin();
	     it != seq.end(); ++it, ++i) {
	  PyTuple_SetItem(obj,i,swig::from<value_type>(*it));
	}
	return obj;
      } else {
	PyErr_SetString(PyExc_OverflowError,"sequence size not valid in python");
	return NULL;
      }
    }
  };
}
}
