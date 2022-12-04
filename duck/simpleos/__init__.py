
'''Simple 'os' module Implementation.'''

__all__='isdir join create_file get_filedata'.split(' ')

import os
import sys
PythonVersion=sys.version.split(' ')[0]

def isdir(path):
	'''Is path a directory or a file, different from os.path.isdir works even on paths which doesnt exist'''
	if '.' not in list(path.split('/')[-1]):
		return True
	else:
		return False
		
def fixdir(d):
	'''Format path correctly according to python version used.'''
	if PythonVersion.startswith('2'):
		return str(d).strip('/')
	return str(d).strip('/')
		
def rpdir(d):
	'''Placing forward slash on path if lacking.'''
	if not str(d).startswith('/'):
		d='/'+str(d)
	return d
		
def join(a, b):
	'''Join two paths 'a' and 'b' ,if paths contains '\\' they are changed to '/' '''
	a ,b=str(a).strip() ,str(b).strip()
	sep='/'
	if '\\' in list(a) or '\\' in list(b):
		a=a.replace('\\','/')
		b=b.replace('\\','/')
		
	if not b.startswith(sep):
		if not a.endswith('/'):
			b='/'+b
	if PythonVersion.startswith('2'):
		if a.startswith('/'):
			a=a.strip('/')
	return a+b
	
def copyfile(srcfile ,dstfile):
	'''Copy srcfile data to dstfile.'''
	with open(fixdir(srcfile) ,'rb') as src:
		create_file(dstfile ,'wb',src.read())
		src.close()
	return True
	
def onlydir(filename):
	'''Returns the directory part of filename or filepath .'''
	fl=filename.split('/')
	dr=''
	for x in fl[:len(fl)]:
		if isdir(x):
			dr=join(dr,x)
	return dr
	
def create_file(filename ,mode ,data):
	'''create and write to a  file even if it doesnt exist'''
	dr=fixdir(onlydir(filename))
	try:
		if isdir(dr):
			os.makedirs(dr)
	except FileExistsError:
		pass
	except OSError:
		pass
		
	with open(filename,'a') as fd :
		fd.close()
	with open(filename,mode) as fd:
		if 'b' in list(mode):
			fd.write(data)
		else:
			if isinstance(data,bytes):
				fd.write(data.decode('utf-8'))
			else:
				fd.write(data)
		fd.close()

def get_filedata(filename ,mode='r',offset=0 ,endoffset=-1):
	'''Returns filedata with given mode which can be 'r' or 'rb' defaults to 'r' ,offset is an integer to represent bytes you want to read the file from and endoffset it defaults to '-1' where it is where the bytes to read ends and offset defaults to '0' from begining of file \nNote any '-' negative number for offset will be at  the end of the file and offset should be a positive integer. If the endoffset is greater than length of file data, the endoffset will be also at end of file .If also the endoffset is less than offset ,the endoffset will be at the end of file'''
	bytesNum=endoffset-offset
	filename=fixdir(filename)
	with open(filename,mode) as f:
		f.seek(offset)
		return f.read(bytesNum)
