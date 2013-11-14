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
 * Declarations for math functions
 */

#ifndef NTA_MATH_FUNCTIONS_HPP
#define NTA_MATH_FUNCTIONS_HPP

#include <nta/utils/Log.hpp> // For NTA_ASSERT

#include <cmath>
#include <boost/math/special_functions/gamma.hpp>
#include <boost/math/special_functions/digamma.hpp>
#include <boost/math/special_functions/beta.hpp>
#include <boost/math/special_functions/erf.hpp>
#include <boost/math/special_functions/factorials.hpp>
#include <boost/math/special_functions/binomial.hpp>


namespace nta {


  static const double pi  =  3.14159265358979311600e+00;

  //--------------------------------------------------------------------------------
  template <typename T>
  inline T lgamma(T x)
  {
    return boost::math::lgamma(x);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline T digamma(T x)
  {
    return boost::math::digamma(x);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline T beta(T x, T y)
  {
    return boost::math::beta(x, y);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline T erf(T x)
  {
    return boost::math::erf(x);
  }

  //--------------------------------------------------------------------------------
  double fact(unsigned long n)
  {
    return boost::math::factorial<double>(n);
  }

  //--------------------------------------------------------------------------------
  double binomial(unsigned long n, unsigned long k)
  {
    {
      NTA_ASSERT(k <= n) << "binomial: Wrong arguments: n= " << n << " k= " << k;
    }
    return boost::math::binomial_coefficient<double>(n, k);
  }

  //--------------------------------------------------------------------------------
}

#endif //NTA_MATH_FUNCTIONS_HPP
