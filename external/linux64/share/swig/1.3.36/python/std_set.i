/*
  Sets
*/

%fragment("StdSetTraits","header",fragment="StdSequenceTraits")
%{
  namespace swig {
    template <class PySeq, class T> 
    inline void 
    assign(const PySeq& pyseq, std::set<T>* seq) {
      // seq->insert(pyseq.begin(), pyseq.end()); // not used as not always implemented
      typedef typename PySeq::value_type value_type;
      typename PySeq::const_iterator it = pyseq.begin();
      for (;it != pyseq.end(); ++it) {
	seq->insert(seq->end(),(value_type)(*it));
      }
    }

    template <class T>
    struct traits_asptr<std::set<T> >  {
      static int asptr(PyObject *obj, std::set<T> **s) {
	return traits_asptr_stdseq<std::set<T> >::asptr(obj, s);
      }
    };

    template <class T>
    struct traits_from<std::set<T> > {
      static PyObject *from(const std::set<T>& vec) {
	return traits_from_stdseq<std::set<T> >::from(vec);
      }
    };
  }
%}

%define %swig_set_methods(set...)
  %swig_sequence_iterator(set);
  %swig_container_methods(set);

  %extend  {
     void append(value_type x) {
       self->insert(x);
     }
  
     bool __contains__(value_type x) {
       return self->find(x) != self->end();
     }

     value_type __getitem__(difference_type i) const throw (std::out_of_range) {
       return *(swig::cgetpos(self, i));
     }

  };
%enddef

%include <std/std_set.i>
