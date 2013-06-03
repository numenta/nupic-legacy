# Copyright (c) 2003-2012 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
import sys

def run_pylint():
    """run pylint"""
    from pylint.lint import Run
    Run(sys.argv[1:])

def run_pylint_gui():
    """run pylint-gui"""
    try:
        from pylint.gui import Run
        Run(sys.argv[1:])
    except ImportError:
        sys.exit('tkinter is not available')

def run_epylint():
    """run pylint"""
    from pylint.epylint import Run
    Run()

def run_pyreverse():
    """run pyreverse"""
    from pylint.pyreverse.main import Run
    Run(sys.argv[1:])

def run_symilar():
    """run symilar"""
    from pylint.checkers.similar import Run
    Run(sys.argv[1:])
