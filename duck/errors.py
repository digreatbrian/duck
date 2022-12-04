'''Class For Duck App Errors.'''
class BaseError(Exception):
	'''base class for Errors'''
	def __init__(self ,message ,**kws):
		self.message = message
            
	def __str__(self):
		return '{}'.format(self.message)
		
class RequestError(BaseError):
	pass
	
class RequestMethodUnsupportedError(RequestError):
	pass
	
class RequestSyntaxError(RequestError):
	pass
	
class RequestTimeoutError(RequestError):
	pass
	
	
class ConfigError(BaseError):
	'''Error when values set on config app cls are Invalid'''
	
class RegistryError(BaseError):
	'''Registry Error specifically for routes'''
	
class HeaderError(BaseError):
	pass
	
class RouteError(BaseError):
	pass
	
class FunctionError(BaseError):
	pass
	
	