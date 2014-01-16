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
 * Implementation of the ArrayBase class
 */

#include <nta/types/types.hpp>
#include <nta/types/BasicType.hpp>
#include <nta/ntypes/ArrayBase.hpp>
#include <nta/utils/Log.hpp>

using namespace nta;

/**
 * Caller provides a buffer to use. 
 * NuPIC always copies data into this buffer
 * Caller frees buffer when no longer needed. 
 */
ArrayBase::ArrayBase(NTA_BasicType type, void* buffer, size_t count) :
  buffer_((char*)buffer), count_(count), type_(type), own_(false)
{
  if(!BasicType::isValid(type))
  {
    NTA_THROW << "Invalid NTA_BasicType " << type << " used in array constructor";
  }
}

/**
 * Caller does not provide a buffer --
 * Nupic will either provide a buffer via setBuffer or 
 * ask the ArrayBase to allocate a buffer via allocateBuffer.
 */
ArrayBase::ArrayBase(NTA_BasicType type) :
  buffer_(NULL), count_(0), type_(type), own_(false)
{
  if(!BasicType::isValid(type))
  {
    NTA_THROW << "Invalid NTA_BasicType " << type << " used in array constructor";
  }
}

/**
 * The destructor calls releaseBuffer() to make sure the ArrayBase
 * doesn't leak.
 */
ArrayBase::~ArrayBase()
{
  releaseBuffer();
}

/**
 * Ask ArrayBase to allocate its buffer
 */
void
ArrayBase::allocateBuffer(size_t count)
{
  if (buffer_ != NULL)
  {
    NTA_THROW << "allocateBuffer -- buffer already set. Use releaseBuffer first";
  }
  count_ = count;
  //Note that you can allocate a buffer of size zero.
  //The C++ spec (5.3.4/7) requires such a new request to return
  //a non-NULL value which is safe to delete.  This allows us to
  //disambiguate uninitialized ArrayBases and ArrayBases initialized with
  //size zero.
  buffer_ = new char[count_ * BasicType::getSize(type_)];
  own_ = true;
}
  
void
ArrayBase::setBuffer(void *buffer, size_t count)
{
  if (buffer_ != NULL)
  {
    NTA_THROW << "setBuffer -- buffer already set. Use releaseBuffer first";
  }
  buffer_ = (char*)buffer;
  count_ = count;
  own_ = false;
}

void
ArrayBase::releaseBuffer()
{
  if (buffer_ == NULL)
    return;
  if (own_)
    delete[] buffer_;
  buffer_ = NULL;
  count_ = 0;
}
       
void* 
ArrayBase::getBuffer() const
{ 
  return buffer_; 
}

// number of elements of given type in the buffer
size_t
ArrayBase::getCount() const
{ 
  return count_; 
};
     
NTA_BasicType 
ArrayBase::getType() const
{ 
  return type_; 
};



