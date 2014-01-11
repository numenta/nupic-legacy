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
 * Definitions for the Value class
 * 
 * A Value object holds a Scalar or an Array
 * A ValueMap is essentially a map<string, Value>
 * It is used internally in the conversion of YAML strings to C++ objects. 
 * The API and implementation are geared towards clarify rather than performance, 
 * since it is expected to be used only during network construction.
 */

#ifndef NTA_VALUE_HPP
#define NTA_VALUE_HPP

#include <nta/types/types.h>
#include <nta/types/BasicType.hpp>
#include <nta/ntypes/Scalar.hpp>
#include <nta/ntypes/Array.hpp>
#include <string>
#include <map>
#include <boost/shared_ptr.hpp>

namespace nta
{

  /**
   * The Value class is used to store construction parameters
   * for regions and links. A YAML string specified by the user
   * is parsed and converted into a set of Values. 
   * 
   * A Value is essentially a union of Scalar/Array/string.
   * In turn, a Scalar is a union of NTA_BasicType types, 
   * and an Array is an array of such types. 
   * 
   * A string is similar to an Array of NTA_BasicType_Byte, but
   * is handled differently, so it is separated in the API. 
   * 
   * The Value API uses boost::shared_ptr instead of directly 
   * using the underlying objects, to avoid copying, and because
   * Array may not be copied. 
   */
  class Value
  {
  public:
    Value(boost::shared_ptr<Scalar>& s);
    Value(boost::shared_ptr<Array>& a);
    Value(boost::shared_ptr<std::string>& s);

    enum Category {scalarCategory, arrayCategory, stringCategory};

    bool isArray() const;
    bool isString() const;
    bool isScalar() const;
    Category getCategory() const;

    NTA_BasicType getType() const;

    boost::shared_ptr<Scalar> getScalar() const;

    boost::shared_ptr<Array> getArray() const;

    boost::shared_ptr<std::string> getString() const;

    template <typename T> T getScalarT() const;
    
    const std::string getDescription() const;

  private:
    // Default constructor would not be useful
    Value(); 
    Category category_;
    boost::shared_ptr<Scalar> scalar_;
    boost::shared_ptr<Array> array_;
    boost::shared_ptr<std::string> string_;
  };


  class ValueMap
  {
  public:
    ValueMap();
    ValueMap(const ValueMap& rhs);
    ~ValueMap();
    void add(const std::string& key, const Value& value);

    // map.find(key) != map.end()
    bool contains(const std::string& key) const;

    // map.find(key) + exception if not found
    Value& getValue(const std::string& key) const;

    // Method below are for convenience, bypassing the Value
    boost::shared_ptr<Array> getArray(const std::string& key) const;
    boost::shared_ptr<Scalar> getScalar(const std::string& key) const;
    boost::shared_ptr<std::string> getString(const std::string& key) const;

    // More convenience methods, bypassing the Value and the contained Scalar

    // use default value if not specified in map
    template <typename T> T getScalarT(const std::string& key, T defaultValue) const;

    // raise exception if value is not specified in map
    template <typename T> T getScalarT(const std::string& key) const;

    void dump() const;

    typedef std::map<std::string, Value*>::const_iterator const_iterator;
    const_iterator begin() const;
    const_iterator end() const;

  private:
    // must be a Value* since Value doesn't have a default constructor
    // We own all the items in the map and must delete them in our destructor
    typedef std::map<std::string, Value*>::iterator iterator;
    std::map<std::string, Value*> map_;
  };


}


#endif // NTA_VALUE_HPP



