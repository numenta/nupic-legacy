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
 * Implementation of Fraction test
 */

#include "FractionTest.hpp"
#include <nta/types/Fraction.hpp>
#include <sstream>
#include <limits>

using namespace nta;

void FractionTest::RunTests()
{
  //create fractions
  Fraction(1);
  Fraction(0);
  Fraction(-1);
  Fraction(1, 2);
  Fraction(2, 1);
  Fraction(-1, 2);
  Fraction(-2, 1);
  Fraction(2, 3);
  Fraction(3, 2);
  // Current overflow cutoff of 10 million
  const static int tooLarge = 20000000;

  SHOULDFAIL(Fraction(3, 0));
  SHOULDFAIL(Fraction(-3, 0));
  SHOULDFAIL(Fraction(0, 0));
  SHOULDFAIL(Fraction(tooLarge, 0));
  SHOULDFAIL(Fraction(tooLarge, 1));
  SHOULDFAIL(Fraction(0, tooLarge));
  // There is some strange interaction with the SHOULDFAIL macro here. 
  // Without this syntax, the compiler thinks we're declaring a new variable
  // tooLarge of type Fraction (which masks the old tooLarge). 
  SHOULDFAIL(Fraction x(tooLarge));
  SHOULDFAIL(Fraction(20000000));
  SHOULDFAIL(Fraction(-tooLarge));
  SHOULDFAIL(Fraction(-tooLarge, 0));
  SHOULDFAIL(Fraction(0, -tooLarge));
  SHOULDFAIL(Fraction(-tooLarge));
  SHOULDFAIL(new Fraction(std::numeric_limits<int>::max()));
  SHOULDFAIL(new Fraction(std::numeric_limits<int>::min()));
    
  //Test isNaturalNumber() (natural numbers must be nonnegative)
  TEST(Fraction(1).isNaturalNumber());
  TEST(Fraction(0).isNaturalNumber());
  TEST(!Fraction(-1).isNaturalNumber());
  TEST(!Fraction(1, 2).isNaturalNumber());
  TEST(Fraction(2, 1).isNaturalNumber());
  TEST(!Fraction(-1, 2).isNaturalNumber());
  TEST(!Fraction(-2, 1).isNaturalNumber());
  TEST(!Fraction(3, 2).isNaturalNumber());
  TEST(!Fraction(-3, 2).isNaturalNumber());

  //Test getNumerator()
  TESTEQUAL(2, Fraction(2, 1).getNumerator());
  TESTEQUAL(0, Fraction(0, 1).getNumerator());
  TESTEQUAL(-2, Fraction(-2, 1).getNumerator());
  TESTEQUAL(2, Fraction(2, -2).getNumerator());
  TESTEQUAL(0, Fraction(0, -2).getNumerator());
  TESTEQUAL(-2, Fraction(-2, -2).getNumerator());

  //Test getDenominator()
  TESTEQUAL(1, Fraction(0).getDenominator());
  TESTEQUAL(1, Fraction(2).getDenominator());
  TESTEQUAL(-2, Fraction(0, -2).getDenominator());
  TESTEQUAL(-2, Fraction(-2, -2).getDenominator());
  
  //Test setNumerator()
  Fraction b(1);
  b.setNumerator(0);
  TESTEQUAL(0, b.getNumerator());
  b = Fraction(2, 3);
  b.setNumerator(-2);
  TESTEQUAL(-2, b.getNumerator());
  b = Fraction(2, -3);
  b.setNumerator(2);
  TESTEQUAL(2, b.getNumerator());

  //Test setDenominator()
  SHOULDFAIL(Fraction(1).setDenominator(0));
  b = Fraction(1);
  b.setDenominator(2);
  TESTEQUAL(2, b.getDenominator());
  b = Fraction(-2, 3);
  b.setDenominator(5);
  TESTEQUAL(5, b.getDenominator());

  //Test setFraction()
  SHOULDFAIL(Fraction(1).setFraction(1, 0));
  SHOULDFAIL(Fraction(-2).setFraction(-3, 0));
  b = Fraction(2);
  b.setFraction(1, 1);
  TEST(Fraction(1) == b);
  b = Fraction(1);
  b.setFraction(-1, 2);
  TEST(Fraction(-1, 2) == b);
  b = Fraction(0);
  b.setFraction(-6, 4);
  TEST(Fraction(-6, 4) == b);
  
  //Test computeGCD()
  TESTEQUAL((UInt32)5, Fraction::computeGCD(5, 10));
  TESTEQUAL((UInt32)1, Fraction::computeGCD(1, 1));
  TESTEQUAL((UInt32)1, Fraction::computeGCD(0, 1));
  TESTEQUAL((UInt32)3, Fraction::computeGCD(3, 0));
  TESTEQUAL((UInt32)1, Fraction::computeGCD(1, 0));
  TESTEQUAL((UInt32)1, Fraction::computeGCD(1, -1));

  //Test computeLCM
  TESTEQUAL((UInt32)10, Fraction::computeLCM(5, 2));
  TESTEQUAL((UInt32)1, Fraction::computeLCM(1, 1));
  TESTEQUAL((UInt32)0, Fraction::computeLCM(0, 0));
  TESTEQUAL((UInt32)0, Fraction::computeLCM(0, -1));
  TESTEQUAL((UInt32)0 , Fraction::computeLCM(-1, 2));
  
  //Test reduce()
  Fraction a = Fraction(1);
  a.reduce();
  TESTEQUAL(1, a.getNumerator());
  TESTEQUAL(1, a.getDenominator());
  a = Fraction(2, 2);
  a.reduce();
  TESTEQUAL(1, a.getNumerator());
  TESTEQUAL(1, a.getDenominator());
  a = Fraction(-1);
  a.reduce();
  TESTEQUAL(-1, a.getNumerator());
  TESTEQUAL(1, a.getDenominator());
  a = Fraction(-1, -1);
  a.reduce();
  TESTEQUAL(1, a.getNumerator());
  TESTEQUAL(1, a.getDenominator());
  a = Fraction(2, -2);
  a.reduce();
  TESTEQUAL(-1, a.getNumerator());
  TESTEQUAL(1, a.getDenominator());
  a = Fraction(-2, 2);
  a.reduce();
  TESTEQUAL(-1, a.getNumerator());
  TESTEQUAL(1, a.getDenominator());
  a = Fraction(20, 6);
  a.reduce();
  TESTEQUAL(10, a.getNumerator());
  TESTEQUAL(3, a.getDenominator());
  a = Fraction(-2, 6);
  a.reduce();
  TESTEQUAL(-1, a.getNumerator());
  TESTEQUAL(3, a.getDenominator());

  //Test *
  Fraction one = Fraction(1);
  Fraction zero = Fraction(0);
  Fraction neg_one = Fraction(-1);
  TEST(one == one*one);
  TEST(one == neg_one*neg_one);
  TEST(zero == zero*one);
  TEST(zero == zero*zero);
  TEST(zero == zero*neg_one);
  TEST(neg_one == one*neg_one);
  TEST(neg_one == neg_one*one);
  TEST(Fraction(10) == one*Fraction(20, 2));

  TEST(one == one*1);
  TEST(one == one*1);
  TEST(zero == zero*1);
  TEST(zero == zero*1);
  TEST(zero == zero*-1);
  TEST(zero == zero*-1);
  TEST(-1 == one*-1);
  TEST(-1 == neg_one*1);
  TEST(Fraction(10) == one*10);
  TEST(Fraction(10) == neg_one*-10);
  
  //Test /
  TEST(one == one/one);
  TEST(zero == zero/one);
  TEST(zero == zero/neg_one);
  TEST(Fraction(-0) == zero/neg_one);
  SHOULDFAIL(one/zero);
  TEST(Fraction(3, 2) == Fraction(3)/Fraction(2));
  TEST(Fraction(2, -3) == Fraction(2)/Fraction(-3));

  //Test -
  TEST(zero == one - one);
  TEST(neg_one == zero - one);
  TEST(one == zero - neg_one);
  TEST(zero == neg_one - neg_one);
  TEST(Fraction(1, 2) == Fraction(3, 2) - one);
  TEST(Fraction(-1, 2) == Fraction(-3, 2) - neg_one);

  //Test +
  TEST(zero == neg_one + one);
  TEST(one == zero + one);
  TEST(one == (neg_one + one) + one);
  TEST(one == one + zero);
  TEST(Fraction(-2) == neg_one + neg_one);
  TEST(Fraction(1, 2) == Fraction(-1, 2) + one);
  TEST(Fraction(-3, 2) == neg_one + Fraction(-1, 2));

  //Test %
  TEST(Fraction(1, 2) == Fraction(3, 2) % one);
  TEST(Fraction(-1, 2) == Fraction(-1, 2) % one);
  TEST(Fraction(3, 2) == Fraction(7, 2) % Fraction(2));
  TEST(Fraction(-1, 2) == Fraction(-3, 2) % one);
  TEST(Fraction(-1, 2) == Fraction(-3, 2) % neg_one);
  TEST(Fraction(1, 2) == Fraction(3, 2) % neg_one);
  SHOULDFAIL(Fraction(1, 2) % Fraction(0));
  SHOULDFAIL(Fraction(-3,2) % Fraction(0, -2));

  //Test <
  TEST(zero < one);
  TEST(!(one < zero));
  TEST(!(zero < zero));
  TEST(!(one < one));
  TEST(Fraction(1, 2) < one);
  TEST(Fraction(-3, 2) < Fraction(1, -2));
  TEST(Fraction(-1, 2) < Fraction(3, 2));

  //Test >
  TEST(one > zero);
  TEST(!(zero > zero));
  TEST(!(one > one));
  TEST(!(zero > one));
  TEST(one > Fraction(1, 2));
  TEST(Fraction(1, -2) > Fraction(-3, 2));
  TEST(Fraction(1, 2) > Fraction(-3, 2));

  //Test <=
  TEST(zero <= one);
  TEST(!(one <= zero));
  TEST(Fraction(1, 2) <= one);
  TEST(Fraction(-3, 2) <= Fraction(1, -2));
  TEST(Fraction(-1, 2) <= Fraction(3, 2));
  TEST(zero <= zero);
  TEST(one <= one);
  TEST(neg_one <= neg_one);
  TEST(Fraction(-7, 4) <= Fraction(14, -8));

  //Test >=
  TEST(one >= zero);
  TEST(!(zero >= one));
  TEST(one >= Fraction(1, 2));
  TEST(Fraction(1, -2) >= Fraction(-3, 2));
  TEST(Fraction(1, 2) >= Fraction(-3, 2));
  TEST(zero >= zero);
  TEST(one >= one);
  TEST(neg_one >= neg_one);
  TEST(Fraction(-7, 4) >= Fraction(14, -8));

  //Test ==
  TEST(one == one);
  TEST(zero == zero);
  TEST(!(one == zero));
  TEST(Fraction(1, 2) == Fraction(2, 4));
  TEST(Fraction(-1, 2) == Fraction(2, -4));
  TEST(Fraction(0, 1) == Fraction(0, -1));
  TEST(Fraction(0, 1) == Fraction(0, 2));

  //Test <<
  std::stringstream ss;
  ss << Fraction(3, 4);
  TESTEQUAL("3/4", ss.str());
  ss.str("");
  ss << Fraction(-2, 4);
  TESTEQUAL("-1/2", ss.str());
  ss.str("");
  ss << Fraction(0, 1);
  TESTEQUAL("0", ss.str());
  ss.str("");
  ss << Fraction(0, -1);
  TESTEQUAL("0", ss.str());
  ss.str("");
  ss << Fraction(1, -2);
  TESTEQUAL("-1/2", ss.str());
  ss.str("");
  ss << Fraction(3, 1);
  TESTEQUAL("3", ss.str());
  ss.str("");
  ss << Fraction(-3, 1);
  TESTEQUAL("-3", ss.str());
  ss.str("");
  ss << Fraction(6, 2);
  TESTEQUAL("3", ss.str());
  ss.str("");
  ss << Fraction(6, -2);
  TESTEQUAL("-3", ss.str());
  ss.str("");
  ss << Fraction(-1, -1);
  TESTEQUAL("1", ss.str());
  ss.str("");
  ss << Fraction(-2, -2);
  TESTEQUAL("1", ss.str());
  ss.str("");

  //Test fromDouble()
  TEST(one == Fraction::fromDouble(1.0));
  TEST(zero == Fraction::fromDouble(0.0));
  TEST(Fraction(1, 2) == Fraction::fromDouble(0.5));
  TEST(Fraction(-1, 2) == Fraction::fromDouble(-0.5));
  TEST(Fraction(333, 1000) == Fraction::fromDouble(.333));
  TEST(Fraction(1, 3) == Fraction::fromDouble(.3333333));
  TEST(Fraction(1, -3) == Fraction::fromDouble(-.33333333));
  SHOULDFAIL(Fraction::fromDouble((double)(tooLarge)));
  SHOULDFAIL(Fraction::fromDouble(1.0/(double)(tooLarge)));
  SHOULDFAIL(Fraction::fromDouble(-(double)tooLarge));
  SHOULDFAIL(Fraction::fromDouble(-1.0/(double)(tooLarge)));
  SHOULDFAIL(Fraction::fromDouble(std::numeric_limits<double>::max()));
  SHOULDFAIL(Fraction::fromDouble(std::numeric_limits<double>::min()));
  SHOULDFAIL(Fraction::fromDouble(-std::numeric_limits<double>::max()));
  SHOULDFAIL(Fraction::fromDouble(-std::numeric_limits<double>::min()));

  //Test toDouble()
  TESTEQUAL(0.0, Fraction(0).toDouble());
  TESTEQUAL(0.0, Fraction(-0).toDouble());
  TESTEQUAL(0.0, Fraction(0, 1).toDouble());
  TESTEQUAL(0.5, Fraction(1, 2).toDouble());
  TESTEQUAL(-0.5, Fraction(-1, 2).toDouble());
  TESTEQUAL(-0.5, Fraction(1, -2).toDouble());
  TESTEQUAL(0.5, Fraction(-1, -2).toDouble());

}
