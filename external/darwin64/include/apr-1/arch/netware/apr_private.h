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
 * This is the netware-specific autoconf-like config file
 * which unix creates at ./configure time.
 */

#ifdef NETWARE

#ifndef APR_PRIVATE_H
#define APR_PRIVATE_H

/* Pick up publicly advertised headers and symbols before the
 * APR internal private headers and symbols
 */
#include <apr.h>

/* Pick up privately consumed headers */
#include <ndkvers.h>

/* Include alloca.h to get compiler-dependent defines */ 
#include <alloca.h>

#include <sys/types.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <library.h>
#include <netware.h>

/* Use this section to define all of the HAVE_FOO_H
 * that are required to build properly.
 */
#define HAVE_DLFCN_H    1
#define HAVE_LIMITS_H   1
#define HAVE_SIGNAL_H   1
#define HAVE_STDDEF_H   1
#define HAVE_STDLIB_H   1
#ifndef USE_WINSOCK
#define HAVE_SYS_SELECT_H 1
#define HAVE_WRITEV       1
#endif
#define HAVE_SYS_STAT_H 1
#define HAVE_SYS_MMAN_H 1
#define HAVE_FCNTL_H    1
#define HAVE_ICONV_H    1
#define HAVE_UTIME_H    1

#define HAVE_STRICMP    1
#define HAVE_STRNICMP   1
#define HAVE_STRDUP     1
#define HAVE_STRSTR     1
#define HAVE_MEMCHR     1
#define HAVE_CALLOC     1
#define HAVE_UTIME      1

#define HAVE_GETENV     1
#define HAVE_SETENV     1
#define HAVE_UNSETENV   1

#define HAVE_WRITEV     1

#define HAVE_GETPASS_R  1
/*
 * Hack around older NDKs which have only the getpassword() function,
 * a threadsafe, API-equivilant of getpass_r().
 */
#if (CURRENT_NDK_THRESHOLD < 709060000)
#define getpass_r       getpassword
#endif

/*#define DSO_USE_DLFCN */

#ifdef NW_BUILD_IPV6
#define HAVE_GETADDRINFO 1
#define HAVE_GETNAMEINFO 1
#endif

/* 1 is used for SIGABRT on netware */
/* 2 is used for SIGFPE on netware */
/* 3 is used for SIGILL on netware */
/* 4 is used for SIGINT on netware */
/* 5 is used for SIGSEGV on netware */
/* 6 is used for SIGTERM on netware */
/* 7 is used for SIGPOLL on netware */

#if (CURRENT_NDK_THRESHOLD < 306030000)
#define SIGKILL         11
#define SIGALRM         13
#define SIGCHLD         14 
#define SIGCONT         15
#define SIGHUP          16
#define SIGPIPE         17
#define SIGQUIT         18
#define SIGSTOP         19
#define SIGTSTP         20
#define SIGTTIN         21
#define SIGTTOU         22
#define SIGUSR1         23
#define SIGUSR2         24
#endif

#define SIGTRAP         25
#define SIGIOT          26
#define SIGSTKFLT       28
#define SIGURG          29
#define SIGXCPU         30
#define SIGXFSZ         31
#define SIGVTALRM       32
#define SIGPROF         33
#define SIGWINCH        34
#define SIGIO           35

#if (CURRENT_NDK_THRESHOLD < 406230000)
#undef  SA_NOCLDSTOP
#define SA_NOCLDSTOP    0x00000001
#endif
#ifndef SIGBUS
#define SIGBUS          SIGSEGV
#endif

#define _getch          getcharacter

#define SIZEOF_SHORT    2
#define SIZEOF_INT      4
#define SIZEOF_LONGLONG 8
#define SIZEOF_CHAR     1
#define SIZEOF_SSIZE_T  SIZEOF_INT

void netware_pool_proc_cleanup();

/* NLM registration routines for managing which NLMs
    are using the library. */
int register_NLM(void *NLMHandle);
int unregister_NLM(void *NLMHandle);

/* Application global data management */
extern int  gLibId;
extern void *gLibHandle;

typedef struct app_data {
    int     initialized;
    void*   gPool;
    void*   gs_aHooksToSort;
    void*   gs_phOptionalHooks;
    void*   gs_phOptionalFunctions;
    void*   gs_nlmhandle;
    rtag_t  gs_startup_rtag;
    rtag_t  gs_socket_rtag;
    rtag_t  gs_lookup_rtag;
    rtag_t  gs_event_rtag;
    rtag_t  gs_pcp_rtag;
    void*   gs_ldap_xref_lock;
    void*   gs_xref_head;
} APP_DATA;

int setGlobalPool(void *data);
void* getGlobalPool();
int setStatCache(void *data);
void* getStatCache();

/* Redefine malloc to use the library malloc call so 
    that all of the memory resources will be owned
    and can be shared by the library. */
#undef malloc
#define malloc(x) library_malloc(gLibHandle,x)
#ifndef __MWERKS__
#define _alloca         alloca
#endif

/* 64-bit integer conversion function */
#define APR_INT64_STRFN strtoll

#if APR_HAS_LARGE_FILES
#define APR_OFF_T_STRFN strtoll
#else
#define APR_OFF_T_STRFN strtol
#endif

/* used to check DWORD overflow for 64bit compiles */
#define APR_DWORD_MAX   0xFFFFFFFFUL

/*
 * Include common private declarations.
 */
#include "../apr_private_common.h"

#endif  /*APR_PRIVATE_H*/
#endif  /*NETWARE*/
