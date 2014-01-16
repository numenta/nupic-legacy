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
 * Definition of the LinkPolicy class
 */

#ifndef NTA_LINKPOLICY_HPP
#define NTA_LINKPOLICY_HPP

#include <string>
#include <nta/engine/Input.hpp> // SplitterMap definition

// LinkPolicy is an interface class subclassed by all link policies
namespace nta 
{


  class Dimensions;

  class LinkPolicy
  {
    // Subclasses implement this constructor:
    //    LinkPolicy(const std::string params, const Dimensions& srcDimensions,
    //               const Dimensions& destDimensions);

  public:
    virtual ~LinkPolicy() {};
    virtual void setSrcDimensions(Dimensions& dims) = 0;
    virtual void setDestDimensions(Dimensions& dims) = 0;
    virtual const Dimensions& getSrcDimensions() const = 0;
    virtual const Dimensions& getDestDimensions() const = 0;
    // initialization is probably unnecessary, but it lets
    // us do a sanity check before generating the splitter map. 
    virtual void initialize() = 0;
    virtual bool isInitialized() const = 0;
    virtual void setNodeOutputElementCount(size_t elementCount) = 0;


    // A "protoSplitterMap" specifies which source output nodes send 
    // data to which dest input nodes. 
    // if protoSplitter[destNode][x] == srcNode for some x, then 
    // srcNode sends its output to destNode. 
    //
    virtual void buildProtoSplitterMap(Input::SplitterMap& splitter) const = 0;

  };


} // namespace nta

#endif // NTA_LINKPOLICY_HPP
