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

#include <iostream>
#include <stdexcept>
#include <nta/test/Tester.hpp>
#include "TesterTest.hpp"

namespace nta {

template <class T> const T& Max( const T& t1, const T& t2) { return (t1 > t2) ? t1 : t2; }
template <class T> const T& Min( const T& t1, const T& t2) { return (t1 < t2) ? t1 : t2; }
    
TesterTest::TesterTest()
{
}

TesterTest::~TesterTest()
{
}

// Run all appropriate tests
void TesterTest::RunTests()
{
  TESTEQUAL2("Integer test, should succeed",1,1);
  TESTEQUAL2("Double test, should succeed",23.42,23.42);
  TESTEQUAL2("String test, should succeed","Numenta","Numenta");
  
  // These are probably the only tests in our test suite that should fail!
  TESTEQUAL2("Integer test, should fail",1,0);
  TESTEQUAL2("Double test, should fail",23.42,23.421);
  TESTEQUAL2("String test, should fail","Numenta","Numenta ");
  
  // Test functions in Common
  TESTEQUAL2("Max test", 23.3, Max(23.2, 23.3));
  TESTEQUAL2("Min test", 23.2, Min(23.2, 23.3));
  TESTEQUAL2("Max test", 'b', Max('a', 'b'));
  TESTEQUAL2("Min test", 'a', Min('a', 'b'));
  
  // Now throw an exception to see if we catch it
  throw std::runtime_error("This exception should get caught.");
}

} // end namespace nta

