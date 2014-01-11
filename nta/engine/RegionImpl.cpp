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


#include <iostream>

#include <nta/engine/RegionImpl.hpp>
#include <nta/ntypes/Buffer.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/types/BasicType.hpp>
#include <nta/engine/Region.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/ntypes/Dimensions.hpp>
#include <nta/ntypes/BundleIO.hpp>
#include <nta/os/FStream.hpp>

namespace nta
{

RegionImpl::RegionImpl(Region *region) : 
  region_(region)
{
}

RegionImpl::~RegionImpl()
{
}

// convenience method
const std::string& RegionImpl::getType() const
{
  return region_->getType();
}

const std::string& RegionImpl::getName() const
{ 
  return region_->getName();
}

const NodeSet& RegionImpl::getEnabledNodes() const
{
  return region_->getEnabledNodes();
}


/* ------------- Parameter support --------------- */
// By default, all typed getParameter calls forward to the
// untyped getParameter that serializes to a buffer

// Use macros to implement these methods. 
// This is similar to a template + explicit instantiation, but
// templated methods can't be virtual and thus can't be
// overridden by subclasses. 

#define getParameterT(Type) \
Type RegionImpl::getParameter##Type(const std::string& name, Int64 index) \
{\
  if (! region_->getSpec()->parameters.contains(name))     \
    NTA_THROW << "getParameter" #Type ": parameter " << name << " does not exist in nodespec"; \
  ParameterSpec p = region_->getSpec()->parameters.getByName(name); \
  if (p.dataType != NTA_BasicType_ ## Type) \
    NTA_THROW << "getParameter" #Type ": parameter " << name << " is of type " \
              << BasicType::getName(p.dataType) << " not " #Type; \
  WriteBuffer wb; \
  getParameterFromBuffer(name, index, wb); \
  ReadBuffer rb(wb.getData(), wb.getSize(), false /* copy */); \
  Type val; \
  int rc = rb.read(val); \
  if (rc != 0)  \
  { \
    NTA_THROW << "getParameter" #Type " -- failure to get parameter '"  \
              << name << "' on node of type " << getType(); \
  } \
  return val; \
}

getParameterT(Int32);
getParameterT(UInt32);
getParameterT(Int64);
getParameterT(UInt64)
getParameterT(Real32);
getParameterT(Real64);


#define setParameterT(Type) \
void RegionImpl::setParameter##Type(const std::string& name, Int64 index, Type value) \
{ \
  WriteBuffer wb; \
  wb.write((Type)value); \
  ReadBuffer rb(wb.getData(), wb.getSize(), false /* copy */); \
  setParameterFromBuffer(name, index, rb); \
}

setParameterT(Int32);
setParameterT(UInt32);
setParameterT(Int64);
setParameterT(UInt64)
setParameterT(Real32);
setParameterT(Real64);

// buffer mechanism can't handle Handles. RegionImpl must override these methods. 
Handle RegionImpl::getParameterHandle(const std::string& name, Int64 index)
{
  NTA_THROW << "Unknown parameter '"  << name << "' of type Handle.";
}

void RegionImpl::setParameterHandle(const std::string& name, Int64 index, Handle h)
{
  NTA_THROW << "Unknown parameter '"  << name << "' of type Handle.";
}  



void RegionImpl::getParameterArray(const std::string& name, Int64 index, Array & array)
{
  WriteBuffer wb;
  getParameterFromBuffer(name, index, wb);
  ReadBuffer rb(wb.getData(), wb.getSize(), false /* copy */);
  size_t count = array.getCount();
  void *buffer = array.getBuffer();

  for (size_t i = 0; i < count; i++)
  { 
    int rc;
    switch (array.getType())
    {

    case NTA_BasicType_Byte:
      rc = rb.read(((Byte*)buffer)[i]);
      break;
    case NTA_BasicType_Int32:
      rc = rb.read(((Int32*)buffer)[i]);
      break;
    case NTA_BasicType_UInt32:
      rc = rb.read(((UInt32*)buffer)[i]);
      break;
    case NTA_BasicType_Int64:
      rc = rb.read(((Int64*)buffer)[i]);
      break;
    case NTA_BasicType_UInt64:
      rc = rb.read(((UInt64*)buffer)[i]);
      break;
    case NTA_BasicType_Real32:
      rc = rb.read(((Real32*)buffer)[i]);
      break;
    case NTA_BasicType_Real64:
      rc = rb.read(((Real64*)buffer)[i]);
      break;
    default:
      NTA_THROW << "Unsupported basic type " << BasicType::getName(array.getType())
                << " in getParameterArray for parameter " << name;
      break;
    }
    
    if (rc != 0)
    {
      NTA_THROW << "getParameterArray -- failure to get parameter '"
                << name << "' on node of type " << getType();
    }
  }
  return;
}


void RegionImpl::setParameterArray(const std::string& name, Int64 index,const Array & array)
{
  WriteBuffer wb;
  size_t count = array.getCount();
  void *buffer = array.getBuffer();
  for (size_t i = 0; i < count; i++)
  { 
    int rc;
    switch (array.getType())
    {

    case NTA_BasicType_Byte:
      rc = wb.write(((Byte*)buffer)[i]);
      break;
    case NTA_BasicType_Int32:
      rc = wb.write(((Int32*)buffer)[i]);
      break;
    case NTA_BasicType_UInt32:
      rc = wb.write(((UInt32*)buffer)[i]);
      break;
    case NTA_BasicType_Int64:
      rc = wb.write(((Int64*)buffer)[i]);
      break;
    case NTA_BasicType_UInt64:
      rc = wb.write(((UInt64*)buffer)[i]);
      break;
    case NTA_BasicType_Real32:
      rc = wb.write(((Real32*)buffer)[i]);
      break;
    case NTA_BasicType_Real64:
      rc = wb.write(((Real64*)buffer)[i]);
      break;
    default:
      NTA_THROW << "Unsupported basic type " << BasicType::getName(array.getType())
                << " in setParameterArray for parameter " << name;
      break;
    }

    NTA_ASSERT(rc == 0) << "getParameterArray - failure to get parameter '" << name << "' on node of type " << getType();
  }

  ReadBuffer rb(wb.getData(), wb.getSize(), false);
  setParameterFromBuffer(name, index, rb);
}


void RegionImpl::setParameterString(const std::string& name, Int64 index, const std::string& s)
{
  ReadBuffer rb(s.c_str(), s.size(), false);
  setParameterFromBuffer(name, index, rb);
}

std::string RegionImpl::getParameterString(const std::string& name, Int64 index)
{
  WriteBuffer wb;
  getParameterFromBuffer(name, index, wb);
  return std::string(wb.getData(), wb.getSize());
}


// Must be overridden by subclasses
bool RegionImpl::isParameterShared(const std::string& name)
{
  NTA_THROW << "RegionImpl::isParameterShared was not overridden in node type " << getType();
}

void RegionImpl::getParameterFromBuffer(const std::string& name, 
                             Int64 index, 
                             IWriteBuffer& value)
{
  NTA_THROW << "RegionImpl::getParameterFromBuffer must be overridden by subclasses";
}

void RegionImpl::setParameterFromBuffer(const std::string& name, 
                          Int64 index,
                          IReadBuffer& value)
{
  NTA_THROW << "RegionImpl::setParameterFromBuffer must be overridden by subclasses";
}



size_t RegionImpl::getParameterArrayCount(const std::string& name, Int64 index)
{
  // Default implementation for RegionImpls with no array parameters
  // that have a dynamic length. 
  //std::map<std::string, ParameterSpec*>::iterator i = nodespec_->parameters.find(name);
  //if (i == nodespec_->parameters.end())

  
  if (!region_->getSpec()->parameters.contains(name))
  {
    NTA_THROW << "getParameterArrayCount -- no parameter named '" 
              << name << "' in node of type " << getType();
  }
  UInt32 count = region_->getSpec()->parameters.getByName(name).count;
  if (count == 0)
  {
    NTA_THROW << "Internal Error -- unknown element count for "
              << "node type " << getType() << ". The RegionImpl "
              << "implementation should override this method.";
  }

  return count;
}


// Provide data access for subclasses

const Input* RegionImpl::getInput(const std::string& name)
{
  return region_->getInput(name);
}

const Output* RegionImpl::getOutput(const std::string& name)
{
  return region_->getOutput(name);
}

const Dimensions& RegionImpl::getDimensions()
{
  return region_->getDimensions();
}

}

