/* -----------------------------------------------------------------------------
 * cdata.i
 *
 * SWIG library file containing macros for manipulating raw C data as strings.
 * ----------------------------------------------------------------------------- */

%{
typedef struct SWIGCDATA {
    char *data;
    int   len;
} SWIGCDATA;
%}

%typemap(gotype) SWIGCDATA %{ []byte %}
%typemap(out) SWIGCDATA %{
  $result.data = (char*)_swig_goallocate($1.len);
  memcpy($result.data, $1.data, $1.len);
  $result.len = (int)$1.len;
%}

/* -----------------------------------------------------------------------------
 * %cdata(TYPE [, NAME]) 
 *
 * Convert raw C data to a binary string.
 * ----------------------------------------------------------------------------- */

%define %cdata(TYPE,NAME...)

%insert("header") {
#if #NAME == ""
static SWIGCDATA cdata_##TYPE(TYPE *ptr, int nelements) {
#else
static SWIGCDATA cdata_##NAME(TYPE *ptr, int nelements) {
#endif
   SWIGCDATA d;
   d.data = (char *) ptr;
#if #TYPE != "void"
   d.len  = nelements*sizeof(TYPE);
#else
   d.len  = nelements;
#endif
   return d;
}
}

%typemap(default) int nelements "$1 = 1;"

#if #NAME == ""
SWIGCDATA cdata_##TYPE(TYPE *ptr, int nelements);
#else
SWIGCDATA cdata_##NAME(TYPE *ptr, int nelements);
#endif
%enddef

%typemap(default) int nelements;

%rename(cdata) ::cdata_void(void *ptr, int nelements);

%cdata(void);

/* Memory move function. Due to multi-argument typemaps this appears
   to be wrapped as
   void memmove(void *data, const char *s); */
void memmove(void *data, char *indata, int inlen);
