# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
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

"""
This file contains the two GUIs for the LPF: TrainingGUI and
InferenceGUI.

They subclass from PredictionGUI. Both essentially just pull a few inspectors
together in one window. Each shows a set of controls (RuntimeInspector) and the
current output from the sensor (RecordSensorInspector). The Inference GUI
also shows the top inference results (ResultsInspector). Both have a button in
the top-right corner to launch more inspectors.

The GUIs are set up by the LPF. When the user specifies the -g
switch to use the GUIs, the LPF passes control to the GUIs to run the experiment
instead of calling net.run(). The GUI is created before training or inference
starts, start() is called for each level of training or each test set of
inference, and then the GUI is destroyed.
"""
import sys
import wx
from nupic.frameworks.prediction.experiment import Experiment
from nupic.support import title
from nupic.analysis import inspect
from nupic.analysis.inspectors.network import PredictionRuntimeInspector, ResultsInspector
from nupic.analysis.inspectors.MultiInspector import getInspectorClass
from nupic.ui.enthought import patchEnthoughtClasses
from nupic.support.resources import getNTAImage
from nupic.analysis import _inspect

class PredictionGUI(wx.Frame):

  """
  The base class for the LPF GUIs. Not used on its own.
  Shows a RuntimeInspector (controls) and a MiniRecordSensorInspector (current
  record).
  """

  def __init__(self, experiment, tierCount=0, addInspectorButton=True):
    """
    experiment -- the experiment to be run.
    tierCount -- Number of tiers in the network, for training, including the
      sensor but not including the effector. Set by TrainingGUI but left at 0
      by InferenceGUI.
    addInspectorButton -- Whether to put an inspector button (magnifying glass)
      in the top-right. Set to False by InferenceGUI because it adds another
      panel to the right and so it adds the inspector button itself.
    """
    assert isinstance(experiment, Experiment)

    wx.Frame.__init__(self, None,
      style=wx.DEFAULT_FRAME_STYLE - wx.MAXIMIZE_BOX - wx.RESIZE_BORDER)

    # Modify several Enthought (Traits) classes to fix bugs
    patchEnthoughtClasses()

    # Set up the font use for inspector titles
    self.titleFont = self.GetFont()
    self.titleFont.SetWeight(wx.FONTWEIGHT_BOLD)
    self.titleFont.SetPointSize(self.titleFont.GetPointSize() + 2)

    self.experiment = experiment
    net = self.network = experiment.network
    #if net is None:
    #  from dbgp.client import brk; brk(port=9011)
    assert net is not None
    self.tierCount = tierCount

    multipleDatasets = not tierCount

    # Catch when the window is closed in order to shut down the inspectors
    self.Bind(wx.EVT_CLOSE, self.close)

    # Create a single panel to hold all the inspectors
    self.panel = wx.Panel(self)
    # The inspectors will be laid out left-to-right in a horizontal sizer
    self.hSizer = wx.BoxSizer(wx.HORIZONTAL)
    self.hSizer.AddSpacer(2)

    # Create the inspector button, which will be added to a sizer later
    inspectorBitmap = wx.Bitmap(getNTAImage('magnifying_glass_24_24'))
    self.inspectorBitmap = wx.StaticBitmap(self.panel, bitmap=inspectorBitmap)
    wx.EVT_LEFT_DOWN(self.inspectorBitmap, self.launchInspector)

    # Add the RuntimeInspector and its title
    runtimeSizer = wx.BoxSizer(wx.VERTICAL)
    self.title = wx.StaticText(self.panel, label=" ")
    self.title.SetFont(self.titleFont)
    self.runtimeInspector = PredictionRuntimeInspector(parent=self.panel,
      experiment=experiment, tierCount=tierCount, showProgressBar=True,
      multipleDatasets=multipleDatasets, startImmediately=False)
    # Add to a vertical sizer
    runtimeSizer.Add(self.title, flag=wx.ALL, border=3)
    runtimeSizer.Add(
      self.runtimeInspector.edit_traits(parent=self.panel,
        view=self.runtimeInspector.traits_view, kind='panel').control)
    # Add the vertical sizer to the horizontal sizer
    self.hSizer.Add(runtimeSizer, flag=wx.ALL, border=3)

    # Add a vertical line in between the inspectors
    self.hSizer.Add(wx.StaticLine(self.panel, style=wx.LI_VERTICAL),
                    flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=2)

    # Add the MiniRecordSensor Inspector
    # This has now been generalized to handle other mini inspectors
    sensorSizer = wx.BoxSizer(wx.VERTICAL)
    sensorTitle = wx.StaticText(self.panel, label='Sensor output')
    sensorTitle.SetFont(self.titleFont)
    sensor = net.regions['sensor']
    inspectorClass = getInspectorClass(sensor, "Mini%sInspector")
    self.sensorInspector = inspectorClass(parent=self.panel, region=sensor)

    # Add to a vertical sizer
    if addInspectorButton:
      # Add the title and the inspector button in a horizontal sizer
      titleSizer = wx.BoxSizer(wx.HORIZONTAL)
      titleSizer.Add(sensorTitle, flag=wx.LEFT|wx.RIGHT|wx.TOP, border=3)
      titleSizer.AddStretchSpacer()
      titleSizer.Add(self.inspectorBitmap)
      sensorSizer.Add(titleSizer, flag=wx.EXPAND|wx.RIGHT, border=2)
    else:
      # Add the title without the inspector button
      sensorSizer.Add(sensorTitle, flag=wx.LEFT|wx.RIGHT|wx.TOP, border=3)
    sensorSizer.AddStretchSpacer()
    sensorSizer.Add(
      self.sensorInspector.edit_traits(parent=self.panel, kind='panel').control)
    sensorSizer.AddStretchSpacer()
    # Add the vertical sizer to the horizontal sizer
    self.hSizer.Add(sensorSizer, flag=wx.LEFT|wx.TOP|wx.RIGHT|wx.EXPAND,
                    border=3)

    # Assign the horizontal sizer as the sizer for the panel
    self.panel.SetSizer(self.hSizer)

    # This list is used to unregister the inspectors when the window is closed
    self.inspectors = [self.runtimeInspector, self.sensorInspector]

    menuBar, self.menuItemIDs = _inspect.createInspectorMenus()
    self.SetMenuBar(menuBar)
    self.Bind(wx.EVT_MENU, self.onMenu)

    self.tier = -1
    self.started = False

  def _getPhase(self, e):
    index = e.position.phase
    name = e.workflow[index][0]
    return e.description[name]

  def start(self, iterationCount=0, tier=0):
    """
    Calls RuntimeInspector.start().

    If this is the first call to start(), displays the GUI on the screen.
    """
    if not self.IsShown():
      # Have the RuntimeInspector show this window after its initialization
      callback = self.show
    else:
      callback = lambda: None

    #from dbgp.client import brk; brk(port=9011)
    self.runtimeInspector.start(iterationCount, target=None, tier=tier, stop=False, callback=callback)

  def show(self):
    """Show the GUI on the screen, after it is fully set up."""

    self.SetClientSize(self.panel.GetBestSize())
    try:
      self.Center()
    except wx._core.PyAssertionError:
      # Sometimes see this assertion (not sure why)
      pass
    self.Show(True)

  def close(self, event=None):
    """
    Stop the RuntimeInspector, and unregister the inspectors from the global
    list of listeners.
    """

    self.runtimeInspector.stop()
    for inspector in self.inspectors:
      inspector.unregister()
    if event:
      event.Skip()  # Being called from EVT_CLOSE
    else:
      self.Destroy()  # Being called from the VF; shut down completely

  def launchInspector(self, event=None):
    """Launch a standalone inspector."""

    # Create the new inspector, without the RuntimeInspector (because there
    # should only be one of those at any given time, and this GUI already
    # has one)
    inspect(self.network, showRun=False)

  def onMenu(self, event):
    """Handle custom menu events for inspectors, such as saving the config."""

    menuItemID = event.GetId()
    name = self.menuItemIDs.get(menuItemID, None)
    if name:
      if name == 'loadConfig':
        _inspect.loadInspectors(self.network, showRun=False)
      elif name == 'saveConfig':
        _inspect.saveInspectors()
      elif name == 'enterPrompt':
        _inspect.enterPrompt(self.network)
      elif name == 'enableLogging':
        _inspect.enableLogging()
      else:
        raise RuntimeError('Unknown command name: %s' % name)
    else:
      event.Skip()


class TrainingGUI(PredictionGUI):

  """GUI used during training. Almost the same as the base class."""

  def __init__(self, experiment):
    """Arguments are passed along to the base class. Just sets the title."""
    PredictionGUI.__init__(self, experiment=experiment)

    # Set the window title
    self.SetTitle("Training network")

  def start(self):
    """Called for each tier. Sets the title and then calls the base class."""
    #title()
    e = self.experiment
    for name in 'spTrain', 'tpTrain', 'classifierTrain':
      phase = e.description[name]
      if len(phase) > 0:
        phase[0]['setup'].append(self.onPhaseSetup)

    phase = e.description['classifierTrain']
    if len(phase) == 0:
      # Add dymmy phase if needed
      phase.append(dict(name='dummy',
                        iterationCount=0,
                        setup=[],
                        iter=[],
                        finish=[self.onPhaseTeardown]))

    phaseName = e.workflow[0][0]
    first = e.description[phaseName]
    if len(first) > 0:
      # There may be no steps in the first phase
      iterationCount = first[0]['iterationCount']
    else:
      iterationCount = 0
    PredictionGUI.start(self, iterationCount, self.tier)

  def onPhaseSetup(self, exp):
    phaseName = exp.workflow[exp.position.phase][0]
    self.title.SetLabel(phaseName)
    self.tier += 1

  def onPhaseTeardown(self, exp):
    #title()

    #from dbgp.client import brk; brk(port=9011)
    phaseName = exp.workflow[exp.position.phase][0]
    assert phaseName == 'classifierTrain'

    self.close()

class InferenceGUI(PredictionGUI):

  def __init__(self, experiment):
    """
    Adds the ResultsInspector and a magnifying glass button to the base class.

    experiment -- the running experiment.
    """
    PredictionGUI.__init__(self, experiment=experiment, addInspectorButton=False)

    # Set the RuntimeInspector title
    self.title.SetLabel('Running inference')

    # Add a vertical line in between the inspectors
    self.hSizer.Add(wx.StaticLine(self.panel, style=wx.LI_VERTICAL),
                    flag=wx.EXPAND|wx.LEFT|wx.RIGHT, border=2)

    # Add the ResultsInspector and its title
    resultsSizer = wx.BoxSizer(wx.VERTICAL)
    title = wx.StaticText(self.panel, label='Inference results')
    title.SetFont(self.titleFont)
    self.resultsInspector = ResultsInspector(parent=self.panel,
                              network=experiment.network, numTopResults=3)
    # Add the title and the inspector button in a horizontal sizer
    titleSizer = wx.BoxSizer(wx.HORIZONTAL)
    titleSizer.Add(title, flag=wx.ALL, border=3)
    titleSizer.AddStretchSpacer()
    titleSizer.Add(self.inspectorBitmap)
    # Add to a vertical sizer
    resultsSizer.Add(titleSizer, flag=wx.EXPAND|wx.RIGHT|wx.BOTTOM, border=2)
    resultsSizer.AddStretchSpacer()
    resultsSizer.Add(self.resultsInspector.edit_traits(parent=self.panel,
                                                       kind='panel').control)
    resultsSizer.AddStretchSpacer()
    # Add the vertical sizer to the horizontal sizer
    self.hSizer.Add(resultsSizer, flag=wx.ALL|wx.EXPAND, border=3)

    # Append the results inspector to the list of inspectors
    self.inspectors.append(self.resultsInspector)

    # Set the window title
    self.SetTitle("Running inference")

  def start(self):
    """Called for each tier. Sets the title and then calls the base class."""

    #from dbgp.client import brk; brk(port=9011)
    self.title.SetLabel('infer')
    phase = self.experiment.description['infer']
    iterationCount = phase[0].get('iterationCount', None) if len(phase) > 0 else None
    PredictionGUI.start(self, iterationCount, self.tier)
