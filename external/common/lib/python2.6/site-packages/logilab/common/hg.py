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
"""mercurial utilities (mercurial should be installed)"""

__docformat__ = "restructuredtext en"

import os
import sys
import os.path as osp

try:
    from mercurial.error import RepoError
    from mercurial.__version__ import version as hg_version
except ImportError:
    from mercurial.repo import RepoError
    from mercurial.version import get_version
    hg_version = get_version()

from mercurial.hg import repository as Repository
from mercurial.ui import ui as Ui
from mercurial.node import short
try:
    # mercurial >= 1.2 (?)
    from mercurial.cmdutil import walkchangerevs
except ImportError, ex:
    from mercurial.commands import walkchangerevs
try:
    # mercurial >= 1.1 (.1?)
    from mercurial.util import cachefunc
except ImportError, ex:
    def cachefunc(func):
        return func
try:
    # mercurial >= 1.3.1
    from mercurial import encoding
    _encoding = encoding.encoding
except ImportError:
    try:
        from mercurial.util import _encoding
    except ImportError:
        import locale
        # stay compatible with mercurial 0.9.1 (etch debian release)
        # (borrowed from mercurial.util 1.1.2)
        try:
            _encoding = os.environ.get("HGENCODING")
            if sys.platform == 'darwin' and not _encoding:
                # On darwin, getpreferredencoding ignores the locale environment and
                # always returns mac-roman. We override this if the environment is
                # not C (has been customized by the user).
                locale.setlocale(locale.LC_CTYPE, '')
                _encoding = locale.getlocale()[1]
            if not _encoding:
                _encoding = locale.getpreferredencoding() or 'ascii'
        except locale.Error:
            _encoding = 'ascii'
try:
    # demandimport causes problems when activated, ensure it isn't
    # XXX put this in apycot where the pb has been noticed?
    from mercurial import demandimport
    demandimport.disable()
except:
    pass

Ui.warn = lambda *args, **kwargs: 0 # make it quiet

def find_repository(path):
    """returns <path>'s mercurial repository

    None if <path> is not under hg control
    """
    path = osp.realpath(osp.abspath(path))
    while not osp.isdir(osp.join(path, ".hg")):
        oldpath = path
        path = osp.dirname(path)
        if path == oldpath:
            return None
    return path


def get_repository(path):
    """Simple function that open a hg repository"""
    repopath = find_repository(path)
    if repopath is None:
        raise RuntimeError('no repository found in %s' % osp.abspath(path))
    return Repository(Ui(), path=repopath)

def incoming(wdrepo, masterrepo):
    try:
        return wdrepo.findincoming(masterrepo)
    except AttributeError:
        from mercurial import hg, discovery
        revs, checkout = hg.addbranchrevs(wdrepo, masterrepo, ('', []), None)
        common, incoming, rheads = discovery.findcommonincoming(
            wdrepo, masterrepo, heads=revs)
        if not masterrepo.local():
            from mercurial import bundlerepo, changegroup
            if revs is None and masterrepo.capable('changegroupsubset'):
                revs = rheads
            if revs is None:
                cg = masterrepo.changegroup(incoming, "incoming")
            else:
                cg = masterrepo.changegroupsubset(incoming, revs, 'incoming')
            fname = changegroup.writebundle(cg, None, "HG10UN")
            # use the created uncompressed bundlerepo
            masterrepo = bundlerepo.bundlerepository(wdrepo.ui, wdrepo.root, fname)
        return masterrepo.changelog.nodesbetween(incoming, revs)[0]

def outgoing(wdrepo, masterrepo):
    try:
        return wdrepo.findoutgoing(masterrepo)
    except AttributeError:
        from mercurial import hg, discovery
        revs, checkout = hg.addbranchrevs(wdrepo, wdrepo, ('', []), None)
        o = discovery.findoutgoing(wdrepo, masterrepo)
        return wdrepo.changelog.nodesbetween(o, revs)[0]
