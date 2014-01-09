/*
 * ---------------------------------------------------------------------
 * Numenta Platform for Intelligent Computing (NuPIC)
 * Copyright (C) 2014, Numenta, Inc.  Unless you have purchased from
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

#include <cstdio>
#include <sstream>

#include <nta/algorithms/svm.hpp>

namespace nta {
  namespace algorithms {
    namespace svm {
      
      using namespace std;

      //--------------------------------------------------------------------------------
      void svm_parameter::print() const
      {
	std::cout << "kernel = " << kernel << std::endl
		  << "probability = " << probability << std::endl
		  << "gamma = " << gamma << std::endl
		  << "C = " << C << std::endl
		  << "eps = " << eps << std::endl
		  << "cache_size = " << cache_size << std::endl
		  << "shrinking = " << shrinking << std::endl;
      }

      //--------------------------------------------------------------------------------
      int svm_parameter::persistent_size() const
      {
	stringstream b;
	b << kernel << ' '
	  << probability << ' '
	  << gamma << ' '
	  << C << ' '
	  << eps << ' '
	  << cache_size << ' '
	  << shrinking << ' '
		<< weight_label << ' '
		<< weight << ' ';

	return b.str().size();
      }

      //--------------------------------------------------------------------------------
      void svm_parameter::save(std::ostream& outStream) const
      {
	outStream << kernel << ' '
		  << probability << ' '
		  << gamma << ' '
		  << C << ' '
		  << eps << ' '
		  << cache_size << ' '
			<< shrinking << ' '
			<< weight_label << ' '
			<< weight << ' ';
			}

      //--------------------------------------------------------------------------------
      void svm_parameter::load(std::istream& inStream)
      {
	inStream >> kernel
		 >> probability
		 >> gamma
		 >> C
		 >> eps
		 >> cache_size
		 >> shrinking
		 >> weight_label
		 >> weight;
			}

      //--------------------------------------------------------------------------------
      int svm_problem::persistent_size() const
      {
	stringstream b;

	b << size() << " " << n_dims() << " ";

	return b.str().size() 
	  + y_.size() * sizeof(label_type)
	  + size() * n_dims() * sizeof(feature_type) + 1;
      }

      //--------------------------------------------------------------------------------
      void svm_problem::save(std::ostream& outStream) const
      {
	outStream << size() << " " << n_dims() << " ";
  
	nta::binary_save(outStream, y_);

	for (int i = 0; i < size(); ++i)
	  nta::binary_save(outStream, x_[i], x_[i] + n_dims());
	outStream << " ";
      }

      //--------------------------------------------------------------------------------
      void svm_problem::load(std::istream& inStream)
      {
	int s = 0;
	inStream >> s >> n_dims_;
  
	if (recover_)
	  for (size_t i = 0; i != x_.size(); ++i)
	    delete [] x_[i];

	y_.resize(s, 0);
	x_.resize(s, 0);

	inStream.ignore(1);
	nta::binary_load(inStream, y_);
	
	for (int i = 0; i < size(); ++i) {

#ifdef NTA_PLATFORM_win32
          x_[i] = (float*) _aligned_malloc(4*n_dims(), 16);
#else
	  x_[i] = new feature_type[n_dims()];
#endif

          std::fill(x_[i], x_[i] + n_dims(), (float) 0);
	  nta::binary_load(inStream, x_[i], x_[i] + n_dims());
	}
      }

      //--------------------------------------------------------------------------------
      int svm_problem01::persistent_size() const
      {
	stringstream b;
	b  << size() << " " << n_dims() << " " << threshold_ << " ";
	int n = b.str().size();

	n += y_.size() * sizeof(float);
	n += nnz_.size() * sizeof(int);

	for (int i = 0; i != size(); ++i)
	  n += nnz_[i] * sizeof(feature_type);

	return n + 1;
      }

      //--------------------------------------------------------------------------------
      void svm_problem01::save(std::ostream& outStream) const
      {
	outStream << size() << " " << n_dims() << " " << threshold_ << " ";
  
	nta::binary_save(outStream, y_);
	nta::binary_save(outStream, nnz_);
	
	for (int i = 0; i < size(); ++i) 
	  nta::binary_save(outStream, x_[i], x_[i] + nnz_[i]);
	outStream << " ";
      }

      //--------------------------------------------------------------------------------
      void svm_problem01::load(std::istream& inStream)
      {
	int s = 0;
	inStream >> s >> n_dims_ >> threshold_;
  
	if (recover_)
	  for (size_t i = 0; i < x_.size(); ++i)
	    delete [] x_[i];

	y_.resize(s, 0);
	nnz_.resize(s, 0);  
	x_.resize(s, 0);
	
	inStream.ignore(1);
	nta::binary_load(inStream, y_);
	nta::binary_load(inStream, nnz_);

	for (int i = 0; i < s; ++i) {
	  x_[i] = new feature_type[nnz_[i]];
	  nta::binary_load(inStream, x_[i], x_[i] + nnz_[i]);
	}
      }

      //--------------------------------------------------------------------------------
      svm_model::~svm_model()
      {
	// in all cases, ownership of the mem for the sv is with svm_model

        if (sv_mem == NULL) {
          for (size_t i = 0; i != sv.size(); ++i)

#ifdef NTA_PLATFORM_win32
            _aligned_free(sv[i]);
#else
            delete [] sv[i];
#endif

        } else {

#ifdef NTA_PLATFORM_win32
          _aligned_free(sv_mem);
#else
          delete [] sv_mem;
#endif

          sv_mem = NULL;
          sv.clear();
        }
          
	for (size_t i = 0; i != sv_coef.size(); ++i)
	  delete [] sv_coef[i];
      }

      //--------------------------------------------------------------------------------
      void svm_model::print() const
      {
	std::cout << "n classes = " << n_class()
		  << " n sv = " << size()
		  << " n dims = " << n_dims()
		  << std::endl;
	  
	std::cout << "Support vectors: " << std::endl;
	for (size_t i = 0; i != sv.size(); ++i) {
	  for (int j = 0; j != n_dims(); ++j)
	    std::cout << sv[i][j] << " ";
	  std::cout << std::endl;
	}
	  
	std::cout << "Support vector coefficients: " << std::endl;
	for (size_t i = 0; i != sv_coef.size(); ++i) {
	  for (int j = 0; j != size(); ++j)
	    std::cout << sv_coef[i][j] << " ";
	  std::cout << std::endl;
	}

	std::cout << "Rho: " << std::endl;
	for (size_t i = 0; i != rho.size(); ++i) 
	  std::cout << rho[i] << " ";
	std::cout << std::endl;
	  
	if (! probA.empty()) {
	  
	  std::cout << "Probabilities A: " << std::endl;
	  for (size_t i = 0; i != probA.size(); ++i)
	    std::cout << probA[i] << " ";
	  std::cout << std::endl;
	  
	  std::cout << "Probabilities B: " << std::endl;
	  for (size_t i = 0; i != probB.size(); ++i)
	    std::cout << probB[i] << " ";
	  std::cout << std::endl;
	}
      }

      //--------------------------------------------------------------------------------
      int svm_model::persistent_size() const
      {
	stringstream b;
	b << n_class() << " "
	  << size() << " " 
	  << n_dims() << " ";
	
	int n = b.str().size();
	
	n += sv.size() * n_dims() * sizeof(float) + 1;
	
	{
	  stringstream b2;
	  for (size_t i = 0; i < sv_coef.size(); ++i) {
	    for (int j = 0; j < size(); ++j) 
	      b2 << sv_coef[i][j] << " ";
	  }
	  n += b2.str().size();
	}

	{ 
	  stringstream b2;
          b2 << rho << " ";
	  n += b2.str().size();
	}

	{ 
	  stringstream b2;
          b2 << label << " ";
	  n += b2.str().size();
	}

	{ 
	  stringstream b2;
          b2 << n_sv << " ";
	  n += b2.str().size();
	}

	{ 
	  stringstream b2;
          b2 << probA << " ";
	  n += b2.str().size();
	}

	{ 
	  stringstream b2;
          b2 << probB << " ";
	  n += b2.str().size();
	}

	{ 
	  stringstream b2;
          b2 << w << " ";
	  n += b2.str().size();
	}

	return n;
      }

      //--------------------------------------------------------------------------------
      void svm_model::save(std::ostream& outStream) const
      {
	outStream << n_class() << " "
		  << size() << " " 
		  << n_dims() << " ";
  
	for (size_t i = 0; i < sv.size(); ++i) 
	  nta::binary_save(outStream, sv[i], sv[i] + n_dims());
	outStream << " ";
  
	for (size_t i = 0; i < sv_coef.size(); ++i) 
	  for (int j = 0; j < size(); ++j) 
	    outStream << sv_coef[i][j] << " ";
  
        outStream << rho << ' '
                  << label << ' '
                  << n_sv << ' '
                  << probA << ' '
                  << probB << ' '
                  << w << ' ';
      }

      //--------------------------------------------------------------------------------
      void svm_model::load(std::istream& inStream)
      {
	int n_class = 0, l = 0;
	inStream >> n_class >> l >> n_dims_; 

        if (sv_mem == NULL) {

          for (size_t i = 0; i < sv.size(); ++i)
            delete [] sv[i];

        } else {

          delete [] sv_mem;
          sv_mem = NULL;
        }

#ifdef NTA_PLATFORM_win32
        sv_mem = (float*) _aligned_malloc(4 * l * n_dims(), 16);
#else
        sv_mem = new float [l * n_dims()];
#endif

        std::fill(sv_mem, sv_mem + l * n_dims(), (float)0);

	sv.resize(l, 0);
	inStream.ignore(1);
	for (int i = 0; i < l; ++i) {
	  sv[i] = sv_mem + i * n_dims();
	  nta::binary_load(inStream, sv[i], sv[i] + n_dims());
	}

	for (size_t i = 0; i < sv_coef.size(); ++i)
	  delete [] sv_coef[i];
  
	sv_coef.resize(n_class-1, 0);
	for (int i = 0; i < n_class-1; ++i) {
	  sv_coef[i] = new float [l];
	  for (int j = 0; j < l; ++j) 
	    inStream >> sv_coef[i][j];
	} 
  
        inStream >> rho
                 >> label
                 >> n_sv
                 >> probA
                 >> probB
                 >> w;
      }

      //--------------------------------------------------------------------------------
    }
  }
}
