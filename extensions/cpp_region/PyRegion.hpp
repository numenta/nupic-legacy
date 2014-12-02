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


#ifndef NTA_PY_REGION_HPP
#define NTA_PY_REGION_HPP

#include <py_support/PyArray.hpp>

#include <string>
#include <vector>
#include <set>

#include <nupic/engine/RegionImpl.hpp>
#include <nupic/engine/Spec.hpp>
#include <nupic/ntypes/Value.hpp>

namespace nupic
{
  struct Spec;

  class PyRegion : public RegionImpl 
  {
    typedef std::map<std::string, Spec> SpecMap;    
  public:
    // Used by RegionImplFactory to create and cache a nodespec
    static Spec * createSpec(const char * nodeType);

    // Used by RegionImplFactory to destroy a node spec when clearing its cache
    static void destroySpec(const char * nodeType);
    
    PyRegion(const char * module, const ValueMap & nodeParams, Region * region);
    PyRegion(const char * module, BundleIO& bundle, Region * region);
    virtual ~PyRegion();

    void serialize(BundleIO& bundle);
    void deserialize(BundleIO& bundle);

    const Spec & getSpec();

    static void createSpec(const char * nodeType, Spec & ns);

    // RegionImpl interface
    
    size_t getNodeOutputElementCount(const std::string& outputName);
    void getParameterFromBuffer(const std::string& name, Int64 index, IWriteBuffer& value);
    void setParameterFromBuffer(const std::string& name, Int64 index, IReadBuffer& value);

    void initialize();
    void compute();
    std::string executeCommand(const std::vector<std::string>& args, Int64 index);

    size_t getParameterArrayCount(const std::string& name, Int64 index);

    virtual Byte getParameterByte(const std::string& name, Int64 index);
    virtual Int32 getParameterInt32(const std::string& name, Int64 index);
    virtual UInt32 getParameterUInt32(const std::string& name, Int64 index);
    virtual Int64 getParameterInt64(const std::string& name, Int64 index);
    virtual UInt64 getParameterUInt64(const std::string& name, Int64 index);
    virtual Real32 getParameterReal32(const std::string& name, Int64 index);
    virtual Real64 getParameterReal64(const std::string& name, Int64 index);
    virtual Handle getParameterHandle(const std::string& name, Int64 index);
    virtual std::string getParameterString(const std::string& name, Int64 index);

    virtual void setParameterByte(const std::string& name, Int64 index, Byte value);
    virtual void setParameterInt32(const std::string& name, Int64 index, Int32 value);
    virtual void setParameterUInt32(const std::string& name, Int64 index, UInt32 value);
    virtual void setParameterInt64(const std::string& name, Int64 index, Int64 value);
    virtual void setParameterUInt64(const std::string& name, Int64 index, UInt64 value);
    virtual void setParameterReal32(const std::string& name, Int64 index, Real32 value);
    virtual void setParameterReal64(const std::string& name, Int64 index, Real64 value);
    virtual void setParameterHandle(const std::string& name, Int64 index, Handle value);
    virtual void setParameterString(const std::string& name, Int64 index, const std::string& value);
    
    virtual void getParameterArray(const std::string& name, Int64 index, Array & array);
    virtual void setParameterArray(const std::string& name, Int64 index, const Array & array);

    // Helper methods
    template <typename T, typename PyT>
    T getParameterT(const std::string & name, Int64 index);
    
    template <typename T, typename PyT>
    void setParameterT(const std::string & name, Int64 index, T value);

  private:
    PyRegion();
    PyRegion(const Region &);

  private:
    static SpecMap specs_;
    std::string module_;
    py::Instance node_;
    std::set<boost::shared_ptr<PyArray<UInt64> > > splitterMaps_;
    // pointers rather than objects because Array doesnt
    // have a default constructor
    std::map<std::string, Array*> inputArrays_;
  };
}

#endif // NTA_PY_REGION_HPP
