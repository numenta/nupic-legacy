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
 * Erosion/dilation
 */

#ifndef NTA_EROSION_HPP
#define NTA_EROSION_HPP

/*
 * Python bindings are used used in GaborNode
 */

using namespace std;

//--------------------------------------------------------------------------------
/**
 * Erode or dilate an image.
 */
template <typename T>
struct Erosion
{
  typedef size_t size_type;
  typedef T value_type;

  size_type nrows_;
  size_type ncols_;
  T* buffer_;

  inline void init(size_type nrows, size_type ncols)
  /*
    : nrows_(nrows), ncols_(ncols)
      buffer_(new T[nrows*ncols])
  */
  {
    nrows_ = nrows;
    ncols_ = ncols;
    buffer_ = new T[nrows*ncols];
  }

  inline Erosion() : buffer_(NULL)
  {
  }

  inline ~Erosion()
  {
    delete [] buffer_;
    buffer_ = NULL;
  }

  /**
   * Erodes (or dilates) the image by convolving with a 3x3 min (or max) filter.
   * Number of iterations is the radius of the erosion/dilation.
   * Does the convolution separably.
   */  
   inline void compute(T* data, T* eroded, size_type iterations,
                       bool dilate=false)
   {
     for (size_type iter = 0; iter != iterations; ++iter) {
       T* in;
       if (!iter) {
         in = data;  // First pass - read from the input buffer
       } else {
         in = eroded;  // Subsequent pass - read from the output buffer
       }
       // Rows (ignoring the first and last column)
       for (size_type i = 0; i != nrows_; ++i) {
         T* b = buffer_ + i*ncols_ + 1;  // Write to b in the buffer
         T* d = in + i*ncols_;  // Start reading from one to the left of b
         while (b != (buffer_ + (i + 1)*ncols_ - 1)) {
           if (dilate) {
             *b = max(max(*d, *(d+1)), *(d+2));
           } else {
             *b = min(min(*d, *(d+1)), *(d+2));
           }
           b++;
           d++;
         }
       }
       if (dilate) {
         // Need to fill the first and last column, which were ignored     
         for (size_type row = 0; row < nrows_; row++) {
           buffer_[row * ncols_] =
             max(in[row * ncols_], in[row * ncols_ + 1]);
           buffer_[(row+1) * ncols_ - 1] = 
             max(in[(row+1) * ncols_ - 2], in[(row+1) * ncols_ - 1]);
         }
       } else {
         // Zero out the first and last column (they are always eroded away)
         for (size_type row = 0; row < nrows_; row++) {
           buffer_[row * ncols_] = 0;
           buffer_[(row + 1) * ncols_ - 1] = 0;
         }
       }
       
       // Columns (ignoring the first and last row)
       for (size_type i = 0; i != ncols_; ++i) {
         T* b = eroded + i + ncols_;  // Write to b in the output
         T* d = buffer_ + i;  // Start reading from one above b
         while (b != (eroded + i + ncols_*(nrows_ - 1))) {
           if (dilate) {
             *b = max(max(*d, *(d + ncols_)), *(d + ncols_*2));
           } else {
             *b = min(min(*d, *(d + ncols_)), *(d + ncols_*2));
           }
           b += ncols_;
           d += ncols_;
         }
       }
       if (dilate) {
         // Need to fill the first and last row, which were ignored     
         for (size_type col = 0; col < ncols_; col++) {
           eroded[col] = max(buffer_[col], buffer_[col + ncols_]);
           eroded[(nrows_ - 1) * ncols_ + col] = 
             max(buffer_[(nrows_ - 1) * ncols_ + col],
                 buffer_[(nrows_ - 2) * ncols_ + col]);
         }
       } else {
         // Zero out the first and last row (they are always eroded away)
         for (size_type col = 0; col < ncols_; col++) {
           eroded[col] = 0;
           eroded[(nrows_ - 1) * ncols_ + col] = 0;
         }
       }
     }
   }

};

//--------------------------------------------------------------------------------
#endif //NTA_EROSION_HPP

