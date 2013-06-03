# -*- coding: Latin-1 -*-
"""test module for astng
"""

__revision__ = '$Id: module.py,v 1.9 2003-11-24 13:40:26 syt Exp $'

from logilab.common import modutils, Execute as spawn
from logilab.common.astutils import *
import os.path

MY_DICT = {}


def global_access(key, val):
    """function test"""
    local = 1
    MY_DICT[key] = val
    for i in val:
        if i:
            del MY_DICT[i]
            continue
        else:
            break
    else:
        print '!!!'

class YO:
    """hehe"""
    a=1
    def __init__(self):
        try:
            self.yo = 1
        except ValueError, ex:
            pass
        except (NameError, TypeError):
            raise XXXError()
        except:
            raise

#print '*****>',YO.__dict__
class YOUPI(YO):
    class_attr = None

    def __init__(self):
        self.member = None

    def method(self):
        """method test"""
        global MY_DICT
        try:
            MY_DICT = {}
            local = None
            autre = [a for a, b in MY_DICT if b]
            if b in autre:
                print 'yo',
            elif a in autre:
                print 'hehe'
            global_access(local, val=autre)
        finally:
            return local

    def static_method():
        """static method test"""
        assert MY_DICT, '???'
    static_method = staticmethod(static_method)

    def class_method(cls):
        """class method test"""
        exec a in b
    class_method = classmethod(class_method)


def nested_args(a, (b, c, d)):
    """nested arguments test"""
    print a, b, c, d
    while 1:
        if a:
            break
        a += +1
    else:
        b += -2
    if c:
        d = a and b or c
    else:
        c = a and b or d
    map(lambda x, y: (y, x), a)

redirect = nested_args
