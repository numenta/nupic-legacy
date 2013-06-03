/*
 * Copyright (c) 1992, 1993
 *	The Regents of the University of California.  All rights reserved.
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
 *	This product includes software developed by the University of
 *	California, Berkeley and its contributors.
 * 4. Neither the name of the University nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 *	@(#)fnmatch.h	8.1 (Berkeley) 6/2/93
 */

/* This file has been modified by the Apache Software Foundation. */
#ifndef	_APR_FNMATCH_H_
#define	_APR_FNMATCH_H_

/**
 * @file apr_fnmatch.h
 * @brief APR FNMatch Functions
 */

#include "apr_errno.h"
#include "apr_tables.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @defgroup apr_fnmatch Filename Matching Functions
 * @ingroup APR 
 * @{
 */

#define APR_FNM_NOMATCH     1     /**< Match failed. */
 
#define APR_FNM_NOESCAPE    0x01  /**< Disable backslash escaping. */
#define APR_FNM_PATHNAME    0x02  /**< Slash must be matched by slash. */
#define APR_FNM_PERIOD      0x04  /**< Period must be matched by period. */
#define APR_FNM_CASE_BLIND  0x08  /**< Compare characters case-insensitively.
                                   * @remark This flag is an Apache addition 
                                   */

/**
 * Try to match the string to the given pattern, return APR_SUCCESS if
 *    match, else return APR_FNM_NOMATCH.
 * @param pattern The pattern to match to
 * @param strings The string we are trying to match
 * @param flags flags to use in the match.  Bitwise OR of:
 * <PRE>
 *              APR_FNM_NOESCAPE       Disable backslash escaping
 *              APR_FNM_PATHNAME       Slash must be matched by slash
 *              APR_FNM_PERIOD         Period must be matched by period
 *              APR_FNM_CASE_BLIND     Compare characters case-insensitively.
 * </PRE>
 */

APR_DECLARE(apr_status_t) apr_fnmatch(const char *pattern, 
                                      const char *strings, int flags);

/**
 * Determine if the given pattern is a regular expression.
 * @param pattern The pattern to search for glob characters.
 * @return non-zero if pattern has any glob characters in it
 */
APR_DECLARE(int) apr_fnmatch_test(const char *pattern);

/**
 * Find all files that match a specified pattern.
 * @param pattern The pattern to use for finding files.
 * @param result Array to use when storing the results
 * @param p The pool to use.
 * @return non-zero if pattern has any glob characters in it
 */
APR_DECLARE(apr_status_t) apr_match_glob(const char *pattern, 
                                         apr_array_header_t **result,
                                         apr_pool_t *p);

/** @} */

#ifdef __cplusplus
}
#endif

#endif /* !_APR_FNMATCH_H_ */
