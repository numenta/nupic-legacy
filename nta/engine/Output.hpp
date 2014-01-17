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
 * Definition of the Internal Output API
 */

#ifndef NTA_OUTPUT_HPP
#define NTA_OUTPUT_HPP

#include <set>
#include <nta/types/types.hpp>
#include <nta/utils/Log.hpp> // temporary, while impl is in this file
namespace nta
{

  class Link;
  class Region;
  class Array;

  /**
   * TODO: document
   */
  class Output
  {
  public:

    /**
     * TODO: document
     * @param region TODO: document
     * @param type TODO: document
     * @param isRegionLevel TODO: document
     */
    Output(Region& region, NTA_BasicType type, bool isRegionLevel);

    /**
     * Destructor
     */
    ~Output();

    /**
     * Outputs need to know their own name
     * @param name TODO: document
     */
    void setName(const std::string& name);

    /**
     * TODO: document
     */
    const std::string& getName() const;

    /**
     * TODO: document
     * @param size TODO: document
     */
    void
    initialize(size_t size);

    /**
     * Does not take ownership
     * @param link TODO: document
     */
    void
    addLink(Link* link);

    /**
     * Called only by Input::removeLink() even
     * if triggered by removing the region that contains us
     * @ param Link TODO: document
     */
    void
    removeLink(Link*);

    /**
     * We cannot delete a region if there are any outgoing links
     * This allows us to check in Network::removeRegion and 
     * the network destructor;
     * @returns TODO: document
     */
    bool
    hasOutgoingLinks();

    /**
     * important to return a const array so caller can't
     * reallocate the buffer.
     * @returns TODO: document
     */
    const Array &
    getData() const;

    /**
     * TODO: document
     * @returns TODO: document
     */
    bool
    isRegionLevel() const;

    /**
     * TODO: document
     * @returns TODO: document
     */
    Region&
    getRegion() const;

    /**
     * TODO: document
     * @returns TODO: document
     */
    size_t
    getNodeOutputElementCount() const;

  private:

    Region& region_; // needed for number of nodes
    Array * data_;
    bool isRegionLevel_;
    // order of links never matters, so store as a set
    // this is different from Input, where they do matter
    std::set<Link*> links_;
    std::string name_;
    size_t nodeOutputElementCount_;
  };

}


#endif // NTA_OUTPUT_HPP
