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
 * Definition of the Link class
 */

#ifndef NTA_LINK_HPP
#define NTA_LINK_HPP

#include <string>
#include <nta/types/types.hpp>
#include <nta/ntypes/Dimensions.hpp>
#include <nta/engine/LinkPolicy.hpp>
#include <nta/engine/Input.hpp> // needed for splitter map 

namespace nta
{

  class Output;
  class Input;

  class Link
  {
  public:
    /**
     * Links have four-phase initialization. 
     * 1. construct with link type, params, names of regions and inputs/outputs
     * 2. wire in to network (setting src and dest Output/Input pointers)
     * 3. set source and destination dimensions
     * 4. initialize -- sets the offset in the destination Input (not known earlier)
     * 
     * De-serializing is the same as phase 1. 
     * The linkType and linkParams parameters are given to 
     * the LinkPolicyFactory to create a link policy
     */

    /* 
     * This constructor does phase 1 initialization 
     */
    Link(const std::string& linkType, const std::string& linkParams,
         const std::string& srcRegionName, const std::string& destRegionName, 
         const std::string& srcOutputName="", const std::string& destInputName="");


    /*
     * connectToNetwork does phase 2 initialization 
     */
    void connectToNetwork(Output *src, Input*dest);

    /*
     * This constructor combines phase 1 and phase 2 initialization
     */
    Link(const std::string& linkType, const std::string& linkParams, 
         Output* srcOutput, Input* destInput);


    ~Link();

    /* 
     * In phase 3, NuPIC will set and/or get 
     * source and/or destination dimensions
     * until both are set. 
     * 
     * Normally we will set the src dimensions and 
     * the dest dimensions will be induced. 
     * It is possible to go the other way, though. 
     */
    void setSrcDimensions(Dimensions& dims);

    void setDestDimensions(Dimensions& dims);

    const Dimensions& getSrcDimensions() const;
    const Dimensions& getDestDimensions() const;

    /*
     * initialize does phase 4 initialization
     */
    void initialize(size_t destinationOffset);


    // Return constructor params
    const std::string& getLinkType() const;
    const std::string& getLinkParams() const;
    const std::string& getSrcRegionName() const;
    const std::string& getSrcOutputName() const;
    const std::string& getDestRegionName() const;
    const std::string& getDestInputName() const;

    const std::string toString() const;


    // The methods below only work on connected links (after phase 2)
    Output& getSrc() const;
    Input& getDest() const;

    // Nodes request input data from their input objects. 
    // The input objects, in turn, request links to copy
    // data into the inputs
    void
    compute();

    // Returns the size of the input contributed by this link
    // for a single node. 
    // @todo index=-1 for region-level input?
    size_t
    getNodeInputSize(size_t nodeIndex);

    // If the input for a particular node is a contiguous subset
    // of the src output, then the splitter map is overkill, and 
    // all we need to know is the offset/size (per node)
    // Returns true if and only if the input for each node
    // is a contiguous chunk of the input buffer. 
    // TODO: not implemented;  necessary?
    bool
    isInputContiguous();

    // Locate the contiguous input for a node. 
    // This method is used only if the input is contiguous
    // TODO: not implemented;  necessary?
    size_t
    getInputOffset(size_t nodeIndex);


    /*
     * A splitter map is a matrix that maps the full input
     * of a region to the inputs of individual nodes within 
     * the region. 
     * A splitter map "sm" is declared as:
     * 
     *    vector< vector<size_t> > sm;
     * 
     * sm.length() == number of nodes
     * 
     * sm[i] is a "sparse vector" used to gather the input 
     * for node i. sm[i].size() is the size (in elements) of 
     * the input for node i
     * 
     * sm[i] gathers the inputs as follows:
     * 
     * T *regionInput; // input buffer for the whole region
     * T *nodeInput; // pre-allocated 
     * for (size_t elem = 0; elem < sm[i].size; elem++)
     *    nodeInput[elem] = regionInput[sm[i][elem]];
     * 
     *
     * The offset specified by sm[i][j] is in units of elements. 
     * To get byte offsets, you'd multiply by the size of an input/output
     * element. 
     * 
     * An input to a region may come from several links. 
     * Each link contributes a contiguous block of the region input
     * starting from a certain offset. The splitter map indices are 
     * with respect to the full region input, not the partial region
     * input contributed by this link, so the destinationOffset for this
     * link is included in each of the splitter map entries. 
     *
     * Finally, the API is designed so that each link associated with 
     * an input can contribute its portion to a full splitter map. 
     * Thus the splitter map is an input-output parameter. This method
     * appends data to each row of the splitter map, assuming that 
     * existing data in the splitter map comes from other links. 
     * 
     * For region-level inputs, a splitter map has just a single row. 
     *
     * Splitter map ownership:
     * The splitter map is owned by the containing Input. Each Link
     * in the input contributes a portion to the splitter map, through
     * the buildSplitterMap method. 
     * 
     */
    void 
    buildSplitterMap(Input::SplitterMap& splitter);

    friend std::ostream& operator<<(std::ostream& f, const Link& link);


  private:
    // common initialization for the two constructors. 
    void commonConstructorInit_(const std::string& linkType, 
                                const std::string& linkParams,
                                const std::string& srcRegionName, 
                                const std::string& destRegionName, 
                                const std::string& srcOutputName, 
                                const std::string& destInputName);

    // TODO: The strings with src/dest names are redundant with
    // the src_ and dest_ objects. For unit testing links, 
    // and for deserializing networks, we need to be able to create
    // a link object without a network. and for deserializing, we 
    // need to be able to instantiate a link before we have instantiated
    // all the regions. (Maybe this isn't true? Revaluate when 
    // more infrastructure is in place). 

    std::string srcRegionName_;
    std::string destRegionName_;
    std::string srcOutputName_;
    std::string destInputName_;

    // We store the values given to use. Use these for 
    // serialization instead of serializing the LinkPolicy
    // itself. 
    std::string linkType_;
    std::string linkParams_;

    LinkPolicy *impl_;

    Output *src_;
    Input *dest_;

    // Each link contributes a contiguous chunk of the destination 
    // input. The link needs to know its offset within the destination 
    // input. This value is set at initialization time. 
    size_t destOffset_;

    // TODO: These are currently unused. Situations where we need them
    // are rare. Would they make more sense as link policy params?
    // Will also need a link getDestinationSize method since
    // the amount of data contributed by this link to the destination input
    // may not equal the size of the source output. 
    size_t srcOffset_;
    size_t srcSize_;

    // link must be initialized before it can compute()
    bool initialized_;

  };


} // namespace nta


#endif // NTA_LINK_HPP
