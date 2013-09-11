/*
  Warnings for Python keywords, built-in names and bad names.
*/

#define PYTHONKW(x) %keywordwarn("'" `x` "' is a python keyword, renaming to '_" `x` "'", rename="_%s")  `x`
#define PYTHONBN(x) %builtinwarn("'" `x` "' conflicts with a built-in name in python")  "::"`x`


/*
  Warnings for Python keywords 
  http://www.fnorb.org/docs/1.2/Fnorb-Guide/node62.html
*/

PYTHONKW(and);
PYTHONKW(assert);
PYTHONKW(break);
PYTHONKW(class);
PYTHONKW(continue);
PYTHONKW(def);
PYTHONKW(del);
PYTHONKW(elif);
PYTHONKW(else);
PYTHONKW(except);
PYTHONKW(exec);
PYTHONKW(finally);
PYTHONKW(for);
PYTHONKW(from);
PYTHONKW(global);
PYTHONKW(if);
PYTHONKW(import);
PYTHONKW(in);
PYTHONKW(is);
PYTHONKW(lambda);
PYTHONKW(not);
PYTHONKW(or);
PYTHONKW(pass);
PYTHONKW(print);
PYTHONKW(raise);
PYTHONKW(return);
PYTHONKW(try);
PYTHONKW(while);
PYTHONKW(yield);

/*
  built-in functions
  http://www.zvon.org/other/python/doc21/lib/built-in-funcs.html
 */ 

PYTHONBN(abs);
PYTHONBN(apply);
PYTHONBN(bool);
PYTHONBN(buffer);
PYTHONBN(callable);
PYTHONBN(chr);
PYTHONBN(classmethod);
PYTHONBN(cmp);
PYTHONBN(coerce);
PYTHONBN(compile);
PYTHONBN(complex);
PYTHONBN(delattr);
PYTHONBN(dict);
PYTHONBN(dir);
PYTHONBN(divmod);
PYTHONBN(enumerate);
PYTHONBN(eval);
PYTHONBN(execfile);
PYTHONBN(file);
PYTHONBN(filter);
PYTHONBN(float);
PYTHONBN(frozenset);
PYTHONBN(getattr);
PYTHONBN(globals);
PYTHONBN(hasattr);
PYTHONBN(hash);
PYTHONBN(hex);
PYTHONBN(id);
PYTHONBN(input);
PYTHONBN(int);
PYTHONBN(intern);
PYTHONBN(isinstance);
PYTHONBN(issubclass);
PYTHONBN(iter);
PYTHONBN(len);
PYTHONBN(list);
PYTHONBN(locals);
PYTHONBN(long);
PYTHONBN(map);
PYTHONBN(max);
PYTHONBN(min);
PYTHONBN(object);
PYTHONBN(oct);
PYTHONBN(open);
PYTHONBN(ord);
PYTHONBN(pow);
PYTHONBN(property);
PYTHONBN(range);
PYTHONBN(raw_input);
PYTHONBN(reduce);
PYTHONBN(reload);
PYTHONBN(repr);
PYTHONBN(reversed);
PYTHONBN(round);
PYTHONBN(set);
PYTHONBN(setattr);
PYTHONBN(slice);
PYTHONBN(sorted);
PYTHONBN(staticmethod);
PYTHONBN(staticmethod);
PYTHONBN(str);
PYTHONBN(sum);
PYTHONBN(super);
PYTHONBN(tuple);
PYTHONBN(type);
PYTHONBN(unichr);
PYTHONBN(unicode);
PYTHONBN(vars);
PYTHONBN(xrange);
PYTHONBN(zip);


/* 
   built-in names
   boolean type and None
*/
PYTHONBN(True);
PYTHONBN(False);
PYTHONBN(None);


/* 
   'self' is also a bad Name
*/
PYTHONBN(self);

#undef PYTHONBN
#undef PYTHONKW
