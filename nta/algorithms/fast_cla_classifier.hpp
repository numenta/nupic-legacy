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
 * Definitions for the CLAClassifier.
 */

#ifndef NTA_fast_cla_classifier_HPP
#define NTA_fast_cla_classifier_HPP

#include <deque>
#include <iostream>
#include <map>
#include <string>
#include <vector>

#include <nta/types/types.hpp>

using namespace std;

namespace nta
{
  namespace algorithms
  {
    namespace cla_classifier
    {

      const UInt Version = 1;

      class BitHistory;
      class ClassifierResult;

      /** CLA classifier implementation in C++.
       *
       * @b Responsibility
       * The CLAClassifier is responsible for computing the likelihoods for
       * each bucket when given an input pattern from the level below. This
       * includes keeping track of past inputs and learning how each input bit
       * history predicts future bucket values.
       *
       * @b Description
       * The input pattern history is stored as patternNZHistory_ and the duty
       * cycles are stored in BitHistory objects in activeBitHistory_.
       *
       */
      class FastCLAClassifier
      {
        public:

          /**
           * Constructor for use when deserializing.
           */
          FastCLAClassifier() {}

          /**
           * Constructor.
           *
           * @param steps The different number of steps to learn and predict.
           * @param alpha The alpha to use when decaying the duty cycles.
           * @param actValueAlpha The alpha to use when decaying the actual
           *                      values for each bucket.
           * @param verbosity The logging verbosity.
           */
          FastCLAClassifier(
              const vector<UInt>& steps, Real64 alpha, Real64 actValueAlpha,
              UInt verbosity);

          /**
           * Destructor.
           */
          virtual ~FastCLAClassifier();

          /**
           * Compute the likelihoods for each bucket.
           *
           * @param recordNum An incrementing integer for each record. Gaps in
           *                  numbers correspond to missing records.
           * @param patternNZ The active input bit indices.
           * @param bucketIdx The current value bucket index.
           * @param actValue The current scalar value.
           * @param category Whether the actual values represent categories.
           * @param learn Whether or not to perform learning.
           * @param infer Whether or not to perform inference.
           * @param result A mapping from prediction step to a vector of
           *               likelihoods where the value at an index corresponds
           *               to the bucket with the same index. In addition, the
           *               values for key 0 correspond to the actual values to
           *               used when predicting each bucket.
           */
          virtual void fastCompute(
              UInt recordNum, const vector<UInt>& patternNZ, UInt bucketIdx,
              Real64 actValue, bool category, bool learn, bool infer,
              ClassifierResult* result);

          UInt version() const
          {
            return version_;
          }

          /**
           * Get the size of the string needed for the serialized state.
           */
          UInt persistentSize() const;

          /**
           * Save the state to the ostream.
           */
          void save(ostream& outStream) const;

          /**
           * Load state from istream.
           */
          void load(istream& inStream);

        private:
          // The list of prediction steps to learn and infer.
          vector<UInt> steps_;
          // The alpha used to decay the duty cycles in the BitHistorys.
          Real64 alpha_;
          // The alpha used to decay the actual values used for each bucket.
          Real64 actValueAlpha_;
          // An incrementing count of the number of learning iterations that
          // have been performed.
          UInt learnIteration_;
          // This contains the offset between the recordNum (provided by
          // caller) and learnIteration (internal only, always starts at 0).
          UInt recordNumMinusLearnIteration_;
          bool recordNumMinusLearnIterationSet_;
          // The maximum number of the prediction steps.
          UInt maxSteps_;
          // Stores the input pattern history, starting with the previous input
          // and containing _maxSteps total input patterns.
          deque<vector<UInt>*> patternNZHistory_;
          deque<UInt> iterationNumHistory_;
          // Mapping from the number of steps in the future to predict to the
          // input bit index to a BitHistory that contains the duty cycles for
          // each bucket.
          map<UInt, map<UInt, BitHistory*>* > activeBitHistory_;
          // The highest bucket index that has been seen so far.
          UInt maxBucketIdx_;
          // The current actual values used for each bucket index. The index of
          // the actual value matches the index of the bucket.
          vector<Real64> actualValues_;
          // A boolean that distinguishes between actual values that have been
          // seen and those that have not.
          vector<bool> actualValuesSet_;
          UInt version_;
          UInt verbosity_;
      }; // end class FastCLAClassifier

    } // end namespace cla_classifier
  } // end namespace algorithms
} // end namespace nta

#endif // NTA_fast_cla_classifier_HPP
