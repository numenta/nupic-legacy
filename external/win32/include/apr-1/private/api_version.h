/* Copyright 2000-2004 The Apache Software Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef API_VERSION_H
#define API_VERSION_H

/**
 * @file api_version.h
 * @brief APR-iconv Versioning Interface
 * 
 * APR-iconv's Version
 *
 * There are several different mechanisms for accessing the version. There
 * is a string form, and a set of numbers; in addition, there are constants
 * which can be compiled into your application, and you can query the library
 * being used for its actual version.
 *
 * Note that it is possible for an application to detect that it has been
 * compiled against a different version of API by use of the compile-time
 * constants and the use of the run-time query function.
 *
 * API version numbering follows the guidelines specified in:
 *
 *     http://apr.apache.org/versioning.html
 */


/* The numeric compile-time version constants. These constants are the
 * authoritative version numbers for API. 
 */

/** major version 
 * Major API changes that could cause compatibility problems for older
 * programs such as structure size changes.  No binary compatibility is
 * possible across a change in the major version.
 */
#define API_MAJOR_VERSION       1

/** minor version
 * Minor API changes that do not cause binary compatibility problems.
 * Reset to 0 when upgrading API_MAJOR_VERSION
 */
#define API_MINOR_VERSION       2

/** patch level 
 * The Patch Level never includes API changes, simply bug fixes.
 * Reset to 0 when upgrading API_MINOR_VERSION
 */
#define API_PATCH_VERSION       1

/** 
 * The symbol API_IS_DEV_VERSION is only defined for internal,
 * "development" copies of API.  It is undefined for released versions
 * of API.
 */
/* #undef API_IS_DEV_VERSION */


#if defined(API_IS_DEV_VERSION) || defined(DOXYGEN)
/** Internal: string form of the "is dev" flag */
#define API_IS_DEV_STRING "-dev"
#else
#define API_IS_DEV_STRING ""
#endif

#ifndef API_STRINGIFY
/** Properly quote a value as a string in the C preprocessor */
#define API_STRINGIFY(n) API_STRINGIFY_HELPER(n)
/** Helper macro for API_STRINGIFY */
#define API_STRINGIFY_HELPER(n) #n
#endif

/** The formatted string of API's version */
#define API_VERSION_STRING \
     API_STRINGIFY(API_MAJOR_VERSION) "." \
     API_STRINGIFY(API_MINOR_VERSION) "." \
     API_STRINGIFY(API_PATCH_VERSION) \
     API_IS_DEV_STRING

/** An alternative formatted string of APR's version */
/* macro for Win32 .rc files using numeric csv representation */
#define API_VERSION_STRING_CSV API_MAJOR_VERSION ##, \
                             ##API_MINOR_VERSION ##, \
                             ##API_PATCH_VERSION


#ifndef API_VERSION_ONLY

/* The C language API to access the version at run time, 
 * as opposed to compile time.  API_VERSION_ONLY may be defined 
 * externally when preprocessing apr_version.h to obtain strictly 
 * the C Preprocessor macro declarations.
 */

#include "apr_version.h"

#include "apr_iconv.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Return APR-iconv's version information information in a numeric form.
 *
 *  @param pvsn Pointer to a version structure for returning the version
 *              information.
 */
API_DECLARE(void) api_version(apr_version_t *pvsn);

/** Return API's version information as a string. */
API_DECLARE(const char *) api_version_string(void);

#ifdef __cplusplus
}
#endif

#endif /* ndef API_VERSION_ONLY */

#endif /* ndef API_VERSION_H */
