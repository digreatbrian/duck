#kwarg handler
'''Handle class keywords in __init__ method .'''

def handle_init_kwargs(obj,kwargs):
	'''Handle class keywords'''
	for x in kwargs.keys():
		exec('obj.{key} = kwargs["{key}"]'.format(key=x))
	