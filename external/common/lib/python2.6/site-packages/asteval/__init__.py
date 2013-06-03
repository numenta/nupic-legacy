"""
   ASTEVAL provides a numpy-aware, safe(ish) "eval" function

   Emphasis is on mathematical expressions, and so numpy ufuncs
   are used if available.  Symbols are held in the Interpreter
   symbol table 'symtable':  a simple dictionary supporting a
   simple, flat namespace.

   Expressions can be compiled into ast node for later evaluation,
   using the values in the symbol table current at evaluation time.

   using python, ast module to parse a python expression.

   version: 0.9
   last update: 7-Apr-2012
   License:  BSD
   Author:  Matthew Newville <newville@cars.uchicago.edu>
            Center for Advanced Radiation Sources,
            The University of Chicago
"""
__version__ = '0.9'

from .asteval import Interpreter
from .astutils import NameFinder, valid_symbol_name

__all__ = [Interpreter, NameFinder, valid_symbol_name]
