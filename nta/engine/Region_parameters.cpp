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
 * Implementation of Region methods related to parameters
 */

#include <nta/engine/Region.hpp>
#include <nta/engine/RegionImpl.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/utils/Log.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/types/types.h>

namespace nta
{


// setParameter

void Region::setParameterInt32(const std::string& name, Int32 value)
{
  impl_->setParameterInt32(name, (Int64)-1, value);
}

void Region::setParameterUInt32(const std::string& name, UInt32 value)
{
  impl_->setParameterUInt32(name, (Int64)-1, value);
}

void Region::setParameterInt64(const std::string& name, Int64 value)
{
  impl_->setParameterInt64(name, (Int64)-1, value);
}

void Region::setParameterUInt64(const std::string& name, UInt64 value)
{
  impl_->setParameterUInt64(name, (Int64)-1, value);
}

void Region::setParameterReal32(const std::string& name, Real32 value)
{
  impl_->setParameterReal32(name, (Int64)-1, value);
}

void Region::setParameterReal64(const std::string& name, Real64 value)
{
  impl_->setParameterReal64(name, (Int64)-1, value);
}

void Region::setParameterHandle(const std::string& name, Handle value)
{
  impl_->setParameterHandle(name, (Int64)-1, value);
}


// getParameter

Int32 Region::getParameterInt32(const std::string& name) const
{
  return impl_->getParameterInt32(name, (Int64)-1);
}

Int64 Region::getParameterInt64(const std::string& name) const
{
  return impl_->getParameterInt64(name, (Int64)-1);
}

UInt32 Region::getParameterUInt32(const std::string& name) const
{
  return impl_->getParameterUInt32(name, (Int64)-1);
}


UInt64 Region::getParameterUInt64(const std::string& name) const
{
  return impl_->getParameterUInt64(name, (Int64)-1);
}

Real32 Region::getParameterReal32(const std::string& name) const
{
  return impl_->getParameterReal32(name, (Int64)-1);
}

Real64 Region::getParameterReal64(const std::string& name) const
{
  return impl_->getParameterReal64(name, (Int64)-1);
}

Handle Region::getParameterHandle(const std::string& name) const
{
  return impl_->getParameterHandle(name, (Int64)-1);
}


// array parameters


void
Region::getParameterArray(const std::string& name, Array & array) const
{
  size_t count = impl_->getParameterArrayCount(name, (Int64)(-1));
  // Make sure we have a buffer to put the data in
  if (array.getBuffer() != NULL) 
  {
    // Buffer has already been allocated. Make sure it is big enough
    if (array.getCount() > count)
      NTA_THROW << "getParameterArray -- supplied buffer for parameter " << name
                << " can hold " << array.getCount() 
                << " elements but parameter count is "
                << count;
  } else {
    array.allocateBuffer(count);
  }

  impl_->getParameterArray(name, (Int64)-1, array);

}


void
Region::setParameterArray(const std::string& name, const Array & array)
{
  // We do not check the array size here because it would be
  // expensive -- involving a check against the nodespec, 
  // and only usable in the rare case that the nodespec specified
  // a fixed size. Instead, the implementation can check the size. 
  impl_->setParameterArray(name, (Int64)-1, array);
}

void
Region::setParameterString(const std::string& name, const std::string& s)
{
  impl_->setParameterString(name, (Int64)-1, s);
}
    
std::string
Region::getParameterString(const std::string& name)
{
  return impl_->getParameterString(name, (Int64)-1);
}

bool
Region::isParameterShared(const std::string& name) const
{
  return impl_->isParameterShared(name);
}

}

