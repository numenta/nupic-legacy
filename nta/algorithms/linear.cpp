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
 * This file contains the implementation for the linear classifier package.
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

#include <algorithm>

#include <nta/algorithms/linear.hpp>

namespace nta {
  namespace algorithms {
    namespace linear {

#ifdef WIN32
#undef min
#undef max
#endif

      template <class T> inline void swap(T& x, T& y) { T t=x; x=y; y=t; }

#define Malloc(type,n) (type *)malloc((n)*sizeof(type))
      
#ifndef min
      template <class T> inline T min(T x,T y) { return (x<y)?x:y; }
#endif

#ifndef max
      template <class T> inline T max(T x,T y) { return (x>y)?x:y; }
#endif
      
      //--------------------------------------------------------------------------------
      float dnrm2_(int *n, float *x, int *incx)
      {
	long ix, nn = *n, iincx = *incx;
	float norm, scale, absxi, ssq, temp;

	if( nn > 0 && iincx > 0 )
	  {
	    if (nn == 1)
	      {
		norm = fabs(x[0]);
	      }  
	    else
	      {
		scale = 0.0f;
		ssq = 1.0f;

		for (ix=(nn-1)*iincx; ix>=0; ix-=iincx)
		  {
		    if (x[ix] != 0.0f)
		      {
			absxi = fabs(x[ix]);
			if (scale < absxi)
			  {
			    temp = scale / absxi;
			    ssq = ssq * (temp * temp) + 1.0f;
			    scale = absxi;
			  }
			else
			  {
			    temp = absxi / scale;
			    ssq += temp * temp;
			  }
		      }
		  }
		norm = scale * sqrt(ssq);
	      }
	  }
	else
	  norm = 0.0f;

	return norm;

      } /* dnrm2_ */

      float ddot_(int *n, float *sx, int *incx, float *sy, int *incy)
      {
	long i, m, nn = *n, iincx = *incx, iincy = *incy;
	float stemp = 0.0f;
	long ix, iy;

	if (nn > 0)
	  {
	    if (iincx == 1 && iincy == 1) /* code for both increments equal to 1 */
	      {
		m = nn-4;
		for (i = 0; i < m; i += 5)
		  stemp += sx[i] * sy[i] + sx[i+1] * sy[i+1] + sx[i+2] * sy[i+2] +
		    sx[i+3] * sy[i+3] + sx[i+4] * sy[i+4];

		for ( ; i < nn; i++)        /* clean-up loop */
		  stemp += sx[i] * sy[i];
	      }
	    else /* code for unequal increments or equal increments not equal to 1 */
	      {
		ix = 0;
		iy = 0;
		if (iincx < 0)
		  ix = (1 - nn) * iincx;
		if (iincy < 0)
		  iy = (1 - nn) * iincy;
		for (i = 0; i < nn; i++)
		  {
		    stemp += sx[ix] * sy[iy];
		    ix += iincx;
		    iy += iincy;
		  }
	      }
	  }

	return stemp;
      } /* ddot_ */

      int daxpy_(int *n, float *sa, float *sx, int *incx, float *sy,
		 int *incy)
      {
	long i, m, ix, iy, nn = *n, iincx = *incx, iincy = *incy;
	register float ssa = *sa;

	if( nn > 0 && ssa != 0.0f)
	  {
	    if (iincx == 1 && iincy == 1) /* code for both increments equal to 1 */
	      {
		m = nn-3;
		for (i = 0; i < m; i += 4)
		  {
		    sy[i] += ssa * sx[i];
		    sy[i+1] += ssa * sx[i+1];
		    sy[i+2] += ssa * sx[i+2];
		    sy[i+3] += ssa * sx[i+3];
		  }
		for ( ; i < nn; ++i) /* clean-up loop */
		  sy[i] += ssa * sx[i];
	      }
	    else /* code for unequal increments or equal increments not equal to 1 */
	      {
		ix = iincx >= 0 ? 0 : (1 - nn) * iincx;
		iy = iincy >= 0 ? 0 : (1 - nn) * iincy;
		for (i = 0; i < nn; i++)
		  {
		    sy[iy] += ssa * sx[ix];
		    ix += iincx;
		    iy += iincy;
		  }
	      }
	  }

	return 0;
      } /* daxpy_ */

      int dscal_(int *n, float *sa, float *sx, int *incx)
      {
	long i, m, nincx, nn = *n, iincx = *incx;
	float ssa = *sa;

	if (nn > 0 && iincx > 0)
	  {
	    if (iincx == 1) /* code for increment equal to 1 */
	      {
		m = nn-4;
		for (i = 0; i < m; i += 5)
		  {
		    sx[i] = ssa * sx[i];
		    sx[i+1] = ssa * sx[i+1];
		    sx[i+2] = ssa * sx[i+2];
		    sx[i+3] = ssa * sx[i+3];
		    sx[i+4] = ssa * sx[i+4];
		  }
		for ( ; i < nn; ++i) /* clean-up loop */
		  sx[i] = ssa * sx[i];
	      }
	    else /* code for increment not equal to 1 */
	      {
		nincx = nn * iincx;
		for (i = 0; i < nincx; i += iincx)
		  sx[i] = ssa * sx[i];
	      }
	  }

	return 0;
      } /* dscal_ */

      //--------------------------------------------------------------------------------
      TRON::TRON(const function *fun_obj, float eps, int max_iter)
      {
	this->fun_obj=const_cast<function *>(fun_obj);
	this->eps=eps;
	this->max_iter=max_iter;
      }

      TRON::~TRON()
      {
      }

      void TRON::tron(float *w)
      {
	// Parameters for updating the iterates.
	float eta0 = 1e-4f, eta1 = 0.25f, eta2 = 0.75f;

	// Parameters for updating the trust region size delta.
	float sigma1 = 0.25f, sigma2 = 0.5f, sigma3 = 4.0f;

	int n = fun_obj->get_nr_variable();
	int i, cg_iter;
	float delta, snorm, one=1.0f;
	float alpha, f, fnew, prered, actred, gs;
	int search = 1, iter = 1, inc = 1;
	float *s = new float[n];
	float *r = new float[n];
	float *w_new = new float[n];
	float *g = new float[n];

	for (i=0; i<n; i++)
	  w[i] = 0;

        f = fun_obj->fun(w);
	fun_obj->grad(w, g);
	delta = dnrm2_(&n, g, &inc);
	float gnorm1 = delta;
	float gnorm = gnorm1;

	if (gnorm1 < eps)
	  search = 0;

	iter = 1;

	while (iter <= max_iter && search)
	  {
	    cg_iter = trcg(delta, g, s, r);

	    memcpy(w_new, w, sizeof(float)*n);
	    daxpy_(&n, &one, s, &inc, w_new, &inc);

	    gs = ddot_(&n, g, &inc, s, &inc);
	    prered = -0.5f*(gs-ddot_(&n, s, &inc, r, &inc));
	    fnew = fun_obj->fun(w_new);

	    // Compute the actual reduction.
	    actred = f - fnew;

	    // On the first iteration, adjust the initial step bound.
	    snorm = dnrm2_(&n, s, &inc);
	    if (iter == 1)
	      delta = min(delta, snorm);

	    // Compute prediction alpha*snorm of the step.
	    if (fnew - f - gs <= 0.0f)
	      alpha = sigma3;
	    else
	      alpha = max(sigma1, (float)-0.5f*(gs/(fnew - f - gs)));

	    // Update the trust region bound according 
	    // to the ratio of actual to predicted reduction.
	    if (actred < eta0*prered)
	      delta = min(max(alpha, sigma1)*snorm, sigma2*delta);
	    else if (actred < eta1*prered)
	      delta = max(sigma1*delta, min(alpha*snorm, sigma2*delta));
	    else if (actred < eta2*prered)
	      delta = max(sigma1*delta, min(alpha*snorm, sigma3*delta));
	    else
	      delta = max(delta, min(alpha*snorm, sigma3*delta));

	    if (actred > eta0*prered)
	      {
		iter++;
		memcpy(w, w_new, sizeof(float)*n);
		f = fnew;
		fun_obj->grad(w, g);

		gnorm = dnrm2_(&n, g, &inc);
		if (gnorm < eps*gnorm1)
		  break;
	      }
	    if (f < 1.0e-32f)
	      {
		break;
	      }
	    if (fabs(actred) <= 0 && fabs(prered) <= 0)
	      {
		break;
	      }
	    if (fabs(actred) <= 1.0e-12f*fabs(f) &&
		fabs(prered) <= 1.0e-12f*fabs(f))
	      {
		break;
	      }
	  }

	delete[] g;
	delete[] r;
	delete[] w_new;
	delete[] s;
      }

      int TRON::trcg(float delta, float *g, float *s, float *r)
      {
	int i, inc = 1;
	int n = fun_obj->get_nr_variable();
	float one = 1.0f;
	float *d = new float[n];
	float *Hd = new float[n];
	float rTr, rnewTrnew, alpha, beta, cgtol;

	for (i=0; i<n; i++)
	  {
	    s[i] = 0;
	    r[i] = -g[i];
	    d[i] = r[i];
	  }
	cgtol = 0.1f*dnrm2_(&n, g, &inc);

	int cg_iter = 0;
	rTr = ddot_(&n, r, &inc, r, &inc);
	while (1)
	  {
	    if (dnrm2_(&n, r, &inc) <= cgtol)
	      break;
	    cg_iter++;
	    fun_obj->Hv(d, Hd);

	    alpha = rTr/ddot_(&n, d, &inc, Hd, &inc);
	    daxpy_(&n, &alpha, d, &inc, s, &inc);
	    if (dnrm2_(&n, s, &inc) > delta)
	      {
		alpha = -alpha;
		daxpy_(&n, &alpha, d, &inc, s, &inc);

		float std = ddot_(&n, s, &inc, d, &inc);
		float sts = ddot_(&n, s, &inc, s, &inc);
		float dtd = ddot_(&n, d, &inc, d, &inc);
		float dsq = delta*delta;
		float rad = sqrt(std*std + dtd*(dsq-sts));
		if (std >= 0)
		  alpha = (dsq - sts)/(std + rad);
		else
		  alpha = (rad - std)/dtd;
		daxpy_(&n, &alpha, d, &inc, s, &inc);
		alpha = -alpha;
		daxpy_(&n, &alpha, Hd, &inc, r, &inc);
		break;
	      }
	    alpha = -alpha;
	    daxpy_(&n, &alpha, Hd, &inc, r, &inc);
	    rnewTrnew = ddot_(&n, r, &inc, r, &inc);
	    beta = rnewTrnew/rTr;
	    dscal_(&n, &beta, d, &inc);
	    daxpy_(&n, &one, r, &inc, d, &inc);
	    rTr = rnewTrnew;
	  }

	delete[] d;
	delete[] Hd;

	return(cg_iter);
      }

      //--------------------------------------------------------------------------------
      class l2loss_svm_fun : public function
      {
      public:
	l2loss_svm_fun(const problem *prob_, float Cp, float Cn)
	  : C(new float[prob_->l]),
	    z(new float[prob_->l]),
	    D(new float[prob_->l]),
	    I(new int[prob_->l]),
	    sizeI(0),
	    prob(prob_)
	{
	  int i;
	  int l=prob->l;
	  int *y=prob->y;

	  for (i=0; i<l; i++)
	    {
	      if (y[i] == 1)
		C[i] = Cp;
	      else
		C[i] = Cn;
	    }
	}

	~l2loss_svm_fun()
	{
	  delete[] z;
	  delete[] D;
	  delete[] C;
	  delete[] I;
	}
	
	float fun(float *w)
	{
	  int i;
	  float f=0.0f;
	  int *y=prob->y;
	  int l=prob->l;
	  int n=prob->n;

	  Xv(w, z);
	  for(i=0;i<l;i++)
	    {
	      z[i] = y[i]*z[i];
	      float d = z[i]-1.0f;
	      if (d < 0)
		f += C[i]*d*d;
	    }
	  f = 2.0f*f;
	  for(i=0;i<n;i++)
	    f += w[i]*w[i];
	  f /= 2.0f;

	  return(f);
	}

	void grad(float *w, float *g)
	{
	  int i;
	  int *y=prob->y;
	  int l=prob->l;
	  int n=prob->n;

	  sizeI = 0;
	  for (i=0;i<l;i++)
	    if (z[i] < 1.0f)
	      {
		z[sizeI] = C[i]*y[i]*(z[i]-1);
		I[sizeI] = i;
		sizeI++;
	      }
	  subXTv(z, g);

	  for(i=0;i<n;i++)
	    g[i] = w[i] + 2.0f*g[i];
	}

	void Hv(float *s, float *Hs)
	{
	  int i;
	  int l=prob->l;
	  int n=prob->n;
	  float *wa = new float[l];

	  subXv(s, wa);
	  for(i=0;i<sizeI;i++)
	    wa[i] = C[I[i]]*wa[i];

	  subXTv(wa, Hs);
	  for(i=0;i<n;i++)
	    Hs[i] = s[i] + 2*Hs[i];
	  delete[] wa;
	}

	int get_nr_variable(void)
	{
	  return prob->n;
	}

      private:
	void Xv(float *v, float *Xv)
	{
	  int i;
	int l=prob->l;
	feature_node **x=prob->x;

	for(i=0;i<l;i++)
	  {
	    feature_node *s=x[i];
	    Xv[i]=0;
	    while(s->index!=-1)
	      {
		Xv[i]+=v[s->index-1]*s->value;
		s++;
	      }
	  }
	}

	void subXv(float *v, float *Xv)
	{
	  	int i;
	feature_node **x=prob->x;

	for(i=0;i<sizeI;i++)
	  {
	    feature_node *s=x[I[i]];
	    Xv[i]=0;
	    while(s->index!=-1)
	      {
		Xv[i]+=v[s->index-1]*s->value;
		s++;
	      }
	  }
	}

	void subXTv(float *v, float *XTv)
	{
		int i;
	int n=prob->n;
	feature_node **x=prob->x;

	for(i=0;i<n;i++)
	  XTv[i]=0;
	for(i=0;i<sizeI;i++)
	  {
	    feature_node *s=x[I[i]];
	    while(s->index!=-1)
	      {
		XTv[s->index-1]+=v[i]*s->value;
		s++;
	      }
	  }
	}

	float *C;
	float *z;
	float *D;
	int *I;
	int sizeI;
	const problem *prob;
      };

      //--------------------------------------------------------------------------------
      class l2_lr_fun : public function
      {
      public:
	l2_lr_fun(const problem *prob, float Cp, float Cn)
	{
	  int l = prob->l;
	  int *y = prob->y;

	  this->prob = prob;

	  z = new float[l];
	  D = new float[l];
	  C = new float[l];

	  for (int i = 0; i != l; ++i) 
	    C[i] = (y[i] == 1) ? Cp : Cn;
	}

	~l2_lr_fun()
	{
	  delete[] z;
	  delete[] D;
	  delete[] C;
	}
	
	float fun(float *w)
	{
	  float f=0.0f;
	  int *y=prob->y;
	  int l=prob->l;
	  int n=prob->n;

	  Xv(w, z);

	  for (int i = 0; i != l; ++i) {
	    float yz = y[i]*z[i];
	    if (yz >= 0)
	      f += C[i]*log(1.0f + exp(-yz));
	    else
	      f += C[i]*(-yz+log(1.0f + exp(yz)));
	  }
	  f = 2.0f*f;
	  for (int i = 0; i != n; ++i)
	    f += w[i]*w[i];
	  f /= 2.0f;

	  return(f);
	}

	void grad(float *w, float *g)
	{
	  int *y=prob->y;
	  int l=prob->l;
	  int n=prob->n;

	  for (int i = 0; i != l; ++i) {
	    z[i] = 1.0f/(1.0f + exp(-y[i]*z[i]));
	    D[i] = z[i]*(1.0f-z[i]);
	    z[i] = C[i]*(z[i]-1.0f)*y[i];
	  }

	  XTv(z, g);

	  for (int i = 0; i != n; ++i)
	    g[i] = w[i] + g[i];
	}

	void Hv(float *s, float *Hs)
	{
	  int l=prob->l;
	  int n=prob->n;
	  float *wa = new float[l];

	  Xv(s, wa);
	  
	  for (int i = 0; i != l; ++i)
	    wa[i] = C[i]*D[i]*wa[i];

	  XTv(wa, Hs);

	  for (int i = 0; i != n; ++i)
	    Hs[i] = s[i] + Hs[i];

	  delete[] wa;
	}

	int get_nr_variable(void)
	{
	  return prob->n;
	}

      private:
	void Xv(float *v, float *Xv)
	{
	 	int i;
	int l=prob->l;
	feature_node **x=prob->x;

	for(i=0;i<l;i++)
	  {
	    feature_node *s=x[i];
	    Xv[i]=0;
	    while(s->index!=-1)
	      {
		Xv[i]+=v[s->index-1]*s->value;
		s++;
	      }
	  }
	}

	void XTv(float *v, float *XTv)
	{
	int i;
	int l=prob->l;
	int n=prob->n;
	feature_node **x=prob->x;

	for(i=0;i<n;i++)
	  XTv[i]=0;
	for(i=0;i<l;i++)
	  {
	    feature_node *s=x[i];
	    while(s->index!=-1)
	      {
		XTv[s->index-1]+=v[i]*s->value;
		s++;
	      }
	  }
	}

	float *C;
	float *z;
	float *D;
	const problem *prob;
      };

      //--------------------------------------------------------------------------------

      // label: label name, start: begin of each class, count: #data of classes, perm: indices to the original data
      // perm, length l, must be allocated before calling this subroutine
      void linear::group_classes(const problem *prob, 
				 int *nr_class_ret, int **label_ret, 
				 int **start_ret, int **count_ret, int *perm)
      {
	int l = prob->l;
	int max_nr_class = 16;
	int nr_class = 0;
	int *label = Malloc(int,max_nr_class);
	int *count = Malloc(int,max_nr_class);
	int *data_label = Malloc(int,l);
	int i;

	for(i=0;i<l;i++)
	  {
	    int this_label = prob->y[i];
	    int j;
	    for(j=0;j<nr_class;j++)
	      {
		if(this_label == label[j])
		  {
		    ++count[j];
		    break;
		  }
	      }
	    data_label[i] = j;
	    if(j == nr_class)
	      {
		if(nr_class == max_nr_class)
		  {
		    max_nr_class *= 2;
		    label = (int *)realloc(label,max_nr_class*sizeof(int));
		    count = (int *)realloc(count,max_nr_class*sizeof(int));
		  }
		label[nr_class] = this_label;
		count[nr_class] = 1;
		++nr_class;
	      }
	  }

	int *start = Malloc(int,nr_class);
	start[0] = 0;
	for(i=1;i<nr_class;i++)
	  start[i] = start[i-1]+count[i-1];
	for(i=0;i<l;i++)
	  {
	    perm[start[data_label[i]]] = i;
	    ++start[data_label[i]];
	  }
	start[0] = 0;
	for(i=1;i<nr_class;i++)
	  start[i] = start[i-1]+count[i-1];

	*nr_class_ret = nr_class;
	*label_ret = label;
	*start_ret = start;
	*count_ret = count;
	free(data_label);
      }

      //--------------------------------------------------------------------------------
      void linear::train_one(const problem *prob, const parameter *param, float *w, float Cp, float Cn)
      {
	float eps=param->eps;

	function *fun_obj=NULL;
	switch(param->solver_type)
	  {
	  case L2_LR:
	    fun_obj=new l2_lr_fun(prob, Cp, Cn);
	    break;
	  case L2LOSS_SVM:
	    fun_obj=new l2loss_svm_fun(prob, Cp, Cn);
	    break;
	  default:
	    break;
	  }

	if(fun_obj)
	  {
	    TRON tron_obj(fun_obj, eps);

	    tron_obj.tron(w);

	    delete fun_obj;
	  }
      }

      //--------------------------------------------------------------------------------
      /**
       * For the dense case, look straight into float **x, which should be allocated 
       * in Python already.
       * Also do the sparse and the binary cases, separately.
       */
      void linear::create_problem(int l, int n, float *y, float *x, float bias)
      {
	the_problem = new problem(l, n, bias);
	x_space = new feature_node[l*(n+1)];
	
	int k = 0;
	
	for (int i = 0; i != l; ++i) {
	  
	  the_problem->x[i] = &x_space[k];
	  the_problem->y[i] = (int)y[i];
	  
	  for (int j = 0; j != n-1; ++j) {

	    x_space[k].index = j + 1;
	    x_space[k].value = x[k];
	    ++k;
	  }
	  
	  if (bias >= 0)
	    x_space[k++].value = bias;
	  
	  x_space[k++].index = -1;
	}
	
	if (bias >= 0) {
	  the_problem->n = n+1;
	  for(int i = 1 ; i != l; ++i)
	    (the_problem->x[i]-2)->index = the_problem->n; 
	  x_space[k-2].index = the_problem->n;
	} else
	  the_problem->n = n;
      }
      
      //--------------------------------------------------------------------------------
      model* linear::train(const problem *prob, const parameter *param)
      {
	int i;
	int l = prob->l;
	int n = prob->n;
	model *model_ = Malloc(model,1);

	if(prob->bias>=0)
	  model_->nr_feature=n-1;
	else
	  model_->nr_feature=n;
	model_->param = *param;
	model_->bias = prob->bias;

	int nr_class;
	int *label = NULL;
	int *start = NULL;
	int *count = NULL;
	int *perm = Malloc(int,l);

	// group training data of the same class
	group_classes(prob,&nr_class,&label,&start,&count,perm);

	model_->nr_class=nr_class;
	model_->label = Malloc(int,nr_class);
	for(i=0;i<nr_class;i++)
	  model_->label[i] = label[i];

	// calculate weighted C
	float *weighted_C = Malloc(float, nr_class);
	for(i=0;i<nr_class;i++)
	  weighted_C[i] = param->C;
	for(i=0;i<param->nr_weight;i++)
	  {
	    int j;
	    for(j=0;j<nr_class;j++)
	      if(param->weight_label[i] == label[j])
		break;
	    if(j == nr_class)
	      fprintf(stderr,"warning: class label %d specified in weight is not found\n", param->weight_label[i]);
	    else
	      weighted_C[j] *= param->weight[i];
	  }

	// constructing the subproblem
	feature_node **x = Malloc(feature_node *,l);
	for(i=0;i<l;i++)
	  x[i] = prob->x[perm[i]];

	int k;
	problem sub_prob(l, n, 0.0f);

	for(int k=0; k<sub_prob.l; k++)
	  sub_prob.x[k] = x[k];

	if(nr_class==2)
	  {
	    model_->w=Malloc(float, n);

	    int e0 = start[0]+count[0];
	    k=0;
	    for(; k<e0; k++)
	      sub_prob.y[k] = +1;
	    for(; k<sub_prob.l; k++)
	      sub_prob.y[k] = -1;

	    train_one(&sub_prob, param, &model_->w[0], weighted_C[0], weighted_C[1]);
	  }
	else
	  {
	    model_->w=Malloc(float, n*nr_class);
	    for(i=0;i<nr_class;i++)
	      {
		int si = start[i];
		int ei = si+count[i];

		k=0;
		for(; k<si; k++)
		  sub_prob.y[k] = -1;
		for(; k<ei; k++)
		  sub_prob.y[k] = +1;
		for(; k<sub_prob.l; k++)
		  sub_prob.y[k] = -1;

		train_one(&sub_prob, param, &model_->w[i*n], weighted_C[i], param->C);
	      }
	  }

	free(x);
	free(label);
	free(start);
	free(count);
	free(perm);
	free(weighted_C);
	return model_;
      }

      //--------------------------------------------------------------------------------
      int linear::save_model(const char *model_file_name, const struct model *model_)
      {
	const char *solver_type_table[]=
	{
	  "L2_LR", "L1_LR", "L2LOSS_SVM", NULL
	};

	int i;
	int nr_feature=model_->nr_feature;
	int n;
	const parameter& param = model_->param;

	if(model_->bias>=0)
	  n=nr_feature+1;
	else
	  n=nr_feature;
	FILE *fp = fopen(model_file_name,"w");
	if(fp==NULL) return -1;

	int nr_classifier;
	if(model_->nr_class==2)
	  nr_classifier=1;
	else
	  nr_classifier=model_->nr_class;

	fprintf(fp, "solver_type %s\n", solver_type_table[param.solver_type]);
	fprintf(fp, "nr_class %d\n", model_->nr_class);
	fprintf(fp, "label");
	for(i=0; i<model_->nr_class; i++)
	  fprintf(fp, " %d", model_->label[i]);
	fprintf(fp, "\n");

	fprintf(fp, "nr_feature %d\n", nr_feature);

	fprintf(fp, "bias %.16g\n", model_->bias);

	fprintf(fp, "w\n");
	for(i=0; i<n; i++)
	  {
	    int j;
	    for(j=0; j<nr_classifier; j++)
	      fprintf(fp, "%.16g ", model_->w[j*n+i]);
	    fprintf(fp, "\n");
	  }

	if (ferror(fp) != 0 || fclose(fp) != 0) return -1;
	else return 0;
      }

      //--------------------------------------------------------------------------------
      struct model* linear::load_model_(const char *model_file_name)
      {
	const char *solver_type_table[]=
	{
	  "L2_LR", "L1_LR", "L2LOSS_SVM", NULL
	};

	FILE *fp = fopen(model_file_name,"r");
	if(fp==NULL) return NULL;

	int i;
	int nr_feature;
	int n;
	int nr_class;
	float bias;
	model *model_ = Malloc(model,1);
	parameter& param = model_->param;

	model_->label = NULL;

	char cmd[81];
	while(1)
	  {
	    int rrr = fscanf(fp,"%80s",cmd);
            ++rrr;
	    if(strcmp(cmd,"solver_type")==0)
	      {
		int rrr = fscanf(fp,"%80s",cmd);
                ++rrr;
		int i;
		for(i=0;solver_type_table[i];i++)
		  {
		    if(strcmp(solver_type_table[i],cmd)==0)
		      {
			param.solver_type=i;
			break;
		      }
		  }
		if(solver_type_table[i] == NULL)
		  {
		    fprintf(stderr,"unknown solver type.\n");
		    free(model_->label);
		    free(model_);
		    fclose(fp);
		    return NULL;
		  }
	      }
	    else if(strcmp(cmd,"nr_class")==0)
	      {
		int rrr = fscanf(fp,"%d",&nr_class);
                ++rrr;
		model_->nr_class=nr_class;
	      }
	    else if(strcmp(cmd,"nr_feature")==0)
	      {
		int rrr = fscanf(fp,"%d",&nr_feature);
                ++rrr;
		model_->nr_feature=nr_feature;
	      }
	    else if(strcmp(cmd,"bias")==0)
	      {
		int rrr = fscanf(fp,"%f",&bias);
                ++rrr;
		model_->bias=bias;
	      }
	    else if(strcmp(cmd,"w")==0)
	      {
		break;
	      }
	    else if(strcmp(cmd,"label")==0)
	      {
		int nr_class = model_->nr_class;
		model_->label = Malloc(int,nr_class);
		for(int i=0;i<nr_class;i++) {
		  int rrr = fscanf(fp,"%d",&model_->label[i]);
                  ++rrr;
                }
	      }
	    else
	      {
		fprintf(stderr,"unknown text in model file: [%s]\n",cmd);
		free(model_);
		fclose(fp);
		return NULL;
	      }
	  }

	nr_feature=model_->nr_feature;
	if(model_->bias>=0)
	  n=nr_feature+1;
	else
	  n=nr_feature;

	int nr_classifier;
	if(nr_class==2)
	  nr_classifier = 1;
	else
	  nr_classifier = nr_class;

	model_->w=Malloc(float, n*nr_classifier);
	for(i=0; i<n; i++)
	  {
	    int j;
	    for(j=0; j<nr_classifier; j++) {
	      int rrr = fscanf(fp, "%f ", &model_->w[j*n+i]);
              ++rrr;
            }
	    int rrr = fscanf(fp, "\n");
            ++rrr;
	  }
	
	if (ferror(fp) != 0 || fclose(fp) != 0) 
	  return NULL;

	return model_;
      }

      //--------------------------------------------------------------------------------
      int linear::predict_values(const struct model *model_, 
				 const struct feature_node *x, 
				 float *dec_values)
      {
	int n;
	if(model_->bias>=0)
	  n=model_->nr_feature+1;
	else
	  n=model_->nr_feature;
	float *w=model_->w;
	int nr_class=model_->nr_class;
	int nr_classifier;
	if(nr_class==2)
	  nr_classifier = 1;
	else
	  nr_classifier = nr_class;
	for(int i=0;i<nr_classifier;i++)
	  {
	    const feature_node *lx = x;
	    float wtx=0.0f;
	    int idx;
	    for(; (idx=lx->index)!=-1; lx++)
	      {
		// the dimension of testing data may exceed that of training
		if(idx<=n)
		  wtx += w[i*n+idx-1]*lx->value;
	      }

	    dec_values[i] = wtx;
	  }

	if(nr_class==2)
	  return (dec_values[0]>0)?model_->label[0]:model_->label[1];
	else
	  {
	    int dec_max_idx = 0;
	    for(int i=1;i<nr_class;i++)
	      {
		if(dec_values[i] > dec_values[dec_max_idx])
		  dec_max_idx = i;
	      }
	    return model_->label[dec_max_idx];
	  }
      }

      //--------------------------------------------------------------------------------
      int linear::predict(const model *model_, const feature_node *x)
      {
	float *dec_values = Malloc(float, model_->nr_class);
	std::fill(dec_values, dec_values + model_->nr_class, (float) 0);
	int label=predict_values(model_, x, dec_values);
	free(dec_values);
	return label;
      }

      //--------------------------------------------------------------------------------
      int linear::predict_probability(const struct model *model_, 
				      const struct feature_node *x, 
				      float* prob_estimates)
      {
	if(model_->param.solver_type==L2_LR)
	  {
	    int i;
	    int nr_class=model_->nr_class;
	    int nr_classifier;
	    if(nr_class==2)
	      nr_classifier = 1;
	    else
	      nr_classifier = nr_class;

	    int label=predict_values(model_, x, prob_estimates);
	    for(i=0;i<nr_classifier;i++)
	      prob_estimates[i]=1.0f/(1.0f+exp(-prob_estimates[i]));

	    if(nr_class==2) // for binary classification
	      prob_estimates[1]=1.0f-prob_estimates[0];
	    else
	      {
		float sum=0.0f;
		for(i=0; i<nr_class; i++)
		  sum+=prob_estimates[i];

		for(i=0; i<nr_class; i++)
		  prob_estimates[i]=prob_estimates[i]/sum;
	      }

	    return label;		
	  }
	else
	  return 0;
      }

      //--------------------------------------------------------------------------------
      void linear::cross_validation(const problem *prob, const parameter *param, 
				    int nr_fold, int *target)
      {
	int i;
	int *fold_start = Malloc(int,nr_fold+1);
	int l = prob->l;
	int *perm = Malloc(int,l);

	for(i=0;i<l;i++) perm[i]=i;
	for(i=0;i<l;i++)
	  {
	    int j = i+rand()%(l-i);
	    swap(perm[i],perm[j]);
	  }
	for(i=0;i<=nr_fold;i++)
	  fold_start[i]=i*l/nr_fold;

	for(i=0;i<nr_fold;i++)
	  {
	    int begin = fold_start[i];
	    int end = fold_start[i+1];
	    int j,k;
	    struct problem subprob(l-(end-begin), prob->n, prob->bias);

	    k=0;
	    for(j=0;j<begin;j++)
	      {
		subprob.x[k] = prob->x[perm[j]];
		subprob.y[k] = prob->y[perm[j]];
		++k;
	      }
	    for(j=end;j<l;j++)
	      {
		subprob.x[k] = prob->x[perm[j]];
		subprob.y[k] = prob->y[perm[j]];
		++k;
	      }
	    struct model *submodel = train(&subprob,param);
	    for(j=begin;j<end;j++)
	      target[perm[j]] = predict(submodel,prob->x[perm[j]]);
	    delete submodel;
	  }
	free(fold_start);
	free(perm);
      }

      //--------------------------------------------------------------------------------
    }
  }
}
