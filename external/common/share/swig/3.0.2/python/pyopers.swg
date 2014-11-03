/* ------------------------------------------------------------
 * Overloaded operator support

 The directives in this file apply whether or not you use the
 -builtin option to SWIG, but operator overloads are particularly
 attractive when using -builtin, because they are much faster
 than named methods.

 If you're using the -builtin option to SWIG, and you want to define
 python operator overloads beyond the defaults defined in this file,
 here's what you need to know:

 There are two ways to define a python slot function: dispatch to a
 statically defined function; or dispatch to a method defined on the
 operand.

 To dispatch to a statically defined function, use %feature("python:<slot>"),
 where <slot> is the name of a field in a PyTypeObject, PyNumberMethods,
 PyMappingMethods, PySequenceMethods, or PyBufferProcs.  For example:

   %{
   
   static long myHashFunc (PyObject *pyobj) {
     MyClass *cobj;
     // Convert pyobj to cobj
     return (cobj->field1 * (cobj->field2 << 7));
   }
   
   %}

   %feature("python:tp_hash") MyClass "myHashFunc";

 NOTE: It is the responsibility of the programmer (that's you) to ensure
 that a statically defined slot function has the correct signature.

 If, instead, you want to dispatch to an instance method, you can
 use %feature("python:slot").  For example:

   class MyClass {
     public:
       long myHashFunc () const;
       ...
   };
   
   %feature("python:slot", "tp_hash", functype="hashfunc") MyClass::myHashFunc;

 NOTE: Some python slots use a method signature which does not
 match the signature of SWIG-wrapped methods.  For those slots,
 SWIG will automatically generate a "closure" function to re-marshall
 the arguments before dispatching to the wrapped method.  Setting
 the "functype" attribute of the feature enables SWIG to generate
 a correct closure function.

 --------------------------------------------------------------

 The tp_richcompare slot is a special case: SWIG automatically generates
 a rich compare function for all wrapped types.  If a type defines C++
 operator overloads for comparison (operator==, operator<, etc.), they
 will be called from the generated rich compare function.  If you
 want to explicitly choose a method to handle a certain comparison
 operation, you may use %feature("python:slot") like this:

   class MyClass {
     public:
       bool lessThan (const MyClass& x) const;
       ...
   };
   
   %feature("python:slot", "Py_LT") MyClass::lessThan;

 ... where "Py_LT" is one of the rich comparison opcodes defined in the
 python header file object.h.

 If there's no method defined to handle a particular comparsion operation,
 the default behavior is to compare pointer values of the wrapped
 C++ objects.

 --------------------------------------------------------------


 For more information about python slots, including their names and
 signatures, you may refer to the python documentation :

   http://docs.python.org/c-api/typeobj.html

 * ------------------------------------------------------------ */


#ifdef __cplusplus

#if defined(SWIGPYTHON_BUILTIN)
#define %pybinoperator(pyname,oper,functp,slt) %rename(pyname) oper; %pythonmaybecall oper; %feature("python:slot", #slt, functype=#functp) oper; %feature("python:slot", #slt, functype=#functp) pyname;
#define %pycompare(pyname,oper,comptype) %rename(pyname) oper; %pythonmaybecall oper; %feature("python:compare", #comptype) oper; %feature("python:compare", #comptype) pyname;
#else
#define %pybinoperator(pyname,oper,functp,slt) %rename(pyname) oper; %pythonmaybecall oper
#define %pycompare(pyname,oper,comptype) %pybinoperator(pyname,oper,,comptype)
#endif

%pybinoperator(__add__,      *::operator+,		binaryfunc, nb_add);
%pybinoperator(__pos__,      *::operator+(),		unaryfunc, nb_positive);
%pybinoperator(__pos__,      *::operator+() const,	unaryfunc, nb_positive);
%pybinoperator(__sub__,      *::operator-,		binaryfunc, nb_subtract);
%pybinoperator(__neg__,      *::operator-(),		unaryfunc, nb_negative);
%pybinoperator(__neg__,      *::operator-() const,	unaryfunc, nb_negative);
%pybinoperator(__mul__,      *::operator*,		binaryfunc, nb_multiply);
%pybinoperator(__div__,      *::operator/,		binaryfunc, nb_div);
%pybinoperator(__mod__,      *::operator%,		binaryfunc, nb_remainder);
%pybinoperator(__lshift__,   *::operator<<,		binaryfunc, nb_lshift);
%pybinoperator(__rshift__,   *::operator>>,		binaryfunc, nb_rshift);
%pybinoperator(__and__,      *::operator&,		binaryfunc, nb_and);
%pybinoperator(__or__,       *::operator|,		binaryfunc, nb_or);
%pybinoperator(__xor__,      *::operator^,		binaryfunc, nb_xor);
%pycompare(__lt__,           *::operator<,		Py_LT);
%pycompare(__le__,           *::operator<=,		Py_LE);
%pycompare(__gt__,           *::operator>,		Py_GT);
%pycompare(__ge__,           *::operator>=,		Py_GE);
%pycompare(__eq__,           *::operator==,		Py_EQ);
%pycompare(__ne__,           *::operator!=,		Py_NE);

%feature("python:slot", "nb_truediv", functype="binaryfunc") *::operator/;

/* Special cases */
%rename(__invert__)     *::operator~;
%feature("python:slot", "nb_invert", functype="unaryfunc") *::operator~;
%rename(__call__)       *::operator();
%feature("python:slot", "tp_call", functype="ternarycallfunc") *::operator();

#if defined(SWIGPYTHON_BUILTIN)
%pybinoperator(__nonzero__,   *::operator bool,		inquiry, nb_nonzero);
#else
%feature("shadow")      *::operator bool %{
def __nonzero__(self):
    return $action(self)
__bool__ = __nonzero__
%};
%rename(__nonzero__)    *::operator bool;
#endif

/* Ignored operators */
%ignoreoperator(LNOT)       operator!;
%ignoreoperator(LAND)       operator&&;
%ignoreoperator(LOR)        operator||;
%ignoreoperator(EQ)         *::operator=;
%ignoreoperator(PLUSPLUS)   *::operator++;
%ignoreoperator(MINUSMINUS) *::operator--;
%ignoreoperator(ARROWSTAR)  *::operator->*;
%ignoreoperator(INDEX)      *::operator[];

/*
  Inplace operator declarations.

  They translate the inplace C++ operators (+=, -=, ...)  into the
  corresponding python equivalents(__iadd__,__isub__), etc,
  disabling the ownership of the input 'self' pointer, and assigning
  it to the returning object:  

     %feature("del") *::Operator;
     %feature("new") *::Operator;
  
  This makes the most common case safe, ie:

     A&  A::operator+=(int i) { ...; return *this; }
    ^^^^                                    ^^^^^^

  will work fine, even when the resulting python object shares the
  'this' pointer with the input one. The input object is usually
  deleted after the operation, including the shared 'this' pointer,
  producing 'strange' seg faults, as reported by Lucriz
  (lucriz@sitilandia.it).

  If you have an interface that already takes care of that, ie, you
  already are using inplace operators and you are not getting
  seg. faults, with the new scheme you could end with 'free' elements
  that never get deleted (maybe, not sure, it depends). But if that is
  the case, you could recover the old behaviour using

     %feature("del","") A::operator+=;
     %feature("new","") A::operator+=;

  which recovers the old behaviour for the class 'A', or if you are
  100% sure your entire system works fine in the old way, use:

    %feature("del","") *::operator+=;
    %feature("new","") *::operator+=;

*/

#if defined(SWIGPYTHON_BUILTIN)
#define %pyinplaceoper(SwigPyOper, Oper, functp, slt) %delobject Oper; %newobject Oper; %feature("python:slot", #slt, functype=#functp) Oper; %rename(SwigPyOper) Oper
#else
#define %pyinplaceoper(SwigPyOper, Oper, functp, slt) %delobject Oper; %newobject Oper; %rename(SwigPyOper) Oper
#endif

%pyinplaceoper(__iadd__   , *::operator +=,	binaryfunc, nb_inplace_add);
%pyinplaceoper(__isub__   , *::operator -=,	binaryfunc, nb_inplace_subtract);
%pyinplaceoper(__imul__   , *::operator *=,	binaryfunc, nb_inplace_multiply);
%pyinplaceoper(__idiv__   , *::operator /=,	binaryfunc, nb_inplace_divide);
%pyinplaceoper(__imod__   , *::operator %=,	binaryfunc, nb_inplace_remainder);
%pyinplaceoper(__iand__   , *::operator &=,	binaryfunc, nb_inplace_and);
%pyinplaceoper(__ior__    , *::operator |=,	binaryfunc, nb_inplace_or);
%pyinplaceoper(__ixor__   , *::operator ^=,	binaryfunc, nb_inplace_xor);
%pyinplaceoper(__ilshift__, *::operator <<=,	binaryfunc, nb_inplace_lshift);
%pyinplaceoper(__irshift__, *::operator >>=,	binaryfunc, nb_inplace_rshift);


/* Finally, in python we need to mark the binary operations to fail as
 'maybecall' methods */

#define %pybinopermaybecall(oper) %pythonmaybecall __ ## oper ## __;  %pythonmaybecall __r ## oper ## __

%pybinopermaybecall(add);
%pybinopermaybecall(pos);
%pybinopermaybecall(pos);
%pybinopermaybecall(sub);
%pybinopermaybecall(neg);
%pybinopermaybecall(neg);
%pybinopermaybecall(mul);
%pybinopermaybecall(div);
%pybinopermaybecall(mod);
%pybinopermaybecall(lshift);
%pybinopermaybecall(rshift);
%pybinopermaybecall(and);
%pybinopermaybecall(or);
%pybinopermaybecall(xor);
%pybinopermaybecall(lt);
%pybinopermaybecall(le);
%pybinopermaybecall(gt);
%pybinopermaybecall(ge);
%pybinopermaybecall(eq);
%pybinopermaybecall(ne);

#endif



