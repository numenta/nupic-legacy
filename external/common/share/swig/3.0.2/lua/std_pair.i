/* -----------------------------------------------------------------------------
 * std_pair.i
 *
 * std::pair typemaps for LUA
 * ----------------------------------------------------------------------------- */

%{
#include <utility>
%}
/*
A really cut down version of the pair class.

this is not useful on its own - it needs a %template definition with it

eg.
namespace std {
    %template(IntPair) pair<int, int>;
    %template(make_IntPair) make_pair<int, int>;
}


*/



namespace std {
  template <class T, class U > struct pair {
    typedef T first_type;
    typedef U second_type;

    pair();
    pair(T first, U second);
    pair(const pair& p);

    T first;
    U second;
  };

  template <class T, class U >
  pair<T,U> make_pair(const T&,const U&);

}
