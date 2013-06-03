# copyright 2003-2011 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
from logilab.common.testlib import TestCase, unittest_main
from logilab.common.interface import *

class IFace1(Interface): pass
class IFace2(Interface): pass
class IFace3(Interface): pass


class A(object):
    __implements__ = (IFace1,)


class B(A): pass


class C1(B):
    __implements__ = list(B.__implements__) + [IFace3]

class C2(B):
    __implements__ = B.__implements__ + (IFace2,)

class D(C1):
    __implements__ = ()

class Z(object): pass

class ExtendTC(TestCase):

    def setUp(self):
        global aimpl, c1impl, c2impl, dimpl
        aimpl = A.__implements__
        c1impl = C1.__implements__
        c2impl = C2.__implements__
        dimpl = D.__implements__

    def test_base(self):
        extend(A, IFace2)
        self.assertEqual(A.__implements__, (IFace1, IFace2))
        self.assertEqual(B.__implements__, (IFace1, IFace2))
        self.assertTrue(B.__implements__ is A.__implements__)
        self.assertEqual(C1.__implements__, [IFace1, IFace3, IFace2])
        self.assertEqual(C2.__implements__, (IFace1, IFace2))
        self.assertTrue(C2.__implements__ is c2impl)
        self.assertEqual(D.__implements__, (IFace2,))

    def test_already_impl(self):
        extend(A, IFace1)
        self.assertTrue(A.__implements__ is aimpl)

    def test_no_impl(self):
        extend(Z, IFace1)
        self.assertEqual(Z.__implements__, (IFace1,))

    def test_notimpl_explicit(self):
        extend(C1, IFace3)
        self.assertTrue(C1.__implements__ is c1impl)
        self.assertTrue(D.__implements__ is dimpl)


    def test_nonregr_implements_baseinterface(self):
        class SubIFace(IFace1): pass
        class X(object):
            __implements__ = (SubIFace,)

        self.assertTrue(SubIFace.is_implemented_by(X))
        self.assertTrue(IFace1.is_implemented_by(X))


if __name__ == '__main__':
    unittest_main()
