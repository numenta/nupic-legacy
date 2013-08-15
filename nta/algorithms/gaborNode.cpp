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
 *  This module implements efficient 2D image convolution (with gabor
 *  filtering as the intended use case.)
 *  It exports a single C function:
 *
 *  void _gaborCompute(const NUMPY_ARRAY * psGaborBank,
 *                     const NUMPY_ARRAY * psInput,
 *                     const NUMPY_ARRAY * psBBox,
 *                     const NUMPY_ARRAY * psOutputs,
 *                     float fGain,
 *                     const NUMPY_ARRAY * psBuffer);
 *
 *  The C NUMPY_ARRAY structure mirrors an ARRAY class in
 *  Python.
 *
 *  This exported C function is expected to be used in conjunction
 *  with ctypes wrappers around numpy array objects.
 */ 

// Includes the correct Python.h. Must be the first header. 

#include <nta/utils/Log.hpp>
#include <stdio.h>
#include <math.h>


// Enable debugging
//#define DEBUG   1

#include "gaborNode.hpp"


// if INIT_FROM_PYTHON is defined, this module can initialize
// logging from a python system reference. This introduces
// a dependency on PythonSystem, which is not included in the
// algorithm source release. So it is disabled by default
#ifdef INIT_FROM_PYTHON
#ifdef NUPIC2
#error "gaborNode should not depend on Python in NuPIC2"

#else

#include <nta/python/cpplibs/nupic_pycommon/PythonSystem.hpp>

void PythonSystem_initFromReferenceP(unsigned long long refP)
{
  NTA_CHECK(refP != 0);
  const nta::PythonSystemRef *p = (nta::PythonSystemRef*)refP;
  nta::PythonSystem::initFromReference(*p);
}
#endif // NUPIC2
#endif // INIT_FROM_PYTHON



#ifdef __cplusplus
extern "C" {
#endif 


// Macros for accessing dimensionalities:
#define IMAGESET_ELEM(array, k)       (((long int*)(array->pnDimensions))[k])
#define IMAGESET_PLANES(array)        IMAGESET_ELEM(array, 0)
#define IMAGESET_ROWS(array)          IMAGESET_ELEM(array, 1)
#define IMAGESET_COLS(array)          IMAGESET_ELEM(array, 2)
#define IMAGESET_STRIDE(array, k)     (((long int*)(array->pnStrides))[k])
#define IMAGESET_PLANESTRIDE(array)   IMAGESET_STRIDE(array, 0)
#define IMAGESET_ROWSTRIDE(array)     IMAGESET_STRIDE(array, 1)

#define IMAGE_ELEM(array, k)          (((long int*)(array->pnDimensions))[k])
#define IMAGE_ROWS(array)             IMAGE_ELEM(array, 0)
#define IMAGE_COLS(array)             IMAGE_ELEM(array, 1)
#define IMAGE_STRIDE(array, k)        (((long int*)(array->pnStrides))[k])
#define IMAGE_ROWSTRIDE(array)        IMAGE_STRIDE(array, 0)

#define GABORSET_ELEM(array, k)       (((long int*)(array->pnDimensions))[k])
#define GABORSET_PLANES(array)        GABORSET_ELEM(array, 0)
#define GABORSET_ROWS(array)          GABORSET_ELEM(array, 2)
#define GABORSET_COLS(array)          GABORSET_ELEM(array, 3)
#define GABORSET_STRIDE(array, k)     (((long int*)(array->pnStrides))[k])
#define GABORSET_PLANESTRIDE(array)   GABORSET_STRIDE(array, 0)
#define GABORSET_SHIFTSTRIDE(array)   GABORSET_STRIDE(array, 1)
#define GABORSET_ROWSTRIDE(array)     GABORSET_STRIDE(array, 2)

#define BBOX_ELEM(bbox, k)            (((int*)(bbox->pData))[k])
#define BBOX_LEFT(bbox)               BBOX_ELEM(bbox, 0)
#define BBOX_TOP(bbox)                BBOX_ELEM(bbox, 1)
#define BBOX_RIGHT(bbox)              BBOX_ELEM(bbox, 2)
#define BBOX_BOTTOM(bbox)             BBOX_ELEM(bbox, 3)
#define BBOX_WIDTH(bbox)              (BBOX_RIGHT(bbox) - BBOX_LEFT(bbox))
#define BBOX_HEIGHT(bbox)             (BBOX_BOTTOM(bbox) - BBOX_TOP(bbox))

#define VECTOR_ELEM(array, k)        (((long int*)(array->pnDimensions))[k])
#define VECTOR_PLANES(array)         VECTOR_ELEM(array, 0)

// Macros for clipping
//#define MIN(x, y)                     ((x) <= (y) ? (x) : (y))
//#define MAX(x, y)                     ((x) <= (y) ? (y) : (x))

// Macro for fast integer abs()
#define IABS32(x)                     (((x) ^ ((x) >> 31)) - ((x) >> 31))
#define IABS64(x)                     (((x) ^ ((x) >> 63)) - ((x) >> 63))

// Macros for aligning integers to even values
#define ALIGN_2_FLOOR(value)          (((value)>>1)<<1)
#define ALIGN_2_CEIL(value)           ALIGN_2_FLOOR((value)+1)
#define ALIGN_4_FLOOR(value)          (((value)>>2)<<2)
#define ALIGN_4_CEIL(value)           ALIGN_4_FLOOR(((value)+3))
#define ALIGN_8_FLOOR(value)          (((value)>>3)<<3)
#define ALIGN_8_CEIL(value)           ALIGN_8_FLOOR((value)+7)


// FUNCTION: _prepareInput_sweepOff()
//
// 1. Convert input image from float to integer32.
// 2. If EDGE_MODE is SWEEPOFF, then add "padding pixels"
//    around the edges of the integrized input plane.
void _prepareInput_sweepOff(const NUMPY_ARRAY * psInput,
                   const NUMPY_ARRAY * psBufferIn,
                   int nHalfFilterDim,
                   const NUMPY_ARRAY * psBBox,
                   const NUMPY_ARRAY * psImageBox,
                   float fOffImageFillValue) {
  int i, j;
  int nFilterDim = nHalfFilterDim << 1;

  // Locate the start of input plane
  const float * pfInput = (const float *)psInput->pData;
  // Compute stride needed to proceed to next input row (in DWORDS)
  int nInputRowStride = IMAGE_ROWSTRIDE(psInput) / sizeof(*pfInput);

  // Locate start of output buffers
  // Note: the 'psBuffer' numpy array is assumed to be format 'int32'
  int * pnOutput = (int *)psBufferIn->pData;
  // Compute stride needed to proceed to next output row (in DWORDS)
  int nOutputRowStride = IMAGE_ROWSTRIDE(psBufferIn) / sizeof(*pnOutput);

  // Guard against buffer over-runs
#ifdef DEBUG
  // Start/end of memory
  const char * pDebugOutputSOMB = (const char*)(psBufferIn->pData);
  const char * pDebugOutputEOMB = pDebugOutputSOMB + IMAGE_ROWSTRIDE(psBufferIn) * IMAGE_ROWS(psBufferIn);
#endif // DEBUG

  // Both the bounding box and the filler box will be expressed
  // with respect to the *output* image (not the *input* image)

  // Take into account bounding box suppression.
  // Our convention is that the bounding box expresses the range
  // of locations in the input image which are valid.
  // So we only need to convert pixel values within the bounding box
  // plus a narrow band around the outside of the bounding box of 
  // width equal to half the width of the filter dimension.
  //
  // We'll also expand our bounding box horizontally to make it line
  // up on a 16-byte boundary (four-pixel boundary)

  // We need to provide fill up to nFill*
  int nFillLeft   = BBOX_LEFT(psBBox);
  int nFillTop    = BBOX_TOP(psBBox);
  int nFillRight  = BBOX_RIGHT(psBBox) + nFilterDim;
  int nFillBottom = BBOX_BOTTOM(psBBox) + nFilterDim;

  // Shrink the pixel boxes to where we have actual pixels
  int nPixelLeft = MAX(nFillLeft, nHalfFilterDim);
  int nPixelTop = MAX(nFillTop,  nHalfFilterDim);
  //int nPixelRight = MIN(nFillRight, BBOX_RIGHT(psBBox) + nHalfFilterDim);
  //int nPixelBottom = MIN(nFillBottom, BBOX_BOTTOM(psBBox) + nHalfFilterDim);
  //int nPixelRight = MIN(nFillRight, BBOX_RIGHT(psBBox) + nHalfFilterDim << 1);
  //int nPixelBottom = MIN(nFillBottom, BBOX_BOTTOM(psBBox) + nHalfFilterDim << 1);
  int nPixelRight = MIN(BBOX_RIGHT(psBBox) + nFilterDim, BBOX_RIGHT(psImageBox) + nHalfFilterDim);
  int nPixelBottom = MIN(BBOX_BOTTOM(psBBox) + nFilterDim, BBOX_BOTTOM(psImageBox) + nHalfFilterDim);

  // If all of our assumptions have been met, then the following
  // conditions should hold (otherwise there is a bug somewhere):
  NTA_ASSERT(nPixelLeft >= nHalfFilterDim);
  NTA_ASSERT(nPixelRight <= IMAGE_COLS(psBufferIn) - nHalfFilterDim);
  NTA_ASSERT(nPixelTop >= nHalfFilterDim);
  NTA_ASSERT(nPixelBottom <= IMAGE_ROWS(psBufferIn) - nHalfFilterDim);

  NTA_ASSERT(nFillLeft >= 0);
  NTA_ASSERT(nFillRight <= IMAGE_COLS(psBufferIn));
  NTA_ASSERT(nFillTop >= 0);
  NTA_ASSERT(nFillBottom <= IMAGE_ROWS(psBufferIn));

  // @todo -- it would be nice if we enforced 16-byte alignment
  // in our bounding boxes (like in 'constrained' mode);
  // but that is starting to get pretty complicated...

  // Advance our output pointer to the beginning of the 
  // fill region.
  // Note: in a bid to get 16-byte alignment most of the time,
  //       we are actually filling our "pure" fill rows at
  //       the top and bottom all the way from the left to
  //       the right.
  pnOutput += nFillTop * nOutputRowStride;

  // Compute numer of pure fill chunks of four 
  int nPureFillQuads = nOutputRowStride >> 2;

  int nOffImageFillValue = (int)fOffImageFillValue;

  // We need to pad the true input image with filler pixels.
  // We'll do the top rows of filler now:
  for (j=nPixelTop - nFillTop; j; j--) {
    // Fill each row 
    for (i=nPureFillQuads; i; i--) {

      // Memory bounds checking
#ifdef DEBUG
      NTA_ASSERT((const char*)pnOutput >= pDebugOutputSOMB);
      NTA_ASSERT((const char*)&(pnOutput[3]) <  pDebugOutputEOMB);
#endif // DEBUG

      *pnOutput++ = nOffImageFillValue;
      *pnOutput++ = nOffImageFillValue;
      *pnOutput++ = nOffImageFillValue;
      *pnOutput++ = nOffImageFillValue;
    }
  }

  // Compute the number of DWORDS (pixels) we'll need to
  // advance to get from the end of row N to the beginning
  // of row N+1
  int nPixelWidth = nPixelRight - nPixelLeft;
  int nInputRowAdvance  = nInputRowStride  - nPixelWidth;
  int nOutputRowAdvance = nOutputRowStride - (nFillRight - nFillLeft);

  // Advance our pointers and row counts to skip past
  // the rows on top of the bounding box, and align
  // our pointers with the left edge of the bounding box.
  pfInput += nInputRowStride  * (nPixelTop - nHalfFilterDim) + (nPixelLeft - nHalfFilterDim);
  //pnOutput += nOutputRowStride * nPixelTop + nPixelLeft;

  // Decide how many rows to convert
  int nOutputRows = nPixelBottom - nPixelTop;

  // We'll process four output pixels at a time
  // (in a partially unrolled loop).  Hopefully the
  // compiler will write SIMD instructions for us. :-)
  // (especially since we went to the trouble of
  // aligning the memory on 16-byte boundaries...)

  // Figure out how many preparatory conersions we should
  // do get 16-byte aligned
  int nNumPrepPixels = (4 - (nPixelLeft % 4)) % 4;
  int nNumPixelsPerRow = nPixelRight - nPixelLeft - nNumPrepPixels;
  int nPixelQuadsPerRow = nNumPixelsPerRow >> 2;
  int nPixelLeftovers = nNumPixelsPerRow - (nPixelQuadsPerRow << 2);
  NTA_ASSERT((nNumPrepPixels + nPixelLeftovers + (nPixelQuadsPerRow << 2)) == (nPixelRight - nPixelLeft));

  // How many pixels to fill on the left and right sides
  int nNumPreFills = nPixelLeft - nFillLeft;
  int nNumPostFills = nFillRight - nPixelRight;

  // Advance past any voids
  pnOutput += nFillLeft;

  // Process each output location
  for (j=nOutputRows; j; j--) {

    // Do pre-filling (on the left side)
    for (i=nNumPreFills; i; i--) {

      // Memory bounds checking
#ifdef DEBUG
      NTA_ASSERT((const char*)pnOutput >= pDebugOutputSOMB);
      NTA_ASSERT((const char*)&(pnOutput[0]) <  pDebugOutputEOMB);
#endif // DEBUG

      *pnOutput++ = nOffImageFillValue;
    }

    // Do prep pixel conversions to get ourselves aligned
    for (i=nNumPrepPixels; i; i--) {

      // Memory bounds checking
#ifdef DEBUG
      NTA_ASSERT((const char*)pnOutput >= pDebugOutputSOMB);
      NTA_ASSERT((const char*)&(pnOutput[0]) <  pDebugOutputEOMB);
#endif // DEBUG

      *pnOutput++ = (int)(*pfInput++);
    }

    // Do pixel conversion
    for (i=nPixelQuadsPerRow; i; i--) {

      // Memory bounds checking
#ifdef DEBUG
      NTA_ASSERT((const char*)pnOutput >= pDebugOutputSOMB);
      NTA_ASSERT((const char*)&(pnOutput[3]) <  pDebugOutputEOMB);
#endif // DEBUG

      // Do four pixel conversions
      *pnOutput++ = (int)(*pfInput++);
      *pnOutput++ = (int)(*pfInput++);
      *pnOutput++ = (int)(*pfInput++);
      *pnOutput++ = (int)(*pfInput++);
    }

    // Do left-overs that didn't fit in a quad
    for (i=nPixelLeftovers; i; i--) {

      // Memory bounds checking
#ifdef DEBUG
      NTA_ASSERT((const char*)pnOutput >= pDebugOutputSOMB);
      NTA_ASSERT((const char*)&(pnOutput[0]) <  pDebugOutputEOMB);
#endif // DEBUG

      *pnOutput++ = (int)(*pfInput++);
    }

    // Do post-filling (on the right side)
    for (i=nNumPostFills; i; i--) {

      // Memory bounds checking
#ifdef DEBUG
      NTA_ASSERT((const char*)pnOutput >= pDebugOutputSOMB);
      NTA_ASSERT((const char*)&(pnOutput[0]) <  pDebugOutputEOMB);
#endif // DEBUG

      *pnOutput++ = nOffImageFillValue;
    }
    
    // Advance to next rows
    pfInput  += nInputRowAdvance;
    pnOutput += nOutputRowAdvance;
  }

  // At this point, our output buffer pointer is 
  // on the correct row (the first row to be filled
  // below the pixel bounding box), but it is advanced 
  // 'nFillLeft' pixels to the right (i.e., it is 
  // on the 'nFillLeft'th column).  So we need to
  // move it back to the beginning of the row
  // (i.e., to the 0th column)
  pnOutput -= nFillLeft;

  // Fill the bottom rows
  for (j=nFillBottom - nPixelBottom; j; j--) {
    // Fill each row 
    for (i=nPureFillQuads; i; i--) {

      // Memory bounds checking
#ifdef DEBUG
      NTA_ASSERT((const char*)pnOutput >= pDebugOutputSOMB);
      NTA_ASSERT((const char*)&(pnOutput[3]) <  pDebugOutputEOMB);
#endif // DEBUG

      *pnOutput++ = nOffImageFillValue;
      *pnOutput++ = nOffImageFillValue;
      *pnOutput++ = nOffImageFillValue;
      *pnOutput++ = nOffImageFillValue;
    }
  }

  // At this point, our output buffer pointer should be
  // exactly positioned at the edge of our memory
#ifdef DEBUG
  NTA_ASSERT((const char*)pnOutput <= pDebugOutputEOMB);
#endif // DEBUG
}


// FUNCTION: _prepareInput_constrained()
//
// 1. Convert input image from float to integer32.
// 2. If EDGE_MODE is SWEEPOFF, then add "padding pixels"
//    around the edges of the integrized input plane.
void _prepareInput_constrained(const NUMPY_ARRAY * psInput,
                   const NUMPY_ARRAY * psBufferIn,
                   int nHalfFilterDim,
                   const NUMPY_ARRAY * psBBox,
                   const NUMPY_ARRAY * psImageBox) {
  int i, j;

  // Locate the start of input plane
  const float * pfInput = (const float *)psInput->pData;
  // Compute stride needed to proceed to next input row (in DWORDS)
  int nInputRowStride = IMAGE_ROWSTRIDE(psInput) / sizeof(*pfInput);

  // Locate start of output buffers
  // Note: the 'psBuffer' numpy array is assumed to be format 'int32'
  int * pnOutput = (int *)psBufferIn->pData;
  // Compute stride needed to proceed to next output row (in DWORDS)
  int nOutputRowStride = IMAGE_ROWSTRIDE(psBufferIn) / sizeof(*pnOutput);

  // Take into account bounding box suppression.
  // Our convention is that the bounding box expresses the range
  // of locations in the input image which are valid.
  // So we only need to convert pixel values within the bounding box
  // plus a narrow band around the outside of the bounding box of 
  // width equal to half the width of the filter dimension.
  //
  // We'll also expand our bounding box horizontally to make it line
  // up on a 16-byte boundary (four-pixel boundary)
  int nBoxLeft   = MAX(ALIGN_4_FLOOR(BBOX_LEFT(psBBox) - nHalfFilterDim), BBOX_LEFT(psImageBox));
  int nBoxRight  = MIN(BBOX_RIGHT(psBBox) + nHalfFilterDim, BBOX_RIGHT(psImageBox));
  int nBoxTop    = MAX(BBOX_TOP(psBBox) - nHalfFilterDim,  BBOX_TOP(psImageBox));
  int nBoxBottom = MIN(BBOX_BOTTOM(psBBox) + nHalfFilterDim, BBOX_BOTTOM(psImageBox));

  // If all of our assumptions have been met, then the following
  // conditions should hold (otherwise there is a bug somewhere):
  NTA_ASSERT(nBoxLeft >= 0);
  NTA_ASSERT(nBoxRight <= IMAGE_COLS(psInput));
  NTA_ASSERT(nBoxTop >= 0);
  NTA_ASSERT(nBoxBottom <= IMAGE_ROWS(psInput));

  // Make sure we got the alignment we wanted
  NTA_ASSERT(nBoxLeft % 4 == 0); 

  // Compute the number of DWORDS (pixels) we'll need to
  // advance to get from the end of row N to the beginning
  // of row N+1
  int nBoxWidth = nBoxRight - nBoxLeft;
  int nInputRowAdvance  = nInputRowStride  - nBoxWidth;
  int nOutputRowAdvance = nOutputRowStride - nBoxWidth;

  // Advance our pointers and row counts to skip past
  // the rows on top of the bounding box, and align
  // our pointers with the left edge of the bounding box.
  pfInput  += nInputRowStride  * nBoxTop + nBoxLeft;
  pnOutput += nOutputRowStride * nBoxTop + nBoxLeft;

  // Decide how many rows to convert
  int nOutputRows = nBoxBottom - nBoxTop;

  // We'll process four output pixels at a time
  // (in a partially unrolled loop).  Hopefully the
  // compiler will write SIMD instructions for us. :-)
  // (especially since we went to the trouble of
  // aligning the memory on 16-byte boundaries...)
  int nQuadsPerRow = nBoxWidth >> 2;

  // Handle leftovers, if any
  int nLeftovers = nBoxWidth - (nQuadsPerRow << 2);

  // Process each output location
  for (j=nOutputRows; j; j--) {

    // Do four pixel conversions
    for (i=nQuadsPerRow; i; i--) {
      *pnOutput++ = (int)(*pfInput++);
      *pnOutput++ = (int)(*pfInput++);
      *pnOutput++ = (int)(*pfInput++);
      *pnOutput++ = (int)(*pfInput++);
    }

    // Convert any leftovers
    for (i=nLeftovers; i; i--)
      *pnOutput++ = (int)(*pfInput++);
    
    // Advance to next rows
    pfInput  += nInputRowAdvance;
    pnOutput += nOutputRowAdvance;
  }
}


// FUNCTION: _prepareInput()
//
// 1. Convert input image from float to integer32.
// 2. If EDGE_MODE is SWEEPOFF, then add "padding pixels"
//    around the edges of the integrized input plane.
void _prepareInput(const NUMPY_ARRAY * psInput,
                   const NUMPY_ARRAY * psBufferIn,
                   int nHalfFilterDim,
                   const NUMPY_ARRAY * psBBox,
                   const NUMPY_ARRAY * psImageBox,
                   EDGE_MODE eEdgeMode,
                   float fOffImageFillValue) {

  if (eEdgeMode == EDGE_MODE_CONSTRAINED)
    _prepareInput_constrained(psInput, 
                              psBufferIn, 
                              nHalfFilterDim, 
                              psBBox,
                              psImageBox);
  else
    _prepareInput_sweepOff(psInput, 
                           psBufferIn, 
                           nHalfFilterDim, 
                           psBBox,
                           psImageBox,
                           fOffImageFillValue);
}


// It is useful for debugging to set this to
// a non-zero value so see where the null responses
// were filled in.
#define NULL_RESPONSE 0
//#define NULL_RESPONSE (64 << 12)

// Flags indicating which statistics to keep on the fly.
#define STATS_NONE          0x00
#define STATS_MAX_ABS       0x01
#define STATS_MAX_MIN       0x02
#define STATS_SUM_ABS       0x04
#define STATS_SUM_POS_NEG   0x08
#define STATS_MAX           (STATS_MAX_ABS|STATS_MAX_MIN)
#define STATS_MEAN          (STATS_SUM_ABS|STATS_SUM_POS_NEG)
#define STATS_SINGLE        (STATS_MAX_ABS|STATS_SUM_ABS)
#define STATS_DUAL          (STATS_MAX_MIN|STATS_SUM_POS_NEG)


void _computeNormalizers(int & nStatPosGrand, 
                         int & nStatNegGrand, 
                         unsigned int nStatFlags,
                         NORMALIZE_METHOD eNormalizeMethod,
                         int nNumPixels) {

  // "Fixed" normalization mode just normalizes by the maximum
  // input value, which for 8-bit images is 255.0
  if (eNormalizeMethod == NORMALIZE_METHOD_FIXED) {
    // We will be adding one to all of them later.
    nStatPosGrand = 255;
    nStatNegGrand = -nStatPosGrand;
  }
  // If we are performing 'mean' operations, then 
  // we need to divide by the total number of pixels
  else if (nStatFlags & STATS_MEAN) {
    if (nNumPixels) {
      nStatPosGrand /= nNumPixels;
      nStatNegGrand /= nNumPixels;
    }
  }
  // Otherwise, downshift by 12 bits to account for
  // the fact that we are doing fixed-precision integer
  // math using a scaling factor of 4096
  else {
    nStatPosGrand >>= GABOR_SCALING_SHIFT;
    nStatNegGrand >>= GABOR_SCALING_SHIFT;
  }
}


// FUNCTION: _doConvolution_alpha()
// 1. Convolve integerized input image (in bufferIn) against
//    each filter in gabor filter bank, storing the result
//    (in integer32) in the output buffers.
// 2. While performing convolution, keeps track of the
//    neccessary statistics for use in normalization
//    during Pass II.
// For case where valid alpha is provided instead of valid box.
void _doConvolution_alpha( const NUMPY_ARRAY * psBufferIn, 
                          const NUMPY_ARRAY * psBufferOut,
                          const NUMPY_ARRAY * psGaborBank, 
                          const NUMPY_ARRAY * psAlpha, 
                          const BBOX * psInputBox,
                          const BBOX * psOutputBox,
                          PHASE_MODE ePhaseMode, 
                          NORMALIZE_METHOD eNormalizeMethod, 
                          NORMALIZE_MODE eNormalizeMode,
                          unsigned int anStatPosGrand[],
                          unsigned int anStatNegGrand[] ) {
  int i, j, jj;
  int nFilterIndex;
  int nResponse;
  int nNumPixels = 0;
  const int * pnInput = NULL;
  const int * pnInputRow = NULL;
  const int * pnInputPtr = NULL;
  const int * pnGaborPtr = NULL;
  const float * pfAlpha = NULL;
  const float * pfAlphaRow = NULL;
  const float * pfAlphaRowPtr = NULL;
  int * pnOutputRow = NULL;

  // Decide which statistics to keep.
  // There are four cases:
  //  1. Record max response in single-phase mode.
  //     To do this, we need to keep track of the maximum
  //     absolute value response.
  //  2. Record max response in dual-phase mode.
  //     For this, we need to keep track of the maximum
  //     and minimum response.  At the end of the processing
  //     cycle, we will do a sanity check to make sure that
  //     something crazy didn't happen, like the minimum
  //     response was positive, or vice versa.
  //  3. Record mean response in single-phase mode.
  //     For this, we need to accummulate the sume of 
  //     the absolute values of the responses.
  //  4. Record mean response in dual-phase mode.
  //     For this, we need to keep the sum of all
  //     negative responses as well as (independently)
  //     the sum of all positive responses.
  // We will use "generalized" variables to keep track
  // of the positive and negative (if dual phase) running
  // statistics.
  // Note also: for the summed values, we'll use a pair of
  // row-wise accummulators, as well as a pair of grand
  // accummulators (in order to avoid overflow issues.)
  int nStatPosGrand, nStatNegGrand;
  int nStatPosRow, nStatNegRow;
  unsigned int nStatFlags = STATS_NONE;
  switch (eNormalizeMethod) {
  // Max-based normalization
  case NORMALIZE_METHOD_MAX:
  case NORMALIZE_METHOD_MAXPOWER:
    if (ePhaseMode == PHASE_MODE_SINGLE)
      nStatFlags |= STATS_MAX_ABS;
    else {
      NTA_ASSERT(ePhaseMode == PHASE_MODE_DUAL);
      nStatFlags |= STATS_MAX_MIN;
    }
    break;
  // Mean-based normalization
  case NORMALIZE_METHOD_MEAN:
  case NORMALIZE_METHOD_MEANPOWER:
    if (ePhaseMode == PHASE_MODE_SINGLE)
      nStatFlags |= STATS_SUM_ABS;
    else {
      NTA_ASSERT(ePhaseMode == PHASE_MODE_DUAL);
      nStatFlags |= STATS_SUM_POS_NEG;
    }
    // We'll need to know the total number of pixels
    nNumPixels = 0;
    //nNumPixels = (psOutputBox->nRight - psOutputBox->nLeft) * (psOutputBox->nBottom - psOutputBox->nTop);
    //if (eNormalizeMode == NORMALIZE_MODE_GLOBAL)
    //  nNumPixels *= GABORSET_PLANES(psGaborBank);
    break;
  // No normalization needed
  case NORMALIZE_METHOD_FIXED:
    break;
  // This case should never happen
  default:
    NTA_ASSERT(false);
  }

  // Ascertain size of gabor filter mask
  NTA_ASSERT(IMAGESET_ROWS(psGaborBank) == IMAGESET_COLS(psGaborBank));
  int nFilterDim = IMAGESET_ROWS(psGaborBank);

  // We might be in constrained mode, in which case we need to
  // map our alpha locations (organized in input space) into
  // our response locations (organized in output space).
  // The shrinkage values (in X and Y dimensions) allow us to
  // convert from input space to output space:
  //    outputX = inputX - nShrinkageX
  //    outputY = inputY - nShrinkageY
  // For sweep-off mode, the shrinkages will be zero.
  int nShrinkageX = (psInputBox->nRight - psOutputBox->nRight) >> 1;
  int nShrinkageY = (psInputBox->nBottom - psOutputBox->nBottom) >> 1;

  // Locate start of correct Gabor filter
  const int * pnFilterBase = (const int *)psGaborBank->pData;

  // Locate start of correct output plane
  int * pnOutputBase = (int *)psBufferOut->pData;
  int nOutputRowStride = IMAGESET_ROWSTRIDE(psBufferOut) / sizeof(*pnOutputBase);

  // Guard against buffer over-runs
#ifdef DEBUG
  // Start/end of memory
  const char * pDebugOutputSOMB = (const char*)(psBufferOut->pData);
  const char * pDebugOutputEOMB = pDebugOutputSOMB + IMAGESET_PLANESTRIDE(psBufferOut) * IMAGESET_PLANES(psBufferOut);
#endif // DEBUG

  // Locate the start of input plane
  const int * pnInputBase = (const int *)psBufferIn->pData;
  int nInputRowStride = IMAGE_ROWSTRIDE(psBufferIn) / sizeof(*pnInputBase);
  int nInputRowAdvance = nInputRowStride - nFilterDim;

  // Locate the start of alpha plane
  const float * pfAlphaBase = (const float *)psAlpha->pData;
  int nAlphaRowStride = IMAGE_ROWSTRIDE(psAlpha) / sizeof(*pfAlphaBase);

  // Take into account bounding box suppression
  int nOutputRows = (psOutputBox->nBottom - psOutputBox->nTop);
  int nOutputCols = (psOutputBox->nRight - psOutputBox->nLeft);

  // Our output buffers should be 4-pixel aligned
  NTA_ASSERT(IMAGESET_COLS(psBufferOut) % 4 == 0);

  // Pre-compute some calculations
  int nNumBlankTopRows = psOutputBox->nTop;

  // Initialize stats
  nStatPosGrand = 0;
  nStatNegGrand = 0;

  for (nFilterIndex=0; nFilterIndex<GABORSET_PLANES(psGaborBank); nFilterIndex++) {

    // Initialize stats
    if (eNormalizeMode == NORMALIZE_MODE_PERORIENT) {
      nStatPosGrand = 0;
      nStatNegGrand = 0;
    }

    // Advance to beginning of our useful input
    pnInput = pnInputBase + nInputRowStride * psInputBox->nTop + psInputBox->nLeft;

    // Process each plane of output
    const int * pnFilter = pnFilterBase;
    int * pnOutput = pnOutputBase;

    // Zero out any rows above the bounding box
    pnOutput += nNumBlankTopRows * nOutputRowStride;

    // Advance to beginning of our alpha channel
    pfAlpha = pfAlphaBase + (nNumBlankTopRows + nShrinkageY) * nAlphaRowStride;

    // Process each row within the bounding box (vertically)
    for (j=nOutputRows; j; j--) {

      // Initialize row-wise accummulator
      nStatPosRow = 0;
      nStatNegRow = 0;

      // Process this ouput row, one output location at a time
      pnInputRow = pnInput;

      // Skip any pixels on this row that lie on left side of bounding box
      pnOutputRow = pnOutput + psOutputBox->nLeft;

      // Alpha 
      pfAlphaRow = pfAlpha + (psOutputBox->nLeft + nShrinkageX);

      // We'll need to know the total number of pixels if we
      // are using a mean-based normalization.  This can be
      // determined on the first pass through the source
      // image (i.e., when generating the response to the
      // first gabor filter.)
      if (nFilterIndex == 0  &&  
           (eNormalizeMethod == NORMALIZE_METHOD_MEAN  ||
            eNormalizeMethod == NORMALIZE_METHOD_MEANPOWER)  &&
          eNormalizeMode == NORMALIZE_MODE_GLOBAL) {
        // Quickly run across the alpha channel to check how
        // many positive pixels it has in this row.
        pfAlphaRowPtr = pfAlphaRow;
        for (i=nOutputCols; i; i--) {
          if (*pfAlphaRowPtr++)
            nNumPixels ++;
        }
      }

      // Unrolled loops; instead of doing this:
      //
      //  for (ii=nFilterDim; ii; ii--)
      //    nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
      //
      // We'll just hard-code the operations
      switch (nFilterDim) {

      // Filter: 5x5
      case 5:
        for (i=nOutputCols; i; i--) {
          // Process each row in the filter mask
          pnGaborPtr = pnFilter;
          pnInputPtr = pnInputRow;

          // Compute gabor response for this location
          nResponse = 0;

          // Only generate a response if the output point
          // lies within our valid alpha channel.
          if (*pfAlphaRow++) {

            for (jj=nFilterDim; jj; jj--) {

              // First 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              // Second 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              pnInputPtr += nInputRowAdvance;
            }

            // Keep statistics for normalization
            if (nStatFlags & STATS_MAX_ABS)
              nStatPosGrand = MAX(nStatPosGrand, IABS32(nResponse));
            else if (nStatFlags & STATS_MAX_MIN) {
              if (nResponse >= 0)
                nStatPosGrand = MAX(nStatPosGrand, nResponse);
              else
                nStatNegGrand = MIN(nStatNegGrand, nResponse);
            }
            else if (nStatFlags & STATS_SUM_ABS)
              nStatPosRow += IABS32(nResponse);
            else if (nStatFlags & STATS_SUM_POS_NEG) {
              if (nResponse >= 0)
                nStatPosRow += nResponse;
              else
                nStatNegRow -= nResponse;
            }
          }

          // Memory bounds checking
#ifdef DEBUG
          NTA_ASSERT((const char*)pnOutputRow >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pnOutputRow <  pDebugOutputEOMB);
#endif // DEBUG

          // Apply abs() and clipping, and then advance to next location
          // Note: our gabor filter masks were pre-scaled by shifting
          // 12 bits to the left, so we'll reverse that.
          *pnOutputRow++ = nResponse;

          // Move the upper-left corner of our gabor receptive field
          // to the next neighboring pixel in image space.
          pnInputRow++;
        }
        break;

      // Filter: 7x7
      case 7:
        for (i=nOutputCols; i; i--) {
          // Process each row in the filter mask
          pnGaborPtr = pnFilter;
          pnInputPtr = pnInputRow;

          // Compute gabor response for this location
          nResponse = 0;

          // Only generate a response if the output point
          // lies within our valid alpha channel.
          if (*pfAlphaRow++) {

            for (jj=nFilterDim; jj; jj--) {

              // First 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              // Second 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              pnInputPtr += nInputRowAdvance;
            }

            // Keep statistics for normalization
            if (nStatFlags & STATS_MAX_ABS)
              nStatPosGrand = MAX(nStatPosGrand, IABS32(nResponse));
            else if (nStatFlags & STATS_MAX_MIN) {
              if (nResponse >= 0)
                nStatPosGrand = MAX(nStatPosGrand, nResponse);
              else
                nStatNegGrand = MIN(nStatNegGrand, nResponse);
            }
            else if (nStatFlags & STATS_SUM_ABS)
              nStatPosRow += IABS32(nResponse);
            else if (nStatFlags & STATS_SUM_POS_NEG) {
              if (nResponse >= 0)
                nStatPosRow += nResponse;
              else
                nStatNegRow -= nResponse;
            }
          }

          // Memory bounds checking
#ifdef DEBUG
          NTA_ASSERT((const char*)pnOutputRow >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pnOutputRow <  pDebugOutputEOMB);
#endif // DEBUG

          // Apply abs() and clipping, and then advance to next location
          // Note: our gabor filter masks were pre-scaled by shifting
          // 12 bits to the left, so we'll reverse that.
          *pnOutputRow++ = nResponse;

          // Move the upper-left corner of our gabor receptive field
          // to the next neighboring pixel in image space.
          pnInputRow++;
        }
        break;

      // Filter: 9x9
      case 9:
        for (i=nOutputCols; i; i--) {
          // Process each row in the filter mask
          pnGaborPtr = pnFilter;
          pnInputPtr = pnInputRow;

          // Compute gabor response for this location
          nResponse = 0;

          // Only generate a response if the output point
          // lies within our valid alpha channel.
          if (*pfAlphaRow++) {

            for (jj=nFilterDim; jj; jj--) {

              // First 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              // Second 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              // Third 128-bits (when we convert to SSE2 we'll
              // do a 12th position - after making sure to pad
              // things in advance to avoid a buffer overflow.)
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              pnInputPtr += nInputRowAdvance;
            }

            // Keep statistics for normalization
            if (nStatFlags & STATS_MAX_ABS)
              nStatPosGrand = MAX(nStatPosGrand, IABS32(nResponse));
            else if (nStatFlags & STATS_MAX_MIN) {
              if (nResponse >= 0)
                nStatPosGrand = MAX(nStatPosGrand, nResponse);
              else
                nStatNegGrand = MIN(nStatNegGrand, nResponse);
            }
            else if (nStatFlags & STATS_SUM_ABS)
              nStatPosRow += IABS32(nResponse);
            else if (nStatFlags & STATS_SUM_POS_NEG) {
              if (nResponse >= 0)
                nStatPosRow += nResponse;
              else
                nStatNegRow -= nResponse;
            }
          }

          // Memory bounds checking
#ifdef DEBUG
          NTA_ASSERT((const char*)pnOutputRow >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pnOutputRow <  pDebugOutputEOMB);
#endif // DEBUG

          // Apply abs() and clipping, and then advance to next location
          // Note: our gabor filter masks were pre-scaled by shifting
          // 12 bits to the left, so we'll reverse that.
          *pnOutputRow++ = nResponse;

          // Move the upper-left corner of our gabor receptive field
          // to the next neighboring pixel in image space.
          pnInputRow++;
        }
        break;

      // Filter: 11x11
      case 11:
        for (i=nOutputCols; i; i--) {
          // Process each row in the filter mask
          pnGaborPtr = pnFilter;
          pnInputPtr = pnInputRow;

          // Compute gabor response for this location
          nResponse = 0;

          // Only generate a response if the output point
          // lies within our valid alpha channel.
          if (*pfAlphaRow++) {

            for (jj=nFilterDim; jj; jj--) {

              // First 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              // Second 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              // Third 128-bits (when we convert to SSE2 we'll
              // do a 12th position - after making sure to pad
              // things in advance to avoid a buffer overflow.)
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              pnInputPtr += nInputRowAdvance;
            }

            // Keep statistics for normalization
            if (nStatFlags & STATS_MAX_ABS)
              nStatPosGrand = MAX(nStatPosGrand, IABS32(nResponse));
            else if (nStatFlags & STATS_MAX_MIN) {
              if (nResponse >= 0)
                nStatPosGrand = MAX(nStatPosGrand, nResponse);
              else
                nStatNegGrand = MIN(nStatNegGrand, nResponse);
            }
            else if (nStatFlags & STATS_SUM_ABS)
              nStatPosRow += IABS32(nResponse);
            else if (nStatFlags & STATS_SUM_POS_NEG) {
              if (nResponse >= 0)
                nStatPosRow += nResponse;
              else
                nStatNegRow -= nResponse;
            }
          }

          // Memory bounds checking
#ifdef DEBUG
          NTA_ASSERT((const char*)pnOutputRow >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pnOutputRow <  pDebugOutputEOMB);
#endif // DEBUG

          // Apply abs() and clipping, and then advance to next location
          // Note: our gabor filter masks were pre-scaled by shifting
          // 12 bits to the left, so we'll reverse that.
          *pnOutputRow++ = nResponse;

          // Move the upper-left corner of our gabor receptive field
          // to the next neighboring pixel in image space.
          pnInputRow++;
        }
        break;

      // Filter: 13x13
      case 13:
        for (i=nOutputCols; i; i--) {
          // Process each row in the filter mask
          pnGaborPtr = pnFilter;
          pnInputPtr = pnInputRow;

          // Compute gabor response for this location
          nResponse = 0;

          // Only generate a response if the output point
          // lies within our valid alpha channel.
          if (*pfAlphaRow++) {

            for (jj=nFilterDim; jj; jj--) {

              // First 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              // Second 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              // Third 128-bits
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              // Fourth 128-bits (when we convert to SSE2 we'll
              // do a 12th position - after making sure to pad
              // things in advance to avoid a buffer overflow.)
              nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

              pnInputPtr += nInputRowAdvance;
            }

            // Keep statistics for normalization
            if (nStatFlags & STATS_MAX_ABS)
              nStatPosGrand = MAX(nStatPosGrand, IABS32(nResponse));
            else if (nStatFlags & STATS_MAX_MIN) {
              if (nResponse >= 0)
                nStatPosGrand = MAX(nStatPosGrand, nResponse);
              else
                nStatNegGrand = MIN(nStatNegGrand, nResponse);
            }
            else if (nStatFlags & STATS_SUM_ABS)
              nStatPosRow += IABS32(nResponse);
            else if (nStatFlags & STATS_SUM_POS_NEG) {
              if (nResponse >= 0)
                nStatPosRow += nResponse;
              else
                nStatNegRow -= nResponse;
            }
          }

          // Memory bounds checking
#ifdef DEBUG
          NTA_ASSERT((const char*)pnOutputRow >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pnOutputRow <  pDebugOutputEOMB);
#endif // DEBUG

          // Apply abs() and clipping, and then advance to next location
          // Note: our gabor filter masks were pre-scaled by shifting
          // 12 bits to the left, so we'll reverse that.
          *pnOutputRow++ = nResponse;

          // Move the upper-left corner of our gabor receptive field
          // to the next neighboring pixel in image space.
          pnInputRow++;
        }
        break;
      }

      // Accummulate our summing stats.
      // We'll rightshift by 8 bits to keep things from overflowing.
      // We'll also flip the sign of the negative accummulator
      if (nStatFlags & STATS_MEAN) {
        nStatPosGrand += (nStatPosRow >> 8);
        nStatNegGrand += ((-nStatNegRow) >> 8);
      }

      // Advance to next rows
      pnInput += nInputRowStride;
      pnOutput += nOutputRowStride;
      pfAlpha += nAlphaRowStride;
    }

    // Advance to correct plane for gabor filter and output buffer
    pnFilterBase += IMAGESET_PLANESTRIDE(psGaborBank) / sizeof(*pnFilter);
    pnOutputBase += IMAGESET_PLANESTRIDE(psBufferOut) / sizeof(*pnOutput);

    // If we are storing statistics on a per-filter basis,
    // then we need to dump our stats to the buffer
    if (eNormalizeMode == NORMALIZE_MODE_PERORIENT) {

      // Compute final values of the normalizers to use
      _computeNormalizers(nStatPosGrand, 
                          nStatNegGrand, 
                          nStatFlags,
                          eNormalizeMethod,
                          nNumPixels);

      NTA_ASSERT(nStatPosGrand >= 0); 
      anStatPosGrand[nFilterIndex] = (unsigned int)(nStatPosGrand + 1);
      // We also need to flip the sign of our negative 
      // max stat if we are in dual phase.
      //if (nStatFlags & STATS_MAX_MIN)
      //  nStatNegGrand = -nStatNegGrand;
      //if (nStatFlags & STATS_DUAL) {
      if (ePhaseMode == PHASE_MODE_DUAL) {
        nStatNegGrand = -nStatNegGrand;
        NTA_ASSERT(nStatNegGrand >= 0); 
        // We add one to the statistical quantity because we want to
        // round up in the case of integer arithmetic round off 
        // errors.  That way (for example) our MAX statistic will
        // be guaranteed to be >= the largest actual value.
        anStatNegGrand[nFilterIndex] = (unsigned int)(nStatNegGrand + 1);
      }

      // Debugging
#ifdef DEBUG
      for (int kk=0; kk<=nFilterIndex; kk++) {
        fprintf(stdout, "[%d]: anStatPosGrand: %d\tanStatNegGrand: %d\n", 
                kk, anStatPosGrand[kk], anStatNegGrand[kk]);
      }
#endif // DEBUG
    }

    // We'll need to know the total number of pixels if we
    // are using a mean-based normalization.  This can be
    // determined on the first pass through the source
    // image (i.e., when generating the response to the
    // first gabor filter.)
    if (nFilterIndex == 0  &&  
         (eNormalizeMethod == NORMALIZE_METHOD_MEAN  ||
          eNormalizeMethod == NORMALIZE_METHOD_MEANPOWER)  &&
        eNormalizeMode == NORMALIZE_MODE_GLOBAL)
      // If using global normalization, then we're summing the
      // responses over all planes, so there will a multiple
      // of positive alpha pixels equal to the number of
      // filter planes.
      nNumPixels *= GABORSET_PLANES(psGaborBank);

  } // for each filter (output plane)

  // If we are storing statistics globally (i.e., not on a 
  // per-filter basis), then we can finally dump our stats 
  // to the buffer.
  if (eNormalizeMode == NORMALIZE_MODE_GLOBAL) {

    // Compute final values of the normalizers to use
    _computeNormalizers(nStatPosGrand, 
                        nStatNegGrand, 
                        nStatFlags,
                        eNormalizeMethod,
                        nNumPixels);

    NTA_ASSERT(nStatPosGrand >= 0); 
    anStatPosGrand[0] = (unsigned int)(nStatPosGrand + 1);
    // We also need to flip the sign of our negative 
    // max stat if we are in dual phase.
    //if (nStatFlags & STATS_MAX_MIN)
    //  nStatNegGrand = -nStatNegGrand;
    //if (nStatFlags & STATS_DUAL) {
    if (ePhaseMode == PHASE_MODE_DUAL) {
      nStatNegGrand = -nStatNegGrand;
      NTA_ASSERT(nStatNegGrand >= 0); 
      anStatNegGrand[0] = (unsigned int)(nStatNegGrand + 1);
    }
  }

  // Debug 
#ifdef DEBUG
  for (int kk=0; kk<1; kk++) {
    fprintf(stdout, "anStatPosGrand[%d]: %d\n", kk, anStatPosGrand[kk]);
    fprintf(stdout, "anStatNegGrand[%d]: %d\n", kk, anStatNegGrand[kk]);
  }
#endif // DEBUG
}




// FUNCTION: _doConvolution_bbox()
// 1. Convolve integerized input image (in bufferIn) against
//    each filter in gabor filter bank, storing the result
//    (in integer32) in the output buffers.
// 2. While performing convolution, keeps track of the
//    neccessary statistics for use in normalization
//    during Pass II.
// For case where valid box is provided instead of valid
// alpha channel.
void _doConvolution_bbox( const NUMPY_ARRAY * psBufferIn, 
                          const NUMPY_ARRAY * psBufferOut,
                          const NUMPY_ARRAY * psGaborBank, 
                          const BBOX * psInputBox,
                          const BBOX * psOutputBox,
                          PHASE_MODE ePhaseMode, 
                          NORMALIZE_METHOD eNormalizeMethod, 
                          NORMALIZE_MODE eNormalizeMode,
                          unsigned int anStatPosGrand[],
                          unsigned int anStatNegGrand[] ) {
  int i, j, jj;
  int nFilterIndex;
  int nResponse;
  int nNumPixels = 0;
  const int * pnInput = NULL;
  const int * pnInputRow = NULL;
  const int * pnInputPtr = NULL;
  const int * pnGaborPtr = NULL;
  int * pnOutputRow = NULL;

  // Decide which statistics to keep.
  // There are four cases:
  //  1. Record max response in single-phase mode.
  //     To do this, we need to keep track of the maximum
  //     absolute value response.
  //  2. Record max response in dual-phase mode.
  //     For this, we need to keep track of the maximum
  //     and minimum response.  At the end of the processing
  //     cycle, we will do a sanity check to make sure that
  //     something crazy didn't happen, like the minimum
  //     response was positive, or vice versa.
  //  3. Record mean response in single-phase mode.
  //     For this, we need to accummulate the sume of 
  //     the absolute values of the responses.
  //  4. Record mean response in dual-phase mode.
  //     For this, we need to keep the sum of all
  //     negative responses as well as (independently)
  //     the sum of all positive responses.
  // We will use "generalized" variables to keep track
  // of the positive and negative (if dual phase) running
  // statistics.
  // Note also: for the summed values, we'll use a pair of
  // row-wise accummulators, as well as a pair of grand
  // accummulators (in order to avoid overflow issues.)
  int nStatPosGrand, nStatNegGrand;
  int nStatPosRow, nStatNegRow;
  unsigned int nStatFlags = STATS_NONE;
  switch (eNormalizeMethod) {
  // Max-based normalization
  case NORMALIZE_METHOD_MAX:
  case NORMALIZE_METHOD_MAXPOWER:
    if (ePhaseMode == PHASE_MODE_SINGLE)
      nStatFlags |= STATS_MAX_ABS;
    else {
      NTA_ASSERT(ePhaseMode == PHASE_MODE_DUAL);
      nStatFlags |= STATS_MAX_MIN;
    }
    break;
  // Mean-based normalization
  case NORMALIZE_METHOD_MEAN:
  case NORMALIZE_METHOD_MEANPOWER:
    if (ePhaseMode == PHASE_MODE_SINGLE)
      nStatFlags |= STATS_SUM_ABS;
    else {
      NTA_ASSERT(ePhaseMode == PHASE_MODE_DUAL);
      nStatFlags |= STATS_SUM_POS_NEG;
    }
    // We'll need to know the total number of pixels
    nNumPixels = (psOutputBox->nRight - psOutputBox->nLeft) * (psOutputBox->nBottom - psOutputBox->nTop);
    if (eNormalizeMode == NORMALIZE_MODE_GLOBAL)
      nNumPixels *= GABORSET_PLANES(psGaborBank);
    break;
  // No normalization needed
  case NORMALIZE_METHOD_FIXED:
    break;
  // This case should never happen
  default:
    NTA_ASSERT(false);
  }

  // Ascertain size of gabor filter mask
  NTA_ASSERT(IMAGESET_ROWS(psGaborBank) == IMAGESET_COLS(psGaborBank));
  int nFilterDim = IMAGESET_ROWS(psGaborBank);

  // Locate start of correct Gabor filter
  const int * pnFilterBase = (const int *)psGaborBank->pData;

  // Locate start of correct output plane
  int * pnOutputBase = (int *)psBufferOut->pData;
  int nOutputRowStride = IMAGESET_ROWSTRIDE(psBufferOut) / sizeof(*pnOutputBase);

  // Guard against buffer over-runs
#ifdef DEBUG
  // Start/end of memory
  const char * pDebugOutputSOMB = (const char*)(psBufferOut->pData);
  const char * pDebugOutputEOMB = pDebugOutputSOMB + IMAGESET_PLANESTRIDE(psBufferOut) * IMAGESET_PLANES(psBufferOut);
#endif // DEBUG

  // Locate the start of input plane
  const int * pnInputBase = (const int *)psBufferIn->pData;
  int nInputRowStride = IMAGE_ROWSTRIDE(psBufferIn) / sizeof(*pnInputBase);
  int nInputRowAdvance = nInputRowStride - nFilterDim;

  // Take into account bounding box suppression
  int nOutputRows = (psOutputBox->nBottom - psOutputBox->nTop);
  int nOutputCols = (psOutputBox->nRight - psOutputBox->nLeft);

  // Our output buffers should be 4-pixel aligned
  NTA_ASSERT(IMAGESET_COLS(psBufferOut) % 4 == 0);

  // Pre-compute some calculations
  int nNumBlankTopRows = psOutputBox->nTop;

  // Initialize stats
  nStatPosGrand = 0;
  nStatNegGrand = 0;

  for (nFilterIndex=0; nFilterIndex<GABORSET_PLANES(psGaborBank); nFilterIndex++) {

    // Initialize stats
    if (eNormalizeMode == NORMALIZE_MODE_PERORIENT) {
      nStatPosGrand = 0;
      nStatNegGrand = 0;
    }

    // Advance to beginning of our useful input
    pnInput = pnInputBase + nInputRowStride * psInputBox->nTop + psInputBox->nLeft;

    // Process each plane of output
    const int * pnFilter = pnFilterBase;
    int * pnOutput = pnOutputBase;

    // Zero out any rows above the bounding box
    pnOutput += nNumBlankTopRows * nOutputRowStride;

    // Process each row within the bounding box (vertically)
    for (j=nOutputRows; j; j--) {
      pnOutputRow = pnOutput;

      // Initialize row-wise accummulator
      nStatPosRow = 0;
      nStatNegRow = 0;

      // Skip any pixels on this row that lie on left side of bounding box
      pnOutputRow += psOutputBox->nLeft;

      // Process this ouput row, one output location at a time
      pnInputRow = pnInput;

      // Unrolled loops; instead of doing this:
      //
      //  for (ii=nFilterDim; ii; ii--)
      //    nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
      //
      // We'll just hard-code the operations
      switch (nFilterDim) {

      // Filter: 5x5
      case 5:
        for (i=nOutputCols; i; i--) {
          // Process each row in the filter mask
          pnGaborPtr = pnFilter;
          pnInputPtr = pnInputRow;

          // Compute gabor response for this location
          nResponse = 0;
          for (jj=nFilterDim; jj; jj--) {

            // First 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            // Second 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            pnInputPtr += nInputRowAdvance;
          }

          // Keep statistics for normalization
          if (nStatFlags & STATS_MAX_ABS)
            nStatPosGrand = MAX(nStatPosGrand, IABS32(nResponse));
          else if (nStatFlags & STATS_MAX_MIN) {
            if (nResponse >= 0)
              nStatPosGrand = MAX(nStatPosGrand, nResponse);
            else
              nStatNegGrand = MIN(nStatNegGrand, nResponse);
          }
          else if (nStatFlags & STATS_SUM_ABS)
            nStatPosRow += IABS32(nResponse);
          else if (nStatFlags & STATS_SUM_POS_NEG) {
            if (nResponse >= 0)
              nStatPosRow += nResponse;
            else
              nStatNegRow -= nResponse;
          }

          // Memory bounds checking
#ifdef DEBUG
          NTA_ASSERT((const char*)pnOutputRow >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pnOutputRow <  pDebugOutputEOMB);
#endif // DEBUG

          // Apply abs() and clipping, and then advance to next location
          // Note: our gabor filter masks were pre-scaled by shifting
          // 12 bits to the left, so we'll reverse that.
          *pnOutputRow++ = nResponse;

          // Move the upper-left corner of our gabor receptive field
          // to the next neighboring pixel in image space.
          pnInputRow++;
        }
        break;

      // Filter: 7x7
      case 7:
        for (i=nOutputCols; i; i--) {
          // Process each row in the filter mask
          pnGaborPtr = pnFilter;
          pnInputPtr = pnInputRow;

          // Compute gabor response for this location
          nResponse = 0;
          for (jj=nFilterDim; jj; jj--) {

            // First 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            // Second 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            pnInputPtr += nInputRowAdvance;
          }

          // Keep statistics for normalization
          if (nStatFlags & STATS_MAX_ABS)
            nStatPosGrand = MAX(nStatPosGrand, IABS32(nResponse));
          else if (nStatFlags & STATS_MAX_MIN) {
            if (nResponse >= 0)
              nStatPosGrand = MAX(nStatPosGrand, nResponse);
            else
              nStatNegGrand = MIN(nStatNegGrand, nResponse);
          }
          else if (nStatFlags & STATS_SUM_ABS)
            nStatPosRow += IABS32(nResponse);
          else if (nStatFlags & STATS_SUM_POS_NEG) {
            if (nResponse >= 0)
              nStatPosRow += nResponse;
            else
              nStatNegRow -= nResponse;
          }

          // Memory bounds checking
#ifdef DEBUG
          NTA_ASSERT((const char*)pnOutputRow >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pnOutputRow <  pDebugOutputEOMB);
#endif // DEBUG

          // Apply abs() and clipping, and then advance to next location
          // Note: our gabor filter masks were pre-scaled by shifting
          // 12 bits to the left, so we'll reverse that.
          *pnOutputRow++ = nResponse;

          // Move the upper-left corner of our gabor receptive field
          // to the next neighboring pixel in image space.
          pnInputRow++;
        }
        break;

      // Filter: 9x9
      case 9:
        for (i=nOutputCols; i; i--) {
          // Process each row in the filter mask
          pnGaborPtr = pnFilter;
          pnInputPtr = pnInputRow;

          // Compute gabor response for this location
          nResponse = 0;
          for (jj=nFilterDim; jj; jj--) {

            // First 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            // Second 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            // Third 128-bits (when we convert to SSE2 we'll
            // do a 12th position - after making sure to pad
            // things in advance to avoid a buffer overflow.)
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            pnInputPtr += nInputRowAdvance;
          }

          // Keep statistics for normalization
          if (nStatFlags & STATS_MAX_ABS)
            nStatPosGrand = MAX(nStatPosGrand, IABS32(nResponse));
          else if (nStatFlags & STATS_MAX_MIN) {
            if (nResponse >= 0)
              nStatPosGrand = MAX(nStatPosGrand, nResponse);
            else
              nStatNegGrand = MIN(nStatNegGrand, nResponse);
          }
          else if (nStatFlags & STATS_SUM_ABS)
            nStatPosRow += IABS32(nResponse);
          else if (nStatFlags & STATS_SUM_POS_NEG) {
            if (nResponse >= 0)
              nStatPosRow += nResponse;
            else
              nStatNegRow -= nResponse;
          }

          // Memory bounds checking
#ifdef DEBUG
          NTA_ASSERT((const char*)pnOutputRow >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pnOutputRow <  pDebugOutputEOMB);
#endif // DEBUG

          // Apply abs() and clipping, and then advance to next location
          // Note: our gabor filter masks were pre-scaled by shifting
          // 12 bits to the left, so we'll reverse that.
          *pnOutputRow++ = nResponse;

          // Move the upper-left corner of our gabor receptive field
          // to the next neighboring pixel in image space.
          pnInputRow++;
        }
        break;

      // Filter: 11x11
      case 11:
        for (i=nOutputCols; i; i--) {
          // Process each row in the filter mask
          pnGaborPtr = pnFilter;
          pnInputPtr = pnInputRow;

          // Compute gabor response for this location
          nResponse = 0;
          for (jj=nFilterDim; jj; jj--) {

            // First 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            // Second 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            // Third 128-bits (when we convert to SSE2 we'll
            // do a 12th position - after making sure to pad
            // things in advance to avoid a buffer overflow.)
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            pnInputPtr += nInputRowAdvance;
          }

          // Keep statistics for normalization
          if (nStatFlags & STATS_MAX_ABS)
            nStatPosGrand = MAX(nStatPosGrand, IABS32(nResponse));
          else if (nStatFlags & STATS_MAX_MIN) {
            if (nResponse >= 0)
              nStatPosGrand = MAX(nStatPosGrand, nResponse);
            else
              nStatNegGrand = MIN(nStatNegGrand, nResponse);
          }
          else if (nStatFlags & STATS_SUM_ABS)
            nStatPosRow += IABS32(nResponse);
          else if (nStatFlags & STATS_SUM_POS_NEG) {
            if (nResponse >= 0)
              nStatPosRow += nResponse;
            else
              nStatNegRow -= nResponse;
          }

          // Memory bounds checking
#ifdef DEBUG
          NTA_ASSERT((const char*)pnOutputRow >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pnOutputRow <  pDebugOutputEOMB);
#endif // DEBUG

          // Apply abs() and clipping, and then advance to next location
          // Note: our gabor filter masks were pre-scaled by shifting
          // 12 bits to the left, so we'll reverse that.
          *pnOutputRow++ = nResponse;

          // Move the upper-left corner of our gabor receptive field
          // to the next neighboring pixel in image space.
          pnInputRow++;
        }
        break;

      // Filter: 13x13
      case 13:
        for (i=nOutputCols; i; i--) {
          // Process each row in the filter mask
          pnGaborPtr = pnFilter;
          pnInputPtr = pnInputRow;

          // Compute gabor response for this location
          nResponse = 0;
          for (jj=nFilterDim; jj; jj--) {

            // First 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            // Second 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            // Third 128-bits
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            // Fourth 128-bits (when we convert to SSE2 we'll
            // do a 12th position - after making sure to pad
            // things in advance to avoid a buffer overflow.)
            nResponse += (*pnGaborPtr++) * (*pnInputPtr++);

            pnInputPtr += nInputRowAdvance;
          }

          // Keep statistics for normalization
          if (nStatFlags & STATS_MAX_ABS)
            nStatPosGrand = MAX(nStatPosGrand, IABS32(nResponse));
          else if (nStatFlags & STATS_MAX_MIN) {
            if (nResponse >= 0)
              nStatPosGrand = MAX(nStatPosGrand, nResponse);
            else
              nStatNegGrand = MIN(nStatNegGrand, nResponse);
          }
          else if (nStatFlags & STATS_SUM_ABS)
            nStatPosRow += IABS32(nResponse);
          else if (nStatFlags & STATS_SUM_POS_NEG) {
            if (nResponse >= 0)
              nStatPosRow += nResponse;
            else
              nStatNegRow -= nResponse;
          }

          // Memory bounds checking
#ifdef DEBUG
          NTA_ASSERT((const char*)pnOutputRow >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pnOutputRow <  pDebugOutputEOMB);
#endif // DEBUG

          // Apply abs() and clipping, and then advance to next location
          // Note: our gabor filter masks were pre-scaled by shifting
          // 12 bits to the left, so we'll reverse that.
          *pnOutputRow++ = nResponse;

          // Move the upper-left corner of our gabor receptive field
          // to the next neighboring pixel in image space.
          pnInputRow++;
        }
        break;
      }

      // Accummulate our summing stats.
      // We'll rightshift by 8 bits to keep things from overflowing.
      // We'll also flip the sign of the negative accummulator
      if (nStatFlags & STATS_MEAN) {
        nStatPosGrand += (nStatPosRow >> 8);
        nStatNegGrand += ((-nStatNegRow) >> 8);
      }

      // Advance to next rows
      pnInput += nInputRowStride;
      pnOutput += nOutputRowStride;
    }

    // Advance to correct plane for gabor filter and output buffer
    pnFilterBase += IMAGESET_PLANESTRIDE(psGaborBank) / sizeof(*pnFilter);
    pnOutputBase += IMAGESET_PLANESTRIDE(psBufferOut) / sizeof(*pnOutput);

    // If we are storing statistics on a per-filter basis,
    // then we need to dump our stats to the buffer
    if (eNormalizeMode == NORMALIZE_MODE_PERORIENT) {

      // Compute final values of the normalizers to use
      _computeNormalizers(nStatPosGrand, 
                          nStatNegGrand, 
                          nStatFlags,
                          eNormalizeMethod,
                          nNumPixels);

      NTA_ASSERT(nStatPosGrand >= 0); 
      anStatPosGrand[nFilterIndex] = (unsigned int)(nStatPosGrand + 1);
      // We also need to flip the sign of our negative 
      // max stat if we are in dual phase.
      //if (nStatFlags & STATS_MAX_MIN)
      //  nStatNegGrand = -nStatNegGrand;
      //if (nStatFlags & STATS_DUAL) {
      if (ePhaseMode == PHASE_MODE_DUAL) {
        nStatNegGrand = -nStatNegGrand;
        NTA_ASSERT(nStatNegGrand >= 0); 
        // We add one to the statistical quantity because we want to
        // round up in the case of integer arithmetic round off 
        // errors.  That way (for example) our MAX statistic will
        // be guaranteed to be >= the largest actual value.
        anStatNegGrand[nFilterIndex] = (unsigned int)(nStatNegGrand + 1);
      }

      // Debugging
#ifdef DEBUG
      for (int kk=0; kk<=nFilterIndex; kk++) {
        fprintf(stdout, "[%d]: anStatPosGrand: %d\tanStatNegGrand: %d\n", 
                kk, anStatPosGrand[kk], anStatNegGrand[kk]);
      }
#endif // DEBUG
    }
  } // for each filter (output plane)

  // If we are storing statistics globally (i.e., not on a 
  // per-filter basis), then we can finally dump our stats 
  // to the buffer.
  if (eNormalizeMode == NORMALIZE_MODE_GLOBAL) {

    // Compute final values of the normalizers to use
    _computeNormalizers(nStatPosGrand, 
                        nStatNegGrand, 
                        nStatFlags,
                        eNormalizeMethod,
                        nNumPixels);

    NTA_ASSERT(nStatPosGrand >= 0); 
    anStatPosGrand[0] = (unsigned int)(nStatPosGrand + 1);
    // We also need to flip the sign of our negative 
    // max stat if we are in dual phase.
    //if (nStatFlags & STATS_MAX_MIN)
    //  nStatNegGrand = -nStatNegGrand;
    //if (nStatFlags & STATS_DUAL) {
    if (ePhaseMode == PHASE_MODE_DUAL) {
      nStatNegGrand = -nStatNegGrand;
      NTA_ASSERT(nStatNegGrand >= 0); 
      anStatNegGrand[0] = (unsigned int)(nStatNegGrand + 1);
    }
  }

  // Debug 
#ifdef DEBUG
  for (int kk=0; kk<1; kk++) {
    fprintf(stdout, "anStatPosGrand[%d]: %d\n", kk, anStatPosGrand[kk]);
    fprintf(stdout, "anStatNegGrand[%d]: %d\n", kk, anStatNegGrand[kk]);
  }
#endif // DEBUG
}


// FUNCTION: _doConvolution()
// 1. Convolve integerized input image (in bufferIn) against
//    each filter in gabor filter bank, storing the result
//    (in integer32) in the output buffers.
// 2. While performing convolution, keeps track of the
//    neccessary statistics for use in normalization
//    during Pass II.
void _doConvolution( const NUMPY_ARRAY * psBufferIn, 
                     const NUMPY_ARRAY * psBufferOut,
                     const NUMPY_ARRAY * psGaborBank, 
                     const NUMPY_ARRAY * psAlpha, 
                     const BBOX * psInputBox,
                     const BBOX * psOutputBox,
                     PHASE_MODE ePhaseMode, 
                     NORMALIZE_METHOD eNormalizeMethod, 
                     NORMALIZE_MODE eNormalizeMode,
                     unsigned int anStatPosGrand[],
                     unsigned int anStatNegGrand[] ) {

  if (psAlpha)
    _doConvolution_alpha(psBufferIn, 
                         psBufferOut,
                         psGaborBank,
                         psAlpha,
                         psInputBox,
                         psOutputBox,
                         ePhaseMode,
                         eNormalizeMethod,
                         eNormalizeMode,
                         anStatPosGrand,
                         anStatNegGrand);
  else
    _doConvolution_bbox(psBufferIn, 
                        psBufferOut,
                        psGaborBank,
                        psInputBox,
                        psOutputBox,
                        ePhaseMode,
                        eNormalizeMethod,
                        eNormalizeMode,
                        anStatPosGrand,
                        anStatNegGrand);
}


// FUNCTION: _computeGains()
// PURPOSE: Compute the positive (and in the case of dual-phase
// filter banks, the negative as well) gains to use by taking
// into account the normalizing factor.
void _computeGains(float fGain, 
                   unsigned int nStatPosGrand,
                   unsigned int nStatNegGrand,
                   PHASE_MODE ePhaseMode,
                   PHASENORM_MODE ePhaseNormMode,
                   float & fGainPos, 
                   float & fGainNeg) {
  fGainPos = fGain;
  NTA_ASSERT(nStatPosGrand > 0);
  fGainPos /= float(nStatPosGrand);

  // Handle inverted phase plane
  if (ePhaseMode == PHASE_MODE_DUAL) {
    NTA_ASSERT(nStatNegGrand > 0);

    // Each phase is normalized individually
    // using it's own normalizing factor (max or mean)
    if (ePhaseNormMode == PHASENORM_MODE_INDIV)
      fGainNeg = -fGain / float(nStatNegGrand);

    // Both phases are normalized using the same 
    // normalizing factor (max or mean)
    else {
      NTA_ASSERT(ePhaseNormMode == PHASENORM_MODE_COMBO);
      // If the negative phase normalizing constant is
      // bigger than the positive one, then use it
      if (nStatNegGrand > nStatPosGrand) {
        fGainNeg = -fGain / float(nStatNegGrand);
        fGainPos = -fGainNeg;
      }
      else
        fGainNeg = -fGainPos;
      NTA_ASSERT(fGainNeg == -fGainPos);
    }
  }
}


// FUNCTION: _postProcess()
// 1. Perform rectification
// 2. Apply gain (in general, this will be different for each
//    image based on auto-normalization results);
// 3. Apply post-processing method if any;
// 4. Convert from integer 32 to float.
void _postProcess( const NUMPY_ARRAY * psBufferIn, 
                   const NUMPY_ARRAY * psOutput, 
                   //const NUMPY_ARRAY * psBBox,
                   const BBOX * psBox,
                   PHASE_MODE ePhaseMode,
                   int nShrinkage,
                   EDGE_MODE eEdgeMode,
                   float fGainConstant,
                   NORMALIZE_METHOD eNormalizeMethod, 
                   NORMALIZE_MODE eNormalizeMode, 
                   PHASENORM_MODE ePhaseNormMode,
                   POSTPROC_METHOD ePostProcMethod, 
                   float fPostProcSlope, 
                   float fPostProcMidpoint,
                   float fPostProcMin, 
                   float fPostProcMax,
                   const unsigned int anStatPosGrand[],
                   const unsigned int anStatNegGrand[],
                   const NUMPY_ARRAY * psPostProcLUT,
                   float fPostProcScalar) {
  int i, j;
  int nFilterIndex;
  int nResponse;
  float fResponse;
  int nDiscreteGainPos = 0;
  int nDiscreteGainNeg = 0;
  unsigned int nSingleBin;
  int nDualBin;
  float fGain, fGainPos = 0.0f, fGainNeg = 0.0f;
  float * pfOutputRowPos = NULL;
  float * pfOutputRowNeg = NULL;
  float * pfOutputPos = NULL;
  float * pfOutputNeg = NULL;
  int * pnInputRow = NULL;

  // Locate start of first input plane
  int * pnInputBase = (int *)psBufferIn->pData;
  int nInputRowStride = IMAGESET_ROWSTRIDE(psBufferIn) / sizeof(*pnInputBase);

  // Locate start of first output plane
  float * pfOutputBase = (float *)psOutput->pData;
  int nOutputRowStride = IMAGESET_ROWSTRIDE(psOutput) / sizeof(*pfOutputBase);

  // Guard against buffer over-runs
#ifdef DEBUG
  // Start/end of memory
  const char * pDebugOutputSOMB = (const char*)(psOutput->pData);
  const char * pDebugOutputEOMB = pDebugOutputSOMB + IMAGESET_PLANESTRIDE(psOutput) * IMAGESET_PLANES(psOutput);
#endif // DEBUG

  // Take into account bounding box suppression
  int nOutputRows = psBox->nBottom - psBox->nTop;
  int nOutputCols = psBox->nRight - psBox->nLeft;

  // Our output buffers should be 4-pixel aligned
  NTA_ASSERT(IMAGESET_COLS(psBufferIn) % 4 == 0);

  // Pre-compute some calculations
  int nNumBlankTopRows = psBox->nTop;
  int nNumBlankBottomRows = IMAGESET_ROWS(psOutput) - psBox->nBottom;
  int nNumBlankRightCols = IMAGESET_COLS(psOutput) - psBox->nRight;

  // Process four pixels at a time
  int nOutputQuadsPerRow = nOutputCols >> 2;
  int nNumLeftovers = nOutputCols - (nOutputQuadsPerRow << 2);
  int nTotalQuadsPerRow = IMAGESET_COLS(psOutput) >> 2;
  int nTotalLeftovers = IMAGESET_COLS(psOutput) - (nTotalQuadsPerRow << 2);

  // Access the post-processing LUT
  const float * pfPostProcLUT = NULL;
  int nNumLutBins = 0;
  int nMaxLutBin = 0;
  unsigned int nOverflowMask = 0x0;
  if (ePostProcMethod != POSTPROC_METHOD_RAW) {
    pfPostProcLUT = (const float *)psPostProcLUT->pData;
    nNumLutBins = VECTOR_PLANES(psPostProcLUT);

    // If we are in single-phase mode, then we'll 
    // just use the LUT as is
    // If we're in dual-phase mode, then we really
    // have two LUTs, each of which is bi-polar
    // (bins on both sides of zero)
    nMaxLutBin = nNumLutBins - 1;

    // Generate a bit mask that can efficiently detect
    // whether a bin will overflow our LUT (so it can be clipped)
    //unsigned int nOverflowMask = ~(nNumLutBins | nMaxLutBin);
    // We'll use a trick to speed up the inner loop:
    // if we are using a normalization method other
    // than MEAN, then we'll be guaranteed to never
    // overflow our LUT because we can pre-calculate the
    // maximum possible value and built our LUT accordingly;
    // (this is only impossible in the MEAN normalization
    // case.)  So we'll set our 'nOverflowMask' to 0x0
    // in the non-MEAN cases so that it will never detect
    // an overflow bin.
    if (eNormalizeMethod == NORMALIZE_METHOD_MEAN) {
      nOverflowMask = ~nMaxLutBin;
      NTA_ASSERT(nOverflowMask);
    }
  }

  // Pre-compute gain amplification
  fGain = fGainConstant / (float)(0x1 << GABOR_SCALING_SHIFT);

  // If we are using global normalization (not per-orientation) then
  // we compute the final gain once
  if (eNormalizeMode == NORMALIZE_MODE_GLOBAL) {
    _computeGains(fGain, 
                  anStatPosGrand[0],
                  anStatNegGrand[0],
                  ePhaseMode,
                  ePhaseNormMode,
                  fGainPos, 
                  fGainNeg);
  }

  // Process each output plane
  for (nFilterIndex=0; nFilterIndex<IMAGESET_PLANES(psBufferIn); nFilterIndex++) {

    // If we are using global normalization (not per-orientation) then
    // we compute the final gain once
    if (eNormalizeMode == NORMALIZE_MODE_PERORIENT) {
      _computeGains(fGain, 
                    anStatPosGrand[nFilterIndex],
                    anStatNegGrand[nFilterIndex],
                    ePhaseMode,
                    ePhaseNormMode,
                    fGainPos, 
                    fGainNeg);
    }

    // Convert floating point gain to integer
    if (ePostProcMethod != POSTPROC_METHOD_RAW) {
      nDiscreteGainPos = int(1.0f / (fPostProcScalar * fGainPos));
      if (ePhaseMode == PHASE_MODE_DUAL)
        nDiscreteGainNeg = int(1.0f / (fPostProcScalar * fGainNeg));
    }

    // Process each plane of output
    int * pnInput = pnInputBase;
    pfOutputPos = pfOutputBase;
    if (ePhaseMode == PHASE_MODE_DUAL)
      pfOutputNeg = pfOutputPos \
                  + IMAGESET_PLANES(psBufferIn) \
                  * IMAGESET_PLANESTRIDE(psOutput) \
                  / sizeof(*pfOutputBase);

    //------------------------------------------------
    // Zero out any rows above the bounding box
    for (j=nNumBlankTopRows; j; j--) {

      // Single phase
      if (ePhaseMode == PHASE_MODE_SINGLE) {
        pfOutputRowPos = pfOutputPos;
        // Hopefully the compiler will use SIMD for this:
        for (i=nTotalQuadsPerRow; i; i--) {
          pfOutputRowPos[0] = NULL_RESPONSE;
          pfOutputRowPos[1] = NULL_RESPONSE;
          pfOutputRowPos[2] = NULL_RESPONSE;
          pfOutputRowPos[3] = NULL_RESPONSE;
          // Advance pointers
          pfOutputRowPos += 4;
        }
        // Handle any leftovers that don't fit in a quad
        for (i=nTotalLeftovers; i; i--)
          *pfOutputRowPos++ = NULL_RESPONSE;
        // Advance our row pointer(s)
        pfOutputPos += nOutputRowStride;
      } // Single phase

      // Dual phase
      else {
        NTA_ASSERT(ePhaseMode == PHASE_MODE_DUAL);
        pfOutputRowPos = pfOutputPos;
        pfOutputRowNeg = pfOutputNeg;
        // Hopefully the compiler will use SIMD for this:
        for (i=nTotalQuadsPerRow; i; i--) {
          pfOutputRowPos[0] = NULL_RESPONSE;
          pfOutputRowNeg[0] = NULL_RESPONSE;
          pfOutputRowPos[1] = NULL_RESPONSE;
          pfOutputRowNeg[1] = NULL_RESPONSE;
          pfOutputRowPos[2] = NULL_RESPONSE;
          pfOutputRowNeg[2] = NULL_RESPONSE;
          pfOutputRowPos[3] = NULL_RESPONSE;
          pfOutputRowNeg[3] = NULL_RESPONSE;
          // Advance pointers
          pfOutputRowPos += 4;
          pfOutputRowNeg += 4;
        }
        // Handle any leftovers that don't fit in a quad
        for (i=nTotalLeftovers; i; i--) {
          *pfOutputRowPos++ = NULL_RESPONSE;
          *pfOutputRowNeg++ = NULL_RESPONSE;
        }
        // Advance our row pointer(s)
        pfOutputPos += nOutputRowStride;
        pfOutputNeg += nOutputRowStride;
      }  // Dual phase
    }    // for (j=nNumBlankTopRows; j; j--)
    pnInput += nInputRowStride * psBox->nTop;

    //------------------------------------------------
    // Process each row within the bounding box (vertically)
    for (j=nOutputRows; j; j--) {

      // Set up row pointers
      pnInputRow = pnInput;
      pfOutputRowPos = pfOutputPos;
      if (ePhaseMode == PHASE_MODE_DUAL)
        pfOutputRowNeg = pfOutputNeg;

      //------------------------------------------------
      // Fill in zeros outside the bounding box 
      if (ePhaseMode == PHASE_MODE_SINGLE) {
        for (i=psBox->nLeft; i; i--)
          *pfOutputRowPos++ = NULL_RESPONSE;
      }
      else {
        NTA_ASSERT(ePhaseMode == PHASE_MODE_DUAL);
        for (i=psBox->nLeft; i; i--) {
          *pfOutputRowPos++ = NULL_RESPONSE;
          *pfOutputRowNeg++ = NULL_RESPONSE;
          }
      }
      // Skip any rows above the bounding box
      pnInputRow += psBox->nLeft;

      // We'll use two code paths: one for 'single-phase', and
      // one for 'dual-phase'

      //------------------------------------------------
      // Single-phase:
      if (ePhaseMode == PHASE_MODE_SINGLE) {

        // No post-processing to be performed
        if (ePostProcMethod == POSTPROC_METHOD_RAW) {

          // Process this ouput row, one output location at a time
          for (i=nOutputQuadsPerRow; i; i--) {

            // Apply abs() and clipping, and then advance to next location
            // Note: our gabor filter masks were pre-scaled by shifting
            // 12 bits to the left, so we'll reverse that.
            pfOutputRowPos[0] = fGainPos * (float)(IABS32(pnInputRow[0]));

            // Repeat three more times
            pfOutputRowPos[1] = fGainPos * (float)(IABS32(pnInputRow[1]));
            pfOutputRowPos[2] = fGainPos * (float)(IABS32(pnInputRow[2]));
            pfOutputRowPos[3] = fGainPos * (float)(IABS32(pnInputRow[3]));

            // Advance pointers
            pnInputRow += 4;
            pfOutputRowPos += 4;
          }    // for (i=nOutputQuadsPerRow; i; i--)

          // Handle leftovers
          for (i=nNumLeftovers; i; i--) {
            *pfOutputRowPos++ = fGainPos * (float)(IABS32(*pnInputRow));
            pnInputRow ++;
          }     // for (i=nNumLeftovers; i; i--)
        }       // no post-processing

        // Post-processing needed
        else {

          // If we have to worry about overflowing
          // our LUT, then we will follow this code path:
          if (nOverflowMask) {

            // Process this ouput row, four locations at a time
            for (i=nOutputQuadsPerRow; i; i--) {

              // Compute LUT bin to use for looking up post-processed value
              nSingleBin = (unsigned int)(IABS32(*pnInputRow) / nDiscreteGainPos);
              // In 'mean' normalization, the maximum values are essentially
              // unbounded; so we have to clip them to make sure they
              // don't overflow our LUT
              // If our bin will overflow the LUT, then clip
              // it to the largest LUT value.
              if (nSingleBin & nOverflowMask)
                nSingleBin = nMaxLutBin;
              // Apply LUT-based post-processing function
              *pfOutputRowPos = pfPostProcLUT[nSingleBin];

              // Second location
              nSingleBin = (unsigned int)(IABS32(pnInputRow[1]) / nDiscreteGainPos);
              if (nSingleBin & nOverflowMask)
                nSingleBin = nMaxLutBin;
              pfOutputRowPos[1] = pfPostProcLUT[nSingleBin];

              // Third location
              nSingleBin = (unsigned int)(IABS32(pnInputRow[2]) / nDiscreteGainPos);
              if (nSingleBin & nOverflowMask)
                nSingleBin = nMaxLutBin;
              pfOutputRowPos[2] = pfPostProcLUT[nSingleBin];

              // Fourth location
              nSingleBin = (unsigned int)(IABS32(pnInputRow[3]) / nDiscreteGainPos);
              if (nSingleBin & nOverflowMask)
                nSingleBin = nMaxLutBin;
              pfOutputRowPos[3] = pfPostProcLUT[nSingleBin];

              // Sanity checks
              NTA_ASSERT(pfOutputRowPos[0] <= 1.0f);
              NTA_ASSERT(pfOutputRowPos[1] <= 1.0f);
              NTA_ASSERT(pfOutputRowPos[2] <= 1.0f);
              NTA_ASSERT(pfOutputRowPos[3] <= 1.0f);
              NTA_ASSERT(pfOutputRowPos[0] >= 0.0f);
              NTA_ASSERT(pfOutputRowPos[1] >= 0.0f);
              NTA_ASSERT(pfOutputRowPos[2] >= 0.0f);
              NTA_ASSERT(pfOutputRowPos[3] >= 0.0f);

              // Advance pointers
              pnInputRow += 4;
              pfOutputRowPos += 4;
            }   // for (i=nOutputQuadsPerRow; i; i--)

            // Handle leftovers
            for (i=nNumLeftovers; i; i--) {
              // Compute LUT bin to use for looking up post-processed value
              nResponse = *pnInputRow++;
              nSingleBin = (unsigned int)(IABS32(nResponse) / nDiscreteGainPos);
              // In 'mean' normalization, the maximum values are essentially
              // unbounded; so we have to clip them to make sure they
              // don't overflow our LUT
              // If our bin will overflow the LUT, then clip
              // it to the largest LUT value.
              if (nSingleBin & nOverflowMask)
                nSingleBin = nMaxLutBin;
              // Apply LUT-based post-processing function
              *pfOutputRowPos++ = pfPostProcLUT[nSingleBin];
            }       // for (i=nNumLeftovers; i; i--)
          }         // if (nOverflowMask)

          // If we don't have to worry about possibly overflowing
          // our LUT, then we'll go through this faster path:
          else {

            // Process this ouput row, four locations at a time
            for (i=nOutputQuadsPerRow; i; i--) {

              // Memory protection
#ifdef DEBUG
              NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
              NTA_ASSERT((const char*)&(pfOutputRowPos[3]) <  pDebugOutputEOMB);
#endif // DEBUG

              // Compute LUT bin to use for looking up post-processed value
              nSingleBin = (unsigned int)(IABS32(*pnInputRow) / nDiscreteGainPos);
              NTA_ASSERT(nSingleBin <= (unsigned int)nMaxLutBin);
              // Apply LUT-based post-processing function
              *pfOutputRowPos = pfPostProcLUT[nSingleBin];

              // Second location
              nSingleBin = (unsigned int)(IABS32(pnInputRow[1]) / nDiscreteGainPos);
              NTA_ASSERT(nSingleBin <= (unsigned int)nMaxLutBin);
              pfOutputRowPos[1] = pfPostProcLUT[nSingleBin];

              // Third location
              nSingleBin = (unsigned int)(IABS32(pnInputRow[2]) / nDiscreteGainPos);
              NTA_ASSERT(nSingleBin <= (unsigned int)nMaxLutBin);
              pfOutputRowPos[2] = pfPostProcLUT[nSingleBin];

              // Fourth location
              nSingleBin = (unsigned int)(IABS32(pnInputRow[3]) / nDiscreteGainPos);
              NTA_ASSERT(nSingleBin <= (unsigned int)nMaxLutBin);
              pfOutputRowPos[3] = pfPostProcLUT[nSingleBin];

              // Advance pointers
              pnInputRow += 4;
              pfOutputRowPos += 4;
            }   // for (i=nOutputQuadsPerRow; i; i--)

            // Handle leftovers
            for (i=nNumLeftovers; i; i--) {

              // Memory protection
#ifdef DEBUG
              NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
              NTA_ASSERT((const char*)pfOutputRowPos <  pDebugOutputEOMB);
#endif // DEBUG

              // Compute LUT bin to use for looking up post-processed value
              nResponse = *pnInputRow++;
              nSingleBin = (unsigned int)(IABS32(nResponse) / nDiscreteGainPos);
              NTA_ASSERT(nSingleBin <= (unsigned int)nMaxLutBin);
              // Apply LUT-based post-processing function
              *pfOutputRowPos++ = pfPostProcLUT[nSingleBin];
            }     // for (i=nNumLeftovers; i; i--)
          }       // if we don't have an overflow problem to worry about
        }         // Non-raw post-processing needed
      }           // Single-phase
    
      //------------------------------------------------
      // Dual-phases
      else {
        NTA_ASSERT(ePhaseMode == PHASE_MODE_DUAL);

        // No post-processing to be performed
        if (ePostProcMethod == POSTPROC_METHOD_RAW) {

          // Process this ouput row, one output location at a time
          for (i=nOutputQuadsPerRow; i; i--) {

            // Memory protection
#ifdef DEBUG
            NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
            NTA_ASSERT((const char*)pfOutputRowNeg >= pDebugOutputSOMB);
            NTA_ASSERT((const char*)&(pfOutputRowPos[3]) <  pDebugOutputEOMB);
            NTA_ASSERT((const char*)&(pfOutputRowNeg[3]) <  pDebugOutputEOMB);
#endif // DEBUG

            // Generate two responses from one original convolution
            fResponse = (float)(pnInputRow[0]);
            if (fResponse >= 0.0f) {
              *pfOutputRowPos = fResponse * fGainPos;
              *pfOutputRowNeg = 0.0f;
            }
            else {
              *pfOutputRowPos = 0.0f;
              *pfOutputRowNeg = fResponse * fGainNeg;
            }
            // Repeat three more times:

            // Second pixel
            fResponse = (float)(pnInputRow[1]);
            if (fResponse >= 0.0f) {
              pfOutputRowPos[1] = fResponse * fGainPos;
              pfOutputRowNeg[1] = 0.0f;
            }
            else {
              pfOutputRowPos[1] = 0.0f;
              pfOutputRowNeg[1] = fResponse * fGainNeg;
            }
            // Third pixel
            fResponse = (float)(pnInputRow[2]);
            if (fResponse >= 0.0f) {
              pfOutputRowPos[2] = fResponse * fGainPos;
              pfOutputRowNeg[2] = 0.0f;
            }
            else {
              pfOutputRowPos[2] = 0.0f;
              pfOutputRowNeg[2] = fResponse * fGainNeg;
            }
            // Fourth pixel
            fResponse = (float)(pnInputRow[3]);
            if (fResponse >= 0.0f) {
              pfOutputRowPos[3] = fResponse * fGainPos;
              pfOutputRowNeg[3] = 0.0f;
            }
            else {
              pfOutputRowPos[3] = 0.0f;
              pfOutputRowNeg[3] = fResponse * fGainNeg;
            }

            // Advance pointers
            pnInputRow += 4;
            pfOutputRowPos += 4;
            pfOutputRowNeg += 4;
          }

          // Handle leftovers
          for (i=nNumLeftovers; i; i--) {

            // Memory protection
#ifdef DEBUG
            NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
            NTA_ASSERT((const char*)pfOutputRowPos <  pDebugOutputEOMB);
            NTA_ASSERT((const char*)pfOutputRowNeg >= pDebugOutputSOMB);
            NTA_ASSERT((const char*)pfOutputRowNeg <  pDebugOutputEOMB);
#endif // DEBUG

            fResponse = (float)(*pnInputRow++);
            if (fResponse >= 0.0f) {
              *pfOutputRowPos++ = fResponse * fGainPos;
              *pfOutputRowNeg++ = 0.0f;
            }
            else {
              *pfOutputRowPos++ = 0.0f;
              *pfOutputRowNeg++ = fResponse * fGainNeg;
            }
          }     // for (i=nNumLeftovers; i; i--)
        }       // if doing 'raw' post-processing

        // Non-trivial post-processing
        else {

          // If we have to worry about overflowing
          // our LUT, then we will follow this code path:
          if (nOverflowMask) {

            // Process one pixel at a time
            for (i=nOutputCols; i; i--) {

              // Compute discretized response (in terms of the 
              // LUT bin).  This value 'nDualBin' could be positive
              // or negative.
              nDualBin = (*pnInputRow) / nDiscreteGainPos;

              // Memory protection
#ifdef DEBUG
              NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
              NTA_ASSERT((const char*)pfOutputRowPos <  pDebugOutputEOMB);
              NTA_ASSERT((const char*)pfOutputRowNeg >= pDebugOutputSOMB);
              NTA_ASSERT((const char*)pfOutputRowNeg <  pDebugOutputEOMB);
#endif // DEBUG

              // If positive response
              if (nDualBin >= 0) {
                // In 'mean' normalization, the maximum values are essentially
                // unbounded; so we have to clip them to make sure they
                // don't overflow our LUT
                // If our bin will overflow the LUT, then clip
                // it to the largest LUT value.
                if (nDualBin > nMaxLutBin)
                  nDualBin = nMaxLutBin;
                NTA_ASSERT(nDualBin <= nMaxLutBin);
                NTA_ASSERT(nDualBin >= 0);
                *pfOutputRowPos++ = pfPostProcLUT[nDualBin];
                *pfOutputRowNeg++ = 0.0f;

//#ifdef DEBUG
//                // TEMP TEMP TEMP
//                if (pfOutputRowPos[-1] < 0.0f || pfOutputRowPos[-1] > 1.0f)
//                  NTA_ASSERT(false);
//#endif // DEBUG

                // Sanity checks
                NTA_ASSERT(pfOutputRowPos[-1] <= 1.0f);
                NTA_ASSERT(pfOutputRowPos[-1] >= 0.0f);
              }

              // If negative response
              else {
                *pfOutputRowPos++ = 0.0f;
                nDualBin = (*pnInputRow) / nDiscreteGainNeg;
                if (nDualBin > nMaxLutBin)
                  nDualBin = nMaxLutBin;
                NTA_ASSERT(nDualBin <= nMaxLutBin);
                NTA_ASSERT(nDualBin >= 0);
                *pfOutputRowNeg++ = pfPostProcLUT[nDualBin];

//#ifdef DEBUG
//                // TEMP TEMP TEMP
//                if (pfOutputRowNeg[-1] < 0.0f || pfOutputRowNeg[-1] > 1.0f)
//                  NTA_ASSERT(false);
//#endif // DEBUG

                // Sanity checks
                NTA_ASSERT(pfOutputRowNeg[-1] <= 1.0f);
                NTA_ASSERT(pfOutputRowNeg[-1] >= 0.0f);
              }

              // Next input
              pnInputRow++;

            }     // for (i=nOutputQuadsPerRow; i; i--)
          }       // if (nOverflowMask)

          // If we don't have to worry about possibly overflowing
          // our LUT, then we'll go through this faster path:
          else {
            // Process one pixel at a time
            for (i=nOutputCols; i; i--) {

              // Memory protection
#ifdef DEBUG
              NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
              NTA_ASSERT((const char*)pfOutputRowPos <  pDebugOutputEOMB);
              NTA_ASSERT((const char*)pfOutputRowNeg >= pDebugOutputSOMB);
              NTA_ASSERT((const char*)pfOutputRowNeg <  pDebugOutputEOMB);
#endif // DEBUG

              // Compute LUT bin to use for looking up final post-processed value
              nDualBin = (*pnInputRow) / nDiscreteGainPos;
              if (nDualBin >= 0) {
                NTA_ASSERT(nDualBin <= nMaxLutBin);
                *pfOutputRowPos++ = pfPostProcLUT[nDualBin];
                *pfOutputRowNeg++ = 0.0f;
              }
              else {
                *pfOutputRowPos++ = 0.0f;
                nDualBin = (*pnInputRow) / nDiscreteGainNeg;
                NTA_ASSERT(nDualBin <= nMaxLutBin);
                *pfOutputRowNeg++ = pfPostProcLUT[nDualBin];
              }

              // Sanity checks
              NTA_ASSERT(pfOutputRowPos[-1] <= 1.0f);
              NTA_ASSERT(pfOutputRowPos[-1] >= 0.0f);
              NTA_ASSERT(pfOutputRowNeg[-1] <= 1.0f);
              NTA_ASSERT(pfOutputRowNeg[-1] >= 0.0f);

              pnInputRow++;
            }     // for (i=nOutputQuadsPerRow; i; i--)
          }       // if we have no overflow mask to worry about
        }       // non-raw post-processing
      }         // Dual-phase

      //------------------------------------------------
      // Fill in zeros to the right of the bounding box.
      if (ePhaseMode == PHASE_MODE_SINGLE) {
        for (i=nNumBlankRightCols; i; i--) {

          // Memory protection
#ifdef DEBUG
          NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
#endif // DEBUG

          *pfOutputRowPos++ = NULL_RESPONSE;
        }
      }
      else {
        NTA_ASSERT(ePhaseMode == PHASE_MODE_DUAL);
        for (i=nNumBlankRightCols; i; i--) {

          // Memory protection
#ifdef DEBUG
          NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pfOutputRowPos <  pDebugOutputEOMB);
          NTA_ASSERT((const char*)pfOutputRowNeg >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pfOutputRowNeg <  pDebugOutputEOMB);
#endif // DEBUG

          *pfOutputRowPos++ = NULL_RESPONSE;
          *pfOutputRowNeg++ = NULL_RESPONSE;
          }
      }

      // Advance to next rows
      pnInput += nInputRowStride;
      pfOutputPos += nOutputRowStride;
      if (ePhaseMode == PHASE_MODE_DUAL)
        pfOutputNeg += nOutputRowStride;
    }

    //------------------------------------------------
    // Zero out any rows below the bounding box
    for (j=nNumBlankBottomRows; j; j--) {

      // Single phase
      if (ePhaseMode == PHASE_MODE_SINGLE) {
        pfOutputRowPos = pfOutputPos;
        // Hopefully the compiler will use SIMD for this:
        for (i=nTotalQuadsPerRow; i; i--) {

          // Memory protection
#ifdef DEBUG
          NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)&(pfOutputRowPos[3]) <  pDebugOutputEOMB);
#endif // DEBUG

          pfOutputRowPos[0] = NULL_RESPONSE;
          pfOutputRowPos[1] = NULL_RESPONSE;
          pfOutputRowPos[2] = NULL_RESPONSE;
          pfOutputRowPos[3] = NULL_RESPONSE;

          // Advance pointers
          pfOutputRowPos += 4;
        }
        // Handle any leftovers that don't fit in a quad
        for (i=nTotalLeftovers; i; i--) {

          // Memory protection
#ifdef DEBUG
          NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pfOutputRowPos <  pDebugOutputEOMB);
#endif // DEBUG

          *pfOutputRowPos++ = NULL_RESPONSE;
        }

        // Advance our row pointer(s)
        pfOutputPos += nOutputRowStride;
      } // Single phase

      // Dual phase
      else {
        NTA_ASSERT(ePhaseMode == PHASE_MODE_DUAL);
        pfOutputRowPos = pfOutputPos;
        pfOutputRowNeg = pfOutputNeg;
        // Hopefully the compiler will use SIMD for this:
        for (i=nTotalQuadsPerRow; i; i--) {

          // Memory protection
#ifdef DEBUG
          NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pfOutputRowNeg >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)&(pfOutputRowPos[3]) <  pDebugOutputEOMB);
          NTA_ASSERT((const char*)&(pfOutputRowNeg[3]) <  pDebugOutputEOMB);
#endif // DEBUG

          pfOutputRowPos[0] = NULL_RESPONSE;
          pfOutputRowNeg[0] = NULL_RESPONSE;
          pfOutputRowPos[1] = NULL_RESPONSE;
          pfOutputRowNeg[1] = NULL_RESPONSE;
          pfOutputRowPos[2] = NULL_RESPONSE;
          pfOutputRowNeg[2] = NULL_RESPONSE;
          pfOutputRowPos[3] = NULL_RESPONSE;
          pfOutputRowNeg[3] = NULL_RESPONSE;

          // Advance pointers
          pfOutputRowPos += 4;
          pfOutputRowNeg += 4;
        }
        // Handle any leftovers that don't fit in a quad
        for (i=nTotalLeftovers; i; i--) {

          // Memory protection
#ifdef DEBUG
          NTA_ASSERT((const char*)pfOutputRowPos >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pfOutputRowPos <  pDebugOutputEOMB);
          NTA_ASSERT((const char*)pfOutputRowNeg >= pDebugOutputSOMB);
          NTA_ASSERT((const char*)pfOutputRowNeg <  pDebugOutputEOMB);
#endif // DEBUG

          *pfOutputRowPos++ = NULL_RESPONSE;
          *pfOutputRowNeg++ = NULL_RESPONSE;
        }

        // Advance our row pointer(s)
        pfOutputPos += nOutputRowStride;
        pfOutputNeg += nOutputRowStride;
      }  // Dual phase
    }    // for (j=nNumBlankBottomRows; j; j--)

    // Advance to correct plane for gabor filter and output buffer
    pnInputBase  += IMAGESET_PLANESTRIDE(psBufferIn) / sizeof(*pnInput);
    pfOutputBase += IMAGESET_PLANESTRIDE(psOutput) / sizeof(*pfOutputBase);

  } // for each filter (output plane)
}


// FUNCTION: _zeroOutputs()
// PURPOSE: Special case for when the output planes
// have to be uniformly zero response (e.g., when
// there is not enough pixels in the input image to
// compute a single response.)
void _zeroOutputs(const NUMPY_ARRAY * psOutput) {

  int k, j, i;
  float * pfOutputRow = NULL;
  float * pfOutputPtr = NULL;

  // Locate start of first output plane
  float * pfOutputBase = (float *)psOutput->pData;
  int nOutputRowStride = IMAGESET_ROWSTRIDE(psOutput) / sizeof(*pfOutputBase);
  int nOutputPlaneStride = IMAGESET_PLANESTRIDE(psOutput) / sizeof(*pfOutputBase);

  // Take into account bounding box suppression
  int nOutputRows = IMAGESET_ROWS(psOutput);
  int nOutputCols = IMAGESET_COLS(psOutput);
  int nNumPlanes = IMAGESET_PLANES(psOutput);

  // Try to process the rows in chunks of four
  int nQuadsPerRow = nOutputCols >> 2;
  int nLeftovers = nOutputCols - (nQuadsPerRow << 2);

  // Zero out each response plane:
  for (k=nNumPlanes; k; k-- ) {

    // Zero out each row
    pfOutputRow = pfOutputBase;
    for (j=nOutputRows; j; j--) {

      // Process most of the row in quads
      pfOutputPtr = pfOutputRow;
      for (i=nQuadsPerRow; i; i--) {
        *pfOutputPtr++ = 0.0f;
        *pfOutputPtr++ = 0.0f;
        *pfOutputPtr++ = 0.0f;
        *pfOutputPtr++ = 0.0f;
      }

      // Handle any leftovers
      for (i=nLeftovers; i; i--)
        *pfOutputPtr++ = 0.0f;

      // Move to next row
      pfOutputRow += nOutputRowStride;
    }

    // Move to next plane
    pfOutputBase += nOutputPlaneStride;
  }
}


// FUNCTION: initFromPython()
// PURPOSE: Initialize logging data structures when we are
// being called from python via ctypes as a dynamically 
// loaded library. 
#ifdef INIT_FROM_PYTHON

NTA_EXPORT 
void initFromPython(unsigned long long refP) {
  PythonSystem_initFromReferenceP(refP);
}
#endif // INIT_FROM_PYTHON

// FUNCTION: gaborCompute()
// PURPOSE: GaborNode implementation
NTA_EXPORT
int  gaborCompute(const NUMPY_ARRAY * psGaborBank,
                  const NUMPY_ARRAY * psInput,
                  const NUMPY_ARRAY * psAlpha,
                  const NUMPY_ARRAY * psBBox,
                  const NUMPY_ARRAY * psImageBox,
                  const NUMPY_ARRAY * psOutput,
                  float fGainConstant,
                  EDGE_MODE eEdgeMode,
                  float fOffImageFillValue,
                  PHASE_MODE ePhaseMode,
                  NORMALIZE_METHOD eNormalizeMethod, 
                  NORMALIZE_MODE eNormalizeMode, 
                  PHASENORM_MODE ePhaseNormMode, 
                  POSTPROC_METHOD ePostProcMethod,
                  float fPostProcSlope,
                  float fPostProcMidpoint,
                  float fPostProcMin,
                  float fPostProcMax,
                  const NUMPY_ARRAY * psBufferIn,
                  const NUMPY_ARRAY * psBufferOut,
                  const NUMPY_ARRAY * psPostProcLUT,
                  float fPostProcScalar
                 ) {

  // Allocate a big chunk of storage on the stack for a temporary buffer
  // to hold our accummulated response statistics.
  unsigned int anStatPosGrand[MAXNUM_FILTERS];
  unsigned int anStatNegGrand[MAXNUM_FILTERS];

  try
  {
    //-------------------------------------------
    // Sanity checks

    // Sanity checks: Filter must be square
    NTA_ASSERT(IMAGESET_ROWS(psGaborBank) == IMAGESET_COLS(psGaborBank));
    int nFilterDim = IMAGESET_ROWS(psGaborBank);
    int nHalfFilterDim = nFilterDim >> 1;
    int nShrinkage = nHalfFilterDim << 1;

    // Sanity check: edge mode and input/output dimensionalities
    // must make sense
    if (eEdgeMode == EDGE_MODE_CONSTRAINED) {
      //NTA_ASSERT(IMAGE_COLS(psBufferIn) == ALIGN_4_CEIL(IMAGE_COLS(psInput)));
      //NTA_ASSERT(IMAGE_ROWS(psBufferIn) == IMAGE_ROWS(psInput));
      //NTA_ASSERT(IMAGESET_COLS(psBufferOut) == ALIGN_4_CEIL(IMAGE_COLS(psInput) - nFilterDim + 1));
      //NTA_ASSERT(IMAGESET_ROWS(psBufferOut) == (IMAGE_ROWS(psInput) - nFilterDim + 1));
      NTA_ASSERT(IMAGESET_COLS(psBufferOut) == ALIGN_4_CEIL(IMAGESET_COLS(psOutput)));
      NTA_ASSERT(IMAGESET_ROWS(psBufferOut) == IMAGESET_ROWS(psOutput));
    } 
    else {
      NTA_ASSERT(eEdgeMode == EDGE_MODE_SWEEPOFF);
      //NTA_ASSERT(IMAGE_COLS(psBufferIn) == ALIGN_4_CEIL(IMAGE_COLS(psInput) + nFilterDim - 1));
      //NTA_ASSERT(IMAGE_ROWS(psBufferIn) == (IMAGE_ROWS(psInput) + nFilterDim - 1));
      //NTA_ASSERT(IMAGE_COLS(psBufferIn) == (ALIGN_4_CEIL(IMAGESET_COLS(psBufferOut)) + nFilterDim - 1));
      NTA_ASSERT(IMAGE_COLS(psBufferIn) <= ALIGN_4_CEIL(IMAGESET_COLS(psBufferOut) + nFilterDim - 1));
      NTA_ASSERT(IMAGE_ROWS(psBufferIn) == (IMAGESET_ROWS(psBufferOut) + nFilterDim - 1));
      NTA_ASSERT(IMAGESET_COLS(psBufferOut) == ALIGN_4_CEIL(IMAGESET_COLS(psOutput)));
      NTA_ASSERT(IMAGESET_ROWS(psBufferOut) == IMAGESET_ROWS(psOutput));
    }

    // Check bounding box (which is expressed with respect to
    // our input image, not our output image)
    NTA_ASSERT(BBOX_LEFT(psBBox) >= 0);
    NTA_ASSERT(BBOX_LEFT(psBBox) <= BBOX_RIGHT(psBBox));
    NTA_ASSERT(BBOX_RIGHT(psBBox) <= IMAGE_COLS(psInput));
    NTA_ASSERT(BBOX_TOP(psBBox) >= 0);
    NTA_ASSERT(BBOX_TOP(psBBox) <= BBOX_BOTTOM(psBBox));
    NTA_ASSERT(BBOX_BOTTOM(psBBox) <= IMAGE_ROWS(psInput));

    // Make sure our buffers are 16-byte aligned
    // (each row aligned on four-DWORD boundaries)
    NTA_ASSERT(IMAGE_COLS(psBufferIn) % 4 == 0);
    NTA_ASSERT(IMAGESET_COLS(psBufferOut) % 4 == 0);

    // Make sure out "image box" (the box that defines the actual
    // image portion of the psInput array) encloses our 
    // "bounding box" (the box that defines the portion of image
    // pixels over which gabor responses are to be computed.)
    NTA_ASSERT(BBOX_LEFT(psBBox)   >= BBOX_LEFT(psImageBox));
    NTA_ASSERT(BBOX_RIGHT(psBBox)  <= BBOX_RIGHT(psImageBox));
    NTA_ASSERT(BBOX_TOP(psBBox)    >= BBOX_TOP(psImageBox));
    NTA_ASSERT(BBOX_BOTTOM(psBBox) <= BBOX_BOTTOM(psImageBox));

    // The alpha mask is optional, but if it is provided,
    // it must be the same size as the input image.
    if (psAlpha) {
      NTA_ASSERT(IMAGE_COLS(psAlpha) >= IMAGE_COLS(psInput));
      NTA_ASSERT(IMAGE_ROWS(psAlpha) >= IMAGE_ROWS(psInput));
    }

    //-------------------------------------------
    // Set up a bounding box that specifies the 
    // range of pixels for which Gabor responses
    // are to be competed:
    //  sBoxInput: the locations in the (padded?)
    //             input buffer for which Gabor
    //             responses are to be computed.
    //  sBoxOutput: the locations in the output
    //             buffers for which Gabor
    //             responses are to be computed.
    BBOX sBoxInput, sBoxOutput;
    if (eEdgeMode == EDGE_MODE_CONSTRAINED) {
      // Input
      sBoxInput.nLeft  = BBOX_LEFT(psBBox);
      sBoxInput.nTop   = BBOX_TOP(psBBox);
      sBoxInput.nRight   = sBoxInput.nLeft  + BBOX_WIDTH(psBBox);
      sBoxInput.nBottom  = sBoxInput.nTop   + BBOX_HEIGHT(psBBox);
      // Output
      sBoxOutput.nLeft   = sBoxInput.nLeft;
      sBoxOutput.nTop    = sBoxInput.nTop;
      sBoxOutput.nRight  = sBoxOutput.nLeft + BBOX_WIDTH(psBBox)  - nShrinkage;
      sBoxOutput.nBottom = sBoxOutput.nTop  + BBOX_HEIGHT(psBBox) - nShrinkage;
    }
    else {
      NTA_ASSERT(eEdgeMode == EDGE_MODE_SWEEPOFF);
      // Input
      sBoxInput.nLeft = BBOX_LEFT(psBBox);
      sBoxInput.nTop  = BBOX_TOP(psBBox);
      sBoxInput.nRight   = sBoxInput.nLeft  + BBOX_WIDTH(psBBox);
      sBoxInput.nBottom  = sBoxInput.nTop   + BBOX_HEIGHT(psBBox);
      // Output
      sBoxOutput.nLeft   = sBoxInput.nLeft;
      sBoxOutput.nTop    = sBoxInput.nTop;
      sBoxOutput.nRight  = sBoxOutput.nLeft + BBOX_WIDTH(psBBox);
      sBoxOutput.nBottom = sBoxOutput.nTop  + BBOX_HEIGHT(psBBox);
    }

    // Debugging
#ifdef DEBUG
    fprintf(stdout, "sBoxInput:  %d %d %d %d (%d x %d)\n", sBoxInput.nLeft,
            sBoxInput.nTop, sBoxInput.nRight, sBoxInput.nBottom,
            (sBoxInput.nRight - sBoxInput.nLeft), 
            (sBoxInput.nBottom - sBoxInput.nTop));
    fprintf(stdout, "sBoxOutput: %d %d %d %d (%d x %d)\n", sBoxOutput.nLeft,
            sBoxOutput.nTop, sBoxOutput.nRight, sBoxOutput.nBottom,
            (sBoxOutput.nRight - sBoxOutput.nLeft), 
            (sBoxOutput.nBottom - sBoxOutput.nTop));
#endif // DEBUG

    //-------------------------------------------
    // Handle case in which bounding box is smaller than 
    // our filter:
    if ((BBOX_RIGHT(psBBox) - BBOX_LEFT(psBBox) < nFilterDim) ||
        (BBOX_BOTTOM(psBBox) - BBOX_TOP(psBBox) < nFilterDim)) {
      _zeroOutputs(psOutput);
      return 0;
    }

    //-------------------------------------------
    // Prepare input:
    // 1. Convert input image from float to integer32.
    // 2. If EDGE_MODE is SWEEPOFF, then add "padding pixels"
    //    around the edges of the integrized input plane.
    _prepareInput(psInput, 
                  psBufferIn, 
                  nFilterDim >> 1,
                  psBBox, 
                  psImageBox,
                  eEdgeMode,
                  fOffImageFillValue);

    //-------------------------------------------
    // Perform convolution:
    // 1. Convolve integerized input image (in bufferIn) against
    //    each filter in gabor filter bank, storing the result
    //    (in integer32) in the output buffers.
    // 2. While performing convolution, keeps track of the
    //    neccessary statistics for use in normalization
    //    during Pass II.
    _doConvolution(psBufferIn, 
                   psBufferOut,
                   psGaborBank, 
                   psAlpha,
                   &sBoxInput,
                   &sBoxOutput,
                   ePhaseMode, 
                   eNormalizeMethod, 
                   eNormalizeMode,
                   anStatPosGrand,
                   anStatNegGrand);

    //-------------------------------------------
    // Perform normalization and post-processing
    // 1. Perform rectification
    // 2. Apply gain (in general, this will be different for each
    //    image based on auto-normalization results);
    // 3. Apply post-processing method if any;
    // 4. Convert from integer 32 to float.
    _postProcess(psBufferOut, 
                 psOutput, 
                 &sBoxOutput,
                 ePhaseMode, 
                 nShrinkage,
                 eEdgeMode,
                 fGainConstant,
                 eNormalizeMethod, 
                 eNormalizeMode, 
                 ePhaseNormMode, 
                 ePostProcMethod, 
                 fPostProcSlope, 
                 fPostProcMidpoint,
                 fPostProcMin, 
                 fPostProcMax,
                 anStatPosGrand,
                 anStatNegGrand,
                 psPostProcLUT,
               fPostProcScalar);
  }
  catch(std::exception& e)
  {
    NTA_WARN << "gaborNode -- returning error: " << e.what();
    return -1;
  }
  return 0;
}

#ifdef __cplusplus
}
#endif 
