/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * director.swg
 *
 * This file contains support for director classes that proxy
 * method calls from C++ to Ocaml extensions.
 *
 * ----------------------------------------------------------------------------- */

#ifdef __cplusplus

#include <string>

namespace Swig {
  /* base class for director exceptions */
  class DirectorException {
    protected:
      std::string swig_msg;
    public:
      DirectorException(const char* msg="") {
      }
      const char *getMessage() const { 
        return swig_msg.c_str(); 
      }
      virtual ~DirectorException() {}
  };

  /* type mismatch in the return value from a python method call */
  class DirectorTypeMismatchException : public Swig::DirectorException {
    public:
      DirectorTypeMismatchException(const char* msg="") {
      }
  };

  /* any python exception that occurs during a director method call */
  class DirectorMethodException : public Swig::DirectorException {};

  /* attempt to call a pure virtual method via a director method */
  class DirectorPureVirtualException : public Swig::DirectorException {
    public:
      DirectorPureVirtualException(const char* msg="") {
      }

      static void raise(const char *msg) {
        throw DirectorPureVirtualException(msg);
      }
  };

  /* simple thread abstraction for pthreads on win32 */
#ifdef __THREAD__
#define __PTHREAD__
#if defined(_WIN32) || defined(__WIN32__)
#define pthread_mutex_lock EnterCriticalSection
#define pthread_mutex_unlock LeaveCriticalSection
#define pthread_mutex_t CRITICAL_SECTION
#define MUTEX_INIT(var) CRITICAL_SECTION var
#else
#include <pthread.h>
#define MUTEX_INIT(var) pthread_mutex_t var = PTHREAD_MUTEX_INITIALIZER 
#endif
#endif

  /* director base class */
  class Director {
    private:
      /* pointer to the wrapped ocaml object */
      CAML_VALUE swig_self;
      /* flag indicating whether the object is owned by ocaml or c++ */
      mutable bool swig_disown_flag;

    public:
      /* wrap a ocaml object, optionally taking ownership */
      Director(CAML_VALUE self) : swig_self(self), swig_disown_flag(false) {
        register_global_root(&swig_self);
      }

      /* discard our reference at destruction */
      virtual ~Director() {
        remove_global_root(&swig_self);
        swig_disown(); 
        // Disown is safe here because we're just divorcing a reference that
        // points to us.  
      }

      /* return a pointer to the wrapped ocaml object */
      CAML_VALUE swig_get_self() const { 
	  return swig_self;
      }

      /* acquire ownership of the wrapped ocaml object (the sense of "disown"
       * is from ocaml) */
      void swig_disown() const { 
        if (!swig_disown_flag) { 
          swig_disown_flag=true;
          callback(*caml_named_value("caml_obj_disown"),swig_self);
        } 
      }
  };
}

#endif /* __cplusplus */
