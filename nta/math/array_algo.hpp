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
 * Algorithms on arrays, dense or sparse. Contains speed-optimized asm
 * code that uses SIMD instructions provided by SSE in x86, only for darwin86
 * so far.
 */

#ifndef NTA_ARRAY_ALGO_HPP
#define NTA_ARRAY_ALGO_HPP

#include <math.h>
#include <iterator>
#include <algorithm>

#ifdef NUPIC2
#include <nta/utils/Random.hpp> // For the official Numenta RNG
#else
#include <nta/common/Random.hpp> // For the official Numenta RNG
#endif

#include <nta/math/math.hpp>
#include <nta/math/types.hpp>

#ifdef WIN32
#undef min
#undef max
#endif

// This include because on darwin86, vDSP provides high quality optimized
// code that exploits SSE. 
#ifdef NTA_PLATFORM_darwin86
#include <vecLib/vDSP.h>
#endif

namespace nta {

#ifdef NTA_PLATFORM_darwin86
  //--------------------------------------------------------------------------------
  // Checks whether the SSE supports the operations we need, i.e. SSE3 and SSE4. 
  // Returns highest SSE level supported by the CPU: 1, 2, 3 or 41 or 42. It also
  // returns -1 if SSE is not present at all.
  //
  // Refer to Intel manuals for details. Basically, after call to cpuid, the 
  // interesting bits are set to 1 in either ecx or edx:
  // If 25th bit of edx is 1, we have sse: 2^25 = 33554432.
  // If 26th bit of edx is 1, we have sse2: 2^26 = 67108864.
  // If 0th bit of ecx is 1, we have sse3.
  // If 19th bit of ecx is 1, we have sse4.1: 2^19 = 524288.
  // If 20th bit of ecx is 1, we have sse4.2: 2^20 = 1048576.
  //--------------------------------------------------------------------------------
  static int checkSSE()
  {
    unsigned int f = 1, c,d;

#ifdef NTA_PLATFORM_win32

    __asm {
      mov eax, f
        cpuid
        mov c, ecx
        mov d, edx
        }
            
#elif defined(NTA_PLATFORM_darwin86)

    unsigned int a,b;

    // PIC-compliant asm
    __asm__ __volatile__(
                         "pushl %%ebx\n\t"
                         "cpuid\n\t"
                         "movl %%ebx, %1\n\t"
                         "popl %%ebx\n\t"
                         : "=a" (a), "=r" (b), "=c" (c), "=d" (d)
                         : "a" (f)
                         : "cc"
                         );
#endif

    int ret = -1;
    if (d & 33554432) ret = 1;
    if (d & 67108864) ret = 2;
    if (c & 1) ret = 3;
    if (c & 524288) ret = 41;
    if (c & 1048576) ret = 42;

    return ret;
  } 
#endif

  //--------------------------------------------------------------------------------
  // Highest SSE level supported by the CPU: 1, 2, 3 or 41 or 42.
  // Note that the asm routines are written for gcc only so far, so we turn them 
  // off for all platforms except darwin86. Also, they won't work properly on 64 bits
  // platforms for now. 
  //--------------------------------------------------------------------------------
#ifdef NTA_PLATFORM_darwin86
  static const int SSE_LEVEL = checkSSE();
#else
  static const int SSE_LEVEL = -1;
#endif

  //--------------------------------------------------------------------------------
  // TESTS
  //
  // TODO: nearly zero for positive numbers
  // TODO: is C++ trying to use that for all types??
  //--------------------------------------------------------------------------------
  template <typename It>
  inline bool
  nearlyZeroRange(It begin, It end,
                  const typename std::iterator_traits<It>::value_type epsilon =nta::Epsilon)
  {
    {
      NTA_ASSERT(begin <= end)
        << "nearlyZeroRange: Invalid input range";
    }

    while (begin != end)
      if (!nearlyZero(*begin++, epsilon))
        return false;
    return true;
  }

  //--------------------------------------------------------------------------------
  template <typename It1, typename It2>
  inline bool
  nearlyEqualRange(It1 begin1, It1 end1, It2 begin2, It2 end2,
                   const typename std::iterator_traits<It1>::value_type epsilon =nta::Epsilon)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "nearlyZeroRange: Invalid first input range";
      NTA_ASSERT(begin2 <= end2)
        << "nearlyZeroRange: Invalid second input range";
      NTA_ASSERT(end1 - begin1 <= end2 - begin2)
        << "nearlyZeroRange: Incompatible ranges";
    }

    while (begin1 != end1)
      if (!nearlyEqual(*begin1++, *begin2++, epsilon))
        return false;
    return true;
  }

  //--------------------------------------------------------------------------------
  template <typename Container1, typename Container2>
  inline bool
  nearlyEqualVector(const Container1& c1, const Container2& c2,
                    const typename Container1::value_type& epsilon =nta::Epsilon)
  {
    typedef typename Container1::value_type T1;
    typedef typename Container2::value_type T2;

    if (c1.size() != c2.size())
      return false;

    return nearlyEqualRange(c1.begin(), c1.end(), c2.begin(), c2.end());
  }

  //--------------------------------------------------------------------------------
  // IS ZERO
  //--------------------------------------------------------------------------------
  template <typename T>
  inline bool is_zero(const T& x)
  {
    return x == 0;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline bool is_zero(const std::pair<T1,T2>& x)
  {
    return x.first == 0 && x.second == 0;
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline bool is_zero(const std::vector<T>& x)
  {
    for (size_t i = 0; i != x.size(); ++i)
      if (!is_zero(x[i]))
        return false;
    return true;
  }

  //--------------------------------------------------------------------------------
  // DENSE isZero
  //--------------------------------------------------------------------------------
  /**
   * Scans a binary 0/1 vector to decide whether it is uniformly zero, 
   * or if it contains non-zeros (4X faster than C++ loop).
   *
   * If vector x is not aligned on a 16 bytes boundary, the function
   * reverts to slow C++. This can happen when using it with slices of numpy
   * arrays.
   *
   * TODO: find 16 bytes aligned block that can be sent to SSE.
   * TODO: support other platforms than just darwin86 for the fast path.
   * TODO: can we go faster if working on ints rather than floats?
   */
  template <typename InputIterator>
  inline bool isZero_01(InputIterator x, InputIterator x_end)
  {
    {
      NTA_ASSERT(x <= x_end);
    }

    // On win32, the asm syntax is not correct.
#ifdef NTA_PLATFORM_darwin86

    // This test can be moved to compile time using a template with an int
    // parameter, and partial specializations that will match the static
    // const int SSE_LEVEL. 
    if (SSE_LEVEL >= 41) { // ptest is a SSE 4.1 instruction

      // n is the total number of floats to process.
      // n1 is the number of floats we can process in parallel using SSE.
      // If x is not aligned on a 4 bytes boundary, we eschew all asm. 
      int result = 0;
      int n = (int)(x_end - x);
      int n1 = 0;
      if (((long)x) % 16 == 0)
        n1 = 8 * (n / 8); // we are going to process 2x4 floats at a time
    
      if (n1 > 0) {

        asm volatile(
                     "pusha\n\t" // save all registers

                     // fill xmm4 with all 1's,
                     // our mask to detect if there are on bits
                     // in the vector or not
                     "subl $16, %%esp\n\t" // allocate 4 floats on the stack
                     "movl $0xffffffff, (%%esp)\n\t" // copy mask 4 times,
                     "movl $0xffffffff, 4(%%esp)\n\t" // then move 16 bytes at once
                     "movl $0xffffffff, 8(%%esp)\n\t" // using movaps
                     "movl $0xffffffff, 12(%%esp)\n\t"
                     "movaps (%%esp), %%xmm4\n\t"
                     "addl $16, %%esp\n\t" // deallocate 4 floats on the stack

                     "0:\n\t"
                     // esi and edi point to the same x, but staggered, so 
                     // that we can load 2x4 bytes into xmm0 and xmm1
                     "movaps (%%edi), %%xmm0\n\t" // move 4 floats from x
                     "movaps (%%esi), %%xmm1\n\t" // move another 4 floats from same x
                     "ptest %%xmm4, %%xmm0\n\t"   // ptest first 4 floats, in xmm0
                     "jne 1f\n\t" // jump if ZF = 0, some bit is not zero
                     "ptest %%xmm4, %%xmm1\n\t"   // ptest second 4 floats, in xmm1
                     "jne 1f\n\t" // jump if ZF = 0, some bit is not zero
                   
                     "addl $32, %%edi\n\t"  // jump over 4 floats
                     "addl $32, %%esi\n\t"  // and another 4 floats here
                     "subl $8, %%ecx\n\t" // processed 8 floats
                     "ja 0b\n\t"
                   
                     "movl $0, %0\n\t" // didn't find anything, result = 0 (int)
                     "jmp 2f\n\t" // exit
                   
                     "1:\n\t" // found something
                     "movl $0x1, %0\n\t" // result = 1 (int)
                   
                     "2:\n\t" // exit
                     "popa\n\t" // restore all registers
                   
                     : "=m" (result), "=D" (x)
                     : "D" (x), "S" (x + 4), "c" (n1)
                     :
                     );
      
        if (result == 1)
          return false;
      }
      
      // Complete computation by iterating over "stragglers" one by one.
      for (int i = n1; i != n; ++i)
        if (*(x+i) > 0)
          return false;
      return true;
    
    } else {
    
      for (; x != x_end; ++x)
        if (*x > 0)
          return false;
      return true;
    }
#else
    for (; x != x_end; ++x)
      if (*x > 0)
        return false;
    return true;
#endif
  }

  //--------------------------------------------------------------------------------
  /**
   * 10X faster than function just above.
   */
  inline bool 
  is_zero_01(const ByteVector& x, size_t begin, size_t end)
  {
    const Byte* x_beg = &x[begin];
    const Byte* x_end = &x[end];

    // On win32, the asm syntax is not correct.
#ifdef NTA_PLATFORM_darwin86

    // This test can be moved to compile time using a template with an int
    // parameter, and partial specializations that will match the static
    // const int SSE_LEVEL. 
    if (SSE_LEVEL >= 41) { // ptest is a SSE 4.1 instruction

      // n is the total number of floats to process.
      // n1 is the number of floats we can process in parallel using SSE.
      // If x is not aligned on a 4 bytes boundary, we eschew all asm. 
      int result = 0;
      int n = (int)(x_end - x_beg);
      int n1 = 0;
      if (((long)x_beg) % 16 == 0)
        n1 = 32 * (n / 32); // we are going to process 32 bytes at a time
    
      if (n1 > 0) {

        asm volatile(
                     "pusha\n\t" // save all registers

                     // fill xmm4 with all 1's,
                     // our mask to detect if there are on bits
                     // in the vector or not
                     "subl $16, %%esp\n\t" // allocate 4 floats on the stack
                     "movl $0xffffffff, (%%esp)\n\t" // copy mask 4 times,
                     "movl $0xffffffff, 4(%%esp)\n\t" // then move 16 bytes at once
                     "movl $0xffffffff, 8(%%esp)\n\t" // using movaps
                     "movl $0xffffffff, 12(%%esp)\n\t"
                     "movaps (%%esp), %%xmm4\n\t"
                     "addl $16, %%esp\n\t" // deallocate 4 floats on the stack

                     "0:\n\t"
                     // esi and edi point to the same x, but staggered, so 
                     // that we can load 2x4 bytes into xmm0 and xmm1
                     "movaps (%%edi), %%xmm0\n\t" // move 4 floats from x
                     "movaps (%%esi), %%xmm1\n\t" // move another 4 floats from same x
                     "ptest %%xmm4, %%xmm0\n\t"   // ptest first 4 floats, in xmm0
                     "jne 1f\n\t" // jump if ZF = 0, some bit is not zero
                     "ptest %%xmm4, %%xmm1\n\t"   // ptest second 4 floats, in xmm1
                     "jne 1f\n\t" // jump if ZF = 0, some bit is not zero
                   
                     "addl $32, %%edi\n\t"  // jump 32 bytes (16 in xmm0 + 16 in xmm1)
                     "addl $32, %%esi\n\t"  // and another 32 bytes
                     "subl $32, %%ecx\n\t" // processed 32 bytes
                     "ja 0b\n\t"
                   
                     "movl $0, %0\n\t" // didn't find anything, result = 0 (int)
                     "jmp 2f\n\t" // exit
                   
                     "1:\n\t" // found something
                     "movl $0x1, %0\n\t" // result = 1 (int)
                   
                     "2:\n\t" // exit
                     "popa\n\t" // restore all registers
                   
                     : "=m" (result), "=D" (x_beg)
                     : "D" (x_beg), "S" (x_beg + 16), "c" (n1)
                     :
                     );
      
        if (result == 1)
          return false;
      }
      
      // Complete computation by iterating over "stragglers" one by one.
      for (int i = n1; i != n; ++i)
        if (*(x_beg+i) > 0)
          return false;
      return true;
    
    } else {
    
      for (; x_beg != x_end; ++x_beg)
        if (*x_beg > 0)
          return false;
      return true;
    }
#else
    for (; x_beg != x_end; ++x_beg)
      if (*x_beg > 0)
        return false;
    return true;
#endif
  }

  //--------------------------------------------------------------------------------
  template <typename InIter>
  inline bool
  positive_less_than(InIter begin, InIter end,
                     const typename std::iterator_traits<InIter>::value_type threshold)
  {
    {
      NTA_ASSERT(begin <= end)
        << "positive_less_than: Invalid input range";
    }

    for (; begin != end; ++begin)
      if (*begin > threshold)
        return false;
    return true;
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void print_bits(const T& x)
  {
    for (int i = sizeof(T) - 1; 0 <= i; --i) {
      unsigned char* b = (unsigned char*)(&x) + i;
      for (int j = 7; 0 <= j; --j)
        std::cout << ((*b & (1 << j)) / (1 << j));
      std::cout << ' ';
    }
  }
  
  //--------------------------------------------------------------------------------
  // N BYTES
  //--------------------------------------------------------------------------------
  /**
   * For primitive types.
   */
  template <typename T>
  inline size_t n_bytes(const T&)
  {
    return sizeof(T);
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline size_t n_bytes(const std::pair<T1,T2>& p)
  {
    size_t n = n_bytes(p.first) + n_bytes(p.second);
    return n;
  }

  //--------------------------------------------------------------------------------
  /**
   * For more bytes for alignment on x86 with darwin: darwin86 always allocates on 
   * 16 bytes boundaries, so the three pointers in the STL vectors (of 32 bits each
   * in -m32), become: 3 * 4 + 4 = 16 bytes. The capacity similarly needs to be 
   * adjusted for aligment. On other platforms, the alignment might be different.
   *
   * NOTE/WARNING: this is really "accurate" only on darwin86. And even, it's probably
   * only approximate.
   */
  template <typename T>
  inline size_t n_bytes(const std::vector<T>& a, size_t alignment =16) 
  {
    size_t n1 = a.capacity() * sizeof(T);
    if (n1 % alignment != 0)
      n1 = alignment * (n1 / alignment + 1);

    size_t n2 = sizeof(std::vector<T>);
    if (n2 % alignment != 0)
      n2 = alignment * (n2 / alignment + 1);

    return n1 + n2;
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline size_t n_bytes(const std::vector<std::vector<T> >& a, size_t alignment =16)
  {
    size_t n = sizeof(std::vector<std::vector<T> >);
    if (n % alignment != 0)
      n = alignment * (n / alignment + 1);

    for (size_t i = 0; i != a.size(); ++i)
      n += n_bytes(a[i]);

    return n;
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline float load_factor(const std::vector<T>& x)
  {
    return (float) x.size() / (float) x.capacity();
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void adjust_load_factor(std::vector<T>& x, float target)
  {
    NTA_ASSERT(0.0 <= target && target <= 1.0);

    size_t new_capacity = (size_t)((float)x.size() / target);

    std::vector<T> y;
    y.reserve(new_capacity);
    y.resize(x.size());
    std::copy(x.begin(), x.end(), y.begin());
    x.swap(y);
  }

  //--------------------------------------------------------------------------------
  // VARIOUS
  //--------------------------------------------------------------------------------
  inline std::string operator+(const std::string& str, size_t idx)
  {
    std::stringstream buff;
    buff << str << idx;
    return buff.str();
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void append(const std::vector<T>& a, std::vector<T>& b)
  {
    b.insert(b.end(), a.begin(), a.end());
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline std::vector<T>& operator+=(std::vector<T>& b, const std::vector<T>& a)
  {
    append(a, b);
    return b;
  }
  
  //--------------------------------------------------------------------------------
  template <typename T>
  inline void append(const std::set<T>& a, std::set<T>& b)
  {
    b.insert(a.begin(), a.end());
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline std::set<T>& operator+=(std::set<T>& b, const std::set<T>& a)
  {
    append(a, b);
    return b;
  }

  //--------------------------------------------------------------------------------
  // map insert or increment
  template <typename T1, typename T2>
  inline void increment(std::map<T1,T2>& m, const T1& key, const T2& init =1)
  {
    typename std::map<T1,T2>::iterator it = m.find(key);
    if (it != m.end())
      ++ it->second;
    else
      m[key] = init;
  }

  //--------------------------------------------------------------------------------
  template <typename K, typename V>
  inline bool is_in(const K& key, const std::map<K,V>& m)
  {
    return m.find(key) != m.end();
  }

  //--------------------------------------------------------------------------------
  // Deriving from std::map to add frequently used functionality
  template <typename K, typename V, typename C =std::less<K>, 
            typename A =std::allocator<std::pair<const K, V> > >
  struct dict : public std::map<K,V,C,A>
  {
    inline bool has_key(const K& key) const 
    {
      return is_in(key, *this);
    }
    
    // Often useful for histograms, where V is an integral type
    inline void increment(const K& key, const V& init =1)
    {
      nta::increment(*this, key, init);
    }

    // Inserts once in the map, or return false if already inserted
    // (saves having to write find(...) == this->end())
    inline bool insert_once(const K& key, const V& v)
    {
      if (has_key(key))
        return false;
      else
        this->insert(std::make_pair(key, v));
      return true;
    }

    /*
    // Returns an existing value for the key, if it is in the dict already,
    // or creates one and returns it. (operator[] on std::map does that?)
    inline V& operator(const K& key) 
    { 
      iterator it = this->find(key);
      if (key == end) {
        (*this)[key] = V(); 
        return (*this)[key]; 
      } else 
        return *it;
    }
    */
  };

  //--------------------------------------------------------------------------------
  // INIT LIST
  //--------------------------------------------------------------------------------
  template <typename T>
  struct vector_init_list
  {
    std::vector<T>& v;
    
    inline vector_init_list(std::vector<T>& v_ref) : v(v_ref) {}
    inline vector_init_list(const vector_init_list& o) : v(o.v) {}

    inline vector_init_list& operator=(const vector_init_list& o) 
    { v(o.v); return *this; }

    template <typename T2>
    inline vector_init_list<T>& operator,(const T2& x)
    {
      v.push_back((T)x);
      return *this;
    }
  };
  
  //--------------------------------------------------------------------------------
  template <typename T, typename T2>
  inline vector_init_list<T> operator+=(std::vector<T>& v, const T2& x)
  {
    v.push_back((T)x);
    return vector_init_list<T>(v);
  }

  //--------------------------------------------------------------------------------
  // TODO: merge with preceding by changing parametrization?
  //--------------------------------------------------------------------------------
  template <typename T>
  struct set_init_list
  {
    std::set<T>& v;
    
    inline set_init_list(std::set<T>& v_ref) : v(v_ref) {}
    inline set_init_list(const set_init_list& o) : v(o.v) {}

    inline set_init_list& operator=(const set_init_list& o) 
    { v(o.v); return *this; }

    template <typename T2>
    inline set_init_list<T>& operator,(const T2& x)
    {
      v.insert((T)x);
      return *this;
    }
  };
  
  //--------------------------------------------------------------------------------
  template <typename T, typename T2>
  inline set_init_list<T> operator+=(std::set<T>& v, const T2& x)
  {
    v.insert((T)x);
    return set_init_list<T>(v);
  }

  //--------------------------------------------------------------------------------
  // FIND IN VECTOR
  //--------------------------------------------------------------------------------
  // T1 and T2 to get around constness with pointers
  template <typename T1, typename T2>
  inline int find_index(const T1& x, const std::vector<T2>& v)
  {
    for (size_t i = 0; i != v.size(); ++i)
      if (v[i] == x)
        return (int) i;
    return -1;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline int find_index(const T1& x, const std::vector<std::pair<T1,T2> >& v)
  {
    for (size_t i = 0; i != v.size(); ++i)
      if (v[i].first == x)
        return (int) i;
    return -1;
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline bool not_in(const T& x, const std::vector<T>& v)
  {
    return std::find(v.begin(), v.end(), x) == v.end();
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline bool not_in(const T1& x, const std::vector<std::pair<T1,T2> >& v)
  {
    typename std::vector<std::pair<T1,T2> >::const_iterator it;
    for (it = v.begin(); it != v.end(); ++it)
      if (it->first == x)
        return false;
    return true;
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline bool not_in(const T& x, const std::set<T>& s)
  {
    return s.find(x) == s.end();
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline bool is_in(const T& x, const std::vector<T>& v)
  {
    return ! not_in(x, v);
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline bool is_in(const T1& x, const std::vector<std::pair<T1,T2> >& v)
  {
    return ! not_in(x, v);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline bool is_in(const T& x, const std::set<T>& s)
  {
    return ! not_in(x, s);
  }

  //--------------------------------------------------------------------------------
  template <typename It>
  inline bool is_sorted(It begin, It end, bool ascending =true, bool unique =true)
  {
    for (It prev = begin, it = ++begin; it < end; ++it, ++prev)

      if (ascending) {
        if (unique) {
          if (*prev >= *it) 
            return false;
        } else {
          if (*prev > *it) 
            return false;
        }
      } else {
        if (unique) {
          if (*prev <= *it)
            return false;
        } else {
          if (*prev < *it)
            return false;
        }
      }

    return true;
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline bool is_sorted(const std::vector<T>& x, bool ascending =true, bool unique =true)
  {
    return is_sorted(x.begin(), x.end(), ascending, unique);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline bool operator==(const std::vector<T>& a, const std::vector<T>& b)
  {
    NTA_ASSERT(a.size() == b.size());
    if (a.size() != b.size())
      return false;
    for (size_t i = 0; i != a.size(); ++i)
      if (a[i] != b[i])
        return false;
    return true;
  }
  
  //--------------------------------------------------------------------------------
  template <typename T>
  inline bool operator!=(const std::vector<T>& a, const std::vector<T>& b)
  {
    return !(a == b);
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline bool operator==(const std::map<T1,T2>& a, const std::map<T1,T2>& b)
  {
    typename std::map<T1,T2>::const_iterator ita = a.begin(), itb = b.begin();
    for (; ita != a.end(); ++ita, ++itb)
      if (ita->first != itb->first || ita->second != itb->second)
        return false;
    return true;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline bool operator!=(const std::map<T1,T2>& a, const std::map<T1,T2>& b)
  {
    return !(a == b);
  }

  //--------------------------------------------------------------------------------
  /**
   * Proxy for an insert iterator that allows inserting at the second element
   * when iterating over a container of pairs.
   */
  template <typename Iterator>
  struct inserter_second
  {
    typedef typename std::iterator_traits<Iterator>::value_type pair_type;
    typedef typename pair_type::second_type second_type;
    typedef second_type value_type;

    Iterator it;

    inline inserter_second(Iterator _it) : it(_it) {}
    inline second_type& operator*() { return it->second; }
    inline void operator++() { ++it; }
  };

  template <typename Iterator>
  inserter_second<Iterator> insert_2nd(Iterator it)
  {
    return inserter_second<Iterator>(it);
  }

  //--------------------------------------------------------------------------------
  /**
   * Proxy for an insert iterator that allows inserting at the second element when
   * iterating over a container of pairs, while setting the first element to the 
   * current index value (watch out if iterator passed to constructor is not 
   * pointing to the beginning of the container!)
   */
  template <typename Iterator>
  struct inserter_second_incrementer_first
  {
    typedef typename std::iterator_traits<Iterator>::value_type pair_type;
    typedef typename pair_type::second_type second_type;
    typedef second_type value_type;

    Iterator it;
    size_t i;

    inline inserter_second_incrementer_first(Iterator _it) 
      : it(_it), i(0) {}
    inline second_type& operator*() { return it->second; }
    inline void operator++() { it->first = i++; ++it; }
  };

  template <typename Iterator>
  inserter_second_incrementer_first<Iterator> insert_2nd_inc(Iterator it)
  {
    return inserter_second_incrementer_first<Iterator>(it);
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline T2 dot(const std::vector<T1>& x, const Buffer<T2>& y)
  {
    size_t n1 = x.size(), n2 = y.nnz, i1 = 0, i2 = 0;
    T2 s = 0;
    
    while (i1 != n1 && i2 != n2) 
      if (x[i1] < y[i2]) {
        ++i1;
      } else if (y[i2] < x[i1]) {
        ++i2;
      } else {
        ++s;
        ++i1; ++i2;
      }

    return s;
  }

  //--------------------------------------------------------------------------------
  inline float dot(const float* x, const float* x_end, const float* y)
  {
    float result = 0;
#ifdef NTA_PLATFORM_darwin86
    vDSP_dotpr(x, 1, y, 1, &result, (x_end - x));
#else
    for (; x != x_end; ++x, ++y)
      result += *x * *y;
#endif
    return result;
  }
  
  //--------------------------------------------------------------------------------
  // copy
  //--------------------------------------------------------------------------------
  template <typename It1, typename It2>
  inline void copy(It1 begin, It1 end, It2 out_begin, It2 out_end)
  {
    std::copy(begin, end, out_begin);
  }

  //--------------------------------------------------------------------------------
  /**
   * Copies a whole container into another.
   *
   * Does not allocate memory for b: b needs to have enough room for
   * a.size() elements.
   *
   * @param a the source container
   * @param b the destination container
   */
  template <typename T1, typename T2>
  inline void copy(const T1& a, T2& b)
  {
    b.resize(a.size());
    copy(a.begin(), a.end(), b.begin(), b.end());
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline void copy(const std::vector<T1>& a, size_t n, std::vector<T2>& b, size_t o =0)
  {
    NTA_ASSERT(o + n <= b.size());
    std::copy(a.begin(), a.begin() + n, b.begin() + o);
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline void copy(const std::vector<T1>& a, size_t i, size_t j, std::vector<T2>& b)
  {
    std::copy(a.begin() + i, a.begin() + j, b.begin() + i);
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline void copy(const std::vector<T1>& a, std::vector<T2>& b, size_t offset)
  {
    NTA_ASSERT(offset + a.size() <= b.size());
    std::copy(a.begin(), a.end(), b.begin() + offset);
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename T>
  inline void copy_indices(const SparseVector<I,T>& x, Buffer<I>& y)
  {
    NTA_ASSERT(x.nnz <= y.size());

    for (size_t i = 0; i != x.nnz; ++i)
      y[i] = x[i].first;
    y.nnz = x.nnz;
  }
  
  //--------------------------------------------------------------------------------
  // TO DENSE
  //--------------------------------------------------------------------------------
  template <typename It1, typename It2>
  inline void to_dense_01(It1 ind, It1 ind_end, It2 dense, It2 dense_end)
  {
    {
      NTA_ASSERT(ind <= ind_end)
        << "to_dense: Mismatched iterators";
      NTA_ASSERT(dense <= dense_end)
        << "to_dense: Mismatched iterators";
      NTA_ASSERT(ind_end - ind <= dense_end - dense)
        << "to_dense: Not enough memory";
    }

    typedef typename std::iterator_traits<It2>::value_type value_type;

    // TODO: make faster with single pass?
    // (but if's for all the elements might be slower)
    std::fill(dense, dense_end, (value_type) 0);
    
    for (; ind != ind_end; ++ind)
      *(dense + *ind) = (value_type) 1;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline void to_dense_01(const std::vector<T1>& sparse, std::vector<T2>& dense)
  {
    to_dense_01(sparse.begin(), sparse.end(), dense.begin(), dense.end());
  }

  //--------------------------------------------------------------------------------
  template <typename T, typename OutIt>
  inline void to_dense_01(const Buffer<T>& buffer, OutIt y, OutIt y_end)
  {
    typedef typename std::iterator_traits<OutIt>::value_type value_type;

    std::fill(y, y_end, (value_type) 0);

    for (size_t i = 0; i != buffer.nnz; ++i)
      y[buffer[i]] = (value_type) 1;
  }

  //--------------------------------------------------------------------------------
  template <typename It, typename T>
  inline void to_dense_01(It begin, It  end, std::vector<T>& dense)
  {
    to_dense_01(begin, end, dense.begin(), dense.end());
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename T, typename OutIt>
  inline void to_dense_1st_01(const SparseVector<I,T>& x, OutIt y, OutIt y_end)
  {
    typedef typename std::iterator_traits<OutIt>::value_type value_type;
    
    std::fill(y, y_end, (value_type) 0);

    for (size_t i = 0; i != x.nnz; ++i)
      y[x[i].first] = (value_type) 1;
  }

  //--------------------------------------------------------------------------------
  template <typename T, typename OutIt>
  inline void 
  to_dense_01(size_t n, const std::vector<T>& buffer, OutIt y, OutIt y_end)
  {
    NTA_ASSERT(n <= buffer.size());

    typedef typename std::iterator_traits<OutIt>::value_type value_type;

    std::fill(y, y_end, (value_type) 0);
    
    const T* b = &buffer[0], *b_end = b + n;
    for (; b != b_end; ++b) {
      NTA_ASSERT(*b < (size_t)(y_end - y));
      y[*b] = (value_type) 1;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Converts a sparse range described with indices and values to a dense
   * range.
   */
  template <typename It1, typename It2, typename It3>
  inline void to_dense(It1 ind, It1 ind_end, It2 nz, It2 nz_end,
                       It3 dense, It3 dense_end)
  {
    {
      NTA_ASSERT(ind <= ind_end)
        << "to_dense: Mismatched ind iterators";
      NTA_ASSERT(dense <= dense_end)
        << "to_dense: Mismatched dense iterators";
      NTA_ASSERT(ind_end - ind <= dense_end - dense)
        << "to_dense: Not enough memory";
      NTA_ASSERT(nz_end - nz == ind_end - ind)
        << "to_dense: Mismatched ind and nz ranges";
    }

    typedef typename std::iterator_traits<It3>::value_type value_type;

    std::fill(dense, dense + (ind_end - ind), (value_type) 0);

    for (; ind != ind_end; ++ind, ++nz)
      *(dense + *ind) = *nz;
  }

  //--------------------------------------------------------------------------------
  /**
   * Needs non-zero indices to be sorted!
   */
  template <typename It>
  inline void in_place_sparse_to_dense_01(int n, It begin, It end)
  {
    for (int i = n - 1; i >= 0; --i) {
      int p = (int) *(begin + i);
      std::fill(begin + p, end, 0);
      *(begin + p) = 1;
      end = begin + p;
    }

    std::fill(begin, end, 0);
  }

  //--------------------------------------------------------------------------------
  /**
   * Pb with size of the vectors?
   */
  template <typename T>
  inline void in_place_sparse_to_dense_01(int n, std::vector<T>& x)
  {
    in_place_sparse_to_dense_01(n, x.begin(), x.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * Converts a sparse range stored in a dense vector into an (index,value)
   * representation.
   *
   * @param begin
   * @param end
   * @param ind
   * @param nz
   * @param eps
   */
  template <typename It1, typename It2, typename It3>
  inline void
  from_dense(It1 begin, It1 end, It2 ind, It3 nz,
             typename std::iterator_traits<It1>::value_type eps = nta::Epsilon)
  {
    {
      NTA_ASSERT(begin <= end)
        << "from_dense: Mismatched dense iterators";
    }

    typedef size_t size_type;
    typedef typename std::iterator_traits<It1>::value_type value_type;

    Abs<value_type> abs_f;

    for (It1 it = begin; it != end; ++it) {
      value_type val = *it;
      if (abs_f(val) > eps) {
        *ind = (size_type) (it - begin);
        *nz = val;
        ++ind; ++nz;
      }
    }
  }

  //--------------------------------------------------------------------------------
  template <typename It, typename T>
  inline void from_dense(It begin, It end, Buffer<T>& buffer)
  {
    NTA_ASSERT((size_t)(end - begin) <= buffer.size());

    typename Buffer<T>::iterator it2 = buffer.begin();

    for (It it = begin; it != end; ++it) 
      if (*it != 0) {
        *it2++ = (T)(it - begin);
      }

    buffer.nnz = it2 - buffer.begin();
  }

  //--------------------------------------------------------------------------------
  // erase from vector
  //--------------------------------------------------------------------------------
  /**
   * Erases a value from a vector.
   *
   * The STL process to really remove a value from a vector is tricky.
   *
   * @param v the vector
   * @param val the value to remove
   */
  template <typename T>
  inline void remove(const T& del, std::vector<T>& v)
  {
    v.erase(std::remove(v.begin(), v.end(), del), v.end());
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void remove(const std::vector<T>& del, std::vector<T>& b)
  {
    for (size_t i = 0; i != del.size(); ++i)
      remove(del[i], b);
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline void remove_for_pairs(const T1& key, std::vector<std::pair<T1,T2> >& v)
  {
    typename std::vector<std::pair<T1,T2> >::const_iterator it;
    for (it = v.begin(); it != v.end() && it->first != key; ++it);
    remove(*it, v);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void remove_from_end(const T& elt, std::vector<T>& a)
  {
    for (int i = a.size() - 1; i >= 0; --i) {
      if (a[i] == elt) {
        for (size_t j = i; j < a.size() - 1; ++j)
          a[j] = a[j+1];
        a.resize(a.size() - 1);
        return;
      }
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Given a vector of indices, removes the elements of a at those indices (indices
   * before any removal is carried out), where a is a vector of pairs.
   * 
   * Need to pass in non-empty vector of sorted, unique indices to delete.
   */
  // TODO: remove this? Should be covered just below??
  template <typename I, typename T1, typename T2>
  inline void 
  remove_for_pairs(const std::vector<I>& del, std::vector<std::pair<T1, T2> >& a)
  {
    NTA_ASSERT(std::set<I>(del.begin(),del.end()).size() == del.size());
    
    if (del.empty())
      return;

    size_t old = del[0] + 1, cur = del[0], d = 1;

    while (old < a.size() && d < del.size()) {
      if (old == (size_t) del[d]) {
        ++d; ++old;
      } else if ((size_t) del[d] < old) {
        ++d;
      } else {
        a[cur++] = a[old++];
      }
    }

    while (old < a.size()) 
      a[cur++] = a[old++];

    a.resize(a.size() - del.size());
  }

  //--------------------------------------------------------------------------------
  /**
   * Remove several elements from a vector, the elements to remove being specified 
   * by their index (in del). After this call, a's size is reduced. Requires 
   * default constructor on T to be defined (for resize). O(n).
   */
  template <typename I, typename T>
  inline void 
  remove_at(const std::vector<I>& del, std::vector<T>& a)
  {
    NTA_ASSERT(std::set<I>(del.begin(),del.end()).size() == del.size());
    
    if (del.empty())
      return;
    
    size_t old = del[0] + 1, cur = del[0], d = 1;
    
    while (old < a.size() && d < del.size()) {
      if (old == (size_t) del[d]) {
        ++d; ++old;
      } else if ((size_t) del[d] < old) {
        ++d;
      } else {
        a[cur++] = a[old++];
      }
    }
    
    while (old < a.size()) 
      a[cur++] = a[old++];
    
    a.resize(a.size() - del.size());
  }
  
  //--------------------------------------------------------------------------------
  /**
   * Finds index of elt in ref, and removes corresponding element of a.
   */
  template <typename T1, typename T2>
  inline void remove(const T2& elt, std::vector<T1>& a, const std::vector<T2>& ref)
  {
    a.erase(a.begin() + find_index(elt, ref));
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void remove(const std::vector<T>& del, std::set<T>& a)
  {
    for (size_t i = 0; i != del.size(); ++i)
      a.erase(del[i]);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void remove(const std::set<T>& y, std::vector<T>& x)
  {
    std::vector<T> del;

    for (size_t i = 0; i != x.size(); ++i)
      if (y.find(x[i]) != y.end()) {
        NTA_ASSERT(not_in(x[i], del));
        del.push_back(x[i]);
      }

    nta::remove(del, x);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline std::set<T>& operator-=(std::set<T>& a, const std::vector<T>& b)
  {
    remove(b, a);
    return a;
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline std::vector<T>& operator-=(std::vector<T>& a, const std::vector<T>& b)
  {
    remove(b, a);
    return a;
  }

  //--------------------------------------------------------------------------------
  // DIFFERENCES
  //--------------------------------------------------------------------------------
  /**
   * Returns a vector that contains the indices of the positions where x and y 
   * have different values.
   */
  template <typename T>
  inline void 
  find_all_differences(const std::vector<T>& x, const std::vector<T>& y,
                       std::vector<size_t>& diffs)
  {
    NTA_ASSERT(x.size() == y.size());
    diffs.clear();
    for (size_t i = 0; i != x.size(); ++i)
      if (x[i] != y[i])
        diffs.push_back(i);
  }

  //--------------------------------------------------------------------------------
  // fill
  //--------------------------------------------------------------------------------
  /**
   * Fills a container with the given value.
   *
   * @param a
   * @param val
   */
  template <typename T>
  inline void fill(T& a, const typename T::value_type& val)
  {
    typename T::iterator i = a.begin(), e = a.end();

    for (; i != e; ++i)
      *i = val;
  }

  //--------------------------------------------------------------------------------
  /**
   * Zeroes out a range.
   *
   * @param begin
   * @param end
   */
  template <typename It>
  inline void zero(It begin, It end)
  {
    {
      NTA_ASSERT(begin <= end)
        << "zero: Invalid input range";
    }

    typedef typename std::iterator_traits<It>::value_type T;

    for (; begin != end; ++begin)
      *begin = T(0);
  }

  //--------------------------------------------------------------------------------
  /**
   * Zeroes out a whole container.
   *
   * @param a the container
   */
  template <typename T>
  inline void zero(T& a)
  {
    zero(a.begin(), a.end());
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void set_to_zero(T& a)
  {
    zero(a);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void set_to_zero(std::vector<T>& a, size_t begin, size_t end)
  {
    zero(a.begin() + begin, a.begin() + end);
  }

  //--------------------------------------------------------------------------------
  /**
   * Fills a range with ones.
   *
   * @param begin
   * @param end
   */
  template <typename It>
  inline void ones(It begin, It end)
  {
    {
      NTA_ASSERT(begin <= end)
        << "ones: Invalid input range";
    }

    typedef typename std::iterator_traits<It>::value_type T;

    for (; begin != end; ++begin)
      *begin = T(1);
  }

  //--------------------------------------------------------------------------------
  /**
   * Fills a container with ones.
   *
   * @param a the container
   */
  template <typename T>
  inline void ones(T& a)
  {
    ones(a.begin(), a.end());
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void set_to_one(std::vector<T>& a)
  {
    ones(a);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void set_to_one(std::vector<T>& a, size_t begin, size_t end)
  {
    ones(a.begin() + begin, a.begin() + end);
  }

  //--------------------------------------------------------------------------------
  /**
   * Sets a range to 0, except for a single value at pos, which will be equal to val.
   *
   * @param pos the position of the single non-zero value
   * @param begin
   * @param end
   * @param val the value of the non-zero value in the range
   */
  template <typename It>
  inline void dirac(size_t pos, It begin, It end,
                    typename std::iterator_traits<It>::value_type val =1)
  {
    {
      NTA_ASSERT(begin <= end)
        << "dirac: Invalid input range";

      NTA_ASSERT(0 <= pos && pos < (size_t)(end - begin))
        << "dirac: Invalid position: " << pos
        << " - Should be between 0 and: " << (size_t)(end - begin);
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    std::fill(begin, end, (value_type) 0);
    *(begin + pos) = val;
  }

  //--------------------------------------------------------------------------------
  /**
   * Sets a range to 0, except for a single value at pos, which will be equal to val.
   *
   * @param pos the position of the single non-zero value
   * @param c the container
   * @param val the value of the Dirac
   */
  template <typename C>
  inline void dirac(size_t pos, C& c, typename C::value_type val =1)
  {
    {
      NTA_ASSERT(pos >= 0 && pos < c.size())
        << "dirac: Can't set Dirac at pos: " << pos
        << " when container has size: " << c.size();
    }

    dirac(pos, c.begin(), c.end(), val);
  }

  //--------------------------------------------------------------------------------
  /**
   * Computes the CDF of the given range seen as a discrete PMF.
   *
   * @param begin1 the beginning of the discrete PMF range
   * @param end1 one past the end of the discrete PMF range
   * @param begin2 the beginning of the CDF range
   */
  template <typename It1, typename It2>
  inline void cumulative(It1 begin1, It1 end1, It2 begin2, It2 end2)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "cumulative: Invalid input range";
      NTA_ASSERT(begin2 <= end2)
        << "cumulative: Invalid output range";
      NTA_ASSERT(end1 - begin1 == end2 - begin2)
        << "cumulative: Incompatible sizes";
    }

    typedef typename std::iterator_traits<It2>::value_type value_type;

    It2 prev = begin2;
    *begin2++ = (value_type) *begin1++;
    for (; begin1 < end1; ++begin1, ++begin2, ++prev)
      *begin2 = *prev + (value_type) *begin1;
  }

  //--------------------------------------------------------------------------------
  /**
   * Computes the CDF of a discrete PMF.
   *
   * @param pmf the PMF
   * @param cdf the CDF
   */
  template <typename C1, typename C2>
  inline void cumulative(const C1& pmf, C2& cdf)
  {
    cumulative(pmf.begin(), pmf.end(), cdf.begin(), cdf.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * Finds percentiles.
   */
  template <typename It1, typename It2>
  inline void percentiles(size_t n_percentiles,
                          It1 begin1, It1 end1,
                          It2 begin2, It2 end2,
                          bool alreadyNormalized =false)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "percentiles: Invalid input range";
      NTA_ASSERT(begin2 <= end2)
        << "percentiles: Invalid output range";
      NTA_ASSERT(end1 - begin1 == end2 - begin2)
        << "percentiles: Mismatched ranges";
    }

    typedef typename std::iterator_traits<It1>::value_type value_type;
    typedef typename std::iterator_traits<It2>::value_type size_type;

    value_type n = (value_type) (alreadyNormalized ? 1.0f : 0.0f);

    if (!alreadyNormalized)
      for (It1 it = begin1; it != end1; ++it)
        n += *it;

    value_type increment = n/value_type(n_percentiles);
    value_type sum = (value_type) 0.0f;
    size_type p = (size_type) 0;

    for (value_type v = increment; v < n; v += increment) {
      for (; sum < v; ++p)
        sum += *begin1++;
      *begin2++ = p;
    }
  }

  //--------------------------------------------------------------------------------
  template <typename C1, typename C2>
  inline void percentiles(size_t n_percentiles, const C1& pmf, C2& pcts)
  {
    percentiles(n_percentiles, pmf.begin(), pmf.end(), pcts.begin());
  }

  //--------------------------------------------------------------------------------
  template <typename It, typename RNG>
  inline void rand_range(It begin, It end,
                         const typename std::iterator_traits<It>::value_type& min_,
                         const typename std::iterator_traits<It>::value_type& max_,
                         RNG& rng)
  {
    {
      NTA_ASSERT(begin <= end)
        << "rand_range: Invalid input range";
      NTA_ASSERT(min_ < max_)
        << "rand_range: Invalid min/max: " << min_ << " " << max_;
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    double range = double(max_ - min_) / double(rng.max() - rng.min());
    for (; begin != end; ++begin)
      *begin = value_type(double(rng()) * range + min_);
  }

  //--------------------------------------------------------------------------------
  /**
   * Initializes a range with random values.
   *
   * @param begin
   * @param end
   * @param min_
   * @param max_
   */
  template <typename It>
  inline void rand_range(It begin, It end,
                         const typename std::iterator_traits<It>::value_type& min_,
                         const typename std::iterator_traits<It>::value_type& max_)
  {
    nta::Random rng;
    rand_range(begin, end, min_, max_, rng);
  }

  //--------------------------------------------------------------------------------
  template <typename T, typename RNG>
  inline void rand_range(T& a,
                         const typename T::value_type& min,
                         const typename T::value_type& max,
                         RNG& rng)
  {
    rand_range(a.begin(), a.end(), min, max, rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Initializes a container with random values.
   *
   * @param a the container
   * @param min
   * @param max
   */
  template <typename T>
  inline void rand_range(T& a,
                         const typename T::value_type& min,
                         const typename T::value_type& max)
  {
    rand_range(a.begin(), a.end(), min, max);
  }

  //--------------------------------------------------------------------------------
  template <typename T, typename RNG>
  inline void rand_float_range(std::vector<T>& x, size_t start, size_t end, RNG& rng)
  {
    for (size_t i = start; i != end; ++i)
      x[i] = (float) rng.getReal64();
  }

  //--------------------------------------------------------------------------------
  /**
   * Initializes a range with the normal distribution.
   *
   * @param begin
   * @param end
   * @param mean
   * @param stddev
   */
  template <typename It>
  inline void normal_range(It begin, It end,
                           const typename std::iterator_traits<It>::value_type& mean,
                           const typename std::iterator_traits<It>::value_type& stddev)
  {
    {
      NTA_ASSERT(begin <= end)
        << "normal_range: Invalid input range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;
    // implement numerical recipes' method
  }

  //--------------------------------------------------------------------------------
  template <typename It, typename RNG>
  inline void rand_range_01(It begin, It end, double pct, RNG& rng)
  {
    {
      NTA_ASSERT(begin <= end)
        << "rand_range_01: Invalid input range";
      NTA_ASSERT(0 <= pct && pct < 1)
        << "rand_range_01: Invalid threshold: " << pct
        << " - Should be between 0 and 1";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    for (; begin != end; ++begin)
      *begin = (value_type)(double(rng()) / double(rng.max() - rng.min()) > pct);
  }

  //--------------------------------------------------------------------------------
  /**
   * Initializes a range with a random binary vector.
   *
   * @param begin
   * @param end
   * @param pct the percentage of ones
   */
  template <typename It>
  inline void rand_range_01(It begin, It end, double pct =.5)
  {
    nta::Random rng;
    rand_range_01(begin, end, pct, rng);
  }

  //--------------------------------------------------------------------------------
  template <typename T, typename RNG>
  inline void rand_range_01(T& a, double pct, RNG& rng)
  {
    rand_range_01(a.begin(), a.end(), pct, rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Initializes a container with a random binary vector.
   *
   * @param a the container
   * @param pct the percentage of ones
   */
  template <typename T>
  inline void rand_range_01(T& a, double pct =.5)
  {
    nta::Random rng;
    rand_range_01(a.begin(), a.end(), pct, rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Initializes a range with a ramp function.
   *
   * @param begin
   * @param end
   * @param start the start value of the ramp
   * @param step the step of the ramp
   */
  template <typename It, typename T>
  inline void ramp_range(It begin, It end, T start =0, T step =1)
  {
    {
      NTA_ASSERT(begin <= end)
        << "ramp_range: Invalid input range";
    }

    for (; begin != end; ++begin, start += step)
      *begin = start;
  }

  //--------------------------------------------------------------------------------
  /**
   * Initializes a range with a ramp function.
   *
   * @param a the container
   * @param start the start value of the ramp
   * @param step the step of the ramp
   */
  template <typename T>
  inline void ramp_range(T& a,
                         typename T::value_type start =0,
                         typename T::value_type step =1)
  {
    ramp_range(a.begin(), a.end(), start);
  }

  //--------------------------------------------------------------------------------
  /**
   * Fills a range with values taken randomly from another range.
   *
   * @param begin
   * @param end
   * @param enum_begin the values to draw from
   * @param enum_end the values to draw from
   * @param replace whether to draw with or without replacements
   */
  template <typename It1, typename It2, typename RNG>
  inline void rand_enum_range(It1 begin, It1 end, It2 enum_begin, It2 enum_end,
                              bool replace, RNG& rng)
  {
    {
      NTA_ASSERT(begin <= end)
        << "rand_enum_range: Invalid input range";

      NTA_ASSERT(enum_begin <= enum_end)
        << "rand_enum_range: Invalid values range";
    }

    typedef typename std::iterator_traits<It1>::value_type value_type;

    size_t n = (size_t)(enum_end - enum_begin);

    if (replace) {

      for (; begin != end; ++begin)
        *begin = (value_type) *(enum_begin + rng() % n);

    } else {

      std::vector<size_t> ind(n);
      ramp_range(ind);

      for (; begin != end; ++begin) {
        size_t p = rng() % ind.size();
        *begin = (value_type) *(enum_begin + p);
        remove(p, ind);
      }
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Fills a range with values taken randomly from another range.
   *
   * @param begin
   * @param end
   * @param enum_begin the values to draw from
   * @param enum_end the values to draw from
   * @param replace whether to draw with or without replacements
   */
  template <typename It1, typename It2>
  inline void rand_enum_range(It1 begin, It1 end, It2 enum_begin, It2 enum_end,
                              bool replace =false)
  {
    {
      NTA_ASSERT(begin <= end)
        << "rand_enum_range: Invalid input range";
      NTA_ASSERT(enum_begin <= enum_end)
        << "rand_enum_range: Invalid enum range";
    }

    nta::Random rng;
    rand_enum_range(begin, end, enum_begin, enum_end, replace, rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Fills a container with values taken randomly from another container.
   *
   * @param a the container to fill
   * @param b the container of the values to use
   * @param replace whether the draw with replacements or not
   */
  template <typename C1, typename C2>
  inline void rand_enum_range(C1& a, const C2& b, bool replace =false)
  {
    rand_enum_range(a.begin(), a.end(), b.begin(), b.end(), replace);
  }

  //--------------------------------------------------------------------------------
  template <typename C1, typename C2, typename RNG>
  inline void rand_enum_range(C1& a, const C2& b, bool replace, RNG& rng)
  {
    rand_enum_range(a.begin(), a.end(), b.begin(), b.end(), replace, rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Fills a range with a random permutation of a ramp.
   *
   * @param begin
   * @param end
   * @param start the start value of the ramp
   * @param step the step value of the ramp
   */
  template <typename It, typename RNG>
  inline void
  random_perm_interval(It begin, It end,
                       typename std::iterator_traits<It>::value_type start,
                       typename std::iterator_traits<It>::value_type step,
                       RNG& rng)
  {
    {
      NTA_ASSERT(begin <= end)
        << "random_perm_interval 1: Invalid input range";
    }

    ramp_range(begin, end, start, step);
    std::random_shuffle(begin, end, rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Fills a range with a random permutation of a ramp.
   *
   * @param begin
   * @param end
   * @param start the start value of the ramp
   * @param step the step value of the ramp
   */
  template <typename It>
  inline void
  random_perm_interval(It begin, It end,
                       typename std::iterator_traits<It>::value_type start =0,
                       typename std::iterator_traits<It>::value_type step =1)
  {
    {
      NTA_ASSERT(begin <= end)
        << "random_perm_interval 2: Invalid input range";
    }

    nta::Random rng;
    random_perm_interval(begin, end, start, step, rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Fills a container with a random permutation of a ramp.
   *
   * @param c the container to fill
   * @param start the start value of the ramp
   * @param step the step value of the ramp
   */
  template <typename C>
  inline void random_perm_interval(C& c,
                                   typename C::value_type start =0,
                                   typename C::value_type step =1)
  {
    random_perm_interval(c.begin(), c.end(), start, step);
  }

  //--------------------------------------------------------------------------------
  template <typename C, typename RNG>
  inline void random_perm_interval(C& c,
                                   typename C::value_type start,
                                   typename C::value_type step,
                                   RNG& rng)
  {
    random_perm_interval(c.begin(), c.end(), start, step, rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Draws a random sample from a range, without replacements.
   *
   * Currently assumes that the first range is larger than the second.
   *
   * @param begin1
   * @param end1
   * @param begin2
   * @param end2
   */
  template <typename It1, typename It2, typename RNG>
  inline void random_sample(It1 begin1, It1 end1, It2 begin2, It2 end2, RNG& rng)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "random_sample 1: Invalid value range";
      NTA_ASSERT(begin2 <= end2)
        << "random_sample 1: Invalid output range";
    }

    size_t n1 = (size_t) (end1 - begin1);
    std::vector<size_t> perm(n1);
    random_perm_interval(perm, 0, n1, rng);
    for (size_t p = 0; begin2 != end2; ++begin2, ++p)
      *begin2 = *(begin1 + p);
  }

  //--------------------------------------------------------------------------------
  /**
   * Draws a random sample from a range, without replacements.
   *
   * Currently assumes that the first range is larger than the second.
   *
   * @param begin1
   * @param end1
   * @param begin2
   * @param end2
   */
  template <typename It1, typename It2>
  inline void random_sample(It1 begin1, It1 end1, It2 begin2, It2 end2)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "random_sample 2: Invalid value range";
      NTA_ASSERT(begin2 <= end2)
        << "random_sample 2: Invalid output range";
    }

    nta::Random rng;
    random_sample(begin1, end1, begin2, end2, rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Draws a random sample from a container, and uses the values to initialize
   * another container.
   *
   * @param c1 the container to initialize
   * @param c2 the container from which to take the values
   */
  template <typename T1, typename T2>
  inline void random_sample(const std::vector<T1>& c1, std::vector<T2>& c2)
  {
    random_sample(c1.begin(), c1.end(), c2.begin(), c2.end());
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2, typename RNG>
  inline void random_sample(const std::vector<T1>& c1, std::vector<T2>& c2, RNG& rng)
  {
    random_sample(c1.begin(), c1.end(), c2.begin(), c2.end(), rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Initializes a container with elements taken from the specified ramp range,
   * randomly.
   *
   * @param c the container to fill
   * @param size the size of the ramp
   * @param start the first value of the ramp
   * @param step the step of the ramp
   */
  template <typename T, typename RNG>
  inline void random_sample(std::vector<T>& c,
                            size_t size,
                            size_t start,
                            size_t step,
                            RNG& rng)
  {
    ramp_range(c, start, step);
    std::random_shuffle(c.begin(), c.end(), rng);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void random_sample(std::vector<T>& c,
                            size_t size,
                            size_t start =0,
                            size_t step =1)
  {
    nta::Random rng;
    random_sample(c, size, start, step, rng);
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void random_sample(size_t n, std::vector<T>& a)
  {
    NTA_ASSERT(0 < a.size());

    std::vector<size_t> x(n);
    for (size_t i = 0; i != n; ++i)
      x[i] = i;
    std::random_shuffle(x.begin(), x.end());
    std::copy(x.begin(), x.begin() + a.size(), a.begin());
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void random_sample(std::vector<T>& a)
  {
    random_sample(a, a.size());
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void random_sample(const std::set<T>& a, std::vector<T>& b)
  {
    NTA_ASSERT(0 < b.size());

    std::vector<T> aa(a.begin(), a.end());
    std::random_shuffle(aa.begin(), aa.end());
    std::copy(aa.begin(), aa.begin() + b.size(), b.begin());
  }
  
  //--------------------------------------------------------------------------------
  template <typename T>
  inline void random_binary(float proba, std::vector<T>& x)
  {
    size_t threshold = (size_t) (proba * 65535);
    std::fill(x.begin(), x.end(), 0);
    for (size_t i = 0; i != x.size(); ++i)
      x[i] = ((size_t) rand() % 65535 < threshold) ? 1 : 0;
  }

  //--------------------------------------------------------------------------------
  /**
   * Generates a matrix of random (index,value) pairs from [0..ncols], with
   * nnzpc numbers per row, and n columns [generates a constant sparse matrix
   * with constant number of non-zeros per row]. This uses a uniform distribution
   * of the non-zero bits.
   */
  template <typename T1, typename T2>
  inline void 
  random_pair_sample(size_t nrows, size_t ncols, size_t nnzpr, 
                     std::vector<std::pair<T1, T2> >& a, 
                     const T2& init_nz_val,
                     int seed =-1,
                     bool sorted =true)
  {
    {
      NTA_ASSERT(0 < a.size());
      NTA_ASSERT(nnzpr <= ncols);
    }

    a.resize(nrows * nnzpr);

#ifdef NTA_PLATFORM_darwin86
    nta::Random rng(seed == -1 ? arc4random() : seed);
#else
    nta::Random rng(seed == -1 ? rand() : seed);
#endif

    std::vector<size_t> x(ncols); 
    for (size_t i = 0; i != ncols; ++i)
      x[i] = i;
    for (size_t i = 0; i != nrows; ++i) {
      std::random_shuffle(x.begin(), x.end(), rng);
      if (sorted)
        std::sort(x.begin(), x.begin() + nnzpr);
      size_t offset = i*nnzpr;
      for (size_t j = 0; j != nnzpr; ++j)
        a[offset + j] = std::make_pair<T1,T2>(x[j], init_nz_val);
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Generates a matrix of random (index,value) pairs from [0..ncols], with
   * nnzpr numbers per row, and n columns [generates a constant sparse matrix
   * with constant number of non-zeros per row]. This uses a 2D Gaussian distribution
   * for the on bits of each coincidence. That is, each coincidence is seen as a 
   * folded 2D array, and a 2D Gaussian is used to distribute the on bits of each
   * coincidence.
   * 
   * Each row is seen as an image of size (ncols / rf_x) by rf_x.
   * 'sigma' is the parameter of the Gaussian, which is centered at the center of 
   * the image. Uses a symmetric Gaussian, specified only by the location of its
   * max and a single sigma parameter (no Sigma matrix). We use the symmetry of the 
   * 2d gaussian to simplify computations. The conditional distribution obtained 
   * from the 2d gaussian by fixing y is again a gaussian, with parameters than can
   * be easily deduced from the original 2d gaussian.
   */
  template <typename T1, typename T2>
  inline void 
  gaussian_2d_pair_sample(size_t nrows, size_t ncols, size_t nnzpr, size_t rf_x,
                          T2 sigma,
                          std::vector<std::pair<T1, T2> >& a, 
                          const T2& init_nz_val,
                          int seed =-1,
                          bool sorted =true)
  {
    {
      NTA_ASSERT(ncols % rf_x == 0);
      NTA_ASSERT(nnzpr <= ncols);
      NTA_ASSERT(0 < sigma);
    }

    a.resize(nrows * nnzpr);

#ifdef NTA_PLATFORM_darwin86
    nta::Random rng(seed == -1 ? arc4random() : seed);
#else
    nta::Random rng(seed == -1 ? rand() : seed);
#endif

    size_t rf_y = ncols / rf_x;
    T2 c_x = float(rf_x - 1.0) / 2.0, c_y = float(rf_y - 1.0) / 2.0;
    Gaussian2D<float> sg2d(c_x, c_y, sigma*sigma, 0, 0, sigma*sigma);
    std::vector<float> z(ncols);

    // Renormalize because we've lost some mass 
    // with a compact domain of definition.
    float s = 0;
    for (size_t j = 0; j != ncols; ++j)
      s += z[j] = sg2d(j / rf_y, j % rf_y);

    for (size_t j = 0; j != ncols; ++j)
      z[j] /= s;
    //z[j] = 1.0f / (float)(rf_x * rf_y);

    //std::vector<int> counts(ncols, 0);

    // TODO: argsort z so that the bigger bins come first, and it's faster
    // to draw samples in the area where the pdf is higher
    for (size_t i = 0; i != nrows; ++i) {

      std::set<size_t> b;

      while (b.size() < nnzpr) {
        T2 s = z[0], p = T2(rng.getReal64());
        size_t k = 0;
        while (s < p && k < ncols-1)
          s += z[++k];
        //++counts[k];
        b.insert(k);
      }

      size_t offset = i*nnzpr;
      std::set<size_t>::const_iterator it = b.begin();
      for (size_t j = 0; j != nnzpr; ++j, ++it)
        a[offset + j] = std::make_pair<T1,T2>(*it, init_nz_val);
    }
    
    /*
    for (size_t i = 0; i != counts.size(); ++i)
      std::cout << counts[i] << " ";
    std::cout << std::endl;
    */
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void random_shuffle(std::vector<T>& x)
  {
    std::random_shuffle(x.begin(), x.end());
  }

  //--------------------------------------------------------------------------------
  // generate
  //--------------------------------------------------------------------------------
  /**
   * Initializes a range by calling gen() repetitively.
   *
   * @param c the container to initialize
   * @param gen the generator functor
   */
  template <typename Container, typename Generator>
  inline void generate(Container& c, Generator gen)
  {
    typename Container::iterator i = c.begin(), e = c.end();

    for (; i != e; ++i)
      *i = gen();
  }

  //--------------------------------------------------------------------------------
  // concatenate
  //--------------------------------------------------------------------------------
  /**
   * Concatenates multiple sub-ranges of a source range into a single range.
   *
   * @param x_begin the beginning of the source range
   * @param seg_begin the beginning of the ranges that describe the
   *  sub-ranges (start, size)
   * @param seg_end one past the end of the ranges that describe the
   *  sub-ranges
   * @param y_begin the beginning of the concatenated range
   */
  template <typename InIt1, typename InIt2, typename OutIt>
  inline void
  concatenate(InIt1 x_begin, InIt2 seg_begin, InIt2 seg_end, OutIt y_begin)
  {
    {
      NTA_ASSERT(seg_begin <= seg_end)
        << "concatenate: Invalid segment range";
    }

    for (; seg_begin != seg_end; ++seg_begin) {
      InIt1 begin = x_begin + seg_begin->first;
      InIt1 end = begin + seg_begin->second;
      std::copy(begin, end, y_begin);
      y_begin += seg_begin->second;
    }
  }

  //--------------------------------------------------------------------------------
  // Clip, threshold, binarize
  //--------------------------------------------------------------------------------
  /**
   * Clip the values in a range to be between min (included) and max (included):
   * any value less than min becomes min and any value greater than max becomes
   * max.
   *
   * @param begin
   * @param end
   * @param _min the minimum value
   * @param _max the maximum value
   */
  template <typename It>
  inline void clip(It begin, It end,
                   const typename std::iterator_traits<It>::value_type& _min,
                   const typename std::iterator_traits<It>::value_type& _max)
  {
    {
      NTA_ASSERT(begin <= end)
        << "clip: Invalid range";
    }

    while (begin != end) {
      typename std::iterator_traits<It>::value_type val = *begin;
      if (val > _max)
        *begin = _max;
      else if (val < _min)
        *begin = _min;
      ++begin;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Clip the values in a container to be between min (included) and max (included):
   * any value less than min becomes min and any value greater than max becomes
   * max.
   *
   * @param a the container
   * @param _min
   * @param _max
   */
  template <typename T>
  inline void clip(T& a,
                   const typename T::value_type& _min,
                   const typename T::value_type& _max)
  {
    clip(a.begin(), a.end(), _min, _max);
  }

  //--------------------------------------------------------------------------------
  /**
   * Threshold a range and puts the values that were not eliminated into
   * another (sparse) range (index, value).
   *
   * @param begin
   * @param end
   * @param ind the beginning of the sparse indices
   * @param nz the beginning of the sparse values
   * @param th the threshold to use
   */
  template <typename InIter, typename OutIter1, typename OutIter2>
  inline size_t threshold(InIter begin, InIter end,
                          OutIter1 ind, OutIter2 nz,
                          const typename std::iterator_traits<InIter>::value_type& th,
                          bool above =true)
  {
    {
      NTA_ASSERT(begin <= end)
        << "threshold: Invalid range";
    }

    typedef typename std::iterator_traits<InIter>::value_type value_type;
    typedef size_t size_type;

    size_type n = 0;

    if (above) {

      for (InIter it = begin; it != end; ++it) {
        value_type val = (value_type) *it;
        if (val >= th) {
          *ind = (size_type) (it - begin);
          *nz = val;
          ++ind; ++nz; ++n;
        }
      }

    } else {

      for (InIter it = begin; it != end; ++it) {
        value_type val = (value_type) *it;
        if (val < th) {
          *ind = (size_type) (it - begin);
          *nz = val;
          ++ind; ++nz; ++n;
        }
      }
    }

    return n;
  }

  //--------------------------------------------------------------------------------
  /**
   * Given a threshold and a dense vector x, returns another dense vectors with 1's 
   * where the value of x is > threshold, and 0 elsewhere. Also returns the count
   * of 1's.
   */
  template <typename InputIterator, typename OutputIterator>
  inline nta::UInt32 
  binarize_with_threshold(nta::Real32 threshold, 
                          InputIterator x, InputIterator x_end,
                          OutputIterator y, OutputIterator y_end)
  {
    {
      NTA_ASSERT(x_end - x == y_end - y);
    }

    nta::UInt32 count = 0;

    for (; x != x_end; ++x, ++y)
      if (*x > threshold) {
        *y = 1;
        ++count;
      } else 
        *y = 0;

    return count;
  }

  //--------------------------------------------------------------------------------
  // INDICATORS
  //--------------------------------------------------------------------------------

  //--------------------------------------------------------------------------------
  /**
   * Given a dense 2D array of 0 and 1, return a vector that has as many rows as x
   * a 1 wherever x as a non-zero row, and a 0 elsewhere. I.e. the result is the
   * indicator of non-zero rows. Gets fast by not scanning a row more than is 
   * necessary, i.e. stops as soon as a 1 is found on the row.
   */
  template <typename InputIterator, typename OutputIterator>
  inline void
  nonZeroRowsIndicator_01(nta::UInt32 nrows, nta::UInt32 ncols,
                          InputIterator x, InputIterator x_end,
                          OutputIterator y, OutputIterator y_end)
  {
    {
      NTA_ASSERT(0 < nrows);
      NTA_ASSERT(0 < ncols);
      NTA_ASSERT((nta::UInt32)(x_end - x) == nrows * ncols);
      NTA_ASSERT((nta::UInt32)(y_end - y) == nrows);
#ifdef NTA_ASSERTION_ON
      for (nta::UInt32 i = 0; i != nrows * ncols; ++i)
        NTA_ASSERT(x[i] == 0 || x[i] == 1);
#endif
    }
    
    for (nta::UInt32 r = 0; r != nrows; ++r, ++y) {
      
      InputIterator it = x + r * ncols, it_end = it + ncols;
      nta::UInt32 found = 0;

      while (it != it_end && found == 0) 
        found = nta::UInt32(*it++);
      
      *y = found;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Given a dense 2D array of 0 and 1, return the number of rows that have 
   * at least one non-zero. Gets fast by not scanning a row more than is 
   * necessary, i.e. stops as soon as a 1 is found on the row.
   */
  template <typename InputIterator>
  inline nta::UInt32 
  nNonZeroRows_01(nta::UInt32 nrows, nta::UInt32 ncols,
                  InputIterator x, InputIterator x_end)
  {
    {
      NTA_ASSERT(0 < nrows);
      NTA_ASSERT(0 < ncols);
      NTA_ASSERT((nta::UInt32)(x_end - x) == nrows * ncols);
#ifdef NTA_ASSERTION_ON
      for (nta::UInt32 i = 0; i != nrows * ncols; ++i)
        NTA_ASSERT(x[i] == 0 || x[i] == 1);
#endif
    }
    
    nta::UInt32 count = 0;
    
    for (nta::UInt32 r = 0; r != nrows; ++r) {
      
      InputIterator it = x + r * ncols, it_end = it + ncols;
      nta::UInt32 found = 0;

      while (it != it_end && found == 0) 
        found = nta::UInt32(*it++);
      
      count += found;
    }

    return count;
  }

  //--------------------------------------------------------------------------------
  /**
   * Given a dense 2D array of 0 and 1 x, return a vector that has as many cols as x
   * a 1 wherever x as a non-zero col, and a 0 elsewhere. I.e. the result is the
   * indicator of non-zero cols. Gets fast by not scanning a row more than is 
   * necessary, i.e. stops as soon as a 1 is found on the col.
   */
  template <typename InputIterator, typename OutputIterator>
  inline void
  nonZeroColsIndicator_01(nta::UInt32 nrows, nta::UInt32 ncols,
                          InputIterator x, InputIterator x_end,
                          OutputIterator y, OutputIterator y_end)
  {
    {
      NTA_ASSERT(0 < nrows);
      NTA_ASSERT(0 < ncols);
      NTA_ASSERT((nta::UInt32)(x_end - x) == nrows * ncols);
      NTA_ASSERT((nta::UInt32)(y_end - y) == ncols);
#ifdef NTA_ASSERTION_ON
      for (nta::UInt32 i = 0; i != nrows * ncols; ++i)
        NTA_ASSERT(x[i] == 0 || x[i] == 1);
#endif
    }
    
    nta::UInt32 N = nrows*ncols;
    
    for (nta::UInt32 c = 0; c != ncols; ++c, ++y) {
      
      InputIterator it = x + c, it_end = it + N;
      nta::UInt32 found = 0;

      while (it != it_end && found == 0) {
        found = nta::UInt32(*it);
        it += ncols;
      }
      
      *y = found;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Given a dense 2D array of 0 and 1, return the number of columns that have 
   * at least one non-zero.
   * Gets fast by not scanning a col more than is necessary, i.e. stops as soon as 
   * a 1 is found on the col.
   */
  template <typename InputIterator>
  inline nta::UInt32 
  nNonZeroCols_01(nta::UInt32 nrows, nta::UInt32 ncols,
                  InputIterator x, InputIterator x_end)
  {
    {
      NTA_ASSERT(0 < nrows);
      NTA_ASSERT(0 < ncols);
      NTA_ASSERT((nta::UInt32)(x_end - x) == nrows * ncols);
#ifdef NTA_ASSERTION_ON
      for (nta::UInt32 i = 0; i != nrows * ncols; ++i)
        NTA_ASSERT(x[i] == 0 || x[i] == 1);
#endif
    }
    
    nta::UInt32 count = 0;
    nta::UInt32 N = nrows*ncols;
    
    for (nta::UInt32 c = 0; c != ncols; ++c) {
      
      InputIterator it = x + c, it_end = it + N;
      nta::UInt32 found = 0;

      while (it != it_end && found == 0) {
        found = nta::UInt32(*it);
        it += ncols;
      }
      
      count += found;
    }

    return count;
  }

  //--------------------------------------------------------------------------------
  // MASK
  //--------------------------------------------------------------------------------
  /**
   * Mask an array.
   */
  template <typename InIter>
  inline void mask(InIter begin, InIter end, InIter zone_begin, InIter zone_end,
                   const typename std::iterator_traits<InIter>::value_type& v =0,
                   bool maskOutside =true)
  {
    { // Pre-conditions
      NTA_ASSERT(begin <= end)
        << "mask 1: Invalid range for vector";
      NTA_ASSERT(zone_begin <= zone_end)
        << "mask 1: Invalid range for mask";
      NTA_ASSERT(begin <= zone_begin && zone_end <= end)
        << "mask 1: Mask incompatible with vector";
    } // End pre-conditions

    typedef typename std::iterator_traits<InIter>::value_type value_type;

    if (maskOutside) {
      std::fill(begin, zone_begin, v);
      std::fill(zone_end, end, v);
    } else {
      std::fill(zone_begin, zone_end, v);
    }
  }

  //--------------------------------------------------------------------------------
  template <typename value_type>
  inline void mask(std::vector<value_type>& x,
                   typename std::vector<value_type>::size_type zone_begin,
                   typename std::vector<value_type>::size_type zone_end,
                   const value_type& v =0,
                   bool maskOutside =true)
  {
    { // Pre-conditions
      NTA_ASSERT(0 <= zone_begin && zone_begin <= zone_end && zone_end <= x.size())
        << "mask 2: Mask incompatible with vector";
    } // End pre-conditions

    mask(x.begin(), x.end(), x.begin() + zone_begin, x.begin() + zone_end,
         v, maskOutside);
  }

  //--------------------------------------------------------------------------------
  template <typename value_type1, typename value_type2>
  inline void mask(std::vector<value_type1>& x, const std::vector<value_type2>& mask,
                   bool multiplyYesNo =false, value_type2 eps =(value_type2)nta::Epsilon)
  {
    { // Pre-conditions
      NTA_ASSERT(x.size() == mask.size())
        << "mask 3: Need mask and vector to have same size";
    } // End pre-conditions

    typedef typename std::vector<value_type1>::size_type size_type;

    if (multiplyYesNo) {
      for (size_type i = 0; i != x.size(); ++i)
        if (!nearlyZero(mask[i]), eps)
          x[i] *= (value_type1) mask[i];
        else
          x[i] = (value_type1) 0;

    } else {
      for (size_type i = 0; i != x.size(); ++i)
        if (nearlyZero(mask[i], eps))
          x[i] = (value_type1) 0;
    }
  }

  //--------------------------------------------------------------------------------
  // NORMS
  //--------------------------------------------------------------------------------
  /**
   * A class that provides init and operator(), to be used in distance
   * computations when using the Hamming (L0) norm.
   */
  template <typename T>
  struct Lp0
  {
    typedef T value_type;

    inline value_type operator()(value_type& a, value_type b) const
    {
      value_type inc = value_type(b < -nta::Epsilon || b > nta::Epsilon);
      a += inc;
      return inc;
    }

    inline value_type root(value_type x) const { return x; }
  };

  //--------------------------------------------------------------------------------
  /**
   * A class that provides init and operator(), to be used in distance
   * computations when using the Manhattan (L1) norm.
   */
  template <typename T>
  struct Lp1
  {
    typedef T value_type;

    inline value_type operator()(value_type& a, value_type b) const
    {
      value_type inc = fabs(b); //b > 0.0 ? b : -b;
      a += inc;
      return inc;
    }

    inline value_type root(value_type x) const { return x; }
  };

  //--------------------------------------------------------------------------------
  /**
   * A class that provides square and square root methods, to be
   * used in distance computations when using L2 norm.
   */
  template <typename T>
  struct Lp2
  {
    typedef T value_type;

    nta::Sqrt<value_type> s;

    inline value_type operator()(value_type& a, value_type b) const
    {
      value_type inc = b * b;
      a += inc;
      return inc;
    }

    inline value_type root(value_type x) const
    {
      return s(x);
    }
  };

  //--------------------------------------------------------------------------------
  /**
   * A class that provides power p and root p methods, to be
   * used in distance computations using Lp norm.
   */
  template <typename T>
  struct Lp
  {
    typedef T value_type;

    nta::Pow<value_type> pf;

    Lp(value_type p_)
      : p(p_), inv_p((value_type)1.0)
    {
      // We allow only positive values of p for now, as this
      // keeps the root function monotonically increasing, which
      // results in further speed-ups.
      NTA_ASSERT(p_ > (value_type)0.0)
        << "NearestNeighbor::PP(): "
        << "Invalid value for p: " << p_
        << " - p needs to be > 0";

      inv_p = (value_type)1.0/p;
    }

    value_type p, inv_p;

    inline value_type operator()(value_type& a, value_type b) const
    {
      value_type inc = pf(b > 0.0 ? b : -b, p);
      a += inc;
      return inc;
    }

    inline value_type root(value_type x) const
    {
      // skipping abs, because we know we've been adding positive
      // numbers when root is called when computing a norm
      return pf(x, inv_p);
    }
  };

  //--------------------------------------------------------------------------------
  /**
   * A class that provides power p and root p methods, to be
   * used in distance computations using LpMax norm.
   */
  template <typename T>
  struct LpMax
  {
    typedef T value_type;

    nta::Max<value_type> m;

    inline value_type operator()(value_type& a, value_type b) const
    {
      value_type inc = m(a, b > 0 ? b : -b);
      a = inc;
      return inc;
    }

    inline value_type root(value_type x) const { return x; }
  };

  //--------------------------------------------------------------------------------
  /**
   * Hamming norm.
   */
  template <typename It>
  inline typename std::iterator_traits<It>::value_type
  l0_norm(It begin, It end, bool =true)
  {
    {
      NTA_ASSERT(begin <= end)
        << "l0_norm: Invalid range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    value_type n = (value_type) 0;
    Lp0<value_type> lp0;

    for (; begin != end; ++begin)
      lp0(n, *begin);

    return n;
  }

  //--------------------------------------------------------------------------------
  /**
   * Hamming norm on a container
   */
  template <typename T>
  inline typename T::value_type l0_norm(const T& a, bool =true)
  {
    return l0_norm(a.begin(), a.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * Manhattan norm.
   */
  template <typename It>
  inline typename std::iterator_traits<It>::value_type
  l1_norm(It begin, It end, bool =true)
  {
    {
      NTA_ASSERT(begin <= end)
        << "l1_norm: Invalid range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    value_type n = (value_type) 0;
    Lp1<value_type> lp1;

    for (; begin != end; ++begin)
      lp1(n, *begin);

    return n;
  }

  //--------------------------------------------------------------------------------
  /**
   * Manhattan norm on a container.
   */
  template <typename T>
  inline typename T::value_type l1_norm(const T& a, bool =true)
  {
    return l1_norm(a.begin(), a.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * Euclidean norm.
   */
  
  //--------------------------------------------------------------------------------
#ifdef NTA_PLATFORM_darwin86
  inline void sum_of_squares(float* begin, int n, float* s)
  {
    vDSP_svesq(begin, 1, s, n);
  }
  
  //--------------------------------------------------------------------------------
  inline void sum_of_squares(double* begin, int n, double* s)
  {
    vDSP_svesqD(begin, 1, s, n);
  }
#endif

  //--------------------------------------------------------------------------------
  template <typename It>
  inline typename std::iterator_traits<It>::value_type
  l2_norm(It begin, It end, bool take_root =true)
  {
    {
      NTA_ASSERT(begin <= end)
        << "l2_norm: Invalid range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;
    value_type n = (value_type) 0;

    Lp2<value_type> lp2;

#ifdef NTA_PLATFORM_darwin86 // 10X faster

    // &*begin won't work on platforms where the iterators are not pointers
    // (win32)
    sum_of_squares(&*begin, (end - begin), &n);

#else

    for (; begin != end; ++begin)
      lp2(n, *begin);
   
#endif

    if (take_root)
      n = lp2.root(n);
    
    return n;
  }

  //--------------------------------------------------------------------------------
  /**
   * Euclidean norm on a container.
   */
  template <typename T>
  inline typename T::value_type l2_norm(const T& a, bool take_root =true)
  {
    return l2_norm(a.begin(), a.end(), take_root);
  }

  //--------------------------------------------------------------------------------
  /**
   * p-norm.
   */
  template <typename It>
  inline typename std::iterator_traits<It>::value_type
  lp_norm(typename std::iterator_traits<It>::value_type p,
          It begin, It end, bool take_root =true)
  {
    {
      NTA_ASSERT(begin <= end)
        << "lp_norm: Invalid range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    value_type n = (value_type) 0;
    Lp<value_type> lp(p);

    for (; begin != end; ++begin)
      lp(n, *begin);

    if (take_root)
      n = lp.root(n);

    return n;
  }

  //--------------------------------------------------------------------------------
  /**
   * p-norm on a container.
   */
  template <typename T>
  inline typename T::value_type
  lp_norm(typename T::value_type p, const T& a, bool take_root =true)
  {
    return lp_norm(p, a.begin(), a.end(), take_root);
  }

  //--------------------------------------------------------------------------------
  /**
   * L inf / L max norm.
   */
  template <typename It>
  inline typename std::iterator_traits<It>::value_type
  lmax_norm(It begin, It end, bool =true)
  {
    {
      NTA_ASSERT(begin <= end)
        << "lmax_norm: Invalid range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    value_type n = (value_type) 0;
    LpMax<value_type> lmax;

    for (; begin != end; ++begin)
      lmax(n, *begin);

    return n;
  }

  //--------------------------------------------------------------------------------
  /**
   * L inf / L max norm on a container.
   */
  template <typename T>
  inline typename T::value_type lmax_norm(const T& a, bool =true)
  {
    return lmax_norm(a.begin(), a.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * Norm function.
   *
   * @param p the norm
   * @param begin
   * @param end
   * @param take_root whether to take the p-th root or not
   */
  template <typename It>
  inline typename std::iterator_traits<It>::value_type
  norm(typename std::iterator_traits<It>::value_type p,
       It begin, It end, bool take_root =true)
  {
    {
      NTA_ASSERT(begin <= end)
        << "norm: Invalid range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    if (p == (value_type) 0)
      return l0_norm(begin, end);
    else if (p == (value_type) 1)
      return l1_norm(begin, end);
    else if (p == (value_type) 2)
      return l2_norm(begin, end, take_root);
    else if (p == std::numeric_limits<value_type>::max())
      return lmax_norm(begin, end);
    else
      return lp_norm(p, begin, end, take_root);
  }
  
  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It>
  inline void
  multiply_val(It begin, It end,
               const typename std::iterator_traits<It>::value_type& val)
  {
    {
      NTA_ASSERT(begin <= end)
        << "multiply_val: Invalid range";
    }

    if (val == 1.0f)
      return;

    for (; begin != end; ++begin)
      *begin *= val;
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename T>
  inline void multiply_val(T& x, const typename T::value_type& val)
  {
    multiply_val(x.begin(), x.end(), val);
  }

  //--------------------------------------------------------------------------------
  /**
   * Norm on a whole container.
   */
  template <typename T>
  inline typename T::value_type
  norm(typename T::value_type p, const T& a, bool take_root =true)
  {
    return norm(p, a.begin(), a.end(), take_root);
  }

  //--------------------------------------------------------------------------------
  /**
   * Normalize a range, according to the p norm, so that the values sum up to n.
   *
   * @param begin
   * @param end
   * @param p the norm
   * @param n the value of the sum of the elements after normalization
   */
  template <typename It>
  inline void
  normalize(It begin, It end,
            const typename std::iterator_traits<It>::value_type& p =1.0,
            const typename std::iterator_traits<It>::value_type& n =1.0)
  {
    {
      NTA_ASSERT(begin <= end)
        << "normalize: Invalid input range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    value_type s = (value_type) 0;

    if (p == (value_type) 0)
      s = l0_norm(begin, end);
    else if (p == (value_type) 1)
      s = l1_norm(begin, end);
    else if (p == (value_type) 2)
      s = l2_norm(begin, end);
    else if (p == std::numeric_limits<value_type>::max())
      s = lmax_norm(begin, end);

    if (s != (value_type) 0)
      multiply_val(begin, end, n/s);
  }

  //--------------------------------------------------------------------------------
  /**
   * Normalize a container, with p-th norm and so that values add up to n.
   */
  template <typename T>
  inline void normalize(T& a,
                        const typename T::value_type& p =1.0,
                        const typename T::value_type& n =1.0)
  {
    normalize(a.begin(), a.end(), p, n);
  }

  //--------------------------------------------------------------------------------
  /**
   * Normalization according to LpMax: finds the max of the range,
   * and then divides all the values so that the max is n.
   * Makes it nicer to call normalize when using LpMax.
   */
  template <typename It>
  inline void
  normalize_max(It begin, It end,
                const typename std::iterator_traits<It>::value_type& n = 1.0)
  {
    {
      NTA_ASSERT(begin <= end)
        << "normalize_max: Invalid range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    normalize(begin, end, std::numeric_limits<value_type>::max(), n);
  }

  //--------------------------------------------------------------------------------
  /**
   * Normalization according to LpMax.
   */
  template <typename value_type>
  inline void normalize_max(std::vector<value_type>& x, const value_type& n = 1.0)
  {
    normalize_max(x.begin(), x.end(), n);
  }
  
  //--------------------------------------------------------------------------------
  /**
   * Fills the container with a range of values.
   */
  template <typename T>
  inline void generate_range(T& t,
                             typename T::value_type start,
                             typename T::value_type end,
                             typename T::value_type increment =1)
  {
    std::insert_iterator<T> it(t, t.begin());

    for (typename T::value_type i = start; i < end; i += increment, ++it)
      *it = i;
  }

  //--------------------------------------------------------------------------------
  /**
   * Initializes a range with the uniform distribution.
   *
   * @param begin beginning of the range
   * @param end one past the end of the range
   * @param val the value to which the sum of the range will be equal to
   */
  template <typename It>
  inline void
  uniform_range(It begin, It end,
                typename std::iterator_traits<It>::value_type val =1)
  {
    {
      NTA_ASSERT(begin <= end)
        << "uniform_range: Invalid input range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;

    std::fill(begin, end, (value_type) 1);
    normalize(begin, end, val);
  }

  //--------------------------------------------------------------------------------
  /**
   * Initializes a container with the uniform distribution.
   *
   * @param a the container
   * @param val the value for normalization
   */
  template <typename C>
  inline void uniform_range(C& a, typename C::value_type val =1)
  {
    uniform_range(a.begin(), a.end(), val);
  }

  //--------------------------------------------------------------------------------
  // DISTANCES
  //--------------------------------------------------------------------------------
  /**
   * Returns the max of the absolute values of the differences.
   *
   * @param begin1
   * @param end1
   * @param begin2
   */
  template <typename It1, typename It2>
  inline typename std::iterator_traits<It1>::value_type
  max_abs_diff(It1 begin1, It1 end1, It2 begin2, It2 end2)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "max_abs_diff: Invalid range 1";
      NTA_ASSERT(begin2 <= end2)
        << "max_abs_diff: Invalid range 2";
      NTA_ASSERT(end1 - begin1 == end2 - begin2)
        << "max_abs_diff: Ranges of different sizes";
    }

    typename std::iterator_traits<It1>::value_type d(0), val(0);

    while (begin1 != end1) {
      val = *begin1 - *begin2;
      val = val > 0 ? val : -val;
      if (val > d)
        d = val;
      ++begin1; ++begin2;
    }

    return d;
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the max of the absolute values of the differences.
   *
   * @param a first container
   * @param b second container
   */
  template <typename T1, typename T2>
  inline typename T1::value_type max_abs_diff(const T1& a, const T2& b)
  {
    return max_abs_diff(a.begin(), a.end(), b.begin(), b.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the Hamming distance of the two ranges.
   *
   * @param begin1
   * @param end1
   * @param begin2
   */
  template <typename It1, typename It2>
  inline typename std::iterator_traits<It1>::value_type
  hamming_distance(It1 begin1, It1 end1, It2 begin2, It2 end2)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "hamming_distance: Invalid range 1";
      NTA_ASSERT(begin2 <= end2)
        << "hamming_distance: Invalid range 2";
      NTA_ASSERT(end1 - begin1 == end2 - begin2)
        << "hamming_distance: Ranges of different sizes";
    }

    typename std::iterator_traits<It1>::value_type d(0);

    while (begin1 != end1) {
      d += *begin1 != *begin2;
      ++begin1; ++begin2;
    }

    return d;
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the Hamming distance of the two containers.
   *
   * @param a first container
   * @param b second container
   */
  template <typename T1, typename T2>
  inline typename T1::value_type
  hamming_distance(const T1& a, const T2& b)
  {
    return hamming_distance(a.begin(), a.end(), b.begin(), b.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * [begin1, end1) and [begin2, end2) are index encodings of binary 0/1 ranges.
   */
  template <typename It1, typename It2>
  inline size_t
  sparse_hamming_distance(It1 begin1, It1 end1, It2 begin2, It2 end2)
  {
    {
      // todo: check that ranges are valid sparse indices ranges
      // (increasing, no duplicate...)
      NTA_ASSERT(begin1 <= end1)
        << "sparse_hamming_distance: Invalid range 1";
      NTA_ASSERT(begin2 <= end2)
        << "sparse_hamming_distance: Invalid range 2";
    }

    typedef size_t size_type;

    size_type d = 0;

    while (begin1 != end1 && begin2 != end2) {
      if (*begin1 < *begin2) {
        ++d;
        ++begin1;
      } else if (*begin2 < *begin1) {
        ++d;
        ++begin2;
      } else {
        ++begin1;
        ++begin2;
      }
    }

    d += (size_type)(end1 - begin1);
    d += (size_type)(end2 - begin2);

    return d;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline typename T1::size_type
  sparse_hamming_distance(const T1& a, const T2& b)
  {
    return sparse_hamming_distance(a.begin(), a.end(), b.begin(), b.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the Manhattan distance of the two ranges.
   *
   * @param begin1
   * @param end1
   * @param begin2
   */
  template <typename It1, typename It2>
  inline typename std::iterator_traits<It1>::value_type
  manhattan_distance(It1 begin1, It1 end1, It2 begin2, It2 end2)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "manhattan_distance: Invalid range 1";
      NTA_ASSERT(begin2 <= end2)
        << "manhattan_distance: Invalid range 2";
      NTA_ASSERT(end1 - begin1 == end2 - begin2)
        << "manhattan_distance: Ranges of different sizes";
    }

    typedef typename std::iterator_traits<It1>::value_type value_type;

    value_type d = (value_type) 0;
    Lp1<value_type> lp1;

    for (; begin1 != end1; ++begin1, ++begin2)
      lp1(d, *begin1 - *begin2);

    return d;
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the Manhattan distance of the two containers.
   *
   * @param a first container
   * @param b second container
   */
  template <typename T1, typename T2>
  inline typename T1::value_type
  manhattan_distance(const T1& a, const T2& b)
  {
    return manhattan_distance(a.begin(), a.end(), b.begin(), b.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the Euclidean distance of the two ranges.
   *
   * @param begin1
   * @param end1
   * @param begin2
   */
  template <typename It1, typename It2>
  inline typename std::iterator_traits<It1>::value_type
  euclidean_distance(It1 begin1, It1 end1, It2 begin2, It2 end2, bool take_root =true)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "euclidean_distance: Invalid range 1";
      NTA_ASSERT(begin2 <= end2)
        << "euclidean_distance: Invalid range 2";
      NTA_ASSERT(end1 - begin1 == end2 - begin2)
        << "euclidean_distance: Ranges of different sizes";
    }

    typedef typename std::iterator_traits<It1>::value_type value_type;

    value_type d = (value_type) 0;
    Lp2<value_type> lp2;

    for (; begin1 != end1; ++begin1, ++begin2)
      lp2(d, *begin1 - *begin2);

    if (take_root)
      d = lp2.root(d);

    return d;
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the Euclidean distance of the two containers.
   *
   * @param a first container
   * @param b second container
   */
  template <typename T1, typename T2>
  inline typename T1::value_type
  euclidean_distance(const T1& a, const T2& b, bool take_root =true)
  {
    return euclidean_distance(a.begin(), a.end(), b.begin(), b.end(), take_root);
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the Lp distance of the two ranges.
   *
   * @param begin1
   * @param end1
   * @param begin2
   */
  template <typename It1, typename It2>
  inline typename std::iterator_traits<It1>::value_type
  lp_distance(typename std::iterator_traits<It1>::value_type p,
              It1 begin1, It1 end1, It2 begin2, It2 end2, bool take_root =true)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "lp_distance: Invalid range 1";
      NTA_ASSERT(begin2 <= end2)
        << "lp_distance: Invalid range 2";
      NTA_ASSERT(end1 - begin1 == end2 - begin2)
        << "lp_distance: Ranges of different sizes";
    }

    typedef typename std::iterator_traits<It1>::value_type value_type;

    value_type d = (value_type) 0;
    Lp<value_type> lp(p);

    for (; begin1 != end1; ++begin1, ++begin2)
      lp(d, *begin1 - *begin2);

    if (take_root)
      d = lp.root(d);

    return d;
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the Lp distance of the two containers.
   *
   * @param a first container
   * @param b second container
   */
  template <typename T1, typename T2>
  inline typename T1::value_type
  lp_distance(typename T1::value_type p,
              const T1& a, const T2& b, bool take_root =true)
  {
    return lp_distance(p, a.begin(), a.end(), b.begin(), b.end(), take_root);
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the Lmax distance of the two ranges.
   *
   * @param begin1
   * @param end1
   * @param begin2
   */
  template <typename It1, typename It2>
  inline typename std::iterator_traits<It1>::value_type
  lmax_distance(It1 begin1, It1 end1, It2 begin2, It2 end2, bool =true)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "lmax_distance: Invalid range 1";
      NTA_ASSERT(begin2 <= end2)
        << "lmax_distance: Invalid range 2";
      NTA_ASSERT(end1 - begin1 == end2 - begin2)
        << "lmax_distance: Ranges of different sizes";
    }

    typedef typename std::iterator_traits<It1>::value_type value_type;

    value_type d = (value_type) 0;
    LpMax<value_type> lmax;

    for (; begin1 != end1; ++begin1, ++begin2)
      lmax(d, *begin1 - *begin2);

    return d;
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the Lmax distance of the two containers.
   *
   * @param a first container
   * @param b second container
   */
  template <typename T1, typename T2>
  inline typename T1::value_type
  lmax_distance(const T1& a, const T2& b, bool =true)
  {
    return lmax_distance(a.begin(), a.end(), b.begin(), b.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the distance of the two ranges.
   *
   * @param begin1
   * @param end1
   * @param begin2
   */
  template <typename It1, typename It2>
  inline typename std::iterator_traits<It1>::value_type
  distance(typename std::iterator_traits<It1>::value_type p,
           It1 begin1, It1 end1, It2 begin2, It2 end2, bool take_root =true)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "distance: Invalid range 1";
      NTA_ASSERT(begin2 <= end2)
        << "distance: Invalid range 2";
      NTA_ASSERT(end1 - begin1 == end2 - begin2)
        << "distance: Ranges of different sizes";
    }

    typedef typename std::iterator_traits<It1>::value_type value_type;

    if (p == (value_type) 0)
      return hamming_distance(begin1, end1, begin2);
    else if (p == (value_type) 1)
      return manhattan_distance(begin1, end1, begin2);
    else if (p == (value_type) 2)
      return euclidean_distance(begin1, end1, begin2, take_root);
    else if (p == std::numeric_limits<value_type>::max())
      return lmax_distance(begin1, end1, begin2);
    else
      return lp_distance(p, begin1, end1, begin2, take_root);
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the distance of the two containers.
   *
   * @param a first container
   * @param b second container
   */
  template <typename T1, typename T2>
  inline typename T1::value_type
  distance(typename T1::value_type p, const T1& a, const T2& b, bool take_root =true)
  {
    return distance(p, a.begin(), a.end(), b.begin(), b.end(), take_root);
  }

  //--------------------------------------------------------------------------------
  // Counting
  //--------------------------------------------------------------------------------
  /**
   * Counts the elements which satisfy the passed predicate in the given range.
   */
  template <typename C, typename Predicate>
  inline size_t count_if(const C& c, Predicate pred)
  {
    return std::count_if(c.begin(), c.end(), pred);
  }

  //--------------------------------------------------------------------------------
  /**
   * Counts the number of zeros in the given range.
   */
  template <typename It>
  inline size_t
  count_zeros(It begin, It end,
              const typename std::iterator_traits<It>::value_type& eps =nta::Epsilon)
  {
    {
      NTA_ASSERT(begin <= end)
        << "count_zeros: Invalid range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;
    return std::count_if(begin, end, IsNearlyZero<DistanceToZero<value_type> >(eps));
  }

  //--------------------------------------------------------------------------------
  /**
   * Counts the number of zeros in the container passed in.
   */
  template <typename C>
  inline size_t count_zeros(const C& c, const typename C::value_type& eps =nta::Epsilon)
  {
    return count_zeros(c.begin, c.end(), eps);
  }

  //--------------------------------------------------------------------------------
  /**
   * Count the number of ones in the given range.
   */
  template <typename It>
  inline size_t
  count_ones(It begin, It end,
             const typename std::iterator_traits<It>::value_type& eps =nta::Epsilon)
  {
    {
      NTA_ASSERT(begin <= end)
        << "count_ones: Invalid range";
    }

    typedef typename std::iterator_traits<It>::value_type value_type;
    return std::count_if(begin, end, IsNearlyZero<DistanceToOne<value_type> >(eps));
  }

  //--------------------------------------------------------------------------------
  /**
   * Count the number of ones in the container passed in.
   */
  template <typename C>
  inline size_t count_ones(const C& c, const typename C::value_type& eps =nta::Epsilon)
  {
    return count_ones(c.begin(), c.end(), eps);
  }

  //--------------------------------------------------------------------------------
  /**
   * Counts the number of values greater than a given threshold in a given range.
   *
   * Asm SSE is many times faster than C++ (almost 10X), and C++ is 10X faster than
   * numpy (some_array > threshold).sum(). The asm code doesn't have branchs, which
   * is probably very good for the CPU front-end.
   *
   * This is not as general as a count_gt that would be parameterized on the type
   * of the elements in the range, and it requires passing in a Python arrays 
   * that are .astype(float32).
   * 
   * Doesn't work for 64 bits platforms, doesn't work on win32.
   */
  inline nta::UInt32
  count_gt(nta::Real32* begin, nta::Real32* end, nta::Real32 threshold)
  {
    NTA_ASSERT(begin <= end);

    // Need this, because the asm syntax is not correct for win32, 
    // we simply can't compile the code as is on win32.
    // this code does not pass the count_gt test with LLVM
#ifdef NTA_PLATFORM_darwin86_disabled

    // Need this, because even on darwin86, some older machines might 
    // not have the right SSE instructions.
    if (SSE_LEVEL >= 3) {

      // Compute offsets into array [begin..end): 
      // start is the first 4 bytes aligned address (to start movaps)
      // n0 is the number of floats before we reach start and can use parallel
      //  xmm operations
      // n1 is the number floats we can process in parallel with xmm
      // n2 is the number of "stragglers" what we will have to do one by one ( < 4)
      nta::Real32 count = 0;
      long x_addr = (long) begin; // 8 bytes on 64 bits platforms
      nta::Real32* start = (x_addr % 16 == 0) ? begin : (nta::Real32*) (16*(x_addr/16+1));
      int n0 = (int)(start - begin);
      int n1 = 4 * ((end - start) / 4);
      int n2 = (int)(end - start - n1);
    
      asm volatile(
                   // Prepare various xmm registers, storing the value of the 
                   // threshold and the value 1: with xmm, we will operate on 
                   // 4 floats at a time, so we replicate threshold 4 times in
                   // xmm1, and 4 times again in xmm2. The operations will be in
                   // parallel.
                   "subl $16, %%esp\n\t"            // allocate 4 floats on stack

                   "movl %%eax, (%%esp)\n\t"        // copy threshold to 4 locations
                   "movl %%eax, 4(%%esp)\n\t"       // on stack: we want threshold 
                   "movl %%eax, 8(%%esp)\n\t"       // to be filling xmm1 and xmm2
                   "movl %%eax, 12(%%esp)\n\t"      // (operate on 4 floats at a time)
                   "movaps (%%esp), %%xmm1\n\t"     // move 4 thresholds into xmm1
                   "movaps %%xmm1, %%xmm2\n\t"      // copy 4 thresholds to xmm2

                   "movl $0x3f800000, (%%esp)\n\t"  // $0x3f800000 = (float) 1.0
                   "movl $0x3f800000, 4(%%esp)\n\t" // we want to have that constant
                   "movl $0x3f800000, 8(%%esp)\n\t" // 8 times, in xmm3 and xmm4,
                   "movl $0x3f800000, 12(%%esp)\n\t"// since the xmm4 registers allow
                   "movaps (%%esp), %%xmm3\n\t"     // us to operate on 4 floats at 
                   "movaps (%%esp), %%xmm4\n\t"     // a time

                   "addl $16, %%esp\n\t"            // deallocate 4 floats on stack
                   
                   "xorps %%xmm5, %%xmm5\n\t"       // set xmm5 to 0

                   // Loop over individual floats till we reach the right alignment
                   // that was computed in n0. If we don't start handling 4 floats
                   // at a time with SSE on a 4 bytes boundary, we get a crash
                   // in movaps (here, we use only movss, moving only 1 float at a 
                   // time).
                   "0:\n\t"
                   "test %%ecx, %%ecx\n\t"          // if n0 == 0, jump to next loop
                   "jz 1f\n\t"

                   "movss (%%esi), %%xmm0\n\t"      // move a single float to xmm0
                   "cmpss $1, %%xmm0, %%xmm1\n\t"   // compare to threshold
                   "andps %%xmm1, %%xmm3\n\t"       // and with all 1s
                   "addss %%xmm3, %%xmm5\n\t"       // add result to xmm5 (=count!)
                   "movaps %%xmm2, %%xmm1\n\t"      // restore threshold in xmm1 
                   "movaps %%xmm4, %%xmm3\n\t"      // restore all 1s in xmm3
                   "addl $4, %%esi\n\t"             // move to next float (4 bytes)
                   "decl %%ecx\n\t"                 // decrement ecx, which started at n0
                   "ja 0b\n\t"                      // jump if not done yet
                   
                   // Loop over 4 floats at a time: this time, we have reached
                   // the proper alignment for movaps, so we can operate in parallel
                   // on 4 floats at a time. The code is the same as the previous loop
                   // except that the "ss" instructions are now "ps" instructions.
                   "1:\n\t"
                   "test %%edx, %%edx\n\t"
                   "jz 2f\n\t"

                   "movaps (%%esi), %%xmm0\n\t"     // note movaps, not movss
                   "cmpps $1, %%xmm0, %%xmm1\n\t"
                   "andps %%xmm1, %%xmm3\n\t"
                   "addps %%xmm3, %%xmm5\n\t"       // addps, not addss
                   "movaps %%xmm2, %%xmm1\n\t"
                   "movaps %%xmm4, %%xmm3\n\t"
                   "addl $16, %%esi\n\t"            // jump over 4 floats
                   "subl $4, %%edx\n\t"             // decrement edx (n1) by 4 
                   "ja 1b\n\t"
                   
                   // Tally up count so far into last float of xmm5: we were 
                   // doing operations in parallels on the 4 floats in the xmm 
                   // registers, resulting in 4 partial counts in xmm5.
                   "xorps %%xmm0, %%xmm0\n\t"
                   "haddps %%xmm0, %%xmm5\n\t"
                   "haddps %%xmm0, %%xmm5\n\t"
                   
                   // Last loop, for stragglers in case the array is not evenly
                   // divisible by 4. We are back to operating on a single float
                   // at a time, using movss and addss.
                   "2:\n\t"
                   "test %%edi, %%edi\n\t"
                   "jz 3f\n\t"
               
                   "movss (%%esi), %%xmm0\n\t"
                   "cmpss $1, %%xmm0, %%xmm1\n\t"
                   "andps %%xmm1, %%xmm3\n\t"
                   "addss %%xmm3, %%xmm5\n\t"
                   "movaps %%xmm2, %%xmm1\n\t"
                   "movaps %%xmm4, %%xmm3\n\t"
                   "addl $4, %%esi\n\t"
                   "decl %%edi\n\t"
                   "ja 0b\n\t"
  
                   // Push result from xmm5 to variable count in memory.
                   "3:\n\t"
                   "movss %%xmm5, %0\n\t"

                   : "=m" (count)
                   : "S" (begin), "a" (threshold), "c" (n0), "d" (n1), "D" (n2)
                   : 
                   );
  
      return (int) count;
    
    } else {
      return std::count_if(begin, end, std::bind2nd(std::greater<nta::Real32>(), threshold));
    }
#else
    return std::count_if(begin, end, std::bind2nd(std::greater<nta::Real32>(), threshold));
#endif
  }

  //--------------------------------------------------------------------------------
  /**
   * Counts the number of values greater than or equal to a given threshold in a 
   *  given range.
   *
   * This is not as general as a count_gt that would be parameterized on the type
   * of the elements in the range, and it requires passing in a Python arrays 
   * that are .astype(float32).
   * 
   */
  inline nta::UInt32
  count_gte(nta::Real32* begin, nta::Real32* end, nta::Real32 threshold)
  {
    NTA_ASSERT(begin <= end);

    return std::count_if(begin, end, 
                         std::bind2nd(std::greater_equal<nta::Real32>(), 
                         threshold));
  }


  //--------------------------------------------------------------------------------
  /**
   * Counts the number of non-zeros in a vector.
   */
  inline size_t count_non_zeros(nta::Real32* begin, nta::Real32* end)
  {
    NTA_ASSERT(begin <= end);
    return count_gt(begin, end, 0);
  }

  //--------------------------------------------------------------------------------
  /**
   * Counts the number of non-zeros in a vector.
   * Doesn't work with vector<bool>.
   */
  template <typename T>
  inline size_t count_non_zeros(const std::vector<T>& x)
  {
    NTA_ASSERT(sizeof(T) == 4);
    nta::Real32* begin = (nta::Real32*) &x[0];
    nta::Real32* end = begin + x.size();
    return count_gt(begin, end, 0);
  }

  //--------------------------------------------------------------------------------
  /**
   * TODO: Use SSE. Maybe requires having our own vector<bool> so that we can avoid 
   * the shenanigans with the bit references and iterators.
   */
  template <>
  inline size_t count_non_zeros(const std::vector<bool>& x)
  {
    size_t count = 0;
    for (size_t i = 0; i != x.size(); ++i)
      count += x[i];
    return count;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline size_t count_non_zeros(const std::vector<std::pair<T1,T2> >& x)
  {
    size_t count = 0;
    for (size_t i = 0; i != x.size(); ++i)
      if (! is_zero(x[i]))
        ++count;
    return count;
  }
  
  //--------------------------------------------------------------------------------
  /**
   * Counts the number of values less than a given threshold in a given range.
   */
  template <typename It>
  inline size_t 
  count_lt(It begin, It end, const typename std::iterator_traits<It>::value_type& thres)
  {
    typedef typename std::iterator_traits<It>::value_type value_type;
    return std::count_if(begin, end, std::bind2nd(std::less<value_type>(), thres));
  }

  //--------------------------------------------------------------------------------
  // Rounding
  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It>
  inline void
  round_01(It begin, It end,
           const typename std::iterator_traits<It>::value_type& threshold =.5)
  {
    {
      NTA_ASSERT(begin <= end)
        << "round_01: Invalid range";
    }

    typename std::iterator_traits<It>::value_type val;

    while (begin != end) {
      val = *begin;
      if (val >= threshold)
        val = 1;
      else
        val = 0;
      *begin = val;
      ++begin;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename T>
  inline void round_01(T& a, const typename T::value_type& threshold =.5)
  {
    round_01(a.begin(), a.end(), threshold);
  }

  //--------------------------------------------------------------------------------
  // Addition...
  //--------------------------------------------------------------------------------
  /**
   * Computes the sum of the elements in a range.
   * vDSP is much faster than C++, even optimized by gcc, but for now this works
   * only with float (rather than double), and only on darwin86. With these 
   * restrictions the speed-up is usually better than 5X over optimized C++.
   * vDSP also handles unaligned vectors correctly, and has good performance
   * also when the vectors are small, not just when they are big. 
   */
  inline nta::Real32 sum(nta::Real32* begin, nta::Real32* end)
  {
    {
      NTA_ASSERT(begin <= end)
        << "sum: Invalid range";
    }

#ifdef NTA_PLATFORM_darwin86

    nta::Real32 result = 0;
    vDSP_sve(begin, 1, &result, (end - begin));
    return result;
    
#else

    nta::Real32 result = 0;
    for (; begin != end; ++begin)
      result += *begin;
    return result;

#endif
  }

  //--------------------------------------------------------------------------------
  /**
   * Compute the sum of a whole container.
   * Here we revert to C++, which is going to be slower than the preceding function,
   * but it will work for a container of anything, that container not necessarily
   * being a contiguous vector of numbers.
   */
  template <typename T>
  inline typename T::value_type sum(const T& x)
  {
    typename T::value_type result = 0;
    typename T::const_iterator it;
    for (it = x.begin(); it != x.end(); ++it)
      result += *it;
    return result;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2, typename T3>
  inline void sum(const std::vector<T1>& a, const std::vector<T2>& b, 
                  size_t begin, size_t end, std::vector<T3>& c)
  {
    for (size_t i = begin; i != end; ++i)
      c[i] = a[i] + b[i];
  }

  //--------------------------------------------------------------------------------
  /**
   * Computes the product of the elements in a range.
   */
  template <typename It>
  inline typename std::iterator_traits<It>::value_type product(It begin, It end)
  {
    {
      NTA_ASSERT(begin <= end)
        << "product: Invalid range";
    }

    typename std::iterator_traits<It>::value_type p(1);

    for (; begin != end; ++begin)
      p *= *begin;

    return p;
  }

  //--------------------------------------------------------------------------------
  /**
   * Computes the product of all the elements in a container.
   */
  template <typename T>
  inline typename T::value_type product(const T& x)
  {
    return product(x.begin(), x.end());
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It>
  inline void add_val(It begin, It end,
                      const typename std::iterator_traits<It>::value_type& val)
  {
    {
      NTA_ASSERT(begin <= end)
        << "add_val: Invalid range";
    }

    if (val == 0.0f)
      return;

    for (; begin != end; ++begin)
      *begin += val;
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename T>
  inline void add_val(T& x, const typename T::value_type& val)
  {
    add_val(x.begin(), x.end(), val);
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It>
  inline void subtract_val(It begin, It end,
                           const typename std::iterator_traits<It>::value_type& val)
  {
    add_val(begin, end, -val);
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename T>
  inline void subtract_val(T& x, const typename T::value_type& val)
  {
    subtract_val(x.begin(), x.end(), val);
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It>
  inline void negate(It begin, It end)
  {
    {
      NTA_ASSERT(begin <= end)
        << "negate: Invalid range";
    }

    for (; begin != end; ++begin)
      *begin = -*begin;
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename T>
  inline void negate(T& x)
  {
    negate(x.begin(), x.end());
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It>
  inline void
  divide_val(It begin, It end,
             const typename std::iterator_traits<It>::value_type& val)
  {
    {
      NTA_ASSERT(begin <= end)
        << "divide_val: Invalid range";
      NTA_ASSERT(val != 0)
        << "divide_val: Division by zero";
    }

    multiply_val(begin, end, 1.0f/val);
  }

  //--------------------------------------------------------------------------------
  // TODO: what if val == 0?
  /**
   */
  template <typename T>
  inline void divide_val(T& x, const typename T::value_type& val)
  {
    divide_val(x.begin(), x.end(), val);
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It1, typename It2>
  inline void add(It1 begin1, It1 end1, It2 begin2, It2 end2)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "add: Invalid range";
      NTA_ASSERT(end1 - begin1 <= end2 - begin2)
        << "add: Incompatible ranges";
    }

    for (; begin1 != end1; ++begin1, ++begin2)
      *begin1 += *begin2;
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename T1, typename T2>
  inline void add(T1& x, const T2& y)
  {
    add(x.begin(), x.end(), y.begin(), y.end());
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It1, typename It2>
  inline void subtract(It1 begin1, It1 end1, It2 begin2, It2 end2)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "subtract: Invalid range";
      NTA_ASSERT(end1 - begin1 <= end2 - begin2)
        << "subtract: Incompatible ranges";
    }

    for (; begin1 != end1; ++begin1, ++begin2)
      *begin1 -= *begin2;
  }

  //--------------------------------------------------------------------------------
  // TODO: should we have the same argument ordering as copy??
  /**
   */
  template <typename T1, typename T2>
  inline void subtract(T1& x, const T2& y)
  {
    subtract(x.begin(), x.end(), y.begin(), y.end());
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It1, typename It2>
  inline void multiply(It1 begin1, It1 end1, It2 begin2, It2 end2)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "Binary multiply: Invalid range";
      NTA_ASSERT(end1 - begin1 <= end2 - begin2)
        << "Binary multiply: Incompatible ranges";
    }

    for (; begin1 != end1; ++begin1, ++begin2)
      *begin1 *= *begin2;
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename T1, typename T2>
  inline void multiply(T1& x, const T2& y)
  {
    multiply(x.begin(), x.end(), y.begin(), y.end());
  }

  //--------------------------------------------------------------------------------
  template <typename It1, typename It2, typename It3>
  inline void multiply(It1 begin1, It1 end1, It2 begin2, It2 end2,
                       It3 begin3, It3 end3)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "Ternary multiply: Invalid range";
      NTA_ASSERT(end1 - begin1 <= end2 - begin2)
        << "Ternary multiply: Incompatible input ranges";
      NTA_ASSERT(end1 - begin1 <= end3 - begin3)
        << "Ternary multiply: Not enough memory for result";
    }

    typedef typename std::iterator_traits<It3>::value_type value_type;

    for (; begin1 != end1; ++begin1, ++begin2, ++begin3)
      *begin3 = (value_type) *begin1 * *begin2;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2, typename T3>
  inline void multiply(const T1& x, const T2& y, T3& z)
  {
    multiply(x.begin(), x.end(), y.begin(), y.end(), z.begin(), z.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * Given a vector of pairs <index, value> and a value val, multiplies the values
   * by val, but only if index is in indices. Needs x and indices to be sorted
   * in order of increasing indices.
   */
  template <typename I, typename T>
  inline void 
  multiply_val(T val, const Buffer<I>& indices, SparseVector<I,T>& x)
  {
    I n1 = indices.nnz, n2 = x.nnz, i1 = 0, i2 =0;

    while (i1 != n1 && i2 != n2)
      if (x[i2].first < indices[i1]) {
        ++i2;
      } else if (indices[i1] < x[i2].first) {
        ++i1;
      } else {
        x[i2].second *= val;
        ++i1; ++i2;
      }
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It1, typename It2>
  inline void divide(It1 begin1, It1 end1, It2 begin2, It2 end2,
                     typename std::iterator_traits<It1>::value_type fuzz =0)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "divide: Invalid range";
      NTA_ASSERT(end1 - begin1 <= end2 - begin2)
        << "divide: Incompatible ranges";
    }

    if (fuzz == 0)
      for (; begin1 != end1; ++begin1, ++begin2)
        *begin1 /= *begin2;
    else
      for (; begin1 != end1; ++begin1, ++begin2)
        *begin1 /= (*begin2 + fuzz);
  }

  //--------------------------------------------------------------------------------
  // What if y contains one or more zeros?
  /**
   */
  template <typename T1, typename T2>
  inline void divide(T1& x, const T2& y, typename T1::value_type fuzz =0)
  {
    divide(x.begin(), x.end(), y.begin(), y.end(), fuzz);
  }

  //--------------------------------------------------------------------------------
  template <typename It1>
  inline void divide_by_max(It1 begin, It1 end)
  {
    {
      NTA_ASSERT(begin <= end)
        << "divide_by_max: Invalid range";
    }

    typename std::iterator_traits<It1>::value_type max_val =
      *(std::max_element(begin, end));

    if (!nta::nearlyZero(max_val))
      for (It1 it = begin; it != end; ++it)
        *it /= max_val;
  }

  //--------------------------------------------------------------------------------
  template <typename T1>
  inline void divide_by_max(T1& v)
  {
    divide_by_max(v.begin(), v.end());
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename It1, typename It2, typename TFuncIsNearlyZero, typename TFuncHandleZero>
  inline void inverseNZ(It1 begin1, It1 end1, It2 out, It2 out_end,
                        TFuncIsNearlyZero fIsZero, TFuncHandleZero fHandleZero)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "inverseNZ: Invalid input range";
      NTA_ASSERT(out <= out_end)
        << "inverseNZ: Invalid output range";
      NTA_ASSERT(end1 - begin1 == out_end - out)
        << "inverseNZ: Incompatible ranges";
    }

    const typename std::iterator_traits<It2>::value_type one(1.0);

    for (; begin1 != end1; ++begin1, ++out) {
      if(fIsZero(*begin1))
        *out = fHandleZero(*begin1); // Can't pass one?
      else
        *out = one / *begin1;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Computes the reciprocal of each element of vector 'x' and writes
   * result into vector 'out'.
   * 'out' must be of at least the size of 'x'.
   * Does not resize 'out'; behavior is undefined if 'out' is not of
   * the correct size.
   * Uses only 'value_type', 'begin()' and 'end()' of 'x' and
   * 'value_type' and 'begin()' of 'out'.
   * Checks the value of each element of 'x' with 'fIsNearlyZero', and
   * if 'fIsNearlyZero' returns false, computes the reciprocal as
   * T2::value_type(1.0) / element value.
   * If 'fIsNearlyZero' returns true, computes uses the output of
   * 'fHandleZero(element value)' as the result for that element.
   *
   * Usage: nta::inverseNZ(input, output,
   *            nta::IsNearlyZero< DistanceToZero<double> >(),
   *            nta::Identity<double>());
   */
  template <typename T1, typename T2, typename TFuncIsNearlyZero, typename TFuncHandleZero>
  inline void inverseNZ(const T1& x, T2 &out,
                        TFuncIsNearlyZero fIsNearlyZero, TFuncHandleZero fHandleZero)
  {
    inverseNZ(x.begin(), x.end(), out.begin(), out.end(), fIsNearlyZero, fHandleZero);
  }

  //--------------------------------------------------------------------------------
  template <typename It1, typename It2>
  inline void inverse(It1 begin1, It1 end1, It2 out, It2 out_end,
                      const typename std::iterator_traits<It2>::value_type one =1.0)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "inverse: Invalid input range";
      NTA_ASSERT(out <= out_end)
        << "inverse: Invalid output range";
      NTA_ASSERT(end1 - begin1 == out_end - out)
        << "inverse: Incompatible ranges";
    }

    for (; begin1 != end1; ++begin1, ++out)
      *out = one / *begin1;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline void inverse(const T1& x, T2 &out, const typename T2::value_type one=1.0)
  {
    inverse(x.begin(), x.end(), out.begin(), out.end(), one);
  }

  //--------------------------------------------------------------------------------
  /**
   * x += k y
   */
  template <typename It1, typename It2>
  inline void add_ky(const typename std::iterator_traits<It1>::value_type& k,
                     It1 y, It1 y_end, It2 x, It2 x_end)
  {
    {
      NTA_ASSERT(y <= y_end)
        << "add_ky: Invalid y range";
      NTA_ASSERT(x <= x_end)
        << "add_ky: Invalid x range";
      NTA_ASSERT(y_end - y <= x - x_end)
        << "add_ky: Result range too small";
    }

    while (y != y_end) {
      *x += k * *y;
      ++x; ++y;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename T1, typename T2>
  inline void add_ky(const typename T1::value_type& k, const T2& y, T1& x)
  {
    add_ky(k, y.begin(), y.end(), x.begin(), x.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * x2 = x1 + k y
   */
  template <typename It1, typename It2, typename It3>
  inline void add_ky(It1 x1, It1 x1_end,
                     const typename std::iterator_traits<It1>::value_type& k,
                     It2 y, It3 x2)
  {
    while (x1 != x1_end) {
      *x2 = *x1 + k * *y;
      ++x2; ++x1; ++y;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename T1, typename T2, typename T3>
  inline void add_ky(const T1& x1,
                     const typename T1::value_type& k, const T2& y,
                     T3& x2)
  {
    ////assert(y.size() >= x.size());

    add_ky(x1.begin(), x1.end(), k, y.begin(), x2.begin());
  }

  // TODO: write binary operations x = y + z ...

  //--------------------------------------------------------------------------------
  /**
   * x = a * x + y
   *
   * TODO: write the rest of BLAS level 1
   */
  template <typename T1, typename T2>
  inline void axpy(T1& x, const typename T1::value_type& a, const T2& y)
  {
    ////assert(y.size() >= x.size());

    typename T1::iterator it_x = x.begin(), it_x_end = x.end();
    typename T2::const_iterator it_y = y.begin();

    while (it_x != it_x_end) {
      *it_x = a * *it_x + *it_y;
      ++it_x; ++it_y;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * x = a * x + b * y
   */
  template <typename X, typename Y>
  inline void axby(const typename std::iterator_traits<X>::value_type& a,
                   X x, X x_end,
                   const typename std::iterator_traits<X>::value_type& b,
                   Y y)
  {
    while (x != x_end) {
      *x = a * *x + b * *y;
      ++x; ++y;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename T1, typename T2>
  inline void axby(const typename T1::value_type& a, T1& x,
                   const typename T1::value_type& b, const T2& y)
  {
    ////assert(y.size() >= x.size());

    axby(a, x.begin(), x.end(), b, y.begin());
  }

  //--------------------------------------------------------------------------------
  /**
   * exp(k * x) for all the elements of a range.
   */
  template <typename It>
  inline void range_exp(typename std::iterator_traits<It>::value_type k,
                        It begin, It end)
  {
    typedef typename std::iterator_traits<It>::value_type value_type;

    Exp<value_type> e_f;

    for (; begin != end; ++begin)
      *begin = e_f(k * *begin);
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename C>
  inline void range_exp(typename C::value_type k, C& c)
  {
    range_exp(k, c.begin(), c.end());
  }

  //--------------------------------------------------------------------------------
  /**
   * k1 * exp(k2 * x) for all the elements of a range.
   */
  template <typename It>
  inline void range_exp(typename std::iterator_traits<It>::value_type k1,
                        typename std::iterator_traits<It>::value_type k2,
                        It begin, It end)
  {
    typedef typename std::iterator_traits<It>::value_type value_type;

    Exp<value_type> e_f;

    for (; begin != end; ++begin)
      *begin = k1 * e_f(k2 * *begin);
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename C>
  inline void range_exp(typename C::value_type k1, typename C::value_type k2, C& c)
  {
    range_exp(k1, k2, c.begin(), c.end());
  }

  //--------------------------------------------------------------------------------
  // Inner product
  //--------------------------------------------------------------------------------
  /**
   * Bypasses the STL API and its init value.
   * TODO: when range is empty??
   */
  template <typename It1, typename It2>
  inline typename std::iterator_traits<It1>::value_type
  inner_product(It1 it_x, It1 it_x_end, It2 it_y)
  {
    typename std::iterator_traits<It1>::value_type n(0);

    while (it_x != it_x_end) {
      n += *it_x * *it_y;
      ++it_x; ++it_y;
    }

    return n;
  }

  //--------------------------------------------------------------------------------
  /**
   * In place transform of a range.
   */
  template <typename F1, typename It>
  inline void transform(It begin, It end, F1 f)
  {
    {
      NTA_ASSERT(begin <= end)
        << "transform: Invalid range";
    }

    for (; begin != end; ++begin)
      *begin = f(*begin);
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename F1, typename T1>
  inline void transform(T1& a, F1 f)
  {
    typename T1::iterator ia = a.begin(), iae = a.end();

    for (; ia != iae; ++ia)
      *ia = f(*ia);
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename F1, typename T1, typename T2>
  inline void transform(const T1& a, T2& b, F1 f)
  {
    ////assert(b.size() >= a.size());

    typename T1::const_iterator ia = a.begin(), iae = a.end();
    typename T2::iterator ib = b.begin();

    for (; ia != iae; ++ia, ++ib)
      *ib = f(*ia);
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename F2, typename T1, typename T2, typename T3>
  inline void transform(const T1& a, const T2& b, T3& c, F2 f)
  {
    ////assert(c.size() >= a.size());
    ////assert(b.size() >= a.size());
    ////assert(c.size() >= b.size());

    typename T1::const_iterator ia = a.begin(), iae = a.end();
    typename T2::const_iterator ib = b.begin();
    typename T3::iterator ic = c.begin();

    for (; ia != iae; ++ia, ++ib, ++ic)
      *ic = f(*ia, *ib);
  }

  //--------------------------------------------------------------------------------
  /**
   */
  template <typename F3, typename T1, typename T2, typename T3, typename T4>
  inline void transform(const T1& a, const T2& b, const T3& c, T4& d, F3 f)
  {
    ////assert(d.size() >= a.size());
    ////assert(d.size() >= b.size());
    ////assert(d.size() >= c.size());
    ////assert(b.size() >= a.size());
    ////assert(c.size() >= a.size());

    typename T1::const_iterator ia = a.begin(), iae = a.end();
    typename T2::const_iterator ib = b.begin();
    typename T3::const_iterator ic = c.begin();
    typename T4::iterator id = d.begin();

    for (; ia != iae; ++ia, ++ib, ++ic, ++id)
      *id = f(*ia, *ib, *ic);
  }

  //--------------------------------------------------------------------------------
  // min_element / max_element
  //--------------------------------------------------------------------------------
  /**
   * Returns the position at which f takes its minimum between first and last.
   */
  template <typename ForwardIterator, typename F>
  inline ForwardIterator
  min_element(ForwardIterator first, ForwardIterator last, F f)
  {
    {
      NTA_ASSERT(first <= last)
        << "min_element: Invalid range";
    }

    typedef typename ForwardIterator::value_type value_type;

    ForwardIterator min_it = first;
    value_type min_val = f(*first);

    while (first != last) {
      value_type val = f(*first);
      if (val < min_val) {
        min_it = first;
        min_val = val;
      }
      ++first;
    }

    return min_it;
  }

  //--------------------------------------------------------------------------------
  /**
   * Returns the position at which f takes its maximum between first and last.
   */
  template <typename ForwardIterator, typename F>
  inline ForwardIterator
  max_element(ForwardIterator first, ForwardIterator last, F f)
  {
    {
      NTA_ASSERT(first <= last)
        << "max_element: Invalid range";
    }

    typedef typename ForwardIterator::value_type value_type;

    ForwardIterator max_it = first;
    value_type max_val = f(*first);

    while (first != last) {
      value_type val = f(*first);
      if (val > max_val) {
        max_it = first;
        max_val = val;
      }
      ++first;
    }

    return max_it;
  }

  //--------------------------------------------------------------------------------
  /**
   * Finds the min element in a container.
   */
  template <typename C>
  inline size_t min_element(const C& c)
  {
    if (c.empty())
      return (size_t) 0;
    else
      return (size_t) (std::min_element(c.begin(), c.end()) - c.begin());
  }

  //--------------------------------------------------------------------------------
  /**
   * Finds the maximum element in a container.
   */
  template <typename C>
  inline size_t max_element(const C& c)
  {
    if (c.empty())
      return (size_t) 0;
    else
      return (size_t) (std::max_element(c.begin(), c.end()) - c.begin());
  }

  //--------------------------------------------------------------------------------
  /**
   * Writes the component-wise minimum to the output vector.
   */
  template <typename It1, typename It2, typename It3>
  inline void minimum(It1 begin1, It1 end1, It2 begin2, It3 out)
  {
    {
      NTA_ASSERT(begin1 <= end1)
        << "minimum: Invalid range";
    }

    typedef typename std::iterator_traits<It3>::value_type T;
    for(; begin1!=end1; ++begin1, ++begin2, ++out) {
      *out = std::min<T>(*begin1, *begin2);
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Writes the component-wise minimum to the output vector.
   */
  template <typename T1, typename T2, typename T3>
  inline void minimum(const T1 &x, const T2 &y, T3 &out)
  {
    minimum(x.begin(), x.end(), y.begin(), out.begin());
  }

  //--------------------------------------------------------------------------------
  // contains
  //--------------------------------------------------------------------------------
  template <typename C>
  inline bool contains(const C& c, typename C::value_type& v)
  {
    return std::find(c.begin(), c.end(), v) != c.end();
  }

  //--------------------------------------------------------------------------------
  template <typename C1, typename C2>
  inline bool is_subsequence(const C1& seq, const C2& sub)
  {
    return std::search(seq.begin(), seq.end(), sub.begin(), sub.end()) != seq.end();
  }

  //--------------------------------------------------------------------------------
  template <typename C1, typename C2>
  inline bool is_subsequence_of(const C1& c, const C2& sub)
  {
    bool found = false;
    typename C1::const_iterator it, end = c.end();
    for (it = c.begin(); it != end; ++it)
      if (is_subsequence(*it, sub))
        found = true;
    return found;
  }

  //--------------------------------------------------------------------------------
  // sample
  //--------------------------------------------------------------------------------
  /**
   * Sample n times from a given pdf.
   */
  template <typename It1, typename It2, typename RNG>
  inline void sample(size_t n, It1 pdf_begin, It1 pdf_end, It2 output, RNG& rng)
  {
    {
      NTA_ASSERT(pdf_begin <= pdf_end)
        << "sample: Invalid range for pdf";
    }

    typedef typename std::iterator_traits<It1>::value_type value_type;
    typedef typename std::iterator_traits<It2>::value_type size_type2;

    size_t size = (size_t) (pdf_end - pdf_begin);
    std::vector<double> cdf(size, 0);
    std::vector<double>::const_iterator it = cdf.begin();
    cumulative(pdf_begin, pdf_end, cdf.begin(), cdf.end());
    double m = cdf[size-1];

    for (size_t i = 0; i != n; ++i, ++output) {
      double p = m * double(rng()) / double(rng.max() - rng.min());
      it = std::lower_bound(cdf.begin(), cdf.end(), p);
      *output = (size_type2) (it - cdf.begin());
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Sample n times from a given pdf.
   */
  template <typename It1, typename It2>
  inline void sample(size_t n, It1 pdf_begin, It1 pdf_end, It2 output)
  {
    {
      NTA_ASSERT(pdf_begin <= pdf_end)
        << "sample: Invalid range for pdf";
    }

    nta::Random rng;
    sample(n, pdf_begin, pdf_end, output, rng);
  }

  //--------------------------------------------------------------------------------
  /**
   * Sample one time from a given pdf.
   */
  template <typename C1>
  inline size_t sample_one(const C1& pdf)
  {
    size_t c = 0;
    sample(1, pdf.begin(), pdf.end(), &c);
    return c;
  }

  //--------------------------------------------------------------------------------
  template <typename C1, typename RNG>
  inline size_t sample_one(const C1& pdf, RNG& rng)
  {
    size_t c = 0;
    sample(1, pdf.begin(), pdf.end(), &c, rng);
    return c;
  }

  //--------------------------------------------------------------------------------
  // DENSE LOGICAL AND/OR
  //-------------------------------------------------------------------------------- 
  /**
   * For each corresponding elements of x and y, put the logical and of those two
   * elements at the corresponding position in z. This is faster than the numpy
   * logical_and, which doesn't seem to be using SSE.
   *
   * x, y and z are arrays of floats, but with 0/1 values.
   *
   * If any of the vectors is not aligned on a 16 bytes boundary, the function
   * reverts to slow C++. This can happen when using it with slices of numpy
   * arrays.
   *
   * Doesn't work on 64 bits platforms, doesn't work on win32.
   *
   * TODO: find 16 bytes aligned block that can be sent to SSE.
   * TODO: support other platforms than just darwin86 for the fast path.
   */
  template <typename InputIterator, typename OutputIterator>
  inline void logical_and(InputIterator x, InputIterator x_end,
                          InputIterator y, InputIterator y_end,
                          OutputIterator z, OutputIterator z_end)
  {
    {
      NTA_ASSERT(x_end - x == y_end - y);
      NTA_ASSERT(x_end - x == z_end - z);
    }

    // See comments in count_gt. We need both conditional compilation and 
    // SSE_LEVEL check.
#ifdef NTA_PLATFORM_darwin86

    if (SSE_LEVEL >= 3) {

      // n is the total number of floats to process
      // n1 is 0 if any of the arrays x,y,z is not aligned on a 4 bytes
      // boundary, or the number of floats we'll be able to process in parallel
      // using the xmm.
      int n = (int)(x_end - x);
      int n1 = 0;
      if (((long)x) % 16 == 0 && ((long)y) % 16 == 0 && ((long)z) % 16 == 0)
        n1 = 16 * (n / 16);
    
      // If we are not aligned on 4 bytes, n1 == 0, and we simply
      // skip the asm. 
      if (n1 > 0) { 

        asm volatile(
                     "pusha\n\t"                   // save all registers
                 
                     "0:\n\t"
                     "movaps (%%esi), %%xmm0\n\t"  // move 4 floats of x to xmm0
                     "andps (%%edi), %%xmm0\n\t"   // parallel and with 4 floats of y
                     "movaps 16(%%esi), %%xmm1\n\t"// play again with next 4 floats
                     "andps 16(%%edi), %%xmm1\n\t"
                     "movaps 32(%%esi), %%xmm2\n\t"// and next 4 floats
                     "andps 32(%%edi), %%xmm2\n\t"
                     "movaps 48(%%esi), %%xmm3\n\t"// and next 4 floats: we've and'ed
                     "andps 48(%%edi), %%xmm3\n\t" // 16 floats of x and y at this point

                     "movaps %%xmm0, (%%ecx)\n\t"  // simply move 4 floats at a time to z
                     "movaps %%xmm1, 16(%%ecx)\n\t"// and next 4 floats
                     "movaps %%xmm2, 32(%%ecx)\n\t"// and next 4 floats
                     "movaps %%xmm3, 48(%%ecx)\n\t"// and next 4: moved 16 floats to z
                 
                     "addl $64, %%esi\n\t"         // increment pointer into x by 16 floats
                     "addl $64, %%edi\n\t"         // increment pointer into y
                     "addl $64, %%ecx\n\t"         // increment pointer into z
                     "subl $16, %%edx\n\t"         // we've processed 16 floats
                     "ja 0b\n\t"                   // loop
                 
                     "popa\n\t"                    // restore registers
               
                     : 
                     : "S" (x), "D" (y), "c" (z), "d" (n1)
                     : 
                     );
      }

      // Finish up for stragglers in case the array length was not 
      // evenly divisible by 4
      for (int i = n1; i != n; ++i)
        *(z+i) = *(x+i) && *(y+i);

    } else {
    
      for (; x != x_end; ++x, ++y, ++z)
        *z = (*x) && (*y);

    }
#else
    for (; x != x_end; ++x, ++y, ++z)
      *z = (*x) && (*y);
#endif
  }

  //--------------------------------------------------------------------------------
  /**
   * Same as previous logical_and, but puts the result back into y.
   * Same comments.
   */
  template <typename Iterator>
  inline void in_place_logical_and(Iterator x, Iterator x_end,
                                   Iterator y, Iterator y_end)
  {
    {
      NTA_ASSERT(x_end - x == y_end - y);
    }

    // See comments in count_gt. We need conditional compilation
    // _AND_ SSE_LEVEL check.
#ifdef NTA_PLATFORM_darwin86

    if (SSE_LEVEL >= 3) {

      // See comments in logical_and.
      int n = (int)(x_end - x);
      int n1 = 0;
      if (((long)x) % 16 == 0 && ((long)y) % 16 == 0)
        n1 = 16 * (n / 16);
    
      if (n1 > 0) {

        asm volatile(
                     "pusha\n\t"
                 
                     "0:\n\t"
                     "movaps (%%esi), %%xmm0\n\t"
                     "movaps 16(%%esi), %%xmm1\n\t"
                     "movaps 32(%%esi), %%xmm2\n\t"
                     "movaps 48(%%esi), %%xmm3\n\t"
                     "andps (%%edi), %%xmm0\n\t"
                     "andps 16(%%edi), %%xmm1\n\t"
                     "andps 32(%%edi), %%xmm2\n\t"
                     "andps 48(%%edi), %%xmm3\n\t"
                     "movaps %%xmm0, (%%edi)\n\t"
                     "movaps %%xmm1, 16(%%edi)\n\t"
                     "movaps %%xmm2, 32(%%edi)\n\t"
                     "movaps %%xmm3, 48(%%edi)\n\t"

                     "addl $64, %%esi\n\t"
                     "addl $64, %%edi\n\t"
                     "subl $16, %%edx\n\t"
                     "prefetch (%%esi)\n\t"                 
                     "ja 0b\n\t"
                 
                     "popa\n\t"
               
                     : 
                     : "S" (x), "D" (y), "d" (n1)
                     : 
                     );
      }

      for (int i = n1; i != n; ++i)
        *(y+i) = *(x+i) && *(y+i);

    } else {
    
      for (; x != x_end; ++x, ++y)
        *y = (*x) && *(y);
    }
#else
    for (; x != x_end; ++x, ++y)
      *y = (*x) && *(y);
#endif
  }

  //--------------------------------------------------------------------------------
  /**
   * A specialization tuned for unsigned char. 
   * TODO: keep only one code that computes the right offsets based on 
   * the iterator value type?
   * TODO: vectorize, but watch out for alignments
   */
  inline void in_place_logical_and(const ByteVector& x, ByteVector& y,
                                   int begin =-1, int end =-1)
  {
    if (begin == -1)
      begin = 0;

    if (end == -1)
      end = (int) x.size();

    for (int i = begin; i != end; ++i)
      y[i] &= x[i];
  }

  //--------------------------------------------------------------------------------
  /**
   * TODO: write with SSE for big enough vectors.
   */
  inline void in_place_logical_or(const ByteVector& x, ByteVector& y,
                                  int begin =-1, int end =-1)
  {
    if (begin == -1)
      begin = 0;

    if (end == -1)
      end = (int) x.size();

    for (int i = begin; i != end; ++i)
      y[i] |= x[i];
  }

  //--------------------------------------------------------------------------------
  inline void 
  logical_or(size_t n, const ByteVector& x, const ByteVector& y, ByteVector& z)
  {
    for (size_t i = 0; i != n; ++i)
      z[i] = x[i] || y[i];
  }

  //--------------------------------------------------------------------------------
  inline void in_place_logical_or(size_t n, const ByteVector& x, ByteVector& y)
  {
    for (size_t i = 0; i != n; ++i)
      y[i] |= x[i];
  }

  //--------------------------------------------------------------------------------
  // SPARSE OR/AND
  //--------------------------------------------------------------------------------
  template <typename InputIterator1, typename InputIterator2, typename OutputIterator>
  inline size_t sparseOr(size_t n,
                         InputIterator1 begin1, InputIterator1 end1,
                         InputIterator2 begin2, InputIterator2 end2,
                         OutputIterator out, OutputIterator out_end)
  {
    { // Pre-conditions
      NTA_ASSERT(0 <= end1 - begin1)
        << "sparseOr: Mismatched iterators for first vector";
      NTA_ASSERT(0 <= end2 - begin2)
        << "sparseOr: Mismatched iterators for second vector";
      NTA_ASSERT(0 <= out_end - out)
        << "sparseOr: Mismatched iterators for output vector";
      NTA_ASSERT(0 <= n)
        << "sparseOr: Invalid max size: " << n;
      NTA_ASSERT((size_t)(end1 - begin1) <= n)
        << "sparseOr: Invalid first vector size";
      NTA_ASSERT((size_t)(end2 - begin2) <= n)
        << "sparseOr: Invalid second vector size";
      NTA_ASSERT(n <= (size_t)(out_end - out))
        << "sparseOr: Insufficient memory for result";
      for (int i = 0; i < (int)(end1 - begin1); ++i)
        NTA_ASSERT(/*0 <= *(begin1 + i) &&*/ *(begin1 + i) < n)
          << "sparseOr: Invalid index in first vector: " << *(begin1 + i);
      for (int i = 1; i < (int)(end1 - begin1); ++i)
        NTA_ASSERT(*(begin1 + i - 1) < *(begin1 + i))
          << "sparseOr: Indices need to be in strictly increasing order"
          << " (first vector)";
      for (int i = 0; i < (int)(end2 - begin2); ++i)
        NTA_ASSERT(/*0 <= *(begin2 + i) &&*/ *(begin2 + i) < n)
          << "sparseOr: Invalid index in second vector: " << *(begin2 + i);
      for (int i = 1; i < (int)(end2 - begin2); ++i)
        NTA_ASSERT(*(begin2 + i - 1) < *(begin2 + i))
          << "sparseOr: Indices need to be in strictly increasing order"
          << " (second vector)";
    } // End pre-conditions

    typedef typename std::iterator_traits<OutputIterator>::value_type value_type;

    OutputIterator out_begin = out;

    while (begin1 != end1 && begin2 != end2) {

      if (*begin1 < *begin2) {
        *out++ = (value_type) *begin1++;
      } else if (*begin2 < *begin1) {
        *out++ = (value_type) *begin2++;
      } else {
        *out++ = (value_type) *begin1++;
        ++begin2;
      }
    }

    for (; begin1 != end1; ++begin1)
      *out++ = (value_type) *begin1;

    for (; begin2 != end2; ++begin2)
      *out++ = (value_type) *begin2;

    return (size_t)(out - out_begin);
  }

  //--------------------------------------------------------------------------------
  template <typename U>
  inline size_t sparseOr(size_t n,
                         const std::vector<U>& x1, const std::vector<U>& x2,
                         std::vector<U>& out)
  {
    return sparseOr(n, x1.begin(), x1.end(), x2.begin(), x2.end(),
                    out.begin(), out.end());
  }

  //--------------------------------------------------------------------------------
  template <typename InputIterator1, typename InputIterator2, typename OutputIterator>
  inline size_t sparseAnd(size_t n,
                          InputIterator1 begin1, InputIterator1 end1,
                          InputIterator2 begin2, InputIterator2 end2,
                          OutputIterator out, OutputIterator out_end)
  {
    { // Pre-conditions
      NTA_ASSERT(0 <= end1 - begin1)
        << "sparseAnd: Mismatched iterators for first vector";
      NTA_ASSERT(0 <= end2 - begin2)
        << "sparseAnd: Mismatched iterators for second vector";
      NTA_ASSERT(0 <= out_end - out)
        << "sparseAnd: Mismatched iterators for output vector";
      NTA_ASSERT(0 <= n)
        << "sparseAnd: Invalid max size: " << n;
      NTA_ASSERT((size_t)(end1 - begin1) <= n)
        << "sparseAnd: Invalid first vector size";
      NTA_ASSERT((size_t)(end2 - begin2) <= n)
        << "sparseAnd: Invalid second vector size";
      //NTA_ASSERT(n <= (size_t)(out_end - out))
      //<< "sparseAnd: Insufficient memory for result";
      for (int i = 0; i < (int)(end1 - begin1); ++i)
        NTA_ASSERT(/*0 <= *(begin1 + i) &&*/ *(begin1 + i) < n)
          << "sparseAnd: Invalid index in first vector: " << *(begin1 + i);
      for (int i = 1; i < (int)(end1 - begin1); ++i)
        NTA_ASSERT(*(begin1 + i - 1) < *(begin1 + i))
          << "sparseAnd: Indices need to be in strictly increasing order"
          << " (first vector)";
      for (int i = 0; i < (int)(end2 - begin2); ++i)
        NTA_ASSERT(/*0 <= *(begin2 + i) &&*/ *(begin2 + i) < n)
          << "sparseAnd: Invalid index in second vector: " << *(begin2 + i);
      for (int i = 1; i < (int)(end2 - begin2); ++i)
        NTA_ASSERT(*(begin2 + i - 1) < *(begin2 + i))
          << "sparseAnd: Indices need to be in strictly increasing order"
          << " (second vector)";
    } // End pre-conditions

    typedef typename std::iterator_traits<OutputIterator>::value_type value_type;

    OutputIterator out_begin = out;

    while (begin1 != end1 && begin2 != end2) {

      if (*begin1 < *begin2) {
        ++begin1;
      } else if (*begin2 < *begin1) {
        ++begin2;
      } else {
        *out++ = (value_type) *begin1++;
        ++begin2;
      }
    }

    return (size_t)(out - out_begin);
  }

  //--------------------------------------------------------------------------------
  template <typename U>
  inline size_t sparseAnd(size_t n,
                          const std::vector<U>& x1, const std::vector<U>& x2,
                          std::vector<U>& out)
  {
    return sparseAnd(n, x1.begin(), x1.end(), x2.begin(), x2.end(),
                     out.begin(), out.end());
  }

  //--------------------------------------------------------------------------------
  // SORTING
  //--------------------------------------------------------------------------------

  //--------------------------------------------------------------------------------
  template <typename C>
  inline void sort(C& c)
  {
    std::sort(c.begin(), c.end());
  }

  //--------------------------------------------------------------------------------
  template <typename C, typename F>
  inline void sort(C& c, F f)
  {
    std::sort(c.begin(), c.end(), f);
  }

  //--------------------------------------------------------------------------------
  template <typename It>
  inline void sort_on_first(It x_begin, It x_end, int direction =1)
  {
    typedef typename std::iterator_traits<It>::value_type P;
    typedef typename P::first_type I;
    typedef typename P::second_type F;

    typedef select1st<std::pair<I,F> > sel1st;
    
    if (direction == -1) {
      std::sort(x_begin, x_end, predicate_compose<std::greater<I>, sel1st>());
    } else {
      std::sort(x_begin, x_end, predicate_compose<std::less<I>, sel1st>());
    }
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename F>
  inline void sort_on_first(size_t n, std::vector<std::pair<I,F> >& x, 
                            int direction =1)
  {
    sort_on_first(x.begin(), x.begin() + n, direction);
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename F>
  inline void sort_on_first(std::vector<std::pair<I,F> >& x, int direction =1)
  {
    sort_on_first(x.begin(), x.end(), direction);
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename F>
  inline void sort_on_first(SparseVector<I,F>& x, int direction =1)
  {
    sort_on_first(x.begin(), x.begin() + x.nnz, direction);
  }

  //--------------------------------------------------------------------------------
  /**
   * Partial sort of a container given a functor.
   */
  template <typename I, typename C, typename F>
  inline void partial_sort(I k, C& elts, F f)
  {
    std::partial_sort(elts.begin(), elts.begin() + k, elts.end(), f);
  }

  //--------------------------------------------------------------------------------
  /**
   * Partial sort of a range, that returns the values and the indices.
   */
  template <typename size_type,
            typename InputIterator,
            typename OutputIterator,
            typename Order>
  inline void
  partial_sort_2nd(size_type k, 
                   InputIterator in_begin, InputIterator in_end,
                   OutputIterator out_begin, Order)
  {
    typedef typename std::iterator_traits<InputIterator>::value_type value_type;
    typedef select2nd<std::pair<size_type, value_type> > sel2nd;

    std::vector<std::pair<size_type, value_type> > v(in_end - in_begin);

    for (size_type i = 0; in_begin != in_end; ++in_begin, ++i)
      v[i] = std::make_pair(i, *in_begin);

    std::partial_sort(v.begin(), v.begin() + k, v.end(),
                      predicate_compose<Order, sel2nd>());

    for (size_type i = 0; i != k; ++i, ++out_begin)
      *out_begin = v[i];
  }

  //--------------------------------------------------------------------------------
  /**
   * Partial sort of a container.
   */
  template <typename C1, typename OutputIterator, typename Order>
  inline void
  partial_sort_2nd(size_t k, const C1& c1, OutputIterator out_begin, Order order)
  {
    partial_sort_2nd(k, c1.begin(), c1.end(), out_begin, order);
  }

  //--------------------------------------------------------------------------------
  /**
   * Partial sort of a range of vectors, based on a given order predicate for
   * the vectors, putting the result into two iterators,
   * one for the indices and one for the element values.
   * Order needs to work for pairs (i.e., is a binary predicate).
   * start_offset specifies an optional for the indices that will be generated
   * for the pairs. This is useful when calling partial_sort_2nd repetitively
   * for different ranges inside a larger range.
   * If resort_on_first is true, the indices of the pairs are resorted,
   * otherwise, the indices might come out in any order.
   */
  template <typename size_type,
            typename InIter,
            typename OutputIterator1,
            typename OutputIterator2,
            typename Order>
  inline void
  partial_sort(size_type k, InIter in_begin, InIter in_end,
               OutputIterator1 ind, OutputIterator2 nz,
               Order order, size_type start_offset =0,
               bool resort_on_first =false)
  {
    typedef typename std::iterator_traits<InIter>::value_type value_type;
    typedef select1st<std::pair<size_type, value_type> > sel1st;

    std::vector<std::pair<size_type, value_type> > v(in_end - in_begin);

    for (size_type i = start_offset; in_begin != in_end; ++in_begin, ++i)
      v[i - start_offset] = std::make_pair(i, *in_begin);

    std::partial_sort(v.begin(), v.begin() + k, v.end(), order);

    if (resort_on_first) {
      std::sort(v.begin(), v.begin() + k,
                predicate_compose<std::less<size_type>, sel1st>());
    }

    for (size_type i = 0; i != k; ++i, ++ind, ++nz) {
      *ind = v[i].first;
      *nz = v[i].second;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * In place.
   */
  template <typename I0, typename I, typename T>
  inline void 
  partial_argsort(I0 k, SparseVector<I,T>& x, int direction =-1)
  {
    {
      NTA_ASSERT(0 < k);   
      NTA_ASSERT(k <= x.size());
      NTA_ASSERT(direction == -1 || direction == 1);
    }
    
    typedef I size_type;
    typedef T value_type;
    
    if (direction == -1) {
      
      greater_2nd_no_ties<size_type, value_type> order;
      std::partial_sort(x.begin(), x.begin() + k, x.begin() + x.nnz, order);

    } else if (direction == 1) {

      less_2nd<size_type, value_type> order;
      std::partial_sort(x.begin(), x.begin() + k, x.begin() + x.nnz, order);
    }
  }

  //--------------------------------------------------------------------------------
  // Static buffer for partial_argsort, so that we don't have to allocate
  // memory each time (faster).
  //--------------------------------------------------------------------------------
  static SparseVector<size_t, float> partial_argsort_buffer;

  //--------------------------------------------------------------------------------
  // A partial argsort that can use an already allocated buffer to avoid creating 
  // a data structure each time it's called. Assumes that the elements to be sorted
  // are nta::Real32, or at least that they have the same size.
  //
  // A partial sort is much faster than a full sort. The elements after the k first
  // in the result are not sorted, except that they are greater (or lesser) than
  // all the k first elements. If direction is -1, the sort is in decreasing order.
  // If direction is 1, the sort is in increasing order.
  //
  // The result is returned in the first k positions of the buffer for speed.
  // 
  // Uses a pre-allocated buffer to avoid allocating memory each time a sort
  // is needed.
  //--------------------------------------------------------------------------------
  template <typename InIter, typename OutIter>
  inline void partial_argsort(size_t k, InIter begin, InIter end,
                              OutIter sorted, OutIter sorted_end,
                              int direction =-1)
  {
    {
      NTA_ASSERT(0 < k);
      NTA_ASSERT(0 < end - begin);
      NTA_ASSERT(k <= (size_t)(end - begin));
      NTA_ASSERT(k <= (size_t)(sorted_end - sorted));
      NTA_ASSERT(direction == -1 || direction == 1);
    }

    typedef size_t size_type;
    typedef float value_type;

    SparseVector<size_type, value_type>& buff = partial_argsort_buffer;

    size_type n = (size_type)(end - begin);

    // Need to clean up, lest the next sort, with a possibly smaller range,
    // picks up values that are not in the current [begin,end).
    buff.resize(n);
    buff.nnz = n;

    InIter it = begin;

    for (size_type i = 0; i != n; ++i, ++it) {
      buff[i].first = i;
      buff[i].second = *it;
    }

    partial_argsort(k, buff, direction);
    
    for (size_type i = 0; i != k; ++i) 
      sorted[i] = buff[i].first;
  }

  //--------------------------------------------------------------------------------
  /**
   * Specialized partial argsort with selective random noise for breaking ties, to 
   * speed-up FDR C SP.
   */
  template <typename InIter, typename OutIter>
  inline void 
  partial_argsort_rnd_tie_break(size_t k, 
                                InIter begin, InIter end,
                                OutIter sorted, OutIter sorted_end,
                                Random& rng,
                                bool real_random =false)
  {
    {
      NTA_ASSERT(0 < k);
      NTA_ASSERT(0 < end - begin);
      NTA_ASSERT(k <= (size_t)(end - begin));
      NTA_ASSERT(k <= (size_t)(sorted_end - sorted));
    }

    typedef size_t size_type;
    typedef float value_type;

    SparseVector<size_type, value_type>& buff = partial_argsort_buffer;

    size_type n = (size_type)(end - begin);

    // Need to clean up, lest the next sort, with a possibly smaller range,
    // picks up values that are not in the current [begin,end).
    buff.resize(n);
    buff.nnz = n;

    InIter it = begin;

    for (size_type i = 0; i != n; ++i, ++it) {
      buff[i].first = i;
      buff[i].second = *it;
    }

    if (!real_random) {
      greater_2nd<size_type, value_type> order;
      std::partial_sort(buff.begin(), buff.begin() + k, buff.begin() + buff.nnz, order);
    } else {
      greater_2nd_rnd_ties<size_type, value_type, Random> order(rng);
      std::partial_sort(buff.begin(), buff.begin() + k, buff.begin() + buff.nnz, order);      
    }
    
    for (size_type i = 0; i != k; ++i) 
      sorted[i] = buff[i].first;
  }

  //--------------------------------------------------------------------------------
  // QUANTIZE
  //--------------------------------------------------------------------------------
  template <typename It1>
  inline void 
  update_with_indices_of_non_zeros(nta::UInt32 segment_size,
                                   It1 input_begin, It1 input_end,
                                   It1 prev_begin, It1 prev_end, 
                                   It1 curr_begin, It1 curr_end)
  {
    typedef nta::UInt32 size_type;
    typedef nta::Real32 value_type;
    
    size_type input_size = (size_type)(input_end - input_begin);

    std::fill(curr_begin, curr_end, 0);

    for (size_type i = 0; i != input_size; ++i) {

      if (*(input_begin + i) == 0)
        continue;

      size_type begin = i*segment_size;
      size_type end = begin + segment_size;
      bool all_zero = true;

      for (size_type j = begin; j != end; ++j) {

        if (*(prev_begin + j) > 0) {
          all_zero = false;
          *(curr_begin + j) = 1;
        }
      }

      if (all_zero) 
        std::fill(curr_begin + begin, curr_begin + end, 1);
    }
  }

  //--------------------------------------------------------------------------------
  // Winner takes all
  //--------------------------------------------------------------------------------
  /**
   * Finds the maximum in each interval defined by the boundaries, replaces that
   * maximum by a 1, and sets all the other values to 0. Returns the max value
   * over all intervals, and its position.
   */
  template <typename I, typename InIter, typename OutIter>
  inline void
  winnerTakesAll(const std::vector<I>& boundaries, InIter begin1, OutIter begin2)
  {
    typedef typename std::iterator_traits<InIter>::value_type value_type;

    I max_i = 0, size = (I) boundaries.size();
    value_type max_v = 0;

    for (I i = 0, k = 0; i < size; ++i) {
      max_v = 0;
      max_i = i == 0 ? 0 : boundaries[i-1];
      while (k < boundaries[i]) {
        if (*begin1 > max_v) {
          max_i = k;
          max_v = *begin1;
        }
        ++k;
        ++begin1;
      }
      *begin2 = (value_type) max_i;
      ++begin2;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * Winner takes all 2.
   */
  template <typename I, typename InIter, typename OutIter>
  std::pair<I, typename std::iterator_traits<InIter>::value_type>
  winnerTakesAll2(const std::vector<I>& boundaries, InIter begin1, OutIter begin2)
  {
    I max_i = 0;
    typedef typename std::iterator_traits<InIter>::value_type value_type;
    value_type max_v = 0;

    for (I i = 0, k = 0; i < boundaries.size(); ++i) {
      max_v = 0;
      max_i = i == 0 ? 0 : boundaries[i-1];
      while (k < boundaries[i]) {
        if (begin1[k] > max_v) {
          begin2[max_i] = 0;
          max_i = k;
          max_v = (value_type) (begin1[k]);
        } else {
          begin2[k] = 0;
        }
        ++k;
      }
      begin2[max_i] = 1;
    }
    return std::make_pair(max_i, max_v);
  }

  //--------------------------------------------------------------------------------
  /**
   * Keeps the values of k winners per segment, where each segment in [begin..end)
   * has length seg_size, and zeroes-out all the other elements.
   * Returns the indices and the values of the winners.
   * For zero segments, we randomly pick a winner, and output its index, with the
   * value zero.
   * If a segment has only zeros, randomly picks a winner.
   */
  template <typename I, typename InIter, typename OutIter1, typename OutIter2,
            typename RNG>
  inline void
  winnerTakesAll3(I k, I seg_size, InIter begin, InIter end,
                  OutIter1 ind, OutIter2 nz, RNG& rng)
  {
    typedef I size_type;
    typedef typename std::iterator_traits<InIter>::value_type value_type;

    { // Pre-conditions
      NTA_ASSERT(k > 0)
        << "winnerTakesAll3: Invalid k: " << k
        << " - Needs to be > 0";

      NTA_ASSERT(seg_size > 0)
        << "winnerTakesAll3: Invalid segment size: " << seg_size
        << " - Needs to be  > 0";

      NTA_ASSERT(k <= seg_size)
        << "winnerTakesAll3: Invalid k (" << k << ") or "
        << "segment size (" << seg_size << ")"
        << " - k needs to be <= seg_size";

      NTA_ASSERT((size_type) (end - begin) % seg_size == 0)
        << "winnerTakesAll3: Invalid input range of size: "
        << (size_type) (end - begin)
        << " - Needs to be integer multiple of segment size: "
        << seg_size;
    } // End pre-conditions

    typedef select2nd<std::pair<size_type, value_type> > sel2nd;

    InIter seg_begin = begin;
    size_type offset = (size_type) 0;

    for (; seg_begin != end; seg_begin += seg_size, offset += seg_size) {

      InIter seg_end = seg_begin + seg_size;
      size_type offset = (size_type) (seg_begin - begin);

      if (nearlyZeroRange(seg_begin, seg_end)) {

        std::vector<size_type> indices(seg_size);
        random_perm_interval(indices, offset, 1, rng);

        sort(indices.begin(), indices.begin() + k, std::less<size_type>());

        for (size_type i = 0; i != k ; ++i, ++ind, ++nz) {
          *ind = indices[i];
          *nz = (value_type) 0;
        }

      } else {

        partial_sort(k, seg_begin, seg_end, ind, nz,
                     predicate_compose<std::greater<value_type>, sel2nd>(),
                     offset, true);
      }
    }
  }

  //--------------------------------------------------------------------------------
  template <typename I, typename InIter, typename OutIter1, typename OutIter2>
  inline void
  winnerTakesAll3(I k, I seg_size, InIter begin, InIter end,
                  OutIter1 ind, OutIter2 nz)
  {
    nta::Random rng;
    winnerTakesAll3(k, seg_size, begin, end, ind, nz, rng);
  }

  //--------------------------------------------------------------------------------
  // Dendritic tree activation
  //
  // Given a window size, a threshold, an array of indices and a vector of values,
  // scans the vector of values with a sliding window on each row of the array of 
  // indices, and as soon as the activation in one window is above the threshold, 
  // declare that the corresponding line of the array of indices has "fired". Real
  // dendrites branch, but we are not modelling that here. Learning of the synapses,
  // i.e. populating the list of indices for each neuron, is not done here. Here,
  // we just compute which neurons fire in a collection of neurons, given the 
  // synaspes on the dendrites for each neuron. 
  //
  // The array of indices represents multiple neurons, one per row, and each row
  // represents multiple segments of the dendritic tree of each neuron. However,
  // the indices are not contiguous (a dendritic segment looks at random positions
  // in its input vector). As soon as the activation in any window in any segment
  // of the dendritic tree reaches the threshold, the neuron fires. Indices are added
  // to the list of indices for a given neuron in a specific order, tying position to 
  // to time of activation of the synapses: the farther away the synapses, the earlier
  // the signal was. 
  //
  // ncells and max_dendrite_size are the number of rows and columns, respectively,
  // of the indices matrix. If ncells is 10,000, max_dendrite_size would be,
  // typically, 100, meaning that a given neuron has synapses in its dendritic
  // tree with at most 100 other neurons. Those synapses are learnt, so during
  // learning, there are actually less than 100 synapses in the dendritic tree.
  // 
  // window_size is the size of the sliding window, i.e. the number of indices
  // we use to sum up activation in dendritic neighborhood. In biology, activation 
  // might be "superlinear" for synapses further down the dendrite. 
  // 
  // threshold is the value which, if reached in any given dendritic neighborhood,
  // triggers activation of the neuron.
  //
  // indices and indices_end are pointers to the start of the matrix of indices
  // and one past the last value in that matrix. This matrix represents synapses
  // that have been learnt between neurons. n_indices and n_indices_end describe
  // a vector that contains the number of indices in the dendritic tree of each
  // neuron. If ncells is 10,000, the values of the indices range from 0 to 9,999.
  //
  // input and input_end are a pointer to the vector of input, and one past the end
  // of that vector. That vector is of size ncells. The inputs are real valued. 
  //
  // output and output_end are a pointer to the vector of output, and one past the
  // end of that vector. That vector is of size ncells. That vector contains either
  // 0 if the corresponding neuron doesn't fire, or the real value of the activation.
  //
  // 'mode' controls which can of operation is performed. For now, mode can only be
  // 0, which performs a sum in the sliding window.
  //--------------------------------------------------------------------------------
  /*
  template <typename I, typename S, typename T>
  inline void 
  dendritic_activation(S nsegs, S max_dendrite_size,
                       S window_size, T threshold,
                       S* indices, S* indices_end,
                       S* n_indices, S* n_indices_end,
                       T* input, T* input_end,
                       I* output, I* output_end,
                       S mode =0)
  {
    typedef S size_type;
    typedef T value_type;

    { // Pre-conditions
      NTA_ASSERT(0 < nsegs);
      NTA_ASSERT(0 < max_dendrite_size);
      NTA_ASSERT(max_dendrite_size <= nsegs);
      NTA_ASSERT(0 < window_size);
      NTA_ASSERT(window_size <= max_dendrite_size);
      NTA_ASSERT(0 <= threshold);
      NTA_ASSERT((S)(indices_end - indices) == nsegs * max_dendrite_size);
      NTA_ASSERT((S)(n_indices_end - n_indices) == nsegs);
      NTA_ASSERT((S)(input_end - input) == nsegs);
      NTA_ASSERT((S)(output_end - output) == nsegs);
#ifdef NTA_ASSERTION_ON
      for (size_type c = 0; c != nsegs; ++c)
        NTA_ASSERT(n_indices[c] == 0 || window_size <= n_indices[c]);
#endif
    } // End pre-conditions
    
    for (size_type seg = 0; seg != nsegs; ++seg) {

      output[seg] = (int) -1;
    
      if (n_indices[seg] == 0) 
        continue;

      // w_end is how far we can move the window down the dendritic segment
      value_type activation = 0;
      size_type seg_start = seg*max_dendrite_size;
    
      for (size_type i = 0; i != window_size; ++i) 
        activation += input[indices[seg_start + i]];
    
      if (activation >= threshold) {

        output[seg] = (int) 0;

      } else {

        int w_end = (int) n_indices[seg] - (int) window_size;

        for (int w_start = 0; w_start < w_end; ++w_start) {

          size_type w_end1 = std::min(w_start + window_size, n_indices[seg]);
          activation -= input[indices[seg_start + w_start]];
          activation += input[indices[seg_start + w_end1]];

          if (activation >= threshold) {
            output[seg] = (int) w_start + 1;
            break;
          }
        }
      }
    }


       // for (size_type cell = 0; cell != ncells; ++cell, ++output) {

       // if (n_indices[cell] == 0) {
       // *output = (int) -1;
       // continue;
       // }

       // size_type w_end = n_indices[cell] - window_size + 1;
      
       // for (size_type w_start = 0; w_start < w_end; ++w_start) {
        
       // size_type w_end1 = w_start + window_size;
       // value_type activation = 0;
        
       // // Maintain activation with +/-
       // for (size_type i = w_start; i < w_end1; ++i) 
       // activation += input[indices[cell*max_dendrite_size+i]];        
        
       // if (activation >= threshold) {
       // *output = (int) w_start;
       // break;
       // }
        
       // *output = (int) -1;
       // }
       // }
    
  }
*/
  
  //--------------------------------------------------------------------------------
} // end namespace nta

#endif // NTA_ARRAY_ALGO_HPP
