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
 * Implementation for TemporalPoolerNode
 */

#include <sstream>
#include <nta/math/array_algo.hpp>
#include <nta/regions/TemporalPoolerNode.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/engine/Input.hpp>
#include <nta/engine/Region.hpp>
#include <nta/ntypes/NodeSet.hpp>
#include <nta/utils/StringUtils.hpp>

#ifdef WIN32
#include <windows.h>
#endif

// Set this to 1 to have the plug-in wait for a gdb attach 
// at the beginning of init(). This
// is useful when you need to single-step through the init() 
// function when it is called
// from the tools during initial network creation. 
#define WAIT_GDB_ATTACH_INIT  0

// Current, equalizeGroupSize is translated into two
// different values of largeGroupPenalty
#define LGP_EQUALIZE_GROUP_SIZE_FALSE  1
#define LGP_EQUALIZE_GROUP_SIZE_TRUE  10

//--------------------------------------------------------------------------------

using namespace std;
namespace nta
{

//--------------------------------------------------------------------------------
const std::string TemporalPoolerNode::current_temporal_pooler_node_version_ =
  "TemporalPoolerNode_1.8";



Spec* TemporalPoolerNode::createSpec()
{
  Spec *ns = new Spec;

  ns->description = 
        "The temporal pooler finds temporal transitions between the outputs\n"
        "of its children. It then uses those temporal transitions to compute "
        "temporal groups \n"
        "that cluster the inputs together in time.\n"
        "The temporal pooler has two modes of operation: \"learning\" and "
        "\"inference\".\n"
        "In \"learning\" mode, it learns temporal transitions in its input space \n"
        "and in \"inference\" mode, it produces an output that reflects its current \n"
        "degree of membership in each temporal group, based on either the current "
        "input\n"
        "or the sequence of inputs received until that point.\n"
        "The temporal groups are computed when switching to inference.\n"
        "The temporal pooler is controlled by the parameters below.\n"
        "Additional documentation is available in NodeAlgorithmsGuide.pdf, "
    "located in $NTA/share/docs.";


  ns->inputs.add(
    "bottomUpIn", 
    InputSpec(
      "The input to this node from children nodes. "
      "It is a vector of reals.",
      NTA_BasicType_Real, 
      0, 
      true, // required?
      false, // isRegionLevel, 
      true   // is DefaultInput
      ));
      


  ns->inputs.add(
    "topDownIn", 
    InputSpec( 
      "The input to this node from nodes above. "
      "It is a vector of reals.",
      NTA_BasicType_Real,
      0, 
      false, // required?
      false, // isRegionLevel, 
      false  // is DefaultInput
      ));
  
  ns->inputs.add(
    "resetIn", 
    InputSpec(
      "When the temporal pooler receives a reset signal on resetIn,\n"
      "it will reset its learning history when in learning mode,\n"
      "and the TBI history when in inference mode.", 
      NTA_BasicType_Real, 
      0, 
      false, // required?
      true,  // isRegionLevel, 
      false  // is DefaultInput
      ));

  ns->outputs.add(
    "bottomUpOut", 
    OutputSpec(
      "The bottom-up output of the temporal pooler is a vector of reals.\n"
      "For each group, it represents the likelihood that the input \n"
      "belongs to that group. The size of this output must be\n"
      "greater than or equal to the requestedGroupCount parameter.",
      NTA_BasicType_Real, 
      0,     // count
      false, // isRegionLevel, 
      true   // is DefaultOutput
      ));


  ns->outputs.add(
    "topDownOut", 
    OutputSpec(
      "The top-down output of the temporal pooler is a vector of reals.\n",
      NTA_BasicType_Real, 
      0,     // count
      false, // isRegionLevel, 
      false   // is DefaultOutput
      ));


  ns->commands.add(
    "computeGroups", 
    CommandSpec("Compute the groups.")
    );

  ns->commands.add(
    "reset", 
    CommandSpec("Reset the history of the temporal pooler.")
    );

  ns->commands.add(
    "sampleFromGroup", 
    CommandSpec("Sample sequences from a given group.\n"
                "*** THIS COMMAND WORKS ONLY WITH TBI ***\n"
                "It takes four arguments: group index, number of steps forward,\n"
                "algorithm (one of 'distribution', 'single_path_max' or "
                "'single_path_sample'), and an initial distribution.\n"
                "Number of steps forward, algorithm and initial distribution\n"
                "are optional and default to 1, 'single_path_sample' and 'none'.\n"
                "If the initial distribution is specified, it is a distribution\n"
                "over the coincidences of the specified group index, and therefore\n"
                "has as many elements as there are coincidences in the group.\n"
                "The returned value is either a full distribution over the coincidences\n"
                "in the group specified, for each step forward, or a single path\n"
                "expressed as a list of coincidences.")
    );

  ns->commands.add(
    "predict",
    CommandSpec("Predicts the likelihood of coincidences or groups\n"
                "for a certain number of steps in the future.\n"
                "*** THIS COMMAND WORKS ONLY WITH TBI IN INFERENCE ***\n"
                "It takes two arguments: 'coincidences' or 'groups'\n"
                "that indicates whether to return likelihoods for groups\n"
                "or coincidences (default is 'coincidences'), and an integer \n"
                "number of steps to predict (default is 1).\n"
                "It returns a matrix that has as many rows as the number\n"
                "of steps requested, and whose number of columns is either\n"
                "the number of coincidences or the number of groups, depending\n"
                "on the mode.")
    );

  ns->commands.add(
    "nta_computeHOT", 
    CommandSpec("Compute higher-order states during learning."));

  ns->parameters.add(
    "clonedNodes", 
    ParameterSpec("Applicable only when the node is used within a Region. If\n"
                  "true, this specifies that all the nodes in the region will\n"
                  "be clones and will share state.",
                  NTA_BasicType_UInt32, 
                  1, 
                  "enum: 0, 1", 
                  "0",
                  ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "maxGroupCount", 
    ParameterSpec("The maximum number of groups that can be learned", 
                  NTA_BasicType_UInt32, 
                  1, 
                  "interval: (0, ...)", 
                  "10", 
                  ParameterSpec::CreateAccess
      ));
  
  ns->parameters.add(
    "nta_phaseIndex",
    ParameterSpec("The scheduler phase.",
                  NTA_BasicType_UInt32,
                  1, 
                  "", 
                  "",
                  ParameterSpec::ReadWriteAccess
      ));
  
  ns->parameters.add(
    "learningMode", 
    ParameterSpec("Whether or not this node is in learning mode.\n"
                  "Turning off learning has the side effect of computing "
                  "groups and turning on inference.",
                  NTA_BasicType_UInt32, 
                  1, 
                  "enum: 0, 1", 
                  "1",
                  ParameterSpec::ReadWriteAccess
      ));


  ns->parameters.add(
    "inferenceMode", 
    ParameterSpec("Whether or not this node is inferring.\n"
                  "Turning on inference has the side effect of computing "
                  "groups and turning off learning.",
                  NTA_BasicType_UInt32, 
                  1,
                  "enum: 0, 1", 
                  "0",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "temporalPoolerAlgorithm", 
    ParameterSpec("The algorithm used by the temporal pooler in inference.",
                  NTA_BasicType_Byte, 
                  0,
                  "enum: maxProp, sumProp, tbi, hardcoded", 
                  "maxProp",
                  ParameterSpec::ReadWriteAccess
      ));
  
  ns->parameters.add(
    "TAM", 
    ParameterSpec("The time adjacency matrix, returned as a sparse matrix.",
                  NTA_BasicType_Byte, 
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));
  
  ns->parameters.add(
    "transitionMemory", 
    ParameterSpec("How far back in time to look for coincidences'\n"
                  "temporal dependencies when learning the TAM.",
                  NTA_BasicType_UInt32, 
                  1,
                  "interval: (0, ...)",
                  "1",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "temporalPoolerHistory", 
    ParameterSpec("The history of the temporal pooler that was accumulated\n"
                  "while learning the TAM.",
                  NTA_BasicType_Byte, 
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "hasTemporalState", 
    ParameterSpec("Whether or not this node has temporal state.",
                  NTA_BasicType_UInt32, 
                  1, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));
  
  ns->parameters.add(
    "temporalState", 
    ParameterSpec("The temporal state of the node. Can be saved and restored\n"
                  "through reading/writing this parameter.",
                  NTA_BasicType_Byte, 
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "equalizeGroupSize", 
    ParameterSpec("Whether the temporal pooler should attempt to form groups that\n"
                  "are roughly equal in size or not.",
                  NTA_BasicType_UInt32, 
                  1,
                  "enum: 0, 1", 
                  "0",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "requestedGroupCount",
    ParameterSpec("Number of groups requested. The temporal pooler will generate\n"
                  "at most that many groups. This number must be less than or equal\n"
                  "to the size of the bottomUpOut output. If set to zero, then it\n"
                  "it is set to the size of the bottomUpOut output.\n",
                  NTA_BasicType_UInt32,
                  1,
                  "interval: [0, ...)", 
                  "0",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "coincidenceCount",
    ParameterSpec("Number of coincidences observed.",
                  NTA_BasicType_UInt32,
                  1, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "groupCount",
    ParameterSpec("Number of groups actually generated. This might be less than\n"
                  "the requested number of groups if a small number of coincidences\n"
                  "are seen during training.",
                  NTA_BasicType_UInt32,
                  1, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "groups",
    ParameterSpec("The computed groups.",
                  NTA_BasicType_Byte,
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "activeOutputCount",
    ParameterSpec("The number of active elements in bottomUpOut. For this node type\n"
                  "this is the same as groupCount",
                  NTA_BasicType_UInt32,
                  1, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "coincidenceVectorCounts",
    ParameterSpec("An array of the number of the frequency count of each\n"
                  "coincidence seen by the temporal pooler.",
                  NTA_BasicType_UInt32,
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "sequencerWindowCount",
    ParameterSpec("The number of windows over which the sequencer "
                  "will build a sequence model.",
                  NTA_BasicType_UInt32,
                  1, 
                  "interval: [0, ...)", 
                  "1",
                  ParameterSpec::CreateAccess
      ));


  ns->parameters.add(
    "sequencerWindowLength",
    ParameterSpec(
                   "The number of iterations in each window where "
                   "the sequencer will build a sequence model.",
                   NTA_BasicType_UInt32,
                   1,
                   "interval: [1, ...)", 
                   "1",
                   ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "sequencerModelComplexity", 
    ParameterSpec("The complexity of the sequence model built "
                  "by the sequencer.", 
                  NTA_BasicType_Real32,
                  1, 
                   // "interval: [0.0, 1.0]", "0.1");
                  "", 
                  "0.1",
                  ParameterSpec::ReadWriteAccess
      ));
                  
  ns->parameters.add(
    "nta_segmentSize", 
    ParameterSpec("The size of the segments.",
                  NTA_BasicType_UInt32,
                  1, 
                  "", 
                  "0",
                  ParameterSpec::CreateAccess
      ));


  ns->parameters.add(
    "nta_patchMasks",
    ParameterSpec("Ignored information about the source of the segments.",
                  NTA_BasicType_UInt32,
                  0, 
                  "", 
                  "",
                  ParameterSpec::CreateAccess
      ));

    
  ns->parameters.add(
    "nta_expandedTAM",
    ParameterSpec("The expanded TAM.",
                  NTA_BasicType_Byte,
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "nta_expandedCoincidenceVectorCounts",
    ParameterSpec("Coincidence vector counts for the expanded TAM.",
                  NTA_BasicType_UInt32,
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "nta_expandedGroups",
    ParameterSpec("Computed groups for the expanded TAM.",
                  NTA_BasicType_Byte,
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "nta_rescaleTBI",
    ParameterSpec("Boolean flag whether TBI inference should be "
                  "rescaled to match the maximum value of the input. "
                  "True by default.",
                  NTA_BasicType_UInt32,
                  1, 
                  "interval: [0, 1]", 
                  "1",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "nta_cache_hot",
    ParameterSpec("Whether to do cached HOT or not.",
                  NTA_BasicType_UInt32,
                  1,
                  "enum: 0,1", 
                  "0",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "nta_sequencer_maxPerStage",
    ParameterSpec("Max number of sequencer states per window.",
                  NTA_BasicType_UInt32,
                  1,
                  "interval: [-1, ...)", 
                  "100",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "nta_sequencer_maxCoincidenceSplitsPerRound",
    ParameterSpec("Max number of splits per unique coincidence per HOT round.",
                  NTA_BasicType_UInt32,
                  1, 
                  "", 
                  "0",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "nta_sequencer_handleSelfTransitions",
    ParameterSpec("Whether to treat self transitions specially.",
                  NTA_BasicType_UInt32,
                  1,
                  "interval: [0, 1]", 
                  "0",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "nta_sequencer_nStates",
    ParameterSpec("Number of sequencer states.",
                  NTA_BasicType_UInt32,
                  1, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "nta_sequencer_s2c",
    ParameterSpec("Sequencer S2C",
                  NTA_BasicType_UInt32,
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "nta_sequencer_c2s",
    ParameterSpec("Sequencer C2S",
                  NTA_BasicType_Byte,
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "nta_largeGroupPenalty", 
    ParameterSpec("Large group penalty used in grouping. The larger the value\n"
                  "the more similar the sizes of the groups.",
                  NTA_BasicType_Real, 
                  1, 
                  "interval: [-1, ...)", 
                  "-1",
                  ParameterSpec::ReadWriteAccess
      ));
  
  ns->parameters.add(
    "nta_tbiCellOutputs", 
    ParameterSpec("The TBI cell output vectors. Returned as a count of number\n"
                  "of groups followed by a vector for each group.",
                  NTA_BasicType_Byte, 
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "nta_tbiCellWeights", 
    ParameterSpec("The TBI cell weight matrices. Returned as a count of\n"
                  "number of groups followed by a sparse matrix for each group.",
                  NTA_BasicType_Byte, 
                  0, 
                  "", 
                  "",
                  ParameterSpec::ReadOnlyAccess
      ));

  return ns;
}



//--------------------------------------------------------------------------------
TemporalPoolerNode::TemporalPoolerNode(const ValueMap& params, Region *region)

  : RegionImpl(region), 
    mode_(Learning),
    phaseIndex_(0),
    clonedNodes_(true),
    nodeCount_(1),
    requestedGroupCount_(1),
    maxGroupCount_(1),
    resetInput_(NULL),
    bottomUpInput_(NULL),
    topDownInput_(NULL),
    bottomUpOutArray_(NTA_BasicType_Real32),
    topDownOutArray_(NTA_BasicType_Real32),
    poolers_(),
    iteration_(1),
    cache_hot_(false),
    winner_cache_(),
    reset_cache_()
{
  
  waitDebuggerAttach_();
  
  OMemStream str;

  string algo = *params.getString("temporalPoolerAlgorithm");
  UInt32 hot_windowCount = params.getScalarT<UInt32>("sequencerWindowCount");
  UInt32 hot_iterPerStage = params.getScalarT<UInt32>("sequencerWindowLength");
  Real32 hot_min_cnt2 = params.getScalarT<Real32>("sequencerModelComplexity");
  UInt32 hot_maxPerStage = params.getScalarT<UInt32>("nta_sequencer_maxPerStage");
  UInt32 hot_maxCoincidenceSplitsPerRound = 
    params.getScalarT<UInt32>("nta_sequencer_maxCoincidenceSplitsPerRound");
  UInt32 hot_handleSelf = 
    params.getScalarT<UInt32>("nta_sequencer_handleSelfTransitions");

  UInt32 iRescaleTBI = params.getScalarT<UInt32>("nta_rescaleTBI");
  NTA_CHECK((iRescaleTBI == 0) || (iRescaleTBI == 1));
  bool rescaleTBI = iRescaleTBI;
      
  maxGroupCount_ = params.getScalarT<UInt32>("maxGroupCount");
  requestedGroupCount_ = params.getScalarT<UInt32>("requestedGroupCount");
  if (requestedGroupCount_ == 0)
    requestedGroupCount_ = maxGroupCount_;

  // If largeGroupPenalty has been set, ignore equalizeGroupSize
  // Otherwise, use equalizeGroupSize to set largeGroupPenalty
  Real32 largeGroupPenalty = params.getScalarT<Real32>("nta_largeGroupPenalty");
  if (largeGroupPenalty == (Real) -1) {
    // largeGroupPenalty not specified -> use equalizeGroupSize
    if (params.getScalarT<UInt32>("equalizeGroupSize"))
    {
      largeGroupPenalty = LGP_EQUALIZE_GROUP_SIZE_TRUE;
    }
    else
    {
      largeGroupPenalty = LGP_EQUALIZE_GROUP_SIZE_FALSE;
    }
  }
  UInt32 segmentSize = params.getScalarT<UInt32>("nta_segmentSize");


  // ---
  // Create one grouper now -- if not cloned, we will create more
  // in initialize(), when we know how many nodes we have
  // 
  // topNeighbors, maxGroupSize and overlappingGroups are used 
  // only in Grouper::group(), which we never call.
  // maxGroupCount is not used directly in Grouper. Instead, 
  // we call AHCGroup(maxGroupCount)
  // 
  // symmetricTime is in fact not ignored if we call predict()
  // (it is also used in group()).
  // ---
  poolers_.push_back(new Grouper(
                       params.getScalarT<UInt32>("transitionMemory"), 
                       1, // topNeighbors, will be ignored 
                       1, // maxGroupCount, will be ignored
                       1, // maxGroupSize, will be ignored
                       false, // symmetricTime, will be ignored
                       false, // overlappingGroups, will be ignored
                       largeGroupPenalty, // set above
                       Grouper::convertMode(algo),
                       hot_windowCount,
                       hot_min_cnt2,
                       hot_iterPerStage,
                       hot_maxPerStage,
                       hot_maxCoincidenceSplitsPerRound,
                       hot_handleSelf,
                       1, // n_tbis
                       segmentSize,
                       rescaleTBI));


}

TemporalPoolerNode::TemporalPoolerNode(BundleIO& bundle, Region* region) : 
  RegionImpl(region), 
  bottomUpOutArray_(NTA_BasicType_Real32),
  topDownOutArray_(NTA_BasicType_Real32)

{
  NTA_THROW << "TemporalPoolerNode deserialization not implemented yet";
}


//--------------------------------------------------------------------------------
TemporalPoolerNode::~TemporalPoolerNode()
{
  for (UInt i = 0; i != poolers_.size(); ++i) {
    delete poolers_[i];
    poolers_[i] = NULL;
  }
}

void TemporalPoolerNode::serialize(BundleIO& bundle)
{
  NTA_THROW << "TemporalPoolerNode::serialize not implemented yet";
}

void TemporalPoolerNode::deserialize(BundleIO& bundle)
{
  NTA_THROW << "TemporalPoolerNode::deserialize not implemented yet";
}




//--------------------------------------------------------------------------------
void TemporalPoolerNode::initialize()
{
  
  NTA_CHECK(region_ != NULL);

  bottomUpInput_ = region_->getInput("bottomUpIn");
  if (bottomUpInput_->getData().getCount() == 0)
  {
    NTA_THROW << "Unable to initialize TemporalPooler Region '"
              << region_->getName() << "' because bottom up input is not linked";
  }

  resetInput_ = region_->getInput("resetIn");
  if (resetInput_->getData().getCount() == 0)
  {
    resetInput_ = NULL;
  }
  
  topDownInput_ = region_->getInput("topDownIn");
  if (topDownInput_->getData().getCount() == 0)
  {
    topDownInput_ = NULL;
  }

  bottomUpOutArray_ = region_->getOutputData("bottomUpOut");
  topDownOutArray_ = region_->getOutputData("topDownOut");

  nodeCount_ = region_->getDimensions().getCount();
  UInt grouperCount = clonedNodes_ ? 1 : nodeCount_;
  NTA_CHECK(nodeCount_ > 0);


  if (clonedNodes_)
  {
    NTA_CHECK(poolers_.size() == 1);
    // If we're cloned, the pooled needs to 
    // keep track of TBI separately. 
    poolers_[0]->setNTBIs(nodeCount_);
  } else 
  {
    // not cloned
    NTA_CHECK(poolers_.size() == 1 || poolers_.size() == grouperCount);
    if (poolers_.size() == 1)
    {
      // Clone the initial pooler created in the constructor
      stringstream buf;
      poolers_[0]->saveState(buf);
      for (UInt i = 1; i < grouperCount; ++i) {
        poolers_.push_back(new Grouper(buf));
      }
    } 
  }

  

  iteration_ = 1;
  cache_hot_ = false;

}

//--------------------------------------------------------------------------------
void TemporalPoolerNode::compute()
{
  // Reset might not be connected, in which case
  // we will ignore that input.
  Real reset = resetInput_ ? *(Real*)(resetInput_->getData().getBuffer()) : (Real) 0;
  bool compute_hot = true;
  Real* td_out_begin = 0, *td_out_the_end = 0;

  ++iteration_;

  std::vector<Real32> buInputVec, tdInputVec;

  for (NodeSet::const_iterator i = getEnabledNodes().begin(); 
       i != getEnabledNodes().end(); i++)
  {
    size_t node = *i;
    bottomUpInput_->getInputForNode(node, buInputVec);

    Real* out = (Real*) bottomUpOutArray_.getBuffer() + node * maxGroupCount_;

    // We figure out the baby pooler to invoke, and the baby_idx.
    // Note how the expressions are opposite from each other.
    // baby_idx is needed to address the dynamic data structures
    // in the Grouper for TBI and/or TAM learning (there is one 
    // separate TAM history for each baby node, even if cloned).
    Grouper* pooler = clonedNodes_ ? poolers_[0] : poolers_[node];
    UInt baby_idx = clonedNodes_ ? (UInt) node : (UInt) 0;

    if (mode_ == Learning) {
      if (pooler->getMode() == Grouper::hardcoded)
        continue;

      // If reset, we reset the history and continue learning.
      // This will have the effect of populating the history
      // with a winner, but the TAM won't be updated (because
      // the transition history is empty).
      if (reset > 0) 
        pooler->resetHistory();

      // Decide whether to augment the Markov graph or not.
      // If clonedNodes_ we need to call hot() only once,
      // regardless of what baby node(s) are enabled...
      if (!cache_hot_ && compute_hot) {
        if (clonedNodes_) {
          if (pooler->getTam().computeHOT(iteration_)) {
            NTA_INFO << "Computing higher-order state splits on iteration "
                     << iteration_;
            pooler->getTam().hot();
          }
          compute_hot = false;
        } else {
          if (pooler->getTam().computeHOT(iteration_)) {
            NTA_INFO << "Computing higher-order state splits on iteration "
                     << iteration_;
            pooler->getTam().hot();
          }
          // don't set compute_hot!
        }
      }
      
      UInt winner = (UInt) (max_element(buInputVec.begin(), buInputVec.end()) - buInputVec.begin());

      if (cache_hot_) {
        winner_cache_.push_back(winner);
        reset_cache_.push_back(reset > 0);
      }

      pooler->learn(&winner, out, baby_idx);
      
    } else if (mode_ == Inference) {

      // If reset, we reset the TBI history,
      // but we continue inferring.
      if (reset > 0) 
        pooler->resetTBIHistory();

      if (phaseIndex_ == 0) {

	pooler->infer(buInputVec.begin(), buInputVec.end(), out, baby_idx);

      } else {
	
	NTA_CHECK(poolers_[0]->getMode() == Grouper::hardcoded)
	  << "Top down inference works only with harcoded temporal poolers";

        NTA_CHECK(topDownInput_ != NULL);

        topDownInput_->getInputForNode(node, tdInputVec);
        Real* td_out = (Real*) bottomUpOutArray_.getBuffer() + node * maxGroupCount_;
	Real* td_out_end = td_out + maxGroupCount_;

	td_out_the_end = td_out_end;

	pooler->topDownInfer(buInputVec.begin(),  buInputVec.end(), tdInputVec.begin(), tdInputVec.end(), td_out, td_out_end);
      }
    }
  }

  // Top-down only
  if (mode_ == Inference && phaseIndex_ == 1) {
    NTA_CHECK(poolers_[0]->getMode() == Grouper::hardcoded)
      << "Top down inference works only with hardcoded temporal poolers";
    nta::divide_by_max(td_out_begin, td_out_the_end);
  }
}

//--------------------------------------------------------------------------------
void TemporalPoolerNode::saveState(IWriteBuffer& state)
{
  // TemporalPoolerNode <clonedNodes> <numNodes> <nodeMode> [<stateSize> <state>]...
  
  UInt grouperCount = clonedNodes_ ? 1 : nodeCount_;

  OMemStream str;
  str << current_temporal_pooler_node_version_ << " "
      << (UInt32) clonedNodes_ << " "
      << (UInt32) grouperCount << " " // *recomputed* in init
      << (UInt32) mode_ << " "
      << (UInt32) requestedGroupCount_ << " ";

  for (UInt i = 0; i != grouperCount; ++i) {
    poolers_[i]->saveState(str);
    str << " ";
  }

  state.write(str.str(), (UInt32) str.pcount());
}

// ---
// String parameters have to be handled separately because they can't be used in 
// the generic buffer interface
// ---
void TemporalPoolerNode::setParameterString(const std::string& paramName, Int64 index, const std::string& s)
{
  if (paramName == "nta_tbiCellOutputs" || 
      paramName == "temporalState" ||
      paramName == "nta_tbiCellWeights" ||
      paramName == "nta_sequencer_c2s" ||
      paramName == "nta_expandedGroups" ||
      paramName == "nta_expandedTAM" ||
      paramName == "temporalState" || 
      paramName == "TemporalPoolerHistory")
  {
    NTA_THROW << "TemporalPoolerNode::setParameter -- parameter '" << paramName 
              << "' is not supported in NuPIC 2";
  }



  if (index == -1 && !clonedNodes_)
  {
    NTA_THROW << "Attempt to access parameter '" << paramName 
              << "' on region " << region_->getName()
              << " but the parameter is not region-level";
  }
      
  Int64 realIndex = index;
  if (index == -1)
    realIndex = 0;


  if (paramName == "temporalPoolerAlgorithm") {
    poolers_[realIndex]->setModeFromStr(s);
  } else {
    NTA_THROW << "Unknown string parameter '" << paramName << "'";
  }

  // --- 
  // All of these parameters are pickled python objects.
  // Leave them that way (too hard to convert for NuPIC 2) 
  // even though they should technically be of type Handle
  // Turns out that most are not used in vision problems
  // so we are dropping support entirely. 

  // groups (this is the only one we keep)
  // TemporalPoolerHistory
  // temporalState
  // nta_expandedTAM
  // nta_expandedGroups
  // nta_sequencer_c2s
  // nta_tbiCellOutputs
  // nta_tbiCellWeights
  // ---
}

void TemporalPoolerNode::getParameterArray(const std::string& paramName, Int64 index, Array & array)
{
  UInt poolerIndex = index;
  if (clonedNodes_)
    poolerIndex = 0;

  if (paramName == "coincidenceVectorCounts") {
    std::vector<UInt> counts = poolers_[poolerIndex]->getCollapsedTAM().getRowCounts();
    // todo: not an internal error. use NTA_THROW
    NTA_CHECK(array.getType() == NTA_BasicType_UInt32);
    array.allocateBuffer(counts.size());
    UInt32 *buf = (UInt32*) array.getBuffer();
    for (UInt k = 0; k != counts.size(); ++k)
      buf[k] = counts[k];
  } else { 
    NTA_THROW << "TemporalPoolerNode::getParameterArray -- unknown parameter '" << paramName << "'";
  }

}





std::string TemporalPoolerNode::getParameterString(const std::string& paramName, Int64 index)
{
  if (paramName == "nta_tbiCellOutputs" || 
      paramName == "temporalState" ||
      paramName == "nta_tbiCellWeights" ||
      paramName == "nta_sequencer_c2s" ||
      paramName == "nta_expandedGroups" ||
      paramName == "nta_expandedTAM" ||
      paramName == "temporalState" || 
      paramName == "TemporalPoolerHistory")
  {
    NTA_THROW << "TemporalPoolerNode::getParameter -- parameter '" << paramName 
              << "' is not supported in NuPIC 2";
  }


  UInt poolerIndex = index;
  if (clonedNodes_)
    poolerIndex = 0;

  if (paramName == "TAM") {       
          // Collapsed TAM, without added HOT states
    OMemStream buf;
    poolers_[poolerIndex]->getCollapsedTAM().toCSR(buf);
    return buf.str();
  } else if (paramName == "temporalPoolerAlgorithm") {
    return poolers_[poolerIndex]->getModeStr();
  } else {
    NTA_THROW << "Unknown parameter '" << paramName << "'";
  }

}




void TemporalPoolerNode::setParameterFromBuffer(const std::string& name, Int64 index, IReadBuffer& buf)
{
  const char* where = "TemporalPoolerNode, while setting parameter: ";

  const string paramName(name);
  Int32 int_param = 0;
  UInt32 uint_param = 0;
  Real float_param = (Real) 0;

  try {
    
    // params that are always region-level
    if (paramName == "learningMode") {

      buf.read(uint_param);
      mode_ = (uint_param == 1) ? Learning : Inference;
      if (mode_ == Inference) 
        switchToInference_();

    } else if (paramName == "inferenceMode") {

      buf.read(uint_param);
      mode_ = (uint_param == 1) ? Inference : Learning;
      if (mode_ == Inference) 
        switchToInference_();

    } else if (paramName == "nta_phaseIndex") {

      buf.read(uint_param);
      phaseIndex_ = uint_param;

    } else {

      // All of these params are region-level if
      // clonedNodes_ otherwise they are node level
      if (!clonedNodes_ && index < 0)
      {
        NTA_THROW << "Attempt to access parameter '" << paramName 
                  << "' of region " << region_->getName() 
                  << " as a region-level parameter but region is not cloned";
      }

      UInt poolerIndex = index;
      if (clonedNodes_)
        poolerIndex = 0;

      if (paramName == "transitionMemory") {
        buf.read(uint_param);
        poolers_[poolerIndex]->setTransitionMemory(uint_param);

      } else if (paramName == "sequencerModelComplexity") {
        buf.read(float_param);
        poolers_[poolerIndex]->getTam().setHOTMinCnt2(float_param);

      } else if (paramName == "nta_sequencer_maxPerStage") {
        buf.read(int_param); // Allow -1!
        poolers_[poolerIndex]->getTam().setHOTMaxPerStage(int_param);

      } else if (paramName == "nta_sequencer_maxCoincidenceSplitsPerRound") {
        buf.read(uint_param);
        poolers_[poolerIndex]->getTam().setHOTMaxCoincidenceSplitsPerRound(uint_param);

      } else if (paramName == "nta_sequencer_handleSelfTransitions") {
        buf.read(uint_param);
        poolers_[poolerIndex]->getTam().setHOTHandleSelfTransitions(uint_param);

      } else if (paramName == "equalizeGroupSize") {
        buf.read(uint_param);
        int largeGroupPenalty = LGP_EQUALIZE_GROUP_SIZE_FALSE;
        if (uint_param)
          largeGroupPenalty = LGP_EQUALIZE_GROUP_SIZE_TRUE;
        poolers_[poolerIndex]->setAHCLargeGroupPenalty(largeGroupPenalty);

      } else if (paramName == "requestedGroupCount") {
        buf.read(uint_param);
        requestedGroupCount_ = uint_param;
          
      } else if (paramName == "nta_largeGroupPenalty") {
        buf.read(float_param);
        poolers_[poolerIndex]->setAHCLargeGroupPenalty(float_param);

      } else if (paramName == "nta_rescaleTBI") {
        buf.read(uint_param);
        NTA_CHECK((uint_param == 0) || (uint_param == 1))
          << "nta_rescaleTBI must be 0 or 1.";
        poolers_[poolerIndex]->setRescaleTBI(uint_param);

      } else if (paramName == "nta_cache_hot") {
        cache_hot_ = true;
          
      } else {
        NTA_THROW << "Unknown parameter '" << paramName << "' on region "
                  << region_->getName() << " of type " << region_->getType();
      }
    }
  } catch (std::exception& e) {
    NTA_THROW << where << "Couldn't set " << paramName
              << ": " << e.what();
  }
}

//--------------------------------------------------------------------------------
void TemporalPoolerNode::getParameterFromBuffer(const std::string& name, Int64 index, IWriteBuffer& value)
{
  const char* where = "TemporalPoolerNode, while getting parameter: ";

  const string paramName(name);
  
  try {

    // The first parameters are always region-level. Ignore the index
    if (paramName == "learningMode") {

      value.write(UInt32(mode_ == Learning ? 1 : 0));

    } else if (paramName == "inferenceMode") {

      value.write(UInt32(mode_ == Learning ? 0 : 1));

    } else if (paramName == "clonedNodes") {

      value.write((UInt32) (clonedNodes_ ? 1 : 0));

    } else if (paramName == "nta_phaseIndex") {

      value.write((UInt32) phaseIndex_);

    } else {

        UInt poolerIndex = clonedNodes_ ? 0 : (UInt) index;

        OMemStream  buf;
    
        if (paramName == "transitionMemory") {
          buf << (UInt32) poolers_[poolerIndex]->getTransitionMemory();

        } else if (paramName == "nta_segmentSize") {
          value.write((UInt32) poolers_[poolerIndex]->getSegmentSize());
        
        } else if (paramName == "nta_patchMasks") {
          // Leave an empty string.
        
        } else if (paramName == "nta_largeGroupPenalty") {
          buf << (Real32) poolers_[poolerIndex]->getAHCLargeGroupPenalty();
        
        } else if (paramName == "equalizeGroupSize") {
          if (poolers_[poolerIndex]->getAHCLargeGroupPenalty() == 
              LGP_EQUALIZE_GROUP_SIZE_TRUE)
            buf << (Real32) 1;
          else
            buf << (Real32) 0;

        } else if (paramName == "coincidenceCount") {
          const Grouper::IntegerTAM &t = poolers_[poolerIndex]->getTam();
          buf << (UInt32) (t.nRows() - t.getHOTNStates());
          
        } else if (paramName == "requestedGroupCount") {
          buf << (UInt32) requestedGroupCount_;

        } else if (paramName == "groupCount" || paramName == "activeOutputCount") {
          buf << (UInt32) poolers_[poolerIndex]->getNGroups();

        } else if (paramName == "groups") {
          poolers_[poolerIndex]->getGroupsString(buf);



        } else if (paramName == "hasTemporalState") {

          buf << (UInt32) (poolers_[poolerIndex]->getMode() == Grouper::tbi);

        } else if (paramName == "sequencerWindowCount") {
          
          buf << (UInt32) poolers_[poolerIndex]->getTam().getHOTRequestedNRounds();
          
        } else if (paramName == "sequencerWindowLength") {

          buf << (UInt32) poolers_[poolerIndex]->getTam().getHOTIterPerStage();

        } else if (paramName == "sequencerModelComplexity") {
          
          buf << (Real32)  poolers_[poolerIndex]->getTam().getHOTMinCnt2();
        
        } else if (paramName == "nta_sequencer_maxPerStage") {

          buf << (Int32) poolers_[poolerIndex]->getTam().getHOTMaxPerStage();

        } else if (paramName == "nta_sequencer_maxCoincidenceSplitsPerRound") {

          buf << (Int32) poolers_[poolerIndex]->getTam().getHOTMaxCoincidenceSplitsPerRound();

        } else if (paramName == "nta_sequencer_handleSelfTransitions") {

          buf << (Int32) poolers_[poolerIndex]->getTam().getHOTHandleSelfTransitions();

        } else if (paramName == "nta_rescaleTBI") {

          buf << (UInt32) poolers_[poolerIndex]->getRescaleTBI();

	} else if (paramName == "nta_cache_hot") {

	  buf << (UInt32) cache_hot_;

        } else if (paramName == "nta_expandedCoincidenceVectorCounts" ||
                   paramName == "nta_sequencer_s2c" ||
                   paramName == "nta_sequencer_nStates") {
          NTA_THROW << "TemporalPoolerNode -- parameter '" << paramName 
                    << " is not supported in NuPIC 2";
        } else {
          NTA_THROW << "Unknown parameter: " << paramName;
        }
        value.write(buf.str(), buf.pcount());
    }


  } catch (std::exception& e) {
    NTA_THROW << where << "Couldn't retrieve: " << paramName
              << ": " << e.what();
  }
}

//--------------------------------------------------------------------------------
std::string TemporalPoolerNode::executeCommand(const std::vector<std::string>& args, Int64 index)
{

  UInt grp_idx = 0, n_steps = 1;
  Grouper::SamplingMode sampling_mode = Grouper::single_path_sample;
  Grouper::PredictionMode pred_mode = Grouper::coincidences;
  std::vector<std::vector<Real> > future;
  std::vector<Real> initial;
    
  UInt32 poolerIndex = index;
  if (clonedNodes_)
  {
    index = 0;
  }
  else if (index == -1)
  {
    NTA_THROW << "Invalid attempt to execute command '" << args[0] 
              << "' on non-cloned region " << region_->getName();
  } 
    
  // returned value goes in buf
  OMemStream buf;

  if (args[0] == "computeGroups") {
    
    if (args.size() != 2)
      NTA_THROW << "TemporalPoolerNode::executeCommand: computeGroups requires a requested group count";

    requestedGroupCount_ = StringUtils::toUInt32(args[1]);
    computeGroups_(poolerIndex);

  } else if (args[0] == "sampleFromGroup") {

    if (args.size() < 2)
      NTA_THROW << "TemporalPoolerNode::executeCommand: sampleFromGroup requires group index";

    grp_idx = StringUtils::toUInt32(args[1]);
    
    // Read in n_steps and dimension future
    // n_steps is optional, default is 1
    if (args.size() > 2)
      n_steps = StringUtils::toUInt32(args[2]);

    future.resize(n_steps);

    // Read in sampling mode (optional)
    if (args.size() > 3)
    {
      std::string sampling_mode_str = args[3];
      if (sampling_mode_str == "distribution")
        sampling_mode = Grouper::distribution;
      else if (sampling_mode_str == "single_path_sample")
        sampling_mode = Grouper::single_path_sample;
      else if (sampling_mode_str == "single_path_max")
        sampling_mode = Grouper::single_path_max;
      else
        NTA_THROW << "TemporalPoolerNode sampleFromGroup: "
                  << "Unknown mode: " << sampling_mode_str;
    }

    for (size_t i = 4; i < args.size(); i++)
    {
      initial.push_back(StringUtils::toInt32(args[i]));
    }

    poolers_[poolerIndex]->sampleFromGroup(grp_idx, sampling_mode, initial, future);
    for (UInt k = 0; k != future.size(); ++k) 
      for (UInt kk = 0; kk != future[k].size(); ++kk) 
        buf << future[k][kk] << " ";



  } else if (args[0] == "predict") {

    if (args.size() < 2)
      NTA_THROW << "TemporalPoolerNode::executeCommand: predict requires number of steps forward to predict";

    n_steps = StringUtils::toUInt32(args[1]);
    future.resize(n_steps);

    if (args.size() > 1)
    {
      std::string pred_mode_str = args[1];
      if (pred_mode_str == "coincidences")
        pred_mode = Grouper::coincidences;
      else if (pred_mode_str == "groups")
        pred_mode = Grouper::groups;
      else
        NTA_THROW << "TemporalPoolerNode predict: "
                  << "Unknown mode: " << pred_mode_str;
    }

    Int32 nodeIndex = index;
    if (nodeIndex == -1)
      NTA_THROW << "Prediction must be invoked at the node level, not the region level";

    poolers_[poolerIndex]->predict(nodeIndex, pred_mode, future);
    
    for (UInt k = 0; k != future.size(); ++k) 
      for (UInt kk = 0; kk != future[k].size(); ++kk) 
        buf << future[k][kk] << " ";

  } else if (args[0] == "reset") {
      if (mode_ == Learning) {
        poolers_[poolerIndex]->resetHistory();
      } else if (mode_ == Inference) {
        poolers_[poolerIndex]->resetTBIHistory();
      }
  } else if (args[0] == "nta_computeHOT") {
      NTA_CHECK(mode_ == Learning)
        << "Only able to compute higher-order states while in learning mode.";
        
      if (poolers_[poolerIndex]->getTam().getHOTRequestedNRounds() < 1)
        poolers_[poolerIndex]->getTam().setHOTNRounds(1);
      poolers_[poolerIndex]->getTam().hot();

  } else {
    NTA_THROW << "TemporalPoolerNode::executeCommand -- unknown command: " << args[0];
  }

  return buf.str();

}

//--------------------------------------------------------------------------------
void TemporalPoolerNode::computeGroups_(UInt poolerIndex)
{
  UInt trace = 0;

  NTA_CHECK(poolers_[poolerIndex]->getTam().nNonZeroRows() > 0)
    << "TemporalPoolerNode: Can't switch to inference, "
    << " node " << poolerIndex << " didn't learn.";

  if (trace) {
    cout << "Baby pooler #" << poolerIndex << endl;
    cout << "Requested: " << requestedGroupCount_ << " groups" << endl;
    cout << "tam nnzr= " << poolers_[poolerIndex]->getTam().nNonZeroRows() << endl;
    cout << "maxGroupCount_= " << maxGroupCount_ << endl;
  }

  UInt nGroups = max((UInt32) 1, requestedGroupCount_);
  nGroups = min(nGroups, poolers_[poolerIndex]->getTam().nNonZeroRows());
  nGroups = min(nGroups, maxGroupCount_);

  if (trace) {
    cout << "Will produce: " << nGroups << " groups" << endl;
  }

  poolers_[poolerIndex]->AHCGroup(nGroups);

  NTA_CHECK(poolers_[poolerIndex]->getNGroups() <= maxGroupCount_)
    << "TemporalPoolerNode: Computed " << poolers_[poolerIndex]->getNGroups()
    << " but there are only " << maxGroupCount_ << " outputs";
}

//--------------------------------------------------------------------------------
void TemporalPoolerNode::switchToInference_()
{
  if (cache_hot_) {
    UInt n = poolers_[0]->getTam().getHOTRequestedNRounds();
    for (UInt i = 0; i != n+1; ++i) {
      for (UInt j = 0; j != winner_cache_.size(); ++j) {
        for (UInt k = 0; k != poolers_.size(); ++k) {
          if (poolers_[k]->getTam().usesHOT()) {
            if (reset_cache_[j])
              poolers_[k]->getTam().resetHistory();
            poolers_[k]->getTam().learn(winner_cache_[j]);
          }
        }
      }
      if (i != n) {
        for (UInt k = 0; k != poolers_.size(); ++k) 
          poolers_[k]->getTam().hot();
      }
    }
  }

  for (UInt i = 0; i != poolers_.size(); ++i) {
    
    if (poolers_[i]->getTam().usesHOT())
      poolers_[i]->getTam().cleanOrphans();

    if (poolers_[i]->getMode() != Grouper::hardcoded)
      computeGroups_(i);
  }

  mode_ = Inference;
}

//--------------------------------------------------------------------------------
void TemporalPoolerNode::waitDebuggerAttach_()
{
  if (WAIT_GDB_ATTACH_INIT) {
#ifdef WIN32
    DWORD pid = ::GetCurrentProcessId();
#else
    pid_t pid = ::getpid();
#endif
    NTA_DEBUG << "TemporalPoolerNode Waiting for connect to process ID " 
              <<  pid << "...";
    string str;
    cin >> str;
    NTA_DEBUG << "Connected.";
  } 
}

//--------------------------------------------------------------------------------


size_t TemporalPoolerNode::getNodeOutputElementCount(const std::string& outputName)
{
  // TODO: add top down output? 
  if (outputName == "bottomUpOut")
    return maxGroupCount_;
  return 0;
}


}

