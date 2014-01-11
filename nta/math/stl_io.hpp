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

/** @file STL IO 
 * This file contains functions to print out and save/load various STL data structures.
 */

#ifndef NTA_STL_IO_HPP
#define NTA_STL_IO_HPP

#include <vector>
#include <list>
#include <map>
#include <set>

#include <iostream>
#include <iomanip>
#include <boost/type_traits.hpp>

#include <nta/types/types.hpp>

#include <nta/math/array_algo.hpp>

namespace nta {

  //--------------------------------------------------------------------------------
  // IO CONTROL AND MANIPULATORS
  //--------------------------------------------------------------------------------
  typedef enum { CSR =0, CSR_01, BINARY, AS_DENSE } SPARSE_IO_TYPE;

  struct IOControl
  {
    int abbr;                  // shorten long vectors output
    bool output_n_elts;        // output vector size at beginning

    bool pair_paren;           // put parens around pairs in vector of pairs
    const char* pair_sep;      // put separator between pair.first and pair.second
   
    int convert_to_sparse;     // convert dense vector to pos. of non-zeros
    int convert_from_sparse;   // convert from pos. of non-zero to dense 0/1 vector
    
    SPARSE_IO_TYPE sparse_io;  // do sparse io according to SPARSE_IO_TYPE

    bool bit_vector;           // output 0/1 vector compactly

    inline IOControl(int a =-1, bool s =true, bool pp =false, const char* psep =" ",
                     SPARSE_IO_TYPE smio =CSR,
                     bool cts =false,
                     bool cfs =false,
                     bool bv =false)
      : abbr(a),
        output_n_elts(s),
        pair_paren(pp),
        pair_sep(psep),
        convert_to_sparse(cts),
        convert_from_sparse(cfs),
        sparse_io(smio),
        bit_vector(bv)
    {}

    inline void reset()
    {
      abbr = -1;
      output_n_elts = true;
      pair_paren = false;
      pair_sep = " ";
      convert_to_sparse = false;
      convert_from_sparse = false;
      sparse_io = CSR;
      bit_vector = false;
    }
  };

  extern IOControl io_control;

  template <typename CharT, typename Traits, typename T>
  inline std::basic_ostream<CharT,Traits>& 
  operator,(std::basic_ostream<CharT,Traits>& out_stream, const T& a)
  {
    return out_stream << ' ' << a;
  }
  
  template <typename CharT, typename Traits, typename T>
  inline std::basic_istream<CharT,Traits>& 
  operator,(std::basic_istream<CharT,Traits>& in_stream, T& a)
  {
    return in_stream >> a;
  }

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  operator,(std::basic_ostream<CharT,Traits>& out_stream, 
            std::basic_ostream<CharT,Traits>& (*pf)(std::basic_ostream<CharT,Traits>&))
  {
    pf(out_stream);
    return out_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  p_paren(std::basic_ostream<CharT,Traits>& out_stream)
  {
    io_control.pair_paren = true;
    return out_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  psep_comma(std::basic_ostream<CharT,Traits>& out_stream)
  {
    io_control.pair_sep = ",";
    return out_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  psep_dot(std::basic_ostream<CharT,Traits>& out_stream)
  {
    io_control.pair_sep = ".";
    return out_stream;
  }

  struct abbr
  {
    int n;
    inline abbr(int _n) : n(_n) {}
  };

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  operator<<(std::basic_ostream<CharT,Traits>& out_stream, abbr s)
  {
    io_control.abbr = s.n;
    return out_stream;
  }

  struct debug
  {
    int n;
    inline debug(int _n =-1) : n(_n) {}
  };

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  operator<<(std::basic_ostream<CharT,Traits>& out_stream, debug d)
  {
    io_control.abbr = d.n;
    io_control.output_n_elts = false;
    io_control.pair_sep = ",";
    io_control.pair_paren = true;
    return out_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_istream<CharT,Traits>& 
  from_csr_01(std::basic_istream<CharT,Traits>& in_stream)
  {
    io_control.convert_from_sparse = CSR_01;
    return in_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  to_csr_01(std::basic_ostream<CharT,Traits>& out_stream)
  {
    io_control.convert_to_sparse = CSR_01;
    return out_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_istream<CharT,Traits>& 
  bit_vector(std::basic_istream<CharT,Traits>& in_stream)
  {
    io_control.bit_vector = true;
    return in_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  bit_vector(std::basic_ostream<CharT,Traits>& out_stream)
  {
    io_control.bit_vector = true;
    return out_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_istream<CharT,Traits>& 
  general_vector(std::basic_istream<CharT,Traits>& in_stream)
  {
    io_control.bit_vector = false;
    return in_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  general_vector(std::basic_ostream<CharT,Traits>& out_stream)
  {
    io_control.bit_vector = false;
    return out_stream;
  }

  //--------------------------------------------------------------------------------
  // SM IO CONTROL
  //--------------------------------------------------------------------------------
  struct sparse_format_class
  {
    SPARSE_IO_TYPE format;
    
    inline sparse_format_class(SPARSE_IO_TYPE f) : format(f) {}
  };

  inline sparse_format_class 
  sparse_format(SPARSE_IO_TYPE f) { return sparse_format_class(f); }

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  operator<<(std::basic_ostream<CharT,Traits>& out_stream, sparse_format_class s)
  {
    io_control.sparse_io = s.format;
    return out_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_istream<CharT,Traits>& 
  operator>>(std::basic_istream<CharT,Traits>& in_stream, sparse_format_class s)
  {
    io_control.sparse_io = s.format;
    return in_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  as_dense(std::basic_ostream<CharT,Traits>& out_stream)
  {
    io_control.sparse_io = AS_DENSE;
    return out_stream;
  }

  template <typename CharT, typename Traits>
  inline std::basic_ostream<CharT,Traits>& 
  as_binary(std::basic_ostream<CharT,Traits>& out_stream)
  {
    io_control.sparse_io = BINARY;
    return out_stream;
  }

  //--------------------------------------------------------------------------------
  // CHECKERS
  //--------------------------------------------------------------------------------
  template <typename T1>
  struct is_positive_checker
  {
    T1& var;

    inline is_positive_checker(T1& v) : var(v) {}

    template <typename CharT, typename Traits>
    inline void do_check(std::basic_istream<CharT,Traits>& in_stream) 
    {
      double value = 0;
      in_stream >> value;
      if (value < 0) {
        std::cout << "Value out of range: " << value
                  << " - Expected positive or zero value"
                  << std::endl;
        exit(-1);
      }
      var = (T1) value;
    }
  };

  template <typename CharT, typename Traits, typename T1>
  inline std::basic_istream<CharT,Traits>& 
  operator>>(std::basic_istream<CharT,Traits>& in_stream, is_positive_checker<T1> cp)
  {
    cp.do_check(in_stream);
    return in_stream;
  }

  template <typename T1>
  inline is_positive_checker<T1> assert_positive(T1& var)
  { 
    return is_positive_checker<T1>(var); 
  }
  
  //--------------------------------------------------------------------------------
  // BINARY PERSISTENCE
  //--------------------------------------------------------------------------------
  template <typename It>
  inline void binary_save(std::ostream& out_stream, It begin, It end)
  {
    typedef typename std::iterator_traits<It>::value_type value_type;
    size_t size = (size_t) (end - begin);
    if (size > 0) {
      char* ptr = (char*) & *begin;
      out_stream.write(ptr, (std::streamsize) size*sizeof(value_type));
    }
  }

  //--------------------------------------------------------------------------------
  template <typename It>
  inline void binary_load(std::istream& in_stream, It begin, It end)
  {
    typedef typename std::iterator_traits<It>::value_type value_type;
    size_t size = (size_t) (end - begin);
    if (size > 0) {
      char* ptr = (char*) & *begin;
      in_stream.read(ptr, (std::streamsize) size*sizeof(value_type));
    }
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void binary_save(std::ostream& out_stream, const std::vector<T>& v)
  {
    nta::binary_save(out_stream, v.begin(), v.end());
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  inline void binary_load(std::istream& in_stream, std::vector<T>& v)
  {
    nta::binary_load(in_stream, v.begin(), v.end());
  }

  //--------------------------------------------------------------------------------
  // STL STREAMING OPERATORS
  //--------------------------------------------------------------------------------

  //--------------------------------------------------------------------------------
  // std::pair
  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline std::ostream& operator<<(std::ostream& out_stream, const std::pair<T1, T2>& p)
  {
    if (io_control.pair_paren)
      out_stream << "(";
    out_stream << p.first;
    out_stream << io_control.pair_sep;
    out_stream << p.second;
    if (io_control.pair_paren)
      out_stream << ")";
    return out_stream;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline std::istream& operator>>(std::istream& in_stream, std::pair<T1, T2>& p)
  {
    in_stream >> p.first >> p.second;
    return in_stream;
  }

  //--------------------------------------------------------------------------------
  // std::vector
  //--------------------------------------------------------------------------------
  template <typename T, bool>
  struct vector_loader
  {
    inline void load(size_t, std::istream&, std::vector<T>&);
  };

  //--------------------------------------------------------------------------------
  /**
   * Partial specialization of above functor for primitive types.
   */
  template <typename T>
  struct vector_loader<T, true> 
  {
    inline void load(size_t n, std::istream& in_stream, std::vector<T>& v)
    {
      if (io_control.convert_from_sparse == CSR_01) {

        std::fill(v.begin(), v.end(), (T) 0);

        for (size_t i = 0; i != n; ++i) {
          int index = 0;
          in_stream >> index;
          v[index] = (T) 1;
        }

      } else if (io_control.bit_vector) {

        for (size_t i = 0; i != n; ++i) {
          float x = 0;
          in_stream >> x;
          if (x)
            v[i] = 1;
          else
            v[i] = 0;
        }
        
      } else {
        for (size_t i = 0; i != n; ++i) 
          in_stream >> v[i];
      }
    }
  };

  // declartion of >> which is used in the following function. Avoid lookup error
  template <typename T> inline std::istream& operator>>(std::istream& in_stream, std::vector<T>& v);
  //--------------------------------------------------------------------------------
  /**
   * Partial specialization for non-primitive types.
   */
  template <typename T>
  struct vector_loader<T, false>
  {
    inline void load(size_t n, std::istream& in_stream, std::vector<T>& v)
    {
      for (size_t i = 0; i != n; ++i) 
        in_stream >> v[i];
    }
  };

  //--------------------------------------------------------------------------------
  /**
   * Factory that will instantiate the right functor to call depending on whether
   * T is a primitive type or not.
   */
  template <typename T>
  inline void vector_load(size_t n, std::istream& in_stream, std::vector<T>& v)
  {
    vector_loader<T, boost::is_fundamental<T>::value > loader;
    loader.load(n, in_stream, v);
  }
  
  //--------------------------------------------------------------------------------
  template <typename T, bool>
  struct vector_saver 
  {
    inline void save(size_t n, std::ostream& out_stream, const std::vector<T>& v);
  };

  //--------------------------------------------------------------------------------
  /**
   * Partial specialization for primitive types.
   */
  template <typename T>
  struct vector_saver<T, true>
  {
    inline void save(size_t n, std::ostream& out_stream, const std::vector<T>& v)
    {
      if (io_control.output_n_elts)
        out_stream << n << ' ';
      
      if (io_control.abbr > 0) 
        n = std::min((size_t) io_control.abbr, n);
      
      if (io_control.convert_to_sparse == CSR_01) {
        
        for (size_t i = 0; i != n; ++i) 
          if (!is_zero(v[i]))
            out_stream << i << ' ';
        
      } else if (io_control.bit_vector) {
        
        size_t k = 7;
        for (size_t i = 0; i != v.size(); ++i) {
          out_stream << (is_zero(v[i]) ? '0' : '1');
          if (i == k) {
            out_stream << ' ';
            k += 8;
          }
        }

      } else {

        for (size_t i = 0; i != n; ++i) 
          out_stream << v[i] << ' ';
      }

      if (io_control.abbr > 0 && n < v.size()) {
        size_t rest = v.size() - n;
        out_stream << "[+" << rest << "/" << count_non_zeros(v) << "]";
      }
    }
  };

  // declartion of << which is used in the following function. Avoid lookup error.
  template <typename T> inline std::ostream& operator<<(std::ostream& out_stream, const std::vector<T>& v);
  //--------------------------------------------------------------------------------
  /**
   * Partial specialization for non-primitive types.
   */
  template <typename T>
  struct vector_saver<T, false>
  {
    inline void save(size_t n, std::ostream& out_stream, const std::vector<T>& v)
    {
      if (io_control.output_n_elts)
        out_stream << n << ' ';
      
      if (io_control.abbr > 0) 
        n = std::min((size_t) io_control.abbr, n);
      
      for (size_t i = 0; i != n; ++i) 
        out_stream << v[i] << ' ';
      
      if (io_control.abbr > 0 && n < v.size()) {
        size_t rest = v.size() - n;
        out_stream << "[+" << rest << "/" << count_non_zeros(v) << "]";
      }
    }
  };

  //--------------------------------------------------------------------------------
  /**
   * Factory that will instantiate the right functor to call depending on whether
   * T is a primitive type or not.
   */
  template <typename T>
  inline void vector_save(size_t n, std::ostream& out_stream, const std::vector<T>& v)
  {
    vector_saver<T, boost::is_fundamental<T>::value> saver;
    saver.save(n, out_stream, v);
  }

  //--------------------------------------------------------------------------------
  /**
   * Saves the size of the vector.
   */
  template <typename T>
  inline std::ostream& operator<<(std::ostream& out_stream, const std::vector<T>& v)
  {
    vector_save(v.size(), out_stream, v);
    return out_stream;
  }

  //--------------------------------------------------------------------------------
  /**
   * Reads in size of the vector, and redimensions it, except if we are reading
   * a sparse binary vector.
   */
  template <typename T>
  inline std::istream& 
  operator>>(std::istream& in_stream, std::vector<T>& v)
  {
    size_t n = 0;
    in_stream >> n;
    v.resize(n);
    vector_load(n, in_stream, v);
    return in_stream;
  }

  //--------------------------------------------------------------------------------
  /**
   * Doesn't save the size of the buffer itself.
   */
  template <typename T>
  inline std::ostream& operator<<(std::ostream& out_stream, const Buffer<T>& b)
  {
    vector_save(b.nnz, out_stream, static_cast<const std::vector<T>&>(b));
    return out_stream;
  }

  //--------------------------------------------------------------------------------
  /**
   * Doesn't set the size of the buffer itself.
   */
  template <typename T>
  inline std::istream& operator>>(std::istream& in_stream, Buffer<T>& b)
  {
    in_stream >> b.nnz;
    NTA_ASSERT(b.nnz <= b.size());
    vector_load(b.nnz, in_stream, static_cast<std::vector<T>&>(b));
    return in_stream;
  }

  //--------------------------------------------------------------------------------
  // std::set
  //--------------------------------------------------------------------------------
  template <typename T1>
  inline std::ostream& operator<<(std::ostream& out_stream, const std::set<T1>& m)
  {
    typename std::set<T1>::const_iterator 
      it = m.begin(), end = m.end();

    while (it != end) {
      out_stream << *it << ' ';
      ++it;
    }

    return out_stream;
  }

  //--------------------------------------------------------------------------------
  // std::map
  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline std::ostream& operator<<(std::ostream& out_stream, const std::map<T1, T2>& m)
  {
    out_stream << m.size() << " ";

    typename std::map<T1, T2>::const_iterator 
      it = m.begin(), end = m.end();

    while (it != end) {
      out_stream << it->first << ' ' << it->second << ' ';
      ++it;
    }

    return out_stream;
  }

  //--------------------------------------------------------------------------------
  template <typename T1, typename T2>
  inline std::istream& operator>>(std::istream& in_stream, std::map<T1, T2>& m)
  {
    int size = 0;
    in_stream >> size;

    for (int i = 0; i != size; ++i) {
      T1 k; T2 v;
      in_stream >> k >> v;
      m.insert(std::make_pair(k, v));
    }

    return in_stream;
  }

  //--------------------------------------------------------------------------------
  // MISCELLANEOUS
  //--------------------------------------------------------------------------------
  template <typename T>
  inline void show_all_differences(const std::vector<T>& x, const std::vector<T>& y)
  {
    std::vector<size_t> diffs;
    find_all_differences(x, y, diffs);
    std::cout << diffs.size() << " differences: " << std::endl;
    for (size_t i = 0; i != diffs.size(); ++i)
      std::cout << "(at:" << diffs[i] 
                << " y=" << x[diffs[i]] 
                << ", ans=" << y[diffs[i]] << ")";
    std::cout << std::endl;
  }

  //--------------------------------------------------------------------------------
} // end namespace nta
#endif // NTA_STL_IO_HPP
