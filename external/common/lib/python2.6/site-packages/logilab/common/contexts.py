from warnings import warn
warn('logilab.common.contexts module is deprecated, use logilab.common.shellutils instead',
     DeprecationWarning, stacklevel=1)

from logilab.common.shellutils import tempfile, pushd
