/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * director.swg
 *
 * This file contains support for director classes that proxy
 * method calls from C++ to Python extensions.
 * ----------------------------------------------------------------------------- */

#ifndef SWIG_DIRECTOR_PYTHON_HEADER_
#define SWIG_DIRECTOR_PYTHON_HEADER_

#ifdef __cplusplus

#include <string>
#include <iostream>
#include <exception>
#include <vector>
#include <map>


/*
  Use -DSWIG_PYTHON_DIRECTOR_NO_VTABLE if you don't want to generate a 'virtual
  table', and avoid multiple GetAttr calls to retrieve the python
  methods.
*/

#ifndef SWIG_PYTHON_DIRECTOR_NO_VTABLE
#ifndef SWIG_PYTHON_DIRECTOR_VTABLE
#define SWIG_PYTHON_DIRECTOR_VTABLE
#endif
#endif



/*
  Use -DSWIG_DIRECTOR_NO_UEH if you prefer to avoid the use of the
  Undefined Exception Handler provided by swift
*/
#ifndef SWIG_DIRECTOR_NO_UEH
#ifndef SWIG_DIRECTOR_UEH
#define SWIG_DIRECTOR_UEH
#endif
#endif


/*
  Use -DSWIG_DIRECTOR_STATIC if you prefer to avoid the use of the
  'Swig' namespace. This could be usefull for multi-modules projects.
*/
#ifdef SWIG_DIRECTOR_STATIC
/* Force anonymous (static) namespace */
#define Swig
#endif


/*
  Use -DSWIG_DIRECTOR_NORTTI if you prefer to avoid the use of the
  native C++ RTTI and dynamic_cast<>. But be aware that directors
  could stop working when using this option.
*/
#ifdef SWIG_DIRECTOR_NORTTI
/* 
   When we don't use the native C++ RTTI, we implement a minimal one
   only for Directors.
*/
# ifndef SWIG_DIRECTOR_RTDIR
# define SWIG_DIRECTOR_RTDIR
#include <map>

namespace Swig {
  class Director;
  SWIGINTERN std::map<void*,Director*>& get_rtdir_map() {
    static std::map<void*,Director*> rtdir_map;
    return rtdir_map;
  }

  SWIGINTERNINLINE void set_rtdir(void *vptr, Director *rtdir) {
    get_rtdir_map()[vptr] = rtdir;
  }

  SWIGINTERNINLINE Director *get_rtdir(void *vptr) {
    std::map<void*,Director*>::const_iterator pos = get_rtdir_map().find(vptr);
    Director *rtdir = (pos != get_rtdir_map().end()) ? pos->second : 0;
    return rtdir;
  }
}
# endif /* SWIG_DIRECTOR_RTDIR */

# define SWIG_DIRECTOR_CAST(Arg) Swig::get_rtdir(static_cast<void*>(Arg))
# define SWIG_DIRECTOR_RGTR(Arg1, Arg2) Swig::set_rtdir(static_cast<void*>(Arg1), Arg2)

#else

# define SWIG_DIRECTOR_CAST(Arg) dynamic_cast<Swig::Director*>(Arg)
# define SWIG_DIRECTOR_RGTR(Arg1, Arg2)

#endif /* SWIG_DIRECTOR_NORTTI */

extern "C" {
  struct swig_type_info;
}

namespace Swig {  

  /* memory handler */
  struct GCItem 
  {
    virtual ~GCItem() = 0;

    virtual int get_own() const
    {
      return 0;
    }
  };

  GCItem::~GCItem()
  {
  }

  struct GCItem_var
  {
    GCItem_var(GCItem *item = 0) : _item(item)
    {
    }

    GCItem_var& operator=(GCItem *item)
    {
      GCItem *tmp = _item;
      _item = item;
      delete tmp;
      return *this;
    }

    ~GCItem_var() 
    {
      delete _item;
    }
    
    GCItem * operator->() const
    {
      return _item;
    }
    
  private:
    GCItem *_item;
  };
  
  struct GCItem_Object : GCItem
  {
    GCItem_Object(int own) : _own(own)
    {
    }
    
    virtual ~GCItem_Object() 
    {
    }

    int get_own() const
    {
      return _own;
    }
    
  private:
    int _own;
  };

  template <typename Type>
  struct GCItem_T : GCItem
  {
    GCItem_T(Type *ptr) : _ptr(ptr)
    {
    }
    
    virtual ~GCItem_T() 
    {
      delete _ptr;
    }
    
  private:
    Type *_ptr;
  };

  template <typename Type>
  struct GCArray_T : GCItem
  {
    GCArray_T(Type *ptr) : _ptr(ptr)
    {
    }
    
    virtual ~GCArray_T() 
    {
      delete[] _ptr;
    }
    
  private:
    Type *_ptr;
  };

  /* base class for director exceptions */
  class DirectorException {
  protected:
    std::string swig_msg;
  public:
    DirectorException(PyObject *error, const char* hdr ="", const char* msg ="") 
      : swig_msg(hdr)
    {
      SWIG_PYTHON_THREAD_BEGIN_BLOCK; 
      if (strlen(msg)) {
        swig_msg += " ";
        swig_msg += msg;
      }
      if (!PyErr_Occurred()) {
        swig_msg.insert(0, ": ");
        PyErr_SetString(error, getMessage());
      } else {
        SWIG_Python_AddErrorMsg(getMessage());
      }
      SWIG_PYTHON_THREAD_END_BLOCK; 
    }

    const char *getMessage() const
    { 
      return swig_msg.c_str(); 
    }

    static void raise(PyObject *error, const char *msg) 
    {
      throw DirectorException(error, msg);
    }

    static void raise(const char *msg) 
    {
      raise(PyExc_RuntimeError, msg);
    }
  };

  /* unknown exception handler  */
  class UnknownExceptionHandler 
  {
#ifdef SWIG_DIRECTOR_UEH
    static void handler()  {
      try {
        throw;
      } catch (DirectorException& e) {
        std::cerr << "Swig Director exception caught:" << std::endl
                  << e.getMessage() << std::endl;
      } catch (std::exception& e) {
        std::cerr << "std::exception caught: "<< e.what() << std::endl;
      } catch (...) {
        std::cerr << "Unknown exception caught." << std::endl;
      }
      
      std::cerr << std::endl
                << "Python interpreter traceback:" << std::endl;
      PyErr_Print();
      std::cerr << std::endl;
      
      std::cerr << "This exception was caught by the SWIG unexpected exception handler." << std::endl
                << "Try using %feature(\"director:except\") to avoid reaching this point." << std::endl
                << std::endl
                << "Exception is being re-thrown, program will like abort/terminate." << std::endl;
      throw;
    }

  public:
    
    std::unexpected_handler old;
    UnknownExceptionHandler(std::unexpected_handler nh = handler)
    {
      old = std::set_unexpected(nh);
    }

    ~UnknownExceptionHandler()
    {
      std::set_unexpected(old);
    }
#endif
  };

  /* type mismatch in the return value from a python method call */
  class DirectorTypeMismatchException : public Swig::DirectorException {
  public:
    DirectorTypeMismatchException(PyObject *error, const char* msg="") 
      : Swig::DirectorException(error, "Swig director type mismatch", msg)
    {
    }

    DirectorTypeMismatchException(const char* msg="") 
      : Swig::DirectorException(PyExc_TypeError, "Swig director type mismatch", msg)
    {
    }

    static void raise(PyObject *error, const char *msg)
    {
      throw DirectorTypeMismatchException(error, msg);
    }

    static void raise(const char *msg)
    {
      throw DirectorTypeMismatchException(msg);
    }
  };

  /* any python exception that occurs during a director method call */
  class DirectorMethodException : public Swig::DirectorException {
  public:
    DirectorMethodException(const char* msg = "") 
      : DirectorException(PyExc_RuntimeError, "Swig director method error.", msg)
    {
    }    

    static void raise(const char *msg)
    {
      throw DirectorMethodException(msg);
    }
  };

  /* attempt to call a pure virtual method via a director method */
  class DirectorPureVirtualException : public Swig::DirectorException
  {
  public:
    DirectorPureVirtualException(const char* msg = "") 
      : DirectorException(PyExc_RuntimeError, "Swig director pure virtual method called", msg)
    { 
    }

    static void raise(const char *msg) 
    {
      throw DirectorPureVirtualException(msg);
    }
  };


#if defined(SWIG_PYTHON_THREADS)
/*  __THREAD__ is the old macro to activate some thread support */
# if !defined(__THREAD__)
#   define __THREAD__ 1
# endif
#endif

#ifdef __THREAD__
# include "pythread.h"
  class Guard
  {
    PyThread_type_lock & mutex_;
    
  public:
    Guard(PyThread_type_lock & mutex) : mutex_(mutex)
    {
      PyThread_acquire_lock(mutex_, WAIT_LOCK);
    }
    
    ~Guard()
    {
      PyThread_release_lock(mutex_);
    }
  };
# define SWIG_GUARD(mutex) Guard _guard(mutex)
#else
# define SWIG_GUARD(mutex) 
#endif

  /* director base class */
  class Director {
  private:
    /* pointer to the wrapped python object */
    PyObject* swig_self;
    /* flag indicating whether the object is owned by python or c++ */
    mutable bool swig_disown_flag;

    /* decrement the reference count of the wrapped python object */
    void swig_decref() const { 
      if (swig_disown_flag) {
        SWIG_PYTHON_THREAD_BEGIN_BLOCK; 
        Py_DECREF(swig_self); 
        SWIG_PYTHON_THREAD_END_BLOCK; 
      }
    }

  public:
    /* wrap a python object, optionally taking ownership */
    Director(PyObject* self) : swig_self(self), swig_disown_flag(false) {
      swig_incref();
    }


    /* discard our reference at destruction */
    virtual ~Director() {
      swig_decref(); 
    }


    /* return a pointer to the wrapped python object */
    PyObject *swig_get_self() const { 
      return swig_self; 
    }

    /* acquire ownership of the wrapped python object (the sense of "disown"
     * is from python) */
    void swig_disown() const { 
      if (!swig_disown_flag) { 
        swig_disown_flag=true;
        swig_incref(); 
      } 
    }

    /* increase the reference count of the wrapped python object */
    void swig_incref() const { 
      if (swig_disown_flag) {
        Py_INCREF(swig_self); 
      }
    }

    /* methods to implement pseudo protected director members */
    virtual bool swig_get_inner(const char* /* name */) const {
      return true;
    }
    
    virtual void swig_set_inner(const char* /* name */, bool /* val */) const {
    }

  /* ownership management */
  private:
    typedef std::map<void*, GCItem_var> ownership_map;
    mutable ownership_map owner;
#ifdef __THREAD__
    static PyThread_type_lock swig_mutex_own;
#endif

  public:
    template <typename Type>
    void swig_acquire_ownership_array(Type *vptr)  const
    {
      if (vptr) {
        SWIG_GUARD(swig_mutex_own);
        owner[vptr] = new GCArray_T<Type>(vptr);
      }
    }
    
    template <typename Type>
    void swig_acquire_ownership(Type *vptr)  const
    {
      if (vptr) {
        SWIG_GUARD(swig_mutex_own);
        owner[vptr] = new GCItem_T<Type>(vptr);
      }
    }

    void swig_acquire_ownership_obj(void *vptr, int own) const
    {
      if (vptr && own) {
        SWIG_GUARD(swig_mutex_own);
        owner[vptr] = new GCItem_Object(own);
      }
    }
    
    int swig_release_ownership(void *vptr) const
    {
      int own = 0;
      if (vptr) {
        SWIG_GUARD(swig_mutex_own);
        ownership_map::iterator iter = owner.find(vptr);
        if (iter != owner.end()) {
          own = iter->second->get_own();
          owner.erase(iter);
        }
      }
      return own;
    }
  };

#ifdef __THREAD__
  PyThread_type_lock Director::swig_mutex_own = PyThread_allocate_lock();
#endif
}

#endif /* __cplusplus */


#endif
