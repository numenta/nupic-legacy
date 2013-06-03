"""
Safe(ish) evaluator of python expressions, using ast module.
The emphasis here is on mathematical expressions, and so
numpy functions are imported if available and used.

Symbols are held in the Interpreter symtable -- a simple
dictionary supporting a simple, flat namespace.

Expressions can be compiled into ast node and then evaluated
later, using the current values in the
"""

from __future__ import division, print_function
from sys import exc_info, stdout, version_info
import ast
import math

from .astutils import (FROM_PY, FROM_MATH, FROM_NUMPY,
                       NUMPY_RENAMES, op2func, ExceptionHolder,
                       valid_symbol_name)
HAS_NUMPY = False
try:
    import numpy
    HAS_NUMPY = True
except ImportError:
    print("Warning: numpy not available... functionality will be limited.")

__version__ = '0.3'

class Interpreter:
    """mathematical expression compiler and interpreter.

  This module compiles expressions and statements to AST representation,
  using python's ast module, and then executes the AST representation
  using a dictionary of named object (variable, functions).

  This then gives a restricted version of Python, being a procedural
  language (though working on Python objects) with a simplified, flat
  namespace (this is overcome in related implementaions). The program
  syntax here is expected to be valid Python.

  The following Python syntax elements are not supported:
      Import, Exec, Lambda, Class, Global, Generators,
      Yield, Decorators, Finally for Try-Except

  Many parts of Python syntax are supported, including:
     advanced slicing:    a[::-1], array[-3:, :, ::2]
     if-expressions:      out = one_thing if TEST else other
     list comprehension
     for-loops, while-loops
     if-then-elif-else conditionals
     try-except (but not the 'finally' variant...)
     function definitions with def
  """

    supported_nodes = ('arg', 'assert', 'assign', 'attribute', 'augassign',
                       'binop', 'boolop', 'break', 'call', 'compare',
                       'continue', 'delete', 'dict', 'ellipsis',
                       'excepthandler', 'expr', 'extslice', 'for',
                       'functiondef', 'if', 'ifexp', 'index', 'interrupt',
                       'list', 'listcomp', 'module', 'name', 'num', 'pass',
                       'print', 'raise', 'repr', 'return', 'slice', 'str',
                       'subscript', 'tryexcept', 'tuple', 'unaryop',
                       'while')

    def __init__(self, symtable=None, writer=None, use_numpy=True):
        self.writer = writer or stdout

        if symtable is None:
            symtable = {}
        self.symtable   = symtable
        self._interrupt = None
        self.error      = []
        self.expr       = None
        self.retval     = None
        self.lineno    = 0
        global HAS_NUMPY
        if not use_numpy:
            HAS_NUMPY = False

        symtable['print'] = self._printer
        for sym in FROM_PY:
            if sym in __builtins__:
                symtable[sym] = __builtins__[sym]
        for sym in FROM_MATH:
            if hasattr(math, sym):
                symtable[sym] = getattr(math, sym)

        if HAS_NUMPY:
            for sym in FROM_NUMPY:
                if hasattr(numpy, sym):
                    symtable[sym] = getattr(numpy, sym)
            for name, sym in NUMPY_RENAMES.items():
                if hasattr(numpy, sym):
                    symtable[name] = getattr(numpy, sym)

        self.node_handlers = dict(((node, getattr(self, "on_%s" % node))
                                   for node in self.supported_nodes))

    def unimplemented(self, node):
        "unimplemented nodes"
        self.raise_exception(node, exc=NotImplementedError,
                             msg="'%s' not supported" % (node.__class__.__name__))

    def raise_exception(self, node, exc=None, msg='', expr=None,
                        lineno=None):
        "add an exception"
        if self.error is None:
            self.error = []
        if expr  is None:
            expr  = self.expr
        if len(self.error) > 0 and not isinstance(node, ast.Module):
            msg = '%s' % msg
        err = ExceptionHolder(node, exc=exc, msg=msg, expr=expr, lineno=lineno)
        self._interrupt = ast.Break()
        self.error.append(err)
        raise RuntimeError

    # main entry point for Ast node evaluation
    #  parse:  text of statements -> ast
    #  run:    ast -> result
    #  eval:   string statement -> result = run(parse(statement))
    def parse(self, text):
        """parse statement/expression to Ast representation"""
        self.expr  = text
        try:
            return ast.parse(text)
        except:
            self.raise_exception(None, exc=SyntaxError,
                                 msg='Syntax Error', expr=text)

    def run(self, node, expr=None, lineno=None, with_raise=True):
        """executes parsed Ast representation for an expression"""
        # Note: keep the 'node is None' test: internal code here may run
        #    run(None) and expect a None in return.
        if node is None:
            return None
        if isinstance(node, str):
            node = self.parse(node)
        if lineno is not None:
            self.lineno = lineno

        if expr   is not None:
            self.expr   = expr

        # get handler for this node:
        #   on_xxx with handle nodes of type 'xxx', etc
        try:
            handler = self.node_handlers[node.__class__.__name__.lower()]
        except KeyError:
            return self.unimplemented(node)

        # run the handler:  this will likely generate
        # recursive calls into this run method.
        try:
            ret = handler(node)
            if isinstance(ret, enumerate):
                ret = list(ret)
            return ret
        except:
            if with_raise:
                self.raise_exception(node, expr=expr)

    def __call__(self, expr, **kw):
        return self.eval(expr, **kw)

    def eval(self, expr, lineno=0, show_errors=True):
        """evaluates a single statement"""
        self.lineno = lineno
        self.error = []
        try:
            node = self.parse(expr)
        except RuntimeError:
            errmsg = exc_info()[1]
            if len(self.error) > 0:
                errmsg = "\n".join(self.error[0].get_error())
            if not show_errors:
                raise RuntimeError(errmsg)
            print(errmsg, file=self.writer)
            return
        out = None
        try:
            return self.run(node, expr=expr, lineno=lineno)
        except RuntimeError:
            errmsg = exc_info()[1]
            if len(self.error) > 0:
                errmsg = "\n".join(self.error[0].get_error())
            if not show_errors:
                raise RuntimeError(errmsg)
            print(errmsg, file=self.writer)
            return

    def dump(self, node, **kw):
        "simple ast dumper"
        return ast.dump(node, **kw)

    # handlers for ast components
    def on_expr(self, node):
        "expression"
        return self.run(node.value)  # ('value',)

    def on_index(self, node):
        "index"
        return self.run(node.value)  # ('value',)

    def on_return(self, node): # ('value',)
        "return statement"
        self.retval = self.run(node.value)
        return

    def on_repr(self, node):
        "repr "
        return repr(self.run(node.value))  # ('value',)

    def on_module(self, node):    # ():('body',)
        "module def"
        out = None
        for tnode in node.body:
            out = self.run(tnode)
        return out

    def on_pass(self, node):
        "pass statement"
        return None  # ()

    def on_ellipsis(self, node):
        "ellipses"
        return Ellipsis

    # for break and continue: set the instance variable _interrupt
    def on_interrupt(self, node):    # ()
        "interrupt handler"
        self._interrupt = node
        return node

    def on_break(self, node):
        "break"
        return self.on_interrupt(node)

    def on_continue(self, node):
        "continue"
        return self.on_interrupt(node)

    def on_assert(self, node):    # ('test', 'msg')
        "assert statement"
        if not self.run(node.test):
            self.raise_exception(node, exc=AssertionError, msg=node.msg)
        return True

    def on_list(self, node):    # ('elt', 'ctx')
        "list"
        return [self.run(e) for e in node.elts]

    def on_tuple(self, node):    # ('elts', 'ctx')
        "tuple"
        return tuple(self.on_list(node))

    def on_dict(self, node):    # ('keys', 'values')
        "dictionary"
        return dict([(self.run(k), self.run(v)) for k, v in \
                     zip(node.keys, node.values)])

    def on_num(self, node): # ('n',)
        'return number'
        return node.n

    def on_str(self, node): # ('s',)
        'return string'
        return node.s

    def on_name(self, node):    # ('id', 'ctx')
        """ Name node """
        ctx = node.ctx.__class__
        if ctx in (ast.Param, ast.Del):
            return str(node.id)
        else:
            if node.id in self.symtable:
                return self.symtable[node.id]
            else:
                msg = "name '%s' is not defined" % node.id
                self.raise_exception(node, exc=NameError, msg=msg)

    def node_assign(self, node, val):
        """here we assign a value (not the node.value object) to a node
        this is used by on_assign, but also by for, list comprehension, etc.
        """
        if node.__class__ == ast.Name:
            if not valid_symbol_name(node.id):
                errmsg = "invalid symbol name (reserved word?) %s" % node.id
                self.raise_exception(node, exc=NameError, msg=errmsg)
            sym = self.symtable[node.id] = val
        elif node.__class__ == ast.Attribute:
            if node.ctx.__class__  == ast.Load:
                msg = "cannot assign to attribute %s" % node.attr
                self.raise_exception(node, exc=AttributeError, msg=msg)

            setattr(self.run(node.value), node.attr, val)

        elif node.__class__ == ast.Subscript:
            sym    = self.run(node.value)
            xslice = self.run(node.slice)
            if isinstance(node.slice, ast.Index):
                sym[xslice] = val
            elif isinstance(node.slice, ast.Slice):
                sym[slice(xslice.start, xslice.stop)] = val
            elif isinstance(node.slice, ast.ExtSlice):
                sym[(xslice)] = val
        elif node.__class__ in (ast.Tuple, ast.List):
            if len(val) == len(node.elts):
                for telem, tval in zip(node.elts, val):
                    self.node_assign(telem, tval)
            else:
                raise ValueError('too many values to unpack')

    def on_attribute(self, node):    # ('value', 'attr', 'ctx')
        "extract attribute"
        ctx = node.ctx.__class__
        if ctx == ast.Load:
            sym = self.run(node.value)
            if hasattr(sym, node.attr):
                return getattr(sym, node.attr)
            else:
                obj = self.run(node.value)
                fmt = "%s does not have attribute '%s'"
                msg = fmt % (obj, node.attr)
                self.raise_exception(node, exc=AttributeError, msg=msg)

        elif ctx == ast.Del:
            return delattr(sym, node.attr)
        elif ctx == ast.Store:
            msg = "attribute for storage: shouldn't be here!"
            self.raise_exception(node, exc=RuntimeError, msg=msg)

    def on_assign(self, node):    # ('targets', 'value')
        "simple assignment"
        val = self.run(node.value)
        for tnode in node.targets:
            self.node_assign(tnode, val)
        return # return val

    def on_augassign(self, node):    # ('target', 'op', 'value')
        "augmented assign"
        return self.on_assign(ast.Assign(targets=[node.target],
                                         value=ast.BinOp(left = node.target,
                                                         op = node.op,
                                                         right= node.value)))

    def on_slice(self, node):    # ():('lower', 'upper', 'step')
        "simple slice"
        return slice(self.run(node.lower),
                     self.run(node.upper),
                     self.run(node.step))


    def on_extslice(self, node):    # ():('dims',)
        "extended slice"
        return tuple([self.run(tnode) for tnode in node.dims])

    def on_subscript(self, node):    # ('value', 'slice', 'ctx')
        "subscript handling -- one of the tricky parts"
        val    = self.run(node.value)
        nslice = self.run(node.slice)
        ctx = node.ctx.__class__
        if ctx in ( ast.Load, ast.Store):
            if isinstance(node.slice, (ast.Index, ast.Slice, ast.Ellipsis)):
                return val.__getitem__(nslice)
            elif isinstance(node.slice, ast.ExtSlice):
                return val[(nslice)]
        else:
            msg = "subscript with unknown context"
            self.raise_exception(node, msg=msg)

    def on_delete(self, node):    # ('targets',)
        "delete statement"
        for tnode in node.targets:
            if tnode.ctx.__class__ != ast.Del:
                break
            children = []
            while tnode.__class__ == ast.Attribute:
                children.append(tnode.attr)
                tnode = tnode.value

            if tnode.__class__ == ast.Name:
                children.append(tnode.id)
                children.reverse()
                self.symtable.pop('.'.join(children))
            else:
                msg = "could not delete symbol"
                self.raise_exception(node, msg=msg)

    def on_unaryop(self, node):    # ('op', 'operand')
        "unary operator"
        return op2func(node.op)(self.run(node.operand))

    def on_binop(self, node):    # ('left', 'op', 'right')
        "binary operator"
        return op2func(node.op)(self.run(node.left),
                                self.run(node.right))

    def on_boolop(self, node):    # ('op', 'values')
        "boolean operator"
        val = self.run(node.values[0])
        is_and = ast.And == node.op.__class__
        if (is_and and val) or (not is_and and not val):
            for n in node.values:
                val = op2func(node.op)(val, self.run(n))
                if (is_and and not val) or (not is_and and val):
                    break
        return val

    def on_compare(self, node):    # ('left', 'ops', 'comparators')
        "comparison operators"
        lval = self.run(node.left)
        out  = True
        for op, rnode in zip(node.ops, node.comparators):
            rval = self.run(rnode)
            out  = op2func(op)(lval, rval)
            lval = rval
            if HAS_NUMPY and isinstance(out, numpy.ndarray) and out.any():
                break
            elif not out:
                break
        return out

    def on_print(self, node):    # ('dest', 'values', 'nl')
        """ note: implements Python2 style print statement, not
        print() function.  May need improvement...."""
        dest = self.run(node.dest) or self.writer
        end = ''
        if node.nl:
            end = '\n'
        out = [self.run(tnode) for tnode in node.values]
        if out and len(self.error)==0:
            self._printer(*out, file=dest, end=end)

    def _printer(self, *out, **kws):
        "generic print function"
        flush = kws.pop('flush', True)
        file = kws.pop('file', self.writer)
        sep = kws.pop('sep', ' ')
        end = kws.pop('sep', '\n')

        print(*out, file=file, sep=sep, end=end)
        if flush:
            file.flush()

    def on_if(self, node):    # ('test', 'body', 'orelse')
        "regular if-then-else statement"
        block = node.body
        if not self.run(node.test):
            block = node.orelse
        for tnode in block:
            self.run(tnode)

    def on_ifexp(self, node):    # ('test', 'body', 'orelse')
        "if expressions"
        expr = node.orelse
        if self.run(node.test):
            expr = node.body
        return self.run(expr)

    def on_while(self, node):    # ('test', 'body', 'orelse')
        "while blocks"
        while self.run(node.test):
            self._interrupt = None
            for tnode in node.body:
                self.run(tnode)
                if self._interrupt is not None:
                    break
            if isinstance(self._interrupt, ast.Break):
                break
        else:
            for tnode in node.orelse:
                self.run(tnode)
        self._interrupt = None

    def on_for(self, node):    # ('target', 'iter', 'body', 'orelse')
        "for blocks"
        for val in self.run(node.iter):
            self.node_assign(node.target, val)
            self._interrupt = None
            for tnode in node.body:
                self.run(tnode)
                if self._interrupt is not None:
                    break
            if isinstance(self._interrupt, ast.Break):
                break
        else:
            for tnode in node.orelse:
                self.run(tnode)
        self._interrupt = None

    def on_listcomp(self, node):    # ('elt', 'generators')
        "list comprehension"
        out = []
        for tnode in node.generators:
            if tnode.__class__ == ast.comprehension:
                for val in self.run(tnode.iter):
                    self.node_assign(tnode.target, val)
                    add = True
                    for cond in tnode.ifs:
                        add = add and self.run(cond)
                    if add:
                        out.append(self.run(node.elt))
        return out

    def on_excepthandler(self, node): # ('type', 'name', 'body')
        "exception handler..."
        return (self.run(node.type), node.name, node.body)

    def on_tryexcept(self, node):    # ('body', 'handlers', 'orelse')
        "try/except blocks"
        no_errors = True
        for tnode in node.body:
            self.run(tnode, with_raise=False)
            no_errors = no_errors and len(self.error) == 0
            if len(self.error) > 0:
                e_type, e_value, e_tback = self.error[-1].exc_info
                for hnd in node.handlers:
                    htype = None
                    if hnd.type is not None:
                        htype = __builtins__.get(hnd.type.id, None)
                    if htype is None or isinstance(e_type(), htype):
                        self.error = []
                        if hnd.name is not None:
                            self.node_assign(hnd.name, e_value)
                        for tline in hnd.body:
                            self.run(tline)
                        break
        if no_errors:
            for tnode in node.orelse:
                self.run(tnode)

    def on_raise(self, node):    # ('type', 'inst', 'tback')
        "raise statement: note difference for python 2 and 3"
        if version_info[0] == 3:
            excnode  = node.exc
            msgnode  = node.cause
        else:
            excnode  = node.type
            msgnode  = node.inst
        out  = self.run(excnode)
        msg = ' '.join(out.args)
        msg2 = self.run(msgnode)
        if msg2 not in (None, 'None'):
            msg = "%s: %s" % (msg, msg2)
        self.raise_exception(None, exc=out.__class__, msg=msg, expr='')

    def on_call(self, node):
        "function execution"
        #  ('func', 'args', 'keywords', 'starargs', 'kwargs')
        func = self.run(node.func)
        if not hasattr(func, '__call__') and not isinstance(func, type):
            msg = "'%s' is not callable!!" % (func)
            self.raise_exception(node, exc=TypeError, msg=msg)

        args = [self.run(targ) for targ in node.args]
        if node.starargs is not None:
            args = args + self.run(node.starargs)

        keywords = {}
        for key in node.keywords:
            if not isinstance(key, ast.keyword):
                msg = "keyword error in function call '%s'" % (func)
                self.raise_exception(node, msg=msg)

            keywords[key.arg] = self.run(key.value)
        if node.kwargs is not None:
            keywords.update(self.run(node.kwargs))

        try:
            return func(*args, **keywords)
        except:
            self.raise_exception(node, exc=RuntimeError, msg = "Error running %s" % (func))

    def on_arg(self, node):    # ('test', 'msg')
        "arg for function definitions"
        # print(" ON ARG ! ", node, node.arg)
        return node.arg

    def on_functiondef(self, node):
        "define procedures"
        # ('name', 'args', 'body', 'decorator_list')
        if node.decorator_list != []:
            raise Warning("decorated procedures not supported!")
        kwargs = []

        offset = len(node.args.args) - len(node.args.defaults)
        for idef, defnode in enumerate(node.args.defaults):
            defval = self.run(defnode)
            keyval = self.run(node.args.args[idef+offset])
            kwargs.append((keyval, defval))

        if version_info[0] == 3:
            args = [tnode.arg for tnode in node.args.args[:offset]]
        else:
            args = [tnode.id for tnode in node.args.args[:offset]]

        doc = None
        if (isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Str)):
            docnode = node.body[0]
            doc = docnode.value.s

        self.symtable[node.name] = Procedure(node.name, self, doc=doc,
                                             body = node.body,
                                             lineno = self.lineno,
                                             args = args,
                                             kwargs = kwargs,
                                             vararg = node.args.vararg,
                                             varkws = node.args.kwarg)

class Procedure(object):
    """Procedure: user-defined function for asteval

    This stores the parsed ast nodes as from the
    'functiondef' ast node for later evaluation.
    """
    def __init__(self, name, interp, doc=None, lineno=0,
                 body=None, args=None, kwargs=None,
                 vararg=None, varkws=None):
        self.name = name
        self.interpreter = interp
        self.raise_exc = self.interpreter.raise_exception
        self.__doc__ = doc
        self.body = body
        self.argnames = args
        self.kwargs = kwargs
        self.vararg = vararg
        self.varkws = varkws
        self.lineno = lineno

    def __repr__(self):
        sig = ""
        if len(self.argnames) > 0:
            sig = "%s%s" % (sig, ', '.join(self.argnames))
        if self.vararg is not None:
            sig = "%s, *%s" % (sig, self.vararg)
        if len(self.kwargs) > 0:
            if len(sig) > 0:
                sig = "%s, " % sig
            _kw = ["%s=%s" % (k, v) for k, v in self.kwargs]
            sig = "%s%s" % (sig, ', '.join(_kw))

        if self.varkws is not None:
            sig = "%s, **%s" % (sig, self.varkws)
        sig = "<Procedure %s(%s)>" % (self.name, sig)
        if self.__doc__ is not None:
            sig = "%s\n  %s" % (sig, self.__doc__)
        return sig

    def __call__(self, *args, **kwargs):
        symlocals = {}
        args = list(args)
        n_args = len(args)
        n_names = len(self.argnames)
        n_kws = len(kwargs)

        # may need to move kwargs to args if names align!
        if (n_args < n_names) and n_kws > 0:
            for name in self.argnames[n_args:]:
                if name in kwargs:
                    args.append(kwargs.pop(name))
            n_args = len(args)
            n_names = len(self.argnames)
            n_kws = len(kwargs)

        if len(self.argnames) > 0 and kwargs is not None:
            msg = "got multiple values for keyword argument '%s' in Procedure %s"

            for targ in self.argnames:
                if targ in kwargs:
                    self.raise_exc(None, exc=TypeError,
                                   msg=msg % (targ, self.name),
                                   lineno=self.lineno)

        if n_args != n_names:
            msg = None
            if n_args < n_names:
                msg = 'not enough arguments for Procedure %s()' % self.name
                msg = '%s (expected %i, got %i)'% (msg, n_names, n_args)
                self.raise_exc(None, exc=TypeError, msg=msg)


        for argname in self.argnames:
            symlocals[argname] = args.pop(0)

        try:
            if self.vararg is not None:
                symlocals[self.vararg] = tuple(args)

            for key, val in self.kwargs:
                if key in kwargs:
                    val = kwargs.pop(key)
                symlocals[key] = val

            if self.varkws is not None:
                symlocals[self.varkws] = kwargs

            elif len(kwargs) > 0:
                msg = 'extra keyword arguments for Procedure %s (%s)'
                msg = msg % (self.name, ','.join(list(kwargs.keys())))
                self.raise_exc(None, msg=msg, exc=TypeError,
                               lineno=self.lineno)

        except (ValueError, LookupError, TypeError,
                NameError, AttributeError):
            msg = 'incorrect arguments for Procedure %s' % self.name
            self.raise_exc(None, msg=msg, lineno=self.lineno)

        save_symtable = self.interpreter.symtable.copy()
        self.interpreter.symtable.update(symlocals)
        self.interpreter.retval = None
        retval = None

        # evaluate script of function
        for node in self.body:
            self.interpreter.run(node, expr='<>', lineno=self.lineno)
            if len(self.interpreter.error) > 0:
                break
            if self.interpreter.retval is not None:
                retval = self.interpreter.retval
                break

        self.interpreter.symtable = save_symtable
        symlocals = None
        return retval
