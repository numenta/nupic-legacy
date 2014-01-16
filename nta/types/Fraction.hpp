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

#ifndef NTA_FRACTION_HPP
#define NTA_FRACTION_HPP

#include <ostream>

namespace nta
{
  class Fraction
  {
  private:
    int numerator_, denominator_;
    // arbitrary cutoff -- need to fix overflow handling. 64-bits everywhere?
    const static int overflowCutoff = 10000000;
      
  public:
    Fraction(int _numerator, int _denominator);
    Fraction(int _numerator);
    Fraction();
    
    bool isNaturalNumber();
    
    int getNumerator();
    int getDenominator();
    
    void setNumerator(int _numerator);
    void setDenominator(int _denominator);
    void setFraction(int _numerator, int _denominator);
    
    static unsigned int computeGCD(int a, int b);
    static unsigned int computeLCM(int a,int b);
    
    void reduce();
    
    Fraction operator*(const Fraction& rhs);
    Fraction operator*(const int rhs);
    friend Fraction operator/(const Fraction& lhs, const Fraction& rhs);
    friend Fraction operator-(const Fraction& lhs, const Fraction& rhs);
    Fraction operator+(const Fraction& rhs);
    Fraction operator%(const Fraction& rhs);
    bool operator<(const Fraction& rhs);
    bool operator>(const Fraction& rhs);
    bool operator<=(const Fraction& rhs);
    bool operator>=(const Fraction& rhs);
    friend bool operator==(Fraction lhs, Fraction rhs);
    friend std::ostream& operator<<(std::ostream& out, Fraction rhs);
    
    static Fraction fromDouble(double value, unsigned int tolerance = 10000);
    double toDouble();
  };
}

#endif //NTA_FRACTION_HPP
