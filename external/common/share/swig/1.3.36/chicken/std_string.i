/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * std_string.i
 *
 * SWIG typemaps for std::string
 * ----------------------------------------------------------------------------- */

%{
#include <string>
%}

namespace std {
    %naturalvar string;
  

    %insert(closprefix) %{ (declare (hide <std-string>)) %}
    %nodefault string;
    %rename("std-string") string;
    class string {
      public:
	~string() {}
    };
    %extend string {
      char *str;
    }
    %{
      #define std_string_str_get(s) ((char *)((s)->c_str()))
      #define std_string_str_set(s,v) (s->assign((char *)(v)))
    %}

    %typemap(typecheck) string = char *;
    %typemap(typecheck) const string & = char *;

    %typemap(in) string (char* tempptr) {
      if ($input == C_SCHEME_FALSE) {
	$1.resize(0);
      } else { 
	if (!C_swig_is_string ($input)) {
	  swig_barf (SWIG_BARF1_BAD_ARGUMENT_TYPE, 
		     "Argument #$argnum is not a string");
	}
	tempptr = SWIG_MakeString($input);
	$1.assign(tempptr);
	if (tempptr) SWIG_free(tempptr);
      }
    }

    %typemap(in) const string& (std::string temp,
			 char* tempptr) {

      if ($input == C_SCHEME_FALSE) {
	temp.resize(0);
	$1 = &temp;
      } else { 
	if (!C_swig_is_string ($input)) {
	  swig_barf (SWIG_BARF1_BAD_ARGUMENT_TYPE, 
		     "Argument #$argnum is not a string");
	}
	tempptr = SWIG_MakeString($input);
	temp.assign(tempptr);
	if (tempptr) SWIG_free(tempptr);
	$1 = &temp;
      }
    }

    %typemap(out) string { 
      int size = $1.size();
      C_word *space = C_alloc (C_SIZEOF_STRING (size));
      $result = C_string (&space, size, (char *) $1.c_str());
    }

    %typemap(out) const string& { 
      int size = $1->size();
      C_word *space = C_alloc (C_SIZEOF_STRING (size));
      $result = C_string (&space, size, (char *) $1->c_str());
    }

    %typemap(varin) string {
      if ($input == C_SCHEME_FALSE) {
	$1.resize(0);
      } else { 
        char *tempptr;
	if (!C_swig_is_string ($input)) {
	  swig_barf (SWIG_BARF1_BAD_ARGUMENT_TYPE, 
		     "Argument #$argnum is not a string");
   	}
	tempptr = SWIG_MakeString($input);
	$1.assign(tempptr);
	if (tempptr) SWIG_free(tempptr);
      }
    }

    %typemap(varout) string { 
      int size = $1.size();
      C_word *space = C_alloc (C_SIZEOF_STRING (size));
      $result = C_string (&space, size, (char *) $1.c_str());
    }
}
