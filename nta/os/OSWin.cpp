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
 * Win32 Implementations for the OS class
 */

#ifdef WIN32
#include <windows.h>
#include <shlobj.h>

#include <nta/os/OS.hpp>
#include <nta/os/Directory.hpp>
#include <nta/os/Path.hpp>
#include <nta/os/Directory.hpp>
#include <nta/os/Env.hpp>
#include <nta/utils/Log.hpp>
#include <nta/os/DynamicLibrary.hpp>
#include <boost/shared_ptr.hpp>


using namespace nta;

std::string OS::getHomeDir()
{
  std::string homeDrive;
  std::string homePath;
  bool found = Env::get("HOMEDRIVE", homeDrive);
  NTA_CHECK(found) << "'HOMEDRIVE' environment variable is not defined";
  found = Env::get("HOMEPATH", homePath);
  NTA_CHECK(found) << "'HOMEPATH' environment variable is not defined";
  return homeDrive + homePath;
}

std::string OS::getUserName()
{
  std::string username;
  bool found = Env::get("USERNAME", username);
  NTA_CHECK(found) << "Environment variable USERNAME is not defined";

  return username;
}

int OS::getLastErrorCode()
{
  return ::GetLastError();
}

std::string OS::getErrorMessageFromErrorCode(int errorCode)
{ 
  // Retrieve the system error message for the last-error code
  LPVOID lpMsgBuf;

  DWORD msgLen = ::FormatMessageA(
      FORMAT_MESSAGE_ALLOCATE_BUFFER | 
      FORMAT_MESSAGE_FROM_SYSTEM |
      FORMAT_MESSAGE_IGNORE_INSERTS,
      NULL,
      errorCode,
      MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT),
      (LPSTR) &lpMsgBuf,
      0, NULL
    );

  std::ostringstream errMessage;
  if(msgLen > 0) {
    errMessage.write((LPSTR) lpMsgBuf, msgLen);
  }
  else {
    errMessage << "Error code: " << errorCode;
  }

  LocalFree(lpMsgBuf);

  return errMessage.str();
}

std::string OS::getErrorMessage()
{
  return getErrorMessageFromErrorCode (getLastErrorCode());
}


#endif //#ifdef WIN32

