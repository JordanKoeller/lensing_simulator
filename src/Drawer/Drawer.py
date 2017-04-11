import numpy as np
from Graphics import Plot
import pyqtgraph as pg 

class Drawer(object):
	def draw(self, parameters, pixels, canvas=None):
		pass

class ImageDrawer(Drawer):
	"""docstring for ImageDrawer"""
	def __init__(self):
		pass
	def draw(self,parameters,pixels, canvas=None):
		if canvas is None:
			canvas = np.zeros((parameters.canvasDim,parameters.canvasDim), dtype=np.uint8)
		if parameters.displayGalaxy:
			parameters.galaxy.drawGalaxy(canvas,parameters)
		if parameters.displayStars:
			parameters.galaxy.drawStars(canvas,parameters)
		if parameters.displayQuasar:
			parameters.quasar.draw(canvas,parameters)
		for pixel in pixels:
			canvas[pixel[0],pixel[1]] = 1
		return canvas


	def __drawEinsteinRadius(self,canvas,radius,centerx,centery):
		x0 = centerx
		y0 = centery
		x = abs(radius/self.__parameters.dTheta)
		y = 0
		err = 0
		while x >= y:
			if x0 + x > 0 and y0 + y > 0 and x0 + x < self.__parameters.canvasDim and y0 + y < self.__parameters.canvasDim:
					canvas[x0 + x, y0 + y] = 3
			if x0 + y > 0 and y0 + x > 0 and x0 + y < self.__parameters.canvasDim and y0 + x < self.__parameters.canvasDim:
					canvas[x0 + y, y0 + x] = 3
			if x0 - y > 0 and y0 + x > 0 and x0 - y < self.__parameters.canvasDim and y0 + x < self.__parameters.canvasDim:
					canvas[x0 - y, y0 + x] = 3
			if x0 - x > 0 and y0 + y > 0 and x0 - x < self.__parameters.canvasDim and y0 + y < self.__parameters.canvasDim:
					canvas[x0 - x, y0 + y] = 3
			if x0 - x > 0 and y0 - y > 0 and x0 - x < self.__parameters.canvasDim and y0 - y < self.__parameters.canvasDim:
					canvas[x0 - x, y0 - y] = 3
			if x0 - y > 0 and y0 - x > 0 and x0 - y < self.__parameters.canvasDim and y0 - x < self.__parameters.canvasDim:
					canvas[x0 - y, y0 - x] = 3
			if x0 + y > 0 and y0 - x > 0 and x0 + y < self.__parameters.canvasDim and y0 - x < self.__parameters.canvasDim:
					canvas[x0 + y, y0 - x] = 3
			if x0 + x > 0 and y0 - y > 0 and x0 + x < self.__parameters.canvasDim and y0 - y < self.__parameters.canvasDim:
					canvas[x0 + x, y0 - y] = 3
			if err <= 0:
				y += 1
				err += 2*y + 1
			if err > 0:
				x -= 1
				err -= 2*x + 1


class CurveDrawer(object):
	"""docstring for CurveDrawer"""
	def __init__(self, plotWidget):
		super(CurveDrawer, self).__init__()
		self.plotWidget = plotWidget
		self.plotItem = self.plotWidget.getPlotItem()
		self.xAxis = np.arange(0,100)
		self.yAxis = np.zeros_like(self.xAxis)
		self.index = 0

	def append(self,y):
		if self.index < self.xAxis.shape[0]:
			self.yAxis[self.index] = y
			self.index += 1
		else:
			replaceX = np.arange(0,self.xAxis.shape[0]*2)
			replaceY = np.zeros_like(replaceX)
			for x in range(0,self.index):
				replaceY[x] = self.yAxis[x]
			self.yAxis = replaceY
			self.xAxis = replaceX
			self.plotItem.plot(self.xAxis,self.yAxis,clear = True)


		




# class CompositeDrawer(Drawer):
# 	"""For drawing more than one thing"""
# 	def __init__(self, *args):
# 		self.__drawers = args

# 	def draw(self,parameters,pixels, canvas=None):

		
		

	