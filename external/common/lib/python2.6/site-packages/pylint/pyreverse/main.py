# # Copyright (c) 2000-2012 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
  %prog [options] <packages>

  create UML diagrams for classes and modules in <packages>
"""

import sys, os
from logilab.common.configuration import ConfigurationMixIn
from logilab.astng.manager import ASTNGManager
from logilab.astng.inspector import Linker

from pylint.pyreverse.diadefslib import DiadefsHandler
from pylint.pyreverse import writer
from pylint.pyreverse.utils import insert_default_options

OPTIONS = (
("filter-mode",
    dict(short='f', default='PUB_ONLY', dest='mode', type='string',
    action='store', metavar='<mode>',
    help="""filter attributes and functions according to
    <mode>. Correct modes are :
                            'PUB_ONLY' filter all non public attributes
                                [DEFAULT], equivalent to PRIVATE+SPECIAL_A
                            'ALL' no filter
                            'SPECIAL' filter Python special functions
                                except constructor
                            'OTHER' filter protected and private
                                attributes""")),

("class",
dict(short='c', action="append", metavar="<class>", dest="classes", default=[],
    help="create a class diagram with all classes related to <class>;\
 this uses by default the options -ASmy")),

("show-ancestors",
dict(short="a",  action="store", metavar='<ancestor>', type='int',
    help='show <ancestor> generations of ancestor classes not in <projects>')),
("all-ancestors",
dict(short="A", default=None,
    help="show all ancestors off all classes in <projects>") ),
("show-associated",
dict(short='s', action="store", metavar='<ass_level>', type='int',
    help='show <ass_level> levels of associated classes not in <projects>')),
("all-associated",
dict(short='S', default=None,
    help='show recursively all associated off all associated classes')),

("show-builtin",
dict(short="b", action="store_true", default=False,
    help='include builtin objects in representation of classes')),

("module-names",
dict(short="m", default=None, type='yn', metavar='[yn]',
    help='include module name in representation of classes')),
# TODO : generate dependencies like in pylint
#("package-dependencies",
#dict(short="M", action="store", metavar='<package_depth>', type='int',
    #help='show <package_depth> module dependencies beyond modules in \
#<projects> (for the package diagram)')),
("only-classnames",
dict(short='k', action="store_true", default=False,
    help="don't show attributes and methods in the class boxes; \
this disables -f values")),
("output", dict(short="o", dest="output_format", action="store",
                 default="dot", metavar="<format>",
                help="create a *.<format> output file if format available.")),
)
# FIXME : quiet mode
#( ('quiet',
                #dict(help='run quietly', action='store_true', short='q')), )

class Run(ConfigurationMixIn):
    """base class providing common behaviour for pyreverse commands"""

    options = OPTIONS

    def __init__(self, args):
        ConfigurationMixIn.__init__(self, usage=__doc__)
        insert_default_options()
        self.manager = ASTNGManager()
        self.register_options_provider(self.manager)
        args = self.load_command_line_configuration()
        sys.exit(self.run(args))

    def run(self, args):
        """checking arguments and run project"""
        if not args:
            print self.help()
            return 1
        # insert current working directory to the python path to recognize
        # dependencies to local modules even if cwd is not in the PYTHONPATH
        sys.path.insert(0, os.getcwd())
        try:
            project = self.manager.project_from_files(args)
            linker = Linker(project, tag=True)
            handler = DiadefsHandler(self.config)
            diadefs = handler.get_diadefs(project, linker)
        finally:
            sys.path.pop(0)

        if self.config.output_format == "vcg":
            writer.VCGWriter(self.config).write(diadefs)
        else:
            writer.DotWriter(self.config).write(diadefs)
        return 0


if __name__ == '__main__':
    Run(sys.argv[1:])
