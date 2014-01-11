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

#ifndef NTA_classifier_result_HPP
#define NTA_classifier_result_HPP

#include <map>
#include <vector>

#include <nta/types/types.hpp>

using namespace std;

namespace nta
{
  namespace algorithms
  {
    namespace cla_classifier
    {

      /** CLA classifier result class.
       *
       * @b Responsibility
       * The ClassifierResult is responsible for storing result data and
       * cleaning up the data when deleted.
       *
       */
      class ClassifierResult
      {
        public:

          /**
           * Constructor.
           */
          ClassifierResult() {}

          /**
           * Destructor - frees memory allocated during lifespan.
           */
          virtual ~ClassifierResult();

          /**
           * Creates and returns a vector for a given step.
           *
           * The vectors created are stored and can be accessed with the
           * iterator methods. The vectors are owned by this class and are
           * deleted in the destructor.
           *
           * @param step The prediction step to create a vector for. If -1, then
           *             a vector for the actual values to use for each bucket
           *             is returned.
           * @param size The size of the desired vector.
           * @param value The value to populate the vector with.
           *
           * @returns The specified vector.
           */
          virtual vector<Real64>* createVector(Int step, UInt size, Real64 value);

          /**
           * Iterator method begin.
           */
          virtual map<Int, vector<Real64>*>::const_iterator begin()
          {
            return result_.begin();
          }

          /**
           * Iterator method end.
           */
          virtual map<Int, vector<Real64>*>::const_iterator end()
          {
            return result_.end();
          }

        private:

          map<Int, vector<Real64>*> result_;

      }; // end class ClassifierResult

    } // end namespace cla_classifier
  } // end namespace algorithms
} // end namespace nta

#endif // NTA_classifier_result_HPP
