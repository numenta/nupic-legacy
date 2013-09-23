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
 *  This header file defines the API for performing efficient
 *  VideoSensorNode processing.
 */ 

#ifndef NTA_VIDEO_SENSOR_NODE_HPP
#define NTA_VIDEO_SENSOR_NODE_HPP

#include <nta/utils/Log.hpp>

#ifdef __cplusplus
extern "C" {
#endif  // __cplusplus

#include <nta/types/types.h>
#include "arrayBuffer.hpp"


// ImageSensorLite control buffer
typedef struct _ISL_CTLBUF {
  // Bounding box
  int     nBoxLeft; 
  int     nBoxTop; 
  int     nBoxRight; 
  int     nBoxBottom; 
  // Address of buffer holding actual pixel data
  void *  pDataAddr;
  // Optional: partition ID
  int     nPartitionID;
  // Optional: category ID
  int     nCategoryID;
  // Optional: video ID
  int     nVideoID;
  // Optional: address of buffer holding alpha data
  void *  pAlphaAddr;
} ISL_CTLBUF;


/*
// Compile-time assertion to make sure that
// the ISL_CTLBUF is 32-bytes long on this
// platform; if not, this code will 
// generate a 'duplicate case value' error
// at compile time.
#define COMPILE_TIME_ASSERT(pred) \
    switch(0){case 0:case pred:;}
#define ASSERT_EXACT_BYTESIZE(type, size) \
    COMPILE_TIME_ASSERT(sizeof(type) == size)
void compile_time_assertions(void) {
    ASSERT_EXACT_BYTESIZE(ISL_CTLBUF, 32);
}
*/


/*
// Structure that wraps the essential elements of 
// a numpy array object.
typedef struct _NUMPY_ARRAY {
  int nNumDims;
  const int * pnDimensions;
  const int * pnStrides;
  const char * pData;
} NUMPY_ARRAY; 

// Bounding box
typedef struct _BBOX {
  int   nLeft;
  int   nRight;
  int   nTop;
  int   nBottom;
} BBOX;
*/

typedef struct _BOXFIXER_PARAMS {
  int       nZonePreExpansionX;
  int       nZonePreExpansionY;
  int       nZonePostExpansionX;
  int       nZonePostExpansionY;
  int       nWindowLenX;
  int       nWindowLenY;
  int       nMinAbsZoneLenX;
  int       nMinAbsZoneLenY;
  float     fMinRelZoneLenX;
  float     fMinRelZoneLenY;
  int       nMinAbsWeakLenX;
  int       nMinAbsWeakLenY;
  float     fMinRelWeakLenX;
  float     fMinRelWeakLenY;
  float     fHeightThresh;
  float     fWidthThresh;
  float     fSecondaryHeightThresh;
  float     fSecondaryWidthThresh;
  int       nTakeBiggest;
} BOXFIXER_PARAMS;

#define MAX_BBOX_WIDTH      640
#define MAX_BBOX_HEIGHT     480

/*
// Structure that wraps specification of the
// target dimension(s)
#define MAXNUM_SCALES   4
typedef struct _TARGETSIZE {
  int   nWidth;
  int   nHeight;
} TARGETSIZE; 
typedef struct _TARGETSIZES {
  int          nNumScales;
  TARGETSIZE   anScales[MAXNUM_SCALES];
} TARGETSIZES; 
*/

// FUNCTION: adjustBox()
// PURPOSE: Implements efficient adjustment of tracking box
NTA_EXPORT
int adjustBox( // Inputs:
               const NUMPY_ARRAY * psSrcImage,
               const BBOX * psBox,
               // Parameters:
               const BOXFIXER_PARAMS * psParams,
               // Outputs:
               BBOX * psFixedBox,
               int * pnTotNumBoxes);


// FUNCTION: accessPixels()
// PURPOSE: Access pixels of a numpy array
NTA_EXPORT
int accessPixels(// Inputs:
                 const NUMPY_ARRAY * psSrcImage,
                 // Outputs:
                 const NUMPY_ARRAY * psDstImage);


// FUNCTION: extractAuxInfo()
// PURPOSE: Extract auxiliary information
NTA_EXPORT
int extractAuxInfo(// Inputs:
                   const char * pCtlBufAddr,
                   //const NUMPY_ARRAY * psCtlBuf,
                   // Outputs:
                   BBOX * psBox,
                   int * pnAddress,
                   int * pnPartitionID,
                   int * pnCategoryID,
                   int * pnVideoID,
                   int * pnAlphaAddress );
/*
int extractAuxInfo(// Inputs:
                   const NUMPY_ARRAY * psBBox,
                   const NUMPY_ARRAY * psCategoryBuf,
                   const NUMPY_ARRAY * psPartitionBuf,
                   const NUMPY_ARRAY * psAddressBuf,
                   int * pnPartitionID,
                   int * pnCategoryID,
                   int * pnAddress,
                   BBOX * psExtractedBBox );
*/

/*
// FUNCTION: formHistogramX()
NTA_EXPORT
int formHistogramX(// Inputs:
                   const NUMPY_ARRAY * psSrcImage,
                   const BBOX * psBox,
                   // Outputs:
                   const NUMPY_ARRAY * psHistogram);

// FUNCTION: formHistogramY()
// PURPOSE: Form a histogram of non-zero SMotion
NTA_EXPORT
int formHistogramY(// Inputs:
                   const NUMPY_ARRAY * psSrcImage,
                   const BBOX * psBox,
                   // Outputs:
                   const NUMPY_ARRAY * psHistogram);
*/

#ifdef __cplusplus
}
#endif  // __cplusplus

#endif // NTA_VIDEO_SENSOR_NODE_HPP
