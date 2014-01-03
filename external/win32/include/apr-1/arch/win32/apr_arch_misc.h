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

#ifndef MISC_H
#define MISC_H

#include "apr.h"
#include "apr_portable.h"
#include "apr_private.h"
#include "apr_general.h"
#include "apr_pools.h"
#include "apr_getopt.h"
#include "apr_thread_proc.h"
#include "apr_file_io.h"
#include "apr_errno.h"
#include "apr_getopt.h"

#if APR_HAVE_STDIO_H
#include <stdio.h>
#endif
#if APR_HAVE_SIGNAL_H
#include <signal.h>
#endif
#if APR_HAVE_PTHREAD_H
#include <pthread.h>
#endif
#if APR_HAVE_STDLIB_H
#include <stdlib.h>
#endif
#if APR_HAVE_STRING_H
#include <string.h>
#endif
#ifndef _WIN32_WCE
#include <tlhelp32.h>
#endif

struct apr_other_child_rec_t {
    apr_pool_t *p;
    struct apr_other_child_rec_t *next;
    apr_proc_t *proc;
    void (*maintenance) (int, void *, int);
    void *data;
    apr_os_file_t write_fd;
};

#define WSAHighByte 2
#define WSALowByte 0

/* start.c and apr_app.c helpers and communication within misc.c
 *
 * They are not for public consumption, although apr_app_init_complete
 * must be an exported symbol to avoid reinitialization.
 */
extern int APR_DECLARE_DATA apr_app_init_complete;

int apr_wastrtoastr(char const * const * *retarr,
                    wchar_t const * const *arr, int args);

/* Platform specific designation of run time os version.
 * Gaps allow for specific service pack levels that
 * export new kernel or winsock functions or behavior.
 */
typedef enum {
    APR_WIN_UNK =       0,
    APR_WIN_UNSUP =     1,
    APR_WIN_95 =       10,
    APR_WIN_95_B =     11,
    APR_WIN_95_OSR2 =  12,
    APR_WIN_98 =       14,
    APR_WIN_98_SE =    16,
    APR_WIN_ME =       18,

    APR_WIN_UNICODE =  20, /* Prior versions support only narrow chars */

    APR_WIN_CE_3 =     23, /* CE is an odd beast, not supporting */
                           /* some pre-NT features, such as the    */
    APR_WIN_NT =       30, /* narrow charset APIs (fooA fns), while  */
    APR_WIN_NT_3_5 =   35, /* not supporting some NT-family features.  */
    APR_WIN_NT_3_51 =  36,

    APR_WIN_NT_4 =     40,
    APR_WIN_NT_4_SP2 = 42,
    APR_WIN_NT_4_SP3 = 43,
    APR_WIN_NT_4_SP4 = 44,
    APR_WIN_NT_4_SP5 = 45,
    APR_WIN_NT_4_SP6 = 46,

    APR_WIN_2000 =     50,
    APR_WIN_2000_SP1 = 51,
    APR_WIN_2000_SP2 = 52,
    APR_WIN_XP =       60,
    APR_WIN_XP_SP1 =   61,
    APR_WIN_XP_SP2 =   62,
    APR_WIN_2003 =     70,
    APR_WIN_VISTA =    80,
    APR_WIN_7 =        90
} apr_oslevel_e;

extern APR_DECLARE_DATA apr_oslevel_e apr_os_level;

apr_status_t apr_get_oslevel(apr_oslevel_e *);

/* The APR_HAS_ANSI_FS symbol is PRIVATE, and internal to APR.
 * APR only supports char data for filenames.  Like most applications,
 * characters >127 are essentially undefined.  APR_HAS_UNICODE_FS lets
 * the application know that utf-8 is the encoding method of APR, and
 * only incidently hints that we have Wide OS calls.
 *
 * APR_HAS_ANSI_FS is simply an OS flag to tell us all calls must be
 * the unicode eqivilant.
 */

#if defined(_WIN32_WCE) || defined(WINNT)
#define APR_HAS_ANSI_FS           0
#else
#define APR_HAS_ANSI_FS           1
#endif

/* IF_WIN_OS_IS_UNICODE / ELSE_WIN_OS_IS_ANSI help us keep the code trivial
 * where have runtime tests for unicode-ness, that aren't needed in any
 * build which supports only WINNT or WCE.
 */
#if APR_HAS_ANSI_FS && APR_HAS_UNICODE_FS
#define IF_WIN_OS_IS_UNICODE if (apr_os_level >= APR_WIN_UNICODE)
#define ELSE_WIN_OS_IS_ANSI else
#else /* APR_HAS_UNICODE_FS */
#define IF_WIN_OS_IS_UNICODE
#define ELSE_WIN_OS_IS_ANSI
#endif /* WINNT */

#if defined(_MSC_VER) && !defined(_WIN32_WCE)
#include "crtdbg.h"

static APR_INLINE void* apr_malloc_dbg(size_t size, const char* filename,
                                       int linenumber)
{
    return _malloc_dbg(size, _CRT_BLOCK, filename, linenumber);
}

static APR_INLINE void* apr_realloc_dbg(void* userData, size_t newSize,
                                        const char* filename, int linenumber)
{
    return _realloc_dbg(userData, newSize, _CRT_BLOCK, filename, linenumber);
}

#else

static APR_INLINE void* apr_malloc_dbg(size_t size, const char* filename,
                                       int linenumber)
{
    return malloc(size);
}

static APR_INLINE void* apr_realloc_dbg(void* userData, size_t newSize,
                                        const char* filename, int linenumber)
{
    return realloc(userData, newSize);
}

#endif  /* ! _MSC_VER */

typedef enum {
    DLL_WINBASEAPI = 0,    /* kernel32 From WinBase.h       */
    DLL_WINADVAPI = 1,     /* advapi32 From WinBase.h       */
    DLL_WINSOCKAPI = 2,    /* mswsock  From WinSock.h       */
    DLL_WINSOCK2API = 3,   /* ws2_32   From WinSock2.h      */
    DLL_SHSTDAPI = 4,      /* shell32  From ShellAPI.h      */
    DLL_NTDLL = 5,         /* shell32  From our real kernel */
    DLL_defined = 6        /* must define as last idx_ + 1  */
} apr_dlltoken_e;

FARPROC apr_load_dll_func(apr_dlltoken_e fnLib, char *fnName, int ordinal);

/* The apr_load_dll_func call WILL return 0 set error to
 * ERROR_INVALID_FUNCTION if the function cannot be loaded
 */
#define APR_DECLARE_LATE_DLL_FUNC(lib, rettype, calltype, fn, ord, args, names) \
    typedef rettype (calltype *apr_winapi_fpt_##fn) args; \
    static apr_winapi_fpt_##fn apr_winapi_pfn_##fn = NULL; \
    static int apr_winapi_chk_##fn = 0; \
    static APR_INLINE int apr_winapi_ld_##fn(void) \
    {   if (apr_winapi_pfn_##fn) return 1; \
        if (apr_winapi_chk_##fn ++) return 0; \
        if (!apr_winapi_pfn_##fn) \
            apr_winapi_pfn_##fn = (apr_winapi_fpt_##fn) \
                                      apr_load_dll_func(lib, #fn, ord); \
        if (apr_winapi_pfn_##fn) return 1; else return 0; }; \
    static APR_INLINE rettype apr_winapi_##fn args \
    {   if (apr_winapi_ld_##fn()) \
            return (*(apr_winapi_pfn_##fn)) names; \
        else { SetLastError(ERROR_INVALID_FUNCTION); return 0;} }; \

#define APR_HAVE_LATE_DLL_FUNC(fn) apr_winapi_ld_##fn()

/* Provide late bound declarations of every API function missing from
 * one or more supported releases of the Win32 API
 *
 * lib is the enumerated token from apr_dlltoken_e, and must correspond
 * to the string table entry in start.c used by the apr_load_dll_func().
 * Token names (attempt to) follow Windows.h declarations prefixed by DLL_
 * in order to facilitate comparison.  Use the exact declaration syntax
 * and names from Windows.h to prevent ambigutity and bugs.
 *
 * rettype and calltype follow the original declaration in Windows.h
 * fn is the true function name - beware Ansi/Unicode #defined macros
 * ord is the ordinal within the library, use 0 if it varies between versions
 * args is the parameter list following the original declaration, in parens
 * names is the parameter list sans data types, enclosed in parens
 *
 * #undef/re#define the Ansi/Unicode generic name to abate confusion
 * In the case of non-text functions, simply #define the original name
 */

#if !defined(_WIN32_WCE) && !defined(WINNT)
/* This group is available to all versions of WINNT 4.0 SP6 and later */

#ifdef GetFileAttributesExA
#undef GetFileAttributesExA
#endif
APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, BOOL, WINAPI, GetFileAttributesExA, 0, (
    IN LPCSTR lpFileName,
    IN GET_FILEEX_INFO_LEVELS fInfoLevelId,
    OUT LPVOID lpFileInformation),
    (lpFileName, fInfoLevelId, lpFileInformation));
#define GetFileAttributesExA apr_winapi_GetFileAttributesExA
#undef GetFileAttributesEx
#define GetFileAttributesEx apr_winapi_GetFileAttributesExA

#ifdef GetFileAttributesExW
#undef GetFileAttributesExW
#endif
APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, BOOL, WINAPI, GetFileAttributesExW, 0, (
    IN LPCWSTR lpFileName,
    IN GET_FILEEX_INFO_LEVELS fInfoLevelId,
    OUT LPVOID lpFileInformation),
    (lpFileName, fInfoLevelId, lpFileInformation));
#define GetFileAttributesExW apr_winapi_GetFileAttributesExW

APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, BOOL, WINAPI, CancelIo, 0, (
    IN HANDLE hFile),
    (hFile));
#define CancelIo apr_winapi_CancelIo

APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, BOOL, WINAPI, TryEnterCriticalSection, 0, (
    LPCRITICAL_SECTION lpCriticalSection),
    (lpCriticalSection));
#define TryEnterCriticalSection apr_winapi_TryEnterCriticalSection

APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, BOOL, WINAPI, SwitchToThread, 0, (
    void),
    ());
#define SwitchToThread apr_winapi_SwitchToThread

APR_DECLARE_LATE_DLL_FUNC(DLL_WINADVAPI, BOOL, WINAPI, GetEffectiveRightsFromAclW, 0, (
    IN PACL pacl,
    IN PTRUSTEE_W pTrustee,
    OUT PACCESS_MASK pAccessRights),
    (pacl, pTrustee, pAccessRights));
#define GetEffectiveRightsFromAclW apr_winapi_GetEffectiveRightsFromAclW

APR_DECLARE_LATE_DLL_FUNC(DLL_WINADVAPI, BOOL, WINAPI, GetNamedSecurityInfoW, 0, (
    IN LPWSTR pObjectName,
    IN SE_OBJECT_TYPE ObjectType,
    IN SECURITY_INFORMATION SecurityInfo,
    OUT PSID *ppsidOwner,
    OUT PSID *ppsidGroup,
    OUT PACL *ppDacl,
    OUT PACL *ppSacl,
    OUT PSECURITY_DESCRIPTOR *ppSecurityDescriptor),
    (pObjectName, ObjectType, SecurityInfo, ppsidOwner, ppsidGroup,
        ppDacl, ppSacl, ppSecurityDescriptor));
#define GetNamedSecurityInfoW apr_winapi_GetNamedSecurityInfoW

APR_DECLARE_LATE_DLL_FUNC(DLL_WINADVAPI, BOOL, WINAPI, GetNamedSecurityInfoA, 0, (
    IN LPSTR pObjectName,
    IN SE_OBJECT_TYPE ObjectType,
    IN SECURITY_INFORMATION SecurityInfo,
    OUT PSID *ppsidOwner,
    OUT PSID *ppsidGroup,
    OUT PACL *ppDacl,
    OUT PACL *ppSacl,
    OUT PSECURITY_DESCRIPTOR *ppSecurityDescriptor),
    (pObjectName, ObjectType, SecurityInfo, ppsidOwner, ppsidGroup,
        ppDacl, ppSacl, ppSecurityDescriptor));
#define GetNamedSecurityInfoA apr_winapi_GetNamedSecurityInfoA
#undef GetNamedSecurityInfo
#define GetNamedSecurityInfo apr_winapi_GetNamedSecurityInfoA

APR_DECLARE_LATE_DLL_FUNC(DLL_WINADVAPI, BOOL, WINAPI, GetSecurityInfo, 0, (
    IN HANDLE handle,
    IN SE_OBJECT_TYPE ObjectType,
    IN SECURITY_INFORMATION SecurityInfo,
    OUT PSID *ppsidOwner,
    OUT PSID *ppsidGroup,
    OUT PACL *ppDacl,
    OUT PACL *ppSacl,
    OUT PSECURITY_DESCRIPTOR *ppSecurityDescriptor),
    (handle, ObjectType, SecurityInfo, ppsidOwner, ppsidGroup,
        ppDacl, ppSacl, ppSecurityDescriptor));
#define GetSecurityInfo apr_winapi_GetSecurityInfo

APR_DECLARE_LATE_DLL_FUNC(DLL_SHSTDAPI, LPWSTR *, WINAPI, CommandLineToArgvW, 0, (
    LPCWSTR lpCmdLine,
    int *pNumArgs),
    (lpCmdLine, pNumArgs));
#define CommandLineToArgvW apr_winapi_CommandLineToArgvW

#endif /* !defined(_WIN32_WCE) && !defined(WINNT) */

#if !defined(_WIN32_WCE)
/* This group is NOT available to all versions of WinNT,
 * these we must always look up
 */

#ifdef GetCompressedFileSizeA
#undef GetCompressedFileSizeA
#endif
APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, DWORD, WINAPI, GetCompressedFileSizeA, 0, (
    IN LPCSTR lpFileName,
    OUT LPDWORD lpFileSizeHigh),
    (lpFileName, lpFileSizeHigh));
#define GetCompressedFileSizeA apr_winapi_GetCompressedFileSizeA
#undef GetCompressedFileSize
#define GetCompressedFileSize apr_winapi_GetCompressedFileSizeA

#ifdef GetCompressedFileSizeW
#undef GetCompressedFileSizeW
#endif
APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, DWORD, WINAPI, GetCompressedFileSizeW, 0, (
    IN LPCWSTR lpFileName,
    OUT LPDWORD lpFileSizeHigh),
    (lpFileName, lpFileSizeHigh));
#define GetCompressedFileSizeW apr_winapi_GetCompressedFileSizeW


APR_DECLARE_LATE_DLL_FUNC(DLL_NTDLL, LONG, WINAPI, NtQueryTimerResolution, 0, (
    ULONG *pMaxRes,  /* Minimum NS Resolution */
    ULONG *pMinRes,  /* Maximum NS Resolution */
    ULONG *pCurRes), /* Current NS Resolution */
    (pMaxRes, pMinRes, pCurRes));
#define QueryTimerResolution apr_winapi_NtQueryTimerResolution

APR_DECLARE_LATE_DLL_FUNC(DLL_NTDLL, LONG, WINAPI, NtSetTimerResolution, 0, (
    ULONG ReqRes,    /* Requested NS Clock Resolution */
    BOOL  Acquire,   /* Aquire (1) or Release (0) our interest */
    ULONG *pNewRes), /* The NS Clock Resolution granted */
    (ReqRes, Acquire, pNewRes));
#define SetTimerResolution apr_winapi_NtSetTimerResolution

typedef struct PBI {
    LONG      ExitStatus;
    PVOID     PebBaseAddress;
    apr_uintptr_t AffinityMask;
    LONG      BasePriority;
    apr_uintptr_t UniqueProcessId;
    apr_uintptr_t InheritedFromUniqueProcessId;
} PBI, *PPBI;

APR_DECLARE_LATE_DLL_FUNC(DLL_NTDLL, LONG, WINAPI, NtQueryInformationProcess, 0, (
    HANDLE hProcess,  /* Obvious */
    INT   info,       /* Use 0 for PBI documented above */
    PVOID pPI,        /* The PIB buffer */
    ULONG LenPI,      /* Use sizeof(PBI) */
    ULONG *pSizePI),  /* returns pPI buffer used (may pass NULL) */
    (hProcess, info, pPI, LenPI, pSizePI));
#define QueryInformationProcess apr_winapi_NtQueryInformationProcess

APR_DECLARE_LATE_DLL_FUNC(DLL_NTDLL, LONG, WINAPI, NtQueryObject, 0, (
    HANDLE hObject,   /* Obvious */
    INT   info,       /* Use 0 for PBI documented above */
    PVOID pOI,        /* The PIB buffer */
    ULONG LenOI,      /* Use sizeof(PBI) */
    ULONG *pSizeOI),  /* returns pPI buffer used (may pass NULL) */
    (hObject, info, pOI, LenOI, pSizeOI));
#define QueryObject apr_winapi_NtQueryObject

typedef struct IOSB {
    union {
    UINT Status;
    PVOID reserved;
    };
    apr_uintptr_t Information; /* Varies by op, consumed buffer size for FSI below */
} IOSB, *PIOSB;

typedef struct FSI {
    LONGLONG AllocationSize;
    LONGLONG EndOfFile;
    ULONG    NumberOfLinks;
    BOOL     DeletePending;
    BOOL     Directory;
} FSI, *PFSI;

APR_DECLARE_LATE_DLL_FUNC(DLL_NTDLL, LONG, WINAPI, ZwQueryInformationFile, 0, (
    HANDLE hObject,    /* Obvious */
    PVOID  pIOSB,      /* Point to the IOSB buffer for detailed return results */
    PVOID  pFI,        /* The buffer, using FIB above */
    ULONG  LenFI,      /* Use sizeof(FI) */
    ULONG  info),      /* Use 5 for FSI documented above*/
    (hObject, pIOSB, pFI, LenFI, info));
#define ZwQueryInformationFile apr_winapi_ZwQueryInformationFile

#ifdef CreateToolhelp32Snapshot
#undef CreateToolhelp32Snapshot
#endif
APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, HANDLE, WINAPI, CreateToolhelp32Snapshot, 0, (
    DWORD dwFlags,
    DWORD th32ProcessID),
    (dwFlags, th32ProcessID));
#define CreateToolhelp32Snapshot apr_winapi_CreateToolhelp32Snapshot

#ifdef Process32FirstW
#undef Process32FirstW
#endif
APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, BOOL, WINAPI, Process32FirstW, 0, (
    HANDLE hSnapshot,
    LPPROCESSENTRY32W lppe),
    (hSnapshot, lppe));
#define Process32FirstW apr_winapi_Process32FirstW

#ifdef Process32NextW
#undef Process32NextW
#endif
APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, BOOL, WINAPI, Process32NextW, 0, (
    HANDLE hSnapshot,
    LPPROCESSENTRY32W lppe),
    (hSnapshot, lppe));
#define Process32NextW apr_winapi_Process32NextW

#if !defined(POLLERR)
/* Event flag definitions for WSAPoll(). */
#define POLLRDNORM  0x0100
#define POLLRDBAND  0x0200
#define POLLIN      (POLLRDNORM | POLLRDBAND)
#define POLLPRI     0x0400

#define POLLWRNORM  0x0010
#define POLLOUT     (POLLWRNORM)
#define POLLWRBAND  0x0020

#define POLLERR     0x0001
#define POLLHUP     0x0002
#define POLLNVAL    0x0004

typedef struct pollfd {
    SOCKET  fd;
    SHORT   events;
    SHORT   revents;

} WSAPOLLFD, *PWSAPOLLFD, FAR *LPWSAPOLLFD;

#endif /* !defined(POLLERR) */
#ifdef WSAPoll
#undef WSAPoll
#endif
APR_DECLARE_LATE_DLL_FUNC(DLL_WINSOCK2API, int, WSAAPI, WSAPoll, 0, (
    IN OUT LPWSAPOLLFD fdArray,
    IN ULONG fds,
    IN INT timeout),
    (fdArray, fds, timeout));
#define WSAPoll apr_winapi_WSAPoll
#define HAVE_POLL   1

#ifdef SetDllDirectoryW
#undef SetDllDirectoryW
#endif
APR_DECLARE_LATE_DLL_FUNC(DLL_WINBASEAPI, BOOL, WINAPI, SetDllDirectoryW, 0, (
    IN LPCWSTR lpPathName),
    (lpPathName));
#define SetDllDirectoryW apr_winapi_SetDllDirectoryW

#endif /* !defined(_WIN32_WCE) */

#endif  /* ! MISC_H */

