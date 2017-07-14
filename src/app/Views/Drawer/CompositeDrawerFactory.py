from .Drawer import Drawer
from .Drawer import PlotDrawer
from .Drawer import ImageDrawer
from .Drawer import CompositeDrawer
from .LensedImageDrawer import LensedImageDrawer
from .LensedImageDrawer_pyqtgraph import LensedImageDrawer_pyqtgraph
from ...Utility.NullSignal import NullSignal

def LensedImageLightCurveComposite(imgSignal=NullSignal, curveSignal=NullSignal):
	img = LensedImageDrawer(imgSignal)
	curve = PlotDrawer(curveSignal)
	return CompositeDrawer(img,curve)

def MagTracerComposite(imgSignal = NullSignal, curveSignal = NullSignal):
	img = LensedImageDrawer_pyqtgraph(imgSignal)
	curve = PlotDrawer(curveSignal)
	return CompositeDrawer(img,curve)
	
