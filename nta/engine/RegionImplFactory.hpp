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
 * Definition of the RegionImpl Factory API
 *
 * A RegionImplFactory creates RegionImpls upon request. 
 * Pynode creation is delegated to another class (TBD). 
 * Because all C++ RegionImpls are compiled in to NuPIC, 
 * the RegionImpl factory knows about them explicitly. 
 * 
 */

#ifndef NTA_REGION_IMPL_FACTORY_HPP
#define NTA_REGION_IMPL_FACTORY_HPP

#include <string>
#include <map>
#include <boost/shared_ptr.hpp>

namespace nta
{

  class RegionImpl;
  class Region;
  class DynamicPythonLibrary;
  struct Spec;
  class BundleIO;

  class RegionImplFactory
  {
  public:
    static RegionImplFactory & getInstance();

    // RegionImplFactory is a lightweight object
    ~RegionImplFactory() {};

    // Create a RegionImpl of a specific type; caller gets ownership.
    RegionImpl* createRegionImpl(const std::string nodeType, 
                                 const std::string nodeParams,
                                 Region* region);

    // Create a RegionImpl from serialized state; caller gets ownership. 
    RegionImpl* deserializeRegionImpl(const std::string nodeType,
                                      BundleIO& bundle,
                                      Region* region);



    // Returns nodespec for a specific node type; Factory retains ownership. 
    Spec* getSpec(const std::string nodeType);

    // RegionImplFactory caches nodespecs and the dynamic library reference
    // This frees up the cached information.
    // Should be called only if there are no outstanding
    // nodespec references (e.g. in NuPIC shutdown) or pynodes. 
    void cleanup();

  private:
    RegionImplFactory() {};
    RegionImplFactory(const RegionImplFactory &);

  private:

    // TODO: implement locking for thread safety for this global data structure
    // TODO: implement cleanup

    // getSpec returns references to nodespecs in this cache. 
    // should not be cleaned up until those references have disappeared. 
    std::map<std::string, Spec*> nodespecCache_;

    // Using shared_ptr here to ensure the dynamic python library object
    // is deleted when the factory goes away. Can't use scoped_ptr
    // because it is not initialized in the constructor.
    boost::shared_ptr<DynamicPythonLibrary> pyLib_; 
  };
}


#endif // NTA_REGION_IMPL_FACTORY_HPP
