%pythoncode %{
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import os

_ALGORITHMS = _algorithms
%}

%{ // Includes necessary to compile the wrappers

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

#include <Python.h>

#include <sstream>
#include <iostream>
#include <fstream>
#include <vector>

#include <nta/math/Types.hpp>
#include <nta/math/Convolution.hpp>
#include <nta/math/Rotation.hpp>
#include <nta/math/Erosion.hpp>
#include <nta/algorithms/GaborNode.hpp>
#include <nta/algorithms/ImageSensorLite.hpp>
#include <nta/algorithms/Scanning.hpp>

#include <nta/math/SparseMatrix.hpp>
#include <nta/math/SparseBinaryMatrix.hpp>
#include <nta/algorithms/Svm.hpp>
#include <nta/algorithms/Linear.hpp>
#include <nta/algorithms/FDRSpatial.hpp>
#include <nta/algorithms/FDRCSpatial.hpp>
#include <nta/algorithms/SpatialPooler.hpp>
#include <nta/algorithms/FlatSpatialPooler.hpp>

#include <nta/algorithms/Cells4.hpp>
#include <nta/algorithms/ClassifierResult.hpp>
#include <nta/algorithms/FastClaClassifier.hpp>
#include <nta/algorithms/SegmentUpdate.hpp>
#include <nta/algorithms/OutSynapse.hpp>
#include <nta/algorithms/InSynapse.hpp>
#include <nta/algorithms/Cell.hpp>

#include <numpy/arrayobject.h>
#include <py_support/NumpyVector.hpp>
#include <py_support/PythonStream.hpp>
#include <py_support/PyHelpers.hpp>

/// %template(_InSynapse) nta::algorithms::Cells3::InSynapse<nta::UInt32, nta::Real32>;
/// %template(Segment3_32) nta::algorithms::Cells3::Segment<nta::UInt32, nta::Real32>;
/// %template(Cell3_32) nta::algorithms::Cells3::Cell<nta::UInt32, nta::Real32>;
/// %template(Cells3_32) nta::algorithms::Cells3::Cells3<nta::UInt32, nta::Real32>;
using namespace nta::algorithms::Cells4;
using namespace nta::algorithms::cla_classifier;
using namespace nta;

#define CHECKSIZE(var) \
  NTA_ASSERT((var)->descr->elsize == 4) << " elsize:" << (var)->descr->elsize


// TODO: This __really__ belongs somewhere else, but no other good place for it.

/* FDRCSpatialInfer
   ----------------
   This runs core FDRCSpatial inference algorithm for the pynode version.

   Roughly, this is a right-vector product with the coincidence matrix and
   the input vector.  We can't use a normal matrix multiply, though, because
   we support cloning.

   This is called via ctypes.

   @param  input                         The input array.  Should be 0/1.
                                         Should be inputWidth*inputHeight big.
   @param  inputWidth                    The width of the input array.
   @param  inputHeight                   The height of the input array.
   @param  cloneMap                      A map that is numColumns big indicating
                                         which clone master should be used for
                                         each column.
   @param  tlYXArr                       A map that is numColumns*2 big that
                                         can be used to find (y, x) for each
                                         column.
   @param  numColumns                    The number of columns.
   @param  masterLearnedCoincidencesArr  An array that is (numMasterCoincs *
                                         2 * coincSize) big that indicates
                                         where the mater coinc matrices should
                                         have 1's.  Else, they have 0.  For
                                         each master coincidence, we have an
                                         array of coincSize y values, then
                                         coincSize x values.  If a given
                                         master is less than coincSize big,
                                         it will be passed with -1.
   @param  coincSize                     The number of non-zeros in each coinc.
   @param  denseOutput                   We'll place the dense output here.
   @param  masterBoredomFactors          An array of floats, one per master,
                                         that indicates how bored that master
                                         is.  All coincidences with that master
                                         will have their outputs multiplied by
                                         this number.  If you don't want to use
                                         the "boredom" features, set all to 1.0
*/

#ifdef __cplusplus
extern "C" {
#endif  // __cplusplus

NTA_EXPORT
void FDRCSpatialInfer(const float* input, int inputWidth, int inputHeight,
                      const int* cloneMap,
                      const int* tlYXArr, int numColumns,
                      const int* masterLearnedCoincidencesArr, int coincSize,
                      float* denseOutput,
                      float* masterBoredomFactors)
{
  for (int columnNum = numColumns-1; columnNum >= 0; columnNum--) {

    int masterNum = *(cloneMap++);
    int tlY = *(tlYXArr++);
    int tlX = *(tlYXArr++);
    const int* yArr = masterLearnedCoincidencesArr + (masterNum * 2 * coincSize);
    const int* xArr = yArr + coincSize;
    float columnSum = 0;
    float boredomFactor = masterBoredomFactors[masterNum];

    for (int i = coincSize-1; i >= 0; i--) {

      int dx = *(xArr++);

      if (dx == -1) {

        break;

      } else {

        int dy = *(yArr++);
        int x = tlX + dx;
        int y = tlY + dy;

        //std::cout << x << "/" << y << "/" << (y*inputWidth + x) << " ";

        columnSum += input[(y * inputWidth) + x];
      }
    }
    //std::cout << std::endl;

    (*denseOutput++) = columnSum * boredomFactor;
  }
}

#ifdef __cplusplus
}
#endif  // __cplusplus

%}

// %pythoncode %{
//   import numpy
//   from nupic.bindings import math
// %}

%naturalvar;


// Hack to keep the linker from stripping (I think this is needed)...
%inline {
void forceRetentionOfFDRCSpatialInfer(void) {
  FDRCSpatialInfer(NULL, 0, 0, NULL, NULL, 0, NULL, 0, NULL, NULL);
}
}

// This dummy inline function exists only to force the linker
// to keep the gaborCompute() function in the resulting
// shared object.
%inline {

void forceRetentionOfGaborComputeWithinLibrary(void) {
 gaborCompute( NULL,                // const NUMPY_ARRAY * psGaborBank
               NULL,                // const NUMPY_ARRAY * psInput
               NULL,                // const NUMPY_ARRAY * psAlpha
               NULL,                // const NUMPY_ARRAY * psBBox
               NULL,                // const NUMPY_ARRAY * psImageBox
               NULL,                // const NUMPY_ARRAY * psOutput
               0.0f,                // float fGainConstant
               (EDGE_MODE)0,        // EDGE_MODE eEdgeMode
               0.0f,                // float fOffImageFillValue
               (PHASE_MODE)0,       // PHASE_MODE ePhaseMode
               (NORMALIZE_METHOD)0, // NORMALIZE_METHOD eNormalizeMethod
               (NORMALIZE_MODE)0,   // NORMALIZE_MODE eNormalizeMode
               (PHASENORM_MODE)0,   // PHASENORM_MODE ePhaseNormMode
               (POSTPROC_METHOD)0,  // POSTPROC_METHOD ePostProcMethod
               0.0f,                // float fPostProcSlope
               0.0f,                // float fPostProcMidpoint
               0.0f,                // float fPostProcMin
               0.0f,                // float fPostProcMax
               NULL,                // const NUMPY_ARRAY * psBufferIn
               NULL,                // const NUMPY_ARRAY * psBufferOut
               NULL,                // const NUMPY_ARRAY * psPostProcLUT
               0.0f                 // float fPostProcScalar
  );
  // Initialization of log system from python disabled for now.
  // See comments in gaborNode.cpp
  // initFromPython(0);
}

}

// These dummy inline functions exist only to force the linker
// to keep the ImageSensorLite functions in the resulting
// shared object.
%inline {
void forceRetentionOfImageSensorLiteLibrary(void) {
  extractAuxInfo( NULL,          // const char * pCtlBufAddr
                  NULL,          // BBOX * psBox
                  NULL,          // int * pnAddress
                  NULL,          // int * pnPartitionID
                  NULL,          // int * pnCategoryID
                  NULL,          // int * pnVideoID
                  NULL           // int * pnAlphaAddress
  );
}
}

//--------------------------------------------------------------------------------
// LINEAR
//--------------------------------------------------------------------------------
%include <nta/algorithms/Linear.hpp>

%extend nta::algorithms::linear::linear
{
  inline void create_problem(int size, int n_dims,
                 PyObject* labelsIn, PyObject* samplesIn,
                 float bias = -1.0)
  {
    PyArrayObject* labels = (PyArrayObject*)labelsIn;
    PyArrayObject* samples = (PyArrayObject*)samplesIn;

    self->create_problem(size, n_dims,
             (float*)(labels->data), (float*)(samples->data),
             bias);
  }

  inline void cross_validation(int nr_fold, PyObject* py_target)
  {
    PyArrayObject* target = (PyArrayObject*)py_target;
    self->cross_validation(nr_fold, (int*)target->data);
  }

  inline int predict_values(PyObject* py_x, PyObject* py_dec_values)
  {
    PyArrayObject* x = (PyArrayObject*)py_x;
    PyArrayObject* dec_values = (PyArrayObject*)py_dec_values;
    return self->predict_values((float*)x->data, (float*)dec_values->data);
  }

  inline int predict(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*)py_x;
    return self->predict((float*)x->data);
  }

  inline int predict_probability(PyObject* py_x, PyObject* py_prob_estimates)
  {
    PyArrayObject* x = (PyArrayObject*)py_x;
    PyArrayObject* prob_estimates = (PyArrayObject*)py_prob_estimates;
    return self->predict_probability((float*)x->data, (float*)prob_estimates->data);
  }
}

//--------------------------------------------------------------------------------
// SVM
//--------------------------------------------------------------------------------
%include <nta/algorithms/Svm.hpp>

%ignore nta::algorithms::svm::operator=;

%extend nta::algorithms::svm::svm_problem
{
  inline void get_samples(PyObject* samplesIn)
  {
    PyArrayObject* samples_py = (PyArrayObject*)samplesIn;
    for (int i = 0; i < self->size(); ++i) {
      float* row_it = (float*)(samples_py->data+i*samples_py->strides[0]);
      *row_it++ = self->y_[i];
      for (int j = 0; j < self->n_dims(); ++j, ++row_it)
    *row_it = self->x_[i][j];
    }
  }
}

%extend nta::algorithms::svm::svm_problem01
{
  inline void get_samples(PyObject* samplesIn)
  {
    PyArrayObject* samples_py = (PyArrayObject*)samplesIn;
    for (int i = 0; i < self->size(); ++i) {
      float* row_it = (float*)(samples_py->data+i*samples_py->strides[0]);
      *row_it++ = self->y_[i];
      std::fill(row_it, row_it + self->n_dims(), (float) 0);
      for (int j = 0; j < self->nnz(i); ++j)
    *(row_it + self->x_[i][j]) = 1;
    }
  }
}

%extend nta::algorithms::svm::svm_model
{
  inline void get_support_vectors(PyObject* svIn)
  {
    PyArrayObject* sv_py = (PyArrayObject*)svIn;
    for (int i = 0; i < self->size(); ++i) {
      float* row_it = (float*)(sv_py->data+i*sv_py->strides[0]);
      for (int j = 0; j < self->n_dims(); ++j, ++row_it)
    *row_it = self->sv[i][j];
    }
  }

  inline void get_support_vector_coefficients(PyObject* svCoeffIn)
  {
    PyArrayObject* sv_coeff_py = (PyArrayObject*)svCoeffIn;
    for (size_t i = 0; i < self->sv_coef.size(); ++i) {
      float* row_it = (float*)(sv_coeff_py->data+i*sv_coeff_py->strides[0]);
      for (int j = 0; j < self->size(); ++j, ++row_it)
    *row_it = self->sv_coef[i][j];
    }
  }

  inline PyObject* get_hyperplanes()
  {
    if (self->n_class() == 1)
      Py_RETURN_NONE;

    size_t m = self->w.size(), n = self->w[0].size();
    int dims[] = { int(m), int(n) };
    nta::NumpyMatrix out(dims);
    for (size_t i = 0; i != m; ++i)
      for (size_t j = 0; j != n; ++j)
    *(out.addressOf(0,0) + i*n + j) = self->w[i][j];
    return out.forPython();
  }
}

%extend nta::algorithms::svm::svm_dense
{
  PyObject* __getstate__()
  {
    SharedPythonOStream py_s(self->persistent_size());
    std::ostream& s = py_s.getStream();
    self->save(s);
    return py_s.close();
  }

  %pythoncode %{
    def __init__(self, *args, **kwargs):
      """
      __init__(self, kernel=0, n_dims=0, threshold=.9, cache_size=100, shrinking=1,
        probability=False, seed=-1) -> svm_dense

      nta::algorithms::svm::svm_dense::svm_dense(int kernel=0, int n_dims=0,
      float threshold=.9, int cache_size=100, int shrinking=1, bool
      probability=false)
      """
      # Convert numpy ints to regular ints for Python 2.6
      for k in ('kernel', 'n_dims', 'cache_size', 'shrinking'):
          if k in kwargs:
            kwargs[k] = int(kwargs[k])

      this = _ALGORITHMS.new_svm_dense(*args, **kwargs)
      try: self.this.append(this)
      except: self.this = this

    def __setstate__(self, inString):
      self.this = _ALGORITHMS.new_svm_dense()
      self.thisown = 1
      self.loadFromString(inString)
      %}

  void loadFromString(const std::string& inString)
  {
    std::istringstream inStream(inString);
    self->load(inStream);
  }

  inline void add_sample(float y_val, PyObject* x_vector)
  {
    PyArrayObject* x = (PyArrayObject*) x_vector;
    self->add_sample(y_val, (float*)x->data);
  }

  inline float predict(PyObject* x_vector)
  {
    PyArrayObject* x = (PyArrayObject*) x_vector;
    return self->predict((float*)x->data);
  }

  inline float predict_probability(PyObject* x_vector, PyObject* proba_vector)
  {
    PyArrayObject* x = (PyArrayObject*) x_vector;
    PyArrayObject* proba = (PyArrayObject*) proba_vector;
    return self->predict_probability((float*)x->data, (float*)proba->data);
  }

  inline void save(const std::string& filename)
  {
    std::ofstream save_file(filename.c_str());
    self->save(save_file);
    save_file.close();
  }

  inline void load(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->load(load_file);
    load_file.close();
  }

  inline float cross_validate(int n_fold, float gamma, float C, float eps)
  {
    float accuracy;
    Py_BEGIN_ALLOW_THREADS;
    accuracy = self->cross_validation(n_fold, gamma, C, eps);
    Py_END_ALLOW_THREADS;
    return accuracy;
  }

  inline void trainReleaseGIL(float gamma, float C, float eps)
  {
    Py_BEGIN_ALLOW_THREADS;
    self->train(gamma, C, eps);
    Py_END_ALLOW_THREADS;
  }
};

%extend nta::algorithms::svm::svm_01
{
  PyObject* __getstate__()
  {
    SharedPythonOStream py_s(self->persistent_size());
    std::ostream& s = py_s.getStream();
    self->save(s);
    return py_s.close();
  }

  %pythoncode %{
    def __setstate__(self, inString):
      self.this = _ALGORITHMS.new_svm_01()
      self.thisown = 1
      self.loadFromString(inString)
      %}

  void loadFromString(const std::string& inString)
  {
    std::istringstream inStream(inString);
    self->load(inStream);
  }

  inline void add_sample(float y_val, PyObject* x_vector)
  {
    PyArrayObject* x = (PyArrayObject*) x_vector;
    self->add_sample(y_val, (float*)x->data);
  }

  inline float predict(PyObject* x_vector)
  {
    PyArrayObject* x = (PyArrayObject*) x_vector;
    return self->predict((float*)x->data);
  }

  inline float predict_probability(PyObject* x_vector, PyObject* proba_vector)
  {
    PyArrayObject* x = (PyArrayObject*) x_vector;
    PyArrayObject* proba = (PyArrayObject*) proba_vector;
    return self->predict_probability((float*)x->data, (float*)proba->data);
  }

  inline float cross_validate(int n_fold, float gamma, float C, float eps)
  {
    float accuracy;
    Py_BEGIN_ALLOW_THREADS;
    accuracy = self->cross_validation(n_fold, gamma, C, eps);
    Py_END_ALLOW_THREADS;
    return accuracy;
  }

  inline void trainReleaseGIL(float gamma, float C, float eps)
  {
    Py_BEGIN_ALLOW_THREADS;
    self->train(gamma, C, eps);
    Py_END_ALLOW_THREADS;
  }

  inline void save(const std::string& filename)
  {
    std::ofstream save_file(filename.c_str());
    self->save(save_file);
    save_file.close();
  }

  inline void load(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->load(load_file);
    load_file.close();
  }
};

//--------------------------------------------------------------------------------
// CONVOLUTION
//--------------------------------------------------------------------------------
%include <nta/math/Convolution.hpp>

%template(Float32SeparableConvolution2D) SeparableConvolution2D<float>;

%extend SeparableConvolution2D<float>
{
  inline void init(nta::UInt32 nrows, nta::UInt32 ncols,
           nta::UInt32 f1_size, nta::UInt32 f2_size,
           PyObject* pyF1, PyObject* pyF2)
  {
    PyArrayObject *f1 = (PyArrayObject*) pyF1;
    PyArrayObject *f2 = (PyArrayObject*) pyF2;

    self->init(nrows, ncols, f1_size, f2_size, (float*)(f1->data), (float*)(f2->data));
  }

  inline void compute(PyObject* pyData, PyObject* pyConvolved, bool rotated45 =false)
  {
    PyArrayObject* data = (PyArrayObject*)pyData;
    PyArrayObject* convolved = (PyArrayObject*)pyConvolved;

    self->compute((float*)(data->data), (float*)(convolved->data), rotated45);
  }

  inline void getBuffer(PyObject* pyBuffer) const
  {
    PyArrayObject *buffer = (PyArrayObject*)pyBuffer;

    const size_t size = self->nrows_ * self->ncols_;
    std::copy(self->buffer_, self->buffer_ + size, (float*)(buffer->data));
  }
};

//--------------------------------------------------------------------------------
// ROTATION
//--------------------------------------------------------------------------------
%include <nta/math/Rotation.hpp>

%template(Float32Rotation45) Rotation45<float>;

%extend Rotation45<float>
{
  inline void rotate(PyObject* pyOriginal, PyObject* pyRotated,
             nta::UInt32 nrows, nta::UInt32 ncols, nta::UInt32 z)
  {
    PyArrayObject* original = (PyArrayObject*)pyOriginal;
    PyArrayObject* rotated = (PyArrayObject*)pyRotated;

    self->rotate((float*)(original->data), (float*)(rotated->data),
      nrows, ncols, z);
  }

  inline void unrotate(PyObject* pyUnrotated, PyObject* pyRotated,
               nta::UInt32 nrows, nta::UInt32 ncols, nta::UInt32 z)
  {
    PyArrayObject* unrotated = (PyArrayObject*)pyUnrotated;
    PyArrayObject* rotated = (PyArrayObject*)pyRotated;

    self->unrotate((float*)(unrotated->data), (float*)(rotated->data),
      nrows, ncols, z);
  }
};

//--------------------------------------------------------------------------------
// EROSION
//--------------------------------------------------------------------------------
%include <nta/math/Erosion.hpp>

%template(Float32Erosion) Erosion<float>;

%extend Erosion<float>
{
  inline void init(nta::UInt32 nrows, nta::UInt32 ncols)
  {
    self->init(nrows, ncols);
  }

  inline void compute(PyObject* pyData, PyObject* pyEroded,
                      nta::UInt32 iterations, bool dilate=false)
  {
    PyArrayObject* data = (PyArrayObject*)pyData;
    PyArrayObject* eroded = (PyArrayObject*)pyEroded;

    self->compute((float*)(data->data), (float*)(eroded->data),
                  iterations, dilate);
  }

  inline void getBuffer(PyObject* pyBuffer) const
  {
    PyArrayObject *buffer = (PyArrayObject*)pyBuffer;

    const size_t size = self->nrows_ * self->ncols_;
    std::copy(self->buffer_, self->buffer_ + size, (float*)(buffer->data));
  }
};

//--------------------------------------------------------------------------------
// SCANNING
//--------------------------------------------------------------------------------

%include <nta/algorithms/Scanning.hpp>
%inline {
  void computeAlpha(nta::UInt32 xstep, nta::UInt32 ystep,
                    nta::UInt32 widthS, nta::UInt32 heightS,
                    nta::UInt32 imageWidth, nta::UInt32 imageHeight,
                    nta::UInt32 xcount, nta::UInt32 ycount,
                    nta::UInt32 weightWidth, float sharpness,
                    PyObject* pyData, PyObject* pyValues,
                    PyObject* pyCounts, PyObject* pyWeights)
  {
    PyArrayObject *data = (PyArrayObject*) pyData;
    PyArrayObject *values = (PyArrayObject*) pyValues;
    PyArrayObject *counts = (PyArrayObject*) pyCounts;
    PyArrayObject *weights = (PyArrayObject*) pyWeights;
    computeAlpha(xstep, ystep, widthS, heightS, imageWidth, imageHeight,
                 xcount, ycount, weightWidth, sharpness,
                 (float*)(data->data), (float*)(values->data),
                 (float*)(counts->data), (float*)(weights->data));
  }
}


//--------------------------------------------------------------------------------
//--------------------------------------------------------------------------------
// DENDRITIC TREE - started Jan 2010
//--------------------------------------------------------------------------------
%template(Byte_Vector) std::vector<nta::Byte>;

%include <nta/math/Types.hpp>
 ///%include <nta/algorithms/Cells.hpp>

 ///%template(Segment_32) nta::algorithms::Segment<nta::UInt32, nta::Real32>;
 ///%template(Branch_32) nta::algorithms::Branch<nta::UInt32, nta::Real32>;
 ///%template(Cell_32) nta::algorithms::Cell<nta::UInt32, nta::Real32>;
 ///%template(SegVector_32) std::vector<nta::algorithms::Segment<nta::UInt32, nta::Real32>*>;
 ///%template(BranchVector_32) std::vector<nta::algorithms::Branch<nta::UInt32, nta::Real32>*>;
 ///%template(Cells_32) nta::algorithms::Cells<nta::UInt32, nta::Real32>;
 ///%template(Int_Seg_32) std::pair<nta::UInt32, nta::algorithms::Segment<nta::UInt32,nta::Real32>*>;

// Already seen by swig on linux32 where size_t is the same size as unsigned int
#if !defined(NTA_PLATFORM_linux32) && !defined(NTA_PLATFORM_linux32arm) && !defined(NTA_PLATFORM_linux32armv7)
%template(Size_T_Vector) std::vector<size_t>;
#endif

//--------------------------------------------------------------------------------
// Some functions, faster than numpy.
//--------------------------------------------------------------------------------
%inline {

  inline nta::UInt32 non_zeros_ui8(PyObject* py_x, PyObject* py_y)
  {
    PyArrayObject* x = (PyArrayObject*)py_x;
    PyArrayObject* y = (PyArrayObject*)py_y;
    nta::UInt32 nnz = 0;
    unsigned char* x_data = (unsigned char*) x->data;
    nta::UInt32* y_res = (nta::UInt32*) y->data;
    for (int i = 0; i != x->dimensions[0]; ++i)
      if (x_data[i] != 0)
        y_res[nnz++] = i;
    return nnz;
  }

  inline nta::UInt32 non_zeros_i32(PyObject* py_x, PyObject* py_y)
  {
    PyArrayObject* x = (PyArrayObject*)py_x;
    PyArrayObject* y = (PyArrayObject*)py_y;
    nta::UInt32 nnz = 0;
    nta::UInt32* x_data = (nta::UInt32*) x->data;
    nta::UInt32* y_res = (nta::UInt32*) y->data;
    for (int i = 0; i != x->dimensions[0]; ++i)
      if (x_data[i] != 0)
        y_res[nnz++] = i;
    return nnz;
  }

  inline nta::UInt32 non_zeros_f32(PyObject* py_x, PyObject* py_y)
  {
    PyArrayObject* x = (PyArrayObject*)py_x;
    CHECKSIZE(x);
    PyArrayObject* y = (PyArrayObject*)py_y;
    CHECKSIZE(y);
    nta::UInt32 nnz = 0;
    nta::Real32* x_data = (nta::Real32*) x->data;
    nta::UInt32* y_res = (nta::UInt32*) y->data;
    for (int i = 0; i != x->dimensions[0]; ++i)
      if (x_data[i] != 0)
        y_res[nnz++] = i;
    return nnz;
  }

  inline void rightVecProdAtIndices(PyObject* py_ind, PyObject* py_x, PyObject* py_y)
  {
    PyArrayObject* ind = (PyArrayObject*)py_ind;
    PyArrayObject* x = (PyArrayObject*)py_x;
    PyArrayObject* y = (PyArrayObject*)py_y;
    nta::UInt32 nc = ind->dimensions[0];
    nta::UInt32 ni = ind->dimensions[1];
    nta::UInt32* ind_data = (nta::UInt32*) ind->data;
    nta::Real32* x_data = (nta::Real32*) x->data;
    nta::Real32* y_res = (nta::Real32*) y->data;

    for (nta::UInt32 c = 0; c != nc; ++c, ind_data += ni) {
      nta::Real32 val = 0;
      for (nta::UInt32 i = 0; i != ni; ++i)
        val += x_data[ind_data[i]];
      *y_res++ = val;
    }
  }
}

//--------------------------------------------------------------------------------
// FDR
//--------------------------------------------------------------------------------
%include <nta/algorithms/FDRSpatial.hpp>

 // Functions to speed-up Python continuous FDR SP and TP
%inline {

  // Continuous cell sweep found in FDR continuous SP
  inline PyObject* CSPSweep(nta::UInt32 cfx, nta::UInt32 cfy,
                            nta::UInt32 stimulusThreshold,
                            nta::UInt32 inhibitionRadius,
                            PyObject* py_denseOutput,
                            PyObject* py_afterInhibition)
  {
    PyArrayObject* denseOutput = (PyArrayObject*) py_denseOutput;
    CHECKSIZE(denseOutput);
    nta::Real32* denseOutput_begin = (nta::Real32*)(denseOutput->data);
    nta::Real32* denseOutput_end = denseOutput_begin + denseOutput->dimensions[0];

    PyArrayObject* afterInhibition = (PyArrayObject*) py_afterInhibition;
    CHECKSIZE(afterInhibition);
    nta::Real32* afterInhibition_begin = (nta::Real32*)(afterInhibition->data);
    nta::Real32* afterInhibition_end = afterInhibition_begin + afterInhibition->dimensions[0];

    std::vector<nta::UInt32> activeElements;

    nta::algorithms::csp_sweep(cfx, cfy, stimulusThreshold, inhibitionRadius,
                               denseOutput_begin, denseOutput_end,
                               activeElements,
                               afterInhibition_begin, afterInhibition_end);

    nta::NumpyVectorT<nta::UInt32> ae(activeElements.size());
    for (size_t i = 0; i != activeElements.size(); ++i)
      ae.set(i, activeElements[i]);
    return ae.forPython();
  }
}

//--------------------------------------------------------------------------------
%extend nta::algorithms::FDRSpatial
{
  %pythoncode %{
    def __init__(self, *args):
        self.this = _ALGORITHMS.new_FDRSpatial(*args)

    def __getstate__(self):
      """
      Used by the pickling mechanism to get state that will be saved.
      """
      return (self.toPyString(),)

    def __setstate__(self, tup):
      """
      Used by the pickling mechanism to restore state that was saved.
      """
      self.this = _ALGORITHMS.new_FDRSpatial()
      self.thisown = 1
      self.fromPyString(tup[0])
  %}

  inline void setCMFromDense(PyObject* py_dense)
  {
    PyArrayObject* x = (PyArrayObject*)py_dense;
    CHECKSIZE(x);
    nta::Real32* x_data = (nta::Real32*) x->data;
    self->set_cm_from_dense(x_data, x_data + x->dimensions[0] * x->dimensions[1]);
  }

  inline void compute(nta::UInt32 i, PyObject* py_x, PyObject* py_y,
                      bool doLearn, bool doInfer)
  {
    PyArrayObject* x = (PyArrayObject*)py_x;
    CHECKSIZE(x);
    PyArrayObject* y = (PyArrayObject*)py_y;
    CHECKSIZE(y);
    nta::Real32* x_data = (nta::Real32*) x->data;
    nta::Real32* y_res = (nta::Real32*) y->data;

    self->compute(i,
                  x_data, x_data + x->dimensions[0],
                  y_res, y_res + y->dimensions[0],
                  doLearn, doInfer);
  }

  inline PyObject* getDenseCoincidence(nta::UInt32 row) const
  {
    nta::NumpyVectorT<nta::Real32> c(self->nCols());
    self->get_cm_row_dense(row, c.begin(), c.end());
    return c.forPython();
  }

  inline PyObject* getSparseCoincidence(nta::UInt32 row) const
  {
    nta::NumpyVectorT<nta::UInt32> cpp_ind(self->nNonZerosPerRow());
    nta::NumpyVectorT<nta::Real32> cpp_nz(self->nNonZerosPerRow());
    self->get_cm_row_sparse(row, cpp_ind.begin(), cpp_nz.begin());
    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, cpp_ind.forPython());
    PyTuple_SET_ITEM(toReturn, 1, cpp_nz.forPython());
    return toReturn;
  }

  inline PyObject* overlaps(PyObject* py_x, PyObject* py_output)
  {
    PyArrayObject* x = (PyArrayObject*)py_x;
    CHECKSIZE(x);
    nta::Real32* x_data = (nta::Real32*) x->data;
    PyArrayObject* output = (PyArrayObject*)py_output;
    CHECKSIZE(output);
    nta::Real32* output_data = (nta::Real32*) output->data;
    std::vector<nta::Real32> y(self->nRows());
    size_t n = self->overlaps(x_data, output_data, y.begin());
    nta::NumpyVectorT<nta::Real32> py_y(n);
    for (size_t i = 0; i != n; ++i)
      py_y.set(i, y[i]);
    return py_y.forPython();
  }

  inline PyObject* toPyString() const
  {
    SharedPythonOStream py_s(self->persistent_size());
    std::ostream& s = py_s.getStream();
    self->save(s);
    return py_s.close();
  }

  inline bool fromPyString(PyObject *s)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(s, &buf, &n); // Reference-neutral.
    if((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->load(s);
      return true;
    } else {
      throw std::runtime_error("Failed to load FDRSpatial");
      return false;
    }
  }
}

//--------------------------------------------------------------------------------
// Continuous FDR
//--------------------------------------------------------------------------------
%include <nta/algorithms/FDRCSpatial.hpp>

//--------------------------------------------------------------------------------
%extend nta::algorithms::FDRCSpatial
{
  %pythoncode %{
    def __init__(self, *args):
        self.this = _ALGORITHMS.new_FDRCSpatial(*args)

    def __getstate__(self):
      """
      Used by the pickling mechanism to get state that will be saved.
      """
      return (self.toPyString(),)

    def __setstate__(self, tup):
      """
      Used by the pickling mechanism to restore state that was saved.
      """
      self.this = _ALGORITHMS.new_FDRCSpatial()
      self.thisown = 1
      self.fromPyString(tup[0])
  %}

  inline void compute(PyObject* py_x, PyObject* py_y, bool doLearn, bool doInfer)
  {
    PyArrayObject* x = (PyArrayObject*)py_x;
    CHECKSIZE(x);
    PyArrayObject* y = (PyArrayObject*)py_y;
    CHECKSIZE(y);
    nta::Real32* x_data = (nta::Real32*) x->data;
    nta::Real32* y_data = (nta::Real32*) y->data;

    self->compute(x_data, x_data + x->dimensions[0],
                  y_data, y_data + y->dimensions[0],
                  doLearn, doInfer);
  }

  inline PyObject* getSparseCoincidence(nta::UInt32 row, bool learnt =false) const
  {
    nta::UInt32 n = learnt ?
      self->getNSamplingBitsPerCoincidence() :
      self->getBitPoolSizePerCoincidence();

    nta::NumpyVectorT<nta::UInt32> cpp_ind(n);
    nta::NumpyVectorT<nta::Real32> cpp_nz(n);
    self->get_cm_row_sparse(row, cpp_ind.begin(), cpp_nz.begin(), learnt);

    PyObject *toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, cpp_ind.forPython());
    PyTuple_SET_ITEM(toReturn, 1, cpp_nz.forPython());
    return toReturn;
  }

  inline PyObject* getHistogram(nta::UInt32 c) const
  {
    nta::NumpyVectorT<nta::UInt32> cpp_ind(self->getBitPoolSizePerCoincidence());
    nta::NumpyVectorT<nta::Real32> cpp_nz(self->getBitPoolSizePerCoincidence());
    self->get_cm_row_sparse(c, cpp_ind.begin(), cpp_nz.begin());
    return cpp_nz.forPython();
  }

  inline PyObject* getMasterLearnedCoincidence(nta::UInt32 m)
  {
    nta::UInt32 n = self->getNSamplingBitsPerCoincidence();
    nta::NumpyVectorT<nta::UInt32> py_rows(n);
    nta::NumpyVectorT<nta::UInt32> py_cols(n);
    self->getMasterLearnedCoincidence(m, py_rows.begin(), py_cols.begin());
    PyObject* toReturn = PyTuple_New(2);
    PyTuple_SET_ITEM(toReturn, 0, py_rows.forPython());
    PyTuple_SET_ITEM(toReturn, 1, py_cols.forPython());
    return toReturn;
  }

  inline PyObject* getMasterHistogram(nta::UInt32 m)
  {
    nta::UInt32 n = self->getBitPoolSizePerCoincidence();
    std::vector<nta::UInt32> rows(n), cols(n);
    std::vector<nta::Real32> vals(n);
    self->getMasterHistogram(m, rows.begin(), cols.begin(), vals.begin());
    nta::NumpyVectorT<nta::Real32> mat(self->getRFSide() * self->getRFSide());
    for (size_t i = 0; i != n; ++i)
      mat.set(rows[i] * self->getRFSide() + cols[i], vals[i]);
    return mat.forPython();
  }

  inline PyObject* getDenseOutput() const
  {
    nta::NumpyVectorT<nta::Real32> y(self->getNColumns());
    self->get_dense_output(y.begin());
    return y.forPython();
  }

  inline PyObject* toPyString() const
  {
    SharedPythonOStream py_s(self->persistent_size());
    std::ostream& s = py_s.getStream();
    self->save(s);
    return py_s.close();
  }

  inline bool fromPyString(PyObject *s)
  {
    Py_ssize_t n = 0;
    char *buf = 0;
    int res = PyString_AsStringAndSize(s, &buf, &n); // Reference-neutral.
    if((res == 0) && (n > 0)) {
      std::istringstream s(std::string(buf, n));
      self->load(s);
      return true;
    } else {
      throw std::runtime_error("Failed to load FDRCSpatial");
      return false;
    }
  }
}

//--------------------------------------------------------------------------------
// LearningSet for continuous FDR TP
//--------------------------------------------------------------------------------
%extend nta::algorithms::Inhibition
{
  %pythoncode %{

    def __init__(self, *args):
      this = _ALGORITHMS.new_Inhibition(*args)
      try:
        self.this.append(this)
      except:
        self.this = this
  %}

  inline
    nta::UInt32 compute(PyObject* py_x, PyObject* py_y, nta::UInt32 stimulus_threshold,
                          nta::Real32 k =.95f)
  {
    PyArrayObject* _x = (PyArrayObject*) py_x;
    CHECKSIZE(_x);
    nta::Real32* x = (nta::Real32*)(_x->data);

    PyArrayObject* _y = (PyArrayObject*) py_y;
    CHECKSIZE(_y);
    nta::UInt32* y = (nta::UInt32*)(_y->data);

    return self->compute(x, y, stimulus_threshold, k);
  }

}; // end extend nta::Inhibition

//--------------------------------------------------------------------------------
%extend nta::algorithms::Inhibition2
{
  %pythoncode %{

    def __init__(self, *args):
      this = _ALGORITHMS.new_Inhibition2(*args)
      try:
        self.this.append(this)
      except:
        self.this = this
  %}

  inline
    nta::UInt32 compute(PyObject* py_x, PyObject* py_y,
        nta::Real32 stimulus_threshold, nta::Real32 add_to_winners)
  {
    PyArrayObject* _x = (PyArrayObject*) py_x;
    CHECKSIZE(_x);
    nta::Real32* x = (nta::Real32*)(_x->data);

    PyArrayObject* _y = (PyArrayObject*) py_y;
    CHECKSIZE(_y);
    nta::UInt32* y = (nta::UInt32*)(_y->data);

    return self->compute(x, y, stimulus_threshold, add_to_winners);
  }

}; // end extend nta::Inhibition2

//--------------------------------------------------------------------------------
%inline {

inline PyObject* generate2DGaussianSample(nta::UInt32 nrows, nta::UInt32 ncols,
                                          nta::UInt32 nnzpr, nta::UInt32 rf_x,
                                          nta::Real32 sigma,
                                          nta::Int32 seed =-1,
                                          bool sorted =true)
{
  std::vector<std::pair<nta::UInt32, nta::Real32> > x;
  nta::gaussian_2d_pair_sample(nrows, ncols, nnzpr, rf_x, sigma, x,
                               (nta::Real32) 1.0f, seed, sorted);
  PyObject* toReturn = PyList_New(nrows);
  for (size_t i = 0; i != nrows; ++i) {
    PyObject* one_master = PyList_New(nnzpr);
    for (size_t j = 0; j != nnzpr; ++j)
      PyList_SET_ITEM(one_master, j, PyInt_FromLong(x[i*nnzpr+j].first));
    PyList_SET_ITEM(toReturn, i, one_master);
  }
  return toReturn;
}
}

//--------------------------------------------------------------------------------
// Optimizations for FDRCSpatial2
%inline {

  // Compute overlaps
  inline void cpp_overlap(PyObject* py_cloneMapFlat,
                          PyObject* py_inputSlices,
                          PyObject* py_coincSlices,
                          PyObject* py_inputShaped,
                          PyObject* py_masterConnectedM,
                          nta::Real32 stimulusThreshold,
                          PyObject* py_overlaps)
  {
    PyArrayObject* _cloneMap = (PyArrayObject*) py_cloneMapFlat;
    CHECKSIZE(_cloneMap);
    nta::UInt32* cloneMap = (nta::UInt32*)(_cloneMap->data);
    nta::UInt32 nColumns = _cloneMap->dimensions[0];

    PyArrayObject* _inputSlices = (PyArrayObject*) py_inputSlices;
    CHECKSIZE(_inputSlices);
    nta::UInt32* inputSlices = (nta::UInt32*)(_inputSlices->data);

    PyArrayObject* _coincSlices = (PyArrayObject*) py_coincSlices;
    CHECKSIZE(_coincSlices);
    nta::UInt32* coincSlices = (nta::UInt32*)(_coincSlices->data);
    //nta::UInt32 coincNCols = _coincSlices->dimensions[1];

    PyArrayObject* _inputShaped = (PyArrayObject*) py_inputShaped;
    CHECKSIZE(_inputShaped);
    nta::Real32* inputShaped = (nta::Real32*)(_inputShaped->data);
    nta::UInt32 inputNCols = _inputShaped->dimensions[1];

    PyArrayObject* _masterConnectedM = (PyArrayObject*) py_masterConnectedM;
    // A bool's size is one byte both in Python and C++
    bool* masterConnectedM = (bool*)(_masterConnectedM->data);
    nta::UInt32 masterNRows = _masterConnectedM->dimensions[1];
    nta::UInt32 masterNCols = _masterConnectedM->dimensions[2];
    nta::UInt32 masterSize = masterNRows * masterNCols;

    PyArrayObject* _overlaps = (PyArrayObject*) py_overlaps;
    CHECKSIZE(_overlaps);
    nta::Real32* overlaps = (nta::Real32*)(_overlaps->data);

    nta::UInt32 inputStartC_p = 0, inputStopC_p = 0;
    nta::Real32 inputSum = 0.0;

    for (nta::UInt32 columnNum = 0; columnNum != nColumns; ++columnNum) {

      nta::UInt32 masterNum = cloneMap[columnNum];

      nta::UInt32 inputStartR = inputSlices[4*columnNum];
      nta::UInt32 inputStopR = inputSlices[4*columnNum+1];
      nta::UInt32 inputStartC = inputSlices[4*columnNum+2];
      nta::UInt32 inputStopC = inputSlices[4*columnNum+3];

      nta::UInt32 coincStartR = coincSlices[4*columnNum];
      //nta::UInt32 coincStopR = coincSlices[4*columnNum+1];
      nta::UInt32 coincStartC = coincSlices[4*columnNum+2];
      //nta::UInt32 coincStopC = coincSlices[4*columnNum+3];

      bool* masterConnected = masterConnectedM + masterNum * masterSize;

      overlaps[columnNum] = 0;

      nta::UInt32 r_input, c_input, r_coinc, c_coinc;

      if (inputStartC == 0) {

        inputSum = 0;

        for (r_input = inputStartR; r_input != inputStopR; ++r_input)
          for (c_input = inputStartC; c_input != inputStopC; ++c_input)
            inputSum += inputShaped[r_input*inputNCols+c_input];

      } else {

        for (r_input = inputStartR; r_input != inputStopR; ++r_input)
          for (c_input = inputStartC_p; c_input < inputStartC; ++c_input)
            inputSum -= inputShaped[r_input*inputNCols+c_input];

        for (r_input = inputStartR; r_input != inputStopR; ++r_input)
          for (c_input = inputStopC_p; c_input < inputStopC; ++c_input)
            inputSum += inputShaped[r_input*inputNCols+c_input];
      }

      inputStartC_p = inputStartC;
      inputStopC_p = inputStopC;

      if (inputSum < stimulusThreshold)
        continue;

      nta::Real32 sum = 0.0;

      for (r_input = inputStartR, r_coinc = coincStartR;
           r_input != inputStopR; ++r_input, ++r_coinc)
        for (c_input = inputStartC, c_coinc = coincStartC;
             c_input != inputStopC; ++c_input, ++c_coinc)
          sum += inputShaped[r_input*inputNCols+c_input]
            * masterConnected[r_coinc*masterNCols+c_coinc];

      if (sum >= stimulusThreshold)
        overlaps[columnNum] = sum;
    }
  }



  // Compute overlaps taking an array of SparseBinaryMatrices
  // WORK IN PROGRESS..NOT DONE YET....
  inline void cpp_overlap_sbm(PyObject* py_cloneMapFlat,
                          PyObject* py_inputSlices,
                          PyObject* py_coincSlices,
                          PyObject* py_inputShaped,
                          PyObject* py_masterConnectedM,
                          nta::Real32 stimulusThreshold,
                          PyObject* py_overlaps)
  {

    /*
    static int attach = 1;
    if (attach) {
      pid_t pid = ::getpid();
      std::cout << "Waiting for connect to process ID " <<  pid << "...";
      std::string str;
      std::cin >> str;
      std::cout << "Connected.";
      attach = 0;
    }

    PyArrayObject* _cloneMap = (PyArrayObject*) py_cloneMapFlat;
    CHECKSIZE(_cloneMap);
    nta::UInt32* cloneMap = (nta::UInt32*)(_cloneMap->data);
    nta::UInt32 nColumns = _cloneMap->dimensions[0];

    PyArrayObject* _inputSlices = (PyArrayObject*) py_inputSlices;
    CHECKSIZE(_inputSlices);
    nta::UInt32* inputSlices = (nta::UInt32*)(_inputSlices->data);

    PyArrayObject* _coincSlices = (PyArrayObject*) py_coincSlices;
    CHECKSIZE(_coincSlices);
    nta::UInt32* coincSlices = (nta::UInt32*)(_coincSlices->data);
    //nta::UInt32 coincNCols = _coincSlices->dimensions[1];

    PyArrayObject* _inputShaped = (PyArrayObject*) py_inputShaped;
    CHECKSIZE(_inputShaped);
    nta::Real32* inputShaped = (nta::Real32*)(_inputShaped->data);
    nta::UInt32 inputNCols = _inputShaped->dimensions[1];


    typedef nta::SparseBinaryMatrix<nta::UInt32,nta::UInt32>* SBM32Ptr;

    PyObject* p = PyList_GET_ITEM(py_masterConnectedM, 0);


    nta::UInt32 masterNRows = masterConnectedM->nRows();
    masterConnectedM = (SBM32Ptr)(PyList_GET_ITEM(_masterConnectedM, 1))
    nta::UInt32 masterNRows2 = masterConnectedM->nRows();


    PyArrayObject* _overlaps = (PyArrayObject*) py_overlaps;
    CHECKSIZE(_overlaps);
    nta::Real32* overlaps = (nta::Real32*)(_overlaps->data);

    nta::UInt32 inputStartC_p = 0, inputStopC_p = 0;
    nta::Real32 inputSum = 0.0;

    for (nta::UInt32 columnNum = 0; columnNum != nColumns; ++columnNum) {

      nta::UInt32 masterNum = cloneMap[columnNum];

      nta::UInt32 inputStartR = inputSlices[4*columnNum];
      nta::UInt32 inputStopR = inputSlices[4*columnNum+1];
      nta::UInt32 inputStartC = inputSlices[4*columnNum+2];
      nta::UInt32 inputStopC = inputSlices[4*columnNum+3];

      nta::UInt32 coincStartR = coincSlices[4*columnNum];
      //nta::UInt32 coincStopR = coincSlices[4*columnNum+1];
      nta::UInt32 coincStartC = coincSlices[4*columnNum+2];
      //nta::UInt32 coincStopC = coincSlices[4*columnNum+3];

      SBM32Ptr masterConnected = masterConnectedM[masterNum];

      overlaps[columnNum] = 0;

      nta::UInt32 r_input, c_input, r_coinc, c_coinc;
      nta::Real32 sum = 0.0;

      for (r_input = inputStartR, r_coinc = coincStartR;
           r_input != inputStopR; ++r_input, ++r_coinc)
        for (c_input = inputStartC, c_coinc = coincStartC;
             c_input != inputStopC; ++c_input, ++c_coinc)
          sum += inputShaped[r_input*inputNCols+c_input]
                 * masterConnected[r_coinc*masterNCols+c_coinc];

      if (sum >= stimulusThreshold)
        overlaps[columnNum] = sum;
    }
    */
  }



  // Update duty cycles
  inline void cpp_updateDutyCycles(nta::UInt32 dutyCyclePeriod,
                                   PyObject* py_cloneMapFlat,
                                   PyObject* py_onCells,
                                   PyObject* py_dutyCycles)
  {
    PyArrayObject* _cloneMap = (PyArrayObject*) py_cloneMapFlat;
    CHECKSIZE(_cloneMap);
    nta::UInt32* cloneMap = (nta::UInt32*)(_cloneMap->data);

    PyArrayObject* _onCells = (PyArrayObject*) py_onCells;
    CHECKSIZE(_onCells);
    nta::UInt32* onCells = (nta::UInt32*)(_onCells->data);
    nta::UInt32 nColumns = _onCells->dimensions[0];

    PyArrayObject* _dutyCycles = (PyArrayObject*) py_dutyCycles;
    CHECKSIZE(_dutyCycles);
    nta::Real32* dutyCycles = (nta::Real32*)(_dutyCycles->data);

    nta::Real32 dcp = (nta::Real32) dutyCyclePeriod;
    nta::Real32 dcp_1 = dcp - 1.0;

    for (nta::UInt32 columnNum = 0; columnNum != nColumns; ++columnNum) {
      nta::UInt32 masterNum = cloneMap[columnNum];
      dutyCycles[masterNum] =
        (dcp_1 * dutyCycles[masterNum] + onCells[columnNum]) / dcp;
    }
  }

  // Adjust master valid permanence
  // This code implements a bit more, commented out for now
  inline void adjustMasterValidPermanence(nta::UInt32 columnNum,
                                          nta::UInt32 masterNum,
                                          nta::UInt32 inputNCols,
                                          nta::UInt32 masterNCols,
                                          //nta::Real32 stimulusThreshold,
                                          nta::Real32 synPermActiveInc,
                                          nta::Real32 synPermInactiveDec,
                                          nta::Real32 synPermActiveSharedDec,
                                          //nta::Real32 synPermBelowStimulusInc,
                                          //nta::Real32 synPermConnected,
                                          //nta::Real32 synPermMin,
                                          //nta::Real32 synPermMax,
                                          PyObject* py_inputShaped,
                                          PyObject* py_inputUse,
                                          PyObject* py_inputSlices,
                                          PyObject* py_coincSlices,
                                          PyObject* py_synPermBoostFactors,
                                          PyObject* py_masterPermanence)
                                          //PyObject* py_masterPotential)
  {
    PyArrayObject* _input = (PyArrayObject*) py_inputShaped;
    nta::Real32* input = (nta::Real32*)(_input->data);

    PyArrayObject* _inputUse = (PyArrayObject*) py_inputUse;
    nta::UInt32* inputUse = (nta::UInt32*)(_inputUse->data);

    PyArrayObject* _inputSlices = (PyArrayObject*) py_inputSlices;
    nta::UInt32* inputSlices = (nta::UInt32*)(_inputSlices->data);

    PyArrayObject* _coincSlices = (PyArrayObject*) py_coincSlices;
    nta::UInt32* coincSlices = (nta::UInt32*)(_coincSlices->data);

    PyArrayObject* _spbf = (PyArrayObject*) py_synPermBoostFactors;
    nta::Real32* spbf = (nta::Real32*)(_spbf->data);

    PyArrayObject* _mpe = (PyArrayObject*) py_masterPermanence;
    nta::Real32* perm = (nta::Real32*)(_mpe->data);

    //PyArrayObject* _mpo = (PyArrayObject*) py_masterPotential;
    //bool* potential = (bool*)(_mpo->data);

    nta::UInt32 inputStartR = inputSlices[4*columnNum];
    nta::UInt32 inputStopR = inputSlices[4*columnNum+1];
    nta::UInt32 inputStartC = inputSlices[4*columnNum+2];
    nta::UInt32 inputStopC = inputSlices[4*columnNum+3];

    nta::UInt32 coincStartR = coincSlices[4*columnNum];
    //nta::UInt32 coincStopR = coincSlices[4*columnNum+1];
    nta::UInt32 coincStartC = coincSlices[4*columnNum+2];
    //nta::UInt32 coincStopC = coincSlices[4*columnNum+3];

    nta::UInt32 r_input = inputStartR, c_input = inputStartC;
    nta::UInt32 r_coinc = coincStartR, c_coinc = coincStartC;

    // Vectors to remember the indices of the potential synapses
    // and which syns are connected
    //std::vector<nta::UInt32> potentialV;
    //std::vector<nta::UInt32> connectedSyns;

    for (; r_input != inputStopR; ++r_input, ++r_coinc) {

      c_input = inputStartC;
      c_coinc = coincStartC;

      for (; c_input != inputStopC; ++c_input, ++c_coinc) {

        nta::UInt32 mp_idx = r_coinc*masterNCols + c_coinc;

        // Skip updates of permanence based on input
        // if not even a potential synapse
        //if (potential[mp_idx]) {

          // Remember index of potential synapes for later
          //potentialV.push_back(mp_idx);
          nta::UInt32 input_idx = r_input*inputNCols + c_input;

          // Decrease permanence on inactive inputs
          if (input[input_idx] == 0.0) {

            perm[mp_idx] -= synPermInactiveDec;

          } else { // Active inputs

            // Increase permanence on active inputs
            perm[mp_idx] += spbf[masterNum] * synPermActiveInc;

            // Decrease dupe inputs
            if (inputUse[input_idx] > 1)
              perm[mp_idx] -= synPermActiveSharedDec;
          }

          // Clip
          //if (perm[mp_idx] < synPermMin)
          //  perm[mp_idx] = synPermMin;

          //if (perm[mp_idx] > synPermMax)
          //  perm[mp_idx] = synPermMax;

          //} // End permanence updates based on inputs

        // Find connected synapses
        //if (perm[mp_idx] >= synPermConnected)
        //  connectedSyns.push_back(mp_idx);

      }
    } // End loops on this master

    // Bump up all (potential) permanences a bit if the number of connected
    // synapes is below stimulusThreshold
    /* while (connectedSyns.size() < stimulusThreshold) { */

    /*   for (size_t k = 0; k != potentialV.size(); ++k) { */
    /*     bool isCandidate = perm[potentialV[k]] < stimulusThreshold; */
    /*     perm[potentialV[k]] += synPermBelowStimulusInc; */
    /*     if (isCandidate && perm[potentialV[k]] >= synPermConnected) */
    /*       connectedSyns.push_back(potentialV[k]); */
    /*   } */
    /* } */
  }

  //--------------------------------------------------------------------------------
  inline nta::UInt32 getSegmentActivityLevel(PyObject* py_seg, PyObject* py_state,
                                             bool connectedSynapsesOnly,
                                             nta::Real32 connectedPerm)
  {
    PyArrayObject* _state = (PyArrayObject*) py_state;
    nta::Byte* state = (nta::Byte*) _state->data;
    nta::UInt32 stride0 = _state->strides[0];

    nta::py::List seg;
    seg.assign(py_seg);
    Py_ssize_t n = seg.getCount();
    nta::UInt32 activity = 0;

    if (connectedSynapsesOnly)
      for (Py_ssize_t i = 0; i < n; ++i) {
        nta::py::List syn;
        syn.assign(seg.fastGetItem(i));
        nta::Real32 p = (nta::Real32) PyFloat_AsDouble(syn.fastGetItem(2));
        if (p >= connectedPerm) {
          nta::UInt32 c = (nta::UInt32) PyLong_AsLong(syn.fastGetItem(0));
          nta::UInt32 j = (nta::UInt32) PyLong_AsLong(syn.fastGetItem(1));
          activity += state[c * stride0 + j];
        }
      }
    else
      for (Py_ssize_t i = 0; i < n; ++i) {
        nta::py::List syn;
        syn.assign(seg.fastGetItem(i));
        nta::UInt32 c = (nta::UInt32) PyLong_AsLong(syn.fastGetItem(0));
        nta::UInt32 j = (nta::UInt32) PyLong_AsLong(syn.fastGetItem(1));
        activity += state[c * stride0 + j];
      }

    return activity;
  }

  //--------------------------------------------------------------------------------
  inline nta::Real32
    getSegmentAvgPermanence(PyObject* py_seg, nta::Real32 connectedPerm)
  {
     nta::py::List seg;
     seg.assign(py_seg);
     Py_ssize_t n = seg.getCount();
     nta::Real32 avg_p = 0;
     nta::UInt32 count = 0;

     for (Py_ssize_t i = 0; i < n; ++i) {
       nta::py::List syn;
       syn.assign(seg.fastGetItem(i));
       nta::Real32 p = (nta::Real32) PyFloat_AsDouble(syn.fastGetItem(2));
       if (p >= connectedPerm) {
        ++count;
        avg_p += p;
       }
     }

    return avg_p / count;
  }

  //--------------------------------------------------------------------------------
  inline nta::Real32
    getSegmentSumActivePermanence(PyObject* py_seg, PyObject* py_state,
                                  nta::Real32 connectedPerm)
  {
    PyArrayObject* _state = (PyArrayObject*) py_state;
    nta::Byte* state = (nta::Byte*) _state->data;
    nta::UInt32 stride0 = _state->strides[0];

    nta::py::List seg;
    seg.assign(py_seg);
    Py_ssize_t n = seg.getCount();
    nta::Real32 sum_p = 0;

    for (Py_ssize_t i = 0; i < n; ++i) {
      nta::py::List syn;
      syn.assign(seg.fastGetItem(i));
      nta::Real32 p = (nta::Real32) PyFloat_AsDouble(syn.fastGetItem(2));
      if (p >= connectedPerm) {
        nta::UInt32 c = (nta::UInt32) PyLong_AsLong(syn.fastGetItem(0));
        nta::UInt32 j = (nta::UInt32) PyLong_AsLong(syn.fastGetItem(1));
        sum_p += state[c * stride0 + j]*p;
      }
    }

    return sum_p;
  }

  //--------------------------------------------------------------------------------
  inline bool isSegmentActive(PyObject* py_seg, PyObject* py_state,
                              nta::Real32 connectedPerm,
                              nta::UInt32 activationThreshold)
  {
    PyArrayObject* _state = (PyArrayObject*) py_state;
    nta::Byte* state = (nta::Byte*) _state->data;
    nta::UInt32 stride0 = _state->strides[0];

    nta::py::List seg;
    seg.assign(py_seg);
    Py_ssize_t n = seg.getCount();
    nta::UInt32 activity = 0;

    if (n < (Py_ssize_t) activationThreshold)
      return false;

    for (Py_ssize_t i = 0; i < n; ++i) {
      nta::py::List syn;
      syn.assign(seg.fastGetItem(i));
      nta::Real32 p = (nta::Real32) PyFloat_AsDouble(syn.fastGetItem(2));
      if (p >= connectedPerm) {
        nta::UInt32 c = (nta::UInt32) PyLong_AsLong(syn.fastGetItem(0));
        nta::UInt32 j = (nta::UInt32) PyLong_AsLong(syn.fastGetItem(1));
        activity += state[c * stride0 + j];
        if (activity >= activationThreshold)
          return true;
      }
    }

    return false;
  }
}


//--------------------------------------------------------------------------------
// NEW ALGORITHMS (Cells4)
%include <nta/algorithms/Segment.hpp>
%include <nta/algorithms/SegmentUpdate.hpp>
%include <nta/algorithms/OutSynapse.hpp>
%include <nta/algorithms/InSynapse.hpp>
%include <nta/algorithms/Cell.hpp>



//--------------------------------------------------------------------------------
%extend nta::algorithms::Cells4::Segment<nta::UInt32, nta::Real32>
{
  %pythoncode %{
    def __init__(self, *args):
      self.this = _ALGORITHMS.new_Segment3_32()
  %}

  inline bool isActive(PyObject* py_activities,
                       nta::Real32 permConnected,
                       nta::UInt32 activationThreshold) const
  {
    PyArrayObject* act = (PyArrayObject*) py_activities;
    return self->isActive((nta::UInt32*) act->data,
                          permConnected,
                          activationThreshold);
  }
};

%pythoncode %{

  def Segment3(*args, **keywords):
     return Segment3_32(*args)
%}



//--------------------------------------------------------------------------------
/*
%inline {

  inline void scalarEncoding(nta::UInt32 minval, nta::UInt32 nInternal,
                             nta::Real32 range, nta::UInt32 padding, nta::UInt32 n,
                             nta::Real32 input, PyObject* py_output)
  {
    PyArrayObject* p_output = (PyArrayObject*) py_output;
    nta::Real32 output = p_output->data;
    int centerbin = padding + int((input - minval) * nInternal / range);

  }

 }
*/


//--------------------------------------------------------------------------------
// EVEN NEWER ALGORITHMS (Cells4)
%include <nta/algorithms/Cells4.hpp>


//--------------------------------------------------------------------------------
%extend nta::algorithms::Cells4::Cells4
{
  %pythoncode %{

    def __init__(self, *args, **kwargs):
      self.this = _ALGORITHMS.new_Cells4(*args, **kwargs)

    def __setstate__(self, inString):
      self.this = _ALGORITHMS.new_Cells4()
      self.loadFromString(inString)
  %}

  void loadFromString(const std::string& inString)
  {
    std::istringstream inStream(inString);
    self->load(inStream);
  }

  PyObject* __getstate__()
  {
    SharedPythonOStream py_s(self->persistentSize());
    std::ostream& s = py_s.getStream();
    self->save(s);
    return py_s.close();
  }

  inline void setStatePointers(PyObject* py_infActiveStateT,
                               PyObject* py_infActiveStateT1,
                               PyObject* py_infPredictedStateT,
                               PyObject* py_infPredictedStateT1,
                               PyObject* py_colConfidenceT,
                               PyObject* py_colConfidenceT1,
                               PyObject* py_cellConfidenceT,
                               PyObject* py_cellConfidenceT1)
  {
    PyArrayObject* infActiveStateT = (PyArrayObject*) py_infActiveStateT;
    PyArrayObject* infActiveStateT1 = (PyArrayObject*) py_infActiveStateT1;
    PyArrayObject* infPredictedStateT = (PyArrayObject*) py_infPredictedStateT;
    PyArrayObject* infPredictedStateT1 = (PyArrayObject*) py_infPredictedStateT1;
    PyArrayObject* colConfidenceT = (PyArrayObject*) py_colConfidenceT;
    PyArrayObject* colConfidenceT1 = (PyArrayObject*) py_colConfidenceT1;
    PyArrayObject* cellConfidenceT = (PyArrayObject*) py_cellConfidenceT;
    PyArrayObject* cellConfidenceT1 = (PyArrayObject*) py_cellConfidenceT1;

    self->setStatePointers((nta::Byte*) infActiveStateT->data,
                           (nta::Byte*) infActiveStateT1->data,
                           (nta::Byte*) infPredictedStateT->data,
                           (nta::Byte*) infPredictedStateT1->data,
                           (nta::Real32*) colConfidenceT->data,
                           (nta::Real32*) colConfidenceT1->data,
                           (nta::Real32*) cellConfidenceT->data,
                           (nta::Real32*) cellConfidenceT1->data);
  }

  inline PyObject* getStates() const
  {
    nta::UInt32 nCells = self->nCells();
    nta::UInt32 nColumns = self->nColumns();

    nta::Byte* cpp_activeT, *cpp_activeT1;
    nta::Byte* cpp_predT, *cpp_predT1;
    nta::Real32* cpp_colConfidenceT, *cpp_colConfidenceT1;
    nta::Real32* cpp_confidenceT, *cpp_confidenceT1;

    self->getStatePointers(cpp_activeT, cpp_activeT1,
                           cpp_predT, cpp_predT1,
                           cpp_colConfidenceT, cpp_colConfidenceT1,
                           cpp_confidenceT, cpp_confidenceT1);

    nta::NumpyVectorT<nta::Byte> activeT(nCells, cpp_activeT);
    nta::NumpyVectorT<nta::Byte> activeT1(nCells, cpp_activeT1);
    nta::NumpyVectorT<nta::Byte> predT(nCells, cpp_predT);
    nta::NumpyVectorT<nta::Byte> predT1(nCells, cpp_predT1);
    nta::NumpyVectorT<nta::Real32> colConfidenceT(nColumns, cpp_colConfidenceT);
    nta::NumpyVectorT<nta::Real32> colConfidenceT1(nColumns, cpp_colConfidenceT1);
    nta::NumpyVectorT<nta::Real32> confidenceT(nCells, cpp_confidenceT);
    nta::NumpyVectorT<nta::Real32> confidenceT1(nCells, cpp_confidenceT1);

    PyObject *result = PyTuple_New(8);
    PyTuple_SET_ITEM(result, 0, activeT.forPython());
    PyTuple_SET_ITEM(result, 1, activeT1.forPython());
    PyTuple_SET_ITEM(result, 2, predT.forPython());
    PyTuple_SET_ITEM(result, 3, predT1.forPython());
    PyTuple_SET_ITEM(result, 4, colConfidenceT.forPython());
    PyTuple_SET_ITEM(result, 5, colConfidenceT1.forPython());
    PyTuple_SET_ITEM(result, 6, confidenceT.forPython());
    PyTuple_SET_ITEM(result, 7, confidenceT1.forPython());

    return result;
  }

  inline PyObject* getLearnStates() const
  {
    nta::UInt32 nCells = self->nCells();

    nta::Byte* cpp_activeT, *cpp_activeT1;
    nta::Byte* cpp_predT, *cpp_predT1;

    self->getLearnStatePointers(cpp_activeT, cpp_activeT1,
                           cpp_predT, cpp_predT1);

    nta::NumpyVectorT<nta::Byte> activeT(nCells, cpp_activeT);
    nta::NumpyVectorT<nta::Byte> activeT1(nCells, cpp_activeT1);
    nta::NumpyVectorT<nta::Byte> predT(nCells, cpp_predT);
    nta::NumpyVectorT<nta::Byte> predT1(nCells, cpp_predT1);

    PyObject *result = PyTuple_New(4);
    PyTuple_SET_ITEM(result, 0, activeT.forPython());
    PyTuple_SET_ITEM(result, 1, activeT1.forPython());
    PyTuple_SET_ITEM(result, 2, predT.forPython());
    PyTuple_SET_ITEM(result, 3, predT1.forPython());

    return result;
  }

  /*
  inline std::pair<nta::UInt32, nta::UInt32>
    getBestMatchingCell(nta::UInt32 colIdx, PyObject* py_state)
    {
      PyArrayObject* st = (PyArrayObject*) py_state;
      return self->getBestMatchingCell(colIdx, (nta::UInt32*) st->data);
    }
  */

  /*
  inline void computeUpdate(nta::UInt32 colIdx, nta::UInt32 cellIdxInCol,
                            nta::UInt32 segIdx, PyObject* py_state,
                            PyObject* py_learnState,
                            bool sequenceSegmentFlag = false,
                            bool newSynapsesFlag = false)
  {
    PyArrayObject* st = (PyArrayObject*) py_state;
    PyArrayObject* lst = (PyArrayObject*) py_learnState;
    self->computeUpdate(colIdx, cellIdxInCol, segIdx, (nta::UInt32*) st->data,
                        (nta::UInt32*) lst->data,
                        sequenceSegmentFlag, newSynapsesFlag);
  }
  */

  inline PyObject* compute(PyObject* py_x, bool doInference, bool doLearning)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    nta::NumpyVectorT<nta::Real32> y(self->nCells());
    self->compute((nta::Real32*) x->data, y.begin(), doInference, doLearning);
    return y.forPython();
  }
}

%include <nta/algorithms/SpatialPooler.hpp>

%extend nta::algorithms::spatial_pooler::SpatialPooler
{
  %pythoncode %{
    import numpy
    from nupic.bindings.math import (SM32 as SparseMatrix,
                                     SM_01_32_32 as SparseBinaryMatrix)

    def __init__(self,
                 inputDimensions=[32,32],
                 columnDimensions=[64,64],
                 potentialRadius=16,
                 potentialPct=0.5,
                 globalInhibition=False,
                 localAreaDensity=-1.0,
                 numActiveColumnsPerInhArea=10.0,
                 stimulusThreshold=0,
                 synPermInactiveDec=0.01,
                 synPermActiveInc=0.1,
                 synPermConnected=0.10,
                 minPctOverlapDutyCycle=0.001,
                 minPctActiveDutyCycle=0.001,
                 dutyCyclePeriod=1000,
                 maxBoost=10.0,
                 seed=-1,
                 spVerbosity=0):
      self.this = _ALGORITHMS.new_SpatialPooler()
      _ALGORITHMS.SpatialPooler_initialize(
        self, inputDimensions, columnDimensions, potentialRadius, potentialPct, 
        globalInhibition, localAreaDensity, numActiveColumnsPerInhArea, 
        stimulusThreshold, synPermInactiveDec, synPermActiveInc, synPermConnected, 
        minPctOverlapDutyCycle, minPctActiveDutyCycle, dutyCyclePeriod, maxBoost, 
        seed, spVerbosity)

    def __getstate__(self):
      # Save the local attributes but override the C++ spatial pooler with the
      # string representation.
      d = dict(self.__dict__)
      d["this"] = self.getCState()
      return d

    def __setstate__(self, state):
      # Create an empty C++ spatial pooler and populate it from the serialized
      # string.
      self.this = _ALGORITHMS.new_SpatialPooler()
      if isinstance(state, str):
        self.loadFromString(state)
        self.valueToCategory = {}
      else:
        self.loadFromString(state["this"])
        # Use the rest of the state to set local Python attributes.
        del state["this"]
        self.__dict__.update(state)

    def compute(self, inputVector, learn, activeArray, stripNeverLearned=True):
      self.convertedCompute(inputVector, learn, activeArray, stripNeverLearned)
  %}

  inline void convertedCompute(PyObject *py_x, bool learn, PyObject *py_y,
                               bool stripNeverLearned)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    PyArrayObject* y = (PyArrayObject*) py_y;
    self->compute((nta::UInt*) x->data, (bool)learn, (nta::UInt*) y->data,
                  (bool)stripNeverLearned);
  }

  inline void stripUnlearnedColumns(PyObject *py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->stripUnlearnedColumns((nta::UInt*) x->data);
  }

  void loadFromString(const std::string& inString)
  {
    std::istringstream inStream(inString);
    self->load(inStream);
  }


  PyObject* getCState()
  {
    SharedPythonOStream py_s(self->persistentSize());
    std::ostream& s = py_s.getStream();
    // TODO: Consider writing floats as binary instead.
    s.flags(ios::scientific);
    s.precision(numeric_limits<double>::digits10 + 1);
    self->save(s);
    return py_s.close();
  }

  inline void setBoostFactors(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->setBoostFactors((nta::Real*) x->data);
  }

  inline void getBoostFactors(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->getBoostFactors((nta::Real*) x->data);
  }

  inline void setOverlapDutyCycles(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->setOverlapDutyCycles((nta::Real*) x->data);
  }

  inline void getOverlapDutyCycles(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->getOverlapDutyCycles((nta::Real*) x->data);
  }

  inline void setActiveDutyCycles(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->setActiveDutyCycles((nta::Real*) x->data);
  }

  inline void getActiveDutyCycles(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->getActiveDutyCycles((nta::Real*) x->data);
  }  


  inline void setMinOverlapDutyCycles(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->setMinOverlapDutyCycles((nta::Real*) x->data);
  }

  inline void getMinOverlapDutyCycles(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->getMinOverlapDutyCycles((nta::Real*) x->data);
  }

  inline void setMinActiveDutyCycles(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->setMinActiveDutyCycles((nta::Real*) x->data);
  }

  inline void getMinActiveDutyCycles(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->getMinActiveDutyCycles((nta::Real*) x->data);
  }  

  inline void setPotential(UInt column, PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->setPotential(column, (nta::UInt*) x->data);
  }

  inline void getPotential(UInt column, PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->getPotential(column, (nta::UInt*) x->data);
  }

  inline void setPermanence(UInt column, PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->setPermanence(column, (nta::Real*) x->data);
  }

  inline void getPermanence(UInt column, PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->getPermanence(column, (nta::Real*) x->data);
  }

  inline void getConnectedSynapses(UInt column, PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->getConnectedSynapses(column, (nta::UInt*) x->data);
  }

  inline void getConnectedCounts(PyObject* py_x)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    self->getConnectedCounts((nta::UInt*) x->data);
  }

}


%include <nta/algorithms/FlatSpatialPooler.hpp>

%extend nta::algorithms::spatial_pooler::FlatSpatialPooler
{
  %pythoncode %{ 
    import numpy

    def __init__(self,
                 inputShape=(32, 32),
                 inputBorder=8,
                 inputDensity=1.0,
                 coincidencesShape=(48, 48),
                 coincInputRadius=16,
                 coincInputPoolPct=0.5,
                 gaussianDist=False,
                 commonDistributions=False,
                 localAreaDensity=-1.0,
                 numActivePerInhArea=10.0,
                 stimulusThreshold=0,
                 synPermInactiveDec=0.01,
                 synPermActiveInc=0.1,
                 synPermActiveSharedDec=0.0,
                 synPermOrphanDec=0.0,
                 synPermConnected=0.10,
                 minPctDutyCycleBeforeInh=0.001,
                 minPctDutyCycleAfterInh=0.001,
                 dutyCyclePeriod=1000,
                 maxFiringBoost=10.0,
                 maxSSFiringBoost=2.0,
                 maxSynPermBoost=10.0,
                 minDistance=0.0,
                 cloneMap=None,
                 numCloneMasters=-1,
                 seed=-1,
                 spVerbosity=0,
                 printPeriodicStats=0,
                 testMode=False,
                 globalInhibition=False,
                 spReconstructionParam="unweighted_mean",
                 useHighTier=True,
                 randomSP=False,
              ):
      
      self.this = _ALGORITHMS.new_FlatSpatialPooler()
      _ALGORITHMS.FlatSpatialPooler_initializeFlat(
        self,
        numInputs=numpy.prod(inputShape),
        numColumns=numpy.prod(coincidencesShape),
        potentialPct = coincInputPoolPct,
        localAreaDensity=localAreaDensity,
        numActiveColumnsPerInhArea=numActivePerInhArea,
        stimulusThreshold=stimulusThreshold,
        synPermInactiveDec=synPermInactiveDec,
        synPermActiveInc=synPermActiveInc,
        synPermConnected=synPermConnected,
        minPctOverlapDutyCycles=minPctDutyCycleBeforeInh,
        minPctActiveDutyCycles=minPctDutyCycleAfterInh,
        dutyCyclePeriod=dutyCyclePeriod,
        maxBoost=maxFiringBoost,
        minDistance=minDistance,
        randomSP=randomSP,
        seed=seed,
        spVerbosity=spVerbosity
      )

    def __getstate__(self):
      # Save the local attributes but override the C++ flat spatial pooler with
      # the string representation.
      d = dict(self.__dict__)
      d["this"] = self.getCState()
      return d

    def __setstate__(self, state):
      # Create an empty C++ flat spatial pooler and populate it from the
      # serialized string.
      self.this = _ALGORITHMS.new_FlatSpatialPooler()
      if isinstance(state, str):
        self.loadFromString(state)
        self.valueToCategory = {}
      else:
        self.loadFromString(state["this"])
        # Use the rest of the state to set local Python attributes.
        del state["this"]
        self.__dict__.update(state)
  %}
}

%include <nta/algorithms/FastClaClassifier.hpp>

%pythoncode %{
  import numpy
%}

%extend nta::algorithms::cla_classifier::FastCLAClassifier
{
  %pythoncode %{
    VERSION = 0

    def __init__(self, steps=(1,), alpha=0.001, actValueAlpha=0.3, verbosity=0):
      self.this = _ALGORITHMS.new_FastCLAClassifier(
          steps, alpha, actValueAlpha, verbosity)
      self.valueToCategory = {}
      self.version = FastCLAClassifier.VERSION

    def compute(self, recordNum, patternNZ, classification, learn, infer):
      isNone = False
      noneSentinel = 3.14159
      if type(classification["actValue"]) in (int, float):
        actValue = classification["actValue"]
        category = False
      elif classification["actValue"] is None:
        # Use the sentinel value so we know if it gets used in actualValues
        # returned.
        actValue = noneSentinel
        # Turn learning off this step.
        learn = False
        category = False
        # This does not get used when learning is disabled anyway.
        classification["bucketIdx"] = 0
        isNone = True
      else:
        actValue = int(classification["bucketIdx"])
        category = True
      result = self.convertedCompute(
          recordNum, patternNZ, int(classification["bucketIdx"]),
          actValue, category, learn, infer)
      if isNone:
        for i, v in enumerate(result["actualValues"]):
          if v - noneSentinel < 0.00001:
            result["actualValues"][i] = None
      arrayResult = dict((k, numpy.array(v)) if k != "actualValues" else (k, v)
                         for k, v in result.iteritems())
      if category:
        # Convert the bucketIdx back to the original value.
        for i in xrange(len(arrayResult["actualValues"])):
          arrayResult["actualValues"][i] = self.valueToCategory.get(int(
              arrayResult["actualValues"][i]), classification["actValue"])
        self.valueToCategory[actValue] = classification["actValue"]
      return arrayResult

    def __getstate__(self):
      # Save the local attributes but override the C++ classifier with the
      # string representation.
      d = dict(self.__dict__)
      d["this"] = self.getCState()
      return d

    def __setstate__(self, state):
      # Create an empty C++ classifier and populate it from the serialized
      # string.
      self.this = _ALGORITHMS.new_FastCLAClassifier()
      if isinstance(state, str):
        self.loadFromString(state)
        self.valueToCategory = {}
      else:
        assert state["version"] == 0
        self.loadFromString(state["this"])
        # Use the rest of the state to set local Python attributes.
        del state["this"]
        self.__dict__.update(state)
  %}

  void loadFromString(const std::string& inString)
  {
    std::istringstream inStream(inString);
    self->load(inStream);
  }

  PyObject* getCState()
  {
    SharedPythonOStream py_s(self->persistentSize());
    std::ostream& s = py_s.getStream();
    // TODO: Consider writing floats as binary instead.
    s.flags(ios::scientific);
    s.precision(numeric_limits<double>::digits10 + 1);
    self->save(s);
    return py_s.close();
  }

  PyObject* convertedCompute(UInt recordNum, const vector<UInt>& patternNZ,
                             UInt bucketIdx, Real64 actValue, bool category,
                             bool learn, bool infer)
  {
    ClassifierResult result;
    self->fastCompute(recordNum, patternNZ, bucketIdx, actValue, category,
                      learn, infer, &result);
    PyObject* d = PyDict_New();
    for (map<Int, vector<Real64>*>::const_iterator it = result.begin();
         it != result.end(); ++it)
    {
      PyObject* key;
      if (it->first == -1)
      {
        key = PyString_FromString("actualValues");
      } else {
        key = PyInt_FromLong(it->first);
      }

      PyObject* value = PyList_New(it->second->size());
      for (UInt i = 0; i < it->second->size(); ++i)
      {
        PyObject* pyActValue = PyFloat_FromDouble(it->second->at(i));
        PyList_SetItem(value, i, pyActValue);
      }

      PyDict_SetItem(d, key, value);
      Py_DECREF(value);
    }
    return d;
  }
}
