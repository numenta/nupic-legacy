# Copyright (c) 2000-2010 LOGILAB S.A. (Paris, FRANCE).
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
"""handle diagram generation options for class diagram or default diagrams
"""

from logilab.common.compat import builtins
BUILTINS_NAME = builtins.__name__
from logilab import astng
from logilab.astng.utils import LocalsVisitor

from pylint.pyreverse.diagrams import PackageDiagram, ClassDiagram

# diagram generators ##########################################################

class DiaDefGenerator:
    """handle diagram generation options
    """
    def __init__(self, linker, handler):
        """common Diagram Handler initialization"""
        self.config = handler.config
        self._set_default_options()
        self.linker = linker
        self.classdiagram = None # defined by subclasses

    def get_title(self, node):
        """get title for objects"""
        title = node.name
        if self.module_names:
            title =  '%s.%s' % (node.root().name, title)
        return title

    def _set_option(self, option):
        """activate some options if not explicitly deactivated"""
        # if we have a class diagram, we want more information by default;
        # so if the option is None, we return True
        if option is None:
            if self.config.classes:
                return True
            else:
                return False
        return option

    def _set_default_options(self):
        """set different default options with _default dictionary"""
        self.module_names = self._set_option(self.config.module_names)
        all_ancestors = self._set_option(self.config.all_ancestors)
        all_associated = self._set_option(self.config.all_associated)
        anc_level, ass_level = (0, 0)
        if  all_ancestors:
            anc_level = -1
        if all_associated:
            ass_level = -1
        if self.config.show_ancestors is not None:
            anc_level = self.config.show_ancestors
        if self.config.show_associated is not None:
            ass_level = self.config.show_associated
        self.anc_level, self.ass_level = anc_level, ass_level

    def _get_levels(self):
        """help function for search levels"""
        return self.anc_level, self.ass_level

    def show_node(self, node):
        """true if builtins and not show_builtins"""
        if self.config.show_builtin:
            return True
        return node.root().name != BUILTINS_NAME

    def add_class(self, node):
        """visit one class and add it to diagram"""
        self.linker.visit(node)
        self.classdiagram.add_object(self.get_title(node), node)

    def get_ancestors(self, node, level):
        """return ancestor nodes of a class node"""
        if level == 0:
            return
        for ancestor in node.ancestors(recurs=False):
            if not self.show_node(ancestor):
                continue
            yield ancestor

    def get_associated(self, klass_node, level):
        """return associated nodes of a class node"""
        if level == 0:
            return
        for ass_nodes in klass_node.instance_attrs_type.values() + \
                         klass_node.locals_type.values():
            for ass_node in ass_nodes:
                if isinstance(ass_node, astng.Instance):
                    ass_node = ass_node._proxied
                if not (isinstance(ass_node, astng.Class) 
                        and self.show_node(ass_node)):
                    continue
                yield ass_node

    def extract_classes(self, klass_node, anc_level, ass_level):
        """extract recursively classes related to klass_node"""
        if self.classdiagram.has_node(klass_node) or not self.show_node(klass_node):
            return
        self.add_class(klass_node)

        for ancestor in self.get_ancestors(klass_node, anc_level):
            self.extract_classes(ancestor, anc_level-1, ass_level)

        for ass_node in self.get_associated(klass_node, ass_level):
            self.extract_classes(ass_node, anc_level, ass_level-1)


class DefaultDiadefGenerator(LocalsVisitor, DiaDefGenerator):
    """generate minimum diagram definition for the project :

    * a package diagram including project's modules
    * a class diagram including project's classes
    """

    def __init__(self, linker, handler):
        DiaDefGenerator.__init__(self, linker, handler)
        LocalsVisitor.__init__(self)

    def visit_project(self, node):
        """visit an astng.Project node

        create a diagram definition for packages
        """
        mode = self.config.mode
        if len(node.modules) > 1:
            self.pkgdiagram = PackageDiagram('packages %s' % node.name, mode)
        else:
            self.pkgdiagram = None
        self.classdiagram = ClassDiagram('classes %s' % node.name, mode)

    def leave_project(self, node):
        """leave the astng.Project node

        return the generated diagram definition
        """
        if self.pkgdiagram:
            return self.pkgdiagram, self.classdiagram
        return self.classdiagram,

    def visit_module(self, node):
        """visit an astng.Module node

        add this class to the package diagram definition
        """
        if self.pkgdiagram:
            self.linker.visit(node)
            self.pkgdiagram.add_object(node.name, node)

    def visit_class(self, node):
        """visit an astng.Class node

        add this class to the class diagram definition
        """
        anc_level, ass_level = self._get_levels()
        self.extract_classes(node, anc_level, ass_level)

    def visit_from(self, node):
        """visit astng.From  and catch modules for package diagram
        """
        if self.pkgdiagram:
            self.pkgdiagram.add_from_depend(node, node.modname)


class ClassDiadefGenerator(DiaDefGenerator):
    """generate a class diagram definition including all classes related to a
    given class
    """

    def __init__(self, linker, handler):
        DiaDefGenerator.__init__(self, linker, handler)

    def class_diagram(self, project, klass):
        """return a class diagram definition for the given klass and its
        related klasses
        """

        self.classdiagram = ClassDiagram(klass, self.config.mode)
        if len(project.modules) > 1:
            module, klass = klass.rsplit('.', 1)
            module = project.get_module(module)
        else:
            module = project.modules[0]
            klass = klass.split('.')[-1]
        klass = module.ilookup(klass).next()

        anc_level, ass_level = self._get_levels()
        self.extract_classes(klass, anc_level, ass_level)
        return self.classdiagram

# diagram handler #############################################################

class DiadefsHandler:
    """handle diagram definitions :

    get it from user (i.e. xml files) or generate them
    """

    def __init__(self, config):
        self.config = config

    def get_diadefs(self, project, linker):
        """get the diagrams configuration data
        :param linker: astng.inspector.Linker(IdGeneratorMixIn, LocalsVisitor)
        :param project: astng.manager.Project        
        """

        #  read and interpret diagram definitions (Diadefs)
        diagrams = []
        generator = ClassDiadefGenerator(linker, self)
        for klass in self.config.classes:
            diagrams.append(generator.class_diagram(project, klass))
        if not diagrams:
            diagrams = DefaultDiadefGenerator(linker, self).visit(project)
        for diagram in diagrams:
            diagram.extract_relationships()
        return  diagrams
