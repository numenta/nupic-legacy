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
 * ----------------------------------------------------------------------
 */

/** @file 
*
*
*
*/

/*
 * TEMPORARY for NUPIC 2 development
 * Included because included by object_model.hpp
 */


#ifndef NTA_OBJECT_MODEL_H
#define NTA_OBJECT_MODEL_H

#ifdef __cplusplus
extern "C" {
#endif

#include <nta/types/types.h>

/*----------------------------------------------------------------------
 */

/**
 * @b Responsibility:
 *  1. Defines the C API for the runtime engine object model.
 *
 * @b Rationale:
 *  The plugin API supports C as a lowest common denominator. Plugins that publish a C API
 *  need to access the runtime services through a C API. This is it.
 *
 * @b Resource/Ownerships:
 *  None. just an interface
 *
 * @b General API information
 * 
 *  An important goal of the C object model is to immitate the C++ object model 
 *  (nta/plugin/object_model.hpp). The C++ object model is implemented as a set of 
 *  interfaces (pure abstract classes). The C object model has a one to one mapping
 *  to each interface. Each C interface consists of a struct with function 
 *  pointers that correspond to the virtual table of the C++ interface. 
 *  The implicit this pointer of a C++ interface is emulated with 
 *  an explicit opaque handle that you must pass to every C function in the 
 *  C object model API.
 *
 *  The reason the 1-1 mapping is so important is that the concrete runtime object model
 * is composed of objects that implement both interfaces and expose a dual C/C++ facade.
 * Having a 1-1 mapping between the interfaces allows reusing the same implementation
 * with minimal forwarding inside each runtime object. 
 *
 *  The naming convention of mapped interfaces is that the C++ nta::I<interface name> corresponds to the 
 *  NTA_<interface name>. The nta namespace is translated to an NTA_ prefix and the I is dropped.
 *  
 * @b Invariants:
 *  
 * @b Notes:
 *  1. There is a compatible C++ object model [object_model.hpp] that documents in detail 
 *  every interface and struct. Please check out this file for detailed documentation on
 *  the corresponding C runtime object interface.  
 */

/** ----------------------
 *
 *   R E A D   B U F F E R
 *
 * -----------------------
 *
 * This struct represents a binary buffer you can read
 * sequentially. You can read formatted input if you
 * know the internal format or you can read it as a byte
 * array. The internal representation is stringified
 * so it works properly on different platforms.
 */ 
typedef struct _NTA_ReadBufferHandle { char c; } * NTA_ReadBufferHandle; 
typedef struct NTA_ReadBuffer
{
  /* functions */
  void (*reset)(NTA_ReadBufferHandle handle);
  NTA_Size (*getSize)(NTA_ReadBufferHandle handle);
  const NTA_Byte * (*getData)(NTA_ReadBufferHandle handle);
  NTA_Int32 (*readByte)(NTA_ReadBufferHandle handle, NTA_Byte * value);
  NTA_Int32 (*readByteArray)(NTA_ReadBufferHandle handle, NTA_Byte * value, NTA_Size * size);
  NTA_Int32 (*readAsString)(NTA_ReadBufferHandle handle, 
      NTA_Byte ** value, 
      NTA_UInt32 * size,
      NTA_Byte *(*fAlloc)(NTA_UInt32),
      void (*fDealloc)(NTA_Byte *)
    );
    
  NTA_Int32 (*readInt32)(NTA_ReadBufferHandle handle, NTA_Int32 * value);
  NTA_Int32 (*readInt32Array)(NTA_ReadBufferHandle handle, NTA_Int32 * value, NTA_Size size);
  NTA_Int32 (*readUInt32)(NTA_ReadBufferHandle handle, NTA_UInt32 * value);
  NTA_Int32 (*readUInt32Array)(NTA_ReadBufferHandle handle, NTA_UInt32 * value, NTA_Size size);
  NTA_Int32 (*readInt64)(NTA_ReadBufferHandle handle, NTA_Int64 * value);
  NTA_Int32 (*readInt64Array)(NTA_ReadBufferHandle handle, NTA_Int64 * value, NTA_Size size);
  NTA_Int32 (*readUInt64)(NTA_ReadBufferHandle handle, NTA_UInt64 * value);
  NTA_Int32 (*readUInt64Array)(NTA_ReadBufferHandle handle, NTA_UInt64 * value, NTA_Size size);
  NTA_Int32 (*readReal32)(NTA_ReadBufferHandle handle, NTA_Real32 * value);
  NTA_Int32 (*readReal32Array)(NTA_ReadBufferHandle handle, NTA_Real32 * value, NTA_Size size);   
  NTA_Int32 (*readReal64)(NTA_ReadBufferHandle handle, NTA_Real64 * value);
  NTA_Int32 (*readReal64Array)(NTA_ReadBufferHandle handle, NTA_Real64 * value, NTA_Size size);   
  
  /* data members */
  NTA_ReadBufferHandle handle;
  
} NTA_ReadBuffer;

/** ---------------------------------------
 *
 *   R E A D   B U F F E R   I T E R A T O R
 *
 * ----------------------------------------
 *
 * This struct represents an iterator over a collection
 * of read buffers. .
 * It has a next() function to get the next buffer in the colection
 * and a reset() function that sets the internal pointer to the first range again.
 */
typedef struct _NTA_ReadBufferIteratorHandle { char c; } * NTA_ReadBufferIteratorHandle;  
typedef struct NTA_ReadBufferIterator
{
   /* functions */
   void (*reset)(NTA_ReadBufferIteratorHandle handle);
   const NTA_ReadBuffer * (*next)(NTA_ReadBufferIteratorHandle handle);
   
   /* data members */
   NTA_ReadBufferIteratorHandle handle;
} NTA_ReadBufferIterator;

/** ------------------------
 *
 *   W R I T E   B U F F E R
 *
 * -------------------------
 *
 * This struct represents a binary buffer you can write
 * sequentially. You can write formatted input if you
 * know the internal format or you can write it as a byte
 * array. The internal representation is stringified
 * so it works properly on different platforms.
 */ 
typedef struct _NTA_WriteBufferHandle { char c; } * NTA_WriteBufferHandle;  
typedef struct NTA_WriteBuffer
{
  /* functions */
  NTA_Size (*getSize)(NTA_WriteBufferHandle handle);
  const NTA_Byte * (*getData)(NTA_WriteBufferHandle handle);
  NTA_Int32 (*writeByte)(NTA_WriteBufferHandle handle, NTA_Byte value);
  NTA_Int32 (*writeByteArray)(NTA_WriteBufferHandle handle, const NTA_Byte * value, NTA_Size size);
  NTA_Int32 (*writeAsString)(NTA_WriteBufferHandle handle, const NTA_Byte * value, NTA_Size size);
  NTA_Int32 (*writeInt32)(NTA_WriteBufferHandle handle, NTA_Int32 value);
  NTA_Int32 (*writeInt32Array)(NTA_WriteBufferHandle handle, const NTA_Int32 * value, NTA_Size size);
  NTA_Int32 (*writeUInt32)(NTA_WriteBufferHandle handle, NTA_UInt32 value);
  NTA_Int32 (*writeUInt32Array)(NTA_WriteBufferHandle handle, const NTA_UInt32 * value, NTA_Size size);
  NTA_Int32 (*writeInt64)(NTA_WriteBufferHandle handle, NTA_Int64 value);
  NTA_Int32 (*writeInt64Array)(NTA_WriteBufferHandle handle, const NTA_Int64 * value, NTA_Size size);
  NTA_Int32 (*writeUInt64)(NTA_WriteBufferHandle handle, NTA_UInt64 value);
  NTA_Int32 (*writeUInt64Array)(NTA_WriteBufferHandle handle, const NTA_UInt64 * value, NTA_Size size);
  NTA_Int32 (*writeReal32)(NTA_WriteBufferHandle handle, NTA_Real32 value);
  NTA_Int32 (*writeReal32Array)(NTA_WriteBufferHandle handle, const NTA_Real32 * value, NTA_Size size);   
  NTA_Int32 (*writeReal64)(NTA_WriteBufferHandle handle, NTA_Real64 value);
  NTA_Int32 (*writeReal64Array)(NTA_WriteBufferHandle handle, const NTA_Real64 * value, NTA_Size size); 
   
  /* data members */
  NTA_WriteBufferHandle handle;
  
} NTA_WriteBuffer;

/** -----------------------
 *
 *   I N P U T  R A N G E 
 *
 * ------------------------
 *
 * This struct represents an input range in a variable.
 * It has const begin/end iterators for traversal and
 * two function get the size of each element in bytes
 * (elementSize) and number of elements in the range
 * (elementCount).
 */
typedef struct _NTA_InputRangeHandle { char c; } * NTA_InputRangeHandle;  
typedef struct NTA_InputRange
{
  /* functions */
  const NTA_Byte * (*begin)(NTA_InputRangeHandle handle);
  const NTA_Byte * (*end)(NTA_InputRangeHandle handle);
  NTA_Size (*getElementCount)(NTA_InputRangeHandle handle);
  NTA_Size (*getElementSize)(NTA_InputRangeHandle handle);

  /* data members */
  NTA_InputRangeHandle handle;
  
} NTA_InputRange;


/** -----------------------------------------
 *
 *   I N P U T  R A N G E   M A P   E N T R Y 
 *
 * ------------------------------------------
 *
 * This struct represents a single entry in an input range map
 * It stores a name, a list of input ranges and the number
 * of input ranges in this entry
 */ 
typedef struct _NTA_InputRangeMapEntryHandle { char c; } * NTA_InputRangeMapEntryHandle;
typedef struct NTA_InputRangeMapEntry
{
  /* functions */
  void (*reset)(NTA_InputRangeMapEntryHandle handle);
  const NTA_InputRange * (*next)(NTA_InputRangeMapEntryHandle handle);

  /* data members */
  const NTA_Byte * name;
  NTA_InputRangeMapEntryHandle handle;
   
} NTA_InputRangeMapEntry;


/** -----------------------------
 *
 *   I N P U T  R A N G E   M A P
 *
 * ------------------------------
 *
 * This struct represents an input range map of a node.
 * It contains entries and provides iterator-like accessor
 * as well as lookup by name accessor.
 */
typedef struct _NTA_InputRangeMapHandle { char c; } * NTA_InputRangeMapHandle;
typedef struct NTA_InputRangeMap
{
  /* functions */
  void (*reset)(NTA_InputRangeMapHandle handle);
  const NTA_InputRangeMapEntry * (*next)(NTA_InputRangeMapHandle handle);
  const NTA_InputRangeMapEntry * (*lookup)(NTA_InputRangeMapHandle handle, const NTA_Byte * name);

  /* data members */
  NTA_InputRangeMapHandle handle;
  
} NTA_InputRangeMap;

/** -----------------------------------------
 *
 *   I N D E X    R A N G E 
 *
 * ------------------------------------------
 *
 * This struct represents a chunk of an input range.
 * This is used to represent each internal link of a multi-node. 
 */ 
typedef struct NTA_IndexRange
{
  /* data members */
  NTA_UInt32       begin;   // begin offset
  NTA_UInt32       size;    // number of elements
   
} NTA_IndexRange;


/** -----------------------------------------
 *
 *   I N D E X   R A N G E    L I S T
 *
 * ------------------------------------------
 *
 * This struct represents a list of NTA_IndexRanges. It encapsulates all
 * the connections for a specific baby node in a multi-node. 
 */ 
typedef struct NTA_IndexRangeList
{
  /* data members */
  NTA_Size          rangeCount;   // number of elements in the ranges array 
  NTA_IndexRange *  ranges;       // array of rangeCount NTA_IndexRange's
   
} NTA_IndexRangeList;

/** -----------------------
 *
 *   O U T P U T  R A N G E 
 *
 * ------------------------
 *
 * This struct represents an output range in a variable.
 * It has const begin/end iterators for traversal and
 * two function get the size of each element in bytes
 * (elementSize) and number of elements in the range
 * (elementCount).
 */
typedef struct _NTA_OutputRangeHandle { char c; } * NTA_OutputRangeHandle;  
typedef struct NTA_OutputRange
{
  /* functions */
  NTA_Byte * (*begin)(NTA_OutputRangeHandle handle);
  NTA_Byte * (*end)(NTA_OutputRangeHandle handle);
  NTA_Size (*getElementCount)(NTA_OutputRangeHandle handle);
  NTA_Size (*getElementSize)(NTA_OutputRangeHandle handle);

  /* data memebers */
  NTA_OutputRangeHandle handle;
  
} NTA_OutputRange;

/** -------------------------------------------
 *
 *   O U T P U T  R A N G E   M A P   E N T R Y 
 *
 * --------------------------------------------
 *
 * This struct represents a single entry in an output range map
 * It stores a name and an output range.
 */
typedef struct NTA_OutputRangeMapEntry
{
  const NTA_Byte * name;
  NTA_OutputRange * range;
   
} NTA_OutputRangeMapEntry;


/** -------------------------------
 *
 *   O U T P U T  R A N G E   M A P
 *
 * --------------------------------
 *
 * This struct represents an output range map of a node.
 * It contains entries and provides iterator-like accessor
 * as well as lookup by name accessor.
 */
typedef struct _NTA_OutputRangeMapHandle { char c; } * NTA_OutputRangeMapHandle;  
typedef struct NTA_OutputRangeMap
{
  /* functions */
  void (*reset)(NTA_OutputRangeMapHandle handle);
  NTA_OutputRangeMapEntry * (*next)(NTA_OutputRangeMapHandle handle);
  NTA_OutputRange * (*lookup)(NTA_OutputRangeMapHandle handle, const NTA_Byte * name);

  /* data members */
  NTA_OutputRangeMapHandle handle;
  
} NTA_OutputRangeMap;

/** --------------------------------------
 *
 *   P A R A M E T E R   M A P   E N T R Y 
 *
 * ---------------------------------------
 *
 * This struct represents a single entry in a parameter map
 * It stores a name, a list of output ranges and the number
 * of output ranges in this entry
 */
typedef struct NTA_ParameterMapEntry
{
  const NTA_Byte * name;
  const NTA_ReadBuffer * value;
   
} NTA_ParameterMapEntry;


/** ---------------------------
 *
 *   P A R A M E T E R   M A P
 *
 * ----------------------------
 *
 * This struct represents a parameter map of a node.
 * It contains various parameters and provides iterator-like accessor
 * as well as lookup by name accessor.
 */
typedef struct _NTA_ParameterMapHandle { char c; } * NTA_ParameterMapHandle;  
typedef struct NTA_ParameterMap
{
  /* functions */
  void (*reset)(NTA_ParameterMapHandle handle);
  const NTA_ParameterMapEntry * (*next)(NTA_ParameterMapHandle handle);
  const NTA_ReadBuffer * (*lookup)(NTA_ParameterMapHandle handle, const NTA_Byte * name);

  /* data members */
  NTA_ParameterMapHandle handle;
  
} NTA_ParameterMap;


/** -------------------------------
 *
 *   I N P U T    
 *
 * --------------------------------
 *
 * This struct represents a flattened input of a node.
 */
typedef struct _NTA_InputHandle { char c; } * NTA_InputHandle;  
typedef struct NTA_Input
{
  /* functions */
  const NTA_Byte * (*begin)(NTA_InputHandle handle, NTA_Int32 nodeIdx, 
                            const NTA_Byte* sentinelP);
  const NTA_Byte * (*end)(NTA_InputHandle handle, NTA_Int32 nodeIdx);
  NTA_Size (*getElementCount)(NTA_InputHandle handle, NTA_Int32 nodeIdx);
  NTA_Size (*getElementSize)(NTA_InputHandle handle);
  
  NTA_Size * (*getLinkBoundaries)(NTA_InputHandle handle, NTA_Int32 nodeIdx);
  NTA_Size (*getLinkCount)(NTA_InputHandle handle, NTA_Int32 nodeIdx);

  /* data members */
  NTA_InputHandle handle;
  
} NTA_Input;


/** -------------------------------
 *
 *   O U T P U T    
 *
 * --------------------------------
 *
 * This struct represents a flattened output of a node.
 */
typedef struct _NTA_OutputHandle { char c; } * NTA_OutputHandle;  
typedef struct NTA_Output
{
  /* functions */
  NTA_Byte * (*begin)(NTA_OutputHandle handle, NTA_Int32 nodeIdx);
  NTA_Byte * (*end)(NTA_OutputHandle handle, NTA_Int32 nodeIdx);
  NTA_Size (*getElementCount)(NTA_OutputHandle handle, NTA_Int32 nodeIdx);
  NTA_Size (*getElementSize)(NTA_OutputHandle handle);
  
  /* data members */
  NTA_OutputHandle handle;
  
} NTA_Output;



/** ---------------------------
 *
 *   N O D E   I N F O
 *
 * ----------------------------
 *
 * This struct contains all the initial information 
 * that a node needs: inputs, outputs, parameters and state
 */
typedef struct _NTA_NodeInfoHandle { char c; } * NTA_NodeInfoHandle;  
typedef struct _NTA_NodeInfo
{
  /* functions */
  NTA_UInt64 (*getID)(NTA_NodeInfoHandle handle);
  const NTA_Byte * (*getType)(NTA_NodeInfoHandle handle);
  NTA_LogLevel (*getLogLevel)(NTA_NodeInfoHandle handle);
  NTA_Input * (*getInput)(NTA_NodeInfoHandle handle, const NTA_Byte* varName);
  NTA_Output * (*getOutput)(NTA_NodeInfoHandle handle, const NTA_Byte* varName);
  NTA_InputRangeMap * (*getInputs)(NTA_NodeInfoHandle handle);
  NTA_OutputRangeMap * (*getOutputs)(NTA_NodeInfoHandle handle);
  NTA_ParameterMap * (*getParameters)(NTA_NodeInfoHandle handle);
  NTA_ReadBuffer * (*getState)(NTA_NodeInfoHandle handle);
  NTA_Size (*getMNNodeCount)(NTA_NodeInfoHandle handle);
  const NTA_IndexRangeList * (*getMNInputLists)(NTA_NodeInfoHandle handle, const NTA_Byte* varName);
  const NTA_Size * (*getMNOutputSizes)(NTA_NodeInfoHandle handle, const NTA_Byte* varName);

  /* data members */
  NTA_NodeInfoHandle handle;
  
} NTA_NodeInfo;


/**------------------------------
 *
 *   M U L T I   N O D E   I N F O
 *
 * -------------------------------
 *
 * This struct contains the additional initial information 
 * that a multi-node needs: number of baby nodes, index ranges of baby nodes inputs
 * and the output size of each baby node
 */
typedef struct _NTA_MultiNodeInfoHandle { char c; } * NTA_MultiNodeInfoHandle;  
typedef struct _NTA_MultiNodeInfo
{
  /* functions */

  NTA_Size (*getNodeCount)(NTA_MultiNodeInfoHandle handle);
  const NTA_IndexRangeList * (*getInputList)(NTA_MultiNodeInfoHandle handle, const NTA_Byte* varName);
  const NTA_Size * (*getOutputSizes)(NTA_NodeInfoHandle handle, const NTA_Byte* varName);

  /* data members */
  NTA_MultiNodeInfoHandle handle;
 
} NTA_MultiNodeInfo;



/** -----------------------------------------
 *
 *   I N P U T  S I Z E   M A P   E N T R Y 
 *
 * ------------------------------------------
 *
 * This struct represents a single entry in an input size map
 * It stores a name and a list of input sizes (one per each input range)
 */ 
typedef struct _NTA_InputSizeMapEntryHandle { char c; } * NTA_InputSizeMapEntryHandle;
typedef struct NTA_InputSizeMapEntry
{
  /* data members */
  const NTA_Byte * name;
  NTA_UInt32       count;
  NTA_UInt32 *     sizes;
   
} NTA_InputSizeMapEntry;


/** -----------------------------
 *
 *   I N P U T  S I Z E   M A P
 *
 * ------------------------------
 *
 * This struct represents an input range map of a node.
 * It contains entries and provides iterator-like accessor
 * as well as lookup by name accessor.
 */
typedef struct _NTA_InputSizeMapHandle { char c; } * NTA_InputSizeMapHandle;
typedef struct NTA_InputSizeMap
{
  /* functions */
  void (*reset)(NTA_InputSizeMapHandle handle);
  const NTA_InputSizeMapEntry * (*next)(NTA_InputSizeMapHandle handle);
  const NTA_InputSizeMapEntry * (*lookup)(NTA_InputSizeMapHandle handle, const NTA_Byte * name);

  /* data members */
  NTA_InputSizeMapHandle handle;
  
} NTA_InputSizeMap;

/** -------------------------------------------
 *
 *   O U T P U T  S I Z E   M A P   E N T R Y 
 *
 * --------------------------------------------
 *
 * This struct represents a single entry in an output size map
 * It stores an output name and the size of this output.
 */
typedef struct NTA_OutputSizeMapEntry
{
  const NTA_Byte * name;
  NTA_UInt32       size;
   
} NTA_OutputSizeMapEntry;


/** -------------------------------
 *
 *   O U T P U T  S I Z E   M A P
 *
 * --------------------------------
 *
 * This struct represents an output size map of a node.
 * It contains entries and provides iterator-like accessor
 * as well as lookup by name accessor.
 */
typedef struct _NTA_OutputSizeMapHandle { char c; } * NTA_OutputSizeMapHandle;  
typedef struct NTA_OutputSizeMap
{
  /* functions */
  void (*reset)(NTA_OutputSizeMapHandle handle);
  NTA_OutputSizeMapEntry * (*next)(NTA_OutputSizeMapHandle handle);
  NTA_UInt32 (*lookup)(NTA_OutputSizeMapHandle handle, const NTA_Byte * name);

  /* data members */
  NTA_OutputSizeMapHandle handle;
  
} NTA_OutputSizeMap;

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
typedef struct _NTA_InitialStateInfoHandle { char c; } * NTA_InitialStateInfoHandle;  
typedef struct _NTA_InitialStateInfo
{
  /* functions */
  const NTA_Byte * (*getNodeType)(NTA_InitialStateInfoHandle handle);
  const NTA_InputSizeMap * (*getInputSizes)(NTA_InitialStateInfoHandle handle);
  const NTA_OutputSizeMap * (*getOutputSizes)(NTA_InitialStateInfoHandle handle);
  const NTA_ParameterMap *  (*getParameters)(NTA_InitialStateInfoHandle handle);
  const NTA_MultiNodeInfo * (*getMultiNodeInfo)(NTA_InitialStateInfoHandle handle);

  /* data members */
  NTA_InitialStateInfoHandle handle;
  
} NTA_InitialStateInfo;


#ifdef  __cplusplus
}
#endif
#endif /* NTA_OBJECT_MODEL_H */

