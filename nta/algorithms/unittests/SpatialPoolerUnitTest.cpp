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
 * Implementation of unit tests for SpatialPooler
 */     

#include <nta/algorithms/SpatialPooler.hpp>
#include <nta/math/array_algo.hpp>

#include "SpatialPoolerUnitTest.hpp"

using namespace std;

// Work around terrible Windows legacy issue - min and max global macros!!!
#ifdef max
#undef max
#endif

namespace nta {    

//  //--------------------------------------------------------------------------------
//  std::vector<UInt> generateBoundaries(Random *r, const UInt& nchildren, const UInt& w)
//  {
//    std::vector<UInt> boundaries(nchildren, 0);
//
//    boundaries[0] = r->getUInt32(w) + 1;
//    for (UInt i = 1; i < nchildren-1; ++i) 
//      boundaries[i] = boundaries[i-1] + r->getUInt32(w) + 1;
//    boundaries[nchildren-1] = nchildren * w;
//
//    return boundaries;
//  }
//
//  //--------------------------------------------------------------------------------
//  void SpatialPoolerUnitTest::unitTestConstruction()
//  {
//    std::vector<UInt> boundaries(2);
//    boundaries[0] = 3; boundaries[1] = 5;
//    SpatialPooler* fsp = new SpatialPooler(boundaries, SpatialPooler::dot, 1, 1);
//    stringstream buf;
//    fsp->saveState(buf);
//    delete fsp;
//    SpatialPooler* fsp2 = new SpatialPooler(buf);
//    stringstream buf2;
//    fsp2->saveState(buf2);
//    delete fsp2;
//  }
//
//  //--------------------------------------------------------------------------------
//  void SpatialPoolerUnitTest::unitTestDot()
//  {
//    {
//      UInt nchildren = 2, ncols = 5;
//    
//      // 2 children inputs, first of size 3, second of size 2. 
//      vector<UInt> boundaries(nchildren);
//      boundaries[0] = 3; boundaries[1] = 5;
//
//      SpatialPooler sp(boundaries, SpatialPooler::dot, 1, 1);
//
//      // Train the matrix. We will end up with the following matrix after this training:
//      //  1 0 0 1 0
//      //  0 1 0 0 1
//      vector<Real> x(ncols), y(ncols);
//    
//      x[0] = 1; x[1] = 0; x[2] = 0; x[3] = 1; x[4] = 0;
//      sp.learn(x.begin(), y.begin());
//
//      x[0] = 0; x[1] = 1; x[2] = 0; x[3] = 0; x[4] = 1;
//      sp.learn(x.begin(), y.begin());
//
//      x[0] = 1; x[1] = 0; x[2] = 0; x[3] = 1; x[4] = 0;
//      sp.learn(x.begin(), y.begin());
//
//      // ---------------------------------------------------------------------------------
//      // First, make the children inputs [2,3,4] and [5,6]
//      // 1 0 0 1 0 * 2 3 4 5 6 = 2 + 5 = 7
//      // 0 1 0 0 1 * 2 3 4 5 6 = 3 + 6 = 9 
//      {   
//        UInt nc = sp.getNCoincidences();
//        vector<Real> output(nc), res(nc);
//
//        x[0] = 2; x[1] = 3; x[2] = 4; x[3] = 5; x[4] = 6;
//        res[0] = 7; res[1] = 9; 
//
//        sp.infer(x.begin(), output.begin());   
//
//        Test("SpatialPooler dot inference,1", nearlyEqualVector(output, res), true);
//      }
//    
//      // ---------------------------------------------------------------------------------
//      // Another test case, children [5,4,3] and [2,1]
//      // 1 0 0 1 0 * 5 4 3 2 1 = 5 + 2 = 7
//      // 0 1 0 0 1 * 5 4 3 2 1 = 4 + 1 = 5
//      {   
//        UInt nc = sp.getNCoincidences();
//        vector<Real> output(nc), res(nc);
//
//        x[0] = 5; x[1] = 4; x[2] = 3; x[3] = 2; x[4] = 1;
//        res[0] = 7; res[1] = 5; 
//
//        sp.infer(x.begin(), output.begin());   
//      
//        Test("SpatialPooler dot inference,2", nearlyEqualVector(output, res), true);
//      }
//    }
//
//    {
//      UInt nchildren, ncols, w, nreps, winner, winner_ref;
//    
//      nchildren = 5;
//      w = 8;
//      ncols = nchildren * w;
//      nreps = 1000;
//    
//      vector<UInt> boundaries = generateBoundaries(rng_, nchildren, w);
//      SpatialPooler sp(boundaries, SpatialPooler::dot, 1, 1);
//
//      { // Learning
//        typedef map<vector<Real>, pair<UInt, UInt> > Check;
//
//        Check control;     
//        Check::iterator it;    
//
//        vector<Real> x(ncols), v(ncols);
//        
//        for (UInt i = 0; i < nreps; ++i) {
//    
//          for (UInt j = 0; j < ncols; ++j)
//            x[j] = rng_->getReal64();
//
//          winnerTakesAll2(boundaries, x.begin(), v.begin());
//
//          it = control.find(v);  
//          if (it == control.end()) { 
//            winner_ref = (UInt)control.size();
//            control[v] = make_pair(winner_ref, 1);   
//          } else {   
//            winner_ref = control[v].first;
//            control[v].second += 1;  
//          }    
//
//          winner = sp.learn(x.begin(), x.begin());   
//          Test("SpatialPooler dot learning 1", winner, winner_ref);
//        }
//      
//        Test("SpatialPooler dot learning 2", sp.getW01()->nRows(), control.size());
//
//        SpatialPooler::RowCounts rc = sp.getRowCounts();
//      
//        for (UInt i = 0; i < rc.size(); ++i) {
//          vector<Real> row(ncols);
//          sp.getW01()->getRow(rc[i].first, row.begin());
//          Test("SpatialPooler dot learning 3", rc[i].second, control[row].second);
//        }
//
//        stringstream buf;
//        sp.saveState(buf);
//        SpatialPooler sp2(buf);
//        SpatialPooler::RowCounts rc2 = sp2.getRowCounts();
//        for (UInt i = 0; i < rc2.size(); ++i) {
//          Test("SpatialPooler dot learning 5", rc[i].first, rc2[i].first);
//          Test("SpatialPooler dot learning 6", rc[i].second, rc2[i].second);
//        }
//      }
//
//      { // Inference
//        for (UInt i = 0; i < nreps; ++i) {
//          
//          vector<Real> x(ncols), y(sp.getNCoincidences());
//
//          for (UInt j = 0; j < ncols; ++j)
//            x[j] = rng_->getReal64();
//
//          sp.infer(x.begin(), y.begin());   
//
//          vector<Real> y2(sp.getW01()->nRows());
//          sp.getW01()->rightVecProd(x.begin(), y2.begin());
//
//          Test("SpatialPooler dot inference 1", nearlyEqualVector(y, y2), true);
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  template <typename Array>
//  struct ListInitializer
//  {
//    typedef typename Array::value_type value_type;
//    typedef typename Array::iterator iterator;
//
//    iterator it;
//
//    inline ListInitializer(Array& a, const value_type& v)
//      : it(a.begin())
//    {
//      *it = v;
//      ++it;
//    }
//
//    inline ListInitializer& operator,(const value_type& v)
//    {
//      *it = v;
//      ++it;
//      return *this;
//    }
//  };
//
//  template <typename T>
//  struct array : public std::vector<T>
//  {
//    typedef typename std::vector<T>::size_type size_type;
//    typedef T value_type;
//
//    inline array(const size_type& n)
//      : std::vector<T>(n)
//    {}
//
//    inline ListInitializer<array> operator=(const value_type& v)
//    {
//      return ListInitializer<array>(*this, v);
//    }
//  };
//
//  //--------------------------------------------------------------------------------
//  void SpatialPoolerUnitTest::unitTestDotMaxD()
//  {
//    { // Manual test
//      UInt nchildren = 3, ncols = 12;
//      array<UInt> boundaries(nchildren); boundaries = 4, 8, 12;
//      SpatialPooler sp(boundaries, SpatialPooler::dot_maxD, 1, 2);
//      array<Real> x(ncols), y(ncols);
//
//      x = .8f, .1f, .2f, .3f,  .1f, .7f, .2f, .3f,  .1f, .2f, .6f, .5f;
//      sp.learn(x.begin(), y.begin());
//
//      x = .1f, .8f, .2f, .3f,  .7f, .1f, .2f, .3f,  .6f, .1f, .2f, .5f;
//      sp.learn(x.begin(), y.begin());
//
//      x = .8f, .1f, .2f, .3f,  .1f, .7f, .2f, .3f,  .1f, .2f, .6f, .5f;
//      sp.learn(x.begin(), y.begin());
//
//      x = .1f, .1f, .8f, .3f,  .1f, .2f, .7f, .3f,  .1f, .6f, .2f, .5f;
//      sp.learn(x.begin(), y.begin());
//
//      // Coincidences are:
//      // 1 0 0 0  0 1 0 0  0 0 1 0
//      // 0 1 0 0  1 0 0 0  1 0 0 0
//      // 0 0 1 0  0 0 1 0  0 1 0 0
//
//      UInt nc = sp.getNCoincidences();
//      array<Real> output(nc), res(nc);
//
//      // res is matrix vector product of coincidences and x
//      x = .8f, .1f, .2f, .3f,  .1f, .7f, .2f, .3f,  .1f, .2f, .6f, .5f;
//      res = .8f + .7f + .6f,  .1f + .1f + .1f,  .2f + .2f + .2f;
//      sp.infer(x.begin(), output.begin());   
//      Test("SpatialPooler dot maxD inference,1", nearlyEqualVector(output, res), true);
//      
//      x = .1f, .8f, .2f, .3f,  .7f, .1f, .2f, .3f,  .1f, .6f, .2f, .5f;
//      res = .1f + .1f + .2f,  .8f + .7f + .1f,  .2f + .2f + .6f;
//      sp.infer(x.begin(), output.begin());   
//      Test("SpatialPooler dot maxD inference,2", nearlyEqualVector(output, res), true);
//    }
//
//    { // Automated random test
//      typedef map<vector<Real>, pair<UInt, UInt> > Check;
//
//      UInt N1 = 20, N2 = 20, N3 = 20;
//
//      for (UInt n = 0; n < N1; ++n) {
//	
//	Check control; Check::iterator it, arg_it;    
//
//	UInt nchildren = 1 + rng_->getUInt32(16);
//
//	std::vector<UInt> boundaries(nchildren);
//
//	boundaries[0] = 8;
//	for (UInt i = 1; i < boundaries.size(); ++i)
//	  boundaries[i] = boundaries[i-1] + 1 + rng_->getUInt32(boundaries[0]-1);
//      
//	UInt ncols = boundaries[boundaries.size()-1];
//      
//	SpatialPooler sp(boundaries, SpatialPooler::dot_maxD, 1, 1);
//      
//	for (UInt i = 0; i < N2; ++i) {
//
//	  // Test setMaxD, getMaxD
//	  Real max_distance = rng_->getReal64();
//	  sp.setMaxD(max_distance);
//	  Test("SpatialPooler dot maxD set/get", sp.getMaxD(), max_distance);
//
//	  // Test learning
//	  UInt winner, winner_ref, hamming, min_hamming;
//	  std::vector<Real> x(ncols), v(ncols);
//	
//	  for (UInt j = 0; j < ncols; ++j)
//	    x[j] =  Real(rng_->getUInt32(100));
//
//	  winnerTakesAll2(boundaries, x.begin(), v.begin());
//
//	  min_hamming = std::numeric_limits<UInt>::max();
//	  arg_it = control.begin();
//      
//	  for (it = control.begin(); it != control.end(); ++it) {
//	    hamming = 0;
//	    for (UInt k = 0; k < ncols; ++k) {
//	      if ((it->first)[k] != v[k]) {
//		++hamming;
//	      }
//	    }
//	    if (hamming < min_hamming) {
//	      min_hamming = hamming;
//	      arg_it = it;
//	    }
//	  }   
//      
//	  if (min_hamming <= max_distance) {
//	    ++ (arg_it->second.second);
//	    winner_ref = arg_it->second.first;
//	  } else {
//	    winner_ref = (UInt)control.size();
//	    control[v] = std::make_pair(winner_ref, 1);
//	  }
//
//	  winner = sp.learn(x.begin(), x.begin());   
//	  Test("SpatialPooler dot maxD learning 1", winner, winner_ref);
//
//	  // Test inference
//	  for (UInt k = 0; k < N3; ++k) {
//	    
//	    vector<Real> y(sp.getNCoincidences());
//	    
//	    for (UInt j = 0; j < ncols; ++j)
//	      x[j] =  Real(rng_->getUInt32(100));
//	    
//	    sp.infer(x.begin(), y.begin());   
//	    
//	    vector<Real> y2(sp.getW01()->nRows());
//	    sp.getW01()->rightVecProd(x.begin(), y2.begin());
//	    
//	    Test("SpatialPooler dot maxD inference 1", nearlyEqualVector(y, y2), true);
//	  }
//      
//	  Test("SpatialPooler dot maxD learning 2", sp.getW01()->nRows(), control.size());
//	
//	  SpatialPooler::RowCounts rc = sp.getRowCounts();
//	
//	  for (UInt i = 0; i < rc.size(); ++i) {
//	    vector<Real> row(ncols);
//	    sp.getW01()->getRow(rc[i].first, row.begin());
//	    Test("SpatialPooler dot maxD learning 3", rc[i].second, control[row].second);
//	  }
//
//	  // Test persistence
//	  stringstream buf;
//	  sp.saveState(buf);
//	  SpatialPooler sp2(buf);
//	  SpatialPooler::RowCounts rc2 = sp2.getRowCounts();
//	
//	  for (UInt i = 0; i < rc2.size(); ++i) {
//	    Test("SpatialPooler dot maxD persistence 5", rc[i].first, rc2[i].first);
//	    Test("SpatialPooler dot maxD persistence 6", rc[i].second, rc2[i].second);
//	  }
//	}
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SpatialPoolerUnitTest::unitTestProduct()
//  {
//    {
//      UInt nchildren, ncols;
//    
//      nchildren = 2; ncols = 5;
//    
//      // 2 children inputs, first of size 3, second of size 2. 
//      vector<UInt> boundaries(2);
//      boundaries[0] = 3; boundaries[1] = 5;
//
//      SpatialPooler sp(boundaries, SpatialPooler::product, 1, 1);
//
//      // Train the matrix. We will end up with the following matrix after this training:
//      //  1 0 0 1 0
//      //  0 1 0 0 1
//      vector<Real> x(ncols), y(ncols);
//    
//      x[0] = 1; x[1] = 0; x[2] = 0; x[3] = 1; x[4] = 0;
//      sp.learn(x.begin(), y.begin());
//    
//      x[0] = 0; x[1] = 1; x[2] = 0; x[3] = 0; x[4] = 1;
//      sp.learn(x.begin(), y.begin());
//
//      x[0] = 1; x[1] = 0; x[2] = 0; x[3] = 1; x[4] = 0;
//      sp.learn(x.begin(), y.begin());
//
//      // ---------------------------------------------------------------------------------
//      // First, make the children inputs [2,3,4] and [5,6]
//      // 1 0 0 1 0 * 2 3 4 5 6 = 2 * 5 = 10
//      // 0 1 0 0 1 * 2 3 4 5 6 = 3 * 6 = 18 
//      {   
//        UInt nc = sp.getNCoincidences();
//        vector<Real> output(nc), res(nc);
//
//        x[0] = 2; x[1] = 3; x[2] = 4; x[3] = 5; x[4] = 6;
//        res[0] = 10; res[1] = 18; 
//        normalize_max(res.begin(), res.end(), 1);
//
//        sp.infer(x.begin(), output.begin());   
//
//        Test("SpatialPooler prod inference,1", nearlyEqualVector(output, res), true);
//      }
//    
//      // ---------------------------------------------------------------------------------
//      // Another test case, children [5,4,3] and [2,1]
//      // 1 0 0 1 0 * 5 4 3 2 1 = 5 * 2 = 10
//      // 0 1 0 0 1 * 5 4 3 2 1 = 4 * 1 = 4
//      {   
//        UInt nc = sp.getNCoincidences();
//        vector<Real> output(nc), res(nc);
//        
//        x[0] = 5; x[1] = 4; x[2] = 3; x[3] = 2; x[4] = 1;
//        res[0] = 10; res[1] = 4; 
//        normalize_max(res.begin(), res.end(), 1);
//
//        sp.infer(x.begin(), output.begin());   
//      
//        Test("SpatialPooler prod inference,2", nearlyEqualVector(output, res), true);
//      }
//    }
//
//    { // Stress test
//      UInt nchildren, ncols, w, nreps, winner, winner_ref;
//    
//      nchildren = 5;
//      w = 8;
//      ncols = nchildren * w;
//      nreps = 1000;
//    
//      vector<UInt> boundaries = generateBoundaries(rng_, nchildren, w);
//      SpatialPooler sp(boundaries, SpatialPooler::product, 1, 1);
//
//      { // Learning
//        typedef map<vector<Real>, pair<UInt, UInt> > Check;
//
//        Check control;   
//        Check::iterator it;    
//    
//        for (UInt i = 0; i < nreps; ++i) {
//          
//          vector<Real> x(ncols);
//          for (UInt j = 0; j < ncols; ++j)
//            x[j] = rng_->getReal64();
//   
//          vector<Real> v(ncols), y(ncols, 0);
//          winnerTakesAll2(boundaries, x.begin(), v.begin());
//   
//          it = control.find(v);  
//          if (it == control.end()) { 
//            winner_ref = (UInt)control.size();
//            control[v] = make_pair(winner_ref, 1);   
//          }
//          else {   
//            winner_ref = control[v].first;
//            control[v].second += 1;  
//          }    
//
//          winner = sp.learn(x.begin(), y.begin());   
//          Test("SpatialPooler prod learning 1",nearlyZeroRange(y.begin(), y.end()), true);
//          Test("SpatialPooler prod learning 2", winner, winner_ref);
//        }
//      
//        Test("SpatialPooler prod learning 3", sp.getW01()->nRows(), control.size());
//
//        SpatialPooler::RowCounts rc = sp.getRowCounts();
//      
//        for (UInt i = 0; i < rc.size(); ++i) {
//          vector<Real> row(ncols);
//          sp.getW01()->getRow(rc[i].first, row.begin());
//          Test("SpatialPooler prod learning 4", rc[i].second, control[row].second);
//        }
//
//        stringstream buf;
//        sp.saveState(buf);
//        SpatialPooler sp2(buf);
//        SpatialPooler::RowCounts rc2 = sp2.getRowCounts();
//        for (UInt i = 0; i < rc2.size(); ++i) {
//          Test("SpatialPooler prod learning 5", rc[i].first, rc2[i].first);
//          Test("SpatialPooler prod learning 6", rc[i].second, rc2[i].second);
//        }
//      }
//
//      { // Inference        
//        for (UInt i = 0; i < nreps; ++i) {
//              
//          vector<Real> x(ncols);
//          for (UInt j = 0; j < ncols; ++j)
//            x[j] = rng_->getReal64();
//   
//          vector<Real> y(sp.getNCoincidences());
//
//          sp.infer(x.begin(), y.begin());   
//
//          vector<Real> y2(sp.getW01()->nRows());
//          sp.getW01()->rowProd(x.begin(), y2.begin());
//          normalize_max(y2.begin(), y2.end(), 1);
//          Test("SpatialPooler prod inference 1", nearlyEqualVector(y, y2), true);
//        }
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SpatialPoolerUnitTest::unitTestProductMaxD()
//  {
//    { // Manual test
//      UInt nchildren = 3, ncols = 12;
//      array<UInt> boundaries(nchildren); boundaries = 4, 8, 12;
//      SpatialPooler sp(boundaries, SpatialPooler::product_maxD, 1, 2);
//      array<Real> x(ncols), y(ncols);
//
//      x = .8f, .1f, .2f, .3f,  .1f, .7f, .2f, .3f,  .1f, .2f, .6f, .5f;
//      sp.learn(x.begin(), y.begin());
//
//      x = .1f, .8f, .2f, .3f,  .7f, .1f, .2f, .3f,  .6f, .1f, .2f, .5f;
//      sp.learn(x.begin(), y.begin());
//
//      x = .8f, .1f, .2f, .3f,  .1f, .7f, .2f, .3f,  .1f, .2f, .6f, .5f;
//      sp.learn(x.begin(), y.begin());
//
//      x = .1f, .1f, .8f, .3f,  .1f, .2f, .7f, .3f,  .1f, .6f, .2f, .5f;
//      sp.learn(x.begin(), y.begin());
//
//      // Coincidences are:
//      // 1 0 0 0  0 1 0 0  0 0 1 0
//      // 0 1 0 0  1 0 0 0  1 0 0 0
//      // 0 0 1 0  0 0 1 0  0 1 0 0
//
//      UInt nc = sp.getNCoincidences();
//      array<Real> output(nc), res(nc);
//
//      // res is matrix vector product of coincidences and x
//      x = .8f, .1f, .2f, .3f,  .1f, .7f, .2f, .3f,  .1f, .2f, .6f, .5f;
//      res = .8f * .7f * .6f,  .1f * .1f * .1f,  .2f * .2f * .2f;
//      normalize_max(res.begin(), res.end(), 1);
//      sp.infer(x.begin(), output.begin());   
//      Test("SpatialPooler product maxD inference,1", 
//	   nearlyEqualVector(output, res), true);
//      
//      x = .1f, .8f, .2f, .3f,  .7f, .1f, .2f, .3f,  .1f, .6f, .2f, .5f;
//      res = .1f * .1f * .2f,  .8f * .7f * .1f,  .2f * .2f * .6f;
//      normalize_max(res.begin(), res.end(), 1);
//      sp.infer(x.begin(), output.begin());   
//      Test("SpatialPooler product maxD inference,2", 
//	   nearlyEqualVector(output, res), true);
//    }
//
//    { // Automated random test
//      typedef map<vector<Real>, pair<UInt, UInt> > Check;
//
//      UInt N1 = 20, N2 = 20, N3 = 20;
//
//      for (UInt n = 0; n < N1; ++n) {
//	
//	Check control; Check::iterator it, arg_it;    
//
//	UInt nchildren = 1 + rng_->getUInt32(16);
//
//	std::vector<UInt> boundaries(nchildren);
//
//	boundaries[0] = 8;
//	for (UInt i = 1; i < boundaries.size(); ++i)
//	  boundaries[i] = boundaries[i-1] + 1 + rng_->getUInt32(boundaries[0]-1);
//      
//	UInt ncols = boundaries[boundaries.size()-1];
//      
//	SpatialPooler sp(boundaries, SpatialPooler::product_maxD, 1, 1);
//      
//	for (UInt i = 0; i < N2; ++i) {
//
//	  // Test setMaxD, getMaxD
//	  Real max_distance = Real(rng_->getUInt32(nchildren));
//	  sp.setMaxD(max_distance);
//	  Test("SpatialPooler product maxD set/get", 
//	       sp.getMaxD(), max_distance);
//
//	  // Test learning
//	  UInt winner, winner_ref, hamming, min_hamming;
//	  std::vector<Real> x(ncols), v(ncols);
//	
//	  for (UInt j = 0; j < ncols; ++j)
//	    x[j] =  Real(rng_->getUInt32(100));
//
//	  winnerTakesAll2(boundaries, x.begin(), v.begin());
//
//	  min_hamming = std::numeric_limits<UInt>::max();
//	  arg_it = control.begin();
//      
//	  for (it = control.begin(); it != control.end(); ++it) {
//	    hamming = 0;
//	    for (UInt k = 0; k < ncols; ++k) {
//	      if ((it->first)[k] != v[k]) {
//		++hamming;
//	      }
//	    }
//	    if (hamming < min_hamming) {
//	      min_hamming = hamming;
//	      arg_it = it;
//	    }
//	  }   
//      
//	  if (min_hamming <= max_distance) {
//	    ++ (arg_it->second.second);
//	    winner_ref = arg_it->second.first;
//	  } else {
//	    winner_ref = (UInt)control.size();
//	    control[v] = std::make_pair(winner_ref, 1);
//	  }
//
//	  winner = sp.learn(x.begin(), x.begin());   
//	  Test("SpatialPooler product maxD learning 1", 
//	       winner, winner_ref);
//
//	  // Test inference
//	  for (UInt k = 0; k < N3; ++k) {
//	    
//	    vector<Real> y(sp.getNCoincidences());
//	    
//	    for (UInt j = 0; j < ncols; ++j)
//	      x[j] =  Real(rng_->getUInt32(100));
//	    
//	    sp.infer(x.begin(), y.begin());   
//	    
//	    vector<Real> y2(sp.getW01()->nRows());
//	    sp.getW01()->rowProd(x.begin(), y2.begin());
//	    normalize_max(y2.begin(), y2.end(), 1);
//	    
//	    Test("SpatialPooler product maxD inference 1", 
//		 nearlyEqualVector(y, y2), true);
//	  }
//      
//	  Test("SpatialPooler product maxD learning 2", 
//	       sp.getW01()->nRows(), control.size());
//	
//	  SpatialPooler::RowCounts rc = sp.getRowCounts();
//	
//	  for (UInt i = 0; i < rc.size(); ++i) {
//	    vector<Real> row(ncols);
//	    sp.getW01()->getRow(rc[i].first, row.begin());
//	    Test("SpatialPooler product maxD learning 3", 
//		 rc[i].second, control[row].second);
//	  }
//
//	  // Test persistence
//	  stringstream buf;
//	  sp.saveState(buf);
//	  SpatialPooler sp2(buf);
//	  SpatialPooler::RowCounts rc2 = sp2.getRowCounts();
//	
//	  for (UInt i = 0; i < rc2.size(); ++i) {
//	    Test("SpatialPooler product maxD persistence 5", 
//		 rc[i].first, rc2[i].first);
//
//	    Test("SpatialPooler product maxD persistence 6", 
//		 rc[i].second, rc2[i].second);
//	  }
//	}
//      }
//    }
//  }
//
//  //--------------------------------------------------------------------------------
//  void SpatialPoolerUnitTest::unitTestGaussian()
//  {
//    UInt nchildren, ncols, w, nreps, winner, min_idx;
//    
//    nchildren = 5;
//    w = 8;
//    ncols = nchildren * w;
//    nreps = 1000;
//
//    Real dist, val, min_dist, maxDistance = 3.5;
//    
//    vector<UInt> boundaries = generateBoundaries(rng_, nchildren, w);
//    SpatialPooler sp(boundaries, SpatialPooler::gaussian, 1, maxDistance);
//
//    { // Learning
//      typedef vector<pair<vector<Real>, UInt> > Check;
//
//      Check control;   
//      Check::iterator it;    
//      vector<Real> dists;
//
//      vector<Real> x(ncols), y;
//    
//      for (UInt i = 0; i < nreps; ++i) {
//
//        for (UInt j = 0; j < ncols; ++j)
//          x[j] = Real(nreps + ncols) / (Real)1000; 
//	//+ Real(rng_->get() % 32768 / 32768.0);
//
//        if (rng_->getReal64() > .7) {
//          for (UInt j = 0; j < ncols; ++j)
//            x[j] = - x[j];
//        }
//   
//        min_idx = 0;
//        min_dist = numeric_limits<Real>::max();
//
//        for (UInt r = 0; r < control.size(); ++r) {
//          dist = 0;
//          for (UInt j = 0; j < ncols && dist < min_dist; ++j) {
//            val = control[r].first[j] - x[j];
//            dist += val * val;
//          }
//          if (dist < min_dist) {
//            min_dist = dist;
//            min_idx = r;
//          }
//        }
//
//        if (control.empty() || min_dist > maxDistance) {
//          min_idx = (UInt)control.size();
//          control.push_back(make_pair(x, 1));
//        } else {
//          control[min_idx].second += 1;
//        }
//
//        winner = sp.learn(x.begin(), y.begin());   
//
//        Test("SpatialPooler gaussian learning 1", winner, min_idx);
//      }
//      
//      Test("SpatialPooler gaussian learning 2", sp.getW()->nRows(), control.size());
//
//      SpatialPooler::RowCounts rc = sp.getRowCounts();
//      
//      for (UInt i = 0; i < rc.size(); ++i) {
//        Test("SpatialPooler gaussian learning 3", rc[i].second, control[i].second);
//      }
//
//    }
//
//    { // Inference
//      for (UInt i = 0; i < nreps; ++i) {
//          
//        vector<Real> x(ncols);
//        for (UInt j = 0; j < ncols; ++j)
//          x[j] = rng_->getReal64();
//   
//        vector<Real> y(sp.getNCoincidences());
//
//        sp.infer(x.begin(), y.begin());   
//
//        vector<Real> y2(sp.getW()->nRows());
//        sp.getW()->L2Dist(x.begin(), y2.begin());
//	for (UInt i = 0; i != sp.getW()->nRows(); ++i)
//	  y2[i] = exp(sp.k2_ * y2[i]);
//        Test("SpatialPooler gaussian inference 1", nearlyEqualVector(y, y2), true);
//      }
//    }
//  }   
//
//  //--------------------------------------------------------------------------------
//  void SpatialPoolerUnitTest::unitTestPruning()
//  {
//    { // dot, product
//      UInt nchildren, ncols, w, nreps, winner, winner_ref;
//    
//      nchildren = 5;
//      w = 8;
//      ncols = nchildren * w;
//      nreps = 10000;
//    
//      vector<UInt> boundaries = generateBoundaries(rng_, nchildren, w);
//      SpatialPooler sp(boundaries, SpatialPooler::product, 1, 1);
//
//      typedef map<vector<Real>, pair<UInt, UInt> > Check;
//      
//      Check control;   
//      Check::iterator it;    
//      
//      // Learn
//      for (UInt i = 0; i < nreps; ++i) {
//        
//        vector<Real> x(ncols);
//        for (UInt j = 0; j < ncols; ++j)
//          x[j] = rng_->getReal64();
//        
//        vector<Real> v(ncols), y(ncols, 0);
//        winnerTakesAll2(boundaries, x.begin(), v.begin());
//        
//        it = control.find(v);  
//        if (it == control.end()) { 
//          winner_ref = (UInt)control.size();
//          control[v] = make_pair(winner_ref, 1);   
//        }
//        else {   
//          winner_ref = control[v].first;
//          control[v].second += 1;  
//        }    
//        
//        winner = sp.learn(x.begin(), y.begin());   
//      }
//      
//      Test("SpatialPooler prod pruning 1", sp.getW01()->nRows(), control.size());
//      
//      SpatialPooler::RowCounts rc = sp.getRowCounts();
//      
//      for (UInt i = 0; i < rc.size(); ++i) {
//        vector<Real> row(ncols);
//        sp.getW01()->getRow(rc[i].first, row.begin());
//        Test("SpatialPooler prod pruning 2", rc[i].second, control[row].second);
//      }
//      
//      // Prune
//      for (UInt i = 2; i < 10; ++i) {
//        UInt nKept = 0;
//        for (it = control.begin(); it != control.end(); ++it)
//          if (it->second.second >= i)
//            ++nKept;
//        std::vector<UInt> del;
//        UInt initial = sp.getW01()->nRows();
//        sp.pruneCoincidences(i, del);
//        Test("SpatialPooler prod pruning 3", sp.getW01()->nRows(), nKept);
//        if (initial > 0)
//          Test("SpatialPooler prod pruning 4", del.size(), initial - nKept);
//      }
//    }
//
//    { // gaussian
//      UInt nchildren, ncols, w, nreps, winner;
//    
//      nchildren = 5;
//      w = 8;
//      ncols = nchildren * w;
//      nreps = 1000;
//    
//      vector<UInt> boundaries = generateBoundaries(rng_, nchildren, w);
//      SpatialPooler sp(boundaries, SpatialPooler::gaussian, 1, 12);
//      vector<Real> x(ncols), y;
//
//      for (UInt i = 0; i < nreps; ++i) {
//
//        for (UInt j = 0; j < ncols; ++j)
//          x[j] = Real(rng_->getUInt32(2));
//
//        winner = sp.learn(x.begin(), y.begin());   
//      }
//      
//      SpatialPooler::RowCounts rc = sp.getRowCounts();
//      
//      // Prune
//      for (UInt i = 2; i < 10; ++i) {
//        UInt nKept = 0;
//        for (UInt j = 0; j < rc.size(); ++j) 
//          if (rc[j].second >= i)
//            ++nKept;
//        std::vector<UInt> del;
//        UInt initial = sp.getW()->nRows();
//        sp.pruneCoincidences(i, del);
//        Test("SpatialPooler prod pruning 5", sp.getW()->nRows(), nKept);
//        Test("SpatialPooler prod pruning 6", del.size(), initial - nKept);
//      }
//    }
//  }
//
  //--------------------------------------------------------------------------------
  void SpatialPoolerUnitTest::RunTests()
  {

#ifdef WIN32
    return;
#endif
    //unitTestConstruction();
    //unitTestDot();
    //unitTestDotMaxD();
    //unitTestProductMaxD();
    //unitTestProduct();
    //unitTestGaussian();
    //unitTestPruning();
  }
    
  //--------------------------------------------------------------------------------
} // end namespace nta


   
