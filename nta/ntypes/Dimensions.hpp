
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

#ifndef NTA_DIMENSIONS_HPP
#define NTA_DIMENSIONS_HPP

#include <vector>
#include <sstream>

namespace nta
{
  /*
   * A coordinate is a single point in an n-dimensional
   * grid described by a Dimensions object. Because
   * a vector of a basic type can be directly wrapped
   * by swig, we do not need a separate class. 
   */
  typedef std::vector<size_t> Coordinate;


  /**
   * A Dimensions object represents the dimensions of a Region
   * It is vector of ints with a few methods for convenience
   * and for wrapping.
   * 
   * A node within a region is identified by a Coordinate, and 
   * the Coordinate<->index mapping is in x-major order, i.e.
   * for Region with dimensions [2,3]:
   * 
   *   [0,0] -> index 0
   *   [1,0] -> index 1
   *   [0,1] -> index 2
   *   [1,1] -> index 3
   *   [0,2] -> index 4
   *   [1,2] -> index 5
   */
  class Dimensions : public std::vector<size_t>
  {
  public:
    Dimensions();
    Dimensions(std::vector<size_t> v);
    Dimensions(size_t x);
    Dimensions(size_t x, size_t y);
    Dimensions(size_t x, size_t y, size_t z);

    /*
     * Returns the product of the dimensions
     */
    size_t 
    getCount() const;

    /*
     * Returns number of dimensions
     * (for wrappers)
     */
    size_t
    getDimensionCount() const;

    /*
     * Returns a specific dimensions
     * (for wrappers)
     */
    size_t
    getDimension(size_t index) const;

    /*
     * There are two "special" values for dimensions
     * Dimensions of [] (dims.size()==0) means "not yet known" aka "unspecified"
     * Dimensions of [0] (dims.size()==1 && dims[0] == 0) means "don't care"
     */
    bool
    isDontcare() const;

    bool
    isUnspecified() const;

    bool
    isSpecified() const;

    // In a few places we treat dimensions [1], [1 1], [1 1 1], etc. as equivalent
    // This provides an easy way to check
    bool 
    isOnes() const;

    /*
     * A dimensions object is valid if it specifies actual dimensions, 
     * or is a special value (unspecified/dontcare). A dimensions object
     * is invalid if any dimensions are 0 (except for dontcare)
     */
    bool
    isValid() const;
    
    // ---
    // Dimensions can be represented as a string
    // In most cases, we want a human-readable string, but for
    // serialization we want only the actual dimension values
    // ---
    std::string
    toString(bool humanReadable=true) const;

    /*
     * Convert a coordinate to a linear index.
     */
    size_t
    getIndex(const Coordinate&) const;

    /*
     * Convert a linear index to a coordinate
     */
    Coordinate
    getCoordinate(const size_t) const;

    // ---
    /// Some linking scenarios require us to treat [1] equivalent to [1 1] etc. 
    // ---
    void
    promote(size_t newDimensionality);

    bool
    operator==(const Dimensions& dims2) const;

    bool
    operator!=(const Dimensions& dims2) const;


#ifdef NTA_INTERNAL
    friend std::ostream& operator<<(std::ostream& f, const Dimensions&);
#endif


  };

}


#endif // NTA_DIMENSIONS_HPP
