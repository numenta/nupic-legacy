/*
 * ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
 * Numenta, Inc. a separate commercial license for this software code, the
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
 * Implementation of functions test
 */

#include "FunctionsTest.hpp"
#include <nta/math/functions.hpp>
#include <iostream>

using namespace nta;
using namespace std;

void FunctionsTest::RunTests()
// functions are: fact,  binomial; and important tresholds are 171, 2000, 171 respectively 
{
  int low=5;
  int tr_low=170;
  int tr_hi=172;
  int high=300;

  // test fact
  cout << "testing fact():" << endl;
  cout << fact(low) << " " << fact(tr_low) << " " << fact(tr_hi) << " " << fact(high) << endl;

  // test binomial
  cout << "testing binomial():" << endl;
  cout << binomial(low, 3) << " " << binomial(tr_low, 50) << " " << binomial(tr_hi, 50) << " " << binomial(high,50) << " " << binomial(1999,50) << " " << binomial(3000, 100) << endl;

}

