"""
Duck: A Python-based web server and proxy with robust Django integration.

Duck is a flexible and secure web server designed specifically for Python applications, with seamless support for Django. 
It enables easy deployment of web applications, supports HTTPS out of the box, and automates SSL certificate generation, 
making it a great choice for developers aiming to simplify the hosting and security of their Django projects.

### Key Features:
- **Django Compatibility**: Deep integration with Django, allowing easy setup and serving of Django applications.
- **HTTPS and SSL**: Built-in HTTPS support and automated SSL certificate generation for secure connections.
- **Proxy Capabilities**: Acts as both a web server and a proxy, offering versatile deployment options.

### Quick Start Example:
To start using Duck, initialize an `App` instance with your desired port and address, then run the application:

```python
from duck.app import App

app = App(port=5000, addr='127.0.0.1', domain='localhost')
app.run()
"""

from duck.version import version

__author__ = "Brian Musakwa"
__email__ = "digreatbrian@gmail.com"
__version__ = version
