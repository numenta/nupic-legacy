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
#include <iterator>
#include <numeric> // std::accumulate
#include <fstream>
#include <sstream>
#include <nta/engine/TestNode.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/engine/Region.hpp>
#include <nta/utils/Log.hpp>
#include <nta/ntypes/object_model.hpp> // IWrite/ReadBuffer
#include <nta/ntypes/Array.hpp>
#include <nta/ntypes/Value.hpp>
#include <nta/ntypes/BundleIO.hpp>
#include <nta/utils/Log.hpp>
#include <nta/engine/Output.hpp>
#include <nta/engine/Input.hpp>



namespace nta
{

  TestNode::TestNode(const ValueMap& params, Region *region) : RegionImpl(region),
                                                               nodeCount_(1)
  {
    // params for get/setParameter testing
    int32Param_ = params.getScalarT<Int32>("int32Param", 32);
    uint32Param_ = params.getScalarT<UInt32>("uint32Param", 33);
    int64Param_ = params.getScalarT<Int64>("int64Param", 64);
    uint64Param_ = params.getScalarT<UInt64>("uint64Param", 65);
    real32Param_ = params.getScalarT<Real32>("real32Param", 32.1);
    real64Param_ = params.getScalarT<Real64>("real64Param", 64.1);

    shouldCloneParam_ = params.getScalarT<UInt32>("shouldCloneParam", 1) != 0;
  
    stringParam_ = *params.getString("stringParam");

    computeCallback_ = NULL;

    real32ArrayParam_.resize(8);
    for (size_t i = 0; i < 8; i++)
    {
      real32ArrayParam_[i] = float(i * 32);
    }

    int64ArrayParam_.resize(4);
    for (size_t i = 0; i < 4; i++)
    {
      int64ArrayParam_[i] = i * 64;
    }

    unclonedParam_.resize(nodeCount_);
    unclonedParam_[0] = params.getScalarT<UInt32>("unclonedParam", 0);

    possiblyUnclonedParam_.resize(nodeCount_);
    possiblyUnclonedParam_[0] = params.getScalarT<UInt32>("possiblyUnclonedParam", 0);

    unclonedInt64ArrayParam_.resize(nodeCount_);
    std::vector<Int64> v(4, 0); //length 4 vector, each element == 0
    unclonedInt64ArrayParam_[0] = v;

    // params used for computation
    outputElementCount_ = 2;
    delta_ = 1;
    iter_ = 0;
  
  }

  TestNode::TestNode(BundleIO& bundle, Region* region) : 
    RegionImpl(region)
  {
    deserialize(bundle);
  }


  TestNode::~TestNode()
  {
  }



  void
  TestNode::compute()
  {
    if (computeCallback_ != NULL)
      computeCallback_(getName());

    const Array & outputArray = bottomUpOut_->getData();
    NTA_CHECK(outputArray.getCount() == nodeCount_ * outputElementCount_);
    NTA_CHECK(outputArray.getType() == NTA_BasicType_Real64);
    Real64 *baseOutputBuffer = (Real64*) outputArray.getBuffer();

    // See TestNode.hpp for description of the computation
    std::vector<Real64> nodeInput;
    Real64* nodeOutputBuffer;
    for (UInt32 node = 0; node < nodeCount_; node++)
    {
      nodeOutputBuffer = baseOutputBuffer + node * outputElementCount_;
      bottomUpIn_->getInputForNode(node, nodeInput);

      // output[0] = number of inputs to this baby node + current iteration number
      nodeOutputBuffer[0] = nta::Real64(nodeInput.size() + iter_);

      // output[n] = node + sum(inputs) + (n-1) * delta
      Real64 sum = std::accumulate(nodeInput.begin(), nodeInput.end(), 0.0);
      for (size_t i = 1; i < outputElementCount_; i++)
        nodeOutputBuffer[i] = node + sum + (i-1)*delta_;
    }

    iter_++;


  }

  Spec*
  TestNode::createSpec()
  {
    Spec *ns = new Spec;

    /* ---- parameters ------ */

    ns->parameters.add(
      "int32Param", 
      ParameterSpec(
        "Int32 scalar parameter",  // description
        NTA_BasicType_Int32,
        1,                         // elementCount
        "",                        // constraints
        "32",                      // defaultValue
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "uint32Param", 
      ParameterSpec(
        "UInt32 scalar parameter", // description
        NTA_BasicType_UInt32, 
        1,                         // elementCount
        "",                        // constraints
        "33",                      // defaultValue
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "int64Param", 
      ParameterSpec(
        "Int64 scalar parameter",  // description
        NTA_BasicType_Int64, 
        1,                         // elementCount
        "",                        // constraints
        "64",                       // defaultValue
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "uint64Param", 
      ParameterSpec(
        "UInt64 scalar parameter", // description
        NTA_BasicType_UInt64,
        1,                         // elementCount
        "",                        // constraints
        "65",                       // defaultValue
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "real32Param", 
      ParameterSpec(
        "Real32 scalar parameter",  // description
        NTA_BasicType_Real32,
        1,                         // elementCount
        "",                        // constraints
        "32.1",                    // defaultValue
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "real64Param", 
      ParameterSpec(
        "Real64 scalar parameter",  // description
        NTA_BasicType_Real64,
        1,                         // elementCount
        "",                        // constraints
        "64.1",                    // defaultValue
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "real32ArrayParam",
      ParameterSpec(
        "int32 array parameter", 
        NTA_BasicType_Real32,
        0, // array
        "", 
        "",
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "int64ArrayParam",
      ParameterSpec(
        "int64 array parameter", 
        NTA_BasicType_Int64,
        0, // array
        "", 
        "",
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "computeCallback",
      ParameterSpec(
        "address of a function that is called at every compute()",
        NTA_BasicType_Handle, 
        1,
        "", 
        "",  // handles must not have a default value
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "stringParam", 
      ParameterSpec(
        "string parameter", 
        NTA_BasicType_Byte, 
        0, // length=0 required for strings
        "", 
        "nodespec value", 
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "unclonedParam",
      ParameterSpec(
        "has a separate value for each node", //description
        NTA_BasicType_UInt32,
        1,                                    //elementCount
        "",                                   //constraints
        "",                                  //defaultValue
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "shouldCloneParam",
      ParameterSpec(
        "whether possiblyUnclonedParam should clone", //description
        NTA_BasicType_UInt32,
        1,                                            //elementCount
        "enum: 0, 1",                                 //constraints
        "1",                                          //defaultValue
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "possiblyUnclonedParam",
      ParameterSpec(
        "cloned if shouldCloneParam is true",  //description
        NTA_BasicType_UInt32,                  
        1,                                     //elementCount
        "",                                    //constraints
        "",                                   //defaultValue
        ParameterSpec::ReadWriteAccess));

    ns->parameters.add(
      "unclonedInt64ArrayParam",
      ParameterSpec(
        "has a separate array for each node", //description
        NTA_BasicType_Int64,
        0, //array                            //elementCount
        "",                                   //constraints
        "",                                   //defaultValue
        ParameterSpec::ReadWriteAccess));


    /* ----- inputs ------- */
    ns->inputs.add(
      "bottomUpIn", 
      InputSpec(
        "Primary input for the node", 
        NTA_BasicType_Real64, 
        0, // count. omit?
        true, // required?
        false, // isRegionLevel, 
        true  // isDefaultOutput
        ));

    /* ----- outputs ------ */
    ns->outputs.add(
      "bottomUpOut", 
      OutputSpec(
        "Primary output for the node", 
        NTA_BasicType_Real64,
        0, // count is dynamic
        false, // isRegionLevel
        true // isDefaultOutput
        ));

    /* ----- commands ------ */
    // commands TBD

    return ns;
  }


#include <string.h>

  Real64 TestNode::getParameterReal64(const std::string& name, Int64 index)
  {
    if (name == "real64Param")
    {
      return real64Param_;
    }
    else 
    {
      NTA_THROW << "TestNode::getParameter<Int64> -- unknown parameter " << name;
    }
  }


  void TestNode::setParameterReal64(const std::string& name, Int64 index, Real64 value)
  {
    if (name == "real64Param")
    {
      real64Param_ = value;
    }
    else 
    {
      NTA_THROW << "TestNode::setParameter<Int64> -- unknown parameter " << name;
    }
  }


  void TestNode::getParameterFromBuffer(const std::string& name, 
                                        Int64 index, 
                                        IWriteBuffer& value)
  {
    if (name == "int32Param") {
      value.write(int32Param_);
    } else if (name == "uint32Param") {
      value.write(uint32Param_);
    } else if (name == "int64Param") {
      value.write(int64Param_);
    } else if (name == "uint64Param") {
      value.write(uint64Param_);
    } else if (name == "real32Param") {
      value.write(real32Param_);
    } else if (name == "real64Param") {
      value.write(real64Param_);
    } else if (name == "stringParam") {
      value.write(stringParam_.c_str(), stringParam_.size());
    } else if (name == "int64ArrayParam") {
      for (size_t i = 0; i < int64ArrayParam_.size(); i++)
      {
        value.write(int64ArrayParam_[i]);
      }
    } else if (name == "real32ArrayParam") {
      for (size_t i = 0; i < real32ArrayParam_.size(); i++)
      {
        value.write(real32ArrayParam_[i]);
      }
    } else if (name == "unclonedParam") {
      if (index < 0)
      {
        NTA_THROW << "uncloned parameters cannot be accessed at region level";
      }
      value.write(unclonedParam_[(UInt)index]);
    } else if (name == "shouldCloneParam") {
      value.write((UInt32)(shouldCloneParam_ ? 1 : 0));
    } else if (name == "possiblyUnclonedParam") {
      if (shouldCloneParam_)
      {
        value.write(possiblyUnclonedParam_[0]);
      }
      else 
      {
        if (index < 0)
        {
          NTA_THROW << "uncloned parameters cannot be accessed at region level";
        }
        value.write(possiblyUnclonedParam_[(UInt)index]);
      }
    } else if (name == "unclonedInt64ArrayParam") {
      if (index < 0)
      {
        NTA_THROW << "uncloned parameters cannot be accessed at region level";
      }
      UInt nodeIndex = (UInt)index;
      for (size_t i = 0; i <  unclonedInt64ArrayParam_[nodeIndex].size(); i++)
      {
        value.write(unclonedInt64ArrayParam_[nodeIndex][i]);
      }
    } else {
      NTA_THROW << "TestNode::getParameter -- Unknown parameter " << name;
    }
  }

  void TestNode::setParameterFromBuffer(const std::string& name, 
                                        Int64 index,
                                        IReadBuffer& value)
  {
    if (name == "int32Param") {
      value.read(int32Param_);
    } else if (name == "uint32Param") {
      value.read(uint32Param_);
    } else if (name == "int64Param") {
      value.read(int64Param_);
    } else if (name == "uint64Param") {
      value.read(uint64Param_);
    } else if (name == "real32Param") {
      value.read(real32Param_);
    } else if (name == "real64Param") {
      value.read(real64Param_);
    } else if (name == "stringParam") {
      stringParam_ = std::string(value.getData(), value.getSize());
    } else if (name == "int64ArrayParam") {
      for (size_t i = 0; i < int64ArrayParam_.size(); i++)
      {
        value.read(int64ArrayParam_[i]);
      }
    } else if (name == "real32ArrayParam") {
      for (size_t i = 0; i < real32ArrayParam_.size(); i++)
      {
        value.read(real32ArrayParam_[i]);
      }
    } else if (name == "unclonedParam") {
      if (index < 0)
      {
        NTA_THROW << "uncloned parameters cannot be accessed at region level";
      }
      value.read(unclonedParam_[(UInt)index]);
    } else if (name == "shouldCloneParam") {
      UInt64 ival;
      value.read(ival);
      shouldCloneParam_ = (ival ? 1 : 0);
    } else if (name == "possiblyUnclonedParam") {
      if (shouldCloneParam_)
      {
        value.read(possiblyUnclonedParam_[0]);
      }
      else 
      {
        if (index < 0)
        {
          NTA_THROW << "uncloned parameters cannot be accessed at region level";
        }
        value.read(possiblyUnclonedParam_[(UInt)index]);
      }
    } else if (name == "unclonedInt64ArrayParam") {
      if (index < 0)
      {
        NTA_THROW << "uncloned parameters cannot be accessed at region level";
      }
      UInt nodeIndex = (UInt)index;
      for (size_t i = 0; i <  unclonedInt64ArrayParam_[nodeIndex].size(); i++)
      {
        value.read(unclonedInt64ArrayParam_[nodeIndex][i]);
      }
    } else if (name == "computeCallback") {
      UInt64 ival;
      value.read(ival);
      computeCallback_ = (computeCallbackFunc)ival;
    } else {
      NTA_THROW << "TestNode::setParameter -- Unknown parameter " << name;
    }

  }

  size_t TestNode::getParameterArrayCount(const std::string& name, Int64 index)
  {
    if (name == "int64ArrayParam") 
    {
      return int64ArrayParam_.size();
    }
    else if (name == "real32ArrayParam") 
    {
      return real32ArrayParam_.size();
    }
    else if (name == "unclonedInt64ArrayParam")
    {
      if (index < 0)
      {
        NTA_THROW << "uncloned parameters cannot be accessed at region level";
      }
      return unclonedInt64ArrayParam_[(UInt)index].size();
    }
    else 
    {
      NTA_THROW << "TestNode::getParameterArrayCount -- unknown parameter " << name;
    }
  }


  void TestNode::initialize()
  {
    nodeCount_ = getDimensions().getCount();
    bottomUpOut_ = getOutput("bottomUpOut");
    bottomUpIn_ = getInput("bottomUpIn");

    unclonedParam_.resize(nodeCount_);
    for (unsigned int i = 1; i < nodeCount_; i++)
    {
      unclonedParam_[i] = unclonedParam_[0];
    }

    if (! shouldCloneParam_)
    {
      possiblyUnclonedParam_.resize(nodeCount_);
      for (unsigned int i = 1; i < nodeCount_; i++)
      {
        possiblyUnclonedParam_[i] = possiblyUnclonedParam_[0];
      }
    }

    unclonedInt64ArrayParam_.resize(nodeCount_);
    std::vector<Int64> v(4, 0); //length 4 vector, each element == 0
    for (unsigned int i = 1; i < nodeCount_; i++)
    {
      unclonedInt64ArrayParam_[i] = v;
    }
  }


// This is the per-node output size
  size_t TestNode::getNodeOutputElementCount(const std::string& outputName)
  {
    if (outputName == "bottomUpOut")
    {
      return outputElementCount_;
    }
    NTA_THROW << "TestNode::getOutputSize -- unknown output " << outputName;
  }

  std::string TestNode::executeCommand(const std::vector<std::string>& args, Int64 index)
  {
    return "";
  }

  bool TestNode::isParameterShared(const std::string& name)
  {
    if ((name == "int32Param") ||
        (name == "uint32Param") ||
        (name == "int64Param") ||
        (name == "uint64Param") ||
        (name == "real32Param") ||
        (name == "real64Param") ||
        (name == "stringParam") ||
        (name == "int64ArrayParam") ||
        (name == "real32ArrayParam") ||
        (name == "shouldCloneParam")) {
      return true;
    } else if ((name == "unclonedParam") ||
               (name == "unclonedInt64ArrayParam")) {
      return false;
    } else if (name == "possiblyUnclonedParam") {
      return shouldCloneParam_;
    } else {
      NTA_THROW << "TestNode::isParameterShared -- Unknown parameter " << name;
    }
  }

  template <typename T> static void 
  arrayOut(std::ostream& s, const std::vector<T>& array, const std::string& name)
  {
    s << "ARRAY_" << name << " ";
    s << array.size() << " "; 
    for (size_t ix = 0; ix < array.size(); ix++)
    {
      s << array[ix] << " ";
    }
  }

  template <typename T> static void
  arrayIn(std::istream& s, std::vector<T>& array, const std::string& name)
  {                                                                     
    std::string expectedCookie = std::string("ARRAY_") + name;
    std::string cookie;
    s >> cookie;
    if (cookie != expectedCookie)
      NTA_THROW << "Bad cookie '" << cookie << "' for serialized array. Expected '" << expectedCookie << "'";
    size_t sz;
    s >> sz;
    array.resize(sz);
    for (size_t ix = 0; ix < sz; ix++)
    {
      s >> array[ix];
    }
  }


  void TestNode::serialize(BundleIO& bundle)
  {
    {
      std::ofstream& f = bundle.getOutputStream("main");
      // There is more than one way to do this. We could serialize to YAML, which 
      // would make a readable format, or we could serialize directly to the stream
      // Choose the easier one. 
      f << "TestNode-v1" << " "
        << nodeCount_ << " "
        << int32Param_ << " "
        << uint32Param_ << " "
        << int64Param_ << " "
        << uint64Param_ << " "
        << real32Param_ << " "
        << real64Param_ << " "
        << outputElementCount_ << " "
        << delta_ << " "
        << iter_ << " ";

      arrayOut(f, real32ArrayParam_, "real32ArrayParam_");
      arrayOut(f, int64ArrayParam_, "int64ArrayParam_");
      arrayOut(f, unclonedParam_, "unclonedParam_");
      f << shouldCloneParam_ << " ";
    
      // outer vector needs to be done by hand. 
      f << "unclonedArray ";
      f << unclonedInt64ArrayParam_.size() << " "; // number of nodes
      for (size_t i = 0; i < unclonedInt64ArrayParam_.size(); i++)
      {
        std::stringstream name;
        name << "unclonedInt64ArrayParam[" << i << "]";
        arrayOut(f, unclonedInt64ArrayParam_[i], name.str());
      }
      f.close();
    }  // main file


    // auxilliary file using stream
    {
      std::ofstream& f = bundle.getOutputStream("aux");
      f << "This is an auxilliary file!\n";
      f.close();
    }

    // auxilliary file using path
    {
      std::string path = bundle.getPath("aux2");
      std::ofstream f(path.c_str());
      f << "This is another auxilliary file!\n";
      f.close();
    }
  }


  void TestNode::deserialize(BundleIO& bundle)
  {
    {
      std::ifstream& f = bundle.getInputStream("main");
      // There is more than one way to do this. We could serialize to YAML, which 
      // would make a readable format, or we could serialize directly to the stream
      // Choose the easier one. 
      std::string versionString;
      f >> versionString;
      if (versionString != "TestNode-v1")
      {
        NTA_THROW << "Bad serialization for region '" << region_->getName() 
                  << "' of type TestNode. Main serialization file must start "
                  << "with \"TestNode-v1\" but instead it starts with '"
                  << versionString << "'";

      }
      f >> nodeCount_;
      f >> int32Param_;
      f >> uint32Param_;
      f >> int64Param_;
      f >> uint64Param_;
      f >> real32Param_;
      f >> real64Param_;
      f >> outputElementCount_;
      f >> delta_;
      f >> iter_;

      arrayIn(f, real32ArrayParam_, "real32ArrayParam_");
      arrayIn(f, int64ArrayParam_, "int64ArrayParam_");
      arrayIn(f, unclonedParam_, "unclonedParam_");

      f >> shouldCloneParam_;

      std::string label;
      f >> label;
      if (label != "unclonedArray")
        NTA_THROW << "Missing label for uncloned array. Got '" << label << "'";
      size_t vecsize;
      f >> vecsize;
      unclonedInt64ArrayParam_.clear();
      unclonedInt64ArrayParam_.resize(vecsize);
      for (size_t i = 0; i < vecsize; i++)
      {
        std::stringstream name;
        name << "unclonedInt64ArrayParam[" << i << "]";
        arrayIn(f, unclonedInt64ArrayParam_[i], name.str());
      }
      f.close();
    }  // main file

    // auxilliary file using stream
    {
      std::ifstream& f = bundle.getInputStream("aux");
      char line1[100];
      f.read(line1, 100);
      line1[f.gcount()] = '\0';
      if (std::string(line1) != "This is an auxilliary file!\n")
      {
        NTA_THROW << "Invalid auxilliary serialization file for TestNode";
      }
      f.close();
    }

    // auxilliary file using path
    {
      std::string path = bundle.getPath("aux2");
      std::ifstream f(path.c_str());
      char line1[100];
      f.read(line1, 100);
      line1[f.gcount()] = '\0';
      if (std::string(line1) != "This is another auxilliary file!\n")
      {
        NTA_THROW << "Invalid auxilliary2 serialization file for TestNode";
      }

      f.close();
    }
  }

}

