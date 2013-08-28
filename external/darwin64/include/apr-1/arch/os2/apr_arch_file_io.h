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

#include "apr_private.h"
#include "apr_general.h"
#include "apr_thread_mutex.h"
#include "apr_file_io.h"
#include "apr_file_info.h"
#include "apr_errno.h"
#include "apr_poll.h"

/* We have an implementation of mkstemp but it's not very multi-threading 
 * friendly & is part of the POSIX emulation rather than native so don't
 * use it.
 */
#undef HAVE_MKSTEMP

#define APR_FILE_DEFAULT_BUFSIZE 4096
#define APR_FILE_BUFSIZE APR_FILE_DEFAULT_BUFSIZE

struct apr_file_t {
    apr_pool_t *pool;
    HFILE filedes;
    char * fname;
    int isopen;
    int buffered;
    int eof_hit;
    apr_int32_t flags;
    int timeout;
    int pipe;
    HEV pipeSem;
    enum { BLK_UNKNOWN, BLK_OFF, BLK_ON } blocking;

    /* Stuff for buffered mode */
    char *buffer;
    apr_size_t bufsize;        /* Read/Write position in buffer             */
    apr_size_t bufpos;         /* Read/Write position in buffer             */
    unsigned long dataRead;    /* amount of valid data read into buffer     */
    int direction;             /* buffer being used for 0 = read, 1 = write */
    unsigned long filePtr;     /* position in file of handle                */
    apr_thread_mutex_t *mutex; /* mutex semaphore, must be owned to access
                                  the above fields                          */
};

struct apr_dir_t {
    apr_pool_t *pool;
    char *dirname;
    ULONG handle;
    FILEFINDBUF3 entry;
    int validentry;
};

apr_status_t apr_file_cleanup(void *);
apr_status_t apr_os2_time_to_apr_time(apr_time_t *result, FDATE os2date, 
                                      FTIME os2time);
apr_status_t apr_apr_time_to_os2_time(FDATE *os2date, FTIME *os2time,
                                      apr_time_t aprtime);

/* see win32/fileio.h for description of these */
extern const char c_is_fnchar[256];

#define IS_FNCHAR(c) c_is_fnchar[(unsigned char)c]

apr_status_t filepath_root_test(char *path, apr_pool_t *p);
apr_status_t filepath_drive_get(char **rootpath, char drive, 
                                apr_int32_t flags, apr_pool_t *p);
apr_status_t filepath_root_case(char **rootpath, char *root, apr_pool_t *p);

#endif  /* ! FILE_IO_H */

