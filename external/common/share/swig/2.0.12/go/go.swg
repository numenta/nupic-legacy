/* ------------------------------------------------------------
 * go.swg
 *
 * Go configuration module.
 * ------------------------------------------------------------ */

/* Basic types */

%typemap(gotype) bool,               const bool &               "bool"
%typemap(gotype) char,               const char &               "byte"
%typemap(gotype) signed char,        const signed char &        "int8"
%typemap(gotype) unsigned char,      const unsigned char &      "byte"
%typemap(gotype) short,              const short &              "int16"
%typemap(gotype) unsigned short,     const unsigned short &     "uint16"
%typemap(gotype) int,                const int &                "int"
%typemap(gotype) unsigned int,       const unsigned int &       "uint"
#if SWIGGO_LONG_TYPE_SIZE == 32
%typemap(gotype) long,               const long &               "int32"
%typemap(gotype) unsigned long,      const unsigned long &      "uint32"
#elif SWIGGO_LONG_TYPE_SIZE == 64
%typemap(gotype) long,               const long &               "int64"
%typemap(gotype) unsigned long,      const unsigned long &      "uint64"
#else
#error "SWIGGO_LONG_TYPE_SIZE not 32 or 64"
#endif
%typemap(gotype) long long,          const long long &          "int64"
%typemap(gotype) unsigned long long, const unsigned long long & "uint64"
%typemap(gotype) float,              const float &              "float32"
%typemap(gotype) double,             const double &             "float64"

%typemap(in) bool,
	     char,
	     signed char,
	     unsigned char,
	     short,
	     unsigned short,
	     int,
	     unsigned int,
	     long,
	     unsigned long,
	     long long,
	     unsigned long long,
	     float,
	     double
%{ $1 = ($1_ltype)$input; %}

%typemap(in) const bool &,
	     const char &,
	     const signed char &,
	     const unsigned char &,
	     const short &,
	     const unsigned short &,
	     const int &,
	     const unsigned int &,
	     const long &,
	     const unsigned long &,
	     const long long &,
	     const unsigned long long &,
	     const float &,
	     const double &
%{ $1 = ($1_ltype)&$input; %}

%typemap(out) bool,
	      char,
	      signed char,
	      unsigned char,
	      short,
	      unsigned short,
	      int,
	      unsigned int,
	      long,
	      unsigned long,
	      long long,
	      unsigned long long,
	      float,
	      double
%{ $result = $1; %}

%typemap(out) const bool &,
	      const char &,
	      const signed char &,
	      const unsigned char &,
	      const short &,
	      const unsigned short &,
	      const int &,
	      const unsigned int &,
	      const long &,
	      const unsigned long &,
	      const long long &,
	      const unsigned long long &,
	      const float &,
	      const double &
%{ $result = ($*1_ltype)*$1; %}

%typemap(out) void ""

%typemap(directorin) bool,
		     char,
		     signed char,
		     unsigned char,
		     short,
		     unsigned short,
		     int,
		     unsigned int,
		     long,
		     unsigned long,
		     long long,
		     unsigned long long,
		     float,
		     double
%{ $input = ($1_ltype)$1; %}

%typemap(directorin) const bool &,
		     const char &,
		     const signed char &,
		     const unsigned char &,
		     const short &,
		     const unsigned short &,
		     const int &,
		     const unsigned int &,
		     const long &,
		     const unsigned long &,
		     const long long &,
		     const unsigned long long &,
		     const float &,
		     const double &
%{ $input = ($*1_ltype)$1; %}

%typemap(directorout) bool,
		      char,
		      signed char,
		      unsigned char,
		      short,
		      unsigned short,
		      int,
		      unsigned int,
		      long,
		      unsigned long,
		      long long,
		      unsigned long long,
		      float,
		      double
%{ $result = ($1_ltype)$input; %}

%typemap(directorout) const bool &,
		      const char &,
		      const signed char &,
		      const unsigned char &,
		      const short &,
		      const unsigned short &,
		      const int &,
		      const unsigned int &,
		      const long &,
		      const unsigned long &,
		      const long long &,
		      const unsigned long long &,
		      const float &,
		      const double &
%{
  $result = ($1_ltype)_swig_goallocate(sizeof($*1_ltype));
  *$result = *($1_ltype)&$input;
%}

/* The size_t type.  */

#if SWIGGO_LONG_TYPE_SIZE == 32
%typemap(gotype) size_t, const size_t & %{int%}
#else
%typemap(gotype) size_t, const size_t & %{int64%}
#endif

%typemap(in) size_t
%{ $1 = (size_t)$input; %}

%typemap(in) const size_t &
%{ $1 = ($1_ltype)&$input; %}

%typemap(out) size_t
%{ $result = $1; %}

%typemap(out) const size_t &
%{ $result = ($*1_ltype)*$1; %}

%typemap(directorin) size_t
%{ $input = (size_t)$1; %}

%typemap(directorin) const size_t &
%{ $input = ($*1_ltype)$1; %}

%typemap(directorout) size_t
%{ $result = ($1_ltype)$input; %}

%typemap(directorout) const size_t &
%{
  $result = ($1_ltype)_swig_goallocate(sizeof($*1_ltype));
  *$result = *($1_ltype)$input;
%}

/* Member pointers.  */

%typemap(gotype) SWIGTYPE (CLASS::*)
%{$gotypename%}

%typemap(in) SWIGTYPE (CLASS::*)
%{ $1 = *($&1_ltype)$input; %}

%typemap(out) SWIGTYPE (CLASS::*)
%{
  $result = _swig_goallocate(sizeof($1_ltype));
  *($&1_ltype)$result = $1;
%}

%typemap(directorin) SWIGTYPE (CLASS::*)
%{ $input = *($&1_ltype)$1; %}

%typemap(directorout) SWIGTYPE (CLASS::*)
%{
  $result = _swig_goallocate(sizeof($1_ltype));
  *($&1_ltype)$result = $input;
%}

/* Pointers.  */

/* We can't translate pointers using a typemap, so that is handled in
   the C++ code.  */
%typemap(gotype) SWIGTYPE *
%{$gotypename%}

%typemap(in) SWIGTYPE *
%{ $1 = *($&1_ltype)&$input; %}

%typemap(out) SWIGTYPE *
%{ *($&1_ltype)&$result = $1; %}

%typemap(directorin) SWIGTYPE *
%{ $input = ($1_ltype)$1; %}

%typemap(directorout) SWIGTYPE *
%{ $result = ($1_ltype)$input; %}

%apply SWIGTYPE * { SWIGTYPE *const }

/* Pointer references.  */

%typemap(gotype) SWIGTYPE *const&
%{$gotypename%}

%typemap(in) SWIGTYPE *const& ($*1_ltype temp = 0)
%{
  temp = *($1_ltype)&$input;
  $1 = ($1_ltype)&temp;
%}

%typemap(out) SWIGTYPE *const&
%{ *($1_ltype)&$result = *$1; %}

/* References.  */

/* Converting a C++ reference to Go has to be handled in the C++
   code.  */
%typemap(gotype) SWIGTYPE &
%{$gotypename%}

%typemap(in) SWIGTYPE &
%{ $1 = *($&1_ltype)&$input; %}

%typemap(out) SWIGTYPE &
%{ *($&1_ltype)&$result = $1; %}

%typemap(directorin) SWIGTYPE &
%{ $input = ($1_ltype)&$1; %}

%typemap(directorout) SWIGTYPE &
%{ *($&1_ltype)&$result = $input; %}

/* C arrays turn into Go pointers.  If we know the length we can use a
   slice.  */

%typemap(gotype) SWIGTYPE []
%{$gotypename%}

%typemap(in) SWIGTYPE []
%{ $1 = *($&1_ltype)&$input; %}

%typemap(out) SWIGTYPE []
%{ *($&1_ltype)&$result = $1; %}

%typemap(directorin) SWIGTYPE []
%{ $input = *($1_ltype)&$1; %}

%typemap(directorout) SWIGTYPE []
%{ *($&1_ltype)&$result = $input; %}

/* Strings.  */

%typemap(gotype)
	char *, char *&, char[ANY], char[],
	signed char *, signed char *&, signed char[ANY], signed char[],
	unsigned char *, unsigned char *&, unsigned char[ANY], unsigned char[]
"string"

/* Needed to avoid confusion with the way the go module handles
   references.  */
%typemap(gotype) char&, unsigned char& "*byte"
%typemap(gotype) signed char& "*int8"

%typemap(in)
	char *, char[ANY], char[],
	signed char *, signed char[ANY], signed char[],
	unsigned char *, unsigned char[ANY], unsigned char[]
%{ $1 = ($1_ltype)$input.p; %}

%typemap(in) char *&, signed char *&, unsigned char *&
%{ $1 = ($1_ltype)$input.p; %}

%typemap(out)
	char *, char *&, char[ANY], char[],
	signed char *, signed char *&, signed char[ANY], signed char[],
	unsigned char *, unsigned char *&, unsigned char[ANY], unsigned char[]
%{ $result = _swig_makegostring((char*)$1, $1 ? strlen((char*)$1) : 0); %}

%typemap(directorin)
	char *, char *&, char[ANY], char[],
	signed char *, signed char *&, signed char[ANY], signed char[],
	unsigned char *, unsigned char *&, unsigned char[ANY], unsigned char[]
%{
  $input = _swig_makegostring((char*)$1, $1 ? strlen((char*)$1) : 0);
%}

%typemap(directorout)
	char *, char *&, char[ANY], char[],
	signed char *, signed char *&, signed char[ANY], signed char[],
	unsigned char *, unsigned char *&, unsigned char[ANY], unsigned char[]
%{ $result = ($1_ltype)$input.p; %}

/* String & length */

%typemap(gotype) (char *STRING, size_t LENGTH) "string"

%typemap(in) (char *STRING, size_t LENGTH)
%{
  $1 = ($1_ltype)$input.p;
  $2 = ($2_ltype)$input.n;
%}

%typemap(out) (char *STRING, size_t LENGTH)
%{ $result = _swig_makegostring((char*)$1, (size_t)$2); %}

%typemap(directorin) (char *STRING, size_t LENGTH)
%{ $input = _swig_makegostring((char*)$1, $2); %}

%typemap(directorout) (char *STRING, size_t LENGTH)
%{
  $1 = ($1_ltype)$input.p;
  $2 = ($2_ltype)$input.n;
%}

/* Enums.  We can't do the right thing for enums in typemap(gotype) so
   we deliberately don't define them.  The right thing would be to
   capitalize the name.  This is instead done in go.cxx.  */

%typemap(gotype) enum SWIGTYPE
%{$gotypename%}

%typemap(in) enum SWIGTYPE
%{ $1 = ($1_ltype)$input; %}

%typemap(out) enum SWIGTYPE
%{ $result = (intgo)$1; %}

%typemap(directorin) enum SWIGTYPE
%{ $input = ($1_ltype)$1; %}

%typemap(directorout) enum SWIGTYPE
%{ $result = ($1_ltype)$input; %}

%typemap(directorin) enum SWIGTYPE & (intgo e)
%{
  e = (intgo)$1;
  $input = &e;
%}

%typemap(directorout) enum SWIGTYPE &
%{
  $*1_ltype f = ($*1_ltype)*$input;
  $result = ($1_ltype)&f;
%}

/* Arbitrary type.  This is a type passed by value in the C/C++ code.
   We convert it to a pointer for the Go code.  Note that all basic
   types are explicitly handled above.  */

%typemap(gotype) SWIGTYPE
%{$gotypename%}

%typemap(in) SWIGTYPE ($&1_type argp)
%{
  argp = ($&1_ltype)$input;
  if (argp == NULL) {
    _swig_gopanic("Attempt to dereference null $1_type");
  }
  $1 = ($1_ltype)*argp;
%}

%typemap(out) SWIGTYPE
#ifdef __cplusplus
%{ *($&1_ltype*)&$result = new $1_ltype($1); %}
#else
{
  $&1_ltype $1ptr = ($&1_ltype)malloc(sizeof($1_ltype));
  memmove($1ptr, &$1, sizeof($1_type));
  *($&1_ltype*)&$result = $1ptr;
}
#endif

%typemap(directorin) SWIGTYPE
%{ $input = ($&1_ltype)&$1; %}

%typemap(directorout) SWIGTYPE
%{ $result = *($&1_ltype)$input; %}

/* Exception handling */

%typemap(throws) char *
%{ _swig_gopanic($1); %}

%typemap(throws) SWIGTYPE, SWIGTYPE &, SWIGTYPE *, SWIGTYPE [], SWIGTYPE [ANY]
%{
  (void)$1;
  _swig_gopanic("C++ $1_type exception thrown");
%}

/* Typecheck typemaps.  The purpose of these is merely to issue a
   warning for overloaded C++ functions * that cannot be overloaded in
   Go as more than one C++ type maps to a single Go type.  */

%typecheck(SWIG_TYPECHECK_BOOL) /* Go bool */
    bool,
    const bool &
    ""

%typecheck(SWIG_TYPECHECK_CHAR) /* Go byte */
    char,
    const char &,
    unsigned char,
    const unsigned char &
    ""

%typecheck(SWIG_TYPECHECK_INT8) /* Go int8 */
    signed char,
    const signed char &
    ""

%typecheck(SWIG_TYPECHECK_INT16) /* Go int16 */
    short,
    const short &
    ""

%typecheck(SWIG_TYPECHECK_INT16) /* Go uint16 */
    unsigned short,
    const unsigned short &
    ""

%typecheck(SWIG_TYPECHECK_INT32) /* Go int */
    int,
    const int &
    ""

%typecheck(SWIG_TYPECHECK_INT32) /* Go uint */
    unsigned int,
    const unsigned int &
    ""

#if SWIGGO_LONG_TYPE_SIZE == 32
%typecheck(SWIG_TYPECHECK_INT32) /* Go int32 */
    long,
    const long &
    ""

%typecheck(SWIG_TYPECHECK_INT32) /* Go uint32 */
    unsigned long,
    const unsigned long &
    ""
#endif

%typecheck(SWIG_TYPECHECK_INT64) /* Go int64 */
#if SWIGGO_LONG_TYPE_SIZE == 64
    long, 
    const long &, 
#endif
    long long,
    const long long &
    ""

%typecheck(SWIG_TYPECHECK_INT64) /* Go uint64 */
#if SWIGGO_LONG_TYPE_SIZE == 64
    unsigned long, 
    const unsigned long &, 
#endif
    unsigned long long,
    const unsigned long long &
    ""

%typecheck(SWIG_TYPECHECK_FLOAT) /* Go float32 */
    float,
    const float &
    ""

%typecheck(SWIG_TYPECHECK_DOUBLE) /* Go float64 */
    double,
    const double &
    ""

%typecheck(SWIG_TYPECHECK_STRING) /* Go string */
    char *,
    char *&,
    char[ANY],
    char [],
    signed char *,
    signed char *&,
    signed char[ANY],
    signed char [],
    unsigned char *,
    unsigned char *&,
    unsigned char[ANY],
    unsigned char []
    ""

%typecheck(SWIG_TYPECHECK_POINTER)
    SWIGTYPE,
    SWIGTYPE *,
    SWIGTYPE &,
    SWIGTYPE *const&,
    SWIGTYPE [],
    SWIGTYPE (CLASS::*)
    ""

/* Go keywords.  */
%include <gokw.swg>

%include <goruntime.swg>
