
from file_session import add_session,read_sessions
import os,threading
import random,time
from encrypto import encrypt

session_secrets=['session','environ','foo😀','upwego😍','cool😜','good😉','stable😊','difficult🙄','happy😂','married🤗','financial🤑']

class SessionEnviron():
	parent_dir='./'
	env_file=''
	_status='activated'
	def __init__(self,name,**kwargs):
		self.name=name
		try:
			os.makedirs(self.parent_dir)
		except FileExistsError:
			pass
		self.prepare_env()
		self.activate()
		
	@property
	def state(self):
		return self._status
		
	def activate(self):
		self._status='activated'
	
	def deactivate(self):
		self._status='deactivated'
			
	def prepare_env(self):
		env_file=os.path.join(self.parent_dir,self.name.lower()+'.env')
		self.env_file=env_file
		#try to open existing env or create new one
		with open(env_file,'a') as d:
			d.close()
		os.environ[self.name.upper()+'_SENV']=env_file

class Session():
	expired=False
	key=session_secrets[random.randint(0,len(session_secrets)-1)]
	
	def __init__(self,name,environ,use_filesave=True,id=None,type=None,timestamp=None,validity=0,extras={},**kwargs):
		self.use_filesave=use_filesave
		self.name=name
		self.type=type
		self.validity=validity
		self.extras=extras
		self.environ=environ
		if not isinstance(environ,SessionEnviron):
			raise TypeError('environ argument should be of type <SessionEnviron> ')
		if not id:
			self.id=encrypt(name,self.key)
		if not timestamp:
			self.timestamp=time.time()
		else:self.timestamp=timestamp
		
		if self.use_filesave:
			self.start_timer()
			self.save()
		
	def save(self):
		'''Save session to environment'''
		if self.environ.state.lower()=='activated':
			add_session(self.environ.env_file,self)
		else:
			raise TypeError('Failed to save session to environment "{env}" because environment not activated .'.format(env=self.environ.name))
		
	def start_timer(self):
		self.timer_up=False
		def interval(*args):
			time.sleep(1)
			while not self.timer_up:
				stop_timestamp=float(self.timestamp)+float(self.validity)
				if time.time()>=stop_timestamp:
					self.expired=True
					self.timer_up=True
					try:
						if self.use_filesave:
							self.save()
					except TypeError:
						pass
		thread=threading.Thread(target=interval)
		thread.start()


