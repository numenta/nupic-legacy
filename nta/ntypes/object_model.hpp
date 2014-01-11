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
 * Interfaces for C++ runtime objects used by INode
 */

/*
 * TEMPORARY for NUPIC 2 development
 * Included because IWriteBuffer/IReadBuffer
 */


#ifndef NTA_OBJECT_MODEL_HPP
#define NTA_OBJECT_MODEL_HPP

#include <nta/types/types.hpp>
#include <nta/ntypes/object_model.h>
#include <string>
#include <stdexcept>

namespace nta 
{
  //--------------------------------------------------------------------------- 
  //
  //   I   R E A D   B U F F E R
  //
  //---------------------------------------------------------------------------   
  /**
  * @b Responsibility:
  *  Interface for reading values from a binary buffer
  */  
  //---------------------------------------------------------------------------
  struct IReadBuffer
  {
    /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~IReadBuffer() {}

    /**
    * Reset the internal pointer to point to the beginning of the buffer.
    *
    * This is necessary if you want to read from the same buffer multiple
    * times.
    */
    virtual void reset() const = 0;

    /**
    * Returns the size in bytes of the buffer's contents
    *
    * This is useful if you want to copy the entire buffer
    * as a byte array.
    *
    * @retval        number of bytes in the buffer
    */
    virtual Size getSize() const = 0;

    /**
    * Returns a pointer to the buffer's contents
    *
    * This is useful if you want to access the bytes directly.
    * The returned buffer is not related in any way to the 
    * internal advancing pointer used in the read() methods.
    *
    * @retval        pointer to beginning of the buffer
    */
    virtual const Byte * getData() const = 0;
    
    /**
    * Read a single byte into 'value' and advance the internal pointer.
    *
    * @param value   the output byte.
    * @retval        0 for success, -1 for failure, 1 for EOF
    */
    virtual Int32 read(Byte & value) const = 0;
    
    /**
    * Read 'size' bytes into the 'value'  array and advance
    * the internal pointer.
    * If the buffer contains less than 'size' bytes it will read 
    * as much as possible and write the number of bytes actually read
    * into the 'size' argument.
    *
    * @param value   the output buffer. Must not be NULL
    * @param size    the size of the output buffer. Must be >0. Receives
    *                the actual number of bytes read if success or 0
    * @retval        0 for success, -1 for failure, 1 for EOF
    */
    virtual Int32 read(Byte * value, Size & size) const = 0;

    /**
     * Read a string into the string object provided in 'value'.
     * The string object should be empty before begin passed in, 
     * or the result will be undefined.
     * The string must have been written to the buffer using the 
     * IWriteBuffer::write(const std::string &) interface.
     * The value of the string upon completion will be undefined on failure.
     * Note that reading and writing a string is slightly different from 
     * reading or writing an arbitrary binary structure in the 
     * the following ways:
     *  * Reading/writing a 0-length string is a sensible operation.
     *  * The length of the string is almost never known ahead of time.
     *
     * @retval value   A reference to a character array pointer (initially null).
     *                 This array will point to a new buffer allocated with the 
     *                 provided allocator upon success.
     *                 The caller is responsible for this memory.
     * @retval size    A reference to a size that will be filled in with the 
     *                 string length.
     * @param fAlloc   A function pointer that will be called to
     *                 perform necessary allocation of value buffer.
     * @param fDealloc A function pointer that will be called if a failure 
     *                 occurs after the value array has been allocated to 
     *                 cleanup allocated memory.
     * @return         0 for success, -1 for failure
     */
    virtual NTA_Int32 readString(
        NTA_Byte * &value, 
        NTA_UInt32 &size,
        NTA_Byte *(fAlloc)(NTA_UInt32 size),
        void (fDealloc)(NTA_Byte *)
      ) const = 0;

    /**
    * Read a single integer (32 bits) into 'value' 
    * and advance the internal pointer.
    *
    * @param value   the output integer.
    * @retval        0 for success, -1 for failure, 1 for EOF
    */
    virtual Int32 read(Int32 & value) const = 0;
    
   /**
    * Read 'size' Int32 elements into the 'value' array and advance 
    * the internal pointer.
    * If the buffer contains less than 'size' bytes it will read 
    * as much as possible and write the number of elements actually read
    * into the 'size' argument.
    *
    * @param value   the output buffer. Must not be NULL
    * @param size    the size of the output buffer. Must be >0.
    * @retval        0 for success, -1 for failure, 1 for EOF
    */
    virtual Int32 read(Int32 * value, Size size) const = 0;

    /**
    * Read a single unsigned integer (32 bits) into 'value' 
    * and advance the internal pointer.
    *
    * @param value   the output unsigned integer.
    * @retval        0 for success, -1 for failure, 1 for EOF
    */
    virtual Int32 read(UInt32 & value) const = 0;

   /**
    * Read 'size' UInt32 elements into the 'value' array and advance 
    * the internal pointer.
    * If the buffer contains less than 'size' bytes it will read 
    * as much as possible and write the number of elements actually read
    * into the 'size' argument.
    *
    * @param value   the output buffer. Must not be NULL
    * @param size    the size of the output buffer. Must be >0. Receives
    *                the actual number of elements read if success or 0
    * @retval        0 for success, -1 for failure, 1 for EOF
    */    
    virtual Int32 read(UInt32 * value, Size size) const = 0;
    
    /**
    * Read a single integer (64 bits) into 'value' 
    * and advance the internal pointer.
    *
    * @param value   the output integer.
    * @retval        0 for success, -1 for failure, 1 for EOF
    */
    virtual Int32 read(Int64 & value) const = 0;

   /**
    * Read 'size' Int64 elements into the 'value' array and advance 
    * the internal pointer.
    * If the buffer contains less than 'size' bytes it will read 
    * as much as possible and write the number of elements actually read
    * into the 'size' argument.
    *
    * @param value   the output buffer. Must not be NULL
    * @param size    the size of the output buffer. Must be >0. Receives
    *                the actual number of elements read if success or 0
    * @retval        0 for success, -1 for failure, 1 for EOF
    */    
    virtual Int32 read(Int64 * value, Size size) const = 0;
    
    /**
    * Read a single unsigned integer (64 bits) into 'value' 
    * and advance the internal pointer.
    *
    * @param value   the output unsigned integer.
    * @retval        0 for success, -1 for failure, 1 for EOF
    */
    virtual Int32 read(UInt64 & value) const = 0;
    
   /**
    * Read 'size' UInt64 elements into the 'value' array and advance 
    * the internal pointer.
    * If the buffer contains less than 'size' bytes it will read 
    * as much as possible and write the number of elements actually read
    * into the 'size' argument.
    *
    * @param value   the output buffer. Must not be NULL
    * @param size    the size of the output buffer. Must be >0. Receives
    *                the actual number of elements read if success or 0
    * @retval        0 for success, -1 for failure, 1 for EOF
    */    
    virtual Int32 read(UInt64 * value, Size size) const = 0;
    

    /**
    * Read a single 32-bit real number (float)
    * into 'value' and advance the internal pointer.
    *
    * @param value   the output real number.
    * @retval        0 for success, -1 for failure, 1 for EOF
    */
    virtual Int32 read(Real32 & value) const = 0;

   /**
    * Read 'size' Real32 elements into the 'value' array and advance 
    * the internal pointer.
    * If the buffer contains less than 'size' bytes it will read 
    * as much as possible and write the number of elements actually read
    * into the 'size' argument.
    *
    * @param value   the output buffer. Must not be NULL
    * @param size    the size of the output buffer. Must be >0. Receives
    *                the actual number of elements read if success or 0
    * @retval        0 for success, -1 for failure, 1 for EOF
    */    
    virtual Int32 read(Real32 * value, Size size) const = 0;
    
    /**
    * Read a single 64-bit real number (double)
    * into 'value' and advance the internal pointer.
    *
    * @param value   the output real number.
    * @retval        0 for success, -1 for failure, 1 for EOF
    */
    virtual Int32 read(Real64 & value) const = 0;
    
   /**
    * Read 'size' Real64 elements into the 'value' array and advance 
    * the internal pointer.
    * If the buffer contains less than 'size' bytes it will read 
    * as much as possible and write the number of elements actually read
    * into the 'size' argument.
    *
    * @param value   the output buffer. Must not be NULL
    * @param size    the size of the output buffer. Must be >0. Receives
    *                the actual number of elements read if success or 0
    * @retval        0 for success, -1 for failure, 1 for EOF
    */    
    virtual Int32 read(Real64 * value, Size size) const = 0;
    
  };

  //--------------------------------------------------------------------------- 
  //
  //   I   R E A D   B U F F E R   I T E R A T O R
  //
  //---------------------------------------------------------------------------
  /**
  * @b Responsibility:
  * Interface for iterating over a collection of IReadBuffer objects
  */  
  //---------------------------------------------------------------------------
  struct IReadBufferIterator
  {
    /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~IReadBufferIterator() {}
    
    /**
    * Reset the internal pointer to point to the beginning of the iterator.
    *
    * The following next() will return the first IReadBuffer in the collection
    * or NULL if the collection is empty. Multiple consecutive calls are allowed
    * but have no effect. 
    */
    virtual void reset() = 0;

    /**
    * Get the next buffer in the collection
    *
    * This method returns the buffer pointed to by the internal pointer and advances
    * the pointer to the next buffer in the collection. If the collection is empty
    * or previous call to next() returned the last buffer, further calls to next()
    * will return NULL.
    *
    * @retval [IReadBuffer *] next buffer or NULL
    */    
    virtual const IReadBuffer * next() = 0;
  };


  //--------------------------------------------------------------------------- 
  //
  //   I   W R I T E   B U F F E R
  //
  //---------------------------------------------------------------------------
  /**
  * @b Responsibility:
  * Interface for writing values to a binary buffer
  */  
  //---------------------------------------------------------------------------
  struct IWriteBuffer 
  {  
    /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~IWriteBuffer() {}
    
   /**
    * Write a single byte into
    * the internal buffer.
    *
    * @param value   the input byte.
    * @retval        0 for success, -1 for failure
    */
    virtual Int32 write(Byte value) = 0;
   
   /**
    * Write a byte array into
    * the internal buffer. 
    *
    * @param value   the input array.
    * @param size    how many bytes to write
    * @retval        0 for success, -1 for failure
    */    
    virtual Int32 write(const Byte * value, Size size) = 0;
     
    /**
     * Write the contents of a string into the stream.
     * The string may be of 0 length and may contain any 8-bit characters
     * (the string must be 1-byte encoded).
     * Note that reading and writing a string is slightly different from 
     * reading or writing an arbitrary binary structure in the 
     * the following ways:
     *  * Reading/writing a 0-length string is a sensible operation.
     *
     * @param value  the input array.
     * @retval       0 for success, -1 for failure
     */
    virtual Int32 writeString(const Byte * value, Size size) = 0;

   /**
    * Write a single integer (32 bits) into
    * the internal buffer.
    *
    * @param value   the input integer.
    * @retval        0 for success, -1 for failure
    */
    virtual Int32 write(Int32 value) = 0; 
    
   /**
    * Write array of Int32 elements into
    * the internal buffer. 
    *
    * @param value   the input array.
    * @param size    how many bytes to write
    * @retval        0 for success, -1 for failure
    */    
    virtual Int32 write(const Int32 * value, Size size) = 0;

   /**
    * Write a single unsigned integer (32 bits) into
    * the internal buffer.
    *
    * @param value    the input unsigned integer.
    * @retval        0 for success, -1 for failure
    */
    virtual Int32 write(UInt32 value) = 0; 

   /**
    * Write array of UInt32 elements into
    * the internal buffer. 
    *
    * @param value   the input array.
    * @param size    how many bytes to write
    * @retval        0 for success, -1 for failure
    */    
    virtual Int32 write(const UInt32 * value, Size size) = 0;
    
   /**
    * Write a single integer (64 bits) into
    * the internal buffer.
    *
    * @param value   the input integer.
    * @retval        0 for success, -1 for failure
    */    
    virtual Int32 write(Int64 value) = 0;

   /**
    * Write array of Int64 elements into
    * the internal buffer. 
    *
    * @param value   the input array.
    * @param size    how many bytes to write
    * @retval        0 for success, -1 for failure
    */    
    virtual Int32 write(const Int64 * value, Size size) = 0;
        
   /**
    * Write a single unsigned integer (64 bits) into
    * the internal buffer.
    *
    * @param value   the input unsigned integer.
    * @retval        0 for success, -1 for failure
    */
    virtual Int32 write(UInt64 value) = 0; 

   /**
    * Write array of UInt64 elements into
    * the internal buffer. 
    *
    * @param value   the input array.
    * @param size    how many bytes to write
    * @retval        0 for success, -1 for failure
    */    
    virtual Int32 write(const UInt64 * value, Size size) = 0;
        
   /**
    * Write a single precision real (32 bits) into
    * the internal buffer.
    *
    * @param value   the input real number.
    * @retval        0 for success, -1 for failure
    */
    virtual Int32 write(Real32 value) = 0;  

   /**
    * Write array of Real32 elements into
    * the internal buffer. 
    *
    * @param value   the input array.
    * @param size    how many bytes to write
    * @retval        0 for success, -1 for failure
    */    
    virtual Int32 write(const Real32 * value, Size size) = 0;
    
   /**
    * Write a double precision real (64 bits) into
    * the internal buffer.
    *
    * @param value   the input real number.
    * @retval        0 for success, -1 for failure
    */    
    virtual Int32 write(Real64 value) = 0;  

   /**
    * Write array of Real64 elements into
    * the internal buffer. 
    *
    * @param value   the input array.
    * @param size    how many bytes to write
    * @retval        0 for success, -1 for failure
    */    
    virtual Int32 write(const Real64 * value, Size size) = 0;
        
   /**
    * Get the size in bytes of the contents of the internal 
    * buffer.
    *
    * @retval [Size] size in bytes of the buffer contents
    */        
    virtual Size getSize() = 0;
    
   /**
    * A pointer to the internal buffer.
    *
    * The buffer is guarantueed to be contiguous.
    *
    * @retval [Byte *] internal buffer
    */            
    virtual const Byte * getData() = 0;
  };


  //--------------------------------------------------------------------------- 
  //
  //   I   R A N G E
  //
  //---------------------------------------------------------------------------
  /**
   * 
   * @b Responsibility
   *  A base interface that defines the common operations for input 
   *  and output ranges. Exposes the numer of elements (elementCount)
   *  and the size of each element in bytes (elementSize).
   *
   * @b Rationale 
   *  Plain old reuse. both IInputRange and IOutputRange are derived
   *  from IRange.
   * 
   */
  //---------------------------------------------------------------------------
  struct IRange
  {
   /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~IRange() {}
    
   /**
    * Get the number of elements in a range
    *
    * @retval [Size] number of elements
    */ 
    virtual Size getElementCount() const = 0;
    
   /**
    * Get the size of a single element in a range
    *
    * All elements in a range have the same size
    * 
    * @retval [Size] size in bytes of a range element.
    */ 
    virtual Size getElementSize() const = 0;
  };

  //--------------------------------------------------------------------------- 
  //
  //   I   I N P U T   R A N G E
  //
  //---------------------------------------------------------------------------
  /**
   * 
   * @b Responsibility
   *  The input range interface. Provides access to a couple of iterator-like
   *  pointers to the beginning and end of the raange. The lag argument
   *  controls the offset (from which buffer to extract the pointers). 
   * @b Note
   *  begin() and end() return a const Byte *. It is the responsibility of the
   *  caller to cast it to te correct type. The memory is not suppposed to
   *  be modified only read.  
   */
  //---------------------------------------------------------------------------
  struct IInputRange : public IRange
  {
   /**
    * Get the beginning pointer to the range's byte array
    * 
    * @retval [Byte *] pointer to internal byte array.
    */ 
    virtual const Byte * begin() const = 0;

   /**
    * Get the end pointer to the range's byte array
    * 
    * The end pointer is pointing to the byte immediately 
    * following the last byte in the internal byte array
    *
    * @retval [Byte *] the end pointer of the internal byte array.
    */ 
    virtual const Byte * end() const = 0;
  };

  //--------------------------------------------------------------------------- 
  //
  //   I   O U T P U T   R A N G E
  //
  //---------------------------------------------------------------------------
  /** 
   * @b Responsibility
   *  The output range interface. Provides access to a couple of iterator-like
   *  pointers to the beginning and end of the raange. 
   *
   * @b Note
   *  begin() and end() return a Byte *. It is the responsibility of the
   *  caller to cast it to te correct type. The memory can be written to of course.  
   */
  //---------------------------------------------------------------------------
  struct IOutputRange : public IRange
  {
   /**
    * Get the beginning pointer to the range's byte array
    * 
    * @retval [Byte *] pointer to internal byte array.
    */ 
    virtual Byte * begin() = 0;
    
   /**
    * Get the end pointer to the range's byte array
    * 
    * The end pointer is pointing to the byte immediately 
    * following the last byte in the internal byte array
    *
    * @retval [Byte *] the end pointer of the internal byte array.
    */ 
    virtual Byte * end() = 0;
  };
	
  
  //--------------------------------------------------------------------------- 
  //
  //   I   I N P U T   R A N G E   M A P   E N T R Y
  //
  //---------------------------------------------------------------------------
  /**
   * @b Responsibility
   *  The input range map entry interface. Each entry has a name and an input
   *  range iterator. That means that a whole collection on input ranges are
   *  accessible via the same name.
   */
  //---------------------------------------------------------------------------
  struct IInputRangeMapEntry
  {
   /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~IInputRangeMapEntry() {}
    
   /**
    * Reset the internal pointer to point to the beginning of the input range iterator.
    *
    * The following next() will return the first IReadBuffer in the collection
    * or NULL if the collection is empty. Multiple consecutive calls are allowed
    * but have no effect. 
    */    
    virtual void reset() const = 0;
   
   /**
    * Get the next input range in the map entry
    *
    * This method returns the input range pointed to by the internal pointer and advances
    * the pointer to the next input range in the map entry. If the collection is empty
    * or previous call to next() returned the last input range, further calls to next()
    * will return NULL.
    *
    * @retval [const IInputRange *] next input range or NULL
    */    
    virtual const IInputRange * next() const = 0;

   /**
    * The name of the input range
    */    
    const Byte * name;
  };


  //--------------------------------------------------------------------------- 
  //
  //   I   I N P U T   R A N G E   M A P
  //
  //---------------------------------------------------------------------------
  /**
   * @b Responsibility
   *  The input range map interface. Stores a collection of IInputMapRangeEntry
   *  objects. It provides lookup by name as well an iterator
   *  to iterate over all the entries. 
   */
  //---------------------------------------------------------------------------
  struct IInputRangeMap
  { 
   /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~IInputRangeMap() {}
    
   /**
    * Reset the internal pointer to point to the first InputRangeMap entry.
    *
    * The following next() will return the first entry in the map or NULL
    * if the collection is empty. Multiple consecutive calls are allowed
    * but have no effect. 
    */    
    virtual void reset() const = 0; 
    
   /**
    * Get the next InputRangeMap entry
    *
    * This method returns the InputRangeMap entry pointed to by the internal pointer 
    * and advances the pointer to the next entry. If the collection is empty
    * or previous call to next() returned the last entry, further calls to next()
    * will return NULL.
    *
    * @retval [const IInputRangeMapEntry *] next map entry or NULL
    */    
    virtual const IInputRangeMapEntry * next() const = 0;
    
   /**
    * Get an InputRangeMap entry by name
    *
    * This method returns the InputRangeMap entry whose name matches the input name
    * or NULL if an entry with this name is not in the map. lookup() calls
    * don't affect the internal iterator pointer.
    *
    * @param [const Byte *] entry name to lookup.
    * @retval [const IInputRangeMapEntry *] map entry or NULL
    */
    virtual const IInputRangeMapEntry * lookup(const Byte * name) const = 0;
  };

  //--------------------------------------------------------------------------- 
  //
  //   I   O U T P U T   R A N G E   M A P   E N T R Y
  //
  //---------------------------------------------------------------------------
  /**
   * @b Responsibility
   *  The output range map entry is just a named output range
   */
  //---------------------------------------------------------------------------
  struct IOutputRangeMapEntry
  {
   /**
    * The name of the output range
    */    
    const Byte * name;
    
  /**
    * The output range
    */    
    IOutputRange * range;
  };


  //--------------------------------------------------------------------------- 
  //
  //   I   O U T P U T   R A N G E   M A P
  //
  //---------------------------------------------------------------------------
  /**
   * @b Responsibility
   *  The output range map interface. Stores pairs of output [name, range].
   *  It provides lookup by name as well as iterator-like
   *  methods (begin(), end()) to iterate over all entries 
   */
  //---------------------------------------------------------------------------
  struct IOutputRangeMap
  { 
   /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~IOutputRangeMap() {}
    
   /**
    * Reset the internal pointer to point to the first OutputRangeMap entry.
    *
    * The following next() will return the first entry in the map or NULL
    * if the collection is empty. Multiple consecutive calls are allowed
    * but have no effect. 
    */    
    virtual void reset() = 0;

   /**
    * Get the next OutputRangeMap entry
    *
    * This method returns the OutputRangeMap entry pointed to by the internal pointer 
    * and advances the pointer to the next entry. If the collection is empty
    * or previous call to next() returned the last entry, further calls to next()
    * will return NULL.
    *
    * @retval [const IOutputRangeMapEntry *] next map entry or NULL
    */     
    virtual IOutputRangeMapEntry * next() = 0;
    
   /**
    * Get an OutputRangeMap entry by name
    *
    * This method returns the OutputRangeMap entry whose name matches the 
    * requested name or NULL if an entry with this name is not in the map. 
    * lookup() calls don't affect the internal iterator pointer.
    *
    * @param [const Byte *] entry name to lookup.
    * @retval [const IOutputRangeMapEntry *] map entry or NULL
    */
    virtual IOutputRange * lookup(const Byte * name) = 0;
  };

  //--------------------------------------------------------------------------- 
  //
  //   I I N P U T
  //
  //---------------------------------------------------------------------------
  /**
   * @b Responsibility
   *  The flattened input accessor. Provides easy access to the flattened input
   *  of a node or a specific baby node within a multi-node.  
   */
  //---------------------------------------------------------------------------
  struct IInput
  { 
    enum {allNodes = -1};
    
   /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~IInput() {}
    
   /**
    * Get the beginning pointer to the input's byte array
    * 
    * @param  nodeIdx [Int32] baby node index, or allNodes for entire input
    * @param  sentinelP [Byte*] pointer to default value to insert for elements of
    *                           the node input that are outside the actual input bounds. 
    * @retval [Byte *] pointer to internal byte array.
    */ 
    virtual const Byte * begin(Int32 nodeIdx=allNodes, const Byte* sentinelP=0) = 0;

   /**
    * Get the end pointer to the input's byte array
    * 
    * The end pointer is pointing to the byte immediately 
    * following the last byte in the internal byte array
    *
    * @param  nodeIdx [Int32] baby node index, or allNodes for entire input
    * @retval [Byte *] the end pointer of the internal byte array.
    */ 
    virtual const Byte * end(Int32 nodeIdx=allNodes) = 0;

   /**
    * Get the number of elements in an input
    *
    * @param  nodeIdx [Int32] baby node index, or allNodes for entire input
    * @retval [Size] number of elements
    */ 
    virtual Size getElementCount(Int32 nodeIdx=allNodes) = 0;
    
   /**
    * Get the size of a single element in an input
    *
    * All elements in a range have the same size
    * 
    * @retval [Size] size in bytes of a range element.
    */ 
    virtual Size getElementSize() = 0;
    
   /**
    * Get the number of links into a specific node
    *
    * @param  nodeIdx [Int32] baby node index, or allNodes for entire input
    * @retval [Size] number of links
    */ 
    virtual Size getLinkCount(Int32 nodeIdx=allNodes) = 0;
    
   /**
    * Get pointer to the link boundaries
    *
    * @param  nodeIdx [Int32] baby node index, or allNodes for entire input
    * @retval [Size] pointer to array of link boundaries
    */ 
    virtual Size * getLinkBoundaries(Int32 nodeIdx=allNodes) = 0;
    
  };


  //--------------------------------------------------------------------------- 
  //
  //   I O U T P U T
  //
  //---------------------------------------------------------------------------
  /**
   * @b Responsibility
   *  The easy output accessor. Provides easy access to the output
   *  of a node or a specific baby node within a multi-node.  
   */
  //---------------------------------------------------------------------------
  struct IOutput
  { 
    enum {allNodes = -1};
    
   /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~IOutput() {}
    
   /**
    * Get the beginning pointer to the input's byte array
    * 
    * @param  nodeIdx [Int32] baby node index, or allNodes for entire input
    * @retval [Byte *] pointer to internal byte array.
    */ 
    virtual Byte * begin(Int32 nodeIdx=allNodes)  = 0;

   /**
    * Get the end pointer to the input's byte array
    * 
    * The end pointer is pointing to the byte immediately 
    * following the last byte in the internal byte array
    *
    * @param  nodeIdx [Int32] baby node index, or allNodes for entire input
    * @retval [Byte *] the end pointer of the internal byte array.
    */ 
    virtual Byte * end(Int32 nodeIdx=allNodes)  = 0;

   /**
    * Get the number of elements in a range
    *
    * @param  nodeIdx [Int32] baby node index, or allNodes for entire input
    * @retval [Size] number of elements
    */ 
    virtual Size getElementCount(Int32 nodeIdx=allNodes)  = 0;
    
   /**
    * Get the size of a single element in a range
    *
    * All elements in a range have the same size
    * 
    * @retval [Size] size in bytes of a range element.
    */ 
    virtual Size getElementSize()  = 0;
    
  };

  //---------------------------------------------------------------------------
  /**
   * @b Responsibility
   *  Aggregate all the information a node needs for initialization. It includes
   *  id, name, logLevel, inputs, outputs and state. This struct is passed to
   *  INode::init() during the initialization of nodes. Note that multi-nodes 
   *  (nodes that represent multiple "baby" nodes require additional information
   *  that is provided by the IMultiNodeInfo interface (see bellow).
   */
  //---------------------------------------------------------------------------
  struct INodeInfo
  {
   /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~INodeInfo() {}
        
   /**
    * Return the type of the node
    *
    * A node is created dynamically by the runtime engine based on
    * its type (used when registering a node type with the plugin manager).
    * Making this type available to the node via INodeInfo
    * saves the node from storing its type internally. It also ensures
    * that there will not be a conflict between the registered type of
    * a node and what the node thinks its type is. 
    *
    * @retval [const Byte *] node type
    */    
    virtual const Byte * getType() = 0;
 
   /**
    * Return the current log level of the node
    *
    * The node should take into account the log level every time
    * it is about to log something. The log level can be modified
    * externally by the user. The node should exercise judgment
    * and call INodeInfo->getLogLevel() frequently 
    * (before every log statement or at the beginning of each compute())
    *
    * @retval [const Byte *] node type
    */ 
    virtual LogLevel getLogLevel() = 0;
    
   /**
    * Return an object used to access the flattened input of a node. 
    *
    * This method can be used to get easy access to a flattened version of any node input.
    * It is much easier to use than the more primitive getInputs() call which can potentially
    * return multiple input ranges that comprise the input. 
    *
    * In addition, the IInput object allows you to easily get a pointer to the portion of
    * the flattened input that corresponds to any particular baby node. 
    *
    * @retval [IInput *] flattened node input object
    */ 
    virtual IInput * getInput(const NTA_Byte* varName) = 0;

   /**
    * Return an object used to access the output of a node. 
    *
    * This method can be used to get easy access to any node output.
    * It is much easier to use than the more primitive getOutputs() call for multi-nodes
    * since it allows you to easily get a pointer to the portion of the output that 
    * corresponds to any particular baby node. 
    *
    * @retval [IOutput *] node output object
    */ 
    virtual IOutput * getOutput(const NTA_Byte* varName) = 0;


   /**
    * Return the inputs of the node
    *
    * The inputs are garantueed to be persistent over the lifetime
    * of the node. That means that the node may call getInputs()
    * multiple times and will always get the same answer.
    * The contents of the inputs may change of course between
    * calls to compute(), but the number of inputs, names and all
    * other structural properties (including the memory area)
    * are all fixed. 
    *
    * @retval [IInputRangeMap &] node inputs
    */ 
    virtual IInputRangeMap & getInputs() = 0;

   /**
    * Return the outputs of the node
    *
    * The outputs are garantueed to be persistent over the lifetime
    * of the node. That means that the node may call getOutputs()
    * multiple times and will always get the same answer.
    * The contents of the outputs may change of course as the node
    * modifies them in compute(), but the number of outputs, names
    * and all other structural properties (including the memory area)
    * are all fixed. 
    *
    * @retval [IOutputRangeMap &] node outputs
    */     
    virtual IOutputRangeMap & getOutputs() = 0;
 
   /**
    * Return the serialized state of the node
    *
    * The state is used to initialize a node on the runtime side
    * to an initial state. The initial state is created on the tools
    * side and stored in serialized form in the network file.
    *
    * @retval [IReadBuffer &] initial node state
    */      
    virtual IReadBuffer & getState() = 0;
    
   /**
    * Return the number of baby nodes in a multi-node. 
    *
    * This method is only used for multi-nodes. 
    * It returns the number of baby nodes for this multi-node. 
    *
    * @retval [NTA_Size] number of baby nodes in this multi-node. 
    */      
    virtual NTA_Size getMNNodeCount() = 0;
    
   /**
    * Return the Multi-node input list for a given input variable in a multi-node
    *
    * This method is only used for multi-nodes. 
    * It returns a pointer to an array of NTA_IndexRangeLists's, one per baby node. Each
    * NTA_IndexRangeList contains a count and an array of NTA_IndexRange's. 
    * Each NTA_IndexRange has an offset and size, specifying the offset within the
    * input variable 'varName', and the number of elements. 
    *
    * @retval [NTA_IndexRangeList *] array of NTA_IndexRangeLists, one for each baby node
    */      
    virtual const NTA_IndexRangeList * getMNInputLists(const NTA_Byte* varName) = 0;
    
   /**
    * Return the Multi-node output sizes for a given output variable of a multi-node
    *
    * This method is only used for multi-nodes. 
    * It returns a pointer to an array of sizes, one per baby node of the multi-node. 
    *
    * @retval [IReadBuffer &] serialized SparseMatrix01
    */      
    virtual const NTA_Size * getMNOutputSizes(const NTA_Byte* varName) = 0;
  };


  //--------------------------------------------------------------------------- 
  //
  //   I   I N P U T  S I Z E   M A P
  //
  //--------------------------------------------------------------------------- 
  /**
   * This interface provides access to the input sizes of a node.
   * It contains entries and provides iterator-like accessor
   * as well as lookup by name accessor.
   */
  //---------------------------------------------------------------------------
  struct IInputSizeMap
  {
    virtual ~IInputSizeMap() {}
    virtual void reset()= 0;
    virtual const NTA_InputSizeMapEntry * next() = 0;
    virtual const NTA_InputSizeMapEntry * lookup(const Byte * name) = 0;
  };


  //--------------------------------------------------------------------------- 
  //
  //   I   O U T P U T  S I Z E   M A P
  //
  //--------------------------------------------------------------------------- 
  /**
   * This interface provides access to the output sizes of a node.
   * It contains entries and provides iterator-like accessor
   * as well as lookup by name accessor.
   */
  //---------------------------------------------------------------------------
  struct IOutputSizeMap
  {
    virtual ~IOutputSizeMap() {}
    virtual void reset()= 0;
    virtual const NTA_OutputSizeMapEntry * next() = 0;
    virtual const NTA_OutputSizeMapEntry * lookup(const Byte * name) = 0;
  };


  //--------------------------------------------------------------------------- 
  //
  //   I   P A R A M E T E R   M A P   E N T R Y
  //
  //---------------------------------------------------------------------------
  /**
   * @b Responsibility
   *  The parameter map entry interface. Each entry has a name and read buffer
   *  that contains the value of the parameter.
   */
  //---------------------------------------------------------------------------
    struct IParameterMapEntry
    {
     /**
      * The parameter name
      */    
      const Byte * name;
    
     /**
      * The parameter value
      */    
      const IReadBuffer * value;
    };

  //--------------------------------------------------------------------------- 
  //
  //   I   P A R A M E T E R   M A P
  //
  //---------------------------------------------------------------------------
  /**
   * @b Responsibility
   *  The parameter map interface. Stores pairs of [name, parameter]
   *  It provides lookup by name as well as iterator-like
   * methods (begin(), end()) to iterate over all entries 
   */
  //---------------------------------------------------------------------------
  struct IParameterMap
  {    
   /**
    * Virtual destructor. Required for abstract classes.
    */
    virtual ~IParameterMap() {}
    
   /**
    * Reset the internal pointer to point to the first parameter entry.
    *
    * The following next() will return the first entry in the map or NULL
    * if the map is empty. Multiple consecutive calls are allowed
    * but have no effect. 
    */    
    virtual void reset() const = 0;

   /**
    * Get the next parameter entry
    *
    * This method returns the parameter entry pointed to by the internal pointer 
    * and advances the pointer to the next entry. If the collection is empty
    * or previous call to next() returned the last entry, further calls to next()
    * will return NULL.
    *
    * @retval [const IParameterMapEntry *] next map entry or NULL
    */         
    virtual const IParameterMapEntry * next() const = 0;

   /**
    * Get a parameter by name
    *
    * This method returns the parameter whose name matches the 
    * requested name or NULL if an entry with this name is not in the map. 
    * lookup() calls don't affect the internal iterator pointer.
    *
    * @param [const Byte *] parameter name to lookup.
    * @retval [const IReadBuffer *] map entry or NULL
    */    
    virtual const IReadBuffer * lookup(const Byte * name) const = 0;
  };


  /** ------------------------------------
   *
   *   I N I T I A L   S T A T E   I N F O
   *
   * -------------------------------------
   *
   * This struct contains all the Information that 
   * NTA_CreateInitialState needs: input sizes, output sizes
   * and a map of the initial parameters.
   */
  struct IInitialStateInfo
  {
    virtual ~IInitialStateInfo() {}
    virtual const Byte * getNodeType() = 0;
    virtual const IInputSizeMap & getInputSizes() = 0;
    virtual const IOutputSizeMap & getOutputSizes() = 0;
    virtual const IParameterMap & getParameters() = 0;
  };

//  //---------------------------------------------------------------------------
//  /**
//   * @b Responsibility
//   *  Aggregate the additional information a multi-node needs for initialization. 
//   * It includes the number of baby nodes and index ranges of each baby node into
//   * the multi-node inputs and outputs. This struct is passed to
//   * INode::init() during the initialization of nodes.
//   */
//  //---------------------------------------------------------------------------
//  struct IMultiNodeInfo
//  {
//   /**
//    * Virtual destructor. Required for abstract classes.
//    */
//    virtual ~IMultiNodeInfo() {}
//    
//   /**
//    * Return the number of baby nodes in a multi-node. 
//    *
//    * This method is only used for multi-nodes. 
//    * It returns the number of baby nodes for this multi-node. 
//    *
//    * @retval [NTA_Size] number of baby nodes in this multi-node. 
//    */      
//    virtual NTA_Size getNodeCount() = 0;
//    
//   /**
//    * Return the Multi-node input list for a given input variable in a multi-node
//    *
//    * This method is only used for multi-nodes. 
//    * It returns a pointer to an array of NTA_IndexRangeLists's, one per baby node. Each
//    * NTA_IndexRangeList contains a count and an array of NTA_IndexRange's. 
//    * Each NTA_IndexRange has an offset and size, specifying the offset within the
//    * input variable 'varName', and the number of elements. 
//    *
//    * @retval [NTA_IndexRangeList *] array of NTA_IndexRangeLists, one for each baby node
//    */      
//    virtual const NTA_IndexRangeList * getInputList(const NTA_Byte* varName) = 0;
//    
//   /**
//    * Return the Multi-node output sizes for a given output variable of a multi-node
//    *
//    * This method is only used for multi-nodes. 
//    * It returns a pointer to an array of sizes, one per baby node of the multi-node. 
//    *
//    * @retval [IReadBuffer &] serialized SparseMatrix01
//    */      
//    virtual const NTA_Size * getOutputSizes(const NTA_Byte* varName) = 0;
//  };

inline NTA_Byte *_ReadString_alloc(NTA_UInt32 size)
  { return new NTA_Byte[size]; }
inline void _ReadString_dealloc(NTA_Byte *p)
  { delete[] p; }

inline std::string ReadStringFromBuffer(const IReadBuffer &buf)
{
  NTA_Byte *value = 0;
  NTA_UInt32 size = 0;
  NTA_Int32 result = buf.readString(value, size, 
      _ReadString_alloc, _ReadString_dealloc); 
  if(result != 0)
    throw std::runtime_error("Failed to read string from stream.");
  std::string toReturn(value, size);
  // Real fps must be provided to use delete here.
  delete[] value;
  return toReturn;
}


  
} // end namespace nta

#endif // NTA_OBJECT_MODEL_HPP



