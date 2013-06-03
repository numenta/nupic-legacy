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


import unittest 


class TestCase(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        
        
    def tearDown(self):
        unittest.TestCase.tearDown(self)
    
    def testIt(self):
        self.a = 10
        self.xxx()


    def xxx(self):
        if False:
            pass
            print 'a'
        
        if False:
            pass
            pass
        
        if False:
            pass
            print 'rara'


if __name__ == '__main__':
    print 'test2'
    unittest.main() 
    
    
