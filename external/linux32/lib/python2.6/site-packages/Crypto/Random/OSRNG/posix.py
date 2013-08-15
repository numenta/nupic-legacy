#
#  Random/OSRNG/posix.py : OS entropy source for POSIX systems
#
# Written in 2008 by Dwayne C. Litzenberger <dlitz@dlitz.net>
#
# ===================================================================
# The contents of this file are dedicated to the public domain.  To
# the extent that dedication to the public domain is not available,
# everyone is granted a worldwide, perpetual, royalty-free,
# non-exclusive license to exercise all rights associated with the
# contents of this file for any purpose whatsoever.
# No rights are reserved.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ===================================================================


__revision__ = "$Id$"
__all__ = ['DevURandomRNG']

import os
import stat

from rng_base import BaseRNG

class DevURandomRNG(BaseRNG):

    def __init__(self, devname=None):
        if devname is None:
            self.name = "/dev/urandom"
        else:
            self.name = devname

        # Test that /dev/urandom is a character special device
        f = open(self.name, "rb", 0)
        fmode = os.fstat(f.fileno())[stat.ST_MODE]
        if not stat.S_ISCHR(fmode):
            f.close()
            raise TypeError("%r is not a character special device" % (self.name,))

        self.__file = f
        self._read = f.read

        BaseRNG.__init__(self)

    def _close(self):
        self.__file.close()

    def _read(self, N):
        return self.__file.read(N)

def new(*args, **kwargs):
    return DevURandomRNG(*args, **kwargs)


# vim:set ts=4 sw=4 sts=4 expandtab:
