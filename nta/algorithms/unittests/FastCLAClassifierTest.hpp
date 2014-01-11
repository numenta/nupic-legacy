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
 * Definitions for FastCLAClassifierTest
 *
 * The FastCLAClassifier class is primarily tested in the Python unit tests
 * but this file provides an easy way to check for memory leaks.
 */

#ifndef NTA_FAST_CLA_CLASSIFIER_TEST
#define NTA_FAST_CLA_CLASSIFIER_TEST

#include <nta/test/Tester.hpp>

namespace nta
{

  class FastCLAClassifierTest : public Tester
  {
  public:
    FastCLAClassifierTest() {}

    virtual ~FastCLAClassifierTest() {}

    // Run all appropriate tests.
    virtual void RunTests();

  private:
    void testBasic();

  }; // end class FastCLAClassifierTest

} // end namespace nta

#endif // NTA_FAST_CLA_CLASSIFIER_TEST
