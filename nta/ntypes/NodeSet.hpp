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

#ifndef NTA_NODESET_HPP
#define NTA_NODESET_HPP

#include <set>

namespace nta
{
  /**
   * A NodeSet represents the set of currently-enabled nodes in a Region
   * It is just a set of indexes, with the ability to add/remove an index, and the 
   * ability to iterate through enabled nodes. 
   * 
   * There are many ways to represent such a set, and the best way to represent
   * it depends on what nodes are typically enabled through this mechanism. 
   * In NuPIC 1 we used an IndexRangeList, which is a list of index ranges. 
   * This is natural, for example, in the original pictures app, where in 
   * training level N+1 we would enable a square patch of nodes at level N.
   * (which is a list of ranges). In the NuPIC 1 API such ranges were initially 
   * specified with ranges ("1-4"). With new algorithms and new training paradigms
   * I think we may always enable nodes individually. 
   * 
   * So for NuPIC 2 we're starting with the simplest possible solution (a set) and 
   * might switch to something else (e.g. a range list) if needed.
   * 
   * TODO: split into hpp/cpp
   */
  class NodeSet
  {
  public:
    NodeSet(size_t nnodes) : nnodes_(nnodes)
    {
      set_.clear();
    }
    
    typedef std::set<size_t>::const_iterator const_iterator;
    
    const_iterator begin() const 
    { 
      return set_.begin(); 
    };

    const_iterator end() const
    {
      return set_.end();
    }
    
    void allOn()
    {
      for (size_t i = 0; i < nnodes_; i++)
      {
        set_.insert(i);
      }
    }

    void allOff()
    {
      set_.clear();
    }

    void add(size_t index)
    {
      if (index > nnodes_)
      {
        NTA_THROW << "Attempt to enable node with index " << index << " which is larger than the number of nodes " << nnodes_;
      }
      set_.insert(index);
    }

    void remove(size_t index)
    {
      iterator f = set_.find(index);
      if (f == set_.end())
        return;
      set_.erase(f);
    }

  private:
    typedef std::set<size_t>::iterator iterator;
    NodeSet();
    size_t nnodes_;
    std::set<size_t> set_;
  };
    
} // namespace nta



#endif // NTA_NODESET_HPP
