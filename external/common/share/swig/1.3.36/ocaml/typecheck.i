/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * typecheck.i
 *
 * Typechecking rules
 * ----------------------------------------------------------------------------- */

%typecheck(SWIG_TYPECHECK_INTEGER) char, signed char, const char &, const signed char & {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_char: $1 = 1; break;
      default: $1 = 0; break;
      }
  }
}

%typecheck(SWIG_TYPECHECK_INTEGER) unsigned char, const unsigned char & {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_uchar: $1 = 1; break;
      default: $1 = 0; break;
      }
  }
}

%typecheck(SWIG_TYPECHECK_INTEGER) short, signed short, const short &, const signed short &, wchar_t {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_short: $1 = 1; break;
      default: $1 = 0; break;
      }
  }
}

%typecheck(SWIG_TYPECHECK_INTEGER) unsigned short, const unsigned short & {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_ushort: $1 = 1; break;
      default: $1 = 0; break;
      }
  }
}

// XXX arty 
// Will move enum SWIGTYPE later when I figure out what to do with it...

%typecheck(SWIG_TYPECHECK_INTEGER) int, signed int, const int &, const signed int &, enum SWIGTYPE {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_int: $1 = 1; break;
      default: $1 = 0; break;
      }
  }
}

%typecheck(SWIG_TYPECHECK_INTEGER) unsigned int, const unsigned int & {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_uint: $1 = 1; break;
      case C_int32: $1 = 1; break;
      default: $1 = 0; break;
      }
  }
}

%typecheck(SWIG_TYPECHECK_INTEGER) long, signed long, unsigned long, long long, signed long long, unsigned long long, const long &, const signed long &, const unsigned long &, const long long &, const signed long long &, const unsigned long long & {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_int64: $1 = 1; break;
      default: $1 = 0; break;
      }
  }
}

%typecheck(SWIG_TYPECHECK_INTEGER) bool, oc_bool, BOOL, const bool &, const oc_bool &, const BOOL & {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_bool: $1 = 1; break;
      default: $1 = 0; break;
      }
  }
}

%typecheck(SWIG_TYPECHECK_DOUBLE) float, const float & {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_float: $1 = 1; break;
      default: $1 = 0; break;
      }
  }  
}

%typecheck(SWIG_TYPECHECK_DOUBLE) double, const double & {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_double: $1 = 1; break;
      default: $1 = 0; break;
      }
  }  
}

%typecheck(SWIG_TYPECHECK_STRING) char * {
  if( !Is_block($input) ) $1 = 0;
  else {
      switch( SWIG_Tag_val($input) ) {
      case C_string: $1 = 1; break;
      case C_ptr: {
	swig_type_info *typeinfo = 
	    (swig_type_info *)(long)SWIG_Int64_val(SWIG_Field($input,1));
	$1 = SWIG_TypeCheck("char *",typeinfo) ||
	     SWIG_TypeCheck("signed char *",typeinfo) ||
	     SWIG_TypeCheck("unsigned char *",typeinfo) ||
	     SWIG_TypeCheck("const char *",typeinfo) ||
	     SWIG_TypeCheck("const signed char *",typeinfo) ||
	     SWIG_TypeCheck("const unsigned char *",typeinfo) ||
	     SWIG_TypeCheck("std::string",typeinfo);
      } break;
      default: $1 = 0; break;
      }
  }    
}

%typecheck(SWIG_TYPECHECK_POINTER) SWIGTYPE *, SWIGTYPE &, SWIGTYPE [] {
  void *ptr;
  $1 = !caml_ptr_val_internal($input, &ptr,$descriptor);
}

#if 0

%typecheck(SWIG_TYPECHECK_POINTER) SWIGTYPE {
  void *ptr;
  $1 = !caml_ptr_val_internal($input, &ptr, $&1_descriptor);
}

#endif

%typecheck(SWIG_TYPECHECK_VOIDPTR) void * {
  void *ptr;
  $1 = !caml_ptr_val_internal($input, &ptr, 0);
}

/* ------------------------------------------------------------
 * Exception handling
 * ------------------------------------------------------------ */

%typemap(throws) int, 
                  long, 
                  short, 
                  unsigned int, 
                  unsigned long, 
                  unsigned short {
  SWIG_exception($1,"Thrown exception from C++ (int)");
}

%typemap(throws) SWIGTYPE CLASS {
  $&1_ltype temp = new $1_ltype($1);
  SWIG_exception((int)temp,"Thrown exception from C++ (object)");
}

%typemap(throws) SWIGTYPE {
  (void)$1;
  SWIG_exception(0,"Thrown exception from C++ (unknown)");
}

%typemap(throws) char * {
  SWIG_exception(0,$1);
}
