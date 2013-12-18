/*
 * ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
 * Numenta, Inc. a separate commercial license for this software code, the
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
 * Basic C++ type definitions used throughout the app and rely on types.h
 */

#ifndef NTA_TYPES_HPP
#define NTA_TYPES_HPP

#include <nta/types/types.h>

//----------------------------------------------------------------------

namespace nta 
{
  // Basic types
  /** TODO: document */
  typedef NTA_Byte            Byte;
  /** TODO: document */
  typedef NTA_Int16           Int16;
  /** TODO: document */
  typedef NTA_UInt16          UInt16;
  /** TODO: document */
  typedef NTA_Int32           Int32;
  /** TODO: document */
  typedef NTA_UInt32          UInt32;
  /** TODO: document */
  typedef NTA_Int64           Int64;
  /** TODO: document */
  typedef NTA_UInt64          UInt64;
  /** TODO: document */
  typedef NTA_Real32          Real32;
  /** TODO: document */
  typedef NTA_Real64          Real64;
  /** TODO: document */
  typedef NTA_Handle          Handle;

  // Flexible types (depending on NTA_DOUBLE_PROCESION and NTA_BIG_INTEGER)
  /** TODO: document */
  typedef NTA_Real Real;
  /** TODO: document */
  typedef NTA_Int  Int;
  /** TODO: document */
  typedef NTA_UInt UInt;

  /** TODO: document */
  typedef NTA_Size            Size;

  /** TODO: document */
  enum LogLevel
  {
    LogLevel_None = NTA_LogLevel_None,
    LogLevel_Minimal,
    LogLevel_Normal,
    LogLevel_Verbose,
  };

} // end namespace nta

#ifdef SWIG
#undef NTA_INTERNAL
#endif // SWIG

#endif // NTA_TYPES_HPP



