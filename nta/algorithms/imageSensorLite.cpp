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
 *  This module implements efficient video-related image extraction.
 *
 *  The C NUMPY_ARRAY structure mirrors an ARRAY class in
 *  Python.
 *
 *  This exported C function is expected to be used in conjunction
 *  with ctypes wrappers around numpy array objects.
 */ 

#include <stdio.h>
#include <math.h>


// Enable debugging
//#define DEBUG   1

#include "imageSensorLite.hpp"

#ifndef MAXFLOAT
#define MAXFLOAT 9.9e19f
#endif // MAXFLOAT

// Visual C++ (Windows) does not come with roundf() in
// the standard library
#ifdef WIN32
#define ROUND(x)     ((x-floor(x))>0.5 ? ceil(x) : floor(x))
#else
#define ROUND(x)     (roundf(x))
#endif // !WIN32


// if INIT_FROM_PYTHON is defined, this module can initialize
// logging from a python system reference. This introduces
// a dependency on PythonSystem, which is not included in the
// algorithm source release. So it is disabled by default
#ifdef INIT_FROM_PYTHON
#error "Unexpected Python dependency for imageSensorLite in NuPIC 2"
#endif


#ifdef __cplusplus
extern "C" {
#endif 

#define GET_CTLBUF_ELEM(ctlBufAddr, k)            (((int*)(ctlBufAddr))[k])

#define BOX_LEFT(ctlBufAddr)              GET_CTLBUF_ELEM(ctlBufAddr, 0)
#define BOX_TOP(ctlBufAddr)               GET_CTLBUF_ELEM(ctlBufAddr, 1)
#define BOX_RIGHT(ctlBufAddr)             GET_CTLBUF_ELEM(ctlBufAddr, 2)
#define BOX_BOTTOM(ctlBufAddr)            GET_CTLBUF_ELEM(ctlBufAddr, 3)
#define DATA_ADDRESS(ctlBufAddr)          GET_CTLBUF_ELEM(ctlBufAddr, 4)
#define DATA_ALPHA_ADDRESS(ctlBufAddr)    GET_CTLBUF_ELEM(ctlBufAddr, 8)
#define PARTITION_ID(ctlBufAddr)          GET_CTLBUF_ELEM(ctlBufAddr, 5)
#define CATEGORY_ID(ctlBufAddr)           GET_CTLBUF_ELEM(ctlBufAddr, 6)
#define VIDEO_ID(ctlBufAddr)              GET_CTLBUF_ELEM(ctlBufAddr, 7)

/*
#define DST_BUF_LEN(psDstBuffer)    (((long int *)(psDstBuffer->pnDimensions))[0])

#define BBOX_ELEM(bbox, k)            (((int*)(bbox->pData))[k])
#define BBOX_LEFT(bbox)               BBOX_ELEM(bbox, 0)
#define BBOX_TOP(bbox)                BBOX_ELEM(bbox, 1)
#define BBOX_RIGHT(bbox)              BBOX_ELEM(bbox, 2)
#define BBOX_BOTTOM(bbox)             BBOX_ELEM(bbox, 3)
#define BBOX_WIDTH(bbox)              (BBOX_RIGHT(bbox) - BBOX_LEFT(bbox))
#define BBOX_HEIGHT(bbox)             (BBOX_BOTTOM(bbox) - BBOX_TOP(bbox))

#define DATA_ADDRESS(ctlbuf)          BBOX_ELEM(ctlbuf, 4)
#define PARTITION_ID(ctlbuf)          BBOX_ELEM(ctlbuf, 5)
#define CATEGORY_ID(ctlbuf)           BBOX_ELEM(ctlbuf, 6)
#define VIDEO_ID(ctlbuf)              BBOX_ELEM(ctlbuf, 7)


#define IMAGE_ELEM(array, k)          (((long int*)(array->pnDimensions))[k])
#define IMAGE_ROWS(array)             IMAGE_ELEM(array, 0)
#define IMAGE_COLS(array)             IMAGE_ELEM(array, 1)
#define IMAGE_STRIDE(array, k)        (((long int*)(array->pnStrides))[k])
#define IMAGE_ROWSTRIDE(array)        IMAGE_STRIDE(array, 0)
*/


/*
// Hanning window of window length 9
// @todo: don't both convolving against the first and
//        last window elements because they're known
//        to be zero.
static const float afHanning[] = {
  0.03661165,  
  0.12500000,  
  0.21338835,  
  0.25000000,
  0.21338835,  
  0.12500000,  
  0.03661165, 
};


#define HANNING_LEN         (sizeof(afHanning)/sizeof(afHanning[0]))
#define HANNING_HALF_LEN    ((HANNING_LEN-1) >> 1)
#define HANNING_REFL_LEN    (HANNING_HALF_LEN << 1)


// FUNCTION: _smooth()
// PURPOSE: Smooth a 1D histogram
float _smoothHist1D(const float * pfHistogram, 
                    float * pfReflHist,
                    float * pfSmoothHist,
                    int nHistWidth) {

  int i, k;
  const float * pfWindowPtr;
  float fAccum;
  float fRef = 2.0 * (*pfHistogram);

  // Construct reflected (extended) histogrm
  float * pfReflHistPtr = pfReflHist + HANNING_HALF_LEN; 
  const float * pfHistPtr = pfHistogram; 
  // Reflect leading elements
  for (k=HANNING_HALF_LEN; k; k--)
    *--pfReflHistPtr = fRef - *++pfHistPtr;
  // Copy internal elemenents
  pfHistPtr = pfHistogram; 
  pfReflHistPtr += HANNING_HALF_LEN;
  for (k=nHistWidth; k; k--)
    *pfReflHistPtr++ = *pfHistPtr++;
  // Reflect trailing elements
  fRef = 2.0 * (*--pfHistPtr);
  for (k=HANNING_HALF_LEN; k; k--)
    *pfReflHistPtr++ = fRef - *--pfHistPtr;

  // Perform convolution
  float fMaxVal = -MAXFLOAT;
  float * pfSmoothHistPtr = pfSmoothHist;
  for (k=nHistWidth; k; k--) {
    pfReflHistPtr = pfReflHist;
    pfWindowPtr = afHanning; 
    fAccum = 0.0f;
    for (i=HANNING_LEN; i; i--)
      fAccum += (*pfWindowPtr++) * (*pfReflHistPtr++);
    *pfSmoothHistPtr++ = fAccum;
    if (fAccum > fMaxVal)
      fMaxVal = fAccum;
    pfReflHist++;
  }

  return fMaxVal;
}


// FUNCTION: _formHistogramX()
// PURPOSE: Form a histogram of non-zero SMotion
void _formHistogramX(// Inputs:
                     const NUMPY_ARRAY * psSrcImage,
                     const BBOX * psBox,
                     // Outputs:
                     float * pfHist
                     ) {
    int i, j;
    int nBoxWidth = psBox->nRight - psBox->nLeft;
    int nRowAdvance = IMAGE_COLS(psSrcImage) - nBoxWidth;

    // Zero out histogram
    float * pfHistPtr = pfHist;
    for (i=nBoxWidth; i; i--)
      *pfHistPtr++ = 0.0f;

    // Scan the expanded box.  Generate a histogram that
    // shows, for each column, the number of pixels that
    // had non-zero SMotion.
    const float * pfSrc = (const float *)(psSrcImage->pData);
    const float * pfSrcPtr = pfSrc + IMAGE_COLS(psSrcImage) * psBox->nTop + psBox->nLeft;
    for (j=psBox->nBottom - psBox->nTop; j; j-- ) {
      pfHistPtr = pfHist;
      for (i=nBoxWidth; i; i-- )
        if (*pfSrcPtr++)
          *pfHistPtr++ += 1.0f;
        else
          pfHistPtr++;
      pfSrcPtr += nRowAdvance;
    }
}


// FUNCTION: _formHistogramY()
// PURPOSE: Form a histogram of non-zero SMotion
NTA_EXPORT
void _formHistogramY(// Inputs:
                     const NUMPY_ARRAY * psSrcImage,
                     const BBOX * psBox,
                     // Outputs:
                     float * pfHist
                     ) {
  int i, j;
  int nBoxWidth  = psBox->nRight - psBox->nLeft;
  int nRowAdvance = IMAGE_COLS(psSrcImage) - nBoxWidth;
  float fAccum;

  // Scan the expanded box.  Generate a histogram that
  // shows, for each column, the number of pixels that
  // had non-zero SMotion.
  const float * pfSrc = (const float *)(psSrcImage->pData);
  const float * pfSrcPtr = pfSrc + IMAGE_COLS(psSrcImage) * psBox->nTop + psBox->nLeft;
  NTA_ASSERT(psBox->nBottom - psBox->nTop >= 0);
  NTA_ASSERT(nBoxWidth >= 0);
  for (j=psBox->nBottom - psBox->nTop; j; j-- ) {
    fAccum = 0.0f;
    for (i=nBoxWidth; i; i-- )
      if (*pfSrcPtr++)
        fAccum += 1.0f;
    *pfHist++ = fAccum;
    pfSrcPtr += nRowAdvance;
  }
}


// We use static storage so we have to impose a maximum
// number of zones.
#define MAXNUM_STRONG_ZONES   32
// Allow twice as many boxes as horizontally strong zones
#define MAXNUM_BOXES          (MAXNUM_STRONG_ZONES << 1)

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
               int * pnTotNumBoxes) {

  int j, k;
  float fMaxX, fMaxY;
  int nMinZoneLen, nMinWeakLen;
  float fThreshX, fThreshY;

  // Allocate a big chunk of storage on the stack to act
  // as a temporary buffer to hold our histograms.
  float afHistogramX[MAX_BBOX_WIDTH];
  float afHistogramY[MAX_BBOX_HEIGHT];
  // Stack-local storage for intermediate buffers to
  // hold the extended (via reflection) histogram
  float afReflHistX[MAX_BBOX_WIDTH + HANNING_REFL_LEN];
  float afReflHistY[MAX_BBOX_HEIGHT + HANNING_REFL_LEN];
  // Stack-local storage for smoothed histogram buffers
  float afSmoothHistX[MAX_BBOX_WIDTH];
  float afSmoothHistY[MAX_BBOX_HEIGHT];
  // Stack-local storage of "strong" SMotion
  int anStrongX[MAX_BBOX_WIDTH];
  int anStrongY[MAX_BBOX_HEIGHT];
  // Stack-local storage for strong zones
  int nNumStrongZonesX = 0;
  int anStrongBeginX[MAXNUM_STRONG_ZONES];
  int anStrongEndX[MAXNUM_STRONG_ZONES];
  int nNumStrongZonesY = 0;
  int anStrongBeginY[MAXNUM_STRONG_ZONES];
  int anStrongEndY[MAXNUM_STRONG_ZONES];
  BBOX aboxFinal[MAXNUM_BOXES];
  int nNumFinalBoxes = 0;


  try {
    int nImageWidth  = IMAGE_COLS(psSrcImage);
    int nImageHeight = IMAGE_ROWS(psSrcImage);

    // Expand bounding box
    BBOX boxExpanded;
    boxExpanded.nLeft   = MAX(0, psBox->nLeft - psParams->nZonePreExpansionX);
    boxExpanded.nTop    = MAX(0, psBox->nTop  - psParams->nZonePreExpansionY);
    boxExpanded.nRight  = MIN(nImageWidth, psBox->nRight + psParams->nZonePreExpansionX);
    boxExpanded.nBottom = MIN(nImageHeight, psBox->nBottom + psParams->nZonePreExpansionY);

    // Sanity checks
    NTA_ASSERT(boxExpanded.nBottom >= boxExpanded.nTop);
    NTA_ASSERT(boxExpanded.nRight  >= boxExpanded.nLeft);

    int nExpandedWidth  = boxExpanded.nRight - boxExpanded.nLeft;
    int nExpandedHeight = boxExpanded.nBottom - boxExpanded.nTop;
    float fExpandedWidth  = (float)nExpandedWidth;
    float fExpandedHeight = (float)nExpandedHeight;

    // Generate a horizontal histogram 
    _formHistogramX(psSrcImage, &boxExpanded, afHistogramX);

    // Smooth the horizontal histogram
    fMaxX = _smoothHist1D(afHistogramX,
                          afReflHistX,
                          afSmoothHistX,
                          nExpandedWidth);

    //-----------------------------------------------------------------------
    // Apply tightening/splitting in horizontal direction

    // Pre-compute the minimum length of a strong
    // zone that we'll accept.
    // This is the max of an absolute length and a
    // minimum fraction of the original box.
    //nMinZoneLen = MAX(psParams->nMinAbsZoneLenX, (int)roundf(psParams->fMinRelZoneLenX * fExpandedWidth));
    nMinZoneLen = MAX(psParams->nMinAbsZoneLenX, (int)ROUND(psParams->fMinRelZoneLenX * fExpandedWidth));

    // Minimum length for a weak gap
    //nMinWeakLen = MAX(psParams->nMinAbsWeakLenX, (int)roundf(psParams->fMinRelWeakLenX * fExpandedWidth));
    nMinWeakLen = MAX(psParams->nMinAbsWeakLenX, (int)ROUND(psParams->fMinRelWeakLenX * fExpandedWidth));

    // For now, simple threshold
    fThreshX = psParams->fHeightThresh * fMaxX;

    // Mark each column as "strong" SMotion or not
    int * pnStrongPtr = anStrongX;
    const float * pfSmoothPtr = (const float *)afSmoothHistX;
    for (j=nExpandedWidth; j; j--) {
      if (*pfSmoothPtr++ >= fThreshX)
        *pnStrongPtr++ = 1;
      else
        *pnStrongPtr++ = 0;
    }

    // Pre-calculate the minimum peak strength for 
    // each lobe to avoid being culled
    float fMinStrength = fMaxX * psParams->fSecondaryHeightThresh;

    int nNumToCheck = nExpandedWidth - 1;
    float fPeakStrength = 0.0f;
    int nAntiDelta;
    int nCandidateBegin = anStrongX[0] ? 0 : -1;
    pnStrongPtr = anStrongX;
    for (k=0; k<nNumToCheck; k++) {
      //nDelta = pnStrongPtr[1] - *pnStrongPtr++;
      nAntiDelta = *(pnStrongPtr++);
      nAntiDelta -= *pnStrongPtr;
      // Beginning of new strong zone
      if (nAntiDelta < 0) {
        NTA_ASSERT(nCandidateBegin == -1);
        // Check if gap was too small
        if (nNumStrongZonesX && ((k - anStrongEndX[nNumStrongZonesX-1]) <= nMinWeakLen)) {
          // Re-start the previous strong zone
          nCandidateBegin = anStrongBeginX[--nNumStrongZonesX];
        } else {
          nCandidateBegin = k + 1;
          fPeakStrength = afSmoothHistX[k];
        }
      }
      // End of current strong zone
      else if (nAntiDelta > 0) {
        NTA_ASSERT(nCandidateBegin >= 0);
        // Accept or cull the zone
        if (k-nCandidateBegin >= nMinZoneLen && fPeakStrength >= fMinStrength) {
          anStrongBeginX[nNumStrongZonesX] = nCandidateBegin;
          anStrongEndX[nNumStrongZonesX++] = k;
          // Make sure we don't exceed our hard-coded limits
          // with a crazily fragmented pathological smotion image
          if (nNumStrongZonesX == MAXNUM_STRONG_ZONES) {
            // We can't accept any more strong zones
            nCandidateBegin = -1;
            break;
          }
        }
        nCandidateBegin = -1;
      }
      // Did we find a new peak strength?
      else if (nCandidateBegin >= 0)
        fPeakStrength = MAX(fPeakStrength, afSmoothHistX[k]);
    }

    // Last one
    if (nCandidateBegin >= 0) {
      if (nNumToCheck - nCandidateBegin >= nMinZoneLen && fPeakStrength >= fMinStrength) {
          anStrongBeginX[nNumStrongZonesX] = nCandidateBegin;
          anStrongEndX[nNumStrongZonesX++] = nNumToCheck;
        }
    }

    
    //-----------------------------------------------------------------------
    // Apply tightening/splitting in vertical direction (to each strong zone)
    for (k=0; k<nNumStrongZonesX; k++) {

      BBOX boxStrong;
      boxStrong.nLeft   = boxExpanded.nLeft + anStrongBeginX[k];
      boxStrong.nTop    = boxExpanded.nTop;
      boxStrong.nRight  = boxExpanded.nLeft + anStrongEndX[k];
      boxStrong.nBottom = boxExpanded.nBottom;

      // Generate a vertical histogram 
      _formHistogramY(psSrcImage, &boxStrong, afHistogramY);

      // Smooth the horizontal histogram
      fMaxY = _smoothHist1D(afHistogramY,
                            afReflHistY,
                            afSmoothHistY,
                            nExpandedHeight);

      // Pre-compute the minimum length of a strong
      // zone that we'll accept.
      // This is the max of an absolute length and a
      // minimum fraction of the original box.
      //nMinZoneLen = MAX(psParams->nMinAbsZoneLenY, (int)roundf(psParams->fMinRelZoneLenY * fExpandedHeight));
      nMinZoneLen = MAX(psParams->nMinAbsZoneLenY, (int)ROUND(psParams->fMinRelZoneLenY * fExpandedHeight));

      // Minimum length for a weak gap
      //nMinWeakLen = MAX(psParams->nMinAbsWeakLenY, (int)roundf(psParams->fMinRelWeakLenY * fExpandedHeight));
      nMinWeakLen = MAX(psParams->nMinAbsWeakLenY, (int)ROUND(psParams->fMinRelWeakLenY * fExpandedHeight));

      // For now, simple threshold
      fThreshY = psParams->fWidthThresh * fMaxY;

      // Mark each row as "strong" SMotion or not
      pnStrongPtr = anStrongY;
      pfSmoothPtr = (const float *)afSmoothHistY;
      for (j=nExpandedHeight; j; j--) {
        if (*pfSmoothPtr++ >= fThreshY)
          *pnStrongPtr++ = 1;
        else
          *pnStrongPtr++ = 0;
      }

      // Pre-calculate the minimum peak strength for 
      // each lobe to avoid being culled
      fMinStrength = fMaxY * psParams->fSecondaryWidthThresh;

      fPeakStrength = 0.0f;
      nNumStrongZonesY = 0;
      nNumToCheck = nExpandedHeight - 1;
      nCandidateBegin = anStrongY[0] ? 0 : -1;
      pnStrongPtr = anStrongY;
      for (j=0; j<nNumToCheck; j++) {
        nAntiDelta = *(pnStrongPtr++);
        nAntiDelta -= *pnStrongPtr;
        // Beginning of new strong zone
        if (nAntiDelta < 0) {
          NTA_ASSERT(nCandidateBegin == -1);
          // Check if gap was too small
          if (nNumStrongZonesY && ((j - anStrongEndY[nNumStrongZonesY-1]) <= nMinWeakLen)) {
            // Re-start the previous strong zone
            nCandidateBegin = anStrongBeginY[--nNumStrongZonesY];
          } else {
            nCandidateBegin = j + 1;
            fPeakStrength = afSmoothHistY[j];
          }
        }
        // End of current strong zone
        else if (nAntiDelta > 0) {
          NTA_ASSERT(nCandidateBegin >= 0);
          // Accept or cull the zone
          if (j-nCandidateBegin >= nMinZoneLen && fPeakStrength >= fMinStrength) {
            anStrongBeginY[nNumStrongZonesY] = nCandidateBegin;
            anStrongEndY[nNumStrongZonesY++] = j;
            // Make sure we don't exceed our hard-coded limits
            // with a crazily fragmented pathological smotion image
            if (nNumStrongZonesY == MAXNUM_STRONG_ZONES) {
              // We can't accept any more strong zones
              nCandidateBegin = -1;
              break;
            }
          }
          nCandidateBegin = -1;
        }
        // Did we find a new peak strength?
        else if (nCandidateBegin >= 0)
          fPeakStrength = MAX(fPeakStrength, afSmoothHistY[j]);
      }

      // Last one
      if (nCandidateBegin >= 0) {
        if (nNumToCheck - nCandidateBegin >= nMinZoneLen && fPeakStrength >= fMinStrength) {
            anStrongBeginY[nNumStrongZonesY] = nCandidateBegin;
            anStrongEndY[nNumStrongZonesY++] = nNumToCheck;
          }
      }

      // Add a new final box for each vertically strong zone.
      // We won't add any more if we hit the hard-coded maximum
      // number of boxes (should only happen in a seriously
      // pathological smotion image)
      for (j=0; j<nNumStrongZonesY && nNumFinalBoxes<MAXNUM_BOXES; j++) {
        BBOX * pboxNew = &aboxFinal[nNumFinalBoxes++];
        pboxNew->nLeft = MAX(0, boxStrong.nLeft - psParams->nZonePostExpansionX);
        pboxNew->nTop  = MAX(0, boxStrong.nTop + anStrongBeginY[j] - psParams->nZonePostExpansionY);
        pboxNew->nRight = MIN(nImageWidth, boxStrong.nRight + psParams->nZonePostExpansionX);
        pboxNew->nBottom = MIN(nImageHeight, boxStrong.nTop + anStrongEndY[j] + psParams->nZonePostExpansionY);
      }
    }

    // If there is more than one box, use the biggest
    // (this is just a heuristic)
    BBOX boxTightened;

    // Policy: take biggest zone
    //if (sParams.bTakeBiggest) {
    if (psParams->nTakeBiggest) {
      int nBoxArea;
      int nBiggestIndex = -1;
      int nBiggestArea = 0;
      for (k=0; k<nNumFinalBoxes; k++) {
        const BBOX * pboxFinal = &aboxFinal[k];
        nBoxArea = (pboxFinal->nRight - pboxFinal->nLeft) * (pboxFinal->nBottom - pboxFinal->nTop);
        if (nBoxArea > nBiggestArea) {
          nBiggestArea = nBoxArea;
          nBiggestIndex = k;
        }
      }
      const BBOX * pboxFinal = &aboxFinal[nBiggestIndex];
      boxTightened.nLeft   = pboxFinal->nLeft;
      boxTightened.nTop    = pboxFinal->nTop;
      boxTightened.nRight  = pboxFinal->nRight;
      boxTightened.nBottom = pboxFinal->nBottom;
    }

    // Policy: take union of zones
    else {
      const BBOX * pboxFinal = &aboxFinal[0];
      boxTightened.nLeft   = pboxFinal->nLeft;
      boxTightened.nTop    = pboxFinal->nTop;
      boxTightened.nRight  = pboxFinal->nRight;
      boxTightened.nBottom = pboxFinal->nBottom;
      for (k=1; k<nNumFinalBoxes; k++) {
        const BBOX * pboxFinal = &aboxFinal[k];
        boxTightened.nLeft   = MIN(boxTightened.nLeft,   pboxFinal->nLeft);
        boxTightened.nTop    = MIN(boxTightened.nTop,    pboxFinal->nTop);
        boxTightened.nRight  = MAX(boxTightened.nRight,  pboxFinal->nRight);
        boxTightened.nBottom = MAX(boxTightened.nBottom, pboxFinal->nBottom);
      }
    }

    // Write final "fixed" box
    if (nNumFinalBoxes) {
      psFixedBox->nLeft   = boxTightened.nLeft;
      psFixedBox->nTop    = boxTightened.nTop;
      psFixedBox->nRight  = boxTightened.nRight;
      psFixedBox->nBottom = boxTightened.nBottom;
    }

    // Write total number of boxes found
    *pnTotNumBoxes = nNumFinalBoxes;
  }

  catch(std::exception& e) {
    NTA_WARN << "adjustBox -- returning error: " << e.what();
    return -1;
  }

  return 0;
}
*/


// FUNCTION: extractAuxInfo()
// PURPOSE: Extract auxiliary information
NTA_EXPORT
int extractAuxInfo(// Inputs:
                   //const NUMPY_ARRAY * psCtlBuf,
                   const char * pCtlBufAddr,
                   //const NUMPY_ARRAY * psBBox,
                   //const NUMPY_ARRAY * psCategoryBuf,
                   //const NUMPY_ARRAY * psPartitionBuf,
                   //const NUMPY_ARRAY * psAddressBuf,
                   BBOX * psBox,
                   int * pnAddress,
                   int * pnPartitionID,
                   int * pnCategoryID,
                   int * pnVideoID,
                   int * pnAlphaAddress
                   ) {

  try
  {
    /*
    // Extract partition and category IDs
    if (psPartitionBuf)
      *pnPartitionID = *((long int *)(psPartitionBuf->pData));
    if (psCategoryBuf)
      *pnCategoryID  = *((long int *)(psCategoryBuf->pData));

    // Extract address of image buffer
    if (psAddressBuf)
      *pnAddress  = *((long int *)(psAddressBuf->pData));
    */

    // Extract BBOX
    psBox->nLeft   = BOX_LEFT(pCtlBufAddr);
    psBox->nTop    = BOX_TOP(pCtlBufAddr);
    psBox->nRight  = BOX_RIGHT(pCtlBufAddr);
    psBox->nBottom = BOX_BOTTOM(pCtlBufAddr);

    // Extract partition and category IDs
    if (pnPartitionID)
      *pnPartitionID = PARTITION_ID(pCtlBufAddr);
    if (pnCategoryID)
      *pnCategoryID = CATEGORY_ID(pCtlBufAddr);
    if (pnVideoID)
      *pnVideoID = VIDEO_ID(pCtlBufAddr);
    if (pnAddress)
      *pnAddress = DATA_ADDRESS(pCtlBufAddr);
    if (pnAlphaAddress)
      *pnAlphaAddress = DATA_ALPHA_ADDRESS(pCtlBufAddr);

    /*
    // Extract BBOX
    psBox->nLeft   = BBOX_LEFT(psCtlBuf);
    psBox->nTop    = BBOX_TOP(psCtlBuf);
    psBox->nRight  = BBOX_RIGHT(psCtlBuf);
    psBox->nBottom = BBOX_BOTTOM(psCtlBuf);

    // Extract partition and category IDs
    if (pnPartitionID)
      *pnPartitionID = PARTITION_ID(psCtlBuf);
    if (pnCategoryID)
      *pnCategoryID  = CATEGORY_ID(psCtlBuf);
    if (pnVideoID)
      *pnVideoID  = VIDEO_ID(psCtlBuf);
    if (pnAddress)
      *pnAddress  = DATA_ADDRESS(psCtlBuf);
    */
  }

  catch(std::exception& e)
  {
    NTA_WARN << "gaborNode -- returning error: " << e.what();
    return -1;
  }
  return 0;
}


/*
// FUNCTION: accessPixels()
// PURPOSE: Access pixels of a numpy array
NTA_EXPORT
int accessPixels(// Inputs:
                 const NUMPY_ARRAY * psSrcImage,
                 // Outputs:
                 const NUMPY_ARRAY * psDstImage) {
  try
  {
    const float * psSrc = (const float *)(psSrcImage->pData);
    float * psDst = (float *)(psDstImage->pData);
    for (int k=IMAGE_ROWS(psSrcImage) * IMAGE_COLS(psSrcImage); k; k--)
      *psDst++ = *psSrc++;
  }

  catch(std::exception& e)
  {
    NTA_WARN << "accessPixels() -- returning error: " << e.what();
    return -1;
  }
  return 0;
}
*/


/* 
// OBSOLETE FUNCTION: formHistogramX()
// PURPOSE: Form a histogram of non-zero SMotion
NTA_EXPORT
int formHistogramX(// Inputs:
                   const NUMPY_ARRAY * psSrcImage,
                   const BBOX * psBox,
                   // Outputs:
                   const NUMPY_ARRAY * psHistogram 
                   ) {
  try {
    float * pfHist = (float *)(psHistogram->pData);
    _formHistogramX(psSrcImage, psBox, pfHist);
  }

  catch(std::exception& e) {
    NTA_WARN << "formHistogramX -- returning error: " << e.what();
    return -1;
  }
  return 0;
}


// OBSOLETE FUNCTION: formHistogramY()
// PURPOSE: Form a histogram of non-zero SMotion
NTA_EXPORT
int formHistogramY(// Inputs:
                   const NUMPY_ARRAY * psSrcImage,
                   const BBOX * psBox,
                   // Outputs:
                   const NUMPY_ARRAY * psHistogram 
                   ) {
  try {
    float * pfHist = (float *)(psHistogram->pData);
    _formHistogramY(psSrcImage, psBox, pfHist);
  }

  catch(std::exception& e) {
    NTA_WARN << "formHistogramY -- returning error: " << e.what();
    return -1;
  }
  return 0;
}
*/


#ifdef __cplusplus
}
#endif 
