from logilab.common.registry import RegistrableObject, RegistrableInstance, yes

class MyRegistrableInstance(RegistrableInstance):
    __regid__ = 'appobject3'
    __select__ = yes()
    __registry__ = 'zereg'

instance = MyRegistrableInstance()
