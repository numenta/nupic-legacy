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
 * Implementation of unit tests for NearestNeighbor
 */     

#include <nta/math/stl_io.hpp>
#include <nta/math/NearestNeighbor.hpp>
#include "NearestNeighborUnitTest.hpp"

using namespace std;

// Work around terrible Windows legacy issue - min and max global macros!!!
#ifdef max
#undef max
#endif

namespace nta {    

#define TEST_LOOP(M)                                  \
  for (nrows = 1, ncols = M, zr = 15;                 \
       nrows < M;                                     \
       nrows += M/10, ncols -= M/10, zr = ncols/10)   \

#define M 64
//
//  //--------------------------------------------------------------------------------
//  void NearestNeighborUnitTest::unit_test_rowLpDist()
//  {
//    if (0) { // Visual tests, off by default
//      
//      UInt ncols = 11, nrows = 7, zr = 2;      
//      Dense<UInt, double> dense(nrows, ncols, zr);
//      NearestNeighbor<SparseMatrix<UInt, double> > sparse(nrows, ncols, dense.begin());
//      std::vector<double> x(ncols, 0);
//
//      for (UInt i = 0; i != ncols; ++i)
//        x[i] = i % 2;
//
//      cout << dense << endl;
//      cout << endl << x << endl;
//
//      // L0
//      for (UInt i = 0; i != nrows; ++i) {
//        cout << "L0 " << i << " "
//             << dense.rowL0Dist(i, x.begin()) << " "
//             << sparse.rowL0Dist(i, x.begin()) 
//             << endl;
//      }
//
//      // L1 
//      for (UInt i = 0; i != nrows; ++i) {
//        cout << "L1 " << i << " "
//             << dense.rowLpDist(1.0, i, x.begin()) << " " 
//             << sparse.rowL1Dist(i, x.begin()) 
//             << endl;
//      }
//
//      // L2
//      for (UInt i = 0; i != nrows; ++i) {
//        cout << "L2 " << i << " "
//             << dense.rowLpDist(2.0, i, x.begin()) << " "
//             << sparse.rowL2Dist(i, x.begin()) 
//             << endl;
//      }
//
//      // Lmax
//      for (UInt i = 0; i != nrows; ++i) {
//        cout << "Lmax " << i << " "
//             << dense.rowLMaxDist(i, x.begin()) << " "
//             << sparse.rowLMaxDist(i, x.begin()) 
//             << endl;
//      }
//
//      // Lp
//      for (UInt i = 0; i != nrows; ++i) {
//        cout << "Lp " << i << " "
//             << dense.rowLpDist(.35, i, x.begin()) << " "
//             << sparse.rowLpDist(.35, i, x.begin()) 
//             << endl;
//      }
//    } // End visual tests
//
//    { // Automated tests
//      UInt ncols = 5, nrows = 7, zr = 2;
//
//      TEST_LOOP(M) {
//
//        if (nrows == 0)
//          continue;
//
//        Dense<UInt, double> dense(nrows, ncols, zr);
//        NearestNeighbor<SparseMatrix<UInt, double> > sparse(nrows, ncols, dense.begin());
//
//        std::vector<double> x(ncols, 0);
//        for (UInt i = 0; i < ncols; ++i)
//          x[i] = Real(i);
//
//        for (double p = 0.0; p < 2.5; p += .5) {
//
//          UInt row = rng_->getUInt32(nrows);
//
//          sparse.decompact();
//          double d1 = dense.rowLpDist(p, row, x.begin());
//          double d2 = sparse.rowLpDist(p, row, x.begin());
//          {
//            std::stringstream str;
//            str << "rowLpDist A " << nrows << "X" << ncols << "/" << zr
//                << " - non compact";
//            TEST(nta::nearlyEqual(d1, d2));
//          }
//
//          sparse.compact();
//          d2 = sparse.rowLpDist(p,row, x.begin());
//          {
//            std::stringstream str;
//            str << "rowLpDist B " << nrows << "X" << ncols << "/" << zr
//                << " - compact";
//            TEST(nta::nearlyEqual(d1, d2));
//
//          }
//        }
//
//        UInt row = rng_->getUInt32(nrows);
//
//        sparse.decompact();
//        double d1 = dense.rowLMaxDist(row, x.begin());
//        double d2 = sparse.rowLMaxDist(row, x.begin());
//        {
//          std::stringstream str;
//          str << "rowLMaxDist A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//            TEST(nta::nearlyEqual(d1, d2));
//        }
//        
//        sparse.compact();
//        d2 = sparse.rowLMaxDist(row, x.begin());
//        {
//          std::stringstream str;
//          str << "rowLMaxDist B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          TEST(nta::nearlyEqual(d1, d2));
//        }
//      }
//    } // End automated tests
//  }
//
//  //--------------------------------------------------------------------------------
//  void NearestNeighborUnitTest::unit_test_LpDist()
//  {
//    if (0) { // Visual tests, off by default
//
//      UInt ncols = 11, nrows = 7, zr = 2;
//      Dense<UInt, double> dense(nrows, ncols, zr);
//      NearestNeighbor<SparseMatrix<UInt, double> > sparse(nrows, ncols, dense.begin());
//      std::vector<double> x(ncols, 0), distances(nrows, 0);
//
//      for (UInt i = 0; i != ncols; ++i)
//        x[i] = i % 2;    
//
//      cout << dense << endl << x << endl << endl;
//
//      // L0   
//      cout << "L0" << endl;
//      dense.L0Dist(x.begin(), distances.begin());
//      cout << distances << endl;
//      sparse.L0Dist(x.begin(), distances.begin());   
//      cout << distances << endl;
//      cout << endl;
//
//      // L1 
//      cout << "L1" << endl;
//      dense.LpDist(1.0, x.begin(), distances.begin());
//      cout << distances << endl;
//      sparse.L1Dist(x.begin(), distances.begin());
//      cout << distances << endl;
//      cout << endl;
//
//      // L2
//      cout << "L2" << endl;
//      dense.LpDist(2.0, x.begin(), distances.begin());
//      cout << distances << endl;
//      sparse.L2Dist(x.begin(), distances.begin());
//      cout << distances << endl;
//      cout << endl;
//
//      // LMax
//      cout << "LMax" << endl;
//      dense.LMaxDist(x.begin(), distances.begin());
//      cout << "dense: " << distances << endl;
//      sparse.LMaxDist(x.begin(), distances.begin());
//      cout << "sparse: " << distances << endl;
//      cout << endl;
//
//      // Lp
//      cout << "Lp" << endl;
//      dense.LpDist(.35, x.begin(), distances.begin());
//      cout << distances << endl;
//      sparse.LpDist(.35, x.begin(), distances.begin());
//      cout << distances << endl;
//      cout << endl;
//    } // End visual tests
//
//    if (1) { // Automated tests
//      
//      UInt ncols = 5, nrows = 7, zr = 2;
//
//      TEST_LOOP(M) {
//
//        if (nrows == 0)
//          continue;
//
//        Dense<UInt, double> dense(nrows, ncols, zr);
//        NearestNeighbor<SparseMatrix<UInt, double> > sparse(nrows, ncols, dense.begin());
//
//        std::vector<double> x(ncols, 0), yref(nrows, 0), y(nrows, 0);
//        for (UInt i = 0; i < ncols; ++i)
//          x[i] = Real(i);
//        
//        for (double p = 0.0; p < 2.5; p += .5) {
//
//          sparse.decompact();
//          dense.LpDist(p, x.begin(), yref.begin());
//          sparse.LpDist(p, x.begin(), y.begin());
//          {
//            std::stringstream str;
//            str << "LpDist A " << nrows << "X" << ncols << "/" << zr
//                << " - non compact";
//            CompareVectors(nrows, y.begin(), yref.begin(), str.str().c_str());
//          }     
//         
//          sparse.compact();
//          sparse.LpDist(p, x.begin(), y.begin());
//          {
//            std::stringstream str;
//            str << "LpDist B " << nrows << "X" << ncols << "/" << zr
//                << " - compact";
//            CompareVectors(nrows, y.begin(), yref.begin(), str.str().c_str());
//          }
//        }
//
//        sparse.decompact();
//        dense.LMaxDist(x.begin(), yref.begin());
//        sparse.LMaxDist(x.begin(), y.begin());
//
//        {
//          std::stringstream str;
//          str << "LMaxDist A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          CompareVectors(nrows, y.begin(), yref.begin(), str.str().c_str());
//        }
//   
//        sparse.compact();
//        sparse.LMaxDist(x.begin(), y.begin());
//
//        {
//          std::stringstream str;
//          str << "LMaxDist B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          CompareVectors(nrows, y.begin(), yref.begin(), str.str().c_str());
//        }
//      }
//    } // End automated tests
//  }
//
//  //--------------------------------------------------------------------------------
//  void NearestNeighborUnitTest::unit_test_LpNearest()
//  {
//    if (0) { // Visual tests, off by default
//      
//      UInt ncols = 11, nrows = 7, zr = 2;
//
//      Dense<UInt, double> dense(nrows, ncols, zr);
//      for (UInt i = 0; i != nrows; ++i)
//        for (UInt j = 0; j != ncols; ++j)
//          dense.at(i,j) = rng_->getReal64() * 2.0;
//      NearestNeighbor<SparseMatrix<UInt, double> > sparse(nrows, ncols, dense.begin());
//      std::vector<double> x(ncols, 0);
//      std::vector<std::pair<UInt, double> > nn1(nrows), nn2(nrows);
//
//      for (UInt i = 0; i != ncols; ++i)
//        x[i] = rng_->getReal64() * 2.0;
//      cout << dense << endl << x << endl << endl;
//
//      // L0
//      cout << "L0" << endl;
//      dense.L0Nearest(x.begin(), nn1.begin(), nrows);
//      sparse.L0Nearest(x.begin(), nn2.begin(), nrows);
//      for (UInt i = 0; i != nrows; ++i)
//        cout << nn1[i].first << "," << nn1[i].second << " ";
//      cout << endl;
//      for (UInt i = 0; i != nrows; ++i)
//        cout << nn2[i].first << "," << nn2[i].second << " ";
//      cout << endl;
//
//      // L1 
//      cout << "L1" << endl;
//      dense.LpNearest(1.0, x.begin(), nn1.begin(), nrows);
//      sparse.L1Nearest(x.begin(), nn2.begin(), nrows);
//      for (UInt i = 0; i != nrows; ++i)
//        cout << nn1[i].first << "," << nn1[i].second << " ";
//      cout << endl;
//      for (UInt i = 0; i != nrows; ++i)
//        cout << nn2[i].first << "," << nn2[i].second << " ";
//      cout << endl << endl;
//          
//      // L2
//      cout << "L2" << endl;
//      dense.LpNearest(2.0, x.begin(), nn1.begin(), nrows);
//      sparse.L2Nearest(x.begin(), nn2.begin(), nrows);
//      for (UInt i = 0; i != nrows; ++i)
//        cout << nn1[i].first << "," << nn1[i].second << " ";
//      cout << endl;
//      for (UInt i = 0; i != nrows; ++i)
//        cout << nn2[i].first << "," << nn2[i].second << " ";
//      cout << endl << endl;
//
//      // LMax     
//      cout << "LMax" << endl;
//      dense.LMaxNearest(x.begin(), nn1.begin(), nrows);
//      sparse.LMaxNearest(x.begin(), nn2.begin(), nrows);
//      for (UInt i = 0; i != nrows; ++i)
//        cout << nn1[i].first << "," << nn1[i].second << " ";
//      cout << endl;
//      for (UInt i = 0; i != nrows; ++i)
//        cout << nn2[i].first << "," << nn2[i].second << " ";
//      cout << endl << endl;
//
//      // Lp
//      cout << "Lp" << endl;
//      dense.LpNearest(.35, x.begin(), nn1.begin(), nrows);
//      sparse.LpNearest(.35, x.begin(), nn2.begin(), nrows);
//      for (UInt i = 0; i != nrows; ++i)
//        cout << nn1[i].first << "," << nn1[i].second << " ";
//      cout << endl;
//      for (UInt i = 0; i != nrows; ++i)
//        cout << nn2[i].first << "," << nn2[i].second << " ";
//      cout << endl << endl;
//    } // End visual tests
//
//    if (1) { // Automated tests
//
//      UInt ncols = 5, nrows = 7, zr = 2;
//
//      TEST_LOOP(M) {
//
//        if (nrows == 0)
//          continue;
//
//        Dense<UInt, double> dense(nrows, ncols, zr);
//        NearestNeighbor<SparseMatrix<UInt, double> > sparse(nrows, ncols, dense.begin());
//
//        std::vector<double> x(ncols, 0);
//        std::vector<std::pair<UInt, double> > yref(nrows), y(nrows);
//        for (UInt i = 0; i < ncols; ++i)
//          x[i] = Real(i);
//        
//        for (double p = 0.0; p < 2.5; p += .5) {
//
//          sparse.decompact();
//          dense.LpNearest(p, x.begin(), yref.begin(), nrows);
//          sparse.LpNearest(p, x.begin(), y.begin(), nrows);
//          {
//            std::stringstream str;
//            str << "LpNearest A " << nrows << "X" << ncols << "/" << zr
//                << " - non compact";
//            Compare(y, yref, str.str().c_str());
//          }     
//         
//          sparse.compact();
//          sparse.LpNearest(p, x.begin(), y.begin(), nrows);
//          {
//            std::stringstream str;
//            str << "LpNearest B " << nrows << "X" << ncols << "/" << zr
//                << " - compact";
//            Compare(y, yref, str.str().c_str());
//          }
//
//          sparse.decompact();
//          dense.LpNearest(p, x.begin(), yref.begin());
//          sparse.LpNearest(p, x.begin(), y.begin());
//          {
//            std::stringstream str;
//            str << "LpNearest C " << nrows << "X" << ncols << "/" << zr
//                << " - non compact";
//            Compare(y, yref, str.str().c_str());
//          }
//          
//          sparse.compact();
//          sparse.LpNearest(p, x.begin(), y.begin());
//          {
//            std::stringstream str;
//            str << "LpNearest D " << nrows << "X" << ncols << "/" << zr
//                << " - compact";
//            Compare(y, yref, str.str().c_str());
//          }
//        }
//      }
//    } // End automated tests
//  }   
//
//  //--------------------------------------------------------------------------------
//  void NearestNeighborUnitTest::unit_test_dotNearest()
//  {
//    UInt ncols, nrows, zr, i, j;
//    ncols = 5;
//    nrows = 7;
//    zr = 2;
//
//    DenseMat dense(nrows, ncols, zr);
//
//    std::vector<Real> x(ncols, 0);
//    for (i = 0; i < ncols; ++i)
//      x[i] = Real(20*i);
//
//    pair<UInt, double> res(0, 0), ref = dense.dotNearest(x.begin());
//
//    NearestNeighbor<SparseMatrix<UInt,Real,Int,Real> > smc(nrows, ncols, dense.begin());
//    res = smc.dotNearest(x.begin());
//    ComparePair(res, ref, "dotNearest compact 1");
//
//    {
//      nrows *= 10;
//      ncols *= 10;
//    
//      Dense<UInt, double> dense2(nrows, ncols);
//      for (i = 0; i < nrows; ++i)
//        for (j = 0; j < ncols; ++j) {
//          dense2.at(i,j) = rng_->getReal64();
//          if (dense2.at(i,j) < .8)
//            dense2.at(i,j) = 0;
//        }
//    
//      NearestNeighbor<SparseMatrix<UInt, double> > sm2(nrows, ncols, dense2.begin());
//    
//      std::vector<double> x2(ncols, 0);
//      for (j = 0; j < ncols; ++j)
//        x2[j] = rng_->getReal64();
//    
//      ref = dense2.dotNearest(x2.begin());
//    
//      res.first = 0; res.second = 0;
//      res = sm2.dotNearest(x2.begin());
//      ComparePair(res, ref, "dotNearest compact 2");
//    }
//
//    {
//      TEST_LOOP(M) {
//
//        DenseMat dense2(nrows, ncols, zr);
//        NearestNeighbor<SparseMatrix<UInt,Real,Int,Real> > sm2(nrows, ncols, dense2.begin());
//
//        std::vector<Real> x2(ncols, 0), yref2(nrows, 0), y2(nrows, 0);
//        for (i = 0; i < ncols; ++i)
//          x2[i] = Real(i);
//
//        sm2.decompact();
//        ref = dense2.dotNearest(x2.begin());
//        res.first = 0; res.second = 0;
//        res = sm2.dotNearest(x2.begin());
//        {
//          std::stringstream str;
//          str << "dotNearest A " << nrows << "X" << ncols << "/" << zr
//              << " - non compact";
//          ComparePair(res, ref, str.str().c_str());
//        }
//
//        sm2.compact();
//        res.first = 0; res.second = 0;
//        res = sm2.dotNearest(x2.begin());
//        {
//          std::stringstream str;
//          str << "dotNearest B " << nrows << "X" << ncols << "/" << zr
//              << " - compact";
//          ComparePair(res, ref, str.str().c_str());
//        }
//      }
//    }
//  }
//
  //--------------------------------------------------------------------------------
  void NearestNeighborUnitTest::RunTests()
  {
    /*
    unit_test_rowLpDist();
    unit_test_LpDist();
    unit_test_LpNearest();
    */
    //unit_test_dotNearest();  
  }
    
  //--------------------------------------------------------------------------------
} // end namespace nta


   
