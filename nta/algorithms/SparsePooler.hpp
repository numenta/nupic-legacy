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

#ifndef NTA_SPARSE_POOLER_HPP
#define NTA_SPARSE_POOLER_HPP

#include <vector>
#include <iostream>

#include <nta/utils/Random.hpp>

#include <nta/math/stl_io.hpp>
#include <nta/math/array_algo.hpp>
#include <nta/math/NearestNeighbor.hpp>

namespace nta {
  
  //------------------------------------------------------------------------------
  /**
   * SparsePoolerInputMasks contains the set of masks used by the SparsePooler
   * to filter its inputs. That works whatever the actual dimensionality
   * of the inputs.
   */
  class SparsePoolerInputMasks
  {
  public:

    typedef nta::UInt size_type;
    typedef nta::Real value_type;

    // segment origin, segment length
    typedef std::vector<std::pair<size_type, size_type> > Mask;
    
    SparsePoolerInputMasks();
    SparsePoolerInputMasks(size_type ss, const std::vector<Mask>& masks);
    SparsePoolerInputMasks(std::istream& inStream);
    SparsePoolerInputMasks& operator=(const SparsePoolerInputMasks& other);

    inline size_t nMasks() const { return masks_.size(); }
    inline bool empty() const { return nMasks() == 0; }
    inline size_type segmentSize() const { return segment_size_; }
    inline size_type minSize() const { return min_size_; }
    inline size_type maxSize() const { return max_size_; }
    inline size_type size(size_type i) const { return sizes_[i]; }
    inline const Mask& mask(size_type i) const { return masks_[i]; }

    inline value_type ratio(size_type i) const 
    {
      // Cast to float before division!!
      return (value_type)sizes_[i] / (value_type)min_size_;
    }

    void saveState(std::ostream& outStream) const;
    void readState(std::istream& inStream);

  private:
    size_type segment_size_;
    size_type min_size_;
    size_type max_size_;
    std::vector<size_type> sizes_;
    std::vector<Mask> masks_;

    void compute_cache_();
  };

  //--------------------------------------------------------------------------------
  class SparsePooler
  {
  public:
    typedef nta::UInt size_type;
    typedef nta::Real value_type;

    typedef SparseMatrix<size_type, value_type> SM;
    typedef NearestNeighbor<SM> Prototypes;

    typedef enum { none, kWinners, threshold } SparsificationMode;
    typedef enum { gaussian, dot, product, kthroot_product } InferenceMode;

    static SparsificationMode convertSparsificationMode(const std::string& name)
    {
      if (name == "0") return none;
      else if (name == "1") return kWinners;
      else if (name == "2") return threshold;
      else if (name == "none") return none;
      else if (name == "kWinners") return kWinners;
      else if (name == "threshold") return threshold;
      
      NTA_THROW << "Invalid SparsePooler sparsification mode: "
		<< name
		<< " - Should be one of: 0,1,2 or "
		<< "none,kWinners,threshold.";
      return none; // Unused.
    }

    static std::string convertSparsificationMode(SparsificationMode mode)
    {
      if (mode == none)
	return std::string("none");
      else if (mode == kWinners)
	return std::string("kWinners");
      else if (mode == threshold)
	return std::string("threshold");
      return std::string("Unknown");
    }
      
    static InferenceMode convertInferenceMode(const std::string& name)
    {
      if (name == "0") return gaussian;
      else if (name == "1") return dot;
      else if (name == "2") return product;
      else if (name == "3") return kthroot_product;
      else if (name == "gaussian") return gaussian;
      else if (name == "dot") return dot;
      else if (name == "product") return product;
      else if (name == "kthroot_product") return kthroot_product;
      
      NTA_THROW << "Invalid SparsePooler inference mode: "
		<< name
		<< " - Should be one of: 0,1,2,3 or "
		<< "gaussian,dot,product,kthroot_product.";
      return gaussian; // Unused.
    }

    static std::string convertInferenceMode(InferenceMode mode)
    {
      if (mode == gaussian)
	return std::string("gaussian");
      else if (mode == dot)
	return std::string("dot");
      else if (mode == product)
	return std::string("product");
      else if (mode == kthroot_product)
	return std::string("kthroot_product");
      return std::string("Unknown");
    }

    SparsePooler();

    SparsePooler(const SparsePoolerInputMasks& inputMasks,
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
		 UInt32 seed =0);   

    SparsePooler(std::istream& inStream, UInt32 seed =0);

    ~SparsePooler();

    void saveState(std::ostream& outStream) const;
    void readState(std::istream& inStream); 

    inline void setDoNormalization(size_type flag)
    {
      NTA_CHECK(flag == 0 || flag == 1)
	<< "SparsePooler::setDoNormalization: "
	<< "Invalid value: " << flag
	<< " - Should be boolean";
      
      normalize_ = flag == (size_type) 1;
    }

    inline size_type getDoNormalization() const
    {
      return (size_type) normalize_;
    }

    inline void setNorm(value_type lp)
    {
      NTA_CHECK(0 <= lp)
	<< "SparsePooler::setNorm: "
	<< "Invalid value for norm: " << lp
	<< " - Should be >= 0";

      lp_ = lp;
    }

    inline value_type getNorm() const
    {
      return lp_;
    }

    inline void setSparsificationMode(size_type mode)
    {
      NTA_CHECK(0 <= mode && mode < 3)
	<< "SparsePooler::setSparsificationMode: "
	<< "Invalid value: " << mode
	<< " - Should be 0, 1, or 2";

      sparsification_mode_ = (SparsificationMode) mode;
    }

    inline size_type getSparsificationMode() const
    {
      return (size_type) sparsification_mode_;
    }

    inline std::string getSparsificationModeStr() const
    {
      return SparsePooler::convertSparsificationMode(sparsification_mode_);
    }

    inline void setKWinners(size_type kWinners)
    {
      NTA_CHECK(0 <= kWinners && kWinners <= getSegmentSize())
	<< "SparsePooler::setKWinners: "
	<< "Invalid k: " << kWinners
	<< " - Should be 0 <= and <= " << getSegmentSize();

      k_winners_ = kWinners;
    }

    inline size_type getKWinners() const 
    {
      return k_winners_;
    }

    inline void setThreshold(value_type threshold)
    {
      NTA_CHECK(threshold >= 0)
	<< "SparsePooler::setThreshold: "
	<< "Invalid threshold: " << threshold
	<< " - Should be >= 0";

      threshold_ = threshold;
    }

    inline value_type getThreshold() const
    {
      return threshold_;
    }

    inline void setMinAcceptDistance(value_type d)
    {
      NTA_CHECK(nta::Epsilon <= d)
	<< "SparsePooler::setMinAcceptDistance: "
	<< "Invalid distance: " << d
	<< " - Should be >= nta::Epsilon = " 
	<< nta::Epsilon;

      min_accept_distance_ = d;
    }

    inline value_type getMinAcceptDistance() const
    {
      return min_accept_distance_;
    }

    inline void setMinAcceptNorm(value_type d)
    {
      NTA_CHECK(0 <= d)
	<< "SparsePooler::setMinAcceptNorm: "
	<< "Invalid norm: " << d
	<< " - Should be positive";

      min_accept_norm_ = d;
    }

    inline value_type getMinAcceptNorm() const
    {
      return min_accept_norm_;
    }

    inline void setMinProtoSum(value_type x)
    {
      NTA_CHECK(0 < x)
	<< "SparsePooler::setMinProtoSum: "
	<< "Invalid value: " << x
	<< " - Should be > 0";

      min_proto_sum_ = x;
    }

    inline value_type getMinProtoSum() const
    {
      return min_proto_sum_;
    }

    inline void setInferenceMode(size_type mode)
    {
      NTA_CHECK(0 <= mode && mode < 4)
	<< "SparsePooler::setInferenceMode: "
	<< "Invalid value: " << mode
	<< " - Should be 0, 1, 2 or 3";

      inference_mode_ = (InferenceMode) mode;
    }

    inline size_type getInferenceMode() const
    {
      return (size_type) inference_mode_;
    }

    inline std::string getInferenceModeStr() const
    {
      return SparsePooler::convertInferenceMode(inference_mode_);
    }

    inline void setSigma(value_type s)
    {
      NTA_CHECK(0 < s)
	<< "SparsePooler::setSigma: "
	<< "Invalid sigma: " << s
	<< " - Should be positive";

      sigma_ = s;
    }

    inline value_type getSigma() const
    {
      return sigma_;
    }

    inline const std::string& getCurrentSparsePoolerVersion() const 
    {
      return current_sparse_pooler_version_;
    }

    inline size_type getSegmentSize() const
    {
      return getInputMasks().segmentSize();
    }

    inline const SparsePoolerInputMasks& getInputMasks() const
    {
      return input_masks_;
    }

    inline SparsePoolerInputMasks& getInputMasks()
    {
      return input_masks_;
    }

    inline void setInputMasks(const SparsePoolerInputMasks& masks)
    {
      input_masks_ = masks;
      prototypes_.resize(masks.nMasks());
      for (size_type i = 0; i != masks.nMasks(); ++i)
        prototypes_[i].resize(0, masks.size(i));
    }

    inline size_type getTotalNPrototypes() const
    {
      size_type n = 0;
      for (size_type i = 0; i != prototypes_.size(); ++i)
	n += prototypes_[i].nRows();
      return n;
    }

    inline size_t getNPrototypeSizes() const
    {
      return prototypes_.size();
    }

    inline size_type getNPrototypes(size_type i) const
    {
      {
	NTA_ASSERT(0 <= i && i < prototypes_.size())
	  << "SparsPooler::getNPrototypes: "
	  << "Invalid index: " << i 
	  << " - Should be between 0 and " << prototypes_.size();
      }

      return prototypes_[i].nRows();
    }

    inline const Prototypes& getPrototypes(size_type i) const
    {
      {
	NTA_ASSERT(0 <= i && i < prototypes_.size())
	  << "SparsePooler::getPrototypes: Invalid index: " << i 
	  << " - Should be between 0 and " << prototypes_.size();
      }
      return prototypes_[i];
    }
    
    // used by for getParameterHandle("coincidenceMatrix")
    inline SM* getCoincidenceMatrixHandle() const
    {
      // TODO: don't regenerate if there has been no learning since the last time
      cachedCM_ .resize(0, getInputMasks().maxSize(), /* setToZero = */ true);
      for (size_type i = 0; i != prototypes_.size(); ++i)
	cachedCM_.append(getPrototypes(i), true);
      return &cachedCM_;
    }

    inline void 
    getCoincidenceMatrix(std::ostream& buf, bool dense =false) const
    {
      SM* cm = getCoincidenceMatrixHandle();
      if (dense) {
	cm->print(buf);
      } else {
	cm->toCSR(buf);
      }
    }

    template <typename InputIterator, typename OutputIterator>
    inline bool
    learn(InputIterator input_begin, InputIterator input_end, 
	  OutputIterator output);

    template <typename InputIterator, typename OutputIterator>
    inline void 
    infer(InputIterator input_begin, InputIterator input_end, 
	  OutputIterator output_begin, OutputIterator output_end);

    template <typename InputIterator, typename InputIterator2, typename OutputIterator>
    inline void 
    topDownInfer(InputIterator bu_in, InputIterator bu_in_end, 
		 InputIterator2 td_in, InputIterator2 td_in_end,
		 OutputIterator td_out);

    inline void setRNGSeed(UInt32 seed)
    {
      rng_ = Random(seed);
    }

  private:
    static const std::string current_sparse_pooler_version_;

    typedef std::vector<value_type> Buffer;
    typedef Buffer::iterator buffer_iterator;

    bool normalize_;
    value_type lp_;

    SparsificationMode sparsification_mode_;
    size_type k_winners_;
    value_type threshold_;    
      
    value_type min_accept_distance_;
    value_type min_accept_norm_;
    value_type min_proto_sum_;

    InferenceMode inference_mode_;
    value_type sigma_;

    SparsePoolerInputMasks input_masks_;

    size_type p_;
    Buffer buf_;

    std::vector<Prototypes> prototypes_;
    
    nta::Random rng_;

    mutable SM cachedCM_;

    void init_invariants_() const;
  };

  //--------------------------------------------------------------------------------

} // end namespace nta

#include <nta/algorithms/SparsePooler_t.hpp>

//--------------------------------------------------------------------------------
#endif // NTA_SPARSE_POOLER_HPP
