/* -----------------------------------------------------------------------------
 * std_string.i
 *
 * SWIG typemaps for std::string
 * ----------------------------------------------------------------------------- */

%{
#include <string>
%}

namespace std {

    %naturalvar string;

    class string;

    /* Overloading check */

    %typemap(typecheck) string = char *;
    %typemap(typecheck) const string & = char *;

    %typemap(in, pikedesc="tStr") string {
      if ($input.type != T_STRING)
        Pike_error("Bad argument: Expected a string.\n");
      $1.assign(STR0($input.u.string));
    }

    %typemap(in, pikedesc="tStr") const string & (std::string temp) {
      if ($input.type != T_STRING)
        Pike_error("Bad argument: Expected a string.\n");
      temp.assign(STR0($input.u.string));
      $1 = &temp;
    }

    %typemap(out, pikedesc="tStr") string "push_text($1.c_str());";

    %typemap(out, pikedesc="tStr") const string & "push_text($1->c_str());";
    
    %typemap(directorin) string, const string &, string & "$1_name.c_str()";

    %typemap(directorin) string *, const string * "$1_name->c_str()";
    
    %typemap(directorout) string {
      if ($input.type == T_STRING)
        $result.assign(STR0($input.u.string));
      else
        throw Swig::DirectorTypeMismatchException("string expected");
    }
    
    %typemap(directorout) const string & (std::string temp) {
      if ($input.type == T_STRING) {
        temp.assign(STR0($input.u.string));
        $result = &temp;
      } else {
        throw Swig::DirectorTypeMismatchException("string expected");
      }
    }

}

