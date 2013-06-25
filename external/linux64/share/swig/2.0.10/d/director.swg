/* -----------------------------------------------------------------------------
 * director.swg
 *
 * This file contains support for director classes so that D proxy
 * methods can be called from C++.
 * ----------------------------------------------------------------------------- */

#ifdef __cplusplus

#if defined(DEBUG_DIRECTOR_OWNED)
#include <iostream>
#endif
#include <string>

namespace Swig {
  // Director base class – not used in D directors.
  class Director {
  };

  // Base class for director exceptions.
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

  // Exception which is thrown when attempting to call a pure virtual method
  // from D code thorugh the director layer.
  class DirectorPureVirtualException : public Swig::DirectorException {
  public:
    DirectorPureVirtualException(const char* msg) : DirectorException(std::string("Attempted to invoke pure virtual method ") + msg) {
    }
  };
}

#endif /* __cplusplus */
