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
"""A daemonize function (for Unices)"""

__docformat__ = "restructuredtext en"

import os
import errno
import signal
import sys
import time
import warnings

def setugid(user):
    """Change process user and group ID

    Argument is a numeric user id or a user name"""
    try:
        from pwd import getpwuid
        passwd = getpwuid(int(user))
    except ValueError:
        from pwd import getpwnam
        passwd = getpwnam(user)

    if hasattr(os, 'initgroups'): # python >= 2.7
        os.initgroups(passwd.pw_name, passwd.pw_gid)
    else:
        import ctypes
        if ctypes.CDLL(None).initgroups(passwd.pw_name, passwd.pw_gid) < 0:
            err = ctypes.c_int.in_dll(ctypes.pythonapi,"errno").value
            raise OSError(err, os.strerror(err), 'initgroups')
    os.setgid(passwd.pw_gid)
    os.setuid(passwd.pw_uid)
    os.environ['HOME'] = passwd.pw_dir


def daemonize(pidfile=None, uid=None, umask=077):
    """daemonize a Unix process. Set paranoid umask by default.

    Return 1 in the original process, 2 in the first fork, and None for the
    second fork (eg daemon process).
    """
    # http://www.faqs.org/faqs/unix-faq/programmer/faq/
    #
    # fork so the parent can exit
    if os.fork():   # launch child and...
        return 1
    # disconnect from tty and create a new session
    os.setsid()
    # fork again so the parent, (the session group leader), can exit.
    # as a non-session group leader, we can never regain a controlling
    # terminal.
    if os.fork():   # launch child again.
        return 2
    # move to the root to avoit mount pb
    os.chdir('/')
    # set umask if specified
    if umask is not None:
        os.umask(umask)
    # redirect standard descriptors
    null = os.open('/dev/null', os.O_RDWR)
    for i in range(3):
        try:
            os.dup2(null, i)
        except OSError, e:
            if e.errno != errno.EBADF:
                raise
    os.close(null)
    # filter warnings
    warnings.filterwarnings('ignore')
    # write pid in a file
    if pidfile:
        # ensure the directory where the pid-file should be set exists (for
        # instance /var/run/cubicweb may be deleted on computer restart)
        piddir = os.path.dirname(pidfile)
        if not os.path.exists(piddir):
            os.makedirs(piddir)
        f = file(pidfile, 'w')
        f.write(str(os.getpid()))
        f.close()
        os.chmod(pidfile, 0644)
    # change process uid
    if uid:
        setugid(uid)
    return None
