"""test module for astng
"""

__revision__ = '$Id: module.py,v 1.2 2005-11-02 11:56:54 syt Exp $'
from logilab.common import modutils
from logilab.common.shellutils import Execute as spawn
from logilab.astng.utils import *
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
    a = 1
    
    def __init__(self):
        try:
            self.yo = 1
        except ValueError, ex:
            pass
        except (NameError, TypeError):
            raise XXXError()
        except:
            raise



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
            autre = [a for (a, b) in MY_DICT if b]
            if b in autre:
                print 'yo',
            else:
                if a in autre:
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


def four_args(a, b, c, d):
    """four arguments (was nested_args)"""
    print a, b, c, d
    while 1:
        if a:
            break
        a += +1
    else:
        b += -2
    if c:
        d = ((a) and (b)) or (c)
    else:
        c = ((a) and (b)) or (d)
    map(lambda x, y: (y, x), a)
redirect = four_args

