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
""" docstring for file clientmodule.py """
from data2.suppliermodule_test import Interface as IFace, DoNothing

class Toto: pass

class Ancestor:
    """ Ancestor method """
    __implements__ = (IFace,)
    
    def __init__(self, value):
        local_variable = 0
        self.attr = 'this method shouldn\'t have a docstring'
        self.__value = value

    def get_value(self):
        """ nice docstring ;-) """
        return self.__value

    def set_value(self, value):
        self.__value = value
        return 'this method shouldn\'t have a docstring'    

class Specialization(Ancestor):
    TYPE = 'final class'
    top = 'class'
    
    def __init__(self, value, _id):
        Ancestor.__init__(self, value)
        self._id = _id
        self.relation = DoNothing()
        self.toto = Toto()
        
