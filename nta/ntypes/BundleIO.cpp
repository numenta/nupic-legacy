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

#include <nta/ntypes/BundleIO.hpp>
#include <nta/os/Path.hpp>
#include <nta/utils/Log.hpp>

namespace nta
{
  BundleIO::BundleIO(const std::string& bundlePath, const std::string& label, 
                     const std::string& regionName, bool isInput) :
    isInput_(isInput),
    bundlePath_(bundlePath), 
    regionName_(regionName),
    ostream_(nullptr), 
    istream_(nullptr)
  {
    if (! Path::exists(bundlePath_))
      NTA_THROW << "Network bundle " << bundlePath << " does not exist";
    
    filePrefix_ = Path::join(bundlePath, label + "-");
  }
  
  BundleIO::~BundleIO()
  {
    if (istream_)
    {
      if (istream_->is_open())
        istream_->close();
      delete istream_;
      istream_ = nullptr;
    }
    if (ostream_)
    {
      if (ostream_->is_open())
        ostream_->close();
      delete ostream_;
      ostream_ = nullptr;
    }
  }

  std::ofstream& BundleIO::getOutputStream(const std::string& name) const
  {
    NTA_CHECK(!isInput_);
    
    checkStreams_();
    
    ostream_ = new OFStream(getPath(name).c_str(), std::ios::out | std::ios::binary);
    if (!ostream_->is_open())
    {
      NTA_THROW << "getOutputStream - Unable to open bundle file " << name
                << " for region " << regionName_ << " in network bundle "
                << bundlePath_;
    }
    
    return *ostream_;
  }
  
  std::ifstream& BundleIO::getInputStream(const std::string& name) const
  {
    NTA_CHECK(isInput_);
    
    checkStreams_();
    
    istream_ = new IFStream(getPath(name).c_str(), std::ios::in | std::ios::binary);
    if (!istream_->is_open())
    {
      NTA_THROW << "getInputStream - Unable to open bundle file " << name
                << " for region " << regionName_ << " in network bundle "
                << bundlePath_;
    }
    
    return *istream_;
  }
  
  std::string BundleIO::getPath(const std::string& name) const
  {
    return filePrefix_ + name;
  }
  

  // Before a request for a new stream, 
  // there should be no open streams. 
  void BundleIO::checkStreams_() const
  {
    // Catch implementation errors and make it easier to 
    // support direct serialization to/from archives
    if (isInput_ && istream_ != nullptr && istream_->is_open())
      NTA_THROW << "Internal Error: istream_ has not been closed";
    
    if (!isInput_ && ostream_ != nullptr && ostream_->is_open())
      NTA_THROW << "Internal Error: ostream_ has not been closed";
  }

} // namespace nta

