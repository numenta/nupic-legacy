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
"""File and file-path manipulation utilities.

:group path manipulation: first_level_directory, relative_path, is_binary,\
get_by_ext, remove_dead_links
:group file manipulation: norm_read, norm_open, lines, stream_lines, lines,\
write_open_mode, ensure_fs_mode, export
:sort: path manipulation, file manipulation
"""
__docformat__ = "restructuredtext en"

import sys
import shutil
import mimetypes
from os.path import isabs, isdir, islink, split, exists, normpath, join
from os.path import abspath
from os import sep, mkdir, remove, listdir, stat, chmod, walk
from stat import ST_MODE, S_IWRITE
from cStringIO import StringIO

from logilab.common import STD_BLACKLIST as BASE_BLACKLIST, IGNORED_EXTENSIONS
from logilab.common.shellutils import find
from logilab.common.deprecation import deprecated
from logilab.common.compat import FileIO, any

def first_level_directory(path):
    """Return the first level directory of a path.

    >>> first_level_directory('home/syt/work')
    'home'
    >>> first_level_directory('/home/syt/work')
    '/'
    >>> first_level_directory('work')
    'work'
    >>>

    :type path: str
    :param path: the path for which we want the first level directory

    :rtype: str
    :return: the first level directory appearing in `path`
    """
    head, tail = split(path)
    while head and tail:
        head, tail = split(head)
    if tail:
        return tail
    # path was absolute, head is the fs root
    return head

def abspath_listdir(path):
    """Lists path's content using absolute paths.

    >>> os.listdir('/home')
    ['adim', 'alf', 'arthur', 'auc']
    >>> abspath_listdir('/home')
    ['/home/adim', '/home/alf', '/home/arthur', '/home/auc']
    """
    path = abspath(path)
    return [join(path, filename) for filename in listdir(path)]


def is_binary(filename):
    """Return true if filename may be a binary file, according to it's
    extension.

    :type filename: str
    :param filename: the name of the file

    :rtype: bool
    :return:
      true if the file is a binary file (actually if it's mime type
      isn't beginning by text/)
    """
    try:
        return not mimetypes.guess_type(filename)[0].startswith('text')
    except AttributeError:
        return 1


def write_open_mode(filename):
    """Return the write mode that should used to open file.

    :type filename: str
    :param filename: the name of the file

    :rtype: str
    :return: the mode that should be use to open the file ('w' or 'wb')
    """
    if is_binary(filename):
        return 'wb'
    return 'w'


def ensure_fs_mode(filepath, desired_mode=S_IWRITE):
    """Check that the given file has the given mode(s) set, else try to
    set it.

    :type filepath: str
    :param filepath: path of the file

    :type desired_mode: int
    :param desired_mode:
      ORed flags describing the desired mode. Use constants from the
      `stat` module for file permission's modes
    """
    mode = stat(filepath)[ST_MODE]
    if not mode & desired_mode:
        chmod(filepath, mode | desired_mode)


# XXX (syt) unused? kill?
class ProtectedFile(FileIO):
    """A special file-object class that automatically does a 'chmod +w' when
    needed.

    XXX: for now, the way it is done allows 'normal file-objects' to be
    created during the ProtectedFile object lifetime.
    One way to circumvent this would be to chmod / unchmod on each
    write operation.

    One other way would be to :

    - catch the IOError in the __init__

    - if IOError, then create a StringIO object

    - each write operation writes in this StringIO object

    - on close()/del(), write/append the StringIO content to the file and
      do the chmod only once
    """
    def __init__(self, filepath, mode):
        self.original_mode = stat(filepath)[ST_MODE]
        self.mode_changed = False
        if mode in ('w', 'a', 'wb', 'ab'):
            if not self.original_mode & S_IWRITE:
                chmod(filepath, self.original_mode | S_IWRITE)
                self.mode_changed = True
        FileIO.__init__(self, filepath, mode)

    def _restore_mode(self):
        """restores the original mode if needed"""
        if self.mode_changed:
            chmod(self.name, self.original_mode)
            # Don't re-chmod in case of several restore
            self.mode_changed = False

    def close(self):
        """restore mode before closing"""
        self._restore_mode()
        FileIO.close(self)

    def __del__(self):
        if not self.closed:
            self.close()


class UnresolvableError(Exception):
    """Exception raised by relative path when it's unable to compute relative
    path between two paths.
    """

def relative_path(from_file, to_file):
    """Try to get a relative path from `from_file` to `to_file`
    (path will be absolute if to_file is an absolute file). This function
    is useful to create link in `from_file` to `to_file`. This typical use
    case is used in this function description.

    If both files are relative, they're expected to be relative to the same
    directory.

    >>> relative_path( from_file='toto/index.html', to_file='index.html')
    '../index.html'
    >>> relative_path( from_file='index.html', to_file='toto/index.html')
    'toto/index.html'
    >>> relative_path( from_file='tutu/index.html', to_file='toto/index.html')
    '../toto/index.html'
    >>> relative_path( from_file='toto/index.html', to_file='/index.html')
    '/index.html'
    >>> relative_path( from_file='/toto/index.html', to_file='/index.html')
    '../index.html'
    >>> relative_path( from_file='/toto/index.html', to_file='/toto/summary.html')
    'summary.html'
    >>> relative_path( from_file='index.html', to_file='index.html')
    ''
    >>> relative_path( from_file='/index.html', to_file='toto/index.html')
    Traceback (most recent call last):
      File "<string>", line 1, in ?
      File "<stdin>", line 37, in relative_path
    UnresolvableError
    >>> relative_path( from_file='/index.html', to_file='/index.html')
    ''
    >>>

    :type from_file: str
    :param from_file: source file (where links will be inserted)

    :type to_file: str
    :param to_file: target file (on which links point)

    :raise UnresolvableError: if it has been unable to guess a correct path

    :rtype: str
    :return: the relative path of `to_file` from `from_file`
    """
    from_file = normpath(from_file)
    to_file = normpath(to_file)
    if from_file == to_file:
        return ''
    if isabs(to_file):
        if not isabs(from_file):
            return to_file
    elif isabs(from_file):
        raise UnresolvableError()
    from_parts = from_file.split(sep)
    to_parts = to_file.split(sep)
    idem = 1
    result = []
    while len(from_parts) > 1:
        dirname = from_parts.pop(0)
        if idem and len(to_parts) > 1 and dirname == to_parts[0]:
            to_parts.pop(0)
        else:
            idem = 0
            result.append('..')
    result += to_parts
    return sep.join(result)


def norm_read(path):
    """Return the content of the file with normalized line feeds.

    :type path: str
    :param path: path to the file to read

    :rtype: str
    :return: the content of the file with normalized line feeds
    """
    return open(path, 'U').read()
norm_read = deprecated("use \"open(path, 'U').read()\"")(norm_read)

def norm_open(path):
    """Return a stream for a file with content with normalized line feeds.

    :type path: str
    :param path: path to the file to open

    :rtype: file or StringIO
    :return: the opened file with normalized line feeds
    """
    return open(path, 'U')
norm_open = deprecated("use \"open(path, 'U')\"")(norm_open)

def lines(path, comments=None):
    """Return a list of non empty lines in the file located at `path`.

    :type path: str
    :param path: path to the file

    :type comments: str or None
    :param comments:
      optional string which can be used to comment a line in the file
      (i.e. lines starting with this string won't be returned)

    :rtype: list
    :return:
      a list of stripped line in the file, without empty and commented
      lines

    :warning: at some point this function will probably return an iterator
    """
    stream = open(path, 'U')
    result = stream_lines(stream, comments)
    stream.close()
    return result


def stream_lines(stream, comments=None):
    """Return a list of non empty lines in the given `stream`.

    :type stream: object implementing 'xreadlines' or 'readlines'
    :param stream: file like object

    :type comments: str or None
    :param comments:
      optional string which can be used to comment a line in the file
      (i.e. lines starting with this string won't be returned)

    :rtype: list
    :return:
      a list of stripped line in the file, without empty and commented
      lines

    :warning: at some point this function will probably return an iterator
    """
    try:
        readlines = stream.xreadlines
    except AttributeError:
        readlines = stream.readlines
    result = []
    for line in readlines():
        line = line.strip()
        if line and (comments is None or not line.startswith(comments)):
            result.append(line)
    return result


def export(from_dir, to_dir,
           blacklist=BASE_BLACKLIST, ignore_ext=IGNORED_EXTENSIONS,
           verbose=0):
    """Make a mirror of `from_dir` in `to_dir`, omitting directories and
    files listed in the black list or ending with one of the given
    extensions.

    :type from_dir: str
    :param from_dir: directory to export

    :type to_dir: str
    :param to_dir: destination directory

    :type blacklist: list or tuple
    :param blacklist:
      list of files or directories to ignore, default to the content of
      `BASE_BLACKLIST`

    :type ignore_ext: list or tuple
    :param ignore_ext:
      list of extensions to ignore, default to  the content of
      `IGNORED_EXTENSIONS`

    :type verbose: bool
    :param verbose:
      flag indicating whether information about exported files should be
      printed to stderr, default to False
    """
    try:
        mkdir(to_dir)
    except OSError:
        pass # FIXME we should use "exists" if the point is about existing dir
             # else (permission problems?) shouldn't return / raise ?
    for directory, dirnames, filenames in walk(from_dir):
        for norecurs in blacklist:
            try:
                dirnames.remove(norecurs)
            except ValueError:
                continue
        for dirname in dirnames:
            src = join(directory, dirname)
            dest = to_dir + src[len(from_dir):]
            if isdir(src):
                if not exists(dest):
                    mkdir(dest)
        for filename in filenames:
            # don't include binary files
            # endswith does not accept tuple in 2.4
            if any([filename.endswith(ext) for ext in ignore_ext]):
                continue
            src = join(directory, filename)
            dest = to_dir + src[len(from_dir):]
            if verbose:
                print >> sys.stderr, src, '->', dest
            if exists(dest):
                remove(dest)
            shutil.copy2(src, dest)


def remove_dead_links(directory, verbose=0):
    """Recursively traverse directory and remove all dead links.

    :type directory: str
    :param directory: directory to cleanup

    :type verbose: bool
    :param verbose:
      flag indicating whether information about deleted links should be
      printed to stderr, default to False
    """
    for dirpath, dirname, filenames in walk(directory):
        for filename in dirnames + filenames:
            src = join(dirpath, filename)
            if islink(src) and not exists(src):
                if verbose:
                    print 'remove dead link', src
                remove(src)

