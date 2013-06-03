""" reporter used by gui.py """

import sys

from pylint.interfaces import IReporter
from pylint.reporters import BaseReporter
from logilab.common.ureports import TextWriter


class GUIReporter(BaseReporter):
    """saves messages"""

    __implements__ = IReporter
    extension = ''

    def __init__(self, gui, output=sys.stdout):
        """init"""
        BaseReporter.__init__(self, output)
        self.msgs = []
        self.gui = gui

    def add_message(self, msg_id, location, msg):
        """manage message of different type and in the context of path"""
        module, obj, line, col_offset = location[1:]
        sigle = self.make_sigle(msg_id)
        full_msg = [sigle, module, obj, str(line), msg]
        self.msgs += [[sigle, module, obj, str(line)]]
        self.gui.msg_queue.put(full_msg)

    def _display(self, layout):
        """launch layouts display"""
        TextWriter().format(layout, self.out)
