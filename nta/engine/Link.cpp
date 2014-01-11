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
 * Implementation of the Link class
 */

#include <cstring> // memcpy
#include <nta/engine/Link.hpp>
#include <nta/utils/Log.hpp>
#include <nta/engine/LinkPolicyFactory.hpp>
#include <nta/engine/LinkPolicy.hpp>
#include <nta/engine/Region.hpp>
#include <nta/engine/Input.hpp>
#include <nta/engine/Output.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/ntypes/ArrayRef.hpp>
#include <nta/types/BasicType.hpp>

namespace nta
{


Link::Link(const std::string& linkType, const std::string& linkParams,
           const std::string& srcRegionName, const std::string& destRegionName, 
           const std::string& srcOutputName, const std::string& destInputName)
{
  commonConstructorInit_(linkType, linkParams, 
        srcRegionName, destRegionName, 
        srcOutputName, destInputName);

}
    
Link::Link(const std::string& linkType, const std::string& linkParams, 
           Output* srcOutput, Input* destInput)
{
  commonConstructorInit_(linkType, linkParams, 
        srcOutput->getRegion().getName(),
        destInput->getRegion().getName(), 
        srcOutput->getName(), 
        destInput->getName() );

  connectToNetwork(srcOutput, destInput);
  // Note -- link is not usable until we set the destOffset, which happens at initialization time
}

void Link::commonConstructorInit_(const std::string& linkType, const std::string& linkParams,
                 const std::string& srcRegionName, const std::string& destRegionName,
                 const std::string& srcOutputName,  const std::string& destInputName)
{
  linkType_ = linkType;
  linkParams_ = linkParams;
  srcRegionName_ = srcRegionName;
  srcOutputName_ = srcOutputName;
  destRegionName_ = destRegionName;
  destInputName_ = destInputName;
  destOffset_ = 0;
  srcOffset_ = 0;
  srcSize_ = 0;
  src_ = NULL;
  dest_ = NULL;
  initialized_ = false;


  impl_ = LinkPolicyFactory().createLinkPolicy(linkType, linkParams, this);
}

Link::~Link()
{
  delete impl_;
}

void Link::initialize(size_t destinationOffset)
{
  // Make sure all information is specified and
  // consistent. Unless there is a NuPIC implementation
  // error, all these checks are guaranteed to pass
  // because of the way the network is constructed
  // and initialized. 
  
  // Make sure we have been attached to a real network
  NTA_CHECK(src_ != NULL);
  NTA_CHECK(dest_ != NULL);

  // Confirm that our dimensions are consistent with the 
  // dimensions of the regions we're connecting. 
  const Dimensions& srcD = getSrcDimensions();
  const Dimensions& destD = getDestDimensions();
  NTA_CHECK(! srcD.isUnspecified());
  NTA_CHECK(! destD.isUnspecified());

  Dimensions oneD;
  oneD.push_back(1);

  if(src_->isRegionLevel())
  {
    Dimensions d;
    for(size_t i = 0; i < src_->getRegion().getDimensions().size(); i++)
    {
      d.push_back(1);
    }
    
    NTA_CHECK(srcD.isDontcare() || srcD == d);
  }
  else if(src_->getRegion().getDimensions() == oneD)
  {
    Dimensions d;
    for(size_t i = 0; i < srcD.size(); i++)
    {
      d.push_back(1);
    }
    NTA_CHECK(srcD.isDontcare() || srcD == d);
  }
  else
  {
    NTA_CHECK(srcD.isDontcare() || srcD == src_->getRegion().getDimensions());
  }

  if(dest_->isRegionLevel())
  {
    Dimensions d;
    for(size_t i = 0; i < dest_->getRegion().getDimensions().size(); i++)
    {
      d.push_back(1);
    }
    
    NTA_CHECK(destD.isDontcare() || destD.isOnes());
  }
  else if(dest_->getRegion().getDimensions() == oneD)
  {
    Dimensions d;
    for(size_t i = 0; i < destD.size(); i++)
    {
      d.push_back(1);
    }
    NTA_CHECK(destD.isDontcare() || destD == d);
  }
  else
  {
    NTA_CHECK(destD.isDontcare() || destD == dest_->getRegion().getDimensions());
  }
  
  destOffset_ = destinationOffset;
  impl_->initialize();
  initialized_ = true;
  
}

void Link::setSrcDimensions(Dimensions& dims)
{
  NTA_CHECK(src_ != NULL && dest_ != NULL) 
    << "Link::setSrcDimensions() can only be called on a connected link";

  size_t nodeElementCount = src_->getNodeOutputElementCount();
  if(nodeElementCount == 0)
  {
    nodeElementCount =
      src_->getRegion().getNodeOutputElementCount(src_->getName());
  }
  impl_->setNodeOutputElementCount(nodeElementCount);

  impl_->setSrcDimensions(dims);
}

void Link::setDestDimensions(Dimensions& dims)
{
  NTA_CHECK(src_ != NULL && dest_ != NULL) 
    << "Link::setDestDimensions() can only be called on a connected link";

  size_t nodeElementCount = src_->getNodeOutputElementCount();
  if(nodeElementCount == 0)
  {
    nodeElementCount =
      src_->getRegion().getNodeOutputElementCount(src_->getName());
  }
  impl_->setNodeOutputElementCount(nodeElementCount);

  impl_->setDestDimensions(dims);
}

const Dimensions& Link::getSrcDimensions() const
{ 
  return impl_->getSrcDimensions(); 
};

const Dimensions& Link::getDestDimensions() const
{ 
  return impl_->getDestDimensions();
};

// Return constructor params
const std::string& Link::getLinkType() const
{
  return linkType_;
}

const std::string& Link::getLinkParams() const
{
  return linkParams_;
}

const std::string& Link::getSrcRegionName() const
{
  return srcRegionName_;
}

const std::string& Link::getSrcOutputName() const
{
  return srcOutputName_;
}

const std::string& Link::getDestRegionName() const
{
  return destRegionName_;
}

const std::string& Link::getDestInputName() const
{
  return destInputName_;
}

const std::string Link::toString() const
{
  std::stringstream ss;
  ss << "[" << getSrcRegionName() << "." << getSrcOutputName();
  if (src_)
  {
    ss << " (region dims: " << src_->getRegion().getDimensions().toString() << ") ";
  }
  ss << " to " << getDestRegionName() << "." << getDestInputName() ;
  if (dest_)
  {
    ss << " (region dims: " << dest_->getRegion().getDimensions().toString() << ") ";
  }
  ss << " type: " << linkType_ << "]";
  return ss.str();
}

// called only by Input::addLink()
void Link::connectToNetwork(Output *src, Input *dest)
{
  NTA_CHECK(src != NULL);
  NTA_CHECK(dest != NULL);

  src_ = src;
  dest_ = dest;
}


// The methods below only work on connected links.
Output& Link::getSrc() const

{ 
  NTA_CHECK(src_ != NULL) 
    << "Link::getSrc() can only be called on a connected link";
  return *src_; 
}

Input& Link::getDest() const
{ 
  NTA_CHECK(dest_ != NULL) 
    << "Link::getDest() can only be called on a connected link";
  return *dest_; 
}

void 
Link::buildSplitterMap(Input::SplitterMap& splitter)
{
  // The link policy generates a splitter map
  // at the element level.  Here we convert it
  // to a full splitter map 
  // 
  // if protoSplitter[destNode][x] == srcElement for some x
  // means that the output srcElement is sent to destNode

  Input::SplitterMap protoSplitter;
  protoSplitter.resize(splitter.size());
  size_t nodeElementCount = src_->getNodeOutputElementCount();
  impl_->setNodeOutputElementCount(nodeElementCount);
  impl_->buildProtoSplitterMap(protoSplitter);

  for (size_t destNode = 0; destNode < splitter.size(); destNode++)
  {
    // convert proto-splitter values into real
    // splitter values;
    for (size_t protoItem = 0; protoItem < protoSplitter[destNode].size(); protoItem++)
    {
      size_t srcElement = protoSplitter[destNode][protoItem];
      size_t elementOffset = srcElement + destOffset_;
      splitter[destNode].push_back(elementOffset);
    }

  }
}

void 
Link::compute()
{
  NTA_CHECK(initialized_);
  
  // Copy data from source to destination. 
  // TBD: with zero-copy optimization, we won't do anything, 
  // but that isn't implemented yet. 
  const Array & src = src_->getData();
  const Array & dest = dest_->getData();

  // TBD: use src offset and src size (only for certain types of links)
  size_t typeSize = BasicType::getSize(src.getType());
  size_t srcSize = src.getCount() * typeSize;
  size_t destByteOffset = destOffset_ * typeSize;
  ::memcpy((char*)(dest.getBuffer()) + destByteOffset, src.getBuffer(), srcSize);
}




namespace nta
{
  std::ostream& operator<<(std::ostream& f, const Link& link)
  {
    f << "<Link>\n";
    f << "  <type>" << link.getLinkType() << "</type>\n";
    f << "  <params>" << link.getLinkParams() << "</params>\n";
    f << "  <srcRegion>" << link.getSrcRegionName() << "</srcRegion>\n";
    f << "  <destRegion>" << link.getDestRegionName() << "</destRegion>\n";
    f << "  <srcOutput>" << link.getSrcOutputName() << "</srcOutput>\n";
    f << "  <destInput>" << link.getDestInputName() << "</destInput>\n";
    f << "</Link>\n";
    return f;
  }
}

}

