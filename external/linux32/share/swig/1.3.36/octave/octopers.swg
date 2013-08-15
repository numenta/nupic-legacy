/* ------------------------------------------------------------
 * Overloaded operator support
 * ------------------------------------------------------------ */

#ifdef __cplusplus

// operators supported in Octave, and the methods they are routed to

// __brace      a{args}
// __brace_asgn a{args} = rhs
// __paren      a(args)
// __paren_asgn a(args) = rhs
// __str        generates string rep

// __not        !a
// __uplus      +a
// __uminus     -a
// __transpose  a.'
// __hermitian  a'
// __incr       a++
// __decr       a--
// __add        a + b
// __sub        a - b
// __mul        a * b
// __div        a / b
// __pow        a ^ b
// __ldiv       a \ b
// __lshift     a << b
// __rshift     a >> b
// __lt         a < b
// __le         a <= b
// __eq         a == b
// __ge         a >= b
// __gt         a > b
// __ne         a != b
// __el_mul     a .* b
// __el_div     a ./ b
// __el_pow     a .^ b
// __el_ldiv    a .\ b
// __el_and     a & b
// __el_or      a | b

// operators supported in C++, and the methods that route to them

%rename(__add)       *::operator+;
%rename(__add)       *::operator+();
%rename(__add)       *::operator+() const;
%rename(__sub)       *::operator-;
%rename(__uminus)    *::operator-();
%rename(__uminus)    *::operator-() const;
%rename(__mul)       *::operator*;
%rename(__div)       *::operator/;
%rename(__mod)       *::operator%;
%rename(__lshift)    *::operator<<;
%rename(__rshift)    *::operator>>;
%rename(__el_and)    *::operator&&;
%rename(__el_or)     *::operator||;
%rename(__xor)       *::operator^;
%rename(__invert)    *::operator~;
%rename(__lt)        *::operator<;
%rename(__le)        *::operator<=;
%rename(__gt)        *::operator>;
%rename(__ge)        *::operator>=;
%rename(__eq)        *::operator==;
%rename(__ne)        *::operator!=;
%rename(__not)       *::operator!;
%rename(__incr)      *::operator++;
%rename(__decr)      *::operator--;
%rename(__paren)     *::operator();
%rename(__brace)     *::operator[];

// Ignored inplace operators
%ignoreoperator(PLUSEQ)     operator+=;
%ignoreoperator(MINUSEQ)    operator-=;
%ignoreoperator(MULEQ)      operator*=;
%ignoreoperator(DIVEQ)      operator/=;
%ignoreoperator(MODEQ)      operator%=;
%ignoreoperator(LSHIFTEQ)   operator<<=;
%ignoreoperator(RSHIFTEQ)   operator>>=;
%ignoreoperator(ANDEQ)      operator&=;
%ignoreoperator(OREQ)       operator|=;
%ignoreoperator(XOREQ)      operator^=;

// Ignored operators
%ignoreoperator(EQ)         operator=;
%ignoreoperator(ARROWSTAR)  operator->*;

#endif /* __cplusplus */
