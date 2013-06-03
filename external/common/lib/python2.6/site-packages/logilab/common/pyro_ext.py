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
"""Python Remote Object utilities

Main functions available:

* `register_object` to expose arbitrary object through pyro using delegation
  approach and register it in the nameserver.
* `ns_unregister` unregister an object identifier from the nameserver.
* `ns_get_proxy` get a pyro proxy from a nameserver object identifier.
"""

__docformat__ = "restructuredtext en"

import logging
import tempfile

from Pyro import core, naming, errors, util, config

_LOGGER = logging.getLogger('pyro')
_MARKER = object()

config.PYRO_STORAGE = tempfile.gettempdir()

def ns_group_and_id(idstr, defaultnsgroup=_MARKER):
    try:
        nsgroup, nsid = idstr.rsplit('.', 1)
    except ValueError:
        if defaultnsgroup is _MARKER:
            nsgroup = config.PYRO_NS_DEFAULTGROUP
        else:
            nsgroup = defaultnsgroup
        nsid = idstr
    if nsgroup is not None and not nsgroup.startswith(':'):
        nsgroup = ':' + nsgroup
    return nsgroup, nsid

def host_and_port(hoststr):
    if not hoststr:
        return None, None
    try:
        hoststr, port = hoststr.split(':')
    except ValueError:
        port = None
    else:
        port = int(port)
    return hoststr, port

_DAEMONS = {}
_PYRO_OBJS = {}
def _get_daemon(daemonhost, start=True):
    if not daemonhost in _DAEMONS:
        if not start:
            raise Exception('no daemon for %s' % daemonhost)
        if not _DAEMONS:
            core.initServer(banner=0)
        host, port = host_and_port(daemonhost)
        daemon = core.Daemon(host=host, port=port)
        _DAEMONS[daemonhost] = daemon
    return _DAEMONS[daemonhost]


def locate_ns(nshost):
    """locate and return the pyro name server to the daemon"""
    core.initClient(banner=False)
    return naming.NameServerLocator().getNS(*host_and_port(nshost))


def register_object(object, nsid, defaultnsgroup=_MARKER,
                    daemonhost=None, nshost=None, use_pyrons=True):
    """expose the object as a pyro object and register it in the name-server

    if use_pyrons is False, then the object is exposed, but no
    attempt to register it to a pyro nameserver is made.

    return the pyro daemon object
    """
    nsgroup, nsid = ns_group_and_id(nsid, defaultnsgroup)
    daemon = _get_daemon(daemonhost)
    if use_pyrons:
        nsd = locate_ns(nshost)
        # make sure our namespace group exists
        try:
            nsd.createGroup(nsgroup)
        except errors.NamingError:
            pass
        daemon.useNameServer(nsd)
    # use Delegation approach
    impl = core.ObjBase()
    impl.delegateTo(object)
    qnsid = '%s.%s' % (nsgroup, nsid)
    uri = daemon.connect(impl, qnsid)
    _PYRO_OBJS[qnsid] = str(uri)
    _LOGGER.info('registered %s a pyro object using group %s and id %s',
                 object, nsgroup, nsid)
    return daemon

def get_object_uri(qnsid):
    return _PYRO_OBJS[qnsid]

def ns_unregister(nsid, defaultnsgroup=_MARKER, nshost=None):
    """unregister the object with the given nsid from the pyro name server"""
    nsgroup, nsid = ns_group_and_id(nsid, defaultnsgroup)
    try:
        nsd = locate_ns(nshost)
    except errors.PyroError, ex:
        # name server not responding
        _LOGGER.error('can\'t locate pyro name server: %s', ex)
    else:
        try:
            nsd.unregister('%s.%s' % (nsgroup, nsid))
            _LOGGER.info('%s unregistered from pyro name server', nsid)
        except errors.NamingError:
            _LOGGER.warning('%s not registered in pyro name server', nsid)


def ns_reregister(nsid, defaultnsgroup=_MARKER, nshost=None):
    """reregister a pyro object into the name server. You only have to specify
    the name-server id of the object (though you MUST have gone through
    `register_object` for the given object previously).

    This is especially useful for long running server while the name server may
    have been restarted, and its records lost.
    """
    nsgroup, nsid = ns_group_and_id(nsid, defaultnsgroup)
    qnsid = '%s.%s' % (nsgroup, nsid)
    nsd = locate_ns(nshost)
    try:
        nsd.unregister(qnsid)
    except errors.NamingError:
        # make sure our namespace group exists
        try:
            nsd.createGroup(nsgroup)
        except errors.NamingError:
            pass
    nsd.register(qnsid, _PYRO_OBJS[qnsid])

def ns_get_proxy(nsid, defaultnsgroup=_MARKER, nshost=None):
    """
    if nshost is None, the nameserver is found by a broadcast.
    """
    # resolve the Pyro object
    nsgroup, nsid = ns_group_and_id(nsid, defaultnsgroup)
    try:
        nsd = locate_ns(nshost)
        pyrouri = nsd.resolve('%s.%s' % (nsgroup, nsid))
    except errors.ProtocolError, ex:
        raise errors.PyroError(
            'Could not connect to the Pyro name server (host: %s)' % nshost)
    except errors.NamingError:
        raise errors.PyroError(
            'Could not get proxy for %s (not registered in Pyro), '
            'you may have to restart your server-side application' % nsid)
    return core.getProxyForURI(pyrouri)

def get_proxy(pyro_uri):
    """get a proxy for the passed pyro uri without using a nameserver
    """
    return core.getProxyForURI(pyro_uri)

def set_pyro_log_threshold(level):
    pyrologger = logging.getLogger('Pyro.%s' % str(id(util.Log)))
    # remove handlers so only the root handler is used
    pyrologger.handlers = []
    pyrologger.setLevel(level)
