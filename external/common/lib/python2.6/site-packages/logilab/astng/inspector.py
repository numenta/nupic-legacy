# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
# copyright 2003-2010 Sylvain Thenault, all rights reserved.
# contact mailto:thenault@gmail.com
#
# This file is part of logilab-astng.
#
# logilab-astng is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 2.1 of the License, or (at your
# option) any later version.
#
# logilab-astng is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-astng. If not, see <http://www.gnu.org/licenses/>.
"""visitor doing some postprocessing on the astng tree.
Try to resolve definitions (namespace) dictionary, relationship...

This module has been imported from pyreverse
"""

__docformat__ = "restructuredtext en"

from os.path import dirname

from logilab.common.modutils import get_module_part, is_relative, \
     is_standard_module

from logilab import astng
from logilab.astng.exceptions import InferenceError
from logilab.astng.utils import LocalsVisitor

class IdGeneratorMixIn:
    """
    Mixin adding the ability to generate integer uid
    """
    def __init__(self, start_value=0):
        self.id_count = start_value
    
    def init_counter(self, start_value=0):
        """init the id counter
        """
        self.id_count = start_value
        
    def generate_id(self):
        """generate a new identifier
        """
        self.id_count += 1
        return self.id_count


class Linker(IdGeneratorMixIn, LocalsVisitor):
    """
    walk on the project tree and resolve relationships.
    
    According to options the following attributes may be added to visited nodes:
    
    * uid,
      a unique identifier for the node (on astng.Project, astng.Module,
      astng.Class and astng.locals_type). Only if the linker has been instantiated
      with tag=True parameter (False by default).
            
    * Function
      a mapping from locals names to their bounded value, which may be a
      constant like a string or an integer, or an astng node (on astng.Module,
      astng.Class and astng.Function).

    * instance_attrs_type
      as locals_type but for klass member attributes (only on astng.Class)
      
    * implements,
      list of implemented interface _objects_ (only on astng.Class nodes)
    """
    
    def __init__(self, project, inherited_interfaces=0, tag=False):
        IdGeneratorMixIn.__init__(self)
        LocalsVisitor.__init__(self)
        # take inherited interface in consideration or not
        self.inherited_interfaces = inherited_interfaces
        # tag nodes or not
        self.tag = tag
        # visited project
        self.project = project

        
    def visit_project(self, node):
        """visit an astng.Project node
        
         * optionally tag the node with a unique id
        """
        if self.tag:
            node.uid = self.generate_id()
        for module in node.modules:
            self.visit(module)
            
    def visit_package(self, node):
        """visit an astng.Package node
        
         * optionally tag the node with a unique id
        """
        if self.tag:
            node.uid = self.generate_id()
        for subelmt in node.values():
            self.visit(subelmt)
            
    def visit_module(self, node):
        """visit an astng.Module node
        
         * set the locals_type mapping
         * set the depends mapping
         * optionally tag the node with a unique id
        """
        if hasattr(node, 'locals_type'):
            return
        node.locals_type = {}
        node.depends = []
        if self.tag:
            node.uid = self.generate_id()
    
    def visit_class(self, node):
        """visit an astng.Class node
        
         * set the locals_type and instance_attrs_type mappings
         * set the implements list and build it
         * optionally tag the node with a unique id
        """
        if hasattr(node, 'locals_type'):
            return
        node.locals_type = {}
        if self.tag:
            node.uid = self.generate_id()
        # resolve ancestors
        for baseobj in node.ancestors(recurs=False):
            specializations = getattr(baseobj, 'specializations', [])
            specializations.append(node)
            baseobj.specializations = specializations
        # resolve instance attributes
        node.instance_attrs_type = {}
        for assattrs in node.instance_attrs.values():
            for assattr in assattrs:
                self.handle_assattr_type(assattr, node)
        # resolve implemented interface
        try:
            node.implements = list(node.interfaces(self.inherited_interfaces))
        except InferenceError:
            node.implements = ()

    def visit_function(self, node):
        """visit an astng.Function node
        
         * set the locals_type mapping
         * optionally tag the node with a unique id
        """
        if hasattr(node, 'locals_type'):
            return
        node.locals_type = {}
        if self.tag:
            node.uid = self.generate_id()
            
    link_project = visit_project
    link_module = visit_module
    link_class = visit_class
    link_function = visit_function
        
    def visit_assname(self, node):
        """visit an astng.AssName node

        handle locals_type
        """
        # avoid double parsing done by different Linkers.visit
        # running over the same project:
        if hasattr(node, '_handled'):
            return
        node._handled = True
        if node.name in node.frame():
            frame = node.frame()
        else:
            # the name has been defined as 'global' in the frame and belongs
            # there. Btw the frame is not yet visited as the name is in the 
            # root locals; the frame hence has no locals_type attribute
            frame = node.root()
        try:
            values = node.infered()
            try:
                already_infered = frame.locals_type[node.name]
                for valnode in values:
                    if not valnode in already_infered:
                        already_infered.append(valnode)
            except KeyError:
                frame.locals_type[node.name] = values
        except astng.InferenceError:
            pass

    def handle_assattr_type(self, node, parent):
        """handle an astng.AssAttr node

        handle instance_attrs_type
        """
        try:
            values = list(node.infer())
            try:
                already_infered = parent.instance_attrs_type[node.attrname]
                for valnode in values:
                    if not valnode in already_infered:
                        already_infered.append(valnode)
            except KeyError:
                parent.instance_attrs_type[node.attrname] = values
        except astng.InferenceError:
            pass
            
    def visit_import(self, node):
        """visit an astng.Import node
        
        resolve module dependencies
        """
        context_file = node.root().file
        for name in node.names:
            relative = is_relative(name[0], context_file)
            self._imported_module(node, name[0], relative)
        

    def visit_from(self, node):
        """visit an astng.From node
        
        resolve module dependencies
        """
        basename = node.modname
        context_file = node.root().file
        if context_file is not None:
            relative = is_relative(basename, context_file)
        else:
            relative = False
        for name in node.names:
            if name[0] == '*':
                continue
            # analyze dependencies
            fullname = '%s.%s' % (basename, name[0])
            if fullname.find('.') > -1:
                try:
                    # XXX: don't use get_module_part, missing package precedence
                    fullname = get_module_part(fullname, context_file)
                except ImportError:
                    continue
            if fullname != basename:
                self._imported_module(node, fullname, relative)

        
    def compute_module(self, context_name, mod_path):
        """return true if the module should be added to dependencies"""
        package_dir = dirname(self.project.path)
        if context_name == mod_path:
            return 0
        elif is_standard_module(mod_path, (package_dir,)):
            return 1
        return 0
    
    # protected methods ########################################################

    def _imported_module(self, node, mod_path, relative):
        """notify an imported module, used to analyze dependencies
        """
        module = node.root()
        context_name = module.name
        if relative:
            mod_path = '%s.%s' % ('.'.join(context_name.split('.')[:-1]),
                                  mod_path)
        if self.compute_module(context_name, mod_path):
            # handle dependencies
            if not hasattr(module, 'depends'):
                module.depends = []
            mod_paths = module.depends
            if not mod_path in mod_paths:
                mod_paths.append(mod_path)
