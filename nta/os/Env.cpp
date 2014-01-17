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
Environment Implementation
*/

#include <nta/os/Env.hpp>
#include <nta/utils/Log.hpp>
#include <apr-1/apr_general.h>
#include <apr-1/apr_env.h>
#include <cctype> // toupper
#include <algorithm> // std::transform

using namespace nta;

bool Env::get(const std::string& name, std::string& value)
{
  // @todo remove apr initialization when we have global initialization
  apr_status_t status = apr_initialize();
  if (status != APR_SUCCESS) {
    NTA_THROW << "Env::get -- Unable to initialize APR" << " name = " << name;
    return false;
  }
  
  // This is annoying. apr_env_get doesn't actually use the memory
  // pool it is given. But we have to set it up because the API
  // requires it and might use it in the future. 
  apr_pool_t *poolP;
  status = apr_pool_create(&poolP, nullptr);
  if (status != APR_SUCCESS) {
    NTA_THROW << "Env::get -- Unable to create a pool" << " name = " << name;
    return false;
  }
  
  char *cvalue;
  bool returnvalue = false;
  status = apr_env_get(&cvalue, name.c_str(), poolP);
  if (status != APR_SUCCESS) {
    returnvalue = false;
  } else {
    returnvalue = true;
    value = cvalue;
  }
  apr_pool_destroy(poolP);
  return returnvalue;
  
}

void Env::set(const std::string& name, const std::string& value)
{
  // @todo remove apr initialization when we have global initialization
  apr_status_t status = apr_initialize();
  if (status != APR_SUCCESS) {
    NTA_THROW << "Env::set -- Unable to initialize APR" << " name = " << name <<
                                                      " value = " << value;
    // ok to return. Haven't created a pool yet
    return;
  }
  
  apr_pool_t *poolP;
  status = apr_pool_create(&poolP, nullptr);
  if (status != APR_SUCCESS) {
    NTA_THROW << "Env::set -- Unable to create a pool." << " name = " << name <<
                                                      " value = " << value;
    // ok to return. Haven't created a pool yet. 
    return;
  }
  
  status = apr_env_set(name.c_str(), value.c_str(), poolP);
  if (status != APR_SUCCESS) {
    NTA_THROW << "Env::set -- Unable to set variable " << name << " to " << value;
  } 
    
  apr_pool_destroy(poolP);
  return;
  
}

void Env::unset(const std::string& name)
{
  // @todo remove apr initialization when we have global initialization
  apr_status_t status = apr_initialize();
  if (status != APR_SUCCESS) {
    NTA_THROW << "Env::unset -- Unable to initialize APR." << " name = " << name;
    return;
  }
  
  apr_pool_t *poolP;
  status = apr_pool_create(&poolP, nullptr);
  if (status != APR_SUCCESS) {
    NTA_THROW << "Env::unset -- Unable to create a pool." << " name = " << name;
    return;
  }
  
  status = apr_env_delete(name.c_str(), poolP);
  if (status != APR_SUCCESS) {
    // not a fatal error because may not exist
    NTA_WARN << "Env::unset -- Unable to delete " << name;
  }
  apr_pool_destroy(poolP);
  return;
  
}

char ** Env::environ_ = nullptr;

#if defined(NTA_PLATFORM_darwin64) || defined(NTA_PLATFORM_darwin86)
#include <crt_externs.h>
#else
extern char **environ;
#endif


char **Env::getenv()
{
  if (environ_ != nullptr)
    return environ_;

#if defined(NTA_PLATFORM_darwin64) || defined(NTA_PLATFORM_darwin86)
  environ_ = *_NSGetEnviron();
#else 
  environ_ = environ;
#endif

  return environ_;
}


static std::string _getOptionEnvironmentVariable(const std::string& optionName)
{
  std::string result="NTA_";
  result += optionName;
  std::transform(result.begin(), result.end(), result.begin(), toupper);
  return result;
}


bool Env::isOptionSet(const std::string& optionName)
{
  std::string envName = _getOptionEnvironmentVariable(optionName);
  std::string value;
  bool found = get(envName, value);
  return found;
}

std::string Env::getOption(const std::string& optionName, std::string defaultValue)
{
  std::string envName = _getOptionEnvironmentVariable(optionName);
  std::string value;
  bool found = get(envName, value);
  if (!found)
    return defaultValue;
  else
    return value;
}

