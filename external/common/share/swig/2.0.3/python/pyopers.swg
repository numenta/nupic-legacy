/* ------------------------------------------------------------
 * Overloaded operator support
 * ------------------------------------------------------------ */


#ifdef __cplusplus

#define %pybinoperator(pyname,oper) %rename(pyname) oper; %pythonmaybecall oper

%pybinoperator(__add__,      *::operator+);
%pybinoperator(__pos__,      *::operator+());
%pybinoperator(__pos__,      *::operator+() const);
%pybinoperator(__sub__,      *::operator-);
%pybinoperator(__neg__,      *::operator-());
%pybinoperator(__neg__,      *::operator-() const);
%pybinoperator(__mul__,      *::operator*);
%pybinoperator(__div__,      *::operator/);
%pybinoperator(__mod__,      *::operator%);
%pybinoperator(__lshift__,   *::operator<<);
%pybinoperator(__rshift__,   *::operator>>);
%pybinoperator(__and__,      *::operator&);
%pybinoperator(__or__,       *::operator|);
%pybinoperator(__xor__,      *::operator^);
%pybinoperator(__lt__,       *::operator<);
%pybinoperator(__le__,       *::operator<=);
%pybinoperator(__gt__,       *::operator>);
%pybinoperator(__ge__,       *::operator>=);
%pybinoperator(__eq__,       *::operator==);
%pybinoperator(__ne__,       *::operator!=);



/* Special cases */
%rename(__invert__)     *::operator~;
%rename(__call__)       *::operator();

%feature("shadow")      *::operator bool %{
def __nonzero__(self):
    return $action(self)
__bool__ = __nonzero__
%};
%rename(__nonzero__)    *::operator bool;

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

#define %pyinplaceoper(SwigPyOper, Oper) %delobject Oper; %newobject Oper; %rename(SwigPyOper) Oper

%pyinplaceoper(__iadd__   , *::operator +=);
%pyinplaceoper(__isub__   , *::operator -=);
%pyinplaceoper(__imul__   , *::operator *=);
%pyinplaceoper(__idiv__   , *::operator /=);
%pyinplaceoper(__imod__   , *::operator %=);
%pyinplaceoper(__iand__   , *::operator &=);
%pyinplaceoper(__ior__    , *::operator |=);
%pyinplaceoper(__ixor__   , *::operator ^=);
%pyinplaceoper(__ilshift__, *::operator <<=);
%pyinplaceoper(__irshift__, *::operator >>=);


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



