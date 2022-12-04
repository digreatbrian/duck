'''Main processor of data received from the client.'''

from .duckrequests import Request
from .errors import *

__all__=['RequestProcessor']

class RequestProcessor():
	raw_request=None
	handler=None
	error=None
	'''handler is where the processed request is going to be forwarded'''
	def __init__(self ,sock,handler,**kw):
		self.handler=handler
		self.sock=sock
		
	def process(self ,request):
		'''Processing of the request.'''
		self.raw_request=request
		rq=Request()
		rq.parse_request(request)
		rq.make_raw_request()
		self.request=rq
		self.data=rq.raw_request
		try:
			#no error will be raised if its a sucessful redirect else Request Error will be raised to continue processing request because its not a redirect
			self.process_for_redirect(rq)
			#returning so as to stop further processing because its a redirect ,will be handled by process_for_redirect
			return 'REDIRECT'
		except RequestError:
			pass
		if  rq.request_error==False:
			#if no error in request format
			meth=rq.method
			try:
				#calling method of handler
				#handle{method}
				c='handle'+meth.upper()
				self.handle=self.handler.__getattribute__(c)
				return self.handle
			except AttributeError:
				self.error=RequestError('Request Method Unsupported')
		else:
			#if error in parsing request
			self.error= RequestError(rq.error)
			
	def process_for_redirect(self,request):
		rq=request
		app_cls=self.handler
		redirect_reg=app_cls.getMethodRegistry('REDIRECTS')
		
		def redirect(used_condition,requestobj,redirect_dict):
			#used_condition is the condition used ,can either be 'if' or 'elif' as a string
			#function that keeps record of all successful redirects and can handle all redirects
			app_cls.redirect_request(self.sock,requestobj,redirect_dict)
		
		if not redirect_reg.routes:
			raise  RequestError("This is not an error ,but its a trigger that there is no redirect for this request")
			
		for rd in redirect_reg.routes:
			if rd['from']==request.path:
				#possible redirect,confirming conditions
				to_=rd['to']
				conditions=rd['conditions']
				def header_func(s):
					return s.lower()
				request_obj=rq
				headerz=rq.headers
				ifs=''
				elifs=''
				try:
					ifconditions=conditions['if']
					cns=ifconditions.split(' ')
					new_cns=[]
					for cn in cns:
						cn=cn.strip()
						if cn.startswith('&header'):
							cn=cn.replace('&header(','header_func(')
						if cn.startswith('&Request'):
							cn=cn.replace('&Request','request_obj')
						if cn.startswith('@'):
							cn=cn.replace('@','')
						if cn.startswith('&headers'):
							cn=cn.replace('&headers','headerz')
						new_cns.append(cn)
						new_cns.append(' ')
					for x in new_cns:
						ifs+=x
				except KeyError:
					pass
				try:
					elifconditions=conditions['elif']
					cns=elifconditions.split(' ')
					new_cns=[]
					for cn in cns:
						cn=cn.strip()
						if cn.startswith('&header'):
							cn=cn.replace('&header(','(header_func')
						if cn.startswith('&Request'):
							cn=cn.replace('&Request','request_obj')
						if cn.startswith('@'):
							cn=cn.replace('@','')
						if cn.startswith('&headers'):
							cn=cn.replace('&headers','headerz')
						new_cns.append(cn)
						new_cns.append(' ')
					for x in new_cns:
						elifs+=x
				except KeyError:
					pass
				#constructing code
				x,y,z='','',''
				if ifs :
					ifs='if '+ifs
					x='''{ifs} :redirect('if',request_obj,rd)'''.format(ifs=ifs)
				if elifs:
					elifs='elif '+elifs
					y='''{elifs} :redirect('elif',request_obj,rd)'''.format(elifs=elifs)
				z='''else:raise RequestError("This is not an error ,but its a trigger that there is no redirect for this request")'''
				code=x+'\n'+y+'\n'+z
				print(code)
				try:
					exec(code)
				except SyntaxError:
					#code doesnt make sense ,maybe no if statement or wrong conditions have been given
					#no redirect so we raise an Error
					raise  RequestError("This is not an error ,but its a trigger that there is no redirect for this request")
			
				
				
	
