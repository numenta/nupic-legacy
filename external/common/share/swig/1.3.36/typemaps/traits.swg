//
// Use the following macro with modern STL implementations
//
//#define SWIG_STD_MODERN_STL
//
// Use this to deactive the previous definition, when using gcc-2.95
// or similar old compilers.
//
//#define SWIG_STD_NOMODERN_STL

// Here, we identify compilers we now have problems with STL.
%{
#if defined(__GNUC__)
#  if __GNUC__ == 2 && __GNUC_MINOR <= 96
#     define SWIG_STD_NOMODERN_STL
#  endif
#endif
%}

//
// Common code for supporting the STD C++ namespace
//

%{
#include <string>
#include <stdexcept>
%}

%fragment("Traits","header") 
{
namespace swig {  
  /*
    type categories
  */
  struct pointer_category { };  
  struct value_category { };

  /*
    General traits that provides type_name and type_info
  */
  template <class Type> struct traits { };

  template <class Type>
  inline const char* type_name() {
    return traits<Type>::type_name();
  }

  template <class Type> 
  struct traits_info {
    static swig_type_info *type_query(std::string name) {
      name += " *";
      return SWIG_TypeQuery(name.c_str());
    }    
    static swig_type_info *type_info() {
      static swig_type_info *info = type_query(type_name<Type>());
      return info;
    }
  };

  template <class Type>
  inline swig_type_info *type_info() {
    return traits_info<Type>::type_info();
  }

  /*
    Partial specialization for pointers
  */
  template <class Type> struct traits <Type *> {
    typedef pointer_category category;
    static std::string make_ptr_name(const char* name) {
      std::string ptrname = name;
      ptrname += " *";
      return ptrname;
    }    
    static const char* type_name() {
      static std::string name = make_ptr_name(swig::type_name<Type>());
      return name.c_str();
    }
  };

 
  template <class Type, class Category = typename traits<Type>::category > 
  struct traits_check { };

  /*
    Traits that provides the from method for an unknown type
  */
  template <int flags, class Type> struct traits_from_ptr {
    static SWIG_Object from SWIG_FROM_DECL_ARGS(Type *val) {
      return SWIG_NewPointerObj(val, type_info<Type>(), flags);
    }
  };

  template <class Type> struct traits_from {
    static SWIG_Object from SWIG_FROM_DECL_ARGS(const Type& val) {
      return traits_from_ptr<SWIG_POINTER_OWN, Type>::from(new Type(val));
    }
  };

  template <class Type> struct traits_from<Type *> {
    static SWIG_Object from SWIG_FROM_DECL_ARGS(Type* val) {
      return traits_from_ptr<0, Type>::from(val);
    }
  };

  template <class Type>
  inline SWIG_Object from SWIG_FROM_DECL_ARGS(const Type& val) {
    return traits_from<Type>::from(val);
  }

  /*
    Traits that provides the asptr/asval method for an unknown type
  */
  template <class Type>
  struct traits_asptr {   
    static int asptr SWIG_AS_DECL_ARGS (SWIG_Object obj, Type **val) {
      Type *p;
      int res = SWIG_ConvertPtr(obj, %as_voidptrptr(&p), type_info<Type>(), 0);
      if (SWIG_IsOK(res) && val) *val = p;
      return res;
    }
  }; 

  template <class Type>
  inline int asptr SWIG_AS_DECL_ARGS(SWIG_Object obj, Type **vptr) {
    return traits_asptr<Type>::asptr SWIG_AS_CALL_ARGS(obj, vptr);
  }

  template <class Type> 
  struct traits_asval {
    static int asval SWIG_AS_DECL_ARGS(SWIG_Object obj, Type *val) {
      if (val) {
	Type *p = 0;
	int res = traits_asptr<Type>::asptr SWIG_AS_CALL_ARGS(obj, &p);
	if (SWIG_IsOK(res) && p) {
	  *val = *p;
	  if (SWIG_IsNewObj(res)) {
	    %delete(p);
	    res = SWIG_DelNewMask(res);
	  }
	}
	return res;
      } else {
	return traits_asptr<Type>::asptr SWIG_AS_CALL_ARGS(obj, (Type **)(0));
      }
    }
  };
  
  template <class Type>
  inline int asval SWIG_AS_DECL_ARGS (SWIG_Object obj, Type *val) {
    return traits_asval<Type>::asval SWIG_AS_CALL_ARGS(obj, val);
  }

  /*
    Traits that provides the check method for an unknown type
  */
#define SWIG_CHECK_DECL_ARGS(obj) SWIG_AS_DECL_ARGS(obj, void * = 0)
#define SWIG_CHECK_CALL_ARGS(obj) SWIG_AS_CALL_ARGS(obj, 0)

  template <class Type> 
  struct traits_checkval {
    static int check SWIG_CHECK_DECL_ARGS(SWIG_Object obj) {
      if (obj) {
	int res = asval SWIG_AS_CALL_ARGS(obj, (Type *)(0));
	return SWIG_CheckState(res);
      } else {
	return 0;
      }
    }
  };

  template <class Type> 
  struct traits_checkptr {
    static int check SWIG_CHECK_DECL_ARGS(SWIG_Object obj) {
      if (obj) {
	int res = asptr SWIG_AS_CALL_ARGS(obj, (Type **)(0));
	return SWIG_CheckState(res);
      } else {
	return 0;
      }
    }
  };

  template <class Type> 
  struct traits_check<Type, value_category> : traits_checkval<Type> {
  };

  template <class Type> 
  struct traits_check<Type, pointer_category> : traits_checkptr<Type> {
  };

  template <class Type>
  inline int check SWIG_CHECK_DECL_ARGS(SWIG_Object obj) {
    return traits_check<Type>::check SWIG_CHECK_CALL_ARGS(obj);
  }

}
}
 
/*
  Generate the traits for an unknown SWIGTYPE
*/

%define %traits_swigtype(Type...)
%fragment(SWIG_Traits_frag(Type),"header",fragment="Traits") {
  namespace swig {
    template <>  struct traits<Type > {
      typedef pointer_category category;
      static const char* type_name() { return  #Type; }
    };
  }
}
%enddef


/*
  Generate the traits for a 'value' type, such as 'double',
  for which the SWIG_AsVal and SWIG_From methods are already defined.
*/

%define %traits_value(Type...)
%fragment(SWIG_Traits_frag(Type),"header",
	  fragment=SWIG_AsVal_frag(Type),
	  fragment=SWIG_From_frag(Type),
	  fragment="Traits") {
namespace swig {
  template <> struct traits<Type > {
    typedef value_category category;
    static const char* type_name() { return  #Type; }
  };  

  template <>  struct traits_asval<Type > {   
    typedef Type value_type;
    static int asval SWIG_AS_DECL_ARGS (SWIG_Object obj, value_type *val) {
      return SWIG_AsVal(Type)(obj, val);
    }
  };

  template <>  struct traits_from<Type > {
    typedef Type value_type;
    static SWIG_Object from SWIG_FROM_DECL_ARGS (const value_type& val) {
      return SWIG_From(Type)(val);
    }
  };
}
}
%enddef

/*
  Generate the traits for a 'pointer' type, such as 'std::string',
  for which the SWIG_AsPtr and SWIG_From methods are already defined.
*/

%define %traits_pointer(Type...)
%fragment(SWIG_Traits_frag(Type),"header",
	  fragment=SWIG_AsVal_frag(Type),
	  fragment=SWIG_From_frag(Type),
	  fragment="Traits") {
namespace swig {
  template <> struct traits<Type > {
    typedef pointer_category category;
    static const char* type_name() { return  #Type; }
  };  
    
  template <>  struct traits_asptr<Type > {   
    typedef Type value_type;
    static int asptr SWIG_AS_DECL_ARGS (SWIG_Object obj, value_type **val) {
      return SWIG_AsPtr(Type)(obj, val);
    }
  };

  template <>  struct traits_from<Type > {
    typedef Type value_type;
    static SWIG_Object from SWIG_FROM_DECL_ARGS (const value_type& val) {
      return SWIG_From(Type)(val);
    }
  };
}
}
%enddef

/*
  Generate the typemaps for a class that has 'value' traits
*/

%define %typemap_traits_value(Code,Type...)
  %typemaps_asvalfrom(%arg(Code),
		      %arg(swig::asval),
		      %arg(swig::from),
		      %arg(SWIG_Traits_frag(Type)),
		      %arg(SWIG_Traits_frag(Type)),
		      Type);
%enddef

/*
  Generate the typemaps for a class that has 'pointer' traits
*/

%define %typemap_traits_pointer(Code,Type...)
  %typemaps_asptrfrom(%arg(Code),
		      %arg(swig::asptr),
		      %arg(swig::from),
		      %arg(SWIG_Traits_frag(Type)),
		      %arg(SWIG_Traits_frag(Type)),
		      Type);
%enddef

