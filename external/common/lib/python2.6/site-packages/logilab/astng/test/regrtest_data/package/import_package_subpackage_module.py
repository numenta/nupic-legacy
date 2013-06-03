# pylint: disable-msg=I0011,C0301,W0611
# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
# copyright 2003-2010 Sylvain Thenault, all rights reserved.
# contact mailto:thenault@gmail.com
#
# This file is part of logilab-astng.
#
# logilab-astng is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 2.1 of the License, or (at your
# option) any later version.
#
# logilab-astng is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-astng. If not, see <http://www.gnu.org/licenses/>.
"""I found some of my scripts trigger off an AttributeError in pylint
0.8.1 (with common 0.12.0 and astng 0.13.1).

Traceback (most recent call last):
  File "/usr/bin/pylint", line 4, in ?
    lint.Run(sys.argv[1:])
  File "/usr/lib/python2.4/site-packages/pylint/lint.py", line 729, in __init__
    linter.check(args)
  File "/usr/lib/python2.4/site-packages/pylint/lint.py", line 412, in check
    self.check_file(filepath, modname, checkers)
  File "/usr/lib/python2.4/site-packages/pylint/lint.py", line 426, in check_file
    astng = self._check_file(filepath, modname, checkers)
  File "/usr/lib/python2.4/site-packages/pylint/lint.py", line 450, in _check_file
    self.check_astng_module(astng, checkers)
  File "/usr/lib/python2.4/site-packages/pylint/lint.py", line 494, in check_astng_module
    self.astng_events(astng, [checker for checker in checkers
  File "/usr/lib/python2.4/site-packages/pylint/lint.py", line 511, in astng_events
    self.astng_events(child, checkers, _reversed_checkers)
  File "/usr/lib/python2.4/site-packages/pylint/lint.py", line 511, in astng_events
    self.astng_events(child, checkers, _reversed_checkers)
  File "/usr/lib/python2.4/site-packages/pylint/lint.py", line 508, in astng_events
    checker.visit(astng)
  File "/usr/lib/python2.4/site-packages/logilab/astng/utils.py", line 84, in visit
    method(node)
  File "/usr/lib/python2.4/site-packages/pylint/checkers/variables.py", line 295, in visit_import
    self._check_module_attrs(node, module, name_parts[1:])
  File "/usr/lib/python2.4/site-packages/pylint/checkers/variables.py", line 357, in _check_module_attrs
    self.add_message('E0611', args=(name, module.name),
AttributeError: Import instance has no attribute 'name'


You can reproduce it by:
(1) create package structure like the following:

package/
        __init__.py
        subpackage/
                   __init__.py
                   module.py

(2) in package/__init__.py write:

import subpackage

(3) run pylint with a script importing package.subpackage.module.
"""
__revision__ = '$Id: import_package_subpackage_module.py,v 1.1 2005-11-10 15:59:32 syt Exp $'
import package.subpackage.module
