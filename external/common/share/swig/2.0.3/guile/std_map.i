/* -----------------------------------------------------------------------------
 * std_map.i
 *
 * SWIG typemaps for std::map
 * ----------------------------------------------------------------------------- */

%include <std_common.i>

// ------------------------------------------------------------------------
// std::map
//
// The aim of all that follows would be to integrate std::map with
// Guile as much as possible, namely, to allow the user to pass and
// be returned Scheme association lists.
// const declarations are used to guess the intent of the function being
// exported; therefore, the following rationale is applied:
//
//   -- f(std::map<T>), f(const std::map<T>&), f(const std::map<T>*):
//      the parameter being read-only, either a Scheme alist or a
//      previously wrapped std::map<T> can be passed.
//   -- f(std::map<T>&), f(std::map<T>*):
//      the parameter must be modified; therefore, only a wrapped std::map
//      can be passed.
//   -- std::map<T> f():
//      the map is returned by copy; therefore, a Scheme alist
//      is returned which is most easily used in other Scheme functions
//   -- std::map<T>& f(), std::map<T>* f(), const std::map<T>& f(),
//      const std::map<T>* f():
//      the map is returned by reference; therefore, a wrapped std::map
//      is returned
// ------------------------------------------------------------------------

%{
#include <map>
#include <algorithm>
#include <stdexcept>
%}

// exported class

namespace std {

    template<class K, class T> class map {
        %typemap(in) map<K,T> (std::map<K,T>* m) {
            if (gh_null_p($input)) {
                $1 = std::map<K,T >();
            } else if (gh_pair_p($input)) {
                $1 = std::map<K,T >();
                SCM alist = $input;
                while (!gh_null_p(alist)) {
                    K* k;
                    T* x;
                    SCM entry, key, val;
                    entry = gh_car(alist);
                    if (!gh_pair_p(entry))
                        SWIG_exception(SWIG_TypeError,"alist expected");
                    key = gh_car(entry);
                    val = gh_cdr(entry);
                    k = (K*) SWIG_MustGetPtr(key,$descriptor(K *),$argnum, 0);
                    if (SWIG_ConvertPtr(val,(void**) &x,
                                    $descriptor(T *), 0) != 0) {
                        if (!gh_pair_p(val))
                            SWIG_exception(SWIG_TypeError,"alist expected");
                        val = gh_car(val);
                        x = (T*) SWIG_MustGetPtr(val,$descriptor(T *),$argnum, 0);
                    }
                    (($1_type &)$1)[*k] = *x;
                    alist = gh_cdr(alist);
                }
            } else {
                $1 = *(($&1_type)
                       SWIG_MustGetPtr($input,$&1_descriptor,$argnum, 0));
            }
        }
        %typemap(in) const map<K,T>& (std::map<K,T> temp,
                                      std::map<K,T>* m),
                     const map<K,T>* (std::map<K,T> temp,
                                      std::map<K,T>* m) {
            if (gh_null_p($input)) {
                temp = std::map<K,T >();
                $1 = &temp;
            } else if (gh_pair_p($input)) {
                temp = std::map<K,T >();
                $1 = &temp;
                SCM alist = $input;
                while (!gh_null_p(alist)) {
                    K* k;
                    T* x;
                    SCM entry, key, val;
                    entry = gh_car(alist);
                    if (!gh_pair_p(entry))
                        SWIG_exception(SWIG_TypeError,"alist expected");
                    key = gh_car(entry);
                    val = gh_cdr(entry);
                    k = (K*) SWIG_MustGetPtr(key,$descriptor(K *),$argnum, 0);
                    if (SWIG_ConvertPtr(val,(void**) &x,
                                    $descriptor(T *), 0) != 0) {
                        if (!gh_pair_p(val))
                            SWIG_exception(SWIG_TypeError,"alist expected");
                        val = gh_car(val);
                        x = (T*) SWIG_MustGetPtr(val,$descriptor(T *),$argnum, 0);
                    }
                    temp[*k] = *x;
                    alist = gh_cdr(alist);
                }
            } else {
                $1 = ($1_ltype) SWIG_MustGetPtr($input,$1_descriptor,$argnum, 0);
            }
        }
        %typemap(out) map<K,T> {
            SCM alist = SCM_EOL;
            for (std::map<K,T >::reverse_iterator i=$1.rbegin(); 
                                                  i!=$1.rend(); ++i) {
                K* key = new K(i->first);
                T* val = new T(i->second);
                SCM k = SWIG_NewPointerObj(key,$descriptor(K *), 1);
                SCM x = SWIG_NewPointerObj(val,$descriptor(T *), 1);
                SCM entry = gh_cons(k,x);
                alist = gh_cons(entry,alist);
            }
            $result = alist;
        }
        %typecheck(SWIG_TYPECHECK_MAP) map<K,T> {
            /* native sequence? */
            if (gh_null_p($input)) {
                /* an empty sequence can be of any type */
                $1 = 1;
            } else if (gh_pair_p($input)) {
                /* check the first element only */
                K* k;
                T* x;
                SCM head = gh_car($input);
                if (gh_pair_p(head)) {
                    SCM key = gh_car(head);
                    SCM val = gh_cdr(head);
                    if (SWIG_ConvertPtr(key,(void**) &k,
                                    $descriptor(K *), 0) != 0) {
                        $1 = 0;
                    } else {
                        if (SWIG_ConvertPtr(val,(void**) &x,
                                        $descriptor(T *), 0) == 0) {
                            $1 = 1;
                        } else if (gh_pair_p(val)) {
                            val = gh_car(val);
                            if (SWIG_ConvertPtr(val,(void**) &x,
                                            $descriptor(T *), 0) == 0)
                                $1 = 1;
                            else
                                $1 = 0;
                        } else {
                            $1 = 0;
                        }
                    }
                } else {
                    $1 = 0;
                }
            } else {
                /* wrapped map? */
                std::map<K,T >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                $&1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %typecheck(SWIG_TYPECHECK_MAP) const map<K,T>&,
                                       const map<K,T>* {
            /* native sequence? */
            if (gh_null_p($input)) {
                /* an empty sequence can be of any type */
                $1 = 1;
            } else if (gh_pair_p($input)) {
                /* check the first element only */
                K* k;
                T* x;
                SCM head = gh_car($input);
                if (gh_pair_p(head)) {
                    SCM key = gh_car(head);
                    SCM val = gh_cdr(head);
                    if (SWIG_ConvertPtr(key,(void**) &k,
                                    $descriptor(K *), 0) != 0) {
                        $1 = 0;
                    } else {
                        if (SWIG_ConvertPtr(val,(void**) &x,
                                        $descriptor(T *), 0) == 0) {
                            $1 = 1;
                        } else if (gh_pair_p(val)) {
                            val = gh_car(val);
                            if (SWIG_ConvertPtr(val,(void**) &x,
                                            $descriptor(T *), 0) == 0)
                                $1 = 1;
                            else
                                $1 = 0;
                        } else {
                            $1 = 0;
                        }
                    }
                } else {
                    $1 = 0;
                }
            } else {
                /* wrapped map? */
                std::map<K,T >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                $1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %rename("length") size;
        %rename("null?") empty;
        %rename("clear!") clear;
        %rename("ref") __getitem__;
        %rename("set!") __setitem__;
        %rename("delete!") __delitem__;
        %rename("has-key?") has_key;
      public:
        map();
        map(const map<K,T> &);
        
        unsigned int size() const;
        bool empty() const;
        void clear();
        %extend {
            const T& __getitem__(const K& key) throw (std::out_of_range) {
                std::map<K,T >::iterator i = self->find(key);
                if (i != self->end())
                    return i->second;
                else
                    throw std::out_of_range("key not found");
            }
            void __setitem__(const K& key, const T& x) {
                (*self)[key] = x;
            }
            void __delitem__(const K& key) throw (std::out_of_range) {
                std::map<K,T >::iterator i = self->find(key);
                if (i != self->end())
                    self->erase(i);
                else
                    throw std::out_of_range("key not found");
            }
            bool has_key(const K& key) {
                std::map<K,T >::iterator i = self->find(key);
                return i != self->end();
            }
            SCM keys() {
                SCM result = SCM_EOL;
                for (std::map<K,T >::reverse_iterator i=$1.rbegin(); 
                                                      i!=$1.rend(); ++i) {
                    K* key = new K(i->first);
                    SCM k = SWIG_NewPointerObj(key,$descriptor(K *), 1);
                    result = gh_cons(k,result);
                }
                return result;
            }
        }
    };


    // specializations for built-ins

    %define specialize_std_map_on_key(K,CHECK,CONVERT_FROM,CONVERT_TO)

    template<class T> class map<K,T> {
        %typemap(in) map<K,T> (std::map<K,T>* m) {
            if (gh_null_p($input)) {
                $1 = std::map<K,T >();
            } else if (gh_pair_p($input)) {
                $1 = std::map<K,T >();
                SCM alist = $input;
                while (!gh_null_p(alist)) {
                    T* x;
                    SCM entry, key, val;
                    entry = gh_car(alist);
                    if (!gh_pair_p(entry))
                        SWIG_exception(SWIG_TypeError,"alist expected");
                    key = gh_car(entry);
                    val = gh_cdr(entry);
                    if (!CHECK(key))
                        SWIG_exception(SWIG_TypeError,
                                       "map<" #K "," #T "> expected");
                    if (SWIG_ConvertPtr(val,(void**) &x,
                                    $descriptor(T *), 0) != 0) {
                        if (!gh_pair_p(val))
                            SWIG_exception(SWIG_TypeError,"alist expected");
                        val = gh_car(val);
                        x = (T*) SWIG_MustGetPtr(val,$descriptor(T *),$argnum, 0);
                    }
                    (($1_type &)$1)[CONVERT_FROM(key)] = *x;
                    alist = gh_cdr(alist);
                }
            } else {
                $1 = *(($&1_type)
                       SWIG_MustGetPtr($input,$&1_descriptor,$argnum, 0));
            }
        }
        %typemap(in) const map<K,T>& (std::map<K,T> temp,
                                      std::map<K,T>* m),
                     const map<K,T>* (std::map<K,T> temp,
                                      std::map<K,T>* m) {
            if (gh_null_p($input)) {
                temp = std::map<K,T >();
                $1 = &temp;
            } else if (gh_pair_p($input)) {
                temp = std::map<K,T >();
                $1 = &temp;
                SCM alist = $input;
                while (!gh_null_p(alist)) {
                    T* x;
                    SCM entry, key, val;
                    entry = gh_car(alist);
                    if (!gh_pair_p(entry))
                        SWIG_exception(SWIG_TypeError,"alist expected");
                    key = gh_car(entry);
                    val = gh_cdr(entry);
                    if (!CHECK(key))
                        SWIG_exception(SWIG_TypeError,
                                       "map<" #K "," #T "> expected");
                    if (SWIG_ConvertPtr(val,(void**) &x,
                                    $descriptor(T *), 0) != 0) {
                        if (!gh_pair_p(val))
                            SWIG_exception(SWIG_TypeError,"alist expected");
                        val = gh_car(val);
                        x = (T*) SWIG_MustGetPtr(val,$descriptor(T *),$argnum, 0);
                    }
                    temp[CONVERT_FROM(key)] = *x;
                    alist = gh_cdr(alist);
                }
            } else {
                $1 = ($1_ltype) SWIG_MustGetPtr($input,$1_descriptor,$argnum, 0);
            }
        }
        %typemap(out) map<K,T> {
            SCM alist = SCM_EOL;
            for (std::map<K,T >::reverse_iterator i=$1.rbegin(); 
                                                  i!=$1.rend(); ++i) {
                T* val = new T(i->second);
                SCM k = CONVERT_TO(i->first);
                SCM x = SWIG_NewPointerObj(val,$descriptor(T *), 1);
                SCM entry = gh_cons(k,x);
                alist = gh_cons(entry,alist);
            }
            $result = alist;
        }
        %typecheck(SWIG_TYPECHECK_MAP) map<K,T> {
            // native sequence?
            if (gh_null_p($input)) {
                /* an empty sequence can be of any type */
                $1 = 1;
            } else if (gh_pair_p($input)) {
                // check the first element only
                T* x;
                SCM head = gh_car($input);
                if (gh_pair_p(head)) {
                    SCM key = gh_car(head);
                    SCM val = gh_cdr(head);
                    if (!CHECK(key)) {
                        $1 = 0;
                    } else {
                        if (SWIG_ConvertPtr(val,(void**) &x,
                                        $descriptor(T *), 0) == 0) {
                            $1 = 1;
                        } else if (gh_pair_p(val)) {
                            val = gh_car(val);
                            if (SWIG_ConvertPtr(val,(void**) &x,
                                            $descriptor(T *), 0) == 0)
                                $1 = 1;
                            else
                                $1 = 0;
                        } else {
                            $1 = 0;
                        }
                    }
                } else {
                    $1 = 0;
                }
            } else {
                // wrapped map?
                std::map<K,T >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                $&1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %typecheck(SWIG_TYPECHECK_MAP) const map<K,T>&,
                                       const map<K,T>* {
            // native sequence?
            if (gh_null_p($input)) {
                /* an empty sequence can be of any type */
                $1 = 1;
            } else if (gh_pair_p($input)) {
                // check the first element only
                T* x;
                SCM head = gh_car($input);
                if (gh_pair_p(head)) {
                    SCM key = gh_car(head);
                    SCM val = gh_cdr(head);
                    if (!CHECK(key)) {
                        $1 = 0;
                    } else {
                        if (SWIG_ConvertPtr(val,(void**) &x,
                                        $descriptor(T *), 0) == 0) {
                            $1 = 1;
                        } else if (gh_pair_p(val)) {
                            val = gh_car(val);
                            if (SWIG_ConvertPtr(val,(void**) &x,
                                            $descriptor(T *), 0) == 0)
                                $1 = 1;
                            else
                                $1 = 0;
                        } else {
                            $1 = 0;
                        }
                    }
                } else {
                    $1 = 0;
                }
            } else {
                // wrapped map?
                std::map<K,T >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                $1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %rename("length") size;
        %rename("null?") empty;
        %rename("clear!") clear;
        %rename("ref") __getitem__;
        %rename("set!") __setitem__;
        %rename("delete!") __delitem__;
        %rename("has-key?") has_key;
      public:
        map();
        map(const map<K,T> &);
        
        unsigned int size() const;
        bool empty() const;
        void clear();
        %extend {
            T& __getitem__(K key) throw (std::out_of_range) {
                std::map<K,T >::iterator i = self->find(key);
                if (i != self->end())
                    return i->second;
                else
                    throw std::out_of_range("key not found");
            }
            void __setitem__(K key, const T& x) {
                (*self)[key] = x;
            }
            void __delitem__(K key) throw (std::out_of_range) {
                std::map<K,T >::iterator i = self->find(key);
                if (i != self->end())
                    self->erase(i);
                else
                    throw std::out_of_range("key not found");
            }
            bool has_key(K key) {
                std::map<K,T >::iterator i = self->find(key);
                return i != self->end();
            }
            SCM keys() {
                SCM result = SCM_EOL;
                for (std::map<K,T >::reverse_iterator i=$1.rbegin(); 
                                                      i!=$1.rend(); ++i) {
                    SCM k = CONVERT_TO(i->first);
                    result = gh_cons(k,result);
                }
                return result;
            }
        }
    };
    %enddef

    %define specialize_std_map_on_value(T,CHECK,CONVERT_FROM,CONVERT_TO)
    template<class K> class map<K,T> {
        %typemap(in) map<K,T> (std::map<K,T>* m) {
            if (gh_null_p($input)) {
                $1 = std::map<K,T >();
            } else if (gh_pair_p($input)) {
                $1 = std::map<K,T >();
                SCM alist = $input;
                while (!gh_null_p(alist)) {
                    K* k;
                    SCM entry, key, val;
                    entry = gh_car(alist);
                    if (!gh_pair_p(entry))
                        SWIG_exception(SWIG_TypeError,"alist expected");
                    key = gh_car(entry);
                    val = gh_cdr(entry);
                    k = (K*) SWIG_MustGetPtr(key,$descriptor(K *),$argnum, 0);
                    if (!CHECK(val)) {
                        if (!gh_pair_p(val))
                            SWIG_exception(SWIG_TypeError,"alist expected");
                        val = gh_car(val);
                        if (!CHECK(val))
                            SWIG_exception(SWIG_TypeError,
                                           "map<" #K "," #T "> expected");
                    }
                    (($1_type &)$1)[*k] = CONVERT_FROM(val);
                    alist = gh_cdr(alist);
                }
            } else {
                $1 = *(($&1_type)
                       SWIG_MustGetPtr($input,$&1_descriptor,$argnum, 0));
            }
        }
        %typemap(in) const map<K,T>& (std::map<K,T> temp,
                                      std::map<K,T>* m),
                     const map<K,T>* (std::map<K,T> temp,
                                      std::map<K,T>* m) {
            if (gh_null_p($input)) {
                temp = std::map<K,T >();
                $1 = &temp;
            } else if (gh_pair_p($input)) {
                temp = std::map<K,T >();
                $1 = &temp;
                SCM alist = $input;
                while (!gh_null_p(alist)) {
                    K* k;
                    SCM entry, key, val;
                    entry = gh_car(alist);
                    if (!gh_pair_p(entry))
                        SWIG_exception(SWIG_TypeError,"alist expected");
                    key = gh_car(entry);
                    val = gh_cdr(entry);
                    k = (K*) SWIG_MustGetPtr(key,$descriptor(K *),$argnum, 0);
                    if (!CHECK(val)) {
                        if (!gh_pair_p(val))
                            SWIG_exception(SWIG_TypeError,"alist expected");
                        val = gh_car(val);
                        if (!CHECK(val))
                            SWIG_exception(SWIG_TypeError,
                                           "map<" #K "," #T "> expected");
                    }
                    temp[*k] = CONVERT_FROM(val);
                    alist = gh_cdr(alist);
                }
            } else {
                $1 = ($1_ltype) SWIG_MustGetPtr($input,$1_descriptor,$argnum, 0);
            }
        }
        %typemap(out) map<K,T> {
            SCM alist = SCM_EOL;
            for (std::map<K,T >::reverse_iterator i=$1.rbegin(); 
                                                  i!=$1.rend(); ++i) {
                K* key = new K(i->first);
                SCM k = SWIG_NewPointerObj(key,$descriptor(K *), 1);
                SCM x = CONVERT_TO(i->second);
                SCM entry = gh_cons(k,x);
                alist = gh_cons(entry,alist);
            }
            $result = alist;
        }
        %typecheck(SWIG_TYPECHECK_MAP) map<K,T> {
            // native sequence?
            if (gh_null_p($input)) {
                /* an empty sequence can be of any type */
                $1 = 1;
            } else if (gh_pair_p($input)) {
                // check the first element only
                K* k;
                SCM head = gh_car($input);
                if (gh_pair_p(head)) {
                    SCM key = gh_car(head);
                    SCM val = gh_cdr(head);
                    if (SWIG_ConvertPtr(val,(void **) &k,
                                    $descriptor(K *), 0) != 0) {
                        $1 = 0;
                    } else {
                        if (CHECK(val)) {
                            $1 = 1;
                        } else if (gh_pair_p(val)) {
                            val = gh_car(val);
                            if (CHECK(val))
                                $1 = 1;
                            else
                                $1 = 0;
                        } else {
                            $1 = 0;
                        }
                    }
                } else {
                    $1 = 0;
                }
            } else {
                // wrapped map?
                std::map<K,T >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                $&1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %typecheck(SWIG_TYPECHECK_MAP) const map<K,T>&,
                                       const map<K,T>* {
            // native sequence?
            if (gh_null_p($input)) {
                /* an empty sequence can be of any type */
                $1 = 1;
            } else if (gh_pair_p($input)) {
                // check the first element only
                K* k;
                SCM head = gh_car($input);
                if (gh_pair_p(head)) {
                    SCM key = gh_car(head);
                    SCM val = gh_cdr(head);
                    if (SWIG_ConvertPtr(val,(void **) &k,
                                    $descriptor(K *), 0) != 0) {
                        $1 = 0;
                    } else {
                        if (CHECK(val)) {
                            $1 = 1;
                        } else if (gh_pair_p(val)) {
                            val = gh_car(val);
                            if (CHECK(val))
                                $1 = 1;
                            else
                                $1 = 0;
                        } else {
                            $1 = 0;
                        }
                    }
                } else {
                    $1 = 0;
                }
            } else {
                // wrapped map?
                std::map<K,T >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                $1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %rename("length") size;
        %rename("null?") empty;
        %rename("clear!") clear;
        %rename("ref") __getitem__;
        %rename("set!") __setitem__;
        %rename("delete!") __delitem__;
        %rename("has-key?") has_key;
      public:
        map();
        map(const map<K,T> &);
        
        unsigned int size() const;
        bool empty() const;
        void clear();
        %extend {
            T __getitem__(const K& key) throw (std::out_of_range) {
                std::map<K,T >::iterator i = self->find(key);
                if (i != self->end())
                    return i->second;
                else
                    throw std::out_of_range("key not found");
            }
            void __setitem__(const K& key, T x) {
                (*self)[key] = x;
            }
            void __delitem__(const K& key) throw (std::out_of_range) {
                std::map<K,T >::iterator i = self->find(key);
                if (i != self->end())
                    self->erase(i);
                else
                    throw std::out_of_range("key not found");
            }
            bool has_key(const K& key) {
                std::map<K,T >::iterator i = self->find(key);
                return i != self->end();
            }
            SCM keys() {
                SCM result = SCM_EOL;
                for (std::map<K,T >::reverse_iterator i=$1.rbegin(); 
                                                      i!=$1.rend(); ++i) {
                    K* key = new K(i->first);
                    SCM k = SWIG_NewPointerObj(key,$descriptor(K *), 1);
                    result = gh_cons(k,result);
                }
                return result;
            }
        }
    };
    %enddef

    %define specialize_std_map_on_both(K,CHECK_K,CONVERT_K_FROM,CONVERT_K_TO,
                                       T,CHECK_T,CONVERT_T_FROM,CONVERT_T_TO)
    template<> class map<K,T> {
        %typemap(in) map<K,T> (std::map<K,T>* m) {
            if (gh_null_p($input)) {
                $1 = std::map<K,T >();
            } else if (gh_pair_p($input)) {
                $1 = std::map<K,T >();
                SCM alist = $input;
                while (!gh_null_p(alist)) {
                    SCM entry, key, val;
                    entry = gh_car(alist);
                    if (!gh_pair_p(entry))
                        SWIG_exception(SWIG_TypeError,"alist expected");
                    key = gh_car(entry);
                    val = gh_cdr(entry);
                    if (!CHECK_K(key))
                        SWIG_exception(SWIG_TypeError,
                                           "map<" #K "," #T "> expected");
                    if (!CHECK_T(val)) {
                        if (!gh_pair_p(val))
                            SWIG_exception(SWIG_TypeError,"alist expected");
                        val = gh_car(val);
                        if (!CHECK_T(val))
                            SWIG_exception(SWIG_TypeError,
                                           "map<" #K "," #T "> expected");
                    }
                    (($1_type &)$1)[CONVERT_K_FROM(key)] = 
                                               CONVERT_T_FROM(val);
                    alist = gh_cdr(alist);
                }
            } else {
                $1 = *(($&1_type)
                       SWIG_MustGetPtr($input,$&1_descriptor,$argnum, 0));
            }
        }
        %typemap(in) const map<K,T>& (std::map<K,T> temp,
                                      std::map<K,T>* m),
                     const map<K,T>* (std::map<K,T> temp,
                                      std::map<K,T>* m) {
            if (gh_null_p($input)) {
                temp = std::map<K,T >();
                $1 = &temp;
            } else if (gh_pair_p($input)) {
                temp = std::map<K,T >();
                $1 = &temp;
                SCM alist = $input;
                while (!gh_null_p(alist)) {
                    SCM entry, key, val;
                    entry = gh_car(alist);
                    if (!gh_pair_p(entry))
                        SWIG_exception(SWIG_TypeError,"alist expected");
                    key = gh_car(entry);
                    val = gh_cdr(entry);
                    if (!CHECK_K(key))
                        SWIG_exception(SWIG_TypeError,
                                           "map<" #K "," #T "> expected");
                    if (!CHECK_T(val)) {
                        if (!gh_pair_p(val))
                            SWIG_exception(SWIG_TypeError,"alist expected");
                        val = gh_car(val);
                        if (!CHECK_T(val))
                            SWIG_exception(SWIG_TypeError,
                                           "map<" #K "," #T "> expected");
                    }
                    temp[CONVERT_K_FROM(key)] = CONVERT_T_FROM(val);
                    alist = gh_cdr(alist);
                }
            } else {
                $1 = ($1_ltype) SWIG_MustGetPtr($input,$1_descriptor,$argnum, 0);
            }
        }
        %typemap(out) map<K,T> {
            SCM alist = SCM_EOL;
            for (std::map<K,T >::reverse_iterator i=$1.rbegin(); 
                                                  i!=$1.rend(); ++i) {
                SCM k = CONVERT_K_TO(i->first);
                SCM x = CONVERT_T_TO(i->second);
                SCM entry = gh_cons(k,x);
                alist = gh_cons(entry,alist);
            }
            $result = alist;
        }
        %typecheck(SWIG_TYPECHECK_MAP) map<K,T> {
            // native sequence?
            if (gh_null_p($input)) {
                /* an empty sequence can be of any type */
                $1 = 1;
            } else if (gh_pair_p($input)) {
                // check the first element only
                SCM head = gh_car($input);
                if (gh_pair_p(head)) {
                    SCM key = gh_car(head);
                    SCM val = gh_cdr(head);
                    if (!CHECK_K(key)) {
                        $1 = 0;
                    } else {
                        if (CHECK_T(val)) {
                            $1 = 1;
                        } else if (gh_pair_p(val)) {
                            val = gh_car(val);
                            if (CHECK_T(val))
                                $1 = 1;
                            else
                                $1 = 0;
                        } else {
                            $1 = 0;
                        }
                    }
                } else {
                    $1 = 0;
                }
            } else {
                // wrapped map?
                std::map<K,T >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                $&1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %typecheck(SWIG_TYPECHECK_MAP) const map<K,T>&,
                                       const map<K,T>* {
            // native sequence?
            if (gh_null_p($input)) {
                /* an empty sequence can be of any type */
                $1 = 1;
            } else if (gh_pair_p($input)) {
                // check the first element only
                SCM head = gh_car($input);
                if (gh_pair_p(head)) {
                    SCM key = gh_car(head);
                    SCM val = gh_cdr(head);
                    if (!CHECK_K(key)) {
                        $1 = 0;
                    } else {
                        if (CHECK_T(val)) {
                            $1 = 1;
                        } else if (gh_pair_p(val)) {
                            val = gh_car(val);
                            if (CHECK_T(val))
                                $1 = 1;
                            else
                                $1 = 0;
                        } else {
                            $1 = 0;
                        }
                    }
                } else {
                    $1 = 0;
                }
            } else {
                // wrapped map?
                std::map<K,T >* m;
                if (SWIG_ConvertPtr($input,(void **) &m,
                                $1_descriptor, 0) == 0)
                    $1 = 1;
                else
                    $1 = 0;
            }
        }
        %rename("length") size;
        %rename("null?") empty;
        %rename("clear!") clear;
        %rename("ref") __getitem__;
        %rename("set!") __setitem__;
        %rename("delete!") __delitem__;
        %rename("has-key?") has_key;
      public:
        map();
        map(const map<K,T> &);
        
        unsigned int size() const;
        bool empty() const;
        void clear();
        %extend {
            T __getitem__(K key) throw (std::out_of_range) {
                std::map<K,T >::iterator i = self->find(key);
                if (i != self->end())
                    return i->second;
                else
                    throw std::out_of_range("key not found");
            }
            void __setitem__(K key, T x) {
                (*self)[key] = x;
            }
            void __delitem__(K key) throw (std::out_of_range) {
                std::map<K,T >::iterator i = self->find(key);
                if (i != self->end())
                    self->erase(i);
                else
                    throw std::out_of_range("key not found");
            }
            bool has_key(K key) {
                std::map<K,T >::iterator i = self->find(key);
                return i != self->end();
            }
            SCM keys() {
                SCM result = SCM_EOL;
                for (std::map<K,T >::reverse_iterator i=$1.rbegin(); 
                                                      i!=$1.rend(); ++i) {
                    SCM k = CONVERT_K_TO(i->first);
                    result = gh_cons(k,result);
                }
                return result;
            }
        }
    };
    %enddef


    specialize_std_map_on_key(bool,gh_boolean_p,
                              gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_key(int,gh_number_p,
                              gh_scm2long,gh_long2scm);
    specialize_std_map_on_key(short,gh_number_p,
                              gh_scm2long,gh_long2scm);
    specialize_std_map_on_key(long,gh_number_p,
                              gh_scm2long,gh_long2scm);
    specialize_std_map_on_key(unsigned int,gh_number_p,
                              gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_key(unsigned short,gh_number_p,
                              gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_key(unsigned long,gh_number_p,
                              gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_key(double,gh_number_p,
                              gh_scm2double,gh_double2scm);
    specialize_std_map_on_key(float,gh_number_p,
                              gh_scm2double,gh_double2scm);
    specialize_std_map_on_key(std::string,gh_string_p,
                              SWIG_scm2string,SWIG_string2scm);

    specialize_std_map_on_value(bool,gh_boolean_p,
                                gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_value(int,gh_number_p,
                                gh_scm2long,gh_long2scm);
    specialize_std_map_on_value(short,gh_number_p,
                                gh_scm2long,gh_long2scm);
    specialize_std_map_on_value(long,gh_number_p,
                                gh_scm2long,gh_long2scm);
    specialize_std_map_on_value(unsigned int,gh_number_p,
                                gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_value(unsigned short,gh_number_p,
                                gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_value(unsigned long,gh_number_p,
                                gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_value(double,gh_number_p,
                                gh_scm2double,gh_double2scm);
    specialize_std_map_on_value(float,gh_number_p,
                                gh_scm2double,gh_double2scm);
    specialize_std_map_on_value(std::string,gh_string_p,
                                SWIG_scm2string,SWIG_string2scm);

    specialize_std_map_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_map_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(int,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_map_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(short,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_map_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(long,gh_number_p,
                               gh_scm2long,gh_long2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_map_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_map_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_map_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_map_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(double,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_map_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(float,gh_number_p,
                               gh_scm2double,gh_double2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
    specialize_std_map_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               bool,gh_boolean_p,
                               gh_scm2bool,SWIG_bool2scm);
    specialize_std_map_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               int,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               short,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               long,gh_number_p,
                               gh_scm2long,gh_long2scm);
    specialize_std_map_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               unsigned int,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               unsigned short,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               unsigned long,gh_number_p,
                               gh_scm2ulong,gh_ulong2scm);
    specialize_std_map_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               double,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               float,gh_number_p,
                               gh_scm2double,gh_double2scm);
    specialize_std_map_on_both(std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm,
                               std::string,gh_string_p,
                               SWIG_scm2string,SWIG_string2scm);
}
