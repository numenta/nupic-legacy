/*
 * ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
 * Numenta, Inc. a separate commercial license for this software code, the
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


#include <stdexcept>
#include <nta/engine/RegionImplFactory.hpp>
#include <nta/engine/RegionImpl.hpp>
#include <nta/engine/Region.hpp>
#include <nta/engine/Spec.hpp>
#include <nta/os/DynamicLibrary.hpp>
#include <nta/os/Path.hpp>
#include <nta/os/OS.hpp>
#include <nta/os/Env.hpp>
#include <nta/ntypes/Value.hpp>
#include <nta/ntypes/BundleIO.hpp>
#include <nta/engine/YAMLUtils.hpp>
#include <nta/engine/TestNode.hpp>
#include <nta/regions/SpatialPoolerNode.hpp>
#include <nta/regions/TemporalPoolerNode.hpp>
#include <nta/regions/VectorFileEffector.hpp>
#include <nta/regions/VectorFileSensor.hpp>
#include <nta/utils/Log.hpp>
#include <nta/utils/StringUtils.hpp>

// from http://stackoverflow.com/a/9096509/1781435
#define stringify(x)  #x
#define expand_and_stringify(x) stringify(x)

// Path from site-packages to packages that contain NuPIC Python regions
const size_t packages_length = 2;
const char * packages[] = { "nupic.regions", "nupic.regions.extra" };

namespace nta
{
  class DynamicPythonLibrary
  {
    typedef void (*initPythonFunc)();
    typedef void (*finalizePythonFunc)();
    typedef void * (*createSpecFunc)(const char *, void **);
    typedef int (*destroySpecFunc)(const char *);
    typedef void * (*createPyNodeFunc)(const char *, void *, void *, void **);
    typedef void * (*deserializePyNodeFunc)(const char *, void *, void *, void *);
  public:
    DynamicPythonLibrary() :
      initPython_(0),
      finalizePython_(0),
      createSpec_(0),
      destroySpec_(0),
      createPyNode_(0)
    {
      // To find the pynode plugin we need the nupic 
      // installation directory.
      // Use NTA_ROOTDIR if it is set, otherwise we infer the 
      // location of the root directory from PYTHONPATH
      bool found = Env::get("NTA_ROOTDIR", rootDir_);
      if (!found)
      {
        // look at each component of PYTHONPATH for component/nupic
        std::string pythonPath;
        found = Env::get("PYTHONPATH", pythonPath);
        if (!found)
        {
          NTA_THROW << "Unable to find the pynode dynamic library because neither NTA_ROOTDIR not PYTHONPATH is set";
        }
        found = false;
#ifdef NTA_PLATFORM_win32
        const char* sep = ";";
#else
        const char* sep = ":";
#endif
        std::string::size_type start = 0;
        std::string::size_type sz = pythonPath.size();
        std::string::size_type len;
        std::string::size_type end = pythonPath.find(sep);
        if (end == std::string::npos)
          len = sz - start;
        else
          len = end - start;

        std::string path;
        while (len > 0)
        {
          std::string component = pythonPath.substr(start, len);
          path = Path::join(component, "nupic");
          if (Path::exists(path) && Path::isDirectory(path))
          {
            found = true;
            break;
          }
          // move to the next component; skip the ":"
          start = start + len + 1;
          if (start >= sz)
            break;

          std::string::size_type end = pythonPath.find(sep, start);
          if (end == std::string::npos)

            len = sz - start;
          else
            len = end - start;
        }
        if (found)
        {
          rootDir_ = Path::normalize(Path::makeAbsolute(Path::join(path, "../../../..")));
        }                                 
      }
      if (!found)
        NTA_THROW << "Unable to find NuPIC installation dir from NTA_ROOTDIR or PYTHONPATH";
      
      
#if defined(NTA_PLATFORM_darwin64)
      const char * filename = "libcpp_region.dylib";
#elif defined(NTA_PLATFORM_darwin86)
      const char * filename = "libcpp_region.dylib";
#elif defined(NTA_PLATFORM_linux64)
      const char * filename = "libcpp_region.so";
#elif defined(NTA_PLATFORM_linux32)
      const char * filename = "libcpp_region.so";
#elif defined(NTA_PLATFORM_win32)
      const char * filename = "cpp_region.dll";
#endif

      std::string libName = Path::join(rootDir_, "lib", filename); 

      if (!Path::exists(libName))
        NTA_THROW << "Unable to find library " << filename 
                  << " in NuPIC installation folder '" << rootDir_ << "'";

      std::string errorString;
      DynamicLibrary * p = 
        DynamicLibrary::load(libName, 
                             // export as LOCAL because we don't want
                             // the symbols to be globally visible; 
                             // But the python module that we load
                             // has to be able to access symbols from
                             // libpython.so; Since libpython.so is linked
                             // to the pynode shared library, it appears
                             // we have to make the pynode shared library
                             // symbols global. TODO: investigate
                             DynamicLibrary::GLOBAL| 
                             // Evaluate them NOW instead of LAZY to catch 
                             // errors up front, even though this takes
                             // a little longer to load the library. 
                             // However -- the current dependency chain
                             // PyNode->Region->RegionImplFactory apparently
                             // creates never-used dependencies on YAML
                             // so until this is resolved use LAZY
                             DynamicLibrary::LAZY,
                             errorString);
      NTA_CHECK(p) << "Unable to load the pynode library: " << errorString;

      pynodeLibrary_ = boost::shared_ptr<DynamicLibrary>(p);

      initPython_ = (initPythonFunc)pynodeLibrary_->getSymbol("NTA_initPython");
      NTA_CHECK(initPython_) << "Unable to find NTA_initPython symbol in " << filename;

      finalizePython_ = (finalizePythonFunc)pynodeLibrary_->getSymbol("NTA_finalizePython");
      NTA_CHECK(finalizePython_) << "Unable to find NTA_finalizePython symbol in " << filename;

      createPyNode_ = (createPyNodeFunc)pynodeLibrary_->getSymbol("NTA_createPyNode");
      NTA_CHECK(createPyNode_) << "Unable to find NTA_createPyNode symbol in " << filename;

      deserializePyNode_ = (deserializePyNodeFunc)pynodeLibrary_->getSymbol("NTA_deserializePyNode");
      NTA_CHECK(createPyNode_) << "Unable to find NTA_createPyNode symbol in " << filename;

      createSpec_ = (createSpecFunc)pynodeLibrary_->getSymbol("NTA_createSpec");
      NTA_CHECK(createSpec_) << "Unable to find NTA_createSpec symbol in " << filename;

      destroySpec_ = (destroySpecFunc)pynodeLibrary_->getSymbol("NTA_destroySpec");
      NTA_CHECK(destroySpec_) << "Unable to find NTA_destroySpec symbol in " << filename;

      (*initPython_)();
    }

    ~DynamicPythonLibrary()
    {
      //NTA_DEBUG << "In DynamicPythonLibrary Destructor";
      if (finalizePython_)
        finalizePython_();
    } 

    void * createSpec(std::string nodeType, void ** exception)
    {
      //NTA_DEBUG << "RegionImplFactory::createSpec(" << nodeType << ")";
      return (*createSpec_)(nodeType.c_str(), exception);
    }

    int destroySpec(std::string nodeType)
    {
      NTA_INFO << "destroySpec(" << nodeType << ")";
      return (*destroySpec_)(nodeType.c_str());
    }

    void * createPyNode(const std::string& nodeType, 
                        ValueMap * nodeParams,
                        Region * region,
                        void ** exception)
    {
      //NTA_DEBUG << "RegionImplFactory::createPyNode(" << nodeType << ")";
      return (*createPyNode_)(nodeType.c_str(),
                              reinterpret_cast<void *>(nodeParams),
                              reinterpret_cast<void*>(region),
                              exception);

    }

    void * deserializePyNode(const std::string& nodeType, 
                             BundleIO* bundle,
                             Region * region, 
                             void ** exception)
    {
      //NTA_DEBUG << "RegionImplFactory::deserializePyNode(" << nodeType << ")";
      return (*deserializePyNode_)(nodeType.c_str(), 
                                   reinterpret_cast<void*>(bundle),
                                   reinterpret_cast<void*>(region), 
                                   exception);
    }

    const std::string& getRootDir() const
    {
      return rootDir_;
    }

  private:
    std::string rootDir_;
    boost::shared_ptr<DynamicLibrary> pynodeLibrary_;
    initPythonFunc initPython_;
    finalizePythonFunc finalizePython_;
    createSpecFunc createSpec_;
    destroySpecFunc destroySpec_;
    createPyNodeFunc createPyNode_;
    deserializePyNodeFunc deserializePyNode_;
  };

RegionImplFactory & RegionImplFactory::getInstance()
{
  static RegionImplFactory instance;

  return instance;
}

static std::string getPackageDir(const std::string& rootDir, const std::string & package)
{
  
  std::string p(package);
  p.replace(p.find("."), 1, "/");
  size_t pos = p.find(".");
  if (pos != std::string::npos)
    p.replace(p.find("."), 1, "/");

  return Path::join(rootDir, "lib/python" expand_and_stringify(NTA_PYTHON_SUPPORT) "/site-packages", p);
}

// This function creates either a NuPIC 2 or NuPIC 1 Python node 
static RegionImpl * createPyNode(DynamicPythonLibrary * pyLib, 
                                 const std::string & nodeType,
                                 ValueMap * nodeParams,
                                 Region * region)
{
  for (size_t i = 0; i < packages_length; ++ i)
  {
    const char * package = packages[i];
    // Construct the full module path to the requested node
    std::string fullNodeType = std::string(package) + std::string(".") +
                               std::string(nodeType.c_str() + 3);

    // Check if node exists and continue if not
    std::string nodePath = Path::join(getPackageDir(pyLib->getRootDir(), package), 
      std::string(nodeType.c_str() + 3) + std::string(".py"));

      if (!Path::exists(nodePath))
        continue;

    void * exception = NULL;
    void * node = pyLib->createPyNode(fullNodeType, nodeParams, region, &exception);
    if (node)
      return static_cast<RegionImpl*>(node);

    if (exception)
    {
      nta::Exception * e = (nta::Exception *)exception;
      throw nta::Exception(*e);
      delete e;
    }
  }

  NTA_THROW << "Unable to create region " << region->getName() << " of type " << nodeType;
  return NULL;
}

// This function deserializes either a NuPIC 2 or NuPIC 1 Python node 
static RegionImpl * deserializePyNode(DynamicPythonLibrary * pyLib, 
                                      const std::string & nodeType,
                                      BundleIO & bundle,
                                      Region * region)
{
  // We need to find the module so that we know if it is NuPIC 1 or NuPIC 2
  for (size_t i = 0; i < packages_length; ++ i)
  {
    const char * package = packages[i];
    // Construct the full module path to the requested node
    std::string fullNodeType = std::string(package) + std::string(".") +
                               std::string(nodeType.c_str() + 3);

    // Check if node exists and continue if not
    std::string nodePath = Path::join(getPackageDir(pyLib->getRootDir(), package), 
           std::string(nodeType.c_str() + 3) + std::string(".py"));

    if (!Path::exists(nodePath))
      continue;



    void *exception = NULL;
    void * node = pyLib->deserializePyNode(fullNodeType, &bundle, region, &exception);
    if (node)
      return static_cast<RegionImpl*>(node);
    
    if (exception)
    {
      nta::Exception * e = (nta::Exception *)exception;
      throw nta::Exception(*e);
      delete e;
    }
  }
  NTA_THROW << "Unable to deserialize region " << region->getName() << " of type " << nodeType;
  return NULL;



}

RegionImpl* RegionImplFactory::createRegionImpl(const std::string nodeType, 
                                                const std::string nodeParams,
                                                Region* region)
{

  RegionImpl *mn = NULL;
  Spec *ns = getSpec(nodeType);
  ValueMap vm = YAMLUtils::toValueMap(
    nodeParams.c_str(), 
    ns->parameters, 
    nodeType, 
    region->getName());
    
  if (nodeType == "TestNode")
  {
    mn = new TestNode(vm, region);
  } else if (nodeType == "SpatialPoolerNode")
  {
    mn = new SpatialPoolerNode(vm, region);
  } else if (nodeType == "TemporalPoolerNode")
  {
    mn = new TemporalPoolerNode(vm, region);
  } else if (nodeType == "VectorFileEffector")
  {
    mn = new VectorFileEffector(vm, region);
  } else if (nodeType == "VectorFileSensor")
  {
    mn = new VectorFileSensor(vm, region);
  } else if ((nodeType.find(std::string("py.")) == 0))
  {
    if (!pyLib_)
      pyLib_ = boost::shared_ptr<DynamicPythonLibrary>(new DynamicPythonLibrary());
    
    mn = createPyNode(pyLib_.get(), nodeType, &vm, region);
  } else
  {
    NTA_THROW << "Unsupported node type '" << nodeType << "'";
  }
  return mn;

}

RegionImpl* RegionImplFactory::deserializeRegionImpl(const std::string nodeType, 
                                                     BundleIO& bundle,
                                                     Region* region)
{

  RegionImpl *mn = NULL;

  if (nodeType == "TestNode")
  {
    mn = new TestNode(bundle, region);
  } else if (nodeType == "SpatialPoolerNode")
  {
    mn = new SpatialPoolerNode(bundle, region);
  } else if (nodeType == "TemporalPoolerNode")
  {
    mn = new TemporalPoolerNode(bundle, region);
  } else if (nodeType == "VectorFileEffector")
  {
    mn = new VectorFileEffector(bundle, region);
  } else if (nodeType == "VectorFileSensor")
  {
    mn = new VectorFileSensor(bundle, region);
  } else if (StringUtils::startsWith(nodeType, "py."))
  {
    if (!pyLib_)
      pyLib_ = boost::shared_ptr<DynamicPythonLibrary>(new DynamicPythonLibrary());
    
    mn = deserializePyNode(pyLib_.get(), nodeType, bundle, region);
  } else
  {
    NTA_THROW << "Unsupported node type '" << nodeType << "'";
  }
  return mn;

}

// This function returns the node spec of a NuPIC 2 or NuPIC 1 Python node 
static Spec * getPySpec(DynamicPythonLibrary * pyLib,
                                const std::string & nodeType)
{
  for (size_t i = 0; i < packages_length; ++ i)
  {
    const char * package = packages[i];

    // Construct the full module path to the requested node
    std::string fullNodeType = std::string(package) + std::string(".") + 
                               std::string(nodeType.c_str() + 3);

    // Check if node exists and continue if not
    std::string nodePath = Path::join(getPackageDir(pyLib->getRootDir(), package), 
      std::string(nodeType.c_str() + 3) + std::string(".py"));

      if (!Path::exists(nodePath))
        continue;
    void * exception = NULL;
    void * ns = pyLib->createSpec(fullNodeType, &exception);
    if (ns) {
      return (Spec *)ns;
    }

    if (exception)
    {
      nta::Exception * e = (nta::Exception *)exception;
      delete e;
      NTA_THROW << "Could not get valid spec for Region: " << nodeType;
    }
  }

  NTA_THROW << "Matching Python module for " << nodeType << " not found.";
}

Spec * RegionImplFactory::getSpec(const std::string nodeType)
{
  std::map<std::string, Spec*>::iterator it;
  // return from cache if we already have it
  it = nodespecCache_.find(nodeType);
  if (it != nodespecCache_.end())
    return it->second;

  // grab the nodespec and cache it
  // one entry per supported node type
  Spec * ns = NULL;
  if (nodeType == "TestNode")
  {
    ns = TestNode::createSpec();
  } 
  else if (nodeType == "SpatialPoolerNode")
  {
    ns = SpatialPoolerNode::createSpec();
  } 
  else if (nodeType == "TemporalPoolerNode")
  {
    ns = TemporalPoolerNode::createSpec();
  }
  else if (nodeType == "VectorFileEffector")
  {
    ns = VectorFileEffector::createSpec();
  }
  else if (nodeType == "VectorFileSensor")
  {
    ns = VectorFileSensor::createSpec();
  }
  else if (nodeType.find(std::string("py.")) == 0)
  {
    if (!pyLib_)
      pyLib_ = boost::shared_ptr<DynamicPythonLibrary>(new DynamicPythonLibrary());

    ns = getPySpec(pyLib_.get(), nodeType);
  } 
  else 
  {
    NTA_THROW << "getSpec() -- Unsupported node type '" << nodeType << "'";
  }

  if (!ns)
    NTA_THROW << "Unable to get node spec for: " << nodeType;

  nodespecCache_[nodeType] = ns;
  return ns;
}
    
void RegionImplFactory::cleanup()
{
  std::map<std::string, Spec*>::iterator ns;
  // destroy all nodespecs
  for (ns = nodespecCache_.begin(); ns != nodespecCache_.end(); ns++)
  {
    assert(ns->second != NULL);
    // PyNode node specs are destroyed by the C++ PyNode
    if (ns->first.substr(0, 3) == "py.")
    {
      pyLib_->destroySpec(ns->first);
    }
    else
    {
      delete ns->second;
    }

    ns->second = NULL;
  }

  nodespecCache_.clear();

  // Never release the Python dynamic library!
  // This is due to cleanup issues of Python itself
  // See: http://docs.python.org/c-api/init.html#Py_Finalize
  //pyLib_.reset();
}

}

