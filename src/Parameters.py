from __future__ import division
from Utility import Vector2D
from Utility import zeroVector
from Stellar import Galaxy
from Stellar import Quasar
from Stellar import defaultQuasar
from Stellar import defaultGalaxy
from Calculator import Kroupa_2001
from astropy.cosmology import WMAP7 as cosmo
from astropy import constants as const
from astropy import units as u 
import math

class Parameters(object):
	"""Stores and processes all the information regarding the setup for a 
	gravitationally lensed system, along with how to display/calculate 
	the images.

	ALL POSSIBLE PARAMETERS:

	General:
		(control variable) is microlensing
		(control variable) auto configure
		dTheta [auto configure]
		canvasdim 
		showGalaxy [is microlensing, dtheta]
		showQuasar [is microlensing, dtheta]

	Galaxy:
		redshift
		velocityDispersion
		shear angle
		shear magnitude
		percent stars
		number of stars [dtheta, percent stars] ***
		star mass function
		star mass postprocessing info
		star mass function resolution
		center position [is microlensing]

	Quasar:
		redshift
		radius
		center position
		velocity
		base position"""
		
	def __init__(self, galaxy = defaultGalaxy, quasar = defaultQuasar, dTheta = 600/800, canvasDim = 800, showGalaxy = True, showQuasar = True, starMassTolerance = 0.05, starMassVariation = None,numStars = 0, curveDim = Vector2D(800,200), center = zeroVector):
		self.__center = center
		self.__galaxy = galaxy
		self.__quasar = quasar
		self.__dTheta = u.Quantity(dTheta/canvasDim,'rad')
		self.__canvasDim = canvasDim
		self.__curveDim = curveDim
		self.showGalaxy = showGalaxy
		self.showQuasar = showQuasar
		self.numStars = numStars
		self.__starMassTolerance = starMassTolerance
		self.__starMassVariation = starMassVariation
		self.dt = 0.1
		self.time = 0


	def generateStars(self):
		m_stars = self.__galaxy.percentStars*self.smoothMassOnScreen
		generator = Kroupa_2001()
		print("Starting generator with mass of "+str(m_stars))
		starMasses = generator.generate_cluster(m_stars)[0]
		print("Done.")
		self.__galaxy.setStarMasses(starMasses,self)

	@property
	def galaxy(self):
		return self.__galaxy
	@property
	def quasar(self):
		return self.__quasar
	@property
	def dTheta(self):
		return self.__dTheta
	@property
	def canvasDim(self):
		return self.__canvasDim
	@property
	def isMicrolensing(self):
		return self.__isMicrolensing
	@property
	def starMassFunction(self):
		return self.__starMassFunction
	@property
	def starMassVariation(self):
		return self.__starMassVariation

	@property
	def einsteinRadius(self):
		return 4 * math.pi * self.__galaxy.velocityDispersion * self.__galaxy.velocityDispersion * self.__dLS/self.quasar.angDiamDist /const.c**2

	@property
	def displayQuasar(self):
		return self.showQuasar

	@property
	def displayGalaxy(self):
		return self.showGalaxy

	@property
	def displayStars(self):
		return self.showGalaxy
	@property
	def stars(self):
		return self.galaxy._Galaxy__stars

	@property
	def dLS(self):
		return cosmo.angular_diameter_distance_z1z2(self.__galaxy.redshift,self.__quasar.redshift).to('lyr')

	@property
	def smoothMassOnScreen(self):
		l = (self.dTheta*self.canvasDim*self.__galaxy.angDiamDist.to('m')).value
		r_in = self.center.magnitude()*self.__galaxy.angDiamDist.to('m').value
		print(l)
		ret = (l * self.__galaxy.velocityDispersion**2 * math.log(r_in/l)/2/const.G.to('m3 / (solMass s2)')).value
		return ret

	@property
	def correctedVelocityDispersion(self):
		return math.sqrt(1-self.__galaxy.percentStars)*self.__galaxy.velocityDispersion

	def setStars(self,stars):
		self.__galaxy.update(stars = stars)

	def setTime(self,time):
		self.time = time
		self.__quasar.setTime(time)

	def getStarMasses(self,mass,tolerance = 0.05):
		ret = defaultMassGenerator.starField(mass,tolerance)
		return ret
	
	@property
	def queryQuasarX(self):
		return self.quasar.position.to('rad').x + self.__center.to('rad').x

	@property
	def queryQuasarY(self):
		return self.quasar.position.to('rad').y + self.__center.to('rad').y

	@property
	def centerX(self):
		return self.__center.to('rad').x

	@property
	def centerY(self):
		return self.__center.to('rad').y

	@property
	def center(self):
		return self.__center.to('rad')
				
	@property
	def queryQuasarRadius(self):
		return self.quasar.radius.value



	def isSimilar(self,other):
		if self.dTheta != other.dTheta:
			return False
		if self.canvasDim != other.canvasDim:
			return False
		if self.center != other.center:
			return False
		if self.starMassVariation != other.starMassVariation:
			return False
		if self.galaxy != other.galaxy:
			return False
		if self.quasar.redshift != other.quasar.redshift:
			return False
		return True

	def __eq__(self,other):
		if not self.isSimilar(other):
			return False
		if self.quasar != other.quasar:
			return False
		if self.showQuasar != other.showQuasar:
			return False
		if self.showGalaxy != other.showGalaxy:
			return False
		return True

	def __str__(self):
		return ("dTheta = " + str(self.dTheta)) + ("\ncanvasDim = " + str(self.canvasDim)) + "\n" + str(self.quasar) + str (self.galaxy) + ("\ndLS = "+ str(self.dLS)) + ("Einstein Radius = " + str(self.einsteinRadius))
