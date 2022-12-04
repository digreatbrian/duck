#@session files
'''Everything related to files used by session module'''
import json

class FSession():
	'''Partial session used for reading session data and parsing out data values to be read.'''
	def __init__(self,**kwargs):
		for x in kwargs.keys():
			exec('self.{key}=kwargs["{key}"]'.format(key=x))

def read_sessions(filename):
	'''Read out all the sessions in a given file and return all of them as a list'''
	file=filename
	with open (file,'r') as fd:
		data=fd.read()
	if not data:
		return {}
	data=data.split('@session')
	sessions=[]
	for x in data:
		if x.strip():
			#single session at a time
			#extracting session data values
			dx={}
			for i in x.split('\n'):
				if i.strip() :
					a,b=i.split(':')
					dx[a.strip().lower()]=b.strip()
			try:
				session=FSession(name=dx['name'],id=dx['id'],type=dx['type'],timestamp=dx['timestamp'],expired=dx['expired'],validity=dx['validity'],extras=json.loads(dx['extras']))
			except KeyError as d :
				raise KeyError('Session with name "{name}" in file "{file}" has a missing key "{key}" '.format(name=dx['name'],file=file,key=str(d).strip('"').strip("'")))
			session.key=str(list(session.name)[:5])
			sessions.append(session)
	return sessions
	
def add_session(filename,session):
	''''Add Session to a file  .'''
	file=filename
	#Extras are any other info in Dict or Json Format
	datas='\n\n@session\nName:{name}\nId:{id}\nType:{type}\nTimestamp:{timestamp}\nExpired:{expired}\nValidity:{validity}\nExtras:{extras}'.format(name=session.name,id=session.id,type=session.type,timestamp=session.timestamp,expired=session.expired,validity=session.validity,extras=session.extras)
	sessions=read_sessions(file)
	for a in sessions:
		if a.name==session.name:
			remove_session(file,a.name)
			break
	with open(file,'a') as fd:
		fd.write(datas)
		fd.close()
		
def remove_session(filename,name):
	'''Remove session from file by referrencing its name.'''
	file=filename
	ss=read_sessions(file)
	removed_session=False
	for x in ss:
		if name==x.name:
			ss.remove(x)
			removed_session=True
	if removed_session:
		with open(file,'w') as fd:
			fd.close()
		for x in ss:
			add_session(file,x)
	

	