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
 * Implementation of BasicType test
 */

#include "NodeSetTest.hpp"
#include <nta/ntypes/NodeSet.hpp>

using namespace nta;

void NodeSetTest::RunTests()
{
  NodeSet ns(4);
  
  TEST(ns.begin() == ns.end());
  ns.allOn();
  NodeSet::const_iterator i = ns.begin();
  TEST(*i == 0);
  ++i;
  TEST(*i == 1);
  ++i;
  TEST(*i == 2);
  ++i;
  TEST(*i == 3);
  ++i;
  TEST(i == ns.end());
  
  ns.allOff();
  TEST(ns.begin() == ns.end());
  
  ns.add(1);
  ns.add(3);
  i = ns.begin();
  TEST(*i == 1);
  ++i;
  TEST(*i == 3);
  ++i;
  TEST(i == ns.end());

  ns.add(4);
  i = ns.begin();
  TEST(*i == 1);
  ++i;
  TEST(*i == 3);
  ++i;
  TEST(*i == 4);
  ++i;
  TEST(i == ns.end());
  
  SHOULDFAIL(ns.add(5));
  
  ns.remove(3);
  i = ns.begin();
  TEST(*i == 1);
  ++i;
  TEST(*i == 4);
  ++i;
  TEST(i == ns.end());

  // this should have no effect since 3 has already been removed
  ns.remove(3);
  i = ns.begin();
  TEST(*i == 1);
  ++i;
  TEST(*i == 4);
  ++i;
  TEST(i == ns.end());

}
