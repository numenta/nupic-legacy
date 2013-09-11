%warnfilter(SWIGWARN_PARSE_KEYWORD) java::lang::ref;

%{
#undef STATIC
%}
%include <gcj/cni.i>
%{
#undef TRUE
#define TRUE 1
%}

%include <jstring.i>
