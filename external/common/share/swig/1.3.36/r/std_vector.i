%fragment("StdVectorTraits","header")
%{
%}

#define %swig_vector_methods(Type...) %swig_sequence_methods(Type)
#define %swig_vector_methods_val(Type...) %swig_sequence_methods_val(Type);



%include <std/std_vector.i>