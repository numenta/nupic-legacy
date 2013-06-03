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
"""Some text manipulation utility functions.


:group text formatting: normalize_text, normalize_paragraph, pretty_match,\
unquote, colorize_ansi
:group text manipulation: searchall, splitstrip
:sort: text formatting, text manipulation

:type ANSI_STYLES: dict(str)
:var ANSI_STYLES: dictionary mapping style identifier to ANSI terminal code

:type ANSI_COLORS: dict(str)
:var ANSI_COLORS: dictionary mapping color identifier to ANSI terminal code

:type ANSI_PREFIX: str
:var ANSI_PREFIX:
  ANSI terminal code notifying the start of an ANSI escape sequence

:type ANSI_END: str
:var ANSI_END:
  ANSI terminal code notifying the end of an ANSI escape sequence

:type ANSI_RESET: str
:var ANSI_RESET:
  ANSI terminal code resetting format defined by a previous ANSI escape sequence
"""
__docformat__ = "restructuredtext en"

import sys
import re
import os.path as osp
from warnings import warn
from unicodedata import normalize as _uninormalize
try:
    from os import linesep
except ImportError:
    linesep = '\n' # gae

from logilab.common.deprecation import deprecated

MANUAL_UNICODE_MAP = {
    u'\xa1': u'!',    # INVERTED EXCLAMATION MARK
    u'\u0142': u'l',  # LATIN SMALL LETTER L WITH STROKE
    u'\u2044': u'/',  # FRACTION SLASH
    u'\xc6': u'AE',   # LATIN CAPITAL LETTER AE
    u'\xa9': u'(c)',  # COPYRIGHT SIGN
    u'\xab': u'"',    # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    u'\xe6': u'ae',   # LATIN SMALL LETTER AE
    u'\xae': u'(r)',  # REGISTERED SIGN
    u'\u0153': u'oe', # LATIN SMALL LIGATURE OE
    u'\u0152': u'OE', # LATIN CAPITAL LIGATURE OE
    u'\xd8': u'O',    # LATIN CAPITAL LETTER O WITH STROKE
    u'\xf8': u'o',    # LATIN SMALL LETTER O WITH STROKE
    u'\xbb': u'"',    # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
    u'\xdf': u'ss',   # LATIN SMALL LETTER SHARP S
    }

def unormalize(ustring, ignorenonascii=None, substitute=None):
    """replace diacritical characters with their corresponding ascii characters

    Convert the unicode string to its long normalized form (unicode character
    will be transform into several characters) and keep the first one only.
    The normal form KD (NFKD) will apply the compatibility decomposition, i.e.
    replace all compatibility characters with their equivalents.

    :type substitute: str
    :param substitute: replacement character to use if decomposition fails

    :see: Another project about ASCII transliterations of Unicode text
          http://pypi.python.org/pypi/Unidecode
    """
    # backward compatibility, ignorenonascii was a boolean
    if ignorenonascii is not None:
        warn("ignorenonascii is deprecated, use substitute named parameter instead",
             DeprecationWarning, stacklevel=2)
        if ignorenonascii:
            substitute = ''
    res = []
    for letter in ustring[:]:
        try:
            replacement = MANUAL_UNICODE_MAP[letter]
        except KeyError:
            replacement = _uninormalize('NFKD', letter)[0]
            if ord(replacement) >= 2 ** 7:
                if substitute is None:
                    raise ValueError("can't deal with non-ascii based characters")
                replacement = substitute
        res.append(replacement)
    return u''.join(res)

def unquote(string):
    """remove optional quotes (simple or double) from the string

    :type string: str or unicode
    :param string: an optionally quoted string

    :rtype: str or unicode
    :return: the unquoted string (or the input string if it wasn't quoted)
    """
    if not string:
        return string
    if string[0] in '"\'':
        string = string[1:]
    if string[-1] in '"\'':
        string = string[:-1]
    return string


_BLANKLINES_RGX = re.compile('\r?\n\r?\n')
_NORM_SPACES_RGX = re.compile('\s+')

def normalize_text(text, line_len=80, indent='', rest=False):
    """normalize a text to display it with a maximum line size and
    optionally arbitrary indentation. Line jumps are normalized but blank
    lines are kept. The indentation string may be used to insert a
    comment (#) or a quoting (>) mark  for instance.

    :type text: str or unicode
    :param text: the input text to normalize

    :type line_len: int
    :param line_len: expected maximum line's length, default to 80

    :type indent: str or unicode
    :param indent: optional string to use as indentation

    :rtype: str or unicode
    :return:
      the input text normalized to fit on lines with a maximized size
      inferior to `line_len`, and optionally prefixed by an
      indentation string
    """
    if rest:
        normp = normalize_rest_paragraph
    else:
        normp = normalize_paragraph
    result = []
    for text in _BLANKLINES_RGX.split(text):
        result.append(normp(text, line_len, indent))
    return ('%s%s%s' % (linesep, indent, linesep)).join(result)


def normalize_paragraph(text, line_len=80, indent=''):
    """normalize a text to display it with a maximum line size and
    optionally arbitrary indentation. Line jumps are normalized. The
    indentation string may be used top insert a comment mark for
    instance.

    :type text: str or unicode
    :param text: the input text to normalize

    :type line_len: int
    :param line_len: expected maximum line's length, default to 80

    :type indent: str or unicode
    :param indent: optional string to use as indentation

    :rtype: str or unicode
    :return:
      the input text normalized to fit on lines with a maximized size
      inferior to `line_len`, and optionally prefixed by an
      indentation string
    """
    text = _NORM_SPACES_RGX.sub(' ', text)
    line_len = line_len - len(indent)
    lines = []
    while text:
        aline, text = splittext(text.strip(), line_len)
        lines.append(indent + aline)
    return linesep.join(lines)

def normalize_rest_paragraph(text, line_len=80, indent=''):
    """normalize a ReST text to display it with a maximum line size and
    optionally arbitrary indentation. Line jumps are normalized. The
    indentation string may be used top insert a comment mark for
    instance.

    :type text: str or unicode
    :param text: the input text to normalize

    :type line_len: int
    :param line_len: expected maximum line's length, default to 80

    :type indent: str or unicode
    :param indent: optional string to use as indentation

    :rtype: str or unicode
    :return:
      the input text normalized to fit on lines with a maximized size
      inferior to `line_len`, and optionally prefixed by an
      indentation string
    """
    toreport = ''
    lines = []
    line_len = line_len - len(indent)
    for line in text.splitlines():
        line = toreport + _NORM_SPACES_RGX.sub(' ', line.strip())
        toreport = ''
        while len(line) > line_len:
            # too long line, need split
            line, toreport = splittext(line, line_len)
            lines.append(indent + line)
            if toreport:
                line = toreport + ' '
                toreport = ''
            else:
                line = ''
        if line:
            lines.append(indent + line.strip())
    return linesep.join(lines)


def splittext(text, line_len):
    """split the given text on space according to the given max line size

    return a 2-uple:
    * a line <= line_len if possible
    * the rest of the text which has to be reported on another line
    """
    if len(text) <= line_len:
        return text, ''
    pos = min(len(text)-1, line_len)
    while pos > 0 and text[pos] != ' ':
        pos -= 1
    if pos == 0:
        pos = min(len(text), line_len)
        while len(text) > pos and text[pos] != ' ':
            pos += 1
    return text[:pos], text[pos+1:].strip()


def splitstrip(string, sep=','):
    """return a list of stripped string by splitting the string given as
    argument on `sep` (',' by default). Empty string are discarded.

    >>> splitstrip('a, b, c   ,  4,,')
    ['a', 'b', 'c', '4']
    >>> splitstrip('a')
    ['a']
    >>>

    :type string: str or unicode
    :param string: a csv line

    :type sep: str or unicode
    :param sep: field separator, default to the comma (',')

    :rtype: str or unicode
    :return: the unquoted string (or the input string if it wasn't quoted)
    """
    return [word.strip() for word in string.split(sep) if word.strip()]

get_csv = deprecated('get_csv is deprecated, use splitstrip')(splitstrip)


def split_url_or_path(url_or_path):
    """return the latest component of a string containing either an url of the
    form <scheme>://<path> or a local file system path
    """
    if '://' in url_or_path:
        return url_or_path.rstrip('/').rsplit('/', 1)
    return osp.split(url_or_path.rstrip(osp.sep))


def text_to_dict(text):
    """parse multilines text containing simple 'key=value' lines and return a
    dict of {'key': 'value'}. When the same key is encountered multiple time,
    value is turned into a list containing all values.

    >>> text_to_dict('''multiple=1
    ... multiple= 2
    ... single =3
    ... ''')
    {'single': '3', 'multiple': ['1', '2']}

    """
    res = {}
    if not text:
        return res
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = [w.strip() for w in line.split('=', 1)]
            if key in res:
                try:
                    res[key].append(value)
                except AttributeError:
                    res[key] = [res[key], value]
            else:
                res[key] = value
    return res


_BLANK_URE = r'(\s|,)+'
_BLANK_RE = re.compile(_BLANK_URE)
__VALUE_URE = r'-?(([0-9]+\.[0-9]*)|((0x?)?[0-9]+))'
__UNITS_URE = r'[a-zA-Z]+'
_VALUE_RE = re.compile(r'(?P<value>%s)(?P<unit>%s)?'%(__VALUE_URE, __UNITS_URE))
_VALIDATION_RE = re.compile(r'^((%s)(%s))*(%s)?$' % (__VALUE_URE, __UNITS_URE,
                                                    __VALUE_URE))

BYTE_UNITS = {
    "b": 1,
    "kb": 1024,
    "mb": 1024 ** 2,
    "gb": 1024 ** 3,
    "tb": 1024 ** 4,
}

TIME_UNITS = {
    "ms": 0.0001,
    "s": 1,
    "min": 60,
    "h": 60 * 60,
    "d": 60 * 60 *24,
}

def apply_units(string, units, inter=None, final=float, blank_reg=_BLANK_RE,
                value_reg=_VALUE_RE):
    """Parse the string applying the units defined in units
    (e.g.: "1.5m",{'m',60} -> 80).

    :type string: str or unicode
    :param string: the string to parse

    :type units: dict (or any object with __getitem__ using basestring key)
    :param units: a dict mapping a unit string repr to its value

    :type inter: type
    :param inter: used to parse every intermediate value (need __sum__)

    :type blank_reg: regexp
    :param blank_reg: should match every blank char to ignore.

    :type value_reg: regexp with "value" and optional "unit" group
    :param value_reg: match a value and it's unit into the
    """
    if inter is None:
        inter = final
    fstring = _BLANK_RE.sub('', string)
    if not (fstring and _VALIDATION_RE.match(fstring)):
        raise ValueError("Invalid unit string: %r." % string)
    values = []
    for match in value_reg.finditer(fstring):
        dic = match.groupdict()
        lit, unit = dic["value"], dic.get("unit")
        value = inter(lit)
        if unit is not None:
            try:
                value *= units[unit.lower()]
            except KeyError:
                raise KeyError('invalid unit %s. valid units are %s' %
                               (unit, units.keys()))
        values.append(value)
    return final(sum(values))


_LINE_RGX = re.compile('\r\n|\r+|\n')

def pretty_match(match, string, underline_char='^'):
    """return a string with the match location underlined:

    >>> import re
    >>> print(pretty_match(re.search('mange', 'il mange du bacon'), 'il mange du bacon'))
    il mange du bacon
       ^^^^^
    >>>

    :type match: _sre.SRE_match
    :param match: object returned by re.match, re.search or re.finditer

    :type string: str or unicode
    :param string:
      the string on which the regular expression has been applied to
      obtain the `match` object

    :type underline_char: str or unicode
    :param underline_char:
      character to use to underline the matched section, default to the
      carret '^'

    :rtype: str or unicode
    :return:
      the original string with an inserted line to underline the match
      location
    """
    start = match.start()
    end = match.end()
    string = _LINE_RGX.sub(linesep, string)
    start_line_pos = string.rfind(linesep, 0, start)
    if start_line_pos == -1:
        start_line_pos = 0
        result = []
    else:
        result = [string[:start_line_pos]]
        start_line_pos += len(linesep)
    offset = start - start_line_pos
    underline = ' ' * offset + underline_char * (end - start)
    end_line_pos = string.find(linesep, end)
    if end_line_pos == -1:
        string = string[start_line_pos:]
        result.append(string)
        result.append(underline)
    else:
        end = string[end_line_pos + len(linesep):]
        string = string[start_line_pos:end_line_pos]
        result.append(string)
        result.append(underline)
        result.append(end)
    return linesep.join(result).rstrip()


# Ansi colorization ###########################################################

ANSI_PREFIX = '\033['
ANSI_END = 'm'
ANSI_RESET = '\033[0m'
ANSI_STYLES = {
    'reset': "0",
    'bold': "1",
    'italic': "3",
    'underline': "4",
    'blink': "5",
    'inverse': "7",
    'strike': "9",
}
ANSI_COLORS = {
    'reset': "0",
    'black': "30",
    'red': "31",
    'green': "32",
    'yellow': "33",
    'blue': "34",
    'magenta': "35",
    'cyan': "36",
    'white': "37",
}

def _get_ansi_code(color=None, style=None):
    """return ansi escape code corresponding to color and style

    :type color: str or None
    :param color:
      the color name (see `ANSI_COLORS` for available values)
      or the color number when 256 colors are available

    :type style: str or None
    :param style:
      style string (see `ANSI_COLORS` for available values). To get
      several style effects at the same time, use a coma as separator.

    :raise KeyError: if an unexistent color or style identifier is given

    :rtype: str
    :return: the built escape code
    """
    ansi_code = []
    if style:
        style_attrs = splitstrip(style)
        for effect in style_attrs:
            ansi_code.append(ANSI_STYLES[effect])
    if color:
        if color.isdigit():
            ansi_code.extend(['38', '5'])
            ansi_code.append(color)
        else:
            ansi_code.append(ANSI_COLORS[color])
    if ansi_code:
        return ANSI_PREFIX + ';'.join(ansi_code) + ANSI_END
    return ''

def colorize_ansi(msg, color=None, style=None):
    """colorize message by wrapping it with ansi escape codes

    :type msg: str or unicode
    :param msg: the message string to colorize

    :type color: str or None
    :param color:
      the color identifier (see `ANSI_COLORS` for available values)

    :type style: str or None
    :param style:
      style string (see `ANSI_COLORS` for available values). To get
      several style effects at the same time, use a coma as separator.

    :raise KeyError: if an unexistent color or style identifier is given

    :rtype: str or unicode
    :return: the ansi escaped string
    """
    # If both color and style are not defined, then leave the text as is
    if color is None and style is None:
        return msg
    escape_code = _get_ansi_code(color, style)
    # If invalid (or unknown) color, don't wrap msg with ansi codes
    if escape_code:
        return '%s%s%s' % (escape_code, msg, ANSI_RESET)
    return msg

DIFF_STYLE = {'separator': 'cyan', 'remove': 'red', 'add': 'green'}

def diff_colorize_ansi(lines, out=sys.stdout, style=DIFF_STYLE):
    for line in lines:
        if line[:4] in ('--- ', '+++ '):
            out.write(colorize_ansi(line, style['separator']))
        elif line[0] == '-':
            out.write(colorize_ansi(line, style['remove']))
        elif line[0] == '+':
            out.write(colorize_ansi(line, style['add']))
        elif line[:4] == '--- ':
            out.write(colorize_ansi(line, style['separator']))
        elif line[:4] == '+++ ':
            out.write(colorize_ansi(line, style['separator']))
        else:
            out.write(line)

