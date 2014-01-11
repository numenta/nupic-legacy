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
 * Basic C type definitions used throughout the app. It is included by 
 * types.hpp - the C++ basic types file
 */

#ifndef NTA_TYPES_H
#define NTA_TYPES_H

#include <stddef.h>

/*---------------------------------------------------------------------- */
 
/** Basic types enumeration */
typedef enum NTA_BasicType
  {
    /** TODO: document */
    NTA_BasicType_Byte,
    /** TODO: document */
    NTA_BasicType_Int16,
    /** TODO: document */
    NTA_BasicType_UInt16,
    /** TODO: document */
    NTA_BasicType_Int32,
    /** TODO: document */
    NTA_BasicType_UInt32,
    /** TODO: document */
    NTA_BasicType_Int64,
    /** TODO: document */
    NTA_BasicType_UInt64,
    /** TODO: document */
    NTA_BasicType_Real32,
    /** TODO: document */
    NTA_BasicType_Real64,
    /** Opaque handles or pointers (same as void *) */
    NTA_BasicType_Handle,
    
    /** this is not an actual type just a marker for validation purposes */
    NTA_BasicType_Last,

#ifdef NTA_DOUBLE_PRECISION 
    /** TODO: document */
    NTA_BasicType_Real = NTA_BasicType_Real64,
#else 
    /** TODO: document */
    NTA_BasicType_Real = NTA_BasicType_Real32,
#endif

  } NTA_BasicType;

/* Basic types */

/** TODO: document */
typedef char           NTA_Byte;

/** TODO: document */
typedef size_t         NTA_Size;

/** TODO: document */
typedef short           NTA_Int16;
/** TODO: document */
typedef unsigned short  NTA_UInt16;
  
/** TODO: document */
typedef float          NTA_Real32;
/** TODO: document */
typedef double         NTA_Real64;
/** TODO: document */
typedef void *         NTA_Handle;

#if defined(NTA_PLATFORM_darwin86)
/** TODO: document */
typedef  int                  NTA_Int32;
/** TODO: document */
typedef  unsigned int         NTA_UInt32;
/** TODO: document */
typedef  long long            NTA_Int64;
/** TODO: document */
typedef  unsigned long long   NTA_UInt64;

#elif defined(NTA_PLATFORM_darwin64)
/** TODO: document */
typedef  int                  NTA_Int32;
/** TODO: document */
typedef  unsigned int         NTA_UInt32;
/** TODO: document */
typedef  long                 NTA_Int64;
/** TODO: document */
typedef  unsigned long        NTA_UInt64;

#elif defined(NTA_PLATFORM_linux32)
/** TODO: document */
typedef  int                  NTA_Int32;
/** TODO: document */
typedef  unsigned int         NTA_UInt32;
/** TODO: document */
typedef  long long            NTA_Int64;
/** TODO: document */
typedef  unsigned long long   NTA_UInt64;

#elif defined(NTA_PLATFORM_linux32arm) || defined(NTA_PLATFORM_linux32armv7)
/** TODO: document */
typedef  int                  NTA_Int32;
/** TODO: document */
typedef  unsigned int         NTA_UInt32;
/** TODO: document */
typedef  long long            NTA_Int64;
/** TODO: document */
typedef  unsigned long long   NTA_UInt64;

#elif defined(NTA_PLATFORM_win32)
/** TODO: document */
typedef  long                NTA_Int32;
/** TODO: document */
typedef  unsigned long       NTA_UInt32;
/** TODO: document */
typedef  long long           NTA_Int64;
/** TODO: document */
typedef  unsigned long long  NTA_UInt64;

#elif defined(NTA_PLATFORM_linux64)
/** TODO: document */
typedef  int                 NTA_Int32;
/** TODO: document */
typedef  unsigned int        NTA_UInt32;
/** TODO: document */
typedef  long                NTA_Int64;
/** TODO: document */
typedef  unsigned long       NTA_UInt64;
#else
#error "Unknown platform"
#endif

#ifdef NTA_DOUBLE_PRECISION 
  /** TODO: document */
  typedef NTA_Real64 NTA_Real;
  #define NTA_REAL_TYPE_STRING "NTA_Real64"
#else
  /** TODO: document */
  typedef NTA_Real32 NTA_Real;
  #define NTA_REAL_TYPE_STRING "NTA_Real32"
#endif
  
#ifdef NTA_BIG_INTEGER
  /** TODO: document */
  typedef  NTA_Int64  NTA_Int;
  /** TODO: document */
  typedef  NTA_UInt64 NTA_UInt;
#else
  /** TODO: document */
  typedef  NTA_Int32  NTA_Int;
  /** TODO: document */
  typedef  NTA_UInt32 NTA_UInt;
#endif

#ifndef SWIG
#ifdef WIN32
#define NTA_EXPORT __declspec(dllexport)
#define NTA_HIDDEN
#else
#define NTA_EXPORT __attribute__ ((visibility ("default")))
#define NTA_HIDDEN __attribute__ ((visibility ("hidden")))
#endif


#else
#define NTA_HIDDEN
#define NTA_EXPORT
#endif

/** This enum represents the documented logging level
 * of the debug logger. Use LDEBUG(NTA_LogLevelXXX)
 */
typedef enum NTA_LogLevel
  {
    /** TODO: document */
    NTA_LogLevel_None,
    /** TODO: document */
    NTA_LogLevel_Minimal,
    /** TODO: document */
    NTA_LogLevel_Normal,
    /** TODO: document */
    NTA_LogLevel_Verbose,
    /** TODO: document */
  } NTA_LogLevel;

#endif /* NTA_TYPES_H */
