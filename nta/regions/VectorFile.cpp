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
* Implementation for VectorFile class
*/

#include <cstring> // memset
#include <stdexcept>
#include <string>
#include <iostream>
#include <sstream>
#include <math.h>
#include <nta/regions/VectorFile.hpp>
#include <nta/utils/Log.hpp>
#include <nta/utils/utils.hpp> // For isSystemLittleEndian and utils::swapBytesInPlace.
#include <nta/os/FStream.hpp>
#include <nta/os/Path.hpp>
#include <stdexcept>
#include <zlib.h>

using namespace std;
using namespace nta;

//----------------------------------------------------------------------------
VectorFile::VectorFile() 
{ }


//----------------------------------------------------------------------------
VectorFile::~VectorFile()
{
  clear();
}

//----------------------------------------------------------------------------
void VectorFile::clear(bool clearScaling)
{
  Size n = fileVectors_.size();
  if(own_.size() != fileVectors_.size()) {
    throw logic_error("Invalid ownership flags.");
  }
  
  for(Size i=0; i<n; ++i) {
    if(own_[i]) delete[] fileVectors_[i];
    fileVectors_[i] = 0;
  }
  fileVectors_.clear();
  own_.clear();

  elementLabels_.clear();
  vectorLabels_.clear();
  if (clearScaling)
  {
    scaleVector_.clear();
    offsetVector_.clear();
  }
}

//----------------------------------------------------------------------------
void VectorFile::appendFile(const string &fileName,
                            NTA_Size expectedElementCount,
                            UInt32 fileFormat)
{ 
  bool handled = false;
  switch(fileFormat)
  {
    case 4: // Little-endian.
      appendFloat32File(fileName, expectedElementCount, false);
      handled = true;
      break;
    case 5: // Big-endian.
      appendFloat32File(fileName, expectedElementCount, true);
      handled = true;
      break;
    case 6:
      appendIDXFile(fileName, int(expectedElementCount), true);
      handled = true;
      break;
  }

  if(!handled) {
    // Open up the vector file
    IFStream inFile(fileName.c_str());
    if (!inFile) {
      NTA_THROW << "VectorFile::appendFile - unable to open file: "
        << fileName;
    }
    inFile.exceptions(ios_base::failbit | ios_base::badbit);
  
    if ( fileFormat > 4 ) {
      NTA_THROW << "VectorFile::appendFile - incorrect file format: "
        << fileFormat;
    }
  
    try {
      if (fileFormat==3)
      {
        appendCSVFile(inFile, expectedElementCount);
      }
      else
      {
        // Read in space separated text file
        string sLine;
        NTA_Size elementCount = expectedElementCount;
        if (fileFormat != 2) {
          inFile >> elementCount;
          getline(inFile, sLine);
  
          if (elementCount != expectedElementCount) {
            NTA_THROW << "VectorFile::appendFile - number of elements"
              << " in file (" << elementCount << ") does not match"
              << " output element count (" << expectedElementCount << ")";
          }
        }
  
        // If format is 'labeled', read in the next line, which is a label per elmnt
        if (fileFormat == 1) {
          getline(inFile, sLine);
  
          // Pull out all the words from the first line
          istringstream aLine(sLine.c_str());
          while(1) {
            string aWord;
            aLine >> aWord;
            if(aLine.fail()) break;
            elementLabels_.push_back(aWord);
          }
  
          // Ensure we have the right number of words
          if (elementLabels_.size() != elementCount) {
            NTA_THROW << "VectorFile::appendFile - wrong number of element labels (" 
              << elementLabels_.size() << ") in file " << fileName;
          }
        }
  
        // Read each vector in, including labels if so indicated
        while (!inFile.eof())
        {
          string vectorLabel;
          if (fileFormat == 1) {
            inFile >> vectorLabel;
          }
  
          NTA_Real *b = new NTA_Real[elementCount];
          for (Size i= 0; i < elementCount; ++i) {
            inFile >> b[i];
          }
  
          if (!inFile.eof()) {
            fileVectors_.push_back(b);
            own_.push_back(true);
            vectorLabels_.push_back(vectorLabel);
          }
          else delete [] b;
        }
      }
    } catch(ios_base::failure&) {
      if (!inFile.eof()) 
        NTA_THROW << "VectorFile::appendFile" 
        << "Error reading from sensor input file: " << fileName 
        << " : improperly formatted data";
    }
  }

  NTA_CHECK(fileVectors_.size() > 0)
    << "VectorFile::appendFile - no vectors were read in.";

  // Reset scaling only if the vector lengths changed
  if (scaleVector_.size() != expectedElementCount)
  {
    NTA_INFO << "appendFile - need to reset scale and offset vectors.";
    resetScaling((UInt)expectedElementCount);
  }
}

// Determine if the file is a DOS file (ASCII 13, or CTRL-M line ending) 
// Searches for ASCII 13 or 10. Return true if ASCII 13 is found before ASCII 10
// False otherwise. 
// This is a bit of a hack - if a string contains 13 or 10 it should not count, but
// we don't support strings in files anyway.
static bool dosEndings(IFStream &inFile)
{
  bool unixLines = true;
  int pos = inFile.tellg();
  while (!inFile.eof())
  {
    int c = inFile.get();
    if (c==10) 
    {
      unixLines = false;
      break;
    }
    else if (c==13)
    {
      unixLines = true;
      break;
    }
  }
  inFile.seekg(pos);  // Reset back to where we were 
  return unixLines;
}

void VectorFile::saveVectors(ostream &out, Size nColumns, UInt32 fileFormat, 
  Int64 begin, const char *lineEndings)
{
  saveVectors(out, nColumns, fileFormat, begin, fileVectors_.size(), lineEndings);
}

void VectorFile::saveVectors(ostream &out, Size nColumns, UInt32 fileFormat, 
  Int64 begin, Int64 end, const char *lineEndings)
{
  out.exceptions(ios_base::failbit | ios_base::badbit);

  Size n = fileVectors_.size();
  if(begin < 0) begin += n;
  if(end < 0) end += n;
  if(begin > Int64(n)) {
    stringstream msg;
    msg << "Begin (" << begin << ") out of bounds.";
    throw runtime_error(msg.str());
  }
  if(end > Int64(n)) {
    stringstream msg;
    msg << "End (" << begin << ") out of bounds.";
    throw runtime_error(msg.str());
  }
  if(end < begin) end = begin;

  // Setup iterators for the rows.
  vector<Real *>::const_iterator i=(fileVectors_.begin() + size_t(begin));
  vector<Real *>::const_iterator iend = i + size_t(end - begin);

  switch(fileFormat) {
    case 0:
    case 1:
    case 2:
    case 3:
    {
      // Could be single chars (faster), but might prevent future extension.
      const char *lineSep = lineEndings ? lineEndings : "\n";
      const char *sep = (fileFormat == 3) ? ",": " ";

      // Output the number of columns
      switch(fileFormat) {
        case 0: case 1: out << nColumns << lineSep; break;
        default: break;
      }

      // Decide if each row should be labelled in the output.
      bool hasRowLabels = false;
      vector<string>::const_iterator iRowLabel;
      switch(fileFormat) {
        case 1:
        // case 3: // Could be supported, but is not.
        {
          hasRowLabels = !vectorLabels_.empty();
          if(Int64(vectorLabels_.size()) < end) {
            stringstream msg;
            msg << "Too few vector labels (" << vectorLabels_.size() << ") "
                   "to write to file (writing to row " << end << ").";
            throw runtime_error(msg.str());
          }
          break;
        }
        default: break;
      }

      // Output the column labels.
      switch(fileFormat) {
        case 1:
        {
          if(nColumns && !elementLabels_.size())
            throw runtime_error("Format '1' requires column labels.");
          vector<string>::const_iterator iLabel=elementLabels_.begin(),
            labelEnd=elementLabels_.end();
          if(hasRowLabels) out << sep; // No row label for header row.
          out << *(iLabel++);
          for(; iLabel!=labelEnd; ++iLabel) out << sep << (*iLabel);
          out << lineSep;
          break;
        }
        case 3: // Identical to 1, but different error conditions.
        {
          if(elementLabels_.size()) {
            vector<string>::const_iterator iLabel=elementLabels_.begin(),
              labelEnd=elementLabels_.end();
            if(hasRowLabels) out << sep; // No row label for header row.
            out << *(iLabel++);
            for(; iLabel!=labelEnd; ++iLabel) out << sep << (*iLabel);
            out << lineSep;
          }
          break;
        }
        default: break;
      }

      // Output the rows.
      for(; i!=iend; ++i) {
        if(hasRowLabels) {
          out << *(iRowLabel++);
          if(nColumns) out << sep;
        }
        const Real *p = *i;
        if(nColumns) {
          const Real *pEnd = p + nColumns;
          out << *(p++);
          for(; p<pEnd;) out << sep << *(p++);
        }
        out << lineSep;
      }

      break;
    }
    case 4:
    case 5:
    {
      if(end <= begin) return;
      const Size rowBytes = nColumns * sizeof(Real32);
      const bool bigEndian = (fileFormat == 5);
      const bool needSwap = (utils::isSystemLittleEndian() == bigEndian);
      const bool needConversion = (sizeof(Real32) == sizeof(Real));
      
      if(needSwap || needConversion) {
        Real32 *buffer = new Real32[nColumns];
        try {
          for(; i!=iend; ++i) {
            if(needConversion) {
              const Real *p = *i;
              for(Size j=0; j<nColumns; ++j) buffer[j] = *(p++);
            }
            if(needSwap) utils::swapBytesInPlace(buffer, nColumns);
            out.write((char *) buffer, streamsize(rowBytes));
          }
        }
        catch(...) {
          delete[] buffer;
          throw;
        }
        delete[] buffer;
      }
      else {
        for(; i!=iend; ++i)
          out.write((char *) (*i), streamsize(rowBytes));
      }
      break;
    }
    default:
    {
      stringstream msg;
      msg << "File format '" << fileFormat << "' not supported for writing.";
      throw runtime_error(msg.str());
    }
  }
  out.flush();
}

class AutoReleaseFile
{
public:
  void * file_;
  AutoReleaseFile(const string &filename) : file_(ZLib::fopen(filename, "rb"))
  {
    if(!file_) throw runtime_error("Unable to open file '" + filename + "'.");
  }
  ~AutoReleaseFile() { ::gzclose((gzFile)file_); file_ = 0; }
  void read(void *out, int n)
  {
    int result = gzread((gzFile)file_, out, n);
    if(result < n) throw runtime_error("Failed to read requested bytes from file.");
  }
};

void VectorFile::appendFloat32File(const string &filename, 
  Size expectedElements, bool bigEndian)
{
  const bool needSwap = (utils::isSystemLittleEndian() == bigEndian);
  AutoReleaseFile file(filename);

  Size totalBytes = Path::getFileSize(filename);
  if(totalBytes == 0) return; // Early exit when there are no new vectors.

  Size nRows = totalBytes / (expectedElements * sizeof(Real32));
  Size totalElements = nRows * expectedElements;
  if((totalElements * sizeof(Real32)) != totalBytes) {
    stringstream msg;
    msg << "Binary file size (" << totalBytes << "b) is not a multiple of "
           "expected elements (" << expectedElements << ") and "
           "32-bit float size.";
    throw runtime_error(msg.str());
  }
  const bool needConversion = (sizeof(Real32) == sizeof(Real));
  // if !(needSwap || needConversion), would like to use:
  //   ::mmap(0, totalBytes, PROT_READ, 0, fileDescriptor, 0);
  
  Size offset = fileVectors_.size();
  if(offset != own_.size()) {
    throw logic_error("Invalid ownership flags.");
  }
  Size nRowLabels = vectorLabels_.size();
  if(nRowLabels && (nRowLabels != offset)) {
    throw logic_error("Invalid number of row labels.");
  }

  Real *block = 0;

  try {
    // Set up the ownership.
    own_.resize(offset + nRows, false);
    own_[offset] = true; // The first vector pointer points to the whole block.

    if(nRowLabels) vectorLabels_.resize(offset + nRows);

    block = new Real[nRows * expectedElements];

    // Set all the row pointers.
    fileVectors_.resize(offset + nRows);
    vector<Real *>::iterator cur = fileVectors_.begin() + offset;
    Real *pEnd = block + (nRows * expectedElements);
    for(Real *pBlock=block; pBlock!=pEnd; pBlock+=expectedElements) {
      *(cur++) = pBlock;
    }
  
    file.read(block, int(totalBytes));

    if(needSwap) utils::swapBytesInPlace(block, totalElements);
    if(needConversion) {
      Real32 *pRead = reinterpret_cast<Real32 *>(block) + (totalElements - 1);
      Real *pWrite = block + (totalElements - 1);
      for(; pWrite>=block;) {
        *(pWrite--) = *(pRead--);
      }
    }
  }
  catch(...) {
    delete[] block;
    fileVectors_.resize(offset);
    own_.resize(offset);
    if(nRowLabels) vectorLabels_.resize(offset);
    throw;
  }
}

// Append a CSV file to the list of stored vectors. There are some strict 
// assumptions here. We assume that each row has at least expectedElements 
// numbers separated by commas. It is ok to have more, we keep the first 
// expectedElements numbers. In addition, the first expectedElements values
// must be numbers. We do not handle having a bunch of strings or empty values
// interspersed in the middle. If a row does have any of the above errors, 
// the routine will silently skip it. The code handles error conditions like:
//    23,,43
//    23,hello,42
//    ,23,,23
//    23443 w4343
//    23,24,
//    23,"42,d",55

void VectorFile::appendCSVFile(IFStream &inFile, Size expectedElements)
{
  // Read in csv file one line at a time. If that line contains any errors, 
  // skip it and move onto the next one.
  try
  {
    bool dosLines = dosEndings(inFile);
    while (!inFile.eof())
    {
      Size elementsFound = 0;
      Real *b = new Real[expectedElements];
      // Read and parse a single line
      string sLine;            // We'll use string for robust line parsing
      stringstream converted;  // We'll use stringstream for robust ascii text to Real conversion
      size_t beg = 0, pos = 0;
      
      // Read the next line, using the appropriate delimiter
      try
      {
        if (dosLines) getline(inFile,sLine,'\r');
        else getline(inFile, sLine);
      } catch(...) {
        // An exception here is ok
        break;
      }
      
      while (pos != string::npos)
      {
        pos = sLine.find(',', beg);
        converted << sLine.substr(beg, pos-beg) << " ";
        beg = pos+1;
      }
      for(Size i = 0; i < expectedElements; i++) {
        converted >> b[i];
        if(converted.fail()) break;
        elementsFound++;
      }

      // Validate the parsed line and store it.
      // At this point b will have some numbers. If elementsFound == expectedElements
      // then everything went well and we can insert the array into fileVectors_
      // If not, then we deallocate the memory for b 
      if (elementsFound == expectedElements)
      {
        fileVectors_.push_back(b);
        own_.push_back(true);
        vectorLabels_.push_back(string());
        b = 0;
      }
      else 
      {
        delete [] b;
        b = 0;
      }
    }

  // any bizarre errors and cleanup
  } catch(...) {
    NTA_THROW << "VectorFile - Error reading CSV file";
  }
}

template<typename T1, typename T2, typename TSize>
void convert(T2 *pOut, const T1 *pIn, TSize n, TSize fill)
{
  for(TSize i=0; i<n; ++i)
    *(pOut++) = T2(*(pIn++));
  if(fill) ::memset(pOut, 0, fill * sizeof(T2));
}

void VectorFile::appendIDXFile(const string &filename,
  int expectedElements, bool bigEndian)
{
  const bool needSwap = (utils::isSystemLittleEndian() == bigEndian);
  AutoReleaseFile file(filename);

  char header[4];
  file.read(header, 4);
  
  int nDims = header[3];
  if(nDims < 1) throw runtime_error("Invalid number of dimensions.");
  int dims[256];
  file.read(dims, nDims * sizeof(int));
  if(needSwap) utils::swapBytesInPlace(dims, nDims);

  int vectorSize = 1;
  for(int i=1; i<nDims; ++i) vectorSize *= dims[i];
  int nRows = dims[0];

  int elSize = 0;
  switch(header[2]) {
    case 0x08: elSize = 1; break; // unsigned byte.
    case 0x09: elSize = 1; break; // signed byte.
    case 0x0B: elSize = 2; break; // signed short.
    case 0x0C: elSize = 4; break; // signed int.
    case 0x0D: elSize = 4; break; // 32-bit float.
    case 0x0E: elSize = 8; break; // 64-bit float.
    default:
      throw runtime_error("Unknown element type.");
  }

  Size offset = fileVectors_.size();
  if(offset != own_.size()) {
    throw logic_error("Invalid ownership flags.");
  }
  Size nRowLabels = vectorLabels_.size();
  if(nRowLabels && (nRowLabels != offset)) {
    throw logic_error("Invalid number of row labels.");
  }

  // We will read into one block and copy across to the final destination.
  // This is not as efficient as it could be in the optimized case, but that
  // is only one of many possible configurations.

  int readRow = vectorSize * elSize;
  char *readBuffer = new char[readRow];

  Real *block = new Real[nRows * expectedElements];
  Real *pBlock = block;
  
  int copy = (expectedElements < vectorSize) ? expectedElements : vectorSize;
  int fill = expectedElements - copy;
  
  try {
    switch(header[2]) {
      case 0x08: // unsigned byte.
      {
        unsigned char *pRead = reinterpret_cast<unsigned char *>(readBuffer);
        for(int row=0; row<nRows; ++row) {
          file.read(pRead, readRow);
          // No need for byte swapping.
          convert(pBlock, pRead, copy, fill);
          pBlock += expectedElements;
        }
        break;
      }
      case 0x09: // signed byte.
      {
        signed char *pRead = reinterpret_cast<signed char *>(readBuffer);
        for(int row=0; row<nRows; ++row) {
          file.read(pRead, readRow);
          // No need for byte swapping.
          convert(pBlock, pRead, copy, fill);
          pBlock += expectedElements;
        }
        break;
      }
      case 0x0B: // signed short.
      {
        short *pRead = reinterpret_cast<short *>(readBuffer);
        for(int row=0; row<nRows; ++row) {
          file.read(pRead, readRow);
          if(needSwap) utils::swapBytesInPlace(pRead, copy);
          convert(pBlock, pRead, copy, fill);
          pBlock += expectedElements;
        }
        break;
      }
      case 0x0C: // signed int.
      {
        int *pRead = reinterpret_cast<int *>(readBuffer);
        for(int row=0; row<nRows; ++row) {
          file.read(pRead, readRow);
          if(needSwap) utils::swapBytesInPlace(pRead, copy);
          convert(pBlock, pRead, copy, fill);
          pBlock += expectedElements;
        }
        break;
      }
      case 0x0D: // 32-bit float.
      {
        float *pRead = reinterpret_cast<float *>(readBuffer);
        for(int row=0; row<nRows; ++row) {
          file.read(pRead, readRow);
          if(needSwap) utils::swapBytesInPlace(pRead, copy);
          convert(pBlock, pRead, copy, fill);
          pBlock += expectedElements;
        }
        break;
      }
      case 0x0E: // 64-bit float.
      {
        double *pRead = reinterpret_cast<double *>(readBuffer);
        for(int row=0; row<nRows; ++row) {
          file.read(pRead, readRow);
          if(needSwap) utils::swapBytesInPlace(pRead, copy);
          convert(pBlock, pRead, copy, fill);
          pBlock += expectedElements;
        }
        break;
      }
      default: throw logic_error("Unsupported type."); break;
    }

    // Set up the ownership.
    own_.resize(offset + nRows, false);
    own_[offset] = true; // The first vector pointer points to the whole block.

    if(nRowLabels) vectorLabels_.resize(offset + nRows);

    // Set all the row pointers.
    fileVectors_.resize(offset + nRows);
    vector<Real *>::iterator cur = fileVectors_.begin() + offset;
    Real *pEnd = block + (nRows * expectedElements);
    for(Real *pCur=block; pCur!=pEnd; pCur+=expectedElements)
      *(cur++) = pCur;
  }
  catch(...) {
    delete[] block;
    delete[] readBuffer;
    fileVectors_.resize(offset);
    own_.resize(offset);
    if(nRowLabels) vectorLabels_.resize(offset);
    throw;
  }

  delete[] readBuffer; readBuffer = 0;
  // Don't delete block, as it is owned by fileVectors_ now.
}

/// Reset scaling to have no effect (unitary scaling vector and zero offset vector)
void VectorFile::resetScaling(UInt nElements)
{
  if (nElements != 0)
  {
    scaleVector_.resize(nElements);
    offsetVector_.resize(nElements);
  }
  for (unsigned int i= 0; i < scaleVector_.size(); i++)
  {
    scaleVector_[i] = 1.0;
    offsetVector_[i] = 0.0;
  }
}

const size_t VectorFile::getElementCount() const
{ 
  return scaleVector_.size(); 
}


/// Retrieve the i'th vector and copy into output without scaling
/// output must have size at least elementCount
void VectorFile::getRawVector(const UInt v, Real *out, UInt offset, Size count)
{
  if (v >= vectorCount())
    NTA_THROW << "Requested non-existent vector: " << v;

  if ( !out || (count==0) )
    NTA_THROW << "Invalid arguments out is null and/or count is zero";

  if (getElementCount() < offset + count)
    NTA_THROW 
      << "Wrong offset/count: the sum " << offset << "+" << count << " = " << offset + count
      << ", must be smaller than element count: " << getElementCount();
  // Get the pointers and copy over the vector
  Real *vec  = fileVectors_[v];
  for (Size i= 0; i < count; i++)
    out[i] = vec[offset + i];
}

/// Retrieve i'th vector, apply scaling and copy result into output
/// output must have size at least 'count' elements
void VectorFile::getScaledVector(const UInt v, Real *out, UInt offset, Size count)
{
  if (v >= vectorCount())
    NTA_THROW << "Requested non-existent vector: " << v;

  NTA_CHECK(getElementCount() <= offset + count);

  // Get the pointers and copy over the vector
  Real *vec  = fileVectors_[v];  
  for (Size i = 0; i < count; i++)
  {
    out[i] = scaleVector_[i]*(vec[i + offset] + offsetVector_[i]);
  }
}

/// Get the scaling and offset values for element e
void VectorFile::getScaling(const UInt e, Real &scale, Real &offset)
{
  if (e >= getElementCount())
    NTA_THROW << "Requested non-existent element: " << e;
  scale = scaleVector_[e];
  offset = offsetVector_[e];
}

/// Set the scale value for element e
void VectorFile::setScale(const UInt e, const Real scale)
{
  if (e >= getElementCount())
    NTA_THROW << "Requested non-existent element: " << e;
  scaleVector_[e] = scale;
}

/// Set the offset value for element e
void VectorFile::setOffset(const UInt e, const Real offset)
{
  if (e >= getElementCount())
    NTA_THROW << "Requested non-existent element: " << e;
  offsetVector_[e] = offset;
}

/// Set the scale and offset vectors to correspond to standard form
/// Sets the offset component of each element to be -mean
/// Sets the scale component of each element to be 1/stddev
void VectorFile::setStandardScaling()
{
  if ( (getElementCount() == 0) || (vectorCount() <= 1) )
    NTA_THROW << "Error in setting standard scaling: insufficient vectors loaded in memory.";

  Size nv = vectorCount();
  for (UInt e= 0; e < getElementCount(); e++)
  {
    double sum = 0, sum2 = 0;   // Accumulate sums as doubles

    // First compute the mean and offset
    for (Size i= 0; i < nv; i++) sum += fileVectors_[i][e];
    double mean = sum / nv;
    offsetVector_[e] = (Real) (-mean);

    // Now compute the squared term for stdev
    for (Size i= 0; i < nv; i++)
    {
      double s = (fileVectors_[i][e]-mean);
      sum2 += s*s;
    }

    // Now compute the "unbiased" or "n-1" form of standard deviation
    double stdev = sqrt( sum2/(nv-1) );
    if (fabs(stdev) < 0.00000001)
      NTA_THROW << "Error setting standard form, stdeviation is almost zero for some component.";
    scaleVector_[e] = (Real) (1.0 / stdev);
  }
}

/// Save the scale and offset vectors to this stream
void VectorFile::saveState(ostream &str)
{
  if (!str.good())
    NTA_THROW << "saveState(): Internal error - Bad stream";

  // Save the number of elements, followed by scaling 
  // and offset numbers for each component
  str << getElementCount() << " ";
  for (UInt i= 0; i < getElementCount(); i++)
  {
    str << scaleVector_[i] << " " << offsetVector_[i] << " ";
  }
  if (!str.good())
    NTA_THROW << "saveState(): Internal error - Bad stream";
}

/// Save the scale and offset vectors to this stream
void VectorFile::readState(istream& str)
{
  if (!str.good())
    NTA_THROW << "readState(): Internal error - Bad stream or network file";

  UInt numElts;
  str >> numElts;
  if ( (vectorCount()>0) && (numElts != getElementCount()) )
    NTA_THROW << "readState(): Number of elements in stream does not match "
              << "stored vectors";

  resetScaling(numElts);
  for (UInt i= 0; i < numElts; i++)
  {
    str >> scaleVector_[i];
    str >> offsetVector_[i];
  }
  if (!str.good())
    NTA_THROW << "readState(): Internal error - Bad stream or network file";
}

