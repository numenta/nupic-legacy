%include <std/std_except.i>
%include <rubystdcommon.swg>
%include <rubystdautodoc.swg>


/*
  Generate the traits for a 'primitive' type, such as 'double',
  for which the SWIG_AsVal and SWIG_From methods are already defined.
*/

%define %traits_ptypen(Type...)
  %fragment(SWIG_Traits_frag(Type),"header",
	    fragment=SWIG_AsVal_frag(Type),
	    fragment=SWIG_From_frag(Type),
	    fragment="StdTraits") {
namespace swig {
  template <> struct traits<Type > {
    typedef value_category category;
    static const char* type_name() { return  #Type; }
  };  
  template <>  struct traits_asval<Type > {   
    typedef Type value_type;
    static int asval(VALUE obj, value_type *val) { 
      return SWIG_AsVal(Type)(obj, val);
    }
  };
  template <>  struct traits_from<Type > {
    typedef Type value_type;
    static VALUE from(const value_type& val) {
      return SWIG_From(Type)(val);
    }
  };
}
}
%enddef


%include <std/std_common.i>

//
// Generates the traits for all the known primitive
// C++ types (int, double, ...)
//
%apply_cpptypes(%traits_ptypen);
