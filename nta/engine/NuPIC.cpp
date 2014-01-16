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

/* @file Implementation of NuPIC init/shutdown operations */

// TODO -- thread safety
// TODO -- add license check

#include <nta/engine/NuPIC.hpp>
#include <nta/engine/RegionImplFactory.hpp>
#include <nta/utils/Log.hpp>
#include <apr-1/apr_general.h>

namespace nta
{

std::set<Network*> NuPIC::networks_;
bool NuPIC::initialized_ = false;

void NuPIC::init()
{
  if (isInitialized())
    return;
  
  // internal consistency check. Nonzero should be impossible. 
  NTA_CHECK(networks_.size() == 0) << "Internal error in NuPIC::init()";
  
  // Initialize APR
  int argc=1;
  const char *argv[1] = {"NuPIC"};
  // TODO: move to OS::initialize()?
  int result = apr_app_initialize(&argc, (const char* const **)&argv, 0 /*env*/);
  if (result) 
    NTA_THROW << "Error initializing APR (code " << result << ")";

  initialized_ = true;
}


void NuPIC::shutdown()
{
  if (!isInitialized())
  {
    NTA_THROW << "NuPIC::shutdown -- NuPIC has not been initialized";
  }

  if (!networks_.empty())
  {
    NTA_THROW << "NuPIC::shutdown -- cannot shut down NuPIC because " 
              << networks_.size() << " networks still exist.";
  }

  RegionImplFactory::getInstance().cleanup();
  initialized_ = false;
}


void NuPIC::registerNetwork(Network* net)
{
  if (!isInitialized())
  {
    NTA_THROW << "Attempt to create a network before NuPIC has been initialized -- call NuPIC::init() before creating any networks";
  }

  std::set<Network*>::iterator n = networks_.find(net);
  // This should not be possible
  NTA_CHECK(n == networks_.end()) << "Internal error -- double registration of network";
  networks_.insert(net);

}

void NuPIC::unregisterNetwork(Network* net)
{
  std::set<Network*>::iterator n = networks_.find(net);
  NTA_CHECK(n != networks_.end()) << "Internal error -- network not registered";
  networks_.erase(n);
}

bool NuPIC::isInitialized()
{
  return initialized_;
}

}

