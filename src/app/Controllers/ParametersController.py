'''
Created on May 31, 2017

@author: jkoeller
'''


#Code associated with constructing/deconstructing an instance of a Parameters Class 
import math
import random
import numpy as np 

from PyQt5 import QtCore
from astropy import constants as const
from astropy.coordinates import CartesianRepresentation
from astropy.coordinates import SkyCoord

from app.Models import Model
import astropy.units as u

from ..Calculator import UnitConverter
from ..Parameters.Parameters import Parameters
from ..Parameters.Stellar import Galaxy, Quasar, EarthVelocity
from ..Utility import Vector2D
from ..Views.GUI.HelpDialog import HelpDialog
from .FileManagerImpl import ParametersFileManager
from .GUIController import GUIController
from .UserInputParser import UserInputParser


class ParametersController(UserInputParser,GUIController):
    '''
    extends UserInputParser, GUIController

    ParametersController is a wrapper of a ParametersView, in charge of pulling information from what the user enters into the ParametersView pane, 
    as well as pushing internal Model data to the ParametersView to communicate to the user.

    More specifically, its primary role is to parse user input to construct a Parameters object instance.
    

    ===========================================
    METHODS:

    displayHelpMessage()
        opens a dialog, displaying the docstrings for the Parameters class.

    hide()
        DEPRECATED.

    show()
        DEPRECATED.

    randomizeGVelocity()
        Produces a random 3D velocity vector for a galaxy, projected into two dimensions orthogonal to the line of sight.
        Called internally when constructing a Parameters instance, when a random velocity is requested by the user.



    ===================================

    ATTRIBUTES:

    modelID
        (str) modelID of the model this controller is associated with. 

    ===================================

    SIGNALS:

    paramLabel_signal 
        DEPRECATED

    paramSetter_signal(object)
        signal that when emitted, will bind the Parameters instance included to the wrapped ParametersView

    '''

    paramLabel_signal = QtCore.pyqtSignal(str)
    paramSetter_signal = QtCore.pyqtSignal(object)

    def __init__(self,view):
        '''
        view (ParametersView)
            view to be wrapped by this ParametersController instance.
        '''
        GUIController.__init__(self, view,None,None)
        UserInputParser.__init__(self,view)
        view.addSignals(paramLabel = self.paramLabel_signal, paramSetter = self.paramSetter_signal)
        self.view.qVelRandomizer.clicked.connect(self.randomizeGVelocity)
        self.view.signals['paramSetter'].connect(self.bindFields)
        self.fileManager = ParametersFileManager(self.view.signals)
        self._tmpStars = []
        
    def displayHelpMessage(self):
        '''
            opens a dialog, displaying the docstrings for the Parameters class.
        '''
        dialog = HelpDialog(self.view)
        dialog.show()
        
    def hide(self):
        '''
        DEPRECATED.
        '''
        self.view.mainSplitter.setSizes([0,100,100])
#         self.view.paramFrame.setHidden(True)
#         self.view.queueBox.setHidden(True)
#         self.view.visualizationBox.setHidden(True)
        
    def show(self):
        '''
        DEPRECATED.
        '''
        pass
        
    def _buildObjectHelper(self):
        """
        Collects and parses all the information from the various user input fields/checkboxes.
        returns them in a Parameters object.
        If the user inputs invalid arguments, will handle the error by returning None and sending a message
        to the progress_label_slot saying "Error. Input could not be parsed to numbers."
        """
        try:
            gRedshift = float(self.view.gRedshift.text())
            qRedshift = float(self.view.qRedshift.text())
            qBHMass = u.Quantity(float(self.view.quasarBHMassEntry.text()),'solMass')
            specials = UnitConverter.generateSpecialUnits(qBHMass,qRedshift,gRedshift)
            with u.add_enabled_units(specials):
                #Setting units
                inputUnit = self.view.scaleUnitOption.currentText()
                #Determination of relative motion
                gVelocity = self.view.qVelocity.text()
                gComponents = gVelocity.strip('()').split(',')
                gPositionRaDec = self.view.gPositionEntry.text()
                apparentV = None
                if len(gComponents) == 2:
                    apparentV = self.vectorFromQString(self.view.qVelocity.text())
                else:
                    gVelocity = CartesianRepresentation(gComponents[0],gComponents[1],gComponents[2],'')
    
    
                    ra,dec = gPositionRaDec.strip('()').split(',')
                    gPositionRaDec = SkyCoord(ra,dec, unit = (u.hourangle,u.deg))
                    apparentV = self.getApparentVelocity(gPositionRaDec,gVelocity)
    
                #Quasar properties
                qPosition = self.vectorFromQString(self.view.qPosition.text(), unit='arcsec').to('rad')
                qRadius = u.Quantity(float(self.view.qRadius.text()), 'uas')
                
                #Galaxy properties
                gVelDispersion = u.Quantity(float(self.view.gVelDispersion.text()), 'km/s')
                gNumStars = int(self.view.gNumStars.text())
                gShearMag = float(self.view.gShearMag.text())
                gShearAngle = u.Quantity(float(self.view.gShearAngle.text()), 'degree')
                gStarStdDev = float(self.view.gStarStdDev.text())
                gStarMean = gVelDispersion
                gStarParams = None
                if gNumStars == 0 or gStarStdDev == 0:
                    gStarParams = None
                else:
                    gStarParams = (gStarMean,gStarStdDev)
                displayCenter = self.vectorFromQString(self.view.gCenter.text(), unit='arcsec').to('rad')
                dTheta = u.Quantity(float(self.view.scaleInput.text()), inputUnit).to('rad').value
                canvasDim = int(self.view.dimensionInput.text())
                displayQuasar = True
                displayGalaxy = True
                if self._tmpStars:
                    galaxy = Galaxy(gRedshift, gVelDispersion, gShearMag, gShearAngle, gNumStars, center=displayCenter, starVelocityParams=gStarParams,skyCoords = gPositionRaDec, velocity = gVelocity,stars = self._tmpStars[1])
                else:
                    galaxy = Galaxy(gRedshift, gVelDispersion, gShearMag, gShearAngle, gNumStars, center=displayCenter, starVelocityParams=gStarParams,skyCoords = gPositionRaDec, velocity = gVelocity)
                quasar = Quasar(qRedshift, qRadius, qPosition, apparentV, mass = qBHMass)
                params = Parameters(galaxy, quasar, dTheta, canvasDim, displayGalaxy, displayQuasar)
                self._tmpStars = None
                if self.view.qRadiusUnitOption.currentIndex() == 1:
                    absRg = (params.quasar.mass*const.G/const.c/const.c).to('m')
                    angle = absRg/params.quasar.angDiamDist.to('m')
                    params.quasar.update(radius = u.Quantity(angle.value*qRadius.value,'rad'))
                self.view.pixelAngleLabel_angle.setText(str(self.__round_to_n(params.pixelScale_angle.value,4)))
                self.view.pixelAngleLabel_thetaE.setText(str(self.__round_to_n(params.pixelScale_thetaE,4)))
                self.view.pixelAngleLabel_Rg.setText(str(self.__round_to_n(params.pixelScale_Rg,4)))
                self.view.quasarRadiusRGEntry.setText(str(self.__round_to_n(params.quasarRadius_rg, 4)))
                return params
        except:
            print("Tried. Failed to build Parameters Instance")
            

    def getApparentVelocity(self,pos,v):
        ev = EarthVelocity
        apparentV = ev.to_cartesian() - v
        posInSky = pos.galactic
        phi,theta = (posInSky.l.to('rad').value,math.pi/2 - posInSky.b.to('rad').value)
        vx = apparentV.x*math.cos(theta)*math.cos(phi)+apparentV.y*math.cos(theta)*math.sin(phi)-apparentV.z*math.sin(theta)
        vy = apparentV.y*math.cos(phi)-apparentV.x*math.sin(phi)
        ret = Vector2D(vx.value,vy.value,'km/s')
        print(ret)
        return ret


    def randomizeGVelocity(self):
        x,y,z = ((random.random() - 0.5)*2,(random.random() - 0.5)*2,(random.random()-0.5)*2)
        res = (x*x+y*y+z*z)**(0.5)
        x /= res
        y /= res
        z /= res
        vel = np.array([x,y,z])
        vel = vel*(random.random()*1e9)
        self.view.qVelocity.setText('(' + str(int(vel[0])) + ","+ str(int(vel[1])) + "," + str(int(vel[2]))+")")

    def _bindFieldsHelper(self,parameters):
        """Sets the User interface's various input fields with the data in the passed-in parameters object."""
        if parameters.stars != []:
            self._tmpStars = (parameters.galaxy.percentStars,parameters.galaxy.stars)
        else:
            self._tmpStars = None
        with u.add_enabled_units(parameters.specialUnits):
            qV = parameters.quasar.velocity.to('rad').unitless()*parameters.quasar.angDiamDist.to('km').value;
            qP = parameters.quasar.position.to(self.view.qPositionLabel.text()).unitless()
            gP = parameters.galaxy.position.to('arcsec').unitless()
            self.view.qVelocity.setText(qV.asString)
            self.view.qPosition.setText(qP.asString)
            self.view.gCenter.setText(gP.asString)
            self.view.qRadius.setText(str(parameters.quasar.radius.to(self.view.qRadiusUnitOption.currentText()).value))
            self.view.qRedshift.setText(str(parameters.quasar.redshift))
            self.view.gRedshift.setText(str(parameters.galaxy.redshift))
            self.view.gVelDispersion.setText(str(parameters.galaxy.velocityDispersion.value))
            self.view.gNumStars.setText(str(int(parameters.galaxy.percentStars*100)))
            self.view.gShearMag.setText(str(parameters.galaxy.shearMag))
            self.view.gShearAngle.setText(str(parameters.galaxy.shearAngle.to('degree').value))
            self.view.scaleInput.setText(str(parameters.dTheta.to(self.view.scaleUnitOption.currentText()).value * parameters.canvasDim))
            self.view.dimensionInput.setText(str(parameters.canvasDim))
            self.view.displayQuasar.setChecked(parameters.showQuasar)
            self.view.displayGalaxy.setChecked(parameters.showGalaxy)
            self.view.quasarBHMassEntry.setText(str(parameters.quasar.mass.to('solMass').value))

        
    def __round_to_n(self, x,n = 6):
        '''
        round x to n many significant figures. Default is 6
        '''
        if x == 0.0:
            return 0
        else:
            return round(float(x), -int(math.floor(math.log10(abs(float(x))))) + (n - 1))
            
    @property
    def modelID(self):
        return self.view.modelID

    def vectorFromQString(self, string,unit = None):
        """
        Converts an ordered pair string of the form (x,y) into a Vector2D of x and y.

        """
        x, y = (string.strip('()')).split(',')
        if ' ' in y:
            y = y.split(' ')[0]
        return Vector2D(float(x), float(y),unit)
