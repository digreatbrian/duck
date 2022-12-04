'''Decorator Module for app decorators.'''

import os
from .simpleos import fixdir 
from .simpleos import isdir
from .simpleos import rpdir
from .simpleos import join
from .logger import log ,cmlog
from .errors import RouteError
from .errors import FunctionError
from .formatters import argformatter as pathformatter
from .simpleos import copyfile
from .simpleos import create_file
from .statuscodes import responses

starter='CONFIGURING ROUTE ...'
ender='REGISTERED ROUTE'

##PARTIAL##
def partial_deco(cl,func,path ,meth):
	'''Decorator for registering route which is already present in app.SITECODE_DIR'''
	app_cls=cl
	route_file=None
	func_args ,path=pathformatter(path, sep='%')
	try:
		if not func_args:
			func()
		else:
			func(*func_args)
	except ValueError:
		funcname=func.__name__
		raise FunctionError('Function %s should accept exactly  %d arguments'%(funcname, len(func_args)))
	if isdir(path)==True:
		#is a directory or ordinary route
		route_file=join(join(app_cls.SITECODE_DIR,path), 'index.html')
	else:
		#is a fileroute
		route_file=join(app_cls.SITECODE_DIR,path)
	#continuing
	if os.path.isfile(route_file)==True:
		if app_cls.debug:
			print('\n')
			log(starter)
		if not isinstance(meth ,list):
			raise RouteError('"meth" argument should be a list of methods.')
		#else
		for mth in meth:
			app_cls.register_route(path ,mth)
		#finished
		if app_cls.debug:
			log(str(ender+' %s @ %s'%(rpdir(path), str(meth).upper().strip('[]'))))
	else:
		raise RouteError('Route or Fileroute doesnt exist in app.SITECODE_DIR')
	
##FILEROUTE##
def fileroute_deco(cl,func,path ,meth):
	'''Decorator for registering new fileroute  ,will be saved in app.SITECODE_DIR'''
	if isdir(path)==True:
		raise RouteError('Path must be a fileroute not an ordinary route ,use @route instead.')
	app_cls=cl
	src_file=None
	func_args ,path=pathformatter(path, sep='%')
	try:
		if not func_args:
			src_file=func()
		else:
			src_file=func(*func_args)
	except ValueError:
		funcname=func.__name__
		raise FunctionError('Function %s should accept exactly  %d arguments'%(funcname, len(func_args)))
	src_file=fixdir(src_file)
	if os.path.exists(src_file):
		#continue
		if app_cls.debug:
			print('\n')
			log(starter)
		if not isinstance(meth ,list):
			raise RouteError('"meth" argument should be a list of methods.')
		#else
		for mth in meth:
			registry=app_cls.getMethodRegistry(mth)
			registry.register(path)
		size=os.stat(fixdir(src_file)).st_size
		copyfile(src_file, join(app_cls.SITECODE_DIR, path))
		if app_cls.debug:
			log(str(ender+' %s @ %s'%(rpdir(path), str(meth).upper().strip('[]'))))
	#else file doesnt exist
	else:
		raise RouteError('File returned by function "%s" doesnt exist.'%func.__name__)

##ROUTE##
def route_deco(cl,func,path ,meth):
	''''Decorator for registering new route will be saved in app.SITECODE_DIR'''
	app_cls=cl
	html_data=None
	func_args ,path=pathformatter(path, sep='%')
	try:
		if not func_args:
			html_data=func()
		else:
			html_data=func(*func_args)
	except ValueError:
		funcname=func.__name__
		raise FunctionError('Function %s should accept exactly  %d arguments'%(funcname, len(func_args)))
	if html_data is None:
		html_data='<b>Duck Server Running ...</b>'
	if isdir(path)==True:
		#continue
		if app_cls.debug:
			print('\n')
			log(starter)
		if not isinstance(meth ,list):
			raise RouteError('"meth" argument should be a list of methods.')
		#else
		for mth in meth:
			registry=app_cls.getMethodRegistry(mth)
			registry.register(path)
		create_file(join(fixdir(join(app_cls.SITECODE_DIR ,path)), 'index.html'),'w',html_data)
		if app_cls.debug:
			log(str(ender+' %s @ %s'%(rpdir(path), str(meth).upper().strip('[]'))))
	#else
	else:
		raise  RouteError('Path should an ordinary route not a fileroute ,use @fileroute instead. ')
	
##ERROR HANDLER##
def error_handler(func ,*args):
	'''Error handler decorator which handle errors such as unsupported protocol ,unsupported http version and unsupported method on app methods of handling requests
	example::
		import duck
		
		@duck.error_handler
		def handleCONNECT(clientsock, request):
			pass
			
		'''		
	def handler(cls, sock ,req):
		#checking existance of meth
		meth=req.method
		registries=cls.getAllRegistries()
		path_exists=False
		for rg in registries:
			if rg.route_exists(req.path):
				path_exists=True
		addr=sock.getsockname()
		addr='@ %s'%list(addr)
		fn='FINISHED'
		meth='METH : %s'%req.method
		err=''
		pth='PATH : %s'%req.path
		if path_exists==True:
			#path exists somewhere
			#in method registries
			methregistry=cls.getMethodRegistry(req.method)
			if methregistry.route_exists(req.path)==True:
				#route and specified path
				#exists
				#parsing request to handler
				#coz all errors cleared
				func(cls, sock ,req)
			else:
				#method for resource path
				#not supported
				cls.send_error(sock ,405)
				errb=list(responses[405])[0]
				err='ERROR : %s'%errb
				if cls.debug==True:
					cmlog('*','\n',addr,meth,pth,err,fn)
		else:
			#path doesnt exist at all in all
			#method registries
			cls.send_error(sock,404)
			errb=list(responses[404])[0]
			err='ERROR : %s'%errb
			if cls.debug==True:
				cmlog('*','\n',addr,meth,pth,err,fn)
	return handler
	
	
def redirect_deco(cl,func,path,meth,parse_headers,conditions):
	app_cls=cl
	to_uri=None
	func_args ,path=pathformatter(path, sep='%')
	
	from_uri=path
	try:
		if not func_args:
			to_uri=func()
		else:
			to_uri=func(*func_args)
	except ValueError:
		funcname=func.__name__
		raise FunctionError('Function %s should accept exactly  %d arguments'%(funcname, len(func_args)))
	#checking if from_uri and to_uri exist in registrie
	registries=app_cls.getAllRegistries()
	redirect_reg=app_cls.getMethodRegistry('REDIRECTS')
	to_uri_exists=False
	from_uri_exists=False
	
	for x in meth:
		reg=app_cls.getMethodRegistry(x)
		if reg.route_exists(from_uri):
			from_uri_exists=True
	
	for x in registries:
		if x.route_exists(to_uri):
			to_uri_exists=True
			
	if not to_uri_exists:
		raise RouteError('URI to redirect to returned by function "%s" is not registered in any method registry or doesnt exist.'%func.__name__)
		
	if not from_uri_exists:
		raise RouteError('URI to redirect from  is not registered in any of the given method registries. ')
		
	#to_uri and from_uri exists
	redirect_reg.register({'from':from_uri,'to':to_uri,'conditions':conditions,'parse_headers':parse_headers},ignorecase=True)