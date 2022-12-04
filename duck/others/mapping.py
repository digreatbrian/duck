import collections as cl

class MapWrapper():
	def __len__(self):
		return self.__dict__.__len__()
	
	def __delitem__(self ,t):
		self.__dict__.__delitem__(t)
		
	def __iter__(self):
		return self.__dict__.__iter__()
		
	def __getitem__(self, t):
		return self.__dict__.__getitem__(t)
		
	def __setitem__(self,key,value):
		self.__dict__.__setitem__(key ,value)
	
	def __initx__(self):
		for x in dir(self):
			exec('self.__setitem__(x,self.{})'.format(x))
	
class MutableMapping(MapWrapper,cl.MutableMapping):
	pass

class CompleteMapping(MapWrapper,cl.MutableMapping):
	'''Map all attributes completely into a dictionary.'''
	def __init__(self ,**kwargs):
		super(CompleteMapping, self).__init__(**kwargs)
		self.__initx__()
	
	
