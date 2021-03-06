# distutils: language=c++
# cython: profile=True
from __future__ import division

import ctypes
import math
import os
import random
import time

from astropy import constants as const
from astropy import units as u
from astropy.cosmology import WMAP7 as cosmo
import cython

from app.utility import Vector2D
from app.utility import zeroVector
import numpy as np
cimport numpy as np
from libcpp.vector cimport vector
from libc.math cimport sin, cos, atan2, sqrt
from libcpp.pair cimport pair
from app.utility.PointerGrid cimport PointerGrid
from .Engine cimport Engine
from libcpp cimport bool
from libc.stdlib cimport malloc, free
cdef class Engine_PointerGrid(Engine):

	"""
	Impliments the Engine class with a grid spatial hashing data structure for fast lensing system calculations, along with fast queries of the system and 
	production of light curves or magnification maps. 
	"""
	def __init__(self, parameter=None):
		Engine.__init__(self,parameter)

	@cython.boundscheck(False)  # turn off bounds-checking for entire function
	@cython.wraparound(False)
	cdef build_data(self, np.ndarray[np.float64_t, ndim=2] xArray, np.ndarray[np.float64_t, ndim=2] yArray,int binsize):
		"""Builds the spatial data structure, based on the passed in numpy arrays representing the x and y values of each
			pixel where it intersects the source plane after lensing effects have been accounted for."""
		cdef int w = xArray.shape[0]
		cdef int h = xArray.shape[1]
		cdef int nd = 2
		cdef double* x = <double*> xArray.data 
		cdef double* y = <double*> yArray.data
		with nogil:
			self.__grid = PointerGrid(x,y,h,w,nd,binsize)

	cdef vector[pair[int,int]] query_data(self, double x, double y, double radius) nogil:
		"""Returns all rays that intersect the source plane within a specified radius of a location on the source plane."""
		cdef vector[pair[int,int]] ret = self.__grid.find_within(x, y, radius)
		return ret
	
	cdef unsigned int query_data_length(self, double x, double y, double radius) nogil:
		return self.__grid.find_within_count(x, y, radius)

	def reconfigure(self):
		self.__grid = PointerGrid()
		begin = time.clock()
		self.__preCalculating = True
		finalData = self.ray_trace(use_GPU=True)
		self.build_data(finalData[0], finalData[1],int(2*finalData[0].shape[0]**2))
		del(finalData)
		self.__preCalculating = False
# 		time.sleep(3)


	@cython.boundscheck(False)  # turn off bounds-checking for entire function
	@cython.wraparound(False)
	cpdef getFrame(self,object x=None,object y=None,object r=None):
		"""
		Returns a 2D numpy array, containing the coordinates of pixels illuminated by the source specified in the system's parameters.
		"""
		#Possible optimization by using vector data rather than copy?
		while self.__preCalculating:
			time.sleep(0.1)
		cdef double qx = 0
		cdef double qy = 0
		cdef double qr = 0
		qx = x or self.__parameters.queryQuasarX
		qy = y or self.__parameters.queryQuasarY
		qr = r or self.__parameters.queryQuasarRadius
		cdef vector[pair[int,int]] ret = self.query_data(qx,qy,qr)
		cdef int retf = ret.size()
		cdef int i = 0
		cdef np.ndarray[np.int32_t, ndim = 2] fret = np.ndarray((ret.size(), 2), dtype=np.int32)
		with nogil:
			for i in range(0, retf):
				fret[i,0] = <int> ret[i].first
				fret[i,1] = <int> ret[i].second
		return fret

