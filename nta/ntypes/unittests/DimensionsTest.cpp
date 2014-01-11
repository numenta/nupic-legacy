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
 * Implementation of BasicType test
 */

#include "DimensionsTest.hpp"
#include <nta/ntypes/Dimensions.hpp>

namespace nta
{
  //internal helper method
  static std::string vecToString(std::vector<size_t> vec)
  {
    std::stringstream ss;
    ss << "[";
    for (size_t i = 0; i < vec.size(); i++)
    {
      ss << vec[i];
      if (i != vec.size()-1)
        ss << " ";
    }
    ss << "]";
    return ss.str();
  }

  void DimensionsTest::RunTests()
  {
    Coordinate zero; // [0];
    zero.push_back(0);

    Coordinate one_two; // [1,2]
    one_two.push_back(1);
    one_two.push_back(2);

    Coordinate three_four; // [3,4]
    three_four.push_back(3);
    three_four.push_back(4);
    

    {
      // empty dimensions (unspecified)
      Dimensions d;
      TEST(d.isUnspecified());
      TEST(d.isValid());
      TEST(!d.isDontcare());
      SHOULDFAIL(d.getCount());
      SHOULDFAIL(d.getDimension(0));
      TESTEQUAL("[unspecified]", d.toString());
      SHOULDFAIL(d.getIndex(one_two));
      SHOULDFAIL(d.getCount());
      SHOULDFAIL(d.getDimension(0));
      TESTEQUAL((unsigned int)0, d.getDimensionCount());
    }

    {
      // dontcare dimensions [0]
      Dimensions d;
      d.push_back(0);
      TEST(!d.isUnspecified());
      TEST(d.isDontcare());
      TEST(d.isValid());
      TESTEQUAL("[dontcare]", d.toString());
      SHOULDFAIL(d.getIndex(zero));
      SHOULDFAIL(d.getCount());
      TESTEQUAL((unsigned int)0, d.getDimension(0));
      TESTEQUAL((unsigned int)1, d.getDimensionCount());
    }


    {
      // invalid dimensions
      Dimensions d;
      d.push_back(1);
      d.push_back(0);
      TEST(!d.isUnspecified());
      TEST(!d.isDontcare());
      TEST(!d.isValid());
      TESTEQUAL("[1 0] (invalid)", d.toString());
      SHOULDFAIL(d.getIndex(one_two));
      SHOULDFAIL(d.getCount());
      TESTEQUAL((unsigned int)1, d.getDimension(0));
      TESTEQUAL((unsigned int)0, d.getDimension(1));
      SHOULDFAIL(d.getDimension(2));
      TESTEQUAL((unsigned int)2, d.getDimensionCount());
    }

    {
      // valid dimensions [2,3]
      // two rows, three columns
      Dimensions d;
      d.push_back(2);
      d.push_back(3);
      TEST(!d.isUnspecified());
      TEST(!d.isDontcare());
      TEST(d.isValid());
      TESTEQUAL("[2 3]", d.toString());
      TESTEQUAL((unsigned int)2, d.getDimension(0));
      TESTEQUAL((unsigned int)3, d.getDimension(1));
      SHOULDFAIL(d.getDimension(2));
      TESTEQUAL((unsigned int)6, d.getCount());
      TESTEQUAL((unsigned int)5, d.getIndex(one_two));
      TESTEQUAL((unsigned int)2, d.getDimensionCount());
    }

    {
      //check a two dimensional matrix for proper x-major ordering
      std::vector<size_t> x;
      x.push_back(4);
      x.push_back(5);
      Dimensions d(x);
      size_t testDim1 = 4;
      size_t testDim2 = 5;
      for(size_t i = 0; i < testDim1; i++)
      {
        for(size_t j = 0; j < testDim2; j++)
        {
          Coordinate testCoordinate;
          testCoordinate.push_back(i);
          testCoordinate.push_back(j);

          TESTEQUAL(i+j*testDim1, d.getIndex(testCoordinate));
          TESTEQUAL(vecToString(testCoordinate),
                    vecToString(d.getCoordinate(i+j*testDim1)));
        }
      }
    }

    {
      //check a three dimensional matrix for proper x-major ordering
      std::vector<size_t> x;
      x.push_back(3);
      x.push_back(4);
      x.push_back(5);
      Dimensions d(x);
      size_t testDim1 = 3;
      size_t testDim2 = 4;
      size_t testDim3 = 5;
      for(size_t i = 0; i < testDim1; i++)
      {
        for(size_t j = 0; j < testDim2; j++)
        {
          for(size_t k = 0; k < testDim3; k++)
          {
            Coordinate testCoordinate;
            testCoordinate.push_back(i);
            testCoordinate.push_back(j);
            testCoordinate.push_back(k);

            TESTEQUAL(i +
                      j*testDim1 +
                      k*testDim1*testDim2, d.getIndex(testCoordinate));

            TESTEQUAL(vecToString(testCoordinate),
                      vecToString(d.getCoordinate(i +
                                                  j*testDim1 +
                                                  k*testDim1*testDim2)));
          }
        }
      }
    }

    { 
      // alternate constructor
      std::vector<size_t> x;
      x.push_back(2);
      x.push_back(5);
      Dimensions d(x);
      TEST(!d.isUnspecified());
      TEST(!d.isDontcare());
      TEST(d.isValid());
      
      TESTEQUAL((unsigned int)2, d.getDimension(0));
      TESTEQUAL((unsigned int)5, d.getDimension(1));
      SHOULDFAIL(d.getDimension(2));
      TESTEQUAL((unsigned int)2, d.getDimensionCount());
    }

  } // RunTests()



} // namespace nta

