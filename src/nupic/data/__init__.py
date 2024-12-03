# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""A data source for the prediction framework has a getNext() method.
FileSource is a base class for file-based sources. There are two
 sub-classes:

TextFileSource - can read delimited text files (e.g. CSV files)
StandardSource - can read a binary file of marshaled Python objects
"""

SENTINEL_VALUE_FOR_MISSING_DATA = None

from function_source import FunctionSource
