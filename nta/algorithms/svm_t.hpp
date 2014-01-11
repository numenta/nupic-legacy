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

#include <math.h>

#ifndef NTA_SVM_T_HPP
#define NTA_SVM_T_HPP

//--------------------------------------------------------------------------------
template <typename TQ>
float Solver<TQ>::solve(int l, TQ& Q, const signed char *y_,
			float *alpha_, float C, float eps, int shrinking)
{
  this->l = l;
  this->Q = &Q;
  this->QD = Q.get_QD();
  this->C = C;
  this->eps = eps;
  unshrinked = false;
  
  p = new float [l];
  std::fill(p, p + l, float(-1.0));

  y = new signed char [l];
  std::copy(y_, y_ + l, y);

  alpha = new float [l];
  std::copy(alpha_, alpha_ + l, alpha);

  // initialize alpha_status
  {
    alpha_status = new int[l];
    for(int i=0;i<l;i++)
      update_alpha_status(i);
  }

  // initialize active set (for shrinking)
  {
    active_set = new int[l];
    for(int i=0;i<l;i++)
      active_set[i] = i;
    active_size = l;
  }

  // initialize gradient
  {
    G = new float[l];
    G_bar = new float[l];
    for(int i=0;i<l;i++)
      {
	G[i] = p[i];
	G_bar[i] = 0;
      }
    for(int i=0;i<l;i++)
      if(!is_lower_bound(i))
	{
	  const float *Q_i = Q.get_Q(i,l);
	  float alpha_i = alpha[i];
	  for(int j=0;j<l;j++)
	    G[j] += alpha_i*Q_i[j];
	  if(is_upper_bound(i))
	    for(int j=0;j<l;j++)
	      G_bar[j] += get_C(i) * Q_i[j];
	}
  }

  // optimization step

  int iter = 0;
  int counter = std::min(l,1000)+1;

  while (1)
    {
      // show progress and do shrinking

      if(--counter == 0)
	{
	  counter = std::min(l,1000);
	  if(shrinking) 
	    do_shrinking();
	}

      int i,j;
      
      if (select_working_set(i, j) != 0)
	{
	  // reconstruct the whole gradient
	  reconstruct_gradient();
	  // reset active set size and check
	  active_size = l;
	  if (select_working_set(i, j) != 0)
	    break;
	  else
	    counter = 1;	// do shrinking next iteration
	}
		
      ++iter;

      // update alpha[i] and alpha[j], handle bounds carefully
      const float *Q_i = Q.get_Q(i, active_size);
      const float *Q_j = Q.get_Q(j, active_size);

      NTA_ASSERT(Q_i != NULL);
      NTA_ASSERT(Q_j != NULL);

      float C_i = get_C(i);
      float C_j = get_C(j);

      float old_alpha_i = alpha[i];
      float old_alpha_j = alpha[j];

      if (y[i]!=y[j])
	{
	  float quad_coef = Q_i[i]+Q_j[j]+2*Q_i[j];
	  if (quad_coef <= 0)
	    quad_coef = TAU;
	  NTA_ASSERT(quad_coef > 0);
	  float delta = (-G[i]-G[j])/quad_coef;
	  float diff = alpha[i] - alpha[j];
	  alpha[i] += delta;
	  alpha[j] += delta;
			
	  if(diff > 0)
	    {
	      if(alpha[j] < 0)
		{
		  alpha[j] = 0;
		  alpha[i] = diff;
		}
	    }
	  else
	    {
	      if(alpha[i] < 0)
		{
		  alpha[i] = 0;
		  alpha[j] = -diff;
		}
	    }
	  if(diff > C_i - C_j)
	    {
	      if(alpha[i] > C_i)
		{
		  alpha[i] = C_i;
		  alpha[j] = C_i - diff;
		}
	    }
	  else
	    {
	      if(alpha[j] > C_j)
		{
		  alpha[j] = C_j;
		  alpha[i] = C_j + diff;
		}
	    }
	}
      else
	{
	  float quad_coef = Q_i[i]+Q_j[j]-2*Q_i[j];
	  if (quad_coef <= 0)
	    quad_coef = TAU;
	  NTA_ASSERT(quad_coef > 0);
	  float delta = (G[i]-G[j])/quad_coef;
	  float sum = alpha[i] + alpha[j];
	  alpha[i] -= delta;
	  alpha[j] += delta;

	  if(sum > C_i)
	    {
	      if(alpha[i] > C_i)
		{
		  alpha[i] = C_i;
		  alpha[j] = sum - C_i;
		}
	    }
	  else
	    {
	      if(alpha[j] < 0)
		{
		  alpha[j] = 0;
		  alpha[i] = sum;
		}
	    }
	  if(sum > C_j)
	    {
	      if(alpha[j] > C_j)
		{
		  alpha[j] = C_j;
		  alpha[i] = sum - C_j;
		}
	    }
	  else
	    {
	      if(alpha[i] < 0)
		{
		  alpha[i] = 0;
		  alpha[j] = sum;
		}
	    }
	}

      // update G
      float delta_alpha_i = alpha[i] - old_alpha_i;
      float delta_alpha_j = alpha[j] - old_alpha_j;
		
      for(int k=0;k<active_size;k++) {
	G[k] += Q_i[k]*delta_alpha_i + Q_j[k]*delta_alpha_j;
	NTA_ASSERT(-HUGE_VAL <= G[k] && G[k] <= HUGE_VAL);
      }

      // update alpha_status and G_bar
      {
	bool ui = is_upper_bound(i);
	bool uj = is_upper_bound(j);
	update_alpha_status(i);
	update_alpha_status(j);

	if(ui != is_upper_bound(i))
	  {
	    Q_i = Q.get_Q(i,l);
	    if(ui)
	      for(int k=0;k<l;k++)
		G_bar[k] -= C_i * Q_i[k];
	    else
	      for(int k=0;k<l;k++)
		G_bar[k] += C_i * Q_i[k];
	  }

	if(uj != is_upper_bound(j))
	  {
	    Q_j = Q.get_Q(j,l);
	    if(uj)
	      for(int k=0;k<l;k++)
		G_bar[k] -= C_j * Q_j[k];
	    else
	      for(int k=0;k<l;k++)
		G_bar[k] += C_j * Q_j[k];
	  }
      }
    }
  
  float rho = calculate_rho();

  // put back the solution
  for(int i=0;i<l;i++)
    alpha_[active_set[i]] = alpha[i];

  delete[] p;
  delete[] y;
  delete[] alpha;
  delete[] alpha_status;
  delete[] active_set;
  delete[] G;
  delete[] G_bar;

  return rho;
}

//--------------------------------------------------------------------------------
template <typename TQ>
void Solver<TQ>::swap_index(int i, int j)
{
  Q->swap_index(i,j);
  std::swap(y[i],y[j]);
  std::swap(G[i],G[j]);
  std::swap(alpha_status[i],alpha_status[j]);
  std::swap(alpha[i],alpha[j]);
  std::swap(p[i],p[j]);
  std::swap(active_set[i],active_set[j]);
  std::swap(G_bar[i],G_bar[j]);
}

//--------------------------------------------------------------------------------
template <typename TQ>
void Solver<TQ>::reconstruct_gradient()
{
  // reconstruct inactive elements of G from G_bar and free variables

  if(active_size == l) return;

  for(int i=active_size;i<l;i++)
    G[i] = G_bar[i] + p[i];
	
  for(int i=0;i<active_size;i++)
    if(is_free(i))
      {
	const float *Q_i = Q->get_Q(i,l);
	float alpha_i = alpha[i];
	for(int j=active_size;j<l;j++)
	  G[j] += alpha_i * Q_i[j];
      }
}

//--------------------------------------------------------------------------------
// return 1 if already optimal, return 0 otherwise
template <typename TQ>
int Solver<TQ>::select_working_set(int &out_i, int &out_j)
{
  // return i,j such that
  // i: maximizes -y_i * grad(f)_i, i in I_up(\alpha)
  // j: minimizes the decrease of obj value
  //    (if quadratic coefficeint <= 0, replace it with tau)
  //    -y_j*grad(f)_j < -y_i*grad(f)_i, j in I_low(\alpha)
	
  float Gmax = -HUGE_VAL; //std::numeric_limits<float>::max();
  float Gmax2 = -HUGE_VAL; //std::numeric_limits<float>::max();
  int Gmax_idx = -1;
  int Gmin_idx = -1;
  float obj_diff_min = HUGE_VAL; //std::numeric_limits<float>::max();

  for (int t=0;t<active_size;t++) {

    if (y[t] == +1)	
      {
	if (!is_upper_bound(t))
	  if (-G[t] >= Gmax)
	    {
	      Gmax = -G[t];
	      Gmax_idx = t;
	    }
      }
    else
      {
	if (!is_lower_bound(t))
	  if (G[t] >= Gmax)
	    {
	      Gmax = G[t];
	      Gmax_idx = t;
	    }
      }
  }

  int i = Gmax_idx;
  const float *Q_i = NULL;

  if (i != -1) // NULL Q_i not accessed: Gmax=-INF if i=-1
    Q_i = Q->get_Q(i,active_size);

  NTA_ASSERT(0 <= i);

  for(int j=0;j<active_size;j++)
    {
      if (y[j] == +1)
	{
	  if (!is_lower_bound(j))
	    {
	      float grad_diff=Gmax+G[j];

	      if (G[j] >= Gmax2)
		Gmax2 = G[j];

	      if (grad_diff > 0)
		{
		  float obj_diff; 
		  float quad_coef=Q_i[i]+QD[j]-2*y[i]*Q_i[j];

		  if (quad_coef > 0)
		    obj_diff = -(grad_diff*grad_diff)/quad_coef;
		  else
		    obj_diff = -(grad_diff*grad_diff)/TAU;

		  if (obj_diff <= obj_diff_min)
		    {
		      Gmin_idx=j;
		      obj_diff_min = obj_diff;
		    }
		}
	    }
	}
      else
	{
	  if (!is_upper_bound(j))
	    {
	      float grad_diff= Gmax - G[j];

	      if (-G[j] >= Gmax2)
		Gmax2 = -G[j];

	      if (grad_diff > 0)
		{
		  float obj_diff; 
		  float quad_coef = Q_i[i]+QD[j]+2*y[i]*Q_i[j];

		  if (quad_coef > 0)
		    obj_diff = -(grad_diff*grad_diff)/quad_coef;
		  else
		    obj_diff = -(grad_diff*grad_diff)/TAU;

		  if (obj_diff <= obj_diff_min)
		    {
		      Gmin_idx = j;
		      obj_diff_min = obj_diff;
		    }
		}
	    } 
	}
    }

  if (Gmax + Gmax2 < eps)
    return 1;

  out_i = Gmax_idx;
  out_j = Gmin_idx;

  NTA_ASSERT(0 <= out_i);
  NTA_ASSERT(0 <= out_j);

  return 0;
}

//--------------------------------------------------------------------------------
template <typename TQ>
bool Solver<TQ>::be_shrunken(int i, float Gmax1, float Gmax2)
{
  if(is_upper_bound(i))
    {
      if(y[i]==+1)
	return(-G[i] > Gmax1);
      else
	return(-G[i] > Gmax2);
    }
  else if(is_lower_bound(i))
    {
      if(y[i]==+1)
	return(G[i] > Gmax2);
      else	
	return(G[i] > Gmax1);
    }
  else
    return(false); 
}

//--------------------------------------------------------------------------------
template <typename TQ>
void Solver<TQ>::do_shrinking()
{
  float Gmax1 = -INF;		// max { -y_i * grad(f)_i | i in I_up(\alpha) }
  float Gmax2 = -INF;		// max { y_i * grad(f)_i | i in I_low(\alpha) }

  // find maximal violating pair first
  for(int i=0;i<active_size;i++)
    {
      if(y[i]==+1)	
	{
	  if(!is_upper_bound(i))	
	    {
	      if(-G[i] >= Gmax1)
		Gmax1 = -G[i];
	    }
	  if(!is_lower_bound(i))	
	    {
	      if(G[i] >= Gmax2)
		Gmax2 = G[i];
	    }
	}
      else	
	{
	  if(!is_upper_bound(i))	
	    {
	      if(-G[i] >= Gmax2)
		Gmax2 = -G[i];
	    }
	  if(!is_lower_bound(i))	
	    {
	      if(G[i] >= Gmax1)
		Gmax1 = G[i];
	    }
	}
    }

  // shrink

  for(int i=0;i<active_size;i++)
    if (be_shrunken(i, Gmax1, Gmax2))
      {
	active_size--;
	while (active_size > i)
	  {
	    if (!be_shrunken(active_size, Gmax1, Gmax2))
	      {
		swap_index(i,active_size);
		break;
	      }
	    active_size--;
	  }
      }

  // unshrink, check all variables again before final iterations

  if(unshrinked || Gmax1 + Gmax2 > eps*10) return;
	
  unshrinked = true;
  reconstruct_gradient();

  for(int i=l-1;i>=active_size;i--)
    if (!be_shrunken(i, Gmax1, Gmax2))
      {
	while (active_size < i)
	  {
	    if (be_shrunken(active_size, Gmax1, Gmax2))
	      {
		swap_index(i,active_size);
		break;
	      }
	    active_size++;
	  }
	active_size++;
      }
}

//--------------------------------------------------------------------------------
template <typename TQ>
float Solver<TQ>::calculate_rho()
{
  float r;
  int nr_free = 0;
  float ub = INF, lb = -INF, sum_free = 0;
  for(int i=0;i<active_size;i++)
    {
      float yG = y[i]*G[i];

      if(is_upper_bound(i))
	{
	  if(y[i]==-1)
	    ub = std::min(ub,yG);
	  else
	    lb = std::max(lb,yG);
	}
      else if(is_lower_bound(i))
	{
	  if(y[i]==+1)
	    ub = std::min(ub,yG);
	  else
	    lb = std::max(lb,yG);
	}
      else
	{
	  ++nr_free;
	  sum_free += yG;
	}
    }

  if(nr_free>0)
    r = sum_free/nr_free;
  else
    r = (ub+lb)/2;

  return r;
}

//--------------------------------------------------------------------------------
// SVM
//--------------------------------------------------------------------------------
// Platt's binary SVM Probablistic Output: an improvement from Lin et al.
template <typename traits>
void svm<traits>::sigmoid_train(int l, 
				const Vector& dec_values, 
				const Vector& labels, 
				float& A, float& B)
{
  float prior1=0, prior0 = 0;

  for (int i=0;i<l;i++)
    if (labels[i] > 0) 
      prior1+=1;
    else 
      prior0+=1;
	
  int max_iter=100; 	// Maximal number of iterations
  float min_step=float(1e-10);	// Minimal step taken in line search
  float sigma=float(1e-3);	// For numerically strict PD of Hessian
  float eps=float(1e-5);
  float hiTarget=(prior1+float(1.0))/(prior1+float(2.0));
  float loTarget=float(1.0)/(prior0+float(2.0));
  Vector t(l);
  float fApB,p,q,h11,h22,h21,g1,g2,det,dA,dB,gd,stepsize;
  float newA,newB,newf,d1,d2;
	
  // Initial Point and Initial Fun Value
  A=0.0; B=log((prior0+float(1.0))/(prior1+float(1.0)));
  float fval = 0.0;

  for (int i=0;i<l;i++)
    {
      if (labels[i]>0) t[i]=hiTarget;
      else t[i]=loTarget;
      fApB = dec_values[i]*A+B;
      if (fApB>=0)
	fval += t[i]*fApB + log(float(1.0)+exp(-fApB));
      else
	fval += (t[i] - float(1.0))*fApB +log(float(1.0)+exp(fApB));
    }
  
  for (int iter=0;iter<max_iter;iter++)
    {
      // Update Gradient and Hessian (use H' = H + sigma I)
      h11=sigma; // numerically ensures strict PD
      h22=sigma;
      h21=0.0f;g1=0.0f;g2=0.0f;
      for (int i=0;i<l;i++)
	{
	  fApB = dec_values[i]*A+B;
	  if (fApB >= 0)
	    {
	      p=exp(-fApB)/(1.0f+exp(-fApB));
	      q=1.0f/(1.0f+exp(-fApB));
	    }
	  else
	    {
	      p=1.0f/(1.0f+exp(fApB));
	      q=exp(fApB)/(1.0f+exp(fApB));
	    }
	  d2=p*q;
	  h11+=dec_values[i]*dec_values[i]*d2;
	  h22+=d2;
	  h21+=dec_values[i]*d2;
	  d1=t[i]-p;
	  g1+=dec_values[i]*d1;
	  g2+=d1;
	}

      // Stopping Criteria
      if (fabs(g1)<eps && fabs(g2)<eps)
	break;

      // Finding Newton direction: -inv(H') * g
      det=h11*h22-h21*h21;
      dA=-(h22*g1 - h21 * g2) / det;
      dB=-(-h21*g1+ h11 * g2) / det;
      gd=g1*dA+g2*dB;

      stepsize = 1; 		// Line Search
      while (stepsize >= min_step)
	{
	  newA = A + stepsize * dA;
	  newB = B + stepsize * dB;

	  // New function value
	  newf = 0.0;
	  for (int i=0;i<l;i++)
	    {
	      fApB = dec_values[i]*newA+newB;
	      if (fApB >= 0)
		newf += t[i]*fApB + log(1.0f+exp(-fApB));
	      else
		newf += (t[i] - 1.0f)*fApB +log(1.0f+exp(fApB));
	    }
	  // Check sufficient decrease
	  if (newf<fval+0.0001f*stepsize*gd)
	    {
	      A=newA;B=newB;fval=newf;
	      break;
	    }
	  else
	    stepsize = stepsize / 2.0f;
	}

      if (stepsize < min_step)
	{
	  break;
	}
    }
}

//--------------------------------------------------------------------------------
template <typename traits>
inline float svm<traits>::sigmoid_predict(float decision_value, float A, float B)
{
  float fApB = decision_value*A+B;
  if (fApB >= 0)
    return exp(-fApB)/(1.0f+exp(-fApB));
  else
    return 1.0f/(1.0f+exp(fApB));
}

//--------------------------------------------------------------------------------
template <typename traits>
inline float svm<traits>::rbf_function(float* x, float* x_end, float* y) const
{
  float sum = 0;

#if defined(NTA_ASM) && defined(NTA_PLATFORM_win32)
  if (with_sse) {

    __asm {
        mov     esi, x
        mov     edi, y
  
        xorps  xmm1, xmm1
        xorps  xmm3, xmm3
        xorps  xmm4, xmm4
  
        label0:
          movaps xmm0, [esi]
          movaps xmm2, [esi + 16]
          subps  xmm0, [edi]
          subps  xmm2, [edi + 16]
          mulps  xmm0, xmm0
          mulps  xmm2, xmm2
          addps  xmm1, xmm0
          addps  xmm3, xmm2

          add     esi, 32
          add     edi, 32
          cmp     esi, x_end
        jne  label0
  
        addps  xmm1, xmm3
        haddps  xmm1, xmm4
        haddps  xmm1, xmm4
        movss    sum, xmm1
        }

  } else { // no sse

    while (x != x_end) {
      float d = *x - *y;
      sum += d * d;
      ++x; ++y;
    }
  }

#elif defined(NTA_ASM) && defined(NTA_PLATFORM_darwin86) 

  if (with_sse) {
    
  asm(
      "xorps %%xmm4,%%xmm4\n\t" // only contains zeros on purpose
      "xorps %%xmm1,%%xmm1\n\t"
      "xorps %%xmm3,%%xmm3\n\t"

      "0:\t\n"
      "movaps   (%%esi), %%xmm0\n\t"
      "movaps 16(%%esi), %%xmm2\n\t"
      "subps    (%%edi), %%xmm0\n\t"
      "subps  16(%%edi), %%xmm2\n\t"
      "mulps  %%xmm0, %%xmm0\n\t"
      "mulps  %%xmm2, %%xmm2\n\t"
      "addps  %%xmm0, %%xmm1\n\t"
      "addps  %%xmm2, %%xmm3\n\t"

      "addl $32, %%esi\n\t"
      "addl $32, %%edi\n\t"
      "cmpl %1, %%esi\n\t"
      "jne 0b\n\t"

      "addps %%xmm3, %%xmm1\n\t"
      "haddps %%xmm4, %%xmm1\n\t"
      "haddps %%xmm4, %%xmm1\n\t"
      "movss  %%xmm1, %0\n\t"

      : "=m" (sum)
      : "m" (x_end), "S" (x), "D" (y)
      : 
      );

  } else { // no sse

    while (x != x_end) {
      float d = *x - *y;
      sum += d * d;
      ++x; ++y;
    }
  }

#else // not NTA_PLATFORM_darwin86, not NTA_PLATFORM_win32; or not NTA_ASM

  while (x != x_end) {
    float d = *x - *y;
    sum += d * d;
    ++x; ++y;
  }

#endif
  
  return exp(-param_.gamma*sum);
}

//--------------------------------------------------------------------------------
template <typename traits>
inline float svm<traits>::linear_function(float* x, float* x_end, float* y) const
{
  float sum = 0;
  while (x != x_end) {
    sum += *x * *y;
    ++x; ++y;
  }
  
  return sum;
}

//--------------------------------------------------------------------------------
template <typename traits>
inline void 
svm<traits>::multiclass_probability(Matrix& pairwise_proba, Vector& prob_estimates)
{
  int n_class = pairwise_proba.nrows(), max_iter = std::max(100, n_class);

  Matrix Q(n_class, n_class);
  Vector Qp(n_class);
  float pQp, eps = float(0.005)/float(n_class);

  for (int t = 0; t < n_class; ++t) {

    prob_estimates[t] = float(1.0)/float(n_class);  // Valid if n_class = 1
    Q(t,t)=0;

    for (int j=0;j<t;j++) {
      Q(t,t)+=pairwise_proba(j,t)*pairwise_proba(j,t);
      Q(t,j)=Q(j,t);
    }

    for (int j=t+1;j<n_class;j++) {
      Q(t,t)+=pairwise_proba(j,t)*pairwise_proba(j,t);
      Q(t,j)=-pairwise_proba(j,t)*pairwise_proba(t,j);
    }
  }

  for (int iter = 0; iter < max_iter; ++iter) {
    // stopping condition, recalculate QP,pQP for numerical accuracy
    pQp=0;
    for (int t=0;t<n_class;t++) {
      Qp[t]=0;
      for (int j=0;j<n_class;j++)
	Qp[t]+=Q(t,j)*prob_estimates[j];
      pQp+=prob_estimates[t]*Qp[t];
    }
    float max_error=0;
    for (int t=0;t<n_class;t++) {
      float error=fabs(Qp[t]-pQp);
      if (error>max_error)
	max_error=error;
    }

    if (max_error<eps) 
      break;
		
    for (int t=0;t<n_class;t++) {
      float diff=(-Qp[t]+pQp)/Q(t,t);
      prob_estimates[t]+=diff;
      pQp=(pQp+diff*(diff*Q(t,t)+2*Qp[t]))/(1+diff)/(1+diff);
      for (int j=0;j<n_class;j++) {
	Qp[j]=(Qp[j]+diff*Q(t,j))/(1+diff);
	prob_estimates[j]/=(1+diff);
      }
    }
  }
}    

//--------------------------------------------------------------------------------
// Cross-validation decision values for probability estimates
template <typename traits>
void 
svm<traits>::binary_probability(const problem_type& prob, float& probA, float& probB)
{
  int nr_fold = 5, l = prob.size(), n_dims = prob.n_dims();
  std::vector<int> perm(l);
  Vector dec_values(l);

  // random shuffle
  for(int i=0;i<l;i++) 
    perm[i]=i;
  
  for(int i=0;i<l;i++) {
    int j = i+rng_.getUInt32()%(l-i);
    std::swap(perm[i], perm[j]);
  }
  
  for(int i=0;i<nr_fold;i++) {

    int begin = i*l/nr_fold;
    int end = (i+1)*l/nr_fold;

    problem_type sub_prob(n_dims, false);
    int sub_prob_size = l-(end-begin);
    sub_prob.resize(sub_prob_size);
			
    int k=0;
    for (int j = 0; j < begin; ++j, ++k)
      sub_prob.set_sample(k, prob.get_sample(perm[j]));

    for (int j = end; j < l; ++j, ++k)
      sub_prob.set_sample(k, prob.get_sample(perm[j]));

    int p_count=0,n_count=0;
    for(int j=0;j<k;j++)
      if(sub_prob.y_[j]>0)
	p_count++;
      else
	n_count++;

    if(p_count==0 && n_count==0)
      for(int j=begin;j<end;j++)
	dec_values[perm[j]] = 0;
    else if(p_count > 0 && n_count == 0)
      for(int j=begin;j<end;j++)
	dec_values[perm[j]] = 1;
    else if(p_count == 0 && n_count > 0)
      for(int j=begin;j<end;j++)
	dec_values[perm[j]] = -1;
    else {

      svm_parameter sub_param(param_.kernel,
			      false, 
			      param_.gamma,
			      1.0, //param_.C, HERE 
			      param_.eps,
			      param_.cache_size,
			      param_.shrinking);

      sub_param.weight_label.resize(2);
      sub_param.weight.resize(2);
      sub_param.weight_label[0]=+1;
      sub_param.weight_label[1]=-1;
      sub_param.weight[0]=param_.C;
      sub_param.weight[1]=param_.C;

      svm_model *sub_model = train(sub_prob, sub_param);

#ifdef NTA_PLATFORM_win32
      float* x_tmp = (float*) _aligned_malloc(4*prob.n_dims(), 16);
#else
      float* x_tmp = new float[prob.n_dims()];
#endif

      for(int j=begin;j<end;j++) {
	prob.dense(perm[j], x_tmp);
	float val;
	predict_values(*sub_model, x_tmp, &val); 
	// ensure +1 -1 order; reason not using CV subroutine
	dec_values[perm[j]] = val * sub_model->label[0];
      }		

#ifdef NTA_PLATFORM_win32
      _aligned_free(x_tmp);
#else
      delete [] x_tmp;
#endif

      delete sub_model;
    }
  }		
  
  sigmoid_train(l, dec_values, prob.y_, probA, probB);
}

//--------------------------------------------------------------------------------
template <typename traits>
void svm<traits>::group_classes(const problem_type& prob, 
				std::vector<int>& label,
				std::vector<int>& start,
				std::vector<int>& count,
				std::vector<int>& perm)
{
  int l = prob.size(), n_class = 0;
  std::vector<int> data_label(l);

  // group training data of the same class
  for (int i = 0; i < l; ++i) {

    int j = 0, this_label = (int)prob.y_[i];

    for (j = 0; j < n_class; ++j)
      if (this_label == label[j]) {
	++count[j];
	break;
      }
    
    data_label[i] = j;

    if (j == n_class) {
      label.push_back(this_label);
      count.push_back(1);
      ++n_class;
    }
  }

  start.resize(n_class);
  
  start[0] = 0;
  for (int i = 1; i < n_class; ++i)
    start[i] = start[i-1]+count[i-1];

  for (int i = 0; i < l; ++i) {
    perm[start[data_label[i]]] = i;
    ++start[data_label[i]];
  }

  start[0] = 0;
  for (int i = 1; i < n_class; ++i)
    start[i] = start[i-1]+count[i-1];
}

//--------------------------------------------------------------------------------
template <typename traits>
svm_model* svm<traits>::train(const problem_type& prob, const svm_parameter& param)
{
  int l = prob.size(), n_dims = prob.n_dims();
  std::vector<int> label, count, start, perm(l);

  // svm_train
  group_classes(prob, label, start, count, perm);
  int n_class = (int) label.size();

  // train k*(k-1)/2 models
  size_t m = n_class*(n_class-1)/2;
  std::vector<bool> nonzero(l, false);
  std::vector<decision_function> f(m);

  svm_model* model = new svm_model;

  if (param.probability) {
    model->probA.resize(m);
    model->probB.resize(m);
  }

  int p = 0;
  for (int i = 0; i < n_class; ++i) {
    for (int j = i+1; j < n_class; ++j, ++p) {
      
      int si = start[i], sj = start[j];
      int ci = count[i], cj = count[j];
      int sub_prob_size = ci+cj;
      
      problem_type sub_prob(n_dims, sub_prob_size, false);

      for (int k = 0; k < ci; ++k) {
	sub_prob.set_sample(k, prob.get_sample(perm[si+k]));
	sub_prob.y_[k] = +1;
      }
	
      for (int k = 0; k < cj; ++k) {
	sub_prob.set_sample(ci+k, prob.get_sample(perm[sj+k]));
	sub_prob.y_[ci+k] = -1;
      }

      // binary svc probability
      if (param.probability)
	binary_probability(sub_prob, model->probA[p], model->probB[p]);

      // solve_c_svc
      float *alpha = new float [sub_prob_size];
      std::fill(alpha, alpha + sub_prob_size, float(0));

      signed char *y = new signed char[l];
      for (int k = 0; k < sub_prob_size; ++k) 
	y[k] = sub_prob.y_[k] > 0 ? +1 : -1;

      q_matrix_type q(sub_prob, param.gamma, param.kernel, param.cache_size);	
      Solver<q_matrix_type> s;

      //param.print();
      //sub_prob.print();
      
      float rho = 
	s.solve(sub_prob_size, q, y, alpha, param.C, param.eps, param.shrinking);
	
      for (int k = 0; k < sub_prob_size; ++k)
	alpha[k] *= y[k];
	
      f[p].alpha = alpha;
      f[p].rho = rho;
     
      for (int k = 0; k < ci; ++k)
	if(!nonzero[si+k] && fabs(f[p].alpha[k]) > 0)
	  nonzero[si+k] = true;
	
      for (int k = 0; k < cj; ++k)
	if(!nonzero[sj+k] && fabs(f[p].alpha[ci+k]) > 0)
	  nonzero[sj+k] = true;

      delete [] y;
    } 
  }

  // finish building model
  model->label.resize(n_class);
  for (int i = 0; i < n_class; ++i)
    model->label[i] = label[i];
		
  model->rho.resize(m);
  for (size_t i = 0; i < m; ++i)
    model->rho[i] = f[i].rho;

  int total_sv = 0;
  std::vector<int> nz_count(n_class);
  model->n_sv.resize(n_class);
  
  for (int i = 0; i < n_class; ++i) {
    int n_sv = 0;
    for(int j=0;j<count[i];j++)
      if(nonzero[start[i]+j]) {
	++n_sv;
	++total_sv;
      }
    model->n_sv[i] = n_sv;
    nz_count[i] = n_sv;
  }
		
  model->n_dims_ = n_dims;

  for (int i = 0; i != l; ++i)
    if (nonzero[i]) {

#ifdef NTA_PLATFORM_win32
      float* new_sv = (float*) _aligned_malloc(4*n_dims, 16);
#else
      float *new_sv = new float[n_dims];
#endif

      prob.dense(perm[i], new_sv);
      model->sv.push_back(new_sv);
    }

  std::vector<int> nz_start(n_class);
  nz_start[0] = 0;
  for (int i = 1; i < n_class; ++i)
    nz_start[i] = nz_start[i-1] + nz_count[i-1];

  model->sv_coef.resize(n_class-1);
  for (int i = 0; i < n_class-1; ++i)
    model->sv_coef[i] = new float [total_sv];

  p = 0;
  for (int i = 0; i < n_class; ++i) {
    for(int j = i+1; j < n_class; ++j, ++p) {

      // classifier (i,j): coefficients with
      // i are in sv_coef[j-1][nz_start[i]...],
      // j are in sv_coef[i][nz_start[j]...]

      int si = start[i], sj = start[j];
      int ci = count[i], cj = count[j];
				
      int q = nz_start[i];
      for (int k = 0; k < ci; ++k)
	if (nonzero[si+k])
	  model->sv_coef[j-1][q++] = f[p].alpha[k];

      q = nz_start[j];
      for (int k = 0; k < cj; ++k)
	if (nonzero[sj+k])
	  model->sv_coef[i][q++] = f[p].alpha[ci+k];
    }
  }

  // ------------------------------------------------------------
  // Compute hyperplanes
  // ------------------------------------------------------------

  if (param.kernel == 0) { // Linear kernel only

    model->w.resize(m);
    for (size_t i = 0; i != m; ++i) 
      model->w[i].resize(n_dims);

    p = 0;
    
    for (int i = 0; i < n_class; ++i) {
      for(int j = i+1; j < n_class; ++j, ++p) {
      
	int si = nz_start[i], sj = nz_start[j];
	int ci = model->n_sv[i], cj = model->n_sv[j];
	float *coef1 = model->sv_coef[j-1], *coef2 = model->sv_coef[i];

	for (int dim = 0; dim != n_dims; ++dim) {

	  float sum = 0;
	  for (int k = 0; k < ci; ++k) {
	    sum += coef1[si+k] * (model->sv[si+k])[dim];
	  }

	  for (int k = 0; k < cj; ++k) {
	    sum += coef2[sj+k] * (model->sv[sj+k])[dim];
	  }

	  model->w[p][dim] = sum;
	}
      }
    }
  }

  return model;
}

//--------------------------------------------------------------------------------
template <typename traits> 
void svm<traits>::predict_values(const svm_model& model, float* x, float* dec_values)
{
  int n_class = model.n_class(), l = model.size();

  Vector kvalue(l);

  if (param_.kernel == 0) {

    for (int i=0;i<l;i++)
      kvalue[i] = linear_function(x, x + model.n_dims(), model.sv[i]);

  } else if (param_.kernel == 1) {

    for (int i=0;i<l;i++) 
      kvalue[i] = rbf_function(x, x + model.n_dims(), model.sv[i]);
  }

  std::vector<int> start(n_class);
  start[0] = 0;
  for(int i=1;i<n_class;i++)
    start[i] = start[i-1]+model.n_sv[i-1];
  
  int p=0;
  for(int i=0;i<n_class;i++)
    for(int j=i+1;j<n_class;j++, ++p) {

      float sum = 0;
      int si = start[i], sj = start[j];
      int ci = model.n_sv[i], cj = model.n_sv[j];
      
      float *coef1 = model.sv_coef[j-1], *coef2 = model.sv_coef[i];
      
      for(int k=0;k<ci;k++)
	sum += coef1[si+k] * kvalue[si+k];

      for(int k=0;k<cj;k++)
	sum += coef2[sj+k] * kvalue[sj+k];

      sum -= model.rho[p];
      
      dec_values[p] = sum;
    }
}

//--------------------------------------------------------------------------------
template <typename traits> template <typename InIter>
float svm<traits>::predict(const svm_model& model, InIter x)
{
  int n_class = model.n_class(), n_dims = model.n_dims();

  if (dec_values_ == NULL) {

    dec_values_ = new float [n_class*(n_class-1)/2];

#ifdef NTA_PLATFORM_win32
    x_tmp_ = (float*) _aligned_malloc(4*n_dims, 16);
#else
    x_tmp_ = new float [n_dims];
#endif

  }

  std::copy(x, x + n_dims, x_tmp_);

  predict_values(model, x_tmp_, dec_values_);

  std::vector<int> vote(n_class, 0);
  
  int pos=0;
  for(int i=0;i<n_class;i++)
    for(int j=i+1;j<n_class;j++)
      {
	if(dec_values_[pos++] > 0)
	  ++vote[i];
	else
	  ++vote[j];
      }
  
  int vote_max_idx = 0;
  for(int i=1;i<n_class;i++)
    if(vote[i] > vote[vote_max_idx])
      vote_max_idx = i;
  
  return (float) model.label[vote_max_idx];
}

//--------------------------------------------------------------------------------
// model is the same between predict and predict_probability
// predict_values comes out the same in predict and predict_probability
template <typename traits> template <typename InIter, typename OutIter>
float svm<traits>::predict_probability(const svm_model& model, InIter x, OutIter proba)
{
  int n_class = model.n_class(), n_dims = model.n_dims();

  if (dec_values_ == NULL) {
    dec_values_ = new float [n_class*(n_class-1)/2];

#ifdef NTA_PLATFORM_win32
    x_tmp_ = (float*) _aligned_malloc(4*n_dims, 16);
#else
    x_tmp_ = new float [n_dims];
#endif

  }

  std::copy(x, x + n_dims, x_tmp_);

  if (param_.probability) {

    predict_values(model, x_tmp_, dec_values_);
    
    float min_prob = float(1e-7);
    Matrix pairwise_proba(n_class, n_class);

    int k = 0;
    for (int i = 0; i < n_class; ++i) {
      pairwise_proba(i,i) = 0;
      for (int j = i+1; j < n_class; ++j, ++k) {
	float v = sigmoid_predict(dec_values_[k], model.probA[k], model.probB[k]);
	pairwise_proba(i,j) = std::min(std::max(v, min_prob), 1-min_prob);
	pairwise_proba(j,i) = 1-pairwise_proba(i,j);
      }
    }

    Vector proba_estimates(n_class);
    multiclass_probability(pairwise_proba, proba_estimates);
    std::copy(proba_estimates.begin(), proba_estimates.end(), proba);

    int prob_max_idx = 0;
    for (int i = 0; i < n_class; ++i)
      if (proba_estimates[i] > proba_estimates[prob_max_idx])
	prob_max_idx = i;
    
    return (float) model.label[prob_max_idx];
    
  } else {
    return predict(model, x);
  }
}

//--------------------------------------------------------------------------------
template <typename traits> 
float svm<traits>::cross_validation(int nr_fold)
{
  int l = problem_->size();
  std::vector<int> fold_start(nr_fold+1), perm(l);

  // stratified cv may not give leave-one-out rate
  // Each class to l folds -> some folds may have zero elements
  if (nr_fold < l) {

    std::vector<int> start, label, count;
    group_classes(*problem_, label, start, count, perm);
    int n_class = (int) label.size();

    // random shuffle and then data grouped by fold using the array perm
    std::vector<int> fold_count(nr_fold), index(l);
      
    for(int i=0;i<l;i++)
      index[i]=perm[i];
    for (int c=0; c<n_class; c++) 
      for(int i=0;i<count[c];i++)
	{
	  int j = i+rng_.getUInt32()%(count[c]-i);
	  std::swap(index[start[c]+j],index[start[c]+i]);
	}
    for(int i=0;i<nr_fold;i++)
      {
	fold_count[i] = 0;
	for (int c=0; c<n_class;c++)
	  fold_count[i]+=(i+1)*count[c]/nr_fold-i*count[c]/nr_fold;
      }
    fold_start[0]=0;
    for (int i=1;i<=nr_fold;i++)
      fold_start[i] = fold_start[i-1]+fold_count[i-1];
    for (int c=0; c<n_class;c++)
      for(int i=0;i<nr_fold;i++)
	{
	  int begin = start[c]+i*count[c]/nr_fold;
	  int end = start[c]+(i+1)*count[c]/nr_fold;
	  for(int j=begin;j<end;j++)
	    {
	      perm[fold_start[i]] = index[j];
	      fold_start[i]++;
	    }
	}
    fold_start[0]=0;
    for (int i=1;i<=nr_fold;i++)
      fold_start[i] = fold_start[i-1]+fold_count[i-1];

  } else {

    for(int i=0;i<l;i++) 
      perm[i]=i;
    for(int i=0;i<l;i++)
      {
	int j = i+rng_.getUInt32()%(l-i);
	std::swap(perm[i],perm[j]);
      }
    for(int i=0;i<=nr_fold;i++)
      fold_start[i]=i*l/nr_fold;
  }

  float success = 0;

  for(int i=0;i<nr_fold;i++) {

    int begin = fold_start[i], end = fold_start[i+1];
    problem_type sub_prob(problem_->n_dims(), false);
    
    if ((end - begin) != l) {

      sub_prob.resize(l-(end-begin));
      
      int k=0;
      for(int j=0;j<begin;j++, ++k)
	sub_prob.set_sample(k, problem_->get_sample(perm[j]));
      
      for(int j=end;j<l;j++, ++k)
	sub_prob.set_sample(k, problem_->get_sample(perm[j]));
      
    } else {

      sub_prob.resize(l);

      // In the case where this only one fold, the sub problem
      // becomes the whole problem
      for (int j = 0; j < l; ++j)
	sub_prob.set_sample(j, problem_->get_sample(perm[j]));
    }
    
    svm_model *sub_model = train(sub_prob, param_);
    float* x_tmp = new float[problem_->n_dims()];

    if (param_.probability) {
      
      std::vector<float> proba_estimates(sub_model->n_class());

      for(int j=begin;j<end;j++) {
	problem_->dense(perm[j], x_tmp);
	float p = predict_probability(*sub_model, x_tmp, proba_estimates.begin());
	if (p == problem_->y_[perm[j]])
	  success += 1.0;
      }
      
    } else {

      for(int j=begin;j<end;j++) {
	problem_->dense(perm[j], x_tmp);
	float p = predict(*sub_model, x_tmp);
	if (p == problem_->y_[perm[j]])
	  success += 1.0;
      }
    }
    
    delete [] x_tmp;
    delete sub_model;
  }		

  return success / float(problem_->size());
}

//--------------------------------------------------------------------------------
template <typename traits>
int svm<traits>::persistent_size() const
{
  int n = 6 + param_.persistent_size();

  if (problem_)
    n += problem_->persistent_size();

  if (model_)
    n += model_->persistent_size();

  return n;
}

//--------------------------------------------------------------------------------
template <typename traits>
void svm<traits>::save(std::ostream& outStream) const
{
  param_.save(outStream);

  if (problem_) {
    outStream << " 1 ";
    problem_->save(outStream);
  } else {
    outStream << " 0 ";
  }

  if (model_) {
    outStream << " 1 ";
    model_->save(outStream);
  } else { 
    outStream << " 0 ";
  }
}

//--------------------------------------------------------------------------------
template <typename traits>
void svm<traits>::load(std::istream& inStream)
{
  param_.load(inStream);

  int problemSaved = 0, modelSaved = 0;

  inStream >> problemSaved;
  
  if (problemSaved == 1) {
    delete problem_;
    problem_ = new problem_type(inStream);
  }

  inStream >> modelSaved;

  if (modelSaved == 1) {
    delete model_;
    model_ = new svm_model;
    model_->load(inStream);
  }

  // Can't assert that, because problem might not get loaded, to save
  // space!
  //NTA_ASSERT(model_->n_dims() == problem_->n_dims());
  
  // Recompute with_sse flag based on possibly new dims of the model
  // just loaded (not the problem, since the problem might not be 
  // loaded to save space, but the model always will).
  with_sse = checkSSE();
}

//--------------------------------------------------------------------------------
#endif /* NTA_SVM_T_HPP */
