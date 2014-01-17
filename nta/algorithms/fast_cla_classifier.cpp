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

#include <deque>
#include <iostream>
#include <limits>
#include <map>
#include <string>
#include <sstream>
#include <vector>
#include <stdio.h>

#include <nta/algorithms/bit_history.hpp>
#include <nta/algorithms/classifier_result.hpp>
#include <nta/algorithms/fast_cla_classifier.hpp>
#include <nta/types/types.hpp>
#include <nta/utils/Log.hpp>

using namespace std;

namespace nta
{
  namespace algorithms
  {
    namespace cla_classifier
    {

      FastCLAClassifier::FastCLAClassifier(
          const vector<UInt>& steps, Real64 alpha, Real64 actValueAlpha,
          UInt verbosity) : alpha_(alpha), actValueAlpha_(actValueAlpha),
          learnIteration_(0), recordNumMinusLearnIteration_(0),
          maxBucketIdx_(0), version_(Version), verbosity_(verbosity)
      {
        for (vector<UInt>::const_iterator it = steps.begin();
             it != steps.end(); ++it)
        {
          steps_.push_back(*it);
        }
        recordNumMinusLearnIterationSet_ = false;
        maxSteps_ = 0;
        for (UInt i = 0; i < steps_.size(); ++i)
        {
          UInt current = steps_.at(i) + 1;
          if (current > maxSteps_)
          {
            maxSteps_ = current;
          }
        }
        actualValues_.push_back(0.0);
        actualValuesSet_.push_back(false);
      }

      FastCLAClassifier::~FastCLAClassifier()
      {
        // Clean up patternNZHistory_.
        for (deque<vector<UInt>*>::const_iterator it =
             patternNZHistory_.begin(); it != patternNZHistory_.end(); ++it)
        {
          delete *it;
        }
        // Clean up activeBitHistory_.
        for (map<UInt, map<UInt, BitHistory*>*>::const_iterator it =
             activeBitHistory_.begin(); it != activeBitHistory_.end(); ++it)
        {
          for (map<UInt, BitHistory*>::const_iterator it2 =
               it->second->begin(); it2 != it->second->end(); ++it2)
          {
            delete it2->second;
          }
          delete it->second;
        }
      }

      void FastCLAClassifier::fastCompute(
          UInt recordNum, const vector<UInt>& patternNZ, UInt bucketIdx,
          Real64 actValue, bool category, bool learn, bool infer,
          ClassifierResult* result)
      {
        // Save the offset between recordNum and learnIteration_ if this is the
        // first compute.
        if (!recordNumMinusLearnIterationSet_)
        {
          recordNumMinusLearnIteration_ = recordNum - learnIteration_;
          recordNumMinusLearnIterationSet_ = true;
        }

        // Update the learn iteration.
        learnIteration_ = recordNum - recordNumMinusLearnIteration_;

        // Update the input pattern history.
        vector<UInt>* newPatternNZ = new vector<UInt>();
        for (UInt i = 0; i < patternNZ.size(); ++i)
        {
          newPatternNZ->push_back(patternNZ[i]);
        }
        patternNZHistory_.push_front(newPatternNZ);
        iterationNumHistory_.push_front(learnIteration_);
        if (patternNZHistory_.size() > maxSteps_)
        {
          delete patternNZHistory_.back();
          patternNZHistory_.pop_back();
          iterationNumHistory_.pop_back();
        }

        // If inference is enabled, compute the likelihoods and add them to the
        // return value.
        if (infer)
        {
          // Add the actual values to the return value. For buckets that haven't
          // been seen yet, the actual value doesn't matter since it will have
          // zero likelihood.
          vector<Real64>* actValueVector = result->createVector(
              -1, actualValues_.size(), 0.0);
          for (UInt i = 0; i < actualValues_.size(); ++i)
          {
            if (actualValuesSet_[i])
            {
              (*actValueVector)[i] = actualValues_[i];
            } else {
              // if doing 0-step ahead prediction, we shouldn't use any
              // knowledge of the classification input during inference
              if (steps_.at(0) == 0)
              {
                (*actValueVector)[i] = 0;
              } else {
                (*actValueVector)[i] = actValue;
              }
            }
          }

          // Generate the predictions for each steps-ahead value
          for (vector<UInt>::const_iterator step = steps_.begin();
               step != steps_.end(); ++step)
          {
            // Skip if we don't have data yet.
            if (activeBitHistory_.find(*step) == activeBitHistory_.end())
            {
              // This call creates the vector with specified default values.
              result->createVector(
                  *step, actualValues_.size(), 1.0 / actualValues_.size());
              continue;
            }

            vector<Real64>* likelihoods = result->createVector(
                *step, maxBucketIdx_ + 1, 0.0);
            vector<Real64> bitVotes(maxBucketIdx_ + 1, 0.0);

            for (vector<UInt>::const_iterator bit = patternNZ.begin();
                 bit != patternNZ.end(); ++bit)
            {
              if (activeBitHistory_[*step]->find(*bit) !=
                  activeBitHistory_[*step]->end())
              {
                BitHistory* history =
                    activeBitHistory_[*step]->find(*bit)->second;
                for (UInt i = 0; i < bitVotes.size(); ++i) {
                  bitVotes[i] = 0.0;
                }
                history->infer(learnIteration_, &bitVotes);
                for (UInt i = 0; i < bitVotes.size(); ++i) {
                  (*likelihoods)[i] += bitVotes[i];
                }
              }
            }
            Real64 total = 0.0;
            for (UInt i = 0; i < likelihoods->size(); ++i)
            {
              total += (*likelihoods)[i];
            }
            for (UInt i = 0; i < likelihoods->size(); ++i)
            {
              if (total > 0.0)
              {
                (*likelihoods)[i] = (*likelihoods)[i] / total;
              } else {
                (*likelihoods)[i] = 1.0 / likelihoods->size();
              }
            }
          }
        }

        // If learning is enabled, update the bit histories.
        if (learn)
        {
          // Update the predicted actual values for each bucket.
          if (bucketIdx > maxBucketIdx_)
          {
            maxBucketIdx_ = bucketIdx;
          }
          while (actualValues_.size() <= maxBucketIdx_)
          {
            actualValues_.push_back(0.0);
            actualValuesSet_.push_back(false);
          }
          if (!actualValuesSet_[bucketIdx] || category)
          {
            actualValues_[bucketIdx] = actValue;
            actualValuesSet_[bucketIdx] = true;
          } else {
            actualValues_[bucketIdx] =
                ((1.0 - actValueAlpha_) * actualValues_[bucketIdx]) +
                (actValueAlpha_ * actValue);
          }

          for (UInt i = 0; i < steps_.size(); ++i)
          {
            UInt step = steps_[i];

            // Check if there is a pattern that should be assigned to this
            // classification in our history. If not, skip it.
            bool found = false;
            deque<vector<UInt>*>::const_iterator patternIteration =
                                                  patternNZHistory_.begin();
            for (deque<UInt>::const_iterator learnIteration =
                 iterationNumHistory_.begin();
                 learnIteration !=iterationNumHistory_.end();
                 ++learnIteration, ++patternIteration)
            {
              if (*learnIteration == (learnIteration_ - step))
              {
                found = true;
                break;
              }
            }
            if (!found)
            {
              continue;
            }

            // Store classification info for each active bit from the pattern
            // that we got step time steps ago.
            const vector<UInt>* learnPatternNZ = *patternIteration;
            for (UInt j = 0; j < learnPatternNZ->size(); ++j)
            {
              UInt bit = learnPatternNZ->at(j);
              if (activeBitHistory_.find(step) == activeBitHistory_.end())
              {
                activeBitHistory_.insert(pair<UInt, map<UInt, BitHistory*>*>(
                      step, new map<UInt, BitHistory*>()));
              }
              map<UInt, BitHistory*>::const_iterator it =
                  activeBitHistory_[step]->find(bit);
              if (it == activeBitHistory_[step]->end())
              {
                (*activeBitHistory_[step])[bit] =
                    new BitHistory(bit, step, alpha_, verbosity_);
              }
              (*activeBitHistory_[step])[bit]->store(learnIteration_, bucketIdx);
            }
          }
        }
      }

      UInt FastCLAClassifier::persistentSize() const
      {
        // TODO: this won't scale!
        stringstream s;
        s.flags(ios::scientific);
        s.precision(numeric_limits<double>::digits10 + 1);
        this->save(s);
        return s.str().size();
      }

      void FastCLAClassifier::save(ostream& outStream) const
      {
        // Write a starting marker and version.
        outStream << "FastCLAClassifier" << endl;
        outStream << version_ << endl;

        // Store the simple variables first.
        outStream << version() << " "
                  << alpha_ << " "
                  << actValueAlpha_ << " "
                  << learnIteration_ << " "
                  << maxSteps_ << " "
                  << maxBucketIdx_ << " "
                  << verbosity_ << " "
                  << endl;

        // V1 additions.
        outStream << recordNumMinusLearnIteration_ << " "
                  << recordNumMinusLearnIterationSet_ << " ";
        outStream << iterationNumHistory_.size() << " ";
        for (deque<UInt>::const_iterator learnIteration =
             iterationNumHistory_.begin(); learnIteration !=
             iterationNumHistory_.end(); ++learnIteration)
        {
          outStream << *learnIteration << " ";
        }
        outStream << endl;

        // Store the different prediction steps.
        outStream << steps_.size() << " ";
        for (UInt i = 0; i < steps_.size(); ++i)
        {
          outStream << steps_[i] << " ";
        }
        outStream << endl;

        // Store the input pattern history.
        vector<UInt>* pattern;
        outStream << patternNZHistory_.size() << " ";
        for (UInt i = 0; i < patternNZHistory_.size(); ++i)
        {
          pattern = patternNZHistory_[i];
          outStream << pattern->size() << " ";
          for (UInt j = 0; j < pattern->size(); ++j)
          {
            outStream << (*pattern)[j] << " ";
          }
        }
        outStream << endl;

        // Store the bucket duty cycles.
        outStream << activeBitHistory_.size() << " ";
        for (map<UInt, map<UInt, BitHistory*>*>::const_iterator it1 =
             activeBitHistory_.begin(); it1 != activeBitHistory_.end(); ++it1)
        {
          outStream << it1->first << " ";
          outStream << it1->second->size() << " ";
          for (map<UInt, BitHistory*>::const_iterator it2 =
               it1->second->begin(); it2 != it1->second->end(); ++it2)
          {
            outStream << it2->first << " ";
            it2->second->save(outStream);
          }
        }

        // Store the actual values for each bucket.
        outStream << actualValues_.size() << " ";
        for (UInt i = 0; i < actualValues_.size(); ++i)
        {
          outStream << actualValues_[i] << " ";
          outStream << actualValuesSet_[i] << " ";
        }
        outStream << endl;

        // Write an ending marker.
        outStream << "~FastCLAClassifier" << endl;

      }

      void FastCLAClassifier::load(istream& inStream)
      {
        // Check the starting marker.
        string marker;
        inStream >> marker;
        NTA_CHECK(marker == "FastCLAClassifier");

        // Check the version.
        UInt version;
        inStream >> version;
        NTA_CHECK(version <= 1);

        // Load the simple variables.
        inStream >> version_
                 >> alpha_
                 >> actValueAlpha_
                 >> learnIteration_
                 >> maxSteps_
                 >> maxBucketIdx_
                 >> verbosity_;

        // V1 additions.
        UInt numIterationHistory;
        UInt curIterationNum;
        if (version == 1)
        {
          inStream >> recordNumMinusLearnIteration_
                   >> recordNumMinusLearnIterationSet_;
          inStream >> numIterationHistory;
          for (UInt i = 0; i < numIterationHistory; ++i)
          {
            inStream >> curIterationNum;
            iterationNumHistory_.push_back(curIterationNum);
          }
        } else {
          recordNumMinusLearnIterationSet_ = false;
        }

        // Load the prediction steps.
        steps_.clear();
        UInt size;
        UInt step;
        inStream >> size;
        for (UInt i = 0; i < size; ++i)
        {
          inStream >> step;
          steps_.push_back(step);
        }

        // Load the input pattern history.
        inStream >> size;
        UInt vSize;
        for (UInt i = 0; i < size; ++i)
        {
          inStream >> vSize;
          vector<UInt>* v = new vector<UInt>(vSize);
          for (UInt j = 0; j < vSize; ++j)
          {
            inStream >> (*v)[j];
          }
          patternNZHistory_.push_back(v);
          if (version == 0)
          {
            iterationNumHistory_.push_back(
                learnIteration_ - (size - i));
          }
        }

        // Load the bucket duty cycles.
        UInt numSteps;
        UInt numInputBits;
        UInt inputBit;
        BitHistory* bitHistory;
        map<UInt, BitHistory*>* bitHistoryMap;
        inStream >> numSteps;
        for (UInt i = 0; i < numSteps; ++i)
        {
          inStream >> step;
          inStream >> numInputBits;
          bitHistoryMap = new map<UInt, BitHistory*>();
          for (UInt j = 0; j < numInputBits; ++j)
          {
            inStream >> inputBit;
            bitHistory = new BitHistory();
            bitHistory->load(inStream);
            bitHistoryMap->insert(
                pair<UInt, BitHistory*>(inputBit, bitHistory));
          }
          activeBitHistory_.insert(
              pair<UInt, map<UInt, BitHistory*>*>(step, bitHistoryMap));
        }

        // Load the actual values for each bucket.
        UInt numBuckets;
        Real64 actualValue;
        bool actualValueSet;
        inStream >> numBuckets;
        for (UInt i = 0; i < numBuckets; ++i)
        {
          inStream >> actualValue;
          actualValues_.push_back(actualValue);
          inStream >> actualValueSet;
          actualValuesSet_.push_back(actualValueSet);
        }

        // Check for the end marker.
        inStream >> marker;
        NTA_CHECK(marker == "~FastCLAClassifier");

        // Update the version number.
        version_ = Version;
      }

    } // end namespace cla_classifier
  } // end namespace algorithms
} // end namespace nta
