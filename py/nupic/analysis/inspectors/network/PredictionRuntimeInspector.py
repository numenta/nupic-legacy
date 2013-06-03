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

#from RuntimeInspectorBase import *

import os
import traceback

import wx
from enthought.traits.api import *
from enthought.traits.ui.api import *
from enthought.traits.ui.menu import OKCancelButtons
from enthought.pyface.api import ImageResource

from nupic.analysis.inspectors.network import NetworkInspector
from nupic.ui.enthought import (alignLeft,
                                alignCenter,
                                alignRight,
                                ProgressEditor,
                                WrappedTextEditor)
from nupic.support.resources import getNTAImage

from nupic.support import title
from nupic.analysis import runtimelistener

def _isSensor(element):
    return len(element.spec.inputs) == 0

def _isEffector(element):
  return element.type == 'VectorFileEffector'

def _getElements(net):
  return net.regions.values()

def _getElement(net, name):
  return net.regions[name]

def _hasElement(net, name):
  return name in net.regions

def _getSelf(region):
  return region.getSelf()

def _disable(net, name):
  _getElement(net, name).disable()

#class PredictionRuntimeInspector(RuntimeInspectorBase):
class PredictionRuntimeInspector(NetworkInspector):
  """The Runtime inspector for the vision framework

  Derives most of its functionality from RuntimeInspectorBase
  """
  # Parameters
  runInterval = 50  # Milliseconds between run calls

  # Displayed traits
  progress = Tuple((0, 0))  # Current and maximum iteration
  speed = Int(1)  # Update every 1, 10, or 100 iterations
  pauseAtNextStep = Bool(True, label='Pause at next step')
  repeatButton = Button("Repeat")
  # The "Next Error" button becomes "Next Target" when user sets a custom one
  nextTargetButton = Event  # Button with dynamic label
  targetButtonLabels = ('Next error', 'Next target')
  targetButtonLabel = Str(targetButtonLabels[0])
  customTargetButton = Button('Custom...')
  pauseTarget = Str
  backwardButton = Button('Back',
                          image=ImageResource(getNTAImage('backward_36_26')))
  runButton      = Button('Run',
                          image=ImageResource(getNTAImage('play_36_26')))
  pauseButton    = Button('Pause',
                          image=ImageResource(getNTAImage('pause_36_26')))
  stepButton     = Button('Step',
                          image=ImageResource(getNTAImage('forward_36_26')))

  # Internal traits
  tier = Int
  tierCount = Int
  running = Bool
  iteration = Int
  numIterations = Int
  mainloopRunning = Bool
  spacer = Str
  pause = Bool
  done = Bool

  @staticmethod
  def getNames():
    """
    Return the short and long names for this inspector. The short name appears
    in the dropdown menu, and the long name is used as the window title.
    """

    return ('run', 'Run Network')

  def __init__(self, parent, experiment, tierCount=0, showProgressBar=False,
               multipleDatasets=False, startImmediately=True):
    """
    """
    #title()
    self.experiment = experiment
    self.pause = True
    self.experiment.pause = True
    self.runCount = None

    network = experiment.network

    NetworkInspector.__init__(self, parent, network)

    self.tierCount = tierCount
    self.showProgressBar = showProgressBar
    self.multipleDatasets = multipleDatasets

    self.stopTarget = None
    self.iteration = 0
    self.iterationCount = 0
    self.usingPauseTarget = False
    self.stepping = False

    # Look for all sensors (regions without inputs)
    # If all sensors are of a supported type, seeking backward is supported
    # Otherwise, seeking backward is not supported, because not all sensors
    # can be run in reverse
    self.sensors = []
    for element in _getElements(self.network):
      if _isSensor(element):
        if element.type == 'VectorFileSensor':
          self.sensors.append(element)
        else:
          # Unsupported sensor type
          self.sensors = []
          break

    # Set the stop button label differently for training and testing
    # The stop button isn't shown at all if neither training nor testing, so
    # don't worry about that case
    if not self.tierCount and self.multipleDatasets:
      self.add_trait('stopButton', Button(label='Skip to next dataset'))
    else:
      self.add_trait('stopButton', Button(label='Stop training this tier'))


    # Set up the default pause target (next error), which the user will be
    # able to change later
    #self._createDefaultPauseTarget()
    #self.pauseTarget = self.defaultPauseTarget

    # Set up the Traits view
    self._createView()

    if startImmediately:
      self.start()  # Start running the network

    #RuntimeInspectorBase.__init__(self, parent, network, tierCount, showProgressBar,
    #                              multipleDatasets, startImmediately)

  def _registerCallbacks(self):
    d = self.experiment.description
    for name in 'spTrain', 'tpTrain', 'classifierTrain', 'infer':
      if not name in d:
        continue
      phase = d[name]
      if len(phase) > 0:
        assert self.onPhaseSetup not in phase[0]['setup']
        phase[0]['setup'].append(self.onPhaseSetup)
        phase[-1]['finish'].append(self.onPhaseTeardown)
        for step in phase:
          # Make sure to be the first callback
          step['iter'].insert(0, self.onIter)


  def _unregisterCallbacks(self):
    d = self.experiment.description
    for name in 'spTrain', 'tpTrain', 'classifierTrain', 'infer':
      if not name in d:
        continue
      phase = d[name]
      if len(phase) > 0:
        assert self.onPhaseSetup in phase[0]['setup']
        phase[0]['setup'].remove(self.onPhaseSetup)
        phase[-1]['finish'].remove(self.onPhaseTeardown)
        for step in phase:
          # Make sure to be the first callback
          step['iter'].remove(self.onIter)


  def _getTierName(self, tier):
    raise NotImplementedError

  def detectNetworkType(self):
    self.isFrameworkNetwork = 'sensor' in self.network.regions and \
      self.network.regions['sensor'].type == 'RecordSensor'

  def _getPhase(self, e):
    index = e.position.phase
    name = e.workflow[index][0]
    return (name, e.description[name])

  def onPhaseSetup(self, exp):
    title()
    self.iteration = 0
    self.phase = self._getPhase(exp)
    phase = self.phase[1]
    self.iterationCount = phase[0]['iterationCount'] if len(phase) > 0 else 0

    if self.pauseAtNextStep and self.pauseAtPhaseSetup:
    #if self.pauseAtNextStep:
      #from dbgp.client import brk; brk(port=9011)
      exp.pause = True
      self.pause = True
      self.pauseAtPhaseSetup = False
    else:
      self.pauseAtPhaseSetup = True


  def onPhaseTeardown(self, exp):
    title()

    index = exp.position.phase
    # Last phase
    if index == len(exp.workflow) - 1:
      self.done = True


  def onIter(self, exp, i):
    """ """
    title(additional='(), self.pause = ' + str(self.pause))
    self.iteration += 1

    # check if the pause button was clicked
    if self.pause:
      exp.pause = True
    elif self.runCount is not None:
      self.runCount -= 1
      if self.runCount == 0:
        exp.pause = True

    runtimelistener.listenersEnabled = exp.pause

  def _setProgress(self):
    """Set the progress trait from the iteration."""

    self.progress = (self.iteration, self.iterationCount)

  def _disableRegions(self):
    """
    Disable any regions that can't be run.

    Currently only looks for VectorFileEffectors whose outputFile parameter
    is equal to 'No output file specified'.
    """

    effectors = [e for e in _getElements(self.network) if _isEffector(e)]

    for e in effectors:
      if e.getParameter('outputFile') == 'No outputFile specified':
        _disable(self.network, e.getName())

  def _createView(self):
    """Set up a view for the traits."""

    items = []

    if self.showProgressBar:
      items.append(Item('progress', show_label=False,
                        editor=ProgressEditor(callback=self._seek)))

    # Controls
    items.append(
      alignCenter(
        Item('backwardButton', style='custom',
          enabled_when='not object.running and object.mainloopRunning '
                      +'and object.sensors and object.iteration > 1'),
        Item('runButton', style='custom',
          enabled_when='object.pause and not object.done'),
        Item('pauseButton', style='custom',
          enabled_when='not (object.pause or object.done)'),
        Item('stepButton', style='custom',
          enabled_when='object.pause and not object.done'),
        show_labels=False,
        orientation='horizontal'
      ))

    # Repeat button and pause target buttons
    items.append(
      alignCenter(
        Item('repeatButton', show_label=False,
             enabled_when='not object.running and object.mainloopRunning '
                          'and object.iteration > 0'),
        Item('nextTargetButton', show_label=False,
             editor=ButtonEditor(label_value='targetButtonLabel'),
             enabled_when='not object.running and object.mainloopRunning '
                          'and object.pauseTarget'),
        Item('customTargetButton', show_label=False,
              enabled_when='not object.running and object.mainloopRunning')
      ))

    # Speed control
    items.append(Item('speed', style='custom', show_label=False,
                      editor=EnumEditor(cols=1, values={
                        1   : '1: Slow (update on every iteration)',
                        10  : '2: Medium (update every 10 iterations)',
                        100 : '3: Fast (update every 100 iterations)'
                      })
                 ))


    items.extend([
      Group(
        Item('pauseAtNextStep'),
        show_left=False
      ),
      alignLeft(
        Item('stopButton', show_label=False, enabled_when='object.iteration')
      )
    ])

    self.traits_view = View(*items)


  def close(self):
    """Called by MultiInspector upon closing."""
    #title()
    self.experiment.pause = True
    if self.running:
      self.running = False

    self._unregisterCallbacks()

  def start(self, numIterations=0, target=None, tier=0, stop=False,
            callback=None):
    """
    Start running the network, and start the mainloop if necessary.

    numIterations -- Number of iterations to run for (optional).
    target -- Run until this condition is met (used by the Vision Framework).
      This is distinct from the user-specified target in the GUI, which simply
      tells the network when to pause.
    tier -- Tier being trained. Used to check the target on it.
    stop -- Whether to stop immediately (used when training a tier for 0
      iterations).
    callback -- Called right after initialization (optional).
    """
    #title()
    self._registerCallbacks()
    self.iterationCount = numIterations
    self.iteration = 0
    self.stopTarget = target
    self.tier = tier
    self.pauseAtPhaseSetup = False

    if callback:
      callback()

    self._disableRegions()  # Disable regions which can't be run (e.g. effectors)

    # Re-enable this window (use this hack to get a reference to it), because
    # it may have been disabled at the end of the previous tier/dataset when
    # running from the Vision Framework
    wx.GetApp().GetTopWindow().Enable()
    # Insert a call into the event loop to run (or stop)
    #if stop:  # Immediately stop - used by training GUI with 0 iterations
    #  wx.CallLater(self.runInterval, self.stop)
    #elif self.running:
    #  wx.CallLater(self.runInterval, self._run)
    self.mainloopRunning = True
    if not wx.GetApp().IsMainLoopRunning():
      wx.GetApp().MainLoop()

    self.close()

  def stop(self):
    """Stop running."""
    # Stop the experiment
    self.experiment.pause = True

    # Any extra calls to _run that are in the event loop should return
    self.stopping = True

    #if self.pauseAtNextTier and self.pauseAtNextDataset:
    if self.pauseAtNextStep:
      # Pausing, so set running to False -- otherwise we will continue running
      # again
      self.running = False

    # Disable the window to prevent user input until start is called again
    # E.g. control will go back to the Vision Framework
    wx.GetApp().GetTopWindow().Disable()
    self.mainloopRunning = False
    wx.GetApp().ExitMainLoop()

  def _seek(self, iteration):
    """Seek to the specified iteration."""

    # Validate it
    if iteration < 1:
      iteration = 1

    # Seek to one iteration before the specified iteration, then run the
    # network for one iteration, so the inspectors will show the right data
    self.iteration = iteration - 1
    self.experiment.position.iter = iteration - 1
    for sensor in self.sensors:
      assert sensor.type == 'VectorFileSensor'
      sensor.setParameter('position', self.iteration)
    self._step()

  def _pause(self):
    #title(additional='(), self.pause = ' + str(self.pause))
    self.pause = True

  def _runExperiment(self):
    #title(additional='(), self.pause = ' + str(self.pause))
    self.experiment.run()
    return self.experiment.done

  def _run(self):
    """Run the experiment."""
    #title(additional='(), self.pause = ' + str(self.pause))
    #if self.experiment.done or self.pause:
    #  return

    # self.speed can be either 1, 10, or 100
    if not self.iterationCount:
      iterations = self.speed
    else:
      iterations = \
        min(self.speed - self.iteration % self.speed, self.iterationCount - self.iteration)

    self.runCount = iterations
    self.experiment.pause = False
    self.done = self._runExperiment()
    # If the experiment is done or paused or stepping
    if self.done or self.pause:
      return

    # Schedule another run
    wx.CallLater(self.runInterval, self._run)

  def update(self, methodName=None, elementName=None, args=None, kwargs=None):
    """
    Called automatically in response to runtime engine activity.

    Extra arguments (optional) are passed by the wrapped methods,
    and they can be used to avoid unnecessary updating.

    @param methodName -- RuntimeElement class method that was called.
    @param elementName -- RuntimeElement name.
    @param args -- Positional arguments passed to the method.
    @param kwargs -- Keyword arguments passed to the method.
    """
    #if methodName != 'run':
    #  return
    ##print methodName
    ##from dbgp.client import brk; brk(port=9011)
    #self.iteration = self.experiment.position.iter
    #exp = self.experiment
    ## check if the pause button was clicked
    #if self.pause:
    #  exp.pause = True
    #elif self.runCount is not None:
    #  self.runCount -= 1
    #  if self.runCount == 0:
    #    exp.pause = True
    #
    #runtimelistener.listenersEnabled = exp.pause

  def _step(self):
    """Run the network for one iteration."""
    title()
    self.runCount = 1
    self.experiment.pause = False
    self._runExperiment()
    self.pause = True

  def _iteration_changed(self):
    """
    Called automatically by Traits when the iteration updates.

    Update the progress bar and check the conditions to see whether to stop or
    pause.
    """
    if self.showProgressBar:
      try:
        self._setProgress()
      except:
        # may fail when switching from training to inference
        from dbgp.client import brk; brk(port=9011)
        pass


  def _runButton_fired(self):
    self.pause = False
    wx.CallLater(self.runInterval, self._run)

  def _pauseButton_fired(self):
    #from dbgp.client import brk; brk(port=9011)
    self.pause = True
    #wx.CallLater(self.runInterval, self._pause)

  def _stepButton_fired(self):
    wx.CallLater(self.runInterval, self._step)

  def _stopButton_fired(self):
    #self.stopping = True
    wx.CallLater(self.runInterval, self.stop)