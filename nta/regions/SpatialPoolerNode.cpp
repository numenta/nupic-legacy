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
 * Implementation for SpatialPoolerNode
 */

#include <sstream>

// #include <nta/math/helpers.hpp>
#include <nta/regions/SpatialPoolerNode.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/engine/Region.hpp>
#include <nta/ntypes/NodeSet.hpp>
#include <nta/ntypes/BundleIO.hpp>
#include <nta/math/array_algo.hpp>

#ifdef WIN32
#include <windows.h>
#endif

// Set this to 1 to have the plug-in wait for a gdb attach at the beginning of init(). This
// is useful when you need to single-step through the init() function when it is called
// from the tools during initial network creation. 
#define WAIT_GDB_ATTACH_INIT  0
  
//--------------------------------------------------------------------------------

using namespace std;
namespace nta
{

Spec* SpatialPoolerNode::createSpec()
{
  Spec *ns = new Spec;
  
  ns->description = 
    "The spatial pooler finds spatial coincidences patterns between the outputs "
    "from its\n"
    "children. It stores an optionally sparse representation of those spatial "
    "coincidences.\n"
    "The spatial pooler has two modes of operation: \"learning\" and "
    "\"inference\".\n"
    "In \"learning\" mode, it learns relevant coincidence patterns, and in\n"
    "\"inference\" mode, it produces an output by comparing the input\n"
    "pattern against all the stored patterns. The output is a vector that "
    "represents\n"
    "the degree of match of the input pattern to all the stored patterns.\n"
    "The spatial pooler is controlled by the parameters below.\n"
    "Additional documentation is available in NodeAlgorithmsGuide.pdf, "
    "located in $NTA/share/docs.";

  ns->inputs.add(
    "bottomUpIn", 
    InputSpec(
      "The input to this node from children nodes.\n"
      "This input is a vector of reals.", 
      NTA_BasicType_Real32, 
      0, // count. omit?
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
      0, // count. omit?
      false, // required?
      false, // isRegionLevel, 
      false  // is DefaultInput
      ));

  ns->outputs.add(
    "bottomUpOut", 
    OutputSpec(
      "The bottom-up output of this node. It is a vector of reals.\n"
      "In learning mode, it is zero (there is no output).\n"
      "In inference mode, it returns an approximation of the input\n"
      "vector using radial basis functions centered on each learned\n"
      "coincidence. There are therefore as many elements\n"
      "in bottomUpOut as there are coincidences stored in the\n"
      "SpatialPooler.",
      NTA_BasicType_Real32, 
      0, // count
      false, // isRegionLevel
      true   // isDefaultOutput
      ));

  ns->outputs.add(
    "topDownOut", 
    OutputSpec(
      "The top-down output of this node is a vector or reals.\n", 
      NTA_BasicType_Real, 
      0, // count
      false, // isRegionLevel
      false  // isDefaultOutput
      ));


  ns->parameters.add(
    "clonedNodes", 
    ParameterSpec(
      "If true, this specifies that all the nodes in the region will\n"
      "be clones and will share state.",
      NTA_BasicType_UInt32, 
      1,  // count
      "enum: 0, 1", 
      "1", // default = true
      ParameterSpec::CreateAccess
      ));


  ns->parameters.add(
    "nta_phaseIndex",
    ParameterSpec(
      "The scheduler phase.",
      NTA_BasicType_UInt32,
      1, // count
      "", 
      "",
      ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "learningMode", 
    ParameterSpec(
      "Whether or not this node is in learning mode.\n"
      "Turning off learning has the side effect of turning on inference.",
      NTA_BasicType_UInt32,
      1, 
      "enum: 0, 1", 
      "1",
      ParameterSpec::ReadWriteAccess
      ));


  ns->parameters.add(
    "inferenceMode", 
    ParameterSpec(
      "Whether or not this node is inferring.\n"
      "Turning on inference has the side effect of turning off learning.",
      NTA_BasicType_UInt32,
      1, 
      "enum: 0, 1", 
      "0",
      ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    // In NuPIC 1 this was specified as a UInt32 parameter, 
    // but it was accessed everywhere as a string. Also, 
    // it the valid values are actually 0 ("none"), 1 ("kWinners"), 
    // 2 ("threshold") but the constraint looks like a boolean
    // To make SP node work in NuPIC 2, changing to a string 
    // parameter but not changing the constraints. 
    "sparsify",  
    ParameterSpec(
      "Whether to sparsify the input vectors or not.",
      NTA_BasicType_Byte,
      0, 
      // NTA_BasicType_UInt32,
      // 1, 
      "enum: 0, 1", 
      "0",
      ParameterSpec::ReadWriteAccess
      ));


  ns->parameters.add(
    "spatialPoolerAlgorithm", 
    ParameterSpec(
      "The algorithm to use during inference.",
      NTA_BasicType_Byte,
      0, 
      "enum: gaussian,kthroot_product", 
      "gaussian",
      ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "maxDistance",
    ParameterSpec(
      "The max distance between a candidate coincidence and a\n"
      "coincidence, within which the candidate will be considered\n"
      "the same as the coincidence.",
      NTA_BasicType_Real32,
      1, 
      "interval: [0, ...)", 
      "0",
      ParameterSpec::CreateAccess
      ));


  ns->parameters.add(
    "sigma", 
    ParameterSpec(
      "Sigma to be used in the radial-basis function in gaussian\n"
      "inference mode.",
      NTA_BasicType_Real32,
      1, 
      "interval: (0, ...)", 
      "1.0",
      ParameterSpec::CreateAccess
      ));
    
  ns->parameters.add(
    "maxCoincidenceCount", 
    ParameterSpec(
      "The maximum number of coincidences that can be learned\n"
      "by each node in this node.",
      NTA_BasicType_UInt32,
      1, 
      "",
      "",
      ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "coincidenceCount", 
    ParameterSpec(
      "The number of coincidences learned.",
      NTA_BasicType_UInt32,
      1, 
      "",
      "",
      ParameterSpec::ReadOnlyAccess
      ));

  ns->parameters.add(
    "coincidenceMatrix", 
    ParameterSpec(
      "The coincidence matrix, as a sparse matrix.", 
      NTA_BasicType_Handle,
      1,
      "",
      "",
      ParameterSpec::ReadOnlyAccess
      ));
    
  ns->parameters.add(
    "activeOutputCount",
    ParameterSpec(
      "The number of active elements in bottomUpOut.",
      NTA_BasicType_UInt32,
      1, 
      "",
      "",
      ParameterSpec::ReadOnlyAccess
      ));


  ns->parameters.add(
    "nta_patchMasks", 
    ParameterSpec( 
      "The masks that will be used to extract prototypes.", 
      NTA_BasicType_Byte,
      0,
      "",
      "",
      ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "nta_segmentSize", 
    ParameterSpec(
      "The size of the segments for sparsification.", 
      NTA_BasicType_UInt32,
      1,
      "interval: [1, ...)", // in NuPIC 1, 0 was allowed
      "", // must be specified -- no default value
      ParameterSpec::CreateAccess
      ));
    
  ns->parameters.add(
    "nta_normalize",
    ParameterSpec(
      "Whether to normalize the inputs or not.",
      NTA_BasicType_UInt32,
      1, 
      "enum: 0, 1", 
      "0",
      ParameterSpec::ReadWriteAccess
      ));

  ns->parameters.add(
    "nta_norm", 
    ParameterSpec(
      "The value to use for normalization.",
      NTA_BasicType_Real32,
      1,
      "interval: [0, ...)", 
      "2",
      ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "nta_kWinners", 
    ParameterSpec(
      "The number of winners to keep per segment, "
      "when using k-winners sparsification mode.",
      NTA_BasicType_UInt32,
      1,
      "interval: [1, ...)", 
      "1",
      ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "nta_minAcceptNorm", 
    ParameterSpec(
      "The min norm that a candidate prototype should have.",
      NTA_BasicType_Real32,
      1, 
      "interval: [0, ...)", 
      "0",
      ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "nta_minProtoSum", 
    ParameterSpec(
      "The min sum of the components of a prototype.",
      NTA_BasicType_Real32,
      1,
      "interval: [0, ...)",
      "8",
      ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "nta_maxNAttempts", 
    ParameterSpec(
      "The max number of attempts.",
      NTA_BasicType_UInt32,
      1, 
      "interval: [0, ...)", 
      "0",
      ParameterSpec::CreateAccess
      ));

  ns->parameters.add(
    "nta_seed", 
    ParameterSpec(
      "Seed the random number generator used for random coincidence "
      "selection. If equal to 0, will be seeded automatically. "
      "Not stored when the node is saved.",
      NTA_BasicType_UInt32,
      1, 
      "interval: [0, ...)", 
      "42",
      ParameterSpec::CreateAccess
      ));


  ns->parameters.add(
    "nta_acceptanceProbability", 
    ParameterSpec(
      "The probability that each node will attempt to learn "
      "on each compute iteration. Only applied if cloning is off. "
      "Setting this to something less than 1.0 "
      "allows presenting many vectors but only considering a tiny "
      "fraction of them for learning. For example, if the total "
      "training input is 100,000 vectors, "
      "and the number of coincidences to be "
      "stored must be no more than 100, then this parameter should be "
      "set to approximately 100/100,000 = 0.001. "
      "This probability is considered "
      "before testing for minimum norm, sparsificiation, max distance "
      "and other checks. "
      "Applied by drawing a pseudorandom 48-bit fraction "
      "between 0 and 1, and attempting to learn only if the value "
      "is less than the parameter value. "
      "When set to 1.0 (the default), no pseudorandom draws occur. "
      "Not stored when the node is saved.",
      NTA_BasicType_Real64,
      1, 
      "interval: (0.0, 1.0]", 
      "1.0",
      ParameterSpec::ReadWriteAccess
      ));


  return ns;
}


//--------------------------------------------------------------------------------
/**
 * 1.6 does not save the random number generator's seed.
 * 1.7 adds saving of the random number generator's seed.
 */
const std::string SpatialPoolerNode::current_spatial_pooler_node_version_ = 
  "SpatialPoolerNode_1.8";

  

//--------------------------------------------------------------------------------
SpatialPoolerNode::SpatialPoolerNode(const ValueMap& params, Region* region)
  : RegionImpl(region), 
    mode_(Learning),
    // clonedNodes_(true), handled below
    nodeCount_(0), // will be set in initialize()
    // segmentSize_ (handled below)
    // sparsificationMode_ (handled below)
    // inferenceMode_ (handled below)
    // patchMasksStr_ (handled below -- nta_patchMasks)
    // normalize -- handled below
    // norm_ -- handled below
    // kWinners_ -- handled below -- nta_kWinners
    // maxDistance_ -- handled below
    // minAcceptNorm_ -- handled below
    // minProtoSum_ -- handled below
    // sigma_ -- handled below
    // seed_ -- handled below
    // maxNAttempts_(0), -- handled below
    // maxNPrototypes_(0) -- handled bedlow (maxCoincidenceCount)
    acceptanceProbability_(1.0),
    // rgen_(42) -- handled below
    poolersAllocated_(false),

    // non-serialized attributes
    bottomUpIn_(NULL), 
    topDownIn_(NULL),
    bottomUpOut_(NTA_BasicType_Real),
    topDownOut_(NTA_BasicType_Real),
    // bottomUpInputVector_ -- default constructor
    // topDownInputVector_ -- default constructor
    buInputSizePerNode_(0),
    tdInputSizePerNode_(0),
    phaseIndex_(0)
{

  waitDebuggerAttach_();
  
  clonedNodes_ = params.getScalarT<UInt32>("clonedNodes");
  segmentSize_ = params.getScalarT<UInt32>("nta_segmentSize");
  sparsificationMode_ = 
    SparsePooler::convertSparsificationMode(*params.getString("sparsify"));
  inferenceMode_ = 
    SparsePooler::convertInferenceMode(*params.getString("spatialPoolerAlgorithm"));
  patchMasksStr_ = *params.getString("nta_patchMasks");
  normalize_ = (bool)params.getScalarT<UInt32>("nta_normalize");
  norm_ = params.getScalarT<Real32>("nta_norm");
  kWinners_ = params.getScalarT<UInt32>("nta_kWinners");
  maxDistance_ = max(nta::Epsilon, params.getScalarT<Real32>("maxDistance"));
  minAcceptNorm_ = params.getScalarT<Real32>("nta_minAcceptNorm");
  minProtoSum_ = params.getScalarT<Real32>("nta_minProtoSum");
  sigma_ = params.getScalarT<Real32>("sigma");
  seed_ = params.getScalarT<UInt32>("nta_seed");
  maxNPrototypes_ = params.getScalarT<UInt32>("maxCoincidenceCount");

  // SpatialPoolerNode <realInitial> <clonedNodes> 
  // <numNodes> <nodeMode> 
  // <maxNPrototypes> <maxNAttempts> 
  // <stateSize> <state>...

  // May be specified in a parameter; if not (or zero), we will calculate 
  // a value in initialize() based on the number of baby nodes. 
  maxNAttempts_ = params.getScalarT<UInt32>("nta_maxNAttempts", 0);

  poolers_.clear();



}


SpatialPoolerNode::SpatialPoolerNode(BundleIO& bundle, Region* region) : 
  RegionImpl(region), 
  bottomUpOut_(NTA_BasicType_Real), 
  topDownOut_(NTA_BasicType_Real)

{
  deserialize(bundle);
}



//--------------------------------------------------------------------------------
SpatialPoolerNode::~SpatialPoolerNode()
{
  for (UInt i = 0; i != poolers_.size(); ++i) {
    delete poolers_[i];
    poolers_[i] = NULL;
  }
}

//--------------------------------------------------------------------------------
void SpatialPoolerNode::initialize()
{
  const char* where = "SpatialPoolerNode, in initialize: ";
  
  NTA_CHECK(region_ != NULL);
  nodeCount_ = region_->getDimensions().getCount();

  bottomUpOut_ = region_->getOutputData("bottomUpOut");
  topDownOut_ = region_->getOutputData("topDownOut");
  bottomUpIn_ = region_->getInput("bottomUpIn");
  topDownIn_ = region_->getInput("topDownIn");

  if (bottomUpIn_->getData().getCount() == 0)
  {
    NTA_THROW << "Unable to initialize SpatialPooler Region '"
              << region_->getName() << "' because bottom up input is not linked.";
  }

  // make sure our primary output has been correctly sized by NuPIC
  NTA_CHECK(bottomUpOut_.getCount() == nodeCount_ * maxNPrototypes_);

    
  NTA_CHECK(mode_ == Learning || mode_ == Inference)
    << where << "Expected 0 (Learning) or 1 (Inference) for nodeMode, got: " 
    << mode_;
  
  if (maxNAttempts_ == 0)
    maxNAttempts_ = (UInt32) min(max((Real32)32, sqrt((Real32)nodeCount_)), (Real32)nodeCount_);

  buInputSizePerNode_ = bottomUpIn_->getData().getCount() / nodeCount_;
  tdInputSizePerNode_ = topDownIn_->getData().getCount() / nodeCount_;


  UInt actualNumNodes = clonedNodes_ ? 1 : nodeCount_;

  // TODO: should we always recreate in initialize()?
  rgen_ = nta::Random(seed_);

  if (!poolersAllocated_)
  {
    std::stringstream tmp;
    tmp << segmentSize_ << " ";
    if (patchMasksStr_.empty()) {
      tmp << " 1 1 0 " << max((size_t)1, buInputSizePerNode_) << " ";
    } else 
      tmp << patchMasksStr_;
    SparsePoolerInputMasks input_masks(tmp);
    for (UInt i = 0; i < actualNumNodes; i++)
    {
      SparsePooler *sp = 
        new SparsePooler( 
          input_masks,
          normalize_, 
          norm_, 
          sparsificationMode_, 
          inferenceMode_, 
          kWinners_, 
          1.0, // threshold, fixed for now
          maxDistance_, 
          minAcceptNorm_, 
          minProtoSum_, 
          sigma_,
          rgen_.getUInt32());
      poolers_.push_back(sp);
    }
    poolersAllocated_ = true;
  }
}

//--------------------------------------------------------------------------------
void SpatialPoolerNode::compute()
{
  if (!poolersAllocated_)
    NTA_THROW << "Invalid operation -- SpatialPoolerNode must be initialized by initializing the network";

  if (mode_ == Learning) {

    if (clonedNodes_) {

      // If we have filled up our quota of prototypes,
      // we return and the output is all zeros (set above).
      if (poolers_[0]->getTotalNPrototypes() >= maxNPrototypes_)
        return;

      // We need to carefully groom maxNAttempts
      UInt maxNAttempts = maxNAttempts_ == 0 ? 
        poolers_[0]->getNPrototypeSizes() : maxNAttempts_;

      // We prepare a list of candidate baby poolers 
      // from the set of enabled baby nodes only (not necessarily
      // all baby nodes).
      vector<UInt> cand;
      for (NodeSet::const_iterator i = getEnabledNodes().begin();
           i != getEnabledNodes().end(); i++)
      {
        cand.push_back(*i);
      }
      
      // If we are rejecting some presentations without looking at them,
      // then check whether we should skip this presentation.
      // TODO: Determine whether we want to adjust the acceptance prob for:
      //       - Number of enabled baby nodes
      //       - maxNAttempts
      //       - numPatchesPerPresentation
      if((acceptanceProbability_ < 1.0) && 
         (rgen_.getReal64() > acceptanceProbability_)) {
        return; // Skip. Trace this?
      }

      bool accepted = false;
      UInt n_attempts = 0;
      
      maxNAttempts = min(maxNAttempts, (UInt)cand.size());

      while (!accepted && n_attempts < maxNAttempts) {

        UInt node = cand[rgen_(cand.size())];

        bottomUpIn_->getInputForNode(node, bottomUpInputVector_);
        // size of each output is maxNPrototypes_
        Real* bottomUpOut = (Real*) bottomUpOut_.getBuffer() + node * maxNPrototypes_;
        
        accepted = poolers_[0]->learn(bottomUpInputVector_.begin(),
                                      bottomUpInputVector_.end(), bottomUpOut);
        
        if (!accepted) 
          cand.erase(remove(cand.begin(), cand.end(), (UInt)node), cand.end());

        ++n_attempts;
      }

    } else { // not cloned

      for (NodeSet::const_iterator i = getEnabledNodes().begin();
           i != getEnabledNodes().end(); i++)
      {
        size_t node = *i;
        
        // If one of the baby poolers has filled up its quota
        // we will skip to the next baby pooler. 
        // The output for the max-ed out baby pooler will be zero.
        if (poolers_[node]->getTotalNPrototypes() < maxNPrototypes_) {
        
          if((acceptanceProbability_ < 1.0) &&
             (rgen_.getReal64() > acceptanceProbability_))
            {
              // Skip. Trace this?
            }
          else {
            bottomUpIn_->getInputForNode(node, bottomUpInputVector_);
            // size of each output is maxNPrototypes_
            Real* bottomUpOut = (Real*) bottomUpOut_.getBuffer() + node * maxNPrototypes_;
            
            poolers_[node]->learn(bottomUpInputVector_.begin(),
                                  bottomUpInputVector_.end(), bottomUpOut);
          }
        }
      }
    }
      
  } else if (mode_ == Inference) {

    for (NodeSet::const_iterator i = getEnabledNodes().begin();
         i != getEnabledNodes().end(); i++)
    {
      size_t node = *i;
      
      bottomUpIn_->getInputForNode(node, bottomUpInputVector_);
      // size of each output is maxNPrototypes_
      Real* bottomUpOut = (Real*) bottomUpOut_.getBuffer() + node * maxNPrototypes_;
      Real* bottomUpOut_end = bottomUpOut + maxNPrototypes_;

      UInt poolerIndex = clonedNodes_ ? (UInt) 0 : (UInt) node;

      if (phaseIndex_ == 0) {

        poolers_[poolerIndex]->infer(bottomUpInputVector_.begin(),
                                     bottomUpInputVector_.end(), bottomUpOut, bottomUpOut_end);

      } else {
        NTA_CHECK(tdInputSizePerNode_ != 0);

        topDownIn_->getInputForNode(node, topDownInputVector_);
        // TODO: top down output size same as bottom up output size?
        Real* topDownOut = (Real*) topDownOut_.getBuffer()+maxNPrototypes_* node;
        
        poolers_[poolerIndex]->topDownInfer(bottomUpInputVector_.begin(),
                                            bottomUpInputVector_.end(), 
                                            topDownInputVector_.begin(),
                                            topDownInputVector_.end(), topDownOut);
      }
    }
  }
}


void SpatialPoolerNode::setParameterString(const std::string& paramName, Int64 index, const std::string& s)
{
  if (!poolersAllocated_)
    NTA_THROW << "Invalid operation -- SpatialPoolerNode must be initialized by initializing the network";

  if (paramName == "sparsify") {
    SparsePooler::SparsificationMode mode = SparsePooler::convertSparsificationMode(s);
    for(std::vector<nta::SparsePooler*>::iterator i = poolers_.begin(); i!=poolers_.end(); ++i)
      (*i)->setSparsificationMode(mode);
  } else {
    NTA_THROW << "Unknown string parameter '" << paramName << "'";
  }
}


std::string SpatialPoolerNode::getParameterString(const std::string& paramName, Int64 index)
{
  if (!poolersAllocated_)
    NTA_THROW << "Invalid operation -- SpatialPoolerNode must be initialized by initializing the network";

  // per-node parameter
  UInt poolerIndex = clonedNodes_ ? 0 : (UInt) index;

  if (paramName == "sparsify") {
    return poolers_[poolerIndex]->getSparsificationModeStr();
  } else if (paramName == "spatialPoolerAlgorithm") {
    return poolers_[poolerIndex]->getInferenceModeStr();
  } else if (paramName == "nta_patchMasks") {
    OMemStream buf;
    poolers_[poolerIndex]->getInputMasks().saveState(buf);
    return buf.str();
  } else if (paramName == "coincidenceMatrixString") {
    OMemStream buf;
    poolers_[0]->getCoincidenceMatrix(buf);
    return buf.str();
  } else {
        NTA_THROW << "Unknown string parameter: " << paramName;
  }
}


Handle SpatialPoolerNode::getParameterHandle(const std::string& paramName, Int64 index)
{
  if (!poolersAllocated_)
    NTA_THROW << "Invalid operation -- SpatialPoolerNode must be initialized by initializing the network";

  if (paramName == "coincidenceMatrix")
  {
    if (clonedNodes_ && index != -1)
    {
      NTA_THROW << "CoincidenceMatrix is a node level parameter -- must be retrieved for a specific node";
    } 
    Int64 poolerIndex = clonedNodes_ ? 0 : index;
    NTA_CHECK((UInt32)poolerIndex < poolers_.size());
    return (Handle)(poolers_[poolerIndex]->getCoincidenceMatrixHandle());
  } else {
    // TODO: create RegionImpl method that creates a better
    // error message by checking against the nodespec -- this 
    // parameter may exist, but may not be a handle.
    NTA_THROW << "Unknown handle parameter '" << paramName << "'";
  }
}


//--------------------------------------------------------------------------------
void SpatialPoolerNode::setParameterFromBuffer(const std::string& paramName, Int64 index, 
                                               IReadBuffer& buf)
{
  // Note: string parametrs are all handled in setParameterString
  const char* where = "SpatialPoolerNode, while setting parameter: ";

  try {

    UInt int_param = 0;
    //Real float_param = (Real) 0;
  
    if (paramName == "nta_phaseIndex") {
      buf.read(int_param);
      phaseIndex_ = (UInt32) int_param;
    }
    
    else if (paramName == "learningMode") {
      buf.read(int_param);
      mode_ = (int_param == 1) ? Learning : Inference;
      if (mode_ == Inference)
        switchToInference_();
    }

    else if (paramName == "inferenceMode") {
      buf.read(int_param);
      mode_ = (int_param == 1) ? Inference : Learning;
      if (mode_ == Inference)
        switchToInference_();
    } 


    else if (paramName == "nta_acceptanceProbability") {
      double x = 1.0;
      buf.read(x);

      // Only 48-bits in a typical draw.
      NTA_CHECK(x > (1.0 / double(0x1LL << 48)))
        << "Acceptance probability is too small. "
        "Fewer samples would be learned than expected.";

      acceptanceProbability_ = x;
    }

    else {

      NTA_THROW << "Unknown parameter: " << paramName;

    }
  } catch (std::exception& e) {
    NTA_THROW << where << "Couldn't set " << paramName
              << ": " << e.what();
  }
}

//--------------------------------------------------------------------------------
void SpatialPoolerNode::getParameterFromBuffer(const std::string& paramName, 
                                               Int64 index, 
                                               IWriteBuffer& value)
{
  // Note: string parameters are handled in getParameterString

  const char* where = "SpatialPoolerNode, while getting parameter: ";

  try {

    if (paramName == "learningMode") {
      value.write((UInt32) (mode_ == Learning ? 1 : 0));
      
    } else if (paramName == "inferenceMode") {
      value.write((UInt32) (mode_ == Inference ? 1 : 0));
      
    } else if (paramName == "maxCoincidenceCount") {
      value.write(maxNPrototypes_);

    } else if (paramName == "clonedNodes") {
      value.write((UInt32) (clonedNodes_ ? 1 : 0));
    } else if (paramName == "nta_phaseIndex") {
      value.write((UInt32) phaseIndex_);
    } else if (paramName == "nta_maxNAttempts") {
      value.write((UInt32) maxNAttempts_);
    } else if (paramName == "nta_acceptanceProbability") {
      value.write(acceptanceProbability_);
    } else if (paramName == "nta_seed") {
      value.write((nta::Int32)rgen_.getSeed());
    } else {
      if (!poolersAllocated_)
        NTA_THROW << "Invalid operation -- SpatialPoolerNode must be initialized by initializing the network";
      // per-node parameter
      UInt poolerIndex = clonedNodes_ ? 0 : (UInt) index;
      OMemStream buf;
      if (paramName == "maxDistance") {
        Real val = poolers_[poolerIndex]->getMinAcceptDistance();
        if (val <= nta::Epsilon)
          val = (Real) 0;
        value.write(val);

      } else if (paramName == "sigma") {
        value.write(poolers_[poolerIndex]->getSigma());

      } else if (paramName == "coincidenceCount") {
        value.write(poolers_[poolerIndex]->getTotalNPrototypes());
          
      } else if (paramName == "activeOutputCount") {
        value.write(poolers_[poolerIndex]->getTotalNPrototypes());
    
      } else if (paramName == "nta_segmentSize") {
        value.write((UInt32) poolers_[poolerIndex]->getSegmentSize());

      } else if (paramName == "nta_normalize") {
        value.write(poolers_[poolerIndex]->getDoNormalization());

      } else if (paramName == "nta_norm") {
        value.write(poolers_[poolerIndex]->getNorm());

      } else if (paramName == "nta_kWinners") {
        value.write(poolers_[poolerIndex]->getKWinners());

      } else if (paramName == "nta_minAcceptNorm") {
        value.write(poolers_[poolerIndex]->getMinAcceptNorm());

      } else if (paramName == "nta_minProtoSum") {
        value.write(poolers_[poolerIndex]->getMinProtoSum());
        
      } else {
        NTA_THROW << "Unknown parameter: " << paramName;
      }
    }
    
  } catch (std::exception& e) {
    NTA_THROW << where << "Couldn't retrieve " << paramName
              << ": " << e.what();
  }
}

//--------------------------------------------------------------------------------
std::string SpatialPoolerNode::executeCommand(const std::vector<std::string>& args, Int64 index)
{
  NTA_CHECK(args.size() >= 1);
  NTA_THROW << "SpatialPoolerNode: command '" << args[0] << " not known";
  return "";
}

//--------------------------------------------------------------------------------
void SpatialPoolerNode::switchToInference_()
{
  if (!poolersAllocated_)
    NTA_THROW << "Invalid operation -- SpatialPoolerNode must be initialized by initializing the network";

  bool hasLearned = true;

  for (UInt i = 0; i != poolers_.size(); ++i)
    if (poolers_[i]->getTotalNPrototypes() == 0)
      hasLearned = false;

  if (hasLearned == false)
    NTA_THROW << "SpatialPoolerNode::switchToInference: "
              << "Can't switch to inference, didn't learn anything.";
}

//--------------------------------------------------------------------------------
void SpatialPoolerNode::waitDebuggerAttach_()
{
  if (WAIT_GDB_ATTACH_INIT) {
#ifdef WIN32
    DWORD pid = ::GetCurrentProcessId();
#else
    pid_t pid = ::getpid();
#endif
    NTA_DEBUG << "SpatialPoolerNode Waiting for connect to process ID " 
              <<  pid << "...";
    string str;
    cin >> str;
    NTA_DEBUG << "Connected.";
  } 
}

//--------------------------------------------------------------------------------

size_t SpatialPoolerNode::getNodeOutputElementCount(const std::string& outputName)
{
  // TODO: add top down output? 
  if (outputName == "bottomUpOut")
    return maxNPrototypes_;
  return 0;
}



void SpatialPoolerNode::serialize(BundleIO& bundle)
{
  std::ofstream& f = bundle.getOutputStream("spmain");
  f   << current_spatial_pooler_node_version_ << " "
      << (UInt32) mode_ << " "
      << (UInt32) clonedNodes_ << " "
      << nodeCount_ << " "
      << segmentSize_ << " "
      << (UInt32) sparsificationMode_ << " "
      << (UInt32) inferenceMode_ << " "
      // patchMasksStr_ not serialized
      << (UInt32) normalize_ << " "
      << norm_ << " "
      << kWinners_ << " "
      << maxDistance_ << " "
      << minAcceptNorm_ << " "
      << minProtoSum_ << " "
      << sigma_ << " "
      << seed_ << " "
      << maxNAttempts_ << " "
      << maxNPrototypes_ << " "
      << acceptanceProbability_ << " "
      // save actual seed separately from seed_ in case it was seeded with "0"
      // TODO: actually serialize rgen_;
      << (UInt32) rgen_.getSeed() << " " 
      << (UInt32) poolersAllocated_ << " ";

  if (poolersAllocated_)
  {
    // If cloned, there is a single pooler. 
    // If not cloned, everybody is saved here. 
    UInt actualNumNodes = clonedNodes_ ? 1 : nodeCount_;
    for (UInt i = 0; i != actualNumNodes; ++i) {
      poolers_[i]->saveState(f);
      f << " ";
    }
  }
  f.close();
}

void SpatialPoolerNode::deserialize(BundleIO& bundle)
{
  std::ifstream& f = bundle.getInputStream("spmain");
  std::string version;
  f >> version;
  NTA_CHECK(version == current_spatial_pooler_node_version_);
  {
    // f >> mode_ doesn't work. 
    Int32 mode;
    f >> mode;
    mode_ = (Mode)mode;
  }
  f >> clonedNodes_;
  f >> nodeCount_;
  f >> segmentSize_;
  {
    Int32 mode;
    f >> mode;
    sparsificationMode_ = (SparsePooler::SparsificationMode) mode;
    f >> mode;
    inferenceMode_ = (SparsePooler::InferenceMode) mode;
  }
  f >> normalize_;
  f >> norm_;
  f >> kWinners_;
  f >> maxDistance_;
  f >> minAcceptNorm_;
  f >> minProtoSum_;
  f >> sigma_;
  // don't use this value to seed; use the one saved from rgen, below
  f >> seed_;
  f >> maxNAttempts_;
  f >> maxNPrototypes_;
  f >> acceptanceProbability_;
  {
    UInt32 actualSeed;
    f >> actualSeed;
    // TODO: this isn't really useful unless the network hasn't been used. 
    // The seed is the same, but internal state is lost.
    rgen_ = nta::Random(actualSeed);
  }
  
  f >> poolersAllocated_;
  if (poolersAllocated_)
  {
    UInt poolerCount = clonedNodes_ ? 1 : nodeCount_;
    poolers_.resize(poolerCount);
    for (UInt i = 0; i != poolerCount; ++i) {
      poolers_[i] = new SparsePooler();
      poolers_[i]->readState(f);
    }
  }
  f.close();


}

}

