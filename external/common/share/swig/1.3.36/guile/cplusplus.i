/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * cplusplus.i
 *
 * SWIG typemaps for C++
 * ----------------------------------------------------------------------------- */

%typemap(guile,out) string, std::string {
  $result = gh_str02scm(const_cast<char*>($1.c_str()));
}
%typemap(guile,in) string, std::string {
  $1 = SWIG_scm2str($input);
}

%typemap(guile,out) complex, complex<double>, std::complex<double> {
  $result = scm_make_rectangular( gh_double2scm ($1.real ()),
           gh_double2scm ($1.imag ()) );
}
%typemap(guile,in) complex, complex<double>, std::complex<double> {
  $1 = std::complex<double>( gh_scm2double (scm_real_part ($input)),
           gh_scm2double (scm_imag_part ($input)) );
}

