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
 * 
 */ 

#include "nta/utils/Log.hpp"
#include "nta/ntypes/MemParser.hpp"
#include "nta/ntypes/MemStream.hpp"
#include <cstring>
#include <cstdlib>



using namespace std;
namespace nta { 
 
////////////////////////////////////////////////////////////////////////////
// MemParser constructor
//////////////////////////////////////////////////////////////////////////////
MemParser::MemParser(std::istream& in, UInt32 bytes) 
{
  if (bytes == 0)
  {
    // -----------------------------------------------------------------------------
    // Read all available bytes from the stream
    // -----------------------------------------------------------------------------
    std::string  data;
    const int  chunkSize = 0x10000;
    auto  chunkP = new char[chunkSize];
    while (!in.eof()) {
      in.read(chunkP, chunkSize);
      NTA_CHECK (in.good() || in.eof()) 
          << "MemParser::MemParser() - error reading data from stream";
      data.append (chunkP, in.gcount());
    }
    
    bytes_ = (UInt32)data.size();
    bufP_ = new char[bytes_+1];
    NTA_CHECK (bufP_ != nullptr) << "MemParser::MemParser() - out of memory";
    ::memmove ((void*)bufP_, data.data(), bytes_);
    ((char*)bufP_)[bytes_] = 0;
    
    delete[] chunkP;
  }
  else
  {
    // -----------------------------------------------------------------------------
    // Read given # of bytes from the stream
    // -----------------------------------------------------------------------------
    bytes_ = bytes;
    bufP_ = new char[bytes_+1];  
    NTA_CHECK (bufP_ != nullptr) << "MemParser::MemParser() - out of memory";
    
    in.read ((char*)bufP_, bytes);
    ((char*)bufP_)[bytes] = 0;
    NTA_CHECK (in.good()) << "MemParser::MemParser() - error reading data from stream";
  }
  // Setup start and end pointers
  startP_ = bufP_;
  endP_ = startP_ + bytes_;  
}  

////////////////////////////////////////////////////////////////////////////
// Destructor
//////////////////////////////////////////////////////////////////////////////
MemParser::~MemParser() 
{
  delete[] bufP_;
}  


////////////////////////////////////////////////////////////////////////////
// Read an unsigned integer number out
//////////////////////////////////////////////////////////////////////////////
void MemParser::get(unsigned long& val) 
{ 
  const char* prefix = "MemParser::get(unsigned long&) - ";
  char* endP;
  
  NTA_CHECK (startP_ < endP_) << prefix << "EOF";

  val = ::strtoul (startP_, &endP, 0);
  
  NTA_CHECK (endP != startP_ && endP <= endP_) << prefix
      << "parse error, not a valid integer";
    
  startP_ = endP;
}  

////////////////////////////////////////////////////////////////////////////
// Read an unsigned long long number out
//////////////////////////////////////////////////////////////////////////////
void MemParser::get(unsigned long long& val) 
{ 
  const char* prefix = "MemParser::get(unsigned long long&) - ";
  char* endP;
  
  NTA_CHECK (startP_ < endP_) << prefix << "EOF";

  val = ::strtoul (startP_, &endP, 0);
  
  NTA_CHECK (endP != startP_ && endP <= endP_) << prefix
      << "parse error, not a valid integer";
    
  startP_ = endP;
}  

////////////////////////////////////////////////////////////////////////////
// Read an signed integer number out
//////////////////////////////////////////////////////////////////////////////
void MemParser::get(long& val) 
{ 
  const char* prefix = "MemParser::get(long&) - ";
  char* endP;
  
  NTA_CHECK (startP_ < endP_) << prefix << "EOF";

  val = ::strtol (startP_, &endP, 0);
  
  NTA_CHECK (endP != startP_ && endP <= endP_) << prefix
      << "parse error, not a valid integer";
    
  startP_ = endP;
}  

////////////////////////////////////////////////////////////////////////////
// Read a double-precision float out
//////////////////////////////////////////////////////////////////////////////
void MemParser::get(double& val) 
{
  const char* prefix = "MemParser::get(double&) - ";
  char* endP;
  
  NTA_CHECK (startP_ < endP_) << prefix << "EOF";

  val = ::strtod (startP_, &endP);
  
  NTA_CHECK (endP != startP_ && endP <= endP_) << prefix
      << "parse error, not a valid floating point value";
    
  startP_ = endP;
}  

#ifdef NTA_QUAD_PRECISION
////////////////////////////////////////////////////////////////////////////
// Read a triple-precision float out
//////////////////////////////////////////////////////////////////////////////
void MemParser::get(long double& val) 
{
  const char* prefix = "MemParser::get(long double&) - ";
  char* endP;
  
  NTA_CHECK (startP_ < endP_) << prefix << "EOF";

  val = ::strtold (startP_, &endP);
  
  NTA_CHECK (endP != startP_ && endP <= endP_) << prefix
      << "parse error, not a valid floating point value";
    
  startP_ = endP;
}  
#endif 

////////////////////////////////////////////////////////////////////////////
// Read a single-precision float out
//////////////////////////////////////////////////////////////////////////////
void MemParser::get(float& val) 
{
  double f;
  get(f);
  val = (float)f;
}  


////////////////////////////////////////////////////////////////////////////
// Read string out
//////////////////////////////////////////////////////////////////////////////
void MemParser::get(std::string& val) 
{ 
  const char* prefix = "MemParser::get(string&) - ";
  
  // First, skip leading white space
  const char* cP = startP_;
  while (cP < endP_) {
    char c = *cP;
    if (c != 0 && c != ' ' && c != '\t' && c != '\n' && c != '\r')
      break;
    cP++;
  }
  NTA_CHECK (cP < endP_) << prefix << "EOF";
  
  size_t len = strcspn(cP, " \t\n\r");
  NTA_CHECK (len > 0) << prefix
      << "parse error, not a valid string";
      
  val.assign (cP, len);
  startP_ = cP + len;
}  



  
} // namespace nta
