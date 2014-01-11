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
 * Definition of the RegionImpl API
 *
 * A RegionImpl is a node "plugin" that provides most of the 
 * implementation of a Region, including algorithms. 
 *
 * The RegionImpl class is expected to be subclassed for particular
 * node types (e.g. FDRNode, PyNode, etc) and RegionImpls are created
 * by the RegionImplFactory
 */

#ifndef NTA_REGION_IMPL_HPP
#define NTA_REGION_IMPL_HPP

#include <string>
#include <vector>
#include <nta/ntypes/object_model.hpp> // IWriteBuffer

namespace nta
{

  struct Spec;
  class Region;
  class Dimensions;
  class Input;
  class Output;
  class Array;
  class ArrayRef;
  class NodeSet;
  class BundleIO;

  class RegionImpl
  {
  public:


    // All subclasses must call this constructor from their regular constructor
    RegionImpl(Region* region);
    
    virtual ~RegionImpl();



    /* ------- Convenience methods  that access region data -------- */

    const std::string& getType() const;
    
    const std::string& getName() const;

    const NodeSet& getEnabledNodes() const;

    /* ------- Parameter support in the base class. ---------*/
    // The default implementation of all of these methods goes through 
    // set/getParameterFromBuffer, which is compatible with NuPIC 1. 
    // RegionImpl subclasses may override for higher performance. 

    virtual Int32 getParameterInt32(const std::string& name, Int64 index);
    virtual UInt32 getParameterUInt32(const std::string& name, Int64 index);
    virtual Int64 getParameterInt64(const std::string& name, Int64 index);
    virtual UInt64 getParameterUInt64(const std::string& name, Int64 index);
    virtual Real32 getParameterReal32(const std::string& name, Int64 index);
    virtual Real64 getParameterReal64(const std::string& name, Int64 index);
    virtual Handle getParameterHandle(const std::string& name, Int64 index);

    virtual void setParameterInt32(const std::string& name, Int64 index, Int32 value);
    virtual void setParameterUInt32(const std::string& name, Int64 index, UInt32 value);
    virtual void setParameterInt64(const std::string& name, Int64 index, Int64 value);
    virtual void setParameterUInt64(const std::string& name, Int64 index, UInt64 value);
    virtual void setParameterReal32(const std::string& name, Int64 index, Real32 value);
    virtual void setParameterReal64(const std::string& name, Int64 index, Real64 value);
    virtual void setParameterHandle(const std::string& name, Int64 index, Handle value);
    
    virtual void getParameterArray(const std::string& name, Int64 index, Array & array);
    virtual void setParameterArray(const std::string& name, Int64 index, const Array & array);

    virtual void setParameterString(const std::string& name, Int64 index, const std::string& s);
    virtual std::string getParameterString(const std::string& name, Int64 index);


    /* -------- Methods that must be implemented by subclasses -------- */

    /**
     * Can't declare a static method in an interface. But RegionFactory
     * expects to find this method. Caller gets ownership. 
     */

    // static Spec* createSpec();

    // Serialize state. 
    virtual void serialize(BundleIO& bundle) = 0;

    // De-serialize state. Must be called from deserializing constructor
    virtual void deserialize(BundleIO& bundle) = 0;


    /**
     * Inputs/Outputs are made available in initialize()
     * It is always called after the constructor (or load from serialized state)
     */
    virtual void initialize() = 0;

    // Compute outputs from inputs and internal state
    virtual void compute() = 0;



    // Execute a command
    virtual std::string executeCommand(const std::vector<std::string>& args, Int64 index) = 0;


    // Per-node size (in elements) of the given output. 
    // For per-region outputs, it is the total element count.
    // This method is called only for outputs whose size is not
    // specified in the nodespec. 
    virtual size_t getNodeOutputElementCount(const std::string& outputName) = 0;

    /**
     * Get a parameter from a write buffer. 
     * This method is called only by the typed getParameter*
     * methods in the RegionImpl base class
     * 
     * Must be implemented by all subclasses.
     *
     * @param index A node index. (-1) indicates a region-level parameter
     *
     */
    virtual void getParameterFromBuffer(const std::string& name, 
                                        Int64 index, 
                                        IWriteBuffer& value) = 0;

    /**
     * Set a parameter from a read buffer.
     * This method is called only by the RegionImpl base class
     * type-specific setParameter* methods
     * Must be implemented by all subclasses.
     *
     * @param index A node index. (-1) indicates a region-level parameter
     */
    virtual void setParameterFromBuffer(const std::string& name, 
                              Int64 index,
                              IReadBuffer& value) = 0;



    /* -------- Methods that may be overridden by subclasses -------- */


    /**
     * Array-valued parameters may have a size determined at runtime. 
     * This method returns the number of elements in the named parameter. 
     * If parameter is not an array type, may throw an exception or return 1.
     *
     * Must be implemented only if the node has one or more array 
     * parameters with a dynamically-determined length.
     */
    virtual size_t getParameterArrayCount(const std::string& name, Int64 index);


    /**
     * isParameterShared must be available after construction
     * Default implementation -- all parameters are shared
     * Tests whether a parameter is node or region level
     */
    virtual bool isParameterShared(const std::string& name);



  protected: 
    Region* region_;

    /* -------- Methods provided by the base class for use by subclasses -------- */
    
    // ---
    /// Callback for subclasses to get an output stream during serialize() 
    /// (for output) and the deserializing constructor (for input)
    /// It is invalid to call this method except inside serialize() in a subclass. 
    /// 
    /// Only one serialization stream may be open at a time. Calling
    /// getSerializationXStream a second time automatically closes the 
    /// first stream. Any open stream is closed when serialize() returns. 
    // ---
    std::ostream& getSerializationOutputStream(const std::string& name);
    std::istream& getSerializationInputStream(const std::string& name);
    std::string getSerializationPath(const std::string& name);

    // These methods provide access to inputs and outputs
    // They raise an exception if the named input or output is 
    // not found. 
    const Input* getInput(const std::string& name);
    const Output* getOutput(const std::string& name);

    const Dimensions& getDimensions();

  };

}


#endif // NTA_REGION_IMPL_HPP
