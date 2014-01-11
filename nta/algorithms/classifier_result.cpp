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

#include <map>
#include <vector>

#include <nta/algorithms/classifier_result.hpp>
#include <nta/types/types.hpp>

using namespace std;

namespace nta
{
  namespace algorithms
  {
    namespace cla_classifier
    {

      ClassifierResult::~ClassifierResult()
      {
        for (map<Int, vector<Real64>*>::const_iterator it = result_.begin();
             it != result_.end(); ++it)
        {
          delete it->second;
        }
      }

      vector<Real64>* ClassifierResult::createVector(Int step, UInt size,
                                                Real64 value)
      {
        vector<Real64>* v;
        map<Int, vector<Real64>*>::const_iterator it = result_.find(step);
        if (it != result_.end())
        {
          v = it->second;
        } else {
          v = new vector<Real64>(size, value);
          result_.insert(pair<Int, vector<Real64>*>(step, v));
        }
        return v;
      }

    } // end namespace cla_classifier
  } // end namespace algorithms
} // end namespace nta
