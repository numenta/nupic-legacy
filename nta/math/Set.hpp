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
 * Our own set object, to beat Python, at least when computing intersection.
 * TODO: this file is currently superceded by built-in python set(), keeping as a reference, 
 * and we should test which is faster for intersection workload, which is heavily used.
 */

#ifndef NTA_MATH_SET_HPP
#define NTA_MATH_SET_HPP

#include <vector>

namespace nta {

  //--------------------------------------------------------------------------------
  // SET
  //
  // Represents the set with an indicator function stored in a bit array.
  //
  // T is an unsigned integral type.
  // T_byte has the size of a byte.
  //
  // Test from Python:
  // Mac PowerBook 2.8 GHz Core 2 Duo, 10.6.3, -O3 -DNDEBUG, gcc 4.2.1 (Apple 5659)
  // m = 50000, n1 = 40, n2 = 10000: 0.00274658203125 0.00162267684937 1.69262415516
  // m = 50000, n1 = 80, n2 = 10000: 0.00458002090454 0.00179862976074 2.54639448568
  // m = 50000, n1 = 200, n2 = 10000: 0.0124213695526 0.00241708755493 5.13898204774
  // m = 50000, n1 = 500, n2 = 10000: 0.0339875221252 0.00330281257629 10.2904785967
  // m = 50000, n1 = 1000, n2 = 10000: 0.0573344230652 0.00443959236145 12.9143440202
  // m = 50000, n1 = 2500, n2 = 10000: 0.155576944351 0.00838160514832 18.5617124164
  // m = 50000, n1 = 5000, n2 = 10000: 0.256726026535 0.0143656730652 17.8707969595
  //--------------------------------------------------------------------------------
  template <typename T =size_t, typename T_byte =unsigned char>
  class Set
  {
  private:
    T m; // max value of non-zero indices
    T n; // number of non-zeros in s
    std::vector<T_byte> s; // indicator of the non-zeros
  
  public:
    // For Python binding
    inline Set()
    {}

    /**
     * Constructs from a list of n element indices ss, each element being 
     * in the interval [0,m[.
     */
    inline Set(T _m, T _n, T* ss)
      : m(_m),
        n(_n),
        s(m/8 + (m % 8 == 0 ? 0 : 1))
    {
      construct(m, n, ss);
    }

    inline void construct(T _m, T _n, T* ss)
    {
      m = _m;
      n = _n;
      s.resize(m/8 + (m % 8 == 0 ? 0 : 1));

      for (T i = 0; i != n; ++i) 
        s[ss[i] / 8] |= 1 << (ss[i] % 8);
    }

    inline Set(const Set& o)
      : s(o.s)
    {}

    inline Set& operator=(const Set& o)
    {
      s = o.s;
      return *this;
    }

    inline T n_elements() const { return n; }
    inline T max_index() const { return m; }
    inline T n_bytes() const { return s.size(); }
    
    /**
     * Computes the intersection between this and another set (n2, s2).
     * n2 is the number of element in the second s, s2 is a pointer to
     * the first element, which needs to be stored contiguously. s2 needs
     * to store the indices of the elements: (2,7,11) is the set of those
     * 3 elements. 
     * r is the result set, and is also a list of element indices. 
     * This method also returns an integer, which is the number of elements
     * in the intersection (so that r can be allocated once, and its first
     * few positions reused over and over again).
     *
     * NOTE: for best performance, have n2 << n
     */
    inline T intersection(T n2, T* s2, T* r) const
    {
      /*
      if (n < n2) {
        std::cout << "Calling nta::Set::intersection "
                  << "with small set: for best performance, "
                  << "call with smaller set as argument"
                  << std::endl;
      }
      */

      T* rr = r;
      for (T* i = s2, *i_end = s2 + n2; i != i_end; ++i) {
        *r = *i;
        r += (s[*i >> 3] & (1 << (*i % 8))) / (1 << (*i % 8));
      }
      return (T) (r - rr);
    }
  };

} // end namespace nta

//--------------------------------------------------------------------------------
#endif //NTA_MATH_SET_HPP
