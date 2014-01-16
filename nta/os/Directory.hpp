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


#ifndef NTA_DIRECTORY_HPP
#define NTA_DIRECTORY_HPP

//----------------------------------------------------------------------

#include <apr-1/apr.h>
#include <apr-1/apr_file_info.h>
#include <string>

//----------------------------------------------------------------------

namespace nta 
{
  class Path;
  
  namespace Directory
  {
    // check if a directory exists
    bool exists(const std::string & path);

    bool empty(const std::string & path);
    
    // get current working directory
    std::string getCWD();
		
    // set current working directories
    void setCWD(const std::string & path);

    // Copy directory tree rooted in 'source' to 'destination'
    void copyTree(const std::string & source, const std::string & destination);
    		
    // Remove directory tree rooted in 'path'
    bool removeTree(const std::string & path, bool noThrow=false);
		
    // Create directory 'path' including all parent directories if missing
    // returns the first directory that was actually created.
    //
    // For example if path is /A/B/C/D 
    //    if /A/B/C/D exists it returns ""
    //    if /A/B exists it returns /A/B/C
    //    if /A doesn't exist it returns /A/B/C/D
    // 
    // Failures will throw an exception
    void create(const std::string & path, bool otherAccess=false, bool recursive=false);

    std::string createTemporary(const std::string &templatePath);

    struct Entry : public apr_finfo_t
    {
      enum Type { FILE, DIRECTORY, LINK };
			
      Type type;
      std::string path;
    };

    class Iterator
    {
    public:

      Iterator(const Path & path);		
      Iterator(const std::string & path);
      ~Iterator();
		
      // Resets directory to start. Subsequent call to next() 
      // will retrieve the first entry
      void reset();
      // get next directory entry
      Entry * next(Entry & e);
		
    private:
      Iterator();
      Iterator(const Iterator &);
		
      void init(const std::string & path);
    private:
      std::string path_;
      apr_dir_t * handle_;
      apr_pool_t * pool_;
    };
  }
}

#endif // NTA_DIRECTORY_HPP


