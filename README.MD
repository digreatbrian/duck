![icon](https://github.com/digreatbrian/duck/blob/main/assets/duck.jpg)

# Duck Description

This module is powerful in the creation of http/https servers.

## Getting Started

To install Duck ,use pip like this::
      
    python -m pip install duck

For creating new server a few things has to be done.Consider routing app to routes and supported methods.Routes are just paths visited by a client through the browser.

This app has 3 ways of creating routes.
Consider code below::

	from duck import App
	#starting server on local host on port 8000
	app=App("Name of App",('0.0.0.0' ,8000))
	
	@app.route('/')
	def home():
		return '<p>Hello There </p>'
		
	@app.fileroute('/app.apk')
	def application():
		return 'source.apk'
		
	@app.partial_route('/comments/%animals%', meth=[post])
	def comments(about):
		print('Comment about '+about)
		
	app.run()
		
**Note**:
	`If 'meth' argument is not specified for any route creating decorator ;the 'GET' method is the default.`
	
**What Happens with these decorators**

**@app.route**  
`ON GET`  
If method "GET",the decorator creates new directories and creates a file named 'index.html' from code returned which is 'Hello There'.This file contains the code for the specified path .If the function with the decorator returns None default site is saved.The specified path will be registered which means it has been recorded that this path is to be accessed with specified method/methods.
		
`ON POST`  
The specified path will only be registered.
		
**@app.fileroute**  
`ON GET`  
Its different from one above as it require filename to be returned from function with decorator.This copies the file to destination path if size<=*app.fileroute_lim* (in megabytes).This also just does what the one above does but in a different way.
			
`ON POST`  
same as above
	
**@app.partial_route**  
`ON GET`  
It just register the path/route but the file/path must be already in *app.SITECODE_DIR directory*.*'%animals%'* mean 'animals' will parsed to the function as an argument.
			
`ON POST`  
same as above.
			
`app.run()` starts the app.
		
For handling **POST** requests override the method handlePOST.But for *GET* requests no use to override handleGET cause its already implemented.Its recommended to do this::
		
		import duck
		
		class TestApp(App):
			def __init__(self ,name,addr ,**kwargs):
				super(TestApp ,self).__init__(name,addr,**kwargs)
				
			@duck.error_handler
			def handleGET(self ,sock, rq):
				self._handleGET(sock, rq)
				#processing if the method fails to handle request.
				
			def handlePOST(self,sock,rq):
				Post handler code here.
		
The decorator "error_handler" handles some basic errors such as *unsupported protocol and unsupported http version, etc*.
**Duck** also enables user to create new methods rather than `GET,POST,HEAD,TRACE,CONNECT`,etc by constructing *handle{method}* method in the app class which will handle the "method" requests.

To create new method we can do this::
	
	import duck
	from duck import App
	
	app=App("TestApp",('0.0.0.0',8000))
	app.debug=True
	
	@duck.error_handler
	def handleCONNECT(appcls,sock,requestobj):
	   #handle code here
	   #code to handle CONNECT METHOD
	   
	  app.handleCONNECT=handleCONNECT

Setting *app.debug* to **True** mean that whatever happens is logged onto the terminal.

You may use **@duck.error_handler** decorator on method handlers like **'handleCONNECT'** for handling of errors like unsupported protocol ,unsupported http version and unsupported method. 

A request with an error  is first parsed to the "duck.handle_error" method within the app class and the app tries to handle request for you by sending error responses to the client ,but there are limitations as this might not handle error requests the way you want it.You may override this method.

To handle other different errors like  *request syntax ,unsupported method and bad header format*,you may use *app.handle_error* method to handle all these types of errors.

To customly handle these errors you may do it like this::

    def handle_error(appcls, sock, error, raw_request) :
   	  #appcls is App class
   	  #sock is where this request came from
   	  #error that the app might have found in the processing of the request
   	  #raw_request is the raw data parsed to the server by the client. We pass raw data because there might be errors is processing data which may destroy the whole data if passed to Request Object.
   	  Handle Code here


Use **APP.cnf** that will be created in directory you are running your Duck App.Use it as an application configuration file so as to manage the server settings.  
To open this file, open it in plain text format so as to edit this file. Dont Add Extra irrelevant or unnecessary data to the file, just edit it properly. 

To support/create new method just create method **'handle+METHOD'** and create a new registry for that method.

Consider example::
			
		class TestApp(App):
				def __init__(self ,name,addr,**kwargs):
					self.create_registry('connect')
				def handleCONNECT(self ,sock ,rq):
					Connect handler code here
		
Use the module's  documentation for more help

* **Terminal Execution** 

It can be also run on terminal::
	
	python -m duck -n TestApp -a 0.0.0.0 -p 8000 


"-n " : NAME of the App  
"-a"  : ADDRESS of the App  
"-p"  : PORT of the App


## Running the tests

To run test sample just import module named tests from duck module and execute function "run" like this::
	
	from duck import tests
	tests.run()

A test script is run and to get the code,call function from duck.tests with name "get_code" and the code will be saved in new directory named "DuckTests"

Do it like This ::
	
	tests.get_code()

## Deployment

Run Simple WebServer app by doing this::
	
	from duck import App
	
	app=App("DuckApp",('0.0.0.0',9000))
	app.debug=True
	
	@app.route('/')
	def home():
		return '<b>We are at the homepage.</b>'
		
	app.run()

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Authors

* **Brian Musakwa** - *Initial work* - [digreatbrian](https://github.com/digreatbrian)

See also the list of [contributors](https://github.com/digreatbrian/duck/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

*We thank the contributors for their efforts in this software as theier investment in this work really matters.
