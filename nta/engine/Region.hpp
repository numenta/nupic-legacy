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
 * Definition of the Region API
 *
 * A region is a set of one or more "identical" nodes, implemented by a 
 * RegionImpl"plugin". A region contains nodes. 
*/

#ifndef NTA_REGION_HPP
#define NTA_REGION_HPP

#include <string>
#include <vector>
#include <map>
#include <set>

#include <nta/types/types.hpp>
// We need the full definitions because these
// objects are returned by value.
#include <nta/ntypes/Dimensions.hpp>
#include <nta/os/Timer.hpp>

namespace nta
{
  class RegionImpl;
  class Output; 
  class Input;
  class ArrayRef;
  class Array;
  struct Spec;
  class NodeSet;
  class BundleIO;
  class Timer;
  class Network;

  /**
   * A region is one or more identical nodes in a network.
   *
   * ### Constructors
   * Region constructors are not available in the public API. 
   * Internally regions are created and owned by Network.
   */
  class Region 
  {
  public:

    /* -------------- region information ----------------- */

    /**
     * Get the network containing this region.
     * @returns The network containing this region
     */
    Network * 
    getNetwork();

    /**
     * Get the name of the region
     * @returns the region's name
     */
    const std::string&
    getName() const;


    /**
     * Get the dimensions of the region
     * @returns the region's dimensions
     */
    const Dimensions&
    getDimensions() const;

    /**
     * Assign width and height to the region
     * @param dimensions a Dimensions object that describes the width and height
     */
    void
    setDimensions(Dimensions & dimensions);

    /* -------------- inputs/outputs ----------------- */

    /**
     * Copies data into the inputs of this region, using
     * the links that are attached to each input. 
     */
    void
    prepareInputs();

    /* -------------- Element interface methods  ----------------- */

    /**
     * Get the type of the region
     * @returns The node type as a string
     */
    const std::string&
    getType() const;

    /**
     * Get the spec of the region
     * @returns The spec that describes this region
     */
    const Spec* 
    getSpec() const;

    /**
     * Get the Spec of a region type without an instance
     * @param nodeType a region type as a string
     * @returns The Spec that describes this region type
     */
    static const Spec* 
    getSpecFromType(const std::string& nodeType);

    /**
     * TODO: document
     * @param name TODO: document
     * @returns TODO: document
     */
    Int32
    getParameterInt32(const std::string& name) const;

    /**
     * TODO: document
     * @param name TODO: document
     * @returns TODO: document
     */
    UInt32
    getParameterUInt32(const std::string& name) const;

    /**
     * TODO: document
     * @param name TODO: document
     * @returns TODO: document
     */
    Int64
    getParameterInt64(const std::string& name) const;

    /**
     * TODO: document
     * @param name TODO: document
     * @returns TODO: document
     */
    UInt64
    getParameterUInt64(const std::string& name) const;

    /**
     * TODO: document
     * @param name TODO: document
     * @returns TODO: document
     */
    Real32
    getParameterReal32(const std::string& name) const;

    /**
     * TODO: document
     * @param name TODO: document
     * @returns TODO: document
     */
    Real64
    getParameterReal64(const std::string& name) const;

    /**
     * TODO: document
     * @param name TODO: document
     * @returns TODO: document
     */
    Handle
    getParameterHandle(const std::string& name) const;


    /**
     * TODO: document
     * @param name TODO: document
     * @param value TODO: document
     */
    void
    setParameterInt32(const std::string& name, Int32 value);

    /**
     * TODO: document
     * @param name TODO: document
     * @param value TODO: document
     */
    void
    setParameterUInt32(const std::string& name, UInt32 value);

    /**
     * TODO: document
     * @param name TODO: document
     * @param value TODO: document
     */
    void
    setParameterInt64(const std::string& name, Int64 value);

    /**
     * TODO: document
     * @param name TODO: document
     * @param value TODO: document
     */
    void
    setParameterUInt64(const std::string& name, UInt64 value);

    /**
     * TODO: document
     * @param name TODO: document
     * @param value TODO: document
     */
    void
    setParameterReal32(const std::string& name, Real32 value);

    /**
     * TODO: document
     * @param name TODO: document
     * @param value TODO: document
     */
    void
    setParameterReal64(const std::string& name, Real64 value);

    /**
     * TODO: document
     * @param name TODO: document
     * @param value TODO: document
     */
    void
    setParameterHandle(const std::string& name, Handle value);


    /**
     * get/setArray methods take a memory buffer. If buffer is
     * not null, they copy into the supplied buffer; otherwise
     * they ask Array to allocate an array and copy into it. 
     * NuPIC throws an exception if supplied array is not big enough.  
     *
     * @todo: auto-reallocate?
     *
     * A typical use might be that the caller would supply an 
     * unallocated buffer on the first call and then reuse the memory
     * buffer on subsequent calls, i.e.
     * 
     *     {
     *       Array buffer(NTA_BasicTypeInt64); // no buffer allocated
     *       getParameterArray("foo", array);  // buffer is allocated, and owned
     *                                         // by array object
     *       getParameterArray("foo", buffer); // uses already-allocated buffer
     *     }    // Array destructor called -- frees the buffer
     * 
     * @param name TODO: document
     * @param array TODO: document
     * @returns TODO: document
     */
    void
    getParameterArray(const std::string& name, Array & array) const;

    /**
     * Caller must initialize the array argument to setParameterArray 
     * Depending on how the buffer was allocated
     * the array owns its buffer.
     * 
     * @param name TODO: document
     * @param array TODO: document
     */
    void
    setParameterArray(const std::string& name, const Array & array);

    /**
     * Strings are handled internally as Byte Arrays, but this interface
     * is clumsy. set/getParameterString internally use byte arrays but
     * converts to/from strings
     *
     * setParameterString is implemented with one copy (from the string into
     * the node) but getParameterString requires a second copy so that there
     * are temporarily three copies of the data in memory (in the node, 
     * in an internal Array object, and in the string returned to the user)
     * 
     * @param name TODO: document
     * @param s TODO: document
     */
    void
    setParameterString(const std::string& name, const std::string& s);
    
    /**
     * TODO: document
     * @param name TODO: document
     */
    std::string
    getParameterString(const std::string& name);

    /**
     * TODO: document
     * @param name TODO: document
     */
    bool
    isParameterShared(const std::string& name) const;

    /**
     * Get the input data into the output array.
     * 
     * ### Description
     * Get the data of an input and store it or point to it in the
     * the output array. The actual behavior is controlled by the 'copy'
     * argument (see below).
     *
     * @todo The param `array` below doesn't make sense
     *
     * @param inputName The name of the target input
     * @param array An output ArrayRef that will contain the input data after
     *              the call returns. It is an error to supply an array with
     *              an empty buffer.
     *
     * @returns array that contains the input data.
     */
    virtual ArrayRef
    getInputData(const std::string& inputName) const;

    /**
     * Get the output data into the output array.
     * 
     * ### Description
     * Get the data of an output and store it or point to it in the
     * the output array. The actual behavior is controlled by the 'copy'
     * argument (see below).
     *
     * @todo The param `array` below doesn't make sense
     * 
     * @param outputName The name of the target output
     * @param array An output ArrayRef that will contain the output data after
     *              the call returns.
     *
     * @returns array that contains the output data.
     */
    virtual ArrayRef
    getOutputData(const std::string& outputName) const;

    /**
     * TODO: document
     * 
     * @todo are getOutput/InputCount needed? count can be obtained from the array objects. 
     * 
     * @param outputName TODO: document
     * @returns TODO: document
     */
    virtual size_t
    getOutputCount(const std::string& outputName) const;

    /**
     * TODO: document
     * @param inputName TODO: document
     * @returns TODO: document
     */
    virtual size_t
    getInputCount(const std::string& inputName) const;

    /**
     * TODO: document
     */
    virtual void
    enable();

    /**
     * TODO: document
     */
    virtual void
    disable();

    /**
     * Request the underlying region to execute a command.
     *
     * @param args A list of strings that the actual region will interpret. 
     *              The first string is the command name. The other arguments 
     *              are optional.
     *
     * @returns The result value  of command execution is a string determined 
     *          by the underlying region.
     */
    virtual std::string
    executeCommand(const std::vector<std::string>& args);

    /**
     * Perform one step of the region computation.
     */
    void
    compute();

    /**
     * Enable profiling of the compute and execute operations
     */
    void
    enableProfiling();

    /**
     * Disable profiling of the compute and execute operations
     */
    void
    disableProfiling();

    /**
     * Reset the compute and execute timers
     */
    void
    resetProfiling();

    /**
     * Get the timer used to profile the compute operation
     * @returns The Timer object used to profile the compute operation
     */
    const Timer& getComputeTimer() const;

    /**
     * Get the timer used to profile the execute operation
     * @returns The Timer object used to profile the execute operation
     */
    const Timer& getExecuteTimer() const;

#ifdef NTA_INTERNAL
    // Internal methods.

    // New region from parameter spec
    Region(const std::string& name,
           const std::string& type,
           const std::string& nodeParams,
           Network * network = NULL);

    // New region from serialized state
    Region(const std::string& name, 
           const std::string& type, 
           const Dimensions& dimensions, 
           BundleIO& bundle,
           Network * network = NULL);

    virtual ~Region();

    void
    initialize();

    bool
    isInitialized() const;



    // Used by RegionImpl to get inputs/outputs
    Output*
    getOutput(const std::string& name) const;
    
    Input*
    getInput(const std::string& name) const;

    // These are used only for serialization
    const std::map<const std::string, Input*>& 
    getInputs() const;

    const std::map<const std::string, Output*>& 
    getOutputs() const;

    // The following methods are called by Network in initialization

    // Returns number of links that could not be fully evaluated
    size_t
    evaluateLinks();

    std::string
    getLinkErrors() const;

    size_t
    getNodeOutputElementCount(const std::string& name);

    void
    initOutputs();

    void
    initInputs() const;

    void
    intialize();

    // Internal -- for link debugging
    void
    setDimensionInfo(const std::string& info);

    const std::string&
    getDimensionInfo() const;
    
    bool 
    hasOutgoingLinks() const;

    // These methods are needed for teardown choreography
    // in Network::~Network()
    // It is an error to call any region methods after uninitialize() 
    // except removeAllIncomingLinks and ~Region
    void 
    uninitialize();

    void
    removeAllIncomingLinks();

    const NodeSet& 
    getEnabledNodes() const;

    // TODO: sort our phases api. Users should never call Region::setPhases
    // and it is here for serialization only. 
    void 
    setPhases(std::set<UInt32>& phases);

    std::set<UInt32>&
    getPhases();

    // Called by Network for serialization
    void 
    serializeImpl(BundleIO& bundle);


#endif // NTA_INTERNAL

  private:
    // verboten
    Region();
    Region(Region&);

    // common method used by both constructors
    // Can be called after nodespec_ has been set. 
    void createInputsAndOutputs_();

    const std::string name_;

    // pointer to the "plugin"; owned by Region
    RegionImpl* impl_;
    const std::string type_;
    Spec* spec_; 

    typedef std::map<const std::string, Output*> OutputMap;
    typedef std::map<const std::string, Input*> InputMap;

    OutputMap outputs_;
    InputMap inputs_;
    // used for serialization only
    std::set<UInt32> phases_; 
    Dimensions dims_; // topology of nodes; starts as []
    bool initialized_;

    NodeSet* enabledNodes_;

    // Region contains a backpointer to network_ only to be able
    // to retrieve the containing network via getNetwork() for inspectors.
    // The implementation should not use network_ in any other methods. 
    Network* network_;

    // Figuring out how a region's dimensions were set
    // can be difficult because any link can induce
    // dimensions. This field says how a region's dimensions
    // were set. 
    std::string dimensionInfo_;

    // private helper methods
    void setupEnabledNodeSet();


    // Profiling related methods and variables.
    bool profilingEnabled_;
    Timer computeTimer_;
    Timer executeTimer_;
  };

} // namespace nta

#endif // NTA_REGION_HPP
