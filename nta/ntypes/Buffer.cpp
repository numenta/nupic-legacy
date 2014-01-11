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
*/

#include <nta/ntypes/Buffer.hpp>
#include <nta/utils/Log.hpp>
#include <string>
#include <algorithm>
#include <cstring>

namespace nta
{

  // -----------------------------------------
  //
  //    R E A D   B U F F E R
  //
  // -----------------------------------------
  
  NTA_Size staticReadBufferGetSize(NTA_ReadBufferHandle handle)
  {
    NTA_CHECK(handle != NULL);
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->getSize();
  }

  const NTA_Byte * staticGetData(NTA_ReadBufferHandle handle)
  {
    NTA_CHECK(handle != NULL);
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->getData();
  }

  void staticReset(NTA_ReadBufferHandle handle)
  {
    NTA_CHECK(handle != NULL);
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->reset();
  }  
  
  static NTA_Int32 staticReadByte(NTA_ReadBufferHandle handle, NTA_Byte * value)
  {
    if (!handle || !value)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(*value);
  }

  NTA_Int32 staticReadByteArray(NTA_ReadBufferHandle handle, NTA_Byte * value, NTA_Size * size)
  {
    if (!handle || !value || !size || *size <= 0)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(value, *size);
  }


  NTA_Int32 staticReadString(NTA_ReadBufferHandle handle, 
      NTA_Byte ** value, 
      NTA_UInt32 * size,
      NTA_Byte *(*fAlloc)(NTA_UInt32),
      void (*fDealloc)(NTA_Byte *)
    )
  {
    if (!handle || !value) {
      return -1;
    }
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->readString(*value, *size, fAlloc, fDealloc);
  }


  static NTA_Int32 staticReadUInt32(NTA_ReadBufferHandle handle, NTA_UInt32 * value)
  {
    if (!handle || !value)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(*value);
  }

  NTA_Int32 staticReadUInt32Array(NTA_ReadBufferHandle handle, NTA_UInt32 * value, NTA_Size size)
  {
    if (!handle || !value || size <= 0)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(value, size);
  }
  
  static NTA_Int32 staticReadInt32(NTA_ReadBufferHandle handle, NTA_Int32 * value)
  {
    if (!handle || !value)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(*value);
  }

  NTA_Int32 staticReadInt32Array(NTA_ReadBufferHandle handle, NTA_Int32 * value, NTA_Size size)
  {
    if (!handle || !value || size <= 0)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(value, size);
  }
  
  static NTA_Int32 staticReadUInt64(NTA_ReadBufferHandle handle, NTA_UInt64 * value)
  {
    if (!handle || !value)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(*value);
  }

  NTA_Int32 staticReadUInt64Array(NTA_ReadBufferHandle handle, NTA_UInt64 * value, NTA_Size size)
  {
    if (!handle || !value || size <= 0)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(value, size);
  }

  static NTA_Int32 staticReadInt64(NTA_ReadBufferHandle handle, NTA_Int64 * value)
  {
    if (!handle || !value)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(*value);
  }
  
  NTA_Int32 staticReadInt64Array(NTA_ReadBufferHandle handle, NTA_Int64 * value, NTA_Size size)
  {
    if (!handle || !value || size <= 0)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(value, size);
  }

  static NTA_Int32 staticReadReal32(NTA_ReadBufferHandle handle, NTA_Real32 * value)
  {
    if (!handle || !value)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(*value);
  }
  
  NTA_Int32 staticReadReal32Array(NTA_ReadBufferHandle handle, NTA_Real32 * value, NTA_Size size)
  {
    if (!handle || !value || size <= 0)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(value, size);
  }

  static NTA_Int32 staticReadReal64(NTA_ReadBufferHandle handle, NTA_Real64 * value)
  {
    if (!handle || !value)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(*value);
  }
  
  NTA_Int32 staticReadReal64Array(NTA_ReadBufferHandle handle, NTA_Real64 * value, NTA_Size size)
  {
    if (!handle || !value || size <= 0)
      return -1;
    
    ReadBuffer * rb = reinterpret_cast<ReadBuffer *>(handle);
    return rb->read(value, size);
  }

  ReadBuffer::ReadBuffer(const char * bytes, Size size, bool copy) : 
    bytes_(copy ? new Byte[size] : NULL),
    memStream_(copy ? bytes_.get() : bytes, size)
  {
    // Copy the buffer to the internal bytes_ array (because 
    // MemStream needs persistent external storage if copy==true
    if (copy)
      ::memcpy(bytes_.get(), bytes, size);
    
    // Turn on exceptions for memStream_
    memStream_.exceptions(std::ostream::failbit | std::ostream::badbit);
    
    // Initialize the NTA_Readbuffer struct
    handle = reinterpret_cast<NTA_ReadBufferHandle>(this);
    NTA_ReadBuffer::reset = staticReset;
    NTA_ReadBuffer::getSize = staticReadBufferGetSize;
    NTA_ReadBuffer::getData = staticGetData;

    readByte = staticReadByte;
    readByteArray = staticReadByteArray;
    readAsString = staticReadString;

    readInt32 = staticReadInt32;  
    readInt32Array = staticReadInt32Array;
    readUInt32 = staticReadUInt32;
    readUInt32Array = staticReadUInt32Array;

    readInt64 = staticReadInt64;
    readInt64Array = staticReadInt64Array;        
    readUInt64 = staticReadUInt64;
    readUInt64Array = staticReadUInt64Array;
    
    readReal32 = staticReadReal32;
    readReal32Array = staticReadReal32Array;
    readReal64 = staticReadReal64;
    readReal64Array = staticReadReal64Array;
  }
  
  ReadBuffer::ReadBuffer(const ReadBuffer & other)
  {
    assign(other);
  }
  
  ReadBuffer & ReadBuffer::operator=(const ReadBuffer & other)
  {
    assign(other);
    return *this;
  }
  
  void ReadBuffer::assign(const ReadBuffer & other)
  {
    handle = reinterpret_cast<NTA_ReadBufferHandle>(this);
    NTA_ReadBuffer::reset = staticReset;
    NTA_ReadBuffer::getSize = staticReadBufferGetSize;
    NTA_ReadBuffer::getData = staticGetData;
    
    readByte = staticReadByte;
    readByteArray = staticReadByteArray;
    readAsString = staticReadString;

    readInt32 = staticReadInt32;  
    readInt32Array = staticReadInt32Array;
    readUInt32 = staticReadUInt32;
    readUInt32Array = staticReadUInt32Array;

    readInt64 = staticReadInt64;
    readInt64Array = staticReadInt64Array;        
    readUInt64 = staticReadUInt64;
    readUInt64Array = staticReadUInt64Array;
    
    readReal32 = staticReadReal32;
    readReal32Array = staticReadReal32Array;
    readReal64 = staticReadReal64;
    readReal64Array = staticReadReal64Array;  
    
    bytes_ = other.bytes_;
    memStream_.str(bytes_.get(), other.getSize());
  }

  void ReadBuffer::reset()  const
  {
    IMemStream::memStreamBufType_ * s = static_cast<IMemStream::memStreamBufType_ *>(memStream_.rdbuf());
    s->setg(bytes_.get(), bytes_.get(), bytes_.get()+memStream_.pcount());
    memStream_.clear();
  }

  Size ReadBuffer::getSize()  const
  {
    return (Size)memStream_.pcount();
  }

  const char * ReadBuffer::getData()  const
  {
    return memStream_.str();
  }

  Int32 ReadBuffer::read(Byte & value)  const
  {
    return readT(value);
  }

  Int32 ReadBuffer::read(Byte * bytes, Size  & size)  const
  {
    ReadBuffer * r = const_cast<ReadBuffer *>(this);
    try
    {
    #ifdef WIN32
      size = r->memStream_._Readsome_s(bytes, size, (std::streamsize)size);
    #else
      size = r->memStream_.readsome(bytes, size);
    #endif
      return 0;
    }
    catch (...)
    {
      size = 0;
      return -1;
    }
  }

  Int32 ReadBuffer::read(Int32 & value) const
  {
    return readT(value);
  }
  
  Int32 ReadBuffer::read(Int32 * value, Size size) const
  {
    return readT(value, size);
  }

  Int32 ReadBuffer::read(UInt32 & value) const
  {
    return readT(value);
  }
  
  Int32 ReadBuffer::read(UInt32 * value, Size size) const
  {
    return readT(value, size);
  }

  Int32 ReadBuffer::read(Int64 & value) const
  {
    return readT(value);
  }
  
  Int32 ReadBuffer::read(Int64 * value, Size size) const
  {
    return readT(value, size);
  }

  Int32 ReadBuffer::read(UInt64 & value) const
  {
    return readT(value);
  }
  
  Int32 ReadBuffer::read(UInt64 * value, Size size) const
  {
    return readT(value, size);
  }

  Int32 ReadBuffer::read(Real32 & value) const
  {
    return readT(value);
  }

  Int32 ReadBuffer::read(Real32 * value, Size size) const
  {
    return readT(value, size);
  }
  
  Int32 ReadBuffer::read(Real64 & value) const
  {
    return readT(value);
  }
  
  Int32 ReadBuffer::read(Real64 * value, Size size) const
  {
    return readT(value, size);
  }

  inline Int32 findWithLeadingWhitespace(const ReadBuffer &r, char c, int maxSearch) 
  {
    char dummy;
    Int32 result;
    for(int i=0; i<maxSearch; ++i) {
      dummy = 0;
      result = r.readT(dummy);
      if(result != 0) return result;
      if(dummy == c) return 0;
      else if(!::isspace(dummy)) {
        return -1;
      }
      else NTA_CHECK(::isspace(dummy));
    }
    return -1;
  }

  inline Int32 findWithLeadingWhitespace(const ReadBuffer &r, const char *s, 
      int maxSearch) 
  {
    Int32 result = 0;
    while(*s) {
      result = findWithLeadingWhitespace(r, *s, maxSearch);
      if(result != 0) return result;
      ++s;
      maxSearch = 1;
    }
    return 0;
  }

  typedef NTA_Byte *(*fp_alloc)(NTA_UInt32);
  typedef void (*fp_dealloc)(NTA_Byte *);

  Int32 ReadBuffer::readString(
      NTA_Byte * &value, 
      NTA_UInt32 &size,
      fp_alloc fAlloc,
      fp_dealloc fDealloc
    ) const
  {
    NTA_ASSERT(fDealloc || !fAlloc); // Assume new/delete if unspecified.
    value = 0;
    size = 0;
    Int32 result = findWithLeadingWhitespace(*this, "<s", 16);
    if(result != 0) return result;
    result = findWithLeadingWhitespace(*this, "n", 16);
    if(result != 0) return result;
    result = findWithLeadingWhitespace(*this, "=", 16);
    if(result != 0) return result;
    result = read(size);
    if(result != 0) return result;
    result = findWithLeadingWhitespace(*this, '>', 16);
    if(result != 0) return result;
    if(size) {
      char *allocated = 0;
      if(fAlloc) allocated = fAlloc(size);
      else allocated = new char[size];
      try {
        result = readT(allocated, size);
        value = allocated;
      }
      catch(...) {
        value = 0;
        size = 0;
        if(fDealloc) fDealloc(allocated);
        else if(fAlloc) { } // Leak (prevented by initial assertion).
        else delete[] allocated;
        throw;
      }
      if(result != 0) return result;
    }
    else {
      value = const_cast<NTA_Byte *>(reinterpret_cast<const NTA_Byte *>(""));
    }
    return findWithLeadingWhitespace(*this, "</s>", 1);
  }

  // ------------------------------------------
  //
  //    R E A D   B U F F E R   I T E R A T O R
  //
  // -----------------------------------------=
  static const NTA_ReadBuffer * staticNext(NTA_ReadBufferIteratorHandle handle)
  {
    NTA_CHECK(handle != NULL);
    
    ReadBufferIterator * rbi = static_cast<ReadBufferIterator *>(reinterpret_cast<IReadBufferIterator *>(handle));
    return static_cast<const ReadBuffer *>(rbi->next());
  }

  static void staticReset(NTA_ReadBufferIteratorHandle handle)
  {
    NTA_CHECK(handle != NULL);
    
    ReadBufferIterator * rbi = static_cast<ReadBufferIterator *>(reinterpret_cast<IReadBufferIterator *>(handle));
    return rbi->reset();
  }

  ReadBufferIterator::ReadBufferIterator(ReadBufferVec & rbv) : 
    readBufferVec_(rbv),
    index_(0)
  {
    // Initialize the NTA_ReadbufferIterator struct
    NTA_ReadBufferIterator::handle = reinterpret_cast<NTA_ReadBufferIteratorHandle>(static_cast<IReadBufferIterator *>(this));
    NTA_ReadBufferIterator::next = staticNext;
    NTA_ReadBufferIterator::reset = staticReset;
  }
  
  const IReadBuffer * ReadBufferIterator::next()
  {
    if (index_ == readBufferVec_.size())
      return NULL;
      
    return readBufferVec_[index_++];
  }

  void ReadBufferIterator::reset()
  {
    index_ = 0;
  }
  // -----------------------------------------
  //
  //    W R I T E   B U F F E R
  //
  // -----------------------------------------
  NTA_Int32 staticWriteUInt32(NTA_WriteBufferHandle handle, NTA_UInt32 value)
  {
    NTA_CHECK(handle != NULL);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value);
  }
  
  NTA_Int32 staticWriteUInt32Array(NTA_WriteBufferHandle handle, const NTA_UInt32 * value, NTA_Size size)
  {
    NTA_CHECK(handle != NULL);
    NTA_CHECK(value != NULL);
    NTA_CHECK(size > 0);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value, size);
  }

  NTA_Int32 staticWriteInt32(NTA_WriteBufferHandle handle, NTA_Int32 value)
  {
    NTA_CHECK(handle != NULL);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value);
  }

  NTA_Int32 staticWriteInt32Array(NTA_WriteBufferHandle handle, const NTA_Int32 * value, NTA_Size size)
  {
    NTA_CHECK(handle != NULL);
    NTA_CHECK(value != NULL);
    NTA_CHECK(size > 0);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value, size);
  }

  NTA_Int32 staticWriteInt64(NTA_WriteBufferHandle handle, NTA_Int64 value)
  {
    NTA_CHECK(handle != NULL);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value);
  }
  
  NTA_Int32 staticWriteInt64Array(NTA_WriteBufferHandle handle, const NTA_Int64 * value, NTA_Size size)
  {
    NTA_CHECK(handle != NULL);
    NTA_CHECK(value != NULL);
    NTA_CHECK(size > 0);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value, size);
  }

  NTA_Int32 staticWriteUInt64(NTA_WriteBufferHandle handle, NTA_UInt64 value)
  {
    NTA_CHECK(handle != NULL);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value);
  }
  
  NTA_Int32 staticWriteUInt64Array(NTA_WriteBufferHandle handle, const NTA_UInt64 * value, NTA_Size size)
  {
    NTA_CHECK(handle != NULL);
    NTA_CHECK(value != NULL);
    NTA_CHECK(size > 0);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value, size);
  }

  NTA_Int32 staticWriteReal32(NTA_WriteBufferHandle handle, NTA_Real32 value)
  {
    NTA_CHECK(handle != NULL);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value);
  }
  
  NTA_Int32 staticWriteReal32Array(NTA_WriteBufferHandle handle, const NTA_Real32 * value, NTA_Size size)
  {
    NTA_CHECK(handle != NULL);
    NTA_CHECK(value != NULL);
    NTA_CHECK(size > 0);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value, size);
  }

  NTA_Int32 staticWriteReal64(NTA_WriteBufferHandle handle, NTA_Real64 value)
  {
    NTA_CHECK(handle != NULL);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value);
  }

  NTA_Int32 staticWriteReal64Array(NTA_WriteBufferHandle handle, const NTA_Real64 * value, NTA_Size size)
  {
    NTA_CHECK(handle != NULL);
    NTA_CHECK(value != NULL);
    NTA_CHECK(size > 0);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value, size);
  }

  NTA_Int32 staticWriteByte(NTA_WriteBufferHandle handle, NTA_Byte value)
  {
    NTA_CHECK(handle != NULL);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value);
  }

  NTA_Int32 staticWriteByteArray(NTA_WriteBufferHandle handle, const NTA_Byte * value, NTA_Size size)
  {
    NTA_CHECK(handle != NULL);
    NTA_CHECK(value != NULL);
    NTA_CHECK(size > 0);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->write(value, size);
  }

  NTA_Int32 staticWriteString(NTA_WriteBufferHandle handle, const NTA_Byte * value, NTA_Size size)
  {
    NTA_CHECK(handle != NULL);
    NTA_CHECK(value != NULL);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->writeString(value, size);
  }

  const Byte * staticGetData(NTA_WriteBufferHandle handle)
  {
    NTA_CHECK(handle != NULL);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->getData();
  }
  
  NTA_Size staticWriteBufferGetSize(NTA_WriteBufferHandle handle)
  {
    NTA_CHECK(handle != NULL);
    
    WriteBuffer * wb = reinterpret_cast<WriteBuffer *>(handle);
    return wb->getSize();
  }

  WriteBuffer::WriteBuffer()
  {
    handle = reinterpret_cast<NTA_WriteBufferHandle>(this);
    NTA_WriteBuffer::getData = staticGetData;
    NTA_WriteBuffer::getSize = staticWriteBufferGetSize;
    
    writeByte = staticWriteByte;
    writeByteArray = staticWriteByteArray;
    writeAsString = staticWriteString;

    writeInt32 = staticWriteInt32;  
    writeInt32Array = staticWriteInt32Array;
    writeUInt32 = staticWriteUInt32;
    writeUInt32Array = staticWriteUInt32Array;

    writeInt64 = staticWriteInt64;
    writeInt64Array = staticWriteInt64Array;        
    writeUInt64 = staticWriteUInt64;
    writeUInt64Array = staticWriteUInt64Array;
    
    writeReal32 = staticWriteReal32;
    writeReal32Array = staticWriteReal32Array;
    writeReal64 = staticWriteReal64;
    writeReal64Array = staticWriteReal64Array;
    
    OMemStream::exceptions(std::ostream::failbit | std::ostream::badbit);
  }

  Int32 WriteBuffer::write(Byte value)
  {
    return writeT(value);
  }
  
  Int32 WriteBuffer::write(const Byte * bytes, Size size)
  {
    try
    {
      OMemStream::write(bytes, (std::streamsize)size);
      return 0;
    }
    catch (...)
    {
      return -1;
    }
  }

  Int32 WriteBuffer::write(Int32 value)
  {
    return writeT(value);
  }

  Int32 WriteBuffer::write(const Int32 * value, Size size)
  {
    return writeT(value, size);
  }

  Int32 WriteBuffer::write(UInt32 value)
  {
    return writeT(value);
  }

  Int32 WriteBuffer::write(const UInt32 * value, Size size)
  {
    return writeT(value, size);
  }
  
  Int32 WriteBuffer::write(Int64 value)
  {
    return writeT(value);
  }

  Int32 WriteBuffer::write(const Int64 * value, Size size)
  {
    return writeT(value, size);
  }
  
  Int32 WriteBuffer::write(UInt64 value)
  {
    return writeT(value);
  }
  
  Int32 WriteBuffer::write(const UInt64 * value, Size size)
  {
    return writeT(value, size);
  }
  
  Int32 WriteBuffer::write(Real32 value)
  {
    return writeT(value);
  }

  Int32 WriteBuffer::write(const Real32 * value, Size size)
  {
    return writeT(value, size);
  }
  
  Int32 WriteBuffer::write(Real64 value)
  {
    return writeT(value);
  }

  Int32 WriteBuffer::write(const Real64 * value, Size size)
  {
    return writeT(value, size);
  }

  NTA_Int32 WriteBuffer::writeString(const NTA_Byte *value, NTA_Size size)
  {
    NTA_Int32 result = write("<s n=", 5);
    if(result != 0) return result;
    result = writeT(size, 0);
    if(result != 0) return result;
    result = writeT('>', 0);
    if(result != 0) return result;
    if(size) {
      result = write(value, size);
      if(result != 0) return result;
    }
    result = write("</s>", 4);
    return result;
  }
  
  const Byte * WriteBuffer::getData()
  {
    try
    {
      return OMemStream::str();
    }
    catch (...)
    {
      return NULL;
    }
  }

  Size WriteBuffer::getSize()
  { 
    return (Size)OMemStream::pcount();
  }
}

