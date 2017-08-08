from .Engine cimport Engine
from ...Utility.Vec2D import Vector2D
import numpy as np

cdef class Engine_MagMap(Engine):
	"""Engine for querying an array of magnification map data. Allows for the same interface whether dealing with pre-generated
	data or on-the-fly data."""
	def __init__(self, parameters, magMapParameters, magMapArray):
		Engine.__init__(self,parameters)
		self.magMapParameters = magMapParameters
		self.magMapArray = magMapArray


	def reconfigure(self):
		if self.__internalEngine:
			self.__internalEngine.reconfigure()


	cdef unsigned int query_data_length(self, double x, double y, double radius) nogil:
		with gil:
			if self.__internalEngine:
				return self.__internalEngine.query_data_length(x,y,radius)
			else:
					pixels = self.magMapParameters.angleToPixel(Vector2D(x,y,'rad'))
					ret = self.magMapArray[round(pixels.x),round(pixels.y)]
					return <unsigned int> ret*self.trueLuminosity

	cdef makeLightCurve_helper(self, object mmin, object mmax, int resolution):
		"""Deprecated"""

		if self.__internalEngine:
			return self.__internalEngine.makeLightCurve_helper(mmin,mmax,resolution)
		else:
			pixels = self.makePixelSteps(mmin,mmax)
			retArr = np.ones_like(pixels.shape[0],dtype=np.float64)
			for index in range(len(retArr)):
				value = self.magMapArray[round(pixels[index,0]),round(pixels[index,1])]
				retArr[index] = value
			return retArr

	def makePixelSteps(self,mmin, mmax):
		if not isinstance(mmin,Vector2D):
			mmin = Vector2D(mmin[0],mmin[1])
		if not isinstance(mmax,Vector2D):
			mmax = Vector2D(mmax[0],mmax[1])
		pixelStart = mmin#self.magMapParameters.angleToPixel(mmin)
		pixelEnd = mmax#self.magMapParameters.angleToPixel(mmax)
		dx = pixelEnd.x - pixelStart.x
		dy = pixelEnd.y - pixelStart.y
		maxD = max(dx,dy)
		xPixels = np.arange(pixelStart.x,pixelEnd.x,dx/maxD)
		yPixels = np.arange(pixelStart.y,pixelEnd.y,dy/maxD)
		ret = np.ndarray((len(xPixels),2))
		ret[:,0] = xPixels
		ret[:,1] = yPixels
		return ret