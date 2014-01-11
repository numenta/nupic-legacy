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


#ifndef NTA_TESTFANIN2LINKPOLICY_HPP
#define NTA_TESTFANIN2LINKPOLICY_HPP

#include <string>
#include <nta/engine/Link.hpp>
#include <nta/ntypes/Dimensions.hpp>

namespace nta
{

  class Link;

  class TestFanIn2LinkPolicy : public LinkPolicy
  {
  public:
    TestFanIn2LinkPolicy(const std::string params, Link* link);

    ~TestFanIn2LinkPolicy();

    void setSrcDimensions(Dimensions& dims);

    void setDestDimensions(Dimensions& dims);
  
    const Dimensions& getSrcDimensions() const;

    const Dimensions& getDestDimensions() const;

    void buildProtoSplitterMap(Input::SplitterMap& splitter) const;

    void setNodeOutputElementCount(size_t elementCount);

    void initialize();

    bool isInitialized() const;

private:
    Link* link_;
    
    Dimensions srcDimensions_;
    Dimensions destDimensions_;

    size_t elementCount_;

    bool initialized_;


  }; // TestFanIn2

} // namespace nta


#endif // NTA_TESTFANIN2LINKPOLICY_HPP
