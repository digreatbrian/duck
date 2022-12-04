'''Class which consist of everything that the server wants to startup.It is the main server class.'''

import threading
from .logger import log
import time
from .processor import RequestProcessor


def localtime():
	'''Return Local Time.'''
	#getting timestamp
	timestamp=time.time()
	weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
	monthname = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun','Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
	year, month, day, hh, mm, ss, wd, y, z = time.localtime(timestamp)
	s = "%s, %02d %3s %04d %02d:%02d:%02d" % (weekdayname[wd],day, monthname[month], year,hh, mm, ss)
	return s


class ServerWrapper(object):
	running=False
	poll=0.0001 #pause
	last_modified=''
	version=None
	ssl_params={}
	buffer=1024
	
	def start_server(self):
		'''Start The Server .'''
		self.running=True
		self.sock.bind(self.addr)
		if self.debug==True:
			print('\n')
		log('SERVER SERVING ON %s  ...'%list(self.addr))
		if self.debug==True:
			log('DATE : %s'%localtime())
			log('LAST-MODIFIED : %s'%self.last_modified)
		
		#listening and accepting
		while self.running:
			self.sock.listen(3)
			sock ,addr=self.sock.accept()
			th=threading.Thread(target=self.handle_conn, args= [sock ,addr])
			th.start()
			time.sleep(self.poll)
			
	def handle_conn(self,sock ,addr):
		'''Handle single connection on success'''
		app_cls=self.app_cls
		
		data=sock.recv(self.buffer)
		p=RequestProcessor(sock,app_cls)
		hndl=p.process(data)
		if not p.error:
			if hndl!='REDIRECT':
				hndl(sock ,p.request)
				
			else:
				#its a redirect so its already handled by RequestProcesser.process_for_redirect
				pass
		else:
			app_cls.handle_error(sock,p.error ,p.raw_request)
			
	def fake_close(self ,s):
		'''Fake close socket 's' '''
		
	def close(self ,sock):
		'''Close sock .'''
		sock.close()
		
	def stop_server(self):
		'''Stop The Server.'''
		self.running=False
		self.close(self.sock)
		log('SERVER STOPPED')