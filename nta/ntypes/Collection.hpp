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

#ifndef NTA_COLLECTION_HPP
#define NTA_COLLECTION_HPP

#include <string>
#include <vector>

namespace nta
{
  // A collection is a templated class that contains items of type t.
  // It supports lookup by name and by index. The items are stored in a map
  // and copies are also stored in a vector (it's Ok to use pointers).
  // You can add items using the add() method.
  //
  template <typename T>
  class Collection
  {
  public:
    Collection();
    virtual ~Collection();
    
    size_t getCount() const;

    // This method provides access by index to the contents of the collection
    // The indices are in insertion order.
    //

    const std::pair<std::string, T>& getByIndex(size_t index) const;
  
    bool contains(const std::string & name) const;

    T getByName(const std::string & name) const;

    // TODO: move add/remove to a ModifiableCollection subclass
    // This method should be internal but is currently tested
    // in net_test.py in test_node_spec
    void add(const std::string & name, const T & item);

    void remove(const std::string& name);


#ifdef NTA_INTERNAL
    std::pair<std::string, T>& getByIndex(size_t index);
#endif

  private:
    typedef std::vector<std::pair<std::string, T> > CollectionStorage;
    CollectionStorage vec_; 
  };
}

#endif

