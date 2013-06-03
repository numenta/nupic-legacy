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
 * Implementation for SparsePooler
 */

#include <limits>

#include <nta/math/SparseMatrixAlgorithms.hpp>

namespace nta {

  // Learn/Infer -------------------------------------------------------------------
  template <typename InputIterator, typename OutputIterator>
  bool
  SparsePooler::learn(InputIterator input_begin, InputIterator input_end, 
                      OutputIterator output)
  {
    using namespace std;

    p_ %= input_masks_.nMasks();
    buffer_iterator buf_begin = buf_.begin();
    buffer_iterator buf_end = buf_begin + input_masks_.size(p_);
    const SparsePoolerInputMasks::Mask& mask = input_masks_.mask(p_);

    vector<size_type> ind;
    vector<value_type> nz;
    vector<pair<size_type, value_type> > nn(1, make_pair(0,0));

    concatenate(input_begin, mask.begin(), mask.end(), buf_begin);

    if (min_accept_norm_ > 0) {
      value_type norm = lp_norm(lp_, buf_begin, buf_end); 
      if (norm < min_accept_norm_ * input_masks_.ratio(p_)) 
        return false;
    }

    if (normalize_) 
      normalize(buf_begin, buf_end, lp_);

    if (inference_mode_ == kthroot_product) {

      size_type ss = getSegmentSize();
      size_type nnz = 0;
      value_type the_max(0);
      size_type n = (size_type)(buf_end - buf_begin) / ss;

      for (size_type i = 0; i != n; ++i) {
        value_type M(0);
        size_type arg_M = 0;
        for (size_type j = i*ss; j != (i+1)*ss; ++j) {
          value_type val = *(buf_begin + j);
          if (val > M) {
            M = val;
            arg_M = j;
          }
        }
        if (M > the_max)
          the_max = M;
        if (*(buf_begin + arg_M) > nta::Epsilon) {
          ind.push_back(arg_M);
          nz.push_back(1);
          ++nnz;
        } 
      }

      if (nnz < min_proto_sum_ || the_max < nta::Epsilon) 
        return false;

      if (getNPrototypes(p_) > 0) {
        
        prototypes_[p_].LpNearest(1.0, ind.begin(), ind.end(), nz.begin(), 
                                  nn.begin(), 1, false);
        
        if (nn[0].second < nta::Epsilon) 
          return false;
      }

      prototypes_[p_].addRow(ind.begin(), ind.end(), nz.begin(), true); 

      ++p_;
      return true;
    }
  
    if (sparsification_mode_ == none) {

      from_dense(buf_begin, buf_end, back_inserter(ind), back_inserter(nz));

      // Use regular LpNearest, that is, we care about all the elements.
      if (getNPrototypes(p_) > 0)
        prototypes_[p_].LpNearest(lp_, buf_begin, nn.begin(), 1, true);
      
    } else {

      // Use modified LpNearest, where we care only about some elements in
      // the prototypes.
      if (getNPrototypes(p_) > 0)
        prototypes_[p_].projLpNearest(lp_, buf_begin, nn.begin(), 1, true);

      if (sparsification_mode_ == kWinners) {
        winnerTakesAll3(k_winners_, getSegmentSize(), buf_begin, buf_end,
                        back_inserter(ind), back_inserter(nz), rng_);
    
      } else if (sparsification_mode_ == threshold) {

        nta::threshold(buf_begin, buf_end, 
                       back_inserter(ind), back_inserter(nz), 
                       threshold_);
      }
    } // end sparsification & nearest in nn
      
    // Check for overflow errors in the distance calculation
    value_type distance = nn[0].second;
    NTA_CHECK (distance >= 0 && distance <= std::numeric_limits<value_type>::max())
      << "\nSparsePooler encountered an overflow error in calculating the distance "
      << "of the input from the existing prototypes. The most likely cause is that "
      << "the inputs to the SpatialPooler node are too large. ";
      
    //value_type normalized_dist = nn[0].second / input_masks_.size(p_);
    if (getNPrototypes(p_) > 0 && distance <= min_accept_distance_) 
      return false;

    // Zero-permissive admission
    prototypes_[p_].addRow(ind.begin(), ind.end(), nz.begin(), true); 
    
#ifdef NTA_ASSERTIONS_ON
    if (sparsification_mode_ == none && inference_mode_ != kthroot_product) { 

      // We can only perform this test if we've got at least 1 row for each
      //  prototype. 
      UInt nRows = 0;
      bool  canInfer = true;
      UInt  protoStartIdx = 0;
      for (size_type p = 0; p != input_masks_.nMasks(); ++p) {
        if (prototypes_[p].nRows() == 0)
          canInfer = false;
        if (p == p_)
          protoStartIdx = nRows;
        nRows += prototypes_[p].nRows();
      }
      
      // Perform an inference and see that we get this last coincidence that we just
      //  added as the winner. 
      if (canInfer) {
        Real* outP = new Real[nRows];   
        infer(input_begin, input_end, outP, outP + nRows);
        Real* protoOutP = outP + protoStartIdx;
        UInt  protoNumRows = prototypes_[p_].nRows();
        UInt winner = (UInt) (std::max_element(protoOutP, protoOutP + protoNumRows) 
                               - protoOutP);
        if (winner != protoNumRows-1) {
          infer(input_begin, input_end, outP, outP + nRows);
        }
        delete[] outP;
        NTA_CHECK (winner == protoNumRows-1) << "New coincidence #" << protoNumRows-1 
              << " is not far enough away from existing one at index " << winner << ".\n"
              << "The probable cause is that maxDistance, " << min_accept_distance_ 
              << ", might be set too low for the available precision.\n";
        }
    }
#endif
    
    ++ p_;
    return true;
  }

  //--------------------------------------------------------------------------------
  /**
   * Output is concatenated in same order as the input masks. 
   */
  template <typename InputIterator, typename OutputIterator>
  void 
  SparsePooler::infer(InputIterator input_begin, InputIterator input_end, 
                      OutputIterator output_begin, OutputIterator output_end)
  {
    using namespace std;

    { // Pre-conditions
      NTA_ASSERT(getTotalNPrototypes() > 0)
        << "SparsePooler::infer: Hasn't learnt yet";
    } // End pre-conditions

    if (inference_mode_ == kthroot_product 
        && nearlyZeroRange(input_begin, input_end)) {
      std::fill(output_begin, output_end, (value_type) 0);
      return;
    }

    const size_type segment_size = input_masks_.segmentSize();

    for (size_type p = 0; p != input_masks_.nMasks(); ++p) {

      const SparsePoolerInputMasks::Mask& mask = input_masks_.mask(p);
      buffer_iterator buf_begin = buf_.begin();
      buffer_iterator buf_end = buf_begin + input_masks_.size(p);

      concatenate(input_begin, mask.begin(), mask.end(), buf_begin);

      if (normalize_)
        normalize(buf_begin, buf_end, lp_);
      
      if (inference_mode_ == gaussian) {
        
        value_type ratio = input_masks_.ratio(p);
        value_type k = -(value_type) 0.5 / (sigma_*sigma_*ratio);
        
        if (sparsification_mode_ == none) {
          // We care about everybody
          prototypes_[p].rbf(lp_, k, buf_begin, output_begin);
        } else {
          // We care only about the non-zeros of the prototypes
          prototypes_[p].projRbf(lp_, k, buf_begin, output_begin);
        }
      } else if (inference_mode_ == dot) {
        prototypes_[p].rightVecProd(buf_begin, output_begin);
        
      } else if (inference_mode_ == product) {
        prototypes_[p].rowVecProd(buf_begin, output_begin);

      } else if (inference_mode_ == kthroot_product) {
        SparseMatrixAlgorithms::kthroot_product(prototypes_[p], 
                                                segment_size, 
                                                buf_begin, output_begin, 
                                                .01f/segment_size);
      }

      output_begin += prototypes_[p].nRows();
    }
  }

  //--------------------------------------------------------------------------------
  template <typename InputIterator, typename InputIterator2, typename OutputIterator>
  void SparsePooler::topDownInfer(InputIterator bu_in, InputIterator bu_in_end, 
                                  InputIterator2 td_in, InputIterator2 td_in_end,
                                  OutputIterator td_out)
  {
    using namespace std;
    using namespace nta;

    size_type n_coincidences = getTotalNPrototypes();
    size_type td_n_parents = (size_type) (td_in_end - td_in) / n_coincidences;
    size_type td_out_size = (size_type) (bu_in_end - bu_in);

    vector<value_type> td_sums(n_coincidences, 0);

    for (size_type i = 0; i != n_coincidences; ++i) {
      for (size_type j = 0; j != td_n_parents; ++j)
        td_sums[i] += *(td_in + i + j*n_coincidences);
      td_sums[i] /= td_n_parents;
    }

    size_type offset = 0;

    if (inference_mode_ == gaussian) {
      
      for (size_type p = 0; p != input_masks_.nMasks(); ++p) {

        size_type nc = prototypes_[p].nRows();
        SparsePoolerInputMasks::Mask mask = input_masks_.mask(p);

        for (size_type j = 0; j != mask.size(); ++j) 
          for (size_type k = mask[j].first; k != mask[j].second; ++k) 
            for (size_type i = 0; i != nc; ++i) 
              *(td_out + k) += td_sums[i] * prototypes_[p].get(i,k);

        offset += nc;
      }

    } else if (inference_mode_ == kthroot_product) {

      vector<value_type> nz(td_sums.size(), 0);
      
      for (size_type i = 0; i != nz.size(); ++i)
        nz[i] = td_sums[i] > 0;

      for (size_type p = 0; p != input_masks_.nMasks(); ++p) {

        size_type nc = prototypes_[p].nRows();
        size_type n = prototypes_[p].nCols();
        vector<value_type> result(n), maxScores(n);

        prototypes_[p].leftVecSumAtNZ(td_sums.begin() + offset, result.begin());
        prototypes_[p].leftVecSumAtNZ(nz.begin() + offset, maxScores.begin());
        nta::clip(maxScores, 1, numeric_limits<value_type>::max());
        nta::divide(result, maxScores);
        
        SparsePoolerInputMasks::Mask mask = input_masks_.mask(p);
        
        for (size_type j = 0; j != mask.size(); ++j)
          for (size_type k = mask[j].first; k != mask[j].second; ++k)
            *(td_out + k) += nc * result[k];
      
        offset += nc;
      }
    }
    
    divide_val(td_out, td_out + td_out_size, n_coincidences);
    value_type s = sum(td_out, td_out + td_out_size);
    add_val(td_out, td_out + td_out_size, .1 * s / td_out_size);
  }

  //--------------------------------------------------------------------------------
    
} // end namespace nta
  
//--------------------------------------------------------------------------------
