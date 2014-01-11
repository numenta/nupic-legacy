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
 * Implementation for maths unit tests
 */

//#include <nta/common/utils.hpp>
#include <nta/math/array_algo.hpp>

#include "MathsTest.hpp"

#include <nta/math/math.hpp>

using namespace std;

namespace nta {    

//  //--------------------------------------------------------------------------------
//  void MathsTest::unitTestNearlyZero()
//  {
//    Test("nearlyZero Reals 1", true, nearlyZero(Real(0.0000000001)));
//    Test("nearlyZero Reals 2", true, nearlyZero(0.0));
//    Test("nearlyZero Reals 3", false, nearlyZero(1.0));
//    Test("nearlyZero Reals 4", false, nearlyZero(0.01));
//    Test("nearlyZero Reals 5", false, nearlyZero(-0.01));
//    Test("nearlyZero Reals 6", false, nearlyZero(-1.0));
//    Test("nearlyZero Reals 7", false, nearlyZero(2.0));
//    Test("nearlyZero Reals 8", false, nearlyZero(1.99999999));
//    Test("nearlyZero Reals 9", false, nearlyZero(-2.00000001));
//    Test("nearlyZero Reals 10", false, nearlyZero(-1.99999999));
//  }
//
//  //--------------------------------------------------------------------------------
//  void MathsTest::unitTestNearlyEqual()
//  {
//    Test("nearlyEqual Reals 1", true, nearlyEqual(Real(0.0), Real(0.0000000001)));
//    Test("nearlyEqual Reals 2", true, nearlyEqual(0.0, 0.0));
//    Test("nearlyEqual Reals 3", false, nearlyEqual(0.0, 1.0));
//    Test("nearlyEqual Reals 4", false, nearlyEqual(0.0, 0.01));
//    Test("nearlyEqual Reals 5", false, nearlyEqual(0.0, -0.01));
//    Test("nearlyEqual Reals 6", false, nearlyEqual(0.0, -1.0));
//    Test("nearlyEqual Reals 7", true, nearlyEqual(Real(2.0), Real(2.000000001)));
//    Test("nearlyEqual Reals 8", true, nearlyEqual(Real(2.0), Real(1.999999999)));
//    Test("nearlyEqual Reals 9", true, nearlyEqual(Real(-2.0), Real(-2.000000001)));
//    Test("nearlyEqual Reals 10", true, nearlyEqual(Real(-2.0), Real(-1.999999999)));
//  }
//
//  //--------------------------------------------------------------------------------
//  void MathsTest::unitTestNearlyEqualVector()
//  { 
//    vector<Real> v1, v2;
//    
//    {
//      Test("nearlyEqualVector, empty vectors", true, nearlyEqualVector(v1, v2));
//      
//      v2.push_back(1);
//      Test("nearlyEqualVector, different sizes", false, nearlyEqualVector(v1, v2));
//      
//      v1.push_back(1);
//      Test("nearlyEqualVector, 1 element", true, nearlyEqualVector(v1, v2));
//      
//#if 0
//      for(UInt i=0; i<2048; ++i) {
//        Real v = Real(rng_->get() % 256)/256.0;
//        v1.push_back(v);
//        v2.push_back(v);
//      }
//      Test("nearlyEqualVector, 2049 elements 1", true, nearlyEqualVector(v1, v2));
//      
//      v2[512] += 1.0;
//      Test("nearlyEqualVector, 2049 elements 2", false, nearlyEqualVector(v1, v2));
//      
//      v1.clear(); v2.clear();
//      Test("nearlyEqualVector, after clear", true, nearlyEqualVector(v1, v2));
//#endif
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void MathsTest::unitTestNormalize()
//  {
//    {
//      vector<Real> v1(3), answer(3);
//
//      {
//        vector<Real> empty1;
//        normalize(empty1.begin(), empty1.end());
//        Test("Normalize vector<Real>, empty", true, nearlyEqualVector(empty1, empty1));
//      }
//	  
//      {
//        v1[0] = Real(0.0); v1[1] = Real(0.0); v1[2] = Real(0.0);
//        answer[0] = Real(0.0); answer[1] = Real(0.0); answer[2] = Real(0.0);
//        normalize(v1.begin(), v1.end());
//        Test("Normalize vector<Real> 11", true, nearlyZero(sum(v1)));
//        Test("Normalize vector<Real> 12", true, nearlyEqualVector(v1, answer));
//      }
//
//      {
//        v1[0] = Real(1.0); v1[1] = Real(1.0); v1[2] = Real(1.0);
//        answer[0] = Real(1.0/3.0); answer[1] = Real(1.0/3.0); answer[2] = Real(1.0/3.0);
//        normalize(v1.begin(), v1.end());
//        Real s = sum(v1);
//        Test("Normalize vector<Real> 21", true, nearlyEqual(s, Real(1.0)));
//        Test("Normalize vector<Real> 22", true, nearlyEqualVector(v1, answer));
//      }
//
//      {
//        v1[0] = Real(0.5); v1[1] = Real(0.5); v1[2] = Real(0.5);
//        answer[0] = Real(0.5/1.5); answer[1] = Real(0.5/1.5); answer[2] = Real(0.5/1.5);
//        normalize(v1.begin(), v1.end());
//        Real s = sum(v1);
//        Test("Normalize vector<Real> 31", true, nearlyEqual(s, Real(1.0)));
//        Test("Normalize vector<Real> 32", true, nearlyEqualVector(v1, answer));
//      }
//
//      {
//        v1[0] = Real(1.0); v1[1] = Real(0.5); v1[2] = Real(1.0);
//        answer[0] = Real(1.0/2.5); answer[1] = Real(0.5/2.5); answer[2] = Real(1.0/2.5);
//        normalize(v1.begin(), v1.end());
//        Real s = sum(v1);
//        Test("Normalize vector<Real> 41", true, nearlyEqual(s, Real(1.0)));
//        Test("Normalize vector<Real> 42", true, nearlyEqualVector(v1, answer));
//      }
//
//      { // Test normalizing to non-1.0
//        v1[0] = Real(1.0); v1[1] = Real(0.5); v1[2] = Real(1.0);
//        answer[0] = Real(3.0/2.5); answer[1] = Real(1.5/2.5); answer[2] = Real(3.0/2.5);
//        normalize(v1.begin(), v1.end(), 1.0, 3.0);
//        Real s = sum(v1);
//        Test("Normalize vector<Real> 51", true, nearlyEqual(s, Real(3.0)));
//        Test("Normalize vector<Real> 52", true, nearlyEqualVector(v1, answer));
//      }
//    }
//	
//    { // normalize
//      std::vector<Real> v1(3), answer(3);
//
//      {
//        std::vector<Real> empty1;
//        normalize(empty1.begin(), empty1.end());
//        Test("Normalize VectorType, empty", true, nearlyEqualVector(empty1, empty1));
//      }
//
//      {
//        v1[0] = 0.0; v1[1] = 0.0; v1[2] = 0.0;
//        answer[0] = 0.0; answer[1] = 0.0; answer[2] = 0.0;
//        normalize(v1.begin(), v1.end());
//        Test("Normalize VectorType 11", true, nearlyZero(sum(v1)));
//        Test("Normalize VectorType 12", true, nearlyEqualVector(v1, answer));
//      }
//
//      {
//        v1[0] = Real(1.0); v1[1] = Real(1.0); v1[2] = Real(1.0);
//        answer[0] = Real(1.0/3.0); answer[1] = Real(1.0/3.0); answer[2] = Real(1.0/3.0);
//        normalize(v1.begin(), v1.end());
//        Real s = sum(v1);
//        Test("Normalize VectorType 21", true, nearlyEqual(s, Real(1.0)));
//        Test("Normalize VectorType 22", true, nearlyEqualVector(v1, answer));
//      }
//
//      {
//        v1[0] = Real(0.5); v1[1] = Real(0.5); v1[2] = Real(0.5);
//        answer[0] = Real(0.5/1.5); answer[1] = Real(0.5/1.5); answer[2] = Real(0.5/1.5);
//        normalize(v1.begin(), v1.end());
//        Real s = sum(v1);
//        Test("Normalize VectorType 31", true, nearlyEqual(s, Real(1.0)));
//        Test("Normalize VectorType 32", true, nearlyEqualVector(v1, answer));
//      }
//
//      {
//        v1[0] = Real(1.0); v1[1] = Real(0.5); v1[2] = Real(1.0);
//        answer[0] = Real(1.0/2.5); answer[1] = Real(0.5/2.5); answer[2] = Real(1.0/2.5);
//        normalize(v1.begin(), v1.end());
//        Real s = sum(v1);
//        Test("Normalize VectorType 41", true, nearlyEqual(s, Real(1.0)));
//        Test("Normalize VectorType 42", true, nearlyEqualVector(v1, answer));
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void MathsTest::unitTestVectorToStream()
//  { /*
//    {
//      vector<Real> v1, v2;
//      stringstream s;
//      s << v1;
//      s >> v2;
//      Test("Empty vector<Real> to stream", true, nearlyEqualVector(v1, v2));
//    }
//
//    {
//      vector<Real> v1(3), v2(3);
//      v1[0] = 1.0; v1[1] = 2.0; v1[2] = 3.0;
//      stringstream s;
//      s << v1;
//      s >> v2;
//      Test("vector<Real> to stream", true, nearlyEqualVector(v1, v2));
//    }
//
//    {
//      vector<Real> v1(3);
//      v1[0] = 1.0; v1[1] = numeric_limits<Real>::infinity(); v1[2] = 3.0;
//      stringstream s, answer;
//#ifdef WIN32
//      answer << "3 1 1.#INF 3 ";
//#else
//      answer << "3 1 inf 3 ";
//#endif
//      s << v1;
//      bool comp = s.str() == answer.str();
//      Test("vector<Real> infinity to stream", true, comp);
//    }
//
//    {
//      vector<Real> v1(3);
//      v1[0] = 1.0; v1[1] = numeric_limits<Real>::quiet_NaN(); v1[2] = 3.0;
//      stringstream s, answer;
//#ifdef WIN32
//      answer << "3 1 1.#QNAN 3 ";
//#else
//      answer << "3 1 nan 3 ";
//#endif
//      s << v1;
//      bool comp = s.str() == answer.str();
//      Test("vector<Real> quiet_NaN to stream", true, comp);
//    }
//	  
//    {
//      vector<Real> v1(3);
//      v1[0] = 1.0; v1[1] = numeric_limits<Real>::signaling_NaN(); v1[2] = 3.0;
//      stringstream s, answer;
//#ifdef WIN32
//      answer << "3 1 1.#QNAN 3 ";
//#else
//      answer << "3 1 nan 3 ";
//#endif
//      s << v1;
//      bool comp = s.str() == answer.str();
//      Test("vector<Real> signaling_NaN to stream", true, comp);
//    }
//    */
//  }
//
//  //--------------------------------------------------------------------------------
//  void MathsTest::unitTestElemOps()
//  {
//    /*
//    const size_t S = 2048;
//
//    { // elem_minus_val constant
//      vector<Real> v1(S, 1), v2(S, 0);
//
//      elem_minus_val(v1.begin(), v1.end(), 1);
//      Test("elem_minus_val 1", true, equal(v1.begin(), v1.end(), v2.begin()));
//
//      fill(v2.begin(), v2.end(), Real(1));
//      elem_minus_val(v1.begin(), v1.end(), -1);
//      Test("elem_minus_val 2", true, equal(v1.begin(), v1.end(), v2.begin()));
//
//      fill(v2.begin(), v2.end(), Real(1));
//      elem_minus_val(v1.begin(), v1.begin(), 2);
//      Test("elem_minus_val 3", true, equal(v1.begin(), v1.end(), v2.begin()));
//
//      fill(v2.begin(), v2.end(), Real(1));
//      elem_minus_val(v1.end(), v1.end(), 2);
//      Test("elem_minus_val 4", true, equal(v1.begin(), v1.end(), v2.begin()));
//    }
//
//    { // elem_minus_val with an output range and a val
//      vector<Real> v1(S, 3), v2(S, 0), v3(S, 1.5);
//
//      elem_minus_val(v1.begin(), v1.end(), v2.begin(), 1.5);
//      Test("elem_minus_val 5", true, equal(v2.begin(), v2.end(), v3.begin()));
//
//      fill(v3.begin(), v3.end(), Real(4));
//      elem_minus_val(v1.begin(), v1.end(), v2.begin(), -1);
//      Test("elem_minus_val 6", true, equal(v2.begin(), v2.end(), v3.begin()));
//
//      fill(v3.begin(), v3.end(), Real(4));
//      elem_minus_val(v1.begin(), v1.begin(), v2.begin(), 2);
//      Test("elem_minus_val 7", true, equal(v2.begin(), v2.end(), v3.begin()));
//
//      fill(v2.begin(), v2.end(), Real(3));
//      elem_minus_val(v1.begin(), v1.begin(), v1.begin(), 2);
//      Test("elem_minus_val 8", true, equal(v1.begin(), v1.end(), v2.begin()));
//
//      fill(v2.begin(), v2.end(), Real(3));
//      elem_minus_val(v1.end(), v1.end(), v1.begin(), 2);
//      Test("elem_minus_val 9", true, equal(v1.begin(), v1.end(), v2.begin()));
//    }
//
//    { // elem_minus
//      vector<Real> v1(S, 3), v2(S, 1.5), v3(S, 0), v4(S, 1.5);
//
//      elem_minus(v1.begin(), v1.end(), v2.begin(), v3.begin());
//      Test("elem_minus 1", true, equal(v4.begin(), v4.end(), v3.begin()));
//
//      fill(v4.begin(), v4.end(), Real(1.5));
//      elem_minus(v1.begin(), v1.end(), v2.begin(), v1.begin());
//      Test("elem_minus 2", true, equal(v4.begin(), v4.end(), v1.begin()));
//
//      fill(v4.begin(), v4.end(), Real(0));
//      elem_minus(v1.begin(), v1.end(), v1.begin(), v1.begin());
//      Test("elem_minus 3", true, equal(v4.begin(), v4.end(), v1.begin()));
//
//      fill(v2.begin(), v2.end(), Real(0));
//      elem_minus(v1.begin(), v1.begin(), v1.begin(), v1.begin());
//      Test("elem_minus 4", true, equal(v1.begin(), v1.end(), v2.begin()));
//
//      fill(v2.begin(), v2.end(), Real(0));
//      elem_minus(v1.end(), v1.end(), v1.begin(), v1.begin());
//      Test("elem_minus 5", true, equal(v1.begin(), v1.end(), v2.begin()));
//    }
//
//    { // elem_div
//      vector<Real> v1(S, 3), v2(S, 2);
//
//      elem_div(v1.begin(), v1.end(), Real(1.5), Real(1e-30));
//      Test("elem_div 1", true, equal(v1.begin(), v1.end(), v2.begin()));
//
//      fill(v2.begin(), v2.end(), Real(-4));
//      elem_div(v1.begin(), v1.end(), Real(-.5), Real(1e-30));
//      Test("elem_div 2", true, equal(v1.begin(), v1.end(), v2.begin()));
//
//      fill(v2.begin(), v2.end(), Real(-4));
//      elem_div(v1.begin(), v1.begin(), Real(-.5), Real(1e-30));
//      Test("elem_div 3", true, equal(v1.begin(), v1.end(), v2.begin()));
//
//      fill(v2.begin(), v2.end(), Real(-4));
//      elem_div(v1.end(), v1.end(), Real(-.5), Real(1e-30));
//      Test("elem_div 4", true, equal(v1.begin(), v1.end(), v2.begin()));
//    }
//
//    { // elem_inv
//      vector<Real> v1(S, 3), v2(S, Real(1./3.));
//
//      elem_inv(v1.begin(), v1.end(), Real(1e-30));
//      Test("elem_inv 1", true, equal(v1.begin(), v1.end(), v2.begin()));
//
//      elem_inv(v1.begin(), v1.begin(), Real(1e-30));
//      Test("elem_inv 2", true, equal(v1.begin(), v1.end(), v2.begin()));
//
//      elem_inv(v1.end(), v1.end(), Real(1e-30));
//      Test("elem_inv 3", true, equal(v1.begin(), v1.end(), v2.begin()));
//    }
//    */
//  }
//
//  //--------------------------------------------------------------------------------
//  void MathsTest::unitTestWinnerTakesAll()
//  {
//    UInt nchildren, ncols, w, nreps;
//
//    nchildren = 21;
//    w = 125;
//    nreps = 1000;
//    
//    vector<UInt> boundaries(nchildren, 0);
//    
//    boundaries[0] = rng_->getUInt32(w) + 1;
//    for (UInt i = 1; i < (nchildren-1); ++i) 
//      boundaries[i] = boundaries[i-1] + (rng_->getUInt32(w) + 1);
//    ncols = nchildren * w;
//    boundaries[nchildren-1] = ncols;
//
//    for (UInt i = 0; i < nreps; ++i) {
//
//      vector<Real> x(ncols), v(ncols);
//      for (UInt j = 0; j < ncols; ++j)
//        x[j] = rng_->getReal64();
//
//      winnerTakesAll2(boundaries, x.begin(), v.begin());
//      
//      UInt k2 = 0;
//      for (UInt k1 = 0; k1 < nchildren; ++k1) {
//
//        vector<Real>::iterator it = 
//          max_element(x.begin() + k2, x.begin() + boundaries[k1]);
//        Test("Maths winnerTakesAll2 1", v[it - x.begin()], 1);
//
//        Real s = accumulate(v.begin() + k2, v.begin() + boundaries[k1], (Real)0);
//        Test("Maths winnerTakesAll2 2", s, (Real) 1);
//        
//        k2 = boundaries[k1];
//      }
//
//      Real s = accumulate(v.begin(), v.end(), (Real)0);
//      Test("Maths winnerTakesAll2 3", s, (Real) nchildren);
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void MathsTest::unitTestScale()
//  {
//    {
//      vector<Real> x;
//      normalize_max(x.begin(), x.end(), 1);
//      Test("scale 1", x.empty(), true);
//    }
//
//    {
//      vector<Real> x(1);
//      x[0] = 1;
//      normalize_max(x.begin(), x.end(), 1);
//      Test("scale 2", nearlyEqual(x[0], (Real)1), true);
//      
//      x[0] = 2;
//      normalize_max(x.begin(), x.end(), 1);
//      Test("scale 3", nearlyEqual(x[0], (Real)1), true);
//      
//      normalize_max(x.begin(), x.end(), .5);
//      Test("scale 4", nearlyEqual(x[0], (Real).5), true);
//
//      // TODO: test negative values in x
//    }
//
//    {
//      vector<Real> x(2);
//      x[0] = 1; x[1] = .5;
//      normalize_max(x.begin(), x.end(), 1);
//      Test("scale 5a", nearlyEqual(x[0], (Real)1), true);
//      Test("scale 5b", nearlyEqual(x[1], (Real).5), true);
//
//      x[0] = 10; x[1] = 7;
//      normalize_max(x.begin(), x.end(), 1);
//      Test("scale 6a", nearlyEqual(x[0], (Real)1), true);
//      Test("scale 6b", nearlyEqual(x[1], (Real).7), true);
//
//      x[0] = 7; x[1] = 10;
//      normalize_max(x.begin(), x.end(), 1);
//      Test("scale 7a", nearlyEqual(x[0], (Real).7), true);
//      Test("scale 7b", nearlyEqual(x[1], (Real)1), true);
//
//      normalize_max(x.begin(), x.end(), 10);
//      Test("scale 8a", nearlyEqual(x[0], (Real)7), true);
//      Test("scale 8b", nearlyEqual(x[1], (Real)10), true);
//    }    
//
//    {
//      const UInt N = 256;
//      vector<Real> x(N), ans(N);
//      ITER_1(100) {
//        for (UInt j = 0; j < N; ++j)
//          x[j] = ans[j] = rng_->getReal64();
//
//        Real max = 0;
//        for (UInt j = 0; j < N; ++j)
//          if (ans[j] > max)
//            max = ans[j];
//        for (UInt j = 0; j < N; ++j)
//          ans[j] /= max;
//
//        normalize_max(x.begin(), x.end(), 1);
//        
//        bool identical = true;
//        for (UInt j = 0; j < N && identical; ++j)
//          if (!nearlyEqual(x[j], ans[j]))
//            identical = false;
//
//        Test("scale 9", identical, true);
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void MathsTest::unitTestQSI()
//  {
//    /*
//    UInt n = 1000; // Changing n will change the error!
//
//    { // Constructor with F only
//      n = 1000; 
//      double lb = -1, ub = 1, t_lb = -2, t_ub = 2, t_step = (t_ub - t_lb)/(10*n);
//      
//      QSI<double, Exp<double> > q_e1(lb, ub, n, Exp<double>());
//      Test("qsi f 1", q_e1.max_error(t_lb, t_ub, t_step).second <= 1e-8, true);
//
//      QSI<double, Exp2<double> > q_e2(lb, ub, n, Exp2<double>());
//      Test("qsi f 2", q_e2.max_error(t_lb, t_ub, t_step).second <= 1e-7, true);
//    }
//
//    { 
//      n = 2000;    
//      Real lb = -1, ub = 1, t_lb = -2, t_ub = 2, t_step = (t_ub - t_lb)/(10*n);
//
//      QSI<Real, Exp<Real> > q_e1(lb, ub, n, Exp<Real>());
//      Test("qsi f 3", q_e1.max_error(t_lb, t_ub, t_step).second <= 1e-3, true);
//
//      QSI<Real, Exp2<Real> > q_e2(lb, ub, n, Exp2<Real>());
//      Test("qsi f 4", q_e2.max_error(t_lb, t_ub, t_step).second <= 1e-3, true);
//    }
//   
//    { // Constructor with F and derivative
//      n = 1000;
//      double lb = -1, ub = 1, t_lb = -2, t_ub = 2, t_step = (t_ub - t_lb)/(10*n);
//
//      QSI<double, Exp<double> > q_e1(lb, ub, n, Exp<double>(1, 2), Exp<double>(2, 2));
//      Test("qsi f ff 1", q_e1.max_error(t_lb, t_ub, t_step).second <= 1e-7, true);
//    }
//     
//    { 
//      n = 2000;
//      Real lb = -1, ub = 1, t_lb = -2, t_ub = 2, t_step = (t_ub - t_lb)/(10*n);
//      QSI<Real, Exp<Real> > q_e2(lb, ub, n, Exp<Real>(1, 2), Exp<Real>(2, 2));
//      Test("qsi f ff 2", q_e2.max_error(t_lb, t_ub, t_step).second <= 1e-5, true);
//    }
//
//    { // Vector to vector
//      n = 1000;
//      double v, lb = -1, ub = 1, t_lb = -2, t_ub = 2, t_step = (t_ub - t_lb)/(n);
//      vector<double> x(n), y(n), yref(n);
//
//      v = lb;
//
//      for (UInt i = 0; i < n; ++i, v += t_step) {
//        x[i] = v;
//        yref[i] = exp(v);
//      }
//
//      QSI<double, Exp<double> > q_e1(lb, ub, n, Exp<double>(1,1), Exp<double>(1,1));
//      q_e1(x.begin(), x.end(), y.begin());
//      Test("qsi vector 1", nearlyEqualRange(y.begin(), y.end(), yref.begin()), true);
//    }   
//    
//    { // Vector to itself
//      n = 1000;
//      double v, lb = -1, ub = 1, t_lb = -2, t_ub = 2, t_step = (t_ub - t_lb)/(n);
//      vector<double> vv(n), yref(n);
//
//      v = lb;
//
//      for (UInt i = 0; i < n; ++i, v += t_step) {
//        vv[i] = v;
//        yref[i] = exp(v);    
//      }
//
//      QSI<double, Exp<double> > q_e1(lb, ub, n, Exp<double>(1,1), Exp<double>(1,1));
//      q_e1(vv.begin(), vv.end());
//      Test("qsi vector 1", nearlyEqualRange(vv.begin(), vv.end(), yref.begin()), true);
//    }
//    */
//  }
//
  //--------------------------------------------------------------------------------
  void MathsTest::RunTests()
  {
    //
    //unitTestNearlyZero();
    //unitTestNearlyEqual();
    //unitTestNearlyEqualVector();
    //unitTestNormalize();
    ////unitTestVectorToStream();
    //unitTestElemOps();
    //unitTestWinnerTakesAll();
    //unitTestScale();
    ////unitTestQSI(); // HEAP CORRUPTION on Windows
  }
  
  //----------------------------------------------------------------------
} // end namespace nta


