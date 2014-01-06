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

/* @file NuPIC init/shutdown operations */

#include <set>

/** @namespace nta
 * Contains the primary NuPIC API.
 */
namespace nta
{
  class Network;

  /**
   * Contains initialization and shutdown operations
   */
  class NuPIC 
  {
  public:
    /** TODO: document */
    static void init();
    /** TODO: document */
    static void shutdown();
    /** TODO: document */
    static bool isInitialized();
  private:
    /**
     * As a safety measure, don't allow NuPIC to be shut down 
     * if there are any networks still around. Networks 
     * register/unregister themselves at creation and 
     * destruction time.
     * 
     * TBD: license checking will be done in NuPIC::init()
     */
    friend class Network;
    static void registerNetwork(Network* net);
    static void unregisterNetwork(Network* net);
    static std::set<Network*> networks_;
    static bool initialized_;
  };
} // namespace nta

