from logilab.astng import MANAGER
from logilab.astng.builder import ASTNGBuilder

def mechanize_transform(module):
    fake = ASTNGBuilder(MANAGER).string_build('''

class Browser(object):
    def open(self, url, data=None, timeout=None):
        return None
    def open_novisit(self, url, data=None, timeout=None):
        return None
    def open_local_file(self, filename):
        return None

''')
    module.locals['Browser'] = fake.locals['Browser']

import py2stdlib
py2stdlib.MODULE_TRANSFORMS['mechanize'] = mechanize_transform

