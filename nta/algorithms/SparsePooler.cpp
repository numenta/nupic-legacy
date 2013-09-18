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

#include <nta/algorithms/SparsePooler.hpp>

using namespace std;

namespace nta {

  //--------------------------------------------------------------------------------
  const std::string SparsePooler::current_sparse_pooler_version_ = "SparsePooler_1.7";

  //--------------------------------------------------------------------------------
  // SPARSE POOLER INPUT MASKS
  //--------------------------------------------------------------------------------
  SparsePoolerInputMasks::SparsePoolerInputMasks()
    : segment_size_(0), min_size_(0), max_size_(0),
      sizes_(), masks_()
  {}
  
  //--------------------------------------------------------------------------------
  SparsePoolerInputMasks::SparsePoolerInputMasks(size_type ss, 
						 const std::vector<Mask>& masks)
    : segment_size_(ss), min_size_(0), max_size_(0),
      sizes_(), masks_(masks)
  {
    compute_cache_();
  }
  
  //--------------------------------------------------------------------------------
  SparsePoolerInputMasks::SparsePoolerInputMasks(std::istream& inStream)
    : segment_size_(0), min_size_(0), max_size_(0),
      sizes_(), masks_()
  {
    readState(inStream);
  }
  
  //--------------------------------------------------------------------------------
  SparsePoolerInputMasks& 
  SparsePoolerInputMasks::operator=(const SparsePoolerInputMasks& other)
  {
    if (&other != this) {
      segment_size_ = other.segment_size_;
      min_size_ = other.min_size_;
      max_size_ = other.max_size_;
      sizes_ = other.sizes_;
      masks_ = other.masks_;
    }
    return *this;
  }

  //--------------------------------------------------------------------------------
  void SparsePoolerInputMasks::saveState(std::ostream& outStream) const
  {
    outStream << segmentSize() << " " << masks_ << " ";
  }
  
  //--------------------------------------------------------------------------------
  void SparsePoolerInputMasks::readState(std::istream& inStream)
  {
    inStream >> segment_size_ >> general_vector >> masks_;
    compute_cache_();
  }

  //--------------------------------------------------------------------------------
  void SparsePoolerInputMasks::compute_cache_()
  {
    { // Pre-conditions
      NTA_ASSERT(segment_size_ > 0)
	<< "SparsePoolerInputMasks: Invalid segment size: " << segment_size_
	<< " - Should be > 0";
      
      NTA_ASSERT(masks_.size() > 0)
	<< "SparsePoolerInputMasks: No masks passed";

      for (size_type i = 0; i != masks_.size(); ++i) {
	
	NTA_ASSERT(masks_[i].size() > 0)
	  << "SparsePoolerInputMasks: Empty mask";
	
	for (size_type j = 0; j != masks_[i].size(); ++j) 
	  NTA_ASSERT(masks_[i][j].second > 0)
	    << "SparsePoolerInputMasks: Empty mask segment";
      }
    } // End pre-conditions

    min_size_ = std::numeric_limits<size_type>::max();
    max_size_ = 0;
    sizes_.resize(masks_.size(), 0);
    
    for (size_type i = 0; i != masks_.size(); ++i) {
      size_type a_size = 0;
      for (size_type j = 0; j != masks_[i].size(); ++j) 
	a_size += masks_[i][j].second;
      sizes_[i] = a_size;
      if (a_size < min_size_)
	min_size_ = a_size;    
      if (a_size > max_size_)
	max_size_ = a_size;
    }
  }

  //--------------------------------------------------------------------------------
  std::ostream& operator<<(std::ostream& outStream, const SparsePoolerInputMasks& masks)
  {
    masks.saveState(outStream);
    return outStream;
  }
  
  //--------------------------------------------------------------------------------
  std::istream& operator>>(std::istream& inStream, SparsePoolerInputMasks& masks)
  {
    masks.readState(inStream);
    return inStream;
  }

  //--------------------------------------------------------------------------------
  // SPARSE POOLER
  //--------------------------------------------------------------------------------
  SparsePooler::SparsePooler()
    : normalize_(false),
      lp_(0),
      sparsification_mode_(none),
      k_winners_(0),
      threshold_(0),
      min_accept_distance_(0),
      min_accept_norm_(0),
      min_proto_sum_(1),
      inference_mode_(product),
      sigma_(0),
      input_masks_(),
      p_(0),
      buf_(),
      prototypes_(),
      rng_(0),
      cachedCM_()
  {}

  //------------------------------------------------------------------------------
  SparsePooler::SparsePooler(const SparsePoolerInputMasks& inputMasks,
			     size_type normalize,
			     value_type norm,
			     size_type sparsification_mode,
			     size_type inference_mode,
			     size_type kWinners,
			     value_type threshold,
			     value_type min_accept_distance,
			     value_type min_accept_norm,
			     value_type min_proto_sum,
			     value_type sigma,
			     UInt32 seed)
    : normalize_(false), 
      lp_(0),
      sparsification_mode_(none),
      k_winners_(0),
      threshold_(0),
      min_accept_distance_(0),
      min_accept_norm_(0),
      min_proto_sum_(1),
      inference_mode_(product),
      sigma_(0),
      input_masks_(inputMasks),
      p_(0),
      buf_(inputMasks.maxSize()),
      prototypes_(),
      rng_(seed)
  {
    setDoNormalization(normalize);
    setNorm(norm);
    setSparsificationMode(sparsification_mode);
    setKWinners(kWinners);
    setInferenceMode(inference_mode);
    setThreshold(threshold);
    setMinAcceptDistance(min_accept_distance);
    setMinAcceptNorm(min_accept_norm);
    setMinProtoSum(min_proto_sum);
    setSigma(sigma);

    prototypes_.resize(inputMasks.nMasks());
    for (size_type i = 0; i != inputMasks.nMasks(); ++i)
      prototypes_[i].resize(0, inputMasks.size(i));

    init_invariants_();
  }
  
  //--------------------------------------------------------------------------------
  SparsePooler::SparsePooler(istream& inStream, UInt32 seed)
    : normalize_(false),
      lp_(0),
      sparsification_mode_(none),
      k_winners_(0),
      threshold_(0),
      min_accept_distance_(0),
      min_accept_norm_(0),
      min_proto_sum_(1),
      inference_mode_(product),
      sigma_(0),
      input_masks_(),
      p_(0),
      buf_(),
      prototypes_(),
      rng_(seed)
  {
    readState(inStream);
  }

  //--------------------------------------------------------------------------------
  SparsePooler::~SparsePooler()
  {}

  //--------------------------------------------------------------------------------
  void SparsePooler::saveState(ostream& outStream) const
  {
    outStream << getCurrentSparsePoolerVersion() << " "
	      << getSparsificationMode() << " "
	      << getInferenceMode() << " "
	      << getInputMasks() << " "
	      << getDoNormalization() << " "
	      << getNorm() << " "
	      << getKWinners() << " "
	      << getThreshold() << " "
	      << getMinAcceptDistance() << " "
	      << getMinAcceptNorm() << " "
	      << getMinProtoSum() << " "
	      << getSigma() << " ";

    for (size_type i = 0; i != prototypes_.size(); ++i)
      getPrototypes(i).toCSR(outStream);
  }
  
  //--------------------------------------------------------------------------------
  void SparsePooler::readState(istream& inStream) 
  {
    const std::string where = "SparsePooler::readState: ";

    string flag("");
    size_type i_val = 0;
    value_type f_val = (value_type) 0;

    inStream >> flag;
    
    inStream >> i_val;
    setSparsificationMode(i_val);

    inStream >> i_val;
    setInferenceMode(i_val);

    inStream >> input_masks_;

    inStream >> i_val;
    setDoNormalization(i_val);

    inStream >> f_val;
    setNorm(f_val);

    inStream >> i_val;
    setKWinners(i_val);

    inStream >> f_val;
    setThreshold(f_val);
    
    inStream >> f_val;
    setMinAcceptDistance(f_val);

    inStream >> f_val;
    setMinAcceptNorm(f_val);

    if (flag == "SparsePooler_1.7") {
      inStream >> f_val;
      setMinProtoSum(f_val);
    }

    inStream >> f_val;
    setSigma(f_val);

    size_type n_prototypes = getInputMasks().nMasks();

    prototypes_.resize(n_prototypes);

    for (size_type i = 0; i != n_prototypes; ++i)
      prototypes_[i].fromCSR(inStream, true);
    
    p_ = 0;
    buf_.resize(getInputMasks().maxSize());

    init_invariants_();
  }

 //--------------------------------------------------------------------------------
  void SparsePooler::init_invariants_() const
  {
  }

  //--------------------------------------------------------------------------------
} // end namespace nta
