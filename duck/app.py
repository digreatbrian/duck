
__author__='@Brian Musakwa'
__all__=['App' ,'BaseApp']

from .cnfg import getcnfvalue 
from .cnfg import getcnf ,createcnf
from .servers import SSLServer 
from .servers import HTTPServer
from .duckrequests import Content
from .duckrequests import Header
from .duckrequests import Response
from .duckrequests import Request
from .logger import log, cmlog
from .errors import *
from .kwarghandler import handle_init_kwargs
from .defaults import SSL_DEFAULTS
from .version import server_version as SERVER_VERSION
from .duckrequests import ERROR_CONTENT as ERR
from .socks import Socket
from .registry import Registry
from .mimes import guess_type
from .simpleos import *
from .simpleos import copyfile ,fixdir ,onlydir ,rpdir
from .route import (
add_route, 
get_routedata ,
delete_route, 
delete_fileroute,
get_fileroutedata)
from .decorators import (
partial_deco ,
fileroute_deco ,
route_deco ,
redirect_deco,
error_handler)
import os
import time
import socket
import sys
from .processor import RequestProcessor

CONFIGNAME='APP.cnf'

def gmtime():
	'''Return GMT Formatted Time.'''
	#getting timestamp
	timestamp=time.time()
	weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
	monthname = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun','Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	#formatting to GMT
	year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
	s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (weekdayname[wd],day, monthname[month], year,hh, mm, ss)
	return s

class BaseApp(object):
	debug=True
	protocol=None
	supportedhttp=[]
	enable_ssl=False
	ssl_params={}
	addr=(None ,None)
	initialised=False
	server_version=None
	headerobj=Header
	contentobj=Content
	http_version='1.1'
	'''Base Class for App class.'''
	def __init__(self,name,addr,**kwargs):
		handle_init_kwargs(self,kwargs)
		self.addr=addr
		self.name=name
		self.SITECODE_DIR=name
		self.setConfigData()
		self._init_server()
		
	def load_file(self,filename):
		'''Load a file especially html documents.'''
		with open(filename, 'r') as d:
			return d.read()
		
	def run(self):
		'''Start the app'''
		self.server.start_server()
		
	def handle_error(self ,clientsock, error ,raw_request):
		'''Handle Errors like Bad Request Syntax and Header Format Error etc.'''
		
	def handleGET(self ,clientsock, request):'''Handle GET Requests.'''
	
	def raise_error(self ,clientsock ,err ,raw_request):
		'''Raise an error for clientsock on raw_request.'''
		self.handle_error(clientsock ,err,raw_request)
		
	def handlePOST(self ,clientsock, request):pass
	
	def add_basic_headers(self, h):
		'''Add basic headers like Date ,Server Name and LastModified Date to headerobject .'''
		#adding basic headers
		ServerVersion=self.server_version
		Date=gmtime()
		#h.add_header('Server-Version' ,ServerVersion)
		h.add_header('Date' ,Date)
		h.add_header('Last-Modified', self.last_modified)
		
	def send_error(self, sock ,code ,msg=None ,explanation=None):
		'''Send error msg to sock and close connection'''
		#sending error
		#creating response
		response=Response()
		headerobj=self.headerobj()
		contobj=self.contentobj()
		
		#adding headers
		headerobj.parse_status(code, msg ,explanation)
		content=ERR%{'code':code,'error_msg':headerobj.explanation}
		content=content.encode('utf-8')
		self.add_basic_headers(headerobj)
		
		#adding content
		contobj.parse_content(content)
		contobj.parse_type('text/html')
		
		#adding content headers
		headerobj.add_header('Server' ,self.server_version)
		headerobj.add_header('Content-Type' ,'text/html')
		headerobj.add_header('Content-Length', contobj.length)
		headerobj.add_header('Encoding' ,contobj.encoding)
		headerobj.add_header('Connection', 'close')
		response.parse(headerobj, contobj)
		self._send_response(sock, response)
		try:
			self.server.close(sock)
		except:
			pass
		
	def _send_response(self,sock, responseobj):
		'''Send response object to socket.'''
		responseobj.make_raw_response()
		resp=responseobj.raw_response
		try:
			sock.sendall(resp)
		except Exception as e:
			log('ERR: '+e.__str__())
		
	def send_response(self ,
	sock ,
	status_code,
	content ,
	content_type,
	encoding='gzip' ,
	status_msg=None ,
	status_explanation=None,
	headers={}):
		'''Send response to client sock.'''
		#creating response
		response=Response()
		headerobj=self.headerobj()
		contobj=self.contentobj()
		
		#adding headers
		headerobj.parse_status(status_code, status_msg ,status_explanation)
		self.add_basic_headers(headerobj)
		
		#adding content
		contobj.parse_content(content ,encoding)
		contobj.parse_type(content_type)
		
		#adding content headers
		headerobj.add_header('Server' ,self.server_version)
		if content_type!='None':
			headerobj.add_header('Content-Type' ,content_type)
		headerobj.add_header('Content-Length', contobj.length)
		headerobj.add_header('Encoding' ,encoding)
		
		#adding parsed headers to the function
		for x in headers.keys():
			headerobj.add_header(x,headers[x])
			
		response.parse(headerobj, contobj)
		self._send_response(sock, response)
		
	def _init_server(self):
		'''Initialising Server Socket'''
		sock=Socket()
		self.server=None
		self.initialised=True
		if self.enable_ssl:
			#configuring ssl options
			if not isinstance(self.ssl_params ,dict):
				raise ConfigError('SSL Parameters must be a Dict Please use Configuration file other than setting yourself')
			if len(self.ssl_params)!=7:
				raise ConfigError('SSL Parameters should be at least 7 ,use Configuration File Instead')
			self.server=SSLServer(sock,self.addr)
		else:
			self.server=HTTPServer(sock,self.addr)
		self.server.debug=self.debug
		self.server.version=self.server_version
		self.server.app_cls=self
		self.server.last_modified=self.last_modified
		
	def setConfigData(self):
		'''Setting Configuration Data To App'''
		msg=getcnf(CONFIGNAME)
		#msg is a configparser object if configname file exists else is None
		if not msg:
			#create app config file coz it doesnt exist
			#creating data values First
			dat=[['HTTPVersions','supported','1.0,1.1'],['APP','debug','False'],['APP','protocol','http'],['APP' ,'ServerVersion', '%s'%SERVER_VERSION],['APP' ,'LastModified',gmtime()],['SSL','certfile','default'],['SSL','cert_reqs','0'],['SSL','keyfile', 'default'], ['SSL', 'version', '2'] ,['SSL' ,'ca_certs' ,'default'],['SSL','supress_ragged_eofs', True], ['SSL', 'ciphers' ,'default']]
			#creating config
			createcnf(CONFIGNAME ,dat)
		name=CONFIGNAME
		protocol_active=None
		if self.protocol:
			protocol_active=self.protocol
		self.supportedhttp,self.debug ,self.protocol,self.server_version,self.last_modified=getcnfvalue(name,'HTTPVersions' ,'supported').split(','),getcnfvalue(name,'APP', 'debug'),getcnfvalue(name,'APP', 'protocol'),getcnfvalue(name,'APP', 'ServerVersion') ,getcnfvalue(name, 'APP', 'LastModified')
		if self.debug.lower().strip()=='true':
			self.debug=True
		else:
			self.debug=False
		if self.protocol!='http':
			self.enable_ssl=True
			certfile ,cert_reqs, keyfile ,version ,ca_certs ,supress_ragged_eofs ,ciphers =getcnfvalue(name,'SSL' ,'certfile') ,getcnfvalue(name,'SSL' ,'cert_reqs'),getcnfvalue(name,'SSL' ,'keyfile'), getcnfvalue(name,'SSL' ,'version') ,getcnfvalue(name,'SSL' ,'ca_certs') ,getcnfvalue(name,'SSL' ,'supress_ragged_eofs'),getcnfvalue(name,'SSL', 'ciphers')
			ars={'certfile':certfile ,'cert_reqs':cert_reqs ,'keyfile':keyfile ,'version':version ,'ca_certs':ca_certs, 'supress_ragged_eofs':supress_ragged_eofs,'ciphers':ciphers}
			num=0
			for x in ars.values():
				if x.strip()=='default':
					ars[list(ars.keys())[num]]=SSL_DEFAULTS[list(ars.keys())[num]]
				num+=1
			self.ssl_params=ars
		if self.debug==True:
			log('CONFIGURATION LOADED')
		if protocol_active:
			self.protocol=protocol_active
			if self.protocol=='https':
				self.enable_ssl=True
			else:
				#restoring default protocol
				self.protocol='http'
			
			
class App(BaseApp):
	GET_REGISTRY=Registry('GET')
	POST_REGISTRY=Registry('POST')
	SITECODE_DIR='sitecode'
	REDIRECTS_REGISTRY=Registry('REDIRECTS')
	#fileroute_lim is megabytes in which a fileroute can be created by the app
	fileroute_lim=50 
		
	def getMethodRegistry(self ,method):
		'''Return specified method registry .'''
		target=method.upper()+'_REGISTRY'
		try:
			return self.__getattribute__(target)
		except AttributeError:
			raise RegistryError('No registry with specified method %r'%target)
			
	def create_registry(self ,method):
		'''Creates New Registry for specified method'''
		target=method.upper()+'_REGISTRY'
		if hasattr(self ,target):
			raise RegistryError('Registry For The Specified Method already exists')
		exec('self.%s'%target+'=Registry("%s")'%method)
		return self.__getattribute__(target)
		
	def getAllRegistries(self):
		'''Returns All Method Registries in App'''
		d=list()
		for i in dir(self):
			a=self.__getattribute__(i)
			if isinstance(a ,Registry):
				d.append(a)
		return d
			
	def register_route(self ,route ,method):
		'''Register Route with specified method.'''
		#register route with specified method
		target=method.upper()+'_REGISTRY'
		routeobj=None
		if hasattr(self, target):
			#method route object exists
			routeobj=self.__getattribute__(target)
			if not isinstance(routeobj ,Registry):
				raise RegistryError('self.%s'%target+' Should be a Registry object')
		else:
			raise RegistryError('Registry for method %s Doesn\'t Exist'%method.upper())
		if routeobj.method.lower()==method.lower():
			routeobj.register(route)
			
	def redirect_request(self,sock,request_obj,redirect_dict):
		#GET TO REDIRECT REQUEST
		processor=RequestProcessor(sock,self)
		parse_headers=redirect_dict['parse_headers']
		
		###making redirect response
		code=201
		to_url=redirect_dict['to']
		parse_headers['host']=to_url
		content=to_url.encode('utf-8')
		self.send_response(sock=sock,content=content,content_type='None',status_code=code,headers=parse_headers)
		sock.close()
			
	def redirect(self,path,meth=['GET'],parse_headers={},conditions={}):
		'''Redirect any url to destination url registered by the app.Argument meth is list of methods supported for a successful redirect.Conditions is a dictionary of conditions that the request should obtain.The keys supported within conditions dict is "if" and "elif" .You may referrence the request headers dict by using &headers and you can also referrence any header in &headers by calling &header(headername).Also you may call any function upon the headerkey or headervalue by calling @func(&header('headername')).To call the request ,you can use &Request.Parse Headers are new headers you want to parse to client.
		Example include::
			
			@app.route('/',meth=["GET"])
			def home():
				return "Redirect Test"
				
			@app.route('/redirect')
			def redirect_():
				return "Redirected To This Site"
				
			conditions={'if':'&header('Referrer')=='/' or @len(&header('connection'))>3','elif':'&Request.http_version=='1.1'}
			
			@app.redirect('/',meth=['Get'],conditions=conditions)
			def direct():
				return '/redirect'
				
				"'''
		def wrapper(func):
			redirect_deco(self,func,path,meth,parse_headers,conditions)
		return wrapper
		
	def route(self ,path,meth=['GET']):
		'''Decorator for adding new route with specified methods.Route code is stored in sitecode directory.'''
		def wrapper(func):
			route_deco(self,func,path ,meth)
		return wrapper
		
	def partial_route(self ,path,meth=['GET']):
		'''Adding route thats already been created.'''
		def wrapper(func):
			partial_deco(self ,func,path ,meth)
		return wrapper
		
	def fileroute(self ,path,meth=['GET']):
		'''Adding Fileroute for methods specified.'''
		
		def wrapper(func):
			fileroute_deco(self,func,path ,meth)
		return wrapper		
			
	def _handleGET(self ,_from ,req):
		'''Handle all 'GET' requests if no error related to request path ,protocol,http version, etc.All these errors are handled by @error_handler decorator.'''
		#errors already handled by 
		#@error_handler
		#supported method
		#supported request syntax
		clientsock=_from
		addr=clientsock.getsockname()
		addr='@ %s'%list(addr)
		fn='FINISHED'
		meth='METHOD : %s'%req.method
		pth='PATH : %s'%req.path
		if isdir(req.path):
			#it is a route
			codepath=fixdir(join(self.SITECODE_DIR ,req.path))
			data=get_routedata(codepath)
			content=data.encode('utf-8')
			status=200 #OK
			self.send_response(clientsock,status,content, 'text/html')
		else:
			#it is a fileroute
			filename=fixdir(join(self.SITECODE_DIR ,req.path))
			content=get_fileroutedata(filename,'rb')
			status=200 #OK
			cont_type=guess_type(req.path ,content)
			self.send_response(clientsock,status,content, cont_type)
		if 'connection' in req.headers.keys():
			if req.headers['connection'].lower()=='keep-alive':self.server.fake_close(clientsock)
			else:self.server.close(clientsock)
		if self.debug==True:
			cmlog('*','\n',addr,meth,pth,fn)
		
	@error_handler
	def handleGET(self ,_from ,req):
		'''Handle all 'GET' requests if no error related to request path ,protocol,http version, etc.All these errors are handled by @error_handler decorator.'''
		self._handleGET(_from ,req)
	
	@error_handler
	def handlePOST(self,sock,request):
		''''Handle all 'POST' requests if no error related to request path ,protocol,http version, etc.All these errors are handled by @error_handler decorator.'''
	
	def _handle_error(self, _from, err,raw_request):
		'''Handle errors like request syntax ,unsupported method and bad header format.'''
		addr=_from.getsockname()
		addr='@ %s'%list(addr)
		fn='FINISHED'
		if err.__str__()=='Request Method Unsupported':
			err='ERROR : %s'%err.__str__()
			try:
				parser=Request()
				parser.parse_request(raw_request)
				if not parser.error:
					topheader=parser.topheader
				else:
					topheader=''
					m=list(raw_request)[0:10]
					for x in m:
						topheader+=x
				topheader='TOPHEADER : %s'%topheader
			except Exception:
				pass
			self.send_error(_from,400 ,'Unsupported Method')
			if self.debug==True:
				try:
					cmlog('*' ,'\n',addr,err,topheader,fn)
				except :
					cmlog('*' ,'\n',addr,err,fn)
		if not raw_request:
			#no data sent
			self.server.close(_from)
	
	def handle_error(self, _from, err,raw_request):
		'''Handle errors like request syntax ,unsupported method and bad header format.'''
		self._handle_error(_from, err,raw_request)
			
			
