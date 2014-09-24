
/* These map the primitive C types to the appropriate R type
   for use in class representations. 
 */

%typemap("rtype") int, int *, int &      "integer";
%apply int {size_t}
%apply int {std::size_t}
%apply int {ptrdiff_t}
%apply int {std::ptrdiff_t}
%apply int {signed int}
%apply int {unsigned int}
%apply int {short}
%apply int {unsigned short}

%typemap("rtype") long, long *, long &      "integer";
%apply long {long long}
%apply long {signed long long}
%apply long {unsigned long long}
%apply long {signed long}
%apply long {unsigned long}

%typemap("rtype") double, double*, double & "numeric";
%typemap("rtype") float, float *, float &  "numeric";
%typemap("rtype") char *, char ** "character";
%typemap("rtype") char            "character";
%typemap("rtype") string, string *, string & "character";
%typemap("rtype") std::string, std::string *, std::string & "character";
%typemap("rtype") bool, bool *    "logical";
%typemap("rtype") enum SWIGTYPE   "character";
%typemap("rtype") enum SWIGTYPE *   "character";
%typemap("rtype") enum SWIGTYPE *const   "character";
%typemap("rtype") enum SWIGTYPE &  "character";
%typemap("rtype") SWIGTYPE * "$R_class";
%typemap("rtype") SWIGTYPE *const "$R_class";
%typemap("rtype") SWIGTYPE & "$R_class";
%typemap("rtype") SWIGTYPE "$&R_class";



/* Have to be careful that as(x, "numeric") is different from as.numeric(x).  
   The latter makes a REALSXP, whereas the former leaves an INTSXP as an
   INTSXP.
*/

/* Force coercion of integer, since by default R sets all constants to
   numeric, which means that you can't directly call a function with an 
   integer using an R numercal literal */

%typemap(scoercein) int, int *, int &
  %{  $input = as.integer($input);     %}
%typemap(scoercein) long, long *, long &
  %{  $input = as.integer($input);     %}
%typemap(scoercein) double, double *, double &
  %{ %}
%typemap(scoercein) float, float *, float &
  %{ %}
%typemap(scoercein) char, char *, char &
  %{  $input = as($input, "character");     %}
%typemap(scoercein) string, string *, string &
  %{  $input = as($input, "character");     %}
%typemap(scoercein) std::string, std::string *, std::string &
  %{  $input = as($input, "character");     %}
%typemap(scoercein) enum SWIGTYPE 
  %{  $input = enumToInteger($input, "$R_class"); %}
%typemap(scoercein) enum SWIGTYPE &
  %{  $input = enumToInteger($input, "$R_class"); %}
%typemap(scoercein) enum SWIGTYPE *
  %{  $input = enumToInteger($input, "$R_class"); %}
%typemap(scoercein) enum SWIGTYPE *const
  %{  $input = enumToInteger($input, "$R_class"); %}


%typemap(scoercein) SWIGTYPE, SWIGTYPE *, SWIGTYPE *const, SWIGTYPE &  
  %{ %}

/*
%typemap(scoercein) SWIGTYPE *, SWIGTYPE *const
  %{ $input = coerceIfNotSubclass($input, "$R_class") %}

%typemap(scoercein) SWIGTYPE & 
  %{ $input = coerceIfNotSubclass($input, "$R_class") %}

%typemap(scoercein) SWIGTYPE  
  %{ $input = coerceIfNotSubclass($input, "$&R_class") %}
*/

%typemap(scoercein) SWIGTYPE[ANY]  
 %{
    if(is.list($input))
      assert(all(sapply($input, class) == "$R_class"));
 %}


/* **************************************************************** */

%typemap(scoercein) bool, bool *, bool & 
		    "$input = as.logical($input);";
%typemap(scoercein) int, 
                    int *, 
		    int &,
                    int[ANY],
		    long,
		    long *,
		    long &,
		    long[ANY]
  "$input = as.integer($input); ";

%typemap(scoercein) char *, string, std::string,
string &, std::string &
%{  $input = as($input, "character"); %}

%typemap(scoerceout) enum SWIGTYPE 
  %{  $result = enumFromInteger($result, "$R_class"); %}

%typemap(scoerceout) enum SWIGTYPE &
  %{  $result = enumFromInteger($result, "$R_class"); %}

%typemap(scoerceout) enum SWIGTYPE *
  %{  $result = enumToInteger($result, "$R_class"); %}

%typemap(scoerceout) enum SWIGTYPE *const
  %{  $result = enumToInteger($result, "$R_class"); %}


%typemap(scoerceout) SWIGTYPE 
  %{ class($result) <- "$&R_class"; %}

%typemap(scoerceout) SWIGTYPE & 
  %{ class($result) <- "$R_class"; %}

%typemap(scoerceout) SWIGTYPE * 
  %{ class($result) <- "$R_class"; %}

%typemap(scoerceout) SWIGTYPE *const
  %{ class($result) <- "$R_class"; %}

/* Override the SWIGTYPE * above. */
%typemap(scoerceout) char,
		     char *,
		     char &,
		     double, 
		     double &,
                     float,
		     float &,
                     int,
		     int &,
		     long,
		     long &,
                     bool,
		     bool &,
		     string,
		     std::string,
		     string &,
		     std::string &, 
		     void,
		     signed int,
		     signed int &,		     
		     unsigned int,
		     unsigned int &,		     
		     short,
		     short &,		     
		     unsigned short,
		     unsigned short &,		     
		     long long,
		     signed long long,
		     signed long long &,		     
		     unsigned long long,
		     unsigned long long &,		     
		     signed long,
		     signed long &,		     
		     unsigned long,
		     unsigned long &		     
 %{    %}


#if 0
 Just examining the values for a SWIGTYPE.

%typemap(scoerceout) SWIGTYPE  %{

  name = $1_name
  type = $1_type
  ltype = $1_ltype

  mangle = $1_mangle
  descriptor = $1_descriptor

  pointer type = $*1_type
  pointer ltype = $*1_ltype

  pointer descriptor = $*1_descriptor
  basetype = $*_basetype

%}
#endif


