'''
Created on Dec 24, 2017

@author: jkoeller
'''
from app.controllers.Controller import Controller
from PyQt5.QtWidgets import QApplication

import numpy as np


class Runner(Controller):

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        Controller.__init__(self, *args, **kwargs)
        self._runningBool = False
        self._initialized = False
        self._spawnedGen = None
        
    def trigger(self, model, masterController):
        if self._runningBool:
            self.halt()
        else:
            if not self._initialized:
                self.initialize(model, masterController)
                self._spawnedGen = self.generator(model, masterController)
            self._runningBool = True
            while self._runningBool:
                try:
                    frame = next(self._spawnedGen)
                    self.broadcast(model, masterController, frame)
                except StopIteration:
                    self._runningBool = False
                    self._initialized = False
                
    def halt(self):
        self._runningBool = False
        
    def reset(self):
        self.halt()
        self._initialized = False
    
    def broadcast(self, model, masterController, frame):
        masterController.parametersController.update(model.parameters)
        masterController.lensedImageController.setLensedImg(model, frame)
        masterController.lightCurveController.add_point_and_plot(frame)
#         masterController.magMapController.update(model.parameters)
        model.parameters.incrementTime(model.parameters.dt)
        QApplication.processEvents()
        
    def initialize(self, model, masterController):
        self._initialized = True
            
    def generator(self, model, masterController):
        pass

    
class AnimationRunner(Runner):
    '''
    Controller for generating animations, like videos.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        Runner.__init__(self, *args, **kwargs)
                        
    def generator(self, model, masterController):
        while True:
            yield model.engine.get_frame()
    
    def initialize(self, model, masterController):
        Runner.initialize(self, model, masterController)
                
    def halt(self):
        self._runningBool = False

    # NEED TO CHANGE THIS TO THE NEW INTERFACE


class FrameRunner(Runner):
    
    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)
        
    def initialize(self, model, masterController):
        Runner.initialize(self, model, masterController)
    
    def generator(self, model, masterController):
        yield model.engine.get_frame()
        raise StopIteration
        
    # THIS ONE TOO

        
class LightCurveRunner(Runner):
    
    def __init__(self, *args, **kwargs):
        Runner.__init__(self, *args, **kwargs)
        self._counter = 0
        self._xStepArr = 0
        self._yStepArr = 0
        self._generator = None
        
    def initialize(self, model, masterController): 
        Runner.initialize(self, model, masterController)
        lcparams = model.parameters.getExtras('lightcurve')
        begin = lcparams.pathStart.to('rad')
        end = lcparams.pathEnd.to('rad')
        resolution = lcparams.resolution
        resolution = 1000
        print("NEED TO REFINE RESOLUTION SETTING IN LIGHTCURVERUNNER")
        dist = begin.distanceTo(end)
        xAxis = np.linspace(0, dist.value, resolution)
        masterController.lightCurveController.reset(xAxis)
        self._xStepArr = np.linspace(begin.x, end.x, resolution)
        self._yStepArr = np.linspace(begin.y, end.y, resolution)
        self._counter = 0
        
    def generator(self, model, masterController):
        while self._counter < len(self._xStepArr):
            x = self._xStepArr[self._counter]
            y = self._yStepArr[self._counter]
            yield model.engine.get_frame(x, y)
            self._counter += 1
        raise StopIteration
    
    def broadcast(self, model, masterController, frame):
        frame = float(frame)
#         masterController.parametersController.update(model.parameters)
#         masterController.lensedImageController.setLensedImg(model,frame)
        masterController.lightCurveController.add_point_and_plot(frame)
#         masterController.magMapController.update(model.parameters)
        model.parameters.incrementTime(model.parameters.dt)
        QApplication.processEvents()
        

    def plotFromLightCurve(self,mastercontroller,lightcurve,x_axis_unit,bounding_box):
        from app.models import LightCurve 
        if isinstance(lightcurve,LightCurve):
            x,y = lightcurve.plottable(x_axis_unit)
            qpts = lightcurve.query_points.to('rad').value
            pixels = bounding_box.angleToPixel(qpts)
            start_trace,end_trace = (pixels[0],pixels[-1])
            mastercontroller.lightCurveController.plot_xy(x,y)
            mastercontroller.magMapController.setROI(start_trace,end_trace)
        else:
            raise ValueError("lightcurve must be an instance of the LightCurve type")
