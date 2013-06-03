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

/** @file Statistics/Dynamic Histogram */

#ifndef NTA_STATISTICS_HISTOGRAM_HPP
#define NTA_STATISTICS_HISTOGRAM_HPP
#ifdef NUPIC2
#error "StatisticsHistogram.hpp is not used in NuPIC2"
#endif

#include <math.h>
#include <iostream>
#include <boost/unordered_set.hpp>

//--------------------------------------------------------------------------------
template <typename Label, typename Size, typename Value>
struct histogram 
{
  typedef Label label_type;
  typedef Size size_type;
  typedef Value value_type;
  typedef boost::unordered_set<label_type, value_type> Counts;
  typedef typename Counts::const_iterator const_iterator;
  typedef typename Counts::iterator iterator;

  // The sum of all the values
  value_type sum_;

  // Values less than eps will be treated as zero
  value_type eps_;

  // The actual counts. All counts are positive.
  Counts counts_;

  inline bool isZero(const value_type& val) const
  {
    return val <= eps_;
  }

  inline histogram(const value_type& eps =1e-6)
    : sum_(0), eps_(eps), counts_()
  {}

  template <typename It>
  inline histogram(It x_it, It x_end, const value_type& eps =1e-6)
    : sum_(T(x_end - x_it)), eps_(eps), counts_()
  {
    while (x_it != x_end) {
      label_type label = *x_it;
      iterator it = find(label);
      if (it == end()) {
        counts_[label] = value_type(1);
      } else {
        ++ it->second;
      }
      ++ x_it;
    }
  }

  inline histogram(const histogram& o)
  {
    sum_ = o.sum_;
    eps_ = o.eps_;
    counts_ = o.counts_;
  }

  inline histogram& operator=(const histogram& o)
  {
    if (&o != this) {
      sum_ = o.sum_;
      eps_ = o.eps_;
      counts_ = o.counts_;
    }
    return *this;
  }

  inline std::pair<std::vector<size_type>, std::vector<value_type> > 
  toArray() const
  {
    std::vector<size_type> labels;
    std::vector<value_type> counts;
    const_iterator it = begin(), e = end();
    for (; it != e; ++it) {
      labels.push_back(it->first);
      counts.push_back(it->second);
    }
    return std::make_pair(labels, counts);
  }

  inline const_iterator begin() const { return counts_.begin(); }
  inline const_iterator end() const { return counts_.end(); }
  inline iterator begin() { return counts_.begin(); }
  inline iterator end() { return counts_.end(); }

  inline size_type size() const { return counts_.size(); }
  inline bool empty() const { return counts_.empty(); }
  inline value_type sum() const { return sum_; }
  inline value_type eps() const { return eps_; }

  inline void clear()
  {
    counts_.clear();
    sum_ = 0;
  }

  inline const_iterator find(const label_type& l) const
  {
    return counts_.find(l);
  }

  inline iterator find(const label_type& l) 
  {
    return counts_.find(l);
  }
  
  inline value_type count(const_iterator it) const
  {
    if (it != end())
      return it->second;
    else
      return value_type(0);
  }

  inline value_type count(const label_type& l) const
  {
    return count(find(l));
  }

  /**
   * If val is zero, simply returns without doing anything.
   */
  inline void update(const label_type& l, const value_type& val)
  {
    if (isZero(val))
      return;

    iterator it = find(l);
    if (it == end()) {
      counts_[l] = val;
    } else {
      it->second += val;
    }
    sum_ += val;
  }

  /**
   * If val is zero, removes l from histogram. 
   */
  inline void set(const label_type& l, const value_type& val)
  {
    iterator it = find(l);
    if (it != end()) {
      if (val == 0) {
        sum_ -= it->second;
        counts_.erase(it);
      } else {
        sum_ += val - it->second;
        it->second = val;
      }
    } else {
      counts_[l] = val;
      sum_ += val;
    }
  }

  inline value_type probability(const label_type& l) const
  {
    if (sum() == 0)
      return value_type(0);
    else 
      return count(l) / sum(); 
  }

  inline value_type probability(const_iterator it) const
  {
    if (it != end()) {
      if (sum() == 0)
        return value_type(0);
      else
        return it->second / sum();
    } else
      return value_type(0);
  }

  inline void operator+=(const histogram& hist)
  {
    const_iterator it = hist.begin(), e = hist.end();

    for (; it != e; ++it) 
      update(it->first, it->second);
  }

  inline void save(std::ostream& outStream) const
  {
    outStream << size() << " " << eps() << " ";
    for (const_iterator i = begin(); i != end(); ++i)
      outStream << i->first << " " << i->second << " ";
  }

  inline void load(std::istream& inStream)
  {
    size_type n;
    label_type l;
    value_type c;

    clear();
    inStream >> n >> eps_;

    for (size_type i = 0; i < n; ++i) {
      inStream >> l >> c;
      set(l, c);
    }
  }

  /*
  template <typename L, typename S, typename V>
  friend std::ostream& operator<<(std::ostream&, const histogram<L,S,V>&);
  */
};

//--------------------------------------------------------------------------------
/*
template <typename L, typename S, typename V>
inline std::ostream& operator<<(std::ostream& outStream, const histogram<L,S,V>& h)
{
  typename histogram<L,S,V>::const_iterator i, end;

  for (i = h.begin(), end = h.end(); i != end; ++i)
    outStream << i->first << " " << i->second << "  ";

  return outStream;
}
*/

//--------------------------------------------------------------------------------
template <typename Hist>
inline typename Hist::const_iterator mode(const Hist& hist)
{
  typedef typename Hist::size_type size_type;
  typedef typename Hist::const_iterator const_iterator;
  const_iterator it = hist.begin(), e = hist.end(), max_it = it;

  size_type val, max_val = it->second;

  while (it != e) {
    val = it->second;
    if (val > max_val) {
      max_it = it;
      max_val = val;
    }
    ++it;
  }

  return max_it;
}

//--------------------------------------------------------------------------------
template <typename Hist>
inline typename Hist::label_type sample(const Hist& hist)
{
  typedef typename Hist::value_type value_type;
  typedef typename Hist::const_iterator const_iterator;
  const_iterator it = hist.begin(), e = hist.end();

  value_type p = rand() % int(hist.sum());
  value_type sum = it->second;

  while (it != e && p >= sum) {
    ++it;
    sum += it->second;
  }

  return it->first;
}

//--------------------------------------------------------------------------------
template <typename Hist>
inline typename Hist::value_type entropy(const Hist& hist)
{
  typedef typename Hist::value_type value_type;
  typedef typename Hist::const_iterator const_iterator;
  const_iterator it = hist.begin(), e = hist.end();

  value_type h = 0;

  while (it != e) {
    value_type p = hist.probability(it);
    h += p * log(p);
    ++it;
  }
  
  return - h / log((value_type)2);
}

//--------------------------------------------------------------------------------
/**
 * Make sure they have the same label sets
 */
template <typename Hist>
inline typename Hist::value_type KL(const Hist& a, const Hist& b)
{
  typedef typename Hist::value_type value_type;
  typedef typename Hist::const_iterator const_iterator;
  const_iterator it_a = a.begin(), e = a.end(), it_b = b.begin();
  
  value_type kl = 0;
  while (it_a != e) {
    value_type p_a = a.probability(it_a), p_b = b.probability(it_b);
    kl += p_a * log(p_a/p_b);
    ++it_a; ++it_b;
  }
  return - kl / log((value_type)2);
}

//--------------------------------------------------------------------------------
/*
template <typename stream_type, typename L, typename S, typename V>
inline 
stream_type& std::operator<<(stream_type& out, const histogram<L,S,V>& h)
{
  typename histogram<L,S,V>::const_iterator it, end;

  for (it = h.begin(), end = h.end(); it != end; ++it) 
    out << it->first << ": " << it->second << ' ';

  return out;
}
*/

//--------------------------------------------------------------------------------
template <typename Hist>
inline void pretty_print_histogram(const Hist& hist) 
{
  typedef typename Hist::const_iterator const_iterator;
  const_iterator it = hist.begin(), e = hist.end(), m = mode(hist);
  for (; it != e; ++it) {
    size_t n = 80*it->second / m->second;
    std::cout << it->first << ": ";
    for (size_t i = 0; i < n; ++i)
      std::cout << "*";
    std::cout << std::endl;
  }
}

//--------------------------------------------------------------------------------
#endif // NTA_STATISTICS_HISTOGRAM_HPP
