/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * std_string.i
 *
 * SWIG typemaps for std::string
 * ----------------------------------------------------------------------------- */

// ------------------------------------------------------------------------
// std::string is typemapped by value
// This can prevent exporting methods which return a string
// in order for the user to modify it.
// However, I think I'll wait until someone asks for it...
// ------------------------------------------------------------------------

%include <exception.i>

%{
#include <string>
%}

namespace std {

    %naturalvar string;

    class string;

    %typemap(typecheck) string = char *;
    %typemap(typecheck) const string & = char *;

    %typemap(in) string (char* tempptr) {
        if (gh_string_p($input)) {
            tempptr = SWIG_scm2str($input);
            $1.assign(tempptr);
            if (tempptr) SWIG_free(tempptr);
        } else {
            SWIG_exception(SWIG_TypeError, "string expected");
        }
    }

    %typemap(in) const string & (std::string temp,
                                 char* tempptr) {
        if (gh_string_p($input)) {
            tempptr = SWIG_scm2str($input);
            temp.assign(tempptr);
            if (tempptr) SWIG_free(tempptr);
            $1 = &temp;
        } else {
            SWIG_exception(SWIG_TypeError, "string expected");
        }
    }

    %typemap(in) string * (char* tempptr) {
        if (gh_string_p($input)) {
            tempptr = SWIG_scm2str($input);
            $1 = new std::string(tempptr);
            if (tempptr) SWIG_free(tempptr);
        } else {
            SWIG_exception(SWIG_TypeError, "string expected");
        }
    }

    %typemap(out) string {
        $result = gh_str02scm($1.c_str());
    }

    %typemap(out) const string & {
        $result = gh_str02scm($1->c_str());
    }

    %typemap(out) string * {
        $result = gh_str02scm($1->c_str());
    }

    %typemap(varin) string {
        if (gh_string_p($input)) {
	    char *tempptr = SWIG_scm2str($input);
            $1.assign(tempptr);
            if (tempptr) SWIG_free(tempptr);
        } else {
            SWIG_exception(SWIG_TypeError, "string expected");
        }
    }

    %typemap(varout) string {
        $result = gh_str02scm($1.c_str());
    }

}
