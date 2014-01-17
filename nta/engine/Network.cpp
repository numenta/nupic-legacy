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
Implementation of the Network class
*/

#include <limits>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <nta/engine/Network.hpp>
#include <nta/engine/Region.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/engine/Link.hpp>
#include <nta/engine/Input.hpp>
#include <nta/utils/Log.hpp>
#include <nta/utils/StringUtils.hpp>
#include <nta/engine/NuPIC.hpp> // for register/unregister
#include <nta/os/FStream.hpp>
#include <nta/os/Path.hpp>
#include <nta/os/Directory.hpp>
#include <nta/ntypes/BundleIO.hpp>
#include <yaml-cpp/yaml.h>


namespace nta
{

Network::Network()
{
  commonInit();
  NuPIC::registerNetwork(this);
}

Network::Network(const std::string& path)
{
  commonInit();
  load(path);
  NuPIC::registerNetwork(this);
}

void Network::commonInit()
{
  initialized_ = false;
  iteration_ = 0;
  minEnabledPhase_ = 0;
  maxEnabledPhase_ = 0;
  // automatic initialization of NuPIC, so users don't
  // have to call NuPIC::initialize
  NuPIC::init();
}



Network::~Network()
{
  NuPIC::unregisterNetwork(this);
  /**
   * Teardown choreography:
   * - unitialize all regions because otherwise we won't be able to disconnect them
   * - remove all links, because we can't delete connected regions
   * - delete the regions themselves. 
   */

  // 1. uninitialize
  for (size_t i = 0; i < regions_.getCount(); i++)
  {
    Region *r = regions_.getByIndex(i).second;
    r->uninitialize();
  }

  // 2. remove all links
  for (size_t i = 0; i < regions_.getCount(); i++)
  {
    Region *r = regions_.getByIndex(i).second;
    r->removeAllIncomingLinks();
  }

  // 3. delete the regions
  for (size_t i = 0; i < regions_.getCount(); i++)
  {
    std::pair<std::string, Region*>& item =  regions_.getByIndex(i);
    delete item.second;
    item.second = nullptr;
  }
}


Region* Network::addRegion(const std::string& name, 
                           const std::string& nodeType, 
                           const std::string& nodeParams)
{
  if (regions_.contains(name))
    NTA_THROW << "Region with name '" << name << "' already exists in network";

  auto r = new Region(name, nodeType, nodeParams, this);
  regions_.add(name, r);
  initialized_ = false;
    
  setDefaultPhase_(r);
  return r;
}

void Network::setDefaultPhase_(Region* region)
{
  UInt32 newphase = phaseInfo_.size();
  std::set<UInt32> phases;
  phases.insert(newphase);
  setPhases_(region, phases);
}




Region* Network::addRegionFromBundle(const std::string& name, 
                                     const std::string& nodeType, 
                                     const Dimensions& dimensions, 
                                     const std::string& bundlePath, 
                                     const std::string& label)
{
  if (regions_.contains(name))
    NTA_THROW << "Invalid saved network: two or more instance of region '" << name << "'";

  if (! Path::exists(bundlePath))
    NTA_THROW << "addRegionFromBundle -- bundle '" << bundlePath 
              << " does not exist";
  
  BundleIO bundle(bundlePath, label, name, /* isInput: */ true );
  auto r = new Region(name, nodeType, dimensions, bundle, this);
  regions_.add(name, r);
  initialized_ = false;
    
  // In the normal use case (deserializing a network from a bundle)
  // this default phase will immediately be overridden with the
  // saved phases. Having it here makes it possible for user code
  // to safely call addRegionFromBundle directly.
  setDefaultPhase_(r);
  return r;
}


void 
Network::setPhases_(Region *r, std::set<UInt32>& phases)
{
  if (phases.empty())
    NTA_THROW << "Attempt to set empty phase list for region " << r->getName();

  UInt32 maxNewPhase = *(phases.rbegin());
  UInt32 nextPhase = phaseInfo_.size();
  if (maxNewPhase >= nextPhase)
  {
    // It is very unlikely that someone would add a region
    // with a phase much greater than the phase of any other
    // region. This sanity check catches such problems, 
    // though it should arguably be legal to set any phase. 
    if (maxNewPhase - nextPhase > 3)
      NTA_THROW << "Attempt to set phase of " << maxNewPhase
                << " when expected next phase is " << nextPhase
                << " -- this is probably an error.";

    phaseInfo_.resize(maxNewPhase+1);
  }
  for (UInt i = 0; i < phaseInfo_.size(); i++)
  {
    bool insertPhase = false;
    if (phases.find(i) != phases.end())
      insertPhase = true;

    // remove previous settings for this region
    std::set<Region*>::iterator item;
    item = phaseInfo_[i].find(r);
    if (item != phaseInfo_[i].end() && !insertPhase)
    {
      phaseInfo_[i].erase(item);
    } else if (insertPhase) 
    {
      phaseInfo_[i].insert(r);
    }
  }

  // keep track (redundantly) of phases inside the Region also, for serialization
  r->setPhases(phases);

  resetEnabledPhases_();

}

void
Network::resetEnabledPhases_()
{
  // min/max enabled phases based on what is in the network
  minEnabledPhase_ = getMinPhase();
  maxEnabledPhase_ = getMaxPhase();
}


void
Network::setPhases(const std::string& name, std::set<UInt32>& phases)
{
  if (! regions_.contains(name))
    NTA_THROW << "setPhases -- no region exists with name '" << name << "'";

  Region *r = regions_.getByName(name);
  setPhases_(r, phases);
}

std::set<UInt32>
Network::getPhases(const std::string& name) const
{
  if (! regions_.contains(name))
    NTA_THROW << "setPhases -- no region exists with name '" << name << "'";
  
  Region *r = regions_.getByName(name);

  std::set<UInt32> phases;
  // construct the set of phases enabled for this region
  for (UInt32 i = 0; i < phaseInfo_.size(); i++)
  {
    if (phaseInfo_[i].find(r) != phaseInfo_[i].end())
    {
      phases.insert(i);
    }
  }
  return phases;
}


void
Network::removeRegion(const std::string& name)
{
  if (! regions_.contains(name))
    NTA_THROW << "removeRegion: no region named '" << name << "'";

  Region *r = regions_.getByName(name);
  if (r->hasOutgoingLinks())
    NTA_THROW << "Unable to remove region '" << name << "' because it has one or more outgoing links";

  // Network does not have to be uninitialized -- removing a region 
  // has no effect on the network as long as it has no outgoing links, 
  // which we have already checked. 
  // initialized_ = false;

  // Must uninitialize the region prior to removing incoming links
  r->uninitialize();
  regions_.remove(name);

  auto phase = phaseInfo_.begin();
  for (; phase != phaseInfo_.end(); phase++)
  {
    auto toremove = phase->find(r);
    if (toremove != phase->end())
      phase->erase(toremove);
  }
  
  // Trim phaseinfo as we may have no more regions at the highest phase(s)
  for (size_t i = phaseInfo_.size() - 1; i > 0; i--)
  {
    if (phaseInfo_[i].empty())
      phaseInfo_.resize(i);
    else
      break;
  }
  resetEnabledPhases_();

  // Region destructor cleans up all incoming links
  delete r;

  return;
}
  

void
Network::link(const std::string& srcRegionName, const std::string& destRegionName, 
              const std::string& linkType, const std::string& linkParams, 
              const std::string& srcOutputName, const std::string& destInputName)
{
  
  // Find the regions
  if (! regions_.contains(srcRegionName))
    NTA_THROW << "Network::link -- source region '" << srcRegionName << "' does not exist";
  Region* srcRegion = regions_.getByName(srcRegionName);
  
  if (! regions_.contains(destRegionName))
    NTA_THROW << "Network::link -- dest region '" << destRegionName << "' does not exist";
  Region* destRegion = regions_.getByName(destRegionName);

  // Find the inputs/outputs
  const Spec* srcSpec = srcRegion->getSpec();
  std::string outputName = srcOutputName;
  if (outputName == "")
    outputName = srcSpec->getDefaultOutputName();
  
  Output* srcOutput = srcRegion->getOutput(outputName);
  if (srcOutput == nullptr)
    NTA_THROW << "Network::link -- output " << outputName 
              << " does not exist on region " << srcRegionName;


  const Spec *destSpec = destRegion->getSpec();
  std::string inputName;
  if (destInputName == "")
    inputName = destSpec->getDefaultInputName();
  else
    inputName = destInputName;

  Input* destInput = destRegion->getInput(inputName);
  if (destInput == nullptr)
  {
    NTA_THROW << "Network::link -- input '" << inputName 
              << " does not exist on region " << destRegionName;
  }

  // Create the link itself
  destInput->addLink(linkType, linkParams, srcOutput);

}


void
Network::removeLink(const std::string& srcRegionName, const std::string& destRegionName, 
                    const std::string& srcOutputName, const std::string& destInputName)
{
  // Find the regions
  if (! regions_.contains(srcRegionName))
    NTA_THROW << "Network::unlink -- source region '" << srcRegionName << "' does not exist";
  Region* srcRegion =  regions_.getByName(srcRegionName);
  
  if (! regions_.contains(destRegionName))
    NTA_THROW << "Network::unlink -- dest region '" << destRegionName << "' does not exist";
  Region* destRegion = regions_.getByName(destRegionName);

  // Find the inputs
  const Spec *srcSpec = srcRegion->getSpec();
  const Spec *destSpec = destRegion->getSpec();
  std::string inputName;
  if (destInputName == "")
    inputName = destSpec->getDefaultInputName();
  else
    inputName = destInputName;

  Input* destInput = destRegion->getInput(inputName);
  if (destInput == nullptr)
  {
    NTA_THROW << "Network::unlink -- input '" << inputName 
              << " does not exist on region " << destRegionName;
  }
  
  std::string outputName = srcOutputName;
  if (outputName == "")
    outputName = srcSpec->getDefaultOutputName();
  Link* link = destInput->findLink(srcRegionName, outputName);

  if (link == nullptr)
    NTA_THROW << "Network::unlink -- no link exists from region " << srcRegionName 
              << " output " << outputName << " to region " << destRegionName 
              << " input " << destInput->getName();

  // Finally, remove the link
  destInput->removeLink(link);

}
  
void
Network::run(int n)
{
  if (!initialized_)
  {
    initialize();
  }

  if (phaseInfo_.empty())
    return;

  NTA_CHECK(maxEnabledPhase_ < phaseInfo_.size()) << "maxphase: " << maxEnabledPhase_ << " size: " << phaseInfo_.size();

  for(int iter = 0; iter < n; iter++)
  {
    iteration_++;

    // compute on all enabled regions in phase order
    for (UInt32 phase = minEnabledPhase_; phase <= maxEnabledPhase_; phase++)
    {
      for (auto r : phaseInfo_[phase])
      {
        
        r->prepareInputs();
        r->compute();
      }
    }
    // invoke callbacks
    for (UInt32 i = 0; i < callbacks_.getCount(); i++)
    {
      std::pair<std::string, callbackItem>& callback = callbacks_.getByIndex(i);
      callback.second.first(this, iteration_, callback.second.second);
    }
    
  }

  return;
}


void
Network::initialize()
{

  /* 
   * Do not reinitialize if already initialized. 
   * Mostly, this is harmless, but it has a side
   * effect of resetting the max/min enabled phases, 
   * which causes havoc if we are in the middle of 
   * a computation. 
   */
  if (initialized_)
    return;

  /*
   * 1. Calculate all region dimensions by 
   * iteratively evaluating links to induce
   * region dimensions.
   */

  
  // Iterate until all regions have finished
  // evaluating their links. If network is
  // incompletely specified, we'll never finish, 
  // so make sure we make progress each time 
  // through the network. 

  size_t nLinksRemainingPrev = std::numeric_limits<size_t>::max();
  size_t nLinksRemaining = nLinksRemainingPrev - 1;
    
  std::vector<Region*>::iterator r;
  while(nLinksRemaining > 0 && nLinksRemainingPrev > nLinksRemaining)
  {
    nLinksRemainingPrev = nLinksRemaining;
    nLinksRemaining = 0;

    for (size_t i = 0; i < regions_.getCount(); i++)
    {
      // evaluateLinks returns the number
      // of links which still need to be 
      // evaluated. 
      Region *r = regions_.getByIndex(i).second;
      nLinksRemaining += r->evaluateLinks();
    }
  }

  if (nLinksRemaining > 0)
  {
    // Try to give complete information to the user
    std::stringstream ss;
    ss << "Network::initialize() -- unable to evaluate all links\n"
       << "The following links could not be evaluated:\n";
    for (size_t i = 0; i < regions_.getCount(); i++)
    {
      Region*r = regions_.getByIndex(i).second;
      std::string errors = r->getLinkErrors();
      if (errors.size() == 0)
        continue;
      ss << errors << "\n";
    }
    NTA_THROW << ss.str();
  }
      

  // Make sure all regions now have dimensions
  for (size_t i = 0; i < regions_.getCount(); i++)
  {
    Region* r = regions_.getByIndex(i).second;
    const Dimensions& d = r->getDimensions();
    if (d.isUnspecified())
    {
      NTA_THROW << "Network::initialize() -- unable to complete initialization "
                << "because region '" << r->getName() << "' has unspecified "
                << "dimensions. You must either specify dimensions directly or "
                << "link to the region in a way that induces dimensions on the region.";
    }
    if (!d.isValid())
    {
      NTA_THROW << "Network::initialize() -- invalid dimensions " << d.toString() 
                << " for Region " << r->getName();
    }

  }


  /*
   * 2. initialize outputs:
   *   - . Delegated to regions
   */ 
  for (size_t i = 0; i < regions_.getCount(); i++)
  {
    Region *r = regions_.getByIndex(i).second;
    r->initOutputs();
  }

  /*
   * 3. initialize inputs
   *    - Delegated to regions
   */
  for (size_t i = 0; i < regions_.getCount(); i++)
  {
    Region *r = regions_.getByIndex(i).second;
    r->initInputs();
  }

  /*
   * 4. initialize region/impl
   */
  for (size_t i = 0; i < regions_.getCount(); i++)
  {
    Region *r = regions_.getByIndex(i).second;
    r->initialize();
  }

  /*
   * 5. Enable all phases in the network
   */
  resetEnabledPhases_();


  /*
   * Mark network as initialized. 
   */
  initialized_ = true;

}


const Collection<Region*>&
Network::getRegions() const
{
  return regions_;
}

Collection<Network::callbackItem>& Network::getCallbacks()
{
  return callbacks_;
}


UInt32
Network::getMinPhase() const
{
  UInt32 i = 0;
  for (; i < phaseInfo_.size(); i++)
  {
    if (!phaseInfo_[i].empty())
      break;
  }
  return i;
}


UInt32
Network::getMaxPhase() const
{
  /*
   * phaseInfo_ is always trimmed, so the max phase is 
   * phaseInfo_.size()-1
   */

  if (phaseInfo_.empty())
    return 0;

  return phaseInfo_.size() - 1;
}


void
Network::setMinEnabledPhase(UInt32 minPhase)
{
  if (minPhase >= phaseInfo_.size())
    NTA_THROW << "Attempt to set min enabled phase " << minPhase
              << " which is larger than the highest phase in the network - "
              << phaseInfo_.size() - 1;
  minEnabledPhase_ = minPhase;
}

void
Network::setMaxEnabledPhase(UInt32 maxPhase)
{
  if (maxPhase >= phaseInfo_.size())
    NTA_THROW << "Attempt to set max enabled phase " << maxPhase
              << " which is larger than the highest phase in the network - "
              << phaseInfo_.size() - 1;
  maxEnabledPhase_ = maxPhase;
}

UInt32
Network::getMinEnabledPhase() const
{
  return minEnabledPhase_;
}


UInt32 
Network::getMaxEnabledPhase() const
{
  return maxEnabledPhase_;
}


void Network::save(const std::string& name)
{

  if (StringUtils::endsWith(name, ".tgz"))
  {
    NTA_THROW << "Gzipped tar archives (" << name << ") not yet supported";
  } else if (StringUtils::endsWith(name, ".nta"))
  {
    saveToBundle(name);
  } else {
    NTA_THROW << "Network::save -- unknown file extension for '" << name 
              << "'. Supported extensions are .tgz and .nta";
  }
}

// A Region "name" is the name specified by the user in addRegion
// This name may not be usable as part of a filesystem path, so 
// bundle files associated with a region use the region "label"
// that can always be stored in the filesystem
static std::string getLabel(size_t index)
{
  return std::string("R") + StringUtils::fromInt(index);
}

// save does the real work with saveToBundle
void Network::saveToBundle(const std::string& name)
{
  if (! StringUtils::endsWith(name, ".nta"))
    NTA_THROW << "saveToBundle: bundle extension must be \".nta\"";

  std::string fullPath = Path::normalize(Path::makeAbsolute(name));
  std::string networkStructureFilename = Path::join(fullPath, "network.yaml");


  // Only overwrite an existing path if it appears to be a network bundle
  if (Path::exists(fullPath))
  {
    if (! Path::isDirectory(fullPath) || ! Path::exists(networkStructureFilename))
    {
      NTA_THROW << "Existing filesystem entry " << fullPath 
                << " is not a network bundle -- refusing to delete";
    }
    Directory::removeTree(fullPath);
  }

  Directory::create(fullPath);

  {
    YAML::Emitter out;
    
    out << YAML::BeginMap;
    out << YAML::Key << "Version" << YAML::Value << 2;
    out << YAML::Key << "Regions" << YAML::Value << YAML::BeginSeq;
    for (size_t regionIndex = 0; regionIndex < regions_.getCount(); regionIndex++)
    {
      std::pair<std::string, Region*>& info = regions_.getByIndex(regionIndex);
      Region *r = info.second;
      // Network serializes the region directly because it is actually easier
      // to do here than inside the region, and we don't have the RegionImpl data yet. 
      out << YAML::BeginMap;
      out << YAML::Key << "name" << YAML::Value << info.first;
      out << YAML::Key << "nodeType" << YAML::Value << r->getType();
      out << YAML::Key << "dimensions" << YAML::Value << r->getDimensions();

      // yaml-cpp doesn't come with a default emitter for std::set, so 
      // implement as a sequence by hand. 
      out << YAML::Key << "phases" << YAML::Value << YAML::BeginSeq;
      std::set<UInt32> phases = r->getPhases();
      for (const auto & phases_phase : phases)
      {
        out << phases_phase;
      }
      out << YAML::EndSeq;

      // label is going to be used to name RegionImpl files within the bundle
      out << YAML::Key << "label" << YAML::Value << getLabel(regionIndex);
      out << YAML::EndMap;
    }
    out << YAML::EndSeq; // end of regions
  
    out << YAML::Key << "Links" << YAML::Value << YAML::BeginSeq;

    for (size_t regionIndex = 0; regionIndex < regions_.getCount(); regionIndex++)
    {
      Region *r = regions_.getByIndex(regionIndex).second;
      const std::map<const std::string, Input*> inputs = r->getInputs();
      for (const auto & inputs_input : inputs)
      {
        const std::vector<Link*>& links = inputs_input.second->getLinks();
        for (const auto & links_link : links)
        {
          Link& l = *(links_link);
          out << YAML::BeginMap;
          out << YAML::Key << "type" << YAML::Value << l.getLinkType();
          out << YAML::Key << "params" << YAML::Value << l.getLinkParams();
          out << YAML::Key << "srcRegion" << YAML::Value << l.getSrcRegionName();
          out << YAML::Key << "srcOutput" << YAML::Value << l.getSrcOutputName();
          out << YAML::Key << "destRegion" << YAML::Value << l.getDestRegionName();
          out << YAML::Key << "destInput" << YAML::Value << l.getDestInputName();
          out << YAML::EndMap;
        }

      }
    }      
    out << YAML::EndSeq; // end of links

    out << YAML::EndMap; // end of network

    OFStream f;
    f.open(networkStructureFilename.c_str());
    f << out.c_str();
    f.close();
  }

  // Now save RegionImpl data
  for (size_t regionIndex = 0; regionIndex < regions_.getCount(); regionIndex++)
  {
    std::pair<std::string, Region*>& info = regions_.getByIndex(regionIndex);
    Region *r = info.second;
    std::string label = getLabel(regionIndex);
    BundleIO bundle(fullPath, label, info.first, /* isInput: */ false);
    r->serializeImpl(bundle);
  }
}

void Network::load(const std::string& path)
{
  if (StringUtils::endsWith(path, ".tgz"))
  {
    NTA_THROW << "Gzipped tar archives (" << path << ") not yet supported";
  } else if (StringUtils::endsWith(path, ".nta"))
  {
    loadFromBundle(path);
  } else {
    NTA_THROW << "Network::save -- unknown file extension for '" << path 
              << "'. Supported extensions are  .tgz and .nta";
  }

}

void Network::loadFromBundle(const std::string& name)
{
  if (! StringUtils::endsWith(name, ".nta"))
    NTA_THROW << "loadFromBundle: bundle extension must be \".nta\"";

  std::string fullPath = Path::normalize(Path::makeAbsolute(name));

  if (! Path::exists(fullPath))
    NTA_THROW << "Path " << fullPath << " does not exist";

  std::string networkStructureFilename = Path::join(fullPath, "network.yaml");
  std::ifstream f(networkStructureFilename.c_str());
  YAML::Parser parser(f);
  YAML::Node doc;
  bool success = parser.GetNextDocument(doc);
  if (!success)
    NTA_THROW << "Unable to find YAML document in network structure file " 
              << networkStructureFilename;

  if (doc.Type() != YAML::NodeType::Map)
    NTA_THROW << "Invalid network structure file -- does not contain a map";

  // Should contain Version, Regions, Links
  if (doc.size() != 3)
    NTA_THROW << "Invalid network structure file -- contains " 
              << doc.size() << " elements";

  // Extra version
  const YAML::Node *node = doc.FindValue("Version");
  if (node == nullptr)
    NTA_THROW << "Invalid network structure file -- no version";
  
  int version;
  *node >> version;
  if (version != 2)
    NTA_THROW << "Invalid network structure file -- only version 2 supported";
  
  // Regions
  const YAML::Node *regions = doc.FindValue("Regions");
  if (regions == nullptr)
    NTA_THROW << "Invalid network structure file -- no regions";

  if (regions->Type() != YAML::NodeType::Sequence)
    NTA_THROW << "Invalid network structure file -- regions element is not a list";
  
  for (YAML::Iterator region = regions->begin(); region != regions->end(); region++)
  {
    // Each region is a map -- extract the 5 values in the map
    if ((*region).Type() != YAML::NodeType::Map)
      NTA_THROW << "Invalid network structure file -- bad region (not a map)";
    
    if ((*region).size() != 5)
      NTA_THROW << "Invalid network structure file -- bad region (wrong size)";
    
    // 1. name
    node = (*region).FindValue("name");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- region has no name";
    std::string name;
    *node >> name;

    // 2. nodeType
    node = (*region).FindValue("nodeType");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- region " 
                << name << " has no node type";
    std::string nodeType;
    *node >> nodeType;

    // 3. dimensions
    node = (*region).FindValue("dimensions");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- region "
                << name << " has no dimensions";
    if ((*node).Type() != YAML::NodeType::Sequence)
      NTA_THROW << "Invalid network structure file -- region "
                << name << " dimensions specified incorrectly";
    Dimensions dimensions;
    for (YAML::Iterator valiter = (*node).begin(); valiter != (*node).end(); valiter++)
    {
      size_t val;
      (*valiter) >> val;
      dimensions.push_back(val);
    }

    // 4. phases
    node = (*region).FindValue("phases");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- region"
                << name << "has no phases";
    if ((*node).Type() != YAML::NodeType::Sequence)
      NTA_THROW << "Invalid network structure file -- region "
                << name << " phases specified incorrectly";

    std::set<UInt32> phases;
    for (YAML::Iterator valiter = (*node).begin(); valiter != (*node).end(); valiter++)
    {
      UInt32 val;
      (*valiter) >> val;
      phases.insert(val);
    }
    
    // 5. label
    node = (*region).FindValue("label");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- region"
                << name << "has no label";
    std::string label;
    *node >> label;
    
    Region *r = addRegionFromBundle(name, nodeType, dimensions, fullPath, label);
    setPhases_(r, phases);


  }

  const YAML::Node *links = doc.FindValue("Links");
  if (links == nullptr)
    NTA_THROW << "Invalid network structure file -- no links";

  if (links->Type() != YAML::NodeType::Sequence)
    NTA_THROW << "Invalid network structure file -- links element is not a list";

  for (YAML::Iterator link = links->begin(); link != links->end(); link++)
  {
    // Each link is a map -- extract the 5 values in the map
    if ((*link).Type() != YAML::NodeType::Map)
      NTA_THROW << "Invalid network structure file -- bad link (not a map)";
    
    if ((*link).size() != 6)
      NTA_THROW << "Invalid network structure file -- bad link (wrong size)";
    
    // 1. type
    node = (*link).FindValue("type");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- link does not have a type";
    std::string linkType;
    *node >> linkType;

    // 2. params
    node = (*link).FindValue("params");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- link does not have params";
    std::string params;
    *node >> params;

    // 3. srcRegion (name)
    node = (*link).FindValue("srcRegion");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- link does not have a srcRegion";
    std::string srcRegionName;
    *node >> srcRegionName;


    // 4. srcOutput
    node = (*link).FindValue("srcOutput");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- link does not have a srcOutput";
    std::string srcOutputName;
    *node >> srcOutputName;

    // 5. destRegion
    node = (*link).FindValue("destRegion");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- link does not have a destRegion";
    std::string destRegionName;
    *node >> destRegionName;

    // 6. destInput
    node = (*link).FindValue("destInput");
    if (node == nullptr)
      NTA_THROW << "Invalid network structure file -- link does not have a destInput";
    std::string destInputName;
    *node >> destInputName;

    if (!regions_.contains(srcRegionName))
      NTA_THROW << "Invalid network structure file -- link specifies source region '" << srcRegionName << "' but no such region exists";
    Region* srcRegion = regions_.getByName(srcRegionName);

    if (!regions_.contains(destRegionName))
      NTA_THROW << "Invalid network structure file -- link specifies destination region '" << destRegionName << "' but no such region exists";
    Region* destRegion = regions_.getByName(destRegionName);

    Output* srcOutput = srcRegion->getOutput(srcOutputName);
    if (srcOutput == nullptr)
      NTA_THROW << "Invalid network structure file -- link specifies source output '" << srcOutputName << "' but no such name exists";

    Input* destInput = destRegion->getInput(destInputName);
    if (destInput == nullptr)
      NTA_THROW << "Invalid network structure file -- link specifies destination input '" << destInputName << "' but no such name exists";

    // Create the link itself
    destInput->addLink(linkType, params, srcOutput);


  } // links

}


void Network::enableProfiling()
{
  for (size_t i = 0; i < regions_.getCount(); i++)
    regions_.getByIndex(i).second->enableProfiling();
}

void Network::disableProfiling()
{
  for (size_t i = 0; i < regions_.getCount(); i++)
    regions_.getByIndex(i).second->disableProfiling();
}

void Network::resetProfiling()
{
  for (size_t i = 0; i < regions_.getCount(); i++)
    regions_.getByIndex(i).second->resetProfiling();
}



} // namespace nta
