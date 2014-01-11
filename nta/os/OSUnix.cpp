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
 * Unix Implementations for the OS class
 */

#ifndef WIN32

#include <nta/os/OS.hpp>
#include <nta/os/Path.hpp>
#include <nta/os/Directory.hpp>
#include <nta/os/Env.hpp>
#include <nta/utils/Log.hpp>
#include <fstream>
#include <cstdlib>
#include <unistd.h>   // getuid()
#include <sys/types.h>
#include <apr-1/apr_errno.h>
#include <apr-1/apr_time.h>
#include <apr-1/apr_network_io.h>


using namespace nta;

std::string OS::getErrorMessage()
{
  char buff[1024];
  apr_status_t st = apr_get_os_error();
  ::apr_strerror(st , buff, 1024);
  return std::string(buff);
}



std::string OS::getHomeDir()
{
  std::string home;
  bool found = Env::get("HOME", home);
  if (!found)
    NTA_THROW << "'HOME' environment variable is not defined";
  return home;
}

std::string OS::getUserName()
{
  std::string username;
  bool found = Env::get("USER", username);

  // USER isn't always set inside a cron job
  if (!found)
    found = Env::get("LOGNAME", username);

  if (!found) 
  {
    NTA_WARN << "OS::getUserName -- USER and LOGNAME environment variables are not set. Using userid = " << getuid();
    std::stringstream ss("");
    ss << getuid();
    username = ss.str(); 
  } 

  return username;
}


 


int OS::getLastErrorCode() { return errno; }

std::string OS::getErrorMessageFromErrorCode(int errorCode)
{
  std::stringstream errorMessage;
  char errorBuffer[1024];
  errorBuffer[0] = '\0';
#ifdef __APPLE__
  int result = ::strerror_r(errorCode, errorBuffer, 1024);
  if(result == 0) errorMessage << errorBuffer;
#else
  char *result = ::strerror_r(errorCode, errorBuffer, 1024);
  if(result != 0) errorMessage << errorBuffer;
#endif
  else errorMessage << "Error code " << errorCode;
  return errorMessage.str();
}

#endif // #ifndef WIN32


