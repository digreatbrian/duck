'''Simple Class for registering routes.'''
from .simpleos import rpdir

class Registry(object):
	#registering Routes
	method=None
	def __init__(self ,method):
		self.routes=list()
		self.method=method.upper()
		
	def register(self, rt,ignorecase=False):
		if not ignorecase:
			rt=rpdir(rt).lower()
		if not rt in self.routes:
			self.routes.append(rt)
			
	def route_exists(self ,route):
		return rpdir(route).lower() in self.routes
			
	def __repr__(self):
		ri=super(Registry,self).__repr__()
		id=ri.split(' ')[-1]
		return '<Registry METH=%s object at %s'%(str(self.method).upper(), id)
		