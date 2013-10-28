/*
  Fragments:
  ==========

  Second to typemaps, fragments are one the most powerful and
  dangerous swig features. So, if you are starting to read about them,
  make sure you read all of this document.

  Basics:
  =======

  Fragments provide a way to include or generate code into "on-demand"
  as the typemaps could require.

  For example, if you have a very long typemap

  %typemap(in) MyClass * {
    MyClass *value = 0;

    <very long typemap>
    ....
    value = somewhere_converted_from_input_object_here($input);
    ...
    <very long typemap>
  
    $result = value;
  }

  very soon you will discover yourself copying the same long
  conversion code in several typemaps, such as varin, directorout,
  etc. Also, you will discover that swig copes verbatim the same very
  long conversion code for every argument that requires it, making the
  code very large too.

  To eliminate this automatic or manual code copying, we define a
  fragment that includes the common conversion code:

  %fragment("AsMyClass","header") {
     MyClass *AsMyClass(PyObject *obj) {
        MyClass *value = 0;
        <very long conversion>
        ....
        value = somewhere_converted_from_input_object_here(obj);
        ...
        <very long conversion>
  
        return value;
     }
  }

  %typemap(in,fragment="AsMyClass") MyClass * {
    $result = AsMyClass($input);
  }

  %typemap(varin,fragment="AsMyClass") MyClass * {
    $result = AsMyClass($input);
  }

  When the 'in' or 'varin' typemaps for MyClass are invoked, the
  fragment "AsMyClass" is added to the "header" section, and then the
  typemap code is emitted. Hence, the method AsMyClass will be
  included in the wrapping code and it will be available at the time
  the typemap is applied.

  To define a fragment then you need a name, a section where it goes,
  and the code. Usually the section refers to the "header" part, and
  both string and braces forms are accepted, ie:

    %fragment("my_name","header") { ... }
    %fragment("my_name","header") "...";

  To ensure all the fragment/typemap engine works as expected, there
  are some rules that fragments follow:

  1.- A fragment is added to the wrapping code only once, ie, for the
      method:
      
        int foo(MyClass *a, MyClass *b);

     the wrapped code will look as much as:

      MyClass *AsMyClass(PyObject *obj) {
        .....
      }
      
      int _wrap_foo(...) {
        ....
        arg1 = AsMyClass(obj1);
        arg2 = AsMyClass(obj2);
        ...
	result = foo(arg1, arg2);
      }


     even when there will be duplicated typemap to process 'a' and
     'b', the 'AsMyClass' method will be defined only once.

     
  2.- A fragment can only defined once, and the first definition
      is the only one taking in account. All other definitions of the
      same fragments are silently ignored. For example, you can have


        %fragment("AsMyClass","header") { <definition 1> }
	....
        %fragment("AsMyClass","header") { <definition 2> }
     
      and then only the first definition is considered. In this way
      you can change the 'system' fragments by including yours first.

      Note that this behavior is opposite to the typemaps, where the
      last typemap applied or defined prevails. Fragment follows the
      first-in-first-out convention since they are intended to be
      "global", while typemaps intend to be "locally" specialized.
      
  3.- Fragments names can not contain commas.
 	

  A fragment can include one or more additional fragments, for example:

    %fragment("<limits.h>", "header")  {
      #include <limits.h>
    }


    %fragment("AsMyClass", "header", fragment="<limits.h>") {
      MyClass *AsMyClass(PyObject *obj) {
        MyClass *value = 0;
	int ival = somewhere_converted_from_input_object_here(obj)
	...
        if  (ival < CHAR_MIN) {
	   value = something_from_ival(ival);
        } else {
	...
	}
	...
        return value;
      }
    }

  in this case, when the "AsMyClass" fragment is emitted, it also
  trigger the inclusion of the "<limits.h>" fragment.

  You can add as many fragments as you want, for example

    %fragment("bigfragment","header", fragment="frag1", fragment="frag2", fragment="frag3") "";

  here, when the "bigfragment" is included, the three fragments "frag1",
  "frag2" and "frag3" are included. Note that as "bigframent" is defined
  empty, "", it does not add any code by itself, buy only trigger the
  inclusion of the other fragments.
  
  In a typemap you can also include more than one fragment, but since the
  syntax is different, you need to specify them in a 'comma separated'
  list, for example, considering the previous example:
 
     %typemap(in,fragment="frag1,frag2,frag3") {...}

  is equivalent to

     %typemap(in,fragment="bigfragment") {...}

  
  Finally, you can force the inclusion of a fragment at any moment as follow:

     %fragment("bigfragment");

  which is very useful inside a template class, for example. 


  Fragment type specialization
  ============================
  
  Fragments can be "type specialized". The syntax is as follows
 									   
    %fragment("name","header") { a type independent fragment }
    %fragment("name" {Type}, "header") { a type dependent fragment  }
 									   
  and they can also, as typemaps, be used inside templates, for exampe:
 									   
     template <class T>					              
     struct A {						              
        %fragment("incode"{A<T>},"header") {			              
 	  'incode' specialized fragment 
 	}							   	    
 									   
 	%typemap(in,fragment="incode"{A<T>}) {		   	    
           here we use the 'type specialized' 		   	    
           fragment "incode"{A<T>}			              
 	}
     };							              
  
   which could seems a not much interesting feature, but is
   fundamental for automatic typemap and template specialization.


  Fragments and automatic typemap specialization:
  ===============================================

  Since fragments can be type specialized, they can be elegantly used
  to specialized typemaps .

  For example, if you have something like:

    %fragment("incode"{float}, "header") {
      float in_method_float(PyObject *obj) {
        ...
      }
    }

    %fragment("incode"{long}, "header") {
      float in_method_long(PyObject *obj) {
        ...
      }
    }
    
    %define %my_typemaps(Type) 
    %typemaps(in,fragment="incode"{Type}) {
      value = in_method_##Type(obj);
    }
    %enddef

    %my_typemaps(float);
    %my_typemaps(long);

  then the proper "incode"{float,double} fragment will be included,
  and the proper in_method_{float,double} will be called.

  Since this is a recurrent fragment use, we provide a couple of
  macros that make the automatic generation of typemaps easier:


  Consider for example the following code:

      %fragment(SWIG_From_frag(bool),"header") {     
      static PyObject*		      
      SWIG_From_dec(bool)(bool value)	       
      {					       
        PyObject *obj = value ? Py_True : Py_False;  
        Py_INCREF(obj);			       
        return obj;				       
      }					       
      }					       
      					 
      %typemap(out,fragment=SWIG_From_frag(bool)) bool {
        $result = SWIG_From(bool)($1));
      }

  Here the macros

      SWIG_From_frag  => fragment 
      SWIG_From_dec   => declaration 
      SWIG_From       => call 
      
  allow you to define/include a fragment, and declare and call the
  'from-bool' method as needed. In the simpler case, these macros 
  just return something like

      SWIG_From_frag(bool)  => "SWIG_From_bool"
      SWIG_From_dec(bool)   =>  SWIG_From_bool
      SWIG_From(bool)       =>  SWIG_From_bool

  But they are specialized for the different languages requirements,
  such as perl or tcl that requires passing the interpreter pointer,
  and also they can manage C++ ugly types, for example:
  
      SWIG_From_frag(std::complex<double>)  => "SWIG_From_std_complex_Sl_double_Sg_"
      SWIG_From_dec(std::complex<double>)   =>  SWIG_From_std_complex_Sl_double_Sg_
      SWIG_From(std::complex<double>)       =>  SWIG_From_std_complex_Sl_double_Sg_


  Hence, to declare methods to use with typemaps, always use the
  SWIG_From* macros. In the same way, the SWIG_AsVal* and SWIG_AsPtr*
  set of macros are provided.
    
*/


/* -----------------------------------------------------------------------------
 * Define the basic macros to 'normalize' the type fragments
 * ----------------------------------------------------------------------------- */

#ifndef SWIG_AS_DECL_ARGS
#define SWIG_AS_DECL_ARGS
#endif

#ifndef SWIG_FROM_DECL_ARGS
#define SWIG_FROM_DECL_ARGS
#endif

#ifndef SWIG_AS_CALL_ARGS
#define SWIG_AS_CALL_ARGS
#endif

#ifndef SWIG_FROM_CALL_ARGS
#define SWIG_FROM_CALL_ARGS
#endif

#define %fragment_name(Name, Type...)     %string_name(Name) "_" {Type}

#define SWIG_Traits_frag(Type...) %fragment_name(Traits, Type) 
#define SWIG_AsPtr_frag(Type...)  %fragment_name(AsPtr, Type)	 
#define SWIG_AsVal_frag(Type...)  %fragment_name(AsVal, Type)	 
#define SWIG_From_frag(Type...)   %fragment_name(From, Type)	 

#define SWIG_AsVal_name(Type...)  %symbol_name(AsVal, Type) 
#define SWIG_AsPtr_name(Type...)  %symbol_name(AsPtr, Type) 
#define SWIG_From_name(Type...)   %symbol_name(From, Type)  

#define SWIG_AsVal_dec(Type...)   SWIG_AsVal_name(Type) SWIG_AS_DECL_ARGS
#define SWIG_AsPtr_dec(Type...)   SWIG_AsPtr_name(Type) SWIG_AS_DECL_ARGS
#define SWIG_From_dec(Type...)    SWIG_From_name(Type)  SWIG_FROM_DECL_ARGS 

#define SWIG_AsVal(Type...)       SWIG_AsVal_name(Type) SWIG_AS_CALL_ARGS 
#define SWIG_AsPtr(Type...)  	  SWIG_AsPtr_name(Type) SWIG_AS_CALL_ARGS 	 
#define SWIG_From(Type...)   	  SWIG_From_name(Type)  SWIG_FROM_CALL_ARGS 

/* ------------------------------------------------------------
 * common fragments 
 * ------------------------------------------------------------ */

/* Default compiler options for gcc allow long_long but not LLONG_MAX. 
 * Define SWIG_NO_LLONG_MAX if this added limits support is not wanted. */
%fragment("<limits.h>","header") %{
#include <limits.h>
#if !defined(SWIG_NO_LLONG_MAX)
# if !defined(LLONG_MAX) && defined(__GNUC__) && defined (__LONG_LONG_MAX__)
#   define LLONG_MAX __LONG_LONG_MAX__
#   define LLONG_MIN (-LLONG_MAX - 1LL)
#   define ULLONG_MAX (LLONG_MAX * 2ULL + 1ULL)
# endif
#endif
%}

%fragment("<math.h>","header") %{
#include <math.h>
%}

%fragment("<wchar.h>","header") %{
#include <wchar.h>
#include <limits.h>
#ifndef WCHAR_MIN
#  define WCHAR_MIN 0
#endif
#ifndef WCHAR_MAX
#  define WCHAR_MAX 65535
#endif
%}

%fragment("<float.h>","header") %{
#include <float.h>
%}

%fragment("<stdio.h>","header") %{
#include <stdio.h>
#if defined(_MSC_VER) || defined(__BORLANDC__) || defined(_WATCOM)
# ifndef snprintf
#  define snprintf _snprintf
# endif
#endif
%}

%fragment("<stdlib.h>","header") %{
#include <stdlib.h>
#ifdef _MSC_VER
# ifndef strtoull
#  define strtoull _strtoui64
# endif
# ifndef strtoll
#  define strtoll _strtoi64
# endif
#endif
%}

/* -----------------------------------------------------------------------------
 * special macros for fragments
 * ----------------------------------------------------------------------------- */

/* Macros to derive numeric types */

%define %numeric_type_from(Type, Base)
%fragment(SWIG_From_frag(Type),"header",
	  fragment=SWIG_From_frag(Base)) {
SWIGINTERNINLINE SWIG_Object
SWIG_From_dec(Type)(Type value)
{    
  return SWIG_From(Base)(value);
}
}
%enddef

%define %numeric_type_asval(Type, Base, Frag, OverflowCond)
%fragment(SWIG_AsVal_frag(Type),"header",
	  fragment=Frag,
	  fragment=SWIG_AsVal_frag(Base)) {
SWIGINTERN int
SWIG_AsVal_dec(Type)(SWIG_Object obj, Type *val)
{
  Base v;
  int res = SWIG_AsVal(Base)(obj, &v);
  if (SWIG_IsOK(res)) {
    if (OverflowCond) {
      return SWIG_OverflowError;
    } else {
      if (val) *val = %numeric_cast(v, Type);
    }
  }  
  return res;
}
}
%enddef

#define %numeric_signed_type_asval(Type, Base, Frag, Min, Max) \
%numeric_type_asval(Type, Base, Frag, (v < Min || v > Max))

#define %numeric_unsigned_type_asval(Type, Base, Frag, Max) \
%numeric_type_asval(Type, Base, Frag, (v > Max))


/* Macro for 'signed long' derived types */

%define %numeric_slong(Type, Frag, Min, Max)
%numeric_type_from(Type, long)
%numeric_signed_type_asval(Type, long, Frag , Min, Max)
%enddef

/* Macro for 'unsigned long' derived types */

%define %numeric_ulong(Type, Frag, Max)
%numeric_type_from(Type, unsigned long)
%numeric_unsigned_type_asval(Type, unsigned long, Frag, Max)
%enddef


/* Macro for 'double' derived types */

%define %numeric_double(Type, Frag, Min, Max)
%numeric_type_from(Type, double)
%numeric_signed_type_asval(Type, double, Frag , Min, Max)
%enddef


/* Macros for missing fragments */

%define %ensure_fragment(Fragment)
%fragment(`Fragment`,"header") {
%#error "Swig language implementation must provide the Fragment fragment"
}
%enddef

%define %ensure_type_fragments(Type)
%fragment(SWIG_From_frag(Type),"header") {
%#error "Swig language implementation must provide a SWIG_From_frag(Type) fragment"
}
%fragment(SWIG_AsVal_frag(Type),"header") {
%#error "Swig language implementation must provide a SWIG_AsVal_frag(Type) fragment"
}
%enddef
