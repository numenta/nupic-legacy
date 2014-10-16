/* -----------------------------------------------------------------------------
 * typemaps.i
 *
 * The Ocaml module handles all types uniformly via typemaps. Here
 * are the definitions.
 * ----------------------------------------------------------------------------- */

/* Pointers */

%typemap(in) void ""

%typemap(out) void "$result = Val_int(0);"

%typemap(in) void * {
    $1 = caml_ptr_val($input,$descriptor);
}

%typemap(varin) void * {
    $1 = ($ltype)caml_ptr_val($input,$descriptor);
}

%typemap(out) void * {
    $result = caml_val_ptr($1,$descriptor);
}

%typemap(varout) void * {
    $result = caml_val_ptr($1,$descriptor);
}

#ifdef __cplusplus

%typemap(in) SWIGTYPE & {
    /* %typemap(in) SWIGTYPE & */
    $1 = ($ltype) caml_ptr_val($input,$1_descriptor);
}

%typemap(varin) SWIGTYPE & {
    /* %typemap(varin) SWIGTYPE & */
    $1 = *(($ltype) caml_ptr_val($input,$1_descriptor));
}

%typemap(out) SWIGTYPE & {
    /* %typemap(out) SWIGTYPE & */
    CAML_VALUE *fromval = caml_named_value("create_$ntype_from_ptr");
    if( fromval ) {
	$result = callback(*fromval,caml_val_ptr((void *) &$1,$1_descriptor));
    } else {
	$result = caml_val_ptr ((void *) &$1,$1_descriptor);
    }
}

#if 0
%typemap(argout) SWIGTYPE & {
    CAML_VALUE *fromval = caml_named_value("create_$ntype_from_ptr");
    if( fromval ) {
	swig_result =
	    caml_list_append(swig_result,
			     callback(*fromval,caml_val_ptr((void *) $1,
							    $1_descriptor)));
    } else {
	swig_result =
	    caml_list_append(swig_result,
			     caml_val_ptr ((void *) $1,$1_descriptor));
    }
}
#endif

%typemap(argout) const SWIGTYPE & { }

%typemap(in) SWIGTYPE {
    $1 = *(($&1_ltype) caml_ptr_val($input,$&1_descriptor)) ;
}

%typemap(out) SWIGTYPE {
    /* %typemap(out) SWIGTYPE */
    $&1_ltype temp = new $ltype((const $1_ltype &) $1);
    CAML_VALUE *fromval = caml_named_value("create_$ntype_from_ptr");
    if( fromval ) {
	$result = callback(*fromval,caml_val_ptr((void *)temp,$&1_descriptor));
    } else {
	$result = caml_val_ptr ((void *)temp,$&1_descriptor);
    }
}

%typemap(in) char *& (char *temp) {
  /* %typemap(in) char *& */
  temp = (char*)caml_val_ptr($1,$descriptor);
  $1 = &temp;
}

%typemap(argout) char *& {
  /* %typemap(argout) char *& */
  swig_result =	caml_list_append(swig_result,caml_val_string_len(*$1, strlen(*$1)));
}

#else

%typemap(in) SWIGTYPE {
    $1 = *(($&1_ltype) caml_ptr_val($input,$&1_descriptor)) ;
}

%typemap(out) SWIGTYPE {
    /* %typemap(out) SWIGTYPE */
    void *temp = calloc(1,sizeof($ltype));
    CAML_VALUE *fromval = caml_named_value("create_$ntype_from_ptr");
    memmove( temp, &$1, sizeof( $1_type ) );
    if( fromval ) {
	$result = callback(*fromval,caml_val_ptr((void *)temp,$&1_descriptor));
    } else {
	$result = caml_val_ptr ((void *)temp,$&1_descriptor);
    }
}

%apply SWIGTYPE { const SWIGTYPE & };

#endif

/* The SIMPLE_MAP macro below defines the whole set of typemaps needed
   for simple types. */

%define SIMPLE_MAP(C_NAME, C_TO_MZ, MZ_TO_C)
/* In */
%typemap(in) C_NAME {
    $1 = MZ_TO_C($input);
}
%typemap(varin) C_NAME {
    $1 = MZ_TO_C($input);
}
%typemap(in) C_NAME & ($*1_ltype temp) {
    temp = ($*1_ltype) MZ_TO_C($input);
    $1 = &temp;
}
%typemap(varin) C_NAME & {
    $1 = MZ_TO_C($input);
}
%typemap(directorout) C_NAME {
    $1 = MZ_TO_C($input);
}
%typemap(in) C_NAME *INPUT ($*1_ltype temp) {
    temp = ($*1_ltype) MZ_TO_C($input);
    $1 = &temp;
}
%typemap(in,numinputs=0) C_NAME *OUTPUT ($*1_ltype temp) {
    $1 = &temp;
}
/* Out */
%typemap(out) C_NAME {
    $result = C_TO_MZ($1);
}
%typemap(varout) C_NAME {
    $result = C_TO_MZ($1);
}
%typemap(varout) C_NAME & {
    /* %typemap(varout) C_NAME & (generic) */
    $result = C_TO_MZ($1);
}
%typemap(argout) C_NAME *OUTPUT {
    swig_result = caml_list_append(swig_result,C_TO_MZ((long)*$1));
}
%typemap(out) C_NAME & {
    /* %typemap(out) C_NAME & (generic) */
    $result = C_TO_MZ(*$1);
}
%typemap(argout) C_NAME & {
    swig_result = caml_list_append(swig_result,C_TO_MZ((long)*$1));
}
%typemap(directorin) C_NAME {
    args = caml_list_append(args,C_TO_MZ($1_name));
}
%enddef

SIMPLE_MAP(bool, caml_val_bool, caml_long_val);
SIMPLE_MAP(oc_bool, caml_val_bool, caml_long_val);
SIMPLE_MAP(char, caml_val_char, caml_long_val);
SIMPLE_MAP(signed char, caml_val_char, caml_long_val);
SIMPLE_MAP(unsigned char, caml_val_uchar, caml_long_val);
SIMPLE_MAP(int, caml_val_int, caml_long_val);
SIMPLE_MAP(short, caml_val_short, caml_long_val);
SIMPLE_MAP(wchar_t, caml_val_short, caml_long_val);
SIMPLE_MAP(long, caml_val_long, caml_long_val);
SIMPLE_MAP(ptrdiff_t, caml_val_int, caml_long_val);
SIMPLE_MAP(unsigned int, caml_val_uint, caml_long_val);
SIMPLE_MAP(unsigned short, caml_val_ushort, caml_long_val);
SIMPLE_MAP(unsigned long, caml_val_ulong, caml_long_val);
SIMPLE_MAP(size_t, caml_val_int, caml_long_val);
SIMPLE_MAP(float, caml_val_float, caml_double_val);
SIMPLE_MAP(double, caml_val_double, caml_double_val);
SIMPLE_MAP(long long,caml_val_ulong,caml_long_val);
SIMPLE_MAP(unsigned long long,caml_val_ulong,caml_long_val);

/* Void */

%typemap(out) void "$result = Val_unit;";

/* Pass through value */

%typemap (in) value,caml::value,CAML_VALUE "$1=$input;";
%typemap (out) value,caml::value,CAML_VALUE "$result=$1;";

/* Arrays */

%typemap(in) ArrayCarrier * {
    $1 = ($ltype)caml_ptr_val($input,$1_descriptor);
}

%typemap(out) ArrayCarrier * {
    CAML_VALUE *fromval = caml_named_value("create_$ntype_from_ptr");
    if( fromval ) {
	$result = callback(*fromval,caml_val_ptr((void *)$1,$1_descriptor));
    } else {
	$result = caml_val_ptr ((void *)$1,$1_descriptor);
    }
}

#if 0
%include <carray.i>
#endif

/* Handle char arrays as strings */

%define %char_ptr_in(how)
%typemap(how)  char *, signed char *, unsigned char * {
    /* %typemap(how) char * ... */
    $1 = ($ltype)caml_string_val($input);
}
/* Again work around the empty array bound bug */
%typemap(how) char [ANY], signed char [ANY], unsigned char [ANY] {
    /* %typemap(how) char [ANY] ... */
    char *temp = caml_string_val($input);
    strcpy((char *)$1,temp); 
    /* strncpy would be better but we might not have an array size */
}
%enddef

%char_ptr_in(in);
%char_ptr_in(varin);
%char_ptr_in(directorout);

%define %char_ptr_out(how) 
%typemap(how) 
    char *, signed char *, unsigned char *, 
    const char *, const signed char *, const unsigned char * {
    $result = caml_val_string((char *)$1);
}
/* I'd like to use the length here but can't because it might be empty */
%typemap(how)
    char [ANY], signed char [ANY], unsigned char [ANY],
    const char [ANY], const signed char [ANY], const unsigned char [ANY] {
    $result = caml_val_string((char *)$1);
}
%enddef

%char_ptr_out(out);
%char_ptr_out(varout);
%char_ptr_out(directorin);

%define %swigtype_ptr_in(how)
%typemap(how) SWIGTYPE * {
    /* %typemap(how) SWIGTYPE * */
    $1 = ($ltype)caml_ptr_val($input,$1_descriptor);
}
%typemap(how) SWIGTYPE (CLASS::*) {
    /* %typemap(how) SWIGTYPE (CLASS::*) */
    void *v = caml_ptr_val($input,$1_descriptor);
    memcpy(& $1, &v, sizeof(v));
}
%enddef

%define %swigtype_ptr_out(how)
%typemap(out) SWIGTYPE * {
    /* %typemap(how) SWIGTYPE *, SWIGTYPE (CLASS::*) */
    CAML_VALUE *fromval = caml_named_value("create_$ntype_from_ptr");
    if( fromval ) {
	$result = callback(*fromval,caml_val_ptr((void *)$1,$1_descriptor));
    } else {
	$result = caml_val_ptr ((void *)$1,$1_descriptor);
    }
}
%typemap(how) SWIGTYPE (CLASS::*) {
    /* %typemap(how) SWIGTYPE *, SWIGTYPE (CLASS::*) */
    void *v;
    memcpy(&v,& $1, sizeof(void *));
    $result = caml_val_ptr (v,$1_descriptor);
}
%enddef

%swigtype_ptr_in(in);
%swigtype_ptr_in(varin);
%swigtype_ptr_in(directorout);
%swigtype_ptr_out(out);
%swigtype_ptr_out(varout);
%swigtype_ptr_out(directorin);

%define %swigtype_array_fail(how,msg)
%typemap(how) SWIGTYPE [] {
    failwith(msg);
}
%enddef

%swigtype_array_fail(in,"Array arguments for arbitrary types need a typemap");
%swigtype_array_fail(varin,"Assignment to global arrays for arbitrary types need a typemap");
%swigtype_array_fail(out,"Array arguments for arbitrary types need a typemap");
%swigtype_array_fail(varout,"Array variables need a typemap");
%swigtype_array_fail(directorin,"Array results with arbitrary types need a typemap");
%swigtype_array_fail(directorout,"Array arguments with arbitrary types need a typemap");

/* C++ References */

/* Enums */
%define %swig_enum_in(how)
%typemap(how) enum SWIGTYPE {
    $1 = ($type)caml_long_val_full($input,"$type_marker");
}
%enddef

%define %swig_enum_out(how)
%typemap(how) enum SWIGTYPE {
    $result = callback2(*caml_named_value(SWIG_MODULE "_int_to_enum"),*caml_named_value("$type_marker"),Val_int((int)$1));
}
%enddef

%swig_enum_in(in)
%swig_enum_in(varin)
%swig_enum_in(directorout)
%swig_enum_out(out)
%swig_enum_out(varout)
%swig_enum_out(directorin)


/* Array reference typemaps */
%apply SWIGTYPE & { SWIGTYPE ((&)[ANY]) }

/* const pointers */
%apply SWIGTYPE * { SWIGTYPE *const }

