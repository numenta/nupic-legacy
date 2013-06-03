# copyright 2003-2012 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
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
"""Table management module."""
__docformat__ = "restructuredtext en"


class Table(object):
    """Table defines a data table with column and row names.
    inv:
        len(self.data) <= len(self.row_names)
        forall(self.data, lambda x: len(x) <= len(self.col_names))
    """

    def __init__(self, default_value=0, col_names=None, row_names=None):
        self.col_names = []
        self.row_names = []
        self.data = []
        self.default_value = default_value
        if col_names:
            self.create_columns(col_names)
        if row_names:
            self.create_rows(row_names)

    def _next_row_name(self):
        return 'row%s' % (len(self.row_names)+1)

    def __iter__(self):
        return iter(self.data)

    def __eq__(self, other):
        if other is None:
            return False
        else:
            return list(self) == list(other)

    def __ne__(self, other):
        return not self == other

    def __len__(self):
        return len(self.row_names)

    ## Rows / Columns creation #################################################
    def create_rows(self, row_names):
        """Appends row_names to the list of existing rows
        """
        self.row_names.extend(row_names)
        for row_name in row_names:
            self.data.append([self.default_value]*len(self.col_names))

    def create_columns(self, col_names):
        """Appends col_names to the list of existing columns
        """
        for col_name in col_names:
            self.create_column(col_name)

    def create_row(self, row_name=None):
        """Creates a rowname to the row_names list
        """
        row_name = row_name or self._next_row_name()
        self.row_names.append(row_name)
        self.data.append([self.default_value]*len(self.col_names))


    def create_column(self, col_name):
        """Creates a colname to the col_names list
        """
        self.col_names.append(col_name)
        for row in self.data:
            row.append(self.default_value)

    ## Sort by column ##########################################################
    def sort_by_column_id(self, col_id, method = 'asc'):
        """Sorts the table (in-place) according to data stored in col_id
        """
        try:
            col_index = self.col_names.index(col_id)
            self.sort_by_column_index(col_index, method)
        except ValueError:
            raise KeyError("Col (%s) not found in table" % (col_id))


    def sort_by_column_index(self, col_index, method = 'asc'):
        """Sorts the table 'in-place' according to data stored in col_index

        method should be in ('asc', 'desc')
        """
        sort_list = sorted([(row[col_index], row, row_name)
                     for row, row_name in zip(self.data, self.row_names)])
        # Sorting sort_list will sort according to col_index
        # If we want reverse sort, then reverse list
        if method.lower() == 'desc':
            sort_list.reverse()

        # Rebuild data / row names
        self.data = []
        self.row_names = []
        for val, row, row_name in sort_list:
            self.data.append(row)
            self.row_names.append(row_name)

    def groupby(self, colname, *others):
        """builds indexes of data
        :returns: nested dictionaries pointing to actual rows
        """
        groups = {}
        colnames = (colname,) + others
        col_indexes = [self.col_names.index(col_id) for col_id in colnames]
        for row in self.data:
            ptr = groups
            for col_index in col_indexes[:-1]:
                ptr = ptr.setdefault(row[col_index], {})
            ptr = ptr.setdefault(row[col_indexes[-1]],
                                 Table(default_value=self.default_value,
                                       col_names=self.col_names))
            ptr.append_row(tuple(row))
        return groups

    def select(self, colname, value):
        grouped = self.groupby(colname)
        try:
            return grouped[value]
        except KeyError:
            return []

    def remove(self, colname, value):
        col_index = self.col_names.index(colname)
        for row in self.data[:]:
            if row[col_index] == value:
                self.data.remove(row)


    ## The 'setter' part #######################################################
    def set_cell(self, row_index, col_index, data):
        """sets value of cell 'row_indew', 'col_index' to data
        """
        self.data[row_index][col_index] = data


    def set_cell_by_ids(self, row_id, col_id, data):
        """sets value of cell mapped by row_id and col_id to data
        Raises a KeyError if row_id or col_id are not found in the table
        """
        try:
            row_index = self.row_names.index(row_id)
        except ValueError:
            raise KeyError("Row (%s) not found in table" % (row_id))
        else:
            try:
                col_index = self.col_names.index(col_id)
                self.data[row_index][col_index] = data
            except ValueError:
                raise KeyError("Column (%s) not found in table" % (col_id))


    def set_row(self, row_index, row_data):
        """sets the 'row_index' row
        pre:
            type(row_data) == types.ListType
            len(row_data) == len(self.col_names)
        """
        self.data[row_index] = row_data


    def set_row_by_id(self, row_id, row_data):
        """sets the 'row_id' column
        pre:
            type(row_data) == types.ListType
            len(row_data) == len(self.row_names)
        Raises a KeyError if row_id is not found
        """
        try:
            row_index = self.row_names.index(row_id)
            self.set_row(row_index, row_data)
        except ValueError:
            raise KeyError('Row (%s) not found in table' % (row_id))


    def append_row(self, row_data, row_name=None):
        """Appends a row to the table
        pre:
            type(row_data) == types.ListType
            len(row_data) == len(self.col_names)
        """
        row_name = row_name or self._next_row_name()
        self.row_names.append(row_name)
        self.data.append(row_data)
        return len(self.data) - 1

    def insert_row(self, index, row_data, row_name=None):
        """Appends row_data before 'index' in the table. To make 'insert'
        behave like 'list.insert', inserting in an out of range index will
        insert row_data to the end of the list
        pre:
            type(row_data) == types.ListType
            len(row_data) == len(self.col_names)
        """
        row_name = row_name or self._next_row_name()
        self.row_names.insert(index, row_name)
        self.data.insert(index, row_data)


    def delete_row(self, index):
        """Deletes the 'index' row in the table, and returns it.
        Raises an IndexError if index is out of range
        """
        self.row_names.pop(index)
        return self.data.pop(index)


    def delete_row_by_id(self, row_id):
        """Deletes the 'row_id' row in the table.
        Raises a KeyError if row_id was not found.
        """
        try:
            row_index = self.row_names.index(row_id)
            self.delete_row(row_index)
        except ValueError:
            raise KeyError('Row (%s) not found in table' % (row_id))


    def set_column(self, col_index, col_data):
        """sets the 'col_index' column
        pre:
            type(col_data) == types.ListType
            len(col_data) == len(self.row_names)
        """

        for row_index, cell_data in enumerate(col_data):
            self.data[row_index][col_index] = cell_data


    def set_column_by_id(self, col_id, col_data):
        """sets the 'col_id' column
        pre:
            type(col_data) == types.ListType
            len(col_data) == len(self.col_names)
        Raises a KeyError if col_id is not found
        """
        try:
            col_index = self.col_names.index(col_id)
            self.set_column(col_index, col_data)
        except ValueError:
            raise KeyError('Column (%s) not found in table' % (col_id))


    def append_column(self, col_data, col_name):
        """Appends the 'col_index' column
        pre:
            type(col_data) == types.ListType
            len(col_data) == len(self.row_names)
        """
        self.col_names.append(col_name)
        for row_index, cell_data in enumerate(col_data):
            self.data[row_index].append(cell_data)


    def insert_column(self, index, col_data, col_name):
        """Appends col_data before 'index' in the table. To make 'insert'
        behave like 'list.insert', inserting in an out of range index will
        insert col_data to the end of the list
        pre:
            type(col_data) == types.ListType
            len(col_data) == len(self.row_names)
        """
        self.col_names.insert(index, col_name)
        for row_index, cell_data in enumerate(col_data):
            self.data[row_index].insert(index, cell_data)


    def delete_column(self, index):
        """Deletes the 'index' column in the table, and returns it.
        Raises an IndexError if index is out of range
        """
        self.col_names.pop(index)
        return [row.pop(index) for row in self.data]


    def delete_column_by_id(self, col_id):
        """Deletes the 'col_id' col in the table.
        Raises a KeyError if col_id was not found.
        """
        try:
            col_index = self.col_names.index(col_id)
            self.delete_column(col_index)
        except ValueError:
            raise KeyError('Column (%s) not found in table' % (col_id))


    ## The 'getter' part #######################################################

    def get_shape(self):
        """Returns a tuple which represents the table's shape
        """
        return len(self.row_names), len(self.col_names)
    shape = property(get_shape)

    def __getitem__(self, indices):
        """provided for convenience"""
        rows, multirows = None, False
        cols, multicols = None, False
        if isinstance(indices, tuple):
            rows = indices[0]
            if len(indices) > 1:
                cols = indices[1]
        else:
            rows = indices
        # define row slice
        if isinstance(rows, str):
            try:
                rows = self.row_names.index(rows)
            except ValueError:
                raise KeyError("Row (%s) not found in table" % (rows))
        if isinstance(rows, int):
            rows = slice(rows, rows+1)
            multirows = False
        else:
            rows = slice(None)
            multirows = True
        # define col slice
        if isinstance(cols, str):
            try:
                cols = self.col_names.index(cols)
            except ValueError:
                raise KeyError("Column (%s) not found in table" % (cols))
        if isinstance(cols, int):
            cols = slice(cols, cols+1)
            multicols = False
        else:
            cols = slice(None)
            multicols = True
        # get sub-table
        tab = Table()
        tab.default_value = self.default_value
        tab.create_rows(self.row_names[rows])
        tab.create_columns(self.col_names[cols])
        for idx, row in enumerate(self.data[rows]):
            tab.set_row(idx, row[cols])
        if multirows :
            if multicols:
                return tab
            else:
                return [item[0] for item in tab.data]
        else:
            if multicols:
                return tab.data[0]
            else:
                return tab.data[0][0]

    def get_cell_by_ids(self, row_id, col_id):
        """Returns the element at [row_id][col_id]
        """
        try:
            row_index = self.row_names.index(row_id)
        except ValueError:
            raise KeyError("Row (%s) not found in table" % (row_id))
        else:
            try:
                col_index = self.col_names.index(col_id)
            except ValueError:
                raise KeyError("Column (%s) not found in table" % (col_id))
        return self.data[row_index][col_index]

    def get_row_by_id(self, row_id):
        """Returns the 'row_id' row
        """
        try:
            row_index = self.row_names.index(row_id)
        except ValueError:
            raise KeyError("Row (%s) not found in table" % (row_id))
        return self.data[row_index]

    def get_column_by_id(self, col_id, distinct=False):
        """Returns the 'col_id' col
        """
        try:
            col_index = self.col_names.index(col_id)
        except ValueError:
            raise KeyError("Column (%s) not found in table" % (col_id))
        return self.get_column(col_index, distinct)

    def get_columns(self):
        """Returns all the columns in the table
        """
        return [self[:, index] for index in range(len(self.col_names))]

    def get_column(self, col_index, distinct=False):
        """get a column by index"""
        col = [row[col_index] for row in self.data]
        if distinct:
            col = list(set(col))
        return col

    def apply_stylesheet(self, stylesheet):
        """Applies the stylesheet to this table
        """
        for instruction in stylesheet.instructions:
            eval(instruction)


    def transpose(self):
        """Keeps the self object intact, and returns the transposed (rotated)
        table.
        """
        transposed = Table()
        transposed.create_rows(self.col_names)
        transposed.create_columns(self.row_names)
        for col_index, column in enumerate(self.get_columns()):
            transposed.set_row(col_index, column)
        return transposed


    def pprint(self):
        """returns a string representing the table in a pretty
        printed 'text' format.
        """
        # The maximum row name (to know the start_index of the first col)
        max_row_name = 0
        for row_name in self.row_names:
            if len(row_name) > max_row_name:
                max_row_name = len(row_name)
        col_start = max_row_name + 5

        lines = []
        # Build the 'first' line <=> the col_names one
        # The first cell <=> an empty one
        col_names_line = [' '*col_start]
        for col_name in self.col_names:
            col_names_line.append(col_name + ' '*5)
        lines.append('|' + '|'.join(col_names_line) + '|')
        max_line_length = len(lines[0])

        # Build the table
        for row_index, row in enumerate(self.data):
            line = []
            # First, build the row_name's cell
            row_name = self.row_names[row_index]
            line.append(row_name + ' '*(col_start-len(row_name)))

            # Then, build all the table's cell for this line.
            for col_index, cell in enumerate(row):
                col_name_length = len(self.col_names[col_index]) + 5
                data = str(cell)
                line.append(data + ' '*(col_name_length - len(data)))
            lines.append('|' + '|'.join(line) + '|')
            if len(lines[-1]) > max_line_length:
                max_line_length = len(lines[-1])

        # Wrap the table with '-' to make a frame
        lines.insert(0, '-'*max_line_length)
        lines.append('-'*max_line_length)
        return '\n'.join(lines)


    def __repr__(self):
        return repr(self.data)

    def as_text(self):
        data = []
        # We must convert cells into strings before joining them
        for row in self.data:
            data.append([str(cell) for cell in row])
        lines = ['\t'.join(row) for row in data]
        return '\n'.join(lines)



class TableStyle:
    """Defines a table's style
    """

    def __init__(self, table):

        self._table = table
        self.size = dict([(col_name, '1*') for col_name in table.col_names])
        # __row_column__ is a special key to define the first column which
        # actually has no name (<=> left most column <=> row names column)
        self.size['__row_column__'] = '1*'
        self.alignment = dict([(col_name, 'right')
                               for col_name in table.col_names])
        self.alignment['__row_column__'] = 'right'

        # We shouldn't have to create an entry for
        # the 1st col (the row_column one)
        self.units = dict([(col_name, '') for col_name in table.col_names])
        self.units['__row_column__'] = ''

    # XXX FIXME : params order should be reversed for all set() methods
    def set_size(self, value, col_id):
        """sets the size of the specified col_id to value
        """
        self.size[col_id] = value

    def set_size_by_index(self, value, col_index):
        """Allows to set the size according to the column index rather than
        using the column's id.
        BE CAREFUL : the '0' column is the '__row_column__' one !
        """
        if col_index == 0:
            col_id = '__row_column__'
        else:
            col_id = self._table.col_names[col_index-1]

        self.size[col_id] = value


    def set_alignment(self, value, col_id):
        """sets the alignment of the specified col_id to value
        """
        self.alignment[col_id] = value


    def set_alignment_by_index(self, value, col_index):
        """Allows to set the alignment according to the column index rather than
        using the column's id.
        BE CAREFUL : the '0' column is the '__row_column__' one !
        """
        if col_index == 0:
            col_id = '__row_column__'
        else:
            col_id = self._table.col_names[col_index-1]

        self.alignment[col_id] = value


    def set_unit(self, value, col_id):
        """sets the unit of the specified col_id to value
        """
        self.units[col_id] = value


    def set_unit_by_index(self, value, col_index):
        """Allows to set the unit according to the column index rather than
        using the column's id.
        BE CAREFUL :  the '0' column is the '__row_column__' one !
        (Note that in the 'unit' case, you shouldn't have to set a unit
        for the 1st column (the __row__column__ one))
        """
        if col_index == 0:
            col_id = '__row_column__'
        else:
            col_id = self._table.col_names[col_index-1]

        self.units[col_id] = value


    def get_size(self, col_id):
        """Returns the size of the specified col_id
        """
        return self.size[col_id]


    def get_size_by_index(self, col_index):
        """Allows to get the size  according to the column index rather than
        using the column's id.
        BE CAREFUL : the '0' column is the '__row_column__' one !
        """
        if col_index == 0:
            col_id = '__row_column__'
        else:
            col_id = self._table.col_names[col_index-1]

        return self.size[col_id]


    def get_alignment(self, col_id):
        """Returns the alignment of the specified col_id
        """
        return self.alignment[col_id]


    def get_alignment_by_index(self, col_index):
        """Allors to get the alignment according to the column index rather than
        using the column's id.
        BE CAREFUL : the '0' column is the '__row_column__' one !
        """
        if col_index == 0:
            col_id = '__row_column__'
        else:
            col_id = self._table.col_names[col_index-1]

        return self.alignment[col_id]


    def get_unit(self, col_id):
        """Returns the unit of the specified col_id
        """
        return self.units[col_id]


    def get_unit_by_index(self, col_index):
        """Allors to get the unit according to the column index rather than
        using the column's id.
        BE CAREFUL : the '0' column is the '__row_column__' one !
        """
        if col_index == 0:
            col_id = '__row_column__'
        else:
            col_id = self._table.col_names[col_index-1]

        return self.units[col_id]


import re
CELL_PROG = re.compile("([0-9]+)_([0-9]+)")

class TableStyleSheet:
    """A simple Table stylesheet
    Rules are expressions where cells are defined by the row_index
    and col_index separated by an underscore ('_').
    For example, suppose you want to say that the (2,5) cell must be
    the sum of its two preceding cells in the row, you would create
    the following rule :
        2_5 = 2_3 + 2_4
    You can also use all the math.* operations you want. For example:
        2_5 = sqrt(2_3**2 + 2_4**2)
    """

    def __init__(self, rules = None):
        rules = rules or []
        self.rules = []
        self.instructions = []
        for rule in rules:
            self.add_rule(rule)


    def add_rule(self, rule):
        """Adds a rule to the stylesheet rules
        """
        try:
            source_code = ['from math import *']
            source_code.append(CELL_PROG.sub(r'self.data[\1][\2]', rule))
            self.instructions.append(compile('\n'.join(source_code),
                'table.py', 'exec'))
            self.rules.append(rule)
        except SyntaxError:
            print "Bad Stylesheet Rule : %s [skipped]"%rule


    def add_rowsum_rule(self, dest_cell, row_index, start_col, end_col):
        """Creates and adds a rule to sum over the row at row_index from
        start_col to end_col.
        dest_cell is a tuple of two elements (x,y) of the destination cell
        No check is done for indexes ranges.
        pre:
            start_col >= 0
            end_col > start_col
        """
        cell_list = ['%d_%d'%(row_index, index) for index in range(start_col,
                                                                   end_col + 1)]
        rule = '%d_%d=' % dest_cell + '+'.join(cell_list)
        self.add_rule(rule)


    def add_rowavg_rule(self, dest_cell, row_index, start_col, end_col):
        """Creates and adds a rule to make the row average (from start_col
        to end_col)
        dest_cell is a tuple of two elements (x,y) of the destination cell
        No check is done for indexes ranges.
        pre:
            start_col >= 0
            end_col > start_col
        """
        cell_list = ['%d_%d'%(row_index, index) for index in range(start_col,
                                                                   end_col + 1)]
        num = (end_col - start_col + 1)
        rule = '%d_%d=' % dest_cell + '('+'+'.join(cell_list)+')/%f'%num
        self.add_rule(rule)


    def add_colsum_rule(self, dest_cell, col_index, start_row, end_row):
        """Creates and adds a rule to sum over the col at col_index from
        start_row to end_row.
        dest_cell is a tuple of two elements (x,y) of the destination cell
        No check is done for indexes ranges.
        pre:
            start_row >= 0
            end_row > start_row
        """
        cell_list = ['%d_%d'%(index, col_index) for index in range(start_row,
                                                                   end_row + 1)]
        rule = '%d_%d=' % dest_cell + '+'.join(cell_list)
        self.add_rule(rule)


    def add_colavg_rule(self, dest_cell, col_index, start_row, end_row):
        """Creates and adds a rule to make the col average (from start_row
        to end_row)
        dest_cell is a tuple of two elements (x,y) of the destination cell
        No check is done for indexes ranges.
        pre:
            start_row >= 0
            end_row > start_row
        """
        cell_list = ['%d_%d'%(index, col_index) for index in range(start_row,
                                                                   end_row + 1)]
        num = (end_row - start_row + 1)
        rule = '%d_%d=' % dest_cell + '('+'+'.join(cell_list)+')/%f'%num
        self.add_rule(rule)



class TableCellRenderer:
    """Defines a simple text renderer
    """

    def __init__(self, **properties):
        """keywords should be properties with an associated boolean as value.
        For example :
            renderer = TableCellRenderer(units = True, alignment = False)
        An unspecified property will have a 'False' value by default.
        Possible properties are :
            alignment, unit
        """
        self.properties = properties


    def render_cell(self, cell_coord, table, table_style):
        """Renders the cell at 'cell_coord' in the table, using table_style
        """
        row_index, col_index = cell_coord
        cell_value = table.data[row_index][col_index]
        final_content = self._make_cell_content(cell_value,
                                                table_style, col_index  +1)
        return self._render_cell_content(final_content,
                                         table_style, col_index + 1)


    def render_row_cell(self, row_name, table, table_style):
        """Renders the cell for 'row_id' row
        """
        cell_value = row_name
        return self._render_cell_content(cell_value, table_style, 0)


    def render_col_cell(self, col_name, table, table_style):
        """Renders the cell for 'col_id' row
        """
        cell_value = col_name
        col_index = table.col_names.index(col_name)
        return self._render_cell_content(cell_value, table_style, col_index +1)



    def _render_cell_content(self, content, table_style, col_index):
        """Makes the appropriate rendering for this cell content.
        Rendering properties will be searched using the
        *table_style.get_xxx_by_index(col_index)' methods

        **This method should be overridden in the derived renderer classes.**
        """
        return content


    def _make_cell_content(self, cell_content, table_style, col_index):
        """Makes the cell content (adds decoration data, like units for
        example)
        """
        final_content = cell_content
        if 'skip_zero' in self.properties:
            replacement_char = self.properties['skip_zero']
        else:
            replacement_char = 0
        if replacement_char and final_content == 0:
            return replacement_char

        try:
            units_on = self.properties['units']
            if units_on:
                final_content = self._add_unit(
                    cell_content, table_style, col_index)
        except KeyError:
            pass

        return final_content


    def _add_unit(self, cell_content, table_style, col_index):
        """Adds unit to the cell_content if needed
        """
        unit = table_style.get_unit_by_index(col_index)
        return str(cell_content) + " " + unit



class DocbookRenderer(TableCellRenderer):
    """Defines how to render a cell for a docboook table
    """

    def define_col_header(self, col_index, table_style):
        """Computes the colspec element according to the style
        """
        size = table_style.get_size_by_index(col_index)
        return '<colspec colname="c%d" colwidth="%s"/>\n' % \
               (col_index, size)


    def _render_cell_content(self, cell_content, table_style, col_index):
        """Makes the appropriate rendering for this cell content.
        Rendering properties will be searched using the
        table_style.get_xxx_by_index(col_index)' methods.
        """
        try:
            align_on = self.properties['alignment']
            alignment = table_style.get_alignment_by_index(col_index)
            if align_on:
                return "<entry align='%s'>%s</entry>\n" % \
                       (alignment, cell_content)
        except KeyError:
            # KeyError <=> Default alignment
            return "<entry>%s</entry>\n" % cell_content


class TableWriter:
    """A class to write tables
    """

    def __init__(self, stream, table, style, **properties):
        self._stream = stream
        self.style = style or TableStyle(table)
        self._table = table
        self.properties = properties
        self.renderer = None


    def set_style(self, style):
        """sets the table's associated style
        """
        self.style = style


    def set_renderer(self, renderer):
        """sets the way to render cell
        """
        self.renderer = renderer


    def update_properties(self, **properties):
        """Updates writer's properties (for cell rendering)
        """
        self.properties.update(properties)


    def write_table(self, title = ""):
        """Writes the table
        """
        raise NotImplementedError("write_table must be implemented !")



class DocbookTableWriter(TableWriter):
    """Defines an implementation of TableWriter to write a table in Docbook
    """

    def _write_headers(self):
        """Writes col headers
        """
        # Define col_headers (colstpec elements)
        for col_index in range(len(self._table.col_names)+1):
            self._stream.write(self.renderer.define_col_header(col_index,
                                                              self.style))

        self._stream.write("<thead>\n<row>\n")
        # XXX FIXME : write an empty entry <=> the first (__row_column) column
        self._stream.write('<entry></entry>\n')
        for col_name in self._table.col_names:
            self._stream.write(self.renderer.render_col_cell(
                col_name, self._table,
                self.style))

        self._stream.write("</row>\n</thead>\n")


    def _write_body(self):
        """Writes the table body
        """
        self._stream.write('<tbody>\n')

        for row_index, row in enumerate(self._table.data):
            self._stream.write('<row>\n')
            row_name = self._table.row_names[row_index]
            # Write the first entry (row_name)
            self._stream.write(self.renderer.render_row_cell(row_name,
                                                            self._table,
                                                            self.style))

            for col_index, cell in enumerate(row):
                self._stream.write(self.renderer.render_cell(
                    (row_index, col_index),
                    self._table, self.style))

            self._stream.write('</row>\n')

        self._stream.write('</tbody>\n')


    def write_table(self, title = ""):
        """Writes the table
        """
        self._stream.write('<table>\n<title>%s></title>\n'%(title))
        self._stream.write(
            '<tgroup cols="%d" align="left" colsep="1" rowsep="1">\n'%
            (len(self._table.col_names)+1))
        self._write_headers()
        self._write_body()

        self._stream.write('</tgroup>\n</table>\n')


