/* -----------------------------------------------------------------------------
 * director.swg
 *
 * This file contains support for director classes so that C# proxy 
 * methods can be called from C++.
 * ----------------------------------------------------------------------------- */

#ifdef __cplusplus

#if defined(DEBUG_DIRECTOR_OWNED)
#include <iostream>
#endif
#include <string>

namespace Swig {
  /* Director base class - not currently used in C# directors */
  class Director {
  };

  /* Base class for director exceptions */
  class DirectorException {
  protected:
    std::string swig_msg;

  public:
    DirectorException(const char* msg) : swig_msg(msg) {
    }
    DirectorException(const std::string &msg) : swig_msg(msg) {
    }
    const std::string& what() const {
      return swig_msg;
    }
    virtual ~DirectorException() {
    }
  };

  /* Pure virtual method exception */
  class DirectorPureVirtualException : public Swig::DirectorException {
  public:
    DirectorPureVirtualException(const char* msg) : DirectorException(std::string("Attempt to invoke pure virtual method ") + msg) {
    }
  };
}

#endif /* __cplusplus */


