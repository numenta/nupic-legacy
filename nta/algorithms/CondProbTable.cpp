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
 * 
 */ 

#include "nta/utils/Log.hpp"
#include "nta/algorithms/CondProbTable.hpp"

using namespace std;

namespace nta { 
 
  ////////////////////////////////////////////////////////////////////////////
  // Constructor
  //////////////////////////////////////////////////////////////////////////////
  CondProbTable::CondProbTable(const UInt hintNumCols, const UInt hintNumRows) 
    :  hintNumCols_(hintNumCols),
       hintNumRows_(hintNumRows),
       tableP_(NULL),
       cleanTableP_(NULL),
       cleanTableValid_(false),
       rowSums_(), 
       colSums_()
  {
  }  

  ////////////////////////////////////////////////////////////////////////////
  // Destructor
  //////////////////////////////////////////////////////////////////////////////
  CondProbTable::~CondProbTable() 
  {
    delete tableP_;
    delete cleanTableP_;
  }  

  ////////////////////////////////////////////////////////////////////////////
  // Get a row of the table
  //////////////////////////////////////////////////////////////////////////////
  void CondProbTable::getRow(const UInt& row, vector<Real>& contents)
  {
    // Overwrite the contents
    contents.resize(tableP_->nCols());
    tableP_->getRowToDense(row, contents.begin());
  }

  ////////////////////////////////////////////////////////////////////////////
  // Grow the # of rows
  //////////////////////////////////////////////////////////////////////////////
  void CondProbTable::grow(const UInt& rows, const UInt& cols)
  {
    const char* errPrefix = "CondProbTable::grow() - ";
    
    // Allocate the matrix now if we haven't already
    if (!tableP_) {
      NTA_ASSERT(cols != 0) << errPrefix << "Must have non-zero columns";
      
      if (hintNumRows_ != 0)
        tableP_ = new SparseMatrix<UInt, Real>(hintNumRows_, cols);
      else
        tableP_ = new SparseMatrix<UInt, Real>(0,0);
      
      // Setup our column sums
      colSums_.resize(cols, (Real)0);
    }

    UInt curRows = tableP_->nRows();
    UInt curCols = tableP_->nCols();
    UInt nextRows = max(rows, curRows);
    UInt nextCols = max(cols, curCols);

    if ((curRows < nextRows) || (curCols < nextCols)) 
      {
        cleanTableValid_ = false;
        tableP_->resize(nextRows, nextCols);

        rowSums_.resize(nextRows);
        colSums_.resize(nextCols);
      }
  }  

  ////////////////////////////////////////////////////////////////////////////
  // Update a row
  ////////////////////////////////////////////////////////////////////////////
  void CondProbTable::updateRow(const UInt& row, const vector<Real>& distribution)
  {
    //const char*   errPrefix = "CondProbTable::updateRow() - ";
  
    // Grow the matrix if necessary
    UInt cols = UInt(distribution.size());
    if (cols < hintNumCols_)
      cols = hintNumCols_;
    grow(row+1, cols);
  
    // Update the row
    cleanTableValid_ = false;
    tableP_->elementRowApply(row, std::plus<Real>(), distribution.begin());
  
    // Update the row sums and column sums
    Real rowSum = 0;
    vector<Real>::iterator colSumsIter = colSums_.begin();
    CONST_LOOP(vector<Real>, iter, distribution) {
      rowSum = rowSum + *iter;
      *colSumsIter = *colSumsIter + *iter;
      colSumsIter++;
    }
    rowSums_[row] += rowSum;
  }

  ////////////////////////////////////////////////////////////////////////////
  // Infer, given vectors as inputs
  //////////////////////////////////////////////////////////////////////////////
  void CondProbTable::inferRow(const vector<Real>& distribution, 
                               vector<Real>& outScores, inferType infer)
  {
    const char* errPrefix = "CondProbTable::inferRow() - ";
    
    // Make sure they gave us the right source size
    NTA_ASSERT(distribution.size() == tableP_->nCols()) 
      << errPrefix
      << "input distribution vector should be " 
      << tableP_->nCols() << " wide";
    
    // And the right output size
    NTA_ASSERT(outScores.size() >= tableP_->nRows()) 
      << errPrefix
      << "Output vector not large enough to hold all " 
      << tableP_->nRows() << " rows.";
    
    // Call the iterator version
    inferRow(distribution.begin(), outScores.begin(), infer);
  }

  ////////////////////////////////////////////////////////////////////////////
  // Infer, given iterators as inputs
  //////////////////////////////////////////////////////////////////////////////
  void CondProbTable::inferRow(vector<Real>::const_iterator distIter, 
                               vector<Real>::iterator outIter, inferType infer)
  {
    const char* errPrefix = "CondProbTable::inferRow() - ";
  
    // Make sure we have a table
    NTA_ASSERT(tableP_ != NULL) 
      << errPrefix
      << "Must call updateRow at least once before doing inference";
    
    // ----------------------------------------------------------------
    // Marginal inference
    // ----------------------------------------------------------------
    if (infer == inferMarginal) {
  
      // Normalize by the column sums first
      vector<Real> normDist;
      LOOP(vector<Real>, iter, colSums_) {
        normDist.push_back(*distIter / *iter);
        ++distIter;
      }
      
      tableP_->rightVecProd(normDist.begin(), outIter);
    }
  
    // ----------------------------------------------------------------
    // Row evidence
    // ----------------------------------------------------------------
    else if (infer == inferRowEvidence) {

      tableP_->rightVecProd(distIter, outIter);
    
      // Normalize by the row sums
      LOOP(vector<Real>, iter, rowSums_) {
        *outIter = *outIter / *iter;
        ++outIter;
      }
    }
  
    // ----------------------------------------------------------------
    // Max product per row
    // ----------------------------------------------------------------
    else if (infer == inferMaxProd) {
      tableP_->vecMaxProd(distIter, outIter);
    }
  
    // ----------------------------------------------------------------
    // Viterbi, Use a "clean" CPD
    // ----------------------------------------------------------------
    else if (infer == inferViterbi) {
  
      if (!cleanTableValid_)
        makeCleanCPT();
    
      // Do max product per row with clean CPD
      cleanTableP_->vecMaxProd(distIter, outIter);
    } 
  
    // ----------------------------------------------------------------
    // Unknown inference method
    // ----------------------------------------------------------------
    else 
      NTA_THROW << errPrefix << "Unknown inference type " << infer;
  }

  ////////////////////////////////////////////////////////////////////////////
  // make clean CPT
  //////////////////////////////////////////////////////////////////////////////
  void CondProbTable::makeCleanCPT()
  {
    delete cleanTableP_;
  
    UInt nrows = tableP_->nRows(), ncols = tableP_->nCols();
    vector<pair<UInt, Real> > col_max(ncols, make_pair(0, Real(0)));
  
    tableP_->colMax(col_max.begin());
  
    cleanTableP_ = new SparseMatrix01<UInt, Real>(ncols, 1);
  
    for (UInt row = 0; row < nrows; ++row) {
      vector<UInt> nz;
      for (UInt col = 0; col < ncols; ++col) 
        if (col_max[col].first == row)
          nz.push_back(col);
      cleanTableP_->addRow(UInt(nz.size()), nz.begin());
    }

    cleanTableValid_ = true;
  }

  ////////////////////////////////////////////////////////////////////////////
  // save state
  //////////////////////////////////////////////////////////////////////////////
  void CondProbTable::saveState(ostream& state) const
  {
    const char* errPrefix = "CondProbTable::saveState() - ";

    NTA_CHECK(state.good()) << errPrefix << "- Bad stream";

    state << "CondProbTable.V1 ";
  
    // Do we have a table yet?
    if (tableP_) {
      state << "1 ";
      state << tableP_->nCols() << " ";
      tableP_->toCSR(state);
    } else {
      state << "0 ";
      state << hintNumCols_ << " " << hintNumRows_;
    }

    state << " ";
  }

  ////////////////////////////////////////////////////////////////////////////
  // read state
  //////////////////////////////////////////////////////////////////////////////
  void CondProbTable::readState(istream& state)
  {
    const char* errPrefix = "CondProbTable::readState() - ";
    ios::iostate excMask;

    NTA_CHECK(state.good()) << errPrefix << "- Bad stream";
    
    // Turn on exceptions on the stream so we can watch for errors
    excMask = state.exceptions();
    state.exceptions(ios_base::failbit | ios_base::badbit);

    // -----------------------------------------------------------------
    // Verify signature on the stream
    // -----------------------------------------------------------------
    string str;
    state >> str;
    if (str != string("CondProbTable.V1")) {
      NTA_THROW << errPrefix << "Invalid state specified";
      return;
    }
   
    // Delete the old table
    if (tableP_) {
      delete tableP_;
      tableP_ = NULL;
    }

    cleanTableValid_ = false;

    // -----------------------------------------------------------------
    // Get # of columns then read in the old matrix
    // -----------------------------------------------------------------
    try {
      bool hasTable;
      state >> hasTable;
      if (hasTable) {
        state >> hintNumCols_;
        tableP_ = new SparseMatrix<UInt, Real> (0, hintNumCols_);
        tableP_->fromCSR(state);
      } else {
        state >> hintNumCols_ >> hintNumRows_;
      }
    
    } catch (exception& e) {
      NTA_THROW << errPrefix
                << "Error reading from stream: " << e.what();
    }

    // -----------------------------------------------------------------
    // Init other vars if we have a table
    // -----------------------------------------------------------------
    if (tableP_) {
      // Update the row sums and column sums
      rowSums_.resize (tableP_->nRows());
      colSums_.resize (tableP_->nCols());
    
      vector<Real>::iterator rowIter = rowSums_.begin();
      vector<Real>  row;
      for (UInt r=0; r<tableP_->nRows(); ++r, ++rowIter) {
        getRow (r, row);
      
        // Get the row sum
        Real  rowSum = 0;
        CONST_LOOP(vector<Real>, iter, row) {
          rowSum += *iter;
        }
        *rowIter = rowSum;
      
        // Add to column sums
        vector<Real>::const_iterator srcIter = row.begin();
        LOOP(vector<Real>, colIter, colSums_) {
          *colIter = *colIter + *srcIter;
          ++srcIter;
        }
      }
    }
 
    // Restore exceptions mask
    state.exceptions(excMask);
  }
} // namespace nta
