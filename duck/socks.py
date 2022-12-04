#socks
'''An advance implementation of socket module.'''
import ssl
import socket

def Socket(family=socket.AF_INET ,type=socket.SOCK_STREAM):
	return socket.socket(family,type)
	
def SSLSocket(sock ,keyfile=None ,certfile=None ,version=2, server_side=False,ca_certs=None ,ciphers =None,**kwargs):
	sock=ssl.wrap_socket(sock,keyfile=keyfile,certfile=certfile,ssl_version=version,ca_certs=ca_certs,server_side=server_side,ciphers=ciphers,**kwargs)
	
	return sock
	
	
