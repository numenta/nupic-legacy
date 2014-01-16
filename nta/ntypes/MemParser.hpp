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

#ifndef NTA_MEM_PARSER2_HPP
#define NTA_MEM_PARSER2_HPP

#include <vector>
#include <sstream>

#include "nta/types/types.hpp"


namespace nta {
  
////////////////////////////////////////////////////////////////////////////
/// Class for parsing numbers and strings out of a memory buffer. 
///
/// This provides a significant performance advantage over using the standard
/// C++ stream input operators operating on a stringstream in memory. 
///
/// @b Responsibility
///  - provide high level parsing functions for extracing numbers and strings
///     from a memory buffer
///
/// @b Resources/Ownerships:
///  - Owns a memory buffer that it allocates in it's constructor. 
///
/// @b Notes:
///  To use this class, you pass in an input stream and a total # of bytes to the
///  constructor. The constructor will then read that number of bytes from the stream
///  into an internal buffer maintained by the MemParser object. Subsequent calls to 
///  MemParser::get() will extract numbers/strings from the internal buffer. 
///
//////////////////////////////////////////////////////////////////////////////
class MemParser
{
public:

  /////////////////////////////////////////////////////////////////////////////////////
  /// Constructor
  ///
  /// @param in     The input stream to get characters from.
  /// @param bytes  The number of bytes to extract from the stream for parsing. 
  ///               0 means extract all bytes 
  ///////////////////////////////////////////////////////////////////////////////////
  MemParser(std::istream& in, UInt32 bytes=0);

  /////////////////////////////////////////////////////////////////////////////////////
  /// Destructor
  ///
  /// Free the MemParser object
  ///////////////////////////////////////////////////////////////////////////////////
  virtual ~MemParser();
  
  /////////////////////////////////////////////////////////////////////////////////////
  /// Read an unsigned integer out of the stream
  ///
  ///////////////////////////////////////////////////////////////////////////////////
  void get(unsigned long& val);

  /////////////////////////////////////////////////////////////////////////////////////
  /// Read an unsigned long long out of the stream
  ///
  ///////////////////////////////////////////////////////////////////////////////////
  void get(unsigned long long& val);
  
  /////////////////////////////////////////////////////////////////////////////////////
  /// Read an signed integer out of the stream
  ///
  ///////////////////////////////////////////////////////////////////////////////////
  void get(long& val);
  
  /////////////////////////////////////////////////////////////////////////////////////
  /// Read a double precision floating point number out of the stream
  ///
  ///////////////////////////////////////////////////////////////////////////////////
  void get(double& val);
  
  /////////////////////////////////////////////////////////////////////////////////////
  /// Read a double precision floating point number out of the stream
  ///
  ///////////////////////////////////////////////////////////////////////////////////
  void get(float& val);

#ifdef NTA_QUAD_PRECISION
  /////////////////////////////////////////////////////////////////////////////////////
  /// Read a triple precision floating point number out of the stream
  ///
  ///////////////////////////////////////////////////////////////////////////////////
  void get(long double& val);
#endif
  
  /////////////////////////////////////////////////////////////////////////////////////
  /// Read a string out of the stream
  ///
  ///////////////////////////////////////////////////////////////////////////////////
  void get(std::string& val);
  
  
  /////////////////////////////////////////////////////////////////////////////////////
  /// >> operator's
  ///////////////////////////////////////////////////////////////////////////////////
  friend MemParser& operator>>(MemParser& in, unsigned long& val)
  {  
    in.get(val);
    return in;
  }

  friend MemParser& operator>>(MemParser& in, unsigned long long& val)
  {  
    in.get(val);
    return in;
  }

  friend MemParser& operator>>(MemParser& in, long& val)
  {  
    in.get(val);
    return in;
  }

  friend MemParser& operator>>(MemParser& in, unsigned int& val)
  {  
    unsigned long lval;
    in.get(lval);
    val = lval;
    return in;
  }

  friend MemParser& operator>>(MemParser& in, int& val)
  {  
    long lval;
    in.get(lval);
    val = lval;
    return in;
  }

  friend MemParser& operator>>(MemParser& in, double& val)
  {  
    in.get(val);
    return in;
  }

  friend MemParser& operator>>(MemParser& in, float& val)
  {  
    in.get(val);
    return in;
  }

#ifdef NTA_QUAD_PRECISION
  friend MemParser& operator>>(MemParser& in, long double& val)
  {  
    in.get(val);
    return in;
  }
#endif

  friend MemParser& operator>>(MemParser& in, std::string& val)
  {  
    in.get(val);
    return in;
  }


private:
  std::string     str_;
  const char*     bufP_;
  UInt32          bytes_;
  
  const char*     startP_;
  const char*     endP_;

};



} // namespace nta

#endif // NTA_MEM_PARSER2_HPP
