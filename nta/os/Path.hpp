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

#ifndef NTA_PATH_HPP
#define NTA_PATH_HPP

//----------------------------------------------------------------------

#include <nta/types/types.hpp>
#include <string>
#include <vector>

//----------------------------------------------------------------------

namespace nta 
{
 /**
   * @b Responsibility:
   *  1. Represent a cross-platform path to a filesystem object 
   *     (file, directory, symlink)
   *  
   *  2. Provide a slew of of path manipulation operations
   *
   * @b Rationale:
   *  File system paths are used a lot. It makes sense to have 
   *  a cross-platform class with a nice interface tailored to our needs. 
   *  In particular operations throw NTA::Exception on failure and 
   *  don't return error codes, which is alligned nicely with the
   *  way we handle errors.
   *
   *  Operations are both static and instance methods (use single implementation).
   *
   * @b Resource/Ownerships:
   *  1. A path string for the instance.
   *  
   * @b Notes:
   *  The Path() constructors don't try to validate the path string
   *  for efficiency reasons (it's complicated too). If you pass
   *  an invalid path string it will fail when you actually try to use
   *  the resulting path.
   *
   *  The error handling strategy is to return error NULLs and not to throw exceptions.
   *  The reason is that it is a very generic low-level class that should not be aware
   *  and depend on the runtime's error handling policy. It may be used in different 
   *  contexts like tools and utilities that may utilize a different error handling 
   *  strategy. It is also a common idiom to return NULL from a failed factory method.
   *
   * @b Performance:
   *  The emphasis is on code readability and ease of use. Performance takes second
   *  place, because the critical path of our codebase doesn't involve a lot of 
   *  path manipulation. In particular, simple ANSI C or POSIX cross-platform implementation
   *  is often preffered to calling specific platform APIs. Whenever possible APR is 
   *  used under the covers.
   *
   *  Note, that constructing a Path object (or calling the Path instance methods)
   * involve an extra copy of the path string into the new Path instance. Again, this 
   * is not prohibitive in most cases. If you are concerned use plain strings and 
   * the static methods.  
   *
   * @b Details, details
   * Portable filesystem interfaces are tricky to get right. We are targeting a simple 
   * and intuitive interface like Python rather than the difficult-to-understand boost interface. 
   * The current implementation does not cover every corner case, but it gets many of them. 
   * For more insight into the details, see the python os.path documentation, java.io.file 
   * documentation and the Wikipedia entry on Path_(computing)
   * 
   * @todo We do not support unicode filenames (yet)
   */
  class Path
  {
  public:
    typedef std::vector<std::string> StringVec;
  
    static const char * sep;
    static const char * pathSep;
    static const char * parDir;
    

    /**
     * This first set of methods act symbolically on strings
     * and don't look at an actual filesystem. 
     */

    /**
     * getParent(path) -> normalize(path/..)
     * Examples: 
     * getParent("/foo/bar") -> "/foo"
     * getParent("foo") -> "."
     * getParent(foo/bar.txt) -> "foo"
     * getParent(rootdir) -> rootdir
     * getParent("../../a") -> "../.."

     * @discussion
     * Can't we do better?
     * What if:  getParent(path) -> normalize(path) - lastElement
     * The problems with this are:
     * - getParent("../..") can't be done 
     * - Also we have to normalize first, because we don't want
     *   getParent("foo/bar/..") -> foo/bar
     * 
     * The main issue with adding ".." are
     * - ".." doesn't exist if you're getting the parent of a file
     *   This is ok because we normalize, which is a symbolic manipulation
     * 
     * For both solutions, we have to know when we reach the "top"
     * if we want to iterate "up" the stack of directories. 
     * With an absolute path, we can check using isRootdir(), but
     * with a relative path, we keep adding ".." forever. 
     * The application has to be aware of this and do the right thing. 
     */
    static std::string getParent(const std::string & path);

    /**
     * getBasename(foo/bar.baz) -> bar.baz
     */
    static std::string getBasename(const std::string & path);

    /**
     * getExtension(foo/bar.baz) -> .baz
     */
    static std::string getExtension(const std::string & path);

    /**
     * Normalize:
     * - remove "../" and "./" (unless leading) c
     * - convert "//" to "/"
     * - remove trailing "/"
     * - normalize(rootdir/..) -> rootdir
     * - normalize(foo/..) -> "."
     * 
     * Note that because we are operating symbolically, the results might
     * be unexpected if there are symbolic links in the path. 
     * For example if /foo/bar is a link to /quux/glorp then
     * normalize("/foo/bar/..")-> "/foo", not "/quux"
     * Also, "path/file/.." is converted to "path" even if "path/file" is a regular
     * file (which doesn't have a ".." entry). 
     * On windows, a path starting with "\\" is a UNC path and the prefix is not converted. 
     */
    static std::string normalize(const std::string & path);

    /**
     * makeAbsolute(path) -> 
     * if isAbsolute(path) -> path
     * unix: -> join(cwd, path)
     * windows: makeAbsolute("c:foo") -> join("c:", cwd, "foo")
     * windows: makeAbsolute("/foo") -> join(cwd.split()[0], "foo")
     */
    static std::string makeAbsolute(const std::string & path);

     /**
     * Convert a unicode string to UTF-8
     */
    static std::string unicodeToUtf8(const std::wstring& path);

     /**
     * Convert a UTF-8 path to a unicode string
     */
    static std::wstring utf8ToUnicode(const std::string& path);

   /**
     * When splitting a path into components, the "prefix" has to be 
     * treated specially. We do not store it in a separate data
     * structure -- the prefix is just the first element of the split. 
     * No normalization is performed. We always have path == join(split(path))
     * except when there are empty components, e.g. foo//bar. Empty components
     * are omitted.
     * See the java.io.file module documentation for some good background
     * split("foo/bar/../quux") -> ("foo", "bar", "..", "quux")
     * split("/foo/bar/quux") -> ("/", "foo", "bar", "quux")
     * split("a:\foo\bar") -> ("a:\", "foo", "bar")
     * split("\\host\drive\file") -> ("\\", "host", "drive", "file")
     * split("/foo//bar/") -> ("/", "foo", "bar") 
     * Note: this behavior is different from the original behavior. 
     */
    static StringVec split(const std::string & path);        

    /**
     * Construct a path from components. path == join(split(path))
     */
    static std::string join(StringVec::const_iterator begin, 
      StringVec::const_iterator end);        

    /**
     * path == "/" on unix
     * path == "/" or path == "a:/" on windows
     */
    static bool isRootdir(const std::string & path);

    /**
     * isAbsolute("/foo/bar") -> true isAbsolute("foo")->false on Unix
     * is Absolute("a:\foo\bar") -> true isAbsolute("\foo\bar") -> false on windows
     */
    static bool isAbsolute(const std::string & path);
    
    /**
     * varargs through overloading
     */
    static std::string join(const std::string & path1, const std::string & path2);
    static std::string join(const std::string & path1, const std::string & path2, 
                            const std::string & path3);
    static std::string join(const std::string & path1, const std::string & path2, 
                            const std::string & path3, const std::string & path4);


    /**
     * This second set of methods must interact with the filesystem 
     * to do their work. 
     */

    /**
     * true if path exists. false is for broken links
     * @todo lexists()
     */
    static bool exists(const std::string & path);

    /**
     * getFileSize throws an exception if does not exist or is a directory
     */
    static Size getFileSize(const std::string & path);

    /**
     * @todo What if source is directory? What id source is file and dest is directory?
     * @todo What if one of source or dest is a symbolic link?
     */
    static void copy(const std::string & source, const std::string & destination);
    static void remove(const std::string & path);
    static void rename(const std::string & oldPath, const std::string & newPath);
    static bool isDirectory(const std::string & path);
    static bool isFile(const std::string & path);
    static bool isSymbolicLink(const std::string & path);
    static bool areEquivalent(const std::string & path1, const std::string & path2);
    // Get a path to the currently running executable
    static std::string getExecutablePath();

    static void setPermissions(const std::string &path, 
        bool userRead, bool userWrite, 
        bool groupRead, bool groupWrite, 
        bool otherRead, bool otherWrite
      );
    
          
    Path(const std::string & path);
    operator const char*() const;

    /**
     * Test for symbolic equivalence, i.e. normalize(a) == normalize(b)
     * To test if they refer to the same file/directory, use areEquivalent
     */
    bool operator==(const Path & other);
    	
    Path & operator +=(const Path & path);
    bool exists() const;
    Path getParent() const;
    Path getBasename() const;
    Path getExtension() const;
    Size getFileSize() const;
    
    Path & normalize();
    Path & makeAbsolute();
    StringVec split() const;      
    
    void remove() const;
    void copy(const std::string & destination) const;
    void rename(const std::string & newPath);
    
    bool isDirectory() const;
    bool isFile() const;
    bool isRootdir() const;
    bool isAbsolute() const;
    bool isSymbolicLink() const;
    bool isEmpty() const;
		
  private:
    // on unix: == "/"; on windows: == "/" || == "C:" || == "C:/"
    static bool isPrefix(const std::string&);
    Path();		
    
  private:
    std::string path_;
  };

  // Global operator  
  Path operator+(const Path & p1, const Path & p2);
}

#endif // NTA_PATH_HPP


