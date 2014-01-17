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

/**
 * @file
 */

#define TIMER_TEST_MS 100

#include "TimerTest.hpp"
#include <nta/utils/Log.hpp>
#include <nta/os/Timer.hpp>
#include <math.h> // fabs
#include <apr-1/apr_time.h>

using namespace nta;

void TimerTest::RunTests() 
{
// Tests are minimal because we have no way to run performance-sensitive tests in a controlled
// environment.

  Timer t1;
  Timer t2(/* startme= */ true);

  TEST(!t1.isStarted());
  TEST(t1.getElapsed() == 0.0);
  TEST(t1.getStartCount() == 0);
  TESTEQUAL("[Elapsed: 0 Starts: 0]", t1.toString());

  apr_sleep(TIMER_TEST_MS);

  TEST(t2.isStarted());
  TEST(t2.getStartCount() == 1);
  TEST(t2.getElapsed() > 0);
  Real64 t2elapsed = t2.getElapsed();

  t1.start();
  apr_sleep(TIMER_TEST_MS);
  t1.stop();

  t2.stop();
  TEST(t1.getStartCount() == 1);
  TEST(t1.getElapsed() > 0);
  TEST(t2.getElapsed() > t2elapsed);
  TEST(t2.getElapsed() > t1.getElapsed());

  t1.start();
  t1.stop();
  TEST(t1.getStartCount() == 2);
}
