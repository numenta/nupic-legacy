/* -----------------------------------------------------------------------------
 * See the LICENSE file for information on copyright, usage and redistribution
 * of SWIG, and the README file for authors - http://www.swig.org/release.html.
 *
 * std_pair.i
 *
 * SWIG typemaps for std::pair
 * ----------------------------------------------------------------------------- */

%include <std_common.i>
%include <exception.i>

// ------------------------------------------------------------------------
// std::pair
// ------------------------------------------------------------------------

%{
#include <utility>
%}

namespace std {

  template<class T, class U> struct pair {

    pair();
    pair(T first, U second);
    pair(const pair& p);

    template <class U1, class U2> pair(const pair<U1, U2> &p);

    T first;
    U second;
  };

  // add specializations here

}
