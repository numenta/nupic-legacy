"""ASTNG hooks for the Python 2 standard library.

Currently help understanding of :

* hashlib.md5 and hashlib.sha1
"""

from logilab.astng import MANAGER
from logilab.astng.builder import ASTNGBuilder

MODULE_TRANSFORMS = {}

def hashlib_transform(module):
    fake = ASTNGBuilder(MANAGER).string_build('''

class md5(object):
  def __init__(self, value): pass
  def hexdigest(self):
    return u''

class sha1(object):
  def __init__(self, value): pass
  def hexdigest(self):
    return u''

''')
    for hashfunc in ('sha1', 'md5'):
        module.locals[hashfunc] = fake.locals[hashfunc]

def collections_transform(module):
    fake = ASTNGBuilder(MANAGER).string_build('''

class defaultdict(dict):
    default_factory = None
    def __missing__(self, key): pass

class deque(object):
    maxlen = 0
    def __init__(iterable=None, maxlen=None): pass
    def append(self, x): pass
    def appendleft(self, x): pass
    def clear(self): pass
    def count(self, x): return 0
    def extend(self, iterable): pass
    def extendleft(self, iterable): pass
    def pop(self): pass
    def popleft(self): pass
    def remove(self, value): pass
    def reverse(self): pass
    def rotate(self, n): pass

''')

    for klass in ('deque', 'defaultdict'):
        module.locals[klass] = fake.locals[klass]

def pkg_resources_transform(module):
    fake = ASTNGBuilder(MANAGER).string_build('''

def resource_exists(package_or_requirement, resource_name):
    pass

def resource_isdir(package_or_requirement, resource_name):
    pass

def resource_filename(package_or_requirement, resource_name):
    pass

def resource_stream(package_or_requirement, resource_name):
    pass

def resource_string(package_or_requirement, resource_name):
    pass

def resource_listdir(package_or_requirement, resource_name):
    pass

def extraction_error():
    pass

def get_cache_path(archive_name, names=()):
    pass

def postprocess(tempname, filename):
    pass

def set_extraction_path(path):
    pass

def cleanup_resources(force=False):
    pass

''')

    for func_name, func in fake.locals.items():
        module.locals[func_name] = func


def urlparse_transform(module):
    fake = ASTNGBuilder(MANAGER).string_build('''

def urlparse(urlstring, default_scheme='', allow_fragments=True):
    return ParseResult()

class ParseResult(object):
    def __init__(self):
        self.scheme = ''
        self.netloc = ''
        self.path = ''
        self.params = ''
        self.query = ''
        self.fragment = ''
        self.username = None
        self.password = None
        self.hostname = None
        self.port = None

    def geturl(self):
        return ''
''')

    for func_name, func in fake.locals.items():
        module.locals[func_name] = func

def subprocess_transform(module):
    fake = ASTNGBuilder(MANAGER).string_build('''

class Popen(object):

    def __init__(self, args, bufsize=0, executable=None,
                 stdin=None, stdout=None, stderr=None,
                 preexec_fn=None, close_fds=False, shell=False,
                 cwd=None, env=None, universal_newlines=False,
                 startupinfo=None, creationflags=0):
        pass

    def communicate(self, input=None):
        return ('string', 'string')
    ''')

    for func_name, func in fake.locals.items():
        module.locals[func_name] = func



MODULE_TRANSFORMS['hashlib'] = hashlib_transform
MODULE_TRANSFORMS['collections'] = collections_transform
MODULE_TRANSFORMS['pkg_resources'] = pkg_resources_transform
MODULE_TRANSFORMS['urlparse'] = urlparse_transform
MODULE_TRANSFORMS['subprocess'] = subprocess_transform


def transform(module):
    try:
        tr = MODULE_TRANSFORMS[module.name]
    except KeyError:
        pass
    else:
        tr(module)

from logilab.astng import MANAGER
MANAGER.register_transformer(transform)


