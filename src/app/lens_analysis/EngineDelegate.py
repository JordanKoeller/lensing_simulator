import copy

_engineRef = None

def _getOrCreateEngine():
	from app.engine import getCalculationEngine
	global _engineRef
	if not _engineRef:
		_engineRef = getCalculationEngine()



class EngineDelegate(object):
	"""A container for communicating with an engine for on-the-fly calculation.
	This allows for a shared engine between Trials, to prevent redundant recalculation
	of data."""
	def __init__(self,parameters=None):
		super(EngineDelegate, self).__init__()
		_getOrCreateEngine()
		if parameters:
			self.reconfigure(parameters)

		#TODO: Put classmethods for fromFile or fro

	@property
	def engine(self):
		global _engineRef
		return _engineRef

	def bind_trial(self,trial):
		self.reconfigure(trial.parameters)
	

	def reconfigure(self,parameters):
		paramcopy = copy.deepcopy(parameters)
		self.engine.update_parameters(parameters)

	def query_point(self,x,y,r):
		self.engine.query_point(x,y,r)

	def query_line(pts,r):
		self.engine.query_line(pts,r)

	def query_light_curves(pts,r):
		self.engine.calculation_delegate.sample_light_curves(pts,r)

	def query_area(area):
		self.engine.make_mag_map(area.center,area.dimensions,area.resolution)




		