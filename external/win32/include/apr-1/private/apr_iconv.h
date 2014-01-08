/*-
 * Copyright (c) 1999,2000
 *	Konstantin Chuguev.  All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. All advertising materials mentioning features or use of this software
 *    must display the following acknowledgement:
 *	This product includes software developed by Konstantin Chuguev
 *	and its contributors.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 */

#ifndef APR_ICONV_H
#define APR_ICONV_H

/**
 * @file apr_iconv.h
 * @brief APR-iconv substitute iconv library implementation 
 */

#include "apr.h"
#include "apr_pools.h"
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif /* __cplusplus */

/**
 * @defgroup apr_iconv substitute iconv implementation
 * @ingroup APR-iconv
 * @{
 */

/**
 * API_DECLARE_EXPORT is defined when building the libapriconv dynamic 
 * library, so that all public symbols are exported.
 *
 * API_DECLARE_STATIC is defined when including the apriconv public headers, 
 * to provide static linkage when the dynamic library may be unavailable.
 *
 * API_DECLARE_STATIC and API_DECLARE_EXPORT are left undefined when
 * including the apr-iconv public headers, to import and link the symbols 
 * from the dynamic libapriconv library and assure appropriate indirection 
 * and calling conventions at compile time.
 */

#if defined(DOXYGEN) || !defined(WIN32)
/**
 * The public apr-iconv functions are declared with API_DECLARE(), so they 
 * use the most portable calling convention.  Public apr-iconv functions 
 * with variable arguments must use API_DECLARE_NONSTD().
 *
 * @deffunc API_DECLARE(rettype) apr_func(args);
 */
#define API_DECLARE(type)            type
/**
 * The private apr-iconv functions are declared with API_DECLARE_NONSTD(), 
 * so they use the most optimal C language calling conventions.
 *
 * @deffunc API_DECLARE(rettype) apr_func(args);
 */
#define API_DECLARE_NONSTD(type)     type
/**
 * All exported apr-iconv variables are declared with API_DECLARE_DATA
 * This assures the appropriate indirection is invoked at compile time.
 *
 * @deffunc API_DECLARE_DATA type apr_variable;
 * @tip extern API_DECLARE_DATA type apr_variable; syntax is required for
 * declarations within headers to properly import the variable.
 */
#define API_DECLARE_DATA
#elif defined(API_DECLARE_STATIC)
#define API_DECLARE(type)            type __stdcall
#define API_DECLARE_NONSTD(type)     type __cdecl
#define API_DECLARE_DATA
#elif defined(API_DECLARE_EXPORT)
#define API_DECLARE(type)            __declspec(dllexport) type __stdcall
#define API_DECLARE_NONSTD(type)     __declspec(dllexport) type __cdecl
#define API_DECLARE_DATA             __declspec(dllexport)
#else
#define API_DECLARE(type)            __declspec(dllimport) type __stdcall
#define API_DECLARE_NONSTD(type)     __declspec(dllimport) type __cdecl
#define API_DECLARE_DATA             __declspec(dllimport)
#endif

/*
 * apr_iconv_t:	charset conversion descriptor type
 */
typedef void *apr_iconv_t;

/* __BEGIN_DECLS */

/**
 * Create a conversion descriptor.
 * @param to name of charset to convert to.
 * @param from name of charset of the input bytes.
 * @param pool pool to alloc memory.
 * @param cd conversion descriptor created in pool.
 */
API_DECLARE(apr_status_t) apr_iconv_open(const char *to, const char *from,
                                         apr_pool_t *pool, apr_iconv_t *cd);
/**
 * Perform character set conversion.
 * @param cd conversion descriptor created by apr_iconv_open().
 * @param inbuf input buffer.
 * @param inbytesleft bytes to convert.
 * @param outbuf output buffer.
 * @param outbytesleft space (in bytes) available in outbuf.
 * @param translated number of input bytes converted.
 */
API_DECLARE(apr_status_t) apr_iconv(apr_iconv_t cd,
                          const char **inbuf, apr_size_t *inbytesleft,
                          char **outbuf, apr_size_t *outbytesleft,
                          apr_size_t *translated);
/**
 * Deallocate descriptor for character set conversion.
 * @param cd conversion descriptor.
 * @param pool pool used in the apr_iconv_open().
 */
API_DECLARE(apr_status_t) apr_iconv_close(apr_iconv_t cd, apr_pool_t *pool);

/* __END_DECLS */

/** @} */

#ifdef __cplusplus
}
#endif

#endif /* APR_ICONV_H */
