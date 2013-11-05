/*
 * ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
 * Numenta, Inc. a separate commercial license for this software code, the
 * following terms and conditions apply:
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 3 as
 * published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see http://www.gnu.org/licenses.
 *
 * http://numenta.org/licenses/
 * ---------------------------------------------------------------------
 */

/** @file */

//----------------------------------------------------------------------

#ifndef NTA_LOGGING_EXCEPTION_HPP
#define NTA_LOGGING_EXCEPTION_HPP

#include <nta/types/Exception.hpp>
#include <sstream>
#include <vector> 

namespace nta
{
  class LoggingException : public Exception
  {
  public:
    LoggingException(const std::string& filename, UInt32 lineno) :
      Exception(filename, lineno, std::string()), ss_(std::string()),
      lmessageValid_(false), alreadyLogged_(false)
    {
    }

    virtual ~LoggingException() throw();

    const char * getMessage() const
    {
      // Make sure we use a persistent string. Otherwise the pointer may
      // become invalid. 
      // If the underlying stringstream object hasn't changed, don't regenerate lmessage_.
      // This is important because if we catch this exception a second call to exception.what() 
      // will trash the buffer returned by a first call to exception.what()
      if (! lmessageValid_) {
        lmessage_ = ss_.str();
        lmessageValid_ = true;
      }
      return lmessage_.c_str();
    }

    // for Index.hpp: // because stringstream cant take << vector
    LoggingException& operator<<(std::vector<unsigned int, std::allocator<unsigned int> >  v)
    {
      lmessageValid_ = false;
      ss_ << "[";
      for(int i=0; i<v.size(); i++)
        ss_ << v[i] << " ";
      ss_ << "]";
      return *this;
    } 

    template <typename T> LoggingException& operator<<(const T& obj)
    {
      // underlying stringstream changes, so let getMessage() know 
      // to regenerate lmessage_
      lmessageValid_ = false;
      ss_ << obj;
      return *this;
    }

    LoggingException(const LoggingException& l) : Exception(l), 
                                                  ss_(l.ss_.str()), 
                                                  lmessage_(""), 
                                                  lmessageValid_(false),
                                                  alreadyLogged_(true) // copied exception does not log

    {
      // make sure message string is up to date for debuggers. 
      getMessage();
    }

  private:
    std::stringstream ss_;
    mutable std::string lmessage_;  // mutable because getMesssage() modifies it
    mutable bool lmessageValid_;
    bool alreadyLogged_;
  }; // class LoggingException

}

#endif // NTA_LOGGING_EXCEPTION_HPP
