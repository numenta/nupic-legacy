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

#include <nta/os/Path.hpp>
#include <nta/os/Directory.hpp>
#include <nta/os/OS.hpp>
#include <nta/os/FStream.hpp>
#include <nta/utils/Log.hpp>
#include <boost/tokenizer.hpp>
#include <boost/scoped_array.hpp>

#include <sstream>
#include <iterator>
#include <apr-1/apr.h>


#ifdef NTA_PLATFORM_win32
  extern "C" {
    #include <apr-1/arch/win32/apr_arch_utf8.h>
  }
  #include <windows.h>
#else
  #include <sys/types.h>
  #include <sys/stat.h>
  #include <fstream>

#if defined(NTA_PLATFORM_darwin86) || defined(NTA_PLATFORM_darwin64)
    #include <mach-o/dyld.h> // _NSGetExecutablePath
  #else
  // linux
    #include <unistd.h> // readlink    
  #endif
#endif

namespace nta
{
#ifdef WIN32
  const char * Path::sep = "\\";
  const char * Path::pathSep = ";";
#else
  const char * Path::sep = "/";
  const char * Path::pathSep = ":";
#endif
  const char * Path::parDir = "..";

  Path::Path(const std::string & path) : path_(path)
  {
  }

  static apr_status_t getInfo(const std::string & path, apr_int32_t wanted, apr_finfo_t & info)
  {
    NTA_CHECK(!path.empty()) << "Can't get the info of an empty path";

    apr_status_t res;
    apr_pool_t * pool = NULL;
    
  #ifdef WIN32 
    res = ::apr_pool_create(&pool, NULL);
    if (res != APR_SUCCESS)
    {
      NTA_WARN << "Internal error: unable to create APR pool when getting info on path '" << path << "'";
    }
  #endif
    
    res = ::apr_stat(&info, path.c_str(), wanted, pool);
    
  #ifdef WIN32
    ::apr_pool_destroy(pool);
  #endif
    
    return res;
  } 
	
  bool Path::exists(const std::string & path)
  {
    if (path.empty())
      return false;
    
    apr_finfo_t st;      
    apr_status_t res  = getInfo(path, APR_FINFO_TYPE, st);
    return res == APR_SUCCESS;
  }

  static apr_filetype_e getType(const std::string & path, bool check = true)
  {
    apr_finfo_t st;
    apr_status_t res = getInfo(path, APR_FINFO_TYPE, st);
	if (check)
	{
		NTA_CHECK(res == APR_SUCCESS) 
		  << "Can't get info for '" << path << "', " << OS::getErrorMessage();
	}
    
    return st.filetype;
  }

  bool Path::isFile(const std::string & path)
  {
    return getType(path, false) == APR_REG;
  }

  bool Path::isDirectory(const std::string & path)
  {
    return getType(path) == APR_DIR;
  }

  bool Path::isSymbolicLink(const std::string & path)
  {
    return getType(path) == APR_LNK;
  }
    
  bool Path::isAbsolute(const std::string & path)
  {
    NTA_CHECK(!path.empty()) << "Empty path is invalid";
  #ifdef WIN32
    if (path.size() < 2)
      return false;
    else
    {
      bool local = ::isalpha(path[0]) && path[1] == ':';
      bool unc   = path.size() > 2 && path[0] == '\\' && path[1] == '\\';
      return local || unc;
    }

  #else
    return path[0] == '/';
  #endif
  }
  
  bool Path::areEquivalent(const std::string & path1, const std::string & path2)
  {
    apr_finfo_t st1;
    apr_finfo_t st2;
    apr_int32_t wanted = APR_FINFO_IDENT;
    

    apr_status_t s;    
    s = getInfo(path1.c_str(), wanted, st1);
    // If either of the paths does not exist, then we say they are not equivalent
    if (s != APR_SUCCESS)
      return false;

    s = getInfo(path2.c_str(), wanted, st2);
    if (s != APR_SUCCESS)
      return false;

    bool res = true;
    res &= st1.device == st2.device;
    res &= st1.inode == st2.inode;
    // We do not require the names to match. Could be a hard link. 
    // res &= std::string(st1.fname) == std::string(st2.fname);
    
    return res;
  }
  
  std::string Path::getParent(const std::string & path)
  {
    if (path == "") 
      return "";

    std::string np = Path::normalize(path);
    Path::StringVec sv = Path::split(np);
    sv.push_back("..");

    return Path::normalize(Path::join(sv.begin(), sv.end()));
  }
  
  std::string Path::getBasename(const std::string & path)
  {
    std::string::size_type index = path.find_last_of(Path::sep);
    
    if (index == std::string::npos)
      return path;
    
    return path.substr(index+1);
  }
 
  std::string Path::getExtension(const std::string & path) 
  {
    std::string basename = Path::getBasename(path);
    std::string::size_type index = basename.find_last_of('.');
    
    // If its a  regular or hidden filenames with no extension
    // return an empty string
    if (index == std::string::npos ||  // regular filename with no ext 
        index == 0                 ||  // hidden file (starts with a '.')
        index == basename.length() -1) // filename ends with a dot
      return "";
    
    // Don't include the dot, just the extension itself (unlike Python)
    return std::string(basename.c_str() + index + 1, basename.length() - index - 1);
  }
  

  Size Path::getFileSize(const std::string & path)
  {
    apr_finfo_t st;
    apr_int32_t wanted = APR_FINFO_TYPE | APR_FINFO_SIZE;
    apr_status_t res = getInfo(path.c_str(), wanted, st);
    NTA_CHECK(res == APR_SUCCESS);
    NTA_CHECK(st.filetype == APR_REG) << "Can't get the size of a non-file object";
    
    return (Size)st.size;
  }

  std::string Path::normalize(const std::string & path)
  {
    // Easiest way is: split, then remove "." and remove a/.. (but not ../.. !)
    // This does not get a/b/../.. so if we remove a/.., go through the string again
    // Also need to treat rootdir/.. specially
    // Also normalize(foo/..) -> "." but normalize(foo/bar/..) -> "foo"
    StringVec v = Path::split(path);
    if (v.size() == 0) 
      return "";

    StringVec outv;
    bool doAgain = true;
    while (doAgain) 
    {
      doAgain = false;
      for (unsigned int i = 0; i < v.size(); i++) 
      {
        if (v[i] == "") continue; // remove empty fields
        if (v[i] == "." && v.size() > 1) continue; // skip "." unless it is by itself
        if (i == 0 && isRootdir(v[i]) && i+1 < v.size() && v[i+1] == "..") 
        {
          // <root>/.. -> <root>
          outv.push_back(v[i]);
          i++; // skipped following ".."
          doAgain = true;
          continue;
        }
        // remove "foo/.."
        if (i+1 < v.size() && v[i] != ".." && v[i+1] == "..")
        {
          // but as a special case, if the full path is "foo/.." return "."
          if (v.size() == 2) return ".";
          i++;
          doAgain = true;
          continue;
        }
        outv.push_back(v[i]);
      }
      if (doAgain) 
      {
        v = outv;
        outv.clear();
      }
    }
    return Path::join(outv.begin(), outv.end());

  }
  
  std::string Path::makeAbsolute(const std::string & path)
  {
    if (Path::isAbsolute(path))
      return path;
      
    std::string cwd = Directory::getCWD();
    // If its already absolute just return the original path
    if (::strncmp(cwd.c_str(), path.c_str(), cwd.length()) == 0) 
      return path;
    
    // Get rid of trailing separators if any
    if (path.find_last_of(Path::sep) == path.length() - 1)
    {
      cwd = std::string(cwd.c_str(), cwd.length()-1);
    }
    // join the cwd to the path and return it (handle duplicate separators) 
    std::string result = cwd;
    if (path.find_first_of(Path::sep) == 0)
    {
      return cwd + path;
    }
    else
    {
      return cwd + Path::sep + path;
    }
    
    return "";
  }
 
  #ifdef WIN32
  std::string Path::unicodeToUtf8(const std::wstring& path)
  {
    // Assume the worst we can do is have 6 UTF-8 bytes per unicode
    //  character. 
    apr_size_t tmpNameSize = path.size() * 6 + 1;
    
    // Store buffer in a boost::scoped_array so it gets cleaned up for us. 
    boost::scoped_array<char> tmpNameBuf;
    char* tmpNameP = new char[tmpNameSize];
    tmpNameBuf.reset(tmpNameP);
    
    apr_size_t  inWords = path.size()+1;
    apr_size_t  outChars = tmpNameSize;
    
    apr_status_t result = ::apr_conv_ucs2_to_utf8((apr_wchar_t *)path.c_str(), 
                              &inWords, tmpNameP, &outChars);
    if (result != 0 || inWords != 0)
    {
      std::stringstream ss;
      ss << "Path::unicodeToUtf8() - error converting path to UTF-8:" 
         << std::endl << "error code: " << result;
      NTA_THROW << ss.str();
    }
    
    return std::string(tmpNameP); 
  }

  std::wstring Path::utf8ToUnicode(const std::string& path)
  {
    // Assume the number of unicode characters is <= number of UTF-8 bytes. 
    apr_size_t tmpNameSize = path.size() + 1;
    
    // Store buffer in a boost::scoped_array so it gets cleaned up for us. 
    boost::scoped_array<wchar_t> tmpNameBuf;
    wchar_t* tmpNameP = new wchar_t[tmpNameSize];
    tmpNameBuf.reset(tmpNameP);
    
    apr_size_t  inBytes = path.size()+1;
    apr_size_t  outWords = tmpNameSize;
    
    apr_status_t result = ::apr_conv_utf8_to_ucs2(path.c_str(), 
                              &inBytes, (apr_wchar_t*)tmpNameP, &outWords);
    if (result != 0 || inBytes != 0)
    {
      char errBuffer[1024];
      std::stringstream ss;
      ss << "Path::utf8ToUnicode() - error converting path to Unicode"
         << std::endl
         << ::apr_strerror(result, errBuffer, 1024);
        
      NTA_THROW << ss.str();
    }
    
    return std::wstring(tmpNameP); 
  }
  #endif

 
  Path::StringVec Path::split(const std::string & path)
  {
    /**
     * Don't use boost::tokenizer because we need to handle the prefix specially.
     * Handling the prefix is messy on windows, but this is the only place we have 
     * to do it
     */
    StringVec parts;
    std::string::size_type curpos = 0;
    if (path.size() == 0)
      return parts;

#ifndef WIN32
    // only possible prefix is "/"
    if (path[0] == '/') 
    {
      parts.push_back("/");
      curpos++;
    }
#else
    // prefix may be 1) "\", 2) "\\", 3) "[a-z]:", 4) "[a-z]:\"
    if (path.size() == 1) 
    {
      // captures both "\" and "a"
      parts.push_back(path);
      return parts;
    }
    if (path[0] == '\\') 
    {
      if (path[1] == '\\') 
      {
        // case 2
        parts.push_back("\\\\");
        curpos = 2;
      } 
      else 
      {
        // case 1
        parts.push_back("\\");
        curpos = 1;
      }
    } 
    else 
    {
      if (path[1] == ':') 
      {
        if (path.size() > 2 && path[2] == '\\') 
        {
          // case 4
          parts.push_back(path.substr(0, 3));
          curpos = 3;
        } 
        else 
        {
          parts.push_back(path.substr(0, 2));
          curpos = 2;
        }
      }
    }          
#endif

    // simple tokenization based on separator. Note that "foo//bar" -> "foo", "", "bar"
    std::string::size_type newpos;
    while (curpos < path.size() && curpos != std::string::npos) 
    {
      // Be able to split on either separator including mixed separators on Windows
    #ifdef WIN32
      std::string::size_type p1 = path.find("\\", curpos);
      std::string::size_type p2 = path.find("/", curpos);
      newpos = p1 < p2 ? p1 : p2;
    #else
      newpos = path.find(Path::sep, curpos);
    #endif
    
      if (newpos == std::string::npos) 
      {
        parts.push_back(path.substr(curpos));
        curpos = newpos;
      } 
      else 
      {
        // note: if we have a "//" then newpos == curpos and this string is empty
        if (newpos != curpos) 
        {
          parts.push_back(path.substr(curpos, newpos - curpos));
        }
        curpos = newpos + 1;
      }
    }
    
    return parts;

  }

  bool Path::isPrefix(const std::string & s)
  {
#ifdef WIN32
    size_t len = s.length();
    if (len < 2)
      return false;
    if (len == 2)
      return ::isalpha(s[0]) && s[1] == ':';
    else if (len == 3)
    {
      bool localPrefix = ::isalpha(s[0]) && s[1] == ':' && s[2] == '\\';
      bool uncPrefix = s[0] == '\\' && s[1] == '\\' && ::isalpha(s[2]);

      return localPrefix || uncPrefix;
    }
    else // len > 3
      return s[0] == '\\' && s[1] == '\\' && ::isalpha(s[2]);
#else
  return s == "/";
#endif
}

  bool Path::isRootdir(const std::string& s)
  {
    // redundant test on unix, but second test covers windows
    return isPrefix(s);
  }

  std::string Path::join(StringVec::const_iterator begin, StringVec::const_iterator end)
  {
    if (begin == end)
      return "";
      
    if (begin + 1 == end)
      return std::string(*begin);
    
    std::string path(*begin);
  #ifdef WIN32
    if (path[path.length()-1] != Path::sep[0])
      path += Path::sep;
  #else
    // Treat first element specially (on Unix) 
    // it may be a prefix, which is not followed by "/"
    if (!Path::isPrefix(*begin)) 
      path += Path::sep;
  #endif
    begin++;

    while (begin != end) 
    {
      path += *begin;
      begin++;
      if (begin != end) 
      {
        path += Path::sep;
      }
    }
      
    return path;
  }


  void Path::copy(const std::string & source, const std::string & destination)
  {
    NTA_CHECK(!source.empty()) 
      << "Can't copy from an empty source";

    NTA_CHECK(!destination.empty()) 
      << "Can't copy to an empty destination";

    NTA_CHECK(source != destination)
      << "Source and destination must be different";
      
    if (isDirectory(source))
    {
      Directory::copyTree(source, destination);
      return;
    } 

    // The target is always a filename. The input destination
    // Can be either a directory or a filename. If the destination
    // doesn't exist it is treated as a filename.
    std::string target(destination);
    if (Path::exists(destination) && isDirectory(destination))
      target = Path::normalize(Path::join(destination, Path::getBasename(source)));
    
    bool success = true;
  #ifdef WIN32

    // Must remove read-only or hidden files before copy 
    // because they cannot be overwritten. For simplicity
    // I just always remove if it exists.
    if (Path::exists(target))
      Path::remove(target);

    // This will quietly overwrite the destination file if it exists
    std::wstring wsource(utf8ToUnicode(source));
    std::wstring wtarget(utf8ToUnicode(target));
    BOOL res = ::CopyFile(/*(LPCTSTR)*/wsource.c_str(), 
                          /*(LPCTSTR)*/wtarget.c_str(), 
                           FALSE);

    success = res != FALSE;
  #else

    try
    {
      OFStream  out(target.c_str()); 
      out.exceptions(std::ofstream::failbit | std::ofstream::badbit);
      UInt64 size = Path::getFileSize(source);
      if(size) {
        IFStream  in(source.c_str());
        if(out.fail()) {
          std::cout << OS::getErrorMessage() << std::endl;
        }
        in.exceptions(std::ifstream::failbit | std::ifstream::badbit);
        out << in.rdbuf();
      }
    }
    catch(std::exception &e) {
      std::cerr << "Path::copy('" << source << "', '" << target << "'): "
           << e.what() << std::endl;
    }
    catch (...)
    {
      success = false;
    }
  #endif
    if (!success)
      NTA_THROW << "Path::copy() - failed copying file " 
                << source << " to " << destination << " os error: "
                << OS::getErrorMessage();
  }

  void Path::setPermissions(const std::string &path, 
      bool userRead, bool userWrite, 
      bool groupRead, bool groupWrite, 
      bool otherRead, bool otherWrite
    )
  {

    if(Path::isDirectory(path)) {
      Directory::Iterator iter(path);
      Directory::Entry e;
      while(iter.next(e)) {
        std::string sub = Path::join(path, e.path);
        setPermissions(sub, 
          userRead, userWrite,
          groupRead, groupWrite,
          otherRead, otherWrite);
      }
    }

#if WIN32
    int countFailure = 0;
    std::wstring wpath(utf8ToUnicode(path));
    DWORD attr = GetFileAttributes(wpath.c_str());
    if(attr != INVALID_FILE_ATTRIBUTES) {
      if(userWrite) attr &= ~FILE_ATTRIBUTE_READONLY;
      BOOL res = SetFileAttributes(wpath.c_str(), attr);
      if(!res) {
        NTA_WARN << "Path::setPermissions: Failed to set attributes for " << path;
        ++countFailure;
      }
    }
    else {
      NTA_WARN << "Path::setPermissions: Failed to get attributes for " << path;
      ++countFailure;
    }

    if(countFailure > 0) {
      NTA_THROW << "Path::setPermissions failed for " << path;
    }
      
#else

    mode_t mode = 0;
    if (userRead) mode |= S_IRUSR;
    if (userWrite) mode |= S_IRUSR;
    if (groupRead) mode |= S_IRGRP;
    if (groupWrite) mode |= S_IWGRP;
    if (otherRead) mode |= S_IROTH;
    if (otherWrite) mode |= S_IWOTH;
    chmod(path.c_str(), mode);

#endif
  }
  
  void Path::remove(const std::string & path)
  {
    NTA_CHECK(!path.empty()) 
      << "Can't remove an empty path";

    // Just return if it doesn't exist already
    if (!Path::exists(path))
      return;
      
    if (isDirectory(path))
    {
      Directory::removeTree(path);
      return;
    } 

  #ifdef WIN32
    std::wstring wpath(utf8ToUnicode(path));
    BOOL res = ::DeleteFile(/*(LPCTSTR)*/wpath.c_str());
    if (res == FALSE)
      NTA_THROW << "Path::remove() -- unable to delete '" << path
                << "' error message: " << OS::getErrorMessage();
  #else
    int res = ::remove(path.c_str());
    if (res != 0)
      NTA_THROW << "Path::remove() -- unable to delete '" << path
                << "' error message: " << OS::getErrorMessage();
  #endif
  }
    
  void Path::rename(const std::string & oldPath, const std::string & newPath)
  {
    NTA_CHECK(!oldPath.empty() && !newPath.empty()) 
      << "Can't rename to/from empty path";
  #ifdef WIN32
    std::wstring wOldPath(utf8ToUnicode(oldPath));
    std::wstring wNewPath(utf8ToUnicode(newPath));
    BOOL res = ::MoveFile(/*(LPCTSTR)*/wOldPath.c_str(), /*(LPCTSTR)*/wNewPath.c_str());
    if (res == FALSE)
      NTA_THROW << "Path::rename() -- unable to rename '" 
                << oldPath << "' to '" << newPath 
                << "' error message: " << OS::getErrorMessage();
  #else
    int res = ::rename(oldPath.c_str(), newPath.c_str());
    if (res == -1)
      NTA_THROW << "Path::rename() -- unable to rename '" 
                << oldPath << "' to '" << newPath 
                << "' error message: " << OS::getErrorMessage();
  #endif
  }
  
  Path::operator const char *() const
  {
    return path_.c_str();
  }
  
  Path & Path::operator+=(const Path & path)
  {
    Path::StringVec sv;
    sv.push_back(std::string(path_));
    sv.push_back(std::string(path.path_));
    path_ = Path::join(sv.begin(), sv.end());
    return *this;
  }

  bool Path::operator==(const Path & other)
  {
    return Path::normalize(path_) == Path::normalize(other.path_);
  }

  Path Path::getParent() const
  {
    return Path::getParent(path_);
  }
  
  Path Path::getBasename() const
  {
    return Path::getBasename(path_);
  }
  
  Path Path::getExtension() const
  {
    return Path::getExtension(path_); 
	}

  Size Path::getFileSize() const
  {
    return Path::getFileSize(path_); 
	}
    
  Path & Path::normalize()
  {
    path_ = Path::normalize(path_);
    return *this;
  }
  
  Path & Path::makeAbsolute()
  {
    if (!isAbsolute())
      path_ = Path::makeAbsolute(path_);
    return *this;
  }
    
  Path::StringVec Path::split() const
  {
    return Path::split(path_);
  }
  
	void Path::remove() const
  {
    Path::remove(path_);
  }
    
  void Path::rename(const std::string & newPath)
  {
    Path::rename(path_, newPath);
    path_ = newPath;
  }

  bool Path::isDirectory() const
  {
    return Path::isDirectory(path_);
  }
  
  bool Path::isFile() const
  {
    return Path::isFile(path_);
  }

  bool Path::isSymbolicLink() const
  {
    return Path::isSymbolicLink(path_);
  }  
  bool Path::isAbsolute() const
  {
    return Path::isAbsolute(path_);
  }

  bool Path::isRootdir() const
  {
    return Path::isRootdir(path_);
  }

  bool Path::exists() const
  {
    return Path::exists(path_);
  }

  bool Path::isEmpty() const
  {
    return path_.empty();
  }
  
  Path operator+(const Path & p1, const Path & p2)
  {
    Path::StringVec sv;
    sv.push_back(std::string(p1));
    sv.push_back(std::string(p2));
    return Path::join(sv.begin(), sv.end());
  }

  std::string Path::join(const std::string & path1, const std::string & path2)
  {
    return path1 + Path::sep + path2;
  }

  std::string Path::join(const std::string & path1, const std::string & path2, 
                            const std::string & path3)
  {
    return path1 + Path::sep + path2 + Path::sep + path3;
  }

  std::string Path::join(const std::string & path1, const std::string & path2, 
                            const std::string & path3, const std::string & path4)
  {
    return path1 + Path::sep + path2 + Path::sep + path3 + Path::sep + path4;
  }
    
  std::string Path::getExecutablePath()
  {

    std::string epath = "UnknownExecutablePath";
#ifndef NTA_PLATFORM_win32
    char *buf = new char[1000];
    UInt32 bufsize = 1000;
    // sets bufsize to actual length. 
#if defined(NTA_PLATFORM_darwin86) || defined(NTA_PLATFORM_darwin64)
    _NSGetExecutablePath(buf, &bufsize);
    if (bufsize < 1000)
      buf[bufsize] = '\0';
  #else
    int count = readlink("/proc/self/exe", buf, bufsize);
    if (count < 0)
      NTA_THROW << "Unable to read /proc/self/exe to get executable name";
    if (count < 1000)
      buf[count] = '\0';
  #endif

    // make sure it's null-terminated
    buf[999] = '\0';
    epath = buf;
    delete[] buf;
#else
    // windows
    wchar_t *buf = new wchar_t[1000];
    GetModuleFileName(NULL, buf, 1000);
    // null-terminated string guaranteed unless length > 999
    buf[999] = '\0';
    std::wstring wpath(buf);
    delete[] buf;
    epath = unicodeToUtf8(wpath);
#endif

    return epath;
  }

} // namespace nta
