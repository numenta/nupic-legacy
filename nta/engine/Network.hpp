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
 * Interface for the Network class
 */

#ifndef NTA_NETWORK_HPP
#define NTA_NETWORK_HPP


#include <map>
#include <string>
#include <vector>
#include <set>
#include <nta/types/types.hpp>
#include <nta/ntypes/Collection.hpp>

namespace nta
{

  class Region;
  class Dimensions;


  /**
   * A Network represents an HTM network. A network is a collection of regions.
   */
  class Network
  {
  public:
    // ---
    // create/load/save
    // ---

    Network();
    Network(const std::string& path);

    ~Network();


    /**
     * Create a new region in a network
     * @param name Name of the region, Must be unique in the network
     * @param nodeType Type of node in the region, e.g. "FDRNode"
     * @param nodeParams A JSON-encoded string specifying writable params
     * @returns A pointer to the newly created Region
     */
    Region*
    addRegion(const std::string& name, 
              const std::string& nodeType, 
              const std::string& nodeParams);

   /**
    * Create a new region from saved state
    * @param name Name of the region, Must be unique in the network
    * @param nodeType Type of node in the region, e.g. "FDRNode"
    * @param dimensions Dimensions of the region
    * @param bundlePath The path to the bundle
    * @returns A pointer to the newly created Region
    */
    Region*
    addRegionFromBundle(const std::string& name, 
                        const std::string& nodeType, 
                        const Dimensions& dimensions, 
                        const std::string& bundlePath, 
                        const std::string& label);

   /**
    * Removes a new region from the network
    * @param name Name of the Region
    */
    void
    removeRegion(const std::string& name);

   /**
    * Create a link and add it to the network
    * @param srcName Name of the source region
    * @param destName Name of the destination region
    * @param linkType Type of the link
    * @param linkParams Parameters of the link
    * @param srcOutput Name of the source output
    * @param destInput Name of the destination input
    */
    void
    link(const std::string& srcName, const std::string& destName, 
         const std::string& linkType, const std::string& linkParams, 
         const std::string& srcOutput="", const std::string& destInput="");


   /**
    * Removes a link 
    * @param srcName Name of the source region
    * @param destName Name of the destination region
    * @param srcOutputName Name of the source output
    * @param destInputName Name of the destination input
    */
    void
    removeLink(const std::string& srcName, const std::string& destName, 
               const std::string& srcOutputName="", const std::string& destInputName=""); 
  
   /**
    * Initialize all elements of a network so that it can run
    */
    void
    initialize();


    //
    // -------------- access to components -----------------
    //

   /**
    * Get all regions
    * @returns A Collection of Region objects in the network
    */
    const Collection<Region*>&
    getRegions() const;
  
   /**
    * Set phases for a region
    * @param name Name of the region
    * @param phases A tuple of phases (must be positive integers)
    */
    void
    setPhases(const std::string& name, std::set<UInt32>& phases);
    
   /**
    * Get phases for a region
    * @param name Name of the region
    * @returns Set of phases for the region
    */
    std::set<UInt32>
    getPhases(const std::string& name) const;


   /**
    * Get minumum phase for regions in this network. If no regions, then min = 0
    * @returns Minimum phase
    */
    UInt32 getMinPhase() const;


   /**
    * Get maximum phase for regions in this network. If no regions, then max = 0
    * @returns Maximum phase
    */
    UInt32 getMaxPhase() const;
    
    // 
    // -------------- run -----------------
    //


   /**
    * Run the network for the given number of iterations
    * @param n Number of iterations
    */
    void
    run(int n);

    /**
     * You can attach a callback function to a network, and the callback
     * function is called after every iteration of run().
     * To add a callback, just get a reference to the callback collection
     * with getCallbacks, and add a callback
     */
    typedef void (*runCallbackFunction)(Network*, UInt64 iteration, void*);
    typedef std::pair<runCallbackFunction, void*> callbackItem;

   /**
    * Get reference to callback Collection
    * @returns Reference to callback Collection
    */
    Collection<callbackItem>& getCallbacks();

   /**
    * Set the minimum enabled phase for this network
    * @param minPhase Minimum enabled phase
    */
    void
    setMinEnabledPhase(UInt32 minPhase);

   /**
    * Set the maximum enabled phase for this network
    * @param minPhase Maximum enabled phase
    */
    void
    setMaxEnabledPhase(UInt32 minPhase);
    
   /**
    * Get the minimum enabled phase for this network
    * @returns Minimum enabled phase for this network
    */
    UInt32
    getMinEnabledPhase() const;
    
   /**
    * Get the maximum enabled phase for this network
    * @returns Maximum enabled phase for this network
    */
    UInt32
    getMaxEnabledPhase() const;

    //
    // ------------ serialization -------------
    //

   /**
    * Save the network to a network bundle (extension ".nta")
    * @param name Name of the bundle
    */
    void save(const std::string& name);

   /**
    * Start profiling for all regions of this network
    */
    void
    enableProfiling();

   /**
    * Stop profiling for all regions of this network
    */
    void
    disableProfiling();

   /**
    * Reset profiling timers for all regions of this network
    */
    void
    resetProfiling();

  private:


    // Both constructors use this common initialization method
    void commonInit();

    // Used by the path-based constructor
    void load(const std::string& path);

    void loadFromBundle(const std::string& path);

    // save() always calls this internal method, which creates
    // a .nta bundle
    void saveToBundle(const std::string& bundleName);

    // internal method using region pointer instead of name
    void 
    setPhases_(Region *r, std::set<UInt32>& phases);

    // default phase assignment for a new region
    void setDefaultPhase_(Region* region);
    
    // whenever we modify a network or change phase
    // information, we set enabled phases to min/max for
    // the network
    void resetEnabledPhases_();

    bool initialized_;
    Collection<Region*> regions_;

    UInt32 minEnabledPhase_;
    UInt32 maxEnabledPhase_;
    
    // This is main data structure used to choreograph
    // network computation
    std::vector< std::set<Region*> > phaseInfo_;
  
    // we invoke these callbacks at every iteration
    Collection<callbackItem> callbacks_;
    
    //number of elapsed iterations
    UInt64 iteration_;
  };

} // namespace nta

#endif // NTA_NETWORK_HPP
