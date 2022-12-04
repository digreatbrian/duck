'''Create and load configuration files.This module makes it easy to use 'ConfigParser' module.'''
try:
	import ConfigParser
except ImportError:
	import configparser
	ConfigParser=configparser.ConfigParser
from ..simpleos import create_file

#Configuration mod
parser=ConfigParser

def opencnf(file):
	'''Open config File .'''
	#open config
	try:
		p=parser.ConfigParser({})
	except AttributeError:
		p=parser({})
	return p.read(file) ,p
	
def getcnf(file):
	'''Get config parser object ,returns config object if successful .'''
	msg,p=opencnf(file)
	if msg!=[]:
		return p
		
def getcnfvalue(file,head ,item):
	'''Get Config value by specifying the section, which is the head and item ,if not successful returns None'''
	par=getcnf(file)
	if par!=None:
		return par.get(head ,item)
	else:
		return 
		
def createcnf(file, data=[[]]):
	'''Create configFile ;data argument is a list containing all lists which want to be added in form of [head ,item ,value] eg::
		data=[[section ,option ,value] ,[sectionb ,optionb , valueb]]'''
	a,ps=opencnf(file)
	file_fp=None
	if a==[]:
		#given file doesnt exist
		create_file(file ,mode='w', data='')
	file_fp=open(file, 'w')
	if type(data)!=type(list()):
		raise TypeError('Data should be a list in form [[section ,option ,value]]')
	for dt in data:
		if type(dt)!=type(list()):
			raise TypeError('Data Values Should be a list in form of [section ,option ,value]')
		if dt!=[]:
			if len(dt)!=3:
				raise TypeError('Data Values Should be a list in form of [section ,option ,value]')
			head ,item ,value=dt
			if not ps.has_section(head):
				ps.add_section(head)
			ps.set(str(head),str(item),str(value))
	#ps.write()
	ps.write(file_fp)
	
