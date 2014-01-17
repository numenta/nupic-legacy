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
 * Implementation of utility functions for string conversion
 */

#include <nta/utils/StringUtils.hpp>
#include <nta/utils/Log.hpp>
#include <apr-1/apr_base64.h>

using namespace nta;

bool StringUtils::toBool(const std::string& s, bool throwOnError, bool * fail)
{
  if (fail)
    *fail = false;
  bool b = false;
  std::string us(s);
  std::transform(us.begin(), us.end(), us.begin(), tolower);
  if (us == "true" || us == "yes" || us == "1") {
    b = true;
  } else if (us == "false" || us == "no" || us == "0") {
    b = false;
  } else if (! throwOnError) {
    if (fail)
      *fail = true;
  } else {
    NTA_THROW << "StringUtils::toBool: tried to parse non-boolean string \"" << s << "\"";
  }
  return b;
}
  

Real32 StringUtils::toReal32(const std::string& s, bool throwOnError, bool * fail)
{
  if (fail)
    *fail = false;
  Real32 r;
  std::istringstream ss(s);
  ss >> r;
  if (ss.fail() || !ss.eof())
  {
    if (throwOnError) 
    {
      NTA_THROW << "StringUtils::toReal32 -- invalid string \"" << s << "\"";
    }
    else
    {
      if (fail)
        *fail = true;
    }
  }

  return r;
}

UInt32 StringUtils::toUInt32(const std::string& s, bool throwOnError, bool * fail)
{
  if (fail)
    *fail = false;
  UInt32 i;
  std::istringstream ss(s);
  ss >> i;
  if (ss.fail() || !ss.eof())
  {
    if (throwOnError) 
    {
      NTA_THROW << "StringUtils::toInt -- invalid string \"" << s << "\"";
    }
    else
    {
      if (fail)
        *fail = true;
    }
  }

  return i;
}

Int32 StringUtils::toInt32(const std::string& s, bool throwOnError, bool * fail)
{
  if (fail)
    *fail = false;
  Int32 i;
  std::istringstream ss(s);
  ss >> i;
  if (ss.fail() || !ss.eof())
  {
    if (throwOnError) 
    {
      NTA_THROW << "StringUtils::toInt -- invalid string \"" << s << "\"";
    }
    else
    {
      if (fail)
        *fail = true;
    }
  }

  return i;
}

UInt64 StringUtils::toUInt64(const std::string& s, bool throwOnError, bool * fail)
{
  if (fail)
    *fail = false;
  UInt64 i;
  std::istringstream ss(s);
  ss >> i;
  if (ss.fail() || !ss.eof())
  {
    if (throwOnError) 
    {
      NTA_THROW << "StringUtils::toInt -- invalid string \"" << s << "\"";
    }
    else
    {
      if (fail)
        *fail = true;
    }
  }

  return i;
}


size_t StringUtils::toSizeT(const std::string& s, bool throwOnError, bool * fail)
{
  if (fail)
    *fail = false;
  size_t i;
  std::istringstream ss(s);
  ss >> i;
  if (ss.fail() || !ss.eof())
  {
    if (throwOnError) 
    {
      NTA_THROW << "StringUtils::toSizeT -- invalid string \"" << s << "\"";
    }
    else
    {
      if (fail)
        *fail = true;
    }
  }  
  return i;
}

bool StringUtils::startsWith(const std::string& s, const std::string& prefix)
{
  return s.find(prefix) == 0;
}

bool StringUtils::endsWith(const std::string& s, const std::string& ending)
{
  if (ending.size() > s.size())
    return false;
  size_t found = s.rfind(ending);
  if (found == std::string::npos)
    return false;
  if (found != s.size() - ending.size())
    return false;
  return true;
}


std::string StringUtils::fromInt(long long i)
{
  std::stringstream ss;
  ss << i;
  return ss.str();
}

std::string StringUtils::base64Encode(const void* buf, Size inLen)
{
  Size len = apr_base64_encode_len((int)inLen); // int-casting for win.
  std::string outS(len, '\0');
  apr_base64_encode((char*)outS.data(), (const char*)buf, (int) inLen); // int-casting for win.
  outS.resize(len-1); // len includes the NULL at the end
  return outS;
}


std::string StringUtils::base64Encode(const std::string& s)
{
  Size len = apr_base64_encode_len ( (int) s.size() );
  std::string outS(len, '\0');
  apr_base64_encode((char*)outS.data(), s.data(), (int) s.size());
  outS.resize(len-1); // len includes the NULL at the end
  return outS;
}

std::string StringUtils::base64Decode(const void* buf, Size inLen)
{
  std::string outS(inLen+1, '\0');
  size_t decodedLen = apr_base64_decode_binary ((unsigned char*)outS.data(), (const char*)buf);
  outS.resize(decodedLen);
  return outS;
}


std::string StringUtils::base64Decode(const std::string& s)
{
  std::string outS(s.size()+1, '\0');
  size_t decodedLen = apr_base64_decode_binary ((unsigned char*)outS.data(), s.c_str());
  outS.resize(decodedLen);
  return outS;
}

#define HEXIFY(val) ((val) > 9 ? ('a' + (val) - 10) : ('0' + (val)))

std::string StringUtils::hexEncode(const void* buf, Size inLen)
{
  std::string s(inLen*2, '\0');
  const unsigned char *charbuf = (const unsigned char*)buf;
  for (Size i = 0; i < inLen; i++)
  {
    unsigned char x = charbuf[i];
    // high order bits
    unsigned char val = x >> 4;
    s[i*2] = HEXIFY(val);
    val = x & 0xF;
    s[i*2+1] = HEXIFY(val);
  }
  return s;
}



//--------------------------------------------------------------------------------
void StringUtils::toIntList(const std::string& s, std::vector<Int>& list, bool allowAll,
        bool asRanges)
{
  if(!toIntListNoThrow(s, list, allowAll, asRanges)) {
    const std::string errPrefix = "StringUtils::toIntList() - ";
    throw (std::runtime_error(errPrefix+"Invalid string: " + s));
  }
}

//--------------------------------------------------------------------------------
bool StringUtils::toIntListNoThrow(const std::string& s, std::vector<Int>& list, 
  bool allowAll, bool asRanges)
{
        
  UInt startNum, endNum;
  const char* startP = s.c_str();
  char*   endP;
    
  // Set global errno to 0. strtoul sets this if a conversion error occurs. 
  errno = 0;
    
  // Loop through the string
  list.clear();

  // Skip white space at start
  while (*startP && isspace(*startP))
    startP++;
      
  // Do we allow all?
  if (allowAll) {
    if (!strncmp (startP, "all", 3) && startP[3] == 0)
      return true;
    if (startP[0] == 0)
      return true;
  } else {
    if (startP[0] == 0)
      return false;
  }
             
  while (*startP) 
  {
    // ------------------------------------------------------------------------------
    // Get first digit 
    startNum = strtoul(startP, &endP, 10 /*base*/);
    if (errno != 0)
      return false;
    startP = endP;
        
    // Skip white space
    while (*startP && isspace(*startP))
      startP++;
        
    // ------------------------------------------------------------------------------
    // Do we have a '-'? If so, get the second number
    if (*startP == '-') {
      startP++;
      endNum = strtoul(startP, &endP, 10 /*base*/);
      if (errno != 0)
        return false;
      startP = endP;
        
      // Store all number into the vector
      if (endNum < startNum)
        return false;
      if (asRanges) {
        list.push_back((Int)startNum);
        list.push_back((Int)(endNum - startNum + 1));
      } else {
        for (UInt i=startNum; i<=endNum; i++)
          list.push_back((Int)i);
      }

      // Skip white space
      while (*startP && isspace(*startP))
        startP++;
    } else {
      list.push_back((Int)startNum);
      if (asRanges) 
        list.push_back((Int)1); 
    }
      
    // Done if end of string
    if (*startP == 0)
      break;
        
    // ------------------------------------------------------------------------------
    // Must have a comma between entries 
    if (*startP++ != ',') 
      return false;
        
    // Skip white space after the comma
    while (*startP && isspace(*startP))
      startP++;
      
    // Must be more digits after the comma
    if (*startP == 0)
      return false;
  }

  return true;
}
    
  
//--------------------------------------------------------------------------------
boost::shared_array<Byte> StringUtils::toByteArray(const std::string& s, Size bitCount)
{
  // Get list of integers
  std::vector<Int> list;
  StringUtils::toIntList(s, list, true /*allowAll*/);
  if (list.empty())
    return boost::shared_array<Byte>(nullptr);
          
  // Put this into the mask
  Size numBytes = (bitCount+7) / 8;
  boost::shared_array<Byte> mask(new Byte[numBytes]);
  Byte* maskP = mask.get();
  ::memset(maskP, 0, numBytes);
  for (auto & elem : list) {
    UInt  entry = elem;
    if (entry >= bitCount)
      NTA_THROW << "StringUtils::toByteArray() - " << "The list " << s 
                << " contains an entry greater than the max allowed of " << bitCount; 
    maskP[entry/8] |= 1 << (entry%8);
  }
      
  // Return it
  return mask;
}


