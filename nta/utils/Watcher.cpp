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
 * Implementation of the Watcher class
 */

#include <sstream>
#include <string>
#include <vector>
#include <exception>

#include <nta/utils/Watcher.hpp>
#include <nta/engine/Region.hpp>
#include <nta/engine/Output.hpp>
#include <nta/engine/Network.hpp>
#include <nta/os/FStream.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/utils/Log.hpp>
#include <nta/types/BasicType.hpp>
#include <nta/ntypes/Array.hpp>
#include <nta/types/types.h>

namespace nta
{

  Watcher::Watcher(std::string fileName)
  {
    data_.fileName = fileName;
    try 
    {
      data_.outStream = new OFStream(fileName.c_str());
    }
    catch (std::exception &)
    {
      NTA_THROW << "Unable to open filename " << fileName << " for network watcher";
    }
  }

  Watcher::~Watcher()
  {
    this->flushFile();
    this->closeFile();
    delete data_.outStream;
  }

  unsigned int Watcher::watchParam(std::string regionName,
                                   std::string varName,
                                   int nodeIndex,
                                   bool sparseOutput)
  {
    watchData watch;
    watch.varName = varName;
    watch.wType = parameter;
    watch.regionName = regionName;
    watch.nodeIndex = nodeIndex;
    watch.sparseOutput = sparseOutput;
    watch.watchID = data_.watches.size()+1;
    data_.watches.push_back(watch);
    return watch.watchID;
  }

  unsigned int Watcher::watchOutput(std::string regionName,
                                    std::string varName,
                                    bool sparseOutput)
  {
    watchData watch;
    watch.varName = varName;
    watch.wType = output;
    watch.regionName = regionName;
    watch.nodeIndex = -1;
    watch.isArray = false;
    watch.sparseOutput = sparseOutput;
    watch.watchID = data_.watches.size()+1;
    data_.watches.push_back(watch);
    return watch.watchID;
  }

  //TODO: clean up, add support for uncloned arrays,
  //add support for output of a different type than Real32
  void Watcher::watcherCallback(Network* net, UInt64 iteration, void* dataIn)
  {
    allData& data = *(static_cast<allData*>(dataIn));
    //iterate through each watch
    for (UInt i = 0; i < data.watches.size(); i++)
    {
      watchData watch = data.watches.at(i);
      std::string value;
      std::stringstream out;
      if (watch.wType == parameter)
      {
        if (watch.isArray) //currently don't support uncloned arrays
        {
          switch(watch.varType)
          {
          case NTA_BasicType_Int32:
          {
            Array a(NTA_BasicType_Int32);
            watch.region->getParameterArray(watch.varName, a);
            Int32* buf = (Int32*) a.getBuffer();
            out << a.getCount();
            if (watch.sparseOutput)
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                if (buf[j] != (Int32)0)
                  out << " " << j;
              }
            }
            else
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                out << " " << buf[j];
              }
            }
            break;
          }
          case NTA_BasicType_UInt32:
          {
            Array a(NTA_BasicType_UInt32);
            watch.region->getParameterArray(watch.varName, a);
            UInt32* buf = (UInt32*) a.getBuffer();
            out << a.getCount();
            if (watch.sparseOutput)
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                if (buf[j] != (UInt32)0)
                  out << " " << j;
              }
            }
            else
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                out << " " << buf[j];
              }
            }
            break;
          }
          case NTA_BasicType_Int64:
          {
            Array a(NTA_BasicType_Int64);
            watch.region->getParameterArray(watch.varName, a);
            Int64* buf = (Int64*) a.getBuffer();
            out << a.getCount();
            if (watch.sparseOutput)
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                if (buf[j] != (Int64)0)
                  out << " " << j;
              }
            }
            else
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                out << " " << buf[j];
              }
            }
            break;
          }
          case NTA_BasicType_UInt64:
          {
            Array a(NTA_BasicType_UInt64);
            watch.region->getParameterArray(watch.varName, a);
            UInt64* buf = (UInt64*) a.getBuffer();
            out << a.getCount();
            if (watch.sparseOutput)
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                if (buf[j] != (UInt64)0)
                  out << " " << j;
              }
            }
            else
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                out << " " << buf[j];
              }
            }
            break;
          }
          case NTA_BasicType_Real32:
          {
            Array a(NTA_BasicType_Real32);
            watch.region->getParameterArray(watch.varName, a);
            Real32* buf = (Real32*) a.getBuffer();
            out << a.getCount();
            if (watch.sparseOutput)
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                if (buf[j] != (Real32)0)
                  out << " " << j;
              }
            }
            else
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                out << " " << buf[j];
              }
            }
            break;
          }
          case NTA_BasicType_Real64:
          {
            Array a(NTA_BasicType_Real64);
            watch.region->getParameterArray(watch.varName, a);
            Real64* buf = (Real64*) a.getBuffer();
            out << a.getCount();
            if (watch.sparseOutput)
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                if (buf[j] != (Real64)0)
                  out << " " << j;
              }
            }
            else
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                out << " " << buf[j];
              }
            }
            break;
          }
          case NTA_BasicType_Byte:
          {
            Array a(NTA_BasicType_Byte);
            watch.region->getParameterArray(watch.varName, a);
            Byte* buf = (Byte*) a.getBuffer();
            out << a.getCount();
            if (watch.sparseOutput)
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                out << " " << buf[j];
              }
            }
            else
            {
              for (UInt j = 0; j < a.getCount(); j++)
              {
                out << " " << buf[j];
              }
            }
            break;
          }
          default:
            NTA_THROW << "Internal error.";
          }
        }
        else if (watch.nodeIndex == -1) 
        {
          switch (watch.varType)
          {
          case NTA_BasicType_Int32:
          {
            Int32 p = watch.region->getParameterInt32(watch.varName);
            out << p;
            break;
          }
          case NTA_BasicType_UInt32:
          {
            UInt32 p = watch.region->getParameterUInt32(watch.varName);
            out << p;
            break;
          }
          case NTA_BasicType_Int64:
          {
            Int64 p = watch.region->getParameterInt64(watch.varName);
            out << p;
            break;
          }
          case NTA_BasicType_UInt64:
          {
            UInt64 p = watch.region->getParameterUInt64(watch.varName);
            out << p;
            break;
          }
          case NTA_BasicType_Real32:
          {
            Real32 p = watch.region->getParameterReal32(watch.varName);
            out << p;
            break;
          }
          case NTA_BasicType_Real64:
          {
            Real64 p = watch.region->getParameterReal64(watch.varName);
            out << p;
            break;
          }
          case NTA_BasicType_Byte:
          {
            std::string p = watch.region->getParameterString(watch.varName);
            out << p;
            break;
          }
          default:
            NTA_THROW << "Internal error.";
          }
        }
        //else //nodeIndex != -1
        //{
        //  Node n = watch.region->getNodeAtIndex((size_t)watch.nodeIndex);
        //  switch (watch.varType)
        //  {
        //  case NTA_BasicType_Int32:
        //  {
        //    Int32 p = n.getParameterInt32(watch.varName);
        //    out << p;
        //    break;
        //  }
        //  case NTA_BasicType_UInt32:
        //  {
        //    UInt32 p = n.getParameterUInt32(watch.varName);
        //    out << p;
        //    break;
        //  }
        //  case NTA_BasicType_Int64:
        //  {
        //    Int64 p = n.getParameterInt64(watch.varName);
        //    out << p;
        //    break;
        //  }
        //  case NTA_BasicType_UInt64:
        //  {
        //    UInt64 p = n.getParameterUInt64(watch.varName);
        //    out << p;
        //    break;
        //  }
        //  case NTA_BasicType_Real32:
        //  {
        //    Real32 p = n.getParameterReal32(watch.varName);
        //    out << p;
        //    break;
        //  }
        //  case NTA_BasicType_Real64:
        //  {
        //    Real64 p = n.getParameterReal64(watch.varName);
        //    out << p;
        //    break;
        //  }
        //  case NTA_BasicType_Byte:
        //  {
        //    std::string p = n.getParameterString(watch.varName);
        //    out << p;
        //    break;
        //  }
        //  default:
        //    NTA_THROW << "Internal error.";
        //  }
        //}
      }
      else if (watch.wType == output)
      {
        switch (watch.varType)
        {
        case NTA_BasicType_Real32:
        {
          Real32* outputData = (Real32*)(watch.array->getBuffer());
          unsigned int numOuts = watch.array->getCount();
          out << numOuts;
          
          if (watch.sparseOutput)
          {
            for (UInt j = 0; j < numOuts; j++)
            {
              if (outputData[j] != (Real32)0)
              {
                out << " " << j;
              }
            }
          }
          else
          {
            for (UInt j = 0; j < numOuts; j++)
            {
              out << " " << outputData[j];
            }
          }
          break;
        }
        case NTA_BasicType_Real64:
        {
          Real64* outputData = (Real64*)(watch.array->getBuffer());
          unsigned int numOuts = watch.array->getCount();
          out << numOuts;
          
          if (watch.sparseOutput)
          {
            for (UInt j = 0; j < numOuts; j++)
            {
              if (outputData[j] != (Real64)0)
              {
                out << " " << j;
              }
            }
          }
          else
          {
            for (UInt j = 0; j < numOuts; j++)
            {
              out << " " << outputData[j];
            }
          }
          break;
        }
        default:
          NTA_THROW << "Watcher only supports Real32 or Real64 outputs.";
        }
      }
      else //should never happen
      {
        NTA_THROW << "Watcher can only watch parameters or outputs.";
      }
      
      value = out.str();

      (*data.outStream) << watch.watchID << ", " << iteration << ", " << value << "\n";
    }
    data.outStream->flush();
  }

  void Watcher::closeFile()
  {
    data_.outStream->close();
  }

  void Watcher::flushFile()
  {
    data_.outStream->flush();
  }

  //attach Watcher to a network and do initial writing to files
  void Watcher::attachToNetwork(Network& net)
  {
    (*data_.outStream) << "Info: watchID, regionName, nodeType, nodeIndex, varName" << "\n";

    //go through each watch
    watchData watch;

    for (UInt i = 0; i < data_.watches.size(); i++)
    {
      watch = data_.watches.at(i);
      const Collection<Region*>& regions = net.getRegions();
      watch.region = regions.getByName(watch.regionName);

      //output general information for each watch
      (*data_.outStream) << watch.watchID << ", ";
      (*data_.outStream) << watch.regionName << ", ";
      (*data_.outStream) << watch.region->getType() << ", ";
      (*data_.outStream) << watch.nodeIndex  << ", ";

      if (watch.wType == parameter)
      {
        //find out varType and add it to watch struct
        ParameterSpec p = watch.region->getSpec()->parameters.getByName(watch.varName);
        watch.varType = p.dataType;

        //find out if varType is supported
        if (watch.varType != NTA_BasicType_Int32 &&
            watch.varType != NTA_BasicType_UInt32 &&
            watch.varType != NTA_BasicType_Int64 &&
            watch.varType != NTA_BasicType_UInt64 &&
            watch.varType != NTA_BasicType_Real32 &&
            watch.varType != NTA_BasicType_Real64 &&
            watch.varType != NTA_BasicType_Byte)
        {
          NTA_THROW << BasicType::getName(watch.varType) << " is not an "
                      << "array parameter type supported by Watcher.";
        }
        
        //found out whether parameter is an array or not
        watch.isArray = ((p.count == 0 || p.count > 1)
                         && watch.varType != NTA_BasicType_Byte);

        (*data_.outStream) << watch.varName << "\n";
      }
      else if (watch.wType == output)
      {
        watch.output = watch.region->getOutput(watch.varName);
        (*data_.outStream) << watch.varName << "\n";

        watch.array = &(watch.output->getData());

        watch.varType = watch.array->getType();

      }
      else //should never happen
      {
        NTA_THROW << "Watcher can only watch parameters or outputs.";
      }

      //add the modified watch struct to data_.watches
      allWatchData::iterator it;
      it = data_.watches.begin()+i;
      data_.watches.erase(it);
      data_.watches.insert(it, watch);
    }

    (*data_.outStream) << "Data: watchID, iteration, paramValue" << "\n";
    
    //actually attach to the network
    Collection<Network::callbackItem>& callbacks = net.getCallbacks();
    Network::callbackItem callback(watcherCallback, (void*)(&data_));
    std::string callbackName = "Watcher: ";
    callbackName += data_.fileName;
    callbacks.add(callbackName, callback);
  }

  void Watcher::detachFromNetwork(Network& net)
  {
    Collection<Network::callbackItem>& callbacks = net.getCallbacks();
    std::string callbackName = "Watcher: ";
    callbackName += data_.fileName;
    callbacks.remove(callbackName);
  }
}
