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
 * UniformLinkPolicy unit tests
 */

#ifndef NTA_UNIFORM_LINK_POLICY_TEST_HPP
#define NTA_UNIFORM_LINK_POLICY_TEST_HPP

//----------------------------------------------------------------------

#include <nta/test/Tester.hpp>
#include <nta/ntypes/Dimensions.hpp>
#include <nta/types/Fraction.hpp>

//----------------------------------------------------------------------

namespace nta {

  struct UniformLinkPolicyTest : public Tester
  {
    virtual ~UniformLinkPolicyTest() {}
    virtual void RunTests();

  private:

    enum LinkSide
    {
      srcLinkSide,
      destLinkSide
    };

    struct CoordBounds
    {
      Coordinate coord;
      size_t dimension;
      std::pair<Fraction, Fraction> bounds;

      CoordBounds(Coordinate c, size_t dim, std::pair<Fraction, Fraction> b) :
        coord(c),
        dimension(dim),
        bounds(b)
      {
      }
    };

    Coordinate makeCoordinate(size_t x, size_t y);

    bool setAndCheckDimensions(LinkSide setLinkSide,
                               Dimensions setDimensions,
                               Dimensions checkDimensions,
                               std::string linkParams,
                               size_t elementCount = 1);

    bool setDimensionsAndCheckBounds(LinkSide setLinkSide,
                                     Dimensions setDimensions,
                                     std::vector<CoordBounds> checkBoundsVec,
                                     std::string linkParams,
                                     size_t elementCount = 1);
  };
}

#endif // NTA_UNIFORM_LINK_POLICY_TEST_HPP
