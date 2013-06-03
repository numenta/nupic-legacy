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
 * Declarations for SpatialPoolerNode
 */

#ifndef NTA_SPATIAL_POOLER_NODE2_HPP
#define NTA_SPATIAL_POOLER_NODE2_HPP

#include <nta/engine/Input.hpp>
#include <nta/engine/RegionImpl.hpp>
#include <nta/ntypes/Value.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/ntypes/ArrayRef.hpp>
#include <nta/utils/Random.hpp>
#include <nta/algorithms/SparsePooler.hpp>

namespace nta
{
//--------------------------------------------------------------------------------
/**
 * SpatialPoolerNode.
 * 
 * @b Responsibility:
 *  Quantize/summarize input vectors.
 *
 * @b Rationale:
 *
 * @b Resource/Ownerships:
 *
 * @b Notes:
 */
  class SpatialPoolerNode : public RegionImpl
  {
  public:
    static Spec* createSpec();
    size_t getNodeOutputElementCount(const std::string& outputName);
    void getParameterFromBuffer(const std::string& name, Int64 index, IWriteBuffer& value);

    /**
     * NOTE:
     * Sigma and maxDistance, two parameters used in SpatialPooler's
     * gaussian mode, cannot be set after initialization of the Node:
     * changing those values would result in different meanings for 
     * the coincidences in the Node. 
     */
    void setParameterFromBuffer(const std::string& name, Int64 index, IReadBuffer& value);

    void setParameterString(const std::string& name, Int64 index, const std::string& s);
    std::string getParameterString(const std::string& name, Int64 index);

    // for coincidenceMatrix
    Handle getParameterHandle(const std::string& paramName, Int64 index);


    void initialize();
  
  
    /**
     * Constructor.
     * The node is set to learning mode by default.
     *
     * @param nodeParams [NTA_NodeParams* UNUSED] the node parameters 
     *
     * @b Exceptions:
     *  @li None.
     */
    SpatialPoolerNode(const ValueMap& params, Region *region);
  
    SpatialPoolerNode(BundleIO& bundle, Region* region);


    /**
     * Destructor.
     * Recovers the memory of the pooler and grouper.
     *
     * @b Exceptions:
     *  @li None.
     */
    virtual ~SpatialPoolerNode();
  

    // ---
    /// Serialize state to bundle
    // ---
    virtual void serialize(BundleIO& bundle);

    // ---
    /// De-serialize state from bundle
    // ---
    virtual void deserialize(BundleIO& bundle);

    /**
     * Computes the output vector for given inputs.
     * Cannot be called before node has been initialized.
     * Compute is called exactly once for each input vector
     * presented to the node. It is on the critical path
     * for performance. Compute is called both in learning
     * and in inference mode. 
     *
     * @b Exceptions:
     *  @li Pooler or grouper not initialized.
     *  @li Unknown mode.
     *  @li Pooler and grouper learning/inference exceptions.
     */
    void compute();

    /**
     * Executes node's commands. See help string for details of available
     * commands.
     * Cannot be called before node has been initialized.
     *
     * NOTE 1: getHistory and getSpatialPoolerOutput return -1 before learning
     * NOTE 2: inference can be turned on only once after learning
     * NOTE 3: inference cannot be turned on prior to learning
     * NOTE 4: learning cannot be turned back on after inference
     *
     * @param cmdLine [IReadBufferIterator&] the command line to execute
     * @param out [IWriteBuffer&] the result of the execution
     * @param nodeSet [NTA_IndexRangeList*] set of nodes to operate on within
     *                   multi-nodes.  
     *
     * @b Exceptions:
     *  @li Pooler or grouper not initialized.
     *  @li If turning on learning after inference.
     *  @li If turning on inference without learning first.
     *  @li If turning off inference.
     *  @li Unknown command.
     *  @li Command syntax error.
     *  @li Command execution error. 
     */
    virtual std::string executeCommand(const std::vector<std::string>& args, Int64 index);

    typedef enum { Learning, Inference } Mode;

  private:
    static const std::string current_spatial_pooler_node_version_;

    Mode mode_;
    bool clonedNodes_;
    UInt64 nodeCount_;

    // create params
    UInt32 segmentSize_;
    SparsePooler::SparsificationMode sparsificationMode_;
    SparsePooler::InferenceMode inferenceMode_;
    std::string patchMasksStr_;
    bool normalize_;
    Real32 norm_;
    Int32 kWinners_;
    Real32 maxDistance_;
    Real32 minAcceptNorm_;
    Real32 minProtoSum_;
    Real32 sigma_;
    UInt32 seed_;


    UInt32 maxNAttempts_;
    UInt32 maxNPrototypes_;
    Real64 acceptanceProbability_;
    Random rgen_;
    bool poolersAllocated_;

    std::vector<SparsePooler*> poolers_;


    // Cached values. Only valid after initialization and not serialized
    // Pointers to Input objects and vectors for reading the input.
    Input* bottomUpIn_;
    Input* topDownIn_;

    // These pointers are references to arrays in Output objects. 
    // Before initialization, they are NULL
    ArrayRef bottomUpOut_; 
    ArrayRef topDownOut_;

    std::vector<Real> bottomUpInputVector_;
    std::vector<Real> topDownInputVector_;

    size_t buInputSizePerNode_;
    size_t tdInputSizePerNode_;

    UInt32 phaseIndex_;


    static void waitDebuggerAttach_();
    void switchToInference_();

    NO_DEFAULTS(SpatialPoolerNode);
  };
} // namespace nta
//--------------------------------------------------------------------------------
#endif // NTA_SPATIAL_POOLER_NODE2_HPP


