%pythoncode %{
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
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

#include <Python.h>

#include <sstream>
#include <iostream>
#include <fstream>
#include <vector>

#include <nta/math/types.hpp>
#include <nta/math/convolution.hpp>
#include <nta/math/rotation.hpp>
#include <nta/math/erosion.hpp>
#include <nta/algorithms/gaborNode.hpp>
#include <nta/algorithms/imageSensorLite.hpp>
#include <nta/algorithms/scanning.hpp>

#include <nta/math/SparseMatrix.hpp>
#include <nta/math/SparseBinaryMatrix.hpp>
#include <nta/algorithms/svm.hpp>
#include <nta/algorithms/linear.hpp>
#include <nta/algorithms/spatial_pooler.hpp>
#include <nta/algorithms/flat_spatial_pooler.hpp>

#include <nta/algorithms/Cells4.hpp>
#include <nta/algorithms/classifier_result.hpp>
#include <nta/algorithms/fast_cla_classifier.hpp>
#include <nta/algorithms/SegmentUpdate.hpp>
#include <nta/algorithms/OutSynapse.hpp>
#include <nta/algorithms/InSynapse.hpp>
#include <nta/algorithms/Cell.hpp>

#include <numpy/arrayobject.h>
#include <lang/py/support/NumpyVector.hpp>
#include <lang/py/support/PythonStream.hpp>
#include <lang/py/support/PyHelpers.hpp>

/// %template(_InSynapse) nta::algorithms::Cells3::InSynapse<nta::UInt32, nta::Real32>;
/// %template(Segment3_32) nta::algorithms::Cells3::Segment<nta::UInt32, nta::Real32>;
/// %template(Cell3_32) nta::algorithms::Cells3::Cell<nta::UInt32, nta::Real32>;
/// %template(Cells3_32) nta::algorithms::Cells3::Cells3<nta::UInt32, nta::Real32>;
using namespace nta::algorithms::Cells4;
using namespace nta::algorithms::cla_classifier;
using namespace nta;

#define CHECKSIZE(var) \
  NTA_ASSERT((var)->descr->elsize == 4) << " elsize:" << (var)->descr->elsize


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
%include <nta/algorithms/linear.hpp>

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
%include <nta/algorithms/svm.hpp>

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
%include <nta/math/convolution.hpp>

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
%include <nta/math/rotation.hpp>

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
%include <nta/math/erosion.hpp>

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

%include <nta/algorithms/scanning.hpp>
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

%include <nta/math/types.hpp>
 ///%include <nta/algorithms/Cells.hpp>

 ///%template(Segment_32) nta::algorithms::Segment<nta::UInt32, nta::Real32>;
 ///%template(Branch_32) nta::algorithms::Branch<nta::UInt32, nta::Real32>;
 ///%template(Cell_32) nta::algorithms::Cell<nta::UInt32, nta::Real32>;
 ///%template(SegVector_32) std::vector<nta::algorithms::Segment<nta::UInt32, nta::Real32>*>;
 ///%template(BranchVector_32) std::vector<nta::algorithms::Branch<nta::UInt32, nta::Real32>*>;
 ///%template(Cells_32) nta::algorithms::Cells<nta::UInt32, nta::Real32>;
 ///%template(Int_Seg_32) std::pair<nta::UInt32, nta::algorithms::Segment<nta::UInt32,nta::Real32>*>;

// Already seen by swig on linux32 where size_t is the same size as unsigned int
#if !defined(NTA_PLATFORM_linux32) && !defined(NTA_PLATFORM_linux32arm) 
%template(Size_T_Vector) std::vector<size_t>;
#endif

//--------------------------------------------------------------------------------
#ifdef OLD_ALGORITHMS
%extend nta::algorithms::Segment<nta::UInt32, nta::Real32>
{
  %pythoncode %{
    def __init__(self, *args):
      self.this = _ALGORITHMS.new_Segment_32()

    #def __str__(self):
    #  return self.to_string().__str__()

    def __eq__(self, o):
      return self.this == o.this

    def __ne__(self, o):
       return self.this != o.this

    def __hash__(self):
       return self.hash()
  %}

  inline nta::UInt32 nSynapses() const { return self->n_synapses(); }
  inline nta::UInt32 cellIndex() const { return self->cell_index(); }
  inline nta::UInt32 getDepth() const { return self->get_depth(); }

  inline nta::algorithms::Branch<nta::UInt32,nta::Real32>* getBranch() const
    {
      return self->branch();
    }

  inline void incrementSynapsesStrength(PyObject* py_ind,
                                        nta::Real32 increment,
                                        nta::Real32 max_val =-1.0,
                                        nta::Real32 min_val =1.0)
  {
    nta::NumpyVectorT<nta::UInt32> ind(py_ind);
    self->increment_synapses_strength(ind.begin(), ind.end(), increment, max_val, min_val);
  }

  inline void addSynapses(PyObject* py_ind, nta::Real32 init_value)
  {
    nta::NumpyVectorT<nta::UInt32> ind(py_ind);
    self->add_synapses(ind.begin(), ind.end(), init_value);
  }

  inline void addSynapses(PyObject* py_ind, PyObject* py_strengths)
  {
    nta::NumpyVectorT<nta::UInt32> ind(py_ind);
    nta::NumpyVectorT<nta::Real32> st(py_strengths);
    self->add_synapses_and_strengths(ind.begin(), ind.end(), st.begin(), st.end());
  }

  inline PyObject* getSynapses() const
  {
    size_t n = (size_t) self->n_synapses();
    nta::NumpyVectorT<nta::UInt32> ind(n);
    nta::NumpyVectorT<nta::Real32> cnt(n);
    self->get_synapses(ind.begin(), ind.end(), cnt.begin(), cnt.end());
    PyObject *result = PyTuple_New(2);
    PyTuple_SET_ITEM(result, 0, ind.forPython());
    PyTuple_SET_ITEM(result, 1, cnt.forPython());
    return result;
  }

  inline std::vector<nta::UInt32> getSynapseIndices() const
  {
    std::vector<nta::UInt32> inds;
    self->get_synapse_indices(inds);
    return inds;
  }

  inline std::vector<nta::Real32> getSynapseStrengths() const
  {
    std::vector<nta::Real32> strengths;
    self->get_synapse_strengths(strengths);
    return strengths;
  }

  inline nta::algorithms::Segment<nta::UInt32,nta::Real32>* getUpSegment() const
  {
    return self->get_up_segment();
  }

  inline std::vector<std::pair<nta::UInt32, nta::Real32> >
    getUpSynapses(int window_size =-1) const
    {
      std::vector<std::pair<nta::UInt32, nta::Real32> > up_synapses;
      self->get_up_synapses(up_synapses, window_size);
      return up_synapses;
    }

} // end extend Segment

//--------------------------------------------------------------------------------
%extend nta::algorithms::Branch<nta::UInt32, nta::Real32>
{
  %pythoncode %{
    def __init__(self, *args):
      self.this = _ALGORITHMS.new_Branch_32(*args)

    #def __str__(self):
    #  return self.to_string().__str__()

    #def __eq__(self, o):
    #  return self.this == o.this

    #def __ne__(self, o):
    #   return self.this != o.this
  %}

  inline nta::UInt32 nSegments() const { return self->n_segments(); }
  inline nta::UInt32 nSynapses() const { return self->n_synapses(); }

  inline nta::algorithms::Segment<nta::UInt32,nta::Real32>*
    createSegment(PyObject* py_ind =NULL,
                  nta::Real32 init_strength =1,
                  nta::UInt32 timeSlot =0)
  {
    if (py_ind == NULL)
      return self->create_segment();
    else {
      nta::NumpyVectorT<nta::UInt32> ind(py_ind);
      std::vector<std::pair<nta::UInt32, nta::Real32> > synapses(ind.size());
      for (int i = 0; i != ind.size(); ++i)
        synapses[i] = std::make_pair(ind.get(i), init_strength);
      typedef nta::algorithms::Segment<nta::UInt32,nta::Real32>* SegPtr;
      SegPtr seg = self->create_segment(timeSlot, synapses);
      return seg;
    }
  }

  inline void
    removeSegment(nta::algorithms::Segment<nta::UInt32,nta::Real32>* seg)
  {
    self->remove_segment(seg);
  }

  inline void
    removeSegment(nta::UInt32 seg_idx)
  {
    self->remove_segment(seg_idx);
  }

  inline void cutAtSegment(nta::algorithms::Segment<nta::UInt32,nta::Real32>* seg)
  {
    self->cut_at_segment(seg);
  }

  inline void cutAtSegment(nta::UInt32 seg_idx)
  {
    self->cut_at_segment(seg_idx);
  }

  inline nta::UInt32 segIndex(nta::algorithms::Segment<nta::UInt32,nta::Real32>* seg) const
  {
    return self->seg_index(seg);
  }

  inline nta::algorithms::Segment<nta::UInt32,nta::Real32>* getSegment(nta::UInt32 idx) const
    {
      return self->get_segment(idx);
    }

  //--------------------------------------------------------------------------------
  /**
   * FOR UNIT TESTS ONLY
   *
   * This just calls first_activation_dfs after allocating a buffer, so that we
   * can unit test first_activation_dfs from Python.
   */
  inline PyObject*
    first_activation_dfs(size_type window,
                         value_type threshold, value_type hiloThreshold,
                         const std::vector<nta::UInt32>& activities)
  {
    std::vector<nta::Real32> buffer(1024);
    std::pair<nta::algorithms::Segment<nta::UInt32,nta::Real32>*, int> p;

    if (window == 1)
      p = self->first_activation_dfs(threshold, hiloThreshold, activities,
                                     buffer);
    else
      p = self->first_activation_dfs_with_window(window, threshold, hiloThreshold,
                                                 activities, buffer);

    PyObject *result = PyTuple_New(2);

    if (p.first) {
      PyTuple_SET_ITEM(result, 0, PyInt_FromLong(p.first->index()));
      PyTuple_SET_ITEM(result, 1, PyInt_FromLong(p.second));
    } else {
      PyTuple_SET_ITEM(result, 0, PyInt_FromLong(-1));
      PyTuple_SET_ITEM(result, 1, PyInt_FromLong(0));
    }

    return result;
  }

  //--------------------------------------------------------------------------------

} // end extend Branch

//--------------------------------------------------------------------------------
%extend nta::algorithms::Cell<nta::UInt32,nta::Real32>
{
  %pythoncode %{
    def __init__(self, *args):
      self.this = _ALGORITHMS.new_Cell_32()

    def __str__(self):
      return self.to_string().__str__()
  %}

} // end extend Cell

//--------------------------------------------------------------------------------
%extend nta::algorithms::Cells<nta::UInt32,nta::Real32>
{
  %pythoncode %{
    def __init__(self, *args):
      if len(args) > 0:
        self.this = _ALGORITHMS.new_Cells_32(*args)
      else:
        self.this = _ALGORITHMS.new_Cells_32()

    def __str__(self):
      return self.to_string().__str__()

    def __getstate__(self):
      """
      Used by the pickling mechanism to get state that will be saved.
      """
      return (self.toPyString(),)

    def __setstate__(self,tup):
      """
      Used by the pickling mechanism to restore state that was saved.
      """
      self.this = _ALGORITHMS.new_Cells_32()
      self.thisown = 1
      self.fromPyString(tup[0])
  %}

  inline nta::UInt32 nCells() const { return self->n_cells(); }
  inline nta::UInt32 nSynapses() const { return self->n_synapses(); }
  inline nta::UInt32 nSegments() const { return self->n_segments(); }

  inline nta::algorithms::Cell<nta::UInt32,nta::Real32>
    getCell(nta::UInt32 idx) const
    {
      return self->get_cell(idx);
    }

  inline PyObject* getAllCellSynapses(nta::UInt32 cellIdx) const
  {
    size_t n = (size_t) self->n_synapses_cell(cellIdx);
    nta::NumpyVectorT<nta::UInt32> ind(n);
    nta::NumpyVectorT<nta::Real32> cnt(n);
    self->get_all_cell_synapses(cellIdx, ind.begin(), cnt.begin());
    PyObject *result = PyTuple_New(2);
    PyTuple_SET_ITEM(result, 0, ind.forPython());
    PyTuple_SET_ITEM(result, 1, cnt.forPython());
    return result;
  }

  inline std::pair<nta::UInt32, nta::algorithms::Segment<nta::UInt32,nta::Real32>*>
    leastUsedFirstSeg(nta::UInt32 begin, nta::UInt32 end) const
  {
    return self->least_used_first_seg(begin, end);
  }

  inline std::vector<nta::UInt32>
    computeActivations(size_t window_size,
                       size_t threshold,
                       PyObject* py_activations,
                       PyObject* py_lat_activations_0,
                       PyObject* py_lat_activations,
                       std::vector<nta::algorithms::Segment<nta::UInt32,nta::Real32>*>& active_segs,
                       nta::Real32 synHiloThreshold =0,
                       size_t baby =0)
  {
    PyArrayObject* _activations = (PyArrayObject*) py_activations;
    nta::Real32* activations = (nta::Real32*) (_activations->data);
    nta::ByteVector cpp_activations(activations, _activations->dimensions[0]);

    PyArrayObject* _lat_activations_0 = (PyArrayObject*) py_lat_activations_0;
    nta::Int32* cpp_lat0 = (nta::Int32*) (_lat_activations_0->data);

    PyArrayObject* _lat_activations = (PyArrayObject*) py_lat_activations;
    nta::Int32* cpp_lat = (nta::Int32*) (_lat_activations->data);

    self->compute_activations(window_size,
                              threshold,
                              cpp_activations,
                              cpp_lat0,
                              cpp_lat,
                              active_segs,
                              synHiloThreshold,
                              baby);

    std::vector<nta::UInt32> active_cells(active_segs.size());
    for (size_t i = 0; i != active_segs.size(); ++i)
      active_cells[i] = active_segs[i]->cell_index();

    return active_cells;
  }

  inline void decaySynapses(nta::Real32 k, nta::Real32 minValue, nta::UInt32 mode =2)
  {
    self->decay_synapses(k, minValue, mode);
  }

  inline PyObject* analyzeSegments()
  {
    std::vector<std::pair<int,int> > syn_per_seg;
    std::vector<std::pair<int,int> > seg_per_branch;
    self->analyze_segments(syn_per_seg, seg_per_branch);
    PyObject *result = PyTuple_New(2);
    PyObject* sps = PyTuple_New(syn_per_seg.size());
    for (size_t i = 0; i != syn_per_seg.size(); ++i) {
      PyObject* p = PyTuple_New(2);
      PyTuple_SET_ITEM(p, 0, PyInt_FromLong(syn_per_seg[i].first));
      PyTuple_SET_ITEM(p, 1, PyInt_FromLong(syn_per_seg[i].second));
      PyTuple_SET_ITEM(sps, i, p);
    }
    PyObject* spb = PyTuple_New(seg_per_branch.size());
    for (size_t i = 0; i != seg_per_branch.size(); ++i) {
      PyObject* p = PyTuple_New(2);
      PyTuple_SET_ITEM(p, 0, PyInt_FromLong(seg_per_branch[i].first));
      PyTuple_SET_ITEM(p, 1, PyInt_FromLong(seg_per_branch[i].second));
      PyTuple_SET_ITEM(spb, i, p);
    }
    PyTuple_SET_ITEM(result, 0, sps);
    PyTuple_SET_ITEM(result, 1, spb);
    return result;
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
      throw std::runtime_error("Failed to load Cells");
      return false;
    }
  }

} // end extend Cells

//--------------------------------------------------------------------------------
%pythoncode %{
  def Segment(*args, **keywords):
     return Segment_32(*args)

  def SegVector(*args, **keywordS):
     return SegVector_32(*args)

  def Branch(*args, **keywords):
     return Branch_32(*args)

  def Cells(*args, **keywords):
     return Cells_32(*args)
%}
#endif // OLD_ALGORITHMS

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

#ifdef OLD_ALGORITHMS
%extend nta::algorithms::LearningSet
{
  %pythoncode %{

    def __init__(self, *args):
      this = _ALGORITHMS.new_LearningSet(*args)
      try:
        self.this.append(this)
      except:
        self.this = this
  %}

  inline int
    getCandidates(nta::UInt32 dst_cell,
                  PyObject* py_src_cells, PyObject* py_candidates) const
  {
    PyArrayObject* _src_cells = (PyArrayObject*) py_src_cells;
    CHECKSIZE(_src_cells);
    nta::UInt32* src_cells = (nta::UInt32*)(_src_cells->data);
    nta::UInt32 n_src_cells = _src_cells->dimensions[0];

    PyArrayObject* _candidates = (PyArrayObject*) py_candidates;
    CHECKSIZE(_candidates);
    nta::UInt32* cands = (nta::UInt32*)(_candidates->data);
    nta::UInt32 n_cands = 0;

    self->candidates(dst_cell, n_src_cells, src_cells, n_cands, cands);

    return n_cands;
  }

} // end extend nta::LearningSet

//--------------------------------------------------------------------------------
%extend nta::algorithms::PySynapses
{
  %pythoncode %{

    def __init__(self, *args):
      self.this = _ALGORITHMS.new_PySynapses(*args)

    def __setstate__(self, inString):
      self.this = _ALGORITHMS.new_PySynapses()
      self.loadFromString(inString)
  %}

  void loadFromString(const std::string& inString)
  {
    std::istringstream inStream(inString);
    self->load(inStream);
  }

  PyObject* __getstate__()
  {
    SharedPythonOStream py_s(self->persistent_size());
    std::ostream& s = py_s.getStream();
    self->save(s);
    return py_s.close();
  }

  inline void
    addSynapses(nta::UInt32 destCellIdx, nta::UInt32 destSegmentIdx,
                nta::UInt32 nSourceCells, PyObject* py_srcCellIdxArr)
  {
    nta::UInt32* srcCellIdxArr = (nta::UInt32*) ((PyArrayObject*)py_srcCellIdxArr)->data;
    CHECKSIZE((PyArrayObject*)py_srcCellIdxArr);

    self->addSynapses(destCellIdx, destSegmentIdx, nSourceCells, srcCellIdxArr);
  }

  inline PyObject *
  getSynapseOnCellSegment(nta::UInt32 cellIdx, nta::UInt32 segmentIdx,
                          nta::UInt32 synapseIdx)
  {
    nta::Real32 permanence;
    nta::Int16  dRow;
    nta::Int16  dCol;

    self->getSynapseOnCellSegment(cellIdx, segmentIdx, synapseIdx,
                                  permanence, dRow, dCol);

    PyObject *toReturn = PyTuple_New(3);
    PyTuple_SET_ITEM(toReturn, 0, PyFloat_FromDouble(permanence));
    PyTuple_SET_ITEM(toReturn, 1, PyInt_FromLong(dRow));
    PyTuple_SET_ITEM(toReturn, 2, PyInt_FromLong(dCol));

    return toReturn;
  }

  inline PyObject *
  getSynapseOnMasterSegment(nta::UInt32 masterNum, nta::UInt32 segmentIdx,
                            nta::UInt32 synapseIdx)
  {
    nta::Real32 permanence;
    nta::Int16  dRow;
    nta::Int16  dCol;

    self->getSynapseOnMasterSegment(masterNum, segmentIdx, synapseIdx,
                                    permanence, dRow, dCol);

    PyObject *toReturn = PyTuple_New(3);
    PyTuple_SET_ITEM(toReturn, 0, PyFloat_FromDouble(permanence));
    PyTuple_SET_ITEM(toReturn, 1, PyInt_FromLong(dRow));
    PyTuple_SET_ITEM(toReturn, 2, PyInt_FromLong(dCol));

    return toReturn;
  }


  inline nta::UInt32
  getAbsSynapsesOnCellSegment(nta::UInt32 cellIdx, nta::UInt32 segmentIdx,
                              PyObject* py_srcCellIndices,
                              PyObject* py_srcPermanences)
  {
    nta::UInt32* srcCellIndices = (nta::UInt32*) ((PyArrayObject*)py_srcCellIndices)->data;
    CHECKSIZE((PyArrayObject*)py_srcCellIndices);
    nta::Real32* srcPermanences = (nta::Real32*) ((PyArrayObject*)py_srcPermanences)->data;
    CHECKSIZE((PyArrayObject*)py_srcPermanences);

    return self->getAbsSynapsesOnCellSegment(cellIdx, segmentIdx,
                                             srcCellIndices, srcPermanences);
  }

  inline nta::UInt32
  computeSegmentActivations(
    nta::SparseMatrix<nta::UInt32,nta::Real32>& segActivations,
    PyObject* py_bestCellIndices, PyObject* py_bestSegmentIndices,
    PyObject* py_bestCellActivations,
    nta::UInt32 nInputs, PyObject* py_input,
    nta::UInt32 thresholdForBest, nta::UInt32 thresholdForActive) const
  {
    const nta::UInt32* input = (const nta::UInt32*) ((PyArrayObject*)py_input)->data;
    CHECKSIZE((PyArrayObject*)py_input);
    nta::UInt32* pBestCellIndices = (nta::UInt32*) ((PyArrayObject*)py_bestCellIndices)->data;
    CHECKSIZE((PyArrayObject*)py_bestCellIndices);
    nta::UInt32* pBestSegmentIndices = (nta::UInt32*) ((PyArrayObject*)py_bestSegmentIndices)->data;
    CHECKSIZE((PyArrayObject*)py_bestSegmentIndices);
    nta::UInt32* pBestCellActivations = (nta::UInt32*) ((PyArrayObject*)py_bestCellActivations)->data;
    CHECKSIZE((PyArrayObject*)py_bestCellActivations);

    return self->computeSegmentActivations(&segActivations,
                                           pBestCellIndices, pBestSegmentIndices,
                                           pBestCellActivations,
                                           nInputs, input, thresholdForBest,
                                           thresholdForActive);
  }

  inline nta::UInt32
  computeBestSegmentActivations(
    PyObject* py_bestCellIndices, PyObject* py_bestSegmentIndices,
    PyObject* py_bestCellActivations,
    nta::UInt32 nInputs, PyObject* py_input,
    nta::UInt32 threshold) const
  {
    const nta::UInt32* input = (const nta::UInt32*) ((PyArrayObject*)py_input)->data;
    CHECKSIZE((PyArrayObject*)py_input);
    nta::UInt32* pBestCellIndices = (nta::UInt32*) ((PyArrayObject*)py_bestCellIndices)->data;
    CHECKSIZE((PyArrayObject*)py_bestCellIndices);
    nta::UInt32* pBestSegmentIndices = (nta::UInt32*) ((PyArrayObject*)py_bestSegmentIndices)->data;
    CHECKSIZE((PyArrayObject*)py_bestSegmentIndices);
    nta::UInt32* pBestCellActivations = (nta::UInt32*) ((PyArrayObject*)py_bestCellActivations)->data;
    CHECKSIZE((PyArrayObject*)py_bestCellActivations);

    return self->computeSegmentActivations(NULL,
                                           pBestCellIndices, pBestSegmentIndices,
                                           pBestCellActivations,
                                           nInputs, input, threshold,
                                           0xFFFFFFFF);
  }

  inline nta::UInt32
  update(
    nta::UInt32 nInputs, PyObject* py_input,
    nta::UInt32 nInstructions, PyObject* py_instructions,
    PyObject* py_touchedSegments)
  {
    typedef const nta::Int32 (*InstructionsT)[3];
    typedef nta::UInt32      (*TouchedSegmentsT)[2];

    const nta::UInt32* input = (const nta::UInt32*) ((PyArrayObject*)py_input)->data;
    CHECKSIZE((PyArrayObject*)py_input);
    const nta::UInt32* instructions = (const nta::UInt32*) ((PyArrayObject*)py_instructions)->data;
    CHECKSIZE((PyArrayObject*)py_instructions);
    nta::UInt32* touchedSegments = (nta::UInt32*) ((PyArrayObject*)py_touchedSegments)->data;
    CHECKSIZE((PyArrayObject*)py_touchedSegments);

    return self->update(nInputs, input, nInstructions,
                        (InstructionsT)instructions,
                        (TouchedSegmentsT)touchedSegments);
  }

  inline void saveToFile(const std::string& filename)
  {
    std::ofstream save_file(filename.c_str());
    self->save(save_file);
    save_file.close();
  }

  inline void loadFromFile(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->load(load_file);
    load_file.close();
  }

}; // end extend::nta::algorithms::PySynapses

//--------------------------------------------------------------------------------

%extend nta::algorithms::CellUpdater
{
  %pythoncode %{

    def __init__(self, *args):
      this = _ALGORITHMS.new_CellUpdater(*args)
      try:
        self.this.append(this)
      except:
        self.this = this
  %}

  inline void
    update(PyObject* py_whatToDo, PyObject* py_buInput, PyObject* py_segsToCells)
  {
    nta::Int32* whatToDo = (nta::Int32*) ((PyArrayObject*)py_whatToDo)->data;
    CHECKSIZE((PyArrayObject*)py_whatToDo);
    nta::Real32* buInput = (nta::Real32*) ((PyArrayObject*)py_buInput)->data;
    CHECKSIZE((PyArrayObject*)py_buInput);
    nta::Int32* segsToCells = (nta::Int32*) ((PyArrayObject*)py_segsToCells)->data;
    CHECKSIZE((PyArrayObject*)py_segsToCells);

    self->update(whatToDo, buInput, segsToCells);
  }
};

//--------------------------------------------------------------------------------
#endif // OLD_ALGORITHMS
/// %include <nta/algorithms/Cells2.hpp>

/// %template(Cells2_32) nta::algorithms::Cells2::Cells<nta::UInt32, nta::Int16, nta::Real32>;
#ifdef OLD_ALGORITHMS

//--------------------------------------------------------------------------------
%extend nta::algorithms::Cells2::Cells<nta::UInt32, nta::Int16, nta::Real32>
{
  %pythoncode %{

    def __init__(self, *args):
      self.this = _ALGORITHMS.new_Cells2_32(*args)

    def __setstate__(self, inString):
      self.this = _ALGORITHMS.new_Cells2_32()
      self.loadFromString(inString)
  %}

  void loadFromString(const std::string& inString)
  {
    std::istringstream inStream(inString);
    self->load(inStream);
  }

  PyObject* __getstate__()
  {
    SharedPythonOStream py_s(self->persistent_size());
    std::ostream& s = py_s.getStream();
    self->save(s);
    return py_s.close();
  }

  inline void
    addSynapses(nta::UInt32 destCellIdx, nta::UInt32 destSegmentIdx,
                nta::UInt32 nSourceCells, PyObject* py_srcCellIdxArr)
  {
    nta::UInt32* srcCellIdxArr = (nta::UInt32*) ((PyArrayObject*)py_srcCellIdxArr)->data;
    CHECKSIZE((PyArrayObject*)py_srcCellIdxArr);

    self->addSynapses(destCellIdx, destSegmentIdx, nSourceCells, srcCellIdxArr);
  }

  inline PyObject *
  getSynapseOnCellSegment(nta::UInt32 cellIdx, nta::UInt32 segmentIdx,
                          nta::UInt32 synapseIdx) const
  {
    nta::Real32 permenance;
    nta::Int16  dRow;
    nta::Int16  dCol;

    self->getSynapseOnCellSegment(cellIdx, segmentIdx, synapseIdx,
                                  permenance, dRow, dCol);

    PyObject *toReturn = PyTuple_New(3);
    PyTuple_SET_ITEM(toReturn, 0, PyFloat_FromDouble(permenance));
    PyTuple_SET_ITEM(toReturn, 1, PyInt_FromLong(dRow));
    PyTuple_SET_ITEM(toReturn, 2, PyInt_FromLong(dCol));

    return toReturn;
  }

  inline PyObject *
  getSynapseOnMasterSegment(nta::UInt32 masterNum, nta::UInt32 segmentIdx,
                            nta::UInt32 synapseIdx) const
  {
    nta::Real32 permenance;
    nta::Int16  dRow;
    nta::Int16  dCol;

    self->getSynapseOnMasterSegment(masterNum, segmentIdx, synapseIdx,
                                    permenance, dRow, dCol);

    PyObject *toReturn = PyTuple_New(3);
    PyTuple_SET_ITEM(toReturn, 0, PyFloat_FromDouble(permenance));
    PyTuple_SET_ITEM(toReturn, 1, PyInt_FromLong(dRow));
    PyTuple_SET_ITEM(toReturn, 2, PyInt_FromLong(dCol));

    return toReturn;
  }

  inline nta::UInt32
  getAbsSynapsesOnCellSegment(nta::UInt32 cellIdx, nta::UInt32 segmentIdx,
                              PyObject* py_srcCellIndices,
                              PyObject* py_srcPermanences) const
  {
    nta::UInt32* srcCellIndices = (nta::UInt32*) ((PyArrayObject*)py_srcCellIndices)->data;
    CHECKSIZE((PyArrayObject*)py_srcCellIndices);
    nta::Real32* srcPermanences = (nta::Real32*) ((PyArrayObject*)py_srcPermanences)->data;
    CHECKSIZE((PyArrayObject*)py_srcPermanences);

    return self->getAbsSynapsesOnCellSegment(cellIdx, segmentIdx,
                                             srcCellIndices, srcPermanences);
  }

  inline nta::UInt32
  computeSegmentActivations(
    nta::SparseMatrix<nta::UInt32,nta::Real32>& segActivations,
    PyObject* py_bestCellIndices, PyObject* py_bestSegmentIndices,
    PyObject* py_bestCellActivations,
    nta::UInt32 nInputs, PyObject* py_input,
    nta::UInt32 thresholdForBest, nta::UInt32 thresholdForActive)
  {
    nta::UInt32* input = (nta::UInt32*) ((PyArrayObject*)py_input)->data;
    CHECKSIZE((PyArrayObject*)py_input);
    nta::UInt32* input_end = input + nInputs;
    nta::UInt32* pBestCellIndices = (nta::UInt32*) ((PyArrayObject*)py_bestCellIndices)->data;
    CHECKSIZE((PyArrayObject*)py_bestCellIndices);
    nta::UInt32* pBestSegmentIndices = (nta::UInt32*) ((PyArrayObject*)py_bestSegmentIndices)->data;
    CHECKSIZE((PyArrayObject*)py_bestSegmentIndices);
    nta::UInt32* pBestCellActivations = (nta::UInt32*) ((PyArrayObject*)py_bestCellActivations)->data;
    CHECKSIZE((PyArrayObject*)py_bestCellActivations);

    return self->computeSegmentActivations(input, input_end,
                                           &segActivations,
                                           pBestCellIndices,
                                           pBestSegmentIndices,
                                           pBestCellActivations,
                                           thresholdForBest,
                                           thresholdForActive);
  }

  inline nta::UInt32
  computeBestSegmentActivations(
    PyObject* py_bestCellIndices, PyObject* py_bestSegmentIndices,
    PyObject* py_bestCellActivations,
    nta::UInt32 nInputs, PyObject* py_input,
    nta::UInt32 threshold)
  {
    nta::UInt32* input = (nta::UInt32*) ((PyArrayObject*)py_input)->data;
    CHECKSIZE((PyArrayObject*)py_input);
    nta::UInt32* input_end = input + nInputs;
    nta::UInt32* pBestCellIndices = (nta::UInt32*) ((PyArrayObject*)py_bestCellIndices)->data;
    CHECKSIZE((PyArrayObject*)py_bestCellIndices);
    nta::UInt32* pBestSegmentIndices = (nta::UInt32*) ((PyArrayObject*)py_bestSegmentIndices)->data;
    CHECKSIZE((PyArrayObject*)py_bestSegmentIndices);
    nta::UInt32* pBestCellActivations = (nta::UInt32*) ((PyArrayObject*)py_bestCellActivations)->data;
    CHECKSIZE((PyArrayObject*)py_bestCellActivations);

    return self->computeSegmentActivations(input, input_end,
                                           NULL,
                                           pBestCellIndices,
                                           pBestSegmentIndices,
                                           pBestCellActivations,
                                           threshold,
                                           0xFFFFFFFF);
  }

  inline nta::UInt32
  update(
    nta::UInt32 nInputs, PyObject* py_input,
    nta::UInt32 nInstructions, PyObject* py_instructions,
    PyObject* py_touchedSegments)
  {
    nta::UInt32* input = (nta::UInt32*) ((PyArrayObject*)py_input)->data;
    nta::UInt32* input_end = input + nInputs;
    CHECKSIZE((PyArrayObject*)py_input);
    nta::Int32* instructions = (nta::Int32*) ((PyArrayObject*)py_instructions)->data;
    CHECKSIZE((PyArrayObject*)py_instructions);
    nta::UInt32* touchedSegments = (nta::UInt32*) ((PyArrayObject*)py_touchedSegments)->data;
    CHECKSIZE((PyArrayObject*)py_touchedSegments);

    return self->update(input, input_end,
                        nInstructions, instructions,
                        touchedSegments);
  }

  inline void saveToFile(const std::string& filename)
  {
    std::ofstream save_file(filename.c_str());
    self->save(save_file);
    save_file.close();
  }

  inline void loadFromFile(const std::string& filename)
  {
    std::ifstream load_file(filename.c_str());
    self->load(load_file);
    load_file.close();
  }

}; // end extend::nta::algorithms::Cells2::Cells


%pythoncode %{

  def Cells2(*args, **keywords):
     return Cells2_32(*args)
%}

#endif //OLD_ALGORITHMS

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

%include <nta/algorithms/spatial_pooler.hpp>

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
  %}

  inline void compute(PyObject *py_x, bool learn, PyObject *py_y)
  {
    PyArrayObject* x = (PyArrayObject*) py_x;
    PyArrayObject* y = (PyArrayObject*) py_y;
    self->compute((nta::UInt*) x->data, (bool)learn, (nta::UInt*) y->data);
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


%include <nta/algorithms/flat_spatial_pooler.hpp>

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
                 coincInputPoolPct=1.0,
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
        seed=seed,
        spVerbosity=spVerbosity
      )
  %}
}

%include <nta/algorithms/fast_cla_classifier.hpp>

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
