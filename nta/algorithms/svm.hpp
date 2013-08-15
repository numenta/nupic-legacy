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

/*
Copyright (c) 2000-2007 Chih-Chung Chang and Chih-Jen Lin
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

3. Neither name of copyright holders nor the names of its contributors
may be used to endorse or promote products derived from this software
without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

/** @file svm
 * This file contains declarations for the svm package.
 */

//--------------------------------------------------------------------------------
#ifndef NTA_SVM_HPP
#define NTA_SVM_HPP

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <iostream> 
#include <algorithm>

#ifdef NTA_PLATFORM_win32 // to align support vectors for SSE
#include <malloc.h>
#endif

#ifdef NUPIC2
#include <nta/utils/Random.hpp>
#else
#include <nta/common/Random.hpp>
#endif

#include <nta/math/math.hpp>
#include <nta/math/stl_io.hpp>
#include <nta/math/array2D.hpp>

namespace nta {
  namespace algorithms {
    namespace svm {

      //--------------------------------------------------------------------------------
#define INF float(1e20)
#define TAU float(1e-12)

      template <typename label_type, typename feature_type>
      struct sample
      {
	int n_;
	label_type y_;
	feature_type* x_;

	inline sample(int n, label_type y, feature_type* x)
	  : n_(n), y_(y), x_(x) 
	{}

	inline sample(const sample& other)
	  : n_(other.n_), y_(other.y_), x_(other.x_)
	{}

	inline sample& operator=(const sample& other)
	{
	  n_ = other.n_;
	  y_ = other.y_;
	  x_ = other.x_;
	  return *this;
	}
      };
    
      //--------------------------------------------------------------------------------
      class svm_problem
      {
      public:
	typedef float label_type;
	typedef float feature_type; 

	typedef sample<label_type, feature_type> sample_type;

	bool recover_;
	int n_dims_;
	std::vector<feature_type*> x_;
	std::vector<label_type> y_;

	inline svm_problem(int n_dims, bool recover, float =0)
	  : recover_(recover), n_dims_(n_dims), x_(), y_()
	{}

	inline svm_problem(int n_dims, int size, bool recover, float =0)
	  : recover_(recover), n_dims_(n_dims), 
            x_(size, (feature_type*)0), y_(size, 0)
	{}

	inline svm_problem(std::istream& inStream)
	  : recover_(true), n_dims_(0), x_(), y_()
	{
	  this->load(inStream);
	}

	inline ~svm_problem()
	{
	  if (recover_)
	    for (int i = 0; i != size(); ++i)
#ifdef NTA_PLATFORM_win32
              _aligned_free(x_[i]);
#else
	      delete [] x_[i];
#endif
	}

	inline int size() const { return (int)x_.size(); }
	inline int n_dims() const { return n_dims_; }
	inline int nnz(int i) const { return n_dims_; }

	inline void resize(int n) 
	{
	  x_.resize(n, 0);
	  y_.resize(n, 0);
	}

	template <typename InIter>
	inline void add_sample(float val, InIter x)
	{
          // Make sure we are not taking in any NaNs or INF
#ifdef NTA_ASSERTIONS_ON
          for (int i = 0; i != n_dims(); ++i)
            NTA_ASSERT(-HUGE_VAL < x[i] && x [i] < HUGE_VAL);
#endif

#ifdef NTA_PLATFORM_win32
          feature_type *new_x = (feature_type*) _aligned_malloc(4*n_dims(), 16);
#else
	  feature_type *new_x = new feature_type [n_dims()];
#endif
	  std::copy(x, x + n_dims(), new_x);
	  x_.push_back(new_x);
	  y_.push_back(val);
	}

	inline void set_sample(int i, const sample_type& s)
	{
	  x_[i] = s.x_;
	  y_[i] = s.y_;
	}

	inline sample_type get_sample(int i) const
	{
	  return sample_type(n_dims(), y_[i], x_[i]);
	}

	inline void dense(int i, float* sv) const
	{
	  std::copy(x_[i], x_[i] + n_dims(), sv);
	}

	int persistent_size() const;
	void save(std::ostream& outStream) const;
	void load(std::istream& inStream);

	void print() const
	{
	  std::cout << "Size = " << size()
		    << " n dims = " << n_dims()
		    << std::endl;

	  for (int i = 0; i != size(); ++i) {
	    std::cout << y_[i] << ": ";
	    for (int j = 0; j != n_dims(); ++j)
	      std::cout << x_[i][j] << " ";
	    std::cout << std::endl;
	  }
	}

      private:
        svm_problem();
        svm_problem(const svm_problem&);
        svm_problem& operator=(svm_problem&);
      };

      //--------------------------------------------------------------------------------
      struct svm_problem01
      {
	typedef float label_type;
	typedef int feature_type;

	typedef sample<label_type, feature_type> sample_type;

	bool recover_;
	int n_dims_;
	float threshold_;
	std::vector<int> nnz_;
	std::vector<feature_type*> x_;
	std::vector<float> y_;

	std::vector<int> buf_; // for admission of new x

	inline svm_problem01(int n_dims, bool recover, float threshold =.9)
	  : recover_(recover), n_dims_(n_dims), threshold_(threshold), buf_(n_dims)
	{}

	inline svm_problem01(int n_dims, int size, bool recover, float threshold = .9)
	  : recover_(recover), n_dims_(n_dims), threshold_(threshold),
	    nnz_(size, 0),
	    x_(size, (feature_type*)0), y_(size, 0),
	    buf_(n_dims)
	{}

	inline svm_problem01(std::istream& inStream)
	  : recover_(true), n_dims_(0), threshold_(0), nnz_(), x_(), y_()
	{
	  this->load(inStream);
	}

	inline ~svm_problem01()
	{
	  if (recover_)
	    for (int i = 0; i != size(); ++i)
	      delete [] x_[i];
	}

	inline int size() const { return (int) x_.size(); }
	inline int n_dims() const { return n_dims_; }
	inline int nnz(int i) const { return nnz_[i]; }

	inline void resize(int n) 
	{
	  nnz_.resize(n, 0);
	  x_.resize(n, 0);
	  y_.resize(n, 0);
	}

	template <typename InIter>
	inline void add_sample(float val, InIter x)
	{
          
          // Make sure we are not taking in any NaN or INF
#ifdef NTA_ASSERTIONS_ON
          for (int i = 0; i != n_dims(); ++i)
            NTA_ASSERT(-HUGE_VAL < x[i] && x [i] < HUGE_VAL);
#endif

	  int nnz = 0;
	  InIter x_it = x, x_end = x + n_dims();

	  while (x_it != x_end) {
	    float val = *x_it;
            if (!nearlyZero(val,threshold_)) {
	      buf_[nnz] = x_it - x;
	      ++nnz;
	    }
	    ++x_it; 
	  }
    
	  feature_type* new_x = new feature_type[nnz];
	  std::copy(buf_.begin(), buf_.begin() + nnz, new_x);

	  nnz_.push_back(nnz);
	  x_.push_back(new_x);
	  y_.push_back(val);
	}

	inline void set_sample(int i, const sample_type& s)
	{
	  nnz_[i] = s.n_;
	  x_[i] = s.x_;
	  y_[i] = s.y_;
	}

	inline sample_type get_sample(int i) const
	{
	  return sample_type(nnz_[i], y_[i], x_[i]);
	}

	inline void dense(int i, float * sv) const
	{
	  std::fill(sv, sv + n_dims(), (float)0);
	  for (int k = 0; k != nnz(i); ++k)
	    sv[x_[i][k]] = 1;
	}

	int persistent_size() const;
	void save(std::ostream& outStream) const;
	void load(std::istream& inStream);

	void print() const
	{
	  std::cout << "Size = " << size()
		    << " n dims = " << n_dims()
		    << std::endl;

	  for (int i = 0; i != size(); ++i) {
	    std::cout << y_[i] << ": " << nnz_[i] << ": ";
	    for (int j = 0; j != nnz_[i]; ++j)
	      std::cout << x_[i][j] << " ";
	    std::cout << std::endl;
	  }
	}
      };

      //--------------------------------------------------------------------------------
      struct decision_function
      {
	inline decision_function()
	  : alpha(NULL), rho(0)
	{}

	inline ~decision_function()
	{
	  delete [] alpha;
	}

	float *alpha;
	float rho;	
      };

      //--------------------------------------------------------------------------------
      /**
       * sv = sv[total_sv < l], redensified in the 0/1 case
       * sv_coef = sv_coef[n_class-1][total_sv < l], SV coeffs in decisions functions 
       * rho = rho[n_class*(n_class-1)/2], constants in decisions functions
       * label = label[n_class], label of each class
       * n_sv = n_sv[n_class], number of SVs for each class
       * probA, probB = [n_class*(n_class-1)/2]
       */
      class svm_model
      {
      public:
	int n_dims_;
        float *sv_mem;
	std::vector<float*> sv, sv_coef;
	std::vector<float> rho;	   
	std::vector<int> label;	 
	std::vector<int> n_sv;
	std::vector<float> probA, probB;
	std::vector<std::vector<float> > w;

	inline int size() const { return (int) sv.size(); } // total number of sv
	inline int n_dims() const { return n_dims_; }
	inline int n_class() const { return (int) label.size(); }

        svm_model()
          : n_dims_(0), 
            sv_mem(NULL), sv(), sv_coef(), 
            rho(), label(), n_sv(), probA(), probB(), w()
        {}

	~svm_model();

	int persistent_size() const;
	void save(std::ostream& outStream) const;
	void load(std::istream& inStream);
	void print() const;
        
      private:
        svm_model(const svm_model&);
        svm_model& operator=(const svm_model&);
      };

      //--------------------------------------------------------------------------------
      template <typename TQ>
      class Solver 
      {
      public:
	Solver() 
	  : active_size(0),
	    y(NULL),
	    G(NULL),
	    alpha_status(NULL),
	    alpha(NULL),
	    Q(NULL),
	    QD(NULL),
	    eps(0),
	    C(0),
	    p(NULL),
	    active_set(NULL),
	    G_bar(NULL),
	    l(0),
	    unshrinked(false)
	{}

	~Solver() {}

	float solve(int l, TQ& Q, const signed char *y_,
		    float *alpha_, float C, float eps, int shrinking);
      private:
	int active_size;
	signed char *y;
	float *G;		// gradient of objective function
	//typedef enum { LOWER_BOUND, UPPER_BOUND, FREE } AlphaStatus;
	int *alpha_status;	// LOWER_BOUND, UPPER_BOUND, FREE
	float *alpha;
	TQ *Q;
	float *QD;
	float eps;
	float C;
	float *p;
	int *active_set;
	float *G_bar;		// gradient, if we treat free variables as 0
	int l;
	bool unshrinked;	

	float get_C(int i)
	{
	  return C;
	}

	void update_alpha_status(int i)
	{
	  NTA_ASSERT(0 <= i);

	  if(alpha[i] >= get_C(i))
	    alpha_status[i] = 1;//UPPER_BOUND;
	  else if(alpha[i] <= 0)
	    alpha_status[i] = 0;//LOWER_BOUND;
	  else alpha_status[i] = 2;//FREE;
	}

	bool is_upper_bound(int i) { return alpha_status[i] == 1;/*UPPER_BOUND;*/ }
	bool is_lower_bound(int i) { return alpha_status[i] == 0;/*LOWER_BOUND;*/ }
	bool is_free(int i) { return alpha_status[i] == 2;/*FREE;*/ }
	void swap_index(int i, int j);
	void reconstruct_gradient();
	int select_working_set(int &i, int &j);
	float calculate_rho();
	void do_shrinking();
	bool be_shrunken(int i, float Gmax1, float Gmax2);	
      };
    
      //--------------------------------------------------------------------------------
      //
      // Kernel Cache
      //
      // l is the number of total data items
      // size is the cache size limit in bytes
      //
      //--------------------------------------------------------------------------------
      template <typename T>
      class Cache
      {
	struct head_t
	{
	  head_t *prev, *next;	// a cicular list
	  T* data;
	  int len;		// data[0,len) is cached in this entry
	};

	int l;
	long int size;
	head_t* head; 
	head_t lru_head;

      public:
	inline Cache(int l_, long int size_)
	  : l(l_), size(size_)
	{
	  head = (head_t *)calloc(l,sizeof(head_t));	// initialized to 0
	  size /= sizeof(float);
	  size -= l * sizeof(head_t) / sizeof(T);
	  // cache must be large enough for 2 columns
	  size = std::max(size, (long int) 2*l); 
	  lru_head.next = lru_head.prev = &lru_head;
	}

	inline ~Cache()
	{
	  for(head_t *h = lru_head.next; h != &lru_head; h=h->next)
	    free(h->data);
	  free(head);
	}

	// request data [0,len)
	// return some position p where [p,len) need to be filled
	// (p >= len if nothing needs to be filled)
	inline int get_data(const int index, T** data, int len)
	{
	  NTA_ASSERT(0 <= index && index < l);
	  NTA_ASSERT(0 <= len);

	  head_t *h = &head[index];
	  if (h->len) lru_delete(h);
	  int more = len - h->len;
    
	  if (more > 0)
	    {
	      // free old space
	      while (size < more)
		{
		  head_t *old = lru_head.next;
		  lru_delete(old);
		  free(old->data);
		  size += old->len;
		  old->data = 0;
		  old->len = 0;
		}
	
	      // allocate new space
	      h->data = (T*)realloc(h->data,sizeof(T)*len);
	      size -= more;
	      std::swap(h->len,len);
	    }
    
	  lru_insert(h);
	  *data = h->data;

	  NTA_ASSERT(data != NULL);

#ifdef DEBUG
	  for (int i = 0; i != h->len; ++i)
	    NTA_ASSERT(-HUGE_VAL < h->data[i] && h->data[i] < HUGE_VAL);
#endif

	  return len;
	}

	inline void swap_index(int i, int j)	// future_option
	{
	  if(i==j) return;

	  if(head[i].len) lru_delete(&head[i]);
	  if(head[j].len) lru_delete(&head[j]);
	  std::swap(head[i].data,head[j].data);
	  std::swap(head[i].len,head[j].len);
	  if(head[i].len) lru_insert(&head[i]);
	  if(head[j].len) lru_insert(&head[j]);

	  if(i>j) std::swap(i,j);
	  for(head_t *h = lru_head.next; h!=&lru_head; h=h->next)
	    {
	      if(h->len > i)
		{
		  if(h->len > j)
		    std::swap(h->data[i],h->data[j]);
		  else
		    {
		      // give up
		      lru_delete(h);
		      free(h->data);
		      size += h->len;
		      h->data = 0;
		      h->len = 0;
		    }
		}
	    }
	}

      private:
	inline void lru_delete(head_t *h)
	{
	  // delete from current location
	  h->prev->next = h->next;
	  h->next->prev = h->prev;
	}

	inline void lru_insert(head_t *h)
	{
	  // insert to last position
	  h->next = &lru_head;
	  h->prev = lru_head.prev;
	  h->prev->next = h;
	  h->next->prev = h;
	}
      };

      //--------------------------------------------------------------------------------
      //
      // Kernel evaluation
      //
      // the static method k_function is for doing single kernel evaluation
      // the constructor of Kernel prepares to calculate the l*l kernel matrix
      // the member function get_Q is for getting one column from the Q Matrix
      //
      //--------------------------------------------------------------------------------
      class QMatrix
      {
      public:
	typedef svm_problem::label_type label_type;
	typedef svm_problem::feature_type feature_type;
	typedef float (QMatrix::*kernel_type)(int i, int j) const;

      private:
	int l, n;
	kernel_type kernel_function;
	float gamma;
	feature_type **x;
	feature_type *x_square;
	signed char *y;
	Cache<float> *cache;
	float *QD;
  
      public:
	QMatrix(const svm_problem& prob, float g, int kernel, int cache_size)
	  : l(prob.size()), n(prob.n_dims()), 
	    kernel_function(0),
	    gamma(g),
	    x(new feature_type* [l]), x_square(new feature_type[l]),
	    y(new signed char[l]),
	    cache(new Cache<float>(l, (long int)(cache_size*(1<<20)))),
	    QD(new float[l])
	{
	  if (kernel == 0) 
	    kernel_function = &QMatrix::linear_kernel;
	  else
	    kernel_function = &QMatrix::rbf_kernel;

	  std::copy(prob.x_.begin(), prob.x_.end(), x);

	  for (int i = 0; i !=l; ++i) {
	    y[i] = prob.y_[i] > 0 ? +1 : -1;
	    x_square[i] = dot(i, i);
	    // ok because x_square[i] initialized!
	    QD[i]= (this->*kernel_function)(i, i); 
	  }
	}

	~QMatrix()
	{
	  delete [] x;
	  delete [] x_square;
	  delete [] y;
	  delete cache;
	  delete [] QD;
	}

	inline float *get_Q(int i, int len) const
	{
	  NTA_ASSERT(0 <= i);
	  NTA_ASSERT(0 <= len);

	  float *data;
	  int start;

	  if ((start = cache->get_data(i,&data,len)) < len) {
	    for (int j=start;j<len;j++)
	      data[j] = (float)(y[i]*y[j]*(this->*kernel_function)(i,j));
	  }

	  NTA_ASSERT(data != NULL);

	  return data;
	}

	inline float *get_QD() const
	{
	  return QD;
	}

	inline void swap_index(int i, int j)
	{
	  NTA_ASSERT(0 <= i);
	  NTA_ASSERT(0 <= j);

	  cache->swap_index(i,j);
	  std::swap(x[i], x[j]);
	  std::swap(x_square[i], x_square[j]);
	  std::swap(y[i], y[j]);
	  std::swap(QD[i], QD[j]);
	}

	inline feature_type dot(int i, int j) const
	{
	  NTA_ASSERT(0 <= i);
	  NTA_ASSERT(0 <= j);

	  feature_type sum = 0;
	  feature_type *x_it = x[i], *x_end1 = x_it + n;
	  feature_type *y_it = x[j];
	  
	  while (x_it != x_end1) {
	    sum += *x_it * *y_it;
	    ++x_it; ++y_it;
	  }
	  
	  return sum;
	}

	inline float linear_kernel(int i, int j) const
	{
	  return dot(i, j);
	}

	inline float rbf_kernel(int i, int j) const
	{
	  float v = expf(-gamma*(x_square[i] + x_square[j] - 2*dot(i, j)));
	  NTA_ASSERT(-HUGE_VAL <= v && v < HUGE_VAL);
	  return v;
	}
      };

      //--------------------------------------------------------------------------------
      class QMatrix01
      {
      public:
	typedef svm_problem01::label_type label_type;
	typedef svm_problem01::feature_type feature_type;
	typedef float (QMatrix01::*kernel_type)(int i, int j) const;

      private:
	int l, n;
	kernel_type kernel_function;
	float gamma;
	std::vector<int> nnz;
	std::vector<feature_type*> x;
	float *x_square;
	signed char *y;
	Cache<float> *cache;
	float *QD;
  
      public:
	QMatrix01(const svm_problem01& prob, float g, int kernel, int cache_size)
	  : l(prob.size()), n(prob.n_dims()),
	    kernel_function(0),
	    gamma(g),
	    nnz(prob.nnz_), x(prob.x_.begin(), prob.x_.end()), x_square(new float[l]),
	    y(new signed char[l]),
	    cache(new Cache<float>(l, (long int)(cache_size*(1<<20)))),
	    QD(new float[l])
	{
	  if (kernel == 0)
	    kernel_function = &QMatrix01::linear_kernel;
	  else
	    kernel_function = &QMatrix01::rbf_kernel;

	  for (int i = 0; i != l; ++i) {
	    y[i] = prob.y_[i] > 0 ? +1 : -1;
	    x_square[i] = (float) dot(i, i);
	    // ok because x_square[i] initialized!
	    QD[i]= (this->*kernel_function)(i, i); 
	  }
	}

	~QMatrix01()
	{
	  delete [] x_square;
	  delete [] y;
	  delete cache;
	  delete [] QD;
	}

	inline float *get_Q(int i, int len) const
	{
	  float *data;
	  int start;
	  if ((start = cache->get_data(i,&data,len)) < len) {
	    for(int j=start;j<len;j++) 
	      data[j] = (float)(y[i]*y[j]*(this->*kernel_function)(i, j));
	  }
	  return data;
	}

	inline float *get_QD() const
	{
	  return QD;
	}

	inline void swap_index(int i, int j)
	{
	  cache->swap_index(i,j);
	  std::swap(nnz[i], nnz[j]);
	  std::swap(x[i], x[j]);
	  std::swap(x_square[i], x_square[j]);
	  std::swap(y[i], y[j]);
	  std::swap(QD[i], QD[j]);
	}

	inline feature_type dot(int i, int j) const
	{
	  feature_type sum = 0;
	  feature_type *x_it = x[i], *x_end = x_it + nnz[i];
	  feature_type *y_it = x[j], *y_end = y_it + nnz[j];

	  while (x_it != x_end && y_it != y_end)
	    if (*x_it < *y_it)
	      ++x_it;
	    else if (*y_it < *x_it)
	      ++y_it;
	    else {
	      ++sum;
	      ++x_it; ++y_it;
	    }

	  return sum;
	}

	inline float linear_kernel(int i, int j) const
	{
	  return (float) dot(i, j);
	}

	inline float rbf_kernel(int i, int j) const
	{
	  float v = expf(-gamma*(x_square[i] + x_square[j] - 2*dot(i, j)));
	  return v;
	}
      };

      //--------------------------------------------------------------------------------
      struct svm_parameter 
      {
	svm_parameter(int k, bool p, float g, float c, float e, int cs, int s)
	  : kernel(k), probability(p), gamma(g), C(c), eps(e), cache_size(cs),
	    shrinking(s)
	{}

	int kernel; // 0 = linear, 1 = rbf
	bool probability;
	float gamma;	
	float C;	   
	float eps;	      /* stopping criteria */
	int cache_size;      /* in MB */
	int shrinking;        /* use the shrinking heuristics */
	std::vector<int> weight_label;
	std::vector<float> weight;

	int persistent_size() const;
	void save(std::ostream& outStream) const;
	void load(std::istream& inStream);
	void print() const;
      };

      //--------------------------------------------------------------------------------
      struct svm_std_traits
      {
	typedef svm_problem::label_type label_type;
	typedef svm_problem::feature_type feature_type;

	typedef sample<label_type, feature_type> sample_type;
	typedef svm_problem problem_type;
	typedef QMatrix q_matrix_type;
      };

      struct svm_01_traits
      {
	typedef svm_problem01::label_type label_type;
	typedef svm_problem01::feature_type feature_type;

	typedef sample<label_type, feature_type> sample_type;
	typedef svm_problem01 problem_type;
	typedef QMatrix01 q_matrix_type;
      };
      
      //--------------------------------------------------------------------------------
      template <typename svm_traits =svm_std_traits>
      class svm
      {
      public:
	typedef typename svm_traits::problem_type problem_type;
	typedef typename svm_traits::q_matrix_type q_matrix_type;
	
        // Need float only because we are using sse/xmm registers.
	typedef std::vector<float> Vector;
	typedef array2D<int, float> Matrix;

	svm_parameter param_;
	problem_type* problem_;
	svm_model* model_;
	nta::Random rng_;
  
	inline svm(int kernel =0, // 0 = linear, 1 = rbf
		   int n_dims =0,
		   float gamma =1,
		   float C =1,
		   float threshold =.9,
		   float eps =1e-3,
		   int cache_size =100,
		   int shrinking =1,
		   bool probability =false,
		   int seed =-1)
	  : param_(kernel, probability, gamma, C, eps, cache_size, shrinking),
	    problem_(new problem_type(n_dims, true, threshold)),
	    model_(NULL), rng_(seed != -1 ? seed : 0),
	    x_tmp_(NULL), dec_values_(NULL),
            with_sse(checkSSE())
	{}

        // Depending on the situation, the problem might be set with a number
        // of dimensions, or only the model, or neither, in case n_dims was set
        // to 0 in the constructor and then loaded from persistence. 
        // For inference, the original problem can be thrown away and only the 
        // model needs to be present in memory.
        // Note that we need to check the model first, because the problem might
        // be created, but with a number of dimensions == 0, while the model
        // would be loaded later with another number of dimensions.
        inline int n_dims() const
        {
          if (model_ != NULL)
            return model_->n_dims();
          else if (problem_ != NULL)
            return problem_->n_dims();
          return 0;
        }

        // Determine whether we can use sse for rbf inference or not
        // This is only for darwin86 or win32, rbf, and when the number
        // of dimensions is a multiple of 8 (because of the sse loading
        // 4 floats at a time in the xmm registers). 
        // The speed-up is about 2X to 2.5X.
        // todo: check size of type used for components of support vectors.
        //       it needs to be 4 bytes (floats) for sse/xmm registers.
        inline bool checkSSE()
        {
          if (param_.kernel == 1 && n_dims() % 8 == 0) { 

            // We really only need to look at register edx after call to cpuid.
            // If 25th bit of edx is 1, we have sse: 2^25 = 22554432.
            // If 26th bit of edx is 1, we have sse2: 2^26 = 67108864.
            // We don't care about sse3, which we are not using.
            // Refer to Intel manuals for details.

#ifdef NTA_PLATFORM_win32

            unsigned int f = 1, d;

            __asm {
                   mov eax, f
                   cpuid
                   mov d, edx
                  }
            
            return ((d & 33554432) > 0) || ((d & 67108864) > 0);

#elif defined(NTA_PLATFORM_darwin86)

            unsigned int f = 1, a,b,c,d;

            // PIC-compliant asm
            __asm__ __volatile__(
                                 "pushl %%ebx\n\t"
                                 "cpuid\n\t"
                                 "movl %%ebx, %1\n\t"
                                 "popl %%ebx\n\t"
                                 : "=a" (a), "=r" (b), "=c" (c), "=d" (d)
                                 : "a" (f)
                                 : "cc"
                                 );

            return ((d & 33554432) > 0) || ((d & 67108864) > 0);
#endif
          } 
          
          return false;
        }

	inline ~svm()
	{
	  delete problem_;
	  problem_ = NULL;
	  delete model_;
	  model_ = NULL;

#ifdef NTA_PLATFORM_win32
          _aligned_free(x_tmp_);
#else
	  delete [] x_tmp_;
#endif

	  x_tmp_ = NULL;
	  delete [] dec_values_;
	  dec_values_ = NULL;
	}

	svm_model* train(const problem_type&, const svm_parameter&);

	inline problem_type* get_problem() { return problem_; }
	inline svm_model* get_model() { return model_; }

	inline void discard_problem()
	{
	  delete problem_;
	  problem_ = NULL;
	}

	template <typename InIter>
	float predict(const svm_model&, InIter);

	template <typename InIter, typename OutIter>
	float predict_probability(const svm_model&, InIter, OutIter);

	float cross_validation(int);

	int persistent_size() const;
	void save(std::ostream& outStream) const;
	void load(std::istream& inStream);

      private:
	void group_classes(const problem_type&, std::vector<int>&, std::vector<int>&,
			   std::vector<int>&, std::vector<int>&);
	void multiclass_probability(Matrix&, Vector&);
	void binary_probability(const problem_type&, float&, float&);
	void sigmoid_train(int, const Vector&, const Vector&, float&, float&);
	float sigmoid_predict(float, float, float);
	float rbf_function(float*, float*, float*) const;
	float linear_function(float*, float*, float*) const;
	void predict_values(const svm_model&, float*, float*);

	float *x_tmp_, *dec_values_;
        bool with_sse;

        svm(const svm&);
        svm& operator=(const svm&);
      };

      //--------------------------------------------------------------------------------
      class svm_dense
      {
	svm<svm_std_traits> svm_;

      public:
	inline svm_dense(int kernel =0, // 0 = linear, 1 = rbf
			 int n_dims =0,
			 float threshold =.9,
			 int cache_size =100,
			 int shrinking =1,
			 bool probability =false,
			 int seed =-1)
	  : svm_(kernel, n_dims, 1, 1, threshold, 1, 
		 cache_size, shrinking, probability, seed)
	{
	}
	
	template <typename InIter>
	inline void add_sample(float val, InIter x)
	{
	  svm_.problem_->add_sample(val, x);
	}

	inline void train(float gamma, float C, float eps)
	{
	  svm_.param_.gamma = gamma;
	  svm_.param_.C = C;
	  svm_.param_.eps = eps;

	  NTA_ASSERT(0 < svm_.param_.gamma);
	  
	  if (svm_.model_) {
	    delete svm_.model_;
	    svm_.model_ = NULL;
	  }

	  svm_.model_ = svm_.train(*svm_.problem_, svm_.param_);
	}

	inline svm_problem& get_problem() { return *svm_.problem_; }
	inline svm_model& get_model() { return *svm_.model_; }
	inline void discard_problem() { svm_.discard_problem(); }
 
	template <typename InIter>
	inline float predict(InIter x)
	{
	  return svm_.predict(*svm_.model_, x);
	}

	template <typename InIter, typename OutIter>
	inline float predict_probability(InIter x, OutIter proba)
	{
	  return svm_.predict_probability(*svm_.model_, x, proba);
	} 

	inline float 
	cross_validation(int n_fold, float gamma, float C, float eps)
	{
	  svm_.param_.gamma = gamma;
	  svm_.param_.C = C;
	  svm_.param_.eps = eps;
	  NTA_ASSERT(0 < svm_.param_.gamma);

	  return svm_.cross_validation(n_fold);
	}

	inline int persistent_size() const
	{
	  return svm_.persistent_size();
	}

	inline void save(std::ostream& outStream) const
	{
	  svm_.save(outStream);
	}

	inline void load(std::istream& inStream)
	{
	  svm_.load(inStream);
	}
     };

      //--------------------------------------------------------------------------------
      class svm_01
      {
	svm<svm_01_traits> svm_;

      public:
	inline svm_01(int kernel =0, // 0 = linear, 1 = rbf
		      int n_dims =0,
		      float threshold =.9,
		      int cache_size =100,
		      int shrinking =1,
		      bool probability =false,
		      int seed =-1)
	  : svm_(kernel, n_dims, 1, 1, threshold, 1, 
		 cache_size, shrinking, probability, seed)
	{
	}
	
	template <typename InIter>
	inline void add_sample(float val, InIter x)
	{
	  svm_.problem_->add_sample(val, x);
	}

	inline void train(float gamma, float C, float eps)
	{
	  svm_.param_.gamma = gamma;
	  svm_.param_.C = C;
	  svm_.param_.eps = eps;
	  NTA_ASSERT(0 < svm_.param_.gamma);

	  if (svm_.model_) {
	    delete svm_.model_;
	    svm_.model_ = NULL;
	  }

	  svm_.model_ = svm_.train(*svm_.problem_, svm_.param_);
	}

	inline svm_problem01& get_problem() { return *svm_.problem_; }
	inline svm_model& get_model() { return *svm_.model_; }
	inline void discard_problem() { svm_.discard_problem(); }
 
	template <typename InIter>
	inline float predict(InIter x)
	{
	  return svm_.predict(*svm_.model_, x);
	}

	template <typename InIter, typename OutIter>
	inline float predict_probability(InIter x, OutIter proba)
	{
	  return svm_.predict_probability(*svm_.model_, x, proba);
	}

	inline float 
	cross_validation(int n_fold, float gamma, float C, float eps)
	{
	  svm_.param_.gamma = gamma;
	  svm_.param_.C = C;
	  svm_.param_.eps = eps;
	  NTA_ASSERT(0 < svm_.param_.gamma);

	  return svm_.cross_validation(n_fold);
	}

	inline int persistent_size() const 
	{
	  return svm_.persistent_size();
	}

	inline void save(std::ostream& outStream) const
	{
	  svm_.save(outStream);
	}

	inline void load(std::istream& inStream)
	{
	  svm_.load(inStream);
	}
      };

#include <nta/algorithms/svm_t.hpp>

    } // end namespace svm
  } // end namespace algorithms
} // end namespace nta

  //--------------------------------------------------------------------------------
#endif /* NTA_SVM_HPP */
