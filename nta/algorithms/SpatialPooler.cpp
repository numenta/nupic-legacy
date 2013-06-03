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
 * Implementation for class SpatialPooler
 */
   
#include <nta/algorithms/SpatialPooler.hpp>
    
namespace nta {   

  //--------------------------------------------------------------------------------
  SpatialPooler::SpatialPooler(const std::vector<UInt>& boundaries,
                               Mode mode, Real var, Real maxD, bool prodModeScaling)
    : mode_(mode), maxDistance_(maxD), k2_(Real(-.5/(var*var))),
      boundaries_(boundaries),
      W_(NULL), W01_(NULL), 
      counts_(),
      scale_(-1),
      prodModeScaling_(prodModeScaling)
  {
    const char* where = "SpatialPooler::SpatialPooler(boundaries): ";

    {
      NTA_CHECK(maxD >= 0)
        << where << "Invalid value for maxDistance, should be >= 0";

      NTA_CHECK(var > 0)
        << where << "Invalid value for variance, should be > 0";

      NTA_CHECK(boundaries.size() >= 1)
        << where << "Need at least one child";

      NTA_CHECK(boundaries_[0] > 0)
        << where << "Zero width child output is not allowed";

      for (UInt i = 1; i < boundaries_.size(); ++i)
        NTA_CHECK(boundaries_[i] > boundaries_[i-1])
          << where
          << "Passed invalid boundaries: " << boundaries_[i-1]
          << " and " << boundaries_[i]   
          << " - Boundaries need to be passed in strictly increasing order"
          << " and no child output element count can be zero";
    }

    UInt ncols = getInputSize();
    UInt nrows = 16;
    UInt nchildren = UInt(boundaries.size());

    try {
      switch (mode_) {
      case gaussian:
	W_ = new NearestNeighbor<SparseMatrix<UInt, Real> >(0, ncols);
	break;
      case dot:
      case product:
      case dot_maxD:
      case product_maxD:
	W01_ = new SparseMatrix01<UInt, Real>(ncols, nrows, nchildren);
	break;
      }
    } catch(const std::bad_alloc& ) {
      
      NTA_THROW 
        << where << "Not enough memory to allocate coincidence matrix";
    }
  }

  //--------------------------------------------------------------------------------
  SpatialPooler::SpatialPooler(std::istream& inStream)
    : mode_(dot), maxDistance_(1), k2_((Real)1.0),
      boundaries_(),
      W_(NULL), W01_(NULL), 
      counts_(), 
      scale_(-1),
      prodModeScaling_(true)
  {
    readState(inStream);
  }

  //--------------------------------------------------------------------------------
  SpatialPooler::~SpatialPooler() 
  {
    delete W_;
    delete W01_;
  }    

  //--------------------------------------------------------------------------------
  SpatialPooler::RowCounts SpatialPooler::getRowCounts() const
  {
    SpatialPooler::RowCounts rowCounts;

    switch (mode_) {
    case dot:
    case product:
    case dot_maxD:
    case product_maxD:
      if (W01_)
	return W01_->getRowCounts();
      else 
	return rowCounts;
      break;
    case gaussian:
      for (UInt i = 0; i < counts_.size(); ++i)
        rowCounts.push_back(std::make_pair(i, counts_[i]));
      break;
    }

    return rowCounts;
  }

  //--------------------------------------------------------------------------------
  void SpatialPooler::pruneCoincidences(const UInt& threshold, 
                                        std::vector<UInt>& del)
  {
    del.clear();

    if (mode_ == dot || mode_ == product
	|| mode_ == dot_maxD || mode_ == product_maxD) {

      std::vector<std::pair<UInt, UInt> > del_rows;
      W01_->deleteRows(threshold, back_inserter(del_rows));
      std::transform(del_rows.begin(), del_rows.end(),
                     back_inserter(del),
                     select1st<std::pair<UInt, UInt> >());

    } else {

      std::vector<UInt> counts_new;

      ITER_1(counts_.size()) 
        if (counts_[i] < threshold) {
          del.push_back(i);
        } else {
          counts_new.push_back(counts_[i]);
        }
      
      W_->deleteRows(del.begin(), del.end());
      counts_.swap(counts_new);
    }
  }
    
  //--------------------------------------------------------------------------------
  void SpatialPooler::saveState(std::ostream& state) const
  {
    {
      NTA_CHECK(state.good())
        << "SpatialPooler::saveState(): "
        << "- Bad stream";

      NTA_CHECK(W_ != NULL || W01_ != NULL)
        << "SpatialPooler::saveState(): "
        << "- Null coincidence matrix";
    }

    // 'SpatialPooler15' adds the 'prodModeScaling' boolean which wasn't
    //  there in 'SpatialPooler'. 
    state << "SpatialPooler15 ";

    // TODO remove extraneous 1, that used to be sigma.
    state << (unsigned int)mode_ << " "
          << maxDistance_ << " 1 "
          << "1" << " " << k2_ << " "
          << (unsigned int)prodModeScaling_ << " ";

    state << boundaries_.size() << " ";
    for (UInt i = 0; i < boundaries_.size(); ++i)
      state << boundaries_[i] << " ";

    switch (mode_) {
    case gaussian:
      state << counts_.size() << " ";
      for (UInt i = 0; i < counts_.size(); ++i)
        state << counts_[i] << " ";
      W_->toCSR(state);
      break;
    case dot:
    case product:
    case dot_maxD:
    case product_maxD:
      W01_->toCSR(state);
      break;
    }
  }

  //--------------------------------------------------------------------------------
  /**
   * readState is a complete factory for SpatialPooler, that allocates
   * the internal data structures. 
   */
  void SpatialPooler::readState(std::istream& state)
  {
    const char* where = "SpatialPooler::readState: ";
    {
      NTA_CHECK(state.good())
        << where << "- Bad stream";
    }
    
    UInt nChildren, childOutputSize;

    boundaries_.clear();

    std::string str;
    state >> str;
    UInt  version = 10;
    if (str == "SpatialPooler")
      version = 10;
    else if (str == "SpatialPooler15")
      version = 15;
    else
      NTA_THROW << where
        << " - Wrong class data format, expected data for SpatialPooler";
      

    unsigned int mode;
    Real sigma, k1;

    state >> mode;
    mode_ = (Mode)mode;
    state >> maxDistance_;
    state >> sigma >> k1 >> k2_;
    
    // Version 1.5 added prodModeScaling
    if (version >= 15)
      state >> prodModeScaling_;
    else
      prodModeScaling_ = true;
      
    state >> nChildren;

    NTA_CHECK(maxDistance_ >= 0)
      << where << "Invalid maxDistance: " << maxDistance_
      << " - Should be >= 0";

    NTA_CHECK(nChildren > 0) 
      << where
      << "Invalid number of children: " << nChildren
      << " - Number of children should be > 0";

    for (UInt i = 0; i < nChildren; ++i) {
      
      state >> childOutputSize;

      NTA_CHECK(childOutputSize > 0) // check upper bound < upper bound of UInt
        << where
        << "Invalid child node output size: " << childOutputSize
        << " for child: " << i
        << " - Child output size should be > 0";

      if (i > 0) {
        NTA_CHECK(UInt(childOutputSize) > boundaries_[boundaries_.size()-1])
          << where
          << "Invalid child node output size: " << childOutputSize
          << " for child: " << i
          << " - the previous boundary is: " << boundaries_[boundaries_.size()-1]
          << " - Boundaries should be in strictly increasing order";
      }

      boundaries_.push_back(UInt(childOutputSize));
    }
    
    delete W_;
    delete W01_;
    
    try {
      
      switch (mode_) {
      case gaussian:
        W_ = new NearestNeighbor<SparseMatrix<UInt, Real> >(0, 16);
        break;
      case dot:
      case product:
      case dot_maxD:
      case product_maxD:
        W01_ = new SparseMatrix01<UInt, Real>(1, 16, UInt(boundaries_.size()));
        break;
      }
      
    } catch (const std::bad_alloc& ) {
      
      NTA_THROW
        << where
        << "Not enough memory to allocate coincidence matrix";
    }

    switch (mode_) {
    case gaussian:
      UInt ncounts;
      state >> ncounts;
      counts_.resize(ncounts, 0);
      for (UInt i = 0; i < ncounts; ++i)
        state >> counts_[i];
      W_->fromCSR(state);
      break;
    case dot:
    case product:
    case dot_maxD:
    case product_maxD:
      // Row counts are handled inside SparseMatrix01, and are restored
      // by fromCSR in the case of a 0/1 sparse matrix.
      W01_->fromCSR(state);
      break;
    }

    if (mode_ == gaussian)
      NTA_CHECK(W_->nCols() == boundaries_[boundaries_.size()-1])
        << where
        << "Invalid number of colums for coincidence matrix: " << W_->nCols()
        << " - doesn't match children nodes aggregated output size: " 
        << boundaries_[boundaries_.size()-1];
    else 
      NTA_CHECK(W01_->nCols() == boundaries_[boundaries_.size()-1])
        << where
        << "Invalid number of colums for coincidence matrix: " << W01_->nCols()
        << " - doesn't match children nodes aggregated output size: " 
        << boundaries_[boundaries_.size()-1];

  }

  //--------------------------------------------------------------------------------

} // end namespace nta


