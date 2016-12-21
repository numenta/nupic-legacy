# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------
# Author: Surabhi Gupta

from Tkinter import *
import math
from nupic.data.generators import data_generator
from nupic.data.generators import distributions

class DataGeneratorApp(): 


  def __init__(self, master, width=1200, height=500):
    """This class can be used to generate artificial datasets for the purpose of
      testing, debugging and evaluation. Freehand drawing of data patterns is
      supported using a gui in addition to predefined distributions. The gui also
      facilitates selection of the sampling rate using a slider
      """
      
    self.canvas = Canvas(master, bg= 'grey', width=width, height=height)
    self.canvas.grid(row=0, column=0, columnspan=3, rowspan=1)
    
    self.width, self.height = (width, height)
    self.color='midnight blue' 
    self.master=master
    
    self._defineButtons(master)

    self.x, self.y= None, None    #Initializing mouse position
    self.draw=False
    self.numLines, self.records=[], {}
    self.pointer = None
    
    self.dg=data_generator.DataGenerator()
    self.dg.defineField('xPos', dict(dataType='int',minval=0,maxval=self.width,
                                     forced=True))
    self.dg.defineField('yPos', dict(dataType='int',minval=0,maxval=self.height,
                                     forced=True))
    
    #Drawing the vertical grid lines
    for i in range(width/10, width, width/10):
      self.canvas.create_line(i, 0, i, height, fill='alice blue')
    
    #Drawing the x-axis
    self.canvas.create_line(0, height*8.5/9, width, height*8.5/9, fill='alice blue')


  def _drawFreeForm(self, event):
    """ The last and current x,y cursor coordinates are updated. If in drawing
    mode, records are created from the x and y coordinates. 
    """
    self.lastx, self.lasty = self.x, self.y
    self.x, self.y=event.x, event.y
    str = "mouse at x=%d  y=%d" % (self.x, self.y)
    self.master.title(str)
    
    if self.pointer is not None:
      self.canvas.delete(self.pointer)
    
    drawPointer=True
    for x in range(self.x-5, self.x+5):
      if drawPointer:
        if x in self.records:
          self.pointer = self.canvas.create_oval(x-4, self.records[x][1]-4, x+4,\
                            self.records[x][1]+4, width=0, fill=self.color)
          drawPointer=False
    if drawPointer:
      self.pointer = self.canvas.create_oval(self.x-4, self.height*8.5/9-4, self.x+4, \
                                self.height*8.5/9+4, width=0, fill=self.color)


  def _createLine(self, fromX, fromY, toX, toY, width=2):
    line = self.canvas.create_line(fromX, fromY, toX, toY, fill=self.color, width=width)
    self.numLines.append(line)
    
    return line


  def motionCallback(self, event, freeForm=True):
    """ Free form drawing is permitted whenever the mouse is moving."""
    self._drawFreeForm(event)


  def buttonReleaseCallback(self, event):
    if (self.lastx, self.lasty)<>(None, None):
      self._createLine(self.lastx, self.lasty, self.lastx, self.height*8.5/9)
      self._createLine(self.x, self.lasty, self.x, self.y)

  ############################################################################ 
  def mousePressedMotionCallback(self, event):
    self.lastx, self.lasty = self.x, self.y
    self.x, self.y=event.x, event.y
    str = "mouse at x=%d  y=%d" % (self.x, self.y)
    self.master.title(str)
    
    if (self.lastx, self.lasty)<>(None, None):
      line = self._createLine(self.lastx, self.lasty, self.x, self.y)
      self.dg.generateRecord([self.x, self.y])

      self.records[self.x]=[line, self.y]
      
      self._addToLog([self.x, self.y], 'Adding')
      
    for i in range(self.lastx, self.x):
      self.records[i]=['',(self.lasty+self.y)/2]

  ############################################################################ 
  def mousePressCallback(self, event):
    """Callback for mouse press. The cursor y-position is marked with a vertical
    line.
    """
    self.lastx, self.lasty = self.x, self.y
    self.x, self.y=event.x, event.y
          
    if (self.lastx, self.lasty)<>(None, None):
      self._createLine(self.lastx, self.lasty, self.lastx, self.height*8.5/9)
      self._createLine(self.x, self.lasty, self.x, self.y) 


  def refreshCallback(self):
    """Callback for the refresh button. All the currently displayed lines except 
    the x-axis and y-axis are erased and all stored records are removed.
    """
    for i in self.numLines:
        self.canvas.delete(i)
    self.records={}
    self.log.insert('1.0', "Erasing the drawing board\n")
    self.dg.removeAllRecords()  


  def sineWave(self):
    """Callback for drawing square waves"""
    sine = distributions.SineWave(dict(amplitude=0.4, period=self.slider.get()))
    records = sine.getData(1000)
    records = [r+0.5 for r in records]
    self.drawWaveform(records, factor=2)


  def squareWave(self):
    """Callback for drawing square waves"""
    records=[]
    for i in range(0,500,10):
      for i in range(0,15,10):
        for i in range(24):
          waveValue = self.square_function(i, 1)
          records.append(waveValue)
      for i in range(0,15,10):
        for i in range(24):
          waveValue = self.square_function(i, 1)
          if waveValue >= 1:
            waveValue = waveValue*2
            records.append(waveValue)
    records = [r/2.01 for r in records]
    self.drawWaveform(records, factor=1)


  def sinePlusNoise(self):
    """Callback for drawing noisy sine waves"""
    records=[]
    for i in range(15):
      for i in range(1,360,5):
        waveValue = self.sine_function(math.radians(i), 1)
        secondWaveValue = self.sine_function(math.radians(i), 32)/4
        finalValue = waveValue + secondWaveValue
        records.append(finalValue)
        
    records = [r+1.0 for r in records]
    self.drawWaveform(records, factor=5)


  def sawToothWave(self):
    """Callback for drawing sawtooth waves"""
    records=[]
    for i in range(15):
      for i in range(1,360, int(self.slider.get())):
        waveValue = self.sawtooth_function(math.radians(i), 1)
        records.append(waveValue)
    
    records = [r+1.0 for r in records]
    self.drawWaveform(records, factor=5)


  def sineCompositeWave(self):
    """Callback for drawing composite sine waves"""
    records=[]
    for i in range(500):
      for i in range(1,360,10):
        waveValue = self.sine_function(math.radians(i), 1)
        secondWaveValue = self.sine_function(math.radians(i), 32) / 4
        finalValue = waveValue + secondWaveValue
        records.append(finalValue)
    
    records = [r+1.0 for r in records]
    self.drawWaveform(records,factor=2)


  def triangleWave(self):
    """Callback for drawing triangle waves"""
    records=[]
    for i in range(15):
      for i in range(1,360,int(self.slider.get())):
        waveValue = self.triangle_function(math.radians(i), 1)
        records.append(waveValue)
    
    records = [r+1.0 for r in records]
    self.drawWaveform(records,factor=6)


  def adjustValues(self, records):
    """ The data points that constitute a waveform in the range (0, 1) are
    scaled to the height of the window
    """
    for i in xrange(len(records)):
      #records[i]=records[i]*(self.height*(8.4/9)*0.5)
      records[i]=records[i]*(self.height*(8.4/9))
    return records


  def drawWaveform(self, records, factor=5):
    """Refresh and draw a waveform adjusted to the width of the screen and the
    horizontal density of the waveform"""
    
    self.refreshCallback()
    records = self.adjustValues(records)
    factor = self.slider.get()
    
    for i in range(1,len(records)):
      #print (i-1)*factor, records[i-1], i*factor, records[i]
      line = self.canvas.create_line((i-1)*factor, records[i-1]+2, i*factor,\
      records[i]+2, fill=self.color, width=2)
      self.records[i*factor]=[line,records[i]]
      self.numLines.append(line)

  ############################################################################ 
  def _addToLog(self, record, operation):
    """Report creation of new record in the log window."""
    
    self.log.insert('1.0', "%s record  %s \n" %(operation, str(record)))
    self.log.mark_set(INSERT, '0.0')
    self.log.focus()


  def _defineButtons(self, master, height=2):
    """Define the buttons and text box and position them"""
    
    twoSine=Button(master, text="Sine Wave", fg="gray77", bg="chocolate1",\
                   command=self.sineWave)
    noisySine=Button(master, text="Noisy Sine", fg="gray77", bg="chocolate1", command=self.sinePlusNoise)
    save=Button(master, text="Save", fg="gray77", bg="chocolate1", command=self.saveFile)
    refresh=Button(master, text="Clear", fg="gray77", bg="chocolate1", command=self.refreshCallback)
    triangle=Button(master, text="Triangle", fg="gray77", bg="chocolate1", command=self.triangleWave)
    sineComposite=Button(master, text="Sine Composite", fg="gray77", bg="chocolate1", command=self.sineCompositeWave)
    sawTooth=Button(master, text="Saw Tooth", fg="gray77", bg="chocolate1", command=self.sawToothWave)
    square=Button(master, text="Square Wave", fg="gray77", bg="chocolate1", command=self.squareWave)
    self.slider=Scale(master, from_=1, to=12, orient=HORIZONTAL, resolution=0.1, bg='gray77', bd=4)
    
    #Positioning buttons
    refresh.grid(row=2, column=0, rowspan=1, sticky=E+W)
    save.grid(row=3, column=0, rowspan=1, sticky=E+W)
    noisySine.grid(row=4, column=0, rowspan=1, sticky=E+W)
    sineComposite.grid(row=2, column=1, rowspan=1, sticky=E+W)
    triangle.grid(row=3, column=1, rowspan=1, sticky=E+W)
    sawTooth.grid(row=4, column=1, rowspan=1, sticky=E+W)
    square.grid(row=5, column=0, rowspan=1, sticky=E+W)
    twoSine.grid(row=5, column=1, rowspan=1, sticky=E+W)
    self.slider.grid(row=6, column=0, columnspan=2, rowspan=1, sticky=E+W)

    #Text box with scrollbar
    frame = Frame(master, bd=1, relief=SUNKEN)
    frame.grid(row=2, column=2, rowspan=6)
    frame.grid_rowconfigure(0, pad=0, weight=1)
    frame.grid_columnconfigure(0, pad=0,weight=1)
    xscrollbar = Scrollbar(frame, orient=HORIZONTAL)
    xscrollbar.grid(row=1, column=0, sticky=E+W)
    yscrollbar = Scrollbar(frame)
    yscrollbar.grid(row=0, column=1, sticky=N+S)
    self.log=Text(frame, wrap=NONE, bd=0, xscrollcommand=xscrollbar.set, \
              yscrollcommand=yscrollbar.set, bg="Black", fg="gray70", height=15, width=70)
    self.log.grid(row=0, column=0, sticky=N+S, in_=frame)
    
    xscrollbar.config(command=self.log.xview)
    yscrollbar.config(command=self.log.yview)
  
  ############################################################################ 
  def saveFile(self, path='output'):
    """Save the records to a file in numenta format."""
    
    self.dg.saveRecords(path=path)
    self.log.insert('1.0', "Saving %s records to file %s \n" \
                    %(str(len(self.records)), str(path+'.csv')))


  #Note: The following function definitions will be ported to the distributions
  #class in future versions


  def sine_function(self,t, f):
    return math.sin(t*f)


  def triangle_function(self,t,f):
      '''
      T is our timestep
      F changes the speed we get to an inversion point
      '''
      value = t * f
      
      # Reduce our value range to 0 to 1
      remainder = math.fmod(value, 1)
      
      # Mulitply by 4 so we end up with both positive and negative values
      q = remainder * 4
          
      # Don't go over 1, invert if we do
      if q > 1:
        q = 2-q
      
      # Don't go under -1, invert if we do
      if q < -1:
        rv = -2-q
      else:
        rv = q
      
      return rv


  def square_function(self,t,f):
    if(f == 0): return 0
    q = 0.5 - math.fmod(t*f,1)
    return (0,1)[q > 0]


  def sawtooth_function(self,t,f):
    
    # Get our initial y value
    value = t * f
    
    # Make sure our values fall between .5 and 1
    remainder = math.fmod(value + 0.5, 1)
    
    # Make sure our values fall between 1 and 2
    rv = remainder * 2.0
    
    # Make sure our values fall between -1 and 1
    rv = rv - 1.0
    
    return rv
  
############################################################################ 
def callBacks(app):
    app.canvas.bind("<Motion>", app.motionCallback)
    app.canvas.bind("<ButtonPress-1>", app.mousePressCallback)
    app.canvas.bind("<B1-Motion>", app.mousePressedMotionCallback)
    app.canvas.bind("<ButtonRelease-1>", app.buttonReleaseCallback)

root = Tk()
app = DataGeneratorApp(root)
callBacks(app)
root.mainloop()		
