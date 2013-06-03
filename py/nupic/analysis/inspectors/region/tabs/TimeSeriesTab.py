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

import traceback

from enthought.traits.api import Trait, Float, List
from enthought.traits.ui.api import View, Group, HGroup, VGroup, Item
import numpy

from nupic.analysis.inspectors.region.tabs import RegionInspectorTab
from nupic.ui.enthought import PlotEditor
from nupic.engine import Array

class TimeSeriesTab(RegionInspectorTab):

  """
  Displays the region inputs and outputs over time.
  """

  @staticmethod
  def isRegionSupported(region):
    """Return True if the tab is appropriate for this region, False otherwise."""
    ns = region.spec
    return len(ns.inputs) > 0 or len(ns.outputs) > 0

  def __init__(self, region):

    RegionInspectorTab.__init__(self, region)
    self._inputNames = []
    self._inputValues = dict()
    self._outputNames = []
    self._outputValues = dict()

    self.nKeep = 2
    self.buffer = 25

    ns = self.region.spec
    emptyArray = numpy.zeros([0])
    for input, spec in ns.inputs.items():
      a = self.region.getInputData(input)
      if len(a):
        self._inputNames.append(input)
        assert not hasattr(self, input)
        self.add_trait(input,
            Float(
                label=input,
                desc=spec.description,
              )
          )
        setattr(self, input, -1)
        self._inputValues[input] = [(emptyArray, emptyArray)] * self.buffer
    for output, spec in ns.outputs.items():
      a = self.region.getOutputData(output)
      if len(a) > 0:
        self._outputNames.append(output)
        assert not hasattr(self, output)
        self.add_trait(output,
            Float(
                label=output,
                desc=spec.description,
              )
          )
        setattr(self, output, -1)
        self._outputValues[output] = [(emptyArray, emptyArray)] * self.buffer
    self.__updateIO()
    self._createView()

  def _plotTS(self, editor, values):
    if not editor.control.IsShownOnScreen():
      return

    def _getColor(i):
      # colors = 'bgrcmykw'
      colors = 'bgrcmyk'
      return colors[i % len(colors)]

    ts = None
    if editor.name in self._inputValues:
      ts = self._inputValues[editor.name]
    elif editor.name in self._outputValues:
      ts = self._outputValues[editor.name]
    else:
      raise RuntimeError("Unrecognized trait attached to plot.")

    # print editor.name
    # print values
    # print tsValues
    if (ts is not None) and len(ts):
      editor._axes.cla()
      nCols = len(ts[-1][0]) # Most recent.
      # cols = range(nCols)
      cols = set()
      for y, order in ts:
        cols.update(order)
      cols = sorted(cols)
      for col in cols:
        colColor = _getColor(col)
        high = numpy.array([(col in order) for y, order in ts])
        # Get values before and after high values.
        for io in xrange(1, 3+1):
          high[0:-io] += high[io]
          high[io:] += high[0:-io]
        high = (high > 0)
        exHigh = numpy.zeros(len(high)+2)
        exHigh[1:-1] = high
        begins = numpy.where(exHigh[1:] > exHigh[:-1])[0]
        ends = numpy.where(exHigh[1:] < exHigh[:-1])[0] - 1
        y = numpy.array([(value[col] if col < len(value) else 0)
            for value, order in ts])
        for b, e in zip(begins, ends):
          xr = numpy.arange(b, e)
          yr = y[b:e]
          if len(xr) != len(yr):
            print xr
            print yr
            import pdb; pdb.set_trace()
          editor._axes.plot(xr, yr, colColor)
          # print numpy.vstack((xr, yr))
      editor._axes.set_xlim(0, len(ts))

  def __updateIO(self):
    inputsToRemove = set()
    ns = self.region.spec
    for input in self._inputNames:
      try:
        spec = ns.inputs[input]
        inputResponse = self.region.getInputData(input)
      except Exception, e:
        print e.message
        if "is not a variable" in e.message:
          inputsToRemove.add(input)
          continue
        else:
          raise
      cinput = inputResponse
      order = cinput.argsort()[-self.nKeep:]
      current = self._inputValues[input]
      current.append((cinput, order))
      nCurrent = len(current)
      if nCurrent > self.buffer:
        self._inputValues[input] = current[(nCurrent - self.buffer):]
      setattr(self, input, getattr(self, input) + 1)

    for itr in inputsToRemove:
      self._inputNames.remove(itr)

    outputsToRemove = set()

    for output in self._outputNames:
      # No clean way to check if output is available in the runtime engine?
      try:
        spec = ns.outputs[output]
        outputResponse = Array(spec.dataType)
      except Exception, e:
        if "Invalid variable name" in e.message:
          outputsToRemove.add(output)
          continue
        else:
          raise
      coutput = _t2v(outputResponse)
      order = coutput.argsort()[-self.nKeep:]
      current = self._outputValues[output]
      current.append((coutput, order))
      nCurrent = len(current)
      if nCurrent > self.buffer:
        self._outputValues[output] = current[(nCurrent - self.buffer):]
      setattr(self, output, getattr(self, output) + 1)

    for otr in outputsToRemove:
      self._outputNames.remove(otr)

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
    self.__updateIO()

  def _createView(self):
    """Set up the view for the traits."""
    wScale = 0.75
    hScale = 1.0
    inputsGroup = []
    for input in self._inputNames:
      inputsGroup.append(Item(
          name=input,
          editor=PlotEditor(
              title=input,
              verticalToolbar=True,
              drawPlot=self._plotTS
            ),
          show_label=False,
          style='custom',
          width=int(self.plotSize[0]*wScale),
          height=int(self.plotSize[1]*hScale),
        ))
    outputsGroup = []
    for output in self._outputNames:
      outputsGroup.append(Item(
          name=output,
          editor=PlotEditor(
              title=output,
              verticalToolbar=True,
              drawPlot=self._plotTS
            ),
          show_label=False,
          style='custom',
          width=int(self.plotSize[0]*wScale),
          height=int(self.plotSize[1]*hScale),
        ))
    self.traits_view = View(
        HGroup(
            VGroup(inputsGroup, label="Inputs"),
            VGroup(outputsGroup, label="Outputs"),
          ),
        title="Time Series",
      )

def _t2v(x):
  return x.asNumpyArray()
  #if len(x) > 1:
  #  return numpy.concatenate([r.getValueAsFloatArray() for r in x])
  #else:
  #  assert len(x) == 1
  #  return numpy.array(x[0].getValueAsFloatArray())