/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * _std_deque.i
 *
 * This file contains a generic definition of std::deque along with
 * some helper functions.  Specific language modules should include
 * this file to generate wrappers. 
 * ----------------------------------------------------------------------------- */

%include <std_except.i>

%{
#include <deque>
#include <stdexcept>
%}


/* This macro defines all of the standard methods for a deque.  This
   is defined as a macro to simplify the task of specialization.  For
   example,

         template<> class deque<int> {
         public:
             %std_deque_methods(int);
         };
*/

%define %std_deque_methods(T)
       typedef T &reference;
       typedef const T& const_reference;

       deque();
       deque(unsigned int size, const T& value=T());
       deque(const deque<T> &);
      ~deque();

       void assign(unsigned int n, const T& value);
       void swap(deque<T> &x);
       unsigned int size() const;
       unsigned int max_size() const;
       void resize(unsigned int n, T c = T());
       bool empty() const;
       const_reference front();
       const_reference back();
       void push_front(const T& x);
       void push_back(const T& x);
       void pop_front();
       void pop_back();
       void clear();

       /* Some useful extensions */
       %extend {
           const_reference getitem(int i) throw (std::out_of_range) {
                int size = int(self->size());
                if (i<0) i += size;
                if (i>=0 && i<size)
                    return (*self)[i];
                else
                    throw std::out_of_range("deque index out of range");
           }
           void setitem(int i, const T& x) throw (std::out_of_range) {
                int size = int(self->size());
                if (i<0) i+= size;
                if (i>=0 && i<size)
                    (*self)[i] = x;
                else
                    throw std::out_of_range("deque index out of range");
           }
           void delitem(int i) throw (std::out_of_range) {
            	int size = int(self->size());
                if (i<0) i+= size;
                if (i>=0 && i<size) {
                    self->erase(self->begin()+i);
                } else {
                    throw std::out_of_range("deque index out of range");
                }
           }
	   std::deque<T> getslice(int i, int j) {
                int size = int(self->size());
                if (i<0) i = size+i;
                if (j<0) j = size+j;
                if (i<0) i = 0;
                if (j>size) j = size;
                std::deque<T > tmp(j-i);
                std::copy(self->begin()+i,self->begin()+j,tmp.begin());
                return tmp;
            }
            void setslice(int i, int j, const std::deque<T>& v) {
                int size = int(self->size());
                if (i<0) i = size+i;
                if (j<0) j = size+j;
                if (i<0) i = 0;
                if (j>size) j = size;
                if (int(v.size()) == j-i) {
                    std::copy(v.begin(),v.end(),self->begin()+i);
                } else {
                    self->erase(self->begin()+i,self->begin()+j);
                    if (i+1 <= size)
                        self->insert(self->begin()+i+1,v.begin(),v.end());
                    else
                        self->insert(self->end(),v.begin(),v.end());
                }
            }
            void delslice(int i, int j) {
                int size = int(self->size());
                if (i<0) i = size+i;
                if (j<0) j = size+j;
                if (i<0) i = 0;
                if (j>size) j = size;
                self->erase(self->begin()+i,self->begin()+j);
            }
       };

%enddef

namespace std {
    template<class T> class deque {
    public:
       %std_deque_methods(T);
    };
}



