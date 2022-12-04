'''Run Duck Tests Operations.'''
	
def get_code():
	data='''from duck import App
import os
from duck.simpleos import create_file

app=App('TestApp',('0.0.0.0',8000))
app.debug=True

@app.route('/%home%/testpage')
def home(par_dir):
	return 'Parent Directory is %s '%par_dir
	
def run():
	app.run()'''
	
	create_file('DuckTests/test.py',mode='w',data=data)
	
def run():
	print('RUNNING DUCK TEST SAMPLES ...')
	print('Navigate to "localhost:8000/home/testpage" in the browser to see the magic.')
	print('Use function "get_code" within this module to save test sample code.Code is saved in "DuckTests" directory in current dir.')
	from duck import App
	from duck.simpleos import create_file
	
	app=App('TestApp',('0.0.0.0',8000))
	app.debug=True
	
	@app.route('/%home%/testpage')
	def home(par_dir):
		return '''<html>
		<head><title>Duck TestPage</title>
		<script>#body{background-color:(100,0,0,0)}</script>
		</head>
		<body><h5>Parent Directory for this page is "%s"</h5></body>
		<html>
		 '''%par_dir

	app.run()
