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
 * Implementation of unit testing for class Domain
 */  
              
//#include <nta/common/version.hpp>
#include "DomainUnitTest.hpp"

using namespace std;  

namespace nta {

  //--------------------------------------------------------------------------------
  void DomainUnitTest::RunTests()
  {
//
//    {
//      /* Doesn't work on shona ???!???
//      Domain<UInt, 3> d(0, 0, 4, 1, 0, 5, 2, 0, 6);
//      Test("Domain list constructor 1", d[0].getDim(), (UInt) 0);
//      Test("Domain list constructor 2", d[0].getLB(), (UInt) 0);
//      Test("Domain list constructor 3", d[0].getUB(), (UInt) 4);
//      Test("Domain list constructor 4", d[1].getDim(), (UInt) 1);
//      Test("Domain list constructor 5", d[1].getLB(), (UInt) 0);
//      Test("Domain list constructor 6", d[1].getUB(), (UInt) 5);
//      Test("Domain list constructor 7", d[2].getDim(), (UInt) 2);
//      Test("Domain list constructor 8", d[2].getLB(), (UInt) 0);
//      Test("Domain list constructor 9", d[2].getUB(), (UInt) 6);
//      */
//    }
//
//    { // DimRange includes
//      DimRange<UInt> dr(0, 0, 3);
//      Test("DimRange includes 1", dr.includes(0), true);
//      Test("DimRange includes 2", dr.includes(1), true);
//      Test("DimRange includes 3", dr.includes(2), true);
//      Test("DimRange includes 4", dr.includes(3), false);
//  
//      DimRange<UInt> dr2(0, 1, 1);
//      Test("DimRange includes 4", dr2.includes(0), false);
//      Test("DimRange includes 5", dr2.includes(1), true);
//      Test("DimRange includes 6", dr2.includes(2), false);
//
//      DimRange<UInt> dr3(0, 0, 1);
//      Test("DimRange includes 7", dr3.includes(0), true);
//      Test("DimRange includes 8", dr3.includes(1), false);
//      Test("DimRange includes 9", dr3.includes(2), false);
//
//      DimRange<UInt> dr4(0, 0, 0);
//      Test("DimRange includes 10", dr4.includes(0), true);
//      Test("DimRange includes 11", dr4.includes(1), false);
//      Test("DimRange includes 12", dr4.includes(2), false);
//
//      DimRange<UInt> dr5(0, 0, 1);
//      Test("DimRange includes 13", dr5.includes(0), true);
//      Test("DimRange includes 14", dr5.includes(1), false);
//      Test("DimRange includes 15", dr5.includes(2), false);
//    }
//
//    {
//      Domain<UInt> d(Index<UInt, 3>(4, 5, 6));
//      Test("Domain half-space constructor 1", d[0].getDim(), (UInt) 0);
//      Test("Domain half-space constructor 2", d[0].getLB(), (UInt) 0);
//      Test("Domain half-space constructor 3", d[0].getUB(), (UInt) 4);
//      Test("Domain half-space constructor 4", d[1].getDim(), (UInt) 1);
//      Test("Domain half-space constructor 5", d[1].getLB(), (UInt) 0);
//      Test("Domain half-space constructor 6", d[1].getUB(), (UInt) 5);
//      Test("Domain half-space constructor 7", d[2].getDim(), (UInt) 2);
//      Test("Domain half-space constructor 8", d[2].getLB(), (UInt) 0);
//      Test("Domain half-space constructor 9", d[2].getUB(), (UInt) 6);
//    }
//
//    {
//      Domain<UInt> d(Index<UInt, 3>(4, 5, 6), Index<UInt, 3>(7, 8, 9));
//      Test("Domain lb/ub constructor 1", d[0].getDim(), (UInt) 0);
//      Test("Domain lb/ub constructor 2", d[0].getLB(), (UInt) 4);
//      Test("Domain lb/ub constructor 3", d[0].getUB(), (UInt) 7);
//      Test("Domain lb/ub constructor 4", d[1].getDim(), (UInt) 1);
//      Test("Domain lb/ub constructor 5", d[1].getLB(), (UInt) 5);
//      Test("Domain lb/ub constructor 6", d[1].getUB(), (UInt) 8);
//      Test("Domain lb/ub constructor 7", d[2].getDim(), (UInt) 2);
//      Test("Domain lb/ub constructor 8", d[2].getLB(), (UInt) 6);
//      Test("Domain lb/ub constructor 9", d[2].getUB(), (UInt) 9);
//    }
//
//    {
//      Domain<UInt> d(Index<UInt, 3>(4, 5, 6));
//      Domain<UInt> d2(d);
//      Test("Domain copy constructor 1", d2[0].getDim(), (UInt) 0);
//      Test("Domain copy constructor 2", d2[0].getLB(), (UInt) 0);
//      Test("Domain copy constructor 3", d2[0].getUB(), (UInt) 4);
//      Test("Domain copy constructor 4", d2[1].getDim(), (UInt) 1);
//      Test("Domain copy constructor 5", d2[1].getLB(), (UInt) 0);
//      Test("Domain copy constructor 6", d2[1].getUB(), (UInt) 5);
//      Test("Domain copy constructor 7", d2[2].getDim(), (UInt) 2);
//      Test("Domain copy constructor 8", d2[2].getLB(), (UInt) 0);
//      Test("Domain copy constructor 9", d2[2].getUB(), (UInt) 6);
//    }
//
//    {
//      Domain<UInt> d(Index<UInt, 3>(4, 5, 6));
//      Domain<UInt> d2 = d;
//      Test("Domain assignment operator 1", d2[0].getDim(), (UInt) 0);
//      Test("Domain assignment operator 2", d2[0].getLB(), (UInt) 0);
//      Test("Domain assignment operator 3", d2[0].getUB(), (UInt) 4);
//      Test("Domain assignment operator 4", d2[1].getDim(), (UInt) 1);
//      Test("Domain assignment operator 5", d2[1].getLB(), (UInt) 0);
//      Test("Domain assignment operator 6", d2[1].getUB(), (UInt) 5);
//      Test("Domain assignment operator 7", d2[2].getDim(), (UInt) 2);
//      Test("Domain assignment operator 8", d2[2].getLB(), (UInt) 0);
//      Test("Domain assignment operator 9", d2[2].getUB(), (UInt) 6);
//    }
//
//    {
//      Domain<UInt> d(Index<UInt, 3>(4, 5, 6), Index<UInt, 3>(7, 8, 9));
//      Index<UInt, 3> lb, ub, dims;
//      d.getLB(lb);
//      Test("Domain getLB 1", lb[0], (UInt) 4);
//      Test("Domain getLB 2", lb[1], (UInt) 5);
//      Test("Domain getLB 3", lb[2], (UInt) 6);
//      d.getUB(ub);
//      Test("Domain getUB 1", ub[0], (UInt) 7);
//      Test("Domain getUB 2", ub[1], (UInt) 8);
//      Test("Domain getUB 3", ub[2], (UInt) 9);
//      d.getDims(dims);
//      Test("Domain getDims 1", dims[0], (UInt) 0);
//      Test("Domain getDims 2", dims[1], (UInt) 1);
//      Test("Domain getDims 3", dims[2], (UInt) 2);
//    }
//
//    {
//      Domain<UInt> d(Index<UInt, 5>(1, 2, 4, 5, 6), Index<UInt, 5>(1, 5, 7, 5, 9));
//
//      Index<UInt, 3> openDims;
//      Test("Domain getOpenDims 1", d.getNOpenDims(), (UInt)3);
//      d.getOpenDims(openDims);
//      Test("Domain getOpenDims 2", openDims[0], (UInt) 1);
//      Test("Domain getOpenDims 3", openDims[1], (UInt) 2);
//      Test("Domain getOpenDims 4", openDims[2], (UInt) 4);
//
//      Index<UInt, 2> closedDims;
//      Test("Domain getClosedDims 1", d.getNClosedDims(), (UInt)2);
//      d.getClosedDims(closedDims);
//      Test("Domain getClosedDims 2", closedDims[0], (UInt) 0);
//      Test("Domain getClosedDims 3", closedDims[1], (UInt) 3);
//    }  
//
//    {
//      Domain<UInt> d(Index<UInt, 5>(1, 2, 4, 5, 6), Index<UInt, 5>(1, 5, 7, 5, 9));
//
//      Index<UInt, 5> idx, lb(1, 2, 4, 5, 6), ub(1, 5, 7, 5, 9);
// 
//      do {
//        if (lb <= idx && idx < ub)
//          Test("Domain includes 1", d.includes(idx), true);
//        else
//          Test("Domain includes 2", d.includes(idx), false);
//          
//      } while (idx.increment(ub));
//
//      Domain<UInt> d1(Index<UInt,4>(0,0,0,0), Index<UInt,4>(1,0,1,0));
//    }
//
//    {
//      DimRange<UInt> r;
//      Test("DimRange default constructor 1", r.getDim(), (UInt)0);
//      Test("DimRange default constructor 2", r.getLB(), (UInt)0);
//      Test("DimRange default constructor 3", r.getUB(), (UInt)0);
//    }
//
//    {
//      DimRange<UInt> r(1, 4, 7);
//      Test("DimRange constructor 1", r.getDim(), (UInt)1);
//      Test("DimRange constructor 2", r.getLB(), (UInt)4);
//      Test("DimRange constructor 3", r.getUB(), (UInt)7);
//    }
//
//    {
//      DimRange<UInt> r(1, 4, 7), r1(r);
//      Test("DimRange copy constructor 1", r1.getDim(), (UInt)1);
//      Test("DimRange copy constructor 2", r1.getLB(), (UInt)4);
//      Test("DimRange copy constructor 3", r1.getUB(), (UInt)7);
//    }
//
//    {
//      DimRange<UInt> r(1, 4, 7), r1 = r;
//      Test("DimRange assignment operator 1", r1.getDim(), (UInt)1);
//      Test("DimRange assignment operator 2", r1.getLB(), (UInt)4);
//      Test("DimRange assignment operator 3", r1.getUB(), (UInt)7);
//    }
//
//    {
//      DimRange<UInt> r;   
//      r.set(1, 4, 7);
//      Test("DimRange set 1", r.getDim(), (UInt)1);
//      Test("DimRange set 2", r.getLB(), (UInt)4);
//      Test("DimRange set 3", r.getUB(), (UInt)7);
//    }
//
//    {
//      DimRange<UInt> r(1, 4, 7);
//      Test("DimRange empty 1", r.empty(), false);
//      r.set(1, 4, 4);
//      Test("DimRange empty 2", r.empty(), true);
//    }
//
//    {
//      DimRange<UInt> r(1, 4, 7);
//      for (UInt i = 0; i < 10; ++i)
//        if (r.getLB() <= i && i < r.getUB())
//          Test("DimRange includes 1", r.includes(i), true);
//        else
//          Test("DimRange includes 2", r.includes(i), false);
//    }
//
//    {
//      typedef Index<UInt, 2> I2;
//      typedef Index<UInt, 3> I3;
//
//      Domain<UInt> d21(I2(0, 0), I2(9, 9));
//      Test("Domain size_elts 1", d21.size_elts(), (UInt)81);
//
//      Domain<UInt> d22(I2(1, 2), I2(9, 8));
//      Test("Domain size_elts 2", d22.size_elts(), (UInt)48);
//
//      Domain<UInt> d23(I2(1, 4), I2(9, 5));
//      Test("Domain size_elts 3", d23.size_elts(), (UInt)8);
//      Test("Domain empty 1", d23.empty(), false);
//
//      Domain<UInt> d24(I2(1, 4), I2(9, 4));
//      Test("Domain size_elts 4", d24.size_elts(), (UInt)0);
//      Test("Domain empty 2", d24.empty(), true);
//      
//      Domain<UInt> d31(I3(0, 1, 2), I3(10, 9, 8));
//      Test("Domain size_elts 5", d31.size_elts(), (UInt)480);
//    }
  } 

  //--------------------------------------------------------------------------------
  
} // namespace nta


