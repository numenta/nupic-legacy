/* ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
 * with Numenta, Inc., for a separate license for this software code, the
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

#ifndef NTA_EXCEPTION_HPP
#define NTA_EXCEPTION_HPP

#include <nta/types/types.hpp>
#include <stdexcept>

//----------------------------------------------------------------------

namespace nta
{
  /**
   * @b Responsibility
   *  The Exception class is the standard Numenta exception class.
   *  It is responsible for storing rich error information: 
   *  the filename and line number where the exceptional situation
   *  occured and a message that describes the exception.
   *  
   * @b Rationale:
   *  It is important to store the location (filename, line number) where
   *  an exception originated, but no standard excepton class does it.
   *  The stack trace is even better and brings C++ programming to the
   *  ease of use of languages like Java and C#.
   *
   * @b Usage:
   *  This class may be used directly by instatiating an instance
   *  and throwing it, but usually you will use the NTA_THROW macro
   *  that makes it much simpler by automatically retreiving the __FILE__
   *  and __LINE__ for you and also using a wrapping LogItem that allows 
   *  you to construct the exception message conveniently using the <<
   *  streame operator (see nta/utils/Log.hpp for further details).
   *
   * @b Notes:
   *  1. Exception is a subclass of the standard std::runtime_error. 
   *  This is useful if your code needs to interoperate with other
   *  code that is not aware of the Exception class, but understands 
   *  std::runtime_error. The what() method will return the exception message
   *  and the location information will not be avaialable to such code.
   *  
   *  2. Source file and line number information is useful of course
   *  only if you have access to the source code. It is not recommended
   *  to display this information to users most of the time.    
   */
  class Exception : public std::runtime_error
  {
  public:
    /**
     * Constructor
     *
     * Take the filename, line number and message
     * and store it in private members
     *
     * @param filename [const std::string &] the name of the source file 
     *        where the exception originated.
     * @param lineno [UInt32] the line number in the source file where 
     *        the exception originated.
     *
     * @param message [const std::string &] the description of exception
     */
    Exception(const std::string & filename, 
              UInt32 lineno, 
              const std::string & message,
              const std::string & stacktrace = "") :
      std::runtime_error(""),
      filename_(filename),
      lineno_(lineno),
      message_(message),
      stackTrace_(stacktrace)
    {
    }
    
    /**
     * Destructor
     *
     * Doesn't do anything, but must be present
     * because the base class std::runtime_error
     * defines a pure virtual destructor and the
     * default destructor provided by the compiler
     * doesn't have a empty exception specification
     *
     */
    virtual ~Exception() throw()
    {
    }
    
    /**
     * Get the exception message via what()
     *
     * Overload the what() method of std::runtime_error
     * and returns the exception description message.
     * The emptry exception specification is required because
     * it is part of the signature of std::runtime_error::what().
     *
     * @retval [const Byte *] the exception message
     */ 
    virtual const char * what() const throw()
    {
      try
      {
        return getMessage();
      }
      catch (...)
      {
        return "Exception caught in non-throwing Exception::what()";
      }
    }
    
    /**
     * Get the source filename
     *
     * Returns the full path to the source file, from which
     * the exception was thrown.
     *
     * @retval [const Byte *] the source filename
     */ 
    const char * getFilename() const
    {
      return filename_.c_str();
    }
    
    /**
     * Get the line number in the source file
     *
     * Returns the (0-based) line number in the source file,
     * from which the exception was thrown.
     *
     * @retval [UInt32] the line number in the source file
     */ 
    UInt32 getLineNumber() const
    {
      return lineno_;
    }

    /**
     * Get the error message
     *
     * @retval [const char *] the error message
     */
    virtual const char * getMessage() const
    {
      return message_.c_str();
    }

    /**
     * Get the stack trace
     *
     * Returns the stack trace from the point the exception
     * was thrown.
     *
     * @retval [const Byte *] the stack trace
     */  
    virtual const char * getStackTrace() const
    {
      return stackTrace_.c_str();
    }

  protected:
    std::string filename_;
    UInt32 lineno_;
    std::string message_;
    std::string stackTrace_;

    
  }; // end class Exception 
} // end namespace nta

#endif // NTA_EXCEPTION_HPP

