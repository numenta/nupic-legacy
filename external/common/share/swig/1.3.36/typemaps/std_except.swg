%include <typemaps/exception.swg>
%include <std/std_except.i>

/* 
   Mark all of std exception classes as "exception classes" via
   the "exceptionclass" feature.
   
   If needed, you can disable it by using %noexceptionclass.
*/

%define %std_exception_map(Exception, Code)
  %exceptionclass  Exception; 
#if !defined(SWIG_STD_EXCEPTIONS_AS_CLASSES)
  %typemap(throws,noblock=1) Exception {
    SWIG_exception_fail(Code, $1.what());
  }
  %ignore Exception;
  struct Exception {
  };
#endif
%enddef

namespace std {
  %std_exception_map(bad_exception,      SWIG_SystemError);
  %std_exception_map(domain_error,       SWIG_ValueError);
  %std_exception_map(exception,          SWIG_SystemError);
  %std_exception_map(invalid_argument,   SWIG_ValueError);
  %std_exception_map(length_error,       SWIG_IndexError);
  %std_exception_map(logic_error,        SWIG_RuntimeError);
  %std_exception_map(out_of_range,       SWIG_IndexError);
  %std_exception_map(overflow_error,     SWIG_OverflowError);
  %std_exception_map(range_error,        SWIG_OverflowError);
  %std_exception_map(runtime_error,      SWIG_RuntimeError);
  %std_exception_map(underflow_error,    SWIG_OverflowError);
}

#if defined(SWIG_STD_EXCEPTIONS_AS_CLASSES)

namespace std {
  struct exception 
  {
    virtual ~exception() throw();
    virtual const char* what() const throw();
  };

  struct bad_exception : exception 
  {
  };

  struct logic_error : exception 
  {
    logic_error(const string& msg);
  };

  struct domain_error : logic_error 
  {
    domain_error(const string& msg);
  };

  struct invalid_argument : logic_error 
  {
    invalid_argument(const string& msg);
  };

  struct length_error : logic_error 
  {
    length_error(const string& msg);
  };

  struct out_of_range : logic_error 
  {
    out_of_range(const string& msg);
  };

  struct runtime_error : exception 
  {
    runtime_error(const string& msg);
  };

  struct range_error : runtime_error 
  {
    range_error(const string& msg);
  };

  struct overflow_error : runtime_error 
  {
    overflow_error(const string& msg);
  };

  struct underflow_error : runtime_error 
  {
    underflow_error(const string& msg);
  };
}

#endif
