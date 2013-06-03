#ifndef NTA_LCG_HPP
#define NTA_LCG_HPP

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

/**
 * Note that the code in this file is shared by the tools, so 
 * depedencies should be kept to a bare minimum. At present there are 
 * few to no dependencies of the tools on math, and this header is an 
 * exception. Care should be taken to keep the libraries as well-separated
 * as possible.
 */

#ifdef NUPIC2
#error "RandomNumberGenerator.hpp should not be in NuPIC2 -- it is not used anywhere"
#else

namespace nta {

/**
 * A linear congruential pseudo-random number generator.
 * Portable variant of lrand48.
 */
class LCG
{
  unsigned long long state_;
public:
  LCG(unsigned long long seed) : state_(seed) {}

  unsigned long long next()
  {
    state_ = ((state_ * 0x5DEECE66DLL) + 0xBLL) % (0x1LL << 48);
    return state_;
  }

  unsigned long long next(unsigned long long upperBoundNotInclusive)
  {
    static unsigned long long maxull = (unsigned long long) -1;
    static unsigned long long max = maxull - (maxull % upperBoundNotInclusive);
    unsigned long long sample;
    do {
      sample = next();
    }
    while(sample > max);
    return sample % upperBoundNotInclusive;
  }

  double nextDouble()
  {
    const static unsigned long long max = 0x1ULL << 48;
    unsigned long long value = next(max);
    return double(value) / double(max);
  }

  inline unsigned long long operator()()
  {
    return next();
  }
};

class CMWC4096
{
  unsigned int Q[4096];
  unsigned int c;
  unsigned int i;

  unsigned int next32()
  {
    unsigned long long a=18782LL, b=4294967295LL; 
    unsigned int r = b-1; 
    i = (i+1) & 4095; 
    unsigned long long t = a*Q[i]+c; 
    c = (t>>32);
    t = (t&b)+c; 
    if(t>r) { c++; t=t-b; }
    Q[i] = r-t;
    return Q[i];
  }   
public:
  CMWC4096(unsigned long long seed) : c(362436), i(4095)
  {
    LCG g(seed);
    // Fill Q.
    for(int i=0; i<4096; ++i) {
      Q[i] = (unsigned int) g.next();
    }   
  }

  unsigned long long next()
  {
    unsigned long long lo = next32();
    unsigned long long hi = next32();
    return lo | (hi << 32);
  }

  unsigned long long next(unsigned long long upperBoundNotInclusive)
  {
    static unsigned long long maxull = (unsigned long long) -1;
    static unsigned long long max = maxull - (maxull % upperBoundNotInclusive);
    unsigned long long sample;
    do {
      sample = next();
    }
    while(sample > max);
    return sample % upperBoundNotInclusive;
  }

  double nextDouble()
  {
    const static unsigned long long max = 0x1ULL << 48;
    unsigned long long value = next(max);
    return double(value) / double(max);
  }
};

}

#endif

