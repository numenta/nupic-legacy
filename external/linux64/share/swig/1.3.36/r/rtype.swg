
/* These map the primitive C types to the appropriate R type
   for use in class representations. 
 */

%typemap("rtype") int, int *, int &      "numeric";
%apply int {size_t}
%apply int {std::size_t}
%apply int {ptrdiff_t}
%apply int {std::ptrdiff_t}

%typemap("rtype") long, long *    "numeric";
%typemap("rtype") unsigned long, 
                  unsigned long * "numeric";
%typemap("rtype") unsigned int, 
                  unsigned int *  "numeric";
%typemap("rtype") double, double*, double & "numeric";
%typemap("rtype") float, float *, float &  "numeric";
%typemap("rtype") char *, char ** "character";
%typemap("rtype") char            "character";
%typemap("rtype") string, string *, string & "character";
%typemap("rtype") std::string, std::string *, std::string & "character";
%typemap("rtype") bool, bool *    "logical";
%typemap("rtype") enum SWIGTYPE   "character";
%typemap("rtype") enum SWIGTYPE *   "character";
%typemap("rtype") enum SWIGTYPE &  "character";
%typemap("rtype") SWIGTYPE * "$R_class";
%typemap("rtype") SWIGTYPE & "$R_class";
%typemap("rtype") SWIGTYPE "$&R_class";



/* Have to be careful that as(x, "numeric") is different from as.numeric(x).  
   The latter makes a REALSXP, whereas the former leaves an INTSXP as an
   INTSXP.
*/


%typemap(scoercein) int, int *, int &
  %{  $input = as($input, "integer");     %}
%typemap(scoercein) ptrdiff_t, ptrdiff_t *, ptrdiff_t &
  %{  $input = as($input, "integer");     %}
%typemap(scoercein) unsigned long, unsigned long *, unsigned long &
  %{  $input = as($input, "integer");     %}
%typemap(scoercein) unsigned int, unsigned int *, unsigned int &
  %{  $input = as($input, "integer");     %}
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
  %{  $input = enumToInteger($input, "$R_class") %}
%typemap(scoercein) enum SWIGTYPE &
  %{  $input = enumToInteger($input, "$R_class") %}
%typemap(scoercein) enum SWIGTYPE *
  %{  $input = enumToInteger($input, "$R_class") %}


%typemap(scoercein) SWIGTYPE, SWIGTYPE *, SWIGTYPE &  
  %{ %}

/*
%typemap(scoercein) SWIGTYPE * 
  %{ $input = coerceIfNotSubclass($input, "$R_class") %}

%typemap(scoercein) SWIGTYPE & 
  %{ $input = coerceIfNotSubclass($input, "$R_class") %}

%typemap(scoercein) SWIGTYPE  
  %{ $input = coerceIfNotSubclass($input, "$&R_class") %}
*/

%typemap(scoercein) SWIGTYPE[ANY]  
 %{
    if(is.list($input))
      assert(all(sapply($input, class) == "$R_class"))     
 %}


/* **************************************************************** */

%typemap(scoercein) bool, bool *, bool & 
		    "$input = as.logical($input) ";
/*
%typemap(scoercein) int, 
                    int *, 
		    int &,
                    int[ANY],
		    size_t,
		    std::size_t,
		    size_t &,
		    std::size_t &
  "$input = as.integer($input) ";


%typemap(scoercein) unsigned int, 
                    unsigned long,
                    double, 
                    float,
                    long,
                    long long,
     	            unsigned int[], 
                    unsigned long[],
                    double[], 
                    float[],
                    long[],
                    long long[],
     	            unsigned int[ANY], 
                    unsigned long[ANY],
                    double[ANY], 
                    float[ANY],
                    long[ANY],
                    long long[ANY],
     	            unsigned int *, 
                    unsigned long *,
                    double*, 
                    float*,
                    long*,
                    long long *
%{  $input = as.numeric($input) %}
*/

%typemap(scoercein) char *, string, std::string,
string &, std::string &
%{  $input = as($input, "character") %}

%typemap(scoerceout) enum SWIGTYPE 
  %{  $result = enumFromInteger($result, "$R_class") %}

%typemap(scoerceout) enum SWIGTYPE &
  %{  $result = enumFromInteger($result, "$R_class") %}

%typemap(scoerceout) enum SWIGTYPE *
  %{  $result = enumToInteger($result, "$R_class") %}


%typemap(scoerceout) SWIGTYPE 
  %{ class($result) <- "$&R_class" %}

%typemap(scoerceout) SWIGTYPE & 
  %{ class($result) <- "$R_class" %}

%typemap(scoerceout) SWIGTYPE * 
  %{ class($result) <- "$R_class" %}

/* Override the SWIGTYPE * above. */
%typemap(scoerceout) char,
		     char *,
		     char &,
		     unsigned int, 
		     unsigned int &, 
                     unsigned long,
                     unsigned long &,
		     double, 
		     double &,
                     float,
		     float &,
                     long,
		     long &,
                     long long,
		     long long &,
                     int,
		     int &,
                     bool,
		     bool &,
		     string,
		     std::string,
		     string &,
		     std::string &, 
		     size_t,
		     std::size_t,
		     size_t &,
		     std::size_t &,
		     void
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


