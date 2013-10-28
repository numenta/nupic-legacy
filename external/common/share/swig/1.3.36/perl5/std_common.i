/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * std_common.i
 *
 * SWIG typemaps for STL - common utilities
 * ----------------------------------------------------------------------------- */

%include <std/std_except.i>

%apply size_t { std::size_t };

%{
#include <string>

double SwigSvToNumber(SV* sv) {
    return SvIOK(sv) ? double(SvIVX(sv)) : SvNVX(sv);
}
std::string SwigSvToString(SV* sv) {
    STRLEN len;
    char *ptr = SvPV(sv, len);
    return std::string(ptr, len);
}
void SwigSvFromString(SV* sv, const std::string& s) {
    sv_setpvn(sv,s.data(),s.size());
}
%}

