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


#ifndef NTA_TESTNODE_HPP
#define NTA_TESTNODE_HPP


#include <nta/engine/RegionImpl.hpp>
#include <nta/ntypes/Value.hpp>
#include <string>
#include <vector>

namespace nta 
{
  
  /*
   * TestNode is does simple computations of inputs->outputs
   * inputs and outputs are Real64 arrays
   * 
   * delta is a parameter used for the computation. defaults to 1
   * 
   * Size of each node output is given by the outputSize parameter (cg)
   * which defaults to 2 and cannot be less than 1. (parameter not yet implemented)
   * 
   * Here is the totally lame "computation"
   * output[0] = number of inputs to this baby node + current iteration number (0 for first compute)
   * output[1] = baby node num + sum of inputs to this baby node 
   * output[2] = baby node num + sum of inputs + (delta)
   * output[3] = baby node num + sum of inputs + (2*delta)
   * ...
   * output[n] = baby node num + sum of inputs + ((n-1) * delta)

   * It can act as a sensor if no inputs are connected (sum of inputs = 0)
   */

  class BundleIO;

  class TestNode : public RegionImpl 
  {
  public:
    typedef void (*computeCallbackFunc)(const std::string&);
    TestNode(const ValueMap& params, Region *region);
    TestNode(BundleIO& bundle, Region* region);
    virtual ~TestNode();

    /* -----------  Required RegionImpl Interface methods ------- */

    // Used by RegionImplFactory to create and cache
    // a nodespec. Ownership is transferred to the caller. 
    static Spec* createSpec();

    std::string getNodeType() { return "TestNode"; };
    void compute();
    std::string executeCommand(const std::vector<std::string>& args, Int64 index);

    size_t getNodeOutputElementCount(const std::string& outputName);
    void getParameterFromBuffer(const std::string& name, Int64 index, IWriteBuffer& value);
    void setParameterFromBuffer(const std::string& name, Int64 index, IReadBuffer& value);

    void initialize();

    void serialize(BundleIO& bundle);
    void deserialize(BundleIO& bundle);


    /* -----------  Optional RegionImpl Interface methods ------- */

    size_t getParameterArrayCount(const std::string& name, Int64 index);

    // Override for Real64 only
    // We choose Real64 in the test node to preserve precision. All other type
    // go through read/write buffer serialization, and floating point values may get
    // truncated in the conversion to/from ascii. 
    Real64 getParameterReal64(const std::string& name, Int64 index);
    void setParameterReal64(const std::string& name, Int64 index, Real64 value);

    bool isParameterShared(const std::string& name);

  private:
    TestNode();

    // parameters
    // cgs parameters for parameter testing
    Int32 int32Param_;
    UInt32 uint32Param_; 
    Int64 int64Param_;
    UInt64 uint64Param_;
    Real32 real32Param_;
    Real64 real64Param_;
    std::string stringParam_;
    computeCallbackFunc computeCallback_;
    
    std::vector<Real32> real32ArrayParam_;
    std::vector<Int64> int64ArrayParam_;

    // read-only count of iterations since initialization
    UInt64 iter_;

    // Constructor param specifying per-node output size
    UInt32 outputElementCount_;

    // parameter used for computation
    Int64 delta_;

    // cloning parameters
    std::vector<UInt32> unclonedParam_;
    bool shouldCloneParam_;
    std::vector<UInt32> possiblyUnclonedParam_;
    std::vector< std::vector<Int64> > unclonedInt64ArrayParam_;

    /* ----- cached info from region ----- */
    size_t nodeCount_;

    // Input/output buffers for the whole region
    const Input *bottomUpIn_;
    const Output *bottomUpOut_;
  };
}

#endif // NTA_TESTNODE_HPP

