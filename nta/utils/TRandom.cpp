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
    Random Number Generator implementation
*/

#include <nta/utils/TRandom.hpp>
#include <nta/utils/Log.hpp>
#include <nta/utils/StringUtils.hpp>
#include <nta/os/Env.hpp>
#include <cstdlib>
#include <ctime>

using namespace nta;

TRandom::TRandom(std::string name)
{

  UInt64 seed = 0;

  std::string optionName = "set_random";
  if (name != "")
  {
    optionName += "_" + name;
  }

  bool seed_from_environment = false;
  if (Env::isOptionSet(optionName))
  {
    seed_from_environment = true;
    std::string val = Env::getOption(optionName);
    try 
    {
      seed = StringUtils::toUInt64(val, true);
    }
    catch (...)       
    {  
      NTA_WARN << "Invalid value \"" << val << "\" for NTA_SET_RANDOM. Using 1";
      seed = 1;
    }
  }
  else
  {
    // Seed the global rng from time(). 
    // Don't seed subsequent ones from time() because several random 
    // number generators may be initialized within the same second. 
    // Instead, use the global rng.  
    if (theInstanceP_ == nullptr) {
      seed = (UInt64)time(nullptr);
    } else {
      seed = (*Random::getSeeder())();
    }

  } 

  if (Env::isOptionSet("random_debug"))
  {
    if (seed_from_environment) {
        NTA_INFO << "TRandom(" << name << ") -- initializing with seed " << seed << " from environment";
    } else {
        NTA_INFO << "TRandom(" << name << ") -- initializing with seed " << seed;
    }
  }

  // Create the actual RNG
  // @todo to add different algorithm support, this is where we will
  // instantiate different implementations depending on the requested
  // algorithm 
  reseed(seed);
}
