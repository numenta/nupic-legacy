/* inout_typemaps.i

   Support for INPUT, OUTPUT, and INOUT typemaps. OUTPUT variables are returned
   as multiple values.

*/


/* Note that this macro automatically adds a pointer to the type passed in.
   As a result, INOUT typemaps for char are for 'char *'. The definition
   of typemaps for 'char' takes advantage of this, believing that it's more
   likely to see an INOUT argument for strings, than a single char. */
%define INOUT_TYPEMAP(type_, OUTresult_, INbind_)
// OUTPUT map.
%typemap(lin,numinputs=0) type_ *OUTPUT, type_ &OUTPUT
%{(cl::let (($out (ff:allocate-fobject '$*in_fftype :c)))
     $body
     OUTresult_
     (ff:free-fobject $out)) %}

// INPUT map.
%typemap(in) type_ *INPUT, type_ &INPUT
%{ $1 = &$input; %}

%typemap(ctype) type_ *INPUT, type_ &INPUT "$*1_ltype";


// INOUT map.
// careful here. the input string is converted to a C string
// with length equal to the input string. This should be large
// enough to contain whatever OUTPUT value will be stored in it.
%typemap(lin,numinputs=1) type_ *INOUT, type_ &INOUT
%{(cl::let (($out (ff:allocate-fobject '$*in_fftype :c)))
     INbind_
     $body
     OUTresult_
     (ff:free-fobject $out)) %}

%enddef

// $in, $out, $lclass,
// $in_fftype, $*in_fftype

INOUT_TYPEMAP(int,
	      (cl::push (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) ACL_result),
	      (cl::setf (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) $in));
INOUT_TYPEMAP(short,
	      (cl::push (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) ACL_result),
	      (cl::setf (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) $in));
INOUT_TYPEMAP(long,
	      (cl::push (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) ACL_result),
	      (cl::setf (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) $in));
INOUT_TYPEMAP(unsigned int,
	      (cl::push (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) ACL_result),
	      (cl::setf (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) $in));
INOUT_TYPEMAP(unsigned short,
	      (cl::push (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) ACL_result),
	      (cl::setf (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) $in));
INOUT_TYPEMAP(unsigned long,
	      (cl::push (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) ACL_result),
	      (cl::setf (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) $in));
// char * mapping for passing strings. didn't quite work
// INOUT_TYPEMAP(char,
//              (cl::push (excl:native-to-string $out) ACL_result),
//	      (cl::setf (ff:fslot-value-typed (cl::quote $in_fftype) :c $out)
//		    (excl:string-to-native $in)))
INOUT_TYPEMAP(float,
	      (cl::push (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) ACL_result),
	      (cl::setf (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) $in));
INOUT_TYPEMAP(double,
	      (cl::push (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) ACL_result),
	      (cl::setf (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) $in));
INOUT_TYPEMAP(bool,
	      (cl::push (not (zerop (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out)))
		    ACL_result),
	      (cl::setf (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) (if $in 1 0)));

%typemap(lisptype) bool *INPUT, bool &INPUT "boolean";

// long long support not yet complete
// INOUT_TYPEMAP(long long);
// INOUT_TYPEMAP(unsigned long long);

// char *OUTPUT map.
// for this to work, swig needs to know how large an array to allocate.
// you can fake this by 
// %typemap(ffitype) char *myarg	"(:array :char 30)";
// %apply char *OUTPUT { char *myarg };
%typemap(lin,numinputs=0) char *OUTPUT, char &OUTPUT
%{(cl::let (($out (ff:allocate-fobject '$*in_fftype :c)))
     $body
     (cl::push (excl:native-to-string $out) ACL_result)
     (ff:free-fobject $out)) %}

// char *INPUT map.
%typemap(in) char *INPUT, char &INPUT
%{ $1 = &$input; %}
%typemap(ctype) char *INPUT, char &INPUT "$*1_ltype";

// char *INOUT map.
%typemap(lin,numinputs=1) char *INOUT, char &INOUT
%{(cl::let (($out (excl:string-to-native $in)))
     $body
     (cl::push (excl:native-to-string $out) ACL_result)
     (ff:free-fobject $out)) %}

// uncomment this if you want INOUT mappings for chars instead of strings.
// INOUT_TYPEMAP(char,
// 	      (cl::push (code-char (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out))
//		    ACL_result),
//	      (cl::setf (ff:fslot-value-typed (cl::quote $*in_fftype) :c $out) $in));
