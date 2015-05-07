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

#include <cpp_region/PyRegion.hpp>
#include <numpy/arrayobject.h>
#include <iostream>
#include <sstream>
#include <memory>
#include <nupic/engine/Spec.hpp>
#include <nupic/engine/Region.hpp>
#include <nupic/engine/Input.hpp>
#include <nupic/engine/Output.hpp>
#include <nupic/utils/Log.hpp>
#include <nupic/ntypes/ObjectModel.hpp> // IWrite/ReadBuffer
#include <nupic/ntypes/Value.hpp>
#include <nupic/ntypes/Array.hpp>
#include <nupic/ntypes/ArrayRef.hpp>
#include <nupic/types/BasicType.hpp>
#include <nupic/ntypes/BundleIO.hpp>
#include <nupic/utils/Log.hpp>
#include <nupic/os/Path.hpp>
#include <py_support/PyArray.hpp>

using namespace nupic;

#define LAST_ERROR_LENGTH 1024
static char lastError[LAST_ERROR_LENGTH];
static bool finalizePython;

extern "C" 
{
  // NTA_initPython() must be called by the MultinodeFactory before any call to 
  // NTA_createPyNode()
  NTA_EXPORT void NTA_initPython()
  {
    finalizePython = false;
    // Initialize Python if it is not initialized already. Python will be initialized
    // if NuPIC is accessed through the Python bindings and hence is already runnning
    // inside a Python process.
    if (!Py_IsInitialized())
    {
      //NTA_DEBUG << "Called Py_Initialize()";
      Py_Initialize();
      NTA_ASSERT(Py_IsInitialized());
      finalizePython = true;
    }
    else
    {
      // Set the PyHelpers flag so it knows its running under Python.
      // This is necessary for PyHelpers to determine if it should
      // clear or restore Python exceptions (see NPC-113)
      py::setRunningUnderPython();
    }
    
    // Important! the following statements must be outside the PyInitialize()
    // conditional block because Python may already be initialized if used
    // through the Python bindings.

    // Initialize numpy.
    import_array();
  }

  // NTA_finalizePython() must be called before unloading the pynode dynamic library
  // to ensure proper cleanup.
  NTA_EXPORT void NTA_finalizePython()
  {
    if (finalizePython)
    {
      //NTA_DEBUG << "Called Py_Finalize()";
      Py_Finalize();
    }
  }

  // createPyNode is used by the MultinodeFactory to create a C++ PyNode instance
  // That references a Python instance. The function tries to create a NuPIC 2.0
  // Py node first and if it fails it tries to create a NuPIC 1.x Py node
  NTA_EXPORT void * NTA_createPyNode(const char * module, void * nodeParams, void * region, void ** exception)
  {
    try
    {
      NTA_CHECK(nodeParams != NULL);
      NTA_CHECK(region != NULL);

      ValueMap * valueMap = static_cast<nupic::ValueMap *>(nodeParams);
      Region * r = static_cast<nupic::Region*>(region);
      RegionImpl * p = NULL;
      p = new nupic::PyRegion(module, *valueMap, r);

      return p;
    }
    catch (nupic::Exception & e)
    {
      *exception = new nupic::Exception(e);
      return NULL;
    }
    catch (...)
    {
      return NULL;
    }
  }

  // deserializePyNode is used by the MultinodeFactory to create a C++ PyNode instance
  // that references a Python instance which has been deserialized from saved state
  NTA_EXPORT void * NTA_deserializePyNode(const char * module, void * bundle, void * region, void ** exception)
  {
    try
    {
      NTA_CHECK(region != NULL);

      Region * r = static_cast<nupic::Region*>(region);
      BundleIO *b = static_cast<nupic::BundleIO*>(bundle);
      RegionImpl * p = NULL;
      p = new PyRegion(module, *b, r);
      return p;
    }
    catch (nupic::Exception & e)
    {
      *exception = new nupic::Exception(e);
      return NULL;
    }
    catch (...)
    {
      return NULL;
    }
  }

  // getLatError() returns the last error message
  NTA_EXPORT const char * NTA_getLastError()
  {
    return lastError;
  }

  // createSpec is used by the RegionImplFactory to get the node spec
  // and cache it. It is a static function so there is no need to instantiate
  // a dummy node, just to get its node spec.
  NTA_EXPORT void * NTA_createSpec(const char * nodeType, void ** exception)
  {
    try
    {
      return PyRegion::createSpec(nodeType);
    }
    catch (nupic::Exception & e)
    {
      *exception = new nupic::Exception(e);
      return NULL;
    }
    catch (...)
    {
      return NULL;
    }
  }

  // destroySpec is used by the RegionImplFactory to destroy
  // a cached node spec.
  NTA_EXPORT int NTA_destroySpec(const char * nodeType)
  {
    try
    {
      PyRegion::destroySpec(nodeType);
      return 0;
    }
    catch (...)
    {
      return -1;
    }
  }
}

// This map stores the node specs for all the Python nodes
std::map<std::string, Spec> PyRegion::specs_;


//
// Get the node spec from the underlying Python node
// and populate a dynamically C++ node spec object.
// Return the node spec pointer (that will be owned
// by RegionImplFactory.
//
Spec * PyRegion::createSpec(const char * nodeType)
{
  // If the node spec for a node type is requested more than once
  // return the exisiting one from the map.
  if (specs_.find(nodeType) != specs_.end())
  {
    Spec & ns = specs_[nodeType];
    return &ns;
  }

  Spec ns;
  createSpec(nodeType, ns);

  specs_[nodeType] = ns;
  //NTA_DEBUG << "node type: " << nodeType << std::endl;
  //NTA_DEBUG << specs_[nodeType].toString() << std::endl;
  return &specs_[nodeType];
}

void PyRegion::destroySpec(const char * nodeType)
{
  specs_.erase(nodeType);
}

namespace nupic
{

class RegionImpl;

static PyObject * makePyValue(const Value & v)
{
  if (v.isArray())
    return array2numpy(*(v.getArray().get()));

  if (v.isString())
  {
    return py::String(*(v.getString().get())).release();
  }

  switch (v.getType())
  {
    case NTA_BasicType_Byte:
      NTA_THROW << "Scalar parameters of type Byte are not supported";
      break;
    case NTA_BasicType_Int16:
      return py::Long(v.getScalarT<NTA_Int16>()).release();
    case NTA_BasicType_Int32:
      return py::Long(v.getScalarT<NTA_Int32>()).release();
    case NTA_BasicType_Int64:
      return py::LongLong(v.getScalarT<NTA_Int64>()).release();
    case NTA_BasicType_UInt16:
      return py::UnsignedLong(v.getScalarT<NTA_UInt16>()).release();
    case NTA_BasicType_UInt32:
      return py::UnsignedLong(v.getScalarT<NTA_UInt32>()).release();
    case NTA_BasicType_UInt64:
      return py::UnsignedLongLong(v.getScalarT<NTA_UInt64>()).release();      
    case NTA_BasicType_Real32:
    {
      std::stringstream ss;
      ss << v.getScalarT<NTA_Real32>();
      return py::Float(ss.str().c_str()).release();
    }
    case NTA_BasicType_Real64:
      return py::Float(v.getScalarT<NTA_Real64>()).release();
    case NTA_BasicType_Handle:
      return (PyObject *)(v.getScalarT<NTA_Handle>());
    default:
      NTA_THROW << "Invalid type: " << v.getType();
  }
}

static void prepareCreationParams(const ValueMap & vm, py::Dict & d)
{
  ValueMap::const_iterator it;
  for (it = vm.begin(); it != vm.end(); ++it)
  {
    try
    {
      py::Ptr v(makePyValue(*(it->second)));
      d.setItem(it->first, v);
    } catch (Exception& e) {
      NTA_THROW << "Unable to create a Python object for parameter '" 
                << it->first << ": " << e.what();
    }
  }
};

PyRegion::PyRegion(const char * module, const ValueMap & nodeParams, Region * region) : 
  RegionImpl(region),
  module_(module)
{
  
  NTA_CHECK(region != NULL);

  std::string className = Path::getExtension(module_);

  // Prepare the creation params as a tuple of PyObject pointers
  py::Tuple args((Py_ssize_t)0);
  py::Dict kwargs;
  prepareCreationParams(nodeParams, kwargs);

  // Instantiate a node and assign it  to the node_ member
  node_.assign(py::Instance(module_, className, args, kwargs));
  NTA_CHECK(node_);
}

PyRegion::PyRegion(const char* module, BundleIO& bundle, Region * region) :
  RegionImpl(region), 
  module_(module)

{
  deserialize(bundle);
  // XXX ADD CHECK TO MAKE SURE THE TYPE MATCHES!
}

PyRegion::~PyRegion()
{
  for (std::map<std::string, Array*>::iterator i = inputArrays_.begin();
       i != inputArrays_.end();
       i++)
  {
    delete i->second;
    i->second = NULL;
  }

}

void PyRegion::serialize(BundleIO& bundle)
{
  // 1. serialize main state using pickle
  // 2. call class method to serialize external state
  
  // 1. Serialize main state
  
  // f = open(path, "wb")
  py::Tuple args(2);
  std::string path = bundle.getPath("pkl");
  py::String filename(path);
  py::String openmode("wb");
  args.setItem(0, filename);
  args.setItem(1, openmode);
  py::Instance f("__builtin__", "file", args);

  // cPickle.dump(node_, f, HIGHEST_PROTOCOL)
  py::Module pickle("cPickle");
  py::Tuple args2(3);
  args2.setItem(0, node_);
  args2.setItem(1, f);
  args2.setItem(2, py::Int(2));
  py::Ptr none(pickle.invoke("dump", args2));

  // f.close()
  py::Tuple args3(Py_ssize_t(0));
  py::Ptr none2(f.invoke("close", args3));
  
  // 2. External state
  // Call the Python serializeExtraData() method
  std::string externalPath = bundle.getPath("xtra");
  py::Tuple args1(1);
  args1.setItem(0, py::String(externalPath));
  
  // Need to put the None result in py::Ptr to decrement the ref count
  py::Ptr none1(node_.invoke("serializeExtraData", args1));
  

}

void PyRegion::deserialize(BundleIO& bundle)
{
  // 1. deserialize main state using pickle
  // 2. call class method to deserialize external state


  // 1. de-serialize main state using pickle
  // f = open(path, "rb")  # binary mode needed on windows
  py::Tuple args(2);
  std::string path = bundle.getPath("pkl");
  py::String filename(path);
  args.setItem(0, filename);
  py::String mode("rb");
  args.setItem(1, mode);
  py::Instance f("__builtin__", "file", args);

  // node_ = cPickle.load(f)
  py::Module pickle("cPickle");
  py::Tuple args2(1);
  args2.setItem(0, f);
  node_.assign(py::Ptr(pickle.invoke("load", args2)));

  // f.close()
  py::Tuple args3((Py_ssize_t)0);
  py::Ptr none2(f.invoke("close", args3));
  
  // 2. External state
  // Call the Python deSerializeExtraData() method
  std::string externalPath = bundle.getPath("xtra");
  py::Tuple args1(1);
  args1.setItem(0, py::String(externalPath));
  
  // Need to put the None result in py::Ptr to decrement the ref count
  py::Ptr none1(node_.invoke("deSerializeExtraData", args1));
  
}




const Spec & PyRegion::getSpec()
{
  return *(PyRegion::createSpec(module_.c_str()));
}

////
//// Get the node spec from the underlying Python node
//// and populate a dynamically C++ node spec object.
//// Return the node spec pointer (that will be owned
//// by RegionImplFactory.
////
//void PyRegion::createSpec(const char * nodeType, Spec & ns)
//{
//  // Get the Python class object
//  std::string className = Path::getExtension(nodeType);
//  py::Class nodeClass(nodeType, className);
//
//  // Get the node spec from the Python class
//  py::Dict nodeSpec(nodeClass.invoke("getSpec", py::Tuple()));
//  //NTA_DEBUG << "'node spec' type: " << nodeSpec.getTypeName();
//  
//  // Extract the 4 dicts from the node spec
//  py::Dict inputs(nodeSpec.getItem("inputs", py::Dict()));
//  py::Dict outputs(nodeSpec.getItem("outputs", py::Dict()));
//  py::Dict parameters(nodeSpec.getItem("parameters", py::Dict()));
//  py::Dict commands(nodeSpec.getItem("commands", py::Dict()));
//
//  // key, value and pos are used to iterate over the
//  // inputs, outputs, parameters and commands dicts
//  // of the Python node spec
//  PyObject * key;
//  PyObject * value;
//  Py_ssize_t pos;
//
//  // Add inputs
//  pos = 0;
//  while (PyDict_Next(inputs, &pos, &key, &value)) 
//  {
//    // key and value are borrowed from the dict. Their ref count
//    // must be incremented so they can be used with
//    // the Py helpers safely
//    Py_INCREF(key);
//    Py_INCREF(value);
//
//    std::string name((const char *)(py::String(key)));
//    py::Dict input(value);
//
//    // Add an InputSpec object for each input spec dict
//
//    std::string description(py::String(input.getItem("description")));
//    std::string dt(py::String(input.getItem("dataType")));
//    NTA_BasicType dataType(BasicType::parse(dt));
//    UInt32 count = py::Int(input.getItem("count"));
//    bool required = py::Int(input.getItem("required")) != 0;
//    bool regionLevel = py::Int(input.getItem("regionLevel")) != 0;
//    bool isDefaultInput = py::Int(input.getItem("isDefaultInput")) != 0;
//    bool requireSplitterMap = py::Int(input.getItem("requireSplitterMap")) != 0;
//    ns.inputs.add(
//      name,
//      InputSpec(
//        description,
//        dataType,
//        count,
//        required,
//        regionLevel,
//        isDefaultInput,
//        requireSplitterMap));
//  }
//
//  // Add outputs
//  pos = 0;
//  while (PyDict_Next(outputs, &pos, &key, &value)) 
//  {
//    // key and value are borrowed from the dict. Their ref count
//    // must be incremented so they can be used with
//    // the Py helpers safely
//    Py_INCREF(key);
//    Py_INCREF(value);
//
//    std::string name((const char *)(py::String(key)));
//    py::Dict output(value);
//
//    // Add an OutputSpec object for each output spec dict
//    std::string description(py::String(output.getItem("description")));
//    std::string dt(py::String(output.getItem("dataType")));
//    NTA_BasicType dataType(BasicType::parse(dt));
//    UInt32 count = py::Int(output.getItem("count"));
//    bool regionLevel = py::Int(output.getItem("regionLevel")) != 0;
//    bool isDefaultOutput = py::Int(output.getItem("isDefaultOutput")) != 0;
//    ns.outputs.add(
//      name,
//      OutputSpec(
//        description,
//        dataType,
//        count,
//        regionLevel,
//        isDefaultOutput));
//  }
//
//  // Add parameters
//  pos = 0;
//  while (PyDict_Next(parameters, &pos, &key, &value)) 
//  {
//    // key and value are borrowed from the dict. Their ref count
//    // must be incremented so they can be used with
//    // the Py helpers safely
//    Py_INCREF(key);
//    Py_INCREF(value);
//
//    std::string name((const char *)(py::String(key)));
//    py::Dict parameter(value);
//
//    // Add an ParameterSpec object for each output spec dict
//    std::string description(py::String(parameter.getItem("description")));
//    std::string dt(py::String(parameter.getItem("dataType")));
//    NTA_BasicType dataType(BasicType::parse(dt));
//    UInt32 count = py::Int(parameter.getItem("count"));
//    std::string constraints(py::String(parameter.getItem("constraints")));
//    std::string defaultValue(py::String(parameter.getItem("defaultValue")));
//    if (defaultValue == "None")
//      defaultValue = "";
//    
//    ParameterSpec::AccessMode accessMode;
//    std::string am(py::String(parameter.getItem("accessMode")));
//    if (am == "Create")
//      accessMode = ParameterSpec::CreateAccess;
//    else if (am == "Read")
//      accessMode = ParameterSpec::ReadOnlyAccess;
//    else if (am == "ReadWrite")
//      accessMode = ParameterSpec::ReadWriteAccess;
//    else
//      NTA_THROW << "Invalid access mode: " << am;
//
//    ns.parameters.add(
//      name,
//      ParameterSpec(
//        description,
//        dataType,
//        count,
//        constraints,
//        defaultValue,
//        accessMode));
//  }
//}

template <typename T, typename PyT>
T PyRegion::getParameterT(const std::string & name, Int64 index)
{
  py::Tuple args(2);
  args.setItem(0, py::String(name));
  args.setItem(1, py::LongLong(index));

  PyT result(node_.invoke("getParameter", args));
  return T(result);    
}

template <typename T, typename PyT>
void PyRegion::setParameterT(const std::string & name, Int64 index, T value)
{
  py::Tuple args(3);
  args.setItem(0, py::String(name));
  args.setItem(1, py::LongLong(index));
  args.setItem(2, PyT(value));
  // Must catch the None return value and decrement
  py::Ptr none(node_.invoke("setParameter", args));
}

Byte PyRegion::getParameterByte(const std::string& name, Int64 index)
{
  return getParameterT<Byte, py::Int>(name, index);   
}

Int32 PyRegion::getParameterInt32(const std::string& name, Int64 index)
{
  //return getParameterT<Int32, py::Long>(name, index);   
  return getParameterT<Int32, py::Int>(name, index);   
}

UInt32 PyRegion::getParameterUInt32(const std::string& name, Int64 index)
{
  return getParameterT<UInt32, py::UnsignedLong>(name, index);   
}

Int64 PyRegion::getParameterInt64(const std::string& name, Int64 index)
{
  return getParameterT<Int64, py::LongLong>(name, index);  
}

UInt64 PyRegion::getParameterUInt64(const std::string& name, Int64 index)
{
  return getParameterT<UInt64, py::LongLong>(name, index);  
}

Real32 PyRegion::getParameterReal32(const std::string& name, Int64 index)
{
  return getParameterT<Real32, py::Float>(name, index);  
}

Real64 PyRegion::getParameterReal64(const std::string& name, Int64 index)
{
  return getParameterT<Real64, py::Float>(name, index);  
}

Handle PyRegion::getParameterHandle(const std::string& name, Int64 index)
{
  if (name == std::string("self"))
  {
    PyObject * o = (PyObject *)node_;
    Py_INCREF(o);
    return o;
  }

  return getParameterT<Handle, py::Ptr>(name, index);  
}

void PyRegion::setParameterByte(const std::string& name, Int64 index, Byte value)
{
  setParameterT<Byte, py::Int>(name, index, value);   
}

void PyRegion::setParameterInt32(const std::string& name, Int64 index, Int32 value)
{
  setParameterT<Int32, py::Long>(name, index, value);   
}

void PyRegion::setParameterUInt32(const std::string& name, Int64 index, UInt32 value)
{
  setParameterT<UInt32, py::UnsignedLong>(name, index, value);   
}

void PyRegion::setParameterInt64(const std::string& name, Int64 index, Int64 value)
{
  setParameterT<Int64, py::LongLong>(name, index, value);   
}

void PyRegion::setParameterUInt64(const std::string& name, Int64 index, UInt64 value)
{
  setParameterT<UInt64, py::UnsignedLongLong>(name, index, value);   
}

void PyRegion::setParameterReal32(const std::string& name, Int64 index, Real32 value)
{
  setParameterT<Real32, py::Float>(name, index, value);   
}

void PyRegion::setParameterReal64(const std::string& name, Int64 index, Real64 value)
{
  setParameterT<Real64, py::Float>(name, index, value);   
}

void PyRegion::setParameterHandle(const std::string& name, Int64 index, Handle value)
{
  setParameterT<PyObject *, py::Ptr>(name, index, (PyObject *)value);   
}

void PyRegion::getParameterArray(const std::string& name, Int64 index, Array & a)
{
  py::Tuple args(3);
  args.setItem(0, py::String(name));
  args.setItem(1, py::LongLong(index));
  args.setItem(2, py::Ptr(array2numpy(a)));

  // Must catch the None return value and decrement
  py::Ptr none(node_.invoke("getParameterArray", args));
}
 
void PyRegion::setParameterArray(const std::string& name, Int64 index, const Array & a)
{
  py::Tuple args(3);
  args.setItem(0, py::String(name));
  args.setItem(1, py::LongLong(index));
  args.setItem(2, py::Ptr(array2numpy(a)));

  // Must catch the None return value and decrement
  py::Ptr none(node_.invoke("setParameterArray", args));
}

std::string PyRegion::getParameterString(const std::string& name, Int64 index)
{
  py::Tuple args(2);
  args.setItem(0, py::String(name));
  args.setItem(1, py::LongLong(index));

  py::String result(node_.invoke("getParameter", args));
  return (const char*)result;
}

void PyRegion::setParameterString(const std::string& name, Int64 index, const std::string& value)
{
  py::Tuple args(3);
  args.setItem(0, py::String(name));
  args.setItem(1, py::LongLong(index));
  args.setItem(2, py::String(value));
  py::Ptr none(node_.invoke("setParameter", args));
}

void PyRegion::getParameterFromBuffer(const std::string& name, 
                                     Int64 index, 
                                     IWriteBuffer& value)
{
  // we override getParameterX for every type, so this should never
  // be called
  NTA_THROW << "::getParameterFromBuffer should not have been called";
}


void PyRegion::setParameterFromBuffer(const std::string& name, 
                            Int64 index,
                            IReadBuffer& value)
{
  // we override getParameterX for every type, so this should never
  // be called
  NTA_THROW << "::setParameterFromBuffer should not have been called";
}

size_t PyRegion::getParameterArrayCount(const std::string& name, Int64 index)
{
  py::Tuple args(2);
  args.setItem(0, py::String(name));
  args.setItem(1, py::LongLong(index));

  py::Int result(node_.invoke("getParameterArrayCount", args));

  return size_t(result);
}

size_t PyRegion::getNodeOutputElementCount(const std::string& outputName)
{
  py::Tuple args(1);
  args.setItem(0, py::String(outputName));

  py::Long result(node_.invoke("getOutputElementCount", args));

  return size_t(result);
}

std::string PyRegion::executeCommand(const std::vector<std::string>& args, Int64 index)
{
  py::String cmd(args[0]);
  py::Tuple t(args.size() - 1);
  for (size_t i = 1; i < args.size(); ++i)
  {
    py::String s(args[i]);
    t.setItem(i-1, s);
  }

  py::Tuple commandArgs(2);
  commandArgs.setItem(0, cmd);
  commandArgs.setItem(1, t);

  py::Instance res(node_.invoke("executeMethod", commandArgs));

  py::String s(res.invoke("__str__", py::Tuple()));
  const char * ss = (const char *)s;
  std::string result(ss);
  NTA_DEBUG << "Result of PyRegion::executeCommand : '" << result << "'";

  return ss;
}

void PyRegion::compute()
{
  const Spec & ns = getSpec();
  // Prepare the inputs dict
  py::Dict inputs;
  for (size_t i = 0; i < ns.inputs.getCount(); ++i)
  {
    // Get the current InputSpec object
    const std::pair<std::string, InputSpec> & p = 
      ns.inputs.getByIndex(i);

    // Get the corresponding input buffer
    Input * inp = region_->getInput(p.first);
    NTA_CHECK(inp);

    // Set pa to point to the original input array
    const Array * pa = &(inp->getData());

    // Skip unlinked inputs of size 0
    if (pa->getCount() == 0)
      continue;

    // If the input requires a splitter map then
    // Copy the original input array to the stored input array, which is larger 
    // by one element and put 0 in the extra element. This is needed for splitter map 
    // access.
    if (p.second.requireSplitterMap)
    {
      // Verify that this input has a stored input array
      NTA_ASSERT(inputArrays_.find(p.first) != inputArrays_.end());
      Array & a = *(inputArrays_[p.first]);

      // Verify that the stored input array is larger by 1  then the original input
      NTA_ASSERT(a.getCount() == pa->getCount() + 1);
      
      // Work at the char * level because there is no good way
      // to work with the actual data type of the input (since the buffer is void *)
      size_t itemSize = BasicType::getSize(p.second.dataType);
      char * begin1 = (char *)pa->getBuffer();
      char * end1 = begin1 + pa->getCount() * itemSize;
      char * begin2 = (char *)a.getBuffer();
      char * end2 = begin2 + a.getCount() * itemSize;

      // Copy the original input array to the stored array
      std::copy(begin1, end1, begin2);

      // Put 0 in the last item (the sentinel value)
      std::fill(end2 - itemSize, end2, 0);

      // Change pa to point to the stored input array (with the sentinel)
      pa = &a;
    }

    // Create a numpy array from pa, which wil be either 
    // the original input array or a stored input array
    // (if a splitter map is needed)
    py::Ptr numpyArray(array2numpy(*pa));
    inputs.setItem(p.first, numpyArray);
  }
     
  // Prepare the outputs dict
  py::Dict outputs;
  for (size_t i = 0; i < ns.outputs.getCount(); ++i)
  {
    // Get the current OutputSpec object
    const std::pair<std::string, OutputSpec> & p = 
      ns.outputs.getByIndex(i);
  
    // Get the corresponding output buffer
    Output * out = region_->getOutput(p.first);
    // Skip optional outputs
    if (!out)
      continue;

    const Array & data = out->getData();
  
    py::Ptr numpyArray(array2numpy(data));
  
    // Insert the buffer to the outputs py::Dict
    outputs.setItem(p.first, numpyArray);
  }
  
  // Call the Python compute() method
  py::Tuple args(2);
  args.setItem(0, inputs);
  args.setItem(1, outputs);

  // Need to put the None result in py::Ptr to decrement the ref count
  py::Ptr none(node_.invoke("compute", args));
}


//
// Get the node spec from the underlying Python node
// and populate a dynamically C++ node spec object.
// Return the node spec pointer (that will be owned
// by RegionImplFactory.
//
void PyRegion::createSpec(const char * nodeType, Spec & ns)
{
  // Get the Python class object
  std::string className = Path::getExtension(nodeType);
  py::Class nodeClass(nodeType, className);

  // Get the node spec from the Python class
  py::Dict nodeSpec(nodeClass.invoke("getSpec", py::Tuple()));

  // Extract the region deascription
  py::String description(nodeSpec.getItem("description"));
  ns.description = std::string(description);

  // Extract the singleNodeOnly attribute
  py::Int singleNodeOnly(nodeSpec.getItem("singleNodeOnly"));
  ns.singleNodeOnly = singleNodeOnly != 0;

  // Extract the 4 dicts from the node spec
  py::Dict inputs(nodeSpec.getItem("inputs", py::Dict()));
  //NTA_DEBUG << "'inputs' type: " << inputs.getTypeName();

  py::Dict outputs(nodeSpec.getItem("outputs", py::Dict()));
  py::Dict parameters(nodeSpec.getItem("parameters", py::Dict()));
  py::Dict commands(nodeSpec.getItem("commands", py::Dict()));

  // key, value and pos are used to iterate over the
  // inputs, outputs, parameters and commands dicts
  // of the Python node spec
  PyObject * key;
  PyObject * value;
  Py_ssize_t pos;

  // Add inputs
  pos = 0;
  while (PyDict_Next(inputs, &pos, &key, &value)) 
  {
    // key and value are borrowed from the dict. Their ref count
    // must be incremented so they can be used with
    // the Py helpers safely
    Py_INCREF(key);
    Py_INCREF(value);

    std::string name((const char *)(py::String(key)));
    py::Dict input(value);

    // Add an InputSpec object for each input spec dict
    std::ostringstream inputMessagePrefix;
    inputMessagePrefix << "Region " << className
      << " spec has missing key for input section " << name << ": ";

    NTA_ASSERT(input.getItem("description") != nullptr)
        << inputMessagePrefix.str() << "description";
    std::string description(py::String(input.getItem("description")));

    NTA_ASSERT(input.getItem("dataType") != nullptr)
        << inputMessagePrefix.str() << "dataType";
    std::string dt(py::String(input.getItem("dataType")));
    NTA_BasicType dataType(BasicType::parse(dt));

    NTA_ASSERT(input.getItem("count") != nullptr)
        << inputMessagePrefix.str() << "count";
    UInt32 count = py::Int(input.getItem("count"));

    NTA_ASSERT(input.getItem("required") != nullptr)
        << inputMessagePrefix.str() << "required";
    bool required = py::Int(input.getItem("required")) != 0;

    NTA_ASSERT(input.getItem("regionLevel") != nullptr)
        << inputMessagePrefix.str() << "regionLevel";
    bool regionLevel = py::Int(input.getItem("regionLevel")) != 0;

    NTA_ASSERT(input.getItem("isDefaultInput") != nullptr)
        << inputMessagePrefix.str() << "isDefaultInput";
    bool isDefaultInput = py::Int(input.getItem("isDefaultInput")) != 0;

    NTA_ASSERT(input.getItem("requireSplitterMap") != nullptr)
        << inputMessagePrefix.str() << "requireSplitterMap";
    bool requireSplitterMap = py::Int(input.getItem("requireSplitterMap")) != 0;
    ns.inputs.add(
      name,
      InputSpec(
        description,
        dataType,
        count,
        required,
        regionLevel,
        isDefaultInput,
        requireSplitterMap));
  }

  // Add outputs
  pos = 0;
  while (PyDict_Next(outputs, &pos, &key, &value)) 
  {
    // key and value are borrowed from the dict. Their ref count
    // must be incremented so they can be used with
    // the Py helpers safely
    Py_INCREF(key);
    Py_INCREF(value);

    std::string name((const char *)(py::String(key)));
    py::Dict output(value);

    // Add an OutputSpec object for each output spec dict
    std::ostringstream outputMessagePrefix;
    outputMessagePrefix << "Region " << className
      << " spec has missing key for output section " << name << ": ";

    NTA_ASSERT(output.getItem("description") != nullptr)
        << outputMessagePrefix.str() << "description";
    std::string description(py::String(output.getItem("description")));

    NTA_ASSERT(output.getItem("dataType") != nullptr)
        << outputMessagePrefix.str() << "dataType";
    std::string dt(py::String(output.getItem("dataType")));
    NTA_BasicType dataType(BasicType::parse(dt));

    NTA_ASSERT(output.getItem("count") != nullptr)
        << outputMessagePrefix.str() << "count";
    UInt32 count = py::Int(output.getItem("count"));

    NTA_ASSERT(output.getItem("regionLevel") != nullptr)
        << outputMessagePrefix.str() << "regionLevel";
    bool regionLevel = py::Int(output.getItem("regionLevel")) != 0;

    NTA_ASSERT(output.getItem("isDefaultOutput") != nullptr)
        << outputMessagePrefix.str() << "isDefaultOutput";
    bool isDefaultOutput = py::Int(output.getItem("isDefaultOutput")) != 0;

    ns.outputs.add(
      name,
      OutputSpec(
        description,
        dataType,
        count,
        regionLevel,
        isDefaultOutput));
  }

  // Add parameters
  pos = 0;
  while (PyDict_Next(parameters, &pos, &key, &value)) 
  {
    // key and value are borrowed from the dict. Their ref count
    // must be incremented so they can be used with
    // the Py helpers safely
    Py_INCREF(key);
    Py_INCREF(value);

    std::string name((const char *)(py::String(key)));
    py::Dict parameter(value);

    // Add an ParameterSpec object for each output spec dict
    std::ostringstream parameterMessagePrefix;
    parameterMessagePrefix << "Region " << className
      << " spec has missing key for parameter section " << name << ": ";

    NTA_ASSERT(parameter.getItem("description") != nullptr)
        << parameterMessagePrefix.str() << "description";
    std::string description(py::String(parameter.getItem("description")));

    NTA_ASSERT(parameter.getItem("dataType") != nullptr)
        << parameterMessagePrefix.str() << "dataType";
    std::string dt(py::String(parameter.getItem("dataType")));
    NTA_BasicType dataType(BasicType::parse(dt));

    NTA_ASSERT(parameter.getItem("count") != nullptr)
        << parameterMessagePrefix.str() << "count";
    UInt32 count = py::Int(parameter.getItem("count"));

    // This parameter is optional
    std::string constraints(py::String(parameter.getItem("constraints")));

    NTA_ASSERT(parameter.getItem("accessMode") != nullptr)
        << parameterMessagePrefix.str() << "accessMode";
    ParameterSpec::AccessMode accessMode;
    std::string am(py::String(parameter.getItem("accessMode")));
    if (am == "Create")
      accessMode = ParameterSpec::CreateAccess;
    else if (am == "Read")
      accessMode = ParameterSpec::ReadOnlyAccess;
    else if (am == "ReadWrite")
      accessMode = ParameterSpec::ReadWriteAccess;
    else
      NTA_THROW << "Invalid access mode: " << am;

    // Get default value as a string if it's a create parameter
    std::string defaultValue;
    if (am == "Create")
    {
      NTA_ASSERT(parameter.getItem("defaultValue") != nullptr)
          << parameterMessagePrefix.str() << "defaultValue";
      py::Instance dv(parameter.getItem("defaultValue"));
      py::String s(dv.invoke("__str__", py::Tuple()));
      defaultValue = std::string(s);
    }
    if (defaultValue == "None")
      defaultValue = "";

    ns.parameters.add(
      name,
      ParameterSpec(
        description,
        dataType,
        count,
        constraints,
        defaultValue,
        accessMode));
  }

  // Add the automatic "self" parameter
  ns.parameters.add(
    "self",
    ParameterSpec(
      "The PyObject * of the region's Python classd",
      NTA_BasicType_Handle,
      1,
      "",
      "",
      ParameterSpec::ReadOnlyAccess));

  // Add commands
  pos = 0;
  while (PyDict_Next(commands, &pos, &key, &value)) 
  {
    // key and value are borrowed from the dict. Their ref count
    // must be incremented so they can be used with
    // the Py helpers safely
    Py_INCREF(key);
    Py_INCREF(value);

    std::string name((const char *)(py::String(key)));
    py::Dict command(value);

    // Add a CommandSpec object for each output spec dict
    std::ostringstream commandsMessagePrefix;
    commandsMessagePrefix << "Region " << className
      << " spec has missing key for commands section " << name << ": ";

    NTA_ASSERT(command.getItem("description") != nullptr)
        << commandsMessagePrefix.str() << "description";
    std::string description(py::String(command.getItem("description")));

    ns.commands.add(
      name,
      CommandSpec(description));
  }
}

// Return the size of the longest raw in a slitter map
// which is the max number of inputs that go into one node
static size_t getMaxInputCount(const nupic::Input::SplitterMap & sm)
{
  size_t maxInputCount = 0;
  for (size_t i = 0; i < sm.size(); ++i)
  {
    size_t inputCount = sm[i].size();
    if (inputCount > maxInputCount)
      maxInputCount = inputCount;
  }

  return maxInputCount;
}

void PyRegion::initialize()
{
  // Prepare the dimensions tuple
  Dimensions d = region_->getDimensions();
  size_t dimCount = d.getDimensionCount();
  py::Tuple dims(dimCount);
  for (size_t i = 0; i < dimCount; ++i)
  {
    dims.setItem(i, py::UnsignedLong(d[i]));
  }
  
  // Prepare the splitter map dict - each input
  // gets its own splitter map. The splitter map
  // for an input is represented as a tuple of 
  // tuples of longs in Python.
  const Spec & ns = getSpec();
  
  // The dict that contains the input maps for all inputs
  py::Dict splitterMaps;
  for (size_t i = 0; i < ns.inputs.getCount(); ++i)
  {
    // Get the current InputSpec object
    const std::pair<std::string, InputSpec> & p = 
      ns.inputs.getByIndex(i);

    // Skip splitter map generation if not required
    if (!p.second.requireSplitterMap)
      continue;

    // Get the corresponding input buffer
    Input * inp = region_->getInput(p.first);
    NTA_CHECK(inp);


    NTA_CHECK(inputArrays_.find(p.first) == inputArrays_.end());

    // Create an input array for inputs that require a splitter map
    // The input array must be larger by one element than the actual input
    // to hold the sentinel value for the splitter map
    inputArrays_[p.first] = new Array(p.second.dataType);
    Array & a = *(inputArrays_[p.first]);
    a.allocateBuffer(inp->getData().getCount() + 1);

    const nupic::Input::SplitterMap & sm = inp->getSplitterMap();
    size_t rawSize = getMaxInputCount(sm);
    
    // The sentinel is padding each input raw
    // in the splitter map after the end of useful input
    UInt64 sentinel = inp->getData().getCount();

    // Create the splitterMap backing store as an ArrayBase object
    size_t mapSize = sm.size() * rawSize;
    boost::shared_ptr<PyArray<UInt64> > splitterMap(new PyArray<UInt64>(mapSize));
    UInt64 * begin = (UInt64 *)(splitterMap->getBuffer());
    for (size_t j = 0; j < sm.size(); ++j)
    {
      //std::cout << "sm[j]:" << std::endl;
      //for (size_t k = 0; k < sm[j].size(); ++k)
      //{
      //  std::cout << " " << sm[j][k];
      //}
      //std::cout << std::endl;

      // Copy current raw into the splitter map
      std::copy(sm[j].begin(), 
                sm[j].end(),
                begin + j * rawSize);

      // Fill the rest of the raw (up to maxInputSize) with the sentinel
      std::fill(begin + j * rawSize + sm[j].size(),
                begin + (j + 1) * rawSize,
                sentinel);                


      //std::cout << "begin[j * rawSizse]:" << std::endl;
      //for (UInt64 k = 0; k < rawSize; ++k)
      //{
      //  std::cout << " " << begin[j * rawSize + k];
      //}
      //std::cout << std::endl;
    }


    // Store all splitter maps in a set so they persist
    splitterMaps_.insert(splitterMap);

    // Create a numpy array version of the serialized splitter map
    py::Instance serialized(splitterMap->asNumpyArray());
    
    // Reshape the array to the real shape of the padded splitter map
    py::Tuple args(2);
    args.setItem(0, py::UnsignedLong(sm.size()));
    args.setItem(1, py::UnsignedLong(rawSize));
    py::Ptr shaped(serialized.invoke("reshape", args));

    // Add the shaped splitter map of input i
    splitterMaps.setItem(p.first.c_str(), shaped);
  }

  // Call the Python initialize() method
  py::Tuple args(2);
  args.setItem(0, dims);
  args.setItem(1, splitterMaps);
  

  //py::Dict dd(args.getItem(1));
  //py::Ptr m(dd.getItem("bottomUpIn"));
  //for (size_t k = 0; k < 10; ++k)
  //{
  //  UInt64 * p = (UInt64 *)(PyArray_GETPTR1((PyObject *)m, k));
  //  std::cout << " " << *p;
  //}

  // Need to put the None result in py::Ptr, so decrement the ref count
  py::Ptr none(node_.invoke("initialize", args));
}


} // end namespace nupic
