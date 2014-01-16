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

/** @file 
 * Definitions for the FStream classes
 * 
 * These classes are versions of ifstream and ofstream that accept platform independent
 * (i.e. win32 or unix) utf-8 path specifiers for their constructor and open() methods.
 *
 * The native ifstream and ofstream classes on unix already accept UTF-8, but on win32,
 * we must convert the utf-8 path to unicode and then pass it to the 'w' version of
 * ifstream or ofstream
 */


#ifndef NTA_F_STREAM_HPP
#define NTA_F_STREAM_HPP

#include <fstream>

namespace nta {

///////////////////////////////////////////////////////////////////////////////////////
/// IFStream
///
/// @b Responsibility
/// 
/// Open a file for reading
/// 
/// @b Description
///
/// This class overrides the open() and constructor methods of the standard ifstream to
/// handle utf-8 paths. 
///
/////////////////////////////////////////////////////////////////////////////////////
class IFStream : public std::ifstream
{

public:
  //////////////////////////////////////////////////////////////////////////
  /// Construct an OFStream
  /////////////////////////////////////////////////////////////////////////
  IFStream ()  : std::ifstream() {}

  ///////////////////////////////////////////////////////////////////////////////////
  /// WARNING: the std library does not declare a virtual destructor for std::basic_ofstream
  ///  or std::basic_ifstream, which we sub-class. Therefore, the destructor for this class
  ///  will NOT be called and therefore it should not allocate any data members that need
  ///  to be deleted at destruction time. 
  ///////////////////////////////////////////////////////////////////////////////////
  virtual ~IFStream() {}
  
  //////////////////////////////////////////////////////////////////////////
  /// Construct an IFStream
  ///
  /// @param filename the name of the file to open
  /// @param mode the open mode
  /////////////////////////////////////////////////////////////////////////
  IFStream (const char * filename, ios_base::openmode mode = ios_base::in ) : std::ifstream()
  {
    open(filename, mode);
  }

  //////////////////////////////////////////////////////////////////////////
  /// open the given file by name
  ///
  /// @param filename the name of the file to open
  /// @param mode the open mode
  /////////////////////////////////////////////////////////////////////////
  void open(const char * filename, ios_base::openmode mode = ios_base::in );
      
  //////////////////////////////////////////////////////////////////////////
  /// print out diagnostic information on a failed open
  /////////////////////////////////////////////////////////////////////////
  static void diagnostics(const char* filename);
  
}; // end class IFStream


///////////////////////////////////////////////////////////////////////////////////////
/// OFStream
///
/// @b Responsibility
/// 
/// Open a file for writing
/// 
/// @b Description
///
/// This class overrides the open() and constructor methods of the standard ofstream to
/// handle utf-8 paths. 
/// 
/////////////////////////////////////////////////////////////////////////////////////
class OFStream : public std::ofstream
{

public:
  //////////////////////////////////////////////////////////////////////////
  /// Construct an OFStream
  /////////////////////////////////////////////////////////////////////////
  OFStream ()  : std::ofstream() {}

  ///////////////////////////////////////////////////////////////////////////////////
  /// WARNING: the std library does not declare a virtual destructor for std::basic_ofstream
  ///  or std::basic_ifstream, which we sub-class. Therefore, the destructor for this class
  ///  will NOT be called and therefore it should not allocate any data members that need
  ///  to be deleted at destruction time. 
  ///////////////////////////////////////////////////////////////////////////////////
  virtual ~OFStream() {}
  
  
  //////////////////////////////////////////////////////////////////////////
  /// Construct an OFStream
  ///
  /// @param filename the name of the file to open
  /// @param mode the open mode
  /////////////////////////////////////////////////////////////////////////
  OFStream (const char * filename, ios_base::openmode mode = ios_base::out ) : std::ofstream()
  {
    open(filename, mode);
  }

  //////////////////////////////////////////////////////////////////////////
  /// open the given file by name
  ///
  /// @param filename the name of the file to open
  /// @param mode the open mode
  /////////////////////////////////////////////////////////////////////////
  void open(const char * filename, ios_base::openmode mode = ios_base::out );
      
  
}; // end class OFStream

class ZLib
{
public:
  static void *fopen(const std::string &filename, const std::string &mode,
    std::string *errorMessage=0);
};



} // end namespace nta





#endif // NTA_F_STREAM_HPP



