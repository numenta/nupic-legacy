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
 * Implementation of Output class
 *
*/

#include <cstring> // memset
#include <nta/types/BasicType.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/engine/Output.hpp>
#include <nta/engine/Region.hpp>
#include <nta/engine/Link.hpp> // temporary


namespace nta
{

Output::Output(Region& region, NTA_BasicType type, bool isRegionLevel) :
  region_(region), isRegionLevel_(isRegionLevel), name_("Unnamed"), nodeOutputElementCount_(0)
{
  data_ = new Array(type);
}

Output::~Output()
{
  // If we have any outgoing links, then there has been an 
  // error in the shutdown process. Not good to thow an exception
  // from a destructor, but we need to catch this error, and it 
  // should never occur if nupic internal logic is correct. 
  NTA_CHECK(links_.size() == 0) << "Internal error in region deletion";
  delete data_;
}

// allaocate buffer
void
Output::initialize(size_t count)
{
  // reinitialization is ok
  // might happen if initial initialization failed with an 
  // exception (elsewhere) and was retried. 
  if (data_->getBuffer() != nullptr)
    return;

  nodeOutputElementCount_ = count;
  size_t dataCount;
  if (isRegionLevel_)
    dataCount = count;
  else
    dataCount = count * region_.getDimensions().getCount();
  if (dataCount != 0)
  {
    data_->allocateBuffer(dataCount);
    // Zero the buffer because unitialized outputs can screw up inspectors, 
    // which look at the output before compute(). NPC-60
    void *buffer = data_->getBuffer();
    size_t byteCount = dataCount * BasicType::getSize(data_->getType());
    memset(buffer, 0, byteCount);
  }
}

void
Output::addLink(Link* link)
{
  // Make sure we don't add the same link twice
  // It is a logic error if we add the same link twice here, since
  // this method should only be called from Input::addLink
  auto linkIter = links_.find(link);
  NTA_CHECK(linkIter == links_.end());

  links_.insert(link);
}

void
Output::removeLink(Link* link)
{
  auto linkIter = links_.find(link);
  // Should only be called internally. Logic error if link not found
  NTA_CHECK(linkIter != links_.end());
  // Output::removeLink is only called from Input::removeLink so we don't
  // have to worry about removing it on the Input side
  links_.erase(linkIter);
}

const Array &
Output::getData() const
{
  return *data_;
}

bool
Output::isRegionLevel() const
{
  return isRegionLevel_;
}


Region&
Output::getRegion() const
{
  return region_;
}


void Output::setName(const std::string& name)
{
  name_ = name;
}

const std::string& Output::getName() const
{
  return  name_;
}


size_t
Output::getNodeOutputElementCount() const
{
  return nodeOutputElementCount_;
}

bool
Output::hasOutgoingLinks()
{
  return (!links_.empty());
}

}

