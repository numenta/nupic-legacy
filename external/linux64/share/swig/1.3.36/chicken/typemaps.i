/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * typemaps.i
 *
 * Pointer handling
 *
 * These mappings provide support for input/output arguments and
 * common uses for C/C++ pointers.  INOUT mappings allow for C/C++
 * pointer variables in addition to input/output arguments.
 * ----------------------------------------------------------------------------- */

// INPUT typemaps.
// These remap a C pointer to be an "INPUT" value which is passed by value
// instead of reference.

/* 
The following methods can be applied to turn a pointer into a simple
"input" value.  That is, instead of passing a pointer to an object,
you would use a real value instead.

         int            *INPUT
         short          *INPUT
         long           *INPUT
	 long long      *INPUT
         unsigned int   *INPUT
         unsigned short *INPUT
         unsigned long  *INPUT
         unsigned long long *INPUT
         unsigned char  *INPUT
         char           *INPUT
         bool           *INPUT
         float          *INPUT
         double         *INPUT
         
To use these, suppose you had a C function like this :

        double fadd(double *a, double *b) {
               return *a+*b;
        }

You could wrap it with SWIG as follows :
        
        %include <typemaps.i>
        double fadd(double *INPUT, double *INPUT);

or you can use the %apply directive :

        %include <typemaps.i>
        %apply double *INPUT { double *a, double *b };
        double fadd(double *a, double *b);

*/

// OUTPUT typemaps.   These typemaps are used for parameters that
// are output only.   The output value is appended to the result as
// a list element.

/* 
The following methods can be applied to turn a pointer into an "output"
value.  When calling a function, no input value would be given for
a parameter, but an output value would be returned.  In the case of
multiple output values, they are returned in the form of a Scheme list.

         int            *OUTPUT
         short          *OUTPUT
         long           *OUTPUT
         long long      *OUTPUT
         unsigned int   *OUTPUT
         unsigned short *OUTPUT
         unsigned long  *OUTPUT
         unsigned long long *OUTPUT
         unsigned char  *OUTPUT
         char           *OUTPUT
         bool           *OUTPUT
         float          *OUTPUT
         double         *OUTPUT
         
For example, suppose you were trying to wrap the modf() function in the
C math library which splits x into integral and fractional parts (and
returns the integer part in one of its parameters).K:

        double modf(double x, double *ip);

You could wrap it with SWIG as follows :

        %include <typemaps.i>
        double modf(double x, double *OUTPUT);

or you can use the %apply directive :

        %include <typemaps.i>
        %apply double *OUTPUT { double *ip };
        double modf(double x, double *ip);

*/

// These typemaps contributed by Robin Dunn
//----------------------------------------------------------------------
//
// T_OUTPUT typemap (and helper function) to return multiple argouts as
// a tuple instead of a list.
//
//----------------------------------------------------------------------

// Simple types

%define INOUT_TYPEMAP(type_, from_scheme, to_scheme, checker, convtype, storage_)

%typemap(in) type_ *INPUT($*1_ltype temp), type_ &INPUT($*1_ltype temp)
%{  if (!checker ($input)) {
    swig_barf (SWIG_BARF1_BAD_ARGUMENT_TYPE, "Argument #$argnum is not of type 'type_'");
  }
  temp = ($*1_ltype) from_scheme ($input);
  $1 = &temp; %}

%typemap(typecheck) type_ *INPUT = type_;
%typemap(typecheck) type_ &INPUT = type_;

%typemap(in, numinputs=0) type_ *OUTPUT($*1_ltype temp), type_ &OUTPUT($*1_ltype temp)
"  $1 = &temp;"

#if "storage_" == "0"

%typemap(argout) type_ *OUTPUT, type_ &OUTPUT 
%{ 
  if ($1 == NULL) {
    swig_barf (SWIG_BARF1_ARGUMENT_NULL, "Argument #$argnum must be non-null");
  }
  SWIG_APPEND_VALUE(to_scheme (convtype (*$1)));
%}

#else

%typemap(argout) type_ *OUTPUT, type_ &OUTPUT 
%{
  {
    C_word *known_space = C_alloc(storage_);
    if ($1 == NULL) {
      swig_barf (SWIG_BARF1_ARGUMENT_NULL, "Variable '$1' must be non-null");
    }
    SWIG_APPEND_VALUE(to_scheme (&known_space, convtype (*$1)));
  }
%}

#endif

%enddef

INOUT_TYPEMAP(int, C_num_to_int, C_fix, C_swig_is_number, (int), 0);
INOUT_TYPEMAP(enum SWIGTYPE, C_num_to_int, C_fix, C_swig_is_number, (int), 0);
INOUT_TYPEMAP(short, C_num_to_int, C_fix, C_swig_is_number, (int), 0);
INOUT_TYPEMAP(long, C_num_to_long, C_long_to_num, C_swig_is_long, (long), C_SIZEOF_FLONUM);
INOUT_TYPEMAP(long long, C_num_to_long, C_long_to_num, C_swig_is_long, (long), C_SIZEOF_FLONUM);
INOUT_TYPEMAP(unsigned int, C_num_to_unsigned_int, C_unsigned_int_to_num, C_swig_is_number, (int), C_SIZEOF_FLONUM);
INOUT_TYPEMAP(unsigned short, C_num_to_unsigned_int, C_fix, C_swig_is_number, (unsigned int), 0);
INOUT_TYPEMAP(unsigned long, C_num_to_unsigned_long, C_unsigned_long_to_num, C_swig_is_long, (unsigned long), C_SIZEOF_FLONUM);
INOUT_TYPEMAP(unsigned long long, C_num_to_unsigned_long, C_unsigned_long_to_num, C_swig_is_long, (unsigned long), C_SIZEOF_FLONUM);
INOUT_TYPEMAP(unsigned char, C_character_code, C_make_character, C_swig_is_char, (unsigned int), 0);
INOUT_TYPEMAP(signed char, C_character_code, C_make_character, C_swig_is_char, (int), 0);
INOUT_TYPEMAP(char, C_character_code, C_make_character, C_swig_is_char, (char), 0);
INOUT_TYPEMAP(bool, C_truep, C_mk_bool, C_swig_is_bool, (bool), 0);
INOUT_TYPEMAP(float, C_c_double, C_flonum, C_swig_is_number, (double), C_SIZEOF_FLONUM);
INOUT_TYPEMAP(double, C_c_double, C_flonum, C_swig_is_number, (double), C_SIZEOF_FLONUM);

// INOUT
// Mappings for an argument that is both an input and output
// parameter

/*
The following methods can be applied to make a function parameter both
an input and output value.  This combines the behavior of both the
"INPUT" and "OUTPUT" methods described earlier.  Output values are
returned in the form of a CHICKEN tuple.  

         int            *INOUT
         short          *INOUT
         long           *INOUT
         long long      *INOUT
         unsigned int   *INOUT
         unsigned short *INOUT
         unsigned long  *INOUT
         unsigned long long *INOUT
         unsigned char  *INOUT
         char           *INOUT
         bool           *INOUT
         float          *INOUT
         double         *INOUT
         
For example, suppose you were trying to wrap the following function :

        void neg(double *x) {
             *x = -(*x);
        }

You could wrap it with SWIG as follows :

        %include <typemaps.i>
        void neg(double *INOUT);

or you can use the %apply directive :

        %include <typemaps.i>
        %apply double *INOUT { double *x };
        void neg(double *x);

As well, you can wrap variables with :

        %include <typemaps.i>
        %apply double *INOUT { double *y };
        extern double *y;

Unlike C, this mapping does not directly modify the input value (since
this makes no sense in CHICKEN).  Rather, the modified input value shows
up as the return value of the function.  Thus, to apply this function
to a CHICKEN variable you might do this :

       x = neg(x)

Note : previous versions of SWIG used the symbol 'BOTH' to mark
input/output arguments.   This is still supported, but will be slowly
phased out in future releases.

*/

%typemap(in) int *INOUT = int *INPUT;
%typemap(in) enum SWIGTYPE *INOUT = enum SWIGTYPE *INPUT;
%typemap(in) short *INOUT = short *INPUT;
%typemap(in) long *INOUT = long *INPUT;
%typemap(in) long long *INOUT = long long *INPUT;
%typemap(in) unsigned *INOUT = unsigned *INPUT;
%typemap(in) unsigned short *INOUT = unsigned short *INPUT;
%typemap(in) unsigned long *INOUT = unsigned long *INPUT;
%typemap(in) unsigned long long *INOUT = unsigned long long *INPUT;
%typemap(in) unsigned char *INOUT = unsigned char *INPUT;
%typemap(in) char *INOUT = char *INPUT;
%typemap(in) bool *INOUT = bool *INPUT;
%typemap(in) float *INOUT = float *INPUT;
%typemap(in) double *INOUT = double *INPUT;

%typemap(in) int &INOUT = int &INPUT;
%typemap(in) enum SWIGTYPE &INOUT = enum SWIGTYPE &INPUT;
%typemap(in) short &INOUT = short &INPUT;
%typemap(in) long &INOUT = long &INPUT;
%typemap(in) long long &INOUT = long long &INPUT;
%typemap(in) unsigned &INOUT = unsigned &INPUT;
%typemap(in) unsigned short &INOUT = unsigned short &INPUT;
%typemap(in) unsigned long &INOUT = unsigned long &INPUT;
%typemap(in) unsigned long long &INOUT = unsigned long long &INPUT;
%typemap(in) unsigned char &INOUT = unsigned char &INPUT;
%typemap(in) char &INOUT = char &INPUT;
%typemap(in) bool &INOUT = bool &INPUT;
%typemap(in) float &INOUT = float &INPUT;
%typemap(in) double &INOUT = double &INPUT;

%typemap(argout) int *INOUT = int *OUTPUT;
%typemap(argout) enum SWIGTYPE *INOUT = enum SWIGTYPE *OUTPUT;
%typemap(argout) short *INOUT = short *OUTPUT;
%typemap(argout) long *INOUT = long *OUTPUT;
%typemap(argout) long long *INOUT = long long *OUTPUT;
%typemap(argout) unsigned *INOUT = unsigned *OUTPUT;
%typemap(argout) unsigned short *INOUT = unsigned short *OUTPUT;
%typemap(argout) unsigned long *INOUT = unsigned long *OUTPUT;
%typemap(argout) unsigned long long *INOUT = unsigned long long *OUTPUT;
%typemap(argout) unsigned char *INOUT = unsigned char *OUTPUT;
%typemap(argout) bool *INOUT = bool *OUTPUT;
%typemap(argout) float *INOUT = float *OUTPUT;
%typemap(argout) double *INOUT = double *OUTPUT;

%typemap(argout) int &INOUT = int &OUTPUT;
%typemap(argout) enum SWIGTYPE &INOUT = enum SWIGTYPE &OUTPUT;
%typemap(argout) short &INOUT = short &OUTPUT;
%typemap(argout) long &INOUT = long &OUTPUT;
%typemap(argout) long long &INOUT = long long &OUTPUT;
%typemap(argout) unsigned &INOUT = unsigned &OUTPUT;
%typemap(argout) unsigned short &INOUT = unsigned short &OUTPUT;
%typemap(argout) unsigned long &INOUT = unsigned long &OUTPUT;
%typemap(argout) unsigned long long &INOUT = unsigned long long &OUTPUT;
%typemap(argout) unsigned char &INOUT = unsigned char &OUTPUT;
%typemap(argout) char &INOUT = char &OUTPUT;
%typemap(argout) bool &INOUT = bool &OUTPUT;
%typemap(argout) float &INOUT = float &OUTPUT;
%typemap(argout) double &INOUT = double &OUTPUT;

/* Overloading information */

%typemap(typecheck) double *INOUT = double;
%typemap(typecheck) bool *INOUT = bool;
%typemap(typecheck) char *INOUT = char;
%typemap(typecheck) signed char *INOUT = signed char;
%typemap(typecheck) unsigned char *INOUT = unsigned char;
%typemap(typecheck) unsigned long *INOUT = unsigned long;
%typemap(typecheck) unsigned long long *INOUT = unsigned long long;
%typemap(typecheck) unsigned short *INOUT = unsigned short;
%typemap(typecheck) unsigned int *INOUT = unsigned int;
%typemap(typecheck) long *INOUT = long;
%typemap(typecheck) long long *INOUT = long long;
%typemap(typecheck) short *INOUT = short;
%typemap(typecheck) int *INOUT = int;
%typemap(typecheck) enum SWIGTYPE *INOUT = enum SWIGTYPE;
%typemap(typecheck) float *INOUT = float;

%typemap(typecheck) double &INOUT = double;
%typemap(typecheck) bool &INOUT = bool;
%typemap(typecheck) char &INOUT = char;
%typemap(typecheck) signed char &INOUT = signed char;
%typemap(typecheck) unsigned char &INOUT = unsigned char;
%typemap(typecheck) unsigned long &INOUT = unsigned long;
%typemap(typecheck) unsigned long long &INOUT = unsigned long long;
%typemap(typecheck) unsigned short &INOUT = unsigned short;
%typemap(typecheck) unsigned int &INOUT = unsigned int;
%typemap(typecheck) long &INOUT = long;
%typemap(typecheck) long long &INOUT = long long;
%typemap(typecheck) short &INOUT = short;
%typemap(typecheck) int &INOUT = int;
%typemap(typecheck) enum SWIGTYPE &INOUT = enum SWIGTYPE;
%typemap(typecheck) float &INOUT = float;
