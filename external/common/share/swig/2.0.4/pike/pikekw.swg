#ifndef PIKE_PIKEKW_SWG_
#define PIKE_PIKEKW_SWG_

/* Warnings for Pike keywords */
#define PIKEKW(x) %namewarn("314: '" #x "' is a pike keyword")  #x

/*
   from
   http://www.http://docs.linux.cz/pike/tutorial_C.html

*/


PIKEKW(array);
PIKEKW(break);
PIKEKW(case);
PIKEKW(catch);
PIKEKW(continue);
PIKEKW(default);
PIKEKW(do);
PIKEKW(else);
PIKEKW(float);
PIKEKW(for);
PIKEKW(foreach);
PIKEKW(function);
PIKEKW(gauge);
PIKEKW(if);
PIKEKW(inherit);
PIKEKW(inline);
PIKEKW(int);
PIKEKW(lambda);
PIKEKW(mapping);
PIKEKW(mixed);
PIKEKW(multiset);
PIKEKW(nomask);
PIKEKW(object);
PIKEKW(predef);
PIKEKW(private);
PIKEKW(program);
PIKEKW(protected);
PIKEKW(public);
PIKEKW(return);
PIKEKW(sscanf);
PIKEKW(static);
PIKEKW(string);
PIKEKW(switch);
PIKEKW(typeof);
PIKEKW(varargs);
PIKEKW(void);
PIKEKW(while);


#undef PIKEKW

#endif //PIKE_PIKEKW_SWG_
