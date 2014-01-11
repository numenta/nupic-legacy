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

#include <nta/ntypes/Collection.hpp>
#include <nta/utils/Log.hpp>
#include <string>
#include <vector>

namespace nta
{

/*
 * Implementation of the templated Collection class. 
 * This code is used to create explicit instantiations
 * of the Collection class. 
 * It is not compiled into the types library because
 * we instantiate for classes outside of the types library. 
 * For example, Collection<OutputSpec> is built in the 
 * net library where OutputSpec is defined. 
 * See nta/engine/Collections.cpp, which is where the 
 * Collection classes are instantiated.
 */

template <typename T> 
Collection<T>::Collection()
{
}
    
template <typename T> 
Collection<T>::~Collection()
{
}
    
template <typename T> 
size_t Collection<T>::getCount() const
{
  return vec_.size();
}

template <typename T> const
std::pair<std::string, T>& Collection<T>::getByIndex(size_t index) const
{
  NTA_CHECK(index < vec_.size());
  return vec_[index];
}

template <typename T> 
std::pair<std::string, T>& Collection<T>::getByIndex(size_t index)
{
  NTA_CHECK(index < vec_.size());
  return vec_[index];
}

template <typename T> 
bool Collection<T>::contains(const std::string & name) const
{
  typename CollectionStorage::const_iterator i;
  for (i = vec_.begin(); i != vec_.end(); i++)
  {
    if (i->first == name)
      return true;
  }
  return false;
}

template <typename T>
T Collection<T>::getByName(const std::string & name) const
{
  typename CollectionStorage::const_iterator i;
  for (i = vec_.begin(); i != vec_.end(); i++)
  {
    if (i->first == name)
      return i->second;
  }  
  NTA_THROW << "No item named: " << name;
}

template <typename T>
void Collection<T>::add(const std::string & name, const T & item)
{
  // make sure we don't already have something with this name
  typename CollectionStorage::const_iterator i;
  for (i = vec_.begin(); i != vec_.end(); i++)
  {
    if (i->first == name)
    {
      NTA_THROW << "Unable to add item '" << name << "' to collection "
                << "because it already exists";
    }
  }

  // Add the new item to the vector
  vec_.push_back(std::make_pair(name, item));
}


template <typename T>
void Collection<T>::remove(const std::string & name)
{
  typename CollectionStorage::iterator i;
  for (i = vec_.begin(); i != vec_.end(); i++)
  {
    if (i->first == name)
      break;
  }
  if (i == vec_.end())
    NTA_THROW << "No item named '" << name << "' in collection";

  vec_.erase(i);
}

}

