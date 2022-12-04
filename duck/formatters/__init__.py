
'''String argument formatting 
	example::
		d='%what%is %that%'
		argformatter(d ,sep=%)
		
	This code returns ((tuple of what is quoted by the separator '%'), and the whole string without quotes.)
	
	it returns (what ,that ,whatisthat)'''
		

def argformatter(str_ ,sep='%'):
	'''Argument string formatting.'''
	str_list=list(str_)
	argstr_=str_.replace(sep ,'')
	parseargs=None
	if sep in str_list:
		if str_list.count(sep)%2!=0:
			raise ValueError('Invalid arg string formatting " %s "'%str_)
		indexes=list()
		count=0
		for x in str_list:
			if x==sep:
				indexes.append(count)
			count+=1
		ln=len(indexes)
		args=list()
		targ=0
		for i in range(int(ln/2)):
			a, b=indexes[targ], indexes[targ+1]
			arg=''
			for c in str_list[a:b]:
				arg+=c
			targ+=2
			r=arg.split(sep)
			args.append(r[1])
		parseargs=tuple(args)
	return parseargs, argstr_
	
