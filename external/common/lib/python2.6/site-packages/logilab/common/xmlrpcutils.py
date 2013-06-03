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
"""XML-RPC utilities."""
__docformat__ = "restructuredtext en"

import xmlrpclib
from base64 import encodestring
#from cStringIO import StringIO

ProtocolError = xmlrpclib.ProtocolError

## class BasicAuthTransport(xmlrpclib.Transport):
##     def __init__(self, username=None, password=None):
##         self.username = username
##         self.password = password
##         self.verbose = None
##         self.has_ssl = httplib.__dict__.has_key("HTTPConnection")

##     def request(self, host, handler, request_body, verbose=None):
##         # issue XML-RPC request
##         if self.has_ssl:
##             if host.startswith("https:"): h = httplib.HTTPSConnection(host)
##             else: h = httplib.HTTPConnection(host)
##         else: h = httplib.HTTP(host)

##         h.putrequest("POST", handler)

##         # required by HTTP/1.1
##         if not self.has_ssl: # HTTPConnection already does 1.1
##             h.putheader("Host", host)
##         h.putheader("Connection", "close")

##         if request_body: h.send(request_body)
##         if self.has_ssl:
##             response = h.getresponse()
##             if response.status != 200:
##                 raise xmlrpclib.ProtocolError(host + handler,
##                                               response.status,
##                                               response.reason,
##                                               response.msg)
##             file = response.fp
##         else:
##             errcode, errmsg, headers = h.getreply()
##             if errcode != 200:
##                 raise xmlrpclib.ProtocolError(host + handler, errcode,
##                                               errmsg, headers)

##             file = h.getfile()

##         return self.parse_response(file)



class AuthMixin:
    """basic http authentication mixin for xmlrpc transports"""

    def __init__(self, username, password, encoding):
        self.verbose = 0
        self.username = username
        self.password = password
        self.encoding = encoding

    def request(self, host, handler, request_body, verbose=0):
        """issue XML-RPC request"""
        h = self.make_connection(host)
        h.putrequest("POST", handler)
        # required by XML-RPC
        h.putheader("User-Agent", self.user_agent)
        h.putheader("Content-Type", "text/xml")
        h.putheader("Content-Length", str(len(request_body)))
        h.putheader("Host", host)
        h.putheader("Connection", "close")
        # basic auth
        if self.username is not None and self.password is not None:
            h.putheader("AUTHORIZATION", "Basic %s" % encodestring(
                "%s:%s" % (self.username, self.password)).replace("\012", ""))
        h.endheaders()
        # send body
        if request_body:
            h.send(request_body)
        # get and check reply
        errcode, errmsg, headers = h.getreply()
        if errcode != 200:
            raise ProtocolError(host + handler, errcode, errmsg, headers)
        file = h.getfile()
##         # FIXME: encoding ??? iirc, this fix a bug in xmlrpclib but...
##         data = h.getfile().read()
##         if self.encoding != 'UTF-8':
##             data = data.replace("version='1.0'",
##                                 "version='1.0' encoding='%s'" % self.encoding)
##         result = StringIO()
##         result.write(data)
##         result.seek(0)
##         return self.parse_response(result)
        return self.parse_response(file)

class BasicAuthTransport(AuthMixin, xmlrpclib.Transport):
    """basic http authentication transport"""

class BasicAuthSafeTransport(AuthMixin, xmlrpclib.SafeTransport):
    """basic https authentication transport"""


def connect(url, user=None, passwd=None, encoding='ISO-8859-1'):
    """return an xml rpc server on <url>, using user / password if specified
    """
    if user or passwd:
        assert user and passwd is not None
        if url.startswith('https://'):
            transport = BasicAuthSafeTransport(user, passwd, encoding)
        else:
            transport = BasicAuthTransport(user, passwd, encoding)
    else:
        transport = None
    server = xmlrpclib.ServerProxy(url, transport, encoding=encoding)
    return server
