/* -----------------------------------------------------------------------------
 * director.swg
 *
 * This file contains support for director classes that proxy
 * method calls from C++ to Ruby extensions.
 * ----------------------------------------------------------------------------- */

/*
  Use -DSWIG_DIRECTOR_NOUEH if you prefer to avoid the use of the
  Undefined Exception Handler provided by swig.
*/
#ifndef SWIG_DIRECTOR_NOUEH
#ifndef SWIG_DIRECTOR_UEH
#define SWIG_DIRECTOR_UEH
#endif
#endif

#ifdef __cplusplus

#include <string>
#include <iostream>
#include <map>

# define SWIG_DIRECTOR_CAST(ARG) dynamic_cast<Swig::Director *>(ARG)

namespace Swig {
  /* memory handler */
  struct GCItem 
  {
    virtual ~GCItem()
    {
    }

    virtual ruby_owntype get_own() const
    {
      return 0;
    }
  };
  
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

  struct GCItem_Object : GCItem
  {
    GCItem_Object(ruby_owntype own) : _own(own)
    {
    }
    
    virtual ~GCItem_Object() 
    {
    }

    ruby_owntype get_own() const
    {
      return _own;
    }
    
  private:
    ruby_owntype _own;
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


  /* body args */
  struct body_args {
    VALUE recv;
    ID id;
    int argc;
    VALUE *argv;
  };
  
  /* Base class for director exceptions */
  class DirectorException {
  protected:
    VALUE swig_error;
    std::string swig_msg;
  protected:
    DirectorException(VALUE error)
      : swig_error(error)
    {
    }
    
    DirectorException(VALUE error, const char* hdr, const char* msg ="") 
      : swig_error(error), swig_msg(hdr) {
      if (strlen(msg)) {
	swig_msg += " ";
	swig_msg += msg;
      }
      if (swig_msg.size()) {
	VALUE str = rb_str_new(swig_msg.data(), swig_msg.size());
	swig_error = rb_exc_new3(error, str);
      } else {
	swig_error = error;
      }
    }
  public:
    VALUE getType() const  { 
      return CLASS_OF(swig_error); 
    }
    VALUE getError() const {
      return swig_error;
    }
    const std::string& getMessage() const 
    {
      return swig_msg;
    }
    
    virtual ~DirectorException() {}
  };
  
  /* unknown exception handler  */

  class UnknownExceptionHandler 
  {
#ifdef SWIG_DIRECTOR_UEH
    static void handler() {
      try {
	throw;
      } catch (DirectorException& e) {
	std::cerr << "SWIG Director exception caught:" << std::endl
		  << e.getMessage() << std::endl;
      } catch (std::exception& e) {
	std::cerr << "std::exception caught: "<< e.what() << std::endl;
      } catch (...) {
	std::cerr << "Unknown exception caught." << std::endl;
      }      
      std::cerr << std::endl
		<< "Ruby interpreter traceback:" << std::endl;
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


  /* Type mismatch in the return value from a Ruby method call */
  class DirectorTypeMismatchException : public Swig::DirectorException {
  public:
    DirectorTypeMismatchException(VALUE error, const char *msg="")
      : Swig::DirectorException(error, "SWIG director type mismatch", msg) 
    {
    }

    DirectorTypeMismatchException(const char *msg="")
      : Swig::DirectorException(rb_eTypeError, "SWIG director type mismatch", msg) 
    {
    }

    static void raise(VALUE error, const char *msg) {
      throw DirectorTypeMismatchException(error, msg);
    }

    static void raise(const char *msg) {
      throw DirectorTypeMismatchException(msg);
    }
  };

  /* Any Ruby exception that occurs during a director method call */
  class DirectorMethodException : public Swig::DirectorException {
  public:
    DirectorMethodException(VALUE error) 
      : Swig::DirectorException(error) {
    }

    DirectorMethodException(const char* msg = "") 
      : Swig::DirectorException(rb_eRuntimeError, "SWIG director method error.", msg) {
    }
    
    static void raise(VALUE error)
    {
      throw DirectorMethodException(error);
    }    
  };

  /* Attempted to call a pure virtual method via a director method */
  class DirectorPureVirtualException : public Swig::DirectorException
  {
  public:
    DirectorPureVirtualException(const char* msg = "") 
      : DirectorException(rb_eRuntimeError, "SWIG director pure virtual method called", msg)
    { 
    }

    static void raise(const char *msg) 
    {
      throw DirectorPureVirtualException(msg);
    }
  };

  /* Simple thread abstraction for pthreads on win32 */
#ifdef __THREAD__
# define __PTHREAD__
# if defined(_WIN32) || defined(__WIN32__)
#  define pthread_mutex_lock EnterCriticalSection
#  define pthread_mutex_unlock LeaveCriticalSection
#  define pthread_mutex_t CRITICAL_SECTION
#  define SWIG_MUTEX_INIT(var) var
# else
#  include <pthread.h>
#  define SWIG_MUTEX_INIT(var) var = PTHREAD_MUTEX_INITIALIZER 
# endif
#endif

#ifdef  __PTHREAD__
  struct Guard
  {
    pthread_mutex_t *_mutex;
    
    Guard(pthread_mutex_t &mutex) : _mutex(&mutex)
    {
      pthread_mutex_lock(_mutex);
    }
    
    ~Guard()
    {
      pthread_mutex_unlock(_mutex);
    }
  };
# define SWIG_GUARD(mutex) Guard _guard(mutex)
#else
# define SWIG_GUARD(mutex) 
#endif

  /* director base class */
  class Director {
  private:
    /* pointer to the wrapped Ruby object */
    VALUE swig_self;
    /* flag indicating whether the object is owned by Ruby or c++ */
    mutable bool swig_disown_flag;

  public:
    /* wrap a Ruby object, optionally taking ownership */
    Director(VALUE self) : swig_self(self), swig_disown_flag(false) {
    }

    /* discard our reference at destruction */
    virtual ~Director() {
    }

    /* return a pointer to the wrapped Ruby object */
    VALUE swig_get_self() const { 
      return swig_self; 
    }

    /* acquire ownership of the wrapped Ruby object (the sense of "disown"
     * is from Ruby) */
    void swig_disown() const { 
      if (!swig_disown_flag) { 
        swig_disown_flag = true;
      } 
    }

  /* ownership management */
  private:
    typedef std::map<void*, GCItem_var> swig_ownership_map;
    mutable swig_ownership_map swig_owner;
#ifdef __PTHREAD__
    static pthread_mutex_t swig_mutex_own;
#endif

  public:
    template <typename Type>
    void swig_acquire_ownership_array(Type *vptr)  const
    {
      if (vptr) {
	SWIG_GUARD(swig_mutex_own);
	swig_owner[vptr] = new GCArray_T<Type>(vptr);
      }
    }
    
    template <typename Type>
    void swig_acquire_ownership(Type *vptr)  const
    {
      if (vptr) {	
	SWIG_GUARD(swig_mutex_own);
	swig_owner[vptr] = new GCItem_T<Type>(vptr);
      }
    }

    void swig_acquire_ownership_obj(void *vptr, ruby_owntype own) const
    {
      if (vptr && own) {
	SWIG_GUARD(swig_mutex_own);
	swig_owner[vptr] = new GCItem_Object(own);
      }
    }
    
    ruby_owntype swig_release_ownership(void *vptr) const
    {
      ruby_owntype own = 0;
      if (vptr) {
	SWIG_GUARD(swig_mutex_own);
	swig_ownership_map::iterator iter = swig_owner.find(vptr);
	if (iter != swig_owner.end()) {
	  own = iter->second->get_own();
	  swig_owner.erase(iter);
	}
      }
      return own;
    }
  };
}

#endif /* __cplusplus */


