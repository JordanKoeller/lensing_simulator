'''
Created on Jan 7, 2018

@author: jkoeller
'''

import math
from astropy import constants as const
import numpy as np

from .CalculationDelegate import CalculationDelegate
from memory_profiler import profile


_sc = None

class ScalaSparkCalculationDelegate(CalculationDelegate):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        CalculationDelegate.__init__(self)
        
    @property
    def parameters(self):
        return self._parameters

    def reconfigure(self,parameters):
        self._parameters = parameters
        self.sc = _get_or_create_context(parameters)
        self.ray_trace()
    
    def make_mag_map(self,center,dims,resolution):
        print("Now querying the source plane to calculate the magnification map.")
        resx = resolution.x
        resy = resolution.y
        start = center - dims/2
        x0 = start.to('rad').x
        y0 = start.to('rad').y+dims.to('rad').y
        radius = self.parameters.queryQuasarRadius
        ctx = self.sc.emptyRDD()._jrdd
        self.sc._jvm.main.Main.setFile("/tmp/magData")
        self.sc._jvm.main.Main.queryPoints(x0,y0,x0+dims.to('rad').x,y0+dims.to('rad').y,int(resx),int(resy),radius,ctx,False)
        with open("/tmp/magData") as file:
            data = file.read()
            stringArr = list(map(lambda row: row.split(','), data.split(':')))
            numArr = [list(map(lambda s:float(s),row)) for row in stringArr]
            npArr = np.array(numArr,dtype = float)
            return npArr    

    def ray_trace(self):
        _width = self.parameters.canvasDim
        _height = self.parameters.canvasDim

        dS = self.parameters.quasar.angDiamDist.to('lyr').value
        dL = self.parameters.galaxy.angDiamDist.to('lyr').value
        dLS = self.parameters.dLS.to('lyr').value
        stars = self.parameters.stars
        starFile = open("/tmp/stars",'w+')
        for star in stars:
            strRow = str(star[0]) + "," + str(star[1]) + "," + str(star[2])
            starFile.write(strRow)
            starFile.write("\n")
        starFile.close()
        args = ("/tmp/stars",
                (4*(const.G/const.c/const.c).to('lyr/solMass').value*dLS/dS/dL),
                (4*math.pi*self.parameters.galaxy.velocityDispersion**2*(const.c**-2).to('s2/km2').value*dLS/dS).value,
                self.parameters.galaxy.shear.magnitude,
                self.parameters.galaxy.shear.angle.to('rad').value,
                self.parameters.dTheta.to('rad').value,
                self.parameters.galaxy.position.to('rad').x,
                self.parameters.galaxy.position.to('rad').y,
                _width,
                _height,
                self.sc.emptyRDD()._jrdd
                )
        print("Calling JVM to ray-trace.")
        self.sc._jvm.main.Main.createRDDGrid(*args)
        print("Finished ray-tracing.")
        
            
    def query_data_length(self,x,y,radius):
        print("Now querying the source plane to calculate the magnification map.")
        x0 = x
        y0 = y
        radius = radius or self.parameters.queryQuasarRadius
        ctx = self.sc.emptyRDD()._jrdd
        self.sc._jvm.main.Main.setFile("/tmp/magData")
        self.sc._jvm.main.Main.queryPoints(x0,y0,x0,y0,1,1,radius,ctx,False)
        with open("/tmp/magData") as file:
            data = file.read()
            stringArr = list(map(lambda row: row.split(','), data.split(':')))
            numArr = [list(map(lambda s:float(s),row)) for row in stringArr]
            npArr = np.array(numArr,dtype = float)
            return int(npArr[0,0])   
            
    def make_light_curve(self,mmin,mmax,resolution):
        raise NotImplementedError
    
    def get_frame(self,x,y,r):
        raise NotImplementedError
    
    
    
def _get_or_create_context(p):
    global _sc
    if not _sc:
        from pyspark.conf import SparkConf
        from pyspark.context import SparkContext
        cd = p.canvasDim
        ns = p.galaxy.percentStars
        conf = SparkConf().setAppName(str(cd) + "," + str(ns))
        conf = (conf)
        _sc = SparkContext(conf=conf)
        _sc.setLogLevel("WARN")
    return _sc
        
