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
 * Definition and implementation for Domain class
 */

#ifndef NTA_DOMAIN_HPP
#define NTA_DOMAIN_HPP

//----------------------------------------------------------------------

#include <nta/math/Index.hpp>

//----------------------------------------------------------------------

namespace nta {

  /**
   * A class that models a range along a given dimension.
   * dim is the dimension number, lb is the lower bound,
   * and ub the upper bound. The range includes its lower bound
   * but does not contain its upper bound: [lb..ub), open
   * on the right.
   */
  template <typename UInt>      
  class DimRange
  {
  public:
    inline DimRange()
      : dim_(0), lb_(0), ub_(0)
    {}

    inline DimRange(const UInt dim, const UInt& lb, const UInt& ub)
      : dim_(dim), lb_(lb), ub_(ub)
    {
      NTA_ASSERT(lb >= 0);
      NTA_ASSERT(lb <= ub)
        << "DimRange::DimRange(dim, lb, ub): "
        << "Lower bound (" << lb << ") should be <= upper bound "
        << "(" << ub << ") for dim: " << dim;
    }

    inline DimRange(const DimRange& o)
      : dim_(o.dim_), lb_(o.lb_), ub_(o.ub_)
    {}

    inline DimRange& operator=(const DimRange& o)
    {
      if (&o != this) {
        dim_ = o.dim_;
        lb_ = o.lb_;
        ub_ = o.ub_;
      }
      return *this;
    }
  
    inline const UInt getDim() const { return dim_; }
    inline const UInt getLB() const { return lb_; }
    inline const UInt getUB() const { return ub_; }
    inline const UInt size() const { return ub_ - lb_; }
    inline bool empty() const { return lb_ == ub_; }
    
    inline bool includes(const UInt& i) const 
    { 
      bool ok = false;
      if (lb_ == ub_) {
        if (i == lb_)
          ok = true;
      }
      else if (lb_ <= i && i < ub_)
        ok = true;
      return ok;
    }

    inline void set(const UInt dim, const UInt& lb, const UInt& ub)
    {
      NTA_ASSERT(lb <= ub)
        << "DimRange::set(dim, lb, ub): "
        << "Lower bound (" << lb << ") should be <= upper bound "
        << "(" << ub << ") for dim: " << dim;

      dim_ = dim;
      lb_ = lb;
      ub_ = ub;
    }

    template <typename UI>
    NTA_HIDDEN friend std::ostream& operator<<(std::ostream&, const DimRange<UI>&);

    template <typename UI>
    NTA_HIDDEN friend bool operator==(const DimRange<UI>& r1, const DimRange<UI>& r2);

    template <typename UI>
    NTA_HIDDEN friend bool operator!=(const DimRange<UI>& r1, const DimRange<UI>& r2);

  private:
    UInt dim_;
    UInt lb_, ub_;
  };

  //--------------------------------------------------------------------------------
  template <typename UI>
  inline std::ostream& operator<<(std::ostream& outStream, const DimRange<UI>& r)
  {
    return outStream << "[" << r.dim_ << ": " << r.lb_ << ".." << r.ub_ << ")";
  }
  
  template <typename UI>
  inline bool operator==(const DimRange<UI>& r1, const DimRange<UI>& r2)
  {
    return r1.dim_ == r2.dim_ && r1.lb_ == r2.lb_ && r1.ub_ == r2.ub_;
  }

  template <typename UI>
  inline bool operator!=(const DimRange<UI>& r1, const DimRange<UI>& r2)
  {
    return ! (r1 == r2);
  }

  //--------------------------------------------------------------------------------
  /**
   * A class that models the cartesian product of several ranges
   * along several dimensions. 
   */
  template <typename UInt>
  class Domain
  {
  public:
    // Doesn't work on shona
    /*
    explicit inline Domain(UInt NDims, UInt d0, UInt lb0, UInt ub0, ...)
    {
      ranges_.push_back(DimRange<UInt>(d0, lb0, ub0));
      va_list indices;
      va_start(indices, ub0);
      for (UInt k = 1; k < NDims; ++k) 
        ranges_.push_back(DimRange<UInt>(va_arg(indices, UInt),
                                         va_arg(indices, UInt),
                                         va_arg(indices, UInt)));
      va_end(indices);
      
      {
        for (UInt i = 0; i < NDims-1; ++i) 
          NTA_ASSERT(ranges_[i].getDim() < ranges_[i+1].getDim())
            << "Domain::Domain(...): "
            << "Dimensions need to be in strictly increasing order";
      }
    }
    */
    
    // Half-space constructor
    template <typename Index>    
    explicit inline Domain(const Index& ub)
      : ranges_()
    {
      for (UInt k = 0; k < ub.size(); ++k)
        ranges_.push_back(DimRange<UInt>(k, 0, ub[k]));
    }

    template <typename Index>
    explicit inline Domain(const Index& lb, const Index& ub)
      : ranges_()
    {
      {
        NTA_ASSERT(lb.size() == ub.size());
      }

      for (UInt k = 0; k < ub.size(); ++k)
        ranges_.push_back(DimRange<UInt>(k, lb[k], ub[k]));
    }

    inline Domain(const Domain& o)
      : ranges_(o.ranges_)
    {}

    inline Domain& operator=(const Domain& o)
    {
      if (&o != this) 
        ranges_ = o.ranges_;
      return *this;
    }

    inline UInt rank() const { return (UInt)ranges_.size(); }
    inline bool empty() const { return size_elts() == 0; }

    inline UInt size_elts() const 
    {
      UInt n = 1;
      for (UInt k = 0; k < rank(); ++k)
        n *= ranges_[k].size();
      return n;
    }

    inline DimRange<UInt> operator[](const UInt& idx) const
    {
      {
        NTA_ASSERT(0 <= idx && idx < rank());
      }

      return ranges_[idx];
    }

    template <typename Index>
    inline void getLB(Index& lb) const
    {
      {
        NTA_ASSERT(lb.size() == rank());
      }

      for (UInt k = 0; k < rank(); ++k)
        lb[k] = ranges_[k].getLB();
    }

    template <typename Index>
    inline void getUB(Index& ub) const
    {
      {
        NTA_ASSERT(ub.size() == rank());
      }

      for (UInt k = 0; k < rank(); ++k)
        ub[k] = ranges_[k].getUB();
    }

    template <typename Index>
    inline void getIterationLast(Index& last) const
    {
      {
        NTA_ASSERT(last.size() == rank());
        NTA_ASSERT(!hasClosedDims());
      }

      for (UInt k = 0; k < rank(); ++k)
        last[k] = ranges_[k].getUB() - 1;
    }

    template <typename Index>
    inline void getDims(Index& dims) const
    {
      {
        NTA_ASSERT(dims.size() == rank());
      }

      for (UInt k = 0; k < rank(); ++k)
        dims[k] = ranges_[k].getDim();
    }

    inline UInt getNOpenDims() const
    {
      UInt k, n;
      for (k = 0, n = 0; k < rank(); ++k)
        if (! ranges_[k].empty())
          ++n;
      return n;
    }

    template <typename Index2>
    inline void getOpenDims(Index2& dims) const
    {
      {
        NTA_ASSERT(dims.size() == getNOpenDims())
          << "Domain::getOpenDims(): "
          << "Wrong number of dimensions, passed: " << dims.size()
          << " - Should be " << getNOpenDims();
      }

      UInt k, k1;
      for (k = 0, k1 = 0; k < rank(); ++k)
        if (! ranges_[k].empty())
          dims[k1++] = ranges_[k].getDim();
    }

    inline bool hasClosedDims() const
    {
      for (UInt k = 0; k < rank(); ++k)
        if (ranges_[k].empty())
          return true;
      return false;
    }

    inline UInt getNClosedDims() const
    {
      return rank() - getNOpenDims();
    }

    template <typename Index2>
    inline void getClosedDims(Index2& dims) const
    {
      {
        NTA_ASSERT(dims.size() == getNClosedDims())
          << "Domain::getClosedDims(): "
          << "Wrong number of dimensions, passed: " << dims.size()
          << " - Should be " << getNClosedDims();
      }

      UInt k, k1;
      for (k = 0, k1 = 0; k < rank(); ++k)
        if (ranges_[k].empty())
          dims[k1++] = ranges_[k].getDim();
    }

    template <typename Index>
    inline bool includes(const Index& index) const
    {
      {
        NTA_ASSERT(index.size() == rank());
      }

      bool ok = true;
      for (UInt k = 0; k < rank() && ok; ++k) 
        ok = ranges_[k].includes(index[k]);
      return ok;
    }

    /**
     * Not strict inclusion.
     */
    inline bool includes(const Domain& d) const
    {
      {
        NTA_ASSERT(d.rank() == rank());
      }

      for (UInt k = 0; k < rank(); ++k)
        if (d.ranges_[k].getLB() < ranges_[k].getLB()
            || d.ranges_[k].getUB() > ranges_[k].getUB())
          return false;
      
      return true;
    }

    template <typename UI>
    NTA_HIDDEN friend std::ostream& operator<<(std::ostream& outStream, const Domain<UI>& dom);
  
    template <typename UI>
    NTA_HIDDEN friend bool operator==(const Domain<UI>& d1, const Domain<UI>& d2);

    template <typename UI>
    NTA_HIDDEN friend bool operator!=(const Domain<UI>& d1, const Domain<UI>& d2);

  protected:
    // Could be a compile time dimension, as it used to be, 
    // and that would be faster
    // sorted by construction, and unique dims
    std::vector<DimRange<UInt> > ranges_; 

    Domain() {}
  };

  //--------------------------------------------------------------------------------
  template <typename UI>
  inline std::ostream& operator<<(std::ostream& outStream, const Domain<UI>& dom)
  {
    outStream << "[";
    for (UInt k = 0; k < dom.rank(); ++k)
      outStream << dom[k] << " ";
    return outStream << "]" << std::endl;
  }

  template <typename UI>
  inline bool operator==(const Domain<UI>& d1, const Domain<UI>& d2)
  {
    if (d1.rank() != d2.rank())
      return false;
    for (UInt k = 0; k < d1.rank(); ++k) 
      if (d1.ranges_[k] != d2.ranges_[k])
        return false;
    return true;
  }

  template <typename UI>
  inline bool operator!=(const Domain<UI>& d1, const Domain<UI>& d2)
  {
    if (d1.rank() != d2.rank())
      return true;
    for (UInt k = 0; k < d1.rank(); ++k) 
      if (d1.ranges_[k] != d2.ranges_[k])
        return true;
    return false;
  }

  //--------------------------------------------------------------------------------
  template <typename T>
  class Domain2D : public Domain<T>
  {
  public:
    inline Domain2D(T first_row, T row_end, T first_col, T col_end)
    {
      this->ranges_.resize(2);
      this->ranges_[0].set(0, first_row, row_end);
      this->ranges_[1].set(1, first_col, col_end);
    }

    inline T getFirstRow() const { return this->ranges_[0].getLB(); }
    inline T getRowEnd() const { return this->ranges_[0].getUB(); }
    inline T getFirstCol() const { return this->ranges_[1].getLB(); }
    inline T getColEnd() const { return this->ranges_[1].getUB(); }
  };

  //--------------------------------------------------------------------------------
} // end namespace nta

#endif // NTA_DOMAIN_HPP
