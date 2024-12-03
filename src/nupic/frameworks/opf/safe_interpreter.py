# Copyright 2013 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Safe Python interpreter for user-submitted code."""

import asteval



class SafeInterpreter(asteval.Interpreter):


  blacklisted_nodes = set(('while', 'for', ))


  def __init__(self, *args, **kwargs):
    """Initialize interpreter with blacklisted nodes removed from supported
    nodes.
    """
    self.supported_nodes = tuple(set(self.supported_nodes) -
                                 self.blacklisted_nodes)
    asteval.Interpreter.__init__(self, *args, **kwargs)
