# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'mainwindow.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import uic
import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui
import threading as par
import time
import imageio
import numpy as np
from Drawer import CompositeDrawer
from Drawer import DiagnosticCompositeDrawer


class SimThread(QtCore.QThread):
    """
    For Internal Use only. 

    Class extending a Qt QThread class. Provides methods for interfacing with the physics engine.
    Enables all calculations to be ran on a separate thread so as to not freeze the GUI.


    PARAMETERS
    ----------

    engine : Engine
        Instance that the SimThread controls
    canvas : QLabel or Matplotlib plot
        Canvas owned by the thread. This is the canas that images generated by the engine are drawn to.
        Default Value: None
    canvasType : CanvasType
        Enum specifying if the canvas is a QLabel-based canvas or a Matplotlib-based canvas.
        DefaultValue: CanvasType.NONE_TYPE

    ATTRIBUTES
    ----------

    canvas : The canvas passed in either upon initialization of with the setCanvas method.

    engine : The engine instance passed in upon initialization of the SimThread instance.


    METHODS
    -------

    setCanvas

    """

    def __init__(self,engine,signals):
        QtCore.QThread.__init__(self)
        self.progress_bar_update  = signals[0]
        self.progress_label_update = signals[1]
        self.image_canvas_update = signals[2]
        self.curve_canvas_update = signals[3]
        self.progress_bar_max_update = signals[4]
        self.__calculating = False
        self.__frameRate = 60
        self.engine = engine
        self.__drawer = CompositeDrawer(self.image_canvas_update,self.curve_canvas_update)


    def updateParameters(self,params):
        self.engine.updateParameters(params)

    def run(self):
        self.progress_label_update.emit("Calculating. Please Wait.")
        self.__calculating = True
        counter = 0
        interval = 1/self.__frameRate
        timeE = 1.0
        while self.__calculating:
            timer = time.clock()
            pixels = self.engine.getFrame()
            img = self.__drawer.draw(self.engine.parameters,pixels)
            self.engine.incrementTime(self.engine.parameters.dt)
            deltaT = time.clock() - timer
            counter += 1
            if counter%100 == 0:
                print("Theoretically, frame rate is " + str(60/deltaT))
                # timeE = timeE.clock() - timer 
                # timeE = timeE.clock()
            if deltaT < interval:
                time.sleep(interval-deltaT)

    def pause(self):
        self.__calculating = False

    def restart(self):
        self.__calculating = False
        self.engine.setTime(0)
        pixels = self.engine.getFrame()
        frame = self.__drawer.draw(self.engine.parameters,pixels)
        self.__drawer.resetCurve()
