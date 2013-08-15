
// basic doc for primitive types....

#ifdef SWIG_DOC_DOXYGEN_STYLE
%typemap(doc) SWIGTYPE "@param $1_name $1_type value";
%typemap(doc) SWIGTYPE* "@param $1_name $1_type value";
%typemap(doc) const SWIGTYPE& "@param $1_name $1_type value";
%typemap(doc) enum SWIGTYPE "@param $1_name enum $1_type value";
#else
%typemap(doc) SWIGTYPE "$1_name: $1_type value";
%typemap(doc) SWIGTYPE* "$1_name: $1_type value";
%typemap(doc) const SWIGTYPE& "$1_name: $1_type value";
%typemap(doc) enum SWIGTYPE "$1_name: enum $1_type value";

%typemap(doc) SWIGTYPE *INOUT "$1_name: $1_type input/ouput value";
%typemap(doc) SWIGTYPE *INPUT "$1_name: $1_type input value";
%typemap(doc) SWIGTYPE *OUTPUT "$1_name: $1_type output value";
#endif
