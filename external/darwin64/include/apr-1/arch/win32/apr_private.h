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

/*
 * Note: 
 * This is the windows specific autoconf-like config file
 * which unix would create at build time.
 */

#ifdef WIN32

#ifndef APR_PRIVATE_H
#define APR_PRIVATE_H

/* Include the public APR symbols, include our idea of the 'right'
 * subset of the Windows.h header.  This saves us repetition.
 */
#include "apr.h"

/* 
 * Add a _very_few_ declarations missing from the restricted set of headers
 * (If this list becomes extensive, re-enable the required headers above!)
 * winsock headers were excluded by WIN32_LEAN_AND_MEAN, so include them now
 */
#ifndef SW_HIDE
#define SW_HIDE             0
#endif

/* For the misc.h late-loaded dynamic symbols, we need some obscure types 
 * Avoid dragging in wtypes.h unless it's absolutely necessary [generally
 * not with APR itself, until some GUI-related security is introduced.]
 */
#ifndef _WIN32_WCE
#define HAVE_ACLAPI 1
#ifdef __wtypes_h__
#include <accctrl.h>
#else
#define __wtypes_h__
#include <accctrl.h>
#undef __wtypes_h__
#endif
#else
#define HAVE_ACLAPI 0
#endif

#if APR_HAVE_SYS_TYPES_H
#include <sys/types.h>
#endif
#if APR_HAVE_STDDEF_H
#include <stddef.h>
#endif
#include <stdio.h>
#if APR_HAVE_TIME_H
#include <time.h>
#endif

/* Use this section to define all of the HAVE_FOO_H
 * that are required to build properly.
 */
#define HAVE_LIMITS_H 1
#define HAVE_MALLOC_H 1
#define HAVE_SIGNAL_H 1
/* #define HAVE_STDDEF_H 1 why not? */
#define HAVE_STDLIB_H 1

#define HAVE_STRICMP  1
#define HAVE_STRNICMP 1
#define HAVE_STRDUP   1
#define HAVE_STRSTR   1
#define HAVE_MEMCHR   1

#define SIGHUP     1
/* 2 is used for SIGINT on windows */
#define SIGQUIT    3
/* 4 is used for SIGILL on windows */
#define SIGTRAP    5
#define SIGIOT     6
#define SIGBUS     7
/* 8 is used for SIGFPE on windows */
#define SIGKILL    9
#define SIGUSR1    10
/* 11 is used for SIGSEGV on windows */
#define SIGUSR2    12
#define SIGPIPE    13
#define SIGALRM    14
/* 15 is used for SIGTERM on windows */
#define SIGSTKFLT  16
#define SIGCHLD    17 
#define SIGCONT    18
#define SIGSTOP    19
#define SIGTSTP    20
/* 21 is used for SIGBREAK on windows */
/* 22 is used for SIGABRT on windows */
#define SIGTTIN    23
#define SIGTTOU    24
#define SIGURG     25
#define SIGXCPU    26
#define SIGXFSZ    27
#define SIGVTALRM  28
#define SIGPROF    29
#define SIGWINCH   30
#define SIGIO      31

/* APR COMPATABILITY FUNCTIONS
 * This section should be used to define functions and
 * macros which are need to make Windows features look
 * like POSIX features.
 */
typedef void (Sigfunc)(int);

#define sleep(t)                 Sleep((t) * 1000)

#define SIZEOF_SHORT           2
#define SIZEOF_INT             4
#define SIZEOF_LONGLONG        8
#define SIZEOF_CHAR            1
#define SIZEOF_SSIZE_T         SIZEOF_INT

unsigned __stdcall SignalHandling(void *);
int thread_ready(void);

#if !APR_HAVE_ERRNO_H
APR_DECLARE_DATA int errno;
#define ENOSPC 1
#endif

#if APR_HAVE_IPV6
#define HAVE_GETADDRINFO 1
#define HAVE_GETNAMEINFO 1
#endif

/* MSVC 7.0 introduced _strtoi64 */
#if _MSC_VER >= 1300 && _INTEGRAL_MAX_BITS >= 64 && !defined(_WIN32_WCE)
#define APR_INT64_STRFN	      _strtoi64
#endif

#if APR_HAS_LARGE_FILES
#ifdef APR_INT64_STRFN
#define APR_OFF_T_STRFN         APR_INT64_STRFN
#else
#define APR_OFF_T_STRFN         apr_strtoi64
#endif
#else
#if defined(_WIN32_WCE)
#define APR_OFF_T_STRFN         strtol
#else
#define APR_OFF_T_STRFN         strtoi
#endif
#endif

/* used to check for DWORD overflow in 64bit compiles */
#define APR_DWORD_MAX 0xFFFFFFFFUL

/*
 * Include common private declarations.
 */
#include "../apr_private_common.h"

#endif  /*APR_PRIVATE_H*/
#endif  /*WIN32*/
