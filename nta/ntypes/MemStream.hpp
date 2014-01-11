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
 * Definitions for the MemStream classes
 * 
 * These classes implement a stream that uses memory buffer for reading/writing.
 * It is more efficient than using stringstream because it doesn't require making a
 * copy of the data when setting up an input stream for reading or getting the
 * contents of an output stream after it has been written to.
 *
 * These classes operate much like the c++ std deprecated strstream class, and have the same
 * member functions for getting to the buffered data (str(), pcount()) to make them
 * drop-in replacements.
 */


#ifndef NTA_MEM_STREAM_HPP
#define NTA_MEM_STREAM_HPP

#include <sstream>
#include <cstdio> //EOF
#include <stdexcept>
#include <nta/utils/Log.hpp>

namespace nta {

void dbgbreak();

///////////////////////////////////////////////////////////////////////////////////////
/// BasicIMemStreamBuf
///
/// @b Responsibility
/// 
/// The basic input stream buffer used by BasicIMemStream. 
/// 
/// @b Description
///
/// This class simply sets up the buffer for the streambuf to be the caller's buffer. 
/// 
/// @b Resource @b Ownership
///
/// None. This class does not take ownership of the input buffer. It is the caller's
///   responsibility to free it after this class is destroyed. 
///
/////////////////////////////////////////////////////////////////////////////////////
template<typename charT, typename traitsT, typename allocT>
class BasicIMemStreamBuf : public std::basic_streambuf<charT, traitsT>
{

public:
  BasicIMemStreamBuf (const charT* bufP, size_t bufSize) 
  {
    setg ((charT*)bufP, (charT*)bufP, (charT*)bufP+bufSize);
    bufP_ = bufP;
    size_ = bufSize;
  }
  
  //////////////////////////////////////////////////////////////////////////
  /// Set the input buffer for this stream
  /////////////////////////////////////////////////////////////////////////
  void str(const charT* bufP, size_t bufSize)
  {
    setg ((charT*)bufP, (charT*)bufP, (charT*)bufP+bufSize);
    bufP_ = bufP;
    size_ = bufSize;
  }
      
  ///////////////////////////////////////////////////////////////////////////////////
  /// Return a pointer to beginning of the memory stream buffer
  ///
  /// @retval pointer to input buffer maintained by this class
  ////////////////////////////////////////////////////////////////////////////////////
  const charT* str() {return bufP_;}

  ///////////////////////////////////////////////////////////////////////////////////
  /// Return size of the input data
  ///
  /// @retval size of the input data in the buffer
  ////////////////////////////////////////////////////////////////////////////////////
  size_t pcount() {return size_;}

  ///////////////////////////////////////////////////////////////////////////////////
  /// Return size of the input data
  ///
  /// @retval size of the input data in the buffer
  ////////////////////////////////////////////////////////////////////////////////////
  void setg(charT * p1, charT * p2, charT * p3) {std::basic_streambuf<charT, traitsT>::setg(p1,p2,p3);}
private:
  const charT*  bufP_;
  size_t        size_;
  
}; // end class BasicIMemStreamBuf



///////////////////////////////////////////////////////////////////////////////////////
/// BasicOMemStreamBuf
///
/// @b Responsibility
/// 
/// The basic output stream buffer used by BasicOMemStream
/// 
/// @b Description
///
/// This class uses an internal basic_string to manage the storage of characters
/// written to the streambuf. It sets the streambuf's buffer to be the capacity of
/// the string and grows the capacity of the string when overflow() is called. 
/// 
/// @b Resource @b Ownership
///
/// The internal buffer used to hold the stream data. 
///
/////////////////////////////////////////////////////////////////////////////////////
template<typename charT, typename traitsT, typename allocT>
class BasicOMemStreamBuf : public std::basic_streambuf<charT, traitsT>
{
public: 
  typedef std::basic_string<charT, traitsT, allocT> 	stringType_;
  typedef typename traitsT::int_type                    int_type;
  
private:
  stringType_ data_;
  static const size_t growByMin_ = 512;

public:
  BasicOMemStreamBuf () 
  {
    data_.reserve (growByMin_);
    char* bufP = (char*)(data_.data());
    this->setp (bufP, bufP + data_.capacity());
  }
  
  virtual int_type overflow (int_type c)
  {
    size_t  growBy; 
    
    if (c == EOF) return c;
    
    // Remember the current size
    size_t curSize = pcount();
    
    // Grow by 12% (1/8th) of the current size, or the minGrowBy
    growBy = curSize >> 3;
    if (growBy < growByMin_)
      growBy = growByMin_;
        
    // Grow the buffer. We do this by allocating a tmp string of the new size
    // and using assign() to transfer the existing data into it. We can't simply
    // call reserve() on the existing string because it's size() is not set and because
    // of this, reserve() won't copy existing characters into the newly grown buffer for us. 
    stringType_ tmp;
    try {
      tmp.reserve (data_.capacity() + growBy);
    } catch (...) {
      NTA_THROW << "MemStream::write() - request of " << data_.capacity() + growBy
                << " bytes (" << data_.capacity() + growBy 
                << ") exceeds the maximum allowable memory block size.";
      // Note: above used std::hex but Visual C++ Express can't handle that for some reason
    }
    tmp.assign (data_.data(), curSize);    
    data_.swap (tmp);
    
    char* bufP = (char*)(data_.data());
    this->setp (bufP, bufP + data_.capacity());
    
    // Restore the current write position after setting the new buffer
    this->pbump ((int)curSize);

    // Store the new character in the bigger buffer
    return this->sputc (c);
  }
  
  ///////////////////////////////////////////////////////////////////////////////////
  /// Return a pointer to the output data
  ///
  /// This call does not transfer ownership of the output buffer to the caller. The
  /// output buffer pointer is only valid until the next write operation to the stream. 
  ///
  /// @retval pointer to output buffer maintained by this class
  ////////////////////////////////////////////////////////////////////////////////////
  inline const charT* str() {return data_.data();}

  ///////////////////////////////////////////////////////////////////////////////////
  /// Return size of the output data
  ///
  /// @retval size of the output data in the buffer
  ////////////////////////////////////////////////////////////////////////////////////
  inline size_t pcount() {return this->pptr() - this->pbase(); }

}; // end class BasicOMemStreamBuf



///////////////////////////////////////////////////////////////////////////////////////
/// BasicIMemStream
///
/// @b Responsibility
/// 
/// An input stream which allows the caller to specify which data buffer to use. 
/// 
/// @b Description
///
/// The caller constructs the input stream by passing in a buffer and size. All
/// input operations from the stream then extract data from this buffer. The stream
/// does *not* take ownership of the buffer. It is the caller's responsibility to free
/// the buffer after deleting this class. 
/// 
/// @b Resource @b Ownership
///
/// This class does not take ownership of the input buffer. It is the caller's
/// responsibility to free it after the class is destroyed. 
///
/////////////////////////////////////////////////////////////////////////////////////
template<typename charT, typename traitsT, typename allocT>
class BasicIMemStream : public std::basic_istream<charT, traitsT>
{
public: 
  typedef BasicIMemStreamBuf<charT, traitsT, allocT> 	memStreamBufType_;
  
private:
  memStreamBufType_   streamBuf_;
  
public:
  BasicIMemStream(const charT* bufP=0, size_t bufSize=0) : std::istream(&streamBuf_),
     streamBuf_(bufP, bufSize)
  {
    this->rdbuf (&streamBuf_);
  }
  
  //////////////////////////////////////////////////////////////////////////
  /// Set the input buffer for this stream
  /////////////////////////////////////////////////////////////////////////
  void str(const charT* bufP, size_t bufSize)
  {
    streamBuf_.str (bufP, bufSize);
  }
    
  ///////////////////////////////////////////////////////////////////////////////////
  /// Return a pointer to beginning of the memory stream buffer
  ///
  /// @retval pointer to input buffer maintained by this class
  ////////////////////////////////////////////////////////////////////////////////////
  const charT* str() {return streamBuf_.str();}

  ///////////////////////////////////////////////////////////////////////////////////
  /// Return size of the input data
  ///
  /// @retval size of the input data in the buffer
  ////////////////////////////////////////////////////////////////////////////////////
  size_t pcount() {return streamBuf_.pcount();}
    
}; // end class BasicIMemStream


///////////////////////////////////////////////////////////////////////////////////////
/// BasicOMemStream
///
/// @b Responsibility
/// 
/// An output stream that appends data to an internal dynamically grown buffer. 
/// 
/// @b Description
///
/// At any time, the caller can get a pointer to the internal buffer and it's current size
/// through the str() and pcount() member functions. This information is valid until the
/// next write operation to the stream. 
/// 
/// @b Resource @b Ownership
///
/// The internal buffer used to hold the stream data. 
///
/////////////////////////////////////////////////////////////////////////////////////
template<typename charT, typename traitsT, typename allocT>
class BasicOMemStream : public std::basic_ostream<charT, traitsT>
{
public: 
  typedef BasicOMemStreamBuf<charT, traitsT, allocT> 	memStreamBufType_;
  
private:
  memStreamBufType_   streamBuf_;
  
public:
  BasicOMemStream() : std::ostream(&streamBuf_),
     streamBuf_()
  {
    this->rdbuf (&streamBuf_);
  }
  
  ///////////////////////////////////////////////////////////////////////////////////
  /// freeze - does nothing in this class, provided only so this class can be a 
  ///  drop-in replacement for strstream
  ////////////////////////////////////////////////////////////////////////////////////
  void freeze (bool f) {}

  ///////////////////////////////////////////////////////////////////////////////////
  /// Return a pointer to the output data
  ///
  /// This call does not transfer ownership of the output buffer to the caller. The
  /// output buffer pointer is only valid until the next write operation to the stream. 
  ///
  /// @retval pointer to output buffer maintained by this class
  ////////////////////////////////////////////////////////////////////////////////////
  const charT* str() {return streamBuf_.str();}

  ///////////////////////////////////////////////////////////////////////////////////
  /// Return size of the output data
  ///
  /// @retval size of the output data in the buffer
  ////////////////////////////////////////////////////////////////////////////////////
  size_t pcount() {return streamBuf_.pcount();}
    
}; // end class BasicOMemStream


///////////////////////////////////////////////////////////////////////////////////////
// Convenience typedefs
///////////////////////////////////////////////////////////////////////////////////////
typedef BasicIMemStream<char,std::char_traits<char>,std::allocator<char> >  
        IMemStream;
typedef BasicIMemStream<wchar_t,std::char_traits<wchar_t>,std::allocator<wchar_t> > 
        WIMemStream;

typedef BasicOMemStream<char,std::char_traits<char>,std::allocator<char> > 
        OMemStream;
typedef BasicOMemStream<wchar_t,std::char_traits<wchar_t>,std::allocator<wchar_t> > 
        WOMemStream;


} // end namespace nta





#endif // NTA_MEM_STREAM_HPP



