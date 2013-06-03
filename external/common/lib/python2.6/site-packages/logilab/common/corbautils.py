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
"""A set of utility function to ease the use of OmniORBpy.




"""
__docformat__ = "restructuredtext en"

from omniORB import CORBA, PortableServer
import CosNaming

orb = None

def get_orb():
    """
    returns a reference to the ORB.
    The first call to the method initialized the ORB
    This method is mainly used internally in the module.
    """

    global orb
    if orb is None:
        import sys
        orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
    return orb

def get_root_context():
    """
    returns a reference to the NameService object.
    This method is mainly used internally in the module.
    """

    orb = get_orb()
    nss = orb.resolve_initial_references("NameService")
    rootContext = nss._narrow(CosNaming.NamingContext)
    assert rootContext is not None, "Failed to narrow root naming context"
    return rootContext

def register_object_name(object, namepath):
    """
    Registers a object in the NamingService.
    The name path is a list of 2-uples (id,kind) giving the path.

    For instance if the path of an object is [('foo',''),('bar','')],
    it is possible to get a reference to the object using the URL
    'corbaname::hostname#foo/bar'.
    [('logilab','rootmodule'),('chatbot','application'),('chatter','server')]
    is mapped to
    'corbaname::hostname#logilab.rootmodule/chatbot.application/chatter.server'

    The get_object_reference() function can be used to resolve such a URL.
    """
    context = get_root_context()
    for id, kind in namepath[:-1]:
        name = [CosNaming.NameComponent(id, kind)]
        try:
            context = context.bind_new_context(name)
        except CosNaming.NamingContext.AlreadyBound, ex:
            context = context.resolve(name)._narrow(CosNaming.NamingContext)
            assert context is not None, \
                   'test context exists but is not a NamingContext'

    id, kind = namepath[-1]
    name = [CosNaming.NameComponent(id, kind)]
    try:
        context.bind(name, object._this())
    except CosNaming.NamingContext.AlreadyBound, ex:
        context.rebind(name, object._this())

def activate_POA():
    """
    This methods activates the Portable Object Adapter.
    You need to call it to enable the reception of messages in your code,
    on both the client and the server.
    """
    orb = get_orb()
    poa = orb.resolve_initial_references('RootPOA')
    poaManager = poa._get_the_POAManager()
    poaManager.activate()

def run_orb():
    """
    Enters the ORB mainloop on the server.
    You should not call this method on the client.
    """
    get_orb().run()

def get_object_reference(url):
    """
    Resolves a corbaname URL to an object proxy.
    See register_object_name() for examples URLs
    """
    return get_orb().string_to_object(url)

def get_object_string(host, namepath):
    """given an host name and a name path as described in register_object_name,
    return a corba string identifier
    """
    strname = '/'.join(['.'.join(path_elt) for path_elt in namepath])
    return 'corbaname::%s#%s' % (host, strname)
