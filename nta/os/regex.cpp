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
*/

#include <nta/os/regex.hpp>
#include <nta/utils/Log.hpp>
#ifdef WIN32
  #include <pcre/pcreposix.h>
#else
  #include <regex.h>
#endif

namespace nta
{
  namespace regex
  {
    bool match(const std::string & re, const std::string & text)
    {        
      NTA_CHECK(!re.empty()) << "Empty regular expressions is invalid";
      
      // Make sure the regex will perform an exact match
      std::string exactRegExp;
      if (re[0] != '^')
        exactRegExp += '^';
      exactRegExp += re;
      if (re[re.length()-1] != '$') 
        exactRegExp += '$';
      
      regex_t r;
      int res = ::regcomp(&r, exactRegExp.c_str(), REG_EXTENDED|REG_NOSUB);
      NTA_CHECK(res == 0) 
        << "regcomp() failed to compile the regular expression: "
        << re << " . The error code is: " << res;
        
      res = regexec(&r, text.c_str(), (size_t) 0, NULL, 0);
      ::regfree(&r);
      return res == 0; 
    }
  }
}
