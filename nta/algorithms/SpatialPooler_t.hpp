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
 * Template implementation for SpatialPooler
 */

#ifndef NTA_SPATIAL_POOLER_T_HPP
#define NTA_SPATIAL_POOLER_T_HPP

#include <nta/math/math.hpp>

#include <limits>

//----------------------------------------------------------------------
namespace nta {

  //--------------------------------------------------------------------------------
  /**
   * SparseMatrix01 handles the counting of the rows for us. It inserts the rows
   * only once in its data structures, and then increases the row count by 1
   * each time the row is seen afterwards. 
   * SparseMatrix, however, does not have that row counting facility, so
   * we need to keep track of rows directly here, with the counts_ vector.
   * begin2 is not used in learning mode, because when a level learns,
   * the level above it is simply idle. 
   */
  template <typename InIter, typename OutIter>
  UInt SpatialPooler::learn(InIter begin1, OutIter begin2)
  {    
    UInt winner = 0;
    std::pair<size_t, Real> closest(0,0);
    
    switch (mode_) {

    case dot:    
    case product:
      
      winner = W01_->addUniqueFilteredRow(boundaries_.begin(), begin1);
      break;

    case dot_maxD:
    case product_maxD:
      
      winner = W01_->addMinHamming(boundaries_.begin(), begin1, maxDistance_);
      break;

    case gaussian:
      
      if (W_->nRows() == 0) 
        {
          W_->addRow(begin1);
          counts_.push_back(1);
        } 
      else 
        {
          W_->L2Nearest(begin1, &closest); //minVecDistSquared(begin1, closest);
          
          // maxDistance_ is actually a squared distance
          if (closest.second > maxDistance_) { 
            winner = W_->addRow(begin1);
            counts_.push_back(1);
          } else {
            winner = (UInt) closest.first;
            ++ counts_[winner];
          }
        } 
      break;
    }
    
    return winner;
  }

  //--------------------------------------------------------------------------------
  template <typename InIter, typename OutIter>
  void SpatialPooler::infer(InIter begin1, OutIter begin2, Real* blank)
  {
    UInt n = getNCoincidences();
    OutIter end = begin2 + n;

    // Epsilon is not involved in any of the sparse matrix operations
    // below, so that we can get maximum precision and no truncation
    // takes place
    switch (mode_) {
    case dot:
    case dot_maxD:
      // Simple matrix vector multiplication
      W01_->rightVecProd(begin1, begin2); 
      return;
      break;

    case gaussian:
      {
	// Computes the square of the distance of the input vector
	// to each row of the sparse matrix
	W_->L2Dist(begin1, begin2); //vecDistSquared(begin1, begin2);
	nta::Exp<Real> exp_f;
	while (begin2 != end) {
	  *begin2 = exp_f(k2_ * *begin2);
	  ++begin2;
	}
      }
      break;
      
    case product:
    case product_maxD:
      // Computes the product of the values in the input vector
      // at the indices of the non-zeros in W01_.
      // This product could underflow.
      W01_->rowProd(begin1, begin2);

      // Scaling: in product mode, we scale the output
      // so that the largest value becomes 1. This reduces
      // the underflow issues.
      if (prodModeScaling_) {
        Real val, max_val = 0;
        OutIter it;
        
        // Get the max of the blank and the outputs
        if (blank) max_val = *blank;
        for (it = begin2; it != end; ++it) {
          val = *it;
          if (val > max_val)
            max_val = val;
        } 
        
        // Scale the blank and the outputs by the same amount
        if (max_val != nta::Real(0)) {
          val = nta::Real(1.0)/max_val;
          if (val == std::numeric_limits<nta::Real>::infinity())
            val = std::numeric_limits<nta::Real>::max();
          for (it = begin2; it != end; ++it)
            *it *= val;
          if (blank) *blank *= val;
        }
        
      }
      break;
    }
  }

  //--------------------------------------------------------------------------------
  template <typename InIter>
  Real SpatialPooler::blankScore(InIter begin1) const
  {
    Real blankScore = 0, val = 0;
    std::vector<UInt>::const_iterator b_it, b_end;
    b_it = boundaries_.begin();
    b_end = --boundaries_.end();

    switch (mode_) {
    case dot:
    case dot_maxD:
      blankScore = *begin1;
      while (b_it != b_end)
        blankScore += *(begin1 + *b_it++);
      break;
    case product:
    case product_maxD:
      blankScore = *begin1;
      while (b_it != b_end)
        blankScore *= *(begin1 + *b_it++);
      break;
    case gaussian:
      blankScore = 1;
      InIter end = begin1 + getInputSize();
      nta::Exp<Real> exp_f;
      while (begin1 != end) {
        val = *begin1++;
        blankScore *= exp_f(k2_ * val * val);
      }
      break;
    }
    return blankScore;
  }

//--------------------------------------------------------------------------------

} // end namespace nta

#endif // NTA_SPATIAL_POOLER_T_HPP



