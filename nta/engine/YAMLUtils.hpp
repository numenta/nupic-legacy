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
#ifndef NTA_YAML_HPP
#define NTA_YAML_HPP


#include <nta/types/types.hpp>
#include <nta/ntypes/Value.hpp>
#include <nta/ntypes/Collection.hpp>
#include <nta/engine/Spec.hpp>

namespace nta
{

  namespace YAMLUtils
  {
    /* 
     * For converting default values
     */
    Value toValue(const std::string& yamlstring, NTA_BasicType dataType);

    /* 
     * For converting param specs for Regions and LinkPolicies
     */
    ValueMap toValueMap(
      const char* yamlstring, 
      Collection<ParameterSpec>& parameters,
      const std::string & nodeType = "",
      const std::string & regionName = ""
      );


  } // namespace YAMLUtils
} // namespace nta

#endif //  NTA_YAML_HPP

