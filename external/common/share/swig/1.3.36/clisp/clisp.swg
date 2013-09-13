/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * clisp.swg
 * ----------------------------------------------------------------------------- */

/* Define a C preprocessor symbol that can be used in interface files
   to distinguish between the SWIG language modules. */ 

#define SWIG_CLISP

/* Typespecs for basic types. */

%typemap(in) void "NIL";

%typemap(in) char "character";
%typemap(in) char * "ffi:c-string";
%typemap(in) unsigned char "ffi:uchar";
%typemap(in) signed char "ffi:char";

%typemap(in) short "ffi:short";
%typemap(in) signed short "ffi:short";
%typemap(in) unsigned short "ffi:ushort";

%typemap(in) int "ffi:int";
%typemap(in) signed int "ffi:int";
%typemap(in) unsigned int "ffi:uint";

%typemap(in) long "ffi:long";
%typemap(in) signed long "ffi:long";
%typemap(in) unsigned long "ffi:ulong";

%typemap(in) float "SINGLE-FLOAT";
%typemap(in) double "DOUBLE-FLOAT";
