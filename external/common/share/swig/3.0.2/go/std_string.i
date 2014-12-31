/* -----------------------------------------------------------------------------
 * std_string.i
 *
 * Typemaps for std::string and const std::string&
 * These are mapped to a Go string and are passed around by value.
 *
 * To use non-const std::string references use the following %apply.  Note 
 * that they are passed by value.
 * %apply const std::string & {std::string &};
 * ----------------------------------------------------------------------------- */

%{
#include <string>
%}

namespace std {

%naturalvar string;

class string;

%typemap(gotype) string, const string & "string"

%typemap(in) string
%{ $1.assign($input.p, $input.n); %}

%typemap(directorout) string
%{ $result.assign($input.p, $input.n); %}

%typemap(out) string
%{ $result = _swig_makegostring($1.data(), $1.length()); %}

%typemap(directorin) string
%{ $input = _swig_makegostring($1.data(), $1.length()); %}

%typemap(in) const string &
%{
  $*1_ltype $1_str($input.p, $input.n);
  $1 = &$1_str;
%}

%typemap(directorout,warning=SWIGWARN_TYPEMAP_THREAD_UNSAFE_MSG) const string &
%{
  static $*1_ltype $1_str;
  $1_str.assign($input.p, $input.n);
  $result = &$1_str;
%}

%typemap(out) const string &
%{ $result = _swig_makegostring((*$1).data(), (*$1).length()); %}

%typemap(directorin) const string &
%{ $input = _swig_makegostring($1.data(), $1.length()); %}

}
