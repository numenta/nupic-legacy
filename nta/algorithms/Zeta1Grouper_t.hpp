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
 * Templates implementation for class Grouper
 */

#ifndef NTA_ZETA1_GROUPER_T_HPP
#define NTA_ZETA1_GROUPER_T_HPP

#ifdef NUPIC2
#error "Zeta1Grouper is used only by Zeta1Node, which is not part of NuPIC 2"
#endif

//----------------------------------------------------------------------
namespace nta {
  
  //--------------------------------------------------------------------------------
  /**
   * begin2 is not used: we do not output anything in learning mode.
   */
  template <typename InIter, typename OutIter>
  void Zeta1Grouper::learn(InIter begin1, OutIter, size_type baby_idx)
  {
    size_type winnerIndex = size_type(*begin1);
    tam_.learn(winnerIndex, baby_idx);
  }

  //--------------------------------------------------------------------------------
  /**
   * x is the output of the coincidence detector
   *
   * If using Time Based Inference ('tbi' set in the constructor), then the inference output
   * is computed by treating the Time Adjacency Matrix (tam) as a set of cell weights between
   * "cells" in each group. The intent here is to have the inference output for each group
   * increase in certainty as we see successive coincidence inputs that are in that group.
   *
   * For the TBI computation, each group is assigned 1 cell per coincidence in the
   * group. Each cell's output is updated after each time step based on the following
   * equation:
   *                             N   /		        	 \
   * cellOut (t) = bottomUp * ( SUM | cellWeight  * cellOut (t-1) |  + A0  )
   *        j              j    i=0  \         ij          i     /
   *
   * The net inference output for each group is then the max of all the cell outputs for
   * that group.
   * 
   * Each group has it's own cellWeight matrix, which is produced by extracting the entries
   * from the TAM corresponding to the coincidences in that group, and then normalizing down
   * the columns so that the sum of the weights in each column is 1.
   *
   * The cellOuts for each group are kept unique from each other - when we have overlapping
   * groups for example, cell 0's output in group A will not necessarily be the same value
   * as cell 0's output in group B - this is because we only consider the contribution
   * from other cells *in the same group* when we peform the above cellOut computation.
   * 
   * The A0 contribution can be considered as the likelihood that this cell is a start of
   * the group, or rather, it is the sum contribution from all the cells in the other
   * groups. Without this factor of course, none of the cell outputs would ever be non-zero.
   * In the end, the exact value chosen for A0 is immaterial since we are only looking at
   * the relative output strengths of each group.
   *
   * cellOut is a joint pdf over groups and coincidences.
   */
  template <typename InIter, typename OutIter>
  void Zeta1Grouper::tbiInfer(InIter x, InIter x_end, 
			 OutIter y, TBICellOutputsVec::iterator cellOuts)
  {
    using namespace std;

    { // Pre-conditions
      NTA_ASSERT(!tbiCellWeights_.empty())
	<< "Grouper::tbiInfer: Cell weights not initialized";
    } // End pre-conditions

    const value_type A0 = (value_type) 0.1;

    // Compute TBI output. 
    OutIter y_begin = y;
    TBICellWeightsVec::iterator w = tbiCellWeights_.begin();
    Groups::const_iterator g = groups_.begin(), g_end = groups_.end();   
    size_type g_idx = 0;

    for (; g != g_end; ++g, ++w, ++cellOuts, ++y, ++g_idx) 
      {
	// Compute the product of the cellWeights and the current 
	// cell outputs.
	// w has size g->size X g->size
	// *cellOuts has size g->size (vector)
	// tbiBuffer_ is sized to be the size of the largest group
	// (only the first g->size positions are used here)
	w->rightVecProd(*cellOuts, tbiBuffer_);

	// Add A0 to each cell output and multiply by the bottom up input 
	AGroup::const_iterator s = g->begin(), s_end = g->end();
	TBICellOutputs::iterator cell = cellOuts->begin();
	TBICellOutputs::const_iterator b = tbiBuffer_.begin();
	value_type maxCellOut = 0.0;

	// In case HOT is used, we need to convert the HOT state 
	// index to its original coincidence. If HOT is not used, 
	// getHOTCoincidence reduces to identity.
	for (; s != s_end; ++s, ++b, ++cell) {
	  size_type c = tam_.getHOTCoincidence(*s);
	  *cell = (*b + A0) * (*(x + c));
	  maxCellOut = max(*cell, maxCellOut);
	}
	
	*y = maxCellOut;
      } 

    if(rescaleTBI_) {
      // Scale the group outputs so that the max is the same as the max of the inputs.
      // This preserves the relative strength between the group output and blank score
      // computed by the spatial pooler. 
      value_type maxInValue = * std::max_element(x, x_end);
      if (maxInValue > (value_type) 0)
        normalize_max(y_begin, y_begin + groups_.size(), maxInValue);
    }
  }

  //--------------------------------------------------------------------------------
  template <typename InIter, typename OutIter>
  void Zeta1Grouper::infer(InIter x, InIter x_end, OutIter y, size_type tbi_idx)
  {
    switch (mode_) {        
      
    case maxProp:
      // For each row, find the max corresponding to a non-zero
      weights_.vecMaxAtNZ(x, y);
      break;
      
    case sumProp:
      weights_.rightVecProd(x, y);
      break;
      
    case tbi: 
      {
	if (tbiCellWeights_.empty())
	  tbi_create_();

	tbiInfer(x, x_end, y, tbiCellOutputs_[tbi_idx].begin());
      }
      break;
    } // switch mode
  } 


  //--------------------------------------------------------------------------------

} // end namespace nta

#endif // NTA_ZETA1_GROUPER_T_HPP
