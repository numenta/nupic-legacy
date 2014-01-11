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
 * Implementation of Input class
 *
 */

#include <cstring> // memset
#include <nta/ntypes/Dimensions.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/engine/Input.hpp>
#include <nta/engine/Output.hpp>
#include <nta/engine/Link.hpp>
#include <nta/engine/Region.hpp>
#include <nta/types/BasicType.hpp>

namespace nta
{

Input::Input(Region& region, NTA_BasicType dataType, bool isRegionLevel) :
  region_(region), isRegionLevel_(isRegionLevel), 
  zeroCopyEnabled_(false), initialized_(false),  data_(dataType), name_("Unnamed")
{
  if (&region == NULL)
  {
    NTA_THROW << "Attempt to create Input with a null region";
  }
}

Input::~Input()
{
  uninitialize();
  std::vector<Link*> linkscopy = links_;
  for (std::vector<Link*>::iterator i = linkscopy.begin(); i != linkscopy.end(); i++)
  {
    removeLink(*i);
  }
}

void
Input::addLink(const std::string& linkType, const std::string& linkParams, Output* srcOutput)
{
  if (initialized_)
    NTA_THROW << "Attempt to add link to input " << name_ 
              << " on region " << region_.getName()
              << " when input is already initialized";

  // Make sure we don't already have a link to the same output
  for (std::vector<Link*>::const_iterator link = links_.begin();
       link != links_.end(); link++)
  {
    if (srcOutput == &((*link)->getSrc()))
    {
      NTA_THROW << "addLink -- link from region " << srcOutput->getRegion().getName()
                << " output " << srcOutput->getName() << " to region "
                << region_.getName() << " input " << getName() << " already exists";
    }
  }

  Link *link = new Link(linkType, linkParams, srcOutput, this);
  links_.push_back(link);
  
  srcOutput->addLink(link);
  // Note -- link is not usable until we set the destOffset, which 
  // is calculated at initialization time
}


void
Input::removeLink(Link*& link)
{

  // removeLink should only be called internally -- if it 
  // does not exist, it is a logic error
  std::vector<Link*>::iterator linkiter = links_.begin();
  for(; linkiter!= links_.end(); linkiter++)
  {
    if (*linkiter == link)
      break;
  }

  NTA_CHECK(linkiter != links_.end());

  if (region_.isInitialized())
    NTA_THROW << "Cannot remove link " << link->toString() 
              << " because destination region " << region_.getName()
              << " is initialized. Remove the region first.";

  // We may have been initialized even if our containing region
  // was not. If so, uninitialize. 
  uninitialize();
  link->getSrc().removeLink(link);
  links_.erase(linkiter);
  delete link;
  link = NULL;
}
    
Link* Input::findLink(const std::string& srcRegionName, 
                      const std::string& srcOutputName)
{
  std::vector<Link*>::const_iterator linkiter = links_.begin();
  for (; linkiter != links_.end(); linkiter++)
  {
    Output& output = (*linkiter)->getSrc();
    if (output.getName() == srcOutputName && 
        output.getRegion().getName() == srcRegionName)
    {
      return *linkiter;
    }
  }
  // Link not found
  return NULL;
}

void
Input::prepare()
{
  // Each link copies data into its section of the overall input
  // TODO: initialization check?
  for (std::vector<Link*>::iterator l = links_.begin(); l != links_.end(); l++)
  {
    (*l)->compute();
  }
}
    
const Array &
Input::getData() const
{
  NTA_CHECK(initialized_);
  return data_;
}
    
Region&
Input::getRegion()
{
  return region_;
}

const std::vector<Link*>&
Input::getLinks()
{
  return links_;
}

bool
Input::isRegionLevel()
{
  return isRegionLevel_;
}
    

// See header file for documentation
size_t
Input::evaluateLinks()
{
  /**
   * It is not an error to call evaluateLinks() on an initialized 
   * input -- just report that no links remain to be evaluated. 
   * This simplifies the logic in Region::evaluateLinks, which calls
   * evaluateLinks on all its inputs at each iteration of network 
   * initialization. 
   */
  if (initialized_)
    return 0;

  size_t nIncompleteLinks = 0;
  std::vector<Link*>::iterator l;
  for (l = links_.begin(); l != links_.end(); l++)
  {
    Region& srcRegion = (*l)->getSrc().getRegion();
    Region& destRegion = (*l)->getDest().getRegion();

    /**
     * The link and region need to be consistent at both 
     * ends of the link. 
     * - Region dimensions may be specified or unspecified
     * - Link dimensions (at either end) may be specified, 
     *   unspecified, or dontcare. 
     * At each of the source and destination, we handle
     * each of the six possible cases of Region/Link specification. 
     */

    /* ------ look at the source side of the link ------- */

    Dimensions srcRegionDims = srcRegion.getDimensions();
    Dimensions srcLinkDims = (*l)->getSrcDimensions();

    /* source region dimensions are unspecified */
    if (srcRegionDims.isUnspecified())
    {
      if (srcLinkDims.isUnspecified())
      {
        // 1. link cares about src dimensions but they aren't set
        // link is incomplete; 
      } else if (srcLinkDims.isDontcare()) 
      {
        // 2. Link doesn't care. We don't need to do anything. 
      } else {
        // 3. Link specifies src dimensions but src region dimensions
        // are unspecified. Induce dimensions on the source region.

        // If source region is initialized, this is a logic error
        NTA_CHECK(!srcRegion.isInitialized());

        if(!((*l)->getSrc().isRegionLevel()))
        {
          // 3.1 Only set the dimensions if the link source is not region
          // level

          // Set the dimensions and record that we set them
          srcRegion.setDimensions(srcLinkDims);
          srcRegionDims = srcRegionDims;

          std::stringstream ss;
          ss << "Specified by source dimensions on link "
             << (*l)->toString();
          srcRegion.setDimensionInfo(ss.str());
        }
        else
        {
          // 3.2 Link is incomplete
        }
      }
    } else {
      /* source region dimensions are specified */
      if (srcLinkDims.isDontcare())
      {
        // 4. Link doesn't care. We don't need to do anything. 
      } else if (srcLinkDims.isUnspecified()) 
      {
        // 5. srcRegion dims set link dims

        if((*l)->getSrc().isRegionLevel())
        {
          // 5.1 link source is region level, so use dimensions of [1]

          Dimensions d;
          for(size_t i = 0; i < srcRegionDims.size(); i++)
          {
            d.push_back(1);
          }

          (*l)->setSrcDimensions(d);
          srcLinkDims = d;
        }
        else
        {
          // 5.2 apply region dimensions to link

          (*l)->setSrcDimensions(srcRegionDims);
          srcLinkDims = srcRegionDims;
        }
      } else {
        // 6. Both region dims and link dims are specified. 
        // Verify that srcRegion dims are the same as 
        // link dims
        if (srcRegionDims != srcLinkDims)
        {
          Dimensions oneD(1);

          bool inconsistentDimensions = false;

          if((*l)->getSrc().isRegionLevel())
          {
            Dimensions d;
            for(size_t i = 0; i < srcRegionDims.size(); i++)
            {
              d.push_back(1);
            }

            if(srcLinkDims != d)
            {
              NTA_THROW << "Internal error while processing Region "
                        << srcRegion.getName() << ".  The link " 
                        << (*l)->toString() << " has a region level source "
                           "output, but the link dimensions are "
                        << srcLinkDims.toString() << " instead of [1]";
            }
          }
          else if(srcRegionDims == oneD)
          {
            Dimensions d;
            for(size_t i = 0; i < srcLinkDims.size(); i++)
            {
              d.push_back(1);
            }

            if(srcLinkDims != d)
            {
              inconsistentDimensions = true;
            }
          }
          else
          {
            inconsistentDimensions = true;
          }

          if(inconsistentDimensions)
          {
            NTA_THROW << "Inconsistent dimension specification encountered. Region "
                      << srcRegion.getName() << " has dimensions "
                      << srcRegionDims.toString() << " but link "
                      << (*l)->toString() << " requires dimensions " 
                      << srcLinkDims.toString() << ". Additional information on " 
                      << "region dimensions: "
            << (srcRegion.getDimensionInfo() == "" ? "(none)" : srcRegion.getDimensionInfo());
          }
        }
      }
    }
    
    /* ------ look at the destination side of the link ------- */
    Dimensions destLinkDims = (*l)->getDestDimensions();
    Dimensions destRegionDims = destRegion.getDimensions();
    
    // The logic here is similar to the logic for the source side 
    // except for the case where the destination region dims are specified and the 
    // link dims are unspecified -- see comment below. 

    /* dest region dimensions are unspecified */
    if (destRegionDims.isUnspecified())
    {
      if (destLinkDims.isUnspecified())
      {
        // 1. link cares about dest dimensions but they aren't set
        //    link is incomplete;  Nothing we can do. 
      } else if (destLinkDims.isDontcare()) 
      {
        // 2. Link doesn't care. We don't need to do anything. 
      } else {
        // 3. Link specifies dest dimensions but region dimensions
        // have not yet been set -- induce dimensions on the region. 

        // If dest region is initialized, this is a logic error
        NTA_CHECK(!destRegion.isInitialized());

        if(!((*l)->getDest().isRegionLevel()))
        {
          // 3.1 Only set the dimensions if the link destination is not region
          // level

          // Set the dimensions and record that we set them
          destRegion.setDimensions(destLinkDims);
          destRegionDims = destRegion.getDimensions();
          std::stringstream ss;
          ss << "Specified by destination dimensions on link " << (*l)->toString();
          destRegion.setDimensionInfo(ss.str());
        }
        else
        {
          // 3.2 Link is incomplete
        }
      }
    } else {
      /* dest region dimensions are specified but src region dims are not */
      if (destLinkDims.isDontcare())
      {
        // 4. Link doesn't care. We don't need to do anything. 
      } else if (destLinkDims.isUnspecified())  {
        // 5. Region has dimensions -- set them on the link. 

        if((*l)->getDest().isRegionLevel())
        {
          // 5.1 link source is region level, so use dimensions of [1]

          Dimensions d;
          for(size_t i = 0; i < destRegionDims.size(); i++)
          {
            d.push_back(1);
          }

          (*l)->setDestDimensions(d);
          destLinkDims = d;
        }
        else
        {
          // 5.2 apply region dimensions to link

          (*l)->setDestDimensions(destRegionDims);
          destLinkDims = destRegionDims;
          
          // Setting the link dest dimensions may set the src
          // dimensions. Since we have already evaluated the source
          // side of the link, we need to re-evaluate here
          if (srcRegionDims.isUnspecified())
          {
            srcLinkDims = (*l)->getSrcDimensions();
            if (!srcLinkDims.isUnspecified() && !srcLinkDims.isDontcare())
            {
              // Induce. TODO: code is the same as on source side -- refactor?
              // If source region is initialized, this is a logic error
              NTA_CHECK(!srcRegion.isInitialized());
              
              // Set the dimensions and record that we set them
              srcRegion.setDimensions(srcLinkDims);
              srcRegionDims = srcRegion.getDimensions();

              std::stringstream ss;
              ss << "Specified by source dimensions on link "
                 << (*l)->toString();
              srcRegion.setDimensionInfo(ss.str());
            }

          } else {
            // src region dims were already specified. Make sure they 
            // are compatible with the link dims. 
            if (srcLinkDims != srcRegionDims)
            {
              NTA_THROW << "Inconsistent dimension specification encountered. Region "
                        << srcRegion.getName() << " has dimensions "
                        << srcRegionDims.toString() << " but link "
                        << (*l)->toString() << " requires dimensions " 
                        << srcLinkDims.toString() << ". Additional information on " 
                        << "region dimensions: "
                        << (srcRegion.getDimensionInfo() == "" ? "(none)" : srcRegion.getDimensionInfo());
            }

          }
        }

      } else {
        // 6. link dims and region dims are specified. 
        // verify that destRegion dims are the same as 
        // link dims. 
        //

        bool inconsistentDimensions = false;

        if (destRegionDims != destLinkDims)
        {
          Dimensions oneD;
          oneD.push_back(1);

          if((*l)->getDest().isRegionLevel())
          {
            if (! destLinkDims.isOnes())
              NTA_THROW << "Internal error while processing Region "
                        << destRegion.getName() << ".  The link " 
                        << (*l)->toString() << " has a region level destination "
                        << "input, but the link dimensions are "
                        << destLinkDims.toString() << " instead of [1]";
          }
          else if(destRegionDims == oneD)
          {
            Dimensions d;
            for(size_t i = 0; i < destLinkDims.size(); i++)
            {
              d.push_back(1);
            }

            if(destLinkDims != d)
            {
              inconsistentDimensions = true;
            }
          }
          else
          {
            inconsistentDimensions = true;
          }

          if(inconsistentDimensions)
          {
            NTA_THROW << "Inconsistent dimension specification encountered. Region "
                      << destRegion.getName() << " has dimensions "
                      << destRegionDims.toString() << " but link "
                      << (*l)->toString() << " requires dimensions " 
                      << destLinkDims.toString() << ". Additional information on " 
                      << "region dimensions: "
            << (destRegion.getDimensionInfo() == "" ? "(none)" : destRegion.getDimensionInfo());
          }
        }
      }
    }

    bool linkIsIncomplete = true;
    if (srcRegionDims.isSpecified() && destRegionDims.isSpecified()) 
    {
      linkIsIncomplete = false;
      // link dims may be specified or dontcare (!isUnspecified)
      NTA_CHECK(srcLinkDims.isSpecified() || srcLinkDims.isDontcare()) 
        << "link: " << (*l)->toString() 
        << " src: " << srcRegionDims.toString()
        << " dest: " << destRegionDims.toString()
        << " srclinkdims: " << srcLinkDims.toString();
      
      NTA_CHECK(destLinkDims.isSpecified() || destLinkDims.isDontcare())
        << "link: " << (*l)->toString() 
        << " src: " << srcRegionDims.toString()
        << " dest: " << destRegionDims.toString()
        << " destlinkdims: " << destLinkDims.toString();
    }

    if (linkIsIncomplete)
      nIncompleteLinks++;

  } // loop over all links connected to this Input

  return nIncompleteLinks;
}

// Called after all links have been evaluated, and 
// all inputs have been initialized. Now we can calculate
// our size and set up any data structures needed
// for copying data over a link. 

void Input::initialize()
{
  if (initialized_)
    return;

  if(region_.getDimensions().isUnspecified())
  {
    NTA_THROW << "Input region's dimensions are unspecified when Input::initialize() "
              << "was called. Region's dimensions must be specified.";
  }

  // Calculate our size and the offset of each link
  size_t count = 0;
  for (std::vector<Link*>::const_iterator l = links_.begin(); l != links_.end(); l++)
  {
    linkOffsets_.push_back(count);
    // Setting the destination offset makes the link usable. 
    // TODO: change 
    (*l)->initialize(count);
    count += (*l)->getSrc().getData().getCount();
  }

  // Later we may optimize with the zeroCopyEnabled_ flag but 
  // for now we always allocate our own buffer. 
  data_.allocateBuffer(count);

  // Zero the inputs (required for inspectors)
  if (count != 0)
  {
    void * buffer = data_.getBuffer();
    size_t byteCount = count * BasicType::getSize(data_.getType());
    ::memset(buffer, 0, byteCount);
  }


  NTA_CHECK(splitterMap_.size() == 0);
        
  // create the splitter map by getting the contributions
  // from each link. 
  if(isRegionLevel_)
  {
    splitterMap_.resize(1);
  }
  else
  {
    splitterMap_.resize(region_.getDimensions().getCount());
  }


  for (std::vector<Link *>::const_iterator link = links_.begin();
       link != links_.end(); link++)
  {
    (*link)->buildSplitterMap(splitterMap_);
  }


  initialized_ = true;
}

void Input::uninitialize()
{
  if (!initialized_)
    return;

  NTA_CHECK(!region_.isInitialized());

  initialized_ = false;
  data_.releaseBuffer();
  splitterMap_.clear();
}

bool Input::isInitialized()
{
  return(initialized_);
}

void Input::setName(const std::string& name)
{
  name_ = name;
}

const std::string& Input::getName() const
{
  return  name_;
}

const std::vector< std::vector<size_t> >& Input::getSplitterMap() const
{
  NTA_CHECK(initialized_);
  // Originally the splitter map was created on demand in this method. 
  // For now we have moved splitter map creation to initialize() because 
  // we have dual heap/libstdc++ allocation/deallocation problems if 
  // this method is called from a node DLL/.so (including pynode). 

  return splitterMap_;
}


template <typename T> void Input::getInputForNode(size_t nodeIndex, std::vector<T>& input) const
{
  NTA_CHECK(initialized_);
  const SplitterMap& sm = getSplitterMap();
  NTA_CHECK(nodeIndex < sm.size());

  const std::vector<size_t>& map = sm[nodeIndex];
  //NTA_CHECK(map.size() > 0);

  input.resize(map.size());
  T* fullInput = (T*)(data_.getBuffer());
  for (size_t i = 0; i < map.size(); i++)
    input[i] = fullInput[map[i]];
}

template void Input::getInputForNode(size_t nodeIndex, std::vector<Real64>& input) const;
template void Input::getInputForNode(size_t nodeIndex, std::vector<Real32>& input) const;
template void Input::getInputForNode(size_t nodeIndex, std::vector<Int64>& input) const;
template void Input::getInputForNode(size_t nodeIndex, std::vector<Int32>& input) const;
template void Input::getInputForNode(size_t nodeIndex, std::vector<UInt64>& input) const;
template void Input::getInputForNode(size_t nodeIndex, std::vector<UInt32>& input) const;
template void Input::getInputForNode(size_t nodeIndex, std::vector<Byte>& input) const;

}

