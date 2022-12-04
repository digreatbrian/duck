import threading
from .kwarghandler import handle_init_kwargs
from .mimes import guess_type
from .errors import *
from .statuscodes import responses
from .simpleos import rpdir
from .others.mapping import MutableMapping as Mapping

ERROR_CONTENT='''<html>
<head><title>Error</title>
<style>body{background-color:rgba(.2,.2,.2,.2);}
#msg{color:grey}
</style>
</head>
<body><h4>Error</h4>
<p>Error Code : %(code)s</p>
<p id="msg">Message : %(error_msg)s</p>
</body>
</html>'''

'''For Managing Requests'''

#########################
# REQUEST
#########################

class Request(Mapping):
	method=None
	path=None
	http_version=None
	headers={}
	request_error=False
	raw_request=''
	error=None
	protocol=None
	content=''
	'''Request object for parsing client request.'''
	def __init__(self,**kwargs):
		handle_init_kwargs(self,kwargs)
		self._map_keys()
		
	def _map_keys(self):
		keys=('method' ,'path' ,'http_version', 'headers', 'request_error', 'raw_request', 'error', 'protocol', 'content')
		for x in keys:
			exec('self.__setitem__(x,self.{})'.format(x))
		
	def add_header(self,header,val):
		'''Adding header to request'''
		self.headers[header]=val.strip()
		self.make_raw_request()
		
	def parse_request(self ,request):
		'''Parse raw request, if error in parsing raw request, the request object will contain the error'''
		try:
			self._parse_request(request)
		except RequestSyntaxError as e:
			self.request_error=True
			self.error=e
		
	def _parse_request(self,request):
		'''Parse request from string.'''
		#parse raw request from string
		self.raw_request=request
		request=request.strip().split(b'\r\n')
		topheader=request[0].strip()
		headers=request[1:]
		self.topheader=topheader
		if topheader:
			if len(topheader.split(b' '))==3:
				self.method,self.path,self.http_version=topheader.split(b' ')
				self.protocol=self.http_version.split(b'/')[0]
				self.method=self.method.decode('utf-8')
				self.path=self.path.decode('utf-8')
				self.http_version=self.http_version.decode('utf-8')
				self.protocol=self.protocol.decode('utf-8')
			else:
				raise RequestSyntaxError('Bad TopHeader Format/Bad Header Syntax')
		if headers:
			for hd in headers:
				if len(hd.split(b':',1))!=2:
					raise RequestSyntaxError('Bad Header Format')
				header,value=hd.split(b':',1)
				self.headers[header.decode('utf-8').strip().lower()]=value.decode('utf-8').strip()
		
	def make_raw_request(self):
		'''Construct raw request from available variables.'''
		starter=' {meth} {path} {hversion}\r\n'
		starter=starter.format(hversion=self.http_version,meth=self.method,path=self.path)
		request=''+starter
		for header in self.headers:
			request+='{header} : {value}\r\n'.format(header=header,value=self.headers[header])
		self.raw_request=request.strip()
		return self.raw_request.encode('utf-8')
	
	def __repr__(self):
		ri=super(Request,self).__repr__()
		return '<Request {} {} HTTP/{} object at {} '.format(self.method ,self.path ,self.http_version,ri.split(' ')[-1])

#########################
# HEADER
#########################

class Header(object):
	status_code=0
	status_message=None
	headers={}
	http_version='1.1'
	raw_headers=''
	explanation=''
	top_header=str()
	'''Response Header object for parsing response headers.'''
	def __init__(self,**kwargs):
		handle_init_kwargs(self,kwargs)
		self.make_raw_headers()
		
	def add_header(self, header, val):
		'''Add header and value to headerobject.'''
		self.headers[header.title()]=val
		self.make_raw_headers()
	
	def parse_status(self ,code ,msg =None ,explanation=None):
		'''Parse status code to send to the client.'''
		if code in responses:
			short,long=responses[code]
			if not msg:
				msg=short
			if not explanation:
				explanation=long
		else:
			if not msg:
				msg=' ??? '
			if not explanation:
				if msg!='???':
					explanation=msg
				else:
					explanation='???'
		self.status_message=msg
		self.status_code=code
		self.explanation=explanation
		self.make_raw_headers()
		
	def make_raw_headers(self):
		'''Make raw headers from available values.'''
		headers='HTTP/%s %d %s '%(self.http_version,self.status_code,self.status_message)
		self.topheader=headers
		headers+='\r\n'
		for header in self.headers:
			headers+='%s : %s'%(header,self.headers[header])
			headers+='\r\n'
		self.raw_headers=headers.encode('utf-8')
	
	def __repr__(self):
		resp=super(Response,self).__repr__()
		return '<Header HTTP/{} {} {} object at {} '.format(self.http_version,self.status_code,self.status_message,resp.split(' ')[-1])

#########################
# CONTENT
#########################

class Content(object):
	content=b''
	encoding='gzip'
	length=None
	type=None
	'''Parse and process the content data to send to client.'''
	def parse_content(self ,data, encoding='gzip'):
		'''Parse content data.'''
		self.encoding=encoding
		self.content=data
		self.length=len(data)
		
	def parse_type(self, type=None):
		'''Parse mimetype of content data, if type is None ,will try to determine the type automatically.'''
		if not type:
			type=guess_type(None,data=self.content)
			if not type:
				type='application/octet-stream'
		self.type=type
		
	def set_content(self ,encoding='gzip',type=None):
		'''Set the content.Content should already been encoded.'''
		#content should be encoded
		contentobj.parse_content(data, encoding)
		contentobj.parse_type(type)

#########################
# RESPONSE
#########################

class Response(Mapping):
	_contentobj=Content()
	_headerobj=Header()
	headers={}
	content=b''
	raw_response=b''
	def __init__(self ,headerobj=None ,contentobj=None,**kwargs):
		handle_init_kwargs(self ,kwargs)
		if headerobj is not None:
			self._headerobj=headerobj
		if contentobj is not None:
			self._contentobj=contentobj
		if not isinstance(self._headerobj ,Header):
			raise ValueError('headerobj should be of type Header object.')
		if not isinstance(self._contentobj ,Content):
			raise ValueError('contentobj should be of type Content object.')
		self._map_keys()
		self.parse(self._headerobj ,self._contentobj)
	
	@property
	def status(self):
		'''Read only for status code and status message for response .'''
		return self._headerobj.status_code ,self._headerobj.status_msg
		
	def _map_keys(self):
		'''Map all important keys.'''
		keys=('_contentobj' ,'_headerobj', 'headers', 'content', )
		for x in keys:
			exec('self.__setitem__(x,self.{})'.format(x))
		
	def parse(self ,hdobj ,contobj):
		'''Parse headerobj and contentobj to the response .'''
		if hdobj:
			self._headerobj=hdobj
			self.headers=hdobj.headers
			self.status_code=hdobj.status_code
			self.status_msg=hdobj.status_message
			self.status_explain=hdobj.explanation
		if contobj:
			self._contentobj=contobj
			self.content=contobj.content
		self.refresh()
		
	def make_raw_response(self):
		'''Create raw_response in bytes.'''
		if not self._contentobj.type:
			self._contentobj.parse_type(None)
		self._headerobj.make_raw_headers()
		self.raw_response=self._headerobj.raw_headers+b'\r\n'+self.content
		
	def refresh(self):
		'''Refresh all parameters.'''
		if self._headerobj:
			self.headers=self._headerobj.headers
		self.make_raw_response()
		
			
	
		
		
		
		