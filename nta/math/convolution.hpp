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
 * Declarations for convolutions
 */

#ifndef NTA_CONVOLUTION_HPP
#define NTA_CONVOLUTION_HPP

//--------------------------------------------------------------------------------
/**
 * Computes convolutions in 2D, for separable kernels.
 */
template <typename T>
struct SeparableConvolution2D
{
  typedef size_t size_type;
  typedef T value_type;

  size_type nrows_;
  size_type ncols_;
  size_type f1_size_;
  size_type f2_size_;
  size_type f1_end_j_;
  size_type f2_end_i_;
  size_type f1_middle_;
  size_type f2_middle_;

  T* f1_;
  T* f2_;
  T *f1_end_;
  T *f2_end_;

  T* buffer_;

  /**
   * nrows is the number of rows in the original image, and ncols
   * is the number of columns.
   */
  inline void init(size_type nrows, size_type ncols,
		   size_type f1_size, size_type f2_size,
		   T* f1, T* f2)
  /*
    : nrows_(nrows), ncols_(ncols),
      f1_size_(f1_size), f2_size_(f2_size),
      f1_end_j_(ncols - f1_size + 1), f2_end_i_(nrows - f2_size + 1),
      f1_middle_(f1_size/2), f2_middle_(f2_size/2),
      f1_(f1), f2_(f2), f1_end_(f1 + f1_size), f2_end_(f2 + f2_size),
      buffer_(new T[nrows*ncols])
  */
  {
    nrows_ = nrows;
    ncols_ = ncols;
    f1_size_ = f1_size;
    f2_size_ = f2_size;
    f1_end_j_ = ncols - f1_size + 1;
    f2_end_i_ = nrows - f2_size + 1;
    f1_middle_ = f1_size / 2;
    f2_middle_ = f2_size / 2;
    f1_ = f1;
    f2_ = f2;
    f1_end_ = f1 + f1_size;
    f2_end_ = f2 + f2_size;
    buffer_ = new T[nrows*ncols];
  }

  inline SeparableConvolution2D() : buffer_(NULL)
  {
  }

  inline ~SeparableConvolution2D()
  {
    delete [] buffer_;
    buffer_ = NULL;
  }

  /**
   * Computes the convolution of an image in data with the two 1D
   * filters f1 and f2, and puts the result in convolved.
   *
   * Down-sampling?
   */
  inline void compute(T* data, T* convolved, bool rotated45 =false)
  {
    for (size_type i = 0; i != nrows_; ++i) {
      T* b = buffer_ + i*ncols_ + f1_middle_, *d_row = data + i*ncols_;
      for (size_type j = 0; j != f1_end_j_; ++j) {
	register T dot = 0, *f = f1_, *d = d_row + j;
	while (f != f1_end_) 
	  dot += *f++ * *d++;
	*b++ = dot;
      }
    }

    for (size_type i = 0; i != f2_end_i_; ++i) {
      T* c = convolved + (i + f2_middle_)*ncols_, *b_row = buffer_ + i*ncols_;
      for (size_type j = 0; j != ncols_; ++j) {
	register T dot = 0, *f = f2_, *b = b_row + j;
	while (f != f2_end_) {
	  dot += *f++ * *b;
	  b += ncols_;
	}
	*c++ = dot;
      }
    }
  }
};

//--------------------------------------------------------------------------------
#endif //NTA_CONVOLUTION_HPP

