'''Advance module for using mimetypes module.'''

import mimetypes

def guess_type(filename, data=None):
	'''Read mimetype specificifying 'filename' or 'data' argument.Argument 'filename' should be None for data 'argument'' to be used'''
	a=None #mimetype
	if filename:
		a ,b=mimetypes.guess_type(filename)
		
	if not a:
		#if type is None
		if filename:
			return read_type(filename,data)
		else:
			if data:
				 return read_type(filename,data)
			else:
				return None
	else:
		return a
				 
		
def read_type(filename,data=None):
	'''Read mimetype from data or filename.Specify filename None for data to be used or vice-versa.'''
	if not data:
		rb=open(filename ,'rb')
		fp=rb
		rb=rb.read(10)#reading first 10bytes
		fp.close()
	else:
		rb=''
		p=10
		if len(data)<p:
			p=-1
		for x in list(data)[:p]:
			rb+=x
	import string
	ls=list(string.printable)
	r=1
	for x in list(rb):
		if  x in ls:
			r+=1
	if r>=len(rb):
		return 'text/plain'
	return 'application/octet-stream'
	