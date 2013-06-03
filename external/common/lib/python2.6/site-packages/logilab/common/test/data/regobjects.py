"""unittest_registry data file"""
from logilab.common.registry import yes, RegistrableObject, RegistrableInstance

class Proxy(object):
    """annoying object should that not be registered, nor cause error"""
    def __getattr__(self, attr):
        return 1

trap = Proxy()

class AppObjectClass(RegistrableObject):
    __registry__ = 'zereg'
    __regid__ = 'appobject1'
    __select__ = yes()

class AppObjectInstance(RegistrableInstance):
    __registry__ = 'zereg'
    __select__ = yes()
    def __init__(self, regid):
        self.__regid__ = regid

appobject2 = AppObjectInstance('appobject2')
