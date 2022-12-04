'''This is a module for creating http/https based servers  by creating an App instance and therefore running it.This can be also run from the terminal.

Documentation::

For creating new server a few things has to be done.Consider routing app to routes and supported methods.Routes are just paths visited by a client through the browser.

This app has 3 ways of creating routes.
Consider code below::
	
from duck import App
#starting server on local host on port 8000
app=App("Name of App",('0.0.0.0' ,8000))
	
@app.route('/')
def home():
	return '<p>Hello There </p>'
		
@app.fileroute('/app.apk')
def application():
	return 'source.apk'
		
@app.partial_route('/comments/%animals%', meth=[post])
def comments(about):
	print('Comment about '+about)
		
app.run()
		
Note::
	If 'meth' argument is not specified for any route creating decorator ;the 'GET' method is the default.
	
From Example::
	
@app.route :: 
If GET::
	It creates new directories and creates a file named 'index.html' from code returned which is '<p>Hello There </p>'.This file contains the code for the specified path .If the function with the decorator returns None default site is saved.The specified path will be registered which means it has been recorded that this path is to be accessed with specified method/methods.
		
If POST::
	The specified path will only be registered.
		
@app.fileroute ::
If GET::
	Its different from one above as it require filename to be returned from function with decorator.This copies the file to destination path if size<=app.fileroute_lim (in megabytes).This also just does what the one above does but in a different way.
			
If POST::
	same as above
	
@app.partial_route::
If GET::
	It just register the path/route but the file/path must be already in app.SITECODE_DIR directory.'%animals%' mean 'animals' will parsed to the function as an argument.
			
If POST::
	same as above.
			
app.run() starts the app.
		
For handling POST requests override the method handlePOST.But for GET requests no use to override handleGET cause its already implemented.Its recommended to do this.
		
class TestApp(App):
	def __init__(self ,name,addr ,**kwargs):
		super(TestApp ,self).__init__(name,addr,**kwargs)
		
	@error_handler
	def handleGET(self ,sock, rq):
		self._handleGET(sock, rq)
		#processing if the method
		fails to handle request.
				
	def handlePOST(self,sock,rq):
		Post handler code here.
		
The decorator 'error_handler' handles some basic errors such as unsupported protocol and unsupported http version etc.
		
All other errors are parsed to handle_error method.To support/create new method just create method 'handle+METHOD' and create a new registry for that method.Consider example::
		
class TestApp(App):
			
	def __init__(self ,name,addr,**kwargs):
		self.create_registry('connect')
				
	def handleCONNECT(self ,sock ,rq):
		Connect handler code here
		
For app configuration edit 'APP.cnf' created by app.To open  use any of the text editors.	

To run test sample just import module named tests from duck module and execute function "run" like this::
	
	from duck import tests
	tests.run()

A test script is run and to get the code,call function from duck.tests with name "get_code" and the code will be saved in new directory named "DuckTests"

Do it like This ::
	
	tests.get_code()
	
'''
__author__='Brian Musakwa'
__email__='ducksoftwarenet@gmail.com'
__all__=['App']

from .app import App
from .registry import Registry
from .decorators import *
from .duckrequests import (
Header ,
Request ,
Content)
from .others.mapping import MutableMapping
import argparse

if __name__=='__main__':
	#Argument passing
	usage='Usage : [-n name] [-a address] [-p port]''\nStart App Server with <name> on <address> and <port>.\nConfigure config file <"APP.cnf"> on protocol to use ssl/https.'
	aparser=argparse.ArgumentParser
	aparser=aparser(usage=usage)
	aparser.add_argument('-n','--name',dest='name',help='Launch app with name <name> ')
	aparser.add_argument('-a','--addr',dest='addr',help='Start app on <addr> ')
	aparser.add_argument('-p','--port',dest='port',help='Start app on <port> ')
	(name,address,port)=aparser.parse_args().name,aparser.parse_args().addr ,aparser.parse_args().port
	if not name:
		name='DuckApp'
	if not address:
		address='0.0.0.0'
	if not port:
		port=8000
	
	a=App(name,(address,port))
	
	a.run()
	
