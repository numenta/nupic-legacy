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

  // --- @doc:begin
  // name: description
  // summary: A region is one or more identical nodes in a network.
  // --- @doc:end
  class Region 
  {
  public:

    /* -------------- constructors, etc. ----------------- */
    // Region constructors are not available in the public API. 
    // Internally regions are created and owned by Network.

    /* -------------- region information ----------------- */
    
    // --- @doc:begin
    // name: getNetwork
    // summary: Get the network containing this region
    // return: The network containing this region
    // --- @doc:end    
    Network * 
    getNetwork();

    // --- @doc:begin
    // name: getName
    // summary: Get the name of the region
    // return: The region's name
    // --- @doc:end    
    const std::string&
    getName() const;


    // --- @doc:begin
    // name: getDimensions
    // summary: Get the dimensions of the region
    // return: The region's dimensions
    // --- @doc:end    
    const Dimensions&
    getDimensions() const;

    // --- @doc:begin
    // name: setDimensions
    // summary: Assign width and height to the region
    // arguments:
    //  - dimensions: a Dimensions object that describes the width and height
    // return: Nothing
    // --- @doc:end    
    void
    setDimensions(Dimensions & dimensions);

    /* -------------- inputs/outputs ----------------- */
    // Copies data into the inputs of this region, using
    // the links that are attached to each input. 
    void
    prepareInputs();
  
    

    /* -------------- Element interface methods  ----------------- */

    // --- @doc:begin
    // name: getType
    // summary: Get the type of the region
    // return: The node type as a string
    // --- @doc:end    
    const std::string&
    getType() const;

    // --- @doc:begin
    // name: getSpec
    // summary: Get the spec of the region
    // return: The spec that describes this region
    // --- @doc:end    
    const Spec* 
    getSpec() const;

    // --- @doc:begin
    // name: getSpecFromType
    // summary: Get the Spec of a region type without an instance
    // arguments:
    //  - nodeType: a region type as a string
    // return: The Spec that describes this region type
    // --- @doc:end    
    static const Spec* 
    getSpecFromType(const std::string& nodeType);

    Int32
    getParameterInt32(const std::string& name) const;
    UInt32
    getParameterUInt32(const std::string& name) const;
    Int64
    getParameterInt64(const std::string& name) const;
    UInt64
    getParameterUInt64(const std::string& name) const;
    Real32
    getParameterReal32(const std::string& name) const;
    Real64
    getParameterReal64(const std::string& name) const;
    Handle
    getParameterHandle(const std::string& name) const;


    void
    setParameterInt32(const std::string& name, Int32 value);
    void
    setParameterUInt32(const std::string& name, UInt32 value);
    void
    setParameterInt64(const std::string& name, Int64 value);
    void
    setParameterUInt64(const std::string& name, UInt64 value);
    void
    setParameterReal32(const std::string& name, Real32 value);
    void
    setParameterReal64(const std::string& name, Real64 value);
    void
    setParameterHandle(const std::string& name, Handle value);


    /**
     * get/setArray methods take a memory buffer. If buffer is
     * not null, they copy into the supplied buffer; otherwise
     * they ask Array to allocate an array and copy into it. 
     * NuPIC throws an exception if supplied array is not big enough.  
     * TODO: auto-reallocate?
     * A typical use might be that the caller would supply an 
     * unallocated buffer on the first call and then reuse the memory
     * buffer on subsequent calls, i.e.
     * 
     * {
     *   Array buffer(NTA_BasicTypeInt64); // no buffer allocated
     *   getParameterArray("foo", array);  // buffer is allocated, and owned
     *                                     // by array object
     *   getParameterArray("foo", buffer); // uses already-allocated buffer
     * }    // Array destructor called -- frees the buffer
     */
    void
    getParameterArray(const std::string& name, Array & array) const;

    /**
     * Caller must initialize the array argument to setParameterArray 
     * Depending on how the buffer was allocated
     * the array owns its buffer.
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
     */

    void
    setParameterString(const std::string& name, const std::string& s);
    
    std::string
    getParameterString(const std::string& name);

    bool
    isParameterShared(const std::string& name) const;

    // --- @doc:begin
    // name: getInputData
    // summary: Get the input data into the output array.
    // description: |
    //   Get the data of an input and store it or point to it in the
    //   the output array. The actual behavior is controlled by the 'copy'
    //   argument (see below).
    //
    // arguments:
    //  - inputName: The name of the target input
    //  - array: |
    //      An output ArrayRef that will contain the input data after
    //      the call returns. It is an error to supply an array with
    //      an empty buffer.
    //
    // return: array that contains the input data.
    // --- @doc:end
    virtual ArrayRef
    getInputData(const std::string& inputName) const;

    // --- @doc:begin
    // name: getOutputData
    // summary: Get the output data into the output array.
    // description: |
    //   Get the data of an output and store it or point to it in the
    //   the output array. The actual behavior is controlled by the 'copy'
    //   argument (see below).
    //
    // arguments:
    //  - outputName: The name of the target output
    //  - array: |
    //      An output ArrayRef that will contain the output data after
    //      the call returns.
    //
    // return: array that contains the output data.
    // --- @doc:end
    virtual ArrayRef
    getOutputData(const std::string& outputName) const;

    // are getOutput/InputCount needed? count can be obtained from the array objects. 
    virtual size_t
    getOutputCount(const std::string& outputName) const;

    virtual size_t
    getInputCount(const std::string& inputName) const;

    // run
    virtual void
    enable();

    virtual void
    disable();

    // --- @doc:begin
    // name: executeCommand
    // summary: Request the undelying region to execute a command.
    //
    // arguments:
    //  - args: |
    //      A list of strings that the actual region will interpret. The first
    //      string is the command name. The other arguments are optional.
    //
    // return: |
    //   The result value  of command execution is a string determined by the
    //    underlying region.
    // --- @doc:end
    virtual std::string
    executeCommand(const std::vector<std::string>& args);

    // --- @doc:begin
    // name: compute
    // summary: Perform one step of the region computation.
    // arguments: None
    // return: Nothing
    // --- @doc:end    
    void
    compute();

    // Profiling functionality
    // --- @doc:begin
    // name: enableProfiling
    // summary: Enable profiling of the compute and execute operations
    // arguments: None
    // return: Nothing
    // --- @doc:end    
    void
    enableProfiling();

    // --- @doc:begin
    // name: disableProfiling
    // summary: Disable profiling of the compute and execute operations
    // arguments: None
    // return: Nothing
    // --- @doc:end    
    void
    disableProfiling();

    // --- @doc:begin
    // name: resetProfiling
    // summary: Reset the compute and execute timers
    // arguments: None
    // return: Nothing
    // --- @doc:end    
    void
    resetProfiling();

    // --- @doc:begin
    // name: getComputeTimer
    // summary: Get the timer used to profile the compute operation
    // arguments: None
    // return: The Timer object used to profile the compute operation
    // --- @doc:end    
    const Timer& getComputeTimer() const;

    // --- @doc:begin
    // name: getExecuteTimer
    // summary: Get the timer used to profile the execute operation
    // arguments: None
    // return: The Timer object used to profile the execute operation
    // --- @doc:end    
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
