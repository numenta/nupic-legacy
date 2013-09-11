#ifdef __cplusplus

/*
  PyObject_ptr is used as a replacement of PyObject *, where
  the INCREF/DECREF are applied as needed.

  You can use PyObject_ptr in a container, such as
  
     std::vector<PyObject_ptr>;

  or as a member variable:
  
     struct A {
       PyObject_ptr obj;
       A(PyObject *o) : _obj(o) {
       }
     };

   or as a input/output value 

     PyObject_ptr func(PyObject_ptr obj) {     
       PyObject_ptr out = PyString_FromFormat("hello %s", PyObject_AsString(obj));
       Py_DECREF(out);
       return out;
     }

   just remember to pair the object creation with the proper DECREF,
   the same as with plain PyObject *ptr, since PyObject_ptr always add
   one reference at construction.

   PyObject_ptr is 'visible' at the wrapped side, so you can do:


      %template(pyvector) std::vector<swig::PyObject_ptr>;

   and all the proper typemaps will be used.
   
*/

namespace swig {
  %ignore PyObject_ptr;
  struct PyObject_ptr {};
  %apply PyObject * {PyObject_ptr};
  %apply PyObject * const& {PyObject_ptr const&};

  /* For output */
  %typemap(out,noblock=1)  PyObject_ptr {
    $result = (PyObject *)$1;
    Py_INCREF($result);
  }
  
  %typemap(out,noblock=1)  PyObject_ptr const & {
    $result = (PyObject *)*$1;
    Py_INCREF($result);
  }
  
}

%{
namespace swig {
  class PyObject_ptr {
  protected:
    PyObject *_obj;

  public:
    PyObject_ptr() :_obj(0)
    {
    }

    PyObject_ptr(const PyObject_ptr& item) : _obj(item._obj)
    {
      Py_XINCREF(_obj);      
    }
    
    PyObject_ptr(PyObject *obj, bool initial_ref = true) :_obj(obj)
    {
      if (initial_ref) {
        Py_XINCREF(_obj);
      }
    }
    
    PyObject_ptr & operator=(const PyObject_ptr& item) 
    {
      Py_XINCREF(item._obj);
      Py_XDECREF(_obj);
      _obj = item._obj;
      return *this;      
    }
    
    ~PyObject_ptr() 
    {
      Py_XDECREF(_obj);
    }
    
    operator PyObject *() const
    {
      return _obj;
    }

    PyObject *operator->() const
    {
      return _obj;
    }
  };
}
%}

/*
  PyObject_var is used to manage 'in the scope' PyObject * variables,
  as in

  int func () {
    PyObject_var obj = PyString_FromString("hello");
  }

  ie, 'obj' is created and destructed in the same scope from
  a python object that carries at least one reference value.
  
  PyObject_var just take care of applying the proper Py_DECREF.

  Hence, this class is purely internal and not visible at the wrapped side.
 */
namespace swig {
  %ignore PyObject_var;
  struct PyObject_var {};
  %apply PyObject * {PyObject_var};
  %apply PyObject * const& {PyObject_var const&};
}

%{
namespace swig {
  struct PyObject_var : PyObject_ptr {
    PyObject_var(PyObject* obj = 0) : PyObject_ptr(obj, false) { }
    
    PyObject_var & operator = (PyObject* obj)
    {
      Py_XDECREF(_obj);
      _obj = obj;
      return *this;      
    }
  };
}
%}


#endif
