# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import logging
import traceback

from enthought.traits.api import *
from enthought.traits.ui.api import *

from nupic import analysis
from nupic.analysis.inspectors.region.tabs import RegionInspectorTab
from nupic.ui.enthought import PlotEditor


import nupic
from nupic.engine import Real32Array, UInt32Array

dataTypeMapping = {
  'Byte': Str,
  'Int16': Int,
  'UInt16': Int,
  'Int32': Int,
  'UInt32': Int,
  'Int64': Int,
  'UInt64': Int,
  'Real32': Float,
  'Real32': Float,
  'Handle': CStr
}

def _getParameters(region):
  return dict((k, v) for (k,v) in region.spec.parameters.items()
           if (not k.startswith('dense') and k != 'self'))

def _getDataType(spec):
  return spec.dataType

def _getDescription(spec):
  return spec.description

def _isWritable(spec):
  return spec.accessMode == 'ReadWrite'

def _isMultiple(spec):
  if _isString(spec):
    return False
  return (spec.constraints == 'multiple') or (spec.count != 1)

def _isString(spec):
  return (spec.dataType == 'Byte' and spec.count != 1) or \
          (spec.dataType == 'Handle' and spec.constraints == 'string')

def _isBoolean(spec):
  return spec.constraints == 'bool'

def _isEnum(spec):

  return spec.constraints.startswith('enum:')

def _getEnumValues(spec):
  assert _isEnum(spec)
  values = spec.constraints[len('enum '):].split(',')
  values = [v.strip() for v in values]
  return values

def _getParameter(region, name):
  return region.getSelf().getParameter(name, -1)

class ParametersTab(RegionInspectorTab):

  """
  Displays any region parameter which matches one of the predefined types.
  Also handles several parameter names which require special processing.

  This tab is commonly subclassed by others. Typically, a subclass will only
  need to override _createView() in order to set up a custom view. The tab
  will automatically only update parameters that appear in the view.
  """

  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise."""
    return True

  # If overriden by a subclass and set to a list, only parameters with these
  #  names will be shown
  allowedParameters = 'all'

  # If allowedParameters is 'all', we'll look at this to take parameters out
  # of the list...
  disallowedParameters = []

  # If the Spec declares a parameter to be 'multiple' (array/matrix/etc.),
  # it will only be shown if it has one of these names
  allowedMultipleParameters = (
    'coincidenceVectorCounts',
    'spatialPoolerOutput',
    'categoryGroupSizes',
    'spatialPoolerOutput',
  )

  title = 'Parameters'

  def __init__(self, region):

    RegionInspectorTab.__init__(self, region)

    self._addTraits()
    self._createView()

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    """
    Called automatically in response to runtime engine activity.

    Extra arguments (optional) are passed by the wrapped methods,
    and they can be used to avoid unnecessary updating.

    @param methodName -- Class method that was called.
    @param elementName -- Name of RuntimeElement.
    @param args -- Positional arguments passed to the method.
    @param kwargs -- Keyword arguments passed to the method.
    """
    for name, spec in self.parameters.iteritems():
      # Skip parameters that aren't in the view
      if name not in str(self.traits_view):
        continue

      # Special parameters
      if name == 'TAM':
        sparseTAM = analysis.responses.GetTAM(self.region)
        # Only display if the TAM has some data but is not too large
        if sparseTAM.nNonZeros() > 0:
          if sparseTAM.nRows() <= 1000:
            self.TAM = sparseTAM.toDense()
            self.tamTooLarge = False
          else:
            self.tamTooLarge = True
      elif name == 'sortedTAM':
        # Only display the sorted TAM if groups have been formed
        if _getParameter(self.region, 'groupCount'):
          if analysis.responses.GetTAM(self.region).nRows() <= 1000:
            self.sortedTAM = analysis.GetSortedTAM(self.region)

      # Other parameters
      else:
        try:
          val = _getParameter(self.region, name)
        except Exception, e:
          print "Trying to update:", self.region, name
          traceback.print_exc()
          continue
        if _isEnum(spec):
          try:
            val = _getEnumValues[int(val)]
          except ValueError:
            pass
        elif type(val) is tuple:
          val = list(val)
        # TODO: formalize this, or use CStr subclass to handle it
        elif name == 'imageInfo' and val is None:
          val = []
        else:
          # Handle special case of 'multiple' parameters like spOverlapDistribution
          if type(val) in (UInt32Array, Real32Array):
            val = list(val.asNumpyArray())
        # Coerce single values that should be multiple to lists
        if self._is_list_trait(name) and type(val) is not list:
          val = [val]

        if _isString(spec):
          val = str(val)

        if isinstance(val, long):
          val = int(val)

        setattr(self, name, val)

  def _addTraits(self):
    """Use the Spec to add parameters as traits."""
    self.parameters = {}
    parameters = _getParameters(self.region)
    if self.allowedParameters != 'all':
      assert not self.disallowedParameters, \
             "Can only use one of allowedParameters and disallowedParameters"
      parameters = dict([(key, value) for key, value in parameters.items()
                         if key in self.allowedParameters])
    elif self.disallowedParameters:
      parameters = dict([(key, value) for key, value in parameters.items()
                         if key not in self.disallowedParameters])

    for name, spec in parameters.items():
      typeName = _getDataType(spec)
      description = _getDescription(spec)

      # Ignore hidden parameters
      if name.startswith('nta_'):
        continue
      # # Ignore PyObject parameters
      # if typeName == 'PyObject':
      #   continue

      # Special parameters
      if name == 'coincidenceVectorCounts':
        trait = List(name=name, desc=description)
      elif name == 'spatialPoolerOutput':
        trait = List(name=name, desc=description)
      elif name == 'TAM':
        logging.debug("Skipping TAM, which appears in TAMTab instead")
        continue

      # Other parameters
      else:
        # Get relevant information from the spec
        if _isMultiple(spec):
          if name not in self.allowedMultipleParameters:
            logging.debug("Skipping unknown multiple parameter %s" % name)
            continue
          trait = List(label=name, desc=description)
        elif _isEnum(spec):
          # Enum is special because it must be provided with the list of values
          trait = Enum(_getEnumValues(spec), label=name, desc=description)
        elif _isBoolean(spec):
          trait = CBool(label=name, desc=description)
        elif (typeName in dataTypeMapping):
          # Use the mapping for the other types
          if typeName in ('int', 'uint', 'float') or ('Int' in typeName) or \
            ('Real' in typeName):
            trait = dataTypeMapping[typeName](label=name, desc=description,
              auto_set=False, enter_set=True)
          else:
            trait = dataTypeMapping[typeName](label=name, desc=description)
        else:
          # Skip unknown types
          logging.debug("Don't know how to display parameter %s" % name)
          continue

      # Add the trait
      self.add_trait(name, trait)
      # Store the spec in the dictionary of parameters
      self.parameters[name] = spec

  def _createView(self):
    """Set up the view for the traits."""

    # Maintain two separate lists for settable and non-settable parameters
    dynamic = []
    static = []
    for name in sorted(self.parameters):
      spec = self.parameters[name]
      if _isWritable(spec):
        style = 'simple'
      else:
        style = 'readonly'
      if _isString(spec):
        item = Item(name=name, style=style,
          editor=TextEditor(auto_set=False, enter_set=True))
      elif _isMultiple(spec):
        item = Group(Item(name=name, editor=PlotEditor(title=name,
                                                       verticalToolbar=True),
                          style='custom', show_label=False,
                          width=self.plotSize[0]-self.toolbarSize,
                          height=-self.plotSize[1]))
      elif _isBoolean(spec) and not _isWritable(spec):
        item = Item(name=name, enabled_when='False')
      else:
        item = Item(name=name, style=style)
      # Put in the appropriate list based on access
      if _isWritable(spec):
        dynamic.append(item)
      else:
        static.append(item)

    # Create groups from the lists
    dynamicGroup = staticGroup = None
    if dynamic:
      dynamicGroup = Group(dynamic, label='Dynamic', show_border=True)
    if static:
      staticGroup = Group(static, label='Static', show_border=True)

    # Create the view
    self.traits_view = View(
      Group([g for g in (dynamicGroup, staticGroup) if g]),
      title=self.title,
      scrollable=True
    )