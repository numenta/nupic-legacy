#ifndef CHICKEN_CHICKENKW_SWG_
#define CHICKEN_CHICKENKW_SWG_

/* Warnings for certain CHICKEN keywords. From Section 7.1.1 of
   Revised^5 Report on the Algorithmic Language Scheme */
#define CHICKENKW(x) %namewarn("314: '" #x "' is a R^5RS syntatic keyword")  #x

CHICKENKW(else);
CHICKENKW(=>);
CHICKENKW(define);
CHICKENKW(unquote);
CHICKENKW(unquote-splicing);
CHICKENKW(quote);
CHICKENKW(lambda);
CHICKENKW(if);
CHICKENKW(set!);
CHICKENKW(begin);
CHICKENKW(cond);
CHICKENKW(and);
CHICKENKW(or);
CHICKENKW(case);
CHICKENKW(let);
CHICKENKW(let*);
CHICKENKW(letrec);
CHICKENKW(do);
CHICKENKW(delay);
CHICKENKW(quasiquote);

#undef CHICKENKW 

#endif //CHICKEN_CHICKENKW_SWG_
