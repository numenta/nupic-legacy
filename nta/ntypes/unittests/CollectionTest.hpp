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
 * Collection unit tests
 */

#ifndef NTA_COLLECTION_TEST_HPP
#define NTA_COLLECTION_TEST_HPP

#include <nta/test/Tester.hpp>

namespace nta
{
  struct CollectionTest : public Tester
  {
    void testEmptyCollection();
    void testCollectionWith_1_Item();
    void testCollectionWith_2_Items();
    void testCollectionWith_137_Items();
    void testCollectionAddRemove();

    virtual void RunTests();        
  };
}

#endif // NTA_COLLECTION_TEST_HPP


