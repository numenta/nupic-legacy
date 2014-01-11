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

/*
Copyright (c) 2007 Xiang-Rui Wang and Chih-Jen Lin
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
 * This file contains declarations for the linear classifier.
 */

#ifndef NTA_LIBLINEAR_H
#define NTA_LIBLINEAR_H

namespace nta {
  namespace algorithms {
    namespace linear {

      //--------------------------------------------------------------------------------
      struct feature_node
      {
	int index;
	float value;
      };

      struct sparse_feature_vector
      {
	feature_node* data;

	sparse_feature_vector() : data(NULL) {}

	sparse_feature_vector(int n, const float* dense_array)
	  : data(new feature_node[n+1])
	{
	  for (int i = 0; i != n; ++i) {
	    data[i].index = i + 1;
	    data[i].value = dense_array[i];
	  }
	  data[n].index = -1;
	  data[n].value = 0;
	}

	~sparse_feature_vector()
	{
	  delete [] data;
	}
      };

      struct problem
      {
	problem(int l_, int n_, float bias_)
	  : l(l_), n(n_), 
	    bias(bias_), 
	    y(new int[l]), x(new feature_node* [l])
	{
	}

	~problem() 
	{
	  delete [] y;
	  delete [] x;
	}

	int l, n;
	float bias;            /* < 0 if no bias term */  
	int *y;
	struct feature_node **x;
      };

      enum { L2_LR, L1_LR, L2LOSS_SVM }; /* solver_type */

      struct parameter
      {
	parameter()
	  : solver_type(0), eps(0), C(0), 
	    nr_weight(0), weight_label(NULL), weight(NULL)
	{}

	parameter(int solver_type_, float eps_, float C_, 
		  int nr_weight_ =0, int *weight_label_ =NULL, float *weight_ =NULL)
	  : solver_type(solver_type_), eps(eps_), C(C_), 
	    nr_weight(nr_weight_), weight_label(weight_label_),
	    weight(weight_)
	{}

	~parameter()
	{
	  delete [] weight_label;
	  delete [] weight;
	}
	      
	int solver_type;

	/* these are for training only */
	float eps;	        /* stopping criteria */
	float C;
	int nr_weight;
	int *weight_label;
	float* weight;
      };

      struct model
      {
	model()
	  : nr_class(0), nr_feature(0),
	    w(NULL), label(NULL), 
	    bias(0)
	{
	}

	~model()
	{
	  delete [] w;
	  delete [] label;
	}

	void get_labels(int* label)
	{
	  if (label != NULL)
	    for(int i=0;i<nr_class;i++)
	      label[i] = label[i];
	}

	struct parameter param;
	int nr_class;		/* number of classes */
	int nr_feature;
	float *w;
	int *label;		/* label of each class (label[n]) */
	float bias;
      };

      class function
      {
      public:
	virtual float fun(float *w) = 0 ;
	virtual void grad(float *w, float *g) = 0 ;
	virtual void Hv(float *s, float *Hs) = 0 ;

	virtual int get_nr_variable(void) = 0 ;
	virtual ~function(void){}
      };

      class TRON
      {
      public:
	TRON(const function *fun_obj, float eps = 0.1, int max_iter = 1000);
	~TRON();

	void tron(float *w);

      private:
	int trcg(float delta, float *g, float *s, float *r);

	float eps;
	int max_iter;
	function *fun_obj;
      };

      //--------------------------------------------------------------------------------
      class linear 
      {
      public:
	linear(int solver_type, float eps, float C, 
	       int nr_weight =0, int *weight_label =NULL, float *weight =NULL)
	  : x_space(NULL),
	    the_param(new parameter(solver_type, eps, C, nr_weight, weight_label, weight)),
	    the_problem(NULL),
	    the_model(NULL)
	{}

	~linear()
	{
	  delete the_model;
	  delete the_param;
	  delete the_problem;
	  delete [] x_space;
	}

	feature_node *x_space;
	parameter* the_param;
	problem* the_problem;
	model* the_model;
	
	void create_problem(int l, int n, float *y, float *x, float bias = -1.0);

	inline void train() 
	{ 
	  the_model = train(the_problem, the_param); 
	}

	inline void cross_validation(int nr_fold, int *target)
	{
	  cross_validation(the_problem, the_param, nr_fold, target);
	}

	inline int predict_values(const float *x, float *dec_values)
	{
	  sparse_feature_vector sfv(the_problem->n, x);
	  return predict_values(the_model, sfv.data, dec_values);
	}

	inline int predict(const float *x)
	{
	  sparse_feature_vector sfv(the_problem->n, x);
	  return predict(the_model, sfv.data);
	}
  
	inline int predict_probability(const float *x, float *prob_estimates)
	{
	  sparse_feature_vector sfv(the_problem->n, x);
	  return predict_probability(the_model, sfv.data, prob_estimates);
	}

	inline int save_model(const char* model_file_name)
	{
	  return save_model(model_file_name, the_model);
	}

	inline void load_model(const char* model_file_name)
	{
	  if (the_model != NULL)
	    free(the_model);

	  the_model = load_model_(model_file_name);
	}

      private:
	struct model* train(const struct problem *prob, const struct parameter *param);
	void cross_validation(const struct problem *prob, 
			      const struct parameter *param, int nr_fold, int *target);
	int predict_values(const struct model *model_, 
			   const struct feature_node *x, float* dec_values);
	int predict(const struct model *model_, const struct feature_node *x);
	int predict_probability(const struct model *model_, 
				const struct feature_node *x, float* prob_estimates);
	int save_model(const char *model_file_name, const struct model *model_);
	struct model *load_model_(const char *model_file_name);
	void group_classes(const problem *prob, int *nr_class_ret, int **label_ret, 
			   int **start_ret, int **count_ret, int *perm);
	void train_one(const problem *prob, const parameter *param, 
		       float *w, float Cp, float Cn);
      };

    }
  }
}

//--------------------------------------------------------------------------------
#endif // NTA_LIBLINEAR_H 

