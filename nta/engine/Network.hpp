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

// ---
/// @file 
/// Interface for the Network class
// ---

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


  // --- @doc:begin
  // name: description
  // summary: A Network represents an HTM network. A network is a collection of regions.
  // --- @doc:end
  class Network
  {
  public:
    // ---
    // create/load/save
    // ---

    Network();
    Network(const std::string& path);

    ~Network();


    // --- @doc:begin
    // name: addRegion
    // summary: Create a new region in a network
    // arguments:
    //  - name: Name of the region, Must be unique in the network
    //  - nodeType: Type of node in the region, e.g. "FDRNode"
    //  - nodeParams: A JSON-encoded string specifying writable params
    // return: A pointer to the newly created region
    // --- @doc:end
    Region*
    addRegion(const std::string& name, 
              const std::string& nodeType, 
              const std::string& nodeParams);

    // --- @doc:begin
    // name: addRegionFromBundle
    // summary: Create a new region from saved state
    // arguments:
    //  - name: Name of the region, Must be unique in the network
    //  - nodeType: Type of node in the region, e.g. "FDRNode"
    //  - dimensions: Dimensions of the region
    //  - bundlePath: The path to the bundle
    // return: A pointer to the newly created region
    // --- @doc:end
    Region*
    addRegionFromBundle(const std::string& name, 
                        const std::string& nodeType, 
                        const Dimensions& dimensions, 
                        const std::string& bundlePath, 
                        const std::string& label);

    // --- @doc:begin
    // name: removeRegion
    // summary: Removes a new region from the network
    // arguments:
    //  - name: Name of the region
    // return: Nothing
    // --- @doc:end
    void
    removeRegion(const std::string& name);

    // --- @doc:begin
    // name: link
    // summary: Create a link and add it to the network
    // arguments:
    //  - srcName: Name of the source region
    //  - destName: Name of the destination region
    //  - linkType: Type of the link
    //  - linkParams: Parameters of the link
    //  - srcOutput: Name of the source output
    //  - destInput: Name of the destination input
    // return: Nothing
    // --- @doc:end
    void
    link(const std::string& srcName, const std::string& destName, 
         const std::string& linkType, const std::string& linkParams, 
         const std::string& srcOutput="", const std::string& destInput="");


    // --- @doc:begin
    // name: removeLink
    // summary: Removes a link 
    // arguments:
    //  - srcName: Name of the source region
    //  - destName: Name of the destination region
    //  - srcOutputName: Name of the source output
    //  - destInputName: Name of the destination input
    // return: Nothing
    // --- @doc:end
    void
    removeLink(const std::string& srcName, const std::string& destName, 
               const std::string& srcOutputName="", const std::string& destInputName=""); 
  
    // --- @doc:begin
    // name: initialize
    // summary: Initialize all elements of a network so that it can run
    // return: Nothing
    // --- @doc:end
    void
    initialize();


    //
    // -------------- access to components -----------------
    //

    // --- @doc:begin
    // name: getRegions
    // summary: Get all regions
    // return: A collection of regions in the network
    // --- @doc:end
    const Collection<Region*>&
    getRegions() const;
  
    // --- @doc:begin
    // name: setPhases
    // summary: Set phases for a region
    // arguments:
    //  - name: Name of the region
    //  - phases: A tuple of phases (must be positive integers)
    // return: Nothing
    // --- @doc:end
    void
    setPhases(const std::string& name, std::set<UInt32>& phases);
    
    // --- @doc:begin
    // name: getPhases
    // summary: Get phases for a region
    // arguments:
    //  - name: Name of the region
    // return: Set of phases for the region
    // --- @doc:end
    std::set<UInt32>
    getPhases(const std::string& name) const;


    // --- @doc:begin
    // name: getMinPhase
    // summary: Get minumum phase for regions in this network. If no regions, then min = 0
    // return: Minimum phase
    // --- @doc:end
    UInt32 getMinPhase() const;


    // --- @doc:begin
    // name: getMaxPhase
    // summary: Get maximum phase for regions in this network. If no regions, then max = 0
    // return: Maximum phase
    // --- @doc:end
    UInt32 getMaxPhase() const;
    
    // 
    // -------------- run -----------------
    //


    // --- @doc:begin
    // name: run
    // summary: Run the network for the given number of iterations
    // arguments:
    //  - n: Number of iterations
    // return: Nothing
    // --- @doc:end
    void
    run(int n);

    //  ---
    /// You can attach a callback function to a network, and the callback
    /// function is called after every iteration of net.run().
    /// To add a callback, just get a reference to the callback collection
    /// with getCallbacks, and add a callback
    //  ---
    typedef void (*runCallbackFunction)(Network*, UInt64 iteration, void*);
    typedef std::pair<runCallbackFunction, void*> callbackItem;
    // --- @doc:begin
    // name: getCallbacks 
    // summary: Get reference to callback collection
    // return: Reference to callback collection
    // --- @doc:end
    Collection<callbackItem>& getCallbacks();

    // --- @doc:begin
    // name: setMinEnabledPhase
    // summary: Set the minimum enabled phase for this network
    // arguments:
    //  - minPhase: Minimum enabled phase
    // return: Nothing
    // --- @doc:end
    void
    setMinEnabledPhase(UInt32 minPhase);

    // --- @doc:begin
    // name: setMaxEnabledPhase
    // summary: Set the maximum enabled phase for this network
    // arguments:
    //  - minPhase: Maximum enabled phase
    // return: Nothing
    // --- @doc:end
    void
    setMaxEnabledPhase(UInt32 minPhase);
    
    // --- @doc:begin
    // name: getMinEnabledPhase
    // summary: Get the minimum enabled phase for this network
    // return: Minimum enabled phase for this network
    // --- @doc:end
    UInt32
    getMinEnabledPhase() const;
    
    // --- @doc:begin
    // name: getMaxEnabledPhase
    // summary: Get the maximum enabled phase for this network
    // return: Maximum enabled phase for this network
    // --- @doc:end
    UInt32
    getMaxEnabledPhase() const;

    //
    // ------------ serialization -------------
    //

    // --- @doc:begin
    // name: save
    // summary: Save the network to a network bundle (extension ".nta")
    // arguments:
    //  - name: Name of the bundle
    // return: Nothing
    // --- @doc:end
    void save(const std::string& name);

    // --- @doc:begin
    // name: enableProfiling
    // summary: Start profiling for all regions of this network
    // return: Nothing
    // --- @doc:end
    void
    enableProfiling();

    // --- @doc:begin
    // name: disableProfiling
    // summary: Stop profiling for all regions of this network
    // return: Nothing
    // --- @doc:end
    void
    disableProfiling();

    // --- @doc:begin
    // name: resetProfiling
    // summary: Reset profiling timers for all regions of this network
    // return: Nothing
    // --- @doc:end
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
