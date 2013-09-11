/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * modula3.swg
 *
 * Modula3 typemaps
 * ----------------------------------------------------------------------------- */

%include <modula3head.swg>

/* The ctype, m3rawtype and m3wraptype typemaps work together and so there should be one of each. 
 * The ctype typemap contains the C type used in the signature of C wrappers for C++ functions. 
 * The m3rawtype typemap contains the M3 type used in the raw interface.
 * The m3rawintype typemap contains the M3 type used as function argument.
 * The m3rawrettype typemap contains the M3 type used as return value.
 * The m3wraptype typemap contains the M3 type used in the M3 type wrapper classes and module class. */

/* Primitive types */
%typemap(ctype) bool,               const bool &               "bool"
%typemap(ctype) char,               const char &               "char"
%typemap(ctype) signed char,        const signed char &        "signed char"
%typemap(ctype) unsigned char,      const unsigned char &      "unsigned short"
%typemap(ctype) short,              const short &              "short"
%typemap(ctype) unsigned short,     const unsigned short &     "unsigned short"
%typemap(ctype) int,                const int &                "int"
%typemap(ctype) unsigned int,       const unsigned int &       "unsigned int"
%typemap(ctype) long,               const long &               "long"
%typemap(ctype) unsigned long,      const unsigned long &      "unsigned long"
%typemap(ctype) long long,          const long long &          "long long"
%typemap(ctype) unsigned long long, const unsigned long long & "unsigned long long"
%typemap(ctype) float,              const float &              "float"
%typemap(ctype) double,             const double &             "double"
%typemap(ctype) char *                                         "char *"
%typemap(ctype) void                                           "void"

%typemap(m3rawtype) bool,               const bool &               "BOOLEAN"
%typemap(m3rawtype) char,               const char &               "C.char"
%typemap(m3rawtype) signed char,        const signed char &        "C.signed_char"
%typemap(m3rawtype) unsigned char,      const unsigned char &      "C.unsigned_char"
%typemap(m3rawtype) short,              const short &              "C.short"
%typemap(m3rawtype) unsigned short,     const unsigned short &     "C.unsigned_short"
%typemap(m3rawtype) int,                const int &                "C.int"
%typemap(m3rawtype) unsigned int,       const unsigned int &       "C.unsigned_int"
%typemap(m3rawtype) long,               const long &               "C.long"
%typemap(m3rawtype) unsigned long,      const unsigned long &      "C.unsigned_long"
%typemap(m3rawtype) long long,          const long long &          "C.long_long"
%typemap(m3rawtype) unsigned long long, const unsigned long long & "C.unsigned_long_long"
%typemap(m3rawtype) float,              const float &              "C.float"
%typemap(m3rawtype) double,             const double &             "C.double"
%typemap(m3rawtype) long double,        const long double &        "C.long_double"
%typemap(m3rawtype) char *                                         "C.char_star"
%typemap(m3rawtype) void                                           ""
%typemap(m3rawtype) FILE                                           "Cstdio.FILE";
%typemap(m3rawtype) FILE *                                         "Cstdio.FILE_star";


%typemap(m3rawintype) bool *,               bool &,               bool               "BOOLEAN"
%typemap(m3rawintype) char *,               char &,               char               "C.char"
%typemap(m3rawintype) signed char *,        signed char &,        signed char        "C.signed_char"
%typemap(m3rawintype) unsigned char *,      unsigned char &,      unsigned char      "C.unsigned_char"
%typemap(m3rawintype) short *,              short &,              short              "C.short"
%typemap(m3rawintype) unsigned short *,     unsigned short &,     unsigned short     "C.unsigned_short"
%typemap(m3rawintype) int *,                int &,                int                "C.int"
%typemap(m3rawintype) unsigned int *,       unsigned int &,       unsigned int       "C.unsigned_int"
%typemap(m3rawintype) long *,               long &,               long               "C.long"
%typemap(m3rawintype) unsigned long *,      unsigned long &,      unsigned long      "C.unsigned_long"
%typemap(m3rawintype) long long *,          long long &,          long long          "C.long_long"
%typemap(m3rawintype) unsigned long long *, unsigned long long &, unsigned long long "C.unsigned_long_long"
%typemap(m3rawintype) float *,              float &,              float              "C.float"
%typemap(m3rawintype) double *,             double &,             double             "C.double"
%typemap(m3rawintype) long double *,        long double &,        long double        "C.long_double"
%typemap(m3rawintype) char *                                                         "C.char_star"
%typemap(m3rawintype) void                                                           ""
%typemap(m3rawintype) void *                                                         "ADDRESS"
%typemap(m3rawintype) FILE                                                           "Cstdio.FILE";
%typemap(m3rawintype) FILE *                                                         "Cstdio.FILE_star";

%typemap(m3rawinmode) char *, void *, FILE *  ""


%typemap(m3rawrettype) bool,               const bool &               "BOOLEAN"
%typemap(m3rawrettype) char,               const char &               "C.char"
%typemap(m3rawrettype) signed char,        const signed char &        "C.signed_char"
%typemap(m3rawrettype) unsigned char,      const unsigned char &      "C.unsigned_char"
%typemap(m3rawrettype) short,              const short &              "C.short"
%typemap(m3rawrettype) unsigned short,     const unsigned short &     "C.unsigned_short"
%typemap(m3rawrettype) int,                const int &                "C.int"
%typemap(m3rawrettype) unsigned int,       const unsigned int &       "C.unsigned_int"
%typemap(m3rawrettype) long,               const long &               "C.long"
%typemap(m3rawrettype) unsigned long,      const unsigned long &      "C.unsigned_long"
%typemap(m3rawrettype) long long,          const long long &          "C.long_long"
%typemap(m3rawrettype) unsigned long long, const unsigned long long & "C.unsigned_long_long"
%typemap(m3rawrettype) float,              const float &              "C.float"
%typemap(m3rawrettype) double,             const double &             "C.double"
%typemap(m3rawrettype) long double,        const long double &        "C.long_double"
%typemap(m3rawrettype) char *                                         "C.char_star"
%typemap(m3rawrettype) void                                           ""
%typemap(m3rawrettype) void *                                         "ADDRESS"
%typemap(m3rawrettype) FILE                                           "Cstdio.FILE";
%typemap(m3rawrettype) FILE *                                         "Cstdio.FILE_star";


%typemap("m3rawtype:import")
  char,               const char &,
  signed char,        const signed char &,
  unsigned char,      const unsigned char &,
  short,              const short &,
  unsigned short,     const unsigned short &,
  int,                const int &,
  unsigned int,       const unsigned int &,
  long,               const long &,
  unsigned long,      const unsigned long &,
  long long,          const long long &,
  unsigned long long, const unsigned long long &,
  float,              const float &,
  double,             const double &,
  long double,        const long double &,
  char *
    "Ctypes AS C"

%typemap("m3rawintype:import")
  char,               const char &,
  signed char,        const signed char &,
  unsigned char,      const unsigned char &,
  short,              const short &,
  unsigned short,     const unsigned short &,
  int,                const int &,
  unsigned int,       const unsigned int &,
  long,               const long &,
  unsigned long,      const unsigned long &,
  long long,          const long long &,
  unsigned long long, const unsigned long long &,
  float,              const float &,
  double,             const double &,
  long double,        const long double &,
  char *
    "Ctypes AS C"

%typemap("m3rawrettype:import")
  char,               const char &,
  signed char,        const signed char &,
  unsigned char,      const unsigned char &,
  short,              const short &,
  unsigned short,     const unsigned short &,
  int,                const int &,
  unsigned int,       const unsigned int &,
  long,               const long &,
  unsigned long,      const unsigned long &,
  long long,          const long long &,
  unsigned long long, const unsigned long long &,
  float,              const float &,
  double,             const double &,
  long double,        const long double &,
  char *
    "Ctypes AS C"

%typemap("m3rawtype:import")
  FILE,   FILE *
    "Cstdio";

%typemap("m3rawintype:import")
  FILE,   FILE *
    "Cstdio";

%typemap("m3rawrettype:import")
  FILE,   FILE *
    "Cstdio";

%typemap(m3wraptype) bool,               const bool &               "BOOLEAN"
%typemap(m3wraptype) char,               const char &               "CHAR"
%typemap(m3wraptype) signed char,        const signed char &        "CHAR"
%typemap(m3wraptype) unsigned char,      const unsigned char &      "CHAR"
%typemap(m3wraptype) short,              const short &              "Integer16.T"
%typemap(m3wraptype) unsigned short,     const unsigned short &     "Cardinal16.T"
%typemap(m3wraptype) int,                const int &                "INTEGER"
%typemap(m3wraptype) unsigned int,       const unsigned int &       "CARDINAL"
%typemap(m3wraptype) long,               const long &               "Integer32.T"
%typemap(m3wraptype) unsigned long,      const unsigned long &      "Cardinal32.T"
%typemap(m3wraptype) long long,          const long long &          "Integer64.T"
%typemap(m3wraptype) unsigned long long, const unsigned long long & "Cardinal64.T"
%typemap(m3wraptype) float,              const float &              "REAL"
%typemap(m3wraptype) double,             const double &             "LONGREAL"
%typemap(m3wraptype) long double,        const long double &        "EXTENDED"
%typemap(m3wraptype) char *                                         "TEXT"
%typemap(m3wraptype) void                                           ""
%typemap(m3wraptype) FILE                                           "Cstdio.FILE";
%typemap(m3wraptype) FILE *                                         "Cstdio.FILE_star";

%typemap(m3wrapintype) bool,               const bool *,               const bool &               "BOOLEAN"
%typemap(m3wrapintype) char,               const char *,               const char &               "CHAR"
%typemap(m3wrapintype) signed char,        const signed char *,        const signed char &        "CHAR"
%typemap(m3wrapintype) unsigned char,      const unsigned char *,      const unsigned char &      "CHAR"
%typemap(m3wrapintype) short,              const short *,              const short &              "INTEGER"
%typemap(m3wrapintype) unsigned short,     const unsigned short *,     const unsigned short &     "CARDINAL"
%typemap(m3wrapintype) int,                const int *,                const int &                "INTEGER"
%typemap(m3wrapintype) unsigned int,       const unsigned int *,       const unsigned int &       "CARDINAL"
%typemap(m3wrapintype) long,               const long *,               const long &               "INTEGER"
%typemap(m3wrapintype) unsigned long,      const unsigned long *,      const unsigned long &      "CARDINAL"
%typemap(m3wrapintype) long long,          const long long *,          const long long &          "INTEGER"
%typemap(m3wrapintype) unsigned long long, const unsigned long long *, const unsigned long long & "CARDINAL"
%typemap(m3wrapintype) float,              const float *,              const float &              "REAL"
%typemap(m3wrapintype) double,             const double *,             const double &             "LONGREAL"
%typemap(m3wrapintype) long double,        const long double *,        const long double &        "EXTENDED"
%typemap(m3wrapintype) const char *, const char []   "TEXT"
%typemap(m3wrapintype,numinputs=0) void              ""
%typemap(m3wrapintype) FILE            "Cstdio.FILE";
%typemap(m3wrapintype) FILE *          "Cstdio.FILE_star";


%typemap(m3wrapouttype) bool,               bool *,               bool &                  "BOOLEAN"
%typemap(m3wrapouttype) char,               char *,               char &                  "CHAR"
%typemap(m3wrapouttype) signed char,        signed char *,        signed char &           "CHAR"
%typemap(m3wrapouttype) unsigned char,      unsigned char *,      unsigned char &         "CHAR"
%typemap(m3wrapouttype) short,              short *,              short &                 "INTEGER"
%typemap(m3wrapouttype) unsigned short,     unsigned short *,     unsigned short &        "CARDINAL"
%typemap(m3wrapouttype) int,                int *,                int &                   "INTEGER"
%typemap(m3wrapouttype) unsigned int,       unsigned int *,       unsigned int &          "CARDINAL"
%typemap(m3wrapouttype) long,               long *,               long &                  "INTEGER"
%typemap(m3wrapouttype) unsigned long,      unsigned long *,      unsigned long &         "CARDINAL"
%typemap(m3wrapouttype) long long,          long long *,          long long &             "INTEGER"
%typemap(m3wrapouttype) unsigned long long, unsigned long long *, unsigned long long &    "CARDINAL"
%typemap(m3wrapouttype) float,              float *,              float &                 "REAL"
%typemap(m3wrapouttype) double,             double *,             double &                "LONGREAL"
%typemap(m3wrapouttype) long double,        long double *,        long double &           "EXTENDED"
%typemap(m3wrapouttype) char *, char []    "TEXT"
%typemap(m3wrapouttype,numinputs=0) void   ""

%typemap(m3wraprettype) bool,               const bool &               "BOOLEAN"
%typemap(m3wraprettype) char,               const char &               "CHAR"
%typemap(m3wraprettype) signed char,        const signed char &        "CHAR"
%typemap(m3wraprettype) unsigned char,      const unsigned char &      "CHAR"
%typemap(m3wraprettype) short,              const short &              "INTEGER"
%typemap(m3wraprettype) unsigned short,     const unsigned short &     "CARDINAL"
%typemap(m3wraprettype) int,                const int &                "INTEGER"
%typemap(m3wraprettype) unsigned int,       const unsigned int &       "CARDINAL"
%typemap(m3wraprettype) long,               const long &               "INTEGER"
%typemap(m3wraprettype) unsigned long,      const unsigned long &      "CARDINAL"
%typemap(m3wraprettype) long long,          const long long &          "INTEGER"
%typemap(m3wraprettype) unsigned long long, const unsigned long long & "CARDINAL"
%typemap(m3wraprettype) float,              const float &              "REAL"
%typemap(m3wraprettype) double,             const double &             "LONGREAL"
%typemap(m3wraprettype) long double,        const long double &        "EXTENDED"
%typemap(m3wraprettype) char *                                         "TEXT"
%typemap(m3wraprettype) void                                           ""
%typemap(m3wraprettype) FILE            "Cstdio.FILE";
%typemap(m3wraprettype) FILE *          "Cstdio.FILE_star";


%typemap(ctype)          char[ANY]               "char *"
%typemap(m3rawtype)      char[ANY]               "C.char_star"
%typemap(m3rawintype)    char[ANY]               "C.char_star"
%typemap(m3rawrettype)   char[ANY]               "C.char_star"
%typemap(m3wraptype)     char[ANY]               "TEXT"
%typemap(m3wrapintype)   char[ANY]               "TEXT"
%typemap(m3wrapouttype)  char[ANY]               "TEXT"
%typemap(m3wraprettype)  char[ANY]               "TEXT"

%typemap(m3wrapinmode)  const char * %{%}
%typemap(m3wrapargvar)  const char * %{$1 : C.char_star;%}
%typemap(m3wrapinconv)  const char * %{$1 := M3toC.SharedTtoS($1_name);%}
%typemap(m3wrapfreearg) const char * %{M3toC.FreeSharedS($1_name,$1);%}
%typemap(m3wrapargraw)  const char * %{$1%}
%typemap("m3wrapargvar:import")  const char * "Ctypes AS C"
%typemap("m3wrapinconv:import")  const char * "M3toC"
%typemap("m3wrapfreearg:import") const char * "M3toC"

%typemap(m3wrapretvar)  char * %{result : C.char_star;%}
%typemap(m3wrapretraw)  char * %{result%}
%typemap(m3wrapretconv) char * %{M3toC.CopyStoT(result)%}
%typemap("m3wrapretvar:import")  char * "Ctypes AS C"
%typemap("m3wrapretconv:import") char * "M3toC"

%typemap(m3wrapinmode)  FILE * %{%}


%typemap("m3wraptype:import")
  FILE,   FILE *
    "Cstdio";

%typemap("m3wrapintype:import")
  FILE,   FILE *
    "Cstdio";

%typemap("m3wraprettype:import")
  FILE,   FILE *
    "Cstdio";


/* Composed types */
%typemap(ctype)                SWIGTYPE "$1_type"
%typemap(m3rawtype)            SWIGTYPE "$1_basetype"
%typemap(m3rawrettype)         SWIGTYPE "UNTRACED REF $1_basetype"
%typemap(m3wraptype)           SWIGTYPE "$1_basetype"
%typemap(m3wrapintype)         SWIGTYPE "$1_basetype"
%typemap(m3wrapouttype)        SWIGTYPE "$1_basetype"
%typemap(m3wraprettype)        SWIGTYPE "$1_basetype"

%typemap(ctype)                SWIGTYPE [] "$1_type"
%typemap(m3rawtype)      const SWIGTYPE [] "UNTRACED REF ARRAY INTEGER OF $1_basetype"
%typemap(m3rawtype)            SWIGTYPE [] "UNTRACED REF ARRAY INTEGER OF $1_basetype"
%typemap(m3rawintype)    const SWIGTYPE [] "(*ARRAY OF*) $1_basetype"
%typemap(m3rawinmode)    const SWIGTYPE [] "READONLY"
%typemap(m3rawintype)          SWIGTYPE [] "(*ARRAY OF*) $1_basetype"
%typemap(m3rawinmode)          SWIGTYPE [] "VAR"
%typemap(m3rawrettype)   const SWIGTYPE [] "UNTRACED REF ARRAY INTEGER OF $1_basetype"
%typemap(m3rawrettype)         SWIGTYPE [] "UNTRACED REF ARRAY INTEGER OF $1_basetype"
%typemap(m3wraptype)           SWIGTYPE [] "$1_basetype"
%typemap(m3wrapintype)   const SWIGTYPE [] "ARRAY OF $1_basetype"
%typemap(m3wrapinmode)   const SWIGTYPE [] "READONLY"
%typemap(m3wrapintype)         SWIGTYPE [] "ARRAY OF $1_basetype"
%typemap(m3wrapinmode)         SWIGTYPE [] "VAR"
%typemap(m3wrapouttype)        SWIGTYPE [] "ARRAY OF $1_basetype"
%typemap(m3wraprettype)        SWIGTYPE [] "REF ARRAY OF $1_basetype"

%typemap(ctype)                SWIGTYPE * "$1_type"
%typemap(m3rawtype)      const SWIGTYPE * "UNTRACED REF $1_basetype"
%typemap(m3rawtype)            SWIGTYPE * "UNTRACED REF $1_basetype"
%typemap(m3rawintype)    const SWIGTYPE * "$1_basetype"
%typemap(m3rawinmode)    const SWIGTYPE * "READONLY"
%typemap(m3rawintype)          SWIGTYPE * "$1_basetype"
%typemap(m3rawinmode)          SWIGTYPE * "VAR"
%typemap(m3rawrettype)   const SWIGTYPE * "UNTRACED REF $1_basetype"
%typemap(m3rawrettype)         SWIGTYPE * "UNTRACED REF $1_basetype"
%typemap(m3wraptype)           SWIGTYPE * "$1_basetype"
%typemap(m3wrapintype)   const SWIGTYPE * "$1_basetype"
%typemap(m3wrapinmode)   const SWIGTYPE * "READONLY"
%typemap(m3wrapintype)         SWIGTYPE * "$1_basetype"
%typemap(m3wrapinmode)         SWIGTYPE * "VAR"
%typemap(m3wrapouttype)        SWIGTYPE * "$1_basetype"
%typemap(m3wraprettype)        SWIGTYPE * "UNTRACED REF $1_basetype"

%typemap(ctype)                SWIGTYPE & "$1_type"
%typemap(m3rawtype)      const SWIGTYPE & "UNTRACED REF $1_basetype"
%typemap(m3rawtype)            SWIGTYPE & "UNTRACED REF $1_basetype"
%typemap(m3rawintype)    const SWIGTYPE & "$1_basetype"
%typemap(m3rawinmode)    const SWIGTYPE & "READONLY"
%typemap(m3rawintype)          SWIGTYPE & "$1_basetype"
%typemap(m3rawinmode)          SWIGTYPE & "VAR"
%typemap(m3rawrettype)   const SWIGTYPE & "UNTRACED REF $1_basetype"
%typemap(m3rawrettype)         SWIGTYPE & "UNTRACED REF $1_basetype"
%typemap(m3wraptype)           SWIGTYPE & "$1_basetype"
%typemap(m3wrapintype)   const SWIGTYPE & "$1_basetype"
%typemap(m3wrapinmode)   const SWIGTYPE & "READONLY"
%typemap(m3wrapintype)         SWIGTYPE & "$1_basetype"
%typemap(m3wrapinmode)         SWIGTYPE & "VAR"
%typemap(m3wrapouttype)        SWIGTYPE & "$1_basetype"
%typemap(m3wraprettype)        SWIGTYPE & "UNTRACED REF $1_basetype"

%typemap(ctype)           enum SWIGTYPE "$1_type"
%typemap(m3rawtype)       enum SWIGTYPE "C.int"
%typemap(m3rawintype)     enum SWIGTYPE "C.int (* $1_type *)"
%typemap(m3rawrettype)    enum SWIGTYPE "C.int"
%typemap(m3wraptype)      enum SWIGTYPE "$*1_type"
%typemap(m3wrapintype)    enum SWIGTYPE "$1_type"
%typemap(m3wrapouttype)   enum SWIGTYPE "$1_type"
%typemap(m3wraprettype)   enum SWIGTYPE "$*1_type"

/* pointer to a class member */
%typemap(ctype)      SWIGTYPE (CLASS::*) "$1_type"
%typemap(m3rawtype)  SWIGTYPE (CLASS::*) "REFANY"
%typemap(m3wraptype) SWIGTYPE (CLASS::*) "$1_basetype"

/* The following are the in, out, freearg, argout typemaps.
   These are the PInvoke code generating typemaps for converting from C# to C and visa versa. */

/* primitive types */
%typemap(in) bool
%{ $1 = $input ? true : false; %}

%typemap(in) char, 
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
             double, 
             enum SWIGTYPE
%{ $1 = ($1_ltype)$input; %}

%typemap(out) bool               %{ $result = $1; %}
%typemap(out) char               %{ $result = $1; %}
%typemap(out) signed char        %{ $result = $1; %}
%typemap(out) unsigned char      %{ $result = $1; %}
%typemap(out) short              %{ $result = $1; %}
%typemap(out) unsigned short     %{ $result = $1; %}
%typemap(out) int                %{ $result = $1; %}
%typemap(out) unsigned int       %{ $result = $1; %}
%typemap(out) long               %{ $result = $1; %}
%typemap(out) unsigned long      %{ $result = $1; %}
%typemap(out) long long          %{ $result = $1; %}
%typemap(out) unsigned long long %{ $result = $1; %}
%typemap(out) float              %{ $result = $1; %}
%typemap(out) double             %{ $result = $1; %}
%typemap(out) enum SWIGTYPE      %{ $result = $1; %}

/* char * - treat as String */
%typemap(in) char * {
  $1 = $input;
}
//%typemap(freearg) char * { if ($1) JCALL2(ReleaseStringUTFChars, jenv, $input, $1); }
//%typemap(out) char * { if($1) $result = JCALL1(NewStringUTF, jenv, $1); }

%typemap(out) void ""

/* primitive types by const reference */
%typemap(in) const bool & (bool temp)
%{ temp = $input ? true : false; 
   $1 = &temp; %}

%typemap(in) const char & (char temp), 
             const signed char & (signed char temp), 
             const unsigned char & (unsigned char temp), 
             const short & (short temp), 
             const unsigned short & (unsigned short temp), 
             const int & (int temp), 
             const unsigned int & (unsigned int temp), 
             const long & (long temp), 
             const unsigned long & (unsigned long temp), 
             const long long & ($*1_ltype temp), 
             const unsigned long long & ($*1_ltype temp), 
             const float & (float temp), 
             const double & (double temp)
%{ temp = ($*1_ltype)$input; 
$1 = &temp; %}

%typemap(out) const bool &               %{ $result = *$1; %}
%typemap(out) const char &               %{ $result = *$1; %}
%typemap(out) const signed char &        %{ $result = *$1; %}
%typemap(out) const unsigned char &      %{ $result = *$1; %}
%typemap(out) const short &              %{ $result = *$1; %}
%typemap(out) const unsigned short &     %{ $result = *$1; %}
%typemap(out) const int &                %{ $result = *$1; %}
%typemap(out) const unsigned int &       %{ $result = *$1; %}
%typemap(out) const long &               %{ $result = *$1; %}
%typemap(out) const unsigned long &      %{ $result = *$1; %}
%typemap(out) const long long &          %{ $result = *$1; %}
%typemap(out) const unsigned long long & %{ $result = *$1; %}
%typemap(out) const float &              %{ $result = *$1; %}
%typemap(out) const double &             %{ $result = *$1; %}

/* Default handling. Object passed by value. Convert to a pointer */
%typemap(in) SWIGTYPE ($&1_type argp)
%{ argp = *($&1_ltype*)&$input; 
   if (!argp) {
//     SWIG_JavaThrowException(jenv, SWIG_JavaNullPointerException, "Attempt to dereference null $1_type");
     RETURN $null;
   }
   $1 = *argp; %}
%typemap(out) SWIGTYPE 
#ifdef __cplusplus
%{*($&1_ltype*)&$result = new $1_ltype((const $1_ltype &)$1); %}
#else
{
  $&1_ltype $1ptr = ($&1_ltype) malloc(sizeof($1_ltype));
  memmove($1ptr, &$1, sizeof($1_type));
  *($&1_ltype*)&$result = $1ptr;
}
#endif

/* Generic pointers and references */
%typemap(in) SWIGTYPE *, SWIGTYPE (CLASS::*) %{ $1 = *($&1_ltype)&$input; %}
%typemap(in) SWIGTYPE & %{ $1 = *($&1_ltype)&$input;
  if(!$1) {
    //SWIG_JavaThrowException(jenv, SWIG_JavaNullPointerException, "$1_type reference is null");
    RETURN $null;
  } %}
%typemap(out) SWIGTYPE *, SWIGTYPE &, SWIGTYPE (CLASS::*) %{ *($&1_ltype)&$result = $1; %} 


/* Default array handling */
%typemap(in) SWIGTYPE [] %{ $1 = *($&1_ltype)&$input; %}
%typemap(out) SWIGTYPE [] %{ *($&1_ltype)&$result = $1; %} 

/* char[ANY] - treat as String */
%typemap(in) char[ANY] { 
    $1 = $input;
}

%typemap(argout) char[ANY] ""
%typemap(freearg) char[ANY] ""//{ if ($1) JCALL2(ReleaseStringUTFChars, jenv, $input, $1); }
%typemap(out) char[ANY] { if($1) $result = $1; }


/* Typecheck typemaps - The purpose of these is merely to issue a warning for overloaded C++ functions 
 * that cannot be overloaded in C# as more than one C++ type maps to a single C# type */

%typecheck(SWIG_TYPECHECK_BOOL) /* Java boolean */
    bool,
    const bool &
    ""

%typecheck(SWIG_TYPECHECK_CHAR) /* Java char */
    char, 
    const char &
    ""

%typecheck(SWIG_TYPECHECK_INT8) /* Java byte */
    signed char,
    const signed char &
    ""

%typecheck(SWIG_TYPECHECK_INT16) /* Java short */
    unsigned char, 
    short, 
    const unsigned char &, 
    const short &
    ""

%typecheck(SWIG_TYPECHECK_INT32) /* Java int */
    unsigned short, 
    int, 
    long, 
    const unsigned short &, 
    const int &, 
    const long &,
    enum SWIGTYPE
    ""

%typecheck(SWIG_TYPECHECK_INT64) /* Java long */
    unsigned int, 
    unsigned long, 
    long long, 
    const unsigned int &, 
    const unsigned long &, 
    const long long &
    ""

%typecheck(SWIG_TYPECHECK_INT128) /* Java BigInteger */
    unsigned long long
    ""

%typecheck(SWIG_TYPECHECK_FLOAT) /* Java float */
    float,
    const float &
    ""

%typecheck(SWIG_TYPECHECK_DOUBLE) /* Java double */
    double,
    const double &
    ""

%typecheck(SWIG_TYPECHECK_STRING) /* Java String */
    char *,
    char[ANY]
    ""

%typecheck(SWIG_TYPECHECK_POINTER) /* Default */
    SWIGTYPE, 
    SWIGTYPE *, 
    SWIGTYPE &, 
    SWIGTYPE [],
    SWIGTYPE (CLASS::*)
    ""

/* Exception handling */

%typemap(throws) int, 
                 long, 
                 short, 
                 unsigned int, 
                 unsigned long, 
                 unsigned short {
  char error_msg[256];
  sprintf(error_msg, "C++ $1_type exception thrown, value: %d", $1);
  SWIG_JavaThrowException(jenv, SWIG_JavaRuntimeException, error_msg);
  RETURN $null;
}

%typemap(throws) SWIGTYPE {
  (void)$1;
  SWIG_JavaThrowException(jenv, SWIG_JavaRuntimeException, "C++ $1_type exception thrown");
  RETURN $null;
}

%typemap(throws) char * {
  SWIG_JavaThrowException(jenv, SWIG_JavaRuntimeException, $1);
  RETURN $null;
}


/* Typemaps for code generation in proxy classes and C# type wrapper classes */

/* The in typemap is used for converting function parameter types from the type 
 * used in the proxy, module or type wrapper class to the type used in the PInvoke class. */
%typemap(m3in)     bool,               const bool &,
                 char,               const char &,
                 signed char,        const signed char &,
                 unsigned char,      const unsigned char &,
                 short,              const short &,
                 unsigned short,     const unsigned short &,
                 int,                const int &,
                 unsigned int,       const unsigned int &,
                 long,               const long &,
                 unsigned long,      const unsigned long &,
                 long long,          const long long &,
                 unsigned long long, const unsigned long long &,
                 float,              const float &,
                 double,             const double &,
                 char *,
                 char[ANY],
                 enum SWIGTYPE 
    "$input"
%typemap(m3in) SWIGTYPE "$&*1_type.getCPtr($input)"
%typemap(m3in) SWIGTYPE *, SWIGTYPE &, SWIGTYPE [], SWIGTYPE (CLASS::*) "$1_basetype.getCPtr($input)"

/* The m3out typemap is used for converting function return types from the return type
 * used in the PInvoke class to the type returned by the proxy, module or type wrapper class. */
%typemap(m3out)   bool,               const bool &,
                  char,               const char &,
                  signed char,        const signed char &,
                  unsigned char,      const unsigned char &,
                  short,              const short &,
                  unsigned short,     const unsigned short &,
                  int,                const int &,
                  unsigned int,       const unsigned int &,
                  long,               const long &,
                  unsigned long,      const unsigned long &,
                  long long,          const long long &,
                  unsigned long long, const unsigned long long &,
                  float,              const float &,
                  double,             const double &,
                  char *,
                  char[ANY],
                  enum SWIGTYPE
%{$imcall%}

%typemap(m3out) void %{$imcall%}

%typemap(m3out) SWIGTYPE %{
    RETURN NEW(REF $1_basetype, $imcall);
%}
%typemap(m3out) SWIGTYPE & %{
    RETURN NEW($1_basetype, $imcall, $owner);
%}
%typemap(m3out) SWIGTYPE *, SWIGTYPE [], SWIGTYPE (CLASS::*) %{
    cPtr := $imcall;
    RETURN (cPtr = IntPtr.Zero) ? null : NEW($1_basetype, cPtr, $owner);
%}

/* Properties */
%typemap(m3varin) SWIGTYPE, SWIGTYPE *, SWIGTYPE &, SWIGTYPE [], SWIGTYPE (CLASS::*) %{
PROCEDURE Set$var (value: $vartype) =
  BEGIN
    $imcall;
  END Set$var;
%}

%typemap(m3varout) bool,               const bool &,
                   char,               const char &,
                   signed char,        const signed char &,
                   unsigned char,      const unsigned char &,
                   short,              const short &,
                   unsigned short,     const unsigned short &,
                   int,                const int &,
                   unsigned int,       const unsigned int &,
                   long,               const long &,
                   unsigned long,      const unsigned long &,
                   long long,          const long long &,
                   unsigned long long, const unsigned long long &,
                   float,              const float &,
                   double,             const double &,
                   char *,
                   char[ANY],
                   enum SWIGTYPE %{
PROCEDURE Get$var (): $vartype =
  BEGIN
    RETURN $imcall;
  END Get$var;
%}

%typemap(m3varout) void %{
    get {
      $imcall;
    } %}
%typemap(m3varout) SWIGTYPE %{
    get {
      RETURN new $&*1_mangle($imcall, true);
    } %}
%typemap(m3varout) SWIGTYPE & %{
    get {
      RETURN new $1_basetype($imcall, $owner);
    } %}
%typemap(m3varout) SWIGTYPE *, SWIGTYPE [], SWIGTYPE (CLASS::*) %{
    get {
      IntPtr cPtr = $imcall;
      RETURN (cPtr == IntPtr.Zero) ? null : new $1_basetype(cPtr, $owner);
    } %}

/* Typemaps used for the generation of proxy and type wrapper class code */
%typemap(m3base)                      SWIGTYPE, SWIGTYPE *, SWIGTYPE &, SWIGTYPE [], SWIGTYPE (CLASS::*) ""
%typemap(m3classmodifiers)            SWIGTYPE, SWIGTYPE *, SWIGTYPE &, SWIGTYPE [], SWIGTYPE (CLASS::*) "public"
%typemap(m3code)                      SWIGTYPE, SWIGTYPE *, SWIGTYPE &, SWIGTYPE [], SWIGTYPE (CLASS::*) ""
%typemap(m3imports)                   SWIGTYPE, SWIGTYPE *, SWIGTYPE &, SWIGTYPE [], SWIGTYPE (CLASS::*) "using System;"
%typemap(m3interfaces)                SWIGTYPE "IDisposable"
%typemap(m3interfaces_derived)                  SWIGTYPE *, SWIGTYPE &, SWIGTYPE [], SWIGTYPE (CLASS::*) ""
%typemap(m3ptrconstructormodifiers) SWIGTYPE, SWIGTYPE *, SWIGTYPE &, SWIGTYPE [], SWIGTYPE (CLASS::*) "internal"

%typemap(m3finalize) SWIGTYPE %{
  ~$1_basetype() {
    Dispose();
  }
%}

%typemap(m3destruct, methodname="Dispose") SWIGTYPE {
    if(swigCPtr != IntPtr.Zero && swigCMemOwn) {
      $imcall;
      swigCMemOwn = false;
    }
    swigCPtr = IntPtr.Zero;
    GC.SuppressFinalize(this);
  }

%typemap(m3destruct_derived, methodname="Dispose") SWIGTYPE {
    if(swigCPtr != IntPtr.Zero && swigCMemOwn) {
      $imcall;
      swigCMemOwn = false;
    }
    swigCPtr = IntPtr.Zero;
    GC.SuppressFinalize(this);
    base.Dispose();
  }

%typemap(m3getcptr) SWIGTYPE, SWIGTYPE *, SWIGTYPE &, SWIGTYPE [], SWIGTYPE (CLASS::*) %{
  internal static IntPtr getCPtr($1_basetype obj) {
    RETURN (obj == null) ? IntPtr.Zero : obj.swigCPtr;
  }
%}

/* M3 specific directives */
#define %m3multiretval        %feature("modula3:multiretval")
#define %constnumeric(num)    %feature("constnumeric","num")

%pragma(modula3) moduleimports=%{
IMPORT BlaBla;
%}

%pragma(modula3) imclassimports=%{
FROM BlaBla IMPORT Bla;
%}

/* Some ANSI C typemaps */

%apply unsigned long { size_t };
