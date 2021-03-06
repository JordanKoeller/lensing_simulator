'''
Created on Jan 7, 2018

@author: jkoeller
'''

import math
from astropy import constants as const
import numpy as np

from .CalculationDelegate import CalculationDelegate
from app.preferences import GlobalPreferences
import os
import tempfile

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
        self._core_count = GlobalPreferences['core_count']
        self.sc = _get_or_create_context()
        
    @property
    def parameters(self):
        return self._parameters

    @property
    def core_count(self):
        return self._core_count
    

    def reconfigure(self,parameters):
        self._parameters = parameters
        self.ray_trace()
    
    def make_mag_map(self,center,dims,resolution):
        resx = resolution.x
        resy = resolution.y
        start = center - dims/2
        x0 = start.to('rad').x
        y0 = start.to('rad').y+dims.to('rad').y
        radius = self.parameters.queryQuasarRadius
        ctx = self.sc.emptyRDD()._jrdd
        retFile = tempfile.NamedTemporaryFile('w+')
        self.sc._jvm.main.Main.setFile(retFile.name)
        self.sc._jvm.main.Main.queryPoints(x0,y0,x0+dims.to('rad').x,y0-dims.to('rad').y,int(resx),int(resy),radius,ctx,False)
        data = retFile.read()
        stringArr = list(map(lambda row: row.split(','), data.split(':')))
        numArr = [list(map(lambda s:float(s),row)) for row in stringArr]
        npArr = np.array(numArr,dtype = float)
        return npArr    

    def ray_trace(self):
        if 'datafile' in self.parameters.extras and self.parameters.getExtras('datafile').num_partitions != 0:
            print("Found parameters for a data file. Loading in RDD from disk.")
            file_descriptions = self.parameters.getExtras('datafile')
            num_parts = file_descriptions.num_partitions
            filename = file_descriptions.filename
            ctx = self.sc.emptyRDD()._jrdd
            self.sc._jvm.main.Main.rddFromFile(filename,num_parts,ctx)
            print("Done loading in file")
        else:
            print("Had to start over")
            _width = self.parameters.canvasDim
            _height = self.parameters.canvasDim

            dS = self.parameters.quasar.angDiamDist.to('lyr').value
            dL = self.parameters.galaxy.angDiamDist.to('lyr').value
            dLS = self.parameters.dLS.to('lyr').value
            stars = self.parameters.stars
            starFile = tempfile.NamedTemporaryFile('w+')
            for star in stars:
                strRow = str(star[0]) + "," + str(star[1]) + "," + str(star[2])
                starFile.write(strRow)
                starFile.write("\n")

            args = (starFile.name,
                    (4*(const.G/const.c/const.c).to('lyr/solMass').value*dLS/dS/dL),
                    (4*math.pi*self.parameters.galaxy.velocityDispersion**2*(const.c**-2).to('s2/km2').value*dLS/dS).value,
                    self.parameters.galaxy.shear.magnitude,
                    self.parameters.galaxy.shear.angle.to('rad').value,
                    self.parameters.dTheta.to('rad').value,
                    self.parameters.galaxy.position.to('rad').x,
                    self.parameters.galaxy.position.to('rad').y,
                    int(_width),
                    int(_height),
                    self.sc.emptyRDD()._jrdd,
                    self.core_count
                    )
            self.sc._jvm.main.Main.createRDDGrid(*args)

    def query_single_point(self,parameters,qx,qy,r):
            _width = parameters.canvasDim
            _height = parameters.canvasDim

            dS = parameters.quasar.angDiamDist.to('lyr').value
            dL = parameters.galaxy.angDiamDist.to('lyr').value
            dLS = parameters.dLS.to('lyr').value
            stars = parameters.stars
            starFile = tempfile.NamedTemporaryFile('w+')
            for star in stars:
                strRow = str(star[0]) + "," + str(star[1]) + "," + str(star[2])
                starFile.write(strRow)
                starFile.write("\n")
            # starFile.close()

            args = (starFile.name,
                    (4*(const.G/const.c/const.c).to('lyr/solMass').value*dLS/dS/dL),
                    (4*math.pi*parameters.galaxy.velocityDispersion**2*(const.c**-2).to('s2/km2').value*dLS/dS).value,
                    parameters.galaxy.shear.magnitude,
                    parameters.galaxy.shear.angle.to('rad').value,
                    parameters.dTheta.to('rad').value,
                    parameters.galaxy.position.to('rad').x,
                    parameters.galaxy.position.to('rad').y,
                    int(_width),
                    int(_height),
                    self.sc.emptyRDD()._jrdd,
                    self.core_count,
                    qx,
                    qy,
                    r
                    )
            count = self.sc._jvm.main.Main.query_single_point(*args)
            return int(count)
        
            
    def query_data_length(self,x,y,radius):
        x0 = x
        y0 = y
        retFile = tempfile.NamedTemporaryFile('w+')
        radius = radius or self.parameters.queryQuasarRadius
        ctx = self.sc.emptyRDD()._jrdd
        self.sc._jvm.main.Main.setFile(retFile.name)
        self.sc._jvm.main.Main.queryPoints(x0,y0,x0,y0,1,1,radius,ctx,False)
        ret = None 
        data = retFile.read()
        stringArr = list(map(lambda row: row.split(','), data.split(':')))
        numArr = [list(map(lambda s:float(s),row)) for row in stringArr]
        npArr = np.array(numArr,dtype = float)
        ret =  npArr
        return ret

    def sample_light_curves(self, pts, radius):
        file = tempfile.NamedTemporaryFile('w+')
        retfile = tempfile.NamedTemporaryFile('w+')
        # with open('/tmp/queryPoints','w+') as file:
        for i in range(len(pts)):
            arr = pts[i]
            for iterator in range(len(arr)):
                x = arr[iterator,0]
                y = arr[iterator,1]
                file.write(str(x)+":"+str(y) + ",")
            file.write("\n")
        self.sc._jvm.main.Main.setFile(retfile.name)
        ctx = self.sc.emptyRDD()._jrdd
        self.sc._jvm.main.Main.sampleLightCurves(file.name,radius,ctx)
        ret = []
        # with open('/tmp/lightCurves') as file:
        data = retfile.read()
        stringArr = list(map(lambda row: row.split(','), data.split(':')))
        #String arr is of type [[str]]
        for curveInd in range(len(stringArr)):
            curve = stringArr[curveInd]
            doubles = list(map(lambda x:int(x), curve))
            # startPt = pts[curveInd][0]
            # endPt = pts[curveInd][-1]
            # ends = np.array([list(startPt),list(endPt)])
            doubles = np.array(doubles,dtype=np.int32)
            ret.append(doubles.flatten())
        return ret
            
    def make_light_curve(self,points,resolution):
        raise NotImplementedError

    def generate_light_curve(self,query_points,radius):
        lcFile = tempfile.NamedTemporaryFile('w+')
        ptsFile = tempfile.NamedTemporaryFile('w+')
        self.sc._jvm.main.Main.setFile(lcFile.name)
        for x,y in query_points:
            ptsFile.write(str(x)+","+str(y))
            ptsFile.write("\n")
        ctx = self.sc.emptyRDD()._jrdd
        self.sc._jvm.main.Main.querySingleCurve(ptsFile.name,radius,ctx)
        values = None
        data = lcFile.read()
        values = list(map(lambda row: int(row),data.split('\n')))
        return np.array(values).flatten()


    def save_rays(self,fname):
        self.sc._jvm.main.Main.storeRDDFile(fname)
    
    def get_frame(self,x,y,r):
        raise NotImplementedError
    
    
    
def _get_or_create_context():
    global _sc
    if not _sc:
        from pyspark.conf import SparkConf
        from pyspark.context import SparkContext
        settings = GlobalPreferences['spark_configuration']
        SparkContext.setSystemProperty("spark.executor.memory",settings['executor-memory'])
        SparkContext.setSystemProperty("spark.driver.memory",settings['driver-memory'])
        conf = SparkConf()
        conf = conf.setMaster(settings['master'])
        conf = conf.set('spark.driver.maxResultSize',settings['driver-memory'])
        _sc = SparkContext.getOrCreate(conf=conf)
        _sc.setLogLevel("WARN")
    return _sc
        
