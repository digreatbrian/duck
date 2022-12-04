
'''Simple pretty logging of messages into the terminal.'''

def log(msg ,s='*'):
	'''pretty log msg.'''
	print('[ %s ] %s'%(s ,msg))

def cmlog(s= '*',*args):
	'''Use different msg into pretty logging of multiple lines.'''
	compile_str=''
	for msg in args:
		if msg!='\n':
			compile_str+='[ %s ] %s'%(s ,msg)
			compile_str+='\n'
		else:
			compile_str+=msg
	print(compile_str)