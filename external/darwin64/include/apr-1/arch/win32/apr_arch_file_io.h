/* Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef FILE_IO_H
#define FILE_IO_H

#include "apr.h"
#include "apr_private.h"
#include "apr_pools.h"
#include "apr_general.h"
#include "apr_tables.h"
#include "apr_thread_mutex.h"
#include "apr_file_io.h"
#include "apr_file_info.h"
#include "apr_errno.h"
#include "apr_arch_misc.h"
#include "apr_poll.h"

#ifdef HAVE_SYS_STAT_H
#include <sys/stat.h>
#endif
#if APR_HAVE_SYS_TYPES_H
#include <sys/types.h>
#endif
#ifdef HAVE_SYS_FCNTL_H
#include <fcntl.h>
#endif
#ifdef HAVE_TIME_H
#include <time.h>
#endif
#if APR_HAVE_DIRENT_H
#include <dirent.h>
#endif
#ifdef HAVE_MALLOC_H
#include <malloc.h>
#endif

#if APR_HAS_UNICODE_FS
#include "arch/win32/apr_arch_utf8.h"
#include <wchar.h>

/* Helper functions for the WinNT ApiW() functions.  APR treats all
 * resource identifiers (files, etc) by their UTF-8 name, to provide 
 * access to all named identifiers.  [UTF-8 completely maps Unicode 
 * into char type strings.]
 *
 * The _path flavors below provide us fast mappings of the
 * Unicode filename //?/D:/path and //?/UNC/mach/share/path mappings,
 * which allow unlimited (well, 32000 wide character) length names.
 * These prefixes may appear in Unicode, but must not appear in the
 * Ascii API calls.  So we tack them on in utf8_to_unicode_path, and
 * strip them right back off in unicode_to_utf8_path.
 */
apr_status_t utf8_to_unicode_path(apr_wchar_t* dststr, apr_size_t dstchars, 
                                  const char* srcstr);
apr_status_t unicode_to_utf8_path(char* dststr, apr_size_t dstchars, 
                                  const apr_wchar_t* srcstr);

#endif /* APR_HAS_UNICODE_FS */

/* Another Helper functions for the WinNT ApiW() functions.  We need to
 * derive some 'resource' names (max length 255 characters, prefixed with
 * Global/ or Local/ on WinNT) from something that looks like a filename.
 * Since 'resource' names never contain slashes, convert these to '_'s
 * and return the appropriate char* or wchar* for ApiA or ApiW calls.
 */

void *res_name_from_filename(const char *file, int global, apr_pool_t *pool);

#define APR_FILE_MAX MAX_PATH

#define APR_FILE_DEFAULT_BUFSIZE 4096
/* For backwards-compat */
#define APR_FILE_BUFSIZE APR_FILE_DEFAULT_BUFSIZE

/* obscure ommissions from msvc's sys/stat.h */
#ifdef _MSC_VER
#define S_IFIFO        _S_IFIFO /* pipe */
#define S_IFBLK        0060000  /* Block Special */
#define S_IFLNK        0120000  /* Symbolic Link */
#define S_IFSOCK       0140000  /* Socket */
#define S_IFWHT        0160000  /* Whiteout */
#endif

/* Internal Flags for apr_file_open */
#define APR_OPENINFO     0x00100000 /* Open without READ or WRITE access */
#define APR_OPENLINK     0x00200000 /* Open a link itself, if supported */
#define APR_READCONTROL  0x00400000 /* Read the file's owner/perms */
#define APR_WRITECONTROL 0x00800000 /* Modify the file's owner/perms */
/* #define APR_INHERIT   0x01000000 -- Defined in apr_arch_inherit.h! */
#define APR_STDIN_FLAG   0x02000000 /* Obtained via apr_file_open_stdin() */
#define APR_STDOUT_FLAG  0x04000000 /* Obtained via apr_file_open_stdout() */
#define APR_STDERR_FLAG  0x06000000 /* Obtained via apr_file_open_stderr() */
#define APR_STD_FLAGS    (APR_STDIN_FLAG | APR_STDOUT_FLAG | APR_STDERR_FLAG)
#define APR_WRITEATTRS   0x08000000 /* Modify the file's attributes */

/* Entries missing from the MSVC 5.0 Win32 SDK:
 */
#ifndef FILE_ATTRIBUTE_DEVICE
#define FILE_ATTRIBUTE_DEVICE        0x00000040
#endif
#ifndef FILE_ATTRIBUTE_REPARSE_POINT
#define FILE_ATTRIBUTE_REPARSE_POINT 0x00000400
#endif
#ifndef FILE_FLAG_OPEN_NO_RECALL
#define FILE_FLAG_OPEN_NO_RECALL     0x00100000
#endif
#ifndef FILE_FLAG_OPEN_REPARSE_POINT
#define FILE_FLAG_OPEN_REPARSE_POINT 0x00200000
#endif
#ifndef TRUSTEE_IS_WELL_KNOWN_GROUP
#define TRUSTEE_IS_WELL_KNOWN_GROUP  5
#endif

/* Information bits available from the WIN32 FindFirstFile function */
#define APR_FINFO_WIN32_DIR (APR_FINFO_NAME  | APR_FINFO_TYPE \
                           | APR_FINFO_CTIME | APR_FINFO_ATIME \
                           | APR_FINFO_MTIME | APR_FINFO_SIZE)

/* Sneak the Readonly bit through finfo->protection for internal use _only_ */
#define APR_FREADONLY 0x10000000 

/* Private function for apr_stat/lstat/getfileinfo/dir_read */
int fillin_fileinfo(apr_finfo_t *finfo, WIN32_FILE_ATTRIBUTE_DATA *wininfo, 
                    int byhandle, apr_int32_t wanted);

/* Private function that extends apr_stat/lstat/getfileinfo/dir_read */
apr_status_t more_finfo(apr_finfo_t *finfo, const void *ufile, 
                        apr_int32_t wanted, int whatfile);

/* whatfile types for the ufile arg */
#define MORE_OF_HANDLE 0
#define MORE_OF_FSPEC  1
#define MORE_OF_WFSPEC 2

/* quick run-down of fields in windows' apr_file_t structure that may have 
 * obvious uses.
 * fname --  the filename as passed to the open call.
 * dwFileAttricutes -- Attributes used to open the file.
 * append -- Windows doesn't support the append concept when opening files.
 *           APR needs to keep track of this, and always make sure we append
 *           correctly when writing to a file with this flag set TRUE.
 */

/* for apr_poll.c */
#define filedes filehand

struct apr_file_t {
    apr_pool_t *pool;
    HANDLE filehand;
    BOOLEAN pipe;              /* Is this a pipe of a file? */
    OVERLAPPED *pOverlapped;
    apr_interval_time_t timeout;
    apr_int32_t flags;

    /* File specific info */
    apr_finfo_t *finfo;
    char *fname;
    DWORD dwFileAttributes;
    int eof_hit;
    BOOLEAN buffered;          // Use buffered I/O?
    int ungetchar;             // Last char provided by an unget op. (-1 = no char)
    int append; 

    /* Stuff for buffered mode */
    char *buffer;
    apr_size_t bufpos;         // Read/Write position in buffer
    apr_size_t bufsize;        // The size of the buffer
    apr_size_t dataRead;       // amount of valid data read into buffer
    int direction;             // buffer being used for 0 = read, 1 = write
    apr_off_t filePtr;         // position in file of handle
    apr_thread_mutex_t *mutex; // mutex semaphore, must be owned to access the above fields

    /* if there is a timeout set, then this pollset is used */
    apr_pollset_t *pollset;

    /* Pipe specific info */    
};

struct apr_dir_t {
    apr_pool_t *pool;
    HANDLE dirhand;
    apr_size_t rootlen;
    char *dirname;
    char *name;
    union {
#if APR_HAS_UNICODE_FS
        struct {
            WIN32_FIND_DATAW *entry;
        } w;
#endif
#if APR_HAS_ANSI_FS
        struct {
            WIN32_FIND_DATAA *entry;
        } n;
#endif        
    };
    int bof;
};

/* There are many goofy characters the filesystem can't accept
 * or can confound the cmd.exe shell.  Here's the list
 * [declared in filesys.c]
 */
extern const char apr_c_is_fnchar[256];

#define IS_FNCHAR(c) (apr_c_is_fnchar[(unsigned char)(c)] & 1)
#define IS_SHCHAR(c) ((apr_c_is_fnchar[(unsigned char)(c)] & 2) == 2)


/* If the user passes APR_FILEPATH_TRUENAME to either
 * apr_filepath_root or apr_filepath_merge, this fn determines
 * that the root really exists.  It's expensive, wouldn't want
 * to do this too frequenly.
 */
apr_status_t filepath_root_test(char *path, apr_pool_t *p);


/* The apr_filepath_merge wants to canonicalize the cwd to the 
 * addpath if the user passes NULL as the old root path (this
 * isn't true of an empty string "", which won't be concatenated.
 *
 * But we need to figure out what the cwd of a given volume is,
 * when the user passes D:foo.  This fn will determine D:'s cwd.
 *
 * If flags includes the bit APR_FILEPATH_NATIVE, the path returned
 * is in the os-native format.
 */
apr_status_t filepath_drive_get(char **rootpath, char drive, 
                                apr_int32_t flags, apr_pool_t *p);


/* If the user passes d: vs. D: (or //mach/share vs. //MACH/SHARE),
 * we need to fold the case to canonical form.  This function is
 * supposed to do so.
 */
apr_status_t filepath_root_case(char **rootpath, char *root, apr_pool_t *p);


apr_status_t file_cleanup(void *);

extern apr_status_t
apr_file_socket_pipe_create(apr_file_t **in,
                            apr_file_t **out,
                            apr_pool_t *p);

extern apr_status_t
apr_file_socket_pipe_close(apr_file_t *file);

#endif  /* ! FILE_IO_H */
