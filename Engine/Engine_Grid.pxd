from __future__ import division
import numpy as np
cimport numpy as np
from libcpp.vector cimport vector
from libcpp cimport bool
import cython
import ctypes
from libcpp.pair cimport pair
from Utility.Grid cimport Grid
from Utility.Grid cimport Pixel
from Engine cimport Engine


cdef class Engine_Grid(Engine):
	cdef Grid __grid

	cdef build_data(self, np.ndarray[np.float64_t, ndim=2] xArray, np.ndarray[np.float64_t, ndim=2] yArray)
	cdef vector[Pixel] query_data(self, double x, double y, double radius)
	cpdef getFrame(self)