"""
This plugin captures stdout during test execution. If the test fails
or raises an error, the captured output will be appended to the error
or failure output. It is enabled by default but can be disabled with
the options ``-s`` or ``--nocapture``.

:Options:
  ``--nocapture``
    Don't capture stdout (any stdout output will be printed immediately)

"""
import logging
import os
import sys
from nose.plugins.base import Plugin
from nose.util import ln
from StringIO import StringIO


log = logging.getLogger(__name__)

class Capture(Plugin):
    """
    Output capture plugin. Enabled by default. Disable with ``-s`` or
    ``--nocapture``. This plugin captures stdout during test execution,
    appending any output captured to the error or failure output,
    should the test fail or raise an error.
    """
    enabled = True
    env_opt = 'NOSE_NOCAPTURE'
    name = 'capture'
    score = 500

    def __init__(self):
        self.stdout = []
        self._buf = None

    def options(self, parser, env):
        """Register commandline options
        """
        parser.add_option(
            "-s", "--nocapture", action="store_false",
            default=not env.get(self.env_opt), dest="capture",
            help="Don't capture stdout (any stdout output "
            "will be printed immediately) [NOSE_NOCAPTURE]")

    def configure(self, options, conf):
        """Configure plugin. Plugin is enabled by default.
        """
        self.conf = conf
        if not options.capture:
            self.enabled = False

    def afterTest(self, test):
        """Clear capture buffer.
        """
        self.end()
        self._buf = None

    def begin(self):
        """Replace sys.stdout with capture buffer.
        """
        self.start() # get an early handle on sys.stdout

    def beforeTest(self, test):
        """Flush capture buffer.
        """
        self.start()

    def formatError(self, test, err):
        """Add captured output to error report.
        """
        test.capturedOutput = output = self.buffer
        self._buf = None
        if not output:
            # Don't return None as that will prevent other
            # formatters from formatting and remove earlier formatters
            # formats, instead return the err we got
            return err
        ec, ev, tb = err
        return (ec, self.addCaptureToErr(ev, output), tb)

    def formatFailure(self, test, err):
        """Add captured output to failure report.
        """
        return self.formatError(test, err)

    def addCaptureToErr(self, ev, output):
        if isinstance(ev, Exception):
            if hasattr(ev, '__unicode__'):
                # 2.6+
                ev = unicode(ev)
            else:
                # 2.5-
                if not hasattr(ev, 'message'):
                    # 2.4
                    msg = len(ev.args) and ev.args[0] or ''
                else:
                    msg = ev.message
                if (isinstance(msg, basestring) and
                    not isinstance(msg, unicode)):
                    msg = msg.decode('utf8', 'replace')
                ev = u'%s: %s' % (ev.__class__.__name__, msg)
        if not isinstance(output, unicode):
            output = output.decode('utf8', 'replace')
        return u'\n'.join([ev, ln(u'>> begin captured stdout <<'),
                           output, ln(u'>> end captured stdout <<')])

    def start(self):
        self.stdout.append(sys.stdout)
        self._buf = StringIO()
        sys.stdout = self._buf

    def end(self):
        if self.stdout:
            sys.stdout = self.stdout.pop()

    def finalize(self, result):
        """Restore stdout.
        """
        while self.stdout:
            self.end()

    def _get_buffer(self):
        if self._buf is not None:
            return self._buf.getvalue()

    buffer = property(_get_buffer, None, None,
                      """Captured stdout output.""")
