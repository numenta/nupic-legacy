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
 * Declarations for TemporalPoolerNode
 */

#ifndef NTA_TEMPORAL_POOLER_NODE2_HPP
#define NTA_TEMPORAL_POOLER_NODE2_HPP


#include <nta/engine/RegionImpl.hpp>
#include <nta/ntypes/Value.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/ntypes/ArrayRef.hpp>
#include <nta/algorithms/Grouper.hpp>


namespace nta
{

//--------------------------------------------------------------------------------
/**
 * TemporalPoolerNode.
 * 
 * @b Responsibility:
 *
 * @b Rationale:
 *
 * @b Resource/Ownerships:
 *
 * @b Notes:
 */
  class TemporalPoolerNode : public RegionImpl
  {
  public:

    static Spec* createSpec();
    size_t getNodeOutputElementCount(const std::string& outputName);
    void getParameterFromBuffer(const std::string& name, Int64 index, IWriteBuffer& value);

    void setParameterFromBuffer(const std::string& name, Int64 index, IReadBuffer& value);

    void setParameterString(const std::string& name, Int64 index, const std::string& s);
    std::string getParameterString(const std::string& name, Int64 index);

    void getParameterArray(const std::string& name, Int64 index, Array & array);


    void initialize();
  


    /**
     * Constructor.
     * The node is set to learning mode by default.
     */
    TemporalPoolerNode(const ValueMap& params, Region *region);
  
    TemporalPoolerNode(BundleIO& bundle, Region* region);

    void serialize(BundleIO& bundle);
    void deserialize(BundleIO& bundle);


    /**
     * Destructor.
     * Recovers the memory of the pooler and grouper.
     *
     * @b Exceptions:
     *  @li None.
     */
    virtual ~TemporalPoolerNode();
  

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
    virtual void compute();

    /**
     * Save the state of this TemporalPoolerNode to the buffer.
     * This includes the states of the pooler and grouper.
     * Cannot be called before node has been initialized.
     *
     * @param state [IWriteBuffer&] the destination buffer for the state
     *
     * @b Exceptions:
     *  @li Pooler or grouper not initialized.
     *  @li Pooler and grouper saveState exceptions.
     */
    virtual void saveState(nta::IWriteBuffer& state);


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
    static const std::string current_temporal_pooler_node_version_;

    Mode mode_;
    nta::UInt32 phaseIndex_;
    bool clonedNodes_;
    nta::UInt nodeCount_;
    nta::UInt requestedGroupCount_;
    nta::UInt maxGroupCount_;

    Input* resetInput_;
    Input* bottomUpInput_; 
    Input* topDownInput_;
    ArrayRef bottomUpOutArray_;          
    ArrayRef topDownOutArray_;

    std::vector<nta::Grouper*> poolers_;
    nta::UInt iteration_;

    void computeGroups_(nta::UInt);
    static void waitDebuggerAttach_();
    void switchToInference_();

    bool cache_hot_;
    std::vector<nta::UInt> winner_cache_;
    std::vector<bool> reset_cache_;

    NO_DEFAULTS(TemporalPoolerNode);
  };
}

//--------------------------------------------------------------------------------
#endif // NTA_TEMPORAL_POOLER_NODE2_HPP
