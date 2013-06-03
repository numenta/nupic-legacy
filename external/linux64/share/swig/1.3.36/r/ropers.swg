#ifdef __cplusplus

// These are auto-supported by the Perl-module
%rename(__plusplus__) *::operator++;
%rename(__minmin__)   *::operator--;
%rename(__add__)      *::operator+;
%rename(__sub__)      *::operator-;
%rename(__neg__)      *::operator-();
%rename(__neg__)      *::operator-() const;
%rename(__mul__)      *::operator*;
%rename(__div__)      *::operator/;
%rename(__eq__)       *::operator==;
%rename(__ne__)       *::operator!=;
%rename(__mod__)      *::operator%;
%rename(__gt__)       *::operator>;
%rename(__lt__)       *::operator<;
%rename(__not__)      *::operator!;

// These are renamed, but no 'use overload...' is added
%rename(__lshift__)   *::operator<<;
%rename(__rshift__)   *::operator>>;
%rename(__and__)      *::operator&;
%rename(__or__)       *::operator|;
%rename(__xor__)      *::operator^;
%rename(__invert__)   *::operator~;
%rename(__le__)       *::operator<=;
%rename(__ge__)       *::operator>=;
%rename(__call__)     *::operator();
%rename(__getitem__)  *::operator[];

%rename(__seteq__)    *::operator=;


%rename(__land__)       operator&&;
%rename(__lor__)        operator||;
%rename(__plusplus__)   *::operator++;
%rename(__minusminus__) *::operator--;
%rename(__arrowstar__)  *::operator->*;
%rename(__index__)      *::operator[];

%rename(Equal) operator =;
%rename(PlusEqual) operator +=;
%rename(MinusEqual) operator -=;
%rename(MultiplyEqual) operator *=;
%rename(DivideEqual) operator /=;
%rename(PercentEqual) operator %=;
%rename(Plus) operator +;
%rename(Minus) operator -;
%rename(Multiply) operator *;
%rename(Divide) operator /;
%rename(Percent) operator %;
%rename(Not) operator !;
%rename(IndexIntoConst) operator[](unsigned idx) const;
%rename(IndexInto) operator[](unsigned idx);
%rename(Functor) operator ();
%rename(EqualEqual) operator ==;
%rename(NotEqual) operator !=;
%rename(LessThan) operator <;
%rename(LessThanEqual) operator <=;
%rename(GreaterThan) operator >;
%rename(GreaterThanEqual) operator >=;
%rename(And) operator &&;
%rename(Or) operator ||;
%rename(PlusPlusPrefix) operator++();
%rename(PlusPlusPostfix) operator++(int);
%rename(MinusMinusPrefix) operator--();
%rename(MinusMinusPostfix) operator--(int);


#endif
