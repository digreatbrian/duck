
''''Module for creating specific servers.'''

from .socks import SSLSocket
import socket #For  type of
from .httpd import ServerWrapper
__all__=['Server','SSLServer','HTTPServer']

#============================
#BASE SERVER
class Server(object):
	enable_ssl=False
	sock=None
	ssl_params={}
	#sock >> Socket Object
	#ssl params >> Dict(ssl_arg:ssl_value)
	def init(self ,sock):
		'''Initialise the server .'''
		if not isinstance(type(sock),type(socket.socket)):
			raise TypeError('sock should be of type socket')
		self.sock=sock
		if self.enable_ssl:
			self.sock=SSLSocket(sock=sock,server_side=True,**self.ssl_params)
			return self.sock
		else:
			return self.sock
			
#===========================
#SSL/HTTPS SERVER
class SSLServer(Server ,ServerWrapper):
	def __init__(self, sock, addr,**kwargs):
		self.ssl_params=kwargs
		self.enable_ssl=True
		self.addr=addr
		self.init(sock)
		
#============================
#HTTP SERVER
class HTTPServer(Server, ServerWrapper):
	def __init__(self ,sock ,addr,**kwargs):
		self.addr=addr
		self.init(sock)		
		
			