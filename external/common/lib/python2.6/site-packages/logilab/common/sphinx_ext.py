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
from logilab.common.decorators import monkeypatch

from sphinx.ext import autodoc

class DocstringOnlyModuleDocumenter(autodoc.ModuleDocumenter):
    objtype = 'docstring'
    def format_signature(self):
        pass
    def add_directive_header(self, sig):
        pass
    def document_members(self, all_members=False):
        pass

    def resolve_name(self, modname, parents, path, base):
        if modname is not None:
            return modname, parents + [base]
        return (path or '') + base, []


#autodoc.add_documenter(DocstringOnlyModuleDocumenter)

def setup(app):
    app.add_autodocumenter(DocstringOnlyModuleDocumenter)



from sphinx.ext.autodoc import (ViewList, Options, AutodocReporter, nodes,
                                assemble_option_dict, nested_parse_with_titles)

@monkeypatch(autodoc.AutoDirective)
def run(self):
    self.filename_set = set()  # a set of dependent filenames
    self.reporter = self.state.document.reporter
    self.env = self.state.document.settings.env
    self.warnings = []
    self.result = ViewList()

    # find out what documenter to call
    objtype = self.name[4:]
    doc_class = self._registry[objtype]
    # process the options with the selected documenter's option_spec
    self.genopt = Options(assemble_option_dict(
        self.options.items(), doc_class.option_spec))
    # generate the output
    documenter = doc_class(self, self.arguments[0])
    documenter.generate(more_content=self.content)
    if not self.result:
        return self.warnings

    # record all filenames as dependencies -- this will at least
    # partially make automatic invalidation possible
    for fn in self.filename_set:
        self.env.note_dependency(fn)

    # use a custom reporter that correctly assigns lines to source
    # filename/description and lineno
    old_reporter = self.state.memo.reporter
    self.state.memo.reporter = AutodocReporter(self.result,
                                               self.state.memo.reporter)
    if self.name in ('automodule', 'autodocstring'):
        node = nodes.section()
        # necessary so that the child nodes get the right source/line set
        node.document = self.state.document
        nested_parse_with_titles(self.state, self.result, node)
    else:
        node = nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(self.result, 0, node)
    self.state.memo.reporter = old_reporter
    return self.warnings + node.children
