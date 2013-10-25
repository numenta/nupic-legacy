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
 * Simple class for reading and processing data files
 */

//----------------------------------------------------------------------

#ifndef NTA_VECTOR_FILE_HPP
#define NTA_VECTOR_FILE_HPP

//----------------------------------------------------------------------

#include <vector>
#include <nta/types/types.hpp>
#include <nta/os/FStream.hpp>

namespace nta 
{
  /**
   *  VectorFile is a simple container class for lists of numerical vectors. Its only
   *  purpose is to support the needs of the VectorFileSensor. Key features of
   *  interest are its ability to read in different text file formats and its
   *  ability to dynamically scale its outputs. 
   */
  class VectorFile
  {
  public:
    
    VectorFile();
    virtual ~VectorFile();

    static Int32 maxFormat() { return 6; }

    /// Read in vectors from the given filename. All vectors are expected to
    /// have the same size (i.e. same number of elements). 
    /// If a list already exists, new vectors are expected to have the same size
    /// and will be appended to the end of the list
    /// appendFile will NOT change the scaling vectors as long as the expectedElementCount
    /// is the same as previously stored vectors.
    /// The fileFormat number corresponds to the file formats in VectorFileSensor:
    ///           0        # Reads in unlabeled file with first number = element count
    ///           1        # Reads in a labeled file with first number = element count
    ///           2        # Reads in unlabeled file without element count
    ///           3        # Reads in a csv file
    ///           4        # Reads in a little-endian float32 binary file
    ///           5        # Reads in a big-endian float32 binary file
    ///           6        # Reads in a big-endian IDX binary file
    void appendFile(const std::string &fileName,
                    NTA_Size expectedElementCount,
                    UInt32 fileFormat);
    
    /// Retrieve i'th vector, apply scaling and copy result into output
    /// output must have size of at least 'count' elements
    void getScaledVector(const UInt i, Real *out, UInt offset, Size count);
    
    /// Retrieve the i'th vector and copy into output without scaling
    /// output must have size at least 'count' elements
    void getRawVector(const UInt i, Real *out, UInt offset, Size count);
    
    /// Return the number of stored vectors
    const size_t vectorCount() { return fileVectors_.size(); }

    /// Return the size of each vevtor (number of elements per vector)
    const size_t getElementCount() const;
    
    /// Set the scale and offset vectors to correspond to standard form
    /// Sets the offset component of each element to be -mean
    /// Sets the scale component of each element to be 1/stddev
    void setStandardScaling();
    
    /// Reset scaling to have no effect (unitary scaling vector and zero offset vector)
    /// If nElements > 0, also resize the scaling vector to have that many elements, 
    /// otherwise leave it as-is
    void resetScaling(UInt nElements = 0);
    
    /// Get the scaling and offset values for element e
    void getScaling(const UInt e, Real &scale, Real &offset);

    /// Set the scale value for element e
    void setScale(const UInt e, const Real scale);

    /// Set the offset value for element e
    void setOffset(const UInt e, const Real offset);

    /// Clear the set of vectors and labels, including scale and offset vectors,
    /// release all memory, and set numElements back to zero.
    void clear(bool clearScaling = true);

    // Return true iff a labeled file was read in
    inline bool isLabeled() const 
    { return (! (elementLabels_.empty() || vectorLabels_.empty()) ); }

    /// Save the scale and offset vectors to this stream
    void saveState(std::ostream &str);
    
    /// Initialize the scaling and offset vectors from this stream
    /// If vectorCount() > 0, it is an error if numElements() 
    /// does not match the data in the stream
    void readState(std::istream& state);

    /// Save vectors, unscaled, to a file with the specified format.
    void saveVectors(std::ostream &out, Size nColumns, UInt32 fileFormat, 
      Int64 begin=0, const char *lineEndings=0);
    void saveVectors(std::ostream &out, Size nColumns, UInt32 fileFormat, 
       Int64 begin, Int64 end, const char *lineEndings=0);

  private:
    std::vector<Real *> fileVectors_;     // list of vectors
    std::vector<bool>   own_;             // memory ownership flags
    std::vector<Real>   scaleVector_;     // the scaling vector
    std::vector<Real>   offsetVector_;    // the offset vector
    
    std::vector<std::string> elementLabels_;  // string denoting the meaning of each element
    std::vector<std::string> vectorLabels_;   // a string label for each vector
    
    //------------------- Utility routines 
    void appendCSVFile(IFStream &inFile, Size expectedElementCount);

    /// Read vectors from a binary file.
    void appendFloat32File(const std::string &filename, Size expectedElements, 
      bool bigEndian);

    /// Read vectors from a binary IDX file.
    void appendIDXFile(const std::string &filename, int expectedElements, 
      bool bigEndian);
    
  }; // end class VectorFile
  
  //----------------------------------------------------------------------
  
}

#endif // NTA_VECTOR_FILE_HPP


