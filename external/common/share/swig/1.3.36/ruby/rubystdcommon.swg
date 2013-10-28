
/* ------------------------------------------------------------
 * The Ruby classes, for C++
 * ------------------------------------------------------------ */
%include <rubyclasses.swg>

%fragment("StdTraits","header",fragment="StdTraitsCommon")
{

namespace swig {  
  /*
    Traits that provides the from method
  */
  template <class Type> struct traits_from_ptr {
    static VALUE from(Type *val, int owner = 0) {
      return SWIG_NewPointerObj(val, type_info<Type>(), owner);
    }
  };

  template <class Type> struct traits_from {
    static VALUE from(const Type& val) {
      return traits_from_ptr<Type>::from(new Type(val), 1);
    }
  };

  template <class Type> struct traits_from<Type *> {
    static VALUE from(Type* val) {
      return traits_from_ptr<Type>::from(val, 0);
    }
  };

  template <class Type> struct traits_from<const Type *> {
    static VALUE from(const Type* val) {
      return traits_from_ptr<Type>::from(const_cast<Type*>(val), 0);
    }
  };


  template <class Type>
  inline VALUE from(const Type& val) {
    return traits_from<Type>::from(val);
  }

  template <class Type>
  inline VALUE from_ptr(Type* val, int owner) {
    return traits_from_ptr<Type>::from(val, owner);
  }

  /*
    Traits that provides the asval/as/check method
  */
  template <class Type>
  struct traits_asptr {   
    static int asptr(VALUE obj, Type **val) {
      Type *p;
      int res = SWIG_ConvertPtr(obj, (void**)&p, type_info<Type>(), 0);
      if (SWIG_IsOK(res)) {
	if (val) *val = p;
      }
      return res;
    }
  }; 

  template <class Type>
  inline int asptr(VALUE obj, Type **vptr) {
    return traits_asptr<Type>::asptr(obj, vptr);
  }

  template <class Type> 
  struct traits_asval {
    static int asval(VALUE obj, Type *val) {
      if (val) {
	Type *p = 0;
	int res = traits_asptr<Type>::asptr(obj, &p);
	if (!SWIG_IsOK(res)) return res;	
	if (p) {
	  typedef typename noconst_traits<Type>::noconst_type noconst_type;
	  *(const_cast<noconst_type*>(val)) = *p;
	  if (SWIG_IsNewObj(res)){
	    %delete(p);
	    res = SWIG_DelNewMask(res);
	  }
	  return res;
	} else {
	  return SWIG_ERROR;
	}
      } else {
	return traits_asptr<Type>::asptr(obj, (Type **)(0));
      }
    }
  };

  template <class Type> struct traits_asval<Type*> {
    static int asval(VALUE obj, Type **val) {
      if (val) {
        typedef typename noconst_traits<Type>::noconst_type noconst_type;
        noconst_type *p = 0;
        int res = traits_asptr<noconst_type>::asptr(obj,  &p);
        if (SWIG_IsOK(res)) {
          *(const_cast<noconst_type**>(val)) = p;
	}
	return res;
      } else {
	return traits_asptr<Type>::asptr(obj, (Type **)(0));
      }
    }
  };
  
  template <class Type>
  inline int asval(VALUE obj, Type *val) {
    return traits_asval<Type>::asval(obj, val);
  }

  template <class Type> 
  struct traits_as<Type, value_category> {
    static Type as(VALUE obj, bool throw_error) {
      Type v;
      int res = asval(obj, &v);
      if (!obj || !SWIG_IsOK(res)) {
	if (throw_error) throw std::invalid_argument("bad type");
	VALUE lastErr = rb_gv_get("$!");
	if (lastErr == Qnil) {
	  %type_error(swig::type_name<Type>());
	}
      }
      return v;
    }
  };

  template <class Type> 
  struct traits_as<Type, pointer_category> {
    static Type as(VALUE obj, bool throw_error) {
      Type *v = 0;      
      int res = (obj ? traits_asptr<Type>::asptr(obj, &v) : SWIG_ERROR);
      if (SWIG_IsOK(res) && v) {
	if (SWIG_IsNewObj(res)) {
	  Type r(*v);
	  %delete(v);
	  return r;
	} else {
	  return *v;
	}
      } else {
	// Uninitialized return value, no Type() constructor required.
	if (throw_error) throw std::invalid_argument("bad type");
	VALUE lastErr = rb_gv_get("$!");
	if (lastErr == Qnil) {
	  %type_error(swig::type_name<Type>());
	}
	static Type *v_def = (Type*) malloc(sizeof(Type));
	memset(v_def,0,sizeof(Type));
	return *v_def;
      }
    }
  };

  template <class Type> 
  struct traits_as<Type*, pointer_category> {
    static Type* as(VALUE obj, bool throw_error) {
      Type *v = 0;      
      int res = (obj ? traits_asptr<Type>::asptr(obj, &v) : SWIG_ERROR);
      if (SWIG_IsOK(res)) {
	return v;
      } else {
	if (throw_error) throw std::invalid_argument("bad type");
	VALUE lastErr = rb_gv_get("$!");
	if (lastErr == Qnil) {
	  %type_error(swig::type_name<Type>());
	}
	return 0;
      }
    }
  };

  template <class Type>
  inline Type as(VALUE obj, bool te = false) {
    return traits_as< Type, typename traits< Type >::category >::as(obj, te);
  }

  template <class Type> 
  struct traits_check<Type, value_category> {
    static bool check(VALUE obj) {
      int res = obj ? asval(obj, (Type *)(0)) : SWIG_ERROR;
      return SWIG_IsOK(res) ? true : false;
    }
  };

  template <class Type> 
  struct traits_check<Type, pointer_category> {
    static bool check(VALUE obj) {
      int res = obj ? asptr(obj, (Type **)(0)) : SWIG_ERROR;
      return SWIG_IsOK(res) ? true : false;
    }
  };

  template <class Type>
  inline bool check(VALUE obj) {
    return traits_check<Type, typename traits<Type>::category>::check(obj);
  }
}
}


// Define GC marking template traits for a container type
%define %create_mark_traits(Type)
%{
  namespace swig {
    template <class T>
    struct mark_traits {
      typedef typename Type<T >::const_iterator const_iterator;

      inline void operator()(const Type<T >& c ) const
      {
	const_iterator i = c.begin();
	const_iterator e = c.end();
	for ( ; i != e; ++i )
	  {
	    rb_gc_mark( swig::from( &(*i) ) );
	  }
      }
    };

    // Partial specializations for classes that requires no GC marking
    // or a special GC marking algorithm.
    template< >
    struct mark_traits<bool> {
      inline void operator()(const Type<bool >& c ) const {}
    };

    template< >
    struct mark_traits<char> {
      inline void operator()(const Type<char >& c ) const {}
    };

    template< >
    struct mark_traits<int> {
      inline void operator()(const Type<int >& c ) const {}
    };

    template< >
    struct mark_traits<unsigned> {
      inline void operator()(const Type<unsigned >& c ) const {}
    };

    template< >
    struct mark_traits<GC_VALUE> {
      typedef Type<GC_VALUE >::const_iterator const_iterator;

      inline void operator()(const Type<GC_VALUE >& c ) const {
	const_iterator i = c.begin();
	const_iterator e = c.end();
	for ( ; i != e; ++i )
	  {
	    VALUE v = *i;
	    if ( FIXNUM_P(v) || SPECIAL_CONST_P(v) || SYMBOL_P(v) ||
		 ( BUILTIN_TYPE(v) == T_NONE ) ) continue;

	    rb_gc_mark( v );
	  }
      }
    };

  }
%}
%enddef
