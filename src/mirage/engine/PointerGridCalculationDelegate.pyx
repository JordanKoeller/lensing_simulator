# cython: boundscheck=False
# cython: cdivision=True
# cython: wraparound=False

from __future__ import division

from .CalculationDelegate cimport CalculationDelegate
from libcpp cimport bool
from mirage.utility.PointerGrid cimport PointerGrid
from libcpp.pair cimport pair
from libcpp.vector cimport vector
import numpy as np 
cimport numpy as np

from libc cimport math as CMATH

from mirage.preferences import GlobalPreferences
from mirage.utility import zeroVector, Vector2D

import ctypes
import os
import random
import time
import math

from astropy import constants as const
from astropy import units as u
from astropy.cosmology import WMAP5 as cosmo
import cython
from cython.parallel import prange

from libc.math cimport sin, cos, atan2, sqrt, atan, atanh, sqrt

cdef class PointerGridCalculationDelegate(CalculationDelegate):

    def __init__(self):
        CalculationDelegate.__init__(self)
        self._parameters = None
        self.__preCalculating = False
        self.core_count = GlobalPreferences['core_count']

    cpdef void reconfigure(self, object parameters):
        self._parameters = parameters
        self.__grid = PointerGrid()
        begin = time.clock()
        self.__preCalculating = True
        finalData = self.ray_trace()
        self.build_data(finalData[0], finalData[1], int(4 * finalData[0].shape[0] ** 2))
        del(finalData)
        self.__preCalculating = False
        print("Time calculating = " + str(time.clock() - begin) + " seconds.")
            
    cpdef object make_light_curve(self, object mmin, object mmax, int resolution):
        while self.__preCalculating:
            time.sleep(0.1)
        mmax = mmax.to('rad')
        mmin = mmin.to('rad')
        cdef double stepX = (mmax.x - mmin.x) / resolution
        cdef double stepY = (mmax.y - mmin.y) / resolution
        cdef np.ndarray[np.float64_t, ndim = 1] yAxis = np.ones(resolution)
        cdef int i = 0
        cdef double radius = self._parameters.quasar.radius.to('rad').value
        cdef double x = mmin.x
        cdef double y = mmin.y
        cdef bool hasVel = False  # Will change later
        with nogil:
            for i in range(0, resolution):
                x += stepX
                y += stepY
                aptLuminosity = self.__grid.find_within_count(x, y, radius)  # Incorrect interface
                yAxis[i] = (< double > aptLuminosity)
        return yAxis  
    
    cpdef object make_mag_map(self, object center, object dims, object resolution):
        cdef int resx = < int > resolution.x
        cdef int resy = < int > resolution.y
        cdef np.ndarray[np.float64_t, ndim = 2] retArr = np.ndarray((resx, resy), dtype=np.float64)
        cdef double stepX = dims.to('rad').x / resolution.x
        cdef double stepY = dims.to('rad').y / resolution.y
        cdef int i = 0
        cdef int j = 0
        cdef double x = 0
        cdef double y = 0
        start = center - dims / 2
        cdef double x0 = center.to('rad').x
        cdef double y0 = center.to('rad').y
        cdef double radius = self._parameters.quasar.radius.to('rad').value
        cdef double roverX, roverY
        cdef double eex, eey
        cdef double angle = 11*math.pi/6
        cdef double cosShear = cos(angle)
        cdef double sinShear = sin(angle)
        for i in prange(-resx/2, resx/2, nogil=True, schedule='guided', num_threads=self.core_count):
            for j in range(-resy/2, resy/2):
                eex = i * stepX
                eey = j * stepY
                roverX = x0 + (eex*cosShear - eey*sinShear)
                roverY = y0 - (eex*sinShear + eey*cosShear)
                retArr[i+resx/2, j+resy/2] = (< double > self.__grid.find_within_count(roverX, roverY, radius))
        return retArr
    
    cpdef object sample_light_curves(self, object pts, double radius): #OPtimizations are definitely possible by cythonizing more, especially the last for loop.
        cdef int i = 0
        cdef int j = 0
        cdef int counts = 0
        cdef double x, y
        lengths = []
        for i in range(len(pts)):
            lengths.append(pts[i].shape[0])
        cdef int max_length = 0
        max_length = max(lengths)
        cdef np.ndarray[np.float64_t,ndim=3] queries = np.zeros((len(pts),max_length,2),dtype=np.float64) #added
        cdef np.ndarray[np.int32_t,ndim=2] ret_pts = np.zeros((len(pts),max_length),dtype=np.int32) #added
        queries = queries - 1.0
        for i in range(0,len(pts)):
            for j in range(0,len(pts[i])):
                queries[i,j] = pts[i][j]
        cdef np.ndarray[np.int32_t, ndim = 1] curve_lengths = < np.ndarray[np.int32_t, ndim = 1] > np.array(lengths,dtype=np.int32)
        cdef int end = len(pts)
        # Now need to actually query them
        for i in prange(0, end, nogil=True, schedule='guided', num_threads=self.core_count):
            for j in range(0, curve_lengths[i]):
                x = queries[i,j,0]
                y = queries[i,j,1]
                counts = self.__grid.find_within_count(x, y, radius)
                ret_pts[i,j] = counts
        retLines = []
        # queryEnds = []
        for i in range(0, len(pts)):
            lineCounts = np.ndarray(curve_lengths[i],dtype=np.int32)
            # queriedPts = pts[i]
            # startLine = queriedPts[0]
            # last = queriedPts.shape[0]
            # endLine = queriedPts[last-1]
            # q = np.array([list(startLine),list(endLine)])
            # queryEnds.append(q)
            for j in range(0,curve_lengths[i]):
                lineCounts[j] = ret_pts[i,j]
            retLines.append(lineCounts)
        return retLines
    

    cpdef object get_frame(self, object x, object y, object r):
        """
        Returns a 2D numpy array, containing the coordinates of pixels illuminated by the source specified in the system's parameters.
        """
        # Possible optimization by using vector data rather than copy?
        while self.__preCalculating:
            print("waiting")
            time.sleep(0.1)
        begin = time.clock()
        cdef double qx = 0
        cdef double qy = 0
        cdef double qr = 0
        qx = x
        qy = y
        qr = r or self._parameters.quasar.radius.to('rad').value
        cdef vector[pair[int, int]] ret = self.query_data(qx, qy, qr)
        cdef int retf = ret.size()
        cdef int i = 0
        cdef np.ndarray[np.int32_t, ndim = 2] fret = np.ndarray((ret.size(), 2), dtype=np.int32)
        with nogil:
            for i in range(0, retf):
                fret[i, 0] = < int > ret[i].first
                fret[i, 1] = < int > ret[i].second
#         print(1/(time.clock()-begin))
        return fret
    
    cpdef unsigned int query_data_length(self, object x, object y, object radius):
        cdef double xx = x
        cdef double yy = y
        cdef double r = radius or self._parameters.quasar.radius.to('rad').value
        with nogil:
            return self.__grid.find_within_count(xx, yy, r)

    cdef vector[pair[int, int]] query_data(self, double x, double y, double radius) nogil:
        """Returns all rays that intersect the source plane within a specified radius of a location on the source plane."""
        cdef vector[pair[int, int]] ret = self.__grid.find_within(x, y, radius)
        return ret
        

    cdef build_data(self, np.ndarray[np.float64_t, ndim=2] xArray, np.ndarray[np.float64_t, ndim=2] yArray, int binsize):
        """Builds the spatial data structure, based on the passed in numpy arrays representing the x and y values of each
            pixel where it intersects the source plane after lensing effects have been accounted for."""
        cdef int w = xArray.shape[0]
        cdef int h = xArray.shape[1]
        cdef int nd = 2
        cdef double * x = < double *> xArray.data 
        cdef double * y = < double *> yArray.data
        with nogil:
            self.__grid = PointerGrid(x, y, h, w, nd, binsize)

    cpdef int query_single_point(self,object parameters, double qx, double qy, double r):
        cdef np.ndarray[np.float64_t,ndim=2] xValues
        cdef np.ndarray[np.float64_t,ndim=2] yValues
        xValues, yValues = self.ray_trace_helper(parameters)
        cdef int i,j, max_x, max_y, count
        cdef double dx, dy, r2
        r2 = r*r
        max_x = xValues.shape[0]
        max_y = xValues.shape[1]
        count = 0
        with nogil:
            for i in range(0,max_x):
                for j in range(0, max_y):
                    dx = qx - xValues[i,j]
                    dy = qy - yValues[i,j]
                    if dx*dx+dy*dy < r2:
                        count += 1
        return count


    cdef ray_trace_helper(self,object parameters):
        begin = time.clock()
        rayfield = parameters.rayfield
        cdef int height = rayfield.resolution.x
        cdef int width = rayfield.resolution.y
        height = height // 2
        width = width // 2
        cdef double dTheta_x = rayfield.dTheta.to('rad').x
        cdef double dTheta_y = rayfield.dTheta.to('rad').y
        cdef np.ndarray[np.float64_t, ndim = 2] result_nparray_x = np.zeros((width * 2, height * 2), dtype=np.float64)
        cdef np.ndarray[np.float64_t, ndim = 2] result_nparray_y = np.zeros((width * 2, height * 2), dtype=np.float64)
        cdef double dS = parameters.quasar.angDiamDist.to('lyr').value
        cdef double dL = parameters.galaxy.angDiamDist.to('lyr').value
        cdef double dLS = parameters.dLS.to('lyr').value
        cdef np.ndarray[np.float64_t, ndim = 1] stars_mass, stars_x, stars_y
        cdef int numStars = 0
        if parameters.galaxy.percent_stars > 0.0:
            stars = parameters.galaxy.stars
            stars_mass = stars[:,0]
            stars_x = stars[:,1]
            stars_y = stars[:,2]
            numStars = len(stars_x)
        cdef double shearMag = parameters.galaxy.shear.magnitude
        cdef double shearAngle = parameters.galaxy.shear.angle.value
        cdef double sis_constant = parameters.einstein_radius.to('rad').value
        cdef double point_constant = (4 * const.G / const.c / const.c).to("lyr/solMass").value * dLS / dS / dL
        cdef double pi2 = math.pi / 2
        cdef int x, y, i
        cdef double incident_angle_x, incident_angle_y, r, deltaR_x, deltaR_y, phi
        cdef double q = parameters.galaxy.ellipticity.magnitude
        cdef double tq = parameters.galaxy.ellipticity.angle.to('rad').value
        cdef double q1 = sqrt(1-q**2), ex, ey
        cdef double eex, eey
        cdef double angle = 0.0#-11*math.pi/6
        # sv = parameters.shear_vector(Vector2D(0,0,'rad'))
        # con = parameters.convergence(Vector2D(0,0,'rad'))
        # print("Shear : " + str(sv))
        # print("ShearAngle : " + str(sv.angle))
        # sm = sv.magnitude()
        # self._angle = math.atan(1/(1-con-sm))
        # print("Calc angle" + str(self._angle))
        # sv = self._parameters.shear_vector(Vector2D(0,0,'rad')).angle
        cdef double cosShear = cos(-angle)
        cdef double sinShear = sin(-angle)
        for x in prange(0, width * 2, 1, nogil=True, schedule='static', num_threads=self.core_count):
            for y in range(0, height * 2):
                eex = (x-width)*dTheta_x
                eey = (height - y)*dTheta_y
                incident_angle_x = eex*cosShear - eey*sinShear
                incident_angle_y = eex*sinShear + eey * cosShear

                for i in range(numStars):
                    deltaR_x = incident_angle_x - stars_x[i]
                    deltaR_y = incident_angle_y - stars_y[i]
                    r = deltaR_x * deltaR_x + deltaR_y * deltaR_y
                    if r != 0.0:
                        result_nparray_x[x, y] += deltaR_x * stars_mass[i] * point_constant / r;
                        result_nparray_y[x, y] += deltaR_y * stars_mass[i] * point_constant / r;                
#                 
                # SIS
                deltaR_x = incident_angle_x
                deltaR_y = incident_angle_y
                r = sqrt(deltaR_x * deltaR_x + deltaR_y * deltaR_y)
                if r != 0.0:
                    if q == 1.0:
                        result_nparray_x[x, y] += deltaR_x * sis_constant / r 
                        result_nparray_y[x, y] += deltaR_y * sis_constant / r
                    else:
                        eex = (deltaR_x*sin(tq)+deltaR_y*cos(tq))
                        eey = (deltaR_y*sin(tq)-deltaR_x*cos(tq))
                        ex = q*sis_constant/q1*atan(q1*eex/sqrt(q*q*eex*eex+eey*eey))
                        ey = q*sis_constant/q1*atanh(q1*eey/sqrt(q*q*eex*eex+eey*eey))
                        result_nparray_x[x,y] += ex*sin(tq) - ey*cos(tq)
                        result_nparray_y[x,y] += ex*cos(tq) + ey*sin(tq)

                # Shear
                phi = 2 * (pi2 - shearAngle) - CMATH.atan2(deltaR_y, deltaR_x)
                # ex = shearMag * r * CMATH.cos(phi)
                # ex = shearMag * r * CMATH.sin(phi)
                result_nparray_x[x, y] += shearMag * r * CMATH.cos(phi)
                result_nparray_y[x, y] += shearMag * r * CMATH.sin(phi)
                result_nparray_x[x, y] = deltaR_x - result_nparray_x[x, y]
                result_nparray_y[x, y] = deltaR_y - result_nparray_y[x, y]
                
        return (result_nparray_x, result_nparray_y)        
    

    cdef ray_trace(self):
        '''Ray-traces the system on the CPU. Does not require openCL
        
        Must call reconfigure() before this method.
        '''
        return self.ray_trace_helper(self._parameters)