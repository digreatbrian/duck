
'''Module for route functions for creating routes and deleting routes and also getting data in routes .
'''
from .simpleos import create_file, isdir, get_filedata ,join,fixdir
from .errors import RouteError
import glob
import sys
import os

PythonVersion=sys.version.split(' ')[0]

__all__='get_routedata delete_fileroute delete_routefiles delete_route add_route'.split(' ')

def get_routedata(route ,mode='r',start_index=0, end_index=-1):
	'''Returns data in route start_ind)ex argument is the byte position where you want to start reading from defaults to 0 ,should be positive and end_index is where to end reading data at defaults to -1 ,and every negative end index will be at end of data '''
	if isdir(route):
		route=join(route ,'index.html')
	fileroute=route
	return get_filedata(fileroute, mode,start_index ,end_index)

def delete_fileroute(filepath):
	'''This deletes specific fileroute that is specific file '''
	with open(filepath ,'w') as d:
		d.close()
	#deleting now
	os.remove(filepath)
	
def delete_routefiles(filepath,types=['*.*']):
	'''This deletes specific files in route using argument types which is a list containing types of files to be deleted defaults to *.* that is all files '''
	for i in types:
		dirr=glob.glob(filepath,i )
		for x in dirr:
			delete_filepath(x)
	
def delete_route(route):
	'''Delete route and whatever in the route'''
	listdir=glob.glob(route ,'*.*')
	for file in listdir:
		delete_fileroute(file)
	os.removedirs(route)
	
def get_fileroutedata(fileroute ,mode='br',start_index=0, end_index=-1):
	'''Get fileroute data by specifying fileroute which is the filename ,and mode which can be 'r' and, 'rb' for buffered reader, start_index is number of bytes to start to read from and, end_index where to read to.'''
	fileroute=fixdir(fileroute)
	data=get_filedata(fileroute, mode,start_index ,end_index)
	return data 
	
def add_route(route ,data):
	'''Creating route by creating files,which  is done for safekeeping of Route Data or for user to see what kind of data was registered for specific route.'''
	if PythonVersion.startswith('2'):
			if route.startswith("/") or route.startswith('\\'):
				if '\\' in list(route):
					route=route.replace('\\','/');route=route.strip('/')
	file=route
	mode='w'
	if isdir(route):
		try:
			os.makedirs(route)
		except OSError:
			pass
		if route=='/':
			file='index.html'
		else:
			file=join(route, 'index.html')
	else:
		raise RouteError('Path specified should be a directory')
	create_file(file ,mode ,data)
		