/* -----------------------------------------------------------------------------
 * std_pair.i
 *
 * SWIG typemaps for std::pair
 * ----------------------------------------------------------------------------- */

%include <std_common.i>
%include <exception.i>

// ------------------------------------------------------------------------
// std::pair
//
// See std_vector.i for the rationale of typemap application
// ------------------------------------------------------------------------

%{
#include <utility>
%}

// exported class

namespace std {

    template<class T, class U> struct pair {
        %typemap(in) pair<T,U> (std::pair<T,U>* m) {
            if (gh_pair_p($input)) {
                T* x;
                U* y;
                SCM first, second;
                first = gh_car($input);
                second = gh_cdr($input);
                x = (T*) SWIG_MustGetPtr(first,$descriptor(T *),$argnum, 0);
                y = (U*) SWIG_MustGetPtr(second,$descriptor(U *),$argnum, 0);
                $1 = std::make_pair(*x,*y);
            } else {
                $1 = *(($&1_type)
                       SWIG_MustGetPtr($input,$&1_descriptor,$argnum, 0));
            }
        }
        %typemap(in) const pair<T,U>& (std::pair<T,U> temp,
                                      std::pair<T,U>* m),
                     const pair<T,U>* (std::pair<T,U> temp,
                                      std::pair<T,U>* m) {
            if (gh_pair_p($input)) {
                T* x;
                U* y;
                SCM first, second;
                first = gh_car($input);
                second = gh_cdr($input);
                x = (T*) SWIG_MustGetPtr(first,$descriptor(T *),$argnum, 0);
                y = (U*) SWIG_MustGetPtr(second,$descriptor(U *),$argnum, 0);
                temp = std::make_pair(*x,*y);
                $1 = &temp;
            } else {
                $1 = ($1_ltype)
                    SWIG_MustGetPtr($input,$1_descriptor,$argnum, 0);
            }
        }
        %typemap(out) pair<T,U> {
            T* x = new T($1.first);
            U* y = new U($1.second);
            SCM first = SWIG_NewPointerObj(x,$descriptor(T *), 1);
            SCM second = SWIG_NewPointerObj(y,$descriptor(U *), 1);
            $result = gh_cons(first,second);
        }
        %typecheck(SWIG_TYPECHECK_PAIR) pair<T,U> {
            /* native pair? */
            if (gh_pair_p($input)) {
                T* x;
                U* y;
                SCM first = gh_car($input);
                SCM second = gh_cdr($input);
                if (SWIG_ConvertPtr(first,(void**) &x,
                                    $descriptor(T *), 0) == 0 &&
                    SWIG_ConvertPtr(second,(void**) &y,
                                    $descriptor(U *), 0) == 0) {
                    $1 = 1;
                } else {
                    $1 = 0;
                }
            } else {
                /* wrapped pair? */
                std::pair<T,U >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                    $&1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %typecheck(SWIG_TYPECHECK_PAIR) const pair<T,U>&,
                                        const pair<T,U>* {
            /* native pair? */
            if (gh_pair_p($input)) {
                T* x;
                U* y;
                SCM first = gh_car($input);
                SCM second = gh_cdr($input);
                if (SWIG_ConvertPtr(first,(void**) &x,
                                    $descriptor(T *), 0) == 0 &&
                    SWIG_ConvertPtr(second,(void**) &y,
                                    $descriptor(U *), 0) == 0) {
                    $1 = 1;
                } else {
                    $1 = 0;
                }
            } else {
                /* wrapped pair? */
                std::pair<T,U >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                    $1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        pair();
        pair(T first, U second);
        pair(const pair& p);

        template <class U1, class U2> pair(const pair<U1, U2> &p);

        T first;
        U second;
    };


    // specializations for built-ins

    %define specialize_std_pair_on_first(T,CHECK,CONVERT_FROM,CONVERT_TO)
    template<class U> struct pair<T,U> {
        %typemap(in) pair<T,U> (std::pair<T,U>* m) {
            if (gh_pair_p($input)) {
                U* y;
                SCM first, second;
                first = gh_car($input);
                second = gh_cdr($input);
                if (!CHECK(first))
                    SWIG_exception(SWIG_TypeError,
                                   "map<" #T "," #U "> expected");
                y = (U*) SWIG_MustGetPtr(second,$descriptor(U *),$argnum, 0);
                $1 = std::make_pair(CONVERT_FROM(first),*y);
            } else {
                $1 = *(($&1_type)
                       SWIG_MustGetPtr($input,$&1_descriptor,$argnum, 0));
            }
        }
        %typemap(in) const pair<T,U>& (std::pair<T,U> temp,
                                       std::pair<T,U>* m),
                     const pair<T,U>* (std::pair<T,U> temp,
                                       std::pair<T,U>* m) {
            if (gh_pair_p($input)) {
                U* y;
                SCM first, second;
                first = gh_car($input);
                second = gh_cdr($input);
                if (!CHECK(first))
                    SWIG_exception(SWIG_TypeError,
                                   "map<" #T "," #U "> expected");
                y = (U*) SWIG_MustGetPtr(second,$descriptor(U *),$argnum, 0);
                temp = std::make_pair(CONVERT_FROM(first),*y);
                $1 = &temp;
            } else {
                $1 = ($1_ltype)
                    SWIG_MustGetPtr($input,$1_descriptor,$argnum, 0);
            }
        }
        %typemap(out) pair<T,U> {
            U* y = new U($1.second);
            SCM second = SWIG_NewPointerObj(y,$descriptor(U *), 1);
            $result = gh_cons(CONVERT_TO($1.first),second);
        }
        %typecheck(SWIG_TYPECHECK_PAIR) pair<T,U> {
            /* native pair? */
            if (gh_pair_p($input)) {
                U* y;
                SCM first = gh_car($input);
                SCM second = gh_cdr($input);
                if (CHECK(first) &&
                    SWIG_ConvertPtr(second,(void**) &y,
                                    $descriptor(U *), 0) == 0) {
                    $1 = 1;
                } else {
                    $1 = 0;
                }
            } else {
                /* wrapped pair? */
                std::pair<T,U >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                    $&1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %typecheck(SWIG_TYPECHECK_PAIR) const pair<T,U>&,
                                        const pair<T,U>* {
            /* native pair? */
            if (gh_pair_p($input)) {
                U* y;
                SCM first = gh_car($input);
                SCM second = gh_cdr($input);
                if (CHECK(first) &&
                    SWIG_ConvertPtr(second,(void**) &y,
                                    $descriptor(U *), 0) == 0) {
                    $1 = 1;
                } else {
                    $1 = 0;
                }
            } else {
                /* wrapped pair? */
                std::pair<T,U >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                    $1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        pair();
        pair(T first, U second);
        pair(const pair& p);

        template <class U1, class U2> pair(const pair<U1, U2> &p);

        T first;
        U second;
    };
    %enddef

    %define specialize_std_pair_on_second(U,CHECK,CONVERT_FROM,CONVERT_TO)
    template<class T> struct pair<T,U> {
        %typemap(in) pair<T,U> (std::pair<T,U>* m) {
            if (gh_pair_p($input)) {
                T* x;
                SCM first, second;
                first = gh_car($input);
                second = gh_cdr($input);
                x = (T*) SWIG_MustGetPtr(first,$descriptor(T *),$argnum, 0);
                if (!CHECK(second))
                    SWIG_exception(SWIG_TypeError,
                                   "map<" #T "," #U "> expected");
                $1 = std::make_pair(*x,CONVERT_FROM(second));
            } else {
                $1 = *(($&1_type)
                       SWIG_MustGetPtr($input,$&1_descriptor,$argnum, 0));
            }
        }
        %typemap(in) const pair<T,U>& (std::pair<T,U> temp,
                                      std::pair<T,U>* m),
                     const pair<T,U>* (std::pair<T,U> temp,
                                      std::pair<T,U>* m) {
            if (gh_pair_p($input)) {
                T* x;
                SCM first, second;
                first = gh_car($input);
                second = gh_cdr($input);
                x = (T*) SWIG_MustGetPtr(first,$descriptor(T *),$argnum, 0);
                if (!CHECK(second))
                    SWIG_exception(SWIG_TypeError,
                                   "map<" #T "," #U "> expected");
                temp = std::make_pair(*x,CONVERT_FROM(second));
                $1 = &temp;
            } else {
                $1 = ($1_ltype)
                    SWIG_MustGetPtr($input,$1_descriptor,$argnum, 0);
            }
        }
        %typemap(out) pair<T,U> {
            T* x = new T($1.first);
            SCM first = SWIG_NewPointerObj(x,$descriptor(T *), 1);
            $result = gh_cons(first,CONVERT_TO($1.second));
        }
        %typecheck(SWIG_TYPECHECK_PAIR) pair<T,U> {
            /* native pair? */
            if (gh_pair_p($input)) {
                T* x;
                SCM first = gh_car($input);
                SCM second = gh_cdr($input);
                if (SWIG_ConvertPtr(first,(void**) &x,
                                    $descriptor(T *), 0) == 0 &&
                    CHECK(second)) {
                    $1 = 1;
                } else {
                    $1 = 0;
                }
            } else {
                /* wrapped pair? */
                std::pair<T,U >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                    $&1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %typecheck(SWIG_TYPECHECK_PAIR) const pair<T,U>&,
                                        const pair<T,U>* {
            /* native pair? */
            if (gh_pair_p($input)) {
                T* x;
                SCM first = gh_car($input);
                SCM second = gh_cdr($input);
                if (SWIG_ConvertPtr(first,(void**) &x,
                                    $descriptor(T *), 0) == 0 &&
                    CHECK(second)) {
                    $1 = 1;
                } else {
                    $1 = 0;
                }
            } else {
                /* wrapped pair? */
                std::pair<T,U >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                    $1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        pair();
        pair(T first, U second);
        pair(const pair& p);

        template <class U1, class U2> pair(const pair<U1, U2> &p);

        T first;
        U second;
    };
    %enddef

    %define specialize_std_pair_on_both(T,CHECK_T,CONVERT_T_FROM,CONVERT_T_TO,
                                        U,CHECK_U,CONVERT_U_FROM,CONVERT_U_TO)
    template<> struct pair<T,U> {
        %typemap(in) pair<T,U> (std::pair<T,U>* m) {
            if (gh_pair_p($input)) {
                SCM first, second;
                first = gh_car($input);
                second = gh_cdr($input);
                if (!CHECK_T(first) || !CHECK_U(second))
                    SWIG_exception(SWIG_TypeError,
                                   "map<" #T "," #U "> expected");
                $1 = std::make_pair(CONVERT_T_FROM(first),
                                    CONVERT_U_FROM(second));
            } else {
                $1 = *(($&1_type)
                       SWIG_MustGetPtr($input,$&1_descriptor,$argnum, 0));
            }
        }
        %typemap(in) const pair<T,U>& (std::pair<T,U> temp,
                                      std::pair<T,U>* m),
                     const pair<T,U>* (std::pair<T,U> temp,
                                      std::pair<T,U>* m) {
            if (gh_pair_p($input)) {
                SCM first, second;
                first = gh_car($input);
                second = gh_cdr($input);
                if (!CHECK_T(first) || !CHECK_U(second))
                    SWIG_exception(SWIG_TypeError,
                                   "map<" #T "," #U "> expected");
                temp = std::make_pair(CONVERT_T_FROM(first),
                                      CONVERT_U_FROM(second));
                $1 = &temp;
            } else {
                $1 = ($1_ltype)
                    SWIG_MustGetPtr($input,$1_descriptor,$argnum, 0);
            }
        }
        %typemap(out) pair<T,U> {
            $result = gh_cons(CONVERT_T_TO($1.first),
                              CONVERT_U_TO($1.second));
        }
        %typecheck(SWIG_TYPECHECK_PAIR) pair<T,U> {
            /* native pair? */
            if (gh_pair_p($input)) {
                SCM first = gh_car($input);
                SCM second = gh_cdr($input);
                if (CHECK_T(first) && CHECK_U(second)) {
                    $1 = 1;
                } else {
                    $1 = 0;
                }
            } else {
                /* wrapped pair? */
                std::pair<T,U >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                    $&1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %typecheck(SWIG_TYPECHECK_PAIR) const pair<T,U>&,
                                        const pair<T,U>* {
            /* native pair? */
            if (gh_pair_p($input)) {
                SCM first = gh_car($input);
                SCM second = gh_cdr($input);
                if (CHECK_T(first) && CHECK_U(second)) {
                    $1 = 1;
                } else {
                    $1 = 0;
                }
            } else {
                /* wrapped pair? */
                std::pair<T,U >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                    $1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        pair();
        pair(T first, U second);
        pair(const pair& p);

        template <class U1, class U2> pair(const pair<U1, U2> &p);

        T first;
        U second;
    };
    %enddef


    specialize_std_pair_on_first(bool,gh_boolean_p,
                              gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_first(int,gh_number_p,
                              gh_scm2long,gh_long2scm);
    specialize_std_pair_on_first(short,gh_number_p,
                              gh_scm2long,gh_long2scm);
    specialize_std_pair_on_first(long,gh_number_p,
                              gh_scm2long,gh_long2scm);
    specialize_std_pair_on_first(unsigned int,gh_number_p,
                              gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_first(unsigned short,gh_number_p,
                              gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_first(unsigned long,gh_number_p,
                              gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_first(double,gh_number_p,
                              gh_scm2double,gh_double2scm);
    specialize_std_pair_on_first(float,gh_number_p,
                              gh_scm2double,gh_double2scm);
    specialize_std_pair_on_first(std::string,gh_string_p,
                              SWIG_scm2string,SWIG_string2scm);

    specialize_std_pair_on_second(bool,gh_boolean_p,
                                gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_second(int,gh_number_p,
                                gh_scm2long,gh_long2scm);
    specialize_std_pair_on_second(short,gh_number_p,
                                gh_scm2long,gh_long2scm);
    specialize_std_pair_on_second(long,gh_number_p,
                                gh_scm2long,gh_long2scm);
    specialize_std_pair_on_second(unsigned int,gh_number_p,
                                gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_second(unsigned short,gh_number_p,
                                gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_second(unsigned long,gh_number_p,
                                gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_second(double,gh_number_p,
                                gh_scm2double,gh_double2scm);
    specialize_std_pair_on_second(float,gh_number_p,
                                gh_scm2double,gh_double2scm);
    specialize_std_pair_on_second(std::string,gh_string_p,
                                SWIG_scm2string,SWIG_string2scm);

    specialize_std_pair_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_pair_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_pair_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_pair_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_pair_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_pair_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_pair_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_pair_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_pair_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_pair_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_pair_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_pair_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_pair_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_pair_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
}
