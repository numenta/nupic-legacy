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
Implementation of the Region class

Methods related to parameters are in Region_parameters.cpp
Methods related to inputs and outputs are in Region_io.cpp

*/

#include <iostream>
#include <stdexcept>
#include <set>
#include <string>
#include <nta/engine/Region.hpp>
#include <nta/engine/RegionImpl.hpp>
#include <nta/engine/RegionImplFactory.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/utils/Log.hpp>
#include <nta/engine/Input.hpp>
#include <nta/engine/Output.hpp>
#include <nta/engine/Link.hpp>
#include <nta/ntypes/NodeSet.hpp>
#include <nta/os/Timer.hpp>

namespace nta
{


// Create region from parameter spec
Region::Region(const std::string& name, 
               const std::string& nodeType, 
               const std::string& nodeParams,
               Network * network) :
  name_(name), 
  type_(nodeType), 
  initialized_(false), 
  enabledNodes_(nullptr),
  network_(network)
{
  // Set region info before creating the RegionImpl so that the 
  // Impl has access to the region info in its constructor.
  RegionImplFactory & factory = RegionImplFactory::getInstance();
  spec_ = factory.getSpec(nodeType);

  // Dimensions start off as unspecified, but if
  // the RegionImpl only supports a single node, we 
  // can immediately set the dimensions. 
  if (spec_->singleNodeOnly)
    dims_.push_back(1);
  // else dims_ = []

  impl_ = factory.createRegionImpl(nodeType, nodeParams, this);
  createInputsAndOutputs_();

}

// Deserialize region
Region::Region(const std::string& name, 
               const std::string& nodeType,
               const Dimensions& dimensions,
               BundleIO& bundle,
               Network * network) :
  name_(name), 
  type_(nodeType), 
  initialized_(false), 
  enabledNodes_(nullptr),
  network_(network)
{
  // Set region info before creating the RegionImpl so that the 
  // Impl has access to the region info in its constructor.
  RegionImplFactory & factory = RegionImplFactory::getInstance();
  spec_ = factory.getSpec(nodeType);

  // Dimensions start off as unspecified, but if
  // the RegionImpl only supports a single node, we 
  // can immediately set the dimensions. 
  if (spec_->singleNodeOnly)
    if (!dimensions.isDontcare() && !dimensions.isUnspecified() &&
        !dimensions.isOnes())
      NTA_THROW << "Attempt to deserialize region of type " << nodeType
                << " with dimensions " << dimensions
                << " but region supports exactly one node.";

  dims_ = dimensions;

  impl_ = factory.deserializeRegionImpl(nodeType, bundle, this);
  createInputsAndOutputs_();
}


Network * Region::getNetwork()
{
  return network_;
}

void Region::createInputsAndOutputs_()
{

  // Create all the outputs for this node type. By default outputs are zero size
  for (size_t i = 0; i < spec_->outputs.getCount(); ++i)
  {
    const std::pair<std::string, OutputSpec> & p = spec_->outputs.getByIndex(i);
    std::string outputName = p.first;
    const OutputSpec & os = p.second;
    auto output = new Output(*this, os.dataType, os.regionLevel);
    outputs_[outputName] = output;
    // keep track of name in the output also -- see note in Region.hpp
    output->setName(outputName);
  }

  // Create all the inputs for this node type.
  for (size_t i = 0; i < spec_->inputs.getCount(); ++i)
  {
    const std::pair<std::string, InputSpec> & p = spec_->inputs.getByIndex(i);
    std::string inputName = p.first;
    const InputSpec &is = p.second;

    auto input = new Input(*this, is.dataType, is.regionLevel);
    inputs_[inputName] = input;
    // keep track of name in the input also -- see note in Region.hpp
    input->setName(inputName);
  }
}


bool Region::hasOutgoingLinks() const
{
  for (const auto & elem : outputs_)
  {
    if (elem.second->hasOutgoingLinks())
    {
      return true;
    } 
  }
  return false;
}
 
Region::~Region()
{
  // If there are any links connected to our outputs, this will fail.
  // We should catch this error in the Network class and give the 
  // user a good error message (regions may be removed either in 
  // Network::removeRegion or Network::~Network())
  for (auto & elem : outputs_)
  {
    delete elem.second;
    elem.second = nullptr;
  }

  for (auto & elem : inputs_)
  {
    delete elem.second;
    elem.second = nullptr;
  }

  delete impl_;
  delete enabledNodes_;

}



void 
Region::initialize()
{
  
  if (initialized_) 
    return;

  impl_->initialize();
  initialized_ = true;
}

bool 
Region::isInitialized() const
{
  return initialized_;
}

const std::string&
Region::getName() const
{
  return name_;
}

const std::string&
Region::getType() const
{ 
  return type_;
}

const Spec*
Region::getSpec() const
{
  return spec_;
}

const Spec*
Region::getSpecFromType(const std::string& nodeType)
{
  RegionImplFactory & factory = RegionImplFactory::getInstance();
  return factory.getSpec(nodeType);
}

const Dimensions&
Region::getDimensions() const
{
  return dims_;
}

void
Region::enable()
{
  NTA_THROW << "Region::enable not implemented (region name: " << getName() << ")";
}


void
Region::disable()
{
  NTA_THROW << "Region::disable not implemented (region name: " << getName() << ")";
}

std::string
Region::executeCommand(const std::vector<std::string>& args)
{
  std::string retVal;
  if (args.size() < 1)
  {
    NTA_THROW << "Invalid empty command specified";
  }


  if (profilingEnabled_)
    executeTimer_.start();

  retVal = impl_->executeCommand(args, (UInt64)(-1));

  if (profilingEnabled_)
    executeTimer_.stop();

  return retVal;
}


void
Region::compute()
{
  if (!initialized_)
    NTA_THROW << "Region " << getName() << " unable to compute because not initialized";

  if (profilingEnabled_)
    computeTimer_.start();

  impl_->compute();

  if (profilingEnabled_)
    computeTimer_.stop();

  return;
}



/**
 * These internal methods are called by Network as
 * part of initialization.
 */

size_t
Region::evaluateLinks()
{
  int nIncompleteLinks = 0;
  for (auto & elem : inputs_)
  {
    nIncompleteLinks += (elem.second)->evaluateLinks();
  }
  return nIncompleteLinks;
}

std::string
Region::getLinkErrors() const
{

  std::stringstream ss;
  for (const auto & elem : inputs_)
  {
    const std::vector<Link*>& links = elem.second->getLinks();
    for (const auto & link : links)
    {
      if ( (link)->getSrcDimensions().isUnspecified() ||
           (link)->getDestDimensions().isUnspecified())
      {
        ss << (link)->toString() << "\n";
      }
    }
  }

  return ss.str();
}

size_t Region::getNodeOutputElementCount(const std::string& name)
{
  // Use output count if specified in nodespec, otherwise
  // ask the Impl
  NTA_CHECK(spec_->outputs.contains(name));
  size_t count = spec_->outputs.getByName(name).count;
  if(count == 0)
  {
    try
    {
      count = impl_->getNodeOutputElementCount(name);
    } catch(Exception& e) {
      NTA_THROW << "Internal error -- the size for the output " << name <<
                   "is unknown. : " << e.what();
    }
  }

  return count;
}

void Region::initOutputs()
{
  // Some outputs are optional. These outputs will have 0 elementCount in the node
  // spec and also return 0 from impl->getNodeOutputElementCount(). These outputs still
  // appear in the output map, but with an array size of 0. 

  
  for (auto & elem : outputs_)
  {
    const std::string& name = elem.first;

    size_t count = 0;
    try
    {
      count = getNodeOutputElementCount(name);
    } catch (nta::Exception& e) {
      NTA_THROW << "Internal error -- unable to get size of output " 
                << name << " : " << e.what();
    }
    elem.second->initialize(count);
  }
}

void Region::initInputs() const
{
  auto i = inputs_.begin();
  for (; i != inputs_.end(); i++)
  {
    i->second->initialize();
  }
}





void
Region::setDimensions(Dimensions& newDims)
{
  // Can only set dimensions one time
  if (dims_ == newDims)
    return;
  
  if (dims_.isUnspecified())
  {
    if (newDims.isDontcare())
    {
      NTA_THROW << "Invalid attempt to set region dimensions to dontcare value";
    }

    if (! newDims.isValid())
    {
      NTA_THROW << "Attempt to set region dimensions to invalid value:"
                << newDims.toString();
    }

    dims_ = newDims;
    dimensionInfo_ = "Specified explicitly in setDimensions()";
  } else {
    NTA_THROW << "Attempt to set dimensions of region " << getName() 
              << " to " << newDims.toString()
              << " but region already has dimensions " << dims_.toString();
  }
  
  // can only create the enabled node set after we know the number of dimensions
  setupEnabledNodeSet();

}

void Region::setupEnabledNodeSet()
{
  NTA_CHECK(dims_.isValid());

  if (enabledNodes_ != nullptr)
  {
    delete enabledNodes_;
  }

  size_t nnodes = dims_.getCount();
  enabledNodes_ = new NodeSet(nnodes);
  
  enabledNodes_->allOn();
}

const NodeSet& Region::getEnabledNodes() const
{
  if (enabledNodes_ == nullptr)
  {
    NTA_THROW << "Attempt to access enabled nodes set before region has been initialized";
  }
  return *enabledNodes_;
}


void
Region::setDimensionInfo(const std::string& info)
{
  dimensionInfo_ = info;
}

const std::string&
Region::getDimensionInfo() const
{
  return dimensionInfo_;
}

void
Region::removeAllIncomingLinks()
{
  InputMap::const_iterator i = inputs_.begin();
  for (; i != inputs_.end(); i++)
  {
    std::vector<Link*> links = i->second->getLinks();
    for (auto & links_link : links)
    {
      i->second->removeLink(links_link);

    }
  }
    
}


void 
Region::uninitialize()
{
  initialized_ = false;
}

void 
Region::setPhases(std::set<UInt32>& phases)
{
  phases_ = phases;
}

std::set<UInt32>&
Region::getPhases()
{
  return phases_;
}


void
Region::serializeImpl(BundleIO& bundle)
{
  impl_->serialize(bundle);
}

void
Region::enableProfiling()
{
  profilingEnabled_ = true;
}

void
Region::disableProfiling()
{
  profilingEnabled_ = false;
}

void
Region::resetProfiling()
{
  computeTimer_.reset();
  executeTimer_.reset();
}

const Timer& Region::getComputeTimer() const
{
  return computeTimer_;
}

const Timer& Region::getExecuteTimer() const
{
  return executeTimer_;
}

}

